"""
Image Handler Module

图片命名、保存和在Markdown中的位置插入
"""


class ImageHandler:
    """图片处理器"""

    def __init__(self, output_dir):
        """初始化图片处理器"""
        self.output_dir = output_dir

    def save_image(self, image_data, doc_index, content_description, sequence_num):
        """
        保存图片文件

        Args:
            image_data: 图片数据
            doc_index: 文档序号（如"02"）
            content_description: 内容描述
            sequence_num: 序号

        Returns:
            str: 保存的图片文件名
        """
        raise NotImplementedError()

    def insert_image_reference(self, markdown_content, image_position, image_filename, alt_text):
        """
        在Markdown中插入图片引用

        Args:
            markdown_content: Markdown内容
            image_position: 图片在文档中的位置
            image_filename: 图片文件名
            alt_text: Alt文本

        Returns:
            str: 插入图片引用后的Markdown
        """
        raise NotImplementedError()

    def filter_images(self, images, min_width=100):
        """
        过滤图片（移除装饰性小图）

        Args:
            images: 图片列表
            min_width: 最小宽度像素

        Returns:
            list: 过滤后的图片列表
        """
        raise NotImplementedError()
