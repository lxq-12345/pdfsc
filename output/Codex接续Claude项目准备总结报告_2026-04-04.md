# Codex接续Claude项目准备总结报告

**项目**：PDF智转器（pdfsc）  
**日期**：2026-04-04  
**执行者**：Codex

---

## 一、工作目标

本次工作目标不是继续开发新功能，而是完成对 `pdfsc` 项目的接续准备，确保 Codex 在后续实施阶段中能够稳定替代 Claude 继续推进项目任务。

---

## 二、已完成的接续准备

### 1. 项目入口与规则确认

- 已读取 [CLAUDE.md](D:/usr/百信公司项目/pdfsc/CLAUDE.md)。
- 已读取 [会话管理协议.md](D:/usr/百信公司项目/pdfsc/会话管理协议.md)。
- 已读取 [plan/项目规划.md](D:/usr/百信公司项目/pdfsc/plan/项目规划.md)。
- 已读取 [skills/Markdown转换规范.md](D:/usr/百信公司项目/pdfsc/skills/Markdown转换规范.md)。
- 已确认本项目要求所有规划、备忘、报告均保存在项目目录内，不依赖外部计划目录。
- 已确认项目处于实施阶段，后续应直接执行、记录、验证，不使用外部 Plan Mode。

### 2. 当前阶段与真实进度核实

- 已核对最新备忘 [mem/备忘-2026-04-04.md](D:/usr/百信公司项目/pdfsc/mem/备忘-2026-04-04.md)。
- 已核对最近提交历史，确认 `master` 已合并到阶段 D1。
- 已确认项目真实进度已超过 `CLAUDE.md` 中记载的 Step0-4，实际已完成：
  - Step0-1 表格转换验证
  - Step0-4 防幻觉验证
  - 阶段 A1 / A2
  - 阶段 B1 / B2 / B3（部分真实测试待补）
  - 阶段 C1 / C2
  - 阶段 D1

### 3. 代码结构与主链路摸排

- 已确认 CLI 主入口为 [src/pdfsc.py](D:/usr/百信公司项目/pdfsc/src/pdfsc.py)。
- 已确认核心模块已具备：
  - [src/converter.py](D:/usr/百信公司项目/pdfsc/src/converter.py)：两步转换流水线
  - [src/extractor.py](D:/usr/百信公司项目/pdfsc/src/extractor.py)：文字与表格提取
  - [src/model_adapter.py](D:/usr/百信公司项目/pdfsc/src/model_adapter.py)：多模型适配层
  - [src/vision.py](D:/usr/百信公司项目/pdfsc/src/vision.py)：图片提取与页面处理
  - [src/image_handler.py](D:/usr/百信公司项目/pdfsc/src/image_handler.py)：图片模式处理与插入
  - [src/validator.py](D:/usr/百信公司项目/pdfsc/src/validator.py)：格式验证与数字幻觉检测
- 已确认当前支持命令：
  - `convert`
  - `convert-batch`
  - `verify`
  - `stats`

### 4. Windows 与 WSL 双环境现状核实

#### Windows 侧

- 项目路径：`D:\usr\百信公司项目\pdfsc`
- 项目内 Windows 虚拟环境存在：`D:\usr\百信公司项目\pdfsc\.venv`
- Windows 系统默认 `python` 指向 Windows Store 占位程序，不可直接作为可靠解释器。
- Git 在 Windows 路径执行正常，当前仓库状态干净，适合作为提交入口。

#### WSL 侧

- 已确认发行版：`Ubuntu`（WSL2）。
- 项目路径可直接使用：
  - `/mnt/d/usr/百信公司项目/pdfsc`
  - `/home/wy885/pdfsc`（软链接）
- 已确认以下软链接存在且有效：
  - `/home/wy885/pdfsc` -> `/mnt/d/usr/百信公司项目/pdfsc`
  - `/home/wy885/pdf_to_kbase` -> `/mnt/d/usr/百信公司项目/pdf_to_kbase`
  - `/home/wy885/projects` -> `/mnt/d/usr/百信公司项目`
- 已确认 WSL 虚拟环境可用：`/home/wy885/pdfsc/.venv_wsl`
- 已确认 WSL 中 `test_stage_d1.py` 可完整通过（18/18）。

### 5. Ollama 本地模型环境核实

- 已确认 Ollama 不在 Windows 侧可见。
- 已确认 WSL 中存在真实 Ollama 二进制：
  - `/home/wy885/ollama-bin/bin/ollama`
- 已按要求删除无效文件：
  - `/home/wy885/ollama`
- 已验证 `ollama help` 可正常执行，说明二进制可用。
- 已验证临时启动 `ollama serve` 后，本地接口可用：
  - `http://127.0.0.1:11434`
- 已确认当前本地模型包含：
  - `qwen2.5:1.5b`
  - `qwen2.5vl:3b`
- 已确认 `pdfsc` 默认配置 [config/default.yml](D:/usr/百信公司项目/pdfsc/config/default.yml) 指向：
  - `provider: ollama`
  - `base_url: http://localhost:11434/v1`

---

## 三、目前识别出的关键事实

### 1. 项目不是空架子，已进入收口与继续推进阶段

当前 `pdfsc` 已具备较完整的主流程、测试、图片处理和本地模型接入能力，后续工作重点应放在工程稳定性、一致性和阶段推进，而不是重新搭架构。

### 2. WSL 是更适合运行本地模型与部分测试的环境

尤其是涉及：

- Ollama 本地模型
- `localhost:11434` 接口调用
- Linux 风格测试执行

这类工作优先在 WSL 中执行更稳妥。

### 3. Git 提交应优先在 Windows 路径执行

虽然 WSL 能访问同一仓库，但 WSL 侧曾观察到大量 `git status` 伪修改视图；而 Windows 侧仓库状态正常、干净，因此后续分支、暂存、提交、查看变更，优先在 `D:\usr\百信公司项目\pdfsc` 执行。

---

## 四、建议形成的操作分工

### Windows 侧负责

- 编辑代码
- 查看变更
- 暂存与提交
- 分支管理
- 项目文档整理

### WSL 侧负责

- 激活 `.venv_wsl`
- 启动和验证 Ollama
- 运行依赖本地模型的测试
- 运行更适合 Linux 环境的验证命令

---

## 五、接续后建议优先事项

基于当前摸排结果，后续开发建议优先处理以下事项：

1. 修复 Windows / WSL 双环境下的测试执行差异。
2. 修正批量汇总报告使用传统 Markdown 表格的问题，使其符合项目转换规范。
3. 在明确环境边界后，再继续进入下一阶段任务实施。

---

## 六、结论

Codex 已完成接续 Claude 项目工作的主要准备事项，已具备继续承担 `pdfsc` 后续实施任务的基础条件。  
当前最重要的不是重新理解项目目标，而是基于已确认的双环境现状，按既定规范继续推进后续修复与开发。
