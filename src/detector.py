"""
PDF Type Detection Module

自动识别PDF类型：
- text_only: 纯文字型
- mixed: 图文混合型
- scanned: 扫描型
"""


class PDFDetector:
    """PDF类型检测器"""

    def __init__(self):
        """初始化检测器"""
        pass

    def detect_type(self, pdf_path):
        """
        检测PDF类型

        Args:
            pdf_path: PDF文件路径

        Returns:
            str: PDF类型 ('text_only' | 'mixed' | 'scanned')
        """
        raise NotImplementedError()

    def analyze(self, pdf_path):
        """
        分析PDF详细信息

        Returns:
            dict: 包含类型、页数、是否有文字、是否有图片等信息
        """
        raise NotImplementedError()
