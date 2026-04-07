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
        body = self._structure_fallback_body(text)
        table_traces = self._extract_table_traces(pdf_content)

        chunks = []
        if frontmatter:
            chunks.append(frontmatter)
        chunks.append(f"# {title}")
        chunks.append("## 文档信息")
        chunks.append(f"- 来源文件：{source_pdf}")
        chunks.append("- 生成模式：本地回退（未调用外部模型）")
        chunks.append("## 原文内容")
        chunks.append(body if body else "（未提取到正文文本）")
        if table_traces:
            chunks.append("## 表格痕迹（回退保留）")
            chunks.append(self._render_table_traces(table_traces))
        return "\n\n".join(chunks).strip() + "\n"

    def _structure_fallback_body(self, text):
        """回退模式下增加基础结构，并过滤页眉页脚/目录噪声。"""
        if not text:
            return ""

        normalized = text.replace('\r\n', '\n').replace('\r', '\n')
        lines = [line.strip() for line in normalized.split('\n')]

        chunks = []
        pending_blank = False

        for line in lines:
            if not line:
                pending_blank = True
                continue

            if self._is_noise_line(line):
                continue

            section_match = re.fullmatch(r'(\d+)\s+(.+)', line)
            subsection_match = re.fullmatch(r'(\d+\.\d+)\s+(.+)', line)
            chapter_match = re.fullmatch(r'(第[一二三四五六七八九十百零\d]+[章节篇部].+)', line)

            heading = None
            if line.startswith('#'):
                heading = line
            elif subsection_match and self._is_probable_heading_text(subsection_match.group(2)):
                heading = f"### {subsection_match.group(1)} {subsection_match.group(2)}"
            elif section_match and int(section_match.group(1)) <= 9 and self._is_probable_heading_text(section_match.group(2)):
                heading = f"## {section_match.group(1)} {section_match.group(2)}"
            elif chapter_match:
                heading = f"## {chapter_match.group(1)}"

            if heading:
                if chunks and chunks[-1] != "":
                    chunks.append("")
                chunks.append(heading)
                chunks.append("")
                pending_blank = False
                continue

            if pending_blank and chunks and chunks[-1] != "":
                chunks.append("")
            chunks.append(line)
            pending_blank = False

        while chunks and not chunks[-1].strip():
            chunks.pop()

        return '\n'.join(chunks)

    def _is_noise_line(self, line):
        """过滤页眉页脚与目录噪声。"""
        s = line.strip()
        if not s:
            return True

        footer_patterns = [
            r'版权所有\s*©?\s*华为技术有限公司',
            r'^文档版本$',
            r'^文档版本\s+发布日期$',
            r'^目\s*录$',
            r'^TaiShan\s*200\s*服务器\s*\(型号\s*2280\)\s*$',
            r'^TaiShan\s*200\s*服务器\s*\(型号\s*2280\)\s*用户指南$',
            r'^用户指南$',
            r'^TaiShan\s*200\s*服务器.*用户指南$',
            r'^前言$',
            r'^发布日期$',
            r'^修改记录$',
            r'^修改说明$',
            r'^(概述|读者对象|符号约定)$',
            r'^(登录|通过)$',
            r'^初始配置（?iBMC.*$',
            r'^常用操作（?iBMC.*$',
            r'^华为技术有限公司$',
            r'^\d{4}-\d{2}-\d{2}$',
            r'^\d{1,2}$',
            r'^\s*[ivxlcdmIVXLCDM]+\s*$',
        ]
        for pattern in footer_patterns:
            if re.search(pattern, s):
                return True

        if re.search(r'[\.。·]{4,}\s*\d+\s*$', s):
            return True
        if re.search(r'^[^\s].{0,60}[\.。·]{8,}.+$', s):
            return True
        if re.search(r'^\d+\s*\(\d{4}-\d{2}-\d{2}\)\s*版权所有', s):
            return True

        return False

    def _is_probable_heading_text(self, text):
        """限制数字行误判为标题（如 7260 64 2.6 ...）。"""
        t = text.strip()
        if not t:
            return False

        if re.match(r'^\d', t):
            return False
        if len(re.findall(r'\d', t)) >= 5:
            return False
        if re.search(r'[\d]+\s+[\d]+', t):
            return False

        heading_keywords = ('简介', '准备', '安装', '上电', '下电', '附录', '规格', '组件', '故障', '安全', '维保', '操作', '资源', '环境', '目录')
        if any(k in t for k in heading_keywords):
            return True

        return len(t) <= 24 and bool(re.search(r'[\u4e00-\u9fff]', t))

    def _extract_table_traces(self, pdf_content):
        """从提取结构中读取表格痕迹。"""
        if not isinstance(pdf_content, dict):
            return []
        tables_node = pdf_content.get('tables')
        if not isinstance(tables_node, dict):
            return []
        tables = tables_node.get('tables', [])
        if not isinstance(tables, list):
            return []
        return tables

    def _render_table_traces(self, tables):
        """把表格痕迹渲染为 Markdown 文本。"""
        rendered = []
        for idx, table in enumerate(tables, start=1):
            if not isinstance(table, dict):
                continue
            page = table.get('page', '?')
            table_idx = table.get('table_index', '?')
            rendered.append(f"### 表格 {idx}（第{page}页，第{table_idx}表）")
            rows = table.get('rows', [])
            if not isinstance(rows, list) or not rows:
                rendered.append("- （未提取到行数据）")
                rendered.append("")
                continue

            preview_rows = rows[:8]
            for row_no, row in enumerate(preview_rows, start=1):
                if isinstance(row, list):
                    row_text = " | ".join(str(col).strip() for col in row if str(col).strip())
                else:
                    row_text = str(row).strip()
                if not row_text:
                    continue
                rendered.append(f"- 第{row_no}行：{row_text}")
            if len(rows) > len(preview_rows):
                rendered.append(f"- ... 其余 {len(rows) - len(preview_rows)} 行省略")
            rendered.append("")

        return "\n".join(rendered).strip()
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
