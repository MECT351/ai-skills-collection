#!/usr/bin/env python3
"""PPT主题管理 — 查看/获取内置主题样式"""

import sys
import json
import argparse

THEMES = {
    "corporate": {
        "name": "商务蓝",
        "description": "专业商务风格，深蓝渐变背景，适合企业汇报",
        "preview": "深蓝 → 宝蓝渐变 | 白色标题 | 蓝色强调色",
        "colors": {"bg": "#1a237e → #1565c0", "title": "#ffffff", "text": "#e3f2fd", "accent": "#42a5f5"}
    },
    "tech-dark": {
        "name": "科技暗黑",
        "description": "暗黑科技风格，适合技术分享和产品发布",
        "preview": "纯黑 → 深蓝渐变 | 青色标题 | 青色强调色",
        "colors": {"bg": "#0d0d0d → #16213e", "title": "#00d4ff", "text": "#e0e0e0", "accent": "#00d4ff"}
    },
    "creative": {
        "name": "创意渐变",
        "description": "紫蓝渐变风格，适合创意提案和品牌展示",
        "preview": "蓝紫渐变 | 白色标题 | 粉色强调色",
        "colors": {"bg": "#667eea → #764ba2", "title": "#ffffff", "text": "#f3e5f5", "accent": "#ff6b9d"}
    },
    "minimal": {
        "name": "极简白",
        "description": "简洁白底风格，适合教学和轻量演示",
        "preview": "纯白背景 | 深色标题 | 蓝色强调色",
        "colors": {"bg": "#ffffff", "title": "#1a1a1a", "text": "#333333", "accent": "#2196f3"}
    },
    "nature": {
        "name": "自然绿",
        "description": "自然绿色风格，适合环保/健康/农业主题",
        "preview": "深绿渐变 | 白色标题 | 绿色强调色",
        "colors": {"bg": "#1b5e20 → #388e3c", "title": "#ffffff", "text": "#e8f5e9", "accent": "#69f0ae"}
    }
}


def list_themes():
    result = []
    for key, theme in THEMES.items():
        result.append({
            "id": key,
            "name": theme["name"],
            "description": theme["description"],
            "preview": theme["preview"],
            "colors": theme["colors"]
        })
    return {"status": "ok", "action": "list", "themes": result}


def get_theme(theme_id):
    if theme_id not in THEMES:
        return {"status": "error", "message": f"未知主题：{theme_id}，可选：{', '.join(THEMES.keys())}"}
    theme = THEMES[theme_id]
    return {
        "status": "ok",
        "action": "get",
        "id": theme_id,
        "name": theme["name"],
        "description": theme["description"],
        "colors": theme["colors"]
    }


def main(args):
    try:
        if args.input:
            data = json.loads(args.input)
        else:
            data = {}

        action = data.get("action", "list")
        theme_id = data.get("theme", "")

        if action == "list":
            result = list_themes()
        elif action == "get":
            result = get_theme(theme_id)
        else:
            result = {"status": "error", "message": f"未知action：{action}"}

        print(json.dumps(result, ensure_ascii=False, indent=2))

    except json.JSONDecodeError:
        print(json.dumps({"status": "error", "message": "输入不是有效的JSON"}, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PPT主题管理")
    parser.add_argument("--input", type=str, help="JSON格式输入")
    args = parser.parse_args()
    main(args)
