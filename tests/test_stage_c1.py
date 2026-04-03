"""
阶段C1验收测试：图片提取

测试内容：
1. VisionProcessor - PDF图片提取、页面渲染、区域识别
2. ImageHandler - 图片保存、过滤、Markdown插入
3. 集成测试 - 使用02号PDF真实提取
"""

import sys
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from vision import VisionProcessor
from image_handler import ImageHandler

# 02号PDF路径（Windows / WSL 双路径兼容）
_PDF_02_WIN = Path(
    r"D:\usr\百信公司项目\pdf_to_kbase\TaiShan-200服务器资料\04快速安装指南"
    r"\TaiShan 200 服务器 快速安装指南 (型号2280) 10.pdf"
)
_PDF_02_WSL = Path(
    "/mnt/d/usr/百信公司项目/pdf_to_kbase/TaiShan-200服务器资料/04快速安装指南"
    "/TaiShan 200 服务器 快速安装指南 (型号2280) 10.pdf"
)
PDF_02 = _PDF_02_WIN if _PDF_02_WIN.exists() else _PDF_02_WSL
SKIP_REAL = not PDF_02.exists()


# ─────────────────────────────────────────────
# 单元测试：ImageHandler
# ─────────────────────────────────────────────

class TestImageHandlerFilter(unittest.TestCase):
    """图片过滤逻辑"""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.handler = ImageHandler(self.tmp)

    def test_filter_removes_small_images(self):
        images = [
            {'width': 50, 'name': 'icon'},
            {'width': 100, 'name': 'diagram'},
            {'width': 200, 'name': 'photo'},
        ]
        result = self.handler.filter_images(images, min_width=100)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['name'], 'diagram')

    def test_filter_default_threshold(self):
        images = [{'width': 99}, {'width': 100}, {'width': 101}]
        result = self.handler.filter_images(images)
        self.assertEqual(len(result), 2)

    def test_filter_empty_list(self):
        self.assertEqual(self.handler.filter_images([]), [])

    def test_filter_missing_width_field(self):
        images = [{'name': 'no_width'}, {'width': 200, 'name': 'ok'}]
        result = self.handler.filter_images(images)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['name'], 'ok')


class TestImageHandlerSave(unittest.TestCase):
    """图片保存和命名"""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.handler = ImageHandler(self.tmp)

    def test_save_creates_file(self):
        data = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100  # 伪造PNG头
        filename = self.handler.save_image(data, '02', '安装示意图', 1)
        self.assertTrue((Path(self.tmp) / filename).exists())

    def test_naming_convention(self):
        data = b'\x89PNG\r\n\x1a\n'
        filename = self.handler.save_image(data, '02', '服务器安装', 3)
        self.assertTrue(filename.startswith('02_03_'))
        self.assertTrue(filename.endswith('.png'))
        self.assertIn('服务器安装', filename)

    def test_special_chars_in_description(self):
        data = b'\x89PNG\r\n\x1a\n'
        filename = self.handler.save_image(data, '02', '图片/说明 (1)', 1)
        # 文件名不含 / 或空格
        self.assertNotIn('/', filename)
        self.assertNotIn(' ', filename)

    def test_description_length_limit(self):
        data = b'\x89PNG\r\n\x1a\n'
        long_desc = '这是一个非常非常非常非常非常非常非常非常非常非常长的描述文字'
        filename = self.handler.save_image(data, '02', long_desc, 1)
        self.assertLess(len(filename), 80)


class TestImageHandlerInsert(unittest.TestCase):
    """Markdown图片插入"""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.handler = ImageHandler(self.tmp)

    def test_insert_at_position(self):
        md = "第一段\n第二段\n第三段"
        result = self.handler.insert_image_reference(md, 1, 'img.png', '示意图')
        lines = result.split('\n')
        self.assertIn('![示意图](img.png)', lines)
        idx = lines.index('![示意图](img.png)')
        self.assertEqual(lines[idx - 1], '第二段')

    def test_insert_out_of_range_appends(self):
        md = "只有一行"
        result = self.handler.insert_image_reference(md, 999, 'img.png', '图')
        self.assertIn('![图](img.png)', result)

    def test_insert_at_position_zero(self):
        md = "第一行\n第二行"
        result = self.handler.insert_image_reference(md, 0, 'img.png', '图')
        lines = result.split('\n')
        self.assertEqual(lines[0], '第一行')
        self.assertEqual(lines[1], '![图](img.png)')


# ─────────────────────────────────────────────
# 集成测试：VisionProcessor（需要真实PDF）
# ─────────────────────────────────────────────

@unittest.skipIf(SKIP_REAL, f"跳过：02号PDF不存在 ({PDF_02})")
class TestVisionProcessorReal(unittest.TestCase):
    """使用02号PDF的真实测试"""

    def setUp(self):
        self.vp = VisionProcessor(PDF_02)

    def tearDown(self):
        self.vp.close()

    def test_identify_image_regions_returns_list(self):
        regions = self.vp.identify_image_regions()
        self.assertIsInstance(regions, list)
        print(f"\n  识别到图片区域：{len(regions)} 个")

    def test_each_region_has_required_fields(self):
        regions = self.vp.identify_image_regions()
        for r in regions[:5]:
            self.assertIn('page_num', r)
            self.assertIn('xref', r)
            self.assertIn('width', r)
            self.assertIn('height', r)

    def test_extract_images_returns_data(self):
        images = self.vp.extract_images(image_mode='extract')
        self.assertIsInstance(images, list)
        print(f"\n  提取图片：{len(images)} 张")

        if images:
            img = images[0]
            self.assertIn('image_bytes', img)
            self.assertIn('width', img)
            self.assertIn('height', img)
            self.assertIn('ext', img)
            self.assertGreater(len(img['image_bytes']), 0)

    def test_extract_images_disabled_returns_empty(self):
        images = self.vp.extract_images(image_mode='disabled')
        self.assertEqual(images, [])

    def test_render_pages_returns_list(self):
        pages = self.vp.render_pages(dpi=72)  # 低分辨率，测试快
        self.assertIsInstance(pages, list)
        self.assertGreater(len(pages), 0)
        print(f"\n  渲染页数：{len(pages)} 页")

        page = pages[0]
        self.assertIn('page_num', page)
        self.assertIn('image_bytes', page)
        self.assertIn('width', page)
        self.assertIn('height', page)
        self.assertGreater(len(page['image_bytes']), 0)

    def test_context_manager(self):
        with VisionProcessor(PDF_02) as vp:
            regions = vp.identify_image_regions()
        self.assertIsInstance(regions, list)

    def test_filter_integration(self):
        """提取后过滤小图"""
        tmp = tempfile.mkdtemp()
        handler = ImageHandler(tmp)

        images = self.vp.extract_images()
        filtered = handler.filter_images(images, min_width=100)

        print(f"\n  提取：{len(images)} 张，过滤后：{len(filtered)} 张")
        self.assertLessEqual(len(filtered), len(images))

    def test_save_extracted_images(self):
        """提取并保存图片到临时目录"""
        tmp = tempfile.mkdtemp()
        handler = ImageHandler(tmp)

        images = self.vp.extract_images()
        filtered = handler.filter_images(images, min_width=100)

        saved = []
        for i, img in enumerate(filtered[:5], start=1):  # 只保存前5张
            filename = handler.save_image(
                img['image_bytes'], '02', 'image', i
            )
            saved.append(filename)
            self.assertTrue((Path(tmp) / filename).exists())

        print(f"\n  已保存 {len(saved)} 张图片到临时目录")
        if saved:
            print(f"  示例：{saved[0]}")


if __name__ == '__main__':
    unittest.main(verbosity=2)
