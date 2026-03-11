#!/usr/bin/env python3
"""快照生成工具 - 将缓冲内容转换为快照文件"""

import os
import sys
from datetime import datetime
from pathlib import Path

def get_project_root():
    """获取项目根目录"""
    script_dir = Path(__file__).parent
    return script_dir.parent

def get_buffer_file():
    """获取缓冲文件路径"""
    root = get_project_root()
    return root / 'mem' / '.snapshot_buffer.md'

def get_snapshot_dir():
    """获取快照目录"""
    root = get_project_root()
    snapshot_dir = root / 'mem' / 'snapshot'
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    return snapshot_dir

def generate_snapshot():
    """根据缓冲文件生成快照"""
    buffer_file = get_buffer_file()
    snapshot_dir = get_snapshot_dir()

    # 如果缓冲文件不存在或为空，跳过
    if not buffer_file.exists():
        return False

    content = buffer_file.read_text(encoding='utf-8')

    if not content.strip():
        return False

    # 生成快照文件名（当前时间）
    now = datetime.now()
    snapshot_name = f"快照-{now.year}-{now.month}-{now.day}-{now.hour}{now.minute:02d}.md"
    snapshot_file = snapshot_dir / snapshot_name

    # 保存快照
    snapshot_file.write_text(content, encoding='utf-8')
    print(f"✅ 快照已生成: {snapshot_name}")

    # 清空缓冲文件
    buffer_file.write_text('', encoding='utf-8')
    return True

if __name__ == '__main__':
    try:
        if generate_snapshot():
            print("成功")
            sys.exit(0)
        else:
            print("无新内容")
            sys.exit(0)
    except Exception as e:
        print(f"❌ 快照生成失败: {e}", file=sys.stderr)
        sys.exit(1)
