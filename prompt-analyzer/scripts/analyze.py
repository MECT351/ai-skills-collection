#!/usr/bin/env python3
"""提示词结构分析器 — 解析prompt的五大模块：角色/任务/约束/示例/格式"""

import sys
import json
import argparse
import re

# 角色识别关键词
ROLE_PATTERNS = [
    r"你是(?:一个|一位|一名)?(.+?)(?:[，。,.\n]|$)",
    r"作为(?:一个|一位|一名)?(.+?)(?:[，。,.\n]|$)",
    r"扮演(?:一个|一位|一名)?(.+?)(?:[，。,.\n]|$)",
    r"act\s+as\s+(?:a\s+|an\s+)?(.+?)(?:[,\.\n]|$)",
    r"you\s+are\s+(?:a\s+|an\s+)?(.+?)(?:[,\.\n]|$)",
    r"role:\s*(.+?)(?:[\n]|$)",
    r"角色[：:]\s*(.+?)(?:[\n。]|$)",
]

# 任务识别关键词
TASK_PATTERNS = [
    r"(?:帮我|请|让我|我要|需要|你来|你的任务|你的工作是)(.+?)(?:[。\n]|$)",
    r"(?:help\s+me|please|I\s+need|I\s+want)\s+(.+?)(?:[.\n]|$)",
    r"(?:task|mission|goal|objective)[：:]\s*(.+?)(?:[\n。]|$)",
    r"(?:任务|目标|目的)[：:]\s*(.+?)(?:[\n。]|$)",
]

# 约束识别关键词
CONSTRAINT_PATTERNS = [
    r"(?:不要|不能|禁止|必须|务必|确保|限制|要求|规则|注意|不可以)(.+?)(?:[。\n]|$)",
    r"(?:do\s+not|don'?t|never|must|always|ensure|avoid|forbidden|require)(.+?)(?:[.\n]|$)",
    r"(?:约束|限制|规则|要求|条件)[：:]\s*(.+?)(?:[\n。]|$)",
]

# 示例识别关键词
EXAMPLE_PATTERNS = [
    r"(?:例如|比如|举例|示例|样例|例子|参考)[：:]\s*(.+?)(?:[\n]|$)",
    r"(?:example|sample|for\s+instance|e\.g\.)[：:]\s*(.+?)(?:[\n]|$)",
    r"```[\s\S]*?```",  # 代码块
]

# 格式识别关键词
FORMAT_PATTERNS = [
    r"(?:输出格式|返回格式|格式要求|格式如下|按以下格式)[：:]\s*(.+?)(?:[\n]|$)",
    r"(?:output\s+format|format|return\s+format)[：:]\s*(.+?)(?:[\n]|$)",
    r"```(?:json|xml|yaml|markdown|html)",  # 格式化代码块
]


def extract_patterns(text, patterns):
    """从文本中提取匹配的模式"""
    results = []
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            content = match.group(1).strip() if match.lastindex else match.group(0).strip()
            if content and len(content) > 1:
                results.append(content)
    return results


def analyze_structure(prompt):
    """分析prompt的五大模块结构"""
    structure = {}

    # 1. 角色分析
    roles = extract_patterns(prompt, ROLE_PATTERNS)
    structure["role"] = {
        "found": len(roles) > 0,
        "content": roles[0] if roles else None,
        "all_matches": roles[:3],
        "completeness": _assess_completeness(roles, "role")
    }

    # 2. 任务分析
    tasks = extract_patterns(prompt, TASK_PATTERNS)
    structure["task"] = {
        "found": len(tasks) > 0,
        "content": tasks[0] if tasks else None,
        "all_matches": tasks[:3],
        "completeness": _assess_completeness(tasks, "task")
    }

    # 3. 约束分析
    constraints = extract_patterns(prompt, CONSTRAINT_PATTERNS)
    structure["constraints"] = {
        "found": len(constraints) > 0,
        "content": constraints if constraints else None,
        "count": len(constraints),
        "completeness": _assess_completeness(constraints, "constraints")
    }

    # 4. 示例分析
    examples = extract_patterns(prompt, EXAMPLE_PATTERNS)
    structure["examples"] = {
        "found": len(examples) > 0,
        "content": examples[0] if examples else None,
        "count": len(examples),
        "completeness": _assess_completeness(examples, "examples")
    }

    # 5. 格式分析
    formats = extract_patterns(prompt, FORMAT_PATTERNS)
    structure["format"] = {
        "found": len(formats) > 0,
        "content": formats[0] if formats else None,
        "completeness": _assess_completeness(formats, "format")
    }

    return structure


def _assess_completeness(matches, module_type):
    """评估模块完整度"""
    if not matches:
        return "missing"

    if module_type == "role":
        if any(kw in matches[0].lower() for kw in ["专业", "专家", "资深", "expert", "professional", "senior"]):
            return "detailed"
        return "basic"

    if module_type == "task":
        if len(matches) >= 2 or len(matches[0]) > 20:
            return "detailed"
        return "low"

    if module_type == "constraints":
        if len(matches) >= 3:
            return "detailed"
        if len(matches) >= 1:
            return "basic"
        return "missing"

    if module_type == "examples":
        if len(matches) >= 2:
            return "detailed"
        if len(matches) >= 1:
            return "basic"
        return "missing"

    if module_type == "format":
        if len(matches) >= 1 and len(matches[0]) > 10:
            return "detailed"
        if len(matches) >= 1:
            return "basic"
        return "missing"

    return "basic"


def compute_stats(prompt):
    """计算prompt统计信息"""
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', prompt))
    english_chars = len(re.findall(r'[a-zA-Z]', prompt))
    sentences = len(re.findall(r'[。！？.!?]+', prompt))
    paragraphs = len([p for p in prompt.split('\n\n') if p.strip()])
    lines = len([l for l in prompt.split('\n') if l.strip()])

    # 结构完整度得分（0-100）
    structure = analyze_structure(prompt)
    found_count = sum(1 for k in ["role", "task", "constraints", "examples", "format"]
                      if structure[k]["found"])
    structure_score = found_count * 20

    return {
        "total_chars": len(prompt),
        "chinese_chars": chinese_chars,
        "english_chars": english_chars,
        "has_chinese": chinese_chars > 0,
        "has_english": english_chars > 0,
        "sentence_count": max(sentences, 1),
        "paragraph_count": max(paragraphs, 1),
        "line_count": lines,
        "structure_score": structure_score
    }


def generate_summary(structure, stats):
    """生成分析摘要"""
    missing = [k for k in ["role", "task", "constraints", "examples", "format"]
               if not structure[k]["found"]]
    weak = [k for k in ["role", "task", "constraints", "examples", "format"]
            if structure[k]["found"] and structure[k]["completeness"] in ("basic", "low")]

    parts = []
    if structure["role"]["found"]:
        parts.append(f"角色定义为「{structure['role']['content']}」")
    else:
        parts.append("缺少角色定义")

    if structure["task"]["found"]:
        parts.append(f"任务为「{structure['task']['content']}」")
    else:
        parts.append("缺少明确任务")

    if missing:
        cn_map = {"role": "角色", "task": "任务", "constraints": "约束条件",
                  "examples": "示例", "format": "输出格式"}
        parts.append(f"缺失模块：{'、'.join(cn_map.get(m, m) for m in missing)}")

    if weak:
        cn_map = {"role": "角色", "task": "任务", "constraints": "约束条件",
                  "examples": "示例", "format": "输出格式"}
        parts.append(f"待加强：{'、'.join(cn_map.get(w, w) for w in weak)}")

    return "；".join(parts)


def main(args):
    try:
        if args.input:
            data = json.loads(args.input)
        else:
            data = {}

        prompt = data.get("prompt", "")
        if not prompt:
            result = {"status": "error", "message": "缺少prompt参数，请提供 --input '{\"prompt\": \"你的提示词\"}'"}
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return

        structure = analyze_structure(prompt)
        stats = compute_stats(prompt)
        summary = generate_summary(structure, stats)

        result = {
            "status": "ok",
            "structure": structure,
            "stats": stats,
            "summary": summary
        }

        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            result["output_file"] = args.output

        print(json.dumps(result, ensure_ascii=False, indent=2))

    except json.JSONDecodeError:
        print(json.dumps({"status": "error", "message": "输入不是有效的JSON"}, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="提示词结构分析器")
    parser.add_argument("--input", type=str, help="JSON格式输入，含prompt字段")
    parser.add_argument("--output", type=str, help="输出文件路径（可选）")
    args = parser.parse_args()
    main(args)
