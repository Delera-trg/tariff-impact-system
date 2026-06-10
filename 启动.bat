@echo off
echo ========================================
echo    关税冲击测算系统 启动中...
echo ========================================
echo.

pip install streamlit pandas openpyxl matplotlib -q 2>nul

streamlit run app.py --server.port 8501
