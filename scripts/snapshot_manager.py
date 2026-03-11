#!/usr/bin/env python3
"""会话快照管理器 - 每15分钟自动生成快照"""

import os
import sys
import time
from datetime import datetime
from pathlib import Path

def get_snapshot_dir():
    """获取快照目录"""
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent
    snapshot_dir = root_dir / 'mem' / 'snapshot'
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    return snapshot_dir

def get_buffer_file():
    """获取缓冲文件路径"""
    root_dir = Path(__file__).parent.parent
    return root_dir / 'mem' / '.snapshot_buffer.md'

def generate_snapshot():
    """根据缓冲文件生成快照"""
    buffer_file = get_buffer_file()
    snapshot_dir = get_snapshot_dir()

    # 如果缓冲文件不存在或为空，跳过
    if not buffer_file.exists() or buffer_file.stat().st_size == 0:
        return False

    # 读取缓冲内容
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

def monitor_loop(interval=900):
    """监控循环 - 每interval秒检查一次（默认900秒=15分钟）"""
    print(f"📸 快照监控已启动（间隔: {interval}秒）")
    print(f"🕐 当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    iteration = 0
    while True:
        time.sleep(interval)
        iteration += 1
        now = datetime.now()
        print(f"\n[快照检查 #{iteration}] {now.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)

        try:
            if generate_snapshot():
                pass  # 快照已生成
            else:
                print(f"  （无新内容）", flush=True)
        except Exception as e:
            print(f"❌ 快照生成失败: {e}", flush=True)

if __name__ == '__main__':
    # 间隔可通过命令行参数覆盖（--interval 秒数）
    interval = 900  # 默认15分钟

    if len(sys.argv) > 1:
        try:
            interval = int(sys.argv[1])
        except ValueError:
            print(f"用法: python snapshot_manager.py [间隔秒数]")
            sys.exit(1)

    monitor_loop(interval)
