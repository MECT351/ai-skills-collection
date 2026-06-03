#!/usr/bin/env python3
"""主人隐私卫士 - 一键清洗"""
import json
import argparse
import os
import time

def sanitize_file(filepath, output_path=None):
    """一键清洗文件"""
    from scan import scan_text
    from redact import redact_text, load_rules, REDACT_STRATEGIES
    
    if not os.path.exists(filepath):
        return {"status": "error", "message": f"文件不存在: {filepath}"}
    
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        original = f.read()
    
    # 第一步：扫描
    findings = scan_text(original)
    
    if not findings:
        return {
            "status": "clean",
            "message": "未发现PII，文件无需清洗",
            "original_size": len(original),
            "findings": 0
        }
    
    # 第二步：脱敏
    rules = load_rules()
    redact_result = redact_text(original, rules, REDACT_STRATEGIES)
    
    # 第三步：二次扫描确认
    remaining = scan_text(redact_result["redacted_text"])
    
    # 输出
    if output_path is None:
        base, ext = os.path.splitext(filepath)
        output_path = f"{base}_sanitized{ext}"
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(redact_result["redacted_text"])
    
    # 统计
    risk_before = {
        "critical": sum(1 for f in findings if f["risk"] == "critical"),
        "high": sum(1 for f in findings if f["risk"] == "high"),
        "medium": sum(1 for f in findings if f["risk"] == "medium"),
        "low": sum(1 for f in findings if f["risk"] == "low")
    }
    
    risk_after = {
        "critical": sum(1 for f in remaining if f["risk"] == "critical"),
        "high": sum(1 for f in remaining if f["risk"] == "high"),
        "medium": sum(1 for f in remaining if f["risk"] == "medium"),
        "low": sum(1 for f in remaining if f["risk"] == "low")
    }
    
    result = {
        "status": "sanitized",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "source_file": filepath,
        "output_file": output_path,
        "original_size": len(original),
        "sanitized_size": len(redact_result["redacted_text"]),
        "findings_before": len(findings),
        "findings_after": len(remaining),
        "redactions": redact_result["total_redactions"],
        "risk_before": risk_before,
        "risk_after": risk_after,
        "redaction_log": redact_result["redaction_log"],
        "verified_clean": len(remaining) == 0
    }
    
    if remaining:
        result["warning"] = f"清洗后仍有{len(remaining)}个疑似PII残留，建议人工复查"
    
    return result

def sanitize_text(text):
    """一键清洗文本"""
    from scan import scan_text
    from redact import redact_text, load_rules, REDACT_STRATEGIES
    
    findings = scan_text(text)
    
    if not findings:
        return {
            "status": "clean",
            "message": "未发现PII",
            "sanitized_text": text,
            "findings": 0
        }
    
    rules = load_rules()
    redact_result = redact_text(text, rules, REDACT_STRATEGIES)
    remaining = scan_text(redact_result["redacted_text"])
    
    return {
        "status": "sanitized",
        "findings_before": len(findings),
        "findings_after": len(remaining),
        "redactions": redact_result["total_redactions"],
        "sanitized_text": redact_result["redacted_text"],
        "redaction_log": redact_result["redaction_log"],
        "verified_clean": len(remaining) == 0
    }

def main():
    parser = argparse.ArgumentParser(description="一键PII清洗")
    parser.add_argument("--file", default=None, help="输入文件路径")
    parser.add_argument("--input", default=None, help="直接输入文本")
    parser.add_argument("--output", default=None, help="输出文件路径(可选)")
    args = parser.parse_args()
    
    if args.file:
        result = sanitize_file(args.file, args.output)
    elif args.input:
        result = sanitize_text(args.input)
    else:
        result = {"status": "error", "message": "请指定 --file 或 --input"}
    
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
