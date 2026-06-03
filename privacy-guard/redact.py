#!/usr/bin/env python3
"""主人隐私卫士 - PII脱敏引擎"""
import json
import argparse
import os
import re
import copy

# 脱敏策略
REDACT_STRATEGIES = {
    "phone_cn": {"mode": "partial", "keep_start": 3, "keep_end": 4, "mask": "*"},
    "id_card_cn": {"mode": "partial", "keep_start": 3, "keep_end": 4, "mask": "*"},
    "email": {"mode": "email", "keep_domain": True},
    "bank_card": {"mode": "partial", "keep_start": 4, "keep_end": 4, "mask": "*"},
    "api_key_generic": {"mode": "full", "replacement": "[REDACTED_KEY]"},
    "api_key_openai": {"mode": "full", "replacement": "[REDACTED_OPENAI_KEY]"},
    "api_key_coze": {"mode": "full", "replacement": "[REDACTED_COZE_TOKEN]"},
    "ipv4_private": {"mode": "partial", "keep_start": 0, "keep_end": 0, "mask": "#"},
    "jwt_token": {"mode": "full", "replacement": "[REDACTED_JWT]"},
    "aws_key": {"mode": "full", "replacement": "[REDACTED_AWS_KEY]"},
    "wechat_appid": {"mode": "partial", "keep_start": 2, "keep_end": 0, "mask": "*"},
    "feishu_appid": {"mode": "partial", "keep_start": 4, "keep_end": 0, "mask": "*"}
}

def load_rules():
    """从scan模块加载PII规则"""
    from scan import PII_RULES
    return PII_RULES

def redact_value(value, strategy):
    """按策略脱敏单个值"""
    mode = strategy.get("mode", "full")
    
    if mode == "full":
        return strategy.get("replacement", "[REDACTED]")
    
    elif mode == "partial":
        keep_start = strategy.get("keep_start", 0)
        keep_end = strategy.get("keep_end", 0)
        mask = strategy.get("mask", "*")
        
        if len(value) <= keep_start + keep_end:
            return mask * len(value)
        
        masked_len = len(value) - keep_start - keep_end
        return value[:keep_start] + mask * masked_len + value[len(value) - keep_end:]
    
    elif mode == "email":
        keep_domain = strategy.get("keep_domain", True)
        parts = value.split("@")
        if len(parts) == 2:
            local = parts[0]
            domain = parts[1] if keep_domain else "***.***"
            if len(local) > 2:
                return local[0] + "***" + local[-1] + "@" + domain
            else:
                return "***@" + domain
        return "[REDACTED_EMAIL]"
    
    return "[REDACTED]"

def redact_text(text, rules=None, strategies=None, custom_rules=None):
    """脱敏文本中的PII"""
    if rules is None:
        rules = load_rules()
    if strategies is None:
        strategies = REDACT_STRATEGIES
    
    if custom_rules:
        strategies.update(custom_rules)
    
    redacted = text
    redaction_log = []
    offset = 0
    
    # 收集所有匹配
    all_matches = []
    for rule in rules:
        rule_id = rule["id"]
        strategy = strategies.get(rule_id, {"mode": "full", "replacement": "[REDACTED]"})
        
        for match in re.finditer(rule["pattern"], text):
            original = match.group()
            replacement = redact_value(original, strategy)
            if original != replacement:
                all_matches.append({
                    "start": match.start(),
                    "end": match.end(),
                    "original": original,
                    "replacement": replacement,
                    "rule_id": rule_id,
                    "type": rule["name"],
                    "risk": rule["risk"]
                })
    
    # 按位置排序，从后往前替换避免偏移
    all_matches.sort(key=lambda x: x["start"], reverse=True)
    
    for m in all_matches:
        redacted = redacted[:m["start"]] + m["replacement"] + redacted[m["end"]:]
        redaction_log.append({
            "type": m["type"],
            "rule_id": m["rule_id"],
            "risk": m["risk"],
            "position": m["start"],
            "original_preview": m["original"][:3] + "***" if len(m["original"]) > 5 else "***",
            "replacement": m["replacement"]
        })
    
    redaction_log.reverse()
    
    return {
        "status": "success",
        "original_length": len(text),
        "redacted_length": len(redacted),
        "total_redactions": len(redaction_log),
        "redacted_text": redacted,
        "redaction_log": redaction_log
    }

def main():
    parser = argparse.ArgumentParser(description="PII脱敏")
    parser.add_argument("--input", default=None, help="直接输入文本")
    parser.add_argument("--file", default=None, help="输入文件路径")
    parser.add_argument("--output", default=None, help="输出文件路径(可选)")
    parser.add_argument("--custom-rules", default=None, help="自定义脱敏规则JSON文件")
    args = parser.parse_args()
    
    custom = None
    if args.custom_rules and os.path.exists(args.custom_rules):
        with open(args.custom_rules, "r", encoding="utf-8") as f:
            custom = json.load(f)
    
    text = None
    if args.file:
        if not os.path.exists(args.file):
            print(json.dumps({"status": "error", "message": f"文件不存在: {args.file}"}, ensure_ascii=False))
            return
        with open(args.file, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
    elif args.input:
        text = args.input
    else:
        print(json.dumps({"status": "error", "message": "请指定 --input 或 --file"}, ensure_ascii=False))
        return
    
    result = redact_text(text, custom_rules=custom)
    
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(result["redacted_text"])
        result["output_file"] = args.output
    
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
