# -*- coding: utf-8 -*-
"""
图表生成模块 - 简洁稳定版
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any


class ChartGenerator:
    """图表生成器"""

    @staticmethod
    def plot_price_comparison(result: Dict[str, Any]) -> None:
        """税前vs税后价格对比"""
        if not result or not result.get("price_changes"):
            st.warning("暂无数据")
            return

        price = result["price_changes"]

        df = pd.DataFrame({
            "环节": ["进口", "批发", "零售"],
            "税前": [
                price["import"]["before"],
                price["wholesale"]["before"],
                price["retail"]["before"]
            ],
            "税后": [
                price["import"]["after"],
                price["wholesale"]["after"],
                price["retail"]["after"]
            ]
        }).set_index("环节")

        st.bar_chart(df, use_container_width=True)

    @staticmethod
    def plot_transmission_chain(result: Dict[str, Any], params: Dict[str, Any] = None) -> None:
        """传导路径"""
        if not result or not result.get("price_changes"):
            st.warning("暂无数据")
            return

        price = result["price_changes"]
        tariff_rate = params.get("tariff_rate", 0) if params else 0
        pt1 = params.get("pass_through_1", 0.8) if params else 0.8
        pt2 = params.get("pass_through_2", 0.7) if params else 0.7

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("**进口**")
            st.markdown(f"税前: ¥{price['import']['before']:.2f}")
            st.markdown(f"税后: ¥{price['import']['after']:.2f}")
            st.markdown(f"变化: +{tariff_rate*100:.0f}%")

        with col2:
            st.markdown("**批发**")
            st.markdown(f"税前: ¥{price['wholesale']['before']:.2f}")
            st.markdown(f"税后: ¥{price['wholesale']['after']:.2f}")
            st.markdown(f"传导: {pt1*100:.0f}%")

        with col3:
            st.markdown("**零售**")
            st.markdown(f"税前: ¥{price['retail']['before']:.2f}")
            st.markdown(f"税后: ¥{price['retail']['after']:.2f}")
            st.markdown(f"传导: {pt2*100:.0f}%")

    @staticmethod
    def plot_welfare_effects(result: Dict[str, Any]) -> None:
        """福利效应"""
        if not result or not result.get("welfare_effects"):
            st.warning("暂无数据")
            return

        welfare = result["welfare_effects"]

        df = pd.DataFrame({
            "项目": ["消费者剩余", "生产者剩余", "政府收入", "无谓损失"],
            "金额": [
                welfare.get("consumer_surplus_change", 0),
                welfare.get("producer_surplus_change", 0),
                welfare.get("government_revenue", 0),
                welfare.get("deadweight_loss", 0)
            ]
        }).set_index("项目")

        st.bar_chart(df, use_container_width=True)
