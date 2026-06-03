#!/usr/bin/env python3
"""总结模板生成器 — 输入总结范围，生成结构化总结文档"""

import sys
import json
import argparse


def generate_summary(data):
    scope = data.get("scope", "工作总结")
    role = data.get("role", "[你的角色]")
    highlights = data.get("highlights", [])
    period = data.get("period", "[时间段]")

    highlights_md = ""
    if highlights:
        for i, h in enumerate(highlights, 1):
            highlights_md += f"{i}. {h}\n"
    else:
        highlights_md = "1. [亮点1 - 量化描述]\n2. [亮点2 - 量化描述]\n"

    content = f"""# {scope} - {role}

## 总体评价
> 用3-5句话概括核心成果和个人成长

## 关键数据
| 维度 | 数据 | 说明 |
|------|------|------|
| [维度1] | [数据] | [对比/增长] |
| [维度2] | [数据] | [对比/增长] |

## 核心亮点
{highlights_md}

## 重点工作
### 1. [项目/工作名称]
- **角色**：[你在其中承担的角色]
- **成果**：[量化成果]
- **方法**：[关键做法和创新点]
- **价值**：[对团队/公司的贡献]

### 2. [项目/工作名称]
- **角色**：
- **成果**：
- **方法**：
- **价值**：

## 能力成长
### 新增能力
- [能力1]：[具体表现]
- [能力2]：[具体表现]

### 能力提升
- [原有能力]：从[XX水平]提升到[XX水平]，体现在[具体案例]

## 不足与反思
### 不足之处
1. [不足1 - 客观描述，不带情绪]
2. [不足2 - 客观描述]

### 根因分析
| 不足 | 根因 | 改进方向 |
|------|------|---------|
| [不足1] | [深层原因] | [具体改进措施] |
| [不足2] | [深层原因] | [具体改进措施] |

## 下阶段规划
### 重点方向
1. [方向1 - 量化目标]
2. [方向2 - 量化目标]

### 关键行动
- [ ] [行动1]
- [ ] [行动2]
- [ ] [行动3]

### 需要的支持
- [资源/培训/指导等具体需求]
"""

    return {"status": "ok", "scope": scope, "role": role, "content": content}


def main(args):
    try:
        if args.input:
            data = json.loads(args.input)
        else:
            data = {}

        result = generate_summary(data)

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
    parser = argparse.ArgumentParser(description="总结模板生成器")
    parser.add_argument("--input", type=str, help="JSON格式输入")
    parser.add_argument("--output", type=str, help="输出文件路径（可选）")
    args = parser.parse_args()
    main(args)
