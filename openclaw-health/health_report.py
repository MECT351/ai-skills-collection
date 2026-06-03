#!/usr/bin/env python3
"""OpenClaw健康自检 - 汇总生成整体健康报告"""
import json
import argparse
import os
import time

def load_config(config_path):
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def run_config_check(config):
    """内嵌配置校验"""
    from config_check import check_config
    return check_config(config)

def run_connectivity(config_path):
    """内嵌连通性检测"""
    from connectivity import check_connectivity
    return check_connectivity(config_path)

def run_channel_diag(config):
    """内嵌渠道诊断"""
    from channel_diag import diagnose_channel
    channels = config.get("channels", {})
    results = []
    for name, ch_config in channels.items():
        results.append(diagnose_channel(name, ch_config))
    return results

def generate_report(config_path):
    """生成完整健康报告"""
    config = load_config(config_path)
    if not config:
        return {"status": "error", "message": f"配置文件不存在: {config_path}"}
    
    report = {
        "status": "healthy",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "agent_name": config.get("agent_name", "unknown"),
        "summary": {
            "total_channels": 0,
            "healthy_channels": 0,
            "unhealthy_channels": 0,
            "total_issues": 0,
            "total_warnings": 0,
            "failed_endpoints": 0
        },
        "config_check": None,
        "connectivity": None,
        "channel_diagnostics": None,
        "recommendations": []
    }
    
    # 1. 配置校验
    try:
        config_result = run_config_check(config)
        report["config_check"] = config_result
        report["summary"]["total_issues"] += config_result.get("total_issues", 0)
        report["summary"]["total_warnings"] += config_result.get("total_warnings", 0)
    except Exception as e:
        report["config_check"] = {"status": "error", "message": str(e)}
    
    # 2. 连通性检测
    try:
        conn_result = run_connectivity(config_path)
        report["connectivity"] = conn_result
        report["summary"]["failed_endpoints"] = conn_result.get("failed_count", 0)
    except Exception as e:
        report["connectivity"] = {"status": "error", "message": str(e)}
    
    # 3. 渠道诊断
    try:
        diag_results = run_channel_diag(config)
        report["channel_diagnostics"] = diag_results
        channels = config.get("channels", {})
        report["summary"]["total_channels"] = len(channels)
        for d in diag_results:
            if d.get("status") == "healthy":
                report["summary"]["healthy_channels"] += 1
            else:
                report["summary"]["unhealthy_channels"] += 1
    except Exception as e:
        report["channel_diagnostics"] = {"status": "error", "message": str(e)}
    
    # 综合判定
    total_issues = report["summary"]["total_issues"]
    failed_eps = report["summary"]["failed_endpoints"]
    unhealthy_chs = report["summary"]["unhealthy_channels"]
    
    if total_issues == 0 and failed_eps == 0 and unhealthy_chs == 0:
        report["status"] = "healthy"
    elif total_issues > 3 or failed_eps > 2 or unhealthy_chs > 1:
        report["status"] = "critical"
    else:
        report["status"] = "degraded"
    
    # 生成建议
    recommendations = []
    if total_issues > 0:
        recommendations.append(f"发现{total_issues}个配置问题，请优先修复error级别项")
    if failed_eps > 0:
        recommendations.append(f"{failed_eps}个端点连通异常，检查网络或代理设置")
    if unhealthy_chs > 0:
        recommendations.append(f"{unhealthy_chs}个渠道配置不完整，参照诊断结果补充")
    if report["summary"]["total_warnings"] > 0:
        recommendations.append(f"有{report['summary']['total_warnings']}个警告项，建议后续优化")
    if not recommendations:
        recommendations.append("所有检查通过，OpenClaw运行状态良好")
    
    report["recommendations"] = recommendations
    return report

def main():
    parser = argparse.ArgumentParser(description="OpenClaw整体健康报告")
    parser.add_argument("--config", required=True, help="配置文件路径")
    args = parser.parse_args()
    
    result = generate_report(args.config)
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
