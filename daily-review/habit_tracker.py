#!/usr/bin/env python3
"""每日状态评测日记 - 习惯打卡与连续追踪"""
import json
import argparse
import os
from datetime import datetime, timedelta

HABIT_FILE = "habits.json"

def load_habits():
    if os.path.exists(HABIT_FILE):
        with open(HABIT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"habits": {}}

def save_habits(data):
    with open(HABIT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def checkin(habit_name, date_str=None):
    data = load_habits()
    today = date_str or datetime.now().strftime("%Y-%m-%d")
    
    if habit_name not in data["habits"]:
        data["habits"][habit_name] = {
            "name": habit_name,
            "created": today,
            "checkins": [],
            "streak": 0,
            "best_streak": 0
        }
    
    habit = data["habits"][habit_name]
    
    if today in habit["checkins"]:
        return {"status": "already_checked", "habit": habit_name, "message": f"{today}已打卡"}
    
    habit["checkins"].append(today)
    habit["checkins"].sort()
    
    # 计算连续天数
    streak = 1
    check_date = datetime.strptime(today, "%Y-%m-%d")
    for i in range(1, 365):
        prev = (check_date - timedelta(days=i)).strftime("%Y-%m-%d")
        if prev in habit["checkins"]:
            streak += 1
        else:
            break
    
    habit["streak"] = streak
    if streak > habit["best_streak"]:
        habit["best_streak"] = streak
    
    save_habits(data)
    return {
        "status": "success",
        "habit": habit_name,
        "date": today,
        "current_streak": streak,
        "best_streak": habit["best_streak"],
        "total_checkins": len(habit["checkins"]),
        "message": f"打卡成功! 连续{streak}天" + (f"，新纪录!" if streak == habit["best_streak"] else "")
    }

def query(habit_name=None):
    data = load_habits()
    if not data["habits"]:
        return {"status": "no_habits", "message": "暂无习惯记录"}
    
    if habit_name:
        if habit_name in data["habits"]:
            h = data["habits"][habit_name]
            return {"status": "success", "habit": h}
        return {"status": "not_found", "habit": habit_name}
    
    # 查询所有
    summary = []
    for name, h in data["habits"].items():
        summary.append({
            "name": name,
            "streak": h["streak"],
            "best_streak": h["best_streak"],
            "total": len(h["checkins"]),
            "last_checkin": h["checkins"][-1] if h["checkins"] else "never"
        })
    return {"status": "success", "habits": summary}

def main():
    parser = argparse.ArgumentParser(description="习惯打卡与追踪")
    parser.add_argument("--habit", required=True, help="习惯名称")
    parser.add_argument("--action", choices=["checkin", "query"], default="checkin", help="操作: checkin打卡, query查询")
    parser.add_argument("--date", default=None, help="指定日期 YYYY-MM-DD")
    args = parser.parse_args()
    
    if args.action == "checkin":
        result = checkin(args.habit, args.date)
    else:
        result = query(args.habit)
    
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
