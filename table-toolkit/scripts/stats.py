#!/usr/bin/env python3
"""CSV统计分析 — 输入CSV数据，输出描述性统计"""

import sys
import json
import argparse
import csv
import io
import math


def load_csv(file_path=None, data_str=None):
    """加载CSV数据"""
    if file_path:
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames or []
            rows = list(reader)
    elif data_str:
        reader = csv.DictReader(io.StringIO(data_str))
        headers = reader.fieldnames or []
        rows = list(reader)
    else:
        return [], []
    return headers, rows


def is_numeric(value):
    """判断是否为数值"""
    if value is None or value.strip() == '':
        return False
    try:
        float(value)
        return True
    except ValueError:
        return False


def compute_stats(values):
    """计算统计量"""
    nums = [float(v) for v in values if is_numeric(v)]
    if not nums:
        return None

    nums.sort()
    n = len(nums)
    mean = sum(nums) / n
    variance = sum((x - mean) ** 2 for x in nums) / max(n - 1, 1)
    std = math.sqrt(variance)

    def percentile(p):
        k = (n - 1) * p
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return nums[int(k)]
        return nums[int(f)] * (c - k) + nums[int(c)] * (k - f)

    return {
        "count": n,
        "mean": round(mean, 4),
        "std": round(std, 4),
        "min": nums[0],
        "max": nums[-1],
        "median": round(percentile(0.5), 4),
        "p25": round(percentile(0.25), 4),
        "p75": round(percentile(0.75), 4),
    }


def analyze(data):
    file_path = data.get("file", None)
    data_str = data.get("data", None)

    if not file_path and not data_str:
        return {"status": "error", "message": "缺少file或data参数"}

    headers, rows = load_csv(file_path, data_str)
    if not rows:
        return {"status": "error", "message": "无数据行"}

    columns = {}
    for h in headers:
        values = [row.get(h, "") for row in rows]
        numeric_values = [v for v in values if is_numeric(v)]

        if numeric_values:
            stats = compute_stats(values)
            columns[h] = {
                "type": "numeric",
                "non_null": len(numeric_values),
                "null_count": len(values) - len(numeric_values),
                "stats": stats
            }
        else:
            # 文本列统计
            non_empty = [v for v in values if v.strip()]
            unique = list(set(non_empty))
            # 频率统计 top5
            freq = {}
            for v in non_empty:
                freq[v] = freq.get(v, 0) + 1
            top5 = sorted(freq.items(), key=lambda x: -x[1])[:5]

            columns[h] = {
                "type": "text",
                "non_null": len(non_empty),
                "null_count": len(values) - len(non_empty),
                "unique_count": len(unique),
                "top_values": [{"value": k, "count": v} for k, v in top5]
            }

    return {
        "status": "ok",
        "row_count": len(rows),
        "column_count": len(headers),
        "columns": columns
    }


def main(args):
    try:
        if args.input:
            data = json.loads(args.input)
        else:
            data = {}

        result = analyze(data)

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
    parser = argparse.ArgumentParser(description="CSV统计分析")
    parser.add_argument("--input", type=str, help="JSON格式输入")
    parser.add_argument("--output", type=str, help="输出文件路径（可选）")
    args = parser.parse_args()
    main(args)
