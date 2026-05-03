# extractor.py

## 程序说明
- 路径：`src/extractor.py`
- 作用：提取 PDF 文本与表格，并对多栏版面做基础顺序重建。
- 输入：PDF 文件路径。
- 输出：文本结果、表格结果、结构化组合结果。

## 函数说明
### `TextExtractor.__init__(pdf_path)`
- 功能：校验路径并初始化提取器。

### `__enter__()` / `__exit__(...)`
- 功能：上下文管理，负责打开/关闭 `pdfplumber` 对象。

### `extract_text()`
- 功能：提取全文与分页面文本。
- 返回：`{full_text, pages, metadata}`。

### `extract_tables()`
- 功能：提取表格并标注页码、行列数。
- 返回：`{tables, metadata}`。

### `extract_structure()`
- 功能：组合文本与表格结果。

### `_extract_page_text(page)`
- 功能：单页提取，优先走布局重建逻辑，失败回退默认提取。

### `_extract_layout_text(words, page_width)`
- 功能：词块 -> 行 -> 列，重建阅读顺序。

### `_build_lines(words, page_width)`
- 功能：按 `top/x` 聚合词块为行。

### `_cluster_columns(lines, page_width)`
- 功能：按 `x0` 聚类列，适配双栏/三栏。

### 便捷函数
- `extract_pdf_text(pdf_path)`：返回全文。
- `extract_pdf_by_pages(pdf_path)`：返回分页面文本。

## 函数调用
- 上游调用：
  - `pdfsc.convert_single_pdf()`。
- 下游调用：
  - `pdfplumber` 页对象的 `extract_words/extract_text/extract_tables`。
- 关键链路：
  - `extract_structure -> extract_text + extract_tables`
  - `extract_text -> _extract_page_text -> _extract_layout_text -> _build_lines/_cluster_columns`
