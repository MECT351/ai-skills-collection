#!/usr/bin/env python3
"""主人隐私卫士 - 隐私审计报告"""
import json
import argparse
import os
import time

def load_scan_result(filepath):
    """加载扫描结果或直接扫描"""
    from scan import scan_file, scan_text
    return scan_file(filepath)

def generate_report(filepath):
    """生成隐私审计报告"""
    scan_result = load_scan_result(filepath)
    
    if scan_result.get("status") != "success":
        return scan_result
    
    findings = scan_result.get("findings", [])
    risk_summary = scan_result.get("risk_summary", {})
    
    # 风险评分 (0-100, 越高越危险)
    score = 0
    score += risk_summary.get("critical", 0) * 25
    score += risk_summary.get("high", 0) * 15
    score += risk_summary.get("medium", 0) * 5
    score += risk_summary.get("low", 0) * 1
    score = min(100, score)
    
    # 风险等级
    if score >= 75:
        risk_level = "危险"
    elif score >= 50:
        risk_level = "高风险"
    elif score >= 25:
        risk_level = "中等风险"
    elif score > 0:
        risk_level = "低风险"
    else:
        risk_level = "安全"
    
    # 按类型统计
    type_stats = {}
    for f in findings:
        t = f["type"]
        if t not in type_stats:
            type_stats[t] = {"count": 0, "risk": f["risk"], "validated": []}
        type_stats[t]["count"] += 1
        if f.get("validated") is not None:
            type_stats[t]["validated"].append(f["validated"])
    
    # 校验结果统计
    validation_stats = {"total_validated": 0, "valid": 0, "invalid": 0}
    for f in findings:
        if f.get("validated") is not None:
            validation_stats["total_validated"] += 1
            if f["validated"]:
                validation_stats["valid"] += 1
            else:
                validation_stats["invalid"] += 1
    
    # 建议生成
    recommendations = []
    
    if risk_summary.get("critical", 0) > 0:
        recommendations.append({
            "priority": "紧急",
            "action": f"发现{risk_summary['critical']}个严重隐私泄露项(API Key/身份证/银行卡)",
            "detail": "立即脱敏或移除，这些信息泄露可能导致财产损失"
        })
    
    if risk_summary.get("high", 0) > 0:
        recommendations.append({
            "priority": "高",
            "action": f"发现{risk_summary['high']}个高风险项(手机号/JWT)",
            "detail": "手机号可被用于短信轰炸/社交工程攻击，建议脱敏"
        })
    
    if risk_summary.get("medium", 0) > 0:
        recommendations.append({
            "priority": "中",
            "action": f"发现{risk_summary['medium']}个中风险项(邮箱/AppID)",
            "detail": "邮箱可能收到垃圾邮件，AppID可能被滥用调用"
        })
    
    if validation_stats["invalid"] > 0:
        recommendations.append({
            "priority": "低",
            "action": f"{validation_stats['invalid']}个疑似PII格式校验未通过",
            "detail": "可能是误报，但建议人工确认"
        })
    
    # 特定类型建议
    for t, stat in type_stats.items():
        if t == "API密钥" and stat["count"] > 0:
            recommendations.append({
                "priority": "紧急",
                "action": "API密钥不应出现在文档中",
                "detail": "请将密钥移至环境变量或密钥管理服务，文档中使用占位符"
            })
            break
    
    if not recommendations:
        recommendations.append({
            "priority": "无",
            "action": "未发现隐私风险",
            "detail": "该文件可以安全分享"
        })
    
    report = {
        "status": "success",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "file": filepath,
        "file_size": scan_result.get("file_size", 0),
        "risk_score": score,
        "risk_level": risk_level,
        "total_findings": len(findings),
        "risk_summary": risk_summary,
        "type_breakdown": type_stats,
        "validation_stats": validation_stats,
        "recommendations": recommendations
    }
    
    return report

def main():
    parser = argparse.ArgumentParser(description="隐私审计报告")
    parser.add_argument("--file", required=True, help="待审计文件路径")
    args = parser.parse_args()
    
    result = generate_report(args.file)
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
