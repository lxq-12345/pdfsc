# 阶段B2任务总结 - 两步转换流水线

**任务名称**：第四阶段B2 - 两步转换流水线
**执行日期**：2026-03-14
**执行状态**：✅ 完成
**验收状态**：✅ 通过（离线模式验收）

---

## 一、任务目标

### 来源
`plan/项目规划.md` 第594-615行 - 第四阶段B2任务

### 目标
端到端转换可用，输出raw版和final版

---

## 二、任务清单完成情况

| 任务 | 状态 | 产出 |
|------|------|------|
| 1. 实现忠实还原步骤 | ✅ 完成 | `src/converter.py` - `convert_restore()` |
| 2. 实现中间产物保存 | ✅ 完成 | output/markdown/raw/*_raw.md |
| 3. 实现智能增强步骤 | ✅ 完成 | `src/converter.py` - `convert_enhance()` |
| 4. 实现完整两步流水线 | ✅ 完成 | `src/converter.py` - `convert_full()` |
| 5. Markdown验证模块 | ✅ 完成 | `src/validator.py` (174行) |
| 6. CLI命令完整接线 | ✅ 完成 | `src/pdfsc.py` (370行) |
| 7. 离线模式机制 | ✅ 完成 | 三源开关（配置/环境变量/CLI） |
| 8. 编写验收测试 | ✅ 完成 | `tests/test_stage_b2.py` (161行) |

---

## 三、详细实现说明

### 1. 两步转换流水线（`src/converter.py`）

#### 核心架构

Converter类实现两步转换流水线，核心方法：

| 方法 | 功能 | 状态 |
|------|------|------|
| `convert_restore(pdf_content, metadata)` | 忠实还原：严格对应原文 | ✅ |
| `convert_enhance(restore_md, metadata)` | 智能增强：有据可依的优化 | ✅ |
| `convert_full(pdf_content, metadata)` | 完整两步合并 | ✅ |
| `_call_model(prompt)` | 统一模型调用入口 | ✅ |
| `_is_offline_mode()` | 离线模式检测 | ✅ |
| `_fallback_restore()` | 本地回退：结构化拼接 | ✅ |
| `_fallback_enhance()` | 本地回退：格式层清理 | ✅ |
| `_build_restore_prompt()` | 忠实还原Prompt构建 | ✅ |
| `_build_enhance_prompt()` | 智能增强Prompt构建 | ✅ |
| `_ensure_frontmatter_and_title()` | Frontmatter和一级标题兜底 | ✅ |
| `_extract_text(pdf_content)` | 多格式文本提取 | ✅ |

#### 调用流程

```
convert_full()
  ├── convert_restore()
  │     ├── _build_restore_prompt()
  │     ├── _call_model()  ← 在线模式：调用adapter
  │     │                  ← 离线模式：短路返回None
  │     │                  ← 异常：捕获后返回None
  │     └── _fallback_restore()  ← model返回None时
  └── convert_enhance()
        ├── _build_enhance_prompt()
        ├── _call_model()
        └── _fallback_enhance()
```

#### 离线模式三源开关

| 来源 | 配置路径 | 值 |
|------|---------|-----|
| 配置文件 | `api.offline_mode` | true/false |
| 环境变量 | `PDFSC_OFFLINE` | 1/true/yes/on |
| CLI参数 | `--offline` | flag |

三源取OR，任一为true即启用离线模式。

#### 本地回退策略

**忠实还原回退** (`_fallback_restore`)：
- 拼接Frontmatter + 一级标题 + 文档信息 + 原文内容
- 不做任何内容变换，确保无幻觉

**智能增强回退** (`_fallback_enhance`)：
- 仅做格式层清理（去除多余空行）
- 不新增任何事实内容

---

### 2. Markdown验证模块（`src/validator.py`）

#### MarkdownValidator类

| 方法 | 功能 | 状态 |
|------|------|------|
| `validate(markdown_content)` | 完整验证，返回结构化结果 | ✅ |
| `check_frontmatter()` | 检查Frontmatter存在性和字段完整性 | ✅ |
| `check_title_hierarchy()` | 检查H1唯一性和层级连续性 | ✅ |
| `check_tables()` | 禁止传统Markdown表格 | ✅ |
| `check_semantic_lists()` | 检查语义列表特征 | ✅ |
| `generate_report(result)` | 生成文本格式报告 | ✅ |

#### 评分机制

```
score = 10.0 - 1.5 × 错误数 - 0.5 × 警告数
范围：[0.0, 10.0]
```

#### 验证返回结构

```python
{
    'valid': bool,       # 是否通过（零错误即通过）
    'errors': list,      # 错误列表
    'warnings': list,    # 警告列表
    'score': float,      # 评分
}
```

---

### 3. CLI命令接线（`src/pdfsc.py`）

#### 4个子命令

| 命令 | 功能 | 关键逻辑 |
|------|------|---------|
| `convert` | 单文件转换 | 检测→提取→metadata→两步转换→输出raw/final |
| `convert-batch` | 批量目录转换 | collect_pdf_files + 循环convert_single_pdf |
| `verify` | 格式验证 | MarkdownValidator + 单文件/目录递归 |
| `stats` | 输出统计 | 统计raw/final数量、总大小 |

#### 辅助函数

| 函数 | 功能 |
|------|------|
| `convert_single_pdf()` | 单文件端到端转换，输出raw/final |
| `build_output_basename()` | 按模板生成`序号_简称`格式文件名 |
| `parse_frontmatter()` | YAML解析Frontmatter字符串 |
| `sanitize_filename()` | 正则清除非法字符 |
| `collect_pdf_files()` | 按模式收集PDF文件列表 |
| `maybe_apply_capability_guard()` | 模型能力检测与视觉自动降级 |

---

## 四、测试验证

### B2验收测试（3/3通过）

| 测试 | 内容 | 结果 |
|------|------|------|
| test_converter_restore_and_full | restore/enhance/full输出结构 | ✅ |
| test_validator | 正例通过 + 反例（传统表格）拒绝 | ✅ |
| test_output_naming | `03_TaiShan_200_快速安装指南_(型号2280)` | ✅ |

### 回归测试（11/11通过）

| 阶段 | 测试数 | 结果 |
|------|--------|------|
| B2 | 3 | ✅ |
| B1 | 4 | ✅ |
| A1 | 4 | ✅ |
| **合计** | **11** | **✅ 零回归** |

---

## 五、关键设计决策

### 决策1：离线模式而非Mock模式

**背景**：API Key暂时不可用（401/403）
**选择**：引入完整离线模式机制（配置+环境变量+CLI三源开关）
**原因**：
- 比简单mock更接近生产行为
- 上层代码路径与在线模式完全一致
- 用户可在生产环境中主动使用离线模式

### 决策2：转换回退采用保守策略

**背景**：离线模式无法调用AI模型
**选择**：忠实还原仅做结构化拼接，智能增强仅做格式清理
**原因**：
- 保守回退确保零幻觉，符合Step0-4防幻觉要求
- 在线模式恢复后，由Prompt驱动更高质量输出

### 决策3：端到端转换链集成到CLI

**背景**：B2需要"端到端转换可用"
**选择**：在pdfsc.py中实现完整的检测→提取→metadata→转换→输出链
**原因**：
- 验证模块间串联无断裂
- 用户可直接使用CLI执行转换

---

## 六、遗留与后续

| 编号 | 事项 | 优先级 | 关联阶段 |
|------|------|--------|---------|
| 1 | API Key激活后在线模式联网质量验证 | 中 | - |
| 2 | 添加真实PDF测试文件到sample_pdfs/ | 中 | 阶段C |
| 3 | 增强规则正式定义（enhance Prompt细化） | 高 | 阶段C |
| 4 | 图片处理流程集成（vision.py + image_handler.py） | 中 | 后续阶段 |

---

## 七、阶段B2完整文件变动

### 新增
- `src/converter.py` — 两步转换流水线（186行）
- `src/validator.py` — Markdown验证器（174行）
- `tests/test_stage_b2.py` — B2验收测试（161行）

### 更新
- `src/pdfsc.py` — CLI完整接线（125行→370行，+245行）
- `src/config.py` — set()/get_api_config()/offline映射
- `config/default.yml` — api.offline_mode配置项
