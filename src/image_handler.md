# image_handler.py

## 程序说明
- 路径：`src/image_handler.py`
- 作用：图片保存、过滤、Markdown 插入与三模式图片流水线协调。
- 输入：图片字节、Markdown 内容、模式配置。
- 输出：更新后的 Markdown、保存后的图片文件。

## 函数说明
### `ImageHandler`
- `save_image(...)`：按命名规则保存图片。
- `insert_image_reference(...)`：在指定位置插入图片引用。
- `filter_images(images, min_width)`：过滤装饰性小图。

### `ImageProcessor.__init__(pdf_path, images_output_dir, doc_index, model_adapter)`
- 功能：初始化视觉处理器与图片处理器。

### `process(markdown_content, image_mode, min_width)`
- 功能：根据模式处理图片并插入 Markdown。
- 模式：`disabled` / `description-only` / `extract`。

### `_find_anchor_position(lines, anchor_text)`
- 功能：根据锚文本定位插入点。

### `_get_description(img, index)`
- 功能：生成图片说明文本（当前为占位描述）。

### `close()/__enter__/__exit__`
- 功能：管理 `VisionProcessor` 资源。

## 函数调用
- 上游调用：
  - `pdfsc.convert_single_pdf()`。
- 下游调用：
  - `VisionProcessor.extract_images/get_image_text_anchors`。
- 关键链路：
  - `process -> vision.extract_images -> handler.filter/save -> Markdown插入`
