#!/usr/bin/env python3
"""OpenClaw健康自检 - 各渠道端点HTTP连通性探测"""
import json
import argparse
import os
import time
import urllib.request
import urllib.error
import ssl

# 各渠道已知端点
CHANNEL_ENDPOINTS = {
    "feishu": [
        {"name": "飞书开放平台", "url": "https://open.feishu.cn/open-apis/bot/v2/hook/", "method": "HEAD", "timeout": 10},
        {"name": "飞书API", "url": "https://open.feishu.cn/open-apis/", "method": "GET", "timeout": 10}
    ],
    "wechat": [
        {"name": "微信API", "url": "https://api.weixin.qq.com/cgi-bin/token", "method": "GET", "timeout": 10}
    ],
    "dingtalk": [
        {"name": "钉钉API", "url": "https://oapi.dingtalk.com/gettoken", "method": "GET", "timeout": 10}
    ],
    "coze": [
        {"name": "Coze API", "url": "https://api.coze.cn/v1/chat", "method": "HEAD", "timeout": 10}
    ]
}

# 通用连通性检测端点
GENERAL_ENDPOINTS = [
    {"name": "DNS解析", "url": "https://www.baidu.com", "method": "HEAD", "timeout": 5},
    {"name": "HTTPS连通", "url": "https://httpbin.org/status/200", "method": "GET", "timeout": 10}
]

def probe_endpoint(endpoint, timeout=10):
    """探测单个端点"""
    url = endpoint["url"]
    method = endpoint.get("method", "GET")
    name = endpoint.get("name", url)
    
    result = {
        "name": name,
        "url": url,
        "method": method,
        "status": "unknown",
        "status_code": None,
        "latency_ms": None,
        "error": None
    }
    
    try:
        ctx = ssl.create_default_context()
        req = urllib.request.Request(url, method=method)
        req.add_header("User-Agent", "OpenClaw-HealthCheck/1.0")
        
        start = time.time()
        resp = urllib.request.urlopen(req, timeout=timeout, context=ctx)
        latency = round((time.time() - start) * 1000, 1)
        
        result["status"] = "ok"
        result["status_code"] = resp.status
        result["latency_ms"] = latency
        
    except urllib.error.HTTPError as e:
        latency = round((time.time() - start) * 1000, 1)
        result["status"] = "http_error"
        result["status_code"] = e.code
        result["latency_ms"] = latency
        result["error"] = str(e)
        
    except urllib.error.URLError as e:
        result["status"] = "connection_error"
        result["error"] = str(e.reason)
        
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
    
    return result

def check_connectivity(config_path, channels_only=False):
    """执行连通性检测"""
    config = None
    configured_channels = []
    
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        configured_channels = list(config.get("channels", {}).keys())
    
    results = {
        "status": "healthy",
        "general": [],
        "channels": {},
        "failed_count": 0
    }
    
    # 通用连通性
    if not channels_only:
        for ep in GENERAL_ENDPOINTS:
            r = probe_endpoint(ep, ep.get("timeout", 10))
            results["general"].append(r)
            if r["status"] not in ("ok", "http_error"):
                results["failed_count"] += 1
    
    # 渠道端点检测
    channels_to_check = configured_channels if configured_channels else list(CHANNEL_ENDPOINTS.keys())
    for ch in channels_to_check:
        if ch not in CHANNEL_ENDPOINTS:
            results["channels"][ch] = {"status": "skip", "message": f"无已知端点: {ch}"}
            continue
        
        ch_results = []
        for ep in CHANNEL_ENDPOINTS[ch]:
            r = probe_endpoint(ep, ep.get("timeout", 10))
            ch_results.append(r)
            if r["status"] not in ("ok", "http_error"):
                results["failed_count"] += 1
        
        all_ok = all(r["status"] == "ok" for r in ch_results)
        results["channels"][ch] = {
            "status": "ok" if all_ok else "degraded",
            "endpoints": ch_results
        }
    
    if results["failed_count"] > 0:
        results["status"] = "degraded" if results["failed_count"] < 3 else "unhealthy"
    
    return results

def main():
    parser = argparse.ArgumentParser(description="OpenClaw连通性探测")
    parser.add_argument("--config", required=True, help="配置文件路径")
    parser.add_argument("--channels-only", action="store_true", help="仅检测配置中的渠道")
    args = parser.parse_args()
    
    result = check_connectivity(args.config, args.channels_only)
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
