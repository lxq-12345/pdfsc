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
        self._last_call_mode = 'unknown'
        self._last_restore_mode = 'unknown'
        self._last_enhance_mode = 'unknown'

    def convert_restore(self, pdf_content, pdf_metadata):
        """
        第一步：忠实还原

        严格对应原文，不增加任何原文没有的内容。
        """
        prompt = self._build_restore_prompt(pdf_content, pdf_metadata)
        model_output = self._call_model(prompt)
        if model_output:
            output = self._ensure_frontmatter_and_title(model_output, pdf_metadata)
            if self._should_mark_low_quality():
                output = self._apply_low_quality_marker(output, stage='restore')
            self._last_restore_mode = self._last_call_mode
            return output

        result = self._apply_low_quality_marker(
            self._fallback_restore(pdf_content, pdf_metadata),
            stage='restore',
        )
        self._last_restore_mode = self._last_call_mode
        return result

    def convert_enhance(self, restore_markdown, pdf_metadata):
        """
        第二步：智能增强

        基于忠实还原版，有据可依的补充和扩展。
        """
        prompt = self._build_enhance_prompt(restore_markdown, pdf_metadata)
        model_output = self._call_model(prompt)
        if model_output:
            output = self._ensure_frontmatter_and_title(model_output, pdf_metadata)
            if self._should_mark_low_quality():
                output = self._apply_low_quality_marker(output, stage='enhance')
            self._last_enhance_mode = self._last_call_mode
            return output

        result = self._apply_low_quality_marker(
            self._fallback_enhance(restore_markdown),
            stage='enhance',
        )
        self._last_enhance_mode = self._last_call_mode
        return result

    def convert_full(self, pdf_content, pdf_metadata):
        """完整转换（两步合并）"""
        restore_markdown = self.convert_restore(pdf_content, pdf_metadata)
        enhance_markdown = self.convert_enhance(restore_markdown, pdf_metadata)
        return restore_markdown, enhance_markdown

    def _call_model(self, prompt):
        """调用模型，失败时返回 None 并走本地回退。"""
        if self._is_offline_mode():
            self._warn('离线模式已启用，跳过外部模型调用。')
            self._last_call_mode = 'offline'
            return None

        try:
            adapter = self._get_adapter()
            max_retries = self._get_config('api.max_retries', 3)
            output = adapter.call(prompt, max_retries=max_retries)
            self._last_call_mode = 'mock' if self._is_mock_mode() else 'model'
            return output
        except Exception as exc:
            self._warn(f"模型调用不可用，已切换本地回退模式: {exc}")
            self._last_call_mode = 'fallback'
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

    def _is_mock_mode(self):
        provider = str(self._get_config('api.provider', '')).strip().lower()
        if provider == 'mock':
            return True

        flag = self._get_config('api.mock_mode', False)
        if isinstance(flag, str):
            flag = flag.strip().lower() in {'1', 'true', 'yes', 'on'}
        return bool(flag)

    def _should_mark_low_quality(self):
        mark_enabled = self._get_config('quality.mark_low_quality_outputs', True)
        if isinstance(mark_enabled, str):
            mark_enabled = mark_enabled.strip().lower() in {'1', 'true', 'yes', 'on'}
        if not mark_enabled:
            return False
        return self._last_call_mode in {'offline', 'fallback', 'mock'}

    def _apply_low_quality_marker(self, markdown, stage):
        marker_header = '<!-- DRAFT/LOW_QUALITY -->'
        if marker_header in markdown:
            return markdown

        mode = self._last_call_mode
        note = (
            f"> **DRAFT/LOW_QUALITY**：当前为流程验证输出（stage={stage}, mode={mode}），"
            "不可作为最终交付版本。\n"
        )
        marker_block = f"{marker_header}\n{note}\n"

        stripped = markdown.strip()
        if stripped.startswith('---'):
            parts = stripped.split('\n')
            fence_count = 0
            end_idx = None
            for idx, line in enumerate(parts):
                if line.strip() == '---':
                    fence_count += 1
                    if fence_count == 2:
                        end_idx = idx
                        break
            if end_idx is not None:
                head = '\n'.join(parts[: end_idx + 1]).strip()
                tail = '\n'.join(parts[end_idx + 1 :]).strip()
                if tail:
                    return f"{head}\n\n{marker_block}{tail}\n"
                return f"{head}\n\n{marker_block}"

        return f"{marker_block}{stripped}\n"

    def _warn(self, message):
        if self.logger and hasattr(self.logger, 'warning'):
            self.logger.warning(message)
            return
        print(f"[WARNING] {message}")

    def get_last_modes(self):
        """返回最近一次转换步骤的运行模式。"""
        return {
            'restore': self._last_restore_mode,
            'enhance': self._last_enhance_mode,
        }
