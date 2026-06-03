#!/usr/bin/env python3
"""PDF元信息提取 — 提取PDF的标题/作者/创建时间等元数据"""

import sys
import json
import argparse
import re


def extract_metadata(file_path):
    """提取PDF元信息"""
    try:
        with open(file_path, 'rb') as f:
            data = f.read()
    except FileNotFoundError:
        return {"status": "error", "message": f"文件不存在：{file_path}"}

    if not data.startswith(b'%PDF'):
        return {"status": "error", "message": "不是有效的PDF文件"}

    metadata = {}

    # PDF版本
    version_match = re.search(rb'%PDF-(\d+\.\d+)', data)
    if version_match:
        metadata["pdf_version"] = version_match.group(1).decode()

    # 从Info对象提取元信息
    info_fields = {
        "Title": "title",
        "Author": "author",
        "Subject": "subject",
        "Keywords": "keywords",
        "Creator": "creator",
        "Producer": "producer",
        "CreationDate": "creation_date",
        "ModDate": "modification_date",
    }

    for pdf_field, json_field in info_fields.items():
        pattern = re.compile(rb'/' + pdf_field.encode() + rb'\s*\(([^)]*)\)')
        match = pattern.search(data)
        if match:
            try:
                value = match.group(1).decode('utf-8', errors='replace')
                metadata[json_field] = value
            except:
                pass

    # 页数统计
    page_count = len(re.findall(rb'/Type\s*/Page[^s]', data))
    if page_count == 0:
        # 另一种方式统计
        page_count = len(re.findall(rb'/Type\s*/Page\b', data))
    metadata["page_count"] = page_count

    # 文件大小
    metadata["file_size"] = len(data)
    metadata["file_size_mb"] = round(len(data) / 1024 / 1024, 2)

    # 是否加密
    metadata["is_encrypted"] = b'/Encrypt' in data

    # 是否有嵌入字体
    metadata["has_embedded_fonts"] = b'/Font' in data and b'/FontDescriptor' in data

    # 是否有图片
    metadata["has_images"] = b'/Image' in data or b'/XObject' in data

    return {
        "status": "ok",
        "file": file_path,
        "metadata": metadata
    }


def main(args):
    try:
        if args.input:
            data = json.loads(args.input)
        else:
            data = {}

        file_path = data.get("file", "")
        if not file_path:
            print(json.dumps({"status": "error", "message": "缺少file参数"}, ensure_ascii=False))
            return

        result = extract_metadata(file_path)

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
    parser = argparse.ArgumentParser(description="PDF元信息提取")
    parser.add_argument("--input", type=str, help="JSON格式输入")
    parser.add_argument("--output", type=str, help="输出文件路径（可选）")
    args = parser.parse_args()
    main(args)
