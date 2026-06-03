---
name: AI Agent提示词分析器
description: 深度解析AI提示词结构，多维度评分，一键生成优化建议和标准模板。输入你的prompt，输出结构分析+评分+优化版+改进建议，让提示词从模糊变精准。
version: "1.0.0"
updated_at: "2026-06-03"
category: ["AI工具", "开发工具"]
tags: ["提示词", "Prompt", "AI优化", "Agent", "提示词工程"]
trigger: ["分析提示词", "优化prompt", "提示词评分", "prompt分析", "AI提示词", "提示词优化"]
---

# AI Agent提示词分析器

> 不是阅读文档，是分析工具。输入你的AI提示词，输出结构拆解、多维评分、优化建议和标准模板。

## 核心能力

1. **结构解析** — 输入prompt → 输出角色/任务/约束/示例/格式五大模块拆解
2. **多维度评分** — 清晰度/完整性/一致性/可执行性/鲁棒性 五维打分，满分100
3. **一键优化** — 输入原始prompt → 输出优化版prompt + 具体改进建议
4. **模板生成** — 按场景（对话/分析/创作/编程/Agent）生成标准prompt模板

---

## 快速开始

### 流程1：分析提示词结构

用户说："分析一下这个提示词" 或 "帮我看看这个prompt"

```bash
python scripts/analyze.py --input '{"prompt": "你是一个专业的文案写手，帮我写一篇关于AI的文章"}'
```

输出示例：
```json
{
  "status": "ok",
  "structure": {
    "role": {"found": true, "content": "专业的文案写手", "completeness": "basic"},
    "task": {"found": true, "content": "写一篇关于AI的文章", "completeness": "low"},
    "constraints": {"found": false, "content": null, "completeness": "missing"},
    "examples": {"found": false, "content": null, "completeness": "missing"},
    "format": {"found": false, "content": null, "completeness": "missing"}
  },
  "stats": {
    "total_chars": 23,
    "has_chinese": true,
    "has_english": true,
    "sentence_count": 1,
    "structure_score": 20
  },
  "summary": "仅包含基础角色和模糊任务，缺少约束、示例和输出格式"
}
```

### 流程2：多维度评分

用户说："给这个提示词打分" 或 "评分一下"

```bash
python scripts/score.py --input '{"prompt": "你是一个专业的文案写手，帮我写一篇关于AI的文章"}'
```

五维评分（每维0-20，总分0-100）：
- **清晰度** — 目标是否明确无歧义
- **完整性** — 是否包含角色/任务/约束/示例/格式
- **一致性** — 各部分是否逻辑自洽无矛盾
- **可执行性** — AI是否能无歧义地执行
- **鲁棒性** — 是否考虑了边界情况和异常处理

### 流程3：一键优化

用户说："优化这个提示词" 或 "帮我改一下prompt"

```bash
python scripts/optimize.py --input '{"prompt": "你是一个专业的文案写手，帮我写一篇关于AI的文章"}'
```

输出：
- `optimized_prompt` — 优化后的完整prompt
- `changes` — 每项改动及理由
- `before_after` — 改动前后对比

### 流程4：生成标准模板

用户说："给我一个XX场景的提示词模板"

```bash
# 查看所有可用场景
python scripts/template.py --input '{"action": "list"}'

# 生成特定场景模板
python scripts/template.py --input '{"action": "generate", "scene": "agent", "role": "数据分析师", "task": "分析销售数据"}'
```

可用场景：
- `dialogue` — 对话型（客服/问答/咨询）
- `analysis` — 分析型（数据/文本/报告）
- `creation` — 创作型（文案/故事/设计）
- `coding` — 编程型（代码/调试/重构）
- `agent` — Agent型（多步骤任务/工具调用）

---

## 脚本说明

### scripts/analyze.py
- 输入：`{"prompt": "提示词文本"}`
- 输出：结构拆解（角色/任务/约束/示例/格式）+ 统计信息
- 逻辑：关键词匹配 + 语义模式识别，拆解prompt五大模块

### scripts/score.py
- 输入：`{"prompt": "提示词文本"}`
- 输出：五维评分 + 总分 + 每维详细说明 + 改进方向
- 逻辑：基于结构完整度、语言精确度、逻辑一致性等指标量化打分

### scripts/optimize.py
- 输入：`{"prompt": "提示词文本", "focus": "all|clarity|completeness|robustness"}`
- 输出：优化版prompt + 改动清单 + 前后对比
- 逻辑：根据评分短板，逐项补充缺失模块、消除歧义、增强约束

### scripts/template.py
- 输入：`{"action": "list|generate", "scene": "场景名", "role": "角色", "task": "任务"}`
- 输出：可用场景列表 或 生成的标准模板
- 逻辑：按场景模板结构 + 用户填入的角色/任务，生成完整prompt

---

## 评分标准详解

### 清晰度（0-20分）
| 分数 | 标准 |
|------|------|
| 16-20 | 目标明确，无歧义，AI可直接执行 |
| 11-15 | 基本明确，有少量模糊表述 |
| 6-10 | 方向正确但细节不足，可能产生偏差 |
| 0-5 | 目标模糊，AI无法确定要做什么 |

### 完整性（0-20分）
| 分数 | 标准 |
|------|------|
| 16-20 | 包含角色+任务+约束+示例+格式五要素 |
| 11-15 | 包含3-4个要素 |
| 6-10 | 包含1-2个要素 |
| 0-5 | 几乎没有结构化要素 |

### 一致性（0-20分）
| 分数 | 标准 |
|------|------|
| 16-20 | 各部分逻辑自洽，无矛盾 |
| 11-15 | 基本一致，有小冲突 |
| 6-10 | 存在明显矛盾 |
| 0-5 | 严重不一致 |

### 可执行性（0-20分）
| 分数 | 标准 |
|------|------|
| 16-20 | AI无需猜测即可执行，输出可预期 |
| 11-15 | 大部分可执行，少量需要推断 |
| 6-10 | 需要AI自行补充大量信息 |
| 0-5 | AI无法确定执行路径 |

### 鲁棒性（0-20分）
| 分数 | 标准 |
|------|------|
| 16-20 | 有异常处理、边界条件、fallback策略 |
| 11-15 | 考虑了部分边界情况 |
| 6-10 | 只覆盖正常流程 |
| 0-5 | 完全没有异常考虑 |

---

## 设计原则

1. **输入→分析→输出** — 给prompt，出结果，不绕弯
2. **量化评分** — 不说"还行""不错"，用分数说话
3. **可操作建议** — 不只说"缺少约束"，给出具体的约束写法
4. **零依赖** — 纯Python标准库，拿到就能跑
5. **JSON标准化** — 输入输出全JSON，Agent好对接
