# Test full equilibrium chart code
import plotly.graph_objects as go
import numpy as np

Q0 = 1000
P0 = 8000
Pt = 8800

Qd = (10000 - Pt) / 2
Qs = (Pt - 4000) / 4
Qd = max(0, min(Qd, 1500))
Qs = max(0, min(Qs, 1500))

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

# 税后价格线 - 使用shape
fig_eq.add_shape(
    type="line",
    x0=0, x1=1500,
    y0=Pt, y1=Pt,
    line=dict(color="orange", width=2, dash="dash"),
    layer="below"
)

# 世界价格线 - 使用shape
fig_eq.add_shape(
    type="line",
    x0=0, x1=1500,
    y0=P0, y1=P0,
    line=dict(color="gray", width=1.5, dash="dash"),
    layer="below"
)

# 添加图例项
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

# 消费者剩余损失
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

# 生产者剩余增加
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

# 政府关税收入
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

# 无谓损失
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

# 简化布局
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

print("Full chart test: OK")
print(f"Number of traces: {len(fig_eq.data)}")
