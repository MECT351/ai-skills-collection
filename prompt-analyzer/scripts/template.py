#!/usr/bin/env python3
"""提示词模板生成器 — 按场景生成标准prompt模板"""

import sys
import json
import argparse

# 场景模板定义
SCENES = {
    "dialogue": {
        "name": "对话型",
        "description": "客服/问答/咨询等交互式场景",
        "structure": [
            "角色定义 — 明确AI的身份和专业领域",
            "对话目标 — 本次对话要解决什么问题",
            "语气风格 — 亲和/专业/幽默/严谨",
            "知识范围 — AI可以回答的领域边界",
            "异常处理 — 遇到无法回答的问题怎么办"
        ]
    },
    "analysis": {
        "name": "分析型",
        "description": "数据/文本/报告等深度分析场景",
        "structure": [
            "角色定义 — 明确分析师的专业背景",
            "分析目标 — 要得出什么结论",
            "数据来源 — 基于什么数据/信息分析",
            "分析方法 — 用什么框架/模型/角度",
            "输出格式 — 结论+论据+建议的标准结构"
        ]
    },
    "creation": {
        "name": "创作型",
        "description": "文案/故事/设计等创意场景",
        "structure": [
            "角色定义 — 明确创作者的风格定位",
            "创作目标 — 要产出什么内容",
            "风格要求 — 语言风格/调性/参考对象",
            "内容约束 — 字数/禁忌/必含元素",
            "质量标准 — 什么样的输出算合格"
        ]
    },
    "coding": {
        "name": "编程型",
        "description": "代码编写/调试/重构等开发场景",
        "structure": [
            "角色定义 — 明确开发者的技术栈和水平",
            "功能需求 — 要实现什么功能",
            "技术约束 — 语言/框架/版本/性能要求",
            "代码规范 — 命名/注释/错误处理标准",
            "输出格式 — 代码块+说明+测试用例"
        ]
    },
    "agent": {
        "name": "Agent型",
        "description": "多步骤任务/工具调用等Agent场景",
        "structure": [
            "角色定义 — 明确Agent的能力和权限",
            "任务目标 — 最终要达成什么结果",
            "执行步骤 — 分步骤描述任务流程",
            "工具使用 — 可用工具及调用条件",
            "异常处理 — 步骤失败时的fallback策略",
            "输出规范 — 中间状态和最终结果的格式"
        ]
    }
}


def list_scenes():
    """列出所有可用场景"""
    result = []
    for key, scene in SCENES.items():
        result.append({
            "id": key,
            "name": scene["name"],
            "description": scene["description"],
            "structure": scene["structure"]
        })
    return result


def generate_template(scene, role=None, task=None):
    """生成标准prompt模板"""
    if scene not in SCENES:
        return {"status": "error", "message": f"未知场景：{scene}，可选：{', '.join(SCENES.keys())}"}

    scene_info = SCENES[scene]
    role = role or "专业助手"
    task = task or "[请描述具体任务]"

    templates = {
        "dialogue": f"""你是一个{role}，擅长通过对话帮助用户解决问题。

## 对话目标
{task}

## 语气风格
- 专业且亲和，不居高临下
- 用通俗易懂的语言解释专业概念
- 适当使用类比帮助理解

## 知识范围
- 本领域内的专业问题可以详细解答
- 超出专业范围的问题，诚实说明并建议咨询相关专家
- 不确定的信息，明确标注"待确认"

## 对话规则
- 先理解用户问题的核心需求，再回答
- 如果问题模糊，先确认再回答
- 每次回答控制在200字以内，复杂问题可分段
- 如果无法回答，说明原因并给出替代建议

## 异常处理
- 遇到无法回答的问题：说明原因 + 建议方向
- 遇到模糊的问题：先确认理解，再回答
- 遇到情绪化的用户：先共情，再提供方案""",

        "analysis": f"""你是一个{role}，擅长深度分析和洞察提炼。

## 分析目标
{task}

## 分析方法
1. 明确分析维度和框架
2. 收集和整理相关数据/信息
3. 逐维度分析，给出论据支撑
4. 综合各维度，提炼核心结论
5. 基于结论，给出可操作建议

## 数据要求
- 所有结论必须有数据或事实支撑
- 如数据不足，明确标注"数据不足，以下为推断"
- 不编造数据，不猜测趋势

## 输出格式
### 核心结论
[一段话总结主要发现]

### 详细分析
1. **维度1**：分析内容 + 数据支撑
2. **维度2**：分析内容 + 数据支撑
3. **维度3**：分析内容 + 数据支撑

### 建议
- 建议1：具体可执行的方案
- 建议2：具体可执行的方案

### 数据来源与局限性
[说明数据来源和分析局限]""",

        "creation": f"""你是一个{role}，擅长创作高质量内容。

## 创作目标
{task}

## 风格要求
- 语言流畅自然，避免AI感
- 有观点有态度，不做无意义的万能话术
- 适当使用修辞手法增强表现力
- 保持专业性的同时兼顾可读性

## 内容约束
- 不编造事实和数据
- 引用信息需标注来源
- 涉及专业领域时使用准确术语
- 字数控制在合理范围内

## 质量标准
- 标题/开头有吸引力
- 内容有逻辑、有层次
- 结尾有力度，不做空洞总结
- 整体读感自然，不像AI生成

## 输出格式
1. 标题（3个备选）
2. 正文
3. 核心观点摘要（50字内）""",

        "coding": f"""你是一个{role}，擅长编写高质量代码。

## 功能需求
{task}

## 技术约束
- 语言/框架：[请指定]
- 版本要求：[请指定]
- 性能要求：[请指定]

## 代码规范
- 遵循语言最佳实践和常见代码规范
- 变量/函数命名清晰有意义
- 关键逻辑添加注释
- 包含必要的错误处理
- 代码可直接运行，包含所有import

## 输出格式
```[language]
# 代码实现
```

### 代码说明
- 核心逻辑：[简要说明]
- 设计考量：[为什么这样做]

### 测试用例
```[language]
# 基本测试
```

### 已知限制
[说明代码的边界和限制]""",

        "agent": f"""你是一个{role}，能够自主执行多步骤任务。

## 任务目标
{task}

## 执行步骤
1. **信息收集**：了解任务所需的所有输入和上下文
2. **方案规划**：制定执行计划，明确每步的目标
3. **逐步执行**：按计划执行，每步确认结果
4. **结果验证**：检查最终结果是否满足目标
5. **输出交付**：整理结果，按要求格式输出

## 工具使用规则
- 优先使用已有工具完成任务
- 工具调用前确认参数正确
- 工具调用失败时记录错误，尝试替代方案
- 不重复调用相同参数的同一工具

## 异常处理
- 步骤执行失败：分析原因，尝试替代方案
- 数据缺失：明确标注，不编造
- 权限不足：说明需要什么权限，停止执行
- 超出能力范围：诚实说明，建议人工介入

## 输出规范
### 执行过程
- 每步操作及结果

### 最终结果
[任务产出物]

### 执行摘要
- 完成情况：已完成/部分完成/失败
- 关键发现：[如有]
- 遗留问题：[如有]"""
    }

    template = templates.get(scene, "")
    if not template:
        return {"status": "error", "message": f"场景 {scene} 的模板生成失败"}

    return {
        "status": "ok",
        "scene": scene,
        "scene_name": scene_info["name"],
        "role": role,
        "task": task,
        "template": template,
        "structure": scene_info["structure"],
        "tips": _get_tips(scene)
    }


def _get_tips(scene):
    """按场景给出使用建议"""
    tips = {
        "dialogue": [
            "对话型prompt重点在于语气和边界，让AI知道什么该说什么不该说",
            "加入「先确认再回答」的规则，减少理解偏差",
            "设置单次回答字数限制，避免长篇大论"
        ],
        "analysis": [
            "分析型prompt必须强调'不编造数据'，这是AI最常见的问题",
            "指定分析框架（如SWOT/PEST/5W2H），比让AI自由分析效果好",
            "要求'论据+结论'的结构，避免AI只给结论不给出依据"
        ],
        "creation": [
            "创作型prompt给参考对象比给抽象描述更有效",
            "明确'不像AI生成'的要求，AI会调整语言风格",
            "要求多个备选标题，比只生成一个质量更高"
        ],
        "coding": [
            "编程型prompt要指定语言和框架版本，避免AI用错误版本",
            "要求'可直接运行'，迫使AI补全所有依赖",
            "要求提供测试用例，既是验证也是文档"
        ],
        "agent": [
            "Agent型prompt要明确分步骤，避免AI跳步或遗漏",
            "每步都要有成功/失败的判断标准",
            "异常处理比正常流程更重要——AI出问题往往在边界情况"
        ]
    }
    return tips.get(scene, [])


def main(args):
    try:
        if args.input:
            data = json.loads(args.input)
        else:
            data = {}

        action = data.get("action", "list")

        if action == "list":
            result = {
                "status": "ok",
                "action": "list",
                "scenes": list_scenes(),
                "usage": '生成模板请使用: --input \'{"action": "generate", "scene": "场景名", "role": "角色", "task": "任务"}\''
            }
        elif action == "generate":
            scene = data.get("scene", "")
            role = data.get("role", None)
            task = data.get("task", None)
            result = generate_template(scene, role, task)
        else:
            result = {"status": "error", "message": f"未知action：{action}，支持 list|generate"}

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
    parser = argparse.ArgumentParser(description="提示词模板生成器")
    parser.add_argument("--input", type=str, help="JSON格式输入")
    parser.add_argument("--output", type=str, help="输出文件路径（可选）")
    args = parser.parse_args()
    main(args)
