import pdfplumber

PDF_PATH = r"c:\pycharm\pythonProject\NingningProject\年报\2018.pdf"
KEYWORDS = ["利润总额", "利息费用"]
MERGE_TABLE = "合并利润表"

def search_keywords_in_pdf(pdf_path, keywords):
    results = {kw: [] for kw in keywords}
    merge_table_pages = []

    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        print(f"PDF 总页数: {total_pages}\n")

        for page_num, page in enumerate(pdf.pages, start=1):
            text = page.extract_text()
            if text is None:
                continue

            # 检查是否包含"合并利润表"
            if MERGE_TABLE in text:
                merge_table_pages.append(page_num)
                print(f">>> 第 {page_num} 页发现「{MERGE_TABLE}」 <<<")

            # 逐行搜索关键词
            lines = text.split("\n")
            for line in lines:
                for kw in keywords:
                    if kw in line:
                        results[kw].append({
                            "page": page_num,
                            "text": line.strip()
                        })

    return results, merge_table_pages

def print_results(results, merge_table_pages):
    print("\n" + "=" * 80)
    print("搜索结果汇总")
    print("=" * 80)

    if merge_table_pages:
        print(f"\n「合并利润表」出现的页码: {merge_table_pages}")

    for kw, matches in results.items():
        print(f"\n--- 关键词「{kw}」共找到 {len(matches)} 处 ---")
        if not matches:
            print("  （未找到）")
            continue
        for match in matches:
            print(f"  第 {match['page']:>3} 页 | {match['text']}")

if __name__ == "__main__":
    results, merge_table_pages = search_keywords_in_pdf(PDF_PATH, KEYWORDS)
    print_results(results, merge_table_pages)
