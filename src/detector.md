# detector.py

## 程序说明
- 路径：`src/detector.py`
- 作用：检测 PDF 类型（`text_only`/`text_image`/`scanned`）。
- 输入：PDF 文件路径。
- 输出：类型字符串与分析元数据。

## 函数说明
### `PDFDetector.__init__(text_threshold, image_threshold)`
- 功能：设置文字/图片阈值。

### `detect_type(pdf_path)`
- 功能：返回类型结果。

### `analyze(pdf_path)`
- 功能：返回详细分析信息（页数、文本量、图片数等）。

### `_analyze_pdf(pdf_path)`
- 功能：调用 `pdfplumber` 与 `PyMuPDF` 收集统计信息。

### `_classify(metadata)`
- 功能：根据统计值判定 PDF 类型。

### `detect_pdf_type(...)`
- 功能：便捷函数，返回 `(type, metadata)`。

## 函数调用
- 上游调用：
  - `pdfsc.convert_single_pdf()`。
- 下游调用：
  - `pdfplumber.open`、`fitz.open`。
- 关键链路：
  - `analyze -> _analyze_pdf -> _classify`
