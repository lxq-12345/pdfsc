"""
Image Handler Module

图片命名、保存和在Markdown中的位置插入
"""

import re
from pathlib import Path


class ImageHandler:
    """图片处理器"""

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
