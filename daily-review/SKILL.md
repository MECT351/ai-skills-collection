---
name: 每日状态评测日记生成器
description: 结构化记录每日状态，追踪情绪趋势与习惯养成，自动生成日评和周度报告。当用户需要写日记、记录心情、追踪习惯、生成周报时使用。4个工具脚本：生成结构化日评模板、情绪趋势分析、习惯打卡与连续天数追踪、周度总结报告。
version: "1.0.0"
category: ["效率工具", "自我管理"]
tags: ["日记", "情绪追踪", "习惯打卡", "周报", "自我管理"]
---

# 每日状态评测日记生成器

结构化记录每日状态，追踪情绪趋势与习惯养成，自动生成日评和周度报告。

## 功能脚本

| 脚本 | 功能 | 输入 | 输出 |
|------|------|------|------|
| daily_review.py | 生成结构化日评模板 | 日期、心情关键词、精力等级 | JSON日评记录 |
| mood_analyze.py | 情绪趋势分析 | 日记数据文件路径 | 趋势报告JSON |
| habit_tracker.py | 习惯打卡与连续追踪 | 习惯名、操作(打卡/查询) | 打卡状态JSON |
| weekly_digest.py | 周度总结报告 | 起始日期 | 周报JSON |

## 使用方式

```bash
# 生成今日日评
python3 daily_review.py --date 2026-06-03 --mood "充实" --energy 8

# 情绪趋势分析
python3 mood_analyze.py --file diary.json

# 习惯打卡
python3 habit_tracker.py --habit "健身" --action checkin

# 生成周报
python3 weekly_digest.py --start 2026-05-29
```

## 数据存储
所有数据以JSON格式存储在当前目录下，零依赖纯标准库。
