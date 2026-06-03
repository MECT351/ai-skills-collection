---
name: PPT幻灯片生成器
description: 输入主题和大纲，自动生成HTML格式演示文稿。支持多种主题风格、自动排版、大纲转幻灯片、内容优化，纯标准库零依赖。
version: "1.0.0"
updated_at: "2026-06-03"
category: ["办公工具", "演示文稿"]
tags: ["PPT", "幻灯片", "演示文稿", "HTML", "自动生成"]
trigger: ["生成PPT", "创建幻灯片", "制作演示文稿", "PPT大纲", "幻灯片生成"]
---

# PPT幻灯片生成器

> 输入主题和大纲，输出完整HTML演示文稿。纯标准库，浏览器直接打开即可演示。

## 核心能力

1. **大纲转幻灯片** — 输入文本大纲 → 输出多页HTML幻灯片
2. **主题风格切换** — 内置5种专业主题，一键切换
3. **内容优化** — 自动拆分过长内容、生成标题和要点
4. **Markdown转PPT** — 输入Markdown文档 → 转为幻灯片

---

## 快速开始

### 流程1：大纲转幻灯片

用户说：帮我生成一个关于XX的PPT / 创建演示文稿

```bash
python scripts/outline.py --input '{"topic": "AI智能体商业化", "outline": ["行业背景", "核心技术", "商业模式", "落地案例", "未来展望"]}'
```

输出完整的HTML幻灯片文件，浏览器打开即可全屏演示。

### 流程2：切换主题风格

```bash
python scripts/outline.py --input '{"topic": "AI智能体商业化", "outline": ["背景", "技术", "模式", "案例"], "theme": "tech-dark"}'
```

内置主题：
- `corporate` — 商务蓝（默认）
- `tech-dark` — 科技暗黑
- `creative` — 创意渐变
- `minimal` — 极简白
- `nature` — 自然绿

### 流程3：Markdown转PPT

```bash
python scripts/md2ppt.py --input '{"markdown": "# 标题\n## 第一页\n- 要点1\n- 要点2\n## 第二页\n内容...", "theme": "tech-dark"}'
```

### 流程4：内容优化

```bash
python scripts/optimize.py --input '{"content": "很长的文本内容...", "max_slides": 10}'
```

自动将长文本拆分为多页，每页3-5个要点。

---

## 脚本说明

### scripts/outline.py
- 输入：topic + outline + theme(可选) + max_slides(可选)
- 输出：完整HTML幻灯片文件
- 逻辑：大纲展开 → 内容生成 → 主题渲染 → HTML输出

### scripts/md2ppt.py
- 输入：markdown字符串或文件路径 + theme(可选)
- 输出：HTML幻灯片文件
- 逻辑：解析Markdown → 按h1/h2分页 → 渲染为幻灯片

### scripts/optimize.py
- 输入：content + max_slides
- 输出：优化后的大纲结构
- 逻辑：文本分段 → 要点提取 → 页面分配 → 大纲输出

### scripts/themes.py
- 输入：action(list|get) + theme名称
- 输出：可用主题列表 或 主题CSS样式
- 逻辑：内置5种主题，支持预览和获取

---

## 设计原则

1. HTML输出，浏览器即开即演 — 不依赖PowerPoint
2. 纯标准库生成 — 零安装
3. 响应式布局 — 自适应屏幕
4. 键盘翻页 — 方向键或空格控制
5. JSON标准化输入输出 — Agent好对接
