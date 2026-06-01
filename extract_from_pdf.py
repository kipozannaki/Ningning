import pdfplumber
import pandas as pd
import re
import os

def parse_number(s):
    """从字符串解析数值"""
    if s is None:
        return None
    s = str(s).strip().replace(',', '').replace(' ', '')
    try:
        return float(s)
    except:
        return None

def find_bs_and_is(pdf_path):
    """从年报PDF中提取合并资产负债表和合并利润表的关键数据"""
    all_lines = []
    
    with pdfplumber.open(pdf_path) as f:
        for page in f.pages:
            txt = page.extract_text()
            if txt:
                for line in txt.split('\n'):
                    line = line.strip()
                    if line:
                        all_lines.append(line)
    
    full_text = '\n'.join(all_lines)
    
    # 找合并资产负债表
    bs_start = full_text.find('合并资产负债表')
    if bs_start < 0:
        bs_start = full_text.find('资产负债表')
    
    # 找合并利润表
    pl_start = full_text.find('合并利润表')
    if pl_start < 0:
        pl_start = full_text.find('利润表')
    
    result = {}
    
    # 提取资产负债表数据
    bs_section = full_text[bs_start:pl_start] if bs_start >= 0 and pl_start > bs_start else full_text
    
    # 要提取的项目及其在资产负债表中的行标识
    bs_items = {
        '应收账款': ['应收账款', '应收票据及应收账款'],
        '存货': ['存货'],
        '流动资产合计': ['流动资产合计'],
        '资产总计': ['资产总计'],
        '流动负债合计': ['流动负债合计'],
        '负债合计': ['负债合计'],
    }
    
    for key, keywords in bs_items.items():
        for kw in keywords:
            for line in bs_section.split('\n'):
                if kw in line and kw == line.split(' ')[0].strip() if len(line.split(' ')) > 1 else kw in line:
                    # 找到匹配行后，提取所有数字
                    nums = re.findall(r'[-−]?\s*[\d,]+\.?\d*', line)
                    if nums:
                        # 资产负债表通常有期末余额和期初余额两列
                        vals = [parse_number(n) for n in nums]
                        vals = [v for v in vals if v is not None and abs(v) > 100]  # 过滤太小的值
                        if len(vals) >= 2:
                            result[f'{key}_期末'] = vals[-2]  # 倒数第二个是期末
                            result[f'{key}_期初'] = vals[-1]  # 最后一个是期初
                        elif len(vals) == 1:
                            result[f'{key}_期末'] = vals[0]
                        break
            if f'{key}_期末' in result:
                break
    
    # 提取利润表数据
    if pl_start >= 0:
        pl_section = full_text[pl_start:]
    else:
        pl_section = full_text
    
    pl_items = {
        '营业收入': ['其中：营业收入', '营业收入'],
        '营业成本': ['其中：营业成本', '营业成本'],
        '净利润': ['净利润（净亏损', '净利润'],
        '归母净利润': ['归属于母公司所有者的净利润'],
    }
    
    for key, keywords in pl_items.items():
        for kw in keywords:
            for line in pl_section.split('\n'):
                if kw in line:
                    nums = re.findall(r'[-−]?\s*[\d,]+\.?\d+', line)
                    if nums:
                        vals = [parse_number(n) for n in nums]
                        vals = [v for v in vals if v is not None]
                        # 收入/成本的值通常较大(>1千万)，过滤掉附注编号等小数字
                        if key in ('营业收入', '营业成本'):
                            vals = [v for v in vals if abs(v) > 1e7]
                        if vals:
                            result[key] = vals[0]  # 取第一个符合条件的数字
                            break
            if key in result:
                break
    
    return result


# 处理所有年份
years = [2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]
all_results = {}

print("=" * 80)
print("开始提取各年年报数据（单位：元）")
print("=" * 80)

for year in years:
    path = f'年报/{year}.pdf'
    if not os.path.exists(path):
        print(f"\n{year}年：文件不存在，跳过")
        continue
    
    print(f"\n{'='*40}")
    print(f"  {year} 年年报")
    print(f"{'='*40}")
    
    data = find_bs_and_is(path)
    all_results[year] = data
    
    for k, v in data.items():
        print(f"  {k}: {v:,.0f}" if v else f"  {k}: 未找到")


# 构建DataFrame并计算指标
print("\n\n" + "=" * 80)
print("计算财务指标")
print("=" * 80)

rows = []
for year in years:
    if year == 2016:
        continue  # 2016仅用于计算2017的增长率，不输出
    d = all_results.get(year, {})
    
    # 需要的数据
    ta_end = d.get('资产总计_期末')  # 年末总资产
    ta_begin = d.get('资产总计_期初')  # 年初总资产
    tl_end = d.get('负债合计_期末')
    ca_end = d.get('流动资产合计_期末')
    cl_end = d.get('流动负债合计_期末')
    inv_end = d.get('存货_期末')
    inv_begin = d.get('存货_期初')
    ar_end = d.get('应收账款_期末')
    ar_begin = d.get('应收账款_期初')
    revenue = d.get('营业收入')
    cost = d.get('营业成本')
    net_profit = d.get('净利润')
    parent_np = d.get('归母净利润')
    
    # 计算各指标
    # 流动比率
    cur_ratio = ca_end / cl_end if ca_end and cl_end and cl_end != 0 else None
    
    # 速动比率 (需要存货数据)
    if ca_end and cl_end and inv_end and cl_end != 0:
        quick_ratio = (ca_end - inv_end) / cl_end
    else:
        quick_ratio = None
    
    # 资产负债率
    debt_ratio = tl_end / ta_end * 100 if tl_end and ta_end and ta_end != 0 else None
    
    # 应收账款周转率 (需要期初期末平均值)
    if revenue and ar_end is not None and ar_begin is not None:
        avg_ar = (ar_end + ar_begin) / 2
        ar_turnover = revenue / avg_ar if avg_ar and avg_ar != 0 else None
    else:
        ar_turnover = None
    
    # 存货周转率
    if cost and inv_end is not None and inv_begin is not None:
        avg_inv = (inv_end + inv_begin) / 2
        inv_turnover = cost / avg_inv if avg_inv and avg_inv != 0 else None
    else:
        inv_turnover = None
    
    # 毛利率
    gross_margin = (revenue - cost) / revenue * 100 if revenue and cost and revenue != 0 else None
    
    # 总资产收益率 (用平均总资产)
    if net_profit and ta_end and ta_begin:
        avg_ta = (ta_end + ta_begin) / 2
        roa = net_profit / avg_ta * 100 if avg_ta != 0 else None
    else:
        roa = None
    
    # 营业收入增长率 (需要上年营收)
    prev_rev = all_results.get(year - 1, {}).get('营业收入')
    if revenue and prev_rev and prev_rev != 0:
        rev_growth = (revenue - prev_rev) / prev_rev * 100
    else:
        rev_growth = None
    
    # 总资产增长率 (需要上年总资产)
    if year - 1 in all_results:
        prev_ta = all_results[year - 1].get('资产总计_期末')
    else:
        prev_ta = None
    if ta_end and prev_ta and prev_ta != 0:
        ta_growth = (ta_end - prev_ta) / prev_ta * 100
    else:
        ta_growth = None
    
    row = {
        '年份': year,
        '资产总计_期末(元)': ta_end,
        '负债合计_期末(元)': tl_end,
        '流动资产合计(元)': ca_end,
        '流动负债合计(元)': cl_end,
        '存货_期末(元)': inv_end,
        '存货_期初(元)': inv_begin,
        '应收账款_期末(元)': ar_end,
        '应收账款_期初(元)': ar_begin,
        '营业收入(元)': revenue,
        '营业成本(元)': cost,
        '净利润(元)': net_profit,
        '归母净利润(元)': parent_np,
        '流动比率': cur_ratio,
        '速动比率': quick_ratio,
        '资产负债率(%)': debt_ratio,
        '应收账款周转率(次)': ar_turnover,
        '存货周转率(次)': inv_turnover,
        '毛利率(%)': gross_margin,
        '总资产收益率(%)': roa,
        '营业收入增长率(%)': rev_growth,
        '总资产增长率(%)': ta_growth,
    }
    rows.append(row)
    
    print(f"\n{year}年:")
    print(f"  流动比率={cur_ratio:.4f}" if cur_ratio else "  流动比率=缺失", end='')
    print(f"  速动比率={quick_ratio:.4f}" if quick_ratio else "  速动比率=缺失", end='')
    print(f"  资产负债率={debt_ratio:.2f}%" if debt_ratio else "  资产负债率=缺失")
    print(f"  应收账款周转率={ar_turnover:.2f}次" if ar_turnover else "  应收账款周转率=缺失", end='')
    print(f"  存货周转率={inv_turnover:.2f}次" if inv_turnover else "  存货周转率=缺失")
    print(f"  毛利率={gross_margin:.2f}%" if gross_margin else "  毛利率=缺失", end='')
    print(f"  总资产收益率={roa:.2f}%" if roa else "  总资产收益率=缺失")
    print(f"  营业收入增长率={rev_growth:.2f}%" if rev_growth else "  营业收入增长率=缺失", end='')
    print(f"  总资产增长率={ta_growth:.2f}%" if ta_growth else "  总资产增长率=缺失")

# 保存
df = pd.DataFrame(rows)
df.to_excel('年报提取数据.xlsx', index=False)
print("\n\n数据已保存到 年报提取数据.xlsx")

# 输出摘要表
print("\n\n=== 指标汇总 ===")
summary = df[['年份', '流动比率', '速动比率', '资产负债率(%)', '应收账款周转率(次)', 
              '存货周转率(次)', '毛利率(%)', '总资产收益率(%)', '营业收入增长率(%)', '总资产增长率(%)']]
print(summary.round(4).to_string())
