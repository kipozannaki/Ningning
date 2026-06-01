import matplotlib.pyplot as plt
import numpy as np

# 设置中文字体（Windows使用SimHei，macOS使用Arial Unicode MS，Linux使用WenQuanYi Zen Hei）
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'WenQuanYi Zen Hei']
plt.rcParams['axes.unicode_minus'] = False

# ====================== 数据定义（基于年报2018-2024） ======================
years = list(range(2018, 2025))

# 5. 员工结构
total_employees = [122, 131, 134, 144, 132, 130, 119]
tech_employees = [63, 69, 69, 77, 71, 71, 71]   # 技术人员数量
tech_ratio = [51.64, 52.67, 51.49, 53.47, 53.79, 54.62, 59.66]   # 技术人员占比（2023年报为58.46%，2024为59.66%）
# 修正2023年技术人员占比实际值为58.46%
tech_ratio[5] = 58.46

# 6. 控股股东李涛合计持股比例
lishi_holding = [45.01, 45.01, 45.01, 44.42, 41.59, 40.50, 41.44]   # %

# ====================== 创建1x2布局 ======================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
fig.suptitle('中科国信2018—2024年经营与治理情况', fontsize=18, fontweight='bold')

# 子图1：员工总数与技术人员占比（双轴图）
ax1.bar(years, total_employees, color='#2C3E50', alpha=0.7, label='员工总数（人）')
ax1.set_ylabel('员工总数（人）', color='#2C3E50')
ax1.tick_params(axis='y', labelcolor='#2C3E50')
ax1.legend(loc='upper left')
ax1_twin = ax1.twinx()
ax1_twin.plot(years, tech_ratio, color='#E67E22', marker='o', linewidth=2, label='技术人员占比（%）')
ax1_twin.set_ylabel('技术人员占比（%）', color='#E67E22')
ax1_twin.tick_params(axis='y', labelcolor='#E67E22')
ax1_twin.legend(loc='upper right')
ax1.set_title('员工规模与技术人才结构', fontsize=13)
ax1.grid(axis='x', linestyle='--', alpha=0.5)

# 子图2：控股股东持股比例（折线图）
ax2.plot(years, lishi_holding, color='#8E44AD', marker='d', linewidth=2, markersize=7)
ax2.set_ylabel('持股比例（%）', fontsize=11)
ax2.set_xlabel('年份')
ax2.set_title('实际控制人李涛合计持股比例变化', fontsize=13)
ax2.grid(True, linestyle='--', alpha=0.6)
ax2.set_ylim(38, 46)

plt.tight_layout(rect=[0, 0, 1, 0.95])   # 为总标题留出空间
plt.savefig('zhongkeguoxi_2018_2024_overview.png', dpi=300, bbox_inches='tight')
plt.show()

print("图表已保存为 'zhongkeguoxi_2018_2024_overview.png'")