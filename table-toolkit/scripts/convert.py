#!/usr/bin/env python3
"""CSV格式转换 — CSV/TSV/JSON/Markdown互转"""

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


def load_tsv(file_path=None, data_str=None):
    source = data_str or ""
    if file_path:
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            source = f.read()
    reader = csv.DictReader(io.StringIO(source), delimiter='\t')
    return reader.fieldnames or [], list(reader)


def load_json(data_str):
    data = json.loads(data_str)
    if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
        headers = list(data[0].keys())
        return headers, data
    return [], []


def to_csv(headers, rows):
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=headers)
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def to_tsv(headers, rows):
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=headers, delimiter='\t')
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def to_json(headers, rows):
    return json.dumps(rows, ensure_ascii=False, indent=2)


def to_markdown(headers, rows):
    lines = []
    # 表头
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    # 数据行
    for row in rows:
        cells = [str(row.get(h, "")) for h in headers]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def convert(data):
    file_path = data.get("file", None)
    data_str = data.get("data", None)
    from_fmt = data.get("from", "csv")
    to_fmt = data.get("to", "json")

    # 加载
    if from_fmt == "csv":
        headers, rows = load_csv(file_path, data_str)
    elif from_fmt == "tsv":
        headers, rows = load_tsv(file_path, data_str)
    elif from_fmt == "json":
        if not data_str:
            return {"status": "error", "message": "JSON格式需要data参数"}
        headers, rows = load_json(data_str)
    else:
        return {"status": "error", "message": f"不支持的源格式：{from_fmt}"}

    if not rows:
        return {"status": "error", "message": "无数据"}

    # 转换
    if to_fmt == "csv":
        result_data = to_csv(headers, rows)
    elif to_fmt == "tsv":
        result_data = to_tsv(headers, rows)
    elif to_fmt == "json":
        result_data = to_json(headers, rows)
    elif to_fmt == "markdown":
        result_data = to_markdown(headers, rows)
    else:
        return {"status": "error", "message": f"不支持的目标格式：{to_fmt}"}

    return {
        "status": "ok",
        "from": from_fmt,
        "to": to_fmt,
        "row_count": len(rows),
        "column_count": len(headers),
        "data": result_data
    }


def main(args):
    try:
        if args.input:
            data = json.loads(args.input)
        else:
            data = {}

        result = convert(data)

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
    parser = argparse.ArgumentParser(description="CSV格式转换")
    parser.add_argument("--input", type=str, help="JSON格式输入")
    parser.add_argument("--output", type=str, help="输出文件路径（可选）")
    args = parser.parse_args()
    main(args)
