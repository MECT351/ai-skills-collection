#!/usr/bin/env python3
"""导航脚本生成器 — 根据操作步骤生成Playwright页面导航脚本"""

import sys
import json
import argparse


def generate_navigate_script(data):
    """生成导航脚本"""
    url = data.get("url", "")
    steps = data.get("steps", [])
    headless = data.get("headless", False)
    timeout = data.get("timeout", 30000)
    slow_mo = data.get("slow_mo", 100)
    screenshot_each = data.get("screenshot_each", False)

    if not url:
        return {"status": "error", "message": "缺少url参数"}
    if not steps:
        return {"status": "error", "message": "缺少steps参数"}

    steps_code = []
    for i, step in enumerate(steps):
        step_num = i + 1
        steps_code.append(f'        # 步骤{step_num}: {step}')

        if "点击" in step:
            selector = _parse_element(step)
            steps_code.append(f'        page.click("{selector}")')
        elif "输入" in step or "填写" in step:
            selector, value = _parse_input(step)
            steps_code.append(f'        page.fill("{selector}", "{value}")')
        elif "等待" in step:
            if "秒" in step:
                import re
                sec = re.search(r'(\d+)秒', step)
                if sec:
                    steps_code.append(f'        time.sleep({sec.group(1)})')
                else:
                    steps_code.append(f'        time.sleep(2)')
            else:
                selector = _parse_element(step)
                steps_code.append(f'        page.wait_for_selector("{selector}", timeout={timeout})')
        elif "截图" in step:
            steps_code.append(f'        page.screenshot(path="step_{step_num}.png")')
            steps_code.append(f'        print(f"[OK] 步骤{step_num}截图已保存")')
        elif "滚动" in step:
            if "底部" in step or "最下面" in step:
                steps_code.append(f'        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")')
            else:
                steps_code.append(f'        page.evaluate("window.scrollBy(0, 500)")')
        elif "选择" in step or "下拉" in step:
            selector, value = _parse_select(step)
            steps_code.append(f'        page.select_option("{selector}", "{value}")')
        elif "键盘" in step or "回车" in step or "Enter" in step:
            if "回车" in step or "Enter" in step:
                steps_code.append(f'        page.keyboard.press("Enter")')
            else:
                steps_code.append(f'        # TODO: 请补充键盘操作')
        else:
            steps_code.append(f'        # TODO: 请手动实现此步骤')

        steps_code.append(f'        time.sleep(0.5)')

        if screenshot_each:
            steps_code.append(f'        page.screenshot(path="step_{step_num}_after.png")')

    script = f'''#!/usr/bin/env python3
"""页面导航脚本 - 由浏览器自动化脚本生成器生成"""

from playwright.sync_api import sync_playwright
import time


def main():
    with sync_playwright() as p:
        # 启动浏览器（导航脚本默认有头模式，方便观察）
        browser = p.chromium.launch(
            headless={'True' if headless else 'False'},
            slow_mo={slow_mo}
        )
        context = browser.new_context(
            viewport={{"width": 1280, "height": 720}},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = context.new_page()

        try:
            # 打开起始页面
            print(f"[INFO] 正在打开 {url}")
            page.goto("{url}", timeout={timeout})
            page.wait_for_load_state("networkidle")

            # 执行导航步骤
{chr(10).join(steps_code)}

            # 完成截图
            page.screenshot(path="navigate_result.png")
            print("[OK] 导航完成，结果截图已保存")

        except Exception as e:
            print(f"[ERROR] 导航失败: {{e}}")
            page.screenshot(path="navigate_error.png")

        finally:
            time.sleep(3)  # 保持3秒便于观察
            browser.close()


if __name__ == "__main__":
    main()
'''

    return {
        "status": "ok",
        "script_type": "navigate",
        "url": url,
        "steps_count": len(steps),
        "script": script,
        "usage": "1. pip install playwright && playwright install\n2. 保存脚本为 navigate.py\n3. python navigate.py"
    }


def _parse_element(step):
    """从步骤描述中提取元素选择器"""
    import re
    # CSS选择器
    match = re.search(r'([#.][\w-]+|[\w-]+\[[\w=]+\])', step)
    if match:
        return match.group(1)
    # 文本匹配
    match = re.search(r'[「"\'『](.+?)[」"\'』]', step)
    if match:
        return f'text="{match.group(1)}"'
    # 通用
    match = re.search(r'点击\s*(.+?)(?:的|的|链接|按钮|$)', step)
    if match:
        return f'text="{match.group(1).strip()}"'
    return "body"


def _parse_input(step):
    """解析输入步骤"""
    import re
    match = re.search(r'[「"\'『](.+?)[」"\'』].*?([#.][\w-]+)', step)
    if match:
        return match.group(2), match.group(1)
    match = re.search(r'([#.][\w-]+).*?[「"\'『](.+?)[」"\'』]', step)
    if match:
        return match.group(1), match.group(2)
    return "#input", "value"


def _parse_select(step):
    """解析选择步骤"""
    import re
    match = re.search(r'([#.][\w-]+).*?[「"\'『](.+?)[」"\'』]', step)
    if match:
        return match.group(1), match.group(2)
    return "select", "option"


def main(args):
    try:
        if args.input:
            data = json.loads(args.input)
        else:
            data = {}

        result = generate_navigate_script(data)

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
    parser = argparse.ArgumentParser(description="导航脚本生成器")
    parser.add_argument("--input", type=str, help="JSON格式输入")
    parser.add_argument("--output", type=str, help="输出文件路径（可选，保存为.py）")
    args = parser.parse_args()
    main(args)
