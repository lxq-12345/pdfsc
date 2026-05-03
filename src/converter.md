# converter.py

## 程序说明
- 路径：`src/converter.py`
- 作用：实现两步转换核心逻辑（restore/enhance），并处理离线回退、mock、低质量标记。
- 输入：提取后的 PDF 内容、元数据、配置。
- 输出：restore Markdown、enhance Markdown。

## 函数说明
### `Converter.__init__(config, logger, pdf_type)`
- 功能：初始化转换器及模式状态。

### `convert_restore(pdf_content, pdf_metadata)`
- 功能：执行忠实还原阶段。
- 返回：restore Markdown。

### `convert_enhance(restore_markdown, pdf_metadata)`
- 功能：执行智能增强阶段。
- 返回：enhance Markdown。

### `convert_full(pdf_content, pdf_metadata)`
- 功能：依次执行 restore 与 enhance。
- 返回：`(restore, enhance)`。

### `_call_model(prompt)`
- 功能：根据模式执行真实调用或回退。
- 返回：模型输出或 `None`。

### `_fallback_restore(...)` / `_fallback_enhance(...)`
- 功能：模型不可用时本地构造输出。

### `_apply_low_quality_marker(markdown, stage)`
- 功能：在低质量模式下注入 `DRAFT/LOW_QUALITY` 标记。

### `get_last_modes()`
- 功能：返回本次 restore/enhance 的运行模式。

## 函数调用
- 上游调用：
  - `pdfsc.convert_single_pdf()`。
- 下游调用：
  - `ModelAdapterFactory.create_from_config()`
  - 适配器 `call()`。
- 关键链路：
  - `convert_full -> convert_restore -> _call_model -> fallback/normal`
  - `convert_full -> convert_enhance -> _call_model -> fallback/normal`
