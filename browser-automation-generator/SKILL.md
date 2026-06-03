---
name: 浏览器自动化脚本生成器
description: 根据操作需求描述自动生成Playwright浏览器自动化脚本。登录、导航、填表、数据采集，4个生成器覆盖浏览器自动化全场景。输入需求描述，输出可运行的.py文件。
version: "1.0.0"
updated_at: "2026-06-03"
category: ["开发工具", "自动化"]
tags: ["浏览器自动化", "Playwright", "脚本生成", "网页操作", "自动化测试"]
trigger: ["生成浏览器脚本", "自动化登录", "自动填表", "网页自动化", "Playwright脚本"]
---

# 浏览器自动化脚本生成器

> 代码生成工具。输入操作需求，输出可运行的Playwright脚本。不依赖浏览器，生成脚本后本地运行。

## 核心能力

1. **登录脚本生成** — 输入网址+登录逻辑 → 生成完整的登录自动化脚本
2. **导航脚本生成** — 输入操作步骤 → 生成页面导航+点击脚本
3. **表单脚本生成** — 输入表单字段 → 生成自动填表提交脚本
4. **采集脚本生成** — 输入抓取目标 → 生成数据采集导出脚本

---

## 快速开始

### 流程1：生成登录脚本

用户说：帮我生成一个XX网站的登录脚本 / 自动登录

```bash
python scripts/login_gen.py --input '{"url": "https://example.com/login", "steps": ["输入用户名到#username", "输入密码到#password", "点击登录按钮button[type=submit]"], "save_session": true}'
```

输出完整的Playwright登录脚本，包含：
- 浏览器启动+页面打开
- 逐步操作逻辑
- 会话保存/恢复
- 错误处理和重试
- 截图验证

### 流程2：生成导航脚本

用户说：生成一个网页操作脚本 / 点击跳转自动化

```bash
python scripts/navigate_gen.py --input '{"url": "https://example.com", "steps": ["点击导航栏的「产品」链接", "等待页面加载", "点击第一个产品卡片", "截图保存"], "headless": false}'
```

输出导航脚本，包含：
- 页面跳转+等待策略
- 元素定位（CSS/XPath）
- 操作间隔和重试
- 截图/日志记录

### 流程3：生成表单脚本

用户说：生成一个自动填表脚本 / 批量提交表单

```bash
python scripts/form_gen.py --input '{"url": "https://example.com/form", "fields": [{"name": "姓名", "selector": "#name", "value": "张三"}, {"name": "邮箱", "selector": "#email", "value": "test@example.com"}, {"name": "备注", "selector": "#remark", "value": "测试提交"}], "submit_selector": "button[type=submit]"}'
```

输出表单脚本，包含：
- 字段逐一填写
- 下拉选择/单选/复选处理
- 文件上传支持
- 提交+结果验证

### 流程4：生成采集脚本

用户说：生成一个数据采集脚本 / 抓取页面数据

```bash
python scripts/scrape_gen.py --input '{"url": "https://example.com/list", "targets": [{"name": "标题", "selector": ".item-title"}, {"name": "价格", "selector": ".item-price"}], "pagination": {"next_selector": ".next-page", "max_pages": 5}, "output_format": "json"}'
```

输出采集脚本，包含：
- 元素定位+数据提取
- 分页翻页逻辑
- 数据去重
- JSON/CSV导出

---

## 脚本说明

### scripts/login_gen.py
- 输入：url + steps + save_session
- 输出：Playwright登录脚本（.py文件内容）
- 生成的脚本支持：有头/无头模式、会话保持、验证码等待提示

### scripts/navigate_gen.py
- 输入：url + steps + headless
- 输出：Playwright导航脚本
- 生成的脚本支持：智能等待、元素重试、截图记录

### scripts/form_gen.py
- 输入：url + fields + submit_selector
- 输出：Playwright表单脚本
- 生成的脚本支持：多种输入类型、批量数据、提交验证

### scripts/scrape_gen.py
- 输入：url + targets + pagination + output_format
- 输出：Playwright采集脚本
- 生成的脚本支持：分页、去重、多格式导出

---

## 生成的脚本依赖

所有生成的脚本需要本地安装Playwright：
```bash
pip install playwright
playwright install
```

本Skill只生成代码，不直接执行浏览器操作。

## 设计原则

1. 输入需求描述，输出可运行代码 — 生成器本身纯标准库
2. 生成的脚本包含完整错误处理 — 拿到就能跑
3. 每步操作都有日志 — 方便调试
4. 支持有头/无头模式 — 开发调试用有头，生产用无头
5. JSON标准化输入输出 — Agent好对接
