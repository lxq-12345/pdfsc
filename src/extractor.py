"""
Text Extraction Module using pdfplumber

从PDF提取结构化文本和表格
"""


class TextExtractor:
    """文本提取器"""

    def __init__(self, pdf_path):
        """初始化提取器"""
        self.pdf_path = pdf_path

    def extract_text(self):
        """
        提取所有文本

        Returns:
            dict: 按页面组织的文本内容
        """
        raise NotImplementedError()

    def extract_tables(self):
        """
        提取表格

        Returns:
            dict: 按页面和位置组织的表格数据
        """
        raise NotImplementedError()

    def extract_structure(self):
        """
        提取文档结构（标题、段落、列表等）

        Returns:
            dict: 结构化的文档内容
        """
        raise NotImplementedError()
