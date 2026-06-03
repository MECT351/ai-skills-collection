---
name: privacy-guard
description: PII隐私信息扫描、脱敏、审计与一键清洗，保护敏感数据不泄露。当用户需要检查文档中是否有隐私泄露、脱敏处理、生成隐私审计报告时使用。4个工具脚本：扫描12类PII(手机号/身份证/邮箱/银行卡/API Key/JWT/AWS Key等)、按规则脱敏替换、风险分级审计报告、一键清洗生成安全版本。
version: "1.0.0"
category: ["安全工具", "隐私保护"]
tags: ["PII", "隐私扫描", "脱敏", "数据安全", "审计"]
---

# 主人隐私卫士

PII隐私信息扫描、脱敏、审计与一键清洗，保护敏感数据不泄露。

## 功能脚本

| 脚本 | 功能 | 输入 | 输出 |
|------|------|------|------|
| scan.py | 扫描文本中的PII(手机/身份证/邮箱/银行卡/API Key等) | 文本或文件 | 发现项清单JSON |
| redact.py | 按规则脱敏(手机→185****4531) | 文本+规则 | 脱敏文本JSON |
| report.py | 隐私审计报告，风险分级 | 文本或文件 | 审计报告JSON |
| sanitize.py | 一键清洗，生成安全可分享版本 | 文本或文件 | 清洗结果JSON |

## 使用方式

```bash
# 扫描PII
python3 scan.py --input "联系我18548034531" 
python3 scan.py --file secret.txt

# 脱敏
python3 redact.py --input "邮箱test@qq.com手机13912345678"

# 审计报告
python3 report.py --file document.txt

# 一键清洗
python3 sanitize.py --file data.txt --output safe_data.txt
```

## 数据存储
纯标准库，零依赖，JSON标准化输入输出。
