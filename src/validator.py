"""
Output Validation Module

验证输出的Markdown是否符合规范
"""


class MarkdownValidator:
    """Markdown验证器"""

    def __init__(self, spec_file):
        """初始化验证器"""
        self.spec_file = spec_file

    def validate(self, markdown_content):
        """
        验证Markdown是否符合规范

        Args:
            markdown_content: Markdown内容

        Returns:
            dict: {
                'valid': bool,
                'errors': list,
                'warnings': list,
                'score': float (0-10)
            }
        """
        raise NotImplementedError()

    def check_frontmatter(self, markdown_content):
        """检查Frontmatter"""
        raise NotImplementedError()

    def check_title_hierarchy(self, markdown_content):
        """检查标题层级"""
        raise NotImplementedError()

    def check_tables(self, markdown_content):
        """检查是否存在传统Markdown表格"""
        raise NotImplementedError()

    def check_semantic_lists(self, markdown_content):
        """检查语义列表的质量"""
        raise NotImplementedError()

    def generate_report(self, validation_result):
        """
        生成验证报告

        Returns:
            str: 验证报告文本
        """
        raise NotImplementedError()
