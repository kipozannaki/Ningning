import pandas as pd
import numpy as np

# 原始列名到新变量名的映射（按指定顺序）
COL_MAP = {
    '流动比率': 'x11',
    '速动比率': 'x13',
    '利息保障倍数': 'x14',
    '资产负债率(%)': 'x12',
    '应收账款周转率(次)': 'x21',
    '存货周转率(次)': 'x22',
    '毛利率(%)': 'x31',
    '总资产收益率(%)': 'x32',
    '营业收入增长率(%)': 'x41',
    '总资产增长率(%)': 'x42',
}

# 新变量名对应的原始列名（用于反向查找）
ORIGINAL_NAMES = {v: k for k, v in COL_MAP.items()}


# ======================
# 1. 读取数据
# ======================
def read_data(file_path):
    df = pd.read_excel(file_path)
    df = df.rename(columns={df.columns[0]: '年份'})
    df.set_index('年份', inplace=True)

    # 清洗列名：去除空格、换行符等特殊字符
    df.columns = df.columns.str.strip().str.replace('\n', '').str.replace(' ', '')

    # 原始列名到新变量名的映射（处理可能的格式差异）
    COL_MAP_CLEAN = {
        '流动比率': 'x11',
        '速动比率': 'x13',
        '利息保障倍数': 'x14',
        '资产负债率(%)': 'x12',
        '应收账款周转率(次)': 'x21',
        '存货周转率(次)': 'x22',
        '毛利率(%)': 'x31',
        '总资产收益率(%)': 'x32',
        '营业收入增长率(%)': 'x41',
        '总资产增长率(%)': 'x42',
    }

    # 筛选需要的列并重命名、按指定顺序排列
    ordered_cols = list(COL_MAP_CLEAN.keys())
    df = df[ordered_cols].rename(columns=COL_MAP_CLEAN)
    return df


# ======================
# 2. 指标标准化（正向 / 负向）
# ======================
def normalize_data(df):
    positive = ['x11', 'x13', 'x14', 'x21', 'x22', 'x31', 'x32', 'x41', 'x42']
    negative = ['x12']

    target_order = ['x11', 'x13', 'x14', 'x12', 'x21', 'x22', 'x31', 'x32', 'x41', 'x42']

    norm_df = pd.DataFrame(index=df.index)

    for col in positive:
        min_val, max_val = df[col].min(), df[col].max()
        norm_df[col] = (df[col] - min_val) / (max_val - min_val)

    for col in negative:
        min_val, max_val = df[col].min(), df[col].max()
        norm_df[col] = (max_val - df[col]) / (max_val - min_val)

    return norm_df[target_order]


# ======================
# 3. 熵权法
# ======================
def entropy_weight(norm_df):
    eps = 1e-10
    P = (norm_df + eps).div((norm_df + eps).sum(axis=0), axis=1)

    k = 1 / np.log(len(norm_df))
    E = -k * (P * np.log(P)).sum(axis=0)
    D = 1 - E
    W = D / D.sum()

    return W


# ======================
# 4. TOPSIS
# ======================
def topsis(norm_df, weights):
    V = norm_df * weights

    ideal_best = V.max()
    ideal_worst = V.min()

    d_pos = np.sqrt(((V - ideal_best) ** 2).sum(axis=1))
    d_neg = np.sqrt(((V - ideal_worst) ** 2).sum(axis=1))

    score = d_neg / (d_pos + d_neg)

    result = pd.DataFrame({
        '相对贴近度': score,
        '排名': score.rank(ascending=False).astype(int)
    })

    return result, V


# ======================
# 5. 各维度综合得分
# ======================
# 维度定义：维度名 -> 包含的指标变量名
DIMENSIONS = {
    '偿债能力': ['x11', 'x13', 'x14', 'x12'],
    '营运能力': ['x21', 'x22'],
    '盈利能力': ['x31', 'x32'],
    '发展能力': ['x41', 'x42'],
}


def calc_dimension_scores(norm_df, weights):
    scores = {}
    for dim_name, indicators in DIMENSIONS.items():
        dim_weight_sum = sum(weights[c] for c in indicators)
        scores[dim_name] = (norm_df[indicators] * weights[indicators]).sum(axis=1) / dim_weight_sum
    return pd.DataFrame(scores)


# ======================
# 6. 主函数
# ======================
def main():
    df = read_data('年报提取数据.xlsx')
    df = df.loc[2019:2025]  # 仅保留2019-2025年数据
    norm_df = normalize_data(df)
    weights = entropy_weight(norm_df)
    topsis_result, weighted_matrix = topsis(norm_df, weights)
    dimension_scores = calc_dimension_scores(norm_df, weights)

    target_order = ['x11', 'x13', 'x14', 'x12', 'x21', 'x22', 'x31', 'x32', 'x41', 'x42']

    print("各指标权重分配：")
    print("=" * 48)
    for idx, name in enumerate(target_order, 1):
        original = ORIGINAL_NAMES[name]
        print(f"{idx}. {name} ({original}): {weights[name]:.4f}")
    print("=" * 48)
    print(f"权重合计: {weights.sum():.4f}")
    print()
    print("各维度权重合计：")
    print("=" * 40)
    for dim_name, indicators in DIMENSIONS.items():
        dim_w = sum(weights[c] for c in indicators)
        print(f"{dim_name}: {dim_w:.4f} ({dim_w*100:.2f}%)")
    print()
    print("各维度历年综合得分：")
    print("=" * 60)
    print(f"{'年份':<6}", end="")
    for dim in DIMENSIONS:
        print(f"{dim:<14}", end="")
    print()
    print("-" * 60)
    for year in dimension_scores.index:
        print(f"{year:<6}", end="")
        for dim in DIMENSIONS:
            print(f"{dimension_scores.loc[year, dim]:<14.4f}", end="")
        print()
    print()
    print("各年份TOPSIS评价结果：")
    print("=" * 40)
    for year, row in topsis_result.iterrows():
        print(f"{year}: 相对贴近度={row['相对贴近度']:.4f}, 排名={int(row['排名'])}")

    with pd.ExcelWriter('熵权法_TOPSIS_结果.xlsx', engine='openpyxl', mode='w') as writer:
        export_df = df.rename(columns=ORIGINAL_NAMES)
        export_df.to_excel(writer, sheet_name='原始数据')
        norm_df_export = norm_df.rename(columns=ORIGINAL_NAMES)
        norm_df_export.to_excel(writer, sheet_name='标准化数据')
        weights_export = pd.DataFrame(weights[target_order], columns=['权重'])
        weights_export.index = [ORIGINAL_NAMES[n] for n in target_order]
        weights_export.to_excel(writer, sheet_name='指标权重')
        topsis_result.to_excel(writer, sheet_name='TOPSIS结果')
        weighted_matrix_export = weighted_matrix[target_order].rename(columns=ORIGINAL_NAMES)
        weighted_matrix_export.to_excel(writer, sheet_name='加权矩阵')
        dimension_scores.to_excel(writer, sheet_name='各维度综合得分')


if __name__ == '__main__':
    main()
