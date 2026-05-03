# metadata.py

## 程序说明
- 路径：`src/metadata.py`
- 作用：从文件名/输入参数生成 YAML frontmatter。
- 输入：PDF 文件路径与可选元数据参数。
- 输出：frontmatter 字符串（含 `---` 分隔）。

## 函数说明
### `FrontmatterGenerator.generate(pdf_path, category, doc_type, keywords, version)`
- 功能：主入口，返回完整 frontmatter。

### `_extract_metadata(...)`
- 功能：组装元数据字典（标题、分类、类型、型号、版本、关键词等）。

### `_extract_title/_extract_model/_extract_version(...)`
- 功能：从文件名解析基础字段。

### `_infer_category/_infer_doc_type(...)`
- 功能：基于规则推断分类与文档类型。

### `_generate_keywords(...)`
- 功能：生成关键词列表并去重截断。

### `_to_yaml(metadata)`
- 功能：将字典序列化为 YAML frontmatter。

### `generate_frontmatter(pdf_path, **kwargs)`
- 功能：便捷函数封装。

## 函数调用
- 上游调用：
  - `pdfsc.convert_single_pdf()`。
- 下游调用：
  - `yaml.dump`、日期工具。
- 关键链路：
  - `generate -> _extract_metadata -> _to_yaml`
