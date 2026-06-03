#!/usr/bin/env python3
"""CSV表格合并 — 纵向追加/横向匹配合并多个CSV"""

import sys
import json
import argparse
import csv
import io


def load_csv(file_path=None, data_str=None):
    if file_path:
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            return reader.fieldnames or [], list(reader)
    elif data_str:
        reader = csv.DictReader(io.StringIO(data_str))
        return reader.fieldnames or [], list(reader)
    return [], []


def merge_data(data):
    files = data.get("files", [])
    datasets = data.get("datasets", [])
    mode = data.get("mode", "vertical")
    key = data.get("key", "")

    # 加载数据
    all_headers = []
    all_rows = []

    for item in files:
        h, r = load_csv(file_path=item)
        if h:
            all_headers.append(h)
            all_rows.append(r)

    for item in datasets:
        h, r = load_csv(data_str=item)
        if h:
            all_headers.append(h)
            all_rows.append(r)

    if not all_rows:
        return {"status": "error", "message": "无有效数据源"}

    if mode == "vertical":
        return merge_vertical(all_headers, all_rows)
    elif mode == "horizontal":
        return merge_horizontal(all_headers, all_rows, key)
    else:
        return {"status": "error", "message": f"未知合并模式：{mode}，支持 vertical/horizontal"}


def merge_vertical(all_headers, all_rows):
    """纵向合并（行追加）"""
    # 合并所有列名
    all_cols = []
    seen = set()
    for headers in all_headers:
        for h in headers:
            if h not in seen:
                all_cols.append(h)
                seen.add(h)

    merged_rows = []
    for rows in all_rows:
        for row in rows:
            new_row = {h: row.get(h, "") for h in all_cols}
            merged_rows.append(new_row)

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=all_cols)
    writer.writeheader()
    writer.writerows(merged_rows)

    return {
        "status": "ok",
        "mode": "vertical",
        "column_count": len(all_cols),
        "row_count": len(merged_rows),
        "sources": len(all_rows),
        "data": output.getvalue()
    }


def merge_horizontal(all_headers, all_rows, key):
    """横向合并（列追加，按key匹配）"""
    if not key:
        return {"status": "error", "message": "横向合并需要指定key字段"}

    if len(all_rows) < 2:
        return {"status": "error", "message": "横向合并至少需要2个数据源"}

    # 以第一个表为基础
    base_rows = all_rows[0]
    base_headers = all_headers[0]

    # 构建查找表
    for i in range(1, len(all_rows)):
        lookup = {}
        extra_headers = []
        for row in all_rows[i]:
            k = row.get(key, "")
            if k:
                lookup[k] = row

        # 收集新列名（排除key）
        for h in all_headers[i]:
            if h != key and h not in base_headers:
                extra_headers.append(h)

        base_headers = base_headers + extra_headers

        # 匹配合并
        for base_row in base_rows:
            k = base_row.get(key, "")
            if k in lookup:
                for h in extra_headers:
                    base_row[h] = lookup[k].get(h, "")
            else:
                for h in extra_headers:
                    base_row[h] = ""

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=base_headers)
    writer.writeheader()
    writer.writerows(base_rows)

    matched = sum(1 for r in base_rows if any(r.get(h, "") for h in base_headers if h != key))

    return {
        "status": "ok",
        "mode": "horizontal",
        "key": key,
        "column_count": len(base_headers),
        "row_count": len(base_rows),
        "matched_rows": matched,
        "data": output.getvalue()
    }


def main(args):
    try:
        if args.input:
            data = json.loads(args.input)
        else:
            data = {}

        result = merge_data(data)

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
    parser = argparse.ArgumentParser(description="CSV表格合并")
    parser.add_argument("--input", type=str, help="JSON格式输入")
    parser.add_argument("--output", type=str, help="输出文件路径（可选）")
    args = parser.parse_args()
    main(args)
