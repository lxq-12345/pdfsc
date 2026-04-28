"""
文字提取模块（基于pdfplumber）

功能：从PDF提取结构化文本和表格
作者：pdfsc项目
创建日期：2026-03-13
"""

import os
from typing import Dict, List

import pdfplumber


class TextExtractor:
    """文本提取器"""

    def __init__(self, pdf_path: str):
        """
        初始化提取器

        Args:
            pdf_path: PDF文件路径
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")

        self.pdf_path = pdf_path
        self._pdf = None

    def __enter__(self):
        """上下文管理器入口"""
        self._pdf = pdfplumber.open(self.pdf_path)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        if self._pdf:
            self._pdf.close()

    def extract_text(self) -> Dict[str, any]:
        """
        提取所有文本

        Returns:
            dict: 提取结果
            {
                'full_text': '完整文本',
                'pages': [
                    {'page_num': 1, 'text': '第1页文本'},
                    {'page_num': 2, 'text': '第2页文本'},
                   ...
                ],
                'metadata': {
                    'total_pages': 10,
                    'filename': 'example.pdf',
                    'total_chars': 5000
                }
            }
        """
        if not self._pdf:
            raise RuntimeError("必须在上下文管理器中使用: with TextExtractor(path) as extractor:")

        pages_data = []
        full_text_parts = []

        for page_num, page in enumerate(self._pdf.pages, start=1):
            text = self._extract_page_text(page)
            pages_data.append({
                'page_num': page_num,
                'text': text.strip()
            })
            full_text_parts.append(text.strip())

        full_text = "\n\n".join(full_text_parts)

        metadata = {
            'total_pages': len(self._pdf.pages),
            'filename': os.path.basename(self.pdf_path),
            'total_chars': len(full_text)
        }

        return {
            'full_text': full_text,
            'pages': pages_data,
            'metadata': metadata
        }

    def extract_tables(self) -> Dict[str, List]:
        """
        提取表格

        Returns:
            dict: 按页面组织的表格数据
            {
                'tables': [
                    {
                        'page_num': 1,
                        'table_index': 0,
                        'data': [[...], [...]],  # 表格数据（二维数组）
                        'rows': 5,
                        'cols': 3
                    },
                    ...
                ],
                'metadata': {
                    'total_tables': 10
                }
            }
        """
        if not self._pdf:
            raise RuntimeError("必须在上下文管理器中使用: with TextExtractor(path) as extractor:")

        all_tables = []

        for page_num, page in enumerate(self._pdf.pages, start=1):
            tables = page.extract_tables()
            if tables:
                for table_index, table_data in enumerate(tables):
                    if table_data:  # 确保表格不为空
                        all_tables.append({
                            'page_num': page_num,
                            'table_index': table_index,
                            'data': table_data,
                            'rows': len(table_data),
                            'cols': len(table_data[0]) if table_data else 0
                        })

        metadata = {
            'total_tables': len(all_tables)
        }

        return {
            'tables': all_tables,
            'metadata': metadata
        }

    def extract_structure(self) -> Dict:
        """
        提取文档结构（简化版，仅提取基本信息）

        Returns:
            dict: 结构化的文档内容
            {
                'text': {...},      # extract_text()的结果
                'tables': {...},    # extract_tables()的结果
                'has_tables': bool
            }
        """
        text_result = self.extract_text()
        tables_result = self.extract_tables()

        return {
            'text': text_result,
            'tables': tables_result,
            'has_tables': tables_result['metadata']['total_tables'] > 0
        }

    @staticmethod
    def _extract_page_text(page) -> str:
        """
        提取单页文本。

        优先尝试按“词 -> 行 -> 列”的顺序重建阅读顺序，降低多栏页面被
        直接线性串接的概率；若判断不出稳定分栏，则回退到 pdfplumber 默认
        的 extract_text()。
        """
        words = page.extract_words(
            use_text_flow=False,
            keep_blank_chars=False,
            x_tolerance=2,
            y_tolerance=3,
        )

        text = TextExtractor._extract_layout_text(words, page.width)
        if text:
            return text

        return (page.extract_text() or "").strip()

    @staticmethod
    def _extract_layout_text(words: List[Dict], page_width: float) -> str:
        """根据词块位置重建更接近版面的阅读顺序。"""
        if not words:
            return ""

        lines = TextExtractor._build_lines(words, page_width)
        if not lines:
            return ""

        columns = TextExtractor._cluster_columns(lines, page_width)
        if len(columns) < 2:
            return "\n".join(
                line['text'] for line in sorted(lines, key=lambda x: (x['top'], x['x0']))
            ).strip()

        ordered_lines = []
        for column in columns:
            ordered_lines.extend(sorted(column, key=lambda x: (x['top'], x['x0'])))

        return "\n".join(line['text'] for line in ordered_lines).strip()

    @staticmethod
    def _build_lines(words: List[Dict], page_width: float) -> List[Dict]:
        """按 top 与水平间隔将词块合并为近似文本行。"""
        if not words:
            return []

        sorted_words = sorted(words, key=lambda x: (round(x['top'], 1), x['x0']))
        lines = []
        current = []
        line_top = None
        last_x1 = None
        y_tolerance = 4
        column_gap_threshold = page_width * 0.08

        def flush_line():
            if not current:
                return
            ordered = sorted(current, key=lambda x: x['x0'])
            text = " ".join(word['text'] for word in ordered).strip()
            if not text:
                return
            lines.append({
                'text': text,
                'top': min(word['top'] for word in ordered),
                'x0': min(word['x0'] for word in ordered),
                'x1': max(word['x1'] for word in ordered),
            })

        for word in sorted_words:
            word_top = word['top']
            word_x0 = word['x0']
            if not current:
                current = [word]
                line_top = word_top
                last_x1 = word['x1']
                continue

            same_row = abs(word_top - line_top) <= y_tolerance
            close_enough = (word_x0 - last_x1) <= column_gap_threshold
            if same_row and close_enough:
                current.append(word)
                last_x1 = max(last_x1, word['x1'])
                continue

            flush_line()
            current = [word]
            line_top = word_top
            last_x1 = word['x1']

        flush_line()
        return lines

    @staticmethod
    def _cluster_columns(lines: List[Dict], page_width: float) -> List[List[Dict]]:
        """按 x0 聚类为列，适配双栏/三栏页面。"""
        if not lines:
            return []

        sorted_lines = sorted(lines, key=lambda x: x['x0'])
        clusters: List[List[Dict]] = [[sorted_lines[0]]]
        split_threshold = page_width * 0.12

        def cluster_center(cluster):
            return sum(item['x0'] for item in cluster) / len(cluster)

        for line in sorted_lines[1:]:
            prev_center = cluster_center(clusters[-1])
            if abs(line['x0'] - prev_center) > split_threshold:
                clusters.append([line])
            else:
                clusters[-1].append(line)

        meaningful = [cluster for cluster in clusters if len(cluster) >= 3]
        if len(meaningful) < 2:
            return [sorted(lines, key=lambda x: (x['top'], x['x0']))]

        return sorted(meaningful, key=cluster_center)


def extract_pdf_text(pdf_path: str) -> str:
    """
    便捷函数：提取PDF全文本

    Args:
        pdf_path: PDF文件路径

    Returns:
        str: 提取的全文本

    示例:
        >>> text = extract_pdf_text("example.pdf")
        >>> print(text[:100])
    """
    with TextExtractor(pdf_path) as extractor:
        result = extractor.extract_text()
        return result['full_text']


def extract_pdf_by_pages(pdf_path: str) -> List[Dict]:
    """
    便捷函数：按页面提取文本

    Args:
        pdf_path: PDF文件路径

    Returns:
        List[Dict]: 每页的文本数据

    示例:
        >>> pages = extract_pdf_by_pages("example.pdf")
        >>> for page in pages:
        >>>     print(f"第{page['page_num']}页: {page['text'][:50]}")
    """
    with TextExtractor(pdf_path) as extractor:
        result = extractor.extract_text()
        return result['pages']


if __name__ == "__main__":
    # 测试代码（需要实际PDF文件）
    import sys

    if len(sys.argv) < 2:
        print("用法: python extractor.py <pdf文件路径>")
        print("示例: python extractor.py test.pdf")
        sys.exit(1)

    pdf_path = sys.argv[1]

    try:
        with TextExtractor(pdf_path) as extractor:
            # 提取文本
            text_result = extractor.extract_text()
            print(f"\n=== 文本提取结果 ===")
            print(f"文件: {text_result['metadata']['filename']}")
            print(f"总页数: {text_result['metadata']['total_pages']}")
            print(f"总字符数: {text_result['metadata']['total_chars']}")

            print(f"\n前100个字符:")
            print(text_result['full_text'][:100])

            # 提取表格
            tables_result = extractor.extract_tables()
            print(f"\n=== 表格提取结果 ===")
            print(f"表格数量: {tables_result['metadata']['total_tables']}")

            if tables_result['tables']:
                print(f"\n第一个表格:")
                first_table = tables_result['tables'][0]
                print(f"  页码: {first_table['page_num']}")
                print(f"  行数: {first_table['rows']}")
                print(f"  列数: {first_table['cols']}")
                print(f"  数据预览（前3行）:")
                for row in first_table['data'][:3]:
                    print(f"    {row}")

    except FileNotFoundError as e:
        print(f"错误: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)
