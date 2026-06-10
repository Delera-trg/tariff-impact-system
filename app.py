# -*- coding: utf-8 -*-
"""
中国商品价格传导与关税冲击测算系统
简洁稳定版
"""

import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 导入模块
from modules.calculator import TariffCalculator
from modules.chart_generator import ChartGenerator
from modules.exporter import Exporter

# 页面配置
st.set_page_config(
    page_title="关税冲击测算系统",
    page_icon="chart_with_upwards_trend",
    layout="wide"
)

# 自定义CSS - 确保高对比度
st.markdown("""
<style>
    /* 强制黑色文字 */
    * { color: #000000 !important; }

    /* 白色背景 */
    .stApp { background-color: #FFFFFF; }

    /* 侧边栏 */
    section[data-testid="stSidebar"] { background-color: #F0F0F0; }

    /* 提示框样式 - 黑色文字 */
    .info-box {
        background-color: #E6F3FF;
        border-left: 4px solid #0066CC;
        padding: 12px;
        margin: 8px 0;
    }

    .warning-box {
        background-color: #FFF3CD;
        border-left: 4px solid #FF9900;
        padding: 12px;
        margin: 8px 0;
    }

    .success-box {
        background-color: #D4EDDA;
        border-left: 4px solid #28A745;
        padding: 12px;
        margin: 8px 0;
    }

    /* 标题 */
    h1, h2, h3 { color: #000000 !important; }
</style>
""", unsafe_allow_html=True)

# 初始化
calculator = TariffCalculator()
chart_gen = ChartGenerator()
exporter = Exporter()

# ==================== 新手引导系统 ====================
def init_session_state():
    """初始化session state"""
    if 'guided' not in st.session_state:
        st.session_state.guided = False
    if 'show_guide' not in st.session_state:
        st.session_state.show_guide = True
    if 'guide_step' not in st.session_state:
        st.session_state.guide_step = 0
    if 'calculation_result' not in st.session_state:
        st.session_state.calculation_result = None
    if 'show_export' not in st.session_state:
        st.session_state.show_export = False
    if 'session_id' not in st.session_state:
        # 生成唯一会话ID
        import uuid
        st.session_state.session_id = str(uuid.uuid4())
    if 'active_tab' not in st.session_state:
        st.session_state.active_tab = "计算"

init_session_state()

def render_guide():
    """渲染交互式新手引导"""
    if not st.session_state.show_guide or st.session_state.guided:
        return

    # 引导步骤配置
    guide_steps = [
        {
            "title": "🎯 欢迎使用关税冲击测算系统",
            "content": "本系统用于分析关税政策对商品价格的影响，适合经济学学习与政策分析。",
            "step_name": "intro"
        },
        {
            "title": "📋 第一步：设置参数",
            "content": "在左侧边栏：\n1. 选择预设场景或自定义\n2. 选择要分析的行业\n3. 调整关税税率\n4. 设置传导参数",
            "step_name": "params"
        },
        {
            "title": "🔢 第二步：开始计算",
            "content": "点击主界面中央的「开始计算」按钮，系统将根据您设置的参数进行关税冲击测算。",
            "step_name": "calc"
        },
        {
            "title": "📊 第三步：解读结果",
            "content": "计算完成后，您将看到：\n• 价格变化表格（进口/批发/零售）\n• 福利效应指标\n• 价格对比图表\n• 可导出Excel报告",
            "step_name": "result"
        }
    ]

    current_step = st.session_state.guide_step
    total_steps = len(guide_steps)

    # 引导容器
    with st.container():
        st.markdown("""
        <style>
            .guide-box {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 12px;
                padding: 20px;
                margin: 10px 0;
                color: white;
            }
            .guide-title {
                font-size: 18px;
                font-weight: bold;
                margin-bottom: 10px;
            }
            .guide-content {
                font-size: 14px;
                line-height: 1.6;
                margin-bottom: 15px;
            }
            .guide-progress {
                display: flex;
                justify-content: center;
                gap: 8px;
                margin-bottom: 15px;
            }
            .guide-dot {
                width: 10px;
                height: 10px;
                border-radius: 50%;
                background: rgba(255,255,255,0.3);
            }
            .guide-dot.active {
                background: white;
            }
        </style>
        """, unsafe_allow_html=True)

        # 进度点
        dots_html = '<div class="guide-progress">'
        for i in range(total_steps):
            if i == current_step:
                dots_html += '<div class="guide-dot active"></div>'
            else:
                dots_html += '<div class="guide-dot"></div>'
        dots_html += '</div>'

        st.markdown(f"""
        <div class="guide-box">
            <div class="guide-title">{guide_steps[current_step]["title"]}</div>
            <div class="guide-content">{guide_steps[current_step]["content"]}</div>
            {dots_html}
        </div>
        """, unsafe_allow_html=True)

        # 兼容旧版Streamlit的刷新函数
        def rerun_page():
            try:
                st.experimental_rerun()
            except:
                import streamlit as st
                st.markdown("<script>window.location.reload()</script>", unsafe_allow_html=True)

        # 按钮列
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("⏭ 跳过引导", key="skip_guide"):
                st.session_state.guided = True
                rerun_page()
        with col2:
            if current_step > 0:
                if st.button("⬆ 上一步", key="prev_step"):
                    st.session_state.guide_step -= 1
                    rerun_page()
        with col3:
            if current_step < total_steps - 1:
                if st.button("下一步 ⬇", key="next_step"):
                    st.session_state.guide_step += 1
                    rerun_page()
            else:
                if st.button("✅ 开始使用", key="finish_guide"):
                    st.session_state.guided = True
                    rerun_page()

# 渲染引导（仅首次）
render_guide()

# 工具函数
def format_currency(value):
    if abs(value) >= 10000:
        return f"¥{value/10000:.2f}万"
    return f"¥{value:,.2f}"


# ==================== 历史记录页面 ====================
def render_history_page(calculator):
    """渲染历史记录页面"""
    st.markdown("## 📜 计算历史记录")

    # 获取历史记录
    session_id = st.session_state.get("session_id", "default")
    history = calculator.db.get_calculation_history(session_id=session_id, limit=50)

    if not history:
        st.info("暂无计算历史记录")
        st.markdown("请先进行关税冲击测算，系统会自动保存计算历史。")
        return

    # 操作按钮
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("🗑 清空历史", key="clear_history"):
            calculator.db.clear_calculation_history(session_id=session_id)
            st.success("历史记录已清空")
            st.experimental_rerun()

    # 显示历史记录表格
    st.markdown("### 历史记录")

    # 转换为DataFrame显示
    df_history = pd.DataFrame(history)
    # 选择显示的列
    display_cols = ["created_at", "hs_code", "industry_name", "tariff_rate", "base_price",
                    "import_after", "retail_after", "government_revenue", "deadweight_loss"]
    df_display = df_history[display_cols].copy()

    # 格式化显示
    df_display["created_at"] = pd.to_datetime(df_display["created_at"]).dt.strftime("%Y-%m-%d %H:%M:%S")
    df_display["tariff_rate"] = df_display["tariff_rate"].apply(lambda x: f"{x*100:.1f}%" if pd.notna(x) else "N/A")
    for col in ["base_price", "import_after", "retail_after"]:
        df_display[col] = df_display[col].apply(lambda x: f"¥{x:,.2f}" if pd.notna(x) else "N/A")
    for col in ["government_revenue", "deadweight_loss"]:
        df_display[col] = df_display[col].apply(lambda x: f"¥{x:,.0f}" if pd.notna(x) else "N/A")

    # 重命名列
    df_display.columns = ["时间", "HS编码", "行业", "关税税率", "进口价", "批发价", "零售价", "关税收入", "无谓损失"]

    st.dataframe(df_display, use_container_width=True, hide_index=True)

    # 选择查看详情
    st.markdown("### 查看详情")
    selected_idx = st.selectbox("选择一条记录查看详情", range(len(history)), format_func=lambda i: f"{history[i]['industry_name']} - {history[i]['tariff_rate']*100:.1f}% 关税")

    if selected_idx is not None:
        record = history[selected_idx]
        st.markdown("#### 计算参数")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("HS编码", record.get("hs_code", "N/A"))
        with col2:
            tariff_val = record.get('tariff_rate') or 0
            st.metric("关税税率", f"{tariff_val*100:.1f}%")
        with col3:
            base_price_val = record.get('base_price') or 0
            st.metric("基准价格", f"¥{base_price_val:,.2f}")
        with col4:
            st.metric("需求弹性", record.get("elasticity", "N/A"))

        st.markdown("#### 价格变化")
        col1, col2, col3 = st.columns(3)
        with col1:
            import_change = (record.get('import_after') or 0) - (record.get('import_before') or 0)
            st.metric("进口价变化", f"¥{import_change:+,.2f}")
        with col2:
            wholesale_change = (record.get('wholesale_after') or 0) - (record.get('wholesale_before') or 0)
            st.metric("批发价变化", f"¥{wholesale_change:+,.2f}")
        with col3:
            retail_change = (record.get('retail_after') or 0) - (record.get('retail_before') or 0)
            st.metric("零售价变化", f"¥{retail_change:+,.2f}")

        st.markdown("#### 福利效应")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            cs = record.get('consumer_surplus') or 0
            st.metric("消费者剩余变化", f"¥{cs:+,.0f}", delta_color="inverse")
        with col2:
            ps = record.get('producer_surplus') or 0
            st.metric("生产者剩余变化", f"¥{ps:+,.0f}", delta_color="inverse")
        with col3:
            gov = record.get('government_revenue') or 0
            st.metric("政府关税收入", f"¥{gov:+,.0f}")
        with col4:
            dwl = record.get('deadweight_loss') or 0
            st.metric("无谓损失", f"¥{dwl:+,.0f}", delta_color="inverse")


# ==================== 敏感性分析页面 ====================
def render_sensitivity_page(calculator):
    """渲染敏感性分析页面"""
    st.markdown("## 📈 敏感性分析")
    st.markdown("分析不同关税税率对价格和福利效应的影响")

    # 获取行业列表
    industries = calculator.get_supported_industries()
    industry_options = {f"{ind['hs_code']} - {ind['name']}": ind['hs_code'] for ind in industries}
    selected_industry_name = st.selectbox("选择行业", list(industry_options.keys()), 0, key="sensitivity_industry")
    hs_code = industry_options[selected_industry_name]

    # 设置税率范围
    st.markdown("### 关税税率范围")
    col1, col2 = st.columns(2)
    with col1:
        min_tariff = st.number_input("最低税率 (%)", 0, 50, 0)
    with col2:
        max_tariff = st.number_input("最高税率 (%)", 0, 50, 50)

    step = st.slider("税率步长 (%)", 1, 10, 5)

    # 传导参数
    st.markdown("### 传导参数")
    col1, col2, col3 = st.columns(3)
    with col1:
        pt1 = st.slider("进口->批发传导率", 0.0, 1.0, 0.8, 0.05)
    with col2:
        pt2 = st.slider("批发->零售传导率", 0.0, 1.0, 0.7, 0.05)
    with col3:
        elasticity = st.number_input("需求弹性", 0.1, 5.0, 1.0, 0.1, key="sensitivity_elasticity")

    if st.button("开始敏感性分析", type="primary"):
        with st.spinner("正在计算..."):
            # 获取行业基准价格
            industry_detail = calculator.db.get_industry_detail(hs_code=hs_code)
            base_price = industry_detail.get("base_price", 100) if industry_detail else 100

            # 收集结果
            results = []
            tariff_rates = list(range(min_tariff, max_tariff + 1, step))

            for rate in tariff_rates:
                result = calculator.calculate(
                    hs_code=hs_code,
                    tariff_rate=rate / 100,
                    custom_params={
                        "base_price": base_price,
                        "pass_through_1": pt1,
                        "pass_through_2": pt2,
                        "elasticity": elasticity
                    }
                )
                if result.get("success"):
                    price = result["price_changes"]
                    welfare = result["welfare_effects"]
                    results.append({
                        "tariff_rate": rate,
                        "import_price": price["import"]["after"],
                        "wholesale_price": price["wholesale"]["after"],
                        "retail_price": price["retail"]["after"],
                        "consumer_surplus": welfare.get("consumer_surplus_change", 0),
                        "producer_surplus": welfare.get("producer_surplus_change", 0),
                        "government_revenue": welfare.get("government_revenue", 0),
                        "deadweight_loss": welfare.get("deadweight_loss", 0)
                    })

            if results:
                # 创建DataFrame
                df = pd.DataFrame(results)

                # 显示结果表格
                st.markdown("### 分析结果")
                st.dataframe(df.style.format({
                    "tariff_rate": "{:.0f}%",
                    "import_price": "¥{:.2f}",
                    "wholesale_price": "¥{:.2f}",
                    "retail_price": "¥{:.2f}",
                    "consumer_surplus": "¥{:.0f}",
                    "producer_surplus": "¥{:.0f}",
                    "government_revenue": "¥{:.0f}",
                    "deadweight_loss": "¥{:.0f}"
                }), use_container_width=True, hide_index=True)

                # 绘制敏感性分析图表
                st.markdown("### 价格敏感性分析")

                # 价格变化图
                import matplotlib.pyplot as plt
                fig_price, ax = plt.subplots(figsize=(10, 5))
                ax.plot(df['tariff_rate'], df['import_price'], marker='o', label='进口价')
                ax.plot(df['tariff_rate'], df['wholesale_price'], marker='s', label='批发价')
                ax.plot(df['tariff_rate'], df['retail_price'], marker='^', label='零售价')
                ax.set_xlabel('关税税率 (%)')
                ax.set_ylabel('价格 (¥)')
                ax.set_title('关税税率 vs 价格变化')
                ax.legend()
                ax.grid(True, alpha=0.3)
                st.pyplot(fig_price)

                # 福利效应图
                st.markdown("### 福利效应敏感性分析")
                fig_welfare, ax2 = plt.subplots(figsize=(10, 5))
                ax2.plot(df["tariff_rate"], df["consumer_surplus"], marker='o', label='消费者剩余变化')
                ax2.plot(df["tariff_rate"], df["producer_surplus"], marker='s', label='生产者剩余变化')
                ax2.plot(df["tariff_rate"], df["government_revenue"], marker='^', label='政府关税收入')
                ax2.plot(df["tariff_rate"], df["deadweight_loss"], marker='x', label='无谓损失')
                ax2.set_xlabel('关税税率 (%)')
                ax2.set_ylabel('金额 (¥)')
                ax2.set_title('关税税率 vs 福利效应')
                ax2.legend()
                ax2.grid(True, alpha=0.3)
                st.pyplot(fig_welfare)

                # 导出结果
                st.markdown("### 导出分析结果")
                file_name = f"敏感性分析_{hs_code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                file_path = exporter.export_to_excel({"sensitivity_analysis": df.to_dict()}, file_name=file_name)
                with open(file_path, "rb") as f:
                    st.download_button("下载Excel报告", data=f, file_name=os.path.basename(file_path),
                                      mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            else:
                st.error("计算失败，请检查参数设置")


# ==================== 侧边栏 ====================
with st.sidebar:
    # 新手引导按钮
    if st.button("📖 重新显示引导", key="show_guide_btn"):
        st.session_state.guided = False
        st.session_state.show_guide = True
        st.session_state.guide_step = 0
        try:
            st.experimental_rerun()
        except:
            st.markdown("<script>window.location.reload()</script>", unsafe_allow_html=True)

    st.markdown("---")

    # ========== 参数设置区域 ==========
    st.markdown("## 参数设置")

    # 预设场景
    preset = st.radio("快速场景", ["自定义", "25%", "5%", "40%", "0%"], key="preset")
    if preset == "25%":
        default_tariff = 25
    elif preset == "5%":
        default_tariff = 5
    elif preset == "40%":
        default_tariff = 40
    elif preset == "0%":
        default_tariff = 0
    else:
        default_tariff = 10

    st.markdown("---")

    # 行业选择
    st.markdown("### 选择行业")
    industries = calculator.get_supported_industries()
    industry_options = {f"{ind['hs_code']} - {ind['name']}": ind['hs_code'] for ind in industries}
    selected_industry = st.selectbox("行业", list(industry_options.keys()), 0, key="main_industry")
    hs_code = industry_options[selected_industry]
    industry_detail = calculator.db.get_industry_detail(hs_code=hs_code)

    st.markdown("---")

    # 关税税率
    st.markdown("### 关税税率")
    if preset == "自定义":
        # 自定义输入框
        custom_tariff = st.number_input("输入自定义税率 (%)", min_value=0, max_value=100, value=default_tariff, step=1)
        tariff_rate = custom_tariff / 100
        st.markdown(f"**当前: {custom_tariff}%**")
    else:
        # 滑块选择
        tariff_rate = st.slider("税率 (%)", 0, 50, default_tariff, 1) / 100
        st.markdown(f"**当前: {tariff_rate*100:.0f}%**")

    st.markdown("---")

    # 传导参数
    st.markdown("### 传导参数")
    pt1 = industry_detail.get("transmission_params", {}).get("import_to_wholesale", {}).get("pass_through_rate", 0.8) if industry_detail else 0.8
    pt2 = industry_detail.get("transmission_params", {}).get("wholesale_to_retail", {}).get("pass_through_rate", 0.7) if industry_detail else 0.7

    pass_through_1 = st.slider("进口->批发传导率", 0.0, 1.0, pt1, 0.05, key="pt1")
    pass_through_2 = st.slider("批发->零售传导率", 0.0, 1.0, pt2, 0.05, key="pt2")
    elasticity = st.number_input("需求弹性", 0.1, 5.0, 1.0, 0.1, key="main_elasticity")

    st.markdown("---")

    # 行业信息
    if industry_detail:
        st.markdown("### 行业信息")
        st.markdown(f"""
- HS编码: **{industry_detail['hs_code']}**
- 进口价: ¥{industry_detail['base_price']:,.2f}
- 批发价: ¥{industry_detail['wholesale_price']:,.2f}
- 零售价: ¥{industry_detail['retail_price']:,.2f}
- 当前关税: {industry_detail.get('current_tariff_rate', 0)*100:.0f}%
        """)

# ==================== 功能选项卡 ====================
# 极简风格的功能选项卡
st.markdown("""
<style>
    .tab-container {
        display: flex;
        gap: 8px;
        margin-bottom: 20px;
    }
    .tab-btn {
        flex: 1;
        padding: 12px 20px;
        background: #f5f5f5;
        border: none;
        border-radius: 8px;
        cursor: pointer;
        font-size: 15px;
        color: #333;
        transition: all 0.2s;
    }
    .tab-btn:hover {
        background: #e8e8e8;
    }
    .tab-btn.active {
        background: #4CAF50;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# 使用session_state存储选项卡状态
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = "计算"

# 创建导航栏样式
st.markdown("""
<style>
    .nav-container {
        display: flex;
        gap: 0;
        margin-bottom: 20px;
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid #ddd;
    }
    .nav-btn {
        flex: 1;
        padding: 14px 20px;
        border: none;
        background: white;
        cursor: pointer;
        font-size: 15px;
        color: #333;
        text-align: center;
        transition: all 0.2s;
        text-decoration: none;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
    }
    .nav-btn:hover {
        background: #f5f5f5;
    }
    .nav-btn.active {
        background: #2196F3;
        color: white;
    }
    .nav-btn:not(.active) {
        border-right: 1px solid #eee;
    }
    .nav-btn:last-child {
        border-right: none;
    }
</style>
""", unsafe_allow_html=True)

# 使用st.tabs实现导航栏
tab1, tab2, tab3 = st.tabs(["📊 关税计算", "📜 历史记录", "📈 敏感性分析"])

with tab1:
    # 关税计算内容
    st.title("中国商品价格传导与关税冲击测算系统")
    st.markdown("**适用对象：经济学学生、国际贸易学习者**")

    # 顶部操作提示
    st.markdown("""
    <div style="background: linear-gradient(90deg, #f5f7fa 0%, #e4e8ec 100%);
                padding: 12px 20px; border-radius: 8px; margin-bottom: 20px;
                border-left: 4px solid #4CAF50;">
        <div style="display: flex; justify-content: center; align-items: center; gap: 30px; flex-wrap: wrap;">
            <div style="text-align: center;">
                <span style="background: #4CAF50; color: white; padding: 4px 12px; border-radius: 12px; font-weight: bold;">1</span>
                <span style="margin-left: 8px; font-weight: 500;">设置参数</span>
            </div>
            <span style="color: #999;">➜</span>
            <div style="text-align: center;">
                <span style="background: #2196F3; color: white; padding: 4px 12px; border-radius: 12px; font-weight: bold;">2</span>
                <span style="margin-left: 8px; font-weight: 500;">点击计算</span>
            </div>
            <span style="color: #999;">➜</span>
            <div style="text-align: center;">
                <span style="background: #FF9800; color: white; padding: 4px 12px; border-radius: 12px; font-weight: bold;">3</span>
                <span style="margin-left: 8px; font-weight: 500;">查看结果</span>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

with tab2:
    # 历史记录内容
    render_history_page(calculator)

with tab3:
    # 敏感性分析内容
    render_sensitivity_page(calculator)

# 计算按钮
if st.button("开始计算", type="primary"):
    with st.spinner("正在计算..."):
        result = calculator.calculate(
            hs_code=hs_code,
            tariff_rate=tariff_rate,
            custom_params={
                "pass_through_1": pass_through_1,
                "pass_through_2": pass_through_2,
                "elasticity": elasticity
            }
        )
        # 保存计算结果到session_state
        st.session_state.calculation_result = result
        st.session_state.show_export = False

        if result.get("success"):
            # 保存历史记录
            session_id = st.session_state.get("session_id", "default")
            calculator.db.save_calculation_history(result, session_id=session_id)

            # 价格变化
            st.markdown("## 计算结果")

            price = result["price_changes"]
            welfare = result["welfare_effects"]
            industry = result["industry"]
            params = result["params"]

            # 结果表格
            df = pd.DataFrame({
                "环节": ["进口", "批发", "零售"],
                "税前价格": [price["import"]["before"], price["wholesale"]["before"], price["retail"]["before"]],
                "税后价格": [price["import"]["after"], price["wholesale"]["after"], price["retail"]["after"]],
                "变化额": [price["import"]["change"], price["wholesale"]["change"], price["retail"]["change"]],
                "变化率": [f"{price['import']['change_rate']:.2f}%", f"{price['wholesale']['change_rate']:.2f}%", f"{price['retail']['change_rate']:.2f}%"]
            })
            st.dataframe(df.style.format({"税前价格": "¥{:.2f}", "税后价格": "¥{:.2f}", "变化额": "¥{:.2f}"}), use_container_width=True, hide_index=True)

            st.markdown("")

            # 福利效应
            col1, col2, col3, col4 = st.columns(4)
            with col1: st.metric("消费者剩余变化", format_currency(welfare.get("consumer_surplus_change", 0)), delta_color="inverse")
            with col2: st.metric("生产者剩余变化", format_currency(welfare.get("producer_surplus_change", 0)), delta_color="inverse")
            with col3: st.metric("政府关税收入", format_currency(welfare.get("government_revenue", 0)))
            with col4: st.metric("无谓损失", format_currency(welfare.get("deadweight_loss", 0)), delta_color="inverse")

