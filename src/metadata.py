"""
Frontmatter元数据生成模块

功能：从PDF文件名和内容生成符合规范的YAML Frontmatter
作者：pdfsc项目
创建日期：2026-03-13
"""

import os
import re
from datetime import date
from typing import Dict, List, Optional
import yaml


class FrontmatterGenerator:
    """Frontmatter生成器"""

    def __init__(self):
        """初始化生成器"""
        pass

    def generate(self, pdf_path: str, category: Optional[str] = None,
                 doc_type: Optional[str] = None,
                 keywords: Optional[List[str]] = None,
                 version: Optional[str] = None) -> str:
        """
        生成Frontmatter YAML字符串

        Args:
            pdf_path: PDF文件路径
            category: 文档分类（可选，如未提供则尝试从文件名推断）
            doc_type: 文档类型（可选，如未提供则尝试从文件名推断）
            keywords: 关键词列表（可选）
            version: 版本号（可选，如未提供则尝试从文件名提取）

        Returns:
            str: YAML格式的Frontmatter字符串（包含---分隔符）

        示例:
            >>> generator = FrontmatterGenerator()
            >>> frontmatter = generator.generate("TaiShan 200 快速安装指南 (型号2280) 10.pdf")
            >>> print(frontmatter)
        """
        # 提取元数据
        metadata = self._extract_metadata(pdf_path, category, doc_type, keywords, version)

        # 生成YAML
        frontmatter_yaml = self._to_yaml(metadata)

        return frontmatter_yaml

    def _extract_metadata(self, pdf_path: str, category: Optional[str],
                         doc_type: Optional[str],
                         keywords: Optional[List[str]],
                         version: Optional[str]) -> Dict:
        """
        从PDF文件名提取元数据

        Args:
            pdf_path: PDF文件路径
            category: 指定的分类（优先使用）
            doc_type: 指定的文档类型（优先使用）
            keywords: 指定的关键词（优先使用）
            version: 指定的版本号（优先使用）

        Returns:
            Dict: 元数据字典
        """
        filename = os.path.basename(pdf_path)
        filename_no_ext = os.path.splitext(filename)[0]

        # 提取标题（去除版本号和后缀）
        title = self._extract_title(filename_no_ext)

        # 提取型号
        model = self._extract_model(filename_no_ext)

        # 提取版本号（如果未手动指定）
        if not version:
            version = self._extract_version(filename_no_ext)

        # 推断分类（如果未手动指定）
        if not category:
            category = self._infer_category(filename_no_ext)

        # 推断文档类型（如果未手动指定）
        if not doc_type:
            doc_type = self._infer_doc_type(filename_no_ext)

        # 生成关键词（如果未手动指定）
        if not keywords:
            keywords = self._generate_keywords(filename_no_ext, category, doc_type)

        # 获取当前日期
        today = date.today().isoformat()

        metadata = {
            'title': title,
            'category': category,
            'type': doc_type,
            'model': model,
            'version': version,
            'date': today,
            'keywords': keywords,
            'source_pdf': filename
        }

        return metadata

    def _extract_title(self, filename: str) -> str:
        """从文件名提取标题"""
        # 移除版本号（数字+点号形式，如" 10"）
        title = re.sub(r'\s+\d+$', '', filename)
        # 移除括号内容（通常是型号）
        # title = re.sub(r'\s*\([^)]*\)\s*', ' ', title)
        return title.strip()

    def _extract_model(self, filename: str) -> str:
        """从文件名提取型号"""
        # 匹配括号中的型号信息
        model_match = re.search(r'[（(]([^)）]*型号[^)）]*)[)）]', filename)
        if model_match:
            return model_match.group(1).strip()

        # 匹配 TaiShan 200 + 型号
        model_match = re.search(r'TaiShan\s*200[^)）]*型号\s*\d+', filename, re.IGNORECASE)
        if model_match:
            return model_match.group(0).strip()

        # 默认值
        return "TaiShan 200"

    def _extract_version(self, filename: str) -> str:
        """从文件名提取版本号"""
        # 匹配文件名末尾的数字（通常是版本号）
        version_match = re.search(r'\s+(\d+)$', filename)
        if version_match:
            return version_match.group(1)

        return "1"

    def _infer_category(self, filename: str) -> str:
        """推断文档分类"""
        filename_lower = filename.lower()

        if '安装' in filename_lower or 'install' in filename_lower:
            return "安装配置"
        elif '故障' in filename_lower or 'trouble' in filename_lower or '维护' in filename_lower:
            return "故障处理"
        elif '用户指南' in filename_lower or 'user guide' in filename_lower:
            return "用户指南"
        elif '产品手册' in filename_lower or 'product manual' in filename_lower:
            return "产品说明"
        elif '技术白皮书' in filename_lower or 'white paper' in filename_lower:
            return "技术文档"
        elif '规格' in filename_lower or 'specification' in filename_lower:
            return "规格参数"
        else:
            return "其他"

    def _infer_doc_type(self, filename: str) -> str:
        """推断文档类型"""
        filename_lower = filename.lower()

        if '快速' in filename_lower and '指南' in filename_lower:
            return "快速指南"
        elif '安装指南' in filename_lower or 'installation guide' in filename_lower:
            return "安装指南"
        elif '用户指南' in filename_lower or 'user guide' in filename_lower:
            return "用户指南"
        elif '手册' in filename_lower or 'manual' in filename_lower:
            return "手册"
        elif '白皮书' in filename_lower or 'white paper' in filename_lower:
            return "白皮书"
        elif '参考' in filename_lower or 'reference' in filename_lower:
            return "参考文档"
        else:
            return "文档"

    def _generate_keywords(self, filename: str, category: str, doc_type: str) -> List[str]:
        """生成关键词"""
        keywords = []

        # 从分类生成关键词
        if category and category != "其他":
            keywords.append(category.replace("配置", "").replace("处理", ""))

        # 从文档类型生成关键词
        if doc_type and doc_type != "文档":
            keywords.append(doc_type.replace("指南", "").replace("手册", ""))

        # 从文件名提取关键词
        filename_lower = filename.lower()
        if 'taishan' in filename_lower or '泰山' in filename_lower:
            keywords.append("TaiShan服务器")
        if '2280' in filename:
            keywords.append("2280")
        if '快速' in filename:
            keywords.append("快速开始")
        if '硬件' in filename_lower:
            keywords.append("硬件配置")

        # 去重并限制数量
        keywords = list(dict.fromkeys(keywords))  # 去重并保持顺序
        return keywords[:5]  # 最多5个关键词

    def _to_yaml(self, metadata: Dict) -> str:
        """
        将元数据转换为YAML格式

        Args:
            metadata: 元数据字典

        Returns:
            str: YAML格式字符串（包含---分隔符）
        """
        yaml_content = yaml.dump(
            metadata,
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False
        )

        frontmatter = f"---\n{yaml_content}---\n"
        return frontmatter


def generate_frontmatter(pdf_path: str, **kwargs) -> str:
    """
    便捷函数：生成Frontmatter

    Args:
        pdf_path: PDF文件路径
        **kwargs: 其他参数（category, doc_type, keywords, version）

    Returns:
        str: YAML格式的Frontmatter

    示例:
        >>> frontmatter = generate_frontmatter(
        ...     "TaiShan 200 快速安装指南 (型号2280) 10.pdf",
        ...     category="安装配置",
        ...     keywords=["安装", "快速开始", "硬件配置"]
        ... )
        >>> print(frontmatter)
    """
    generator = FrontmatterGenerator()
    return generator.generate(pdf_path, **kwargs)


if __name__ == "__main__":
    # 测试代码
    import sys

    if len(sys.argv) < 2:
        print("用法: python metadata.py <pdf文件路径>")
        print("示例: python metadata.py 'TaiShan 200 快速安装指南 (型号2280) 10.pdf'")
        sys.exit(1)

    pdf_path = sys.argv[1]

    try:
        frontmatter = generate_frontmatter(pdf_path)
        print("\n=== 生成的Frontmatter ===")
        print(frontmatter)

    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)
