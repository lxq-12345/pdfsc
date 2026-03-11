"""
Two-Step Conversion Pipeline

实现忠实还原和智能增强的两步转换流水线
"""


class Converter:
    """两步转换流水线"""

    def __init__(self, config):
        """初始化转换器"""
        self.config = config

    def convert_restore(self, pdf_content, pdf_metadata):
        """
        第一步：忠实还原

        严格对应原文，不增加任何原文没有的内容

        Args:
            pdf_content: 提取的PDF内容
            pdf_metadata: 元数据（标题、分类等）

        Returns:
            str: 忠实还原版 Markdown
        """
        raise NotImplementedError()

    def convert_enhance(self, restore_markdown, pdf_metadata):
        """
        第二步：智能增强

        基于忠实还原版，有据可依的补充和扩展
        遵守防幻觉三等级约束

        Args:
            restore_markdown: 忠实还原版
            pdf_metadata: 元数据

        Returns:
            str: 智能增强版 Markdown
        """
        raise NotImplementedError()

    def convert_full(self, pdf_content, pdf_metadata):
        """
        完整转换（两步合并）

        Args:
            pdf_content: 提取的PDF内容
            pdf_metadata: 元数据

        Returns:
            tuple: (restore_markdown, enhance_markdown)
        """
        raise NotImplementedError()
