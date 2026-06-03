#!/usr/bin/env python3
"""网页变化检测 — 记录指纹基线，对比发现变化"""

import sys
import json
import argparse
import hashlib
import os
import re
from html.parser import HTMLParser
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


STATE_DIR = "monitor_state"


class TextExtractor(HTMLParser):
    """提取网页可见文本"""
    SKIP_TAGS = {'script', 'style', 'noscript', 'header', 'footer', 'nav', 'aside'}

    def __init__(self):
        super().__init__()
        self.text_parts = []
        self._skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag.lower() in self.SKIP_TAGS:
            self._skip_depth += 1

    def handle_endtag(self, tag):
        if tag.lower() in self.SKIP_TAGS:
            self._skip_depth = max(0, self._skip_depth - 1)

    def handle_data(self, data):
        if self._skip_depth == 0:
            text = data.strip()
            if text:
                self.text_parts.append(text)


def compute_hash(content):
    """计算内容指纹"""
    return hashlib.md5(content.encode('utf-8')).hexdigest()


def load_state(name, suffix):
    """加载状态文件"""
    path = os.path.join(STATE_DIR, f"{name}_{suffix}.json")
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


def save_state(name, suffix, data):
    """保存状态文件"""
    os.makedirs(STATE_DIR, exist_ok=True)
    path = os.path.join(STATE_DIR, f"{name}_{suffix}.json")
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def check_web(data):
    url = data.get("url", "")
    name = data.get("name", "default")
    check_hash = data.get("check_hash", True)
    check_keywords = data.get("check_keywords", [])
    timeout = data.get("timeout", 15)

    if not url:
        return {"status": "error", "message": "缺少url参数"}

    # 抓取页面
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml",
    }

    try:
        req = Request(url, headers=headers)
        with urlopen(req, timeout=timeout) as response:
            html_bytes = response.read()
            # 检测编码
            content_type = response.headers.get("Content-Type", "")
            import re as _re
            charset_match = _re.search(r'charset=([^\s;]+)', content_type, re.IGNORECASE)
            encoding = charset_match.group(1).strip('"\'') if charset_match else 'utf-8'
            try:
                html = html_bytes.decode(encoding)
            except (UnicodeDecodeError, LookupError):
                html = html_bytes.decode('utf-8', errors='replace')
    except HTTPError as e:
        return {"status": "error", "message": f"HTTP {e.code}: {e.reason}", "alert": True}
    except URLError as e:
        return {"status": "error", "message": f"URL错误: {e.reason}", "alert": True}
    except Exception as e:
        return {"status": "error", "message": str(e), "alert": True}

    # 提取文本
    extractor = TextExtractor()
    extractor.feed(html)
    text_content = "\n".join(extractor.text_parts)
    current_hash = compute_hash(text_content)

    # 加载历史基线
    baseline = load_state(name, "hash")
    is_first_check = baseline is None

    result = {
        "status": "ok",
        "name": name,
        "url": url,
        "is_first_check": is_first_check,
        "current_hash": current_hash,
    }

    if is_first_check:
        # 首次检查，建立基线
        save_state(name, "hash", {"hash": current_hash, "url": url, "text_length": len(text_content)})
        save_state(name, "last", {"hash": current_hash, "text_length": len(text_content), "timestamp": _now()})
        result["message"] = "已建立监控基线，后续检查将对比此次内容"
        result["changed"] = False
        return result

    # 对比指纹
    old_hash = baseline.get("hash", "")
    hash_changed = current_hash != old_hash

    result["changed"] = hash_changed
    result["old_hash"] = old_hash

    if hash_changed:
        result["message"] = "检测到网页内容变化！"
        result["alert"] = True

        # 更新基线
        save_state(name, "hash", {"hash": current_hash, "url": url, "text_length": len(text_content)})

        # 记录历史
        history = load_state(name, "history") or {"records": []}
        history["records"].append({
            "timestamp": _now(),
            "old_hash": old_hash,
            "new_hash": current_hash,
        })
        # 只保留最近20条
        history["records"] = history["records"][-20:]
        save_state(name, "history", history)
    else:
        result["message"] = "无变化"

    # 关键词检测
    if check_keywords:
        found_keywords = [kw for kw in check_keywords if kw in text_content]
        result["keywords_found"] = found_keywords
        if found_keywords:
            result["message"] += f" | 发现关键词：{', '.join(found_keywords)}"
            result["alert"] = True

    # 更新上次检查结果
    save_state(name, "last", {"hash": current_hash, "text_length": len(text_content), "timestamp": _now()})

    return result


def _now():
    from datetime import datetime
    return datetime.now().isoformat()


def main(args):
    try:
        if args.input:
            data = json.loads(args.input)
        else:
            data = {}

        result = check_web(data)

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
    parser = argparse.ArgumentParser(description="网页变化检测")
    parser.add_argument("--input", type=str, help="JSON格式输入")
    parser.add_argument("--output", type=str, help="输出文件路径（可选）")
    args = parser.parse_args()
    main(args)
