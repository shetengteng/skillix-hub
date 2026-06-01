#!/usr/bin/env bash
# run-opencode.sh — 在非 TTY 环境（如 Cursor Shell）中运行 OpenCode 并解析输出
#
# OpenCode 的 TUI 渲染依赖 TTY。在 IDE 内嵌 Shell 中直接调用会丢失输出。
# 本脚本通过 --format json + nohup + 文件重定向绕过此限制。
#
# Usage:
#   bash run-opencode.sh "你的自然语言指令"
#   bash run-opencode.sh "你的指令" --model "ai_chat/claude-sonnet-4-6"
#   bash run-opencode.sh "你的指令" --raw          # 输出原始 JSONL
#   bash run-opencode.sh "你的指令" --timeout 120   # 超时秒数（默认 300）

set -euo pipefail

PROMPT=""
MODEL="ai_chat/claude-sonnet-4-6"
RAW=false
TIMEOUT=300
OUTPUT_FILE="/tmp/opencode-run-$(date +%s).jsonl"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --model)   MODEL="$2"; shift 2 ;;
    --raw)     RAW=true; shift ;;
    --timeout) TIMEOUT="$2"; shift 2 ;;
    --output)  OUTPUT_FILE="$2"; shift 2 ;;
    -*)        echo "Unknown flag: $1" >&2; exit 1 ;;
    *)         PROMPT="$1"; shift ;;
  esac
done

if [[ -z "$PROMPT" ]]; then
  echo "Usage: bash run-opencode.sh \"你的指令\" [--model MODEL] [--raw] [--timeout SEC]" >&2
  exit 1
fi

nohup opencode run --format json -m "$MODEL" \
  --dangerously-skip-permissions "$PROMPT" \
  > "$OUTPUT_FILE" 2>&1 &
BG_PID=$!

echo "PID: $BG_PID | Output: $OUTPUT_FILE | Timeout: ${TIMEOUT}s" >&2

ELAPSED=0
while kill -0 "$BG_PID" 2>/dev/null; do
  sleep 2
  ELAPSED=$((ELAPSED + 2))
  if [[ $ELAPSED -ge $TIMEOUT ]]; then
    echo "Timeout (${TIMEOUT}s). Killing PID $BG_PID" >&2
    kill "$BG_PID" 2>/dev/null || true
    break
  fi
done

wait "$BG_PID" 2>/dev/null || true

if [[ "$RAW" == "true" ]]; then
  cat "$OUTPUT_FILE"
  exit 0
fi

python3 -c "
import json, sys

with open('$OUTPUT_FILE') as f:
    lines = f.readlines()

skills_loaded = []
tool_calls = []
text_parts = []

for line in lines:
    line = line.strip()
    if not line:
        continue
    try:
        ev = json.loads(line)
        t = ev.get('type', '')
        if t == 'tool_use':
            part = ev['part']
            tool = part.get('tool', '')
            state = part.get('state', {})
            inp = state.get('input', {})
            out = state.get('output', '')
            if tool == 'skill':
                skills_loaded.append(inp.get('name', '?'))
            elif tool == 'bash':
                cmd = inp.get('command', inp.get('description', ''))
                tool_calls.append({'tool': 'bash', 'command': cmd[:120], 'output': out[:800]})
            else:
                tool_calls.append({'tool': tool, 'input': str(inp)[:120], 'output': out[:800]})
        elif t == 'text':
            text_parts.append(ev['part'].get('text', ''))
    except:
        pass

print('=== Skills Loaded ===')
for s in skills_loaded:
    print(f'  - {s}')

print()
print('=== Tool Calls ===')
for tc in tool_calls:
    print(f'  [{tc[\"tool\"]}] {tc.get(\"command\", tc.get(\"input\", \"\"))}')
    if tc['output']:
        preview = tc['output'][:300]
        print(f'    -> {preview}')
    print()

if text_parts:
    print('=== Final Response ===')
    print(''.join(text_parts))
"
