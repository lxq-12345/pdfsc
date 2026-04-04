"""
阶段D1验收测试：批量处理与质量检测

测试内容：
1. HallucinationDetector - 数字幻觉检测逻辑
2. MarkdownValidator - 格式验证（已有实现，回归测试）
3. 批量转换流程 - 离线模式下三个PDF批量处理
4. 报告生成 - quality_report 和 batch_summary
"""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from validator import HallucinationDetector, MarkdownValidator

# 三个测试PDF路径
def _pdf(subfolder, filename):
    base = Path(r"D:\usr\百信公司项目\pdf_to_kbase\TaiShan-200服务器资料")
    wsl = Path("/mnt/d/usr/百信公司项目/pdf_to_kbase/TaiShan-200服务器资料")
    root = base if base.exists() else wsl
    return root / subfolder / filename

PDF_01 = _pdf("01产品概述", "产品概述01华为TaiShan服务器彩页01.pdf")
PDF_02 = _pdf("04快速安装指南", "TaiShan 200 服务器 快速安装指南 (型号2280) 10.pdf")
PDF_03 = None  # 在 setUp 中动态查找

SKIP_REAL = not PDF_02.exists()


def _python_executable():
    """返回当前测试环境可复用的 Python 解释器。"""
    current = Path(sys.executable) if sys.executable else None
    if current and current.exists():
        return str(current)

    return 'python.exe' if sys.platform.startswith('win') else 'python3'


# ─────────────────────────────────────────────
# 单元测试：HallucinationDetector
# ─────────────────────────────────────────────

class TestHallucinationDetector(unittest.TestCase):

    def setUp(self):
        self.det = HallucinationDetector()

    def test_detects_new_numbers_in_final(self):
        raw = "服务器支持 256GB 内存，处理器主频 2.6GHz。"
        final = "服务器支持 256GB 内存，处理器主频 2.6GHz，最大支持 512GB。"
        result = self.det.detect(raw, final)
        # 正则提取纯数字，512GB → '512'
        self.assertIn('512', result['new_in_final'])

    def test_no_hallucination_when_identical(self):
        text = "产品型号 2280，支持 16 个 DDR4 内存插槽，最大 3200MHz。"
        result = self.det.detect(text, text)
        self.assertEqual(result['hallucination_count'], 0)
        self.assertEqual(result['risk_level'], 'low')

    def test_detects_lost_numbers(self):
        raw = "额定功率 800W，峰值功率 1000W。"
        final = "额定功率 800W。"
        result = self.det.detect(raw, final)
        self.assertIn('1000', result['lost_in_final'])

    def test_risk_level_high(self):
        raw = "参数 A。"
        final = "参数 A，数值 100、200、300、400、500、600。"
        result = self.det.detect(raw, final)
        self.assertEqual(result['risk_level'], 'high')

    def test_risk_level_medium(self):
        raw = "版本 1.0。"
        final = "版本 1.0，支持 32GB 和 64GB。"
        result = self.det.detect(raw, final)
        self.assertEqual(result['risk_level'], 'medium')

    def test_risk_level_low(self):
        raw = "版本 1.0，支持 32GB。"
        final = "版本 1.0，支持 32GB。"
        result = self.det.detect(raw, final)
        self.assertEqual(result['risk_level'], 'low')

    def test_extract_numbers(self):
        text = "支持 256GB 内存，3.2GHz，100% 兼容，共 42U。"
        nums = self.det.extract_numbers(text)
        self.assertIn('256', nums)
        self.assertIn('3.2', nums)
        self.assertIn('42', nums)
        self.assertIn('100', nums)

    def test_generate_report_contains_risk(self):
        result = {'new_in_final': ['512', '1024'], 'lost_in_final': [],
                  'hallucination_count': 2, 'risk_level': 'medium'}
        report = self.det.generate_report(result, pdf_name='test.pdf')
        self.assertIn('MEDIUM', report)
        self.assertIn('512', report)


# ─────────────────────────────────────────────
# 单元测试：MarkdownValidator（回归）
# ─────────────────────────────────────────────

class TestMarkdownValidatorRegression(unittest.TestCase):

    def setUp(self):
        self.v = MarkdownValidator()

    def _good_md(self):
        return (
            "---\n"
            "title: 测试文档\ncategory: hardware\ntype: guide\n"
            "model: claude\nversion: '1.0'\ndate: '2026-04-04'\n"
            "keywords: [服务器, 安装]\nsource_pdf: test.pdf\n"
            "---\n\n"
            "# 测试文档\n\n## 简介\n\n产品型号：TaiShan 200。\n产品类型：服务器。\n"
        )

    def test_valid_document_passes(self):
        result = self.v.validate(self._good_md())
        self.assertTrue(result['valid'])
        self.assertEqual(len(result['errors']), 0)

    def test_missing_frontmatter_fails(self):
        result = self.v.validate("# 标题\n\n内容。\n")
        self.assertFalse(result['valid'])

    def test_missing_required_field_fails(self):
        md = self._good_md().replace("title: 测试文档\n", "")
        result = self.v.validate(md)
        self.assertFalse(result['valid'])

    def test_table_detected_as_error(self):
        md = self._good_md() + "\n| 列1 | 列2 |\n|-----|-----|\n| a | b |\n"
        result = self.v.validate(md)
        self.assertFalse(result['valid'])

    def test_score_decreases_with_errors(self):
        good = self.v.validate(self._good_md())
        bad = self.v.validate("# 无frontmatter文档\n\n内容。\n")
        self.assertGreater(good['score'], bad['score'])


# ─────────────────────────────────────────────
# 集成测试：批量转换（离线模式）
# ─────────────────────────────────────────────

@unittest.skipIf(SKIP_REAL, "跳过：测试PDF不存在")
class TestBatchConversionOffline(unittest.TestCase):
    """使用离线模式测试批量转换流程（不需要API Key）"""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        # 动态查找03号PDF
        pdf03_dir = PDF_02.parent.parent / "10用户指南"
        pdfs = list(pdf03_dir.glob("*.pdf")) if pdf03_dir.exists() else []
        self.pdf_03 = pdfs[0] if pdfs else None

    def _run_convert(self, pdf_path):
        """在独立进程中以离线模式转换单个PDF"""
        import subprocess
        worktree = Path(__file__).parent.parent
        cmd = [
            _python_executable(), str(worktree / 'src' / 'pdfsc.py'),
            'convert', str(pdf_path),
            '--output', str(self.tmp),
            '--offline',
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return result

    def test_single_pdf_convert_offline(self):
        """单个PDF离线转换无报错"""
        result = self._run_convert(PDF_02)
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        md_files = list((self.tmp / 'markdown').rglob('*.md'))
        self.assertGreater(len(md_files), 0)
        print(f"\n  离线转换输出：{[f.name for f in md_files]}")

    def test_output_reports_generated(self):
        """转换后生成质量报告"""
        self._run_convert(PDF_02)
        reports = list((self.tmp / 'reports').glob('*.md'))
        self.assertGreater(len(reports), 0)
        print(f"\n  生成报告：{[r.name for r in reports]}")

    def test_quality_report_contains_sections(self):
        """质量报告包含验证和幻觉检测两个章节"""
        self._run_convert(PDF_02)
        reports = list((self.tmp / 'reports').glob('*quality_report*.md'))
        if reports:
            content = reports[0].read_text(encoding='utf-8')
            self.assertIn('Markdown验证报告', content)
            self.assertIn('数字幻觉检测', content)

    def test_batch_summary_uses_semantic_format(self):
        """批量汇总报告不应使用传统Markdown表格"""
        import subprocess
        worktree = Path(__file__).parent.parent
        pdf_dir = PDF_02.parent
        cmd = [
            _python_executable(), str(worktree / 'src' / 'pdfsc.py'),
            'convert-batch', str(pdf_dir),
            '--output', str(self.tmp),
            '--offline',
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        self.assertEqual(result.returncode, 0, msg=result.stderr)

        summaries = list((self.tmp / 'reports').glob('batch_summary_*.md'))
        self.assertGreater(len(summaries), 0)
        content = summaries[0].read_text(encoding='utf-8')
        self.assertIn('## 各文件结果', content)
        self.assertIn('文档类型：', content)
        self.assertNotIn('| 文件 | 类型 | 格式评分 | 幻觉风险 | 报告 |', content)


# ─────────────────────────────────────────────
# 集成测试：数字幻觉检测实际样本
# ─────────────────────────────────────────────

class TestHallucinationWithRealSamples(unittest.TestCase):
    """用真实文档片段测试幻觉检测器"""

    def setUp(self):
        self.det = HallucinationDetector()

    def test_taishan_specs_no_hallucination(self):
        """相同内容不应触发幻觉"""
        raw = (
            "TaiShan 200（型号2280）服务器，支持2路华为鲲鹏920处理器，"
            "最大主频2.6GHz，支持16个DDR4内存插槽，最大内存容量4TB。"
        )
        result = self.det.detect(raw, raw)
        self.assertEqual(result['hallucination_count'], 0)

    def test_added_fake_spec_detected(self):
        """增强版添加了原文没有的规格参数，应被检测"""
        raw = "服务器支持2路处理器，最大内存容量为4TB。"
        # 100 和 200 均不在噪声过滤范围（1-19），应被检测为潜在幻觉
        final = "服务器支持2路处理器，最大内存容量为4TB，最大存储扩展到100TB，支持200个节点。"
        result = self.det.detect(raw, final)
        self.assertGreater(result['hallucination_count'], 0)
        # 正则提取纯数字，100TB → '100'
        self.assertIn('100', result['new_in_final'])


if __name__ == '__main__':
    unittest.main(verbosity=2)



