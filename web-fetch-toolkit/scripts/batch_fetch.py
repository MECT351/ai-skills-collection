#!/usr/bin/env python3
"""批量网页抓取器 — 多URL并发抓取+去重+汇总报告"""

import sys
import json
import argparse
import time
import threading
from urllib.parse import urlparse


def fetch_single(url, timeout=10):
    """抓取单个URL（复用fetch.py的逻辑）"""
    from html.parser import HTMLParser
    from urllib.request import Request, urlopen
    from urllib.error import URLError, HTTPError
    import re

    class SimpleParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.title = ""
            self.content_parts = []
            self._skip_depth = 0
            self._title_depth = 0
            self._text_buffer = ""
            self._skip_tags = {'script', 'style', 'noscript', 'header', 'footer', 'nav', 'aside'}
            self._block_tags = {'p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'br', 'hr'}

        def handle_starttag(self, tag, attrs):
            tag = tag.lower()
            if tag in self._skip_tags:
                self._skip_depth += 1
                return
            if tag == "title":
                self._title_depth += 1
            if tag in self._block_tags and self._text_buffer.strip():
                self.content_parts.append(self._text_buffer.strip())
                self._text_buffer = ""

        def handle_endtag(self, tag):
            tag = tag.lower()
            if tag in self._skip_tags:
                self._skip_depth = max(0, self._skip_depth - 1)
                return
            if tag == "title":
                self._title_depth = max(0, self._title_depth - 1)
            if tag in self._block_tags and self._text_buffer.strip():
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

    start_time = time.time()
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
            charset_match = re.search(r'charset=([^\s;]+)', response.headers.get("Content-Type", ""), re.IGNORECASE)
            encoding = charset_match.group(1).strip('"\'') if charset_match else 'utf-8'
            try:
                html = html_bytes.decode(encoding)
            except (UnicodeDecodeError, LookupError):
                html = html_bytes.decode('utf-8', errors='replace')

        parser = SimpleParser()
        parser.feed(html)

        fetch_time = int((time.time() - start_time) * 1000)

        return {
            "status": "ok",
            "url": url,
            "title": parser.title or "",
            "content_length": len(parser.get_content()),
            "fetch_time_ms": fetch_time
        }

    except Exception as e:
        return {"status": "error", "url": url, "message": str(e)}


def batch_fetch(urls, concurrency=3, delay=1):
    """批量抓取"""
    # URL去重
    seen = set()
    unique_urls = []
    for url in urls:
        normalized = url.strip().rstrip('/')
        if normalized not in seen:
            seen.add(normalized)
            unique_urls.append(url.strip())

    results = []
    lock = threading.Lock()
    queue = list(unique_urls)
    queue_lock = threading.Lock()
    total = len(queue)

    def worker():
        while True:
            with queue_lock:
                if not queue:
                    return
                url = queue.pop(0)
                idx = total - len(queue)

            result = fetch_single(url)
            with lock:
                results.append(result)

            if delay > 0 and queue:
                time.sleep(delay)

    start_time = time.time()
    threads = []
    for _ in range(min(concurrency, total)):
        t = threading.Thread(target=worker)
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    total_time = int((time.time() - start_time) * 1000)

    success_count = sum(1 for r in results if r["status"] == "ok")
    error_count = sum(1 for r in results if r["status"] == "error")

    return {
        "status": "ok",
        "results": results,
        "summary": {
            "total": total,
            "unique": len(unique_urls),
            "success": success_count,
            "error": error_count,
            "total_time_ms": total_time
        }
    }


def main(args):
    try:
        if args.input:
            data = json.loads(args.input)
        else:
            data = {}

        urls = data.get("urls", [])
        concurrency = data.get("concurrency", 3)
        delay = data.get("delay", 1)

        if not urls:
            print(json.dumps({"status": "error", "message": "缺少urls参数"}, ensure_ascii=False))
            return

        result = batch_fetch(urls, concurrency, delay)

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
    parser = argparse.ArgumentParser(description="批量网页抓取器")
    parser.add_argument("--input", type=str, help="JSON格式输入，含urls数组")
    parser.add_argument("--output", type=str, help="输出文件路径（可选）")
    args = parser.parse_args()
    main(args)
