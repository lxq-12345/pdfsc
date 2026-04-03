"""
PDF类型检测模块

功能：自动识别PDF文件的类型（纯文字型、图文混合型、扫描型）
作者：pdfsc项目
创建日期：2026-03-13
"""

import pdfplumber
import fitz  # PyMuPDF
from typing import Tuple, Dict


class PDFDetector:
    """PDF类型检测器"""

    def __init__(self, text_threshold: int = 100, image_threshold: int = 2):
        """
        初始化检测器

        Args:
            text_threshold: 文字数量阈值（少于此值视为扫描型）
            image_threshold: 图片数量阈值（多于此值视为包含图片）
        """
        self.text_threshold = text_threshold
        self.image_threshold = image_threshold

    def detect_type(self, pdf_path: str) -> str:
        """
        检测PDF类型

        Args:
            pdf_path: PDF文件路径

        Returns:
            str: PDF类型 ('text_only' | 'text_image' | 'scanned')
        """
        metadata = self._analyze_pdf(pdf_path)
        pdf_type_enum = self._classify(metadata)
        return pdf_type_enum

    def analyze(self, pdf_path: str) -> Dict:
        """
        分析PDF详细信息

        Args:
            pdf_path: PDF文件路径

        Returns:
            dict: 包含类型、页数、是否有文字、是否有图片等信息

        示例返回值:
        {
            'type': 'text_image',
            'total_pages': 10,
            'text_chars': 5000,
            'images_count': 5,
            'avg_text_per_page': 500.0,
            'has_text': True,
            'has_images': True
        }
        """
        metadata = self._analyze_pdf(pdf_path)
        pdf_type = self._classify(metadata)
        metadata['type'] = pdf_type
        return metadata

    def _analyze_pdf(self, pdf_path: str) -> Dict:
        """
        分析PDF内容

        Args:
            pdf_path: PDF文件路径

        Returns:
            分析元数据
        """
        # 使用pdfplumber提取文字统计
        text_chars = 0
        total_pages = 0

        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text_chars += len(text.strip())

        # 使用PyMuPDF提取图片统计
        images_count = 0

        doc = fitz.open(pdf_path)
        for page_num in range(len(doc)):
            page = doc[page_num]
            image_list = page.get_images(full=True)
            # 过滤小图片（宽度<100px的装饰性图标）
            for img in image_list:
                xref = img[0]
                base_image = doc.extract_image(xref)
                if base_image:
                    width = base_image.get("width", 0)
                    if width >= 100:  # 只统计有实质内容的图片
                        images_count += 1
        doc.close()

        # 计算元数据
        avg_text_per_page = text_chars / total_pages if total_pages > 0 else 0
        has_text = text_chars > self.text_threshold
        has_images = images_count >= self.image_threshold

        return {
            'total_pages': total_pages,
            'text_chars': text_chars,
            'images_count': images_count,
            'avg_text_per_page': avg_text_per_page,
            'has_text': has_text,
            'has_images': has_images
        }

    def _classify(self, metadata: Dict) -> str:
        """
        根据元数据分类PDF类型

        Args:
            metadata: 分析元数据

        Returns:
            PDF类型字符串
        """
        has_text = metadata['has_text']
        has_images = metadata['has_images']

        if not has_text and has_images:
            # 几乎没有文字，但有图片 → 扫描型
            return 'scanned'
        elif has_text and has_images:
            # 既有文字又有图片 → 图文混合型
            return 'text_image'
        elif has_text and not has_images:
            # 有文字，没有（或很少）图片 → 纯文字型
            return 'text_only'
        else:
            # 既没文字也没图片（罕见情况），默认为扫描型
            return 'scanned'


def detect_pdf_type(pdf_path: str, text_threshold: int = 100,
                   image_threshold: int = 2) -> Tuple[str, Dict]:
    """
    便捷函数：检测PDF类型

    Args:
        pdf_path: PDF文件路径
        text_threshold: 文字数量阈值
        image_threshold: 图片数量阈值

    Returns:
        (PDF类型, 检测元数据)

    示例:
        >>> pdf_type, metadata = detect_pdf_type("example.pdf")
        >>> print(f"PDF类型: {pdf_type}")
        >>> print(f"总页数: {metadata['total_pages']}")
        >>> print(f"文字字符数: {metadata['text_chars']}")
        >>> print(f"图片数量: {metadata['images_count']}")
    """
    detector = PDFDetector(text_threshold, image_threshold)
    metadata = detector.analyze(pdf_path)
    pdf_type = metadata['type']
    return pdf_type, metadata


if __name__ == "__main__":
    # 测试代码（需要实际PDF文件）
    import sys

    if len(sys.argv) < 2:
        print("用法: python detector.py <pdf文件路径>")
        print("示例: python detector.py test.pdf")
        sys.exit(1)

    pdf_path = sys.argv[1]

    try:
        pdf_type, metadata = detect_pdf_type(pdf_path)

        print(f"\n=== PDF类型检测结果 ===")
        print(f"文件: {pdf_path}")
        print(f"类型: {pdf_type}")
        print(f"\n元数据:")
        print(f"  总页数: {metadata['total_pages']}")
        print(f"  文字字符数: {metadata['text_chars']}")
        print(f"  每页平均文字数: {metadata['avg_text_per_page']:.1f}")
        print(f"  图片数量: {metadata['images_count']}")
        print(f"  包含文字: {'是' if metadata['has_text'] else '否'}")
        print(f"  包含图片: {'是' if metadata['has_images'] else '否'}")

    except FileNotFoundError:
        print(f"错误: 文件 '{pdf_path}' 不存在")
        sys.exit(1)
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)
