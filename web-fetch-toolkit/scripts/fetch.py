#!/usr/bin/env python3
"""单URL网页抓取器 — 抓取网页内容，提取标题+正文+元信息"""

import sys
import json
import argparse
import re
from html.parser import HTMLParser
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from urllib.parse import urlparse


class HTMLPageParser(HTMLParser):
    """解析HTML提取结构化信息"""

    TAGS_NO_CONTENT = {'script', 'style', 'noscript', 'header', 'footer', 'nav', 'aside'}
    BLOCK_TAGS = {'p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'tr', 'br', 'hr', 'blockquote', 'pre'}

    def __init__(self):
        super().__init__()
        self.title = ""
        self.meta = {}
        self.content_parts = []
        self._skip_depth = 0
        self._current_tag = ""
        self._title_depth = 0
        self._text_buffer = ""

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        self._current_tag = tag
        attrs_dict = dict(attrs)

        if tag in self.TAGS_NO_CONTENT:
            self._skip_depth += 1
            return

        if tag == "title":
            self._title_depth += 1

        if tag == "meta":
            name = attrs_dict.get("name", attrs_dict.get("property", "")).lower()
            content = attrs_dict.get("content", "")
            if name and content:
                self.meta[name] = content

        if tag in self.BLOCK_TAGS and self._text_buffer.strip():
            self.content_parts.append(self._text_buffer.strip())
            self._text_buffer = ""

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in self.TAGS_NO_CONTENT:
            self._skip_depth = max(0, self._skip_depth - 1)
            return

        if tag == "title":
            self._title_depth = max(0, self._title_depth - 1)

        if tag in self.BLOCK_TAGS and self._text_buffer.strip():
            self.content_parts.append(self._text_buffer.strip())
            self._text_buffer = ""

    def handle_data(self, data):
        if self._skip_depth > 0:
            return

        text = data.strip()
        if not text:
            return

        if self._title_depth > 0:
            self.title = text
            return

        self._text_buffer += " " + text

    def get_content(self):
        if self._text_buffer.strip():
            self.content_parts.append(self._text_buffer.strip())
        # 去重相邻重复，合并短段落
        seen = set()
        result = []
        for part in self.content_parts:
            if len(part) < 3:
                continue
            key = part[:100]
            if key not in seen:
                seen.add(key)
                result.append(part)
        return "\n\n".join(result)


def detect_encoding(response, html_bytes):
    """检测网页编码"""
    content_type = response.headers.get("Content-Type", "")
    # 1. 从Content-Type检测
    charset_match = re.search(r'charset=([^\s;]+)', content_type, re.IGNORECASE)
    if charset_match:
        enc = charset_match.group(1).strip('"\'')
        try:
            html_bytes.decode(enc)
            return enc
        except (UnicodeDecodeError, LookupError):
            pass

    # 2. 从meta标签检测
    meta_match = re.search(rb'charset=["\']?([^\s"\'/>]+)', html_bytes[:2048], re.IGNORECASE)
    if meta_match:
        enc = meta_match.group(1).decode('ascii', errors='ignore').strip()
        try:
            html_bytes.decode(enc)
            return enc
        except (UnicodeDecodeError, LookupError):
            pass

    # 3. 默认UTF-8
    return 'utf-8'


def fetch_url(url, timeout=10):
    """抓取单个URL"""
    import time
    start_time = time.time()

    parsed = urlparse(url)
    if not parsed.scheme:
        url = "https://" + url

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }

    try:
        req = Request(url, headers=headers)
        with urlopen(req, timeout=timeout) as response:
            html_bytes = response.read()
            encoding = detect_encoding(response, html_bytes)
            html = html_bytes.decode(encoding, errors='replace')

        parser = HTMLPageParser()
        parser.feed(html)

        fetch_time = int((time.time() - start_time) * 1000)

        content = parser.get_content()

        return {
            "status": "ok",
            "url": url,
            "title": parser.title or "",
            "content": content,
            "meta": {
                "description": parser.meta.get("description", ""),
                "keywords": parser.meta.get("keywords", ""),
                "author": parser.meta.get("author", ""),
                "og_title": parser.meta.get("og:title", ""),
                "og_description": parser.meta.get("og:description", ""),
            },
            "stats": {
                "content_length": len(content),
                "fetch_time_ms": fetch_time,
                "encoding": encoding
            }
        }

    except HTTPError as e:
        return {"status": "error", "url": url, "message": f"HTTP {e.code}: {e.reason}"}
    except URLError as e:
        return {"status": "error", "url": url, "message": f"URL错误: {str(e.reason)}"}
    except Exception as e:
        return {"status": "error", "url": url, "message": str(e)}


def main(args):
    try:
        if args.input:
            data = json.loads(args.input)
        else:
            data = {}

        url = data.get("url", "")
        timeout = data.get("timeout", 10)

        if not url:
            print(json.dumps({"status": "error", "message": "缺少url参数"}, ensure_ascii=False))
            return

        result = fetch_url(url, timeout)

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
    parser = argparse.ArgumentParser(description="单URL网页抓取器")
    parser.add_argument("--input", type=str, help="JSON格式输入，含url字段")
    parser.add_argument("--output", type=str, help="输出文件路径（可选）")
    args = parser.parse_args()
    main(args)
