#!/usr/bin/env python3
"""OpenClaw健康自检 - 配置文件校验"""
import json
import argparse
import os
import re

# OpenClaw配置必需字段定义
REQUIRED_ROOT = ["agent_name", "channels"]
OPTIONAL_ROOT = ["port", "log_level", "base_url", "secret_key"]

CHANNEL_SCHEMAS = {
    "feishu": {
        "required": ["app_id", "app_secret", "verification_token", "encrypt_key"],
        "optional": ["bot_name"],
        "patterns": {"app_id": r"^cli_[a-f0-9]+$", "verification_token": r"^[a-zA-Z0-9]{10,}$"}
    },
    "wechat": {
        "required": ["app_id", "app_secret", "token", "encoding_aes_key"],
        "optional": ["bot_name"],
        "patterns": {"app_id": r"^wx[a-f0-9]{16}$", "encoding_aes_key": r"^[a-zA-Z0-9]{43}$"}
    },
    "dingtalk": {
        "required": ["client_id", "client_secret"],
        "optional": ["bot_name", "robot_code"],
        "patterns": {"client_id": r"^ding[a-z0-9]+$"}
    },
    "coze": {
        "required": ["bot_id", "api_key"],
        "optional": ["bot_name"],
        "patterns": {"api_key": r"^pat_[a-zA-Z0-9]+$|^sk_[a-zA-Z0-9]+$"}
    }
}

def validate_pattern(value, pattern):
    return bool(re.match(pattern, str(value))) if value else False

def check_config(config):
    issues = []
    warnings = []
    
    if isinstance(config, str):
        if not os.path.exists(config):
            return {"status": "error", "issues": [{"level": "critical", "field": "config_file", "message": f"文件不存在: {config}"}]}
        with open(config, "r", encoding="utf-8") as f:
            config = json.load(f)
    
    # 根字段校验
    for field in REQUIRED_ROOT:
        if field not in config:
            issues.append({"level": "critical", "field": field, "message": f"缺少必需字段: {field}"})
        elif not config[field]:
            issues.append({"level": "error", "field": field, "message": f"字段为空: {field}"})
    
    for field in OPTIONAL_ROOT:
        if field not in config:
            warnings.append({"level": "warning", "field": field, "message": f"建议配置字段: {field}"})
    
    # port校验
    if "port" in config:
        port = config["port"]
        if not isinstance(port, int) or port < 1 or port > 65535:
            issues.append({"level": "error", "field": "port", "message": f"端口号无效: {port}，应为1-65535"})
    
    # channels校验
    channels = config.get("channels", {})
    if isinstance(channels, list):
        issues.append({"level": "error", "field": "channels", "message": "channels应为对象(dict)而非数组"})
    elif isinstance(channels, dict):
        for ch_name, ch_config in channels.items():
            if ch_name not in CHANNEL_SCHEMAS:
                warnings.append({"level": "warning", "field": f"channels.{ch_name}", "message": f"未识别的渠道类型: {ch_name}"})
                continue
            
            schema = CHANNEL_SCHEMAS[ch_name]
            ch_issues = check_channel(ch_name, ch_config, schema)
            issues.extend(ch_issues.get("issues", []))
            warnings.extend(ch_issues.get("warnings", []))
    
    # secret_key检查
    if "secret_key" in config:
        sk = config["secret_key"]
        if len(str(sk)) < 8:
            warnings.append({"level": "warning", "field": "secret_key", "message": "secret_key过短，建议至少8位"})
    
    return {
        "status": "healthy" if not issues else "unhealthy",
        "total_issues": len(issues),
        "total_warnings": len(warnings),
        "issues": issues,
        "warnings": warnings
    }

def check_channel(name, config, schema):
    issues = []
    warnings = []
    
    if not isinstance(config, dict):
        issues.append({"level": "error", "field": f"channels.{name}", "message": f"渠道配置应为对象"})
        return {"issues": issues, "warnings": warnings}
    
    for field in schema["required"]:
        if field not in config:
            issues.append({"level": "error", "field": f"channels.{name}.{field}", "message": f"缺少必需字段: {field}"})
        elif not config[field]:
            issues.append({"level": "error", "field": f"channels.{name}.{field}", "message": f"字段为空: {field}"})
    
    for field in schema.get("optional", []):
        if field not in config:
            warnings.append({"level": "warning", "field": f"channels.{name}.{field}", "message": f"建议配置: {field}"})
    
    # 格式校验
    for field, pattern in schema.get("patterns", {}).items():
        if field in config and config[field]:
            if not validate_pattern(config[field], pattern):
                warnings.append({"level": "warning", "field": f"channels.{name}.{field}", "message": f"字段格式可能不正确: {field}={config[field][:6]}..."})
    
    return {"issues": issues, "warnings": warnings}

def main():
    parser = argparse.ArgumentParser(description="OpenClaw配置文件校验")
    parser.add_argument("--config", required=True, help="配置文件路径或JSON字符串")
    args = parser.parse_args()
    
    result = check_config(args.config)
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
