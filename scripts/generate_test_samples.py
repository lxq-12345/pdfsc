#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试样本生成脚本 - PREP-3
用途: 从源 MD 文件提取三个层次的表格内容，生成测试样本文件

Author: Claude (pdfsc项目)
Created: 2026-03-12
"""

import os
import re
from pathlib import Path


def read_md_lines(file_path, start_line, end_line):
    """读取 MD 文件的指定行范围（行号从1开始）"""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    # 转换为0-based索引
    return ''.join(lines[start_line-1:end_line])


def remove_markdown_formatting(text):
    """去除 Markdown 格式化，模拟 PDF 提取的原始文本"""
    # 保留原始文本，但去除 Markdown 特殊符号
    result = text

    # 去除标题符号 ##
    result = re.sub(r'^#{1,6}\s+', '', result, flags=re.MULTILINE)

    # 去除粗体 **text**
    result = re.sub(r'\*\*([^*]+)\*\*', r'\1', result)

    # 去除emoji符号（可选，根据PDF实际情况调整）
    # 这里保留emoji，因为它们可能在PDF中也存在

    # 去除引用符号 >
    result = re.sub(r'^>\s+', '', result, flags=re.MULTILINE)

    # 去除列表符号 -
    result = re.sub(r'^-\s+', '  ', result, flags=re.MULTILINE)

    return result


def create_test_sample(level_name, level_dir, content, metadata):
    """创建单个测试样本的文件对"""
    level_path = Path(level_dir) / level_name
    level_path.mkdir(parents=True, exist_ok=True)

    # 生成 input.txt（模拟PDF提取）
    input_text = remove_markdown_formatting(content)
    with open(level_path / 'input.txt', 'w', encoding='utf-8') as f:
        f.write(input_text)

    # 生成 expected.md（标准输出）
    with open(level_path / 'expected.md', 'w', encoding='utf-8') as f:
        f.write(content)

    # 生成 metadata.json（元数据）
    import json
    with open(level_path / 'metadata.json', 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print(f"✅ 已创建测试样本: {level_name}")
    print(f"   - input.txt: {len(input_text)} 字符")
    print(f"   - expected.md: {len(content)} 字符")


def main():
    """主函数"""
    # 配置路径
    source_md = Path("d:/usr/百信公司项目/pdf_to_kbase/TaiShan-200服务器资料/转换文档/02_TaiShan200_快速安装指南_型号2280.md")
    test_dir = Path("d:/usr/百信公司项目/pdfsc/tests/test_cases/bottleneck1")

    print("=" * 60)
    print("PREP-3: 测试样本生成")
    print("=" * 60)

    # Level 1: 符号说明表 (2D键值对)
    print("\n[1/3] 生成 Level 1 - 简单表格（符号说明）...")
    level1_content = read_md_lines(source_md, 25, 40)
    create_test_sample(
        'level1_simple',
        test_dir,
        level1_content,
        {
            'level': 1,
            'type': '2D键值对表格',
            'description': '符号说明 - 简单映射关系',
            'source_file': str(source_md),
            'source_lines': '25-40',
            'records': 6,
            'dimensions': ['符号', '含义']
        }
    )

    # Level 2: 环境参数要求 (3D嵌套)
    print("\n[2/3] 生成 Level 2 - 复杂表格（环境参数）...")
    level2_content = read_md_lines(source_md, 63, 113)
    create_test_sample(
        'level2_complex',
        test_dir,
        level2_content,
        {
            'level': 2,
            'type': '3D嵌套表格',
            'description': '环境参数要求 - 多维度嵌套（温度/湿度/海拔）',
            'source_file': str(source_md),
            'source_lines': '63-113',
            'categories': ['温度要求', '湿度要求', '海拔高度要求', '其他环境条件'],
            'dimensions': ['类别', '工作条件', '存储条件']
        }
    )

    # Level 3: 线缆连接表 (5D语义)
    print("\n[3/3] 生成 Level 3 - 语义表格（线缆连接）...")
    level3_content = read_md_lines(source_md, 219, 236)
    create_test_sample(
        'level3_semantic',
        test_dir,
        level3_content,
        {
            'level': 3,
            'type': '5D语义表格',
            'description': '线缆类型和连接位置 - 多维语义关系',
            'source_file': str(source_md),
            'source_lines': '219-236',
            'records': 7,
            'dimensions': ['线缆名称', '用途', '配置数量', '连接位置', '功能说明']
        }
    )

    # 生成 README.md
    print("\n[4/4] 生成 README.md...")
    readme_content = f"""# 瓶颈1验证 - 表格语义转换测试样本

**生成时间**: 2026-03-12
**任务编号**: PREP-3
**验证目标**: 测试 AI 提示词对三个层次表格的转换质量

---

## 📁 目录结构

```
bottleneck1/
├── level1_simple/        # 第一层次：2D键值对表格
│   ├── input.txt         # 模拟PDF提取的原始文本
│   ├── expected.md       # 标准Markdown输出
│   └── metadata.json     # 元数据
├── level2_complex/       # 第二层次：3D嵌套表格
│   ├── input.txt
│   ├── expected.md
│   └── metadata.json
├── level3_semantic/      # 第三层次：5D语义表格
│   ├── input.txt
│   ├── expected.md
│   └── metadata.json
└── README.md            # 本文件
```

---

## 🎯 测试样本说明

### Level 1: 简单表格（符号说明）
- **类型**: 2D键值对
- **来源**: 02_TaiShan200_快速安装指南_型号2280.md (行25-40)
- **特征**: 简单映射关系，符号→含义
- **记录数**: 6条
- **难度**: ⭐ 低

### Level 2: 复杂表格（环境参数要求）
- **类型**: 3D嵌套表格
- **来源**: 02_TaiShan200_快速安装指南_型号2280.md (行63-113)
- **特征**: 多维度嵌套（温度/湿度/海拔），包含条件分支
- **类别数**: 4个主类别
- **难度**: ⭐⭐ 中

### Level 3: 语义表格（线缆连接）
- **类型**: 5D语义表格
- **来源**: 02_TaiShan200_快速安装指南_型号2280.md (行219-236)
- **特征**: 多维语义关系（名称→用途→数量→位置→说明）
- **记录数**: 7条线缆
- **难度**: ⭐⭐⭐ 高

---

## ✅ 验收标准（VAL-1）

根据 `plan/项目规划.md` Step0-1 要求：

1. **评分标准**: 使用 `mem/瓶颈1评分标准_2026-03-11.md`
2. **通过条件**: 每个层次连续3次测试得分 ≥ 9.7/10
3. **测试次数**: 共9次（3个层次 × 3次迭代）
4. **优化策略**: 得分 < 9.7 时，分析问题并优化提示词

---

## 🔗 数据溯源

- **源项目**: d:/usr/百信公司项目/pdf_to_kbase
- **源文件**: TaiShan-200服务器资料/转换文档/02_TaiShan200_快速安装指南_型号2280.md
- **质量评分**: 9.7/10（已验证）
- **生成脚本**: scripts/generate_test_samples.py

---

## 📝 使用说明

1. **VAL-1验证阶段**:
   - 使用 `input.txt` 作为提示词输入
   - 使用 `expected.md` 作为标准答案
   - 使用评分标准对比输出质量

2. **后续开发阶段**:
   - 这些样本将作为单元测试的基准数据
   - 用于回归测试，确保代码修改不影响转换质量

---

**生成者**: Claude (pdfsc项目)
**版本**: v1.0
"""

    with open(test_dir / 'README.md', 'w', encoding='utf-8') as f:
        f.write(readme_content)

    print("✅ 已生成 README.md")

    print("\n" + "=" * 60)
    print("✅ PREP-3 完成！所有测试样本已生成。")
    print("=" * 60)


if __name__ == '__main__':
    main()
