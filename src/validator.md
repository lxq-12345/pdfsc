# validator.py

## 程序说明
- 路径：`src/validator.py`
- 作用：对 Markdown 输出做规范校验与数字幻觉检测。
- 输入：Markdown 文本（raw/final）。
- 输出：验证结果字典与可读报告文本。

## 函数说明
### `MarkdownValidator`
- `validate(markdown_content)`：执行完整验证，返回 `valid/errors/warnings/score`。
- `check_frontmatter(...)`：检查 frontmatter 存在性与字段完整性。
- `check_title_hierarchy(...)`：检查标题层级与 H1 数量。
- `check_tables(...)`：检查传统 Markdown 表格违规。
- `check_semantic_lists(...)`：语义列表特征检查。
- `generate_report(validation_result)`：输出验证报告文本。

### `validate_markdown_file(markdown_file, spec_file)`
- 功能：文件级便捷验证函数。

### `HallucinationDetector`
- `extract_numbers(text)`：提取数字集合。
- `detect(raw_content, final_content)`：检测新增/丢失数字并判定风险。
- `generate_report(detection_result, pdf_name)`：输出幻觉检测报告文本。

## 函数调用
- 上游调用：
  - `pdfsc.run_verify()`
  - `pdfsc.convert_single_pdf()`（质量报告）
- 下游调用：
  - 正则解析、`yaml.safe_load`。
- 关键链路：
  - `validate -> frontmatter/title/table/semantic`
  - `detect(raw, final) -> risk_level`
