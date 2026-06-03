#!/usr/bin/env python3
"""调度配置生成器 — 生成Calendar日程配置，实现定时监控"""

import sys
import json
import argparse


def generate_schedule(data):
    name = data.get("name", "monitor_task")
    interval = data.get("interval", "HOURLY")
    script = data.get("script", "web_check")
    params = data.get("params", {})
    description = data.get("description", "")

    valid_intervals = {
        "MINUTELY": "每10分钟",
        "HOURLY": "每小时",
        "DAILY": "每天",
        "WEEKLY": "每周",
        "MONTHLY": "每月",
    }

    if interval not in valid_intervals:
        return {"status": "error", "message": f"不支持的间隔：{interval}，可选：{', '.join(valid_intervals.keys())}"}

    valid_scripts = {
        "web_check": "网页变化检测",
        "api_check": "接口状态检查",
        "condition_check": "条件判断",
    }

    if script not in valid_scripts:
        return {"status": "error", "message": f"不支持的脚本：{script}，可选：{', '.join(valid_scripts.keys())}"}

    # 生成调度命令
    script_file = f"{script}.py"
    params_json = json.dumps(params, ensure_ascii=False)

    command = f"python skills/condition-monitor/scripts/{script_file} --input '{params_json}'"

    # 生成Calendar日程工单描述
    schedule_description = f"""## 监控任务：{name}

### 执行步骤
1. 执行命令：{command}
2. 解析输出JSON
3. 如果 alert=true 或 changed=true 或 condition_met=true → 通知用户变更内容
4. 如果无变化 → 输出 NO_REPLY（不打扰用户）

### 监控参数
- 脚本：{valid_scripts[script]}
- 参数：{params_json}

### 通知规则
- 有变化/异常：立即通知用户
- 无变化：静默，不发送任何消息"""

    schedule_summary = f"条件监控 - {name}"

    result = {
        "status": "ok",
        "name": name,
        "interval": interval,
        "interval_desc": valid_intervals[interval],
        "script": script,
        "script_desc": valid_scripts[script],
        "command": command,
        "calendar_config": {
            "summary": schedule_summary,
            "description": schedule_description,
            "rrule": {
                "freq": interval,
                "interval": 10 if interval == "MINUTELY" else 1,
            },
            "time_range": {
                "earliest_schedule_time": "-10min",
                "latest_schedule_time": "+10min",
            }
        },
        "setup_guide": f"请创建Calendar日程：\n- 标题：{schedule_summary}\n- 重复：{valid_intervals[interval]}\n- 描述中包含以上工单内容\n- 系统将按计划自动执行检查"
    }

    return result


def main(args):
    try:
        if args.input:
            data = json.loads(args.input)
        else:
            data = {}

        result = generate_schedule(data)

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
    parser = argparse.ArgumentParser(description="调度配置生成器")
    parser.add_argument("--input", type=str, help="JSON格式输入")
    parser.add_argument("--output", type=str, help="输出文件路径（可选）")
    args = parser.parse_args()
    main(args)
