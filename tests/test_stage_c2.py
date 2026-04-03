"""
阶段C2验收测试：图片语义插入

测试内容：
1. ImageProcessor 三种模式（disabled / description-only / extract）
2. 语义位置判断（锚文本匹配）
3. 集成测试 - 使用02号PDF + 离线回退模式
"""

import sys
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from image_handler import ImageHandler, ImageProcessor

PDF_02_WIN = Path(
    r"D:\usr\百信公司项目\pdf_to_kbase\TaiShan-200服务器资料\04快速安装指南"
    r"\TaiShan 200 服务器 快速安装指南 (型号2280) 10.pdf"
)
PDF_02_WSL = Path(
    "/mnt/d/usr/百信公司项目/pdf_to_kbase/TaiShan-200服务器资料/04快速安装指南"
    "/TaiShan 200 服务器 快速安装指南 (型号2280) 10.pdf"
)
PDF_02 = PDF_02_WIN if PDF_02_WIN.exists() else PDF_02_WSL
SKIP_REAL = not PDF_02.exists()


# ─────────────────────────────────────────────
# 单元测试：_find_anchor_position
# ─────────────────────────────────────────────

class TestAnchorPosition(unittest.TestCase):
    """测试锚文本位置查找（staticmethod，不需要真实PDF）"""

    def _pos(self, lines, anchor):
        return ImageProcessor._find_anchor_position(lines, anchor)

    def test_finds_matching_line(self):
        # 锚文本前10字符"安装说明如下，请按照"应能匹配行"安装说明如下，请按照以下步骤操作"
        lines = ["第一段文字", "安装说明如下，请按照以下步骤操作", "步骤三"]
        self.assertEqual(self._pos(lines, "安装说明如下，请按照以下步骤"), 1)

    def test_no_match_returns_last_line(self):
        lines = ["aaa", "bbb", "ccc"]
        self.assertEqual(self._pos(lines, "完全不存在的文字xyz"), 2)

    def test_empty_anchor_returns_last_line(self):
        lines = ["a", "b"]
        self.assertEqual(self._pos(lines, ""), 1)

    def test_none_anchor_returns_last_line(self):
        lines = ["a", "b"]
        self.assertEqual(self._pos(lines, None), 1)

    def test_case_insensitive_match(self):
        lines = ["Server Installation Guide", "step two"]
        self.assertEqual(self._pos(lines, "server installation"), 0)


# ─────────────────────────────────────────────
# 单元测试：disabled 模式
# ─────────────────────────────────────────────

@unittest.skipIf(SKIP_REAL, f"跳过：02号PDF不存在")
class TestDisabledMode(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.proc = ImageProcessor(PDF_02, self.tmp, '02')

    def tearDown(self):
        self.proc.close()

    def test_disabled_returns_unchanged_markdown(self):
        original = "# 标题\n\n正文内容\n"
        result = self.proc.process(original, image_mode='disabled')
        self.assertEqual(result, original)

    def test_disabled_no_files_created(self):
        self.proc.process("# 内容", image_mode='disabled')
        png_files = list(Path(self.tmp).glob('*.png'))
        self.assertEqual(len(png_files), 0)


# ─────────────────────────────────────────────
# 集成测试：extract 模式
# ─────────────────────────────────────────────

@unittest.skipIf(SKIP_REAL, f"跳过：02号PDF不存在")
class TestExtractMode(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.proc = ImageProcessor(PDF_02, self.tmp, '02')
        self.sample_md = (
            "# TaiShan 200 快速安装指南\n\n"
            "## 1. 产品简介\n\n"
            "TaiShan 200 服务器是华为推出的高性能服务器。\n\n"
            "## 2. 安装步骤\n\n"
            "按照以下步骤安装服务器。\n"
        )

    def tearDown(self):
        self.proc.close()

    def test_extract_creates_image_files(self):
        result = self.proc.process(self.sample_md, image_mode='extract', min_width=100)
        png_files = list(Path(self.tmp).glob('*.png'))
        self.assertGreater(len(png_files), 0)
        print(f"\n  保存图片：{len(png_files)} 张")

    def test_extract_inserts_references_in_markdown(self):
        result = self.proc.process(self.sample_md, image_mode='extract', min_width=100)
        self.assertIn('![', result)
        self.assertIn('](images/', result)
        count = result.count('![')
        print(f"\n  插入图片引用：{count} 处")

    def test_extract_image_files_naming_convention(self):
        self.proc.process(self.sample_md, image_mode='extract', min_width=100)
        png_files = list(Path(self.tmp).glob('*.png'))
        for f in png_files:
            # 命名格式：02_NN_image.png
            parts = f.stem.split('_')
            self.assertEqual(parts[0], '02')
            self.assertTrue(parts[1].isdigit())


# ─────────────────────────────────────────────
# 集成测试：description-only 模式
# ─────────────────────────────────────────────

@unittest.skipIf(SKIP_REAL, f"跳过：02号PDF不存在")
class TestDescriptionOnlyMode(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.proc = ImageProcessor(PDF_02, self.tmp, '02')
        self.sample_md = "# 文档\n\n内容文字。\n"

    def tearDown(self):
        self.proc.close()

    def test_description_only_no_image_files(self):
        self.proc.process(self.sample_md, image_mode='description-only', min_width=100)
        png_files = list(Path(self.tmp).glob('*.png'))
        self.assertEqual(len(png_files), 0)

    def test_description_only_inserts_text(self):
        result = self.proc.process(self.sample_md, image_mode='description-only', min_width=100)
        self.assertIn('图片说明', result)
        count = result.count('图片说明')
        print(f"\n  插入图片说明：{count} 处")


# ─────────────────────────────────────────────
# 集成测试：锚文本定位
# ─────────────────────────────────────────────

@unittest.skipIf(SKIP_REAL, f"跳过：02号PDF不存在")
class TestAnchorTextIntegration(unittest.TestCase):

    def setUp(self):
        self.proc = ImageProcessor(PDF_02, tempfile.mkdtemp(), '02')

    def tearDown(self):
        self.proc.close()

    def test_get_image_text_anchors_returns_list(self):
        anchors = self.proc.vision.get_image_text_anchors()
        self.assertIsInstance(anchors, list)
        print(f"\n  锚文本记录：{len(anchors)} 条")

    def test_anchors_have_required_fields(self):
        anchors = self.proc.vision.get_image_text_anchors()
        for a in anchors[:5]:
            self.assertIn('page_num', a)
            self.assertIn('xref', a)
            self.assertIn('anchor_text', a)

    def test_some_anchors_have_text(self):
        anchors = self.proc.vision.get_image_text_anchors()
        non_none = [a for a in anchors if a['anchor_text']]
        print(f"\n  有锚文本的图片：{len(non_none)}/{len(anchors)}")
        # 至少应有一些图片能找到上方文字
        if anchors:
            self.assertGreater(len(non_none), 0)


# ─────────────────────────────────────────────
# 集成测试：Step0-3 瓶颈3验证
# ─────────────────────────────────────────────

@unittest.skipIf(SKIP_REAL, f"跳过：02号PDF不存在")
class TestStep03Bottleneck3(unittest.TestCase):
    """
    Step0-3 瓶颈3验证：图片语义位置插入（已降级为工程问题）
    验证结论：工程实现（提取→命名→保存→插入）链路可跑通
    """

    def test_full_pipeline_runnable(self):
        """完整流水线可跑通（extract模式）"""
        tmp = tempfile.mkdtemp()
        md = (
            "# TaiShan 200 快速安装指南\n\n"
            "## 安装准备\n\n"
            "安装前请确认包装内容。\n\n"
            "## 安装步骤\n\n"
            "将服务器固定到机架。\n"
        )

        with ImageProcessor(PDF_02, tmp, '02') as proc:
            result = proc.process(md, image_mode='extract', min_width=100)

        # 工程链路验证
        img_dir = Path(tmp)
        saved_images = list(img_dir.glob('*.png'))

        print(f"\n  [Step0-3] 提取图片: {len(saved_images)} 张")
        print(f"  [Step0-3] Markdown引用数: {result.count('![')}")

        self.assertGreater(len(saved_images), 0, "应有图片被提取并保存")
        self.assertIn('![', result, "Markdown中应有图片引用")

        # 所有引用应指向 images/ 目录
        for ref in [r for r in result.split('\n') if '![' in r]:
            self.assertIn('images/', ref)

        print(f"  [Step0-3] 结论：工程链路可跑通 ✅")


if __name__ == '__main__':
    unittest.main(verbosity=2)
