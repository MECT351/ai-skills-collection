#!/usr/bin/env python3
"""计划模板生成器 — 输入目标，生成工作计划文档"""

import sys
import json
import argparse


def generate_plan(data):
    goal = data.get("goal", "[计划目标]")
    duration = data.get("duration", "[时间跨度]")
    team_size = data.get("team_size", "")
    priority = data.get("priority", "中")

    content = f"""# {goal} - 工作计划

## 目标定义
### 核心目标
> {goal}

### 关键结果（KR）
1. KR1：[量化关键结果]
2. KR2：[量化关键结果]
3. KR3：[量化关键结果]

### 目标对齐
- 上级目标：[与什么战略/OKR对齐]
- 横向依赖：[需要哪些团队配合]

## 时间规划
**总周期**：{duration}

### Phase 1：准备阶段
- 时间：[第X周 - 第X周]
- 目标：[阶段目标]
- 交付物：
  - [ ] [交付物1]
  - [ ] [交付物2]

### Phase 2：执行阶段
- 时间：[第X周 - 第X周]
- 目标：[阶段目标]
- 交付物：
  - [ ] [交付物1]
  - [ ] [交付物2]

### Phase 3：收尾阶段
- 时间：[第X周 - 第X周]
- 目标：[阶段目标]
- 交付物：
  - [ ] [交付物1]
  - [ ] [交付物2]

## 任务分解
| 任务 | 负责人 | 优先级 | 预计耗时 | 依赖 | 截止时间 | 状态 |
|------|--------|--------|---------|------|---------|------|
| [任务1] | | P0/P1/P2 | | | | 待开始 |
| [任务2] | | P0/P1/P2 | | | | 待开始 |
| [任务3] | | P0/P1/P2 | | | | 待开始 |

## 团队分工{'（' + str(team_size) + '人）' if team_size else ''}
| 角色 | 姓名 | 职责 | 时间占比 |
|------|------|------|---------|
| 项目负责人 | | 整体协调、进度把控 | 100% |
| 核心执行 | | [具体职责] | XX% |
| 协作支持 | | [具体职责] | XX% |

## 风险预案
| 风险 | 概率 | 影响 | 预防措施 | 应急方案 |
|------|------|------|---------|---------|
| [进度延期] | 中 | 高 | 留buffer、关键路径监控 | 砍非核心需求 |
| [人员变动] | 低 | 高 | 知识文档化、交叉备岗 | 临时调配资源 |
| [需求变更] | 高 | 中 | 变更评审机制 | 评估影响再决策 |

## 沟通机制
| 会议 | 频率 | 参与人 | 目的 |
|------|------|--------|------|
| 站会 | 每日 | 核心成员 | 同步进度、暴露问题 |
| 周会 | 每周 | 全员 | 里程碑回顾、计划调整 |
| 评审 | 按需 | 利益相关方 | 关键决策 |

## 验收标准
- [ ] [标准1：量化可验证]
- [ ] [标准2：量化可验证]
- [ ] [标准3：量化可验证]

## 复盘计划
- 复盘时间：[计划结束后X天内]
- 复盘范围：[目标达成度、过程效率、经验教训]
- 输出：[复盘报告]
"""

    return {"status": "ok", "goal": goal, "duration": duration, "content": content}


def main(args):
    try:
        if args.input:
            data = json.loads(args.input)
        else:
            data = {}

        result = generate_plan(data)

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
    parser = argparse.ArgumentParser(description="计划模板生成器")
    parser.add_argument("--input", type=str, help="JSON格式输入")
    parser.add_argument("--output", type=str, help="输出文件路径（可选）")
    args = parser.parse_args()
    main(args)
