#!/usr/bin/env python3
"""采集脚本生成器 — 根据抓取目标生成Playwright数据采集脚本"""

import sys
import json
import argparse


def generate_scrape_script(data):
    """生成数据采集脚本"""
    url = data.get("url", "")
    targets = data.get("targets", [])
    pagination = data.get("pagination", None)
    output_format = data.get("output_format", "json")
    headless = data.get("headless", True)
    timeout = data.get("timeout", 30000)
    max_items = data.get("max_items", 1000)

    if not url:
        return {"status": "error", "message": "缺少url参数"}
    if not targets:
        return {"status": "error", "message": "缺少targets参数，请指定要采集的元素"}

    # 生成目标提取代码
    target_names = [t.get("name", f"field{i+1}") for i, t in enumerate(targets)]
    targets_code = []
    for i, target in enumerate(targets):
        name = target.get("name", f"field{i+1}")
        selector = target.get("selector", f".{name}")
        attr = target.get("attr", "text")  # text or specific attribute like href, src

        if attr == "text":
            targets_code.append(f'                    "{name}": item.query_selector("{selector}").inner_text() if item.query_selector("{selector}") else ""')
        else:
            targets_code.append(f'                    "{name}": item.query_selector("{selector}").get_attribute("{attr}") if item.query_selector("{selector}") else ""')

    # 分页代码
    pagination_code = ""
    if pagination:
        next_selector = pagination.get("next_selector", ".next-page")
        max_pages = pagination.get("max_pages", 5)
        pagination_code = f'''
    # 分页采集
    max_pages = {max_pages}
    for page_num in range(max_pages):
        print(f"[INFO] 正在采集第 {{page_num + 1}} 页...")

        # 采集当前页数据
        items = page.query_selector_all("{targets[0].get('container', '.item') if 'container' in targets[0] else '.item'}")
        for item in items:
            if len(all_data) >= {max_items}:
                break
            try:
                row = {{
{chr(10).join(targets_code)}
                }}
                all_data.append(row)
            except Exception as e:
                print(f"[WARN] 数据提取失败: {{e}}")

        # 翻页
        next_btn = page.query_selector("{next_selector}")
        if next_btn and len(all_data) < {max_items}:
            next_btn.click()
            page.wait_for_load_state("networkidle")
            time.sleep(1)
        else:
            print("[INFO] 没有更多页面或已达到采集上限")
            break'''
    else:
        pagination_code = f'''
    # 单页采集
    items = page.query_selector_all("{targets[0].get('container', '.item') if 'container' in targets[0] else '.item'}")
    for item in items[:{max_items}]:
        try:
            row = {{
{chr(10).join(targets_code)}
            }}
            all_data.append(row)
        except Exception as e:
            print(f"[WARN] 数据提取失败: {{e}}")'''

    # 导出代码
    if output_format == "csv":
        export_code = '''
    # 导出CSV
    import csv
    if all_data:
        with open("scrape_result.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=all_data[0].keys())
            writer.writeheader()
            writer.writerows(all_data)
        print(f"[OK] 数据已导出到 scrape_result.csv")'''
    else:
        export_code = '''
    # 导出JSON
    import json
    with open("scrape_result.json", "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
    print(f"[OK] 数据已导出到 scrape_result.json")'''

    script = f'''#!/usr/bin/env python3
"""数据采集脚本 - 由浏览器自动化脚本生成器生成"""

from playwright.sync_api import sync_playwright
import time


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless={'True' if headless else 'False'})
        context = browser.new_context(
            viewport={{"width": 1280, "height": 720}},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = context.new_page()
        all_data = []

        try:
            # 打开目标页面
            print(f"[INFO] 正在打开 {url}")
            page.goto("{url}", timeout={timeout})
            page.wait_for_load_state("networkidle")
{pagination_code}
            # 数据去重
            seen = set()
            unique_data = []
            for row in all_data:
                key = tuple(sorted(row.items()))
                if key not in seen:
                    seen.add(key)
                    unique_data.append(row)
            all_data = unique_data
            print(f"[OK] 共采集 {{len(all_data)}} 条数据（去重后）")
{export_code}

        except Exception as e:
            print(f"[ERROR] 采集失败: {{e}}")

        finally:
            browser.close()


if __name__ == "__main__":
    main()
'''

    return {
        "status": "ok",
        "script_type": "scrape",
        "url": url,
        "targets_count": len(targets),
        "has_pagination": pagination is not None,
        "output_format": output_format,
        "script": script,
        "usage": "1. pip install playwright && playwright install\n2. 保存脚本为 scrape.py\n3. python scrape.py"
    }


def main(args):
    try:
        if args.input:
            data = json.loads(args.input)
        else:
            data = {}

        result = generate_scrape_script(data)

        if args.output and result.get("script"):
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(result["script"])
            result["output_file"] = args.output

        print(json.dumps(result, ensure_ascii=False, indent=2))

    except json.JSONDecodeError:
        print(json.dumps({"status": "error", "message": "输入不是有效的JSON"}, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="采集脚本生成器")
    parser.add_argument("--input", type=str, help="JSON格式输入")
    parser.add_argument("--output", type=str, help="输出文件路径（可选，保存为.py）")
    args = parser.parse_args()
    main(args)
