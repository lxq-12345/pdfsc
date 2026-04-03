"""
Output Validation Module

验证输出的 Markdown 是否符合项目规范。
"""

import re

import yaml


class MarkdownValidator:
    """Markdown 验证器"""

    REQUIRED_FRONTMATTER_FIELDS = [
        'title',
        'category',
        'type',
        'model',
        'version',
        'date',
        'keywords',
        'source_pdf',
    ]

    def __init__(self, spec_file=None):
        """初始化验证器"""
        self.spec_file = spec_file

    def validate(self, markdown_content):
        """执行完整验证并返回结构化结果。"""
        errors = []
        warnings = []

        fm_errors, fm_warnings = self.check_frontmatter(markdown_content)
        errors.extend(fm_errors)
        warnings.extend(fm_warnings)

        title_errors, title_warnings = self.check_title_hierarchy(markdown_content)
        errors.extend(title_errors)
        warnings.extend(title_warnings)

        table_errors = self.check_tables(markdown_content)
        errors.extend(table_errors)

        semantic_warnings = self.check_semantic_lists(markdown_content)
        warnings.extend(semantic_warnings)

        score = max(0.0, min(10.0, 10.0 - 1.5 * len(errors) - 0.5 * len(warnings)))

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'score': round(score, 2),
        }

    def check_frontmatter(self, markdown_content):
        """检查 Frontmatter 是否存在且字段完整。"""
        errors = []
        warnings = []

        if not markdown_content.startswith('---\n'):
            errors.append('缺少 Frontmatter 起始分隔符（---）。')
            return errors, warnings

        lines = markdown_content.splitlines()
        end_idx = None
        for idx, line in enumerate(lines[1:], start=1):
            if line.strip() == '---':
                end_idx = idx
                break

        if end_idx is None:
            errors.append('Frontmatter 未正确闭合（缺少结束 ---）。')
            return errors, warnings

        yaml_text = '\n'.join(lines[1:end_idx])
        try:
            metadata = yaml.safe_load(yaml_text) or {}
        except yaml.YAMLError as exc:
            errors.append(f'Frontmatter YAML 解析失败: {exc}')
            return errors, warnings

        missing_fields = [
            field for field in self.REQUIRED_FRONTMATTER_FIELDS if field not in metadata
        ]
        if missing_fields:
            errors.append(f"Frontmatter 缺少必填字段: {', '.join(missing_fields)}")

        keywords = metadata.get('keywords')
        if keywords is not None and not isinstance(keywords, list):
            warnings.append('Frontmatter 字段 keywords 建议使用列表类型。')

        return errors, warnings

    def check_title_hierarchy(self, markdown_content):
        """检查标题层级。"""
        errors = []
        warnings = []

        title_lines = re.findall(r'^(#{1,6})\s+.+$', markdown_content, flags=re.MULTILINE)
        h1_count = sum(1 for level in title_lines if len(level) == 1)

        if h1_count != 1:
            errors.append(f'一级标题数量应为 1，当前为 {h1_count}。')

        last_level = 0
        for level_marks in title_lines:
            level = len(level_marks)
            if level > 4:
                warnings.append(f'检测到 {level} 级标题，建议不超过 4 级。')

            if last_level and level - last_level > 1:
                warnings.append(f'标题层级跳跃：从 {last_level} 级直接到 {level} 级。')
            last_level = level

        if not title_lines:
            errors.append('文档中未检测到任何标题。')

        return errors, warnings

    def check_tables(self, markdown_content):
        """检查是否包含传统 Markdown 表格。"""
        errors = []

        lines = markdown_content.splitlines()
        for idx in range(len(lines) - 1):
            if re.match(r'^\|.+\|\s*$', lines[idx].strip()) and re.match(
                r'^\|[\s\-:|]+\|\s*$', lines[idx + 1].strip()
            ):
                errors.append(
                    f'检测到传统 Markdown 表格（第 {idx + 1} 行附近），应转换为语义列表完整句式。'
                )
                break

        return errors

    def check_semantic_lists(self, markdown_content):
        """检查语义列表完整句式的基础特征。"""
        warnings = []

        candidate_lines = [
            line for line in markdown_content.splitlines()
            if line.strip() and '：' in line and not line.strip().startswith('#')
        ]
        if len(candidate_lines) < 2:
            warnings.append('语义列表特征较弱，建议补充“字段：说明”式完整句表达。')

        return warnings

    def generate_report(self, validation_result):
        """生成文本报告。"""
        status = '通过' if validation_result['valid'] else '未通过'
        lines = [
            '# Markdown验证报告',
            '',
            f"- 结果：{status}",
            f"- 评分：{validation_result['score']}/10",
            f"- 错误数：{len(validation_result['errors'])}",
            f"- 警告数：{len(validation_result['warnings'])}",
            '',
            '## 错误',
        ]

        if validation_result['errors']:
            lines.extend([f"- {item}" for item in validation_result['errors']])
        else:
            lines.append('- 无')

        lines.extend(['', '## 警告'])
        if validation_result['warnings']:
            lines.extend([f"- {item}" for item in validation_result['warnings']])
        else:
            lines.append('- 无')

        return '\n'.join(lines) + '\n'


def validate_markdown_file(markdown_file, spec_file=None):
    """便捷函数：验证单个 Markdown 文件。"""
    with open(markdown_file, 'r', encoding='utf-8') as f:
        content = f.read()

    validator = MarkdownValidator(spec_file=spec_file)
    result = validator.validate(content)
    return result, validator.generate_report(result)


class HallucinationDetector:
    """
    数字幻觉自动检测器

    通过对比 raw（忠实还原）和 final（智能增强）两个版本的数字，
    检测 final 中出现但 raw 中没有的数字（潜在幻觉）。
    """

    # 匹配整数和小数（不用 \b 避免中文字边界失效）
    NUMBER_PATTERN = re.compile(r'\d+(?:\.\d+)?')

    def extract_numbers(self, text):
        """从文本中提取所有数字字符串，返回集合。"""
        # 排除纯标题序号（如 ## 2. 步骤）
        clean = re.sub(r'^#+\s+\d+[\.、]\s*', '', text, flags=re.MULTILINE)
        return set(self.NUMBER_PATTERN.findall(clean))

    def detect(self, raw_content, final_content):
        """
        对比 raw 和 final，返回检测结果。

        Returns:
            dict:
                - new_in_final: final有但raw没有的数字（潜在幻觉）
                - lost_in_final: raw有但final没有的数字（潜在遗漏）
                - hallucination_count: 潜在幻觉数量
                - risk_level: 'high' / 'medium' / 'low'
        """
        raw_nums = self.extract_numbers(raw_content)
        final_nums = self.extract_numbers(final_content)

        new_in_final = final_nums - raw_nums
        lost_in_final = raw_nums - final_nums

        # 过滤掉常见无意义数字（1、2、3等序号）
        noise = {str(i) for i in range(1, 20)}
        new_in_final -= noise
        lost_in_final -= noise

        count = len(new_in_final)
        if count >= 5:
            risk = 'high'
        elif count >= 2:
            risk = 'medium'
        else:
            risk = 'low'

        return {
            'new_in_final': sorted(new_in_final),
            'lost_in_final': sorted(lost_in_final),
            'hallucination_count': count,
            'risk_level': risk,
        }

    def generate_report(self, detection_result, pdf_name=''):
        """生成数字幻觉检测报告文本。"""
        r = detection_result
        risk_emoji = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}
        lines = [
            '## 数字幻觉检测',
            '',
            f"- 文件：{pdf_name}" if pdf_name else '',
            f"- 风险等级：{risk_emoji.get(r['risk_level'], '')} {r['risk_level'].upper()}",
            f"- 潜在幻觉数字数量：{r['hallucination_count']}",
            '',
            '### final中新增（raw中没有）',
        ]
        lines = [l for l in lines if l != '']  # 去空行占位

        if r['new_in_final']:
            lines.extend([f"  - `{n}`" for n in r['new_in_final']])
        else:
            lines.append('  - 无')

        lines.extend(['', '### raw中有但final丢失'])
        if r['lost_in_final']:
            lines.extend([f"  - `{n}`" for n in r['lost_in_final']])
        else:
            lines.append('  - 无')

        return '\n'.join(lines) + '\n'
