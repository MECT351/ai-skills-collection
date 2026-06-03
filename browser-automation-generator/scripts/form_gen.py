#!/usr/bin/env python3
"""表单脚本生成器 — 根据字段定义生成Playwright自动填表脚本"""

import sys
import json
import argparse


def generate_form_script(data):
    """生成表单填写脚本"""
    url = data.get("url", "")
    fields = data.get("fields", [])
    submit_selector = data.get("submit_selector", "button[type=submit]")
    headless = data.get("headless", False)
    timeout = data.get("timeout", 30000)
    submit = data.get("submit", True)
    verify_text = data.get("verify_text", "")

    if not url:
        return {"status": "error", "message": "缺少url参数"}
    if not fields:
        return {"status": "error", "message": "缺少fields参数"}

    # 生成字段填写代码
    fields_code = []
    for i, field in enumerate(fields):
        name = field.get("name", f"字段{i+1}")
        selector = field.get("selector", f"#field{i+1}")
        value = field.get("value", "")
        field_type = field.get("type", "text")

        fields_code.append(f'        # 填写: {name}')

        if field_type == "select" or field_type == "dropdown":
            fields_code.append(f'        page.select_option("{selector}", "{value}")')
        elif field_type == "checkbox" or field_type == "check":
            fields_code.append(f'        page.check("{selector}")')
        elif field_type == "radio":
            fields_code.append(f'        page.click("{selector}")')
        elif field_type == "file" or field_type == "upload":
            fields_code.append(f'        page.set_input_files("{selector}", "{value}")')
        elif field_type == "textarea":
            fields_code.append(f'        page.fill("{selector}", "{value}")')
        else:
            fields_code.append(f'        page.fill("{selector}", "{value}")')

        fields_code.append(f'        time.sleep(0.3)')

    # 提交代码
    submit_code = ""
    if submit:
        submit_code = f'''
        # 提交表单
        print("[INFO] 正在提交表单...")
        page.click("{submit_selector}")
        page.wait_for_load_state("networkidle")
        time.sleep(2)'''

    # 验证代码
    verify_code = ""
    if verify_text:
        verify_code = f'''
        # 验证提交结果
        page_content = page.content()
        if "{verify_text}" in page_content:
            print("[OK] 表单提交成功，验证文本已找到")
        else:
            print("[WARN] 表单提交后未找到验证文本，请手动检查")'''

    script = f'''#!/usr/bin/env python3
"""自动填表脚本 - 由浏览器自动化脚本生成器生成"""

from playwright.sync_api import sync_playwright
import time


def main():
    with sync_playwright() as p:
        # 启动浏览器
        browser = p.chromium.launch(headless={'True' if headless else 'False'}, slow_mo=200)
        context = browser.new_context(
            viewport={{"width": 1280, "height": 720}},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = context.new_page()

        try:
            # 打开表单页面
            print(f"[INFO] 正在打开 {url}")
            page.goto("{url}", timeout={timeout})
            page.wait_for_load_state("networkidle")

            # 填写表单字段
{chr(10).join(fields_code)}
{submit_code}
{verify_code}

            # 截图保存
            page.screenshot(path="form_result.png")
            print("[OK] 表单填写完成，截图已保存")

        except Exception as e:
            print(f"[ERROR] 表单操作失败: {{e}}")
            page.screenshot(path="form_error.png")

        finally:
            time.sleep(3)
            browser.close()


if __name__ == "__main__":
    main()
'''

    return {
        "status": "ok",
        "script_type": "form",
        "url": url,
        "fields_count": len(fields),
        "script": script,
        "usage": "1. pip install playwright && playwright install\n2. 保存脚本为 form.py\n3. python form.py"
    }


def main(args):
    try:
        if args.input:
            data = json.loads(args.input)
        else:
            data = {}

        result = generate_form_script(data)

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
    parser = argparse.ArgumentParser(description="表单脚本生成器")
    parser.add_argument("--input", type=str, help="JSON格式输入")
    parser.add_argument("--output", type=str, help="输出文件路径（可选，保存为.py）")
    args = parser.parse_args()
    main(args)
