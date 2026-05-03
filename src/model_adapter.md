# model_adapter.py

## 程序说明
- 路径：`src/model_adapter.py`
- 作用：统一多模型调用接口，封装 provider 差异与重试逻辑。
- 输入：配置、prompt、可选图片输入。
- 输出：模型返回文本（失败时抛异常给上层处理）。

## 函数说明
### `BaseModelAdapter`
- 核心能力：
  - `call(...)` 抽象接口
  - `check_vision_support()/apply_capability_guard()` 能力降级
  - `_prepare_images/_encode_image()` 图片输入标准化
  - `_resolve_api_key()` 环境变量读取

### `ModelAdapterFactory`
- `create_adapter(...)`：按 provider 创建具体适配器。
- `create_from_config(...)`：从配置对象创建适配器。

### 具体适配器
- `AnthropicAdapter.call(...)`
- `OpenAICompatibleAdapter.call(...)`
- `OpenAIAdapter`（OpenAI）
- `QwenAdapter`（Dashscope OpenAI兼容）
- `OllamaAdapter`（本地 OpenAI兼容）
- `MockAdapter.call(...)`（无网络流程联调）

## 函数调用
- 上游调用：
  - `Converter._get_adapter()`。
- 下游调用：
  - `anthropic` SDK、`openai` SDK 或 mock 本地输出。
- 关键链路：
  - `Converter._call_model -> Factory.create_from_config -> Adapter.call`
