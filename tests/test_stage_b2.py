#!/usr/bin/env python3
"""
阶段B2验收测试脚本

测试内容：
1. 两步转换流水线（含无 Key 本地回退）
2. Markdown 验证模块
3. 输出命名辅助函数
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from config import ConfigManager
from converter import Converter
from pdfsc import build_output_basename
from validator import MarkdownValidator


def build_config():
    config = ConfigManager()
    config.load_default()
    config.set('api.provider', 'anthropic')
    config.set('api.model', 'claude-sonnet-4-5')
    config.set('api.offline_mode', True)
    config.set('conversion.mode', 'full')
    config.set('conversion.save_intermediate', True)
    return config


def make_sample_data():
    pdf_content = {
        'text': {
            'full_text': (
                'TaiShan 200 服务器安装步骤。\n'
                '步骤1：连接电源线。\n'
                '步骤2：检查指示灯状态。'
            )
        }
    }

    metadata = {
        'title': 'TaiShan 200 服务器 快速安装指南（型号2280）',
        'source_pdf': 'TaiShan 200 服务器 快速安装指南 (型号2280) 10.pdf',
        'frontmatter': (
            '---\n'
            'title: TaiShan 200 服务器 快速安装指南（型号2280）\n'
            'category: 安装配置\n'
            'type: 快速指南\n'
            'model: TaiShan 200 型号2280\n'
            'version: "10"\n'
            'date: 2026-03-14\n'
            'keywords:\n'
            '  - 安装\n'
            '  - 快速开始\n'
            'source_pdf: TaiShan 200 服务器 快速安装指南 (型号2280) 10.pdf\n'
            '---'
        ),
    }
    return pdf_content, metadata


def test_converter_restore_and_full():
    print('=' * 60)
    print('测试1：两步转换流水线（本地回退）')
    print('=' * 60)

    config = build_config()
    converter = Converter(config)
    pdf_content, metadata = make_sample_data()

    restore = converter.convert_restore(pdf_content, metadata)
    enhance = converter.convert_enhance(restore, metadata)
    full_restore, full_enhance = converter.convert_full(pdf_content, metadata)

    assert restore.startswith('---\n')
    assert '# TaiShan 200 服务器 快速安装指南（型号2280）' in restore
    assert '## 原文内容' in restore
    assert isinstance(enhance, str) and len(enhance) > 0
    assert full_restore.startswith('---\n')
    assert full_enhance.startswith('---\n')

    print('✅ restore/enhance/full 输出结构正确')


def test_validator():
    print('\n' + '=' * 60)
    print('测试2：Markdown 验证模块')
    print('=' * 60)

    validator = MarkdownValidator()
    _, metadata = make_sample_data()

    valid_md = (
        metadata['frontmatter']
        + '\n\n'
        + '# 标题\n\n'
        + '## 文档信息\n\n'
        + '- 来源文件：demo.pdf\n\n'
        + '现象：电源灯不亮\n'
        + '可能原因：电源线未连接。\n'
    )

    invalid_md = (
        metadata['frontmatter']
        + '\n\n'
        + '# 标题\n\n'
        + '| 列1 | 列2 |\n'
        + '| --- | --- |\n'
        + '| A | B |\n'
    )

    valid_result = validator.validate(valid_md)
    invalid_result = validator.validate(invalid_md)

    assert valid_result['valid'] is True
    assert invalid_result['valid'] is False
    assert any('传统 Markdown 表格' in err for err in invalid_result['errors'])

    report_text = validator.generate_report(invalid_result)
    assert 'Markdown验证报告' in report_text

    print('✅ 验证模块可识别规范与违规内容')


def test_output_naming():
    print('\n' + '=' * 60)
    print('测试3：输出命名')
    print('=' * 60)

    config = build_config()
    basename = build_output_basename('TaiShan 200 快速安装指南 (型号2280)', 3, config)

    assert basename.startswith('03_')
    assert 'TaiShan_200_快速安装指南_(型号2280)' in basename

    print(f'✅ 生成文件基名: {basename}')


def main():
    tests = [
        ('两步转换流水线', test_converter_restore_and_full),
        ('验证模块', test_validator),
        ('输出命名', test_output_naming),
    ]

    results = []
    for name, func in tests:
        try:
            func()
            results.append((name, True))
        except Exception as exc:
            print(f'❌ {name} 测试失败: {exc}')
            results.append((name, False))

    print('\n' + '=' * 60)
    print('测试汇总')
    print('=' * 60)
    for name, passed in results:
        print(f"{name:20s}: {'✅ 通过' if passed else '❌ 失败'}")

    all_passed = all(passed for _, passed in results)
    print('\n' + '=' * 60)
    if all_passed:
        print('🎉 所有测试通过！阶段B2核心能力可用！')
    else:
        print('⚠️ 部分测试失败，需要修复')
    print('=' * 60)
    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())