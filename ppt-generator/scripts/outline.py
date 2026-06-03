#!/usr/bin/env python3
"""大纲转幻灯片 — 输入主题和大纲，生成HTML演示文稿"""

import sys
import json
import argparse


THEMES = {
    "corporate": {
        "name": "商务蓝",
        "bg": "linear-gradient(135deg, #1a237e 0%, #283593 50%, #1565c0 100%)",
        "title_color": "#ffffff",
        "text_color": "#e3f2fd",
        "accent": "#42a5f5",
    },
    "tech-dark": {
        "name": "科技暗黑",
        "bg": "linear-gradient(135deg, #0d0d0d 0%, #1a1a2e 50%, #16213e 100%)",
        "title_color": "#00d4ff",
        "text_color": "#e0e0e0",
        "accent": "#00d4ff",
    },
    "creative": {
        "name": "创意渐变",
        "bg": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        "title_color": "#ffffff",
        "text_color": "#f3e5f5",
        "accent": "#ff6b9d",
    },
    "minimal": {
        "name": "极简白",
        "bg": "#ffffff",
        "title_color": "#1a1a1a",
        "text_color": "#333333",
        "accent": "#2196f3",
    },
    "nature": {
        "name": "自然绿",
        "bg": "linear-gradient(135deg, #1b5e20 0%, #2e7d32 50%, #388e3c 100%)",
        "title_color": "#ffffff",
        "text_color": "#e8f5e9",
        "accent": "#69f0ae",
    },
}


def generate_ppt(data):
    topic = data.get("topic", "")
    outline = data.get("outline", [])
    theme_name = data.get("theme", "corporate")
    max_slides = data.get("max_slides", 20)
    subtitle = data.get("subtitle", "")
    author = data.get("author", "")

    if not topic:
        return {"status": "error", "message": "缺少topic参数"}
    if not outline:
        return {"status": "error", "message": "缺少outline参数"}

    theme = THEMES.get(theme_name, THEMES["corporate"])
    slides_html = []

    # 封面页
    slides_html.append(generate_cover(topic, subtitle, author, theme))

    # 目录页（如果大纲超过3项）
    if len(outline) > 3:
        slides_html.append(generate_toc(topic, outline, theme))

    # 内容页
    for i, item in enumerate(outline[:max_slides]):
        if isinstance(item, str):
            slides_html.append(generate_content_page(item, [], i+1, len(outline), theme))
        elif isinstance(item, dict):
            title = item.get("title", "")
            points = item.get("points", [])
            slides_html.append(generate_content_page(title, points, i+1, len(outline), theme))

    # 结尾页
    slides_html.append(generate_ending(topic, theme))

    html = wrap_html(slides_html, topic, theme)

    return {
        "status": "ok",
        "topic": topic,
        "theme": theme_name,
        "theme_name": theme["name"],
        "slides_count": len(slides_html),
        "html": html,
    }


def generate_cover(topic, subtitle, author, theme):
    return f'''    <section class="slide cover">
        <h1>{topic}</h1>
        {f'<p class="subtitle">{subtitle}</p>' if subtitle else ''}
        {f'<p class="author">{author}</p>' if author else ''}
    </section>'''


def generate_toc(topic, outline, theme):
    items = []
    for i, item in enumerate(outline):
        title = item if isinstance(item, str) else item.get("title", "")
        items.append(f'<li><span class="toc-num">{i+1:02d}</span> {title}</li>')
    return f'''    <section class="slide toc">
        <h2>目录</h2>
        <ol class="toc-list">{"".join(items)}</ol>
    </section>'''


def generate_content_page(title, points, current, total, theme):
    progress = f'<div class="progress">{current}/{total}</div>'
    if points:
        points_html = "".join(f'<li>{p}</li>' for p in points)
        content = f'<ul class="points">{points_html}</ul>'
    else:
        content = f'<div class="placeholder-content"><p>（在此添加详细内容）</p></div>'
    return f'''    <section class="slide content">
        {progress}
        <h2>{title}</h2>
        {content}
    </section>'''


def generate_ending(topic, theme):
    return f'''    <section class="slide ending">
        <h1>Thank You</h1>
        <p class="subtitle">{topic}</p>
    </section>'''


def wrap_html(slides, title, theme):
    slides_joined = "\n\n".join(slides)
    is_dark = theme_name_is_dark(theme)
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", "Microsoft YaHei", sans-serif;
            background: {theme["bg"]};
            color: {theme["text_color"]};
            overflow: hidden;
            height: 100vh;
        }}
        .slide {{
            display: none;
            width: 100vw;
            height: 100vh;
            padding: 60px 80px;
            flex-direction: column;
            justify-content: center;
            position: relative;
        }}
        .slide.active {{ display: flex; }}
        .slide.cover, .slide.ending {{
            align-items: center;
            text-align: center;
        }}
        .slide h1 {{
            font-size: 3.2em;
            color: {theme["title_color"]};
            margin-bottom: 20px;
            letter-spacing: 2px;
        }}
        .slide h2 {{
            font-size: 2.4em;
            color: {theme["title_color"]};
            margin-bottom: 40px;
            border-left: 5px solid {theme["accent"]};
            padding-left: 20px;
        }}
        .subtitle {{ font-size: 1.4em; opacity: 0.8; margin-top: 10px; }}
        .author {{ font-size: 1.1em; opacity: 0.6; margin-top: 30px; }}
        .progress {{
            position: absolute;
            top: 30px;
            right: 40px;
            font-size: 0.9em;
            opacity: 0.5;
        }}
        .points {{ list-style: none; font-size: 1.3em; line-height: 2.2; }}
        .points li::before {{
            content: "▸";
            color: {theme["accent"]};
            margin-right: 12px;
            font-weight: bold;
        }}
        .toc-list {{ list-style: none; font-size: 1.4em; line-height: 2.5; }}
        .toc-num {{
            color: {theme["accent"]};
            font-weight: bold;
            margin-right: 16px;
            font-size: 0.9em;
        }}
        .placeholder-content {{ opacity: 0.4; font-size: 1.2em; margin-top: 30px; }}
        .nav-hint {{
            position: fixed;
            bottom: 20px;
            right: 30px;
            font-size: 0.8em;
            opacity: 0.3;
        }}
    </style>
</head>
<body>
{slides_joined}
    <div class="nav-hint">← → 翻页 | 空格下一页</div>
    <script>
        let current = 0;
        const slides = document.querySelectorAll('.slide');
        function show(n) {{
            slides.forEach(s => s.classList.remove('active'));
            current = Math.max(0, Math.min(n, slides.length - 1));
            slides[current].classList.add('active');
        }}
        show(0);
        document.addEventListener('keydown', e => {{
            if (e.key === 'ArrowRight' || e.key === ' ' || e.key === 'ArrowDown') show(current + 1);
            if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') show(current - 1);
            if (e.key === 'Home') show(0);
            if (e.key === 'End') show(slides.length - 1);
        }});
    </script>
</body>
</html>'''


def theme_name_is_dark(theme):
    return "dark" in theme.get("bg", "") or theme["title_color"] == "#ffffff"


def main(args):
    try:
        if args.input:
            data = json.loads(args.input)
        else:
            data = {}

        result = generate_ppt(data)

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
    parser = argparse.ArgumentParser(description="大纲转幻灯片")
    parser.add_argument("--input", type=str, help="JSON格式输入")
    parser.add_argument("--output", type=str, help="输出HTML文件路径（可选）")
    args = parser.parse_args()
    main(args)
