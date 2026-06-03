#!/usr/bin/env python3
"""主人隐私卫士 - PII扫描引擎"""
import json
import argparse
import os
import re

# PII检测规则定义
PII_RULES = [
    {
        "id": "phone_cn",
        "name": "中国手机号",
        "pattern": r"(?<!\d)1[3-9]\d{9}(?!\d)",
        "risk": "high",
        "description": "11位中国手机号"
    },
    {
        "id": "id_card_cn",
        "name": "中国身份证号",
        "pattern": r"(?<!\d)[1-9]\d{5}(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx](?!\d)",
        "risk": "critical",
        "description": "18位中国身份证号"
    },
    {
        "id": "email",
        "name": "电子邮箱",
        "pattern": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        "risk": "medium",
        "description": "电子邮件地址"
    },
    {
        "id": "bank_card",
        "name": "银行卡号",
        "pattern": r"(?<!\d)(?:62|4[0-9]|5[1-5])\d{14,17}(?!\d)",
        "risk": "critical",
        "description": "银联/Visa/Mastercard银行卡号"
    },
    {
        "id": "api_key_generic",
        "name": "API密钥",
        "pattern": r"(?:sk|pk|pk_live|pk_test|pat|Bearer)\s*[_-]?[a-zA-Z0-9]{20,}",
        "risk": "critical",
        "description": "常见API密钥格式"
    },
    {
        "id": "api_key_openai",
        "name": "OpenAI API Key",
        "pattern": r"sk-[a-zA-Z0-9_-]{20,}",
        "risk": "critical",
        "description": "OpenAI格式API Key"
    },
    {
        "id": "api_key_coze",
        "name": "Coze API Key",
        "pattern": r"pat_[a-zA-Z0-9]{20,}",
        "risk": "critical",
        "description": "Coze格式Personal Access Token"
    },
    {
        "id": "ipv4_private",
        "name": "内网IP地址",
        "pattern": r"(?<!\d)(?:10\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])|192\.168)\.\d{1,3}\.\d{1,3}(?!\d)",
        "risk": "low",
        "description": "私有IP地址"
    },
    {
        "id": "jwt_token",
        "name": "JWT令牌",
        "pattern": r"eyJ[a-zA-Z0-9_-]+\.eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+",
        "risk": "high",
        "description": "JSON Web Token"
    },
    {
        "id": "aws_key",
        "name": "AWS Access Key",
        "pattern": r"(?:A3T[A-Z0-9]|AKIA)[A-Z0-9]{16}",
        "risk": "critical",
        "description": "AWS访问密钥"
    },
    {
        "id": "wechat_appid",
        "name": "微信AppID",
        "pattern": r"wx[a-f0-9]{16}",
        "risk": "medium",
        "description": "微信公众号/小程序AppID"
    },
    {
        "id": "feishu_appid",
        "name": "飞书AppID",
        "pattern": r"cli_[a-f0-9]+",
        "risk": "medium",
        "description": "飞书应用AppID"
    }
]

def validate_id_card(number):
    """校验身份证号校验位"""
    if len(number) != 18:
        return False
    weights = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
    check_chars = "10X98765432"
    try:
        total = sum(int(number[i]) * weights[i] for i in range(17))
        return check_chars[total % 11] == number[17].upper()
    except (ValueError, IndexError):
        return False

def validate_bank_card(number):
    """LUHN算法校验银行卡号"""
    digits = [int(d) for d in number]
    odd_digits = digits[-1::-2]
    even_digits = digits[-2::-2]
    total = sum(odd_digits)
    for d in even_digits:
        total += sum(divmod(d * 2, 10))
    return total % 10 == 0

def scan_text(text, rules=None):
    """扫描文本中的PII"""
    findings = []
    active_rules = rules or PII_RULES
    
    for rule in active_rules:
        matches = re.finditer(rule["pattern"], text)
        for match in matches:
            value = match.group()
            start = match.start()
            
            finding = {
                "rule_id": rule["id"],
                "type": rule["name"],
                "risk": rule["risk"],
                "position": start,
                "length": len(value),
                "preview": value[:3] + "***" + value[-2:] if len(value) > 8 else value[:2] + "***",
                "validated": None
            }
            
            # 格式校验
            if rule["id"] == "id_card_cn" and len(value) == 18:
                finding["validated"] = validate_id_card(value)
            elif rule["id"] == "bank_card":
                finding["validated"] = validate_bank_card(value)
            
            findings.append(finding)
    
    # 去重(同位置同类型)
    seen = set()
    unique = []
    for f in findings:
        key = (f["rule_id"], f["position"])
        if key not in seen:
            seen.add(key)
            unique.append(f)
    
    return unique

def scan_file(filepath):
    """扫描文件"""
    if not os.path.exists(filepath):
        return {"status": "error", "message": f"文件不存在: {filepath}"}
    
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()
    
    findings = scan_text(text)
    return {
        "status": "success",
        "file": filepath,
        "file_size": os.path.getsize(filepath),
        "total_findings": len(findings),
        "findings": findings,
        "risk_summary": {
            "critical": sum(1 for f in findings if f["risk"] == "critical"),
            "high": sum(1 for f in findings if f["risk"] == "high"),
            "medium": sum(1 for f in findings if f["risk"] == "medium"),
            "low": sum(1 for f in findings if f["risk"] == "low")
        }
    }

def main():
    parser = argparse.ArgumentParser(description="PII隐私扫描")
    parser.add_argument("--input", default=None, help="直接输入文本")
    parser.add_argument("--file", default=None, help="扫描文件路径")
    args = parser.parse_args()
    
    if args.file:
        result = scan_file(args.file)
    elif args.input:
        findings = scan_text(args.input)
        result = {
            "status": "success",
            "total_findings": len(findings),
            "findings": findings,
            "risk_summary": {
                "critical": sum(1 for f in findings if f["risk"] == "critical"),
                "high": sum(1 for f in findings if f["risk"] == "high"),
                "medium": sum(1 for f in findings if f["risk"] == "medium"),
                "low": sum(1 for f in findings if f["risk"] == "low")
            }
        }
    else:
        result = {"status": "error", "message": "请指定 --input 或 --file"}
    
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
