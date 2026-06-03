#!/usr/bin/env python3
"""每日状态评测日记 - 生成结构化日评模板"""
import json
import argparse
import os
from datetime import datetime

DATA_FILE = "diary.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"records": {}}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def create_review(date_str, mood, energy, focus=None, gratitude=None, todo_done=None, todo_plan=None):
    data = load_data()
    review = {
        "date": date_str,
        "mood": mood,
        "energy": max(1, min(10, energy)),
        "focus": focus or "",
        "gratitude": gratitude or "",
        "todo_done": todo_done or [],
        "todo_plan": todo_plan or [],
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "tags": []
    }
    # 自动标签
    if energy >= 8:
        review["tags"].append("高能量")
    elif energy <= 3:
        review["tags"].append("低能量")
    if any(w in mood for w in ["焦虑", "压力", "烦躁"]):
        review["tags"].append("需关注")
    if any(w in mood for w in ["开心", "充实", "满足"]):
        review["tags"].append("正向")
    
    data["records"][date_str] = review
    save_data(data)
    return review

def main():
    parser = argparse.ArgumentParser(description="生成结构化日评")
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"), help="日期 YYYY-MM-DD")
    parser.add_argument("--mood", required=True, help="心情关键词")
    parser.add_argument("--energy", type=int, required=True, help="精力等级1-10")
    parser.add_argument("--focus", default="", help="今日专注事项")
    parser.add_argument("--gratitude", default="", help="感恩/收获")
    parser.add_argument("--done", nargs="*", default=[], help="已完成事项")
    parser.add_argument("--plan", nargs="*", default=[], help="明日计划")
    args = parser.parse_args()

    result = create_review(args.date, args.mood, args.energy, args.focus, args.gratitude, args.done, args.plan)
    print(json.dumps({"status": "success", "review": result}, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
