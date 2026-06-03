#!/usr/bin/env python3
"""条件判断检查 — 获取数据并判断条件是否满足"""

import sys
import json
import argparse
import os
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


STATE_DIR = "monitor_state"


def load_state(name, suffix):
    path = os.path.join(STATE_DIR, f"{name}_{suffix}.json")
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


def save_state(name, suffix, data):
    os.makedirs(STATE_DIR, exist_ok=True)
    path = os.path.join(STATE_DIR, f"{name}_{suffix}.json")
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def check_condition(data):
    name = data.get("name", "condition_default")
    data_source = data.get("data_source", "url")
    url = data.get("url", "")
    field = data.get("field", "")
    operator = data.get("operator", "==")
    threshold = data.get("threshold", "")
    raw_data = data.get("raw_data", None)
    timeout = data.get("timeout", 10)

    # 获取数据
    current_value = None

    if data_source == "url" and url:
        try:
            req = Request(url, headers={"User-Agent": "ConditionMonitor/1.0", "Accept": "application/json"})
            with urlopen(req, timeout=timeout) as response:
                body = response.read().decode('utf-8', errors='replace')
                resp_data = json.loads(body)
                current_value = _get_nested(resp_data, field) if field else resp_data
        except HTTPError as e:
            return {"status": "error", "message": f"HTTP {e.code}", "alert": True}
        except URLError as e:
            return {"status": "error", "message": f"URL错误: {e.reason}", "alert": True}
        except Exception as e:
            return {"status": "error", "message": str(e), "alert": True}
    elif data_source == "raw" and raw_data is not None:
        if isinstance(raw_data, dict):
            current_value = _get_nested(raw_data, field) if field else raw_data
        else:
            current_value = raw_data
    else:
        return {"status": "error", "message": "缺少data_source配置"}

    # 判断条件
    condition_met = _evaluate(current_value, operator, threshold)

    result = {
        "status": "ok",
        "name": name,
        "current_value": current_value,
        "operator": operator,
        "threshold": threshold,
        "condition_met": condition_met,
    }

    if condition_met:
        result["alert"] = True
        result["message"] = f"条件已满足：{field or '值'} {operator} {threshold}（当前值：{current_value}）"
    else:
        result["message"] = f"条件未满足：{field or '值'} {operator} {threshold}（当前值：{current_value}）"

    # 记录历史
    history = load_state(name, "condition_history") or {"records": []}
    history["records"].append({
        "timestamp": _now(),
        "value": current_value,
        "condition_met": condition_met,
    })
    history["records"] = history["records"][-50:]
    save_state(name, "condition_history", history)

    return result


def _evaluate(current, operator, threshold):
    """判断条件"""
    try:
        # 尝试数值比较
        num_current = float(current) if current is not None else None
        num_threshold = float(threshold)
        is_numeric = True
    except (ValueError, TypeError):
        is_numeric = False

    if operator == ">" and is_numeric:
        return num_current > num_threshold
    elif operator == "<" and is_numeric:
        return num_current < num_threshold
    elif operator == ">=" and is_numeric:
        return num_current >= num_threshold
    elif operator == "<=" and is_numeric:
        return num_current <= num_threshold
    elif operator == "==":
        return str(current) == str(threshold)
    elif operator == "!=":
        return str(current) != str(threshold)
    elif operator == "contains":
        return str(threshold) in str(current)
    elif operator == "not_contains":
        return str(threshold) not in str(current)
    else:
        return False


def _get_nested(data, field_path):
    keys = field_path.split('.')
    current = data
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key)
        elif isinstance(current, list):
            try:
                current = current[int(key)]
            except (ValueError, IndexError):
                return None
        else:
            return None
        if current is None:
            return None
    return current


def _now():
    from datetime import datetime
    return datetime.now().isoformat()


def main(args):
    try:
        if args.input:
            data = json.loads(args.input)
        else:
            data = {}

        result = check_condition(data)

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
    parser = argparse.ArgumentParser(description="条件判断检查")
    parser.add_argument("--input", type=str, help="JSON格式输入")
    parser.add_argument("--output", type=str, help="输出文件路径（可选）")
    args = parser.parse_args()
    main(args)
