import pdfplumber
import os
import re

PDF_DIR = r"c:\pycharm\pythonProject\NingningProject\年报"
YEARS = range(2019, 2026)

CATEGORIES = [
    {
        "name": "1. 流动负债/短期借款大幅变化说明",
        "keywords": ["流动负债", "短期借款"],
        "context_triggers": ["增加", "减少", "上升", "下降", "增长", "降低", "变动", "变化", "原因", "主要", "大幅", "所致"],
    },
    {
        "name": "2. 流动资产/应收账款/存货大幅变化原因",
        "keywords": ["流动资产", "应收账款", "存货"],
        "context_triggers": ["增加", "减少", "上升", "下降", "增长", "降低", "变动", "变化", "原因", "主要", "大幅", "所致"],
    },
    {
        "name": "3. 融资事件",
        "keywords": ["募集资金", "增发", "定向发行", "非公开发行", "可转债", "发行股票", "股票发行"],
        "context_triggers": [],
    },
    {
        "name": "4. 疫情/新冠对公司经营的影响",
        "keywords": ["疫情", "新冠"],
        "context_triggers": [],
    },
    {
        "name": "5. 营业收入大幅变动原因",
        "keywords": ["营业收入"],
        "context_triggers": ["增加", "减少", "上升", "下降", "增长", "降低", "变动", "变化", "原因", "主要", "同比", "大幅", "所致"],
    },
    {
        "name": "6. 回款/收款相关描述",
        "keywords": ["回款", "收款"],
        "context_triggers": [],
    },
]

SECTION_TITLES = [
    "管理层讨论与分析",
    "经营情况讨论与分析",
    "经营情况分析",
    "会计数据、经营情况和管理层分析",
    "管理层分析",
]


def find_section_content_start(pdf):
    """找到管理层讨论章节的正文起始页（跳过目录页）"""
    candidates = []
    for i, page in enumerate(pdf.pages):
        if i < 5:  # 跳过前5页（目录区域）
            continue
        text = page.extract_text()
        if not text:
            continue
        for title in SECTION_TITLES:
            if title in text and len(text) > 200:  # 确保是正文页而非目录页
                candidates.append((i, title))
    if candidates:
        return candidates[0][0]
    return None


def split_sentences(text):
    """按中文标点拆分句子，保留有意义的片段"""
    raw = re.split(r'(?<=[。；;！!？?\n])', text)
    result = []
    for s in raw:
        s = s.strip()
        if s and len(s) > 8:
            result.append(s)
    return result


def extract_sentences_around(text, keyword, max_sentences=3):
    """在文本中找到关键词，返回该关键词所在位置前后至多max_sentences句"""
    sentences = split_sentences(text)
    results = []

    for i, sent in enumerate(sentences):
        if keyword in sent:
            start = max(0, i - 1)
            end = min(len(sentences), i + 2)
            context_sents = sentences[start:end]
            combined = "".join(context_sents)
            if len(combined) > 500:
                combined = combined[:500] + "..."
            results.append(combined)
            if len(results) >= 3:
                break

    return results


def has_context_trigger(text, triggers):
    """检查文本中是否包含变化/原因触发词"""
    if not triggers:
        return True
    for t in triggers:
        if t in text:
            return True
    return False


def extract_text_range(pdf, start_page, page_count=80):
    """提取指定范围的页面文本"""
    parts = []
    end = min(start_page + page_count, len(pdf.pages))
    for i in range(start_page, end):
        t = pdf.pages[i].extract_text()
        if t:
            parts.append(t)
    return "\n".join(parts)


def extract_full_text(pdf):
    """提取全文"""
    parts = []
    for i in range(len(pdf.pages)):
        t = pdf.pages[i].extract_text()
        if t:
            parts.append(t)
    return "\n".join(parts)


def process_pdf(pdf_path, year):
    """处理单个PDF"""
    print(f"\n{'='*80}")
    print(f"  【{year} 年年报】")
    print(f"{'='*80}")

    try:
        with pdfplumber.open(pdf_path) as pdf:
            total = len(pdf.pages)
            print(f"  总页数: {total}")

            mgmt_start = find_section_content_start(pdf)
            if mgmt_start is not None:
                print(f"  管理层讨论章节正文起始页: 第{mgmt_start + 1}页")
            else:
                print(f"  未找到管理层讨论章节正文，从第6页开始搜索")
                mgmt_start = 5

            mgmt_text = extract_text_range(pdf, mgmt_start, 80)
            full_text = extract_full_text(pdf)

            for cat in CATEGORIES:
                print(f"\n  --- {cat['name']} ---")
                found = False

                for kw in cat["keywords"]:
                    for search_text, source_label in [(mgmt_text, ""), (full_text, "(全文)")]:
                        if kw not in search_text:
                            continue

                        contexts = extract_sentences_around(search_text, kw, max_sentences=3)
                        for ctx in contexts:
                            if cat["context_triggers"] and not has_context_trigger(ctx, cat["context_triggers"]):
                                continue
                            ctx_clean = ctx.replace("\n", " ").strip()
                            # 去重：如果和前一条很相似就跳过
                            print(f"    [{kw}]{source_label} {ctx_clean}")
                            found = True

                        if found and source_label == "":
                            break
                    if found and source_label == "":
                        break

                if not found:
                    print(f"    (未找到相关内容)")

            print()

    except Exception as e:
        print(f"  处理出错: {e}")


def main():
    for year in YEARS:
        pdf_path = os.path.join(PDF_DIR, f"{year}.pdf")
        if not os.path.exists(pdf_path):
            print(f"  {year}.pdf 不存在，跳过")
            continue
        process_pdf(pdf_path, year)

    print("\n" + "=" * 80)
    print("  全部处理完成！")
    print("=" * 80)


if __name__ == "__main__":
    main()
