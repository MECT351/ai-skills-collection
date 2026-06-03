#!/usr/bin/env python3
"""每日状态评测日记 - 周度总结报告"""
import json
import argparse
import os
from datetime import datetime, timedelta

def load_data(filepath):
    if not os.path.exists(filepath):
        return None
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def load_habits(filepath):
    if not os.path.exists(filepath):
        return None
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def generate_weekly(start_date_str, diary_path="diary.json", habits_path="habits.json"):
    data = load_data(diary_path)
    if not data:
        return {"status": "error", "message": "日记数据文件不存在"}
    
    start = datetime.strptime(start_date_str, "%Y-%m-%d")
    dates = [(start + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
    
    records = data.get("records", {})
    week_records = {d: records[d] for d in dates if d in records}
    
    if not week_records:
        return {"status": "no_data", "message": f"{start_date_str}起一周内无日记记录"}
    
    # 统计
    energy_vals = [r.get("energy", 5) for r in week_records.values()]
    mood_list = [r.get("mood", "") for r in week_records.values()]
    all_tags = []
    all_done = []
    all_plan = []
    
    for r in week_records.values():
        all_tags.extend(r.get("tags", []))
        all_done.extend(r.get("todo_done", []))
        all_plan.extend(r.get("todo_plan", []))
    
    tag_count = {}
    for t in all_tags:
        tag_count[t] = tag_count.get(t, 0) + 1
    
    avg_energy = round(sum(energy_vals) / len(energy_vals), 1) if energy_vals else 0
    
    # 习惯数据
    habits_data = load_habits(habits_path)
    habit_summary = []
    if habits_data:
        for name, h in habits_data.get("habits", {}).items():
            week_checkins = [c for c in h.get("checkins", []) if c in dates]
            if week_checkins:
                habit_summary.append({
                    "name": name,
                    "week_checkins": len(week_checkins),
                    "current_streak": h.get("streak", 0),
                    "best_streak": h.get("best_streak", 0)
                })
    
    # 周度评价
    if avg_energy >= 7:
        week_level = "高效周"
    elif avg_energy >= 5:
        week_level = "平稳周"
    else:
        week_level = "调整周"
    
    report = {
        "status": "success",
        "period": f"{dates[0]} ~ {dates[6]}",
        "recorded_days": len(week_records),
        "energy": {
            "average": avg_energy,
            "max": max(energy_vals) if energy_vals else 0,
            "min": min(energy_vals) if energy_vals else 0,
            "daily": {d: records[d].get("energy", 5) for d in week_records}
        },
        "mood_summary": mood_list,
        "tag_distribution": tag_count,
        "completed_tasks": all_done,
        "planned_tasks": all_plan,
        "habits": habit_summary,
        "week_level": week_level,
        "suggestion": ""
    }
    
    # 建议生成
    suggestions = []
    if avg_energy < 5:
        suggestions.append("本周精力偏低，建议增加运动和休息时间")
    if tag_count.get("需关注", 0) >= 3:
        suggestions.append("负面情绪出现较多，建议安排放松活动")
    if len(all_done) < 5:
        suggestions.append("完成事项较少，可尝试拆分大目标为小步骤")
    if habit_summary:
        low_habits = [h["name"] for h in habit_summary if h["week_checkins"] < 4]
        if low_habits:
            suggestions.append(f"习惯「{'、'.join(low_habits)}」本周打卡不足4天，需加强")
    
    if not suggestions:
        suggestions.append("本周状态不错，继续保持!")
    
    report["suggestion"] = "；".join(suggestions)
    return report

def main():
    parser = argparse.ArgumentParser(description="周度总结报告")
    parser.add_argument("--start", required=True, help="周起始日期 YYYY-MM-DD")
    parser.add_argument("--diary", default="diary.json", help="日记数据文件路径")
    parser.add_argument("--habits", default="habits.json", help="习惯数据文件路径")
    args = parser.parse_args()
    
    result = generate_weekly(args.start, args.diary, args.habits)
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
