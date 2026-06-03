#!/usr/bin/env python3
"""PDF页面提取 — 提取指定页码的文本"""

import sys
import json
import argparse
import re
import zlib


def extract_pages_text(file_path, page_numbers):
    """提取指定页面的文本"""
    try:
        with open(file_path, 'rb') as f:
            data = f.read()
    except FileNotFoundError:
        return {"status": "error", "message": f"文件不存在：{file_path}"}

    if not data.startswith(b'%PDF'):
        return {"status": "error", "message": "不是有效的PDF文件"}

    # 提取所有页面文本
    all_pages = _extract_all_pages(data)

    if not all_pages:
        return {"status": "ok", "file": file_path, "pages": {},
                "warning": "未提取到文本，可能是扫描件/图片PDF"}

    # 筛选指定页面
    result_pages = {}
    for pn in page_numbers:
        if 1 <= pn <= len(all_pages):
            result_pages[str(pn)] = all_pages[pn - 1]
        else:
            result_pages[str(pn)] = f"[页码超出范围，PDF共{len(all_pages)}页]"

    return {
        "status": "ok",
        "file": file_path,
        "total_pages": len(all_pages),
        "requested_pages": list(result_pages.keys()),
        "pages": result_pages
    }


def _extract_all_pages(data):
    """提取所有页面文本"""
    from extract_all import extract_pages
    return extract_pages(data)


def main(args):
    try:
        if args.input:
            data = json.loads(args.input)
        else:
            data = {}

        file_path = data.get("file", "")
        pages = data.get("pages", [1])

        if not file_path:
            print(json.dumps({"status": "error", "message": "缺少file参数"}, ensure_ascii=False))
            return

        result = extract_pages_text(file_path, pages)

        if args.output and result.get("pages"):
            with open(args.output, 'w', encoding='utf-8') as f:
                for pn, text in result["pages"].items():
                    f.write(f"=== 第{pn}页 ===\n{text}\n\n")
            result["output_file"] = args.output

        print(json.dumps(result, ensure_ascii=False, indent=2))

    except json.JSONDecodeError:
        print(json.dumps({"status": "error", "message": "输入不是有效的JSON"}, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PDF页面提取")
    parser.add_argument("--input", type=str, help="JSON格式输入")
    parser.add_argument("--output", type=str, help="输出文本文件路径（可选）")
    args = parser.parse_args()
    main(args)
