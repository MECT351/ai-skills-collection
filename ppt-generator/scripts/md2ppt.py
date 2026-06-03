#!/usr/bin/env python3
"""Markdown转PPT — 解析Markdown文档，按标题分页生成HTML幻灯片"""

import sys
import json
import argparse
import re


def md2ppt(data):
    markdown = data.get("markdown", "")
    theme_name = data.get("theme", "corporate")
    max_slides = data.get("max_slides", 30)

    if not markdown:
        return {"status": "error", "message": "缺少markdown参数"}

    # 解析Markdown为页面
    pages = parse_markdown(markdown)

    # 引入主题
    from outline import THEMES, generate_cover, generate_ending, wrap_html
    theme = THEMES.get(theme_name, THEMES["corporate"])

    # 提取标题
    title = pages[0]["title"] if pages else "演示文稿"
    if title == "封面":
        title = "演示文稿"

    slides_html = []

    # 封面
    slides_html.append(generate_cover(title, "", "", theme))

    # 内容页
    for i, page in enumerate(pages[:max_slides]):
        points_html = "".join(f'<li>{p}</li>' for p in page.get("points", []))
        if points_html:
            content = f'<ul class="points">{points_html}</ul>'
        else:
            content = f'<p class="placeholder-content">{page.get("body", "")}</p>'

        progress = f'<div class="progress">{i+1}/{min(len(pages), max_slides)}</div>'
        slides_html.append(f'''    <section class="slide content">
        {progress}
        <h2>{page["title"]}</h2>
        {content}
    </section>''')

    # 结尾
    slides_html.append(generate_ending(title, theme))

    html = wrap_html(slides_html, title, theme)

    return {
        "status": "ok",
        "title": title,
        "theme": theme_name,
        "slides_count": len(slides_html),
        "html": html,
    }


def parse_markdown(md):
    """解析Markdown，按h1/h2分页"""
    pages = []
    current = None

    for line in md.split('\n'):
        line = line.strip()

        # h1 作为新页面标题
        h1_match = re.match(r'^#\s+(.+)', line)
        if h1_match:
            if current:
                pages.append(current)
            current = {"title": h1_match.group(1), "points": [], "body": ""}
            continue

        # h2 作为新页面标题
        h2_match = re.match(r'^##\s+(.+)', line)
        if h2_match:
            if current:
                pages.append(current)
            current = {"title": h2_match.group(1), "points": [], "body": ""}
            continue

        if not current:
            current = {"title": "开场", "points": [], "body": ""}

        # 列表项
        li_match = re.match(r'^[-*]\s+(.+)', line)
        if li_match:
            current["points"].append(li_match.group(1))
            continue

        # 有序列表
        ol_match = re.match(r'^\d+\.\s+(.+)', line)
        if ol_match:
            current["points"].append(ol_match.group(1))
            continue

        # 普通文本
        if line and not line.startswith('```'):
            current["body"] += line + " "

    if current:
        pages.append(current)

    return pages


def main(args):
    try:
        if args.input:
            data = json.loads(args.input)
        else:
            data = {}

        result = md2ppt(data)

        if args.output and result.get("html"):
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(result["html"])
            result["output_file"] = args.output
            result.pop("html", None)

        print(json.dumps(result, ensure_ascii=False, indent=2))

    except json.JSONDecodeError:
        print(json.dumps({"status": "error", "message": "输入不是有效的JSON"}, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Markdown转PPT")
    parser.add_argument("--input", type=str, help="JSON格式输入")
    parser.add_argument("--output", type=str, help="输出HTML文件路径（可选）")
    args = parser.parse_args()
    main(args)
