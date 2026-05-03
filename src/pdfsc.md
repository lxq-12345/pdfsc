# pdfsc.py

## 程序说明
- 路径：`src/pdfsc.py`
- 作用：CLI 主入口，负责参数解析、配置加载、任务调度、单文件/批量转换、验证与统计。
- 输入：命令行参数、配置文件、PDF/Markdown 文件路径。
- 输出：转换结果文件、质量报告、批量汇总、日志输出。

## 函数说明
### `main()`
- 功能：解析命令并分发到具体执行函数。
- 参数：无（读取 CLI 参数）。
- 返回：无（失败时 `sys.exit(1)`）。

### `run_convert(args, config, logger)`
- 功能：执行单文件转换。
- 参数：命令参数、配置对象、日志对象。
- 返回：无（内部调用 `convert_single_pdf`）。

### `run_convert_batch(args, config, logger)`
- 功能：执行批量转换并生成批量汇总。
- 参数：同上。
- 返回：无。

### `run_verify(args, logger)`
- 功能：验证 Markdown 规范符合性。
- 参数：验证目标路径、日志对象。
- 返回：无。

### `run_stats(args, logger)`
- 功能：统计输出目录中的转换产物。
- 参数：输出目录路径。
- 返回：无。

### `maybe_apply_capability_guard(config, logger)`
- 功能：根据模型能力自动降级图片模式。
- 参数：配置、日志。
- 返回：无。

### `convert_single_pdf(pdf_path, output_root, config, logger, index)`
- 功能：单个 PDF 的完整处理链路（检测→提取→转换→图片处理→验证→落盘）。
- 参数：输入 PDF、输出目录、配置、日志、序号。
- 返回：结果字典（raw/final/report 路径、评分、风险、运行模式）。

### `_write_batch_summary(summary_path, results, success_count, total_count)`
- 功能：生成批量汇总报告（含模式统计与低质量命中）。
- 返回：无（落盘写文件）。

### 辅助函数
- `_today()`：返回日期字符串。
- `collect_pdf_files(...)`：收集 PDF 文件列表。
- `parse_frontmatter(...)`：解析 frontmatter。
- `build_output_basename(...)`：按模板生成输出文件名。
- `sanitize_filename(...)`：清理非法文件名字符。
- `_is_low_quality_mode(mode)`：判断低质量模式。

## 函数调用
- 上游调用：
  - 用户命令行直接调用 `main()`。
- 下游调用：
  - `ConfigManager`（配置加载）
  - `PDFDetector`、`TextExtractor`、`FrontmatterGenerator`
  - `Converter`（两步转换）
  - `ImageProcessor`（可选图片处理）
  - `MarkdownValidator`、`HallucinationDetector`
- 关键链路：
  - `main -> run_convert(_batch) -> convert_single_pdf -> Converter -> validator/report`
