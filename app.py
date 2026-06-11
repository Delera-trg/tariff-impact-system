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

# ==================== 页面隔离系统 ====================
# 页面ID常量
PAGE_TARIFF_CALC = "tariff_calculation"
PAGE_HISTORY = "history"
PAGE_SENSITIVITY = "sensitivity_analysis"

def clear_page_content(page_id):
    """清除指定页面的临时内容（History页面除外）"""
    if page_id == PAGE_HISTORY:
        # History页面保留内容和设置，不清除
        return

    if page_id == PAGE_TARIFF_CALC:
        # 清除关税计算页面的临时结果
        st.session_state.calculation_result = None
        st.session_state.show_export = False
        # 清除计算相关的一次性状态
        if 'calculate_clicked' in st.session_state:
            del st.session_state['calculate_clicked']

    elif page_id == PAGE_SENSITIVITY:
        # 清除敏感性分析页面的临时结果
        # 注意：敏感性分析的结果是在函数内部动态生成的，不需要额外清除
        pass

def init_session_state():
    """初始化session state"""
    # 页面追踪 - 用于检测页面切换
    if 'current_page' not in st.session_state:
        st.session_state.current_page = PAGE_TARIFF_CALC
    if 'last_page' not in st.session_state:
        st.session_state.last_page = None

    # 新手引导状态
    if 'guided' not in st.session_state:
        st.session_state.guided = False
    if 'show_guide' not in st.session_state:
        st.session_state.show_guide = True
    if 'guide_step' not in st.session_state:
        st.session_state.guide_step = 0

    # 计算结果（页面级隔离）
    if 'calculation_result' not in st.session_state:
        st.session_state.calculation_result = None
    if 'show_export' not in st.session_state:
        st.session_state.show_export = False

    # 会话ID
    if 'session_id' not in st.session_state:
        import uuid
        st.session_state.session_id = str(uuid.uuid4())

    # 活跃标签页
    if 'active_tab' not in st.session_state:
        st.session_state.active_tab = "Calculation"

    # 统一管理税率参数（全局参数，跨页面共享）
    if 'tariff_rate' not in st.session_state:
        st.session_state.tariff_rate = 0.10  # 默认10%
    if 'current_preset' not in st.session_state:
        st.session_state.current_preset = "Custom"

init_session_state()

# 检测页面切换并清除旧页面的临时内容
def handle_page_change(new_page):
    """检测页面变化并处理页面隔离"""
    last = st.session_state.get('last_page')

    if last is not None and new_page != last:
        # 页面切换了，清除旧页面的临时内容
        clear_page_content(last)

    st.session_state.last_page = new_page
    st.session_state.current_page = new_page

# 注意：页面切换处理在标签页上下文中调用

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
        st.info("No calculation history found. Please run a calculation in the Tariff Calculation tab first.")
        return

    # Display history table - Records
    st.markdown("### Records")

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

    # View Details
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

                # Create tabs for Academic and Business views
                tab_academic, tab_business = st.tabs(["📊 ACADEMIC CONCLUSION", "💼 BUSINESS ANALYSIS"])

                with tab_academic:
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

                    # Price chart
                    st.markdown("### Price Sensitivity Analysis")
                    st.markdown('<div class="chart-card">', unsafe_allow_html=True)

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
                    plt.close(fig_price)
                    st.markdown('</div>', unsafe_allow_html=True)

                    # Welfare chart
                    st.markdown("### Welfare Effect Sensitivity Analysis")
                    st.markdown('<div class="chart-card">', unsafe_allow_html=True)

                    # Plotly welfare chart
                    import plotly.graph_objects as go
                    fig_welfare = go.Figure()
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

                    # ========== Academic Conclusion (within tab) ==========
                    st.markdown("### Comprehensive Analysis Conclusion (English)")

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
                        color: #2c3e50;
                    }
                    .conclusion-note {
                        font-size: 0.85rem;
                        color: #666;
                        font-style: italic;
                        margin-top: 15px;
                    }
                </style>
                """, unsafe_allow_html=True)

                # Generate comprehensive conclusion
                avg_price_increase = df['retail_price'].iloc[-1] - df['retail_price'].iloc[0]
                max_deadweight = df['deadweight_loss'].max() if 'deadweight_loss' in df.columns else 0
                total_gov_revenue = df['government_revenue'].sum() if 'government_revenue' in df.columns else 0
                welfare_loss_rate = (max_deadweight / total_gov_revenue * 100) if total_gov_revenue > 0 else 0

                st.markdown('<div class="conclusion-card">', unsafe_allow_html=True)
                st.markdown("### Key Findings")
                st.markdown(f"""
                <ul>
                    <li><strong>Price Impact:</strong> Retail prices increase from ¥{df['retail_price'].iloc[0]:.2f} to ¥{df['retail_price'].iloc[-1]:.2f} as tariff rates rise from {min_tariff}% to {max_tariff}%</li>
                    <li><strong>Consumer Welfare:</strong> Consumer surplus decreases by ¥{abs(df['consumer_surplus'].iloc[-1]):.0f} at {max_tariff}% tariff rate</li>
                    <li><strong>Government Revenue:</strong> Total revenue reaches ¥{total_gov_revenue:,.0f} across all tariff levels</li>
                    <li><strong>Deadweight Loss:</strong> Maximum welfare loss of ¥{max_deadweight:,.0f} represents {welfare_loss_rate:.1f}% of government revenue</li>
                </ul>
                """, unsafe_allow_html=True)

                st.markdown("### Policy Implications")
                st.markdown(f"""
                <ul>
                    <li><strong>Optimal Tariff Range:</strong> Based on the analysis, tariffs between {min_tariff}% and {min(max_tariff//3, 15)}% minimize welfare losses while generating reasonable government revenue</li>
                    <li><strong>Price Transmission:</strong> The pass-through rates (α={pt1}, β={pt2}) indicate {'high' if pt1 > 0.7 else 'moderate'} transmission of tariff costs to retail prices</li>
                    <li><strong>Elasticity Considerations:</strong> With demand elasticity of {elasticity}, consumer demand {'significantly' if elasticity > 1.5 else 'moderately'} responds to price changes</li>
                </ul>
                """, unsafe_allow_html=True)

                st.markdown("### Economic Analysis Summary")
                st.markdown(f"""
                <ul>
                    <li><strong>Efficiency:</strong> The tariff analysis reveals a typical Laffer Curve pattern where revenue initially increases then decreases as deadweight loss grows</li>
                    <li><strong>Distributional Effects:</strong> Consumers bear the majority of the tariff burden through higher prices, while producers and government share the remaining impact</li>
                    <li><strong>Policy Recommendation:</strong> A balanced approach targeting tariff rates that maximize revenue efficiency while limiting consumer welfare loss is recommended</li>
                </ul>
                """, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

                st.markdown('<p class="conclusion-note">*Note: This conclusion is generated based solely on current model parameters and scenario assumptions. It is for reference only and does not constitute formal policy advice.*</p>', unsafe_allow_html=True)

                # Export button for Academic
                st.markdown("### Export Academic Results")
                col1, col2 = st.columns([3, 1])
                with col1:
                    file_name = f"Sensitivity_Analysis_Academic_{hs_code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                with col2:
                    st.download_button(
                        label="📥 Export to Excel",
                        data=exporter.export_to_excel({"sensitivity_analysis": df.to_dict()}, file_name=file_name),
                        file_name=f"{file_name}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="sensitivity_academic_export"
                    )

                # ========== BUSINESS ANALYSIS TAB ==========
                with tab_business:
                    tariff_rates_data = [r["tariff_rate"] for r in results]
                    retail_prices = [r["retail_price"] for r in results]
                    import_prices = [r["import_price"] for r in results]
                    gr_data = [r["government_revenue"] for r in results]

                    P_imp0 = import_prices[0] / (1 + tariff_rates_data[0]) if tariff_rates_data[0] > 0 else import_prices[0]
                    P_ret0 = retail_prices[0]

                    business_metrics = []
                    for i, rate in enumerate(tariff_rates_data):
                        unit_tariff = import_prices[i] - P_imp0
                        retail_increase_pct = ((retail_prices[i] - P_ret0) / P_ret0 * 100) if P_ret0 > 0 else 0
                        gr = gr_data[i]

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
                    st.markdown(f"Based on the sensitivity analysis with transmission coefficients α={pt1} (Import→Wholesale) and β={pt2} (Wholesale→Retail):")

                    # Key metrics table
                    metrics_data = []
                    for m in business_metrics:
                        metrics_data.append({
                            "Tariff Rate": f"{m['rate']*100:.0f}%",
                            "Unit Tariff Cost": f"¥{m['unit_tariff']:,.2f}",
                            "Retail Price Increase": f"{m['retail_increase_pct']:.2f}%",
                            "Pressure Level": m['pressure']
                        })

                    st.dataframe(pd.DataFrame(metrics_data), use_container_width=True, hide_index=True)

                    # Price pressure distribution
                    low_count = sum(1 for m in business_metrics if m["pressure"] == "Low")
                    mod_count = sum(1 for m in business_metrics if m["pressure"] == "Moderate")
                    high_count = sum(1 for m in business_metrics if m["pressure"] == "High")

                    st.markdown(f"**Price Pressure Distribution:** Low (≤3%): {low_count} | Moderate (3-8%): {mod_count} | High (>8%): {high_count}")

                    # Recommended range
                    st.markdown("### Recommended Tariff Range for Business")
                    if low_pressure_rates:
                        min_optimal = min(low_pressure_rates) * 100
                        max_optimal = max(low_pressure_rates) * 100
                        st.success(f"**Optimal Range: {min_optimal:.0f}% - {max_optimal:.0f}%**")
                        st.markdown("Within this range, retail price increases remain below 3%.")
                    elif moderate_pressure_rates:
                        min_optimal = min(moderate_pressure_rates) * 100
                        max_optimal = max(moderate_pressure_rates) * 100
                        st.warning(f"**Moderate Risk Range: {min_optimal:.0f}% - {max_optimal:.0f}%**")
                    else:
                        st.error("**High Risk: All tariff levels result in >8% price increases**")

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
                        st.markdown(f"- **Best Revenue Efficiency**: {best_efficiency_rate*100:.0f}% offers the best balance between revenue and price pressure.")
                        st.markdown(f"- **Cost Transmission**: {pt1*100:.0f}% (import→wholesale), {pt2*100:.0f}% (wholesale→retail)")

                    st.caption("*Note: This business analysis is for reference only.")

                    # Export button for Business
                    st.markdown("### Export Business Results")
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        file_name_biz = f"Sensitivity_Analysis_Business_{hs_code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    with col2:
                        st.download_button(
                            label="📥 Export to Excel",
                            data=exporter.export_to_excel({"sensitivity_analysis": df.to_dict()}, file_name=file_name_biz),
                            file_name=f"{file_name_biz}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key="sensitivity_business_export"
                        )

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
    # 关税计算页面 - 处理页面切换并清除旧页面内容
    handle_page_change(PAGE_TARIFF_CALC)
    # 关税计算内容
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

    # Calculate Button - inside tab1 only
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
                # ... (rest of calculation results)

with tab2:
    # History页面 - 保持当前页面状态，不清除内容
    handle_page_change(PAGE_HISTORY)
    # History content
    render_history_page(calculator)

with tab3:
    # 敏感性分析页面 - 处理页面切换
    handle_page_change(PAGE_SENSITIVITY)
    # Sensitivity analysis content
    render_sensitivity_page(calculator)

