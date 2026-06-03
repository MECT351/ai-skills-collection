#!/usr/bin/env python3
"""PDF关键词统计 — 提取文本后统计词频和关键信息"""

import sys
import json
import argparse
import re


def analyze_keywords(file_path=None, text=None, top_n=20, min_length=2):
    """统计关键词"""
    # 获取文本
    if file_path:
        from extract_all import extract_text_from_pdf
        result = extract_text_from_pdf(file_path)
        if result.get("status") != "ok":
            return result
        text = result.get("text", "")
        if not text:
            return {"status": "error", "message": "无法提取文本，可能是扫描件"}
    elif not text:
        return {"status": "error", "message": "缺少file或text参数"}

    # 分词（中文按字/词，英文按空格）
    # 简单策略：中文字符单独统计，英文按空格分词
    chinese_chars = re.findall(r'[\u4e00-\u9fff]+', text)
    english_words = re.findall(r'[a-zA-Z]+', text)

    # 中文双字词统计
    cn_bigrams = {}
    for segment in chinese_chars:
        for i in range(len(segment) - 1):
            bigram = segment[i:i+2]
            if len(bigram) >= min_length:
                cn_bigrams[bigram] = cn_bigrams.get(bigram, 0) + 1

    # 英文词频（转小写，过滤停用词）
    stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
                  'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
                  'would', 'could', 'should', 'may', 'might', 'can', 'shall',
                  'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from',
                  'as', 'into', 'through', 'during', 'before', 'after', 'and',
                  'but', 'or', 'not', 'no', 'nor', 'so', 'yet', 'both', 'either',
                  'neither', 'each', 'every', 'all', 'any', 'few', 'more', 'most',
                  'other', 'some', 'such', 'than', 'too', 'very', 'just', 'about'}

    en_freq = {}
    for word in english_words:
        w = word.lower()
        if len(w) >= min_length and w not in stop_words:
            en_freq[w] = en_freq.get(w, 0) + 1

    # 排序取top
    cn_top = sorted(cn_bigrams.items(), key=lambda x: -x[1])[:top_n]
    en_top = sorted(en_freq.items(), key=lambda x: -x[1])[:top_n]

    # 数字提取
    numbers = re.findall(r'\d+\.?\d*', text)
    number_freq = {}
    for n in numbers:
        number_freq[n] = number_freq.get(n, 0) + 1
    num_top = sorted(number_freq.items(), key=lambda x: -x[1])[:10]

    # 基础统计
    total_chars = len(text)
    total_cn_chars = sum(len(s) for s in chinese_chars)
    total_en_words = len(english_words)

    return {
        "status": "ok",
        "file": file_path,
        "stats": {
            "total_chars": total_chars,
            "chinese_chars": total_cn_chars,
            "english_words": total_en_words,
            "unique_cn_bigrams": len(cn_bigrams),
            "unique_en_words": len(en_freq)
        },
        "chinese_keywords": [{"word": w, "count": c} for w, c in cn_top],
        "english_keywords": [{"word": w, "count": c} for w, c in en_top],
        "frequent_numbers": [{"number": n, "count": c} for n, c in num_top]
    }


def main(args):
    try:
        if args.input:
            data = json.loads(args.input)
        else:
            data = {}

        file_path = data.get("file", None)
        text = data.get("text", None)
        top_n = data.get("top_n", 20)
        min_length = data.get("min_length", 2)

        result = analyze_keywords(file_path, text, top_n, min_length)

        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            result["output_file"] = args.output

        print(json.dumps(result, ensure_ascii=False, indent=2))

    except json.JSONDecodeError:
        print(json.dumps({"status": "error", "message": "输入不是有效的JSON"}, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PDF关键词统计")
    parser.add_argument("--input", type=str, help="JSON格式输入")
    parser.add_argument("--output", type=str, help="输出文件路径（可选）")
    args = parser.parse_args()
    main(args)
