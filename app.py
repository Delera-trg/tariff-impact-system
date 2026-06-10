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
    /* 主要按钮 - 更突出 */
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #3182CE 0%, #2B6CB0 100%);
        border: none;
        border-radius: 8px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        color: white;
        width: 100%;
        transition: all 0.2s ease;
        box-shadow: 0 2px 8px rgba(49,130,206,0.3);
    }

    div.stButton > button[kind="primary"]:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(49,130,206,0.4);
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
def get_params_hash(preset, hs_code, tariff_rate, pt1, pt2, elasticity):
    """生成参数哈希，用于检测参数变化"""
    import hashlib
    params_str = f"{preset}|{hs_code}|{tariff_rate}|{pt1}|{pt2}|{elasticity}"
    return hashlib.md5(params_str.encode()).hexdigest()

# 检测参数变化，清除缓存
current_params_hash = get_params_hash(
    st.session_state.get('tariff_mode', 'Quick Presets'),
    hs_code if 'hs_code' in dir() else '',
    st.session_state.get('tariff_rate', 0),
    st.session_state.get('pt1', 0.8),
    st.session_state.get('pt2', 0.7),
    st.session_state.get('elasticity', 1.0)
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
        st.info("No calculation history found")
        st.markdown("Please run a tariff impact calculation first. The system will automatically save your history.")
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


# ==================== Sensitivity Analysis Page ====================
def render_sensitivity_page(calculator):
    """Render sensitivity analysis page"""
    st.markdown("## Sensitivity Analysis")
    st.markdown("Analyze the impact of different tariff rates on prices and welfare effects")

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

    pass_through_1 = st.slider("Import->Wholesale Pass-Through", 0.0, 1.0, db_pt1, 0.05, key="pt1",
        help="Tariff cost transfer ratio: 1 = complete transfer to buyers, 0 = importer bears all costs")
    pass_through_2 = st.slider("Wholesale->Retail Pass-Through", 0.0, 1.0, db_pt2, 0.05, key="pt2",
        help="Tariff cost transfer ratio from wholesale to retail")
    elasticity = st.number_input("Demand Elasticity (Ed)", 0.1, 5.0, db_elasticity, 0.1, key="main_elasticity",
        help="Price elasticity of demand (absolute value): 0<Ed<1 = inelastic, Ed=1 = unit elastic, Ed>1 = elastic")

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

with tab2:
    # History content
    render_history_page(calculator)

with tab3:
    # Sensitivity analysis content
    render_sensitivity_page(calculator)

# ========== Calculate Button ==========
st.markdown("---")
st.markdown('<div class="result-card">', unsafe_allow_html=True)
col_calc1, col_calc2, col_calc3 = st.columns([1, 2, 1])
with col_calc2:
    st.markdown("### Ready to Analyze")
    st.markdown("*Click the button below to run the tariff impact calculation*")
    calculate_clicked = st.button("Calculate Tariff Impact", type="primary", use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

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
            elasticity
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

            # Card 2: Welfare Effects
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

            st.markdown("")

            # Card 3: Supply-Demand Equilibrium Chart
            st.markdown('<div class="chart-card">', unsafe_allow_html=True)
            st.markdown("### Supply-Demand Equilibrium Analysis")
            st.markdown("*Visual representation of tariff impact on market welfare*")
            import matplotlib.pyplot as plt
            import numpy as np

            # 固定关键数据点
            Q0 = 1000  # 初始均衡数量
            P0 = 8000  # 初始均衡价格（也是世界价格）
            Pt = 8800  # 固定税后价格
            Pw = P0  # 世界价格

            # 需求曲线: P = 10000 - 2Q
            # 供给曲线: P = 4000 + 4Q
            Qd = (10000 - Pt) / 2  # 需求曲线与Pt的交点
            Qs = (Pt - 4000) / 4   # 供给曲线与Pt的交点

            # 确保Qd和Qs在合理范围内
            Qd = max(0, min(Qd, 1500))
            Qs = max(0, min(Qs, 1500))

            fig_eq, ax_eq = plt.subplots(figsize=(12, 7))

            # 绘制供需曲线
            q_range = np.linspace(0, 1500, 100)
            # 需求曲线: P = 10000 - 2Q
            p_demand = 10000 - 2 * q_range
            # 供给曲线: P = 4000 + 4Q
            p_supply = 4000 + 4 * q_range

            ax_eq.plot(q_range, p_demand, 'b-', label='Demand Curve', linewidth=2.5)
            ax_eq.plot(q_range, p_supply, 'r-', label='Supply Curve', linewidth=2.5)

            # 初始均衡点
            ax_eq.axvline(x=Q0, color='gray', linestyle='--', alpha=0.5)
            ax_eq.axhline(y=P0, color='gray', linestyle='--', alpha=0.5)
            ax_eq.plot(Q0, P0, 'go', markersize=12, label=f'Initial Equilibrium (Q={Q0}, P={P0})')

            # 税后价格线
            ax_eq.axhline(y=Pt, color='orange', linestyle='--', linewidth=2.5, label=f'Price After Tariff (P={Pt})')

            # 【1. 消费者剩余损失 Consumer Surplus Loss（粉色）】
            # 区域: (0, Pt) → (Qd, Pt) → (Q0, P0) → (0, P0) → (0, Pt)
            cs_polygon = plt.Polygon([
                [0, Pt],
                [Qd, Pt],
                [Q0, P0],
                [0, P0],
                [0, Pt]
            ], alpha=0.4, color='pink', label='Consumer Surplus Loss')
            ax_eq.add_patch(cs_polygon)

            # 【2. 生产者剩余增加 Producer Surplus Gain（浅绿）】
            # 区域: (0, Pt) → (Qs, Pt) → (Q0, P0) → (0, P0) → (0, Pt)
            ps_polygon = plt.Polygon([
                [0, Pt],
                [Qs, Pt],
                [Q0, P0],
                [0, P0],
                [0, Pt]
            ], alpha=0.3, color='lightgreen', label='Producer Surplus Gain')
            ax_eq.add_patch(ps_polygon)

            # 【3. 政府关税收入 Government Revenue（深绿）矩形】
            # 区域: (Qs, 8000) → (Qd, 8000) → (Qd, 8800) → (Qs, 8800)
            if Qd > Qs:
                gov_rect = plt.Polygon([
                    [Qs, P0],
                    [Qd, P0],
                    [Qd, Pt],
                    [Qs, Pt],
                    [Qs, P0]
                ], alpha=0.5, color='darkgreen', label='Government Revenue')
                ax_eq.add_patch(gov_rect)

            # 【4. 无谓损失 Deadweight Loss（淡紫色，两个三角形）】
            # 左侧生产扭曲损失: (Qs, 8000) → (Qs, 8800) → (1000, 8000)
            if Qs > 0:
                dwl1_polygon = plt.Polygon([
                    [Qs, P0],
                    [Qs, Pt],
                    [Q0, P0],
                    [Qs, P0]
                ], alpha=0.4, color='plum', label='Deadweight Loss')
                ax_eq.add_patch(dwl1_polygon)

            # 右侧消费扭曲损失: (Qd, 8000) → (Qd, 8800) → (1000, 8000)
            if Qd < Q0:
                dwl2_polygon = plt.Polygon([
                    [Qd, P0],
                    [Qd, Pt],
                    [Q0, P0],
                    [Qd, P0]
                ], alpha=0.4, color='plum')
                ax_eq.add_patch(dwl2_polygon)

            # 放大字体
            ax_eq.set_xlabel('Quantity', fontsize=14, fontweight='bold')
            ax_eq.set_ylabel('Price (CNY)', fontsize=14, fontweight='bold')
            ax_eq.set_title('Partial Equilibrium: Tariff Impact on Welfare', fontsize=16, fontweight='bold', pad=15)
            ax_eq.legend(loc='upper right', fontsize=11, framealpha=0.9)
            ax_eq.grid(True, alpha=0.3, linestyle='--')
            ax_eq.set_xlim(0, 1500)
            ax_eq.set_ylim(0, max(Pt * 1.3, P0 * 1.3))

            # 调整刻度字体大小
            ax_eq.tick_params(axis='both', labelsize=12)

            st.pyplot(fig_eq, use_container_width=True)
            plt.close(fig_eq)
            st.markdown('</div>', unsafe_allow_html=True)

