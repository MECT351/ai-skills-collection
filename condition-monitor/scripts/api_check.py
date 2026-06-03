#!/usr/bin/env python3
"""接口状态检查 — 检查API是否正常、返回值是否变化"""

import sys
import json
import argparse
import hashlib
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


def check_api(data):
    url = data.get("url", "")
    name = data.get("name", "api_default")
    method = data.get("method", "GET").upper()
    headers = data.get("headers", {})
    body = data.get("body", None)
    timeout = data.get("timeout", 10)
    expected_status = data.get("expected_status", 200)
    expected_field = data.get("expected_field", "")
    expected_value = data.get("expected_value", "")
    check_response_change = data.get("check_response_change", False)

    if not url:
        return {"status": "error", "message": "缺少url参数"}

    # 请求API
    req_headers = {
        "User-Agent": "Mozilla/5.0 ConditionMonitor/1.0",
        "Accept": "application/json, text/plain, */*",
    }
    req_headers.update(headers)

    try:
        req = Request(url, headers=req_headers, method=method)
        if body:
            req.data = json.dumps(body).encode('utf-8') if isinstance(body, dict) else body.encode('utf-8')

        with urlopen(req, timeout=timeout) as response:
            status_code = response.status
            response_body = response.read().decode('utf-8', errors='replace')

    except HTTPError as e:
        return {
            "status": "ok", "name": name,
            "alert": True,
            "message": f"API返回错误状态码 {e.code}",
            "is_healthy": False,
            "status_code": e.code
        }
    except URLError as e:
        return {
            "status": "ok", "name": name,
            "alert": True,
            "message": f"API不可达: {e.reason}",
            "is_healthy": False
        }
    except Exception as e:
        return {
            "status": "ok", "name": name,
            "alert": True,
            "message": f"请求失败: {str(e)}",
            "is_healthy": False
        }

    # 基础状态检查
    is_healthy = status_code == expected_status
    result = {
        "status": "ok",
        "name": name,
        "url": url,
        "is_healthy": is_healthy,
        "status_code": status_code,
        "expected_status": expected_status,
    }

    alerts = []
    if not is_healthy:
        alerts.append(f"状态码异常：期望{expected_status}，实际{status_code}")

    # 解析响应体
    response_data = None
    try:
        response_data = json.loads(response_body)
    except (json.JSONDecodeError, ValueError):
        pass

    # 字段值检查
    if expected_field and response_data:
        actual_value = _get_nested(response_data, expected_field)
        if actual_value is not None:
            field_match = str(actual_value) == str(expected_value)
            result["field_check"] = {
                "field": expected_field,
                "expected": expected_value,
                "actual": actual_value,
                "match": field_match
            }
            if not field_match:
                alerts.append(f"字段{expected_field}异常：期望{expected_value}，实际{actual_value}")
        else:
            alerts.append(f"字段{expected_field}不存在于响应中")

    # 响应体变化检测
    if check_response_change:
        current_hash = hashlib.md5(response_body.encode('utf-8')).hexdigest()
        baseline = load_state(name, "api_hash")

        if baseline is None:
            save_state(name, "api_hash", {"hash": current_hash})
            result["response_change"] = "首次检查，已建立基线"
        elif baseline.get("hash") != current_hash:
            alerts.append("API响应内容发生变化")
            result["response_change"] = "已变化"
            save_state(name, "api_hash", {"hash": current_hash})
        else:
            result["response_change"] = "无变化"

    # 汇总
    if alerts:
        result["alert"] = True
        result["message"] = "；".join(alerts)
    else:
        result["message"] = "API状态正常"

    return result


def _get_nested(data, field_path):
    """获取嵌套字段值，支持 a.b.c 格式"""
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


def main(args):
    try:
        if args.input:
            data = json.loads(args.input)
        else:
            data = {}

        result = check_api(data)

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
    parser = argparse.ArgumentParser(description="接口状态检查")
    parser.add_argument("--input", type=str, help="JSON格式输入")
    parser.add_argument("--output", type=str, help="输出文件路径（可选）")
    args = parser.parse_args()
    main(args)
