#!/usr/bin/env python3
"""
D2流程优先测试：mock adapter + 低质量标记
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from config import ConfigManager
from converter import Converter


def build_config():
    config = ConfigManager()
    config.load_default()
    config.set('api.provider', 'mock')
    config.set('api.model', 'mock-v1')
    config.set('api.offline_mode', False)
    config.set('api.mock_mode', True)
    config.set('quality.mark_low_quality_outputs', True)
    return config


def sample_data():
    pdf_content = {'text': {'full_text': '测试文档内容：步骤1，步骤2。'}}
    metadata = {
        'title': 'D2 流程联调样本',
        'source_pdf': 'd2_mock.pdf',
        'frontmatter': (
            '---\n'
            'title: D2 流程联调样本\n'
            'category: 测试\n'
            'type: 联调\n'
            'model: Mock\n'
            'version: "1"\n'
            'date: 2026-04-05\n'
            'keywords:\n'
            '  - mock\n'
            '  - d2\n'
            'source_pdf: d2_mock.pdf\n'
            '---'
        ),
    }
    return pdf_content, metadata


def main():
    config = build_config()
    converter = Converter(config)
    pdf_content, metadata = sample_data()

    raw_md, final_md = converter.convert_full(pdf_content, metadata)

    assert '<!-- DRAFT/LOW_QUALITY -->' in raw_md
    assert '<!-- DRAFT/LOW_QUALITY -->' in final_md
    assert '# D2 流程联调样本' in raw_md
    assert '# D2 流程联调样本' in final_md

    print('✅ D2 mock 流程测试通过')
    return 0


if __name__ == '__main__':
    sys.exit(main())
