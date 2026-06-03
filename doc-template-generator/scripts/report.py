#!/usr/bin/env python3
"""报告模板生成器 — 输入报告类型，生成结构化报告骨架"""

import sys
import json
import argparse

TEMPLATES = {
    "日报": """# {department}日报 - {period}

## 今日完成
- [ ] [任务1：描述及完成情况]
- [ ] [任务2：描述及完成情况]

## 进行中
- [任务名] 进度XX%，预计完成时间
- [任务名] 进度XX%，卡点说明

## 明日计划
- [ ] [任务1：描述]
- [ ] [任务2：描述]

## 需要协助
- [问题描述及所需支持]

## 备注
[其他需要说明的事项]
""",

    "周报": """# {department}周报 - {period}

## 本周概况
> 一句话总结本周核心进展

## 重点工作
### 1. [项目/任务名称]
- **目标**：[本周要达成什么]
- **进展**：[实际完成情况，含关键数据]
- **状态**：已完成 / 进行中 / 延期

### 2. [项目/任务名称]
- **目标**：
- **进展**：
- **状态**：

## 关键成果
| 成果 | 数据/说明 |
|------|----------|
| [成果1] | [量化数据] |
| [成果2] | [量化数据] |

## 问题与风险
| 问题 | 影响 | 解决方案 | 负责人 | 截止时间 |
|------|------|---------|--------|---------|
| [问题描述] | 高/中/低 | [方案] | [人] | [日期] |

## 下周计划
- [ ] [优先级1任务]
- [ ] [优先级2任务]
- [ ] [优先级3任务]

## 需要的资源/支持
- [列出需要的资源或上级支持]
""",

    "月报": """# {department}月报 - {period}

## 月度概况
> 3-5句话总结本月核心进展和关键数据

## 核心指标
| 指标 | 目标值 | 实际值 | 完成率 | 环比变化 |
|------|-------|-------|--------|---------|
| [指标1] | | | | |
| [指标2] | | | | |

## 重点项目
### 1. [项目名称]
- **本月目标**：
- **实际进展**：
- **关键里程碑**：
- **下月计划**：

### 2. [项目名称]
- **本月目标**：
- **实际进展**：
- **关键里程碑**：
- **下月计划**：

## 团队情况
- 人员变动：
- 能力提升：
- 团队氛围：

## 问题与改进
| 问题 | 根因分析 | 改进措施 | 时间节点 |
|------|---------|---------|---------|
| | | | |

## 下月规划
### 重点目标
1. [目标1]
2. [目标2]

### 关键行动
- [ ] [行动1]
- [ ] [行动2]

## 需要的支持
- [列出需要的跨部门或上级支持]
""",

    "季报": """# {department}季报 - {period}

## 季度概况
> 本季度核心成果和关键数据概述

## 经营指标
| 指标 | Q目标 | Q实际 | 完成率 | 同比 | 环比 |
|------|-------|-------|--------|------|------|
| [营收/用户/转化等] | | | | | |

## 重点项目回顾
### 项目1：[名称]
- 季度目标：
- 完成情况：
- 核心数据：
- 经验教训：

### 项目2：[名称]
- 季度目标：
- 完成情况：
- 核心数据：
- 经验教训：

## 季度亮点
1. [亮点1及数据支撑]
2. [亮点2及数据支撑]

## 季度不足
1. [不足1及改进方向]
2. [不足2及改进方向]

## 下季度规划
### 核心目标
1. [目标1 - 量化]
2. [目标2 - 量化]

### 重点项目
1. [项目1 - 关键里程碑]
2. [项目2 - 关键里程碑]

## 资源需求
- [人员/预算/工具等需求]
""",

    "专项报告": """# {title} - 专项报告

## 报告背景
> 为什么要写这份报告，解决什么问题

## 调研方法
- 数据来源：
- 调研范围：
- 时间范围：

## 核心发现
### 发现1：[标题]
- 数据支撑：
- 影响分析：

### 发现2：[标题]
- 数据支撑：
- 影响分析：

## 详细分析
### 维度1：[名称]
[分析内容]

### 维度2：[名称]
[分析内容]

## 结论
1. [结论1]
2. [结论2]

## 建议
| 建议 | 优先级 | 预期效果 | 所需资源 |
|------|--------|---------|---------|
| [建议1] | 高/中/低 | | |
| [建议2] | 高/中/低 | | |

## 附录
- 数据明细表
- 调研问卷/访谈记录
"""
}


def generate_report(data):
    report_type = data.get("type", "周报")
    department = data.get("department", "[部门名称]")
    period = data.get("period", "[时间段]")
    title = data.get("title", department + report_type)

    if report_type not in TEMPLATES:
        return {"status": "error", "message": f"不支持的报告类型：{report_type}，可选：{', '.join(TEMPLATES.keys())}"}

    template = TEMPLATES[report_type]
    content = template.format(department=department, period=period, title=title)

    return {
        "status": "ok",
        "type": report_type,
        "content": content
    }


def main(args):
    try:
        if args.input:
            data = json.loads(args.input)
        else:
            data = {}

        result = generate_report(data)

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
    parser = argparse.ArgumentParser(description="报告模板生成器")
    parser.add_argument("--input", type=str, help="JSON格式输入")
    parser.add_argument("--output", type=str, help="输出文件路径（可选）")
    args = parser.parse_args()
    main(args)
