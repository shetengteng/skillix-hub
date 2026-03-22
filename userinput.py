#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
交互式用户输入脚本
Usage:
    tt userinput.py # 自动检测prompts.txt，如不存在则进入交互模式
"""

import os

def read_prompts_file(filename='prompts.txt'):
    """读取prompts文件并返回所有内容"""
    if not os.path.exists(filename):
        return None
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if content:
                return content
    except Exception as e:
        print(f"读取文件 {filename} 时出错: {e}")
    
    return None


def main():
    """主函数"""
      
    content = read_prompts_file()
    if content:
        print(content)
    else:
        print("结束会话")
        
if __name__ == "__main__":
    main() 
