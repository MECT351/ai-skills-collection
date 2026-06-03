---
name: PDF文本提取器
description: 纯Python标准库实现PDF文本提取。提取全文/指定页面/元信息/关键词统计，4个脚本覆盖PDF文本处理全场景。零依赖，拿到就能跑。
version: "1.0.0"
updated_at: "2026-06-03"
category: ["办公工具", "文档处理"]
tags: ["PDF", "文本提取", "文档解析", "元信息", "关键词"]
trigger: ["提取PDF", "PDF转文本", "解析PDF", "PDF元信息", "PDF内容"]
---

# PDF文本提取器

> 纯标准库PDF文本提取工具。输入PDF，输出文本内容。零依赖。

## 核心能力

1. **全文提取** — 输入PDF → 输出全部文本内容
2. **页面提取** — 输入PDF+页码范围 → 输出指定页面文本
3. **元信息提取** — 输入PDF → 输出标题/作者/创建时间等元数据
4. **关键词统计** — 输入PDF → 输出词频统计+关键信息

---

## 快速开始

### 流程1：提取全文

```bash
python scripts/extract_all.py --input '{"file": "document.pdf"}'
```

### 流程2：提取指定页面

```bash
python scripts/extract_pages.py --input '{"file": "document.pdf", "pages": [1, 2, 3]}'
```

### 流程3：提取元信息

```bash
python scripts/metadata.py --input '{"file": "document.pdf"}'
```

### 流程4：关键词统计

```bash
python scripts/keywords.py --input '{"file": "document.pdf", "top_n": 20}'
```

---

## 设计原则

1. 纯标准库解析PDF结构 — 不依赖PyPDF2/pdfplumber
2. 支持文本型PDF — 扫描件/图片PDF需OCR，不在本工具范围
3. 优雅降级 — 遇到加密/损坏文件返回明确错误
4. JSON标准化输出 — Agent好对接

## 注意事项

- 本工具基于PDF底层文本流解析，适用于文本型PDF
- 扫描件/图片型PDF需要OCR工具配合，本工具无法提取
- 加密PDF需要先解密再提取
