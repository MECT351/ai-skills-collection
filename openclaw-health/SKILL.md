---
name: OpenClaw健康自检器
description: OpenClaw多渠道网关配置校验、连通性检测与渠道诊断，生成整体健康报告。当用户部署OpenClaw后需要检查配置是否正确、各渠道是否连通、排查问题时使用。4个工具脚本：配置文件字段校验、各渠道HTTP端点探测、逐渠道配置诊断(飞书/微信/钉钉/Coze)、整体健康报告汇总。
version: "1.0.0"
category: ["开发工具", "OpenClaw"]
tags: ["OpenClaw", "配置校验", "连通性检测", "渠道诊断", "健康检查"]
---

# OpenClaw健康自检器

OpenClaw多渠道网关配置校验、连通性检测与渠道诊断，生成整体健康报告。

## 功能脚本

| 脚本 | 功能 | 输入 | 输出 |
|------|------|------|------|
| config_check.py | 配置文件字段/格式/完整性校验 | OpenClaw配置JSON | 问题清单JSON |
| connectivity.py | 各渠道端点HTTP连通性探测 | 配置JSON | 响应状态+耗时JSON |
| channel_diag.py | 逐渠道配置诊断(飞书/微信/钉钉等) | 配置JSON | 诊断结果JSON |
| health_report.py | 汇总生成整体健康报告 | 以上三项结果 | 健康报告JSON |

## 使用方式

```bash
# 配置校验
python3 config_check.py --config openclaw.json

# 连通性探测
python3 connectivity.py --config openclaw.json

# 渠道诊断
python3 channel_diag.py --config openclaw.json --channel feishu

# 整体健康报告
python3 health_report.py --config openclaw.json
```

## 数据存储
纯标准库，零依赖，JSON标准化输入输出。
