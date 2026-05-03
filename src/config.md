# config.py

## 程序说明
- 路径：`src/config.py`
- 作用：提供配置加载/合并与模型能力注册表查询。
- 输入：`default.yml`、用户配置文件、CLI 覆盖参数、模型能力文件。
- 输出：运行时配置字典与模型能力描述。

## 函数说明
### `ConfigManager`
- `load_default()`：加载默认配置。
- `load_user(config_file)`：加载并覆盖用户配置。
- `load_cli_overrides(cli_args)`：应用命令行覆盖。
- `get(key, default)` / `set(key, value)`：读写点路径配置。
- `get_api_config(pdf_type)`：返回按 `type_overrides` 合并后的 API 配置。
- `save_user_config(config_file)`：保存当前配置。

### `ModelCapabilities`
- `load_registry(registry_file)`：加载模型能力注册表。
- `get_model_info(provider, model)`：获取模型能力项（支持去标签匹配）。
- `get_vision_support(...)` / `get_chinese_support(...)`：能力查询。
- `describe(...)`：统一输出能力描述字典。

## 函数调用
- 上游调用：
  - `pdfsc.py`、`model_adapter.py`。
- 下游调用：
  - `yaml.safe_load/dump`、文件系统读写。
- 关键链路：
  - `main -> ConfigManager(load_default/load_user/load_cli_overrides)`
  - `ModelAdapterFactory -> ModelCapabilities.describe/get_vision_support`
