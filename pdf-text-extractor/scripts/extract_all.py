#!/usr/bin/env python3
"""PDF全文提取 — 纯标准库解析PDF文本流"""

import sys
import json
import argparse
import re
import zlib
import struct


def extract_text_from_pdf(file_path):
    """从PDF文件提取文本"""
    try:
        with open(file_path, 'rb') as f:
            data = f.read()
    except FileNotFoundError:
        return {"status": "error", "message": f"文件不存在：{file_path}"}
    except Exception as e:
        return {"status": "error", "message": f"读取文件失败：{str(e)}"}

    # 检查PDF头
    if not data.startswith(b'%PDF'):
        return {"status": "error", "message": "不是有效的PDF文件"}

    # 检查加密
    if b'/Encrypt' in data:
        return {"status": "error", "message": "PDF已加密，请先解密后再提取"}

    # 提取文本
    pages = extract_pages(data)

    if not pages:
        return {"status": "ok", "file": file_path, "page_count": 0, "text": "",
                "warning": "未提取到文本，可能是扫描件/图片PDF，需要OCR工具"}

    full_text = "\n\n".join(pages)
    return {
        "status": "ok",
        "file": file_path,
        "page_count": len(pages),
        "text": full_text,
        "char_count": len(full_text)
    }


def extract_pages(data):
    """提取每页的文本"""
    pages = []

    # 找到所有页面对象
    # 方法：找到所有流对象，解压后提取文本
    obj_pattern = re.compile(rb'(\d+ \d+ obj.*?endobj)', re.DOTALL)

    for match in obj_pattern.finditer(data):
        obj_data = match.group(1)

        # 检查是否包含文本流
        if b'BT' in obj_data and b'ET' in obj_data:
            text = extract_text_from_stream(obj_data)
            if text.strip():
                pages.append(text)
        else:
            # 尝试解压缩流
            stream_match = re.search(rb'stream\r?\n(.*?)\r?\nendstream', obj_data, re.DOTALL)
            if stream_match:
                stream_data = stream_match.group(1)
                try:
                    decompressed = zlib.decompress(stream_data)
                    if b'BT' in decompressed and b'ET' in decompressed:
                        text = extract_text_from_stream(decompressed)
                        if text.strip():
                            pages.append(text)
                except zlib.error:
                    pass

    return pages


def extract_text_from_stream(data):
    """从PDF流中提取文本"""
    text_parts = []

    # 匹配文本操作符
    # Tj - 显示字符串
    # TJ - 显示字符串数组
    # ' - 换行并显示字符串
    # " - 设置间距、换行并显示字符串

    # 提取 (text) Tj
    tj_pattern = re.compile(rb'\(([^)]*)\)\s*Tj')
    for match in tj_pattern.finditer(data):
        try:
            text = match.group(1).decode('latin-1', errors='replace')
            text_parts.append(text)
        except:
            pass

    # 提取 [(text) num (text)] TJ
    tj_array_pattern = re.compile(rb'\[(.*?)\]\s*TJ')
    for match in tj_array_pattern.finditer(data):
        array_content = match.group(1)
        # 提取数组中的字符串
        str_pattern = re.compile(rb'\(([^)]*)\)')
        for str_match in str_pattern.finditer(array_content):
            try:
                text = str_match.group(1).decode('latin-1', errors='replace')
                text_parts.append(text)
            except:
                pass

    # 提取十六进制字符串 <hex> Tj
    hex_pattern = re.compile(rb'<([0-9A-Fa-f]+)>\s*Tj')
    for match in hex_pattern.finditer(data):
        try:
            hex_str = match.group(1).decode('ascii')
            text = bytes.fromhex(hex_str).decode('latin-1', errors='replace')
            text_parts.append(text)
        except:
            pass

    # 检测换行操作符
    if b'Td' in data or b'TD' in data or b'T*' in data:
        # 简单处理：在文本间加空格
        result = " ".join(text_parts)
    else:
        result = "".join(text_parts)

    # 清理PDF转义
    result = re.sub(r'\\n', '\n', result)
    result = re.sub(r'\\r', '\r', result)
    result = re.sub(r'\\t', '\t', result)

    return result


def main(args):
    try:
        if args.input:
            data = json.loads(args.input)
        else:
            data = {}

        file_path = data.get("file", "")
        if not file_path:
            print(json.dumps({"status": "error", "message": "缺少file参数"}, ensure_ascii=False))
            return

        result = extract_text_from_pdf(file_path)

        if args.output and result.get("text"):
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(result["text"])
            result["output_file"] = args.output

        # 输出时截断过长文本
        if len(result.get("text", "")) > 5000:
            result["text_preview"] = result["text"][:2000] + "...(已截断，完整内容请保存到文件)"
            result.pop("text", None)

        print(json.dumps(result, ensure_ascii=False, indent=2))

    except json.JSONDecodeError:
        print(json.dumps({"status": "error", "message": "输入不是有效的JSON"}, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PDF全文提取")
    parser.add_argument("--input", type=str, help="JSON格式输入")
    parser.add_argument("--output", type=str, help="输出文本文件路径（可选）")
    args = parser.parse_args()
    main(args)
