# logger.py

## 程序说明
- 路径：`src/logger.py`
- 作用：统一日志封装，支持控制台与文件双输出。
- 输入：日志级别、日志路径、控制台开关。
- 输出：`Logger` 对象，供全系统记录日志。

## 函数说明
### `Logger.__init__(name, level, log_file, console_output)`
- 功能：创建并配置 Python `logging` handler。

### `debug/info/warning/error/critical(msg)`
- 功能：各级别日志输出。

### `create_logger(config)`
- 功能：根据配置对象构建 `Logger`。
- 参数：`ConfigManager`。
- 返回：`Logger` 实例。

## 函数调用
- 上游调用：
  - `pdfsc.main()`。
- 下游调用：
  - Python 标准库 `logging`。
- 关键链路：
  - `main -> create_logger -> Logger.xxx`
