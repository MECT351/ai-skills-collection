#!/usr/bin/env python3
"""OpenClaw健康自检 - 逐渠道配置诊断"""
import json
import argparse
import os
import re

def load_config(config_path):
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

# 各渠道诊断规则
DIAGNOSTICS = {
    "feishu": {
        "name": "飞书",
        "checks": [
            {
                "field": "app_id",
                "label": "应用ID",
                "rules": [
                    {"type": "required", "message": "飞书app_id不能为空"},
                    {"type": "pattern", "pattern": r"^cli_[a-f0-9]+$", "message": "app_id格式应为cli_开头+十六进制"}
                ]
            },
            {
                "field": "app_secret",
                "label": "应用密钥",
                "rules": [
                    {"type": "required", "message": "app_secret不能为空"},
                    {"type": "min_length", "min": 20, "message": "app_secret长度不足，可能不完整"}
                ]
            },
            {
                "field": "verification_token",
                "label": "事件验证令牌",
                "rules": [
                    {"type": "required", "message": "verification_token不能为空"},
                    {"type": "min_length", "min": 10, "message": "verification_token长度不足"}
                ]
            },
            {
                "field": "encrypt_key",
                "label": "加密密钥",
                "rules": [
                    {"type": "required", "message": "encrypt_key不能为空(可为空字符串但需显式配置)"}
                ]
            },
            {
                "field": "bot_name",
                "label": "机器人名称",
                "rules": [
                    {"type": "optional", "message": "建议配置bot_name便于识别"}
                ]
            }
        ],
        "common_issues": [
            "事件订阅未配置回调地址",
            "权限范围不足(需消息接收+回复权限)",
            "encrypt_key为空但开启了加密",
            "app_id与app_secret不匹配"
        ]
    },
    "wechat": {
        "name": "微信",
        "checks": [
            {
                "field": "app_id",
                "label": "公众号/小程序AppID",
                "rules": [
                    {"type": "required", "message": "微信app_id不能为空"},
                    {"type": "pattern", "pattern": r"^wx[a-f0-9]{16}$", "message": "app_id应以wx开头+16位十六进制"}
                ]
            },
            {
                "field": "app_secret",
                "label": "应用密钥",
                "rules": [
                    {"type": "required", "message": "app_secret不能为空"},
                    {"type": "min_length", "min": 20, "message": "app_secret长度不足"}
                ]
            },
            {
                "field": "token",
                "label": "消息校验Token",
                "rules": [
                    {"type": "required", "message": "token不能为空"},
                    {"type": "min_length", "min": 3, "message": "token长度不足"}
                ]
            },
            {
                "field": "encoding_aes_key",
                "label": "消息加解密密钥",
                "rules": [
                    {"type": "required", "message": "encoding_aes_key不能为空"},
                    {"type": "pattern", "pattern": r"^[a-zA-Z0-9]{43}$", "message": "encoding_aes_key应为43位字母数字"}
                ]
            }
        ],
        "common_issues": [
            "服务器地址(Token)未配置",
            "IP白名单未添加服务器IP",
            "消息加解密方式不匹配",
            "公众号类型不支持所需接口"
        ]
    },
    "dingtalk": {
        "name": "钉钉",
        "checks": [
            {
                "field": "client_id",
                "label": "应用ClientID",
                "rules": [
                    {"type": "required", "message": "client_id不能为空"}
                ]
            },
            {
                "field": "client_secret",
                "label": "应用ClientSecret",
                "rules": [
                    {"type": "required", "message": "client_secret不能为空"},
                    {"type": "min_length", "min": 20, "message": "client_secret长度不足"}
                ]
            }
        ],
        "common_issues": [
            "机器人未启用或未发布",
            "事件订阅回调地址未验证",
            "应用权限未开通消息接口",
            "robot_code与client_id不匹配"
        ]
    },
    "coze": {
        "name": "Coze",
        "checks": [
            {
                "field": "bot_id",
                "label": "Bot ID",
                "rules": [
                    {"type": "required", "message": "bot_id不能为空"}
                ]
            },
            {
                "field": "api_key",
                "label": "API密钥",
                "rules": [
                    {"type": "required", "message": "api_key不能为空"},
                    {"type": "pattern", "pattern": r"^pat_|^sk_", "message": "api_key应以pat_或sk_开头"}
                ]
            }
        ],
        "common_issues": [
            "Bot未发布或已下线",
            "API Key权限不足",
            "Bot版本与API版本不匹配",
            "工作流/插件调用权限未开通"
        ]
    }
}

def run_check(value, rule):
    """执行单条校验规则"""
    rtype = rule["type"]
    
    if rtype == "required":
        if not value:
            return rule["message"]
    elif rtype == "optional":
        if not value:
            return rule["message"]
    elif rtype == "pattern":
        if value and not re.match(rule["pattern"], str(value)):
            return rule["message"]
    elif rtype == "min_length":
        if value and len(str(value)) < rule["min"]:
            return rule["message"]
    
    return None

def diagnose_channel(channel_name, channel_config):
    """诊断单个渠道"""
    if channel_name not in DIAGNOSTICS:
        return {
            "channel": channel_name,
            "status": "unknown",
            "message": f"未识别的渠道类型: {channel_name}",
            "checks": [],
            "tips": []
        }
    
    diag = DIAGNOSTICS[channel_name]
    check_results = []
    issue_count = 0
    
    for check in diag["checks"]:
        field = check["field"]
        value = channel_config.get(field, "") if isinstance(channel_config, dict) else ""
        
        for rule in check["rules"]:
            msg = run_check(value, rule)
            if msg:
                level = "warning" if rule["type"] == "optional" else "error"
                check_results.append({
                    "field": field,
                    "label": check["label"],
                    "level": level,
                    "message": msg
                })
                if level == "error":
                    issue_count += 1
    
    return {
        "channel": channel_name,
        "channel_name": diag["name"],
        "status": "healthy" if issue_count == 0 else "unhealthy",
        "checks": check_results,
        "tips": diag.get("common_issues", [])
    }

def main():
    parser = argparse.ArgumentParser(description="OpenClaw渠道诊断")
    parser.add_argument("--config", required=True, help="配置文件路径")
    parser.add_argument("--channel", default=None, help="指定渠道名(不传则诊断全部)")
    args = parser.parse_args()
    
    config = load_config(args.config)
    if not config:
        print(json.dumps({"status": "error", "message": f"配置文件不存在: {args.config}"}, ensure_ascii=False))
        return
    
    channels = config.get("channels", {})
    if not channels:
        print(json.dumps({"status": "error", "message": "配置中无渠道定义"}, ensure_ascii=False))
        return
    
    if args.channel:
        if args.channel not in channels:
            print(json.dumps({"status": "error", "message": f"渠道不存在: {args.channel}"}, ensure_ascii=False))
            return
        result = diagnose_channel(args.channel, channels[args.channel])
    else:
        results = []
        for name, ch_config in channels.items():
            results.append(diagnose_channel(name, ch_config))
        result = {
            "status": "healthy" if all(r["status"] == "healthy" for r in results) else "unhealthy",
            "channels": results
        }
    
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
