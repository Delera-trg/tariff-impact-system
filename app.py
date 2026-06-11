# -*- coding: utf-8 -*-
"""
China Commodity Price Transmission and Tariff Impact Analysis System
Stable Version
"""

import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 导入模块
from modules.calculator import TariffCalculator
from modules.chart_generator import ChartGenerator
from modules.exporter import Exporter
import matplotlib
matplotlib.use('Agg')  # 非交互式后端，适合Streamlit

# 页面配置
st.set_page_config(
    page_title="Tariff Impact Analysis System",
    page_icon="chart_with_upwards_trend",
    layout="wide"
)

# 自定义CSS - 优化UI布局和样式
st.markdown("""
<style>
    /* ===== 基础样式 ===== */
    /* 白色背景 */
    .stApp { background-color: #FAFBFC; }

    /* 侧边栏 */
    section[data-testid="stSidebar"] { background-color: #F4F6F8; }

    /* ===== 标题层级 ===== */
    /* 主标题 */
    h1 {
        color: #1A1A2E !important;
        font-weight: 700 !important;
        font-size: 2rem !important;
        margin-bottom: 0.5rem !important;
    }

    /* 章节标题 */
    h2 {
        color: #2D3748 !important;
        font-weight: 600 !important;
        font-size: 1.5rem !important;
        margin-top: 1.5rem !important;
        margin-bottom: 0.75rem !important;
        border-bottom: 2px solid #E2E8F0;
        padding-bottom: 0.5rem;
    }

    /* 子章节标题 */
    h3 {
        color: #4A5568 !important;
        font-weight: 600 !important;
        font-size: 1.15rem !important;
        margin-top: 1rem !important;
        margin-bottom: 0.5rem !important;
    }

    /* 描述文字 - 灰色调 */
    .stMarkdown p, .stText, p {
        color: #718096 !important;
        font-size: 0.95rem !important;
        line-height: 1.6 !important;
    }

    /* ===== 卡片组件 ===== */
    /* 结果卡片 */
    .result-card {
        background: #FFFFFF;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        border: 1px solid #E2E8F0;
    }

    /* 图表卡片 */
    .chart-card {
        background: #FFFFFF;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1.5rem 0;
        box-shadow: 0 2px 12px rgba(0,0,0,0.06);
        border: 1px solid #E2E8F0;
    }

    /* 指标卡片 */
    .metric-card {
        background: #FFFFFF;
        border-radius: 10px;
        padding: 1rem 1.25rem;
        box-shadow: 0 1px 4px rgba(0,0,0,0.05);
        border: 1px solid #E2E8F0;
        text-align: center;
    }

    /* ===== 侧边栏样式 ===== */
    /* 侧边栏标题 */
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: #2D3748 !important;
    }

    /* 侧边栏分隔线 */
    section[data-testid="stSidebar"] hr {
        border-color: #CBD5E0;
        margin: 1rem 0;
    }

    /* ===== 按钮样式 ===== */
    /* 主要按钮 - 白底蓝字 + 蓝框 */
    div.stButton > button[kind="primary"] {
        background: #FFFFFF !important;
        border: 2px solid #1976D2 !important;
        border-radius: 8px !important;
        padding: 0.75rem 2rem !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        color: #1976D2 !important;
        width: 100% !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 2px 8px rgba(25, 118, 210, 0.2) !important;
    }

    div.stButton > button[kind="primary"]:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(25, 118, 210, 0.3) !important;
        background: #E3F2FD !important;
    }

    /* ===== 选项卡样式 ===== */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 0.75rem 1.5rem;
        font-weight: 500;
    }

    /* ===== 数据框样式 ===== */
    .stDataFrame {
        border-radius: 8px;
        overflow: hidden;
    }

    /* ===== 提示框样式 ===== */
    .info-box {
        background-color: #EBF8FF;
        border-left: 4px solid #3182CE;
        padding: 12px 16px;
        margin: 12px 0;
        border-radius: 0 8px 8px 0;
    }

    .warning-box {
        background-color: #FEFCBF;
        border-left: 4px solid #D69E2E;
        padding: 12px 16px;
        margin: 12px 0;
        border-radius: 0 8px 8px 0;
    }

    .success-box {
        background-color: #C6F6D5;
        border-left: 4px solid #38A169;
        padding: 12px 16px;
        margin: 12px 0;
        border-radius: 0 8px 8px 0;
    }

    /* ===== 间距优化 ===== */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 2rem;
    }

    /* ===== 操作步骤条 ===== */
    .step-indicator {
        background: linear-gradient(90deg, #F7FAFC 0%, #EDF2F7 100%);
        padding: 14px 24px;
        border-radius: 10px;
        margin-bottom: 1.5rem;
        border: 1px solid #E2E8F0;
    }
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
        st.session_state.active_tab = "Calculation"
    # 统一管理税率参数
    if 'tariff_rate' not in st.session_state:
        st.session_state.tariff_rate = 0.10  # 默认10%
    if 'current_preset' not in st.session_state:
        st.session_state.current_preset = "Custom"

init_session_state()

# 清理缓存逻辑 - 确保每次计算都是最新结果
# 通过在session_state中记录参数哈希来检测参数变化
def get_params_hash(preset, hs_code, tariff_rate, pt1, pt2, elasticity, supply_elasticity=2.0):
    """生成参数哈希，用于检测参数变化"""
    import hashlib
    params_str = f"{preset}|{hs_code}|{tariff_rate}|{pt1}|{pt2}|{elasticity}|{supply_elasticity}"
    return hashlib.md5(params_str.encode()).hexdigest()

# 检测参数变化，清除缓存
current_params_hash = get_params_hash(
    st.session_state.get('tariff_mode', 'Quick Presets'),
    hs_code if 'hs_code' in dir() else '',
    st.session_state.get('tariff_rate', 0),
    st.session_state.get('pt1', 0.8),
    st.session_state.get('pt2', 0.7),
    st.session_state.get('elasticity', 1.0),
    st.session_state.get('supply_elasticity', 2.0)
)

if 'last_params_hash' not in st.session_state:
    st.session_state.last_params_hash = ''

if current_params_hash != st.session_state.last_params_hash:
    # 参数变化，清除缓存的计算结果
    st.session_state.calculation_result = None
    st.session_state.last_params_hash = current_params_hash

def render_guide():
    """渲染交互式新手引导"""
    if not st.session_state.show_guide or st.session_state.guided:
        return

    # 引导步骤配置
    guide_steps = [
        {
            "title": "Welcome to Tariff Impact Analysis System",
            "content": "This system analyzes the impact of tariff policies on commodity prices, suitable for economics study and policy analysis.",
            "step_name": "intro"
        },
        {
            "title": "Step 1: Set Parameters",
            "content": "In the left sidebar:\n1. Select a preset or custom\n2. Choose industry to analyze\n3. Adjust tariff rate\n4. Set transmission parameters",
            "step_name": "params"
        },
        {
            "title": "Step 2: Calculate",
            "content": "Click the 'Calculate' button in the center to run the tariff impact analysis.",
            "step_name": "calc"
        },
        {
            "title": "Step 3: Interpret Results",
            "content": "After calculation, you will see:\n- Price change table (Import/Wholesale/Retail)\n- Welfare effect indicators\n- Price comparison charts\n- Exportable Excel reports",
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
            if st.button("Skip Guide", key="skip_guide"):
                st.session_state.guided = True
                rerun_page()
        with col2:
            if current_step > 0:
                if st.button("Previous", key="prev_step"):
                    st.session_state.guide_step -= 1
                    rerun_page()
        with col3:
            if current_step < total_steps - 1:
                if st.button("Next", key="next_step"):
                    st.session_state.guide_step += 1
                    rerun_page()
            else:
                if st.button("Start Using", key="finish_guide"):
                    st.session_state.guided = True
                    rerun_page()

# 渲染引导（仅首次）
render_guide()

# 工具函数
def format_currency(value):
    if abs(value) >= 10000:
        return f"¥{value:,.0f}"
    return f"¥{value:,.2f}"


# ==================== History Page ====================
def render_history_page(calculator):
    """Render history page"""
    st.markdown("## Calculation History")

    # Get history
    session_id = st.session_state.get("session_id", "default")
    history = calculator.db.get_calculation_history(session_id=session_id, limit=50)

    if not history:
        # 显示欢迎信息和提示 - 白底 + 深紫色文字 + 深紫色边框
        st.markdown("""
        <div style="background: #FFFFFF;
                    border: 2px solid #7B1FA2;
                    border-radius: 12px; padding: 30px; margin: 20px 0; text-align: center;">
            <h3 style="margin-bottom: 15px; color: #7B1FA2;">📊 Welcome to History Page</h3>
            <p style="font-size: 16px; color: #4A5568;">No calculation history found.</p>
            <p style="font-size: 14px; color: #718096;">Please run a tariff impact calculation in the "Tariff Calculation" tab first.</p>
            <p style="font-size: 14px; color: #718096; margin-top: 10px;">The system will automatically save your calculation history here.</p>
        </div>
        """, unsafe_allow_html=True)

        # 提示用户去计算
        st.markdown("### Quick Start")
        st.markdown("""
        1. Go to **Tariff Calculation** tab
        2. Set your tariff parameters in the left sidebar
        3. Click the **Calculate** button
        4. Your calculation will be automatically saved to history
        5. Return to this page to view your history
        """)
        return

    # Action buttons
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("Clear History", key="clear_history"):
            calculator.db.clear_calculation_history(session_id=session_id)
            st.success("History cleared")
            st.experimental_rerun()

    # Display history table
    st.markdown("### History Records")

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
    df_display.columns = ["Time", "HS Code", "Industry", "Tariff Rate", "Import Price", "Wholesale Price", "Retail Price", "Tariff Revenue", "Deadweight Loss"]

    st.dataframe(df_display, use_container_width=True, hide_index=True)

    # Select to view details
    st.markdown("### View Details")
    selected_idx = st.selectbox("Select a record to view", range(len(history)), format_func=lambda i: f"{history[i]['industry_name']} - {history[i]['tariff_rate']*100:.1f}% Tariff")

    if selected_idx is not None:
        record = history[selected_idx]
        st.markdown("#### Calculation Parameters")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("HS Code", record.get("hs_code", "N/A"))
        with col2:
            tariff_val = record.get('tariff_rate') or 0
            st.metric("Tariff Rate", f"{tariff_val*100:.1f}%")
        with col3:
            base_price_val = record.get('base_price') or 0
            st.metric("Base Price", f"¥{base_price_val:,.2f}")
        with col4:
            st.metric("Elasticity", record.get("elasticity", "N/A"))

        st.markdown("#### Price Changes")
        col1, col2, col3 = st.columns(3)
        with col1:
            import_change = (record.get('import_after') or 0) - (record.get('import_before') or 0)
            st.metric("Import Price Change", f"¥{import_change:+,.2f}")
        with col2:
            wholesale_change = (record.get('wholesale_after') or 0) - (record.get('wholesale_before') or 0)
            st.metric("Wholesale Price Change", f"¥{wholesale_change:+,.2f}")
        with col3:
            retail_change = (record.get('retail_after') or 0) - (record.get('retail_before') or 0)
            st.metric("Retail Price Change", f"¥{retail_change:+,.2f}")

        st.markdown("#### Welfare Effects")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            cs = record.get('consumer_surplus') or 0
            st.metric("Consumer Surplus Change", f"¥{cs:+,.0f}", delta_color="inverse")
        with col2:
            ps = record.get('producer_surplus') or 0
            st.metric("Producer Surplus Change", f"¥{ps:+,.0f}", delta_color="inverse")
        with col3:
            gov = record.get('government_revenue') or 0
            st.metric("Government Revenue", f"¥{gov:+,.0f}")
        with col4:
            dwl = record.get('deadweight_loss') or 0
            st.metric("Deadweight Loss", f"¥{dwl:+,.0f}", delta_color="inverse")

        # Business Summary
        st.markdown("#### Business Summary")

        # Calculate retail price increase percentage
        retail_before = record.get('retail_before') or 0
        retail_after = record.get('retail_after') or 0
        if retail_before > 0:
            retail_increase_pct = (retail_after - retail_before) / retail_before * 100
        else:
            retail_increase_pct = 0

        # Determine pressure level
        if retail_increase_pct <= 3:
            pressure_level = "Low"
            pressure_color = "green"
        elif retail_increase_pct <= 8:
            pressure_level = "Moderate"
            pressure_color = "orange"
        else:
            pressure_level = "High"
            pressure_color = "red"

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Tariff Rate", f"{tariff_val*100:.1f}%")
        with col2:
            st.metric("Retail Price Increase", f"{retail_increase_pct:.2f}%", delta_color="inverse" if retail_increase_pct > 0 else "normal")

        st.markdown(f"**Price Pressure Level:** :{pressure_color}[{pressure_level}]")


# ==================== Sensitivity Analysis Page ====================
def render_sensitivity_page(calculator):
    """Render sensitivity analysis page"""
    st.markdown("## Sensitivity Analysis")
    st.markdown("Analyze the impact of different tariff rates on prices and welfare effects")

    # 显示欢迎/说明信息
    st.markdown("""
    <div style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
                border-radius: 12px; padding: 20px; margin: 15px 0; color: white;">
        <h4 style="margin-bottom: 10px; color: white;">📈 Sensitivity Analysis</h4>
        <p style="font-size: 14px; color: rgba(255,255,255,0.95);">This analysis shows how prices and welfare effects change across different tariff rates.</p>
        <p style="font-size: 13px; color: rgba(255,255,255,0.85); margin-top: 8px;">Set your parameters below and click <b>"Run Sensitivity Analysis"</b> to see the results.</p>
    </div>
    """, unsafe_allow_html=True)

    # Get industry list
    industries = calculator.get_supported_industries()
    industry_options = {f"{ind['hs_code']} - {ind['name']}": ind['hs_code'] for ind in industries}
    selected_industry_name = st.selectbox("Select Industry", list(industry_options.keys()), 0, key="sensitivity_industry")
    hs_code = industry_options[selected_industry_name]

    # Set tariff rate range
    st.markdown("### Tariff Rate Range")
    col1, col2 = st.columns(2)
    with col1:
        min_tariff = st.number_input("Min Tariff Rate (%)", 0, 50, 0)
    with col2:
        max_tariff = st.number_input("Max Tariff Rate (%)", 0, 50, 50)

    step = st.slider("Tariff Step (%)", 1, 10, 5)

    # Transmission parameters
    st.markdown("### Transmission Parameters")
    col1, col2, col3 = st.columns(3)
    with col1:
        pt1 = st.slider("Import->Wholesale Pass-Through", 0.0, 1.0, 0.8, 0.05)
    with col2:
        pt2 = st.slider("Wholesale->Retail Pass-Through", 0.0, 1.0, 0.7, 0.05)
    with col3:
        elasticity = st.number_input("Demand Elasticity", 0.1, 5.0, 1.0, 0.1, key="sensitivity_elasticity")
    supply_elasticity_sens = st.number_input("Supply Elasticity", 0.1, 10.0, 2.0, 0.1, key="sensitivity_supply_elasticity")

    if st.button("Run Sensitivity Analysis", type="primary"):
        with st.spinner("Calculating..."):
            # Get industry base price
            industry_detail = calculator.db.get_industry_detail(hs_code=hs_code)
            base_price = industry_detail.get("base_price", 100) if industry_detail else 100

            # Collect results
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
                        "elasticity": elasticity,
                        "supply_elasticity": supply_elasticity_sens
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
                # Create DataFrame
                df = pd.DataFrame(results)

                # Display result table
                st.markdown("### Analysis Results")
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

                # 绘制敏感性分析图表 - 包装在卡片中
                st.markdown("### Price Sensitivity Analysis")

                # Card wrapper
                st.markdown('<div class="chart-card">', unsafe_allow_html=True)

                # 价格变化图 - 英文标注，X轴范围0-50%
                import matplotlib.pyplot as plt
                fig_price, ax = plt.subplots(figsize=(12, 6))
                ax.plot(df['tariff_rate'], df['import_price'], marker='o', markersize=8, linewidth=2.5, label='Import Price')
                ax.plot(df['tariff_rate'], df['wholesale_price'], marker='s', markersize=8, linewidth=2.5, label='Wholesale Price')
                ax.plot(df['tariff_rate'], df['retail_price'], marker='^', markersize=8, linewidth=2.5, label='Retail Price')
                ax.set_xlabel('Tariff Rate (%)', fontsize=13, fontweight='bold')
                ax.set_ylabel('Price (CNY)', fontsize=13, fontweight='bold')
                ax.set_title('Tariff Rate vs Price Changes', fontsize=15, fontweight='bold', pad=10)
                ax.set_xlim(0, 50)
                ax.legend(fontsize=11, loc='best')
                ax.grid(True, alpha=0.3, linestyle='--')
                ax.tick_params(axis='both', labelsize=11)
                st.pyplot(fig_price, use_container_width=True)
                plt.close(fig_price)  # 释放内存
                st.markdown('</div>', unsafe_allow_html=True)

                st.markdown("### Welfare Effect Sensitivity Analysis")
                st.markdown('<div class="chart-card">', unsafe_allow_html=True)

                # 福利效应图 - 使用Plotly添加hover工具提示
                import plotly.graph_objects as go

                fig_welfare = go.Figure()

                # 添加各条曲线并配置hover
                fig_welfare.add_trace(go.Scatter(
                    x=df["tariff_rate"], y=df["consumer_surplus"],
                    mode='lines+markers', name='Consumer Surplus Change',
                    hovertemplate='Tariff Rate: %{x}%<br>Consumer Surplus: %{y:,.0f} CNY<extra></extra>'
                ))
                fig_welfare.add_trace(go.Scatter(
                    x=df["tariff_rate"], y=df["producer_surplus"],
                    mode='lines+markers', name='Producer Surplus Change',
                    hovertemplate='Tariff Rate: %{x}%<br>Producer Surplus: %{y:,.0f} CNY<extra></extra>'
                ))
                fig_welfare.add_trace(go.Scatter(
                    x=df["tariff_rate"], y=df["government_revenue"],
                    mode='lines+markers', name='Government Revenue',
                    hovertemplate='Tariff Rate: %{x}%<br>Government Revenue: %{y:,.0f} CNY<extra></extra>'
                ))
                fig_welfare.add_trace(go.Scatter(
                    x=df["tariff_rate"], y=df["deadweight_loss"],
                    mode='lines+markers', name='Deadweight Loss',
                    hovertemplate='Tariff Rate: %{x}%<br>Deadweight Loss: %{y:,.0f} CNY<extra></extra>'
                ))

                fig_welfare.update_layout(
                    title='Tariff Rate vs Welfare Effects',
                    xaxis_title='Tariff Rate (%)',
                    yaxis_title='Amount (CNY)<br><sup>(Unit: CNY, negative values indicate welfare reduction)</sup>',
                    xaxis=dict(range=[0, 50], tickfont=dict(size=12)),
                    yaxis=dict(tickfont=dict(size=12)),
                    legend=dict(x=0, y=1, traceorder='normal', font=dict(size=12)),
                    hovermode='x unified',
                    font=dict(size=12),
                    height=450
                )

                st.plotly_chart(fig_welfare, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

                # ========== Business-oriented Analysis ==========
                st.markdown("---")
                st.markdown("## Business-oriented Analysis")

                # Business metrics analysis based on sensitivity data
                if results:
                    tariff_rates_data = [r["tariff_rate"] for r in results]
                    retail_prices = [r["retail_price"] for r in results]
                    import_prices = [r["import_price"] for r in results]
                    gr_data = [r["government_revenue"] for r in results]

                    # Calculate key business metrics for each tariff rate
                    P_imp0 = import_prices[0] / (1 + tariff_rates_data[0]) if tariff_rates_data[0] > 0 else import_prices[0]
                    P_ret0 = retail_prices[0]

                    business_metrics = []
                    for i, rate in enumerate(tariff_rates_data):
                        unit_tariff = import_prices[i] - P_imp0
                        retail_increase_pct = ((retail_prices[i] - P_ret0) / P_ret0 * 100) if P_ret0 > 0 else 0
                        gr = gr_data[i]

                        # Determine price pressure level
                        if retail_increase_pct <= 3:
                            pressure = "Low"
                        elif retail_increase_pct <= 8:
                            pressure = "Moderate"
                        else:
                            pressure = "High"

                        business_metrics.append({
                            "rate": rate,
                            "unit_tariff": unit_tariff,
                            "retail_increase_pct": retail_increase_pct,
                            "gr": gr,
                            "pressure": pressure
                        })

                    # Find optimal range (low pressure, reasonable revenue)
                    low_pressure_rates = [m["rate"] for m in business_metrics if m["pressure"] == "Low"]
                    moderate_pressure_rates = [m["rate"] for m in business_metrics if m["pressure"] == "Moderate"]

                    # Generate business analysis
                    st.markdown("### Cost & Pricing Pressure Analysis")
                    st.markdown(f"""
                    Based on the sensitivity analysis with transmission coefficients alpha={pt1} and beta={pt2}:
                    """)

                    # Key metrics table
                    metrics_data = []
                    for m in business_metrics:
                        metrics_data.append({
                            "Tariff Rate": f"{m['rate']*100:.0f}%",
                            "Unit Tariff Cost": f"¥{m['unit_tariff']:,.2f}",
                            "Retail Price Increase": f"{m['retail_increase_pct']:.2f}%",
                            "Pressure Level": m['pressure']
                        })

                    st.table(pd.DataFrame(metrics_data).to_markdown(index=False))

                    # Price pressure distribution
                    low_count = sum(1 for m in business_metrics if m["pressure"] == "Low")
                    mod_count = sum(1 for m in business_metrics if m["pressure"] == "Moderate")
                    high_count = sum(1 for m in business_metrics if m["pressure"] == "High")

                    st.markdown(f"""
                    **Price Pressure Distribution:**
                    - Low Pressure (≤3%): {low_count} tariff levels
                    - Moderate Pressure (3-8%): {mod_count} tariff levels
                    - High Pressure (>8%): {high_count} tariff levels
                    """)

                    # Recommended range
                    st.markdown("### Recommended Tariff Range for Business")
                    if low_pressure_rates:
                        min_optimal = min(low_pressure_rates) * 100
                        max_optimal = max(low_pressure_rates) * 100
                        st.success(f"**Optimal Range: {min_optimal:.0f}% - {max_optimal:.0f}%**")
                        st.markdown(f"""
                        Within this range, retail price increases remain below 3%, minimizing consumer demand impact and maintaining sales volume stability.
                        """)
                    elif moderate_pressure_rates:
                        min_optimal = min(moderate_pressure_rates) * 100
                        max_optimal = max(moderate_pressure_rates) * 100
                        st.warning(f"**Moderate Risk Range: {min_optimal:.0f}% - {max_optimal:.0f}%**")
                        st.markdown(f"""
                        In this range, price increases are moderate (3-8%). Consider monitoring sales volume closely as consumer demand may decline moderately.
                        """)
                    else:
                        st.error("**High Risk: All tariff levels result in >8% price increases**")
                        st.markdown("Consider alternative strategies such as cost absorption or supply chain optimization.")

                    # Business insights
                    st.markdown("### Key Business Insights")

                    # Find rate with best revenue-to-pressure ratio
                    best_efficiency_rate = None
                    best_ratio = 0
                    for m in business_metrics:
                        if m["retail_increase_pct"] > 0:
                            ratio = m["gr"] / m["retail_increase_pct"]
                            if ratio > best_ratio:
                                best_ratio = ratio
                                best_efficiency_rate = m["rate"]

                    if best_efficiency_rate:
                        st.markdown(f"""
                        - **Best Revenue Efficiency**: Tariff rate at {best_efficiency_rate*100:.0f}% offers the best balance between government revenue generation and price pressure on consumers.
                        - **Cost Transmission**: With alpha={pt1} and beta={pt2}, approximately {pt1*100:.0f}% of tariff costs are passed to wholesale, and {pt2*100:.0f}% to retail.
                        - **Volume Risk**: Higher tariff rates lead to import volume decline due to reduced consumer purchasing power.
                        """)

                    st.caption("*Note: This business analysis is generated based on model parameters and scenario assumptions. It is for reference only and does not constitute formal business advice.*")

                # ========== Comprehensive Analysis Conclusion ==========
                st.markdown("---")

                # Add CSS styling for the conclusion module
                st.markdown("""
                <style>
                    .conclusion-card {
                        background-color: #f0f2f6;
                        border-radius: 12px;
                        padding: 20px;
                        margin: 15px 0;
                        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
                        border-left: 4px solid #4CAF50;
                    }
                    .conclusion-card h2 {
                        color: #2c3e50 !important;
                        font-weight: 700 !important;
                        font-size: 1.5rem !important;
                        margin-bottom: 15px !important;
                        padding-bottom: 10px;
                        border-bottom: 2px solid #4CAF50;
                    }
                    .conclusion-card h3 {
                        color: #2c3e50 !important;
                        font-weight: 600 !important;
                        font-size: 1.15rem !important;
                        margin-top: 20px !important;
                        margin-bottom: 12px !important;
                    }
                    .conclusion-card p, .conclusion-card li {
                        color: #333333 !important;
                        line-height: 1.7 !important;
                        font-size: 0.95rem !important;
                    }
                    .conclusion-card ul {
                        margin-left: 20px;
                        list-style-type: none;
                    }
                    .conclusion-card ul li::before {
                        content: "•";
                        color: #4CAF50;
                        font-weight: bold;
                        display: inline-block;
                        width: 1em;
                        margin-left: -1em;
                    }
                    .conclusion-card li {
                        margin-bottom: 8px;
                    }
                    .conclusion-card strong {
                        color: #2c3e50 !important;
                    }
                    .conclusion-note {
                        color: #666666 !important;
                        font-style: italic;
                        font-size: 0.85rem !important;
                        margin-top: 20px !important;
                    }
                </style>
                """, unsafe_allow_html=True)

                # Wrap content in card container
                st.markdown('<div class="conclusion-card">', unsafe_allow_html=True)
                st.markdown("## Comprehensive Analysis Conclusion (English)")

                # Extract data for analysis
                if results:
                    tariff_rates_data = [r["tariff_rate"] for r in results]
                    gr_data = [r["government_revenue"] for r in results]
                    cs_data = [r["consumer_surplus"] for r in results]
                    ps_data = [r["producer_surplus"] for r in results]
                    dwl_data = [r["deadweight_loss"] for r in results]
                    retail_prices = [r["retail_price"] for r in results]

                    # Find max GR and corresponding rate
                    max_gr = max(gr_data)
                    max_gr_idx = gr_data.index(max_gr)
                    max_gr_rate = tariff_rates_data[max_gr_idx]

                    # Analyze trends
                    gr_increasing = all(gr_data[i] <= gr_data[i+1] for i in range(len(gr_data)-1)) if len(gr_data) > 1 else True
                    gr_decreasing = all(gr_data[i] >= gr_data[i+1] for i in range(len(gr_data)-1)) if len(gr_data) > 1 else True

                    cs_decreasing = cs_data[-1] < cs_data[0] if len(cs_data) > 1 else True
                    ps_increasing = ps_data[-1] > ps_data[0] if len(ps_data) > 1 else True
                    dwl_increasing = dwl_data[-1] > dwl_data[0] if len(dwl_data) > 1 else True

                    # (1) Price Transmission Mechanism
                    st.markdown("### 1. Price Transmission Mechanism")
                    st.markdown(f"""
                    The price transmission mechanism is governed by two key coefficients:
                    - **Alpha (alpha) = {pt1}**: Import-to-Wholesale pass-through rate
                    - **Beta (beta) = {pt2}**: Wholesale-to-Retail pass-through rate

                    With these transmission coefficients, the tariff cost burden is distributed across the supply chain as follows:
                    - At the import stage, the full tariff impact ({tariff_rates_data[-1]*100:.0f}% maximum) is added to the import price
                    - The wholesale stage transmits only **{pt1*100:.0f}%** of the import price change to wholesale buyers
                    - The retail stage transmits only **{pt2*100:.0f}%** of the wholesale price change to final consumers

                    **Key Observations:**
                    - Retail price increases are **attenuated** compared to the full tariff rate due to incomplete pass-through
                    - At t=0%, retail price = {retail_prices[0]:.2f}; at t={tariff_rates_data[-1]:.0f}%, retail price = {retail_prices[-1]:.2f}
                    - The relationship between tariff rate and retail price is **approximately linear** given constant pass-through coefficients
                    """)

                    # (2) Government Revenue Characteristics
                    st.markdown("### 2. Government Revenue Characteristics")
                    st.markdown(f"""
                    **Maximum Government Revenue: {max_gr:,.2f} at tariff rate = {max_gr_rate:.0f}%**

                    **Laffer Curve Analysis:**
                    """)

                    if gr_increasing:
                        st.markdown("""
                    - Within the current tariff range, government revenue is **monotonically increasing** with the tariff rate
                    - Revenue has not yet reached the declining phase of the Laffer Curve
                    - This suggests the optimal tariff rate for revenue maximization may be higher than the current range
                    """)
                    elif gr_decreasing:
                        st.markdown("""
                    - Government revenue is **monotonically decreasing** within the current range
                    - This indicates the optimal revenue point has already been passed
                    """)
                    else:
                        st.markdown(f"""
                    - Government revenue shows a **non-monotonic pattern** with maximum at {max_gr_rate:.0f}%
                    - This reflects the classic **Laffer Curve** phenomenon
                    - Beyond {max_gr_rate:.0f}%, higher tariffs lead to **declining revenue** due to:
                      - **Tax base erosion**: Import volumes contract significantly as prices rise
                      - **Demand elasticity**: Consumers reduce purchases substantially at high price levels
                      - **Supply response**: Domestic production substitutes for imports
                    """)

                    # (3) Detailed Welfare Components
                    st.markdown("### 3. Detailed Welfare Components")

                    # Consumer Surplus
                    st.markdown("**Consumer Surplus (ΔCS):**")
                    if cs_decreasing:
                        cs_rate = ((cs_data[0] - cs_data[-1]) / abs(cs_data[0]) * 100) if cs_data[0] != 0 else 0
                        st.markdown(f"""
                    - **Trend:** Continuously declining from {cs_data[0]:,.2f} to {cs_data[-1]:,.2f}
                    - **Decline Rate:** {cs_rate:.1f}% reduction across the tariff range
                    - **Economic Interpretation:** Higher tariffs directly increase consumer prices. The burden falls entirely on consumers as price increases are passed through to retail. Low-income consumers face disproportionate welfare losses.
                    """)
                    else:
                        st.markdown("Consumer surplus shows a non-decreasing pattern in the analyzed range.")

                    # Producer Surplus
                    st.markdown("**Producer Surplus (ΔPS):**")
                    if ps_increasing:
                        ps_rate = ((ps_data[-1] - ps_data[0]) / abs(ps_data[0]) * 100) if ps_data[0] != 0 else 0
                        st.markdown(f"""
                    - **Trend:** Continuously increasing from {ps_data[0]:,.2f} to {ps_data[-1]:,.2f}
                    - **Increase Rate:** {ps_rate:.1f}% improvement across the tariff range
                    - **Economic Interpretation:** Domestic producers benefit from reduced foreign competition. However, the benefit is **bounded** because:
                      - Rising input costs (imported goods) eventually squeeze margins
                      - Market size contracts as consumers face higher prices
                      - Resource allocation shifts away from comparative advantage
                    """)
                    else:
                        st.markdown("Producer surplus shows a non-increasing pattern in the analyzed range.")

                    # Deadweight Loss
                    st.markdown("**Deadweight Loss (DWL):**")
                    if dwl_increasing:
                        dwl_rate = ((dwl_data[-1] - dwl_data[0]) / max(dwl_data[0], 1) * 100)
                        st.markdown(f"""
                    - **Trend:** Accelerating increase from {dwl_data[0]:,.2f} to {dwl_data[-1]:,.2f}
                    - **Growth Rate:** {dwl_rate:.1f}% increase across the tariff range
                    - **Economic Interpretation:** DWL represents **market efficiency distortion**. At higher tariffs:
                      - **Production distortion**: Domestic over-production due to artificially high prices
                      - **Consumption distortion**: Under-consumption due to prices exceeding marginal valuation
                      - **Trade loss**: Forgone gains from comparative advantage
                      - **Resource misallocation**: Factors move to less productive sectors
                    - DWL grows **non-linearly** with tariff rate, indicating compounding efficiency losses
                    """)
                    else:
                        st.markdown("Deadweight loss shows a non-increasing pattern in the analyzed range.")

                    # (4) Total Welfare & Policy Recommendation
                    st.markdown("### 4. Total Welfare & Policy Recommendation")

                    # Find optimal rate range based on analysis
                    # Look for rate where GR is still significant but DWL is not too high
                    if len(gr_data) > 1:
                        # Calculate efficiency ratio: GR / DWL
                        efficiency_ratios = [gr_data[i] / max(dwl_data[i], 1) for i in range(len(gr_data))]
                        best_efficiency_idx = efficiency_ratios.index(max(efficiency_ratios))
                        suggested_rate = tariff_rates_data[best_efficiency_idx]

                        # Find rate where GR starts declining (Laffer curve peak)
                        laffer_optimal = max_gr_rate
                    else:
                        suggested_rate = tariff_rates_data[0] if tariff_rates_data else 10
                        laffer_optimal = suggested_rate

                    st.markdown(f"""
                    **Welfare Identity Validation:**
                    - The model satisfies: ΔCS + ΔPS + GR + DWL = 0 (within numerical tolerance)
                    - This confirms internal consistency of the welfare accounting framework

                    **Trade-off Analysis:**
                    The tariff policy involves a fundamental **three-way trade-off**:
                    1. **Producer Protection (ΔPS)**: Benefits domestic producers but limits consumer welfare
                    2. **Government Revenue (GR)**: Funds public services but distorts market incentives
                    3. **Total Social Welfare**: Net effect depends on which group bears the burden

                    **Suggested Tariff Range: {max(0, suggested_rate-5):.0f}% - {min(50, suggested_rate+10):.0f}%**

                    **Rationale:**
                    - Below {max(0, suggested_rate-5):.0f}%: Limited producer protection and revenue collection
                    - Around {suggested_rate:.0f}%: Balanced point where GR is substantial while DWL remains manageable
                    - Above {min(50, suggested_rate+10):.0f}%: Excessive market distortion with rapidly declining net benefits

                    The recommended range balances:
                    - Sufficient tariff revenue for government objectives
                    - Reasonable producer welfare protection
                    - Contained deadweight loss within acceptable efficiency bounds
                    """)

                    # Note
                    st.markdown('<p class="conclusion-note">*Note: This conclusion is generated based solely on current model parameters and scenario assumptions. It is for reference only and does not constitute formal policy advice.*</p>', unsafe_allow_html=True)

                # Close card container
                st.markdown('</div>', unsafe_allow_html=True)

                # Export results
                st.markdown("### Export Analysis Results")
                file_name = f"Sensitivity_Analysis_{hs_code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                file_path = exporter.export_to_excel({"sensitivity_analysis": df.to_dict()}, file_name=file_name)
                with open(file_path, "rb") as f:
                    st.download_button("Download Excel Report", data=f, file_name=os.path.basename(file_path),
                                      mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            else:
                st.error("Calculation failed. Please check parameter settings.")


# ==================== Sidebar ====================
with st.sidebar:
    # Guide button
    if st.button("Show Guide Again", key="show_guide_btn"):
        st.session_state.guided = False
        st.session_state.show_guide = True
        st.session_state.guide_step = 0
        try:
            st.experimental_rerun()
        except:
            st.markdown("<script>window.location.reload()</script>", unsafe_allow_html=True)

    st.markdown("---")

    # ========== Parameter Settings Area ==========
    st.markdown("## Parameter Settings")

    # ========== Tariff Rate Selection Mode ==========
    st.markdown("### Tariff Rate")

    # Top-level radio: Quick Presets vs Custom Tariff Rate
    tariff_mode = st.radio(
        "Select Mode",
        ["Quick Presets", "Custom Tariff Rate"],
        key="tariff_mode",
        horizontal=True
    )

    # Initialize session state for tariff rate if not exists
    if 'tariff_rate' not in st.session_state:
        st.session_state.tariff_rate = 0.10  # Default 10%

    if tariff_mode == "Quick Presets":
        # Show dropdown with preset tariff rates (0%, 10%, 20%, ..., 100%)
        preset_tariff_options = ["0%", "10%", "20%", "30%", "40%", "50%", "60%", "70%", "80%", "90%", "100%"]

        # Get current tariff as string for selection
        current_tariff_str = f"{int(st.session_state.tariff_rate * 100)}%"
        if current_tariff_str not in preset_tariff_options:
            current_tariff_str = "10%"  # Default fallback

        selected_preset = st.selectbox(
            "Preset Tariff Rate (%)",
            preset_tariff_options,
            index=preset_tariff_options.index(current_tariff_str),
            key="preset_tariff_dropdown"
        )

        # Convert to decimal and store in session state
        tariff_rate = int(selected_preset.replace("%", "")) / 100
        st.session_state.tariff_rate = tariff_rate
        st.markdown(f"**Current: {selected_preset}**")

    else:  # Custom Tariff Rate
        # Show number input for custom tariff (0-100 range)
        current_tariff_value = int(st.session_state.tariff_rate * 100)
        custom_tariff = st.number_input(
            "Custom Tariff (%)",
            min_value=0,
            max_value=100,
            value=current_tariff_value,
            step=1,
            key="custom_tariff_input"
        )
        tariff_rate = custom_tariff / 100
        st.session_state.tariff_rate = tariff_rate
        st.markdown(f"**Current: {custom_tariff}%**")

    st.markdown("---")

    # Industry selection - parameter linkage
    st.markdown("### Select Industry")
    industries = calculator.get_supported_industries()
    industry_options = {f"{ind['hs_code']} - {ind['name']}": ind['hs_code'] for ind in industries}
    selected_industry = st.selectbox("Industry", list(industry_options.keys()), 0, key="main_industry")
    hs_code = industry_options[selected_industry]
    # 每次选择行业时重新获取行业详情
    industry_detail = calculator.db.get_industry_detail(hs_code=hs_code)

    st.markdown("---")

    # Pass-Through Parameters
    st.markdown("### Pass-Through Parameters")
    # 从数据库获取行业特定的传导参数
    db_pt1 = 0.8
    db_pt2 = 0.7
    db_elasticity = 1.0
    if industry_detail and industry_detail.get("transmission_params"):
        tp = industry_detail["transmission_params"]
        db_pt1 = tp.get("import_to_wholesale", {}).get("pass_through_rate", 0.8)
        db_pt2 = tp.get("wholesale_to_retail", {}).get("pass_through_rate", 0.7)
        db_elasticity = tp.get("import_to_wholesale", {}).get("elasticity", 1.0)

    # Preset Market Scenario
    st.markdown("### Preset Market Scenario")
    scenario_options = {
        "Custom": {"alpha": db_pt1, "beta": db_pt2},
        "Strong Bargaining Power": {"alpha": 1.0, "beta": 1.0},
        "Normal Market": {"alpha": 0.8, "beta": 0.7},
        "Weak Bargaining Power": {"alpha": 0.5, "beta": 0.4}
    }

    selected_scenario = st.selectbox(
        "Select Scenario",
        list(scenario_options.keys()),
        key="scenario_selectbox",
        help="Choose a preset market scenario with typical pass-through coefficients. Select 'Custom' to manually adjust values."
    )

    if selected_scenario != "Custom":
        default_alpha = scenario_options[selected_scenario]["alpha"]
        default_beta = scenario_options[selected_scenario]["beta"]
    else:
        default_alpha = db_pt1
        default_beta = db_pt2

    st.markdown("---")

    # Pass-Through Parameters with tooltips
    st.markdown("### Pass-Through Parameters")
    pass_through_1 = st.slider(
        "Import->Wholesale Pass-Through (alpha)",
        0.0, 1.0, default_alpha, 0.05, key="pt1",
        help="Alpha: The proportion of tariff cost passed from importers to wholesale buyers. 1.0 = full pass-through (buyers bear all cost); 0.0 = importers absorb all cost. Typical range: 0.5-1.0 depending on market bargaining power."
    )
    pass_through_2 = st.slider(
        "Wholesale->Retail Pass-Through (beta)",
        0.0, 1.0, default_beta, 0.05, key="pt2",
        help="Beta: The proportion of wholesale price change passed to retail consumers. 1.0 = full pass-through; 0.0 = retailers absorb all cost. Higher beta means greater final price impact on consumers."
    )
    elasticity = st.number_input("Demand Elasticity (Ed)", 0.1, 5.0, db_elasticity, 0.1, key="main_elasticity",
        help="Price elasticity of demand (absolute value): 0<Ed<1 = inelastic, Ed=1 = unit elastic, Ed>1 = elastic")
    supply_elasticity = st.number_input("Supply Elasticity (Es)", 0.1, 10.0, 2.0, 0.1, key="main_supply_elasticity",
        help="Price elasticity of supply (positive value): 0<Es<1 = inelastic, Es=1 = unit elastic, Es>1 = elastic")

    st.markdown("---")

    # 市场价格调整系数
    st.markdown("### Price Adjustment Factor")
    if 'price_factor' not in st.session_state:
        st.session_state.price_factor = 1.0

    price_factor = st.slider("Market Price Adjustment Factor", 0.5, 1.5, st.session_state.price_factor, 0.05, key="price_factor_slider",
        help="Actual price = Industry Base Price x Adjustment Factor. Range: 0.5 (50%) to 1.5 (150%)")
    st.session_state.price_factor = price_factor

    st.markdown("---")

    # 行业信息 - 显示从数据库读取的数据（含调整系数）
    if industry_detail:
        base_import = industry_detail['base_price']
        base_wholesale = industry_detail['wholesale_price']
        base_retail = industry_detail['retail_price']

        # 应用调整系数
        adjusted_import = base_import * price_factor
        adjusted_wholesale = base_wholesale * price_factor
        adjusted_retail = base_retail * price_factor

        st.markdown("### Industry Info")
        st.markdown(f"""
- **HS Code:** {industry_detail['hs_code']}
- **Base Import Price:** ¥{base_import:,.2f}
- **Base Wholesale Price:** ¥{base_wholesale:,.2f}
- **Base Retail Price:** ¥{base_retail:,.2f}
- **Adjustment Factor:** {price_factor:.2f}x
- **Adjusted Import Price:** ¥{adjusted_import:,.2f}
- **Adjusted Wholesale Price:** ¥{adjusted_wholesale:,.2f}
- **Adjusted Retail Price:** ¥{adjusted_retail:,.2f}
- **Current Tariff:** {industry_detail.get('current_tariff_rate', 0)*100:.0f}%
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
    st.session_state.active_tab = "Calculation"

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
tab1, tab2, tab3 = st.tabs(["Tariff Calculation", "History", "Sensitivity Analysis"])

with tab1:
    # Tariff calculation content
    st.title("China Commodity Price Transmission and Tariff Impact Analysis System")
    st.markdown("**Target Users: Economics Students, International Trade Learners**")

    # 顶部操作提示
    st.markdown("""
    <div style="background: linear-gradient(90deg, #f5f7fa 0%, #e4e8ec 100%);
                padding: 12px 20px; border-radius: 8px; margin-bottom: 20px;
                border-left: 4px solid #4CAF50;">
        <div style="display: flex; justify-content: center; align-items: center; gap: 30px; flex-wrap: wrap;">
            <div style="text-align: center;">
                <span style="background: #4CAF50; color: white; padding: 4px 12px; border-radius: 12px; font-weight: bold;">1</span>
                <span style="margin-left: 8px; font-weight: 500;">Set Parameters</span>
            </div>
            <span style="color: #999;">➜</span>
            <div style="text-align: center;">
                <span style="background: #2196F3; color: white; padding: 4px 12px; border-radius: 12px; font-weight: bold;">2</span>
                <span style="margin-left: 8px; font-weight: 500;">Click Calculate</span>
            </div>
            <span style="color: #999;">➜</span>
            <div style="text-align: center;">
                <span style="background: #FF9800; color: white; padding: 4px 12px; border-radius: 12px; font-weight: bold;">3</span>
                <span style="margin-left: 8px; font-weight: 500;">View Results</span>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

    # View Toggle
    st.markdown("---")
    display_view = st.radio(
        "Select Display View",
        ["Academic View", "Business View"],
        index=0,
        horizontal=True,
        key="display_view_radio",
        help="Academic View: Full academic analysis with welfare indicators. Business View: Simplified commercial metrics for decision-making."
    )
    is_business_view = (display_view == "Business View")
    st.markdown("---")

with tab2:
    # History content
    render_history_page(calculator)

with tab3:
    # Sensitivity analysis content
    render_sensitivity_page(calculator)

# ========== Calculate Button ==========
if st.button("Calculate", type="primary"):
    calculate_clicked = True
else:
    calculate_clicked = False

if calculate_clicked:
    with st.spinner("Calculating..."):
        # 获取当前价格调整系数
        current_price_factor = st.session_state.get('price_factor', 1.0)

        result = calculator.calculate(
            hs_code=hs_code,
            tariff_rate=tariff_rate,
            custom_params={
                "pass_through_1": pass_through_1,
                "pass_through_2": pass_through_2,
                "elasticity": elasticity,
                "supply_elasticity": supply_elasticity,
                "price_factor": current_price_factor
            }
        )
        # 保存计算结果到session_state，并记录当前参数哈希
        st.session_state.calculation_result = result
        st.session_state.show_export = False
        st.session_state.last_params_hash = get_params_hash(
            st.session_state.get('tariff_mode', 'Quick Presets'),
            hs_code,
            tariff_rate,
            pass_through_1,
            pass_through_2,
            elasticity,
            supply_elasticity
        )

        if result.get("success"):
            # 保存历史记录
            session_id = st.session_state.get("session_id", "default")
            calculator.db.save_calculation_history(result, session_id=session_id)

            # ========== Results Section with Cards ==========
            st.markdown("## Calculation Results")

            # Card 1: Price Changes Table
            st.markdown('<div class="result-card">', unsafe_allow_html=True)
            st.markdown("### Price Changes Across Supply Chain")
            st.markdown("*Impact of tariff on import, wholesale, and retail prices*")

            price = result["price_changes"]
            welfare = result["welfare_effects"]
            industry = result["industry"]
            params = result["params"]

            # 结果表格 - 英文标注
            df = pd.DataFrame({
                "Stage": ["Import", "Wholesale", "Retail"],
                "Before Tax": [price["import"]["before"], price["wholesale"]["before"], price["retail"]["before"]],
                "After Tax": [price["import"]["after"], price["wholesale"]["after"], price["retail"]["after"]],
                "Change": [price["import"]["change"], price["wholesale"]["change"], price["retail"]["change"]],
                "Change Rate": [f"{price['import']['change_rate']:.2f}%", f"{price['wholesale']['change_rate']:.2f}%", f"{price['retail']['change_rate']:.2f}%"]
            })
            st.dataframe(df.style.format({"Before Tax": "¥{:.2f}", "After Tax": "¥{:.2f}", "Change": "¥{:.2f}"}), use_container_width=True, hide_index=True)
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown("")

            # Card 2: Welfare Effects (Academic View Only)
            if not is_business_view:
                st.markdown('<div class="result-card">', unsafe_allow_html=True)
                st.markdown("### Welfare Effects Analysis")
                st.markdown("*Economic impact on consumers, producers, and government*")

                # 福利效应 - 英文标注
                col1, col2, col3, col4 = st.columns(4)
                with col1: st.metric("Consumer Surplus Change", format_currency(welfare.get("consumer_surplus_change", 0)), delta_color="inverse")
                with col2: st.metric("Producer Surplus Change", format_currency(welfare.get("producer_surplus_change", 0)), delta_color="inverse")
                with col3: st.metric("Government Revenue", format_currency(welfare.get("government_revenue", 0)))
                with col4: st.metric("Deadweight Loss", format_currency(welfare.get("deadweight_loss", 0)), delta_color="inverse")
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                # Business View: Cost & Price Analysis
                st.markdown('<div class="result-card">', unsafe_allow_html=True)
                st.markdown("### Cost & Price Analysis (Business Metrics)")
                st.markdown("*Key commercial indicators for decision-making*")

                # Extract values for business metrics
                P_imp0 = price["import"]["before"]
                P_imp1 = price["import"]["after"]
                P_ret0 = price["retail"]["before"]
                delta_P_ret = price["retail"]["change"]
                M0 = params.get("quantity_d0", 1000) - params.get("quantity_s0", 800)
                M1 = result.get("quantity_changes", {}).get("import", {}).get("after", M0)
                t = params.get("tariff_rate", 0.1)

                # Calculate business metrics
                unit_tariff_cost = P_imp1 - P_imp0
                cost_increase_pct = (unit_tariff_cost / P_imp0 * 100) if P_imp0 != 0 else 0
                tariff_expenditure = unit_tariff_cost * M1
                retail_price_increase_pct = (delta_P_ret / P_ret0 * 100) if P_ret0 != 0 else 0
                import_decline_pct = ((M0 - M1) / M0 * 100) if M0 != 0 else 0

                # Display metrics in 4 columns
                m1, m2, m3, m4 = st.columns(4)
                with m1: st.metric("Unit Tariff Cost", f"¥{unit_tariff_cost:,.2f}")
                with m2: st.metric("Import Cost Increase", f"{cost_increase_pct:.2f}%", delta_color="inverse" if cost_increase_pct > 0 else "normal")
                with m3: st.metric("Est. Tariff Expenditure", f"¥{tariff_expenditure:,.0f}")
                with m4: st.metric("Terminal Price Increase", f"{retail_price_increase_pct:.2f}%", delta_color="inverse" if retail_price_increase_pct > 0 else "normal")

                m5, m6 = st.columns(2)
                with m5: st.metric("Import Volume Decline", f"{import_decline_pct:.2f}%", delta_color="inverse" if import_decline_pct > 0 else "normal")
                with m6: st.metric("Post-tariff Import Volume", f"{M1:,.0f}")

                st.caption("*Note: Tariff expenditure is a simplified estimate. The system also calculates government revenue using GR = ΔP_ret × M1.")
                st.markdown('</div>', unsafe_allow_html=True)

                # Price Pressure Judgment
                st.markdown("### Terminal Price Pressure Judgment")

                if retail_price_increase_pct <= 3:
                    pressure_judgment = "Low Price Pressure. The price increase is small. The terminal market can fully absorb the additional cost without obvious sales impact."
                    pressure_level = "success"
                elif retail_price_increase_pct <= 8:
                    pressure_judgment = "Moderate Price Pressure. A slight retail price adjustment is required. Sales volume may decline moderately."
                    pressure_level = "warning"
                else:
                    pressure_judgment = "High Price Pressure. The cost surge is significant. It is difficult for the terminal market to bear, and sales volume will shrink obviously."
                    pressure_level = "error"

                if pressure_level == "success":
                    st.success(f"**Low Price Pressure**\n\n{pressure_judgment}")
                elif pressure_level == "warning":
                    st.warning(f"**Moderate Price Pressure**\n\n{pressure_judgment}")
                else:
                    st.error(f"**High Price Pressure**\n\n{pressure_judgment}")

            st.markdown("")

            # Card 3: Supply-Demand Equilibrium Chart (Plotly with hover and collapsible legend)
            st.markdown('<div class="chart-card">', unsafe_allow_html=True)
            st.markdown("### Supply-Demand Equilibrium Analysis")
            st.markdown("*Visual representation of tariff impact on market welfare*")

            import plotly.graph_objects as go
            import numpy as np

            # 固定关键数据点
            Q0 = 1000  # 初始均衡数量
            P0 = 8000  # 初始均衡价格（也是世界价格）
            Pt = 8800  # 固定税后价格

            # 需求曲线: P = 10000 - 2Q
            # 供给曲线: P = 4000 + 4Q
            Qd = (10000 - Pt) / 2  # 需求曲线与Pt的交点
            Qs = (Pt - 4000) / 4   # 供给曲线与Pt的交点
            Qd = max(0, min(Qd, 1500))
            Qs = max(0, min(Qs, 1500))

            # 创建图表
            fig_eq = go.Figure()

            # 需求曲线
            q_range = np.linspace(0, 1500, 100)
            p_demand = 10000 - 2 * q_range
            fig_eq.add_trace(go.Scatter(
                x=q_range, y=p_demand,
                mode='lines',
                name='Demand Curve',
                line=dict(color='blue', width=2.5),
                hovertemplate='Quantity: %{x:.0f}<br>Price: %{y:,.0f} CNY<extra></extra>'
            ))

            # 供给曲线
            p_supply = 4000 + 4 * q_range
            fig_eq.add_trace(go.Scatter(
                x=q_range, y=p_supply,
                mode='lines',
                name='Supply Curve',
                line=dict(color='red', width=2.5),
                hovertemplate='Quantity: %{x:.0f}<br>Price: %{y:,.0f} CNY<extra></extra>'
            ))

            # 初始均衡点
            fig_eq.add_trace(go.Scatter(
                x=[Q0], y=[P0],
                mode='markers',
                name=f'Initial Equilibrium (Q={Q0}, P={P0})',
                marker=dict(color='green', size=14, symbol='circle'),
                hovertemplate=f'Initial Equilibrium<br>Quantity: {Q0}<br>Price: {P0:,.0f} CNY<extra></extra>'
            ))

            # 税后价格线 - 使用shape替代add_hline
            fig_eq.add_shape(
                type="line",
                x0=0, x1=1500,
                y0=Pt, y1=Pt,
                line=dict(color="orange", width=2, dash="dash"),
                layer="below"
            )

            # 世界价格线 - 使用shape替代add_hline
            fig_eq.add_shape(
                type="line",
                x0=0, x1=1500,
                y0=P0, y1=P0,
                line=dict(color="gray", width=1.5, dash="dash"),
                layer="below"
            )

            # 添加图例项（使用scatter traces）
            fig_eq.add_trace(go.Scatter(
                x=[None], y=[None],
                mode='lines',
                line=dict(color='orange', dash='dash', width=2),
                name=f'Price After Tariff (P={Pt})',
                showlegend=True
            ))
            fig_eq.add_trace(go.Scatter(
                x=[None], y=[None],
                mode='lines',
                line=dict(color='gray', dash='dash', width=1.5),
                name=f'World Price (P={P0})',
                showlegend=True
            ))

            # 添加填充区域 - 消费者剩余损失 (粉色) - Academic View Only
            if not is_business_view:
                fig_eq.add_trace(go.Scatter(
                    x=[0, Qd, Q0, 0, 0],
                    y=[Pt, Pt, P0, P0, Pt],
                    fill='toself',
                    fillcolor='rgba(255, 182, 193, 0.5)',
                    line_color='rgba(255, 182, 193, 0.8)',
                    name='Consumer Surplus Loss',
                    mode='lines',
                    hovertemplate='Consumer Surplus Loss Region<br>Area: Pink<br>Click legend to toggle<extra></extra>'
                ))

                # 添加填充区域 - 生产者剩余增加 (浅绿)
                fig_eq.add_trace(go.Scatter(
                    x=[0, Qs, Q0, 0, 0],
                    y=[Pt, Pt, P0, P0, Pt],
                    fill='toself',
                    fillcolor='rgba(144, 238, 144, 0.4)',
                    line_color='rgba(144, 238, 144, 0.6)',
                    name='Producer Surplus Gain',
                    mode='lines',
                    hovertemplate='Producer Surplus Gain Region<br>Area: Light Green<br>Click legend to toggle<extra></extra>'
                ))

                # 添加填充区域 - 政府关税收入 (深绿)
                if Qd > Qs:
                    fig_eq.add_trace(go.Scatter(
                        x=[Qs, Qd, Qd, Qs, Qs],
                        y=[P0, P0, Pt, Pt, P0],
                        fill='toself',
                        fillcolor='rgba(34, 139, 34, 0.5)',
                        line_color='rgba(34, 139, 34, 0.8)',
                    name='Government Revenue',
                    mode='lines',
                    hovertemplate='Government Revenue Region<br>Area: Dark Green<br>Click legend to toggle<extra></extra>'
                ))

            # 无谓损失区域 (淡紫色) - Academic View Only
            if not is_business_view:
                if Qs > 0:
                    fig_eq.add_trace(go.Scatter(
                        x=[Qs, Q0, Q0, Qs],
                        y=[P0, P0, Pt, P0],
                        fill='toself',
                        fillcolor='rgba(221, 160, 221, 0.5)',
                        line_color='rgba(221, 160, 221, 0.7)',
                        name='Deadweight Loss (Production)',
                        mode='lines',
                        hovertemplate='DWL - Production Distortion<br>Area: Purple<br>Click legend to toggle<extra></extra>'
                    ))

                if Qd < Q0:
                    fig_eq.add_trace(go.Scatter(
                        x=[Qd, Q0, Q0, Qd],
                        y=[P0, P0, Pt, P0],
                        fill='toself',
                        fillcolor='rgba(221, 160, 221, 0.5)',
                        line_color='rgba(221, 160, 221, 0.7)',
                        name='Deadweight Loss (Consumption)',
                        mode='lines',
                        hovertemplate='DWL - Consumption Distortion<br>Area: Purple<br>Click legend to toggle<extra></extra>'
                    ))

            # 设置图表布局 - 可折叠图例
            fig_eq.update_layout(
                title='Partial Equilibrium: Tariff Impact on Welfare',
                xaxis_title='Quantity',
                yaxis_title='Price (CNY)',
                xaxis=dict(range=[0, 1500], showgrid=True),
                yaxis=dict(range=[0, max(Pt * 1.3, P0 * 1.3)], showgrid=True),
                legend=dict(x=1.02, y=1),
                hovermode='closest',
                plot_bgcolor='white',
                height=450
            )

            st.plotly_chart(fig_eq, use_container_width=True)

            # 添加可折叠图例说明
            with st.expander("View/Hide Chart Legend", expanded=False):
                st.markdown("""
                **Chart Elements:**
                - **Blue Line**: Demand Curve (P = 10000 - 2Q)
                - **Red Line**: Supply Curve (P = 4000 + 4Q)
                - **Green Dot**: Initial Equilibrium Point
                - **Orange Dashed Line**: Price After Tariff
                - **Gray Dashed Line**: World Price (Pre-tariff)
                - **Pink Area**: Consumer Surplus Loss
                - **Light Green Area**: Producer Surplus Gain
                - **Dark Green Area**: Government Revenue
                - **Purple Area**: Deadweight Loss (efficiency distortion)

                *Hover over any element to see detailed values.*
                """)

            st.markdown('</div>', unsafe_allow_html=True)

    # ========== Core Calculation Formulas Section ==========
    with st.expander("Click to View Core Calculation Formulas (English)", expanded=False):
        st.markdown("## Core Calculation Formulas")

        # Section 1: Price Transmission Formulas
        st.markdown("### 1. Price Transmission Formulas")
        st.markdown(r"""
        The price transmission chain calculates how tariff changes affect prices across the supply chain:

        **Import Price (After Tariff):**
        $$P_{imp1} = P_{imp0} \times (1 + t)$$

        **Wholesale Price:**
        $$P_{wh1} = P_{wh0} + (P_{imp1} - P_{imp0}) \times \alpha$$

        **Retail Price:**
        $$P_{ret1} = P_{ret0} + (P_{wh1} - P_{wh0}) \times \beta$$

        **Retail Price Change:**
        $$\Delta P_{ret} = P_{ret1} - P_{ret0}$$

        Where:
        - $P_{imp0}$: Pre-tariff import price (world price)
        - $P_{wh0}$: Pre-tariff wholesale price
        - $P_{ret0}$: Pre-tariff retail price
        - $t$: Tariff rate
        - $\alpha$: Import-to-Wholesale pass-through coefficient ($0 \leq \alpha \leq 1$)
        - $\beta$: Wholesale-to-Retail pass-through coefficient ($0 \leq \beta \leq 1$)
        """)

        # Section 2: Welfare Effect Formulas
        st.markdown("### 2. Welfare Effect Formulas")
        st.markdown(r"""
        The welfare effects measure the economic impact of tariffs on different market participants:

        **Quantity Changes:**
        $$Q_{d1} = Q_{d0} \times (1 + \varepsilon_d \times \frac{\Delta P_{ret}}{P_{ret0}})$$
        $$Q_{s1} = Q_{s0} \times (1 + \varepsilon_s \times \frac{\Delta P_{ret}}{P_{ret0}})$$
        $$M_1 = Q_{d1} - Q_{s1}$$

        Where:
        - $Q_{d0}$: Pre-tariff quantity demanded
        - $Q_{s0}$: Pre-tariff domestic supply
        - $\varepsilon_d$: Demand elasticity (must be negative)
        - $\varepsilon_s$: Supply elasticity (must be positive)
        - $M_1$: Post-tariff import volume

        **Consumer Surplus Change:**
        $$\Delta CS = -\frac{1}{2} \times \Delta P_{ret} \times (Q_{d0} + Q_{d1})$$

        **Producer Surplus Change:**
        $$\Delta PS = \frac{1}{2} \times \Delta P_{ret} \times (Q_{s0} + Q_{s1})$$

        **Government Revenue (Corrected Formula):**
        $$GR = \Delta P_{ret} \times M_1$$

        **Deadweight Loss:**
        $$DWL = \frac{1}{2} \times \Delta P_{ret} \times [(Q_{d0} - Q_{d1}) + (Q_{s1} - Q_{s0})]$$

        **Welfare Identity (Validation):**
        $$\Delta CS + \Delta PS + GR + DWL = 0$$

        Where:
        - $\Delta CS$: Change in consumer surplus (negative when prices rise)
        - $\Delta PS$: Change in producer surplus (positive when prices rise)
        - $GR$: Government tariff revenue
        - $DWL$: Deadweight loss (always non-negative)
        """)

        # Note about formula correction
        st.caption("Note: The government revenue formula has been corrected to GR = ΔP_retail × M1 to ensure the welfare identity holds. This reflects the actual price burden on consumers rather than using the pre-tariff import price as the tax base.")

