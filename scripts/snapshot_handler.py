#!/usr/bin/env python3
"""
快照配置驱动处理器
读取会话管理协议.md的配置，识别快照关键词，自动生成快照
支持会话隔离：每个会话有唯一SESSION_ID
"""

import re
import uuid
from pathlib import Path
from datetime import datetime

class SnapshotHandler:
    """快照处理的配置驱动实现"""

    def __init__(self, root_dir=None, session_id=None):
        """初始化处理器"""
        if root_dir is None:
            # 脚本位置：scripts/snapshot_handler.py
            # 项目根目录：../
            root_dir = Path(__file__).parent.parent

        self.root_dir = Path(root_dir)
        self.protocol_file = self.root_dir / "会话管理协议.md"
        self.snapshot_dir = self.root_dir / "mem" / "snapshot"

        # 生成或使用传入的SESSION_ID
        if session_id is None:
            now = datetime.now()
            short_uuid = uuid.uuid4().hex[:4]
            self.session_id = f"{now.strftime('%Y%m%d_%H%M')}_{short_uuid}"
        else:
            self.session_id = session_id

        # 隔离的缓冲文件（带SESSION_ID后缀）
        self.buffer_file = self.root_dir / "mem" / f".snapshot_buffer_{self.session_id}.md"

        # 缓存的关键词配置
        self.keywords = self._load_keywords()

        print(f"📍 会话隔离已启用，SESSION_ID: {self.session_id}")

    def _load_keywords(self):
        """从会话管理协议.md读取关键词配置"""
        if not self.protocol_file.exists():
            print(f"❌ 协议文件不存在: {self.protocol_file}")
            return {}

        content = self.protocol_file.read_text(encoding='utf-8')

        # 解析第四章的触发词汇表
        keywords = {
            'snapshot': [],      # 快照触发
            'archive': [],       # 结束归档
            'resume': []         # 恢复会话
        }

        # 提取快照触发关键词 (快照触发：    "快照" / "保存快照")
        snapshot_match = re.search(
            r'快照触发：\s*"([^"]+)"\s*/\s*"([^"]*)"',
            content
        )
        if snapshot_match:
            keywords['snapshot'] = [snapshot_match.group(1)]
            if snapshot_match.group(2):
                keywords['snapshot'].append(snapshot_match.group(2))

        # 提取结束归档关键词
        archive_match = re.search(
            r'结束归档：\s*"([^"]+)"\s*/\s*"([^"]*)"',
            content
        )
        if archive_match:
            keywords['archive'] = [archive_match.group(1)]
            if archive_match.group(2):
                keywords['archive'].append(archive_match.group(2))

        # 提取恢复会话关键词
        resume_match = re.search(
            r'恢复会话：\s*"([^"]+)"\s*/\s*"([^"]*)"',
            content
        )
        if resume_match:
            keywords['resume'] = [resume_match.group(1)]
            if resume_match.group(2):
                keywords['resume'].append(resume_match.group(2))

        print(f"✅ 已加载关键词配置:")
        print(f"   快照触发: {keywords['snapshot']}")
        print(f"   结束归档: {keywords['archive']}")
        print(f"   恢复会话: {keywords['resume']}")

        return keywords

    def check_trigger(self, user_message):
        """
        检查用户消息是否触发快照动作
        返回: ('snapshot' | 'archive' | 'resume' | None)
        """
        message = user_message.strip()

        # 检查快照触发
        for keyword in self.keywords.get('snapshot', []):
            if keyword in message:
                return 'snapshot'

        # 检查结束归档
        for keyword in self.keywords.get('archive', []):
            if keyword in message:
                return 'archive'

        # 检查恢复会话
        for keyword in self.keywords.get('resume', []):
            if re.search(keyword, message):
                return 'resume'

        return None

    def generate_snapshot(self, conversation_text):
        """
        生成快照文件
        文件名格式：快照-YYYY-M-D-HHMM-[SESSION_ID].md

        Args:
            conversation_text: 本次会话的对话文本

        Returns:
            快照文件路径
        """
        # 确保目录存在
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)

        # 生成文件名（当前时间 + SESSION_ID）
        now = datetime.now()
        snapshot_name = f"快照-{now.year}-{now.month}-{now.day}-{now.hour}{now.minute:02d}-{self.session_id}.md"
        snapshot_file = self.snapshot_dir / snapshot_name

        # 保存快照
        snapshot_file.write_text(conversation_text, encoding='utf-8')
        print(f"✅ 快照已生成: {snapshot_name}")
        print(f"   路径: {snapshot_file}")

        return snapshot_file

    def clear_buffer(self):
        """清空缓冲文件并重新初始化新周期"""
        # 初始化新缓冲
        new_buffer = f"""# 会话快照缓冲 - {datetime.now().strftime('%Y-%m-%d %H:%M')}+ [{self.session_id}]

**当前会话开始时间**：{datetime.now().strftime('%Y-%m-%d %H:%M')}
**会话ID**：{self.session_id}
**参与方**：用户 + Claude Code（本地）

---

## 时间段：{datetime.now().strftime('%H:%M')} - 进行中

（本次会话记录将从此开始累积）
"""
        self.buffer_file.write_text(new_buffer, encoding='utf-8')
        print(f"✅ 缓冲已清空并重新初始化：{self.buffer_file.name}")

    def process_message(self, user_message, conversation_text=None):
        """
        处理用户消息，根据配置自动触发快照操作

        Args:
            user_message: 用户输入的消息
            conversation_text: 当前会话的对话内容（用于生成快照）

        Returns:
            ('snapshot' | 'archive' | 'resume' | None, 操作说明)
        """
        trigger_type = self.check_trigger(user_message)

        if trigger_type == 'snapshot':
            if conversation_text:
                self.generate_snapshot(conversation_text)
                self.clear_buffer()
            return ('snapshot', '✅ 快照生成成功')

        elif trigger_type == 'archive':
            return ('archive', '✅ 触发备忘生成流程')

        elif trigger_type == 'resume':
            return ('resume', '✅ 触发会话恢复流程')

        return (None, '（无快照操作）')


if __name__ == '__main__':
    # 测试处理器
    handler = SnapshotHandler()

    print(f"\n=== 测试快照触发机制 [SESSION_ID: {handler.session_id}] ===\n")

    # 测试1：快照触发
    test_messages = [
        ("快照", True),
        ("保存快照", True),
        ("归档", False),
        ("正常对话，无快照", False)
    ]

    for msg, should_trigger in test_messages:
        trigger_type, explanation = handler.process_message(msg)
        status = "✅" if (trigger_type is not None) == should_trigger else "❌"
        print(f"{status} 消息: '{msg}'")
        print(f"   触发类型: {trigger_type}")
        print(f"   说明: {explanation}\n")
