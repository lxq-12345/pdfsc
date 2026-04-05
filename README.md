# PDF智转器（pdfsc）

AI 驱动的 PDF -> Markdown 转换工具，面向知识库/RAG 场景。

## 功能概览

- 两步转换流水线：忠实还原（raw）+ 智能增强（final）
- 支持单文件与批量转换
- 支持多模型适配：`anthropic/openai/qwen/ollama/mock`
- 支持离线回退与 D2 流程联调（`mock/offline`）
- 批量报告支持模式分布与低质量命中统计

## 项目结构

- `src/`：核心代码
- `config/`：默认配置与示例配置
- `scripts/`：安装、运行、测试脚本
- `tests/`：回归与阶段测试
- `output/`：转换输出与阶段报告
- `mem/`：会话备忘与归档

## 环境要求

- Python 3.10+
- Linux/macOS 或 Windows + WSL2（推荐）
- 可选：Ollama（本地模型）

## 安装

在项目根目录执行：

```bash
bash scripts/install.sh
```

安装脚本会优先创建并使用 `.venv_wsl`（兼容当前 WSL 工作流），若在非 WSL 环境则使用 `.venv`。

### Ubuntu 安装包安装（推荐用于服务器验收）

```bash
tar -xzf pdfsc-ubuntu-installer-20260405.tar.gz
cd pdfsc-ubuntu-installer-20260405
bash scripts/install.sh
cp config/config.example.yml config/config.yml
bash scripts/run_d2.sh flow-test
```

详细步骤请参考 [用户使用手册](./用户使用手册.md) 的安装章节。

## 配置

1. 复制配置模板：

```bash
cp config/config.example.yml config/config.yml
```

2. 按需修改模型与输出路径。

常用模式：

- 联调：`api.provider: mock`
- 离线：CLI 增加 `--offline`
- 本地模型：`api.provider: ollama`

## 使用方法

### 单文件转换

```bash
python3 src/pdfsc.py convert ./pdfs/sample.pdf --config ./config/config.yml
```

### 批量转换

```bash
python3 src/pdfsc.py convert-batch ./pdfs --config ./config/config.yml
```

### 验证与统计

```bash
python3 src/pdfsc.py verify ./output
python3 src/pdfsc.py stats ./output
```

### D2 一键流程联调

```bash
bash scripts/run_d2.sh flow-test
```

## 输出说明

- `output/markdown/raw/`：忠实还原输出
- `output/markdown/final/`：增强输出
- `output/reports/`：质量报告与批量汇总

当运行在 `mock/offline/fallback` 场景时，输出会自动打 `DRAFT/LOW_QUALITY` 标记，避免误当最终交付。

## 参考文档

- [项目规划](./plan/项目规划.md)
- [项目技术约定](./plan/项目技术约定.md)
- [技术手册](./技术手册.md)
- [用户使用手册](./用户使用手册.md)
- [软件体系架构](./软件体系架构.md)
- [程序清单（含说明）](./程序清单.md)
- [Markdown转换规范](./skills/Markdown转换规范.md)
- [环境说明](./环境说明.md)
- [配置模板](./config/config.example.yml)
