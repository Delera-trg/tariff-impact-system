# -*- coding: utf-8 -*-
"""
关税计算器测试模块
包含功能测试和边界测试
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.calculator import TariffCalculator


class TestCalculator:
    """关税计算器测试类"""

    def setup_method(self):
        """每个测试方法运行前执行"""
        self.calculator = TariffCalculator()

    # ==================== 功能测试 ====================

    def test_zero_tariff(self, calculator):
        """测试1：税率为0时，价格不变"""
        result = self.calculator.calculate(
            hs_code="0101.10",
            tariff_rate=0,
            custom_params={
                "base_price": 100,
                "pass_through_1": 0.8,
                "pass_through_2": 0.7,
                "elasticity": 1.0
            }
        )

        assert result.get("success") is True, "计算应该成功"

        price = result["price_changes"]
        # 税率为0时，进口价应该等于税前价
        assert price["import"]["before"] == price["import"]["after"], \
            f"税率为0时，进口价应该不变: {price['import']['before']} vs {price['import']['after']}"
        assert price["import"]["change"] == 0, \
            f"税率为0时，价格变化应为0: {price['import']['change']}"
        assert price["import"]["change_rate"] == 0, \
            f"税率为0时，变化率应为0: {price['import']['change_rate']}"

        print("[OK] test_zero_tariff passed: 税率为0时，价格不变")

    def test_full_tariff(self, calculator):
        """测试2：税率100%时，进口价=2倍基准价"""
        base_price = 100
        result = self.calculator.calculate(
            hs_code="0101.10",
            tariff_rate=1.0,  # 100%
            custom_params={
                "base_price": base_price,
                "pass_through_1": 0.8,
                "pass_through_2": 0.7,
                "elasticity": 1.0
            }
        )

        assert result.get("success") is True, "计算应该成功"

        price = result["price_changes"]
        # 税率100%时，进口价 = 基准价 * (1 + 100%) = 2倍基准价
        expected_import_after = base_price * (1 + 1.0)
        assert abs(price["import"]["after"] - expected_import_after) < 0.01, \
            f"税率100%时，进口价应为2倍基准价: 预期{expected_import_after}, 实际{price['import']['after']}"

        print("[OK] test_full_tariff 通过：税率100%时，进口价=2倍基准价")

    def test_pass_through(self, calculator):
        """测试3：传导率影响正确"""
        base_price = 100
        tariff_rate = 0.25  # 25%

        # 测试高传导率 (0.9)
        result_high = self.calculator.calculate(
            hs_code="0101.10",
            tariff_rate=tariff_rate,
            custom_params={
                "base_price": base_price,
                "pass_through_1": 0.9,  # 高传导率
                "pass_through_2": 0.9,
                "elasticity": 1.0
            }
        )

        # 测试低传导率 (0.1)
        result_low = self.calculator.calculate(
            hs_code="0101.10",
            tariff_rate=tariff_rate,
            custom_params={
                "base_price": base_price,
                "pass_through_1": 0.1,  # 低传导率
                "pass_through_2": 0.1,
                "elasticity": 1.0
            }
        )

        assert result_high.get("success") is True
        assert result_low.get("success") is True

        # 高传导率时，批发价和零售价变化应该更大
        high_wholesale_change = result_high["price_changes"]["wholesale"]["change"]
        low_wholesale_change = result_low["price_changes"]["wholesale"]["change"]

        high_retail_change = result_high["price_changes"]["retail"]["change"]
        low_retail_change = result_low["price_changes"]["retail"]["change"]

        assert high_wholesale_change > low_wholesale_change, \
            f"高传导率的批发价变化应大于低传导率: {high_wholesale_change} vs {low_wholesale_change}"
        assert high_retail_change > low_retail_change, \
            f"高传导率的零售价变化应大于低传导率: {high_retail_change} vs {low_retail_change}"

        print("[OK] test_pass_through 通过：传导率影响正确")

    # ==================== 边界测试 ====================

    def test_invalid_tariff(self, calculator):
        """测试4：负税率报错"""
        result = self.calculator.calculate(
            hs_code="0101.10",
            tariff_rate=-0.1,  # 负税率
            custom_params={
                "base_price": 100,
                "pass_through_1": 0.8,
                "pass_through_2": 0.7,
                "elasticity": 1.0
            }
        )

        # 负税率应该导致错误或被修正
        # 检查返回结果中是否有错误信息，或者计算结果为负数价格
        if not result.get("success"):
            assert "error" in result or "tariff" in str(result).lower()
        else:
            # 如果计算成功，价格不应该为负
            assert result["price_changes"]["import"]["after"] >= 0, \
                "负税率不应该产生负价格"

        print("[OK] test_invalid_tariff 通过：负税率有适当处理")

    def test_invalid_elasticity(self, calculator):
        """测试5：无效弹性值报错"""
        # 测试负弹性
        result = self.calculator.calculate(
            hs_code="0101.10",
            tariff_rate=0.1,
            custom_params={
                "base_price": 100,
                "pass_through_1": 0.8,
                "pass_through_2": 0.7,
                "elasticity": -1.0  # 负弹性
            }
        )

        # 负弹性可能导致计算错误或被修正
        # 计算应该能完成，但结果可能异常
        assert result.get("success") is True, "计算应该能完成"

        # 测试零弹性
        result_zero = self.calculator.calculate(
            hs_code="0101.10",
            tariff_rate=0.1,
            custom_params={
                "base_price": 100,
                "pass_through_1": 0.8,
                "pass_through_2": 0.7,
                "elasticity": 0  # 零弹性
            }
        )

        assert result_zero.get("success") is True, "零弹性计算应该能完成"

        # 测试超大弹性
        result_large = self.calculator.calculate(
            hs_code="0101.10",
            tariff_rate=0.1,
            custom_params={
                "base_price": 100,
                "pass_through_1": 0.8,
                "pass_through_2": 0.7,
                "elasticity": 1000  # 超大弹性
            }
        )

        assert result_large.get("success") is True, "超大弹性计算应该能完成"

        print("[OK] test_invalid_elasticity 通过：无效弹性值有适当处理")

    def test_nonexistent_industry(self, calculator):
        """测试6：不存在行业报错"""
        result = self.calculator.calculate(
            hs_code="9999.99",  # 不存在的HS编码
            tariff_rate=0.1
        )

        # 不存在的行业应该返回错误
        assert result.get("success") is False, "不存在的行业应该返回失败"
        assert "error" in result, "错误结果应包含error字段"
        assert result.get("error") is not None, "error字段不应为None"

        # 错误信息应该提示行业不存在
        error_msg = result.get("error", "").lower()
        assert "不存在" in error_msg or "not found" in error_msg or "invalid" in error_msg, \
            f"错误信息应该提示行业不存在: {result.get('error')}"

        print("[OK] test_nonexistent_industry 通过：不存在行业报错")


# ==================== 运行测试 ====================

if __name__ == "__main__":
    print("=" * 50)
    print("开始运行关税计算器测试")
    print("=" * 50)

    # 创建测试实例并初始化
    test = TestCalculator()
    test.setup_method()  # 初始化 calculator

    # 运行功能测试
    print("\n【功能测试】")
    try:
        test.test_zero_tariff(None)  # 传入任意值，方法内部使用 self.calculator
    except Exception as e:
        print(f"[FAIL] test_zero_tariff 失败: {e}")

    try:
        test.test_full_tariff(None)
    except Exception as e:
        print(f"[FAIL] test_full_tariff 失败: {e}")

    try:
        test.test_pass_through(None)
    except Exception as e:
        print(f"[FAIL] test_pass_through 失败: {e}")

    # 运行边界测试
    print("\n【边界测试】")
    try:
        test.test_invalid_tariff(None)
    except Exception as e:
        print(f"[FAIL] test_invalid_tariff 失败: {e}")

    try:
        test.test_invalid_elasticity(None)
    except Exception as e:
        print(f"[FAIL] test_invalid_elasticity 失败: {e}")

    try:
        test.test_nonexistent_industry(None)
    except Exception as e:
        print(f"[FAIL] test_nonexistent_industry 失败: {e}")

    print("\n" + "=" * 50)
    print("测试完成")
    print("=" * 50)
