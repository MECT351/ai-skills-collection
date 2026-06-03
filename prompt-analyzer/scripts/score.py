#!/usr/bin/env python3
"""提示词多维度评分器 — 清晰度/完整性/一致性/可执行性/鲁棒性 五维打分"""

import sys
import json
import argparse
import re


def score_clarity(prompt):
    """评分：清晰度（0-20）
    - 目标是否明确无歧义
    - 语言是否精确
    - 是否有模糊表述
    """
    score = 8  # 基础分
    details = []

    # 加分项
    if any(kw in prompt for kw in ["具体", "明确", "精确", "exactly", "specifically"]):
        score += 2
        details.append("包含精确性要求")

    if len(re.findall(r'[，。；：、]', prompt)) >= 3:
        score += 2
        details.append("语句结构清晰，标点规范")

    if any(kw in prompt for kw in ["目标", "目的", "objective", "goal", "target"]):
        score += 2
        details.append("明确提到目标")

    if re.search(r'第[一二三四五\d]+[步阶段部分]', prompt):
        score += 2
        details.append("有分步骤描述")

    # 减分项
    vague_words = ["大概", "可能", "差不多", "大概其", "maybe", "perhaps", "somehow", "sort of"]
    vague_count = sum(1 for w in vague_words if w in prompt.lower())
    if vague_count > 0:
        score -= min(vague_count * 2, 4)
        details.append(f"包含{vague_count}处模糊表述")

    if len(prompt) < 20:
        score -= 3
        details.append("提示词过短，信息不足")
    elif len(prompt) > 500:
        score += 2
        details.append("提示词内容充实")

    # 目标可识别性
    has_clear_target = bool(re.search(r'(写|生成|分析|总结|翻译|列出|设计|创建|完成|帮我|请)', prompt))
    if has_clear_target:
        score += 2
        details.append("有明确的动作目标")
    else:
        score -= 2
        details.append("缺少明确的动作目标")

    return {
        "score": max(0, min(20, score)),
        "max": 20,
        "details": details,
        "level": _score_level(score, 20)
    }


def score_completeness(prompt):
    """评分：完整性（0-20）
    - 是否包含角色/任务/约束/示例/格式
    """
    score = 0
    details = []
    modules_found = []

    # 角色
    has_role = bool(re.search(r'(你是|作为|扮演|act as|you are|角色)', prompt, re.IGNORECASE))
    if has_role:
        score += 4
        modules_found.append("角色")
        details.append("包含角色定义")
    else:
        details.append("缺少角色定义")

    # 任务
    has_task = bool(re.search(r'(帮我|请|让我|我要|需要|任务|目标|help|please|task)', prompt, re.IGNORECASE))
    if has_task:
        score += 4
        modules_found.append("任务")
        details.append("包含任务描述")
    else:
        details.append("缺少任务描述")

    # 约束
    has_constraint = bool(re.search(r'(不要|不能|禁止|必须|务必|确保|限制|要求|规则|do not|must|never|always)', prompt, re.IGNORECASE))
    if has_constraint:
        score += 4
        modules_found.append("约束")
        details.append("包含约束条件")
    else:
        details.append("缺少约束条件")

    # 示例
    has_example = bool(re.search(r'(例如|比如|举例|示例|样例|例子|example|sample|e\.g\.)', prompt, re.IGNORECASE))
    if has_example:
        score += 4
        modules_found.append("示例")
        details.append("包含示例")
    else:
        details.append("缺少示例")

    # 格式
    has_format = bool(re.search(r'(输出格式|返回格式|格式要求|格式如下|output format|format)', prompt, re.IGNORECASE))
    if has_format:
        score += 4
        modules_found.append("格式")
        details.append("包含输出格式")
    else:
        details.append("缺少输出格式")

    # 额外加分
    if len(modules_found) == 5:
        score += 2
        details.append("五大模块齐全，额外加分")

    return {
        "score": max(0, min(20, score)),
        "max": 20,
        "modules_found": modules_found,
        "details": details,
        "level": _score_level(score, 20)
    }


def score_consistency(prompt):
    """评分：一致性（0-20）
    - 各部分是否逻辑自洽
    - 是否有矛盾指令
    """
    score = 15  # 基础分较高，大多数prompt不会自相矛盾
    details = []

    # 检测矛盾
    contradictions = [
        (r'简短.*?详细', '同时要求简短和详细'),
        (r'简单.*?复杂', '同时要求简单和复杂'),
        (r'简短.*?全面', '同时要求简短和全面'),
        (r'brief.*?detailed', '同时要求brief和detailed'),
        (r'simple.*?comprehensive', '同时要求simple和comprehensive'),
        (r'不要.*?中文.*?中文', '对中文使用有矛盾要求'),
        (r'不要.*?英文.*?英文', '对英文使用有矛盾要求'),
    ]

    for pattern, desc in contradictions:
        if re.search(pattern, prompt, re.IGNORECASE):
            score -= 4
            details.append(f"存在矛盾：{desc}")

    # 正面信号
    if re.search(r'如果.*?那么|if.*?then', prompt, re.IGNORECASE):
        score += 2
        details.append("有条件逻辑，结构清晰")

    if re.search(r'否则|otherwise|else', prompt, re.IGNORECASE):
        score += 1
        details.append("有备选方案")

    # 多角色冲突检测
    roles = re.findall(r'(?:你是|作为|扮演)\s*(?:一个|一位|一名)?\s*(.+?)(?:[，。,.\n]|$)', prompt)
    if len(roles) > 2:
        score -= 3
        details.append(f"定义了{len(roles)}个角色，可能造成角色冲突")

    if not details:
        details.append("未检测到明显逻辑矛盾")

    return {
        "score": max(0, min(20, score)),
        "max": 20,
        "details": details,
        "level": _score_level(score, 20)
    }


def score_executability(prompt):
    """评分：可执行性（0-20）
    - AI是否能无歧义执行
    - 输出是否可预期
    """
    score = 8
    details = []

    # 加分项
    if re.search(r'(输出|返回|回复|回答|生成)\s*(?:为|是|用|以)', prompt):
        score += 2
        details.append("有明确的输出方式")

    if re.search(r'\d+[\s]*[个条项步部分点]', prompt):
        score += 2
        details.append("有数量要求")

    if re.search(r'(字数|篇幅|长度|长度|words?|characters?)', prompt, re.IGNORECASE):
        score += 2
        details.append("有长度要求")

    if re.search(r'(语气|风格|语调|tone|style|voice)', prompt, re.IGNORECASE):
        score += 2
        details.append("有风格要求")

    if re.search(r'(JSON|XML|Markdown|表格|列表|代码块)', prompt, re.IGNORECASE):
        score += 2
        details.append("有明确输出格式")

    # 减分项
    if re.search(r'(随便|都行|无所谓|whatever|anything)', prompt, re.IGNORECASE):
        score -= 3
        details.append("包含模糊放权表述")

    if not re.search(r'(写|生成|分析|总结|翻译|列出|设计|创建|回答|解释|计算)', prompt):
        score -= 3
        details.append("缺少明确动作词")

    # 可预期性
    if len(prompt) > 200:
        score += 2
        details.append("提示词较长，信息充分")

    return {
        "score": max(0, min(20, score)),
        "max": 20,
        "details": details,
        "level": _score_level(score, 20)
    }


def score_robustness(prompt):
    """评分：鲁棒性（0-20）
    - 是否考虑了边界情况
    - 是否有异常处理
    - 是否有fallback策略
    """
    score = 4  # 大部分prompt没考虑这些
    details = []

    # 加分项
    if re.search(r'(如果.*?不存在|如果.*?没有|如果.*?无法|if.*?not|if.*?cannot|if.*?missing)', prompt, re.IGNORECASE):
        score += 4
        details.append("有缺失数据处理")

    if re.search(r'(否则|其他情况|另外|otherwise|fallback|default)', prompt, re.IGNORECASE):
        score += 3
        details.append("有备选/默认方案")

    if re.search(r'(错误|异常|失败|error|exception|fail|invalid)', prompt, re.IGNORECASE):
        score += 3
        details.append("考虑了错误处理")

    if re.search(r'(边界|极端|特殊|异常|boundary|edge|corner|special)', prompt, re.IGNORECASE):
        score += 3
        details.append("考虑了边界情况")

    if re.search(r'(不确定|无法确定|不知道|uncertain|unsure|unknown)', prompt, re.IGNORECASE):
        score += 2
        details.append("有不确定时的处理指引")

    if re.search(r'(最多|最少|不超过|至少|至少|max|min|limit|at most|at least)', prompt, re.IGNORECASE):
        score += 2
        details.append("有数量限制/边界")

    if not details or all("未" in d for d in details):
        details.append("未考虑异常和边界情况")

    return {
        "score": max(0, min(20, score)),
        "max": 20,
        "details": details,
        "level": _score_level(score, 20)
    }


def _score_level(score, max_score):
    """根据分数返回等级"""
    pct = score / max_score * 100
    if pct >= 80:
        return "优秀"
    if pct >= 60:
        return "良好"
    if pct >= 40:
        return "一般"
    if pct >= 20:
        return "较弱"
    return "缺失"


def score_prompt(prompt):
    """综合评分"""
    clarity = score_clarity(prompt)
    completeness = score_completeness(prompt)
    consistency = score_consistency(prompt)
    executability = score_executability(prompt)
    robustness = score_robustness(prompt)

    total = clarity["score"] + completeness["score"] + consistency["score"] + executability["score"] + robustness["score"]

    # 改进优先级
    dimensions = {
        "completeness": completeness,
        "clarity": clarity,
        "executability": executability,
        "robustness": robustness,
        "consistency": consistency,
    }
    sorted_dims = sorted(dimensions.items(), key=lambda x: x[1]["score"])
    improvement_priority = [{"dimension": cn_dim(k), "score": v["score"], "level": v["level"]}
                            for k, v in sorted_dims]

    return {
        "total_score": total,
        "max_score": 100,
        "percentage": round(total, 1),
        "level": _score_level(total, 100),
        "dimensions": {
            "clarity": clarity,
            "completeness": completeness,
            "consistency": consistency,
            "executability": executability,
            "robustness": robustness,
        },
        "improvement_priority": improvement_priority
    }


def cn_dim(key):
    """维度中文名"""
    mapping = {
        "clarity": "清晰度",
        "completeness": "完整性",
        "consistency": "一致性",
        "executability": "可执行性",
        "robustness": "鲁棒性",
    }
    return mapping.get(key, key)


def main(args):
    try:
        if args.input:
            data = json.loads(args.input)
        else:
            data = {}

        prompt = data.get("prompt", "")
        if not prompt:
            result = {"status": "error", "message": "缺少prompt参数"}
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return

        result = score_prompt(prompt)
        result["status"] = "ok"

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
    parser = argparse.ArgumentParser(description="提示词多维度评分器")
    parser.add_argument("--input", type=str, help="JSON格式输入，含prompt字段")
    parser.add_argument("--output", type=str, help="输出文件路径（可选）")
    args = parser.parse_args()
    main(args)
