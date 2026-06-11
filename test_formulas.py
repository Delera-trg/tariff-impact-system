# -*- coding: utf-8 -*-
"""公式验证测试脚本"""

import sys
sys.path.insert(0, '.')

from modules.calculator import TariffCalculator

calc = TariffCalculator()

# 测试参数
t = 0.10       # 关税税率 10%
P_imp0 = 8000   # 税前进口价
P_wh0 = 10400   # 税前批发价
P_ret0 = 12800  # 税前零售价
alpha = 0.8     # 进口转批发传导系数
beta = 0.7      # 批发转零售传导系数
epsilon_d = -1.0  # 需求弹性 (<0)
epsilon_s = 2.0   # 供给弹性 (>0)
Q_d0 = 1000     # 税前需求量
Q_s0 = 800       # 税前供给量

result = calc._calculate_with_formulas(
    tariff_rate=t,
    P_imp0=P_imp0,
    P_wh0=P_wh0,
    P_ret0=P_ret0,
    alpha=alpha,
    beta=beta,
    epsilon_d=epsilon_d,
    epsilon_s=epsilon_s,
    Q_d0=Q_d0,
    Q_s0=Q_s0
)

print('=' * 60)
print('关税冲击测算验证报告')
print('=' * 60)
print('输入参数:')
print(f'  t={t}, P_imp0={P_imp0}, P_wh0={P_wh0}, P_ret0={P_ret0}')
print(f'  alpha={alpha}, beta={beta}, epsilon_d={epsilon_d}, epsilon_s={epsilon_s}')
print(f'  Q_d0={Q_d0}, Q_s0={Q_s0}')
print()

pc = result['price_changes']
qc = result['quantity_changes']
we = result['welfare_effects']
val = result['validation']

print('【价格传导】')
print(f'  P_imp1 = {pc["import"]["after"]:.2f}')
print(f'  P_wh1  = {pc["wholesale"]["after"]:.2f}')
print(f'  P_ret1 = {pc["retail"]["after"]:.2f}')
print(f'  ΔP_ret = {pc["retail"]["change"]:.2f}')
print()

print('【数量变化】')
print(f'  Q_d1 = {qc["demand"]["after"]:.2f}')
print(f'  Q_s1 = {qc["supply"]["after"]:.2f}')
print(f'  M1 = Q_d1 - Q_s1 = {qc["demand"]["after"]:.2f} - {qc["supply"]["after"]:.2f} = {qc["import"]["after"]:.2f}')
print()

print('【福利效应】')
print(f'  ΔCS = {we["consumer_surplus_change"]:,.2f}')
print(f'  ΔPS = {we["producer_surplus_change"]:,.2f}')
print(f'  GR  = {we["government_revenue"]:,.2f}')
print(f'  DWL = {we["deadweight_loss"]:,.2f}')
print()

print('【校验结果】')
print(f'  welfare_sum = {we["welfare_sum"]:.10f}')
print(f'  welfare_identity_valid: {val["welfare_identity_valid"]}')
print(f'  all_valid: {val["all_valid"]}')
print()

# 手动验证
delta_P_ret = pc['retail']['change']
Q_d1 = qc['demand']['after']
Q_s1 = qc['supply']['after']
M1 = qc['import']['after']

manual_CS = -0.5 * delta_P_ret * (Q_d0 + Q_d1)
manual_PS = 0.5 * delta_P_ret * (Q_s0 + Q_s1)
manual_GR = M1 * P_imp0 * t
manual_DWL = 0.5 * delta_P_ret * ((Q_d0 - Q_d1) + (Q_s1 - Q_s0))
manual_sum = manual_CS + manual_PS + manual_GR + manual_DWL

print('【手动验证】')
print(f'  手动ΔCS = {manual_CS:,.2f}')
print(f'  手动ΔPS = {manual_PS:,.2f}')
print(f'  手动GR  = {manual_GR:,.2f}')
print(f'  手动DWL = {manual_DWL:,.2f}')
print(f'  手动sum = {manual_sum:.10f}')
print(f'  误差 < 1e-6: {abs(manual_sum) < 1e-6}')

if val['all_valid']:
    print('\n✅ 所有校验通过!')
else:
    print('\n❌ 校验失败!')
