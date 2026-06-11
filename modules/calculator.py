# -*- coding: utf-8 -*-
"""
计算引擎模块 - 关税冲击测算核心逻辑
基于小国局部均衡关税模型（固定公式版本）

公式来源：用户提供的固定规则、公式与约束
"""

import os
import sys
from typing import Dict, List, Any, Optional

# 导入同级模块
from .database import DatabaseManager
from .stata_bridge import StataBridge


class TariffCalculator:
    """
    关税冲击计算引擎

    基于小国局部均衡关税模型，使用固定公式计算价格传导和福利效应
    """

    def __init__(self):
        """初始化计算引擎"""
        self.db = DatabaseManager()
        # 初始化Stata，超时设置为120秒
        self.stata = StataBridge(timeout=120)
        # 优先使用本地计算（Stata启动太慢）
        self.use_stata = False

    def calculate(
        self,
        industry_id: str = None,
        hs_code: str = None,
        tariff_rate: float = None,
        custom_params: Dict = None
    ) -> Dict[str, Any]:
        """
        计算关税冲击影响（主方法）

        使用固定公式计算关税传导效应

        Args:
            industry_id: 行业ID
            hs_code: HS编码（与industry_id二选一）
            tariff_rate: 关税税率（支持负值，兼容补贴场景）
            custom_params: 自定义参数（覆盖默认值）

        Returns:
            dict: 计算结果，包含行业信息、价格变化、福利效应等
        """
        # 1. 获取行业信息
        industry = self.db.get_industry_detail(hs_code=hs_code) if hs_code else \
                   self.db.get_industry_detail(industry_id=industry_id)

        if not industry:
            return {
                "success": False,
                "error": "行业不存在"
            }

        # 2. 获取或设置关税税率
        if tariff_rate is None:
            tariff_rate = industry.get("current_tariff_rate", 0.10)

        # 3. 获取传导参数
        transmission_params = industry.get("transmission_params", {})

        # 获取默认参数
        default_pt1 = transmission_params.get("import_to_wholesale", {}).get("pass_through_rate", 0.8)
        default_pt2 = transmission_params.get("wholesale_to_retail", {}).get("pass_through_rate", 0.7)
        default_ed = transmission_params.get("import_to_wholesale", {}).get("elasticity", 1.0)

        # 合并自定义参数
        if custom_params:
            pass_through_1 = custom_params.get("pass_through_1", default_pt1)
            pass_through_2 = custom_params.get("pass_through_2", default_pt2)
            elasticity_d = custom_params.get("elasticity", default_ed)  # 需求价格弹性 ε_d (<0)
            elasticity_s = custom_params.get("supply_elasticity", 2.0)  # 供给价格弹性 ε_s (>0)
        else:
            pass_through_1 = default_pt1
            pass_through_2 = default_pt2
            elasticity_d = default_ed
            elasticity_s = 2.0  # 默认供给弹性

        # 4. 获取基准价格（应用价格调整系数）
        industry_base_price = industry.get("base_price")
        if industry_base_price is None:
            industry_base_price = 8000.0  # 默认基准进口价

        # 从custom_params获取或使用行业默认值
        if custom_params and custom_params.get("base_price") is not None:
            base_price = custom_params.get("base_price")
        else:
            base_price = industry_base_price

        # 获取价格调整系数
        price_factor = 1.0
        if custom_params:
            pf = custom_params.get("price_factor")
            if pf is not None:
                try:
                    price_factor = float(pf)
                except (ValueError, TypeError):
                    price_factor = 1.0

        # 确保base_price是有效数值
        if base_price is None or not isinstance(base_price, (int, float)):
            base_price = 8000.0

        # 应用调整系数
        base_price = base_price * price_factor

        # 5. 计算基准价格链
        # 从数据库获取批发价和零售价
        wholesale_base = industry.get("wholesale_price")
        retail_base = industry.get("retail_price")

        if wholesale_base is None:
            wholesale_base = base_price * 1.30  # 默认
        if retail_base is None:
            retail_base = base_price * 1.60  # 默认

        # 应用价格调整系数
        wholesale_base = wholesale_base * price_factor
        retail_base = retail_base * price_factor

        # 6. 获取基准数量
        # 从custom_params或使用默认值
        if custom_params and custom_params.get("quantity_d0") is not None:
            quantity_d0 = custom_params.get("quantity_d0")
        else:
            quantity_d0 = 1000.0  # 默认基准需求量

        if custom_params and custom_params.get("quantity_s0") is not None:
            quantity_s0 = custom_params.get("quantity_s0")
        else:
            # 假设自给自足率，比如80%国内供给
            quantity_s0 = quantity_d0 * 0.8

        # 7. 使用固定公式计算
        # 注意：用户输入的是需求弹性的绝对值，公式要求负值，因此需要取负
        result = self._calculate_with_formulas(
            tariff_rate=tariff_rate,
            P_imp0=base_price,
            P_wh0=wholesale_base,
            P_ret0=retail_base,
            alpha=pass_through_1,  # 进口→批发传导系数
            beta=pass_through_2,   # 批发→零售传导系数
            epsilon_d=-abs(elasticity_d),  # 需求价格弹性 (<0)，取负值
            epsilon_s=abs(elasticity_s),  # 供给价格弹性 (>0)，取正值
            Q_d0=quantity_d0,
            Q_s0=quantity_s0
        )

        if not result.get("success"):
            return result

        # 8. 整合结果
        return {
            "success": True,
            "industry": {
                "hs_code": industry["hs_code"],
                "name": industry["name"],
                "category": industry["category"],
                "unit": industry["unit"]
            },
            "params": {
                "tariff_rate": tariff_rate,
                "base_price": base_price,
                "price_factor": price_factor,
                "pass_through_1": pass_through_1,
                "pass_through_2": pass_through_2,
                "elasticity": elasticity_d,
                "supply_elasticity": elasticity_s,
                "quantity_d0": quantity_d0,
                "quantity_s0": quantity_s0
            },
            "price_changes": result.get("price_changes", {}),
            "quantity_changes": result.get("quantity_changes", {}),
            "welfare_effects": result.get("welfare_effects", {}),
            "validation": result.get("validation", {})
        }

    def _calculate_with_formulas(
        self,
        tariff_rate: float,
        P_imp0: float,
        P_wh0: float,
        P_ret0: float,
        alpha: float,
        beta: float,
        epsilon_d: float,
        epsilon_s: float,
        Q_d0: float,
        Q_s0: float
    ) -> Dict[str, Any]:
        """
        使用固定公式计算关税影响

        基于用户提供的固定公式：
        （一）基础模型前提
        - 小国假设：本国为世界价格接受者，关税不改变国际进口价
        - 单一商品局部均衡，无跨市场一般均衡反馈
        - 线性供需曲线，使用点价格弹性计算数量变动

        （二）参数合法性约束
        0 ≤ α ≤ 1, 0 ≤ β ≤ 1
        """
        # ========== 参数校验 ==========
        # 确保传导系数在[0,1]范围内
        alpha = max(0.0, min(1.0, alpha))
        beta = max(0.0, min(1.0, beta))

        # ========== （三）价格传导计算链 ==========

        # 税后进口价: P_imp1 = P_imp0 * (1 + t)
        P_imp1 = P_imp0 * (1 + tariff_rate)

        # 税后批发价: P_wh1 = P_wh0 + (P_imp1 - P_imp0) * α
        P_wh1 = P_wh0 + (P_imp1 - P_imp0) * alpha

        # 税后零售价: P_ret1 = P_ret0 + (P_wh1 - P_wh0) * β
        P_ret1 = P_ret0 + (P_wh1 - P_wh0) * beta

        # 零售价格变动幅度: ΔP_ret = P_ret1 - P_ret0
        delta_P_ret = P_ret1 - P_ret0

        # ========== （四）供需数量 & 进口量计算 ==========

        # 税后需求量: Q_d1 = Q_d0 * (1 + ε_d * ΔP_ret / P_ret0)
        if P_ret0 != 0:
            Q_d1 = Q_d0 * (1 + epsilon_d * (delta_P_ret / P_ret0))
        else:
            Q_d1 = Q_d0

        # 税后供给量: Q_s1 = Q_s0 * (1 + ε_s * ΔP_ret / P_ret0)
        if P_ret0 != 0:
            Q_s1 = Q_s0 * (1 + epsilon_s * (delta_P_ret / P_ret0))
        else:
            Q_s1 = Q_s0

        # 进口量恒等关系: M = Q_d - Q_s
        M0 = Q_d0 - Q_s0  # 税前进口量
        M1 = Q_d1 - Q_s1  # 税后进口量

        # ========== （五）福利效应计算 ==========

        # 消费者剩余变化: ΔCS = -0.5 * ΔP_ret * (Q_d0 + Q_d1)
        delta_CS = -0.5 * delta_P_ret * (Q_d0 + Q_d1)

        # 约束检验: sign(ΔCS) = -sign(ΔP_ret)
        if delta_P_ret != 0:
            expected_sign_CS = -1 if delta_P_ret > 0 else 1
            actual_sign_CS = 1 if delta_CS > 0 else -1
            cs_sign_valid = (expected_sign_CS == actual_sign_CS)
        else:
            cs_sign_valid = True

        # 生产者剩余变化: ΔPS = 0.5 * ΔP_ret * (Q_s0 + Q_s1)
        delta_PS = 0.5 * delta_P_ret * (Q_s0 + Q_s1)

        # 约束检验: sign(ΔPS) = sign(ΔP_ret)
        if delta_P_ret != 0:
            expected_sign_PS = 1 if delta_P_ret > 0 else -1
            actual_sign_PS = 1 if delta_PS > 0 else -1
            ps_sign_valid = (expected_sign_PS == actual_sign_PS)
        else:
            ps_sign_valid = True

        # 政府关税收入（从价税，税基 = 税前进口价）: GR = M1 * P_imp0 * t
        GR = M1 * P_imp0 * tariff_rate

        # 约束检验: GR符号与税率t一致
        if tariff_rate != 0:
            expected_sign_GR = 1 if tariff_rate > 0 else -1
            actual_sign_GR = 1 if GR > 0 else -1
            gr_sign_valid = (expected_sign_GR == actual_sign_GR)
        else:
            gr_sign_valid = True

        # 社会无谓损失（消费扭曲 + 生产扭曲）:
        # DWL = 0.5 * ΔP_ret * [(Q_d0 - Q_d1) + (Q_s1 - Q_s0)]
        DWL = 0.5 * delta_P_ret * ((Q_d0 - Q_d1) + (Q_s1 - Q_s0))

        # ========== （六）全局校验规则 ==========

        # 核心福利恒等式: ΔCS + ΔPS + GR + DWL = 0
        welfare_sum = delta_CS + delta_PS + GR + DWL
        welfare_identity_valid = abs(welfare_sum) < 1e-6

        # 构建价格变化结果
        price_changes = {
            "import": {
                "before": P_imp0,
                "after": P_imp1,
                "change": P_imp1 - P_imp0,
                "change_rate": ((P_imp1 - P_imp0) / P_imp0 * 100) if P_imp0 != 0 else 0
            },
            "wholesale": {
                "before": P_wh0,
                "after": P_wh1,
                "change": P_wh1 - P_wh0,
                "change_rate": ((P_wh1 - P_wh0) / P_wh0 * 100) if P_wh0 != 0 else 0
            },
            "retail": {
                "before": P_ret0,
                "after": P_ret1,
                "change": delta_P_ret,
                "change_rate": ((P_ret1 - P_ret0) / P_ret0 * 100) if P_ret0 != 0 else 0
            }
        }

        # 构建数量变化结果
        quantity_changes = {
            "demand": {
                "before": Q_d0,
                "after": Q_d1,
                "change": Q_d1 - Q_d0,
                "change_rate": ((Q_d1 - Q_d0) / Q_d0 * 100) if Q_d0 != 0 else 0
            },
            "supply": {
                "before": Q_s0,
                "after": Q_s1,
                "change": Q_s1 - Q_s0,
                "change_rate": ((Q_s1 - Q_s0) / Q_s0 * 100) if Q_s0 != 0 else 0
            },
            "import": {
                "before": M0,
                "after": M1,
                "change": M1 - M0
            }
        }

        # 构建福利效应结果
        welfare_effects = {
            "consumer_surplus_change": delta_CS,
            "producer_surplus_change": delta_PS,
            "government_revenue": GR,
            "deadweight_loss": DWL,
            "welfare_sum": welfare_sum
        }

        # 构建校验结果
        validation = {
            "welfare_identity": welfare_sum,
            "welfare_identity_valid": welfare_identity_valid,
            "cs_sign_valid": cs_sign_valid,
            "ps_sign_valid": ps_sign_valid,
            "gr_sign_valid": gr_sign_valid,
            "all_valid": welfare_identity_valid and cs_sign_valid and ps_sign_valid and gr_sign_valid
        }

        return {
            "success": True,
            "price_changes": price_changes,
            "quantity_changes": quantity_changes,
            "welfare_effects": welfare_effects,
            "validation": validation
        }

    def calculate_welfare(
        self,
        tariff_rate: float,
        base_price: float,
        quantity: float = 1000,
        elasticity: float = 1.0
    ) -> Dict[str, Any]:
        """
        计算福利效应（兼容旧接口）

        Args:
            tariff_rate: 关税税率 (0-1)
            base_price: 基准价格
            quantity: 需求量
            elasticity: 需求弹性

        Returns:
            dict: 福利效应分析结果
        """
        result = self._calculate_with_formulas(
            tariff_rate=tariff_rate,
            P_imp0=base_price,
            P_wh0=base_price * 1.30,
            P_ret0=base_price * 1.60,
            alpha=0.8,
            beta=0.7,
            epsilon_d=-elasticity,
            epsilon_s=2.0,
            Q_d0=quantity,
            Q_s0=quantity * 0.8
        )

        if result.get("success"):
            welfare = result["welfare_effects"]
            return {
                "tariff_rate": tariff_rate,
                "base_price": base_price,
                "quantity": quantity,
                "elasticity": elasticity,
                "consumer_surplus_change": welfare["consumer_surplus_change"],
                "producer_surplus_change": welfare["producer_surplus_change"],
                "government_revenue": welfare["government_revenue"],
                "deadweight_loss": welfare["deadweight_loss"],
                "total_welfare_change": welfare["consumer_surplus_change"] + welfare["producer_surplus_change"] + welfare["government_revenue"] + welfare["deadweight_loss"],
                "validation": result["validation"],
                "summary": {
                    "消费者负担": -welfare["consumer_surplus_change"],
                    "政府收入": welfare["government_revenue"],
                    "社会净损失": welfare["deadweight_loss"]
                }
            }
        return {"success": False, "error": "计算失败"}

    def sensitivity_analysis(
        self,
        hs_code: str = None,
        industry_id: int = None,
        tariff_rates: List[float] = None,
        custom_params: Dict = None
    ) -> Dict[str, Any]:
        """
        敏感性分析

        分析不同关税税率下的价格变化

        Args:
            hs_code: HS编码
            industry_id: 行业ID
            tariff_rates: 税率列表，默认 [0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30]
            custom_params: 自定义参数

        Returns:
            dict: 敏感性分析结果
        """
        # 默认税率序列
        if tariff_rates is None:
            tariff_rates = [0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50]

        # 获取行业基准信息
        if hs_code:
            industry = self.db.get_industry_detail(hs_code=hs_code)
        elif industry_id:
            industry = self.db.get_industry_detail(industry_id=industry_id)
        else:
            return {"success": False, "error": "需要提供hs_code或industry_id"}

        if not industry:
            return {"success": False, "error": "行业不存在"}

        base_price = custom_params.get("base_price") if custom_params else industry["base_price"]

        # 对每个税率进行计算
        results = []
        validation_results = []

        for rate in tariff_rates:
            result = self.calculate(
                hs_code=hs_code,
                industry_id=industry_id,
                tariff_rate=rate,
                custom_params=custom_params
            )

            if result.get("success"):
                pc = result["price_changes"]
                we = result["welfare_effects"]
                val = result["validation"]

                results.append({
                    "tariff_rate": rate,
                    "tariff_rate_percent": rate * 100,
                    "import_price": pc["import"]["after"],
                    "wholesale_price": pc["wholesale"]["after"],
                    "retail_price": pc["retail"]["after"],
                    "retail_price_change": pc["retail"]["change"],
                    "retail_price_change_rate": pc["retail"]["change_rate"],
                    "demand_quantity": result["quantity_changes"]["demand"]["after"],
                    "supply_quantity": result["quantity_changes"]["supply"]["after"],
                    "import_quantity": result["quantity_changes"]["import"]["after"],
                    "consumer_surplus_change": we["consumer_surplus_change"],
                    "producer_surplus_change": we["producer_surplus_change"],
                    "government_revenue": we["government_revenue"],
                    "deadweight_loss": we["deadweight_loss"],
                    "welfare_sum": we["welfare_sum"]
                })

                # 记录校验结果
                validation_results.append({
                    "tariff_rate": rate,
                    "welfare_identity_valid": val["welfare_identity_valid"],
                    "all_valid": val["all_valid"]
                })

        # 汇总分析
        if results:
            max_retail_idx = max(range(len(results)), key=lambda i: results[i]["retail_price"])
            max_dwl_idx = max(range(len(results)), key=lambda i: results[i]["deadweight_loss"])
            max_gr_idx = max(range(len(results)), key=lambda i: results[i]["government_revenue"])

            return {
                "success": True,
                "industry": {
                    "hs_code": industry["hs_code"],
                    "name": industry["name"],
                    "base_price": base_price
                },
                "analysis": results,
                "validation_summary": validation_results,
                "summary": {
                    "max_retail_price": results[max_retail_idx]["retail_price"],
                    "max_retail_price_rate": results[max_retail_idx]["tariff_rate_percent"],
                    "max_deadweight_loss": results[max_dwl_idx]["deadweight_loss"],
                    "max_deadweight_loss_rate": results[max_dwl_idx]["tariff_rate_percent"],
                    "optimal_rate_for_revenue": results[max_gr_idx]["tariff_rate_percent"],
                    "max_government_revenue": results[max_gr_idx]["government_revenue"],
                    "all_validations_passed": all(v["all_valid"] for v in validation_results)
                }
            }

        return {"success": False, "error": "计算失败"}

    def industry_comparison(
        self,
        hs_codes: List[str],
        tariff_rate: float = 0.10,
        custom_params: Dict = None
    ) -> Dict[str, Any]:
        """
        多行业对比分析

        对比不同行业在相同关税税率下的传导效应

        Args:
            hs_codes: HS编码列表
            tariff_rate: 关税税率
            custom_params: 自定义参数

        Returns:
            dict: 行业对比结果
        """
        results = []

        for hs_code in hs_codes:
            result = self.calculate(
                hs_code=hs_code,
                tariff_rate=tariff_rate,
                custom_params=custom_params
            )

            if result.get("success"):
                pc = result["price_changes"]
                we = result["welfare_effects"]

                results.append({
                    "hs_code": result["industry"]["hs_code"],
                    "name": result["industry"]["name"],
                    "category": result["industry"]["category"],
                    "base_price": result["params"]["base_price"],
                    "retail_price_before": pc["retail"]["before"],
                    "retail_price_after": pc["retail"]["after"],
                    "retail_price_change_rate": pc["retail"]["change_rate"],
                    "consumer_surplus_change": we["consumer_surplus_change"],
                    "producer_surplus_change": we["producer_surplus_change"],
                    "government_revenue": we["government_revenue"],
                    "deadweight_loss": we["deadweight_loss"]
                })

        # 按零售价变化率排序
        results.sort(key=lambda x: x["retail_price_change_rate"], reverse=True)

        return {
            "success": True,
            "tariff_rate": tariff_rate,
            "comparison": results,
            "summary": {
                "most_affected": results[0] if results else None,
                "least_affected": results[-1] if results else None,
                "total_government_revenue": sum(r["government_revenue"] for r in results),
                "total_deadweight_loss": sum(r["deadweight_loss"] for r in results)
            }
        }

    def get_supported_industries(self, category: str = None) -> List[Dict]:
        """
        获取支持计算的行业列表

        Args:
            category: 分类筛选

        Returns:
            list: 行业列表
        """
        return self.db.get_industry_list(category=category)


# 测试代码
if __name__ == "__main__":
    calc = TariffCalculator()

    # 测试1: 基本计算
    print("=== 测试1: 基本计算 ===")
    result = calc.calculate(hs_code="0101.10", tariff_rate=0.10)
    print(f"Success: {result.get('success')}")
    if result.get("success"):
        pc = result['price_changes']
        we = result['welfare_effects']
        val = result['validation']
        print(f"Retail Price: {pc['retail']['before']} -> {pc['retail']['after']}")
        print(f"Retail Change Rate: {pc['retail']['change_rate']:.2f}%")
        print(f"Consumer Surplus Change: {we['consumer_surplus_change']:,.2f}")
        print(f"Producer Surplus Change: {we['producer_surplus_change']:,.2f}")
        print(f"Government Revenue: {we['government_revenue']:,.2f}")
        print(f"Deadweight Loss: {we['deadweight_loss']:,.2f}")
        print(f"Welfare Sum (should be ~0): {we['welfare_sum']:.10f}")
        print(f"Welfare Identity Valid: {val['welfare_identity_valid']}")
        print(f"All Validations Passed: {val['all_valid']}")

    # 测试2: 敏感性分析
    print("\n=== 测试2: 敏感性分析 ===")
    sa_result = calc.sensitivity_analysis(hs_code="0101.10", tariff_rates=[0, 0.1, 0.2, 0.3])
    print(f"Success: {sa_result.get('success')}")
    if sa_result.get("success"):
        for item in sa_result["analysis"]:
            print(f"税率 {item['tariff_rate_percent']:.0f}% -> 零售价: {item['retail_price']:.2f}, "
                  f"变化: {item['retail_price_change_rate']:.2f}%, "
                  f"DWL: {item['deadweight_loss']:.2f}")
        print(f"All Validations Passed: {sa_result['summary']['all_validations_passed']}")

    # 测试3: 行业对比
    print("\n=== 测试3: 行业对比 ===")
    comp_result = calc.industry_comparison(hs_codes=["0101.10", "1201.90", "8703.23"], tariff_rate=0.10)
    print(f"Success: {comp_result.get('success')}")
    if comp_result.get("success"):
        for item in comp_result["comparison"]:
            print(f"{item['name']}: 零售价变化 {item['retail_price_change_rate']:.2f}%")
