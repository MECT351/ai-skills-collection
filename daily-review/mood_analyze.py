#!/usr/bin/env python3
"""每日状态评测日记 - 情绪趋势分析"""
import json
import argparse
import os
from datetime import datetime, timedelta

def load_data(filepath):
    if not os.path.exists(filepath):
        return None
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def analyze_trend(data, days=7):
    records = data.get("records", {})
    if not records:
        return {"status": "no_data", "message": "暂无日记数据"}
    
    # 按日期排序
    sorted_dates = sorted(records.keys(), reverse=True)[:days]
    sorted_dates.reverse()
    
    energy_list = []
    mood_list = []
    tag_count = {}
    
    for d in sorted_dates:
        r = records[d]
        energy_list.append(r.get("energy", 5))
        mood_list.append(r.get("mood", ""))
        for t in r.get("tags", []):
            tag_count[t] = tag_count.get(t, 0) + 1
    
    avg_energy = sum(energy_list) / len(energy_list) if energy_list else 5
    max_energy = max(energy_list) if energy_list else 5
    min_energy = min(energy_list) if energy_list else 5
    
    # 能量趋势判断
    if len(energy_list) >= 3:
        first_half = sum(energy_list[:len(energy_list)//2]) / (len(energy_list)//2)
        second_half = sum(energy_list[len(energy_list)//2:]) / (len(energy_list) - len(energy_list)//2)
        if second_half > first_half + 1:
            trend = "上升"
        elif second_half < first_half - 1:
            trend = "下降"
        else:
            trend = "平稳"
    else:
        trend = "数据不足"
    
    # 情绪关键词统计
    mood_keywords = {}
    for m in mood_list:
        for w in m.split():
            mood_keywords[w] = mood_keywords.get(w, 0) + 1
    
    result = {
        "status": "success",
        "period": f"最近{len(sorted_dates)}天",
        "energy": {
            "average": round(avg_energy, 1),
            "max": max_energy,
            "min": min_energy,
            "trend": trend,
            "daily": {d: records[d].get("energy", 5) for d in sorted_dates}
        },
        "mood_keywords": dict(sorted(mood_keywords.items(), key=lambda x: -x[1])[:10]),
        "tag_distribution": tag_count,
        "suggestion": ""
    }
    
    # 生成建议
    if avg_energy < 4:
        result["suggestion"] = "近期精力偏低，建议关注休息质量与运动频率"
    elif avg_energy > 7:
        result["suggestion"] = "近期精力充沛，适合推进重要目标"
    if tag_count.get("需关注", 0) > len(sorted_dates) * 0.4:
        result["suggestion"] += "；负面情绪频次较高，建议适当放松或调整节奏"
    
    return result

def main():
    parser = argparse.ArgumentParser(description="情绪趋势分析")
    parser.add_argument("--file", default="diary.json", help="日记数据文件路径")
    parser.add_argument("--days", type=int, default=7, help="分析最近N天")
    args = parser.parse_args()
    
    data = load_data(args.file)
    if not data:
        print(json.dumps({"status": "error", "message": f"文件不存在: {args.file}"}, ensure_ascii=False))
        return
    
    result = analyze_trend(data, args.days)
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
