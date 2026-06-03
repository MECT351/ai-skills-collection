---
name: 条件监控提醒器
description: 定时检查网页更新/API变化/自定义条件，满足时触发提醒。配合Calendar定时触发，实现主动轮询提醒。网页变化检测/接口状态检查/条件判断/调度配置，4个脚本覆盖监控全场景。
version: "1.0.0"
updated_at: "2026-06-03"
category: ["监控工具", "自动化"]
tags: ["监控", "轮询", "提醒", "定时检查", "网页变化"]
trigger: ["监控提醒", "定时检查", "网页变化检测", "条件监控", "轮询通知"]
---

# 条件监控提醒器

> 配合Calendar定时触发，实现主动轮询+变化提醒。Skill提供检查逻辑，Calendar负责定时调度。

## 核心能力

1. **网页变化检测** — 记录页面指纹，对比发现变化时触发提醒
2. **接口状态检查** — 检查API是否正常、返回值是否变化
3. **条件判断** — 自定义条件表达式，满足时触发提醒
4. **调度配置生成** — 一键生成Calendar日程配置，自动设定定时触发

---

## 工作原理

Calendar定时触发 → Agent读取日程工单 → 调用本Skill脚本 → 检查是否有变化 → 有变化通知用户 / 无变化静默

## 快速开始

### 流程1：监控网页变化

用户说：帮我盯着这个网页，有变化提醒我

```bash
python scripts/web_check.py --input '{"url": "https://example.com/news", "name": "news_page", "check_hash": true, "check_keywords": ["新品发布", "更新"]}'
```

首次运行：记录页面指纹，返回"已建立监控基线"
后续运行：对比指纹，有变化返回变更详情，无变化返回"无变化"

### 流程2：检查接口状态

用户说：帮我监控这个API，挂了提醒我

```bash
python scripts/api_check.py --input '{"url": "https://api.example.com/health", "method": "GET", "expected_status": 200, "expected_field": "status", "expected_value": "ok"}'
```

### 流程3：条件判断

用户说：当XX条件满足时提醒我

```bash
python scripts/condition_check.py --input '{"name": "price_monitor", "data_source": "url", "url": "https://api.example.com/price", "field": "price", "operator": ">", "threshold": 100}'
```

支持运算符：> / < / >= / <= / == / != / contains / not_contains

### 流程4：生成调度配置

用户说：帮我设置定时监控

```bash
python scripts/scheduler.py --input '{"name": "news_monitor", "interval": "HOURLY", "script": "web_check", "params": {"url": "https://example.com/news", "name": "news_page"}}'
```

输出Calendar日程创建指令，Agent据此创建定时任务。

---

## 状态存储

检查结果和基线数据存储在 monitor_state/ 目录下：
- {name}_hash.json — 网页指纹基线
- {name}_last.json — 上次检查结果
- {name}_history.json — 历史变化记录

---

## 脚本说明

### scripts/web_check.py
- 输入：url + name + check_hash + check_keywords
- 输出：变化状态 + 变更详情（如有）
- 逻辑：抓取页面 → 计算指纹 → 对比基线 → 输出结果

### scripts/api_check.py
- 输入：url + method + expected_status + expected_field + expected_value
- 输出：接口状态 + 异常信息（如有）
- 逻辑：请求接口 → 校验状态码/返回值 → 输出结果

### scripts/condition_check.py
- 输入：name + data_source + field + operator + threshold
- 输出：条件是否满足 + 当前值
- 逻辑：获取数据 → 判断条件 → 输出结果

### scripts/scheduler.py
- 输入：name + interval + script + params
- 输出：Calendar日程创建配置（JSON）
- 逻辑：生成日程工单描述，Agent据此创建Calendar

---

## 设计原则

1. 有状态检查 — 记录历史基线，能检测变化
2. 静默优先 — 无变化不输出，不干扰用户
3. 配合Calendar — Skill只负责检查，定时靠外部调度
4. 纯标准库 — 零安装
5. JSON标准化 — Agent好对接
