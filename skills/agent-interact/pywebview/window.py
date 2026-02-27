#!/usr/bin/env python3
"""
pywebview window manager for agent-interact.
Replaces electron/main.js — connects to the Express/WebSocket server
and opens a native WKWebView window for each dialog:open event.

Usage: python3 window.py <port>
"""

import json
import os
import subprocess
import sys
import threading
import time

try:
    import webview
except ImportError:
    print(json.dumps({"error": "pywebview not installed. Run: pip3 install pywebview"}), flush=True)
    sys.exit(1)

try:
    import websocket
except ImportError:
    print(json.dumps({"error": "websocket-client not installed. Run: pip3 install websocket-client"}), flush=True)
    sys.exit(1)

port = int(sys.argv[1]) if len(sys.argv) > 1 else 7890
server_url = f"http://127.0.0.1:{port}"
ws_url = f"ws://127.0.0.1:{port}/ws"

READY_FILE = os.path.join(os.path.dirname(__file__), '..', f'.pywebview-ready-{port}')

BASE_SIZES = {
    "confirm":      (500, 440),
    "wait":         (440, 400),
    "chart":        (720, 560),
    "form":         (520, 560),
    "approval":     (520, 500),
    "progress":     (500, 520),
    "custom":       (620, 560),
    "notification": (420, 200),
}


def estimate_window_size(dialog):
    dtype = dialog.get("type", "custom")
    width, height = BASE_SIZES.get(dtype, (480, 400))

    if dtype == "notification" and dialog.get("message"):
        lines = max(1, len(dialog["message"]) // 40)
        height = max(height, 120 + lines * 22)

    if dtype == "confirm" and dialog.get("options"):
        height = max(height, 240 + len(dialog["options"]) * 76)

    if dtype == "form" and dialog.get("fields"):
        height = max(height, 240 + len(dialog["fields"]) * 84)

    if dtype == "progress" and dialog.get("steps"):
        height = max(height, 280 + len(dialog["steps"]) * 52)

    if dtype == "custom" and dialog.get("content"):
        content_height = 0
        for node in dialog["content"]:
            kind = node.get("kind", "")
            if kind == "heading":       content_height += 40
            elif kind == "text":        content_height += 30
            elif kind == "divider":     content_height += 20
            elif kind == "alert":       content_height += 50
            elif kind == "badge":       content_height += 32
            elif kind == "kv":          content_height += (len(node.get("items", [])) * 28 or 60) + 16
            elif kind == "progress":    content_height += 50
            elif kind == "table":       content_height += 40 + len(node.get("rows", [])) * 36
            elif kind == "chart":
                content_height += 280
                width = max(width, 640)
            elif kind == "code":        content_height += 80
            elif kind == "image":       content_height += 200
            elif kind in ("input", "select"): content_height += 70
            elif kind == "textarea":    content_height += 100
            elif kind == "checkbox":    content_height += 40
            elif kind in ("row", "column", "grid", "section", "group"):
                content_height += 60 + len(node.get("children", [])) * 50
            else:                       content_height += 40
        height = max(height, 200 + content_height)

        meta = dialog.get("meta", {})
        if meta.get("maxWidth") == "2xl":   width = max(width, 800)
        elif meta.get("maxWidth") == "xl":  width = max(width, 700)

    return min(width, 1200), min(height, 900)


def show_notification(dialog):
    """Use macOS native notification via osascript."""
    level_emoji = {"success": "✅", "warning": "⚠️", "error": "❌", "info": "ℹ️"}
    emoji = level_emoji.get(dialog.get("level", ""), "")
    title = f"{emoji} {dialog.get('title', 'Agent Interact')}".strip()
    message = dialog.get("message", "")
    try:
        script = f'display notification "{message}" with title "{title}"'
        subprocess.Popen(
            ["osascript", "-e", script],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass


# Map: dialog_id -> webview.Window
_windows: dict = {}
_windows_lock = threading.Lock()

# Thread-safe queue for window operations (must execute on GUI thread via func callback)
_open_queue: list = []
_close_queue: list = []
_queue_lock = threading.Lock()
_queue_event = threading.Event()
_running = True


def _open_dialog_window(dialog):
    """Create and show a pywebview window for the given dialog. Called on GUI thread."""
    dialog_id = dialog.get("id")
    dtype = dialog.get("type")

    with _windows_lock:
        if dialog_id in _windows:
            return

    width, height = estimate_window_size(dialog)
    url = f"{server_url}?dialogId={dialog_id}"

    win = webview.create_window(
        title=dialog.get("title", "Agent Interact"),
        url=url,
        width=width,
        height=height,
        on_top=True,
        resizable=True,
    )

    with _windows_lock:
        _windows[dialog_id] = win

    if dtype == "notification":
        show_notification(dialog)
        auto_close = dialog.get("autoClose", 8)

        def _auto_close():
            time.sleep(auto_close)
            with _windows_lock:
                w = _windows.pop(dialog_id, None)
            if w:
                try:
                    w.destroy()
                except Exception:
                    pass

        threading.Thread(target=_auto_close, daemon=True).start()


def _close_dialog_window(dialog_id):
    """Close a pywebview window. Called on GUI thread."""
    with _windows_lock:
        win = _windows.pop(dialog_id, None)
    if win:
        try:
            win.destroy()
        except Exception:
            pass


def _gui_loop():
    """
    Runs as the func passed to webview.start().
    Waits for queue events instead of busy-polling, to avoid CPU usage.
    """
    global _running
    try:
        open(READY_FILE, 'w').close()
    except Exception:
        pass

    while _running:
        _queue_event.wait(timeout=1.0)
        _queue_event.clear()

        with _queue_lock:
            opens = list(_open_queue)
            closes = list(_close_queue)
            _open_queue.clear()
            _close_queue.clear()

        for dialog_id in closes:
            _close_dialog_window(dialog_id)

        for dialog in opens:
            _open_dialog_window(dialog)


def _ws_thread():
    """Background thread: connect to WebSocket and handle dialog events."""
    reconnect_delay = 1

    while _running:
        try:
            ws_app = websocket.WebSocketApp(
                ws_url,
                on_message=_on_ws_message,
                on_error=lambda ws, e: None,
                on_close=lambda ws, code, msg: None,
            )
            ws_app.run_forever()
        except Exception:
            pass

        if not _running:
            break
        time.sleep(reconnect_delay)
        reconnect_delay = min(reconnect_delay * 2, 10)


def _on_ws_message(ws, raw):
    try:
        msg = json.loads(raw)
        event = msg.get("event")
        data = msg.get("data", {})

        if event == "dialog:open":
            with _queue_lock:
                _open_queue.append(data)
            _queue_event.set()
        elif event == "dialog:close":
            dialog_id = data.get("id")
            if dialog_id:
                with _queue_lock:
                    _close_queue.append(dialog_id)
                _queue_event.set()
    except Exception:
        pass


def main():
    global _running

    # Start WebSocket listener in background
    ws_t = threading.Thread(target=_ws_thread, daemon=True)
    ws_t.start()

    # pywebview requires at least one window before start().
    # Create a hidden placeholder so the event loop can start.
    # Real dialog windows are created dynamically via _gui_loop().
    webview.create_window("", url="about:blank", width=1, height=1, hidden=True)

    try:
        webview.start(_gui_loop, debug=False)
    finally:
        _running = False
        try:
            os.unlink(READY_FILE)
        except Exception:
            pass


if __name__ == "__main__":
    main()
