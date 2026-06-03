#!/usr/bin/env python3
"""网页元素提取器 — 按CSS选择器精准提取网页指定内容"""

import sys
import json
import argparse
import re
from html.parser import HTMLParser
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from urllib.parse import urlparse


class ElementExtractor(HTMLParser):
    """按标签/class/id/属性提取元素"""

    def __init__(self, selector):
        super().__init__()
        self.selector = selector
        self.target_tag = selector.get("tag", "").lower()
        self.target_class = selector.get("class", "")
        self.target_id = selector.get("id", "")
        self.target_attr = selector.get("attr", "")

        self.results = []
        self._current_depth = 0
        self._in_target = False
        self._target_depth = 0
        self._target_text = ""
        self._target_attrs = {}
        self._skip_tags = {'script', 'style', 'noscript'}

    def _match_selector(self, tag, attrs):
        """检查元素是否匹配选择器"""
        attrs_dict = dict(attrs)
        tag = tag.lower()

        # tag匹配
        if self.target_tag and tag != self.target_tag:
            return False

        # class匹配
        if self.target_class:
            elem_classes = attrs_dict.get("class", "").split()
            if self.target_class not in elem_classes:
                return False

        # id匹配
        if self.target_id:
            if attrs_dict.get("id", "") != self.target_id:
                return False

        # attr匹配 (格式: "name:value")
        if self.target_attr:
            if ":" in self.target_attr:
                attr_name, attr_value = self.target_attr.split(":", 1)
                if attrs_dict.get(attr_name, "") != attr_value:
                    return False
            else:
                if self.target_attr not in attrs_dict:
                    return False

        return True

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()

        if tag in self._skip_tags:
            self._current_depth += 1
            return

        # 检查是否匹配选择器
        if not self._in_target and self._match_selector(tag, attrs):
            self._in_target = True
            self._target_depth = 0
            self._target_text = ""
            self._target_attrs = dict(attrs)

        if self._in_target:
            self._target_depth += 1

    def handle_endtag(self, tag):
        tag = tag.lower()

        if tag in self._skip_tags:
            self._current_depth = max(0, self._current_depth - 1)
            return

        if self._in_target:
            self._target_depth -= 1
            if self._target_depth == 0:
                self._in_target = False
                text = self._target_text.strip()
                if text:
                    self.results.append({
                        "tag": tag,
                        "text": text,
                        "attrs": self._target_attrs
                    })

    def handle_data(self, data):
        if self._in_target:
            text = data.strip()
            if text:
                self._target_text += " " + text


def detect_encoding(response, html_bytes):
    """检测编码"""
    content_type = response.headers.get("Content-Type", "")
    charset_match = re.search(r'charset=([^\s;]+)', content_type, re.IGNORECASE)
    if charset_match:
        enc = charset_match.group(1).strip('"\'')
        try:
            html_bytes.decode(enc)
            return enc
        except (UnicodeDecodeError, LookupError):
            pass
    return 'utf-8'


def extract_elements(url, selector, timeout=10):
    """抓取网页并提取指定元素"""
    parsed = urlparse(url)
    if not parsed.scheme:
        url = "https://" + url

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    try:
        req = Request(url, headers=headers)
        with urlopen(req, timeout=timeout) as response:
            html_bytes = response.read()
            encoding = detect_encoding(response, html_bytes)
            html = html_bytes.decode(encoding, errors='replace')

        extractor = ElementExtractor(selector)
        extractor.feed(html)

        return {
            "status": "ok",
            "url": url,
            "selector": selector,
            "count": len(extractor.results),
            "elements": extractor.results[:50],  # 最多返回50个
            "truncated": len(extractor.results) > 50
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
        selector = data.get("selector", {})
        timeout = data.get("timeout", 10)

        if not url:
            print(json.dumps({"status": "error", "message": "缺少url参数"}, ensure_ascii=False))
            return

        if not selector:
            print(json.dumps({"status": "error", "message": "缺少selector参数，至少指定tag/class/id/attr之一"}, ensure_ascii=False))
            return

        result = extract_elements(url, selector, timeout)

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
    parser = argparse.ArgumentParser(description="网页元素提取器")
    parser.add_argument("--input", type=str, help="JSON格式输入，含url和selector")
    parser.add_argument("--output", type=str, help="输出文件路径（可选）")
    args = parser.parse_args()
    main(args)
