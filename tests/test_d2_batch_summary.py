#!/usr/bin/env python3
"""
D2 批量报告统计字段测试
"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from pdfsc import _write_batch_summary


def main():
    with tempfile.TemporaryDirectory() as tmp_dir:
        summary = Path(tmp_dir) / 'summary.md'
        results = [
            {
                'pdf': '/tmp/a.pdf',
                'type': 'text',
                'restore_mode': 'mock',
                'enhance_mode': 'mock',
                'low_quality': True,
                'validation_score': 8.5,
                'hallucination_risk': 'low',
                'report_path': '/tmp/a_report.md',
            },
            {
                'pdf': '/tmp/b.pdf',
                'type': 'mixed',
                'restore_mode': 'model',
                'enhance_mode': 'model',
                'low_quality': False,
                'validation_score': 9.2,
                'hallucination_risk': 'low',
                'report_path': '/tmp/b_report.md',
            },
        ]
        _write_batch_summary(summary, results, success_count=2, total_count=2)

        content = summary.read_text(encoding='utf-8')
        assert '低质量模式命中' in content
        assert 'Restore 模式分布' in content
        assert 'Enhance 模式分布' in content
        assert '运行模式：restore=mock / enhance=mock' in content
        assert '低质量模式命中：是' in content

    print('✅ D2 批量报告统计测试通过')
    return 0


if __name__ == '__main__':
    sys.exit(main())
