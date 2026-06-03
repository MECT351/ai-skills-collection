#!/usr/bin/env python3
"""登录脚本生成器 — 根据需求生成Playwright登录自动化脚本"""

import sys
import json
import argparse


def generate_login_script(data):
    """生成登录脚本"""
    url = data.get("url", "")
    steps = data.get("steps", [])
    save_session = data.get("save_session", False)
    headless = data.get("headless", True)
    timeout = data.get("timeout", 30000)
    screenshot = data.get("screenshot", True)

    if not url:
        return {"status": "error", "message": "缺少url参数"}
    if not steps:
        return {"status": "error", "message": "缺少steps参数，请描述登录步骤"}

    # 生成步骤代码
    steps_code = []
    for i, step in enumerate(steps):
        step_num = i + 1
        steps_code.append(f'        # 步骤{step_num}: {step}')
        
        # 智能识别操作类型
        if "输入" in step or "填写" in step or "填入" in step:
            selector, value = _parse_input_step(step)
            steps_code.append(f'        await page.fill("{selector}", "{value}")')
        elif "点击" in step:
            selector = _parse_click_step(step)
            steps_code.append(f'        await page.click("{selector}")')
        elif "等待" in step:
            selector = _parse_wait_step(step)
            steps_code.append(f'        await page.wait_for_selector("{selector}", timeout={timeout})')
        else:
            # 通用步骤，添加注释让用户手动补充
            steps_code.append(f'        # TODO: 请手动实现此步骤')
            steps_code.append(f'        # await page.xxx(...)')

    # 会话保存代码
    session_code = ""
    if save_session:
        session_code = """
    # 保存登录会话
    await context.storage_state(path="auth_session.json")
    print("[OK] 登录会话已保存到 auth_session.json")"""

    # 截图代码
    screenshot_code = ""
    if screenshot:
        screenshot_code = """
    # 登录后截图验证
    await page.screenshot(path="login_result.png")
    print("[OK] 登录结果截图已保存到 login_result.png")"""

    script = f'''#!/usr/bin/env python3
"""自动登录脚本 - 由浏览器自动化脚本生成器生成"""

from playwright.sync_api import sync_playwright
import time


def main():
    with sync_playwright() as p:
        # 启动浏览器
        browser = p.chromium.launch(headless={'True' if headless else 'False'})
        context = browser.new_context(
            viewport={{"width": 1280, "height": 720}},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        try:
            # 打开登录页面
            print(f"[INFO] 正在打开 {{url}}")
            page.goto("{url}", timeout={timeout})
            page.wait_for_load_state("networkidle")

            # 执行登录步骤
{chr(10).join(steps_code)}

            # 等待登录完成
            page.wait_for_load_state("networkidle")
            time.sleep(2)
{session_code}
{screenshot_code}

            # 验证登录结果
            current_url = page.url
            print(f"[OK] 登录完成，当前页面: {{current_url}}")

        except Exception as e:
            print(f"[ERROR] 登录失败: {{e}}")
            await page.screenshot(path="login_error.png")
            raise

        finally:
            # 保持浏览器打开（调试时注释掉下行）
            browser.close()


if __name__ == "__main__":
    main()
'''

    return {
        "status": "ok",
        "script_type": "login",
        "url": url,
        "steps_count": len(steps),
        "script": script,
        "usage": "1. pip install playwright && playwright install\n2. 保存脚本为 login.py\n3. python login.py"
    }


def _parse_input_step(step):
    """解析输入步骤，提取选择器和值"""
    import re
    # 尝试匹配: 输入XXX到#selector / 输入"value"到selector
    match = re.search(r'输入[「"\'"]?(.+?)[」"\'"]?到\s*([#.][\w-]+|[\w-]+\[[\w=]+\])', step)
    if match:
        return match.group(2), match.group(1)
    # 尝试匹配: 在#selector输入value
    match = re.search(r'在\s*([#.][\w-]+|[\w-]+\[[\w=]+\])\s*输入[「"\'"]?(.+?)[」"\'"]?$', step)
    if match:
        return match.group(1), match.group(2)
    return "#input", "value"


def _parse_click_step(step):
    """解析点击步骤，提取选择器"""
    import re
    match = re.search(r'点击\s*(.+)', step)
    if match:
        target = match.group(1).strip()
        # 如果已经是CSS选择器
        if target.startswith('#') or target.startswith('.') or target.startswith('['):
            return target
        # 尝试转为button/text选择器
        return f'text="{target}"'
    return "button"


def _parse_wait_step(step):
    """解析等待步骤，提取选择器"""
    import re
    match = re.search(r'等待\s*(.+)', step)
    if match:
        target = match.group(1).strip()
        if target.startswith('#') or target.startswith('.'):
            return target
        return f'text="{target}"'
    return "body"


def main(args):
    try:
        if args.input:
            data = json.loads(args.input)
        else:
            data = {}

        result = generate_login_script(data)

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
    parser = argparse.ArgumentParser(description="登录脚本生成器")
    parser.add_argument("--input", type=str, help="JSON格式输入")
    parser.add_argument("--output", type=str, help="输出文件路径（可选，保存为.py）")
    args = parser.parse_args()
    main(args)
