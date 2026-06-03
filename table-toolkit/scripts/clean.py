#!/usr/bin/env python3
"""CSV数据清洗 — 去重、空值处理、格式统一"""

import sys
import json
import argparse
import csv
import io
import math


def load_csv(file_path=None, data_str=None):
    if file_path:
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            return reader.fieldnames or [], list(reader)
    elif data_str:
        reader = csv.DictReader(io.StringIO(data_str))
        return reader.fieldnames or [], list(reader)
    return [], []


def save_csv(headers, rows):
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=headers)
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def clean_data(data):
    file_path = data.get("file", None)
    data_str = data.get("data", None)
    dedup = data.get("dedup", True)
    fill_na = data.get("fill_na", "empty")  # mean/median/zero/drop/empty
    trim_space = data.get("trim_space", True)
    remove_empty_rows = data.get("remove_empty_rows", True)

    if not file_path and not data_str:
        return {"status": "error", "message": "缺少file或data参数"}

    headers, rows = load_csv(file_path, data_str)
    if not rows:
        return {"status": "error", "message": "无数据行"}

    report = {"original_rows": len(rows), "actions": []}
    original_count = len(rows)

    # 1. 去除首尾空白
    if trim_space:
        for row in rows:
            for k in row:
                if isinstance(row[k], str):
                    row[k] = row[k].strip()
        report["actions"].append("去除首尾空白")

    # 2. 去重
    if dedup:
        seen = set()
        unique_rows = []
        for row in rows:
            key = tuple(sorted(row.items()))
            if key not in seen:
                seen.add(key)
                unique_rows.append(row)
        dup_count = len(rows) - len(unique_rows)
        rows = unique_rows
        if dup_count > 0:
            report["actions"].append(f"去除{dup_count}行重复数据")
        else:
            report["actions"].append("无重复数据")

    # 3. 空值处理
    if fill_na != "skip":
        na_count = 0
        # 先计算每列的mean/median
        col_stats = {}
        for h in headers:
            values = [row.get(h, "") for row in rows]
            nums = []
            for v in values:
                try:
                    nums.append(float(v))
                except (ValueError, TypeError):
                    pass
            if nums:
                col_stats[h] = {
                    "mean": round(sum(nums) / len(nums), 4),
                    "median": sorted(nums)[len(nums) // 2],
                }

        for row in rows:
            for h in headers:
                val = row.get(h, "")
                if val == "" or val is None:
                    na_count += 1
                    if fill_na == "mean" and h in col_stats:
                        row[h] = str(col_stats[h]["mean"])
                    elif fill_na == "median" and h in col_stats:
                        row[h] = str(col_stats[h]["median"])
                    elif fill_na == "zero":
                        row[h] = "0"
                    elif fill_na == "empty":
                        row[h] = ""
                    # drop模式在后面处理

        if na_count > 0:
            report["actions"].append(f"处理{na_count}个空值（策略：{fill_na}）")

    # 4. 去除空行
    if remove_empty_rows:
        before = len(rows)
        rows = [r for r in rows if any(v.strip() for v in r.values() if isinstance(v, str))]
        removed = before - len(rows)
        if removed > 0:
            report["actions"].append(f"去除{removed}行空行")

    # 5. drop模式空值行
    if fill_na == "drop":
        before = len(rows)
        rows = [r for r in rows if all(v.strip() for v in r.values() if isinstance(v, str))]
        removed = before - len(rows)
        if removed > 0:
            report["actions"].append(f"去除{removed}行含空值行（drop模式）")

    cleaned_csv = save_csv(headers, rows)
    report["cleaned_rows"] = len(rows)
    report["removed_rows"] = original_count - len(rows)

    return {
        "status": "ok",
        "report": report,
        "row_count": len(rows),
        "data": cleaned_csv
    }


def main(args):
    try:
        if args.input:
            data = json.loads(args.input)
        else:
            data = {}

        result = clean_data(data)

        if args.output and result.get("data"):
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(result["data"])
            result["output_file"] = args.output

        print(json.dumps(result, ensure_ascii=False, indent=2))

    except json.JSONDecodeError:
        print(json.dumps({"status": "error", "message": "输入不是有效的JSON"}, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CSV数据清洗")
    parser.add_argument("--input", type=str, help="JSON格式输入")
    parser.add_argument("--output", type=str, help="输出文件路径（可选）")
    args = parser.parse_args()
    main(args)
