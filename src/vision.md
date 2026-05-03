# vision.py

## 程序说明
- 路径：`src/vision.py`
- 作用：基于 PyMuPDF 执行页面渲染、图片提取、图片锚文本识别。
- 输入：PDF 文件路径。
- 输出：页面图像数据、图片对象列表、锚文本与区域信息。

## 函数说明
### `VisionProcessor.__init__(pdf_path)`
- 功能：初始化处理器并延迟打开文档。

### `_get_doc() / close() / __enter__ / __exit__`
- 功能：文档句柄生命周期管理。

### `render_pages(dpi)`
- 功能：按页渲染 PNG 字节。
- 返回：页级图像数据列表。

### `extract_images(image_mode)`
- 功能：提取嵌入图片（含尺寸、xref、bbox）。
- 返回：图片列表。

### `_get_image_bbox(page, xref)`
- 功能：定位图片边界框。

### `get_image_text_anchors()`
- 功能：获取图片上方最近文字块作为锚文本。

### `identify_image_regions()`
- 功能：仅识别图片区域，不提取字节。

## 函数调用
- 上游调用：
  - `ImageProcessor`（`image_handler.py`）。
- 下游调用：
  - `fitz`（PyMuPDF）文档与页面接口。
- 关键链路：
  - `ImageProcessor.process -> VisionProcessor.extract_images/get_image_text_anchors`
