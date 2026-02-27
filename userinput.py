#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
用户输入脚本 - 轮询等待版本
Usage:
    tt userinput.py           # 等待 prompts.txt 出现（默认超时 3600s）
    tt userinput.py --timeout 60  # 自定义超时时间（秒）

行为：
  - prompts.txt 有内容时：读取并清空，立即返回
  - prompts.txt 为空时：轮询等待，直到用户写入内容或超时
"""

import os
import sys
import time

POLL_INTERVAL = 5
DEFAULT_TIMEOUT = 3600
END_KEYWORDS = {"结束", "end", "exit", "quit", "stop"}


PLACEHOLDER = "# 在此输入任务，保存后 AI 将自动读取\n"


def read_and_clear(filename='prompts.txt'):
    if not os.path.exists(filename):
        return None
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        lines = [l for l in content.splitlines() if not l.strip().startswith('#')]
        stripped = '\n'.join(lines).strip()
        if stripped:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(PLACEHOLDER)
            return stripped
    except Exception as e:
        print(f"读取文件 {filename} 时出错: {e}")
    return None


def parse_timeout():
    timeout = DEFAULT_TIMEOUT
    if '--timeout' in sys.argv:
        idx = sys.argv.index('--timeout')
        if idx + 1 < len(sys.argv):
            try:
                timeout = int(sys.argv[idx + 1])
            except ValueError:
                pass
    return timeout


def is_end_signal(content: str) -> bool:
    return content.strip().lower() in END_KEYWORDS


def main():
    content = read_and_clear()
    if content:
        if is_end_signal(content):
            print("[END_SESSION]")
            print("用户已说结束，会话终止。")
            return
        print("发现 prompts.txt 文件，内容如下:")
        print("=" * 60)
        print(content)
        print("=" * 60)
        print("\n任务完成！")
        return

    timeout = parse_timeout()
    print(f"⏳ 等待用户输入...（超时 {timeout}s）")
    print("   请在 prompts.txt 中写入任务内容。")

    elapsed = 0
    while elapsed < timeout:
        time.sleep(POLL_INTERVAL)
        elapsed += POLL_INTERVAL
        content = read_and_clear()
        if content:
            if is_end_signal(content):
                print("[END_SESSION]")
                print("用户已说结束，会话终止。")
                return
            print(f"\n✅ 检测到新任务（等待了 {elapsed}s），内容如下:")
            print("=" * 60)
            print(content)
            print("=" * 60)
            print("\n任务完成！")
            return

    print(f"\n⚠️ 超时（{timeout}s），未检测到输入，跳过。")


if __name__ == "__main__":
    main()
