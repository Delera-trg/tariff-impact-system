# -*- coding: utf-8 -*-
"""
计算引擎模块 - 关税冲击测算核心逻辑
整合数据库查询和Stata计算
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

    整合数据库查询和Stata计算，提供完整的关税传导分析功能
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

        整合数据库查询和Stata计算，返回完整的分析结果

        Args:
            industry_id: 行业ID
            hs_code: HS编码（与industry_id二选一）
            tariff_rate: 关税税率（0-1）
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

        # 合并自定义参数
        if custom_params:
            pass_through_1 = custom_params.get("pass_through_1",
                transmission_params.get("import_to_wholesale", {}).get("pass_through_rate", 0.8))
            pass_through_2 = custom_params.get("pass_through_2",
                transmission_params.get("wholesale_to_retail", {}).get("pass_through_rate", 0.7))
            elasticity = custom_params.get("elasticity", 1.0)
        else:
            pass_through_1 = transmission_params.get("import_to_wholesale", {}).get("pass_through_rate", 0.8)
            pass_through_2 = transmission_params.get("wholesale_to_retail", {}).get("pass_through_rate", 0.7)
            elasticity = transmission_params.get("import_to_wholesale", {}).get("elasticity", 1.0)

        # 4. 获取基准价格（应用价格调整系数）
        base_price = custom_params.get("base_price") if custom_params else industry["base_price"]
        price_factor = custom_params.get("price_factor") if custom_params else 1.0
        # 确保price_factor是数字类型
        try:
            price_factor = float(price_factor) if price_factor else 1.0
        except (ValueError, TypeError):
            price_factor = 1.0
        # 应用调整系数
        base_price = base_price * price_factor

        # 5. 调用计算（优先使用本地计算，Stata启动太慢）
        if self.use_stata and self.stata.is_available():
            # 使用Stata计算
            result = self.stata.calculate_tariff_impact(
                tariff_rate=tariff_rate,
                base_price=base_price,
                pass_through_1=pass_through_1,
                pass_through_2=pass_through_2,
                elasticity=elasticity
            )
        else:
            # 使用Python本地计算
            result = self._calculate_locally(
                tariff_rate=tariff_rate,
                base_price=base_price,
                pass_through_1=pass_through_1,
                pass_through_2=pass_through_2,
                elasticity=elasticity
            )

        if not result.get("success"):
            return result

        # 6. 整合结果
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
                "elasticity": elasticity
            },
            "price_changes": result.get("price_changes", {}),
            "welfare_effects": result.get("welfare_effects", {})
        }

    def _calculate_locally(
        self,
        tariff_rate: float,
        base_price: float,
        pass_through_1: float,
        pass_through_2: float,
        elasticity: float
    ) -> Dict[str, Any]:
        """
        本地计算（当Stata不可用时）

        使用Python进行关税传导计算
        """
        # 如果base_price为None，使用默认值
        if base_price is None or base_price == 0:
            base_price = 100.0  # 默认基准价格

        # 基准价格
        wholesale_before = base_price * 1.30
        retail_before = base_price * 1.60

        # 税后价格
        import_after = base_price * (1 + tariff_rate)
        wholesale_after = wholesale_before + (import_after - base_price) * pass_through_1
        retail_after = retail_before + (wholesale_after - wholesale_before) * pass_through_2

        # 福利效应
        quantity = 1000
        tariff_increase = import_after - base_price

        consumer_surplus = -tariff_increase * quantity * 0.5 * (1 + elasticity)
        government_revenue = tariff_increase * quantity
        producer_surplus = -tariff_increase * quantity * 0.3
        deadweight_loss = tariff_increase * quantity * tariff_rate * 0.5

        return {
            "success": True,
            "price_changes": {
                "import": {
                    "before": base_price,
                    "after": import_after,
                    "change": import_after - base_price,
                    "change_rate": tariff_rate * 100
                },
                "wholesale": {
                    "before": wholesale_before,
                    "after": wholesale_after,
                    "change": wholesale_after - wholesale_before,
                    "change_rate": (wholesale_after - wholesale_before) / wholesale_before * 100
                },
                "retail": {
                    "before": retail_before,
                    "after": retail_after,
                    "change": retail_after - retail_before,
                    "change_rate": (retail_after - retail_before) / retail_before * 100
                }
            },
            "welfare_effects": {
                "consumer_surplus_change": consumer_surplus,
                "producer_surplus_change": producer_surplus,
                "government_revenue": government_revenue,
                "deadweight_loss": deadweight_loss
            }
        }

    def calculate_welfare(
        self,
        tariff_rate: float,
        base_price: float,
        quantity: float = 1000,
        elasticity: float = 1.0
    ) -> Dict[str, Any]:
        """
        计算福利效应

        Args:
            tariff_rate: 关税税率 (0-1)
            base_price: 基准价格
            quantity: 需求量
            elasticity: 需求弹性

        Returns:
            dict: 福利效应分析结果
        """
        tariff_increase = base_price * tariff_rate

        # 消费者剩余变化 (简化计算)
        consumer_surplus_change = -tariff_increase * quantity * 0.5 * (1 + elasticity)

        # 政府关税收入
        government_revenue = tariff_increase * quantity

        # 生产者剩余变化
        producer_surplus_change = -tariff_increase * quantity * 0.3

        # 无谓损失
        deadweight_loss = tariff_increase * quantity * tariff_rate * 0.5

        # 总福利
        total_welfare_change = consumer_surplus_change + producer_surplus_change + government_revenue

        return {
            "tariff_rate": tariff_rate,
            "base_price": base_price,
            "quantity": quantity,
            "elasticity": elasticity,
            "consumer_surplus_change": consumer_surplus_change,
            "producer_surplus_change": producer_surplus_change,
            "government_revenue": government_revenue,
            "deadweight_loss": deadweight_loss,
            "total_welfare_change": total_welfare_change,
            "summary": {
                "消费者负担": -consumer_surplus_change,
                "政府收入": government_revenue,
                "社会净损失": deadweight_loss
            }
        }

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
        for rate in tariff_rates:
            result = self.calculate(
                hs_code=hs_code,
                industry_id=industry_id,
                tariff_rate=rate,
                custom_params=custom_params
            )

            if result.get("success"):
                results.append({
                    "tariff_rate": rate,
                    "tariff_rate_percent": rate * 100,
                    "import_price": result["price_changes"]["import"]["after"],
                    "wholesale_price": result["price_changes"]["wholesale"]["after"],
                    "retail_price": result["price_changes"]["retail"]["after"],
                    "retail_price_change_rate": result["price_changes"]["retail"]["change_rate"],
                    "consumer_burden": -result["welfare_effects"].get("consumer_surplus_change", 0),
                    "government_revenue": result["welfare_effects"].get("government_revenue", 0),
                    "deadweight_loss": result["welfare_effects"].get("deadweight_loss", 0)
                })

        return {
            "success": True,
            "industry": {
                "hs_code": industry["hs_code"],
                "name": industry["name"],
                "base_price": base_price
            },
            "analysis": results,
            "summary": {
                "max_retail_price": max(r["retail_price"] for r in results),
                "max_deadweight_loss": max(r["deadweight_loss"] for r in results),
                "optimal_rate": results[results.index(max(results, key=lambda x: x["government_revenue"]))]["tariff_rate"] if results else 0
            }
        }

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
                results.append({
                    "hs_code": result["industry"]["hs_code"],
                    "name": result["industry"]["name"],
                    "category": result["industry"]["category"],
                    "base_price": result["params"]["base_price"],
                    "retail_price_after": result["price_changes"]["retail"]["after"],
                    "retail_price_change_rate": result["price_changes"]["retail"]["change_rate"],
                    "consumer_burden": -result["welfare_effects"].get("consumer_surplus_change", 0),
                    "government_revenue": result["welfare_effects"].get("government_revenue", 0),
                    "deadweight_loss": result["welfare_effects"].get("deadweight_loss", 0)
                })

        # 按零售价变化率排序
        results.sort(key=lambda x: x["retail_price_change_rate"], reverse=True)

        return {
            "success": True,
            "tariff_rate": tariff_rate,
            "comparison": results,
            "summary": {
                "most_affected": results[0] if results else None,  # 影响最大
                "least_affected": results[-1] if results else None,  # 影响最小
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
        print(f"Retail Price: {result['price_changes']['retail']['after']}")
        print(f"Retail Change Rate: {result['price_changes']['retail']['change_rate']:.2f}%")

    # 测试2: 敏感性分析
    print("\n=== 测试2: 敏感性分析 ===")
    sa_result = calc.sensitivity_analysis(hs_code="0101.10", tariff_rates=[0, 0.1, 0.2, 0.3])
    print(f"Success: {sa_result.get('success')}")
    if sa_result.get("success"):
        for item in sa_result["analysis"]:
            print(f"税率 {item['tariff_rate_percent']:.0f}% -> 零售价: {item['retail_price']:.2f}, 变化: {item['retail_price_change_rate']:.2f}%")

    # 测试3: 行业对比
    print("\n=== 测试3: 行业对比 ===")
    comp_result = calc.industry_comparison(hs_codes=["0101.10", "1201.90", "8703.23"], tariff_rate=0.10)
    print(f"Success: {comp_result.get('success')}")
    if comp_result.get("success"):
        for item in comp_result["comparison"]:
            print(f"{item['name']}: 零售价变化 {item['retail_price_change_rate']:.2f}%")
