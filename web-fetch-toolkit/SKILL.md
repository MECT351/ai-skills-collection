---
name: 网页抓取工具箱
description: 轻量级网页内容抓取与转换工具。单URL抓取、批量抓取、指定元素提取、HTML转Markdown，4个可执行脚本覆盖网页数据采集全场景。纯Python标准库，零依赖拿到就能跑。
version: "1.0.0"
updated_at: "2026-06-03"
category: ["开发工具", "数据采集"]
tags: ["网页抓取", "web fetch", "HTML解析", "Markdown转换", "数据采集"]
trigger: ["抓取网页", "网页内容", "HTML转Markdown", "批量抓取", "提取网页"]
---

# 网页抓取工具箱

> 轻量级网页内容抓取工具。输入URL，输出结构化内容。纯标准库，零依赖。

## 核心能力

1. **单URL抓取** — 输入URL，输出标题+正文+元信息，自动识别编码
2. **批量抓取** — 输入多个URL，并发抓取+去重+汇总报告
3. **指定元素提取** — 输入URL+选择器，精准提取目标内容
4. **HTML转Markdown** — 输入URL或HTML，输出干净Markdown文本

---

## 快速开始

### 流程1：抓取单个网页

用户说：抓取这个网页 / 获取网页内容

```bash
python scripts/fetch.py --input '{"url": "https://example.com"}'
```

输出：
```json
{
  "status": "ok",
  "url": "https://example.com",
  "title": "网页标题",
  "content": "正文内容...",
  "meta": {
    "description": "页面描述",
    "keywords": "关键词"
  },
  "stats": {
    "content_length": 1234,
    "fetch_time_ms": 523
  }
}
```

### 流程2：批量抓取

用户说：批量抓取这些网页 / 同时获取多个页面

```bash
python scripts/batch_fetch.py --input '{"urls": ["https://example.com/page1", "https://example.com/page2"]}'
```

输出每个URL的抓取结果 + 汇总报告（成功/失败数、总耗时）

### 流程3：提取指定元素

用户说：提取网页中的XX内容 / 获取某个区域

```bash
python scripts/extract.py --input '{"url": "https://example.com", "selector": {"tag": "div", "class": "article-content"}}'
```

支持的选择器：
- tag — 按标签名（如 h1, p, article）
- class — 按class名
- id — 按id名
- attr — 按属性名和值

### 流程4：HTML转Markdown

用户说：把这个网页转成Markdown / 网页转MD

```bash
python scripts/to_markdown.py --input '{"url": "https://example.com"}'
```

自动完成：
- 去除导航栏、广告、脚本、样式等无关内容
- 保留标题、段落、列表、链接、图片等核心结构
- 输出干净可读的Markdown文本

---

## 脚本说明

### scripts/fetch.py
- 输入：url + timeout(可选,默认10)
- 输出：标题+正文+元信息+统计
- 逻辑：HTTP请求 -> 编码检测 -> HTML解析 -> 正文提取 -> 元信息提取

### scripts/batch_fetch.py
- 输入：urls数组 + concurrency(可选,默认3) + delay(可选,默认1)
- 输出：每个URL的结果 + 汇总报告
- 逻辑：队列调度 -> 并发抓取 -> 去重检查 -> 结果汇总

### scripts/extract.py
- 输入：url + selector(tag/class/id/attr)
- 输出：匹配元素的内容列表
- 逻辑：抓取页面 -> 按选择器过滤 -> 提取文本和属性

### scripts/to_markdown.py
- 输入：url 或 html字符串
- 输出：Markdown文本 + 转换统计
- 逻辑：抓取/解析HTML -> 去噪 -> 标签转Markdown语法 -> 输出

---

## 设计原则

1. 纯标准库 — 只用urllib/html.parser/json/re，零安装
2. 自动编码检测 — 支持UTF-8/GBK/GB2312等中文编码
3. 智能正文提取 — 基于文本密度算法，自动过滤导航/广告/脚注
4. 优雅降级 — 请求失败返回明确错误信息，不崩溃
5. JSON标准化 — 输入输出全JSON，Agent好对接
