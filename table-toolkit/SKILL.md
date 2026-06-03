---
name: 数据表格处理工具
description: CSV/TSV数据表格分析处理工具。统计分析、数据清洗、表格合并、格式转换，4个可执行脚本覆盖数据表格处理全场景。纯Python标准库，零依赖。
version: "1.0.0"
updated_at: "2026-06-03"
category: ["办公工具", "数据处理"]
tags: ["CSV", "数据分析", "表格处理", "数据清洗", "Excel"]
trigger: ["分析CSV", "表格处理", "数据清洗", "合并表格", "CSV统计"]
---

# 数据表格处理工具

> 轻量级数据表格处理工具。输入CSV，输出分析结果。纯标准库，零依赖。

## 核心能力

1. **统计分析** — 输入CSV → 输出描述性统计（均值/中位数/标准差/分位数）
2. **数据清洗** — 输入CSV → 输出清洗后数据（去重/空值处理/格式统一）
3. **表格合并** — 输入多个CSV → 输出合并结果（纵向/横向合并）
4. **格式转换** — 输入CSV → 输出JSON/TSV/Markdown表格

---

## 快速开始

### 流程1：统计分析

用户说：分析这个CSV数据 / 统计数据概况

```bash
python scripts/stats.py --input '{"file": "data.csv"} 或 {"data": "name,age,score\\n张三,25,85\\n李四,30,92"}'
```

输出每列的描述性统计：数量、均值、标准差、最小值、最大值、中位数

### 流程2：数据清洗

用户说：清洗这个数据 / 去重去空值

```bash
python scripts/clean.py --input '{"file": "data.csv", "dedup": true, "fill_na": "mean", "trim_space": true}'
```

清洗选项：
- dedup — 去除完全重复行
- fill_na — 空值填充策略：mean/median/zero/drop/空字符串
- trim_space — 去除首尾空白

### 流程3：表格合并

用户说：合并这些表格 / 把两个CSV合在一起

```bash
python scripts/merge.py --input '{"files": ["a.csv", "b.csv"], "mode": "vertical", "key": "id"}'
```

合并模式：
- vertical — 纵向合并（行追加，列相同）
- horizontal — 横向合并（列追加，按key匹配合并）

### 流程4：格式转换

用户说：CSV转JSON / 表格转Markdown

```bash
python scripts/convert.py --input '{"file": "data.csv", "from": "csv", "to": "json"}'
```

支持格式：csv / tsv / json / markdown

---

## 脚本说明

### scripts/stats.py
- 输入：file路径 或 data字符串
- 输出：每列统计信息 + 整体概况
- 逻辑：解析CSV → 识别数值/文本列 → 分别计算统计量

### scripts/clean.py
- 输入：file/data + 清洗选项
- 输出：清洗后数据 + 清洗报告（处理了多少行/列）
- 逻辑：去重 → 空值处理 → 格式统一 → 输出

### scripts/merge.py
- 输入：files列表 + mode + key(横向合并时)
- 输出：合并结果 + 合并报告
- 逻辑：读取多个CSV → 按模式合并 → 输出

### scripts/convert.py
- 输入：file/data + from格式 + to格式
- 输出：转换后内容
- 逻辑：解析输入格式 → 转为目标格式 → 输出

---

## 设计原则

1. 纯标准库csv/json模块 — 零安装
2. 支持文件路径和内联数据 — 灵活输入
3. 自动识别数值/文本列 — 智能统计
4. 清洗操作可配置 — 不替用户做决定
5. JSON标准化输出 — Agent好对接
