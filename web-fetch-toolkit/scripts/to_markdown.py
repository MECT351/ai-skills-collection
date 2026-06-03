#!/usr/bin/env python3
"""HTML转Markdown工具 — 将网页或HTML字符串转换为干净的Markdown"""

import sys
import json
import argparse
import re
from html.parser import HTMLParser
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from urllib.parse import urlparse


NOISE_TAGS = {'script', 'style', 'noscript', 'header', 'footer', 'nav', 'aside', 'iframe', 'svg'}
INLINE_TAGS = {'strong', 'b', 'em', 'i', 'code', 'a', 'img', 'span', 'sup', 'sub', 'del', 's', 'mark'}
LIST_TAGS = {'ul', 'ol'}
HEADING_TAGS = {'h1', 'h2', 'h3', 'h4', 'h5', 'h6'}


class HTMLToMarkdown(HTMLParser):
    """将HTML转换为Markdown"""

    def __init__(self):
        super().__init__()
        self.output = []
        self._skip_depth = 0
        self._list_stack = []  # 跟踪嵌套列表
        self._list_counter = []  # 有序列表计数器
        self._in_link = False
        self._link_href = ""
        self._link_text = ""
        self._in_heading = False
        self._heading_level = 0
        self._heading_text = ""
        self._in_code_block = False
        self._code_text = ""
        self._in_table = False
        self._table_rows = []
        self._current_row = []
        self._in_cell = False
        self._cell_text = ""
        self._is_header_row = False
        self._paragraph_buffer = ""

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        attrs_dict = dict(attrs)

        if tag in NOISE_TAGS:
            self._skip_depth += 1
            return

        if self._skip_depth > 0:
            return

        self._flush_paragraph()

        if tag in HEADING_TAGS:
            self._in_heading = True
            self._heading_level = int(tag[1])
            self._heading_text = ""

        elif tag == 'p':
            pass  # 段落由_flush_paragraph处理

        elif tag in ('strong', 'b'):
            self.output.append('**')

        elif tag in ('em', 'i'):
            self.output.append('*')

        elif tag == 'code':
            if not self._in_code_block:
                self.output.append('`')

        elif tag == 'pre':
            self._in_code_block = True
            self._code_text = ""
            self.output.append('\n```\n')

        elif tag == 'a':
            self._in_link = True
            self._link_href = attrs_dict.get('href', '')
            self._link_text = ""

        elif tag == 'img':
            alt = attrs_dict.get('alt', '')
            src = attrs_dict.get('src', '')
            if src:
                self.output.append(f'![{alt}]({src})')

        elif tag == 'br':
            self.output.append('  \n')

        elif tag == 'hr':
            self.output.append('\n---\n')

        elif tag == 'ul':
            self._list_stack.append('ul')
            self._list_counter.append(0)

        elif tag == 'ol':
            self._list_stack.append('ol')
            self._list_counter.append(1)

        elif tag == 'li':
            indent = '  ' * (len(self._list_stack) - 1)
            if self._list_stack and self._list_stack[-1] == 'ol':
                num = self._list_counter[-1]
                self._list_counter[-1] = num + 1
                self.output.append(f'\n{indent}{num}. ')
            else:
                self.output.append(f'\n{indent}- ')

        elif tag == 'blockquote':
            self.output.append('\n> ')

        elif tag == 'table':
            self._in_table = True
            self._table_rows = []

        elif tag == 'tr':
            self._current_row = []
            self._is_header_row = bool(attrs_dict.get('class', '').find('header') >= 0)

        elif tag in ('td', 'th'):
            self._in_cell = True
            self._cell_text = ""
            if tag == 'th':
                self._is_header_row = True

    def handle_endtag(self, tag):
        tag = tag.lower()

        if tag in NOISE_TAGS:
            self._skip_depth = max(0, self._skip_depth - 1)
            return

        if self._skip_depth > 0:
            return

        if tag in HEADING_TAGS and self._in_heading:
            self._in_heading = False
            prefix = '#' * self._heading_level
            self.output.append(f'\n{prefix} {self._heading_text.strip()}\n')

        elif tag == 'p':
            self._flush_paragraph()

        elif tag in ('strong', 'b'):
            self.output.append('**')

        elif tag in ('em', 'i'):
            self.output.append('*')

        elif tag == 'code' and not self._in_code_block:
            self.output.append('`')

        elif tag == 'pre' and self._in_code_block:
            self._in_code_block = False
            self.output.append(self._code_text)
            self.output.append('\n```\n')

        elif tag == 'a' and self._in_link:
            self._in_link = False
            if self._link_href:
                self.output.append(f'[{self._link_text.strip()}]({self._link_href})')
            else:
                self.output.append(self._link_text)

        elif tag in ('ul', 'ol'):
            if self._list_stack:
                self._list_stack.pop()
                self._list_counter.pop()
            self.output.append('\n')

        elif tag == 'blockquote':
            self.output.append('\n')

        elif tag in ('td', 'th') and self._in_cell:
            self._in_cell = False
            self._current_row.append(self._cell_text.strip())

        elif tag == 'tr' and self._in_table:
            self._table_rows.append({
                "cells": self._current_row,
                "is_header": self._is_header_row
            })

        elif tag == 'table' and self._in_table:
            self._in_table = False
            self._render_table()

    def handle_data(self, data):
        if self._skip_depth > 0:
            return

        text = data

        if self._in_heading:
            self._heading_text += text

        elif self._in_code_block:
            self._code_text += text

        elif self._in_link:
            self._link_text += text

        elif self._in_cell:
            self._cell_text += text

        else:
            # 压缩多余空白
            text = re.sub(r'[ \t]+', ' ', text)
            if text.strip():
                self._paragraph_buffer += text

    def _flush_paragraph(self):
        if self._paragraph_buffer.strip():
            self.output.append(self._paragraph_buffer.strip())
            self.output.append('\n\n')
            self._paragraph_buffer = ""

    def _render_table(self):
        """渲染Markdown表格"""
        if not self._table_rows:
            return

        self.output.append('\n')

        for i, row in enumerate(self._table_rows):
            cells = row["cells"]
            line = '| ' + ' | '.join(cells) + ' |'
            self.output.append(line + '\n')

            # 第一行或header行后加分隔线
            if i == 0 or row["is_header"]:
                sep = '|' + '|'.join([' --- ' for _ in cells]) + '|'
                self.output.append(sep + '\n')

        self.output.append('\n')

    def get_markdown(self):
        self._flush_paragraph()
        md = ''.join(self.output)
        # 清理多余空行
        md = re.sub(r'\n{3,}', '\n\n', md)
        return md.strip()


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


def html_to_markdown(html):
    """将HTML字符串转为Markdown"""
    converter = HTMLToMarkdown()
    converter.feed(html)
    md = converter.get_markdown()
    return {
        "status": "ok",
        "markdown": md,
        "stats": {
            "input_length": len(html),
            "output_length": len(md),
            "compression_ratio": round(len(md) / max(len(html), 1) * 100, 1)
        }
    }


def url_to_markdown(url, timeout=10):
    """抓取URL并转为Markdown"""
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

        result = html_to_markdown(html)
        result["url"] = url
        return result

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
        html = data.get("html", "")
        timeout = data.get("timeout", 10)

        if url:
            result = url_to_markdown(url, timeout)
        elif html:
            result = html_to_markdown(html)
        else:
            result = {"status": "error", "message": "缺少url或html参数"}
            print(json.dumps(result, ensure_ascii=False))
            return

        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(result.get("markdown", ""))
            result["output_file"] = args.output

        print(json.dumps(result, ensure_ascii=False, indent=2))

    except json.JSONDecodeError:
        print(json.dumps({"status": "error", "message": "输入不是有效的JSON"}, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="HTML转Markdown工具")
    parser.add_argument("--input", type=str, help="JSON格式输入，含url或html字段")
    parser.add_argument("--output", type=str, help="输出文件路径（可选，保存为.md）")
    args = parser.parse_args()
    main(args)
