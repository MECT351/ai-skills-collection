#!/usr/bin/env python3
"""方案模板生成器 — 输入方案主题，生成结构化方案文档"""

import sys
import json
import argparse


def generate_proposal(data):
    topic = data.get("topic", "[方案主题]")
    target = data.get("target", "决策层")
    scope = data.get("scope", "")
    budget = data.get("budget", "")
    timeline = data.get("timeline", "")

    content = f"""# {topic} - 方案书

## 一、项目背景
> 为什么做这件事，解决什么问题

### 现状分析
- 当前痛点：
- 影响范围：
- 不做的后果：

### 机会分析
- 市场机会：
- 竞争态势：
- 时间窗口：

## 二、项目目标
### 核心目标
1. [量化目标1]
2. [量化目标2]

### 成功标准
| 指标 | 基线值 | 目标值 | 衡量方式 |
|------|-------|-------|---------|
| [指标1] | | | |
| [指标2] | | | |

## 三、方案内容
### 整体思路
> 一句话说清楚怎么做

### 详细方案
#### 方案A：[名称]（推荐）
- 描述：
- 优势：
- 劣势：
- 适用场景：

#### 方案B：[名称]（备选）
- 描述：
- 优势：
- 劣势：
- 适用场景：

### 方案对比
| 维度 | 方案A | 方案B |
|------|-------|-------|
| 实施难度 | | |
| 成本 | | |
| 见效周期 | | |
| 风险等级 | | |
| 推荐指数 | | |

## 四、实施计划
### 里程碑
| 阶段 | 时间 | 交付物 | 负责人 |
|------|------|--------|--------|
| 准备阶段 | | | |
| 实施阶段 | | | |
| 验收阶段 | | | |

### 关键路径
1. [路径1]
2. [路径2]

## 五、资源需求
### 人力资源
| 角色 | 人数 | 职责 | 到位时间 |
|------|------|------|---------|
| | | | |

### 预算{'（' + budget + '）' if budget else ''}
| 项目 | 金额 | 说明 |
|------|------|------|
| | | |

## 六、风险与应对
| 风险 | 概率 | 影响 | 应对措施 | 负责人 |
|------|------|------|---------|--------|
| [风险1] | 高/中/低 | 高/中/低 | | |
| [风险2] | 高/中/低 | 高/中/低 | | |

## 七、预期收益
### 直接收益
- [收益1 - 量化]

### 间接收益
- [收益2 - 描述]

### ROI分析
- 投入：
- 回报周期：
- 预期ROI：

## 八、下一步行动
| 序号 | 行动 | 负责人 | 截止时间 |
|------|------|--------|---------|
| 1 | 方案审批 | | |
| 2 | 团队组建 | | |
| 3 | 启动会议 | | |
"""

    return {"status": "ok", "topic": topic, "target": target, "content": content}


def main(args):
    try:
        if args.input:
            data = json.loads(args.input)
        else:
            data = {}

        result = generate_proposal(data)

        if args.output and result.get("content"):
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(result["content"])
            result["output_file"] = args.output

        print(json.dumps(result, ensure_ascii=False, indent=2))

    except json.JSONDecodeError:
        print(json.dumps({"status": "error", "message": "输入不是有效的JSON"}, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="方案模板生成器")
    parser.add_argument("--input", type=str, help="JSON格式输入")
    parser.add_argument("--output", type=str, help="输出文件路径（可选）")
    args = parser.parse_args()
    main(args)
