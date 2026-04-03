"""
Two-Step Conversion Pipeline

实现忠实还原和智能增强的两步转换流水线。
在没有可用 API Key 时自动回退到本地安全模式，确保流程可跑通。
"""

import os
import re

from model_adapter import ModelAdapterFactory


class Converter:
    """两步转换流水线"""

    def __init__(self, config, logger=None, pdf_type=None):
        """初始化转换器"""
        self.config = config
        self.logger = logger
        self.pdf_type = pdf_type
        self._adapter = None

    def convert_restore(self, pdf_content, pdf_metadata):
        """
        第一步：忠实还原

        严格对应原文，不增加任何原文没有的内容。
        """
        prompt = self._build_restore_prompt(pdf_content, pdf_metadata)
        model_output = self._call_model(prompt)
        if model_output:
            return self._ensure_frontmatter_and_title(model_output, pdf_metadata)

        return self._fallback_restore(pdf_content, pdf_metadata)

    def convert_enhance(self, restore_markdown, pdf_metadata):
        """
        第二步：智能增强

        基于忠实还原版，有据可依的补充和扩展。
        """
        prompt = self._build_enhance_prompt(restore_markdown, pdf_metadata)
        model_output = self._call_model(prompt)
        if model_output:
            return self._ensure_frontmatter_and_title(model_output, pdf_metadata)

        return self._fallback_enhance(restore_markdown)

    def convert_full(self, pdf_content, pdf_metadata):
        """完整转换（两步合并）"""
        restore_markdown = self.convert_restore(pdf_content, pdf_metadata)
        enhance_markdown = self.convert_enhance(restore_markdown, pdf_metadata)
        return restore_markdown, enhance_markdown

    def _call_model(self, prompt):
        """调用模型，失败时返回 None 并走本地回退。"""
        if self._is_offline_mode():
            self._warn('离线模式已启用，跳过外部模型调用。')
            return None

        try:
            adapter = self._get_adapter()
            max_retries = self._get_config('api.max_retries', 3)
            return adapter.call(prompt, max_retries=max_retries)
        except Exception as exc:
            self._warn(f"模型调用不可用，已切换本地回退模式: {exc}")
            return None

    def _get_adapter(self):
        if self._adapter is None:
            self._adapter = ModelAdapterFactory.create_from_config(
                self.config,
                logger=self.logger,
                pdf_type=self.pdf_type,
            )
        return self._adapter

    def _build_restore_prompt(self, pdf_content, pdf_metadata):
        title = pdf_metadata.get('title', '未命名文档')
        source_pdf = pdf_metadata.get('source_pdf', 'unknown.pdf')
        text = self._extract_text(pdf_content)
        return (
            "你是技术文档还原助手。请严格忠实还原原文，不添加原文没有的信息。\n"
            f"文档标题: {title}\n"
            f"源文件: {source_pdf}\n"
            "以下是提取文本:\n"
            f"{text}"
        )

    def _build_enhance_prompt(self, restore_markdown, pdf_metadata):
        title = pdf_metadata.get('title', '未命名文档')
        return (
            "你是技术文档增强助手。请在不新增无依据信息的前提下优化表达和结构。\n"
            f"文档标题: {title}\n"
            "以下是忠实还原版 Markdown:\n"
            f"{restore_markdown}"
        )

    def _fallback_restore(self, pdf_content, pdf_metadata):
        """本地回退：直接生成结构化忠实还原版。"""
        frontmatter = pdf_metadata.get('frontmatter', '').strip()
        title = pdf_metadata.get('title', '未命名文档')
        source_pdf = pdf_metadata.get('source_pdf', 'unknown.pdf')
        text = self._extract_text(pdf_content)

        chunks = []
        if frontmatter:
            chunks.append(frontmatter)
        chunks.append(f"# {title}")
        chunks.append("## 文档信息")
        chunks.append(f"- 来源文件：{source_pdf}")
        chunks.append("- 生成模式：本地回退（未调用外部模型）")
        chunks.append("## 原文内容")
        chunks.append(text if text else "（未提取到正文文本）")
        return "\n\n".join(chunks).strip() + "\n"

    def _fallback_enhance(self, restore_markdown):
        """本地回退：仅做格式层增强，不新增事实内容。"""
        lines = [line.rstrip() for line in restore_markdown.splitlines()]

        enhanced = []
        blank_count = 0
        for line in lines:
            if not line.strip():
                blank_count += 1
                if blank_count <= 2:
                    enhanced.append("")
            else:
                blank_count = 0
                enhanced.append(line)

        content = "\n".join(enhanced).strip() + "\n"
        return content

    def _extract_text(self, pdf_content):
        if isinstance(pdf_content, str):
            return pdf_content.strip()

        if not isinstance(pdf_content, dict):
            return str(pdf_content)

        if 'full_text' in pdf_content:
            return str(pdf_content.get('full_text', '')).strip()

        text_block = pdf_content.get('text')
        if isinstance(text_block, dict):
            return str(text_block.get('full_text', '')).strip()

        pages = pdf_content.get('pages')
        if isinstance(pages, list):
            parts = []
            for page in pages:
                if isinstance(page, dict):
                    parts.append(str(page.get('text', '')))
            return "\n\n".join(parts).strip()

        return ""

    def _ensure_frontmatter_and_title(self, markdown, pdf_metadata):
        """确保输出包含 Frontmatter 和一级标题。"""
        output = markdown.strip()
        frontmatter = pdf_metadata.get('frontmatter', '').strip()
        title = pdf_metadata.get('title', '未命名文档')

        if frontmatter and not output.startswith('---'):
            output = f"{frontmatter}\n\n{output}".strip()

        heading_pattern = re.compile(r'^#\s+', re.MULTILINE)
        if not heading_pattern.search(output):
            output = f"{output}\n\n# {title}".strip()

        return output + "\n"

    def _get_config(self, key, default=None):
        if hasattr(self.config, 'get'):
            return self.config.get(key, default)
        return default

    def _is_offline_mode(self):
        flag = self._get_config('api.offline_mode', False)
        if isinstance(flag, str):
            flag = flag.strip().lower() in {'1', 'true', 'yes', 'on'}

        env_flag = os.getenv('PDFSC_OFFLINE', '').strip().lower()
        return bool(flag) or env_flag in {'1', 'true', 'yes', 'on'}

    def _warn(self, message):
        if self.logger and hasattr(self.logger, 'warning'):
            self.logger.warning(message)
            return
        print(f"[WARNING] {message}")
