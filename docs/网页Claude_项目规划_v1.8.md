# PDF智转器（pdf-smart-converter）项目规划文档

**文档版本**: 1.8  
**创建日期**: 2026-03-08  
**状态**: 待审批  
**作者**: 项目规划（网页Claude协作）

---

## 一、项目概述

### 1.1 项目背景

原有`tools`工具集是为处理华为TaiShan-200服务器资料而开发的项目特定实现，存在路径硬编码、无法跨项目复用、缺少文档等严重局限。

阶段一至三已手工完成21个PDF文件的转换，质量评分9.7/10，积累了宝贵的转换经验和高质量的参照样本。现需将这一经验沉淀为**可复用的智能工具**。

### 1.2 项目定位

PDF智转器是一个**AI辅助的智能PDF转Markdown转换工具**，核心特征是：

- 不是简单的格式转换脚本，而是具备语义理解能力的智能流水线
- 以Claude API为核心AI引擎，结合脚本层处理机械性工作
- 输出符合《Markdown转换规范v1.1》的高质量知识库文档

### 1.3 项目名称

- **中文名**：PDF智转器
- **英文ID**：pdf-smart-converter
- **命令行工具名**：pdfsc

### 1.4 验收基准

用工具重新处理21个TaiShan-200 PDF文件，输出质量须达到或超过已完成的Markdown文件标准（≥9.7/10）。已完成的21个Markdown文件同时作为：

- **开发期**：测试集和质量对比基准
- **完成后**：工具可复用性的证明

---

## 二、项目文件结构

```
pdfsc/
├── CLAUDE.md                         # Claude Code项目入口（自动读取）
├── CHECKPOINT_PROTOCOL.md            # 会话检查点安全协议
├── requirements.txt                  # Python依赖声明
├── docker-compose.yml                # Ollama本地大模型容器配置
├── README.md                         # 项目概述（阶段E完成后生成）
│
├── scripts/                          # Shell脚本目录
│   ├── run.sh                        # 启动程序
│   ├── test.sh                       # 运行测试
│   ├── install.sh                    # 安装依赖
│   └── validate.sh                   # 验证输出质量
│
├── src/                              # 所有Python源代码
│   ├── pdfsc.py                      # CLI入口
│   ├── detector.py                   # PDF类型检测
│   ├── extractor.py                  # 文字提取（pdfplumber）
│   ├── vision.py                     # 图片提取和视觉处理（PyMuPDF）
│   ├── converter.py                  # 两步转换流水线
│   ├── model_adapter.py              # 多模型适配层
│   ├── image_handler.py              # 图片命名、保存、插入
│   ├── validator.py                  # 输出格式验证
│   └── config.py                     # 配置管理
│
├── skills/                           # AI行为规范（AI的"宪法"）
│   └── markdown_conversion.md        # Markdown转换规范
│
├── prompts/                          # AI执行提示词
│   ├── restore.md                    # 忠实还原提示词
│   ├── enhance.md                    # 智能增强提示词
│   └── examples/                     # 示例文件体系
│       ├── table_level1.md           # 第一层次示例（2维）
│       ├── table_level2.md           # 第二层次示例（3维）
│       ├── table_level3.md           # 第三层次示例（4维+）
│       ├── table_selection.md        # 层次判断规则
│       └── images/                   # 示例截图
│
├── config/                           # 工具行为配置
│   ├── config.yml                    # 用户配置文件
│   ├── config.example.yml            # 完整配置示例（含注释）
│   ├── default.yml                   # 默认配置（内置）
│   └── model_capabilities.yml        # 模型能力注册表（内置）
│
├── plan/                             # 项目规划文档
│   ├── 项目规划.md                    # 完整技术方案
│   └── 项目记忆文档.md                # 决策背景和约束
│
├── mem/                              # 项目备忘日志
│   └── pdf-smart-converter_备忘_YYYY-MM-DD.md
│
├── output/                           # 转换输出和验收文件
│   ├── markdown/
│   │   ├── raw/                      # 忠实还原版
│   │   └── final/                    # 智能增强版
│   └── reports/                      # 质量检查验收报告
│       ├── validation_report.md
│       ├── quality_report.md
│       └── stage_review.md
│
└── tests/                            # 测试素材和基准
    ├── sample_pdfs/                  # 测试用PDF样本
    ├── test_cases/                   # 各瓶颈验证测试案例文件
    │   ├── bottleneck1/              # 瓶颈1：表格语义转换
    │   ├── bottleneck2/              # 瓶颈2：扫描型PDF视觉理解
    │   ├── bottleneck3/              # 瓶颈3：图片语义位置插入
    │   ├── bottleneck4/              # 瓶颈4：防幻觉边界控制
    │   ├── bottleneck5/              # 瓶颈5：Ollama本地模型质量
    │   └── bottleneck6/              # 瓶颈6：多模型适配兼容性
    └── expected_outputs/             # 期望输出（来自21个已完成文件）
```

---

## 三、核心设计原则

### 2.1 两步转换策略

转换过程严格分为两步，不可合并：

```
第一步：忠实还原
PDF原文 → 完整提取（含图片理解）→ 严格对应原文的Markdown
（不增加任何原文没有的内容）

第二步：智能增强
忠实还原版 → 有据可依的补充和扩展 → 最终高质量Markdown
```

**两步分离的价值**：
- 忠实还原版作为"事实锚点"，防止增强步骤产生幻觉
- 中间产物可保存，便于质量追溯和问题定位
- 灵活适配不同场景需求（存档用还原版，知识库用增强版）

### 2.2 防幻觉三等级约束

智能增强步骤的内容必须遵守以下约束：

| 等级 | 内容类型 | 规则 |
|------|---------|------|
| 等级1（允许） | 格式重组、表达优化、步骤补全 | 自由增强，属于理解原文后的表达 |
| 等级2（谨慎） | 跨文档引用、技术参数补充 | 必须来自同批次其他PDF，须标注来源 |
| 等级3（禁止） | 原文和其他PDF均无依据的内容 | 绝对禁止，提示词层面强制约束 |

### 2.3 图片处理模式（可配置）

图片处理作为独立配置选项，用户根据使用场景灵活选择，默认不提取图片。

#### 三种图片模式

**模式一：disabled（默认）**
完全忽略图片，输出纯文字Markdown。
适用场景：知识库RAG用途、快速批量处理、纯文字型PDF。

**模式二：description-only（推荐过渡方案）**
不保存图片文件，但Claude理解图片内容后在对应位置插入文字描述。
适用场景：需要图片信息但不需要图片文件、降低存储开销。

```markdown
<!-- 示例输出 -->
> **📷 图示**：服务器推入机柜示意图，显示服务器从正面水平推入
> 机柜滑道，挂耳与机柜方孔条对齐的安装位置关系。
```

**模式三：extract（完整图片）**
从PDF提取图片文件，保存至`images/`目录，在Markdown正确位置插入引用。
适用场景：文档归档、需要完整还原原始文档、图文并茂的安装指南。

```markdown
<!-- 示例输出 -->
![服务器推入机柜示意图](./images/02_安装步骤_01.png)
```

#### 图片过滤规则（extract模式）

- 忽略宽度小于100px的装饰性小图（图标、分隔符等）
- 忽略纯色背景图和水印
- 保留安装示意图、接口图、流程图等有实质内容的图片

#### 图片命名规范（extract模式）

```
{文档序号}_{内容描述}_{编号}.png
示例：
02_安装步骤_01.png
02_前面板接口图_01.png
02_指示灯说明_01.png
```

---

## 四、系统架构

### 3.1 整体架构

```
输入：PDF文件
  ↓
┌─────────────────────────────────────┐
│              脚本层                  │
│  PDF类型判断 → 文字提取 → 图片提取   │
└─────────────────────────────────────┘
  ↓
┌─────────────────────────────────────┐
│         AI层（多模型适配）            │
│  Claude / GPT-4o / Qwen / Ollama   │
│                                     │
│  [能力检测]  确认模型是否支持视觉    │
│  [视觉理解]  页面图像 → 内容语义     │
│  [信息融合]  文字+图片+版面 → 整合   │
│  [忠实还原]  整合信息 → 还原版MD     │
│  [智能增强]  还原版MD → 最终MD       │
└─────────────────────────────────────┘
  ↓
┌─────────────────────────────────────┐
│              脚本层                  │
│  格式验证 → 图片整理 → 文件输出      │
└─────────────────────────────────────┘
  ↓
输出：Markdown文件 + images/目录
```

### 3.2 PDF类型适配

工具自动识别PDF类型并选择处理路径：

```
PDF文件
  ↓ 类型检测
  ├→ 纯文字型    → 直接文字提取 → AI处理
  ├→ 图文混合型  → 文字提取 + pdf2image → AI视觉+文字双路处理
  └→ 扫描型      → pdf2image全页 → AI视觉理解（主要依赖）
```

### 3.3 图片处理流程（按模式）

```
PDF页面遇到图片
  ↓ 读取配置：image_mode
  ├→ disabled
  │     忽略图片，继续处理文字
  │
  ├→ description-only
  │     [Claude] 理解图片语义
  │     ↓ 在Markdown对应位置插入文字描述块
  │     > **📷 图示**：[Claude生成的图片描述]
  │
  └→ extract
        [PyMuPDF] 识别图片位置和区域
        [PyMuPDF] 裁剪提取图片文件
        [Claude]  理解图片语义，生成alt文本
        ↓ 按规范命名并保存至 images/ 目录
        ↓ 在Markdown正确位置插入：
          ![图片描述](./images/02_安装步骤_01.png)
```

### 3.4 输出目录结构

```
output/
├── 02_TaiShan200_快速安装指南_型号2280.md     # 最终增强版
├── 02_TaiShan200_快速安装指南_型号2280_raw.md  # 忠实还原版（中间产物）
└── images/                                    # 仅extract模式生成
    ├── 02_安装步骤_01.png
    ├── 02_前面板接口图_01.png
    └── 02_指示灯说明_01.png
```

---

## 五、技术选型

### 4.1 核心依赖

| 组件 | 技术选型 | 用途 | 理由 |
|------|---------|------|------|
| AI引擎 | 多模型适配层 | 语义理解、内容转换 | 支持Claude/GPT-4o/Qwen/Ollama |
| PDF文字提取 | pdfplumber | 结构化文字和表格提取 | 已在原工具集验证 |
| PDF转图片 | pdf2image / PyMuPDF | 页面渲染、图片提取 | 成熟稳定，支持高分辨率 |
| CLI框架 | argparse | 命令行参数 | Python标准库，无额外依赖 |
| 配置管理 | YAML（.yml） | 所有配置项管理 | 支持嵌套结构和列表，INI无法满足 |
| 格式验证 | 自研脚本 | 输出Markdown验证 | 基于现有verify_markdown.js改造 |

### 4.2 多模型支持架构

工具通过统一适配层支持多家大模型，用户只需修改配置文件即可切换：

```
用户配置选择模型
       ↓
  模型适配层（统一接口）
  ├→ AnthropicAdapter   → Claude Sonnet / Opus
  ├→ OpenAIAdapter      → GPT-4o / GPT-4o-mini
  ├→ QwenAdapter        → Qwen-VL-Max / Qwen-Max
  └→ OllamaAdapter      → qwen2.5-vl / llama3.2-vision（本地）
       ↓
  统一调用接口：convert(text, images) → markdown
```

**Ollama本地化部署说明**：Ollama原生兼容OpenAI接口格式，复用OpenAI适配器，仅需将`base_url`指向本地地址，无需API Key，数据完全不经过外部网络。

### 4.3 模型能力注册表

工具内置模型能力注册表，启动时自动查表判断当前模型是否支持视觉：

```yaml
# model_capabilities.yml（内置，随工具发布）

anthropic:
  claude-sonnet-4-5: { vision: true,  chinese: true  }
  claude-opus-4-5:   { vision: true,  chinese: true  }

openai:
  gpt-4o:            { vision: true,  chinese: true  }
  gpt-4o-mini:       { vision: true,  chinese: true  }

qwen:
  qwen-vl-max:       { vision: true,  chinese: true  }
  qwen-max:          { vision: false, chinese: true  }

ollama:
  qwen2.5-vl:        { vision: true,  chinese: true  }
  qwen2.5:           { vision: false, chinese: true  }
  llama3.2-vision:   { vision: true,  chinese: false }
  llama3.1:          { vision: false, chinese: false }
```

### 4.4 模型能力自动降级

当模型不支持视觉时，工具自动降级并给出明确提示，不报错崩溃：

```
启动转换
  ↓ 查询模型能力注册表
  ├→ 支持视觉 → 按用户配置的image_mode执行
  └→ 不支持视觉
        强制 image_mode = disabled
        输出警告：
        ⚠️  当前模型 qwen2.5 不支持视觉（多模态）
            图片模式已自动切换为：disabled
            如需图片支持，推荐切换至：
            - Ollama: qwen2.5-vl
            - Claude: claude-sonnet-4-5
        ▶  继续以纯文字模式转换...
```

**未知模型的处理**：注册表中没有的模型，默认假设不支持视觉（保守降级），避免因错误假设导致崩溃。

### 4.5 API调用策略

- 每个PDF按页面分块处理，避免超出上下文窗口
- 图文混合页面：图片和文字同时输入，一次调用获取完整理解
- 忠实还原和智能增强分两次独立API调用
- 保留每次调用的中间结果，便于调试和质量追溯

---

## 六、配置文件规范

### 5.1 配置格式

配置文件统一采用**YAML（.yml）格式**。选择理由：支持任意层级嵌套、原生列表和布尔类型、注释友好；INI格式仅支持两层结构，无法表达本项目所需的复杂配置。

### 5.2 完整配置文件示例

```yaml
# pdf-smart-converter/config/config.yml
# PDF智转器完整配置文件
# 复制此文件并按需修改，使用 --config 参数指定

# ─────────────────────────────────────
# 1. 路径配置
# ─────────────────────────────────────
paths:
  project_root: ./                    # 项目根路径
  input_pdf: ./pdfs/                  # 原始PDF文件路径
  output_md: ./output/                # 生成MD文档路径
  log_file: ./logs/pdfsc.log          # 日志文件路径

# ─────────────────────────────────────
# 2. 日志配置
# ─────────────────────────────────────
logging:
  enabled: true                       # 日志开关（true/false）
  level: INFO                         # DEBUG / INFO / WARNING / ERROR
  console_output: true                # 是否同时输出到控制台

# ─────────────────────────────────────
# 3. 图片处理配置
# ─────────────────────────────────────
images:
  mode: disabled                      # disabled / description-only / extract
  min_width: 100                      # extract模式：忽略低于此宽度的小图（px）
  formats: [png, jpg]                 # extract模式：支持的图片格式

# ─────────────────────────────────────
# 4. 转换配置
# ─────────────────────────────────────
conversion:
  mode: full                          # full / restore-only / enhance-only
  save_intermediate: true             # 是否保留忠实还原版中间产物
  language: auto                      # auto / zh / en

# ─────────────────────────────────────
# 5. AI模型配置
# ─────────────────────────────────────
api:
  provider: anthropic                 # anthropic / openai / qwen / ollama
  model: claude-sonnet-4-5            # 模型名称
  key_env: ANTHROPIC_API_KEY          # API Key环境变量名（本地模型留空）
  base_url:                           # 留空使用默认；Ollama填 http://localhost:11434/v1
  max_retries: 3                      # 最大重试次数
  timeout: 120                        # 超时时间（秒）
  unknown_model_vision: false         # 未知模型是否假设支持视觉（保守降级）

  # 按PDF类型指定不同模型（可选）
  type_overrides:
    text_only:                        # 纯文字型，可用轻量模型
      provider: ollama
      model: qwen2.5
      base_url: http://localhost:11434/v1
    scanned:                          # 扫描型，用视觉最强的模型
      provider: anthropic
      model: claude-sonnet-4-5
      key_env: ANTHROPIC_API_KEY

# ─────────────────────────────────────
# 6. 批量处理配置
# ─────────────────────────────────────
batch:
  recursive: false                    # 是否递归处理子目录
  file_pattern: "*.pdf"              # 文件名过滤规则
  overwrite_existing: false           # 是否覆盖已存在的输出文件

# ─────────────────────────────────────
# 7. 输出命名配置
# ─────────────────────────────────────
naming:
  template: "{index}_{title}.md"     # 命名模板
  index_start: 1                     # 序号起始值
  index_digits: 2                    # 序号位数（2→01, 3→001）

# ─────────────────────────────────────
# 8. 质量控制配置
# ─────────────────────────────────────
quality:
  auto_validate: true                 # 是否自动运行格式验证
  on_failure: warn                    # warn（警告继续）/ stop（报错停止）
```

### 5.3 配置优先级

```
命令行参数  >  用户配置文件  >  默认配置文件（default.yml）
```

命令行参数始终优先，方便临时覆盖配置文件中的设置。

### 5.4 提示词管理

提示词内容**不放入配置文件**，单独用`.md`文件管理，便于频繁调整和版本控制：

```
prompts/
├── restore.md    # 忠实还原提示词
└── enhance.md    # 智能增强提示词
```

---

## 七、开发阶段规划

### 阶段A：基础框架（第1-2天）

**目标**：建立项目骨架，实现PDF文字提取和基本转换

**任务清单**：

1. 创建项目目录结构
2. 编写`requirements.txt`（所有Python依赖）
3. 实现PDF类型自动检测模块
4. 实现纯文字型PDF提取（基于pdfplumber）
5. 实现基础CLI入口（`pdfsc convert input.pdf`）
6. 实现Frontmatter元数据生成

**阶段A产出**：可处理纯文字型PDF的基础版本

---

### 阶段B：AI核心（第3-4天）

**目标**：接入Claude API，实现两步转换流水线

**任务清单**：

1. 实现Claude API调用模块（含错误重试）
2. 编写忠实还原提示词（含防幻觉约束）
3. 编写智能增强提示词（含三等级约束）
4. 实现两步转换流水线
5. 实现中间产物（还原版）的保存和管理
6. 实现API调用成本统计和日志

**阶段B产出**：核心AI转换能力就绪，可处理文字型PDF

---

### 阶段C：视觉理解（第5-6天）

**目标**：支持图文混合型和扫描型PDF

**任务清单**：

1. 集成pdf2image / PyMuPDF
2. 实现PDF页面转图片
3. 实现图片区域识别和裁剪提取
4. 实现图片语义命名（Claude生成描述）
5. 实现图片在Markdown中的正确位置插入
6. 实现images/目录管理

**阶段C产出**：支持所有三类PDF，图片完整保留

---

### 阶段D：质量验证（第7天）

**目标**：用21个TaiShan-200 PDF验证工具质量

**任务清单**：

1. 批量处理21个PDF文件
2. 与已完成的21个Markdown进行对比评分
3. 记录差异和问题
4. 针对性优化提示词
5. 再次验证，确认质量达标（≥9.7/10）

**阶段D产出**：质量验证报告，工具达到验收标准

---

### 阶段E：文档和打包（第8天）

**目标**：完整文档，工具可独立发布

**任务清单**：

1. 编写README.md（项目概述、快速开始）
2. 编写INSTALLATION.md（安装步骤）
3. 编写USAGE.md（完整使用说明）
4. 编写CONFIG.md（配置文件说明）
5. 编写ARCHITECTURE.md（架构说明）

**阶段E产出**：完整文档，工具可交付使用

---

## 八、CLI使用规范

### 基本用法

```bash
# 转换单个PDF（默认：不提取图片）
pdfsc convert input.pdf --output ./output/

# 使用description-only模式（图片转文字描述）
pdfsc convert input.pdf --image-mode description-only

# 使用extract模式（完整提取图片）
pdfsc convert input.pdf --image-mode extract

# 批量转换目录下所有PDF
pdfsc convert-batch ./pdfs/ --output ./output/

# 只生成忠实还原版（不做增强）
pdfsc convert input.pdf --mode restore-only

# 验证已生成的Markdown
pdfsc verify output.md

# 查看转换统计
pdfsc stats ./output/
```

### 参数说明

```bash
pdfsc convert <input.pdf>
  --output <dir>          输出目录（默认：./output）
  --mode <mode>           转换模式：full（默认）/ restore-only / enhance-only
  --image-mode <mode>     图片模式：disabled（默认）/ description-only / extract
  --config <file>         配置文件路径
  --title <title>         文档标题（覆盖自动提取）
  --category <cat>        文档分类
  --verbose               显示详细处理日志
```

### 配置文件示例

```yaml
# default.yaml

# 图片处理配置
images:
  mode: disabled            # disabled / description-only / extract
  min_width: 100            # extract模式：忽略低于此宽度的装饰性小图（px）
  formats: [png, jpg]       # extract模式：支持的图片格式

# 转换配置
conversion:
  mode: full                # full / restore-only / enhance-only
  save_intermediate: true   # 是否保留忠实还原版中间产物

# 输出配置
output:
  dir: ./output
  naming: "{index}_{title}.md"
```

---

## 九、技术瓶颈验证任务

每个瓶颈对应一个独立验证任务（Step），在正式开发阶段前逐一完成。  
每个任务的详细方案待实施前再细化，此处只做框架占位。

**测试案例文件来源**：从 `pdf_to_kbase/` 项目的原始PDF和已完成MD文件中剪裁制作，届时与用户沟通确定具体片段。

---

### 9.1 瓶颈风险评估总览

| 瓶颈 | 风险等级 | 验证状态 | 说明 |
|------|---------|---------|------|
| 瓶颈1：表格语义转换质量 | 🔴 最高 | 待验证 | 核心需求，直接决定工具价值 |
| 瓶颈2：扫描型PDF视觉理解 | 🟢 低 | 已验证 | Claude统一视觉理解，无需区分类型 |
| 瓶颈3：图片语义位置插入 | 🟢 低 | 已降级 | Claude多模态理解图文关系，剩余是工程问题 |
| 瓶颈4：边界控制（防幻觉） | 🟡 中 | 待验证 | 四层保障体系，人工复查兜底 |
| 瓶颈5：Ollama本地模型质量 | 🟡 中 | 待验证 | 实操时验证，不影响主线开发 |
| 瓶颈6：多模型适配兼容性 | 🟢 低 | 可控 | 已知工程问题，逐个适配 |

---

### 9.2 Step0-1：瓶颈1验证任务（阶段A前必须完成）

```
验证目标：
  确认表格语义转换提示词效果稳定达标

测试案例文件：
  tests/test_cases/bottleneck1/
  → 覆盖三个层次的典型表格（待从pdf_to_kbase剪裁制作）

验证方案：待细化

通过标准：
  三个层次表格转换质量均≥9.7分，连续3次稳定

失败处理：
  调整提示词和示例文件后重新验证
  <8.0分则暂停，向用户报告，重新讨论方案
```

---

### 9.3 Step0-2：瓶颈2验证任务（已验证，记录结论）

```
验证目标：
  确认Claude可统一处理文字型和扫描型PDF

验证结论（已完成）：
  TaiShan 200快速安装指南PDF实测通过
  Claude直接视觉理解，无需区分PDF类型
  中文技术术语、特殊符号、图文混排全部正确识别

对架构的影响：
  PDF类型检测模块可大幅简化
  统一用视觉理解方式处理所有PDF

测试案例文件：
  tests/test_cases/bottleneck2/（已有实测结果，归档备查）
```

---

### 9.4 Step0-3：瓶颈3验证任务（已降级为工程问题）

```
验证目标：
  确认图片语义位置插入的正确性

验证结论（已降级）：
  Claude多模态直接理解图片与周边文字的语义关系
  位置判断不是技术难题
  剩余挑战是工程实现（提取→命名→保存→插入路径）

测试案例文件：
  tests/test_cases/bottleneck3/（待从pdf_to_kbase剪裁制作）

验证时机：阶段C图片处理开发完成后验证
```

---

### 9.5 Step0-4：瓶颈4验证任务

```
验证目标：
  确认防幻觉四层保障体系有效
  还原版与原PDF内容100%对应
  增强版无等级3幻觉内容

测试案例文件：
  tests/test_cases/bottleneck4/（待从pdf_to_kbase剪裁制作）
  → 选择有扩展风险的片段（工具说明、参数描述等）

验证方案：待细化

通过标准：
  还原版与原文内容100%对应
  增强版无原文依据之外的技术参数

失败处理：
  调整提示词约束后重新验证
  暂停向用户报告
```

---

### 9.6 Step0-5：瓶颈5验证任务

```
验证目标：
  确认Ollama本地模型（qwen2.5-vl）的中文转换质量

测试案例文件：
  tests/test_cases/bottleneck5/（与瓶颈1共用测试案例）

验证方案：待细化（换模型时执行）

通过标准：
  ≥9.0分：本地模型可用于日常处理
  8.0-9.0分：需增强提示词后使用
  <8.0分：不推荐，建议使用云端模型

验证时机：阶段B完成后，切换Ollama模型时执行
```

---

### 9.7 Step0-6：瓶颈6验证任务

```
验证目标：
  确认多模型适配层切换模型时行为正常

测试案例文件：
  tests/test_cases/bottleneck6/（API调用格式测试用例）

验证方案：待细化

通过标准：
  切换模型时输出格式一致
  图片输入格式适配正确
  错误处理正常

验证时机：每新增一个模型适配器时执行
```

---

### 9.8 表格转换三层次（维度模型）

判断层次只需数维度：

| 维度数 | 层次 | 典型表格 |
|--------|------|---------|
| 2维（键+值） | 第一层次 | 符号说明、术语解释 |
| 3维（主分类+键+值） | 第二层次 | 故障排查（现象+原因+解决方案） |
| 4维+（主实体+多属性） | 第三层次 | 规格参数（型号+多个属性） |

---

### 9.9 防幻觉四层质量保障体系

```
第一层：提示词约束（预防）
  → 禁止常识性补充，只用原文材料
  → 输出前检查清单自检

第二层：两步分离（架构保护）
  → 还原版作为事实锚点
  → 增强步骤只能在锚点基础上扩展

第三层：自动检测（发现数字幻觉）
  → 对比两版本数字差异，新增数字触发警告

第四层：人工复查（最终保障）
  → AI存在指令遵循不稳定性，会偶尔"打盹"
  → 人工复查是不可替代的最后防线
  → 对比两版本，只审查增强版新增部分
```

---

## 十、验收标准

### 功能验收

- ✅ 支持三类PDF（文字型、图文混合型、扫描型）
- ✅ 两步转换流水线正常运行
- ✅ 图片正确提取、命名、插入Markdown
- ✅ 输出Frontmatter完整规范
- ✅ 批量处理命令可用

### 质量验收

- ✅ 21个TaiShan-200 PDF重新处理，输出质量≥9.7/10
- ✅ 无明显幻觉内容（无依据的技术参数或步骤）
- ✅ 表格100%转换为语义列表完整句式
- ✅ 图片在Markdown中位置语义正确

### 规范验收

- ✅ 输出完全符合《Markdown转换规范v1.1》
- ✅ 文件命名符合规范（{序号}_{简称}.md）
- ✅ 图片命名符合规范（{序号}_{描述}_{编号}.png）

### 工程验收

- ✅ 依赖声明完整（requirements.txt）
- ✅ 文档完整（README / INSTALLATION / USAGE）
- ✅ 命令行参数支持完整
- ✅ 错误处理和日志记录完善

---

## 十一、风险管理

| 风险 | 概率 | 影响 | 缓解策略 |
|------|------|------|---------|
| 模型视觉理解质量不稳定 | 中 | 高 | 能力注册表+自动降级，扫描型可指定最强模型 |
| 图片提取位置识别不准确 | 中 | 中 | 人工抽查验证，图片位置可手动调整 |
| 智能增强产生幻觉内容 | 低 | 高 | 三等级约束+还原版对比审查 |
| API调用成本超预期 | 低 | 低 | 21个文件规模可控；可切换Ollama本地模型零成本 |
| 扫描型PDF质量过低 | 低 | 中 | 预处理图像增强，或标记为人工处理 |
| Ollama本地模型中文质量不足 | 中 | 中 | 推荐qwen2.5-vl；复杂文档可切换云端模型 |

---

## 十二、后续升级路径

本工具完成后，具备向知识库集成升级的条件：

```
当前版本（PDF→Markdown）
  ↓ 升级
知识库版本（Markdown→向量知识库）
  新增：文档分块策略
  新增：Embedding生成
  新增：向量数据库写入
  架构：AI层扩展，脚本层增加向量化模块
```

两步走架构天然支持这一升级，无需推倒重来。

---

## 十三、版本管理规范

### 13.1 git 初始化

```
时机：项目目录创建后，阶段A开始前立即执行
命令：
  cd pdfsc/
  git init
  git add .
  git commit -m "[初始化] 项目结构创建完毕"
```

### 13.2 分支策略

```
main          → 稳定版本，每个阶段验收通过后合并
dev           → 日常开发分支
feature/阶段A → 阶段A功能分支
feature/阶段B → 阶段B功能分支
...

工作流程：
  从 dev 创建 feature/阶段X
    ↓
  阶段开发完成，验收通过
    ↓
  合并到 dev
    ↓
  重大里程碑（如阶段D验收通过）合并到 main，打 tag
```

### 13.3 提交规范

```
提交时机：
  每个功能模块完成后
  每个阶段验收通过后
  任何重要决策落地后

提交信息格式：
  [阶段X] 简短描述

示例：
  [初始化] 项目结构创建完毕
  [阶段A] PDF类型检测模块完成
  [阶段A] CLI入口和配置加载完成
  [阶段A] 阶段A验收通过
  [阶段B] Claude API调用模块完成
  [阶段B] 两步转换流水线完成
```

### 13.4 .gitignore 清单

```
# API Key和敏感配置（重要！不能提交）
config/config.yml

# 转换输出（不提交）
output/

# Python缓存
__pycache__/
*.pyc
*.pyo
*.pyd
.Python

# 虚拟环境
venv/
.venv/
env/

# 环境变量
.env
.env.local

# 系统文件
.DS_Store
Thumbs.db

# IDE文件
.vscode/
.idea/

# 日志文件
*.log
logs/

# 测试输出
.pytest_cache/
```

### 13.5 特别说明：config.yml 保护

```
config.yml 含 API Key，绝对不能提交到 git。

正确做法：
  config/config.example.yml  → 提交（模板，无敏感信息）
  config/config.yml          → 加入 .gitignore，永远不提交

用户使用流程：
  复制 config.example.yml → config.yml
  填入自己的 API Key
  开始使用
```

### 13.6 版本 tag 规范

```
打 tag 时机：
  阶段D验收通过（核心功能完整）→ v0.9.0
  阶段E完成（文档齐全）        → v1.0.0
  后续功能升级                 → v1.x.0

命令：
  git tag -a v1.0.0 -m "PDF智转器 v1.0.0 正式版"
```

---

## 十四、环境准备与前置条件

### 14.1 运行环境

```
操作系统：
  Linux    → 原生支持，推荐
  macOS    → 原生支持，推荐
  Windows  → 需要 WSL2（Ubuntu 20.04+）

Python版本：3.10+
Docker版本：20.10+

硬件要求：
  内存：≥8GB（使用云端模型）
        ≥16GB（使用本地Ollama模型）
  磁盘：≥10GB（含模型文件）
```

### 14.2 Windows 环境说明

```
工作方式（已在 pdf_to_kbase 项目验证）：
  用户：在 VS Code 中配置 WSL 终端（一次性，已完成）
  本地 Claude Code：在 WSL 环境内完成所有配置和操作
  用户：无需直接进入 WSL 手动操作

WSL 前提条件：
  Windows 10（版本2004+）或 Windows 11
  已启用 WSL2
  已安装 Ubuntu 20.04+
  VS Code 已配置 WSL 终端
  Docker Desktop 已开启 WSL2 后端
```

### 14.3 前置条件（开始前需准备）

**云端模型（必须）**：
```
Anthropic API Key
  → 访问 console.anthropic.com 申请
  → 填入 config/config.yml 的 api.key 字段
```

**本地模型（可选）**：
```
Docker 已安装并运行
Ollama 镜像通过 docker-compose.yml 自动拉取
qwen2.5-vl 模型通过 docker-compose.yml 自动下载
```

### 14.4 本地 Claude Code 负责的环境配置

```
以下由本地 Claude Code 在 WSL 环境内自动完成：
  Python 虚拟环境创建
  scripts/install.sh 安装所有 Python 依赖
  docker-compose up 启动 Ollama 容器
  项目目录结构初始化
  git 初始化
```

---

## 修订历史

| 版本 | 日期 | 内容 | 作者 |
|------|------|------|------|
| 1.8 | 2026-03-10 | 新增第十四章：环境准备与前置条件（运行环境、Windows/WSL说明、前置条件、Claude负责的配置） | 网页Claude |
| 1.7 | 2026-03-10 | 第九章重构为六个瓶颈验证任务框架，新增tests/test_cases/目录 | 网页Claude |
| 1.6 | 2026-03-10 | 新增第十三章：版本管理规范 | 网页Claude |
| 1.5 | 2026-03-10 | 目录结构重构：删除冗余文档、pdfsc.py移入src/、新增scripts/、docker-compose.yml、CHECKPOINT_PROTOCOL.md、plan/、mem/、output/ | 网页Claude |
| 1.4 | 2026-03-10 | 项目文件结构章节移至第二章，目录名改为pdfsc | 网页Claude |
| 1.3 | 2026-03-08 | 新增技术瓶颈优先验证章节、表格维度模型、防幻觉四层保障体系 | 网页Claude |
| 1.2 | 2026-03-08 | 新增多模型支持、模型能力自动降级、完整YAML配置规范 | 网页Claude |
| 1.1 | 2026-03-08 | 新增图片处理三模式配置（disabled/description-only/extract） | 网页Claude |
| 1.0 | 2026-03-08 | 初版规划文档 | 网页Claude（与用户协作讨论后形成） |

---

**规划完成日期**: 2026-03-08  
**下一步**: 提交本地Claude Code审阅，开始阶段A实施
