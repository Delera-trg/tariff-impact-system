# Test Plotly compatibility
import plotly.graph_objects as go
import numpy as np

Q0 = 1000
P0 = 8000
Pt = 8800

fig = go.Figure()

# 添加曲线
q_range = np.linspace(0, 1500, 100)
fig.add_trace(go.Scatter(x=q_range, y=10000-2*q_range, mode='lines', name='Demand'))

# 添加shape
fig.add_shape(type="line", x0=0, x1=1500, y0=Pt, y1=Pt,
              line=dict(color="orange", width=2, dash="dash"), layer="below")

# 简化布局
fig.update_layout(
    title='Test',
    xaxis_title='X',
    yaxis_title='Y',
    height=400
)

print("Plotly test: OK")
