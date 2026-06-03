#!/usr/bin/env python3
"""PPT内容优化器 — 将长文本拆分为多页幻灯片，每页3-5个要点"""

import sys
import json
import argparse
import re


def optimize_content(data):
    content = data.get("content", "")
    max_slides = data.get("max_slides", 10)
    items_per_slide = data.get("items_per_slide", 5)

    if not content:
        return {"status": "error", "message": "缺少content参数"}

    # 提取要点
    points = extract_points(content)

    # 分页
    slides = []
    for i in range(0, len(points), items_per_slide):
        chunk = points[i:i + items_per_slide]
        slide_num = i // items_per_slide + 1
        slides.append({
            "slide": slide_num,
            "title": f"第{slide_num}页",
            "points": chunk
        })

    # 限制页数
    slides = slides[:max_slides]

    return {
        "status": "ok",
        "total_points": len(points),
        "total_slides": len(slides),
        "slides": slides
    }


def extract_points(text):
    """从文本中提取要点"""
    points = []

    # 先尝试按列表提取
    list_items = re.findall(r'^[-*]\s+(.+)$', text, re.MULTILINE)
    if list_items:
        points.extend(list_items)

    # 按编号列表提取
    ol_items = re.findall(r'^\d+[.、)\s]+(.+)$', text, re.MULTILINE)
    if ol_items:
        points.extend(ol_items)

    # 按句号分割提取
    if not points:
        sentences = re.split(r'[。！？\n]', text)
        for s in sentences:
            s = s.strip()
            if len(s) > 5:
                points.append(s)

    # 如果还是太少，按逗号分割
    if len(points) < 3:
        parts = re.split(r'[,，；;]', text)
        for p in parts:
            p = p.strip()
            if len(p) > 3 and p not in points:
                points.append(p)

    return points


def main(args):
    try:
        if args.input:
            data = json.loads(args.input)
        else:
            data = {}

        result = optimize_content(data)

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
    parser = argparse.ArgumentParser(description="PPT内容优化器")
    parser.add_argument("--input", type=str, help="JSON格式输入")
    parser.add_argument("--output", type=str, help="输出文件路径（可选）")
    args = parser.parse_args()
    main(args)
