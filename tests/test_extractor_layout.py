import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from extractor import TextExtractor


class TestExtractorLayout(unittest.TestCase):
    def test_extract_layout_text_prefers_column_order(self):
        words = [
            {'text': '左1', 'x0': 40, 'x1': 60, 'top': 100},
            {'text': '左2', 'x0': 40, 'x1': 60, 'top': 200},
            {'text': '左3', 'x0': 40, 'x1': 60, 'top': 300},
            {'text': '中1', 'x0': 420, 'x1': 440, 'top': 110},
            {'text': '中2', 'x0': 420, 'x1': 440, 'top': 210},
            {'text': '中3', 'x0': 420, 'x1': 440, 'top': 310},
            {'text': '右1', 'x0': 810, 'x1': 830, 'top': 120},
            {'text': '右2', 'x0': 810, 'x1': 830, 'top': 220},
            {'text': '右3', 'x0': 810, 'x1': 830, 'top': 320},
        ]

        text = TextExtractor._extract_layout_text(words, page_width=1200)
        self.assertEqual(
            text.splitlines(),
            ['左1', '左2', '左3', '中1', '中2', '中3', '右1', '右2', '右3'],
        )

    def test_extract_layout_text_falls_back_for_single_column(self):
        words = [
            {'text': '第一行', 'x0': 50, 'x1': 100, 'top': 100},
            {'text': '第二行', 'x0': 52, 'x1': 102, 'top': 140},
            {'text': '第三行', 'x0': 54, 'x1': 104, 'top': 180},
        ]

        text = TextExtractor._extract_layout_text(words, page_width=1200)
        self.assertEqual(text.splitlines(), ['第一行', '第二行', '第三行'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
