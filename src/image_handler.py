"""
Image Handler Module

图片命名、保存和在Markdown中的位置插入，以及三种图片模式的流水线。
"""

import re
import sys
from pathlib import Path


class ImageHandler:
    """图片处理器：命名、保存、过滤、Markdown插入"""

    def __init__(self, output_dir):
        """初始化图片处理器"""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def save_image(self, image_data, doc_index, content_description, sequence_num):
        """
        保存图片文件

        命名规范：{doc_index}_{sequence_num:02d}_{content_description}.png

        Args:
            image_data: 图片字节数据
            doc_index: 文档序号字符串（如"02"）
            content_description: 内容描述（如"服务器安装示意图"）
            sequence_num: 图片序号（int，从1开始）

        Returns:
            str: 保存的图片文件名（不含目录）
        """
        safe_desc = re.sub(r'[^\w\u4e00-\u9fff\-]', '_', content_description)
        safe_desc = safe_desc.strip('_')[:30]
        filename = f"{doc_index}_{sequence_num:02d}_{safe_desc}.png"

        filepath = self.output_dir / filename
        filepath.write_bytes(image_data)

        return filename

    def insert_image_reference(self, markdown_content, image_position, image_filename, alt_text):
        """
        在Markdown中插入图片引用

        Args:
            markdown_content: Markdown内容
            image_position: 插入位置（行号，0-indexed）
            image_filename: 图片文件名
            alt_text: Alt文本

        Returns:
            str: 插入图片引用后的Markdown
        """
        image_ref = f"![{alt_text}]({image_filename})"
        lines = markdown_content.split('\n')

        if isinstance(image_position, int) and 0 <= image_position < len(lines):
            lines.insert(image_position + 1, image_ref)
        else:
            lines.append(image_ref)

        return '\n'.join(lines)

    def filter_images(self, images, min_width=100):
        """
        过滤装饰性小图

        Args:
            images: 图片列表（每项需含 'width' 字段）
            min_width: 最小宽度像素（默认100）

        Returns:
            list: 过滤后的图片列表
        """
        return [img for img in images if img.get('width', 0) >= min_width]


class ImageProcessor:
    """
    图片处理流水线

    负责协调 VisionProcessor + ImageHandler，实现三种图片模式：
    - disabled:          忽略图片，Markdown不变
    - description-only:  插入图片文字说明（不保存图片文件）
    - extract:           提取图片文件 + 插入Markdown引用
    """

    def __init__(self, pdf_path, images_output_dir, doc_index, model_adapter=None):
        """
        Args:
            pdf_path: PDF文件路径
            images_output_dir: 图片输出目录
            doc_index: 文档序号字符串（如"02"）
            model_adapter: 可选，用于description-only模式的AI描述
        """
        # 延迟导入，避免循环依赖
        sys.path.insert(0, str(Path(__file__).parent))
        from vision import VisionProcessor
        self.vision = VisionProcessor(pdf_path)
        self.handler = ImageHandler(images_output_dir)
        self.doc_index = doc_index
        self.model_adapter = model_adapter

    def process(self, markdown_content, image_mode='extract', min_width=100):
        """
        处理图片，返回插入图片引用后的Markdown内容。

        Args:
            markdown_content: 原始Markdown文本
            image_mode: 'disabled' | 'description-only' | 'extract'
            min_width: 过滤小图的最小宽度

        Returns:
            str: 更新后的Markdown内容
        """
        if image_mode == 'disabled':
            return markdown_content

        images = self.vision.extract_images(image_mode)
        filtered = self.handler.filter_images(images, min_width)

        if not filtered:
            return markdown_content

        anchors = self.vision.get_image_text_anchors()
        anchor_map = {a['xref']: a.get('anchor_text') for a in anchors}

        lines = markdown_content.split('\n')

        # 收集所有插入操作，之后倒序执行避免行号偏移
        insertions = []  # (line_index, text)

        for seq, img in enumerate(filtered, start=1):
            anchor_text = anchor_map.get(img['xref'], '')
            position = self._find_anchor_position(lines, anchor_text)

            if image_mode == 'extract':
                filename = self.handler.save_image(
                    img['image_bytes'], self.doc_index, 'image', seq
                )
                ref = f"![图片{seq}](images/{filename})"

            else:  # description-only
                description = self._get_description(img, seq)
                ref = f"\n> **图片说明**（第{img['page_num'] + 1}页）：{description}\n"

            insertions.append((position, ref))

        # 倒序插入，保持行号稳定
        for position, ref in sorted(insertions, key=lambda x: x[0], reverse=True):
            lines.insert(position + 1, ref)

        return '\n'.join(lines)

    @staticmethod
    def _find_anchor_position(lines, anchor_text):
        """在Markdown行列表中查找锚文本所在行号，未找到则返回末行。"""
        if not anchor_text:
            return len(lines) - 1

        # 取锚文本前10个字符做模糊匹配（确保比单行短，提高命中率）
        key = re.sub(r'\s+', ' ', anchor_text[:10].strip().lower())
        if not key:
            return len(lines) - 1

        for i, line in enumerate(lines):
            if key in line.lower():
                return i

        return len(lines) - 1

    def _get_description(self, img, index):
        """生成图片描述（无AI时使用占位符）。"""
        if self.model_adapter:
            # 预留：未来接入AI视觉描述
            pass
        return f"第{img['page_num'] + 1}页第{index}张图片（{img['width']}×{img['height']} px）"

    def close(self):
        self.vision.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
