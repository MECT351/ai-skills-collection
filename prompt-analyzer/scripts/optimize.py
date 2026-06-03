#!/usr/bin/env python3
"""提示词优化器 — 输入原始prompt，输出优化版prompt + 改动清单 + 前后对比"""

import sys
import json
import argparse
import re


def optimize_prompt(prompt, focus="all"):
    """优化prompt
    focus: all|clarity|completeness|robustness — 优化侧重点
    """
    changes = []
    optimized = prompt

    # ========== 完整性优化 ==========
    if focus in ("all", "completeness"):
        # 1. 补充角色定义
        if not re.search(r'(你是|作为|扮演|act as|you are|角色)', optimized, re.IGNORECASE):
            role = _infer_role(optimized)
            if role:
                prefix = f"你是一个{role}。"
                optimized = prefix + optimized
                changes.append({
                    "type": "add",
                    "module": "角色定义",
                    "before": "无",
                    "after": prefix,
                    "reason": f"补充角色定义，让AI明确身份和视角"
                })

        # 2. 补充输出格式
        if not re.search(r'(输出格式|返回格式|格式要求|格式如下|output format)', optimized, re.IGNORECASE):
            fmt = _infer_format(optimized)
            if fmt:
                suffix = f"\n\n输出格式：{fmt}"
                optimized += suffix
                changes.append({
                    "type": "add",
                    "module": "输出格式",
                    "before": "无",
                    "after": fmt,
                    "reason": "补充输出格式，让AI知道如何组织结果"
                })

        # 3. 补充约束条件
        if not re.search(r'(不要|不能|禁止|必须|确保|do not|must|never)', optimized, re.IGNORECASE):
            constraints = _infer_constraints(optimized)
            if constraints:
                suffix = f"\n\n要求：\n{constraints}"
                optimized += suffix
                changes.append({
                    "type": "add",
                    "module": "约束条件",
                    "before": "无",
                    "after": constraints.strip(),
                    "reason": "补充约束条件，减少AI输出偏差"
                })

    # ========== 清晰度优化 ==========
    if focus in ("all", "clarity"):
        # 4. 替换模糊表述
        vague_replacements = {
            "大概": "具体来说",
            "差不多": "精确地",
            "一些": "3-5个",
            "几个": "3-5个",
            "很多": "10个以上",
            "尽量": "务必",
            "最好": "必须",
            "maybe": "specifically",
            "some": "3-5",
            "a few": "3-5",
            "a lot": "10+",
        }
        for vague, precise in vague_replacements.items():
            if vague in optimized:
                optimized = optimized.replace(vague, precise, 1)
                changes.append({
                    "type": "replace",
                    "module": "模糊表述",
                    "before": vague,
                    "after": precise,
                    "reason": f"将模糊表述「{vague}」替换为精确表述「{precise}」"
                })

        # 5. 为短任务添加具体化
        if len(optimized) < 50 and not re.search(r'[，。；]', optimized):
            expanded = _expand_short_prompt(optimized)
            if expanded != optimized:
                changes.append({
                    "type": "expand",
                    "module": "任务具体化",
                    "before": optimized,
                    "after": expanded,
                    "reason": "过短的提示词容易产生歧义，补充关键细节"
                })
                optimized = expanded

    # ========== 鲁棒性优化 ==========
    if focus in ("all", "robustness"):
        # 6. 补充异常处理
        if not re.search(r'(如果.*?不存在|如果.*?没有|如果.*?无法|否则|otherwise|fallback)', optimized, re.IGNORECASE):
            fallback = _generate_fallback(optimized)
            if fallback:
                optimized += f"\n\n{fallback}"
                changes.append({
                    "type": "add",
                    "module": "异常处理",
                    "before": "无",
                    "after": fallback,
                    "reason": "补充异常情况处理，提高输出鲁棒性"
                })

    # ========== 通用优化 ==========
    # 7. 添加分隔结构（如果prompt较长但没有结构）
    if len(optimized) > 200 and optimized.count('\n') < 3:
        structured = _add_structure(optimized)
        if structured != optimized:
            changes.append({
                "type": "restructure",
                "module": "结构化",
                "before": "整段文字，无分层",
                "after": "按模块分段落/分点描述",
                "reason": "长提示词需要结构化，便于AI理解各部分权重"
            })
            optimized = structured

    return {
        "original_prompt": prompt,
        "optimized_prompt": optimized,
        "changes": changes,
        "change_count": len(changes),
        "focus": focus
    }


def _infer_role(prompt):
    """从任务推断角色"""
    role_map = {
        "写": "专业的文案写手",
        "分析": "资深分析师",
        "翻译": "专业翻译专家",
        "总结": "内容提炼专家",
        "设计": "高级设计师",
        "编程": "高级软件工程师",
        "计算": "数据计算专家",
        "解释": "知识讲解专家",
        "列出": "信息整理专家",
        "对比": "对比分析专家",
        "review": "senior code reviewer",
        "write": "professional writer",
        "analyze": "senior analyst",
        "design": "senior designer",
        "code": "senior software engineer",
    }
    for keyword, role in role_map.items():
        if keyword in prompt.lower():
            return role
    return "专业助手"


def _infer_format(prompt):
    """从任务推断输出格式"""
    if re.search(r'(列出|清单|list)', prompt, re.IGNORECASE):
        return "编号列表，每项包含标题和简要说明"
    if re.search(r'(对比|比较|compare)', prompt, re.IGNORECASE):
        return "对比表格，包含维度/选项A/选项B三列"
    if re.search(r'(分析|analysis)', prompt, re.IGNORECASE):
        return "1.核心结论 2.详细分析 3.数据支撑 4.建议"
    if re.search(r'(总结|摘要|summary)', prompt, re.IGNORECASE):
        return "一段话总结（100字内）+ 关键要点列表"
    if re.search(r'(代码|编程|code|program)', prompt, re.IGNORECASE):
        return "代码块 + 简要注释说明"
    if re.search(r'(翻译|translate)', prompt, re.IGNORECASE):
        return "原文 + 译文对照"
    return "结构化文本，包含标题、正文和结论"


def _infer_constraints(prompt):
    """从任务推断约束条件"""
    constraints = []
    if re.search(r'(文章|文案|写作)', prompt):
        constraints.append("- 语言流畅自然，避免AI感过重的表述")
        constraints.append("- 内容准确，不编造数据或事实")
    if re.search(r'(代码|编程|code)', prompt, re.IGNORECASE):
        constraints.append("- 代码可直接运行，包含必要的import")
        constraints.append("- 遵循最佳实践和代码规范")
    if re.search(r'(分析|报告)', prompt):
        constraints.append("- 基于事实和数据，不推测不编造")
        constraints.append("- 如数据不足，明确标注")
    if re.search(r'(翻译|translate)', prompt, re.IGNORECASE):
        constraints.append("- 保持原文语义，不意译不增删")
        constraints.append("- 专业术语使用通用译法")

    if constraints:
        return "\n".join(constraints)
    return "- 内容准确，不编造信息\n- 如不确定，明确说明"


def _generate_fallback(prompt):
    """生成异常处理说明"""
    fallbacks = []
    if re.search(r'(数据|信息|内容)', prompt):
        fallbacks.append("如果相关数据或信息不足，请明确说明缺少什么，不要编造。")
    if re.search(r'(搜索|查找|查询)', prompt):
        fallbacks.append("如果搜索不到相关结果，返回空结果并说明原因，不要猜测。")
    if not fallbacks:
        fallbacks.append("如果无法完成指定任务，请说明原因并给出替代方案。")
    return "\n".join(fallbacks)


def _expand_short_prompt(prompt):
    """扩展过短的prompt"""
    # 尝试识别动作
    action_match = re.search(r'(帮我|请|我要)(.+)', prompt)
    if action_match:
        action = action_match.group(2).strip()
        return f"请帮我{action}。\n\n要求：\n- 内容准确具体\n- 结构清晰有条理\n- 如不确定请说明"

    return prompt


def _add_structure(prompt):
    """为长prompt添加结构化分隔"""
    # 简单策略：在关键句号后加换行
    lines = re.split(r'([。！？])', prompt)
    result = []
    current = ""
    for i, part in enumerate(lines):
        current += part
        if part in ('。', '！', '？') and len(current) > 30:
            result.append(current.strip())
            current = ""
    if current.strip():
        result.append(current.strip())

    return '\n\n'.join(result)


def main(args):
    try:
        if args.input:
            data = json.loads(args.input)
        else:
            data = {}

        prompt = data.get("prompt", "")
        focus = data.get("focus", "all")

        if not prompt:
            result = {"status": "error", "message": "缺少prompt参数"}
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return

        if focus not in ("all", "clarity", "completeness", "robustness"):
            result = {"status": "error", "message": "focus参数仅支持 all|clarity|completeness|robustness"}
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return

        result = optimize_prompt(prompt, focus)
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
    parser = argparse.ArgumentParser(description="提示词优化器")
    parser.add_argument("--input", type=str, help="JSON格式输入，含prompt和可选focus字段")
    parser.add_argument("--output", type=str, help="输出文件路径（可选）")
    args = parser.parse_args()
    main(args)
