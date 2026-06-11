# -*- coding: utf-8 -*-
"""测试已部署的Streamlit应用"""

from playwright.sync_api import sync_playwright
import time

def test_streamlit_app():
    """测试Streamlit应用"""

    print("=" * 60)
    print("测试关税冲击测算系统 - Streamlit Cloud")
    print("=" * 60)

    with sync_playwright() as p:
        # 启动浏览器
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = context.new_page()

        # 收集控制台消息
        console_messages = []
        console_errors = []

        def handle_console(msg):
            console_messages.append(f"[{msg.type}] {msg.text}")
            if msg.type == 'error':
                console_errors.append(msg.text)

        page.on('console', handle_console)

        # 导航到应用
        url = "https://tariff-impact-system-krok4kvcjnrlk2q8rzpbbs.streamlit.app/"
        print(f"\n1. 正在打开: {url}")

        try:
            response = page.goto(url, wait_until="networkidle", timeout=90000)
            print(f"   响应状态: {response.status}")

            # 等待页面加载
            time.sleep(5)

            # 获取页面标题
            title = page.title()
            print(f"   页面标题: {title}")

            # 检查是否需要登录
            current_url = page.url
            print(f"   当前URL: {current_url}")

            if "login" in current_url.lower():
                print("\n⚠️  应用需要登录才能访问")
                print("   这是Streamlit Cloud的认证保护")
                print("   请在浏览器中手动登录后使用")

                # 截图保存
                page.screenshot(path="app_login_required.png", full_page=True)
                print("   已保存截图: app_login_required.png")

                browser.close()
                return {
                    "status": "login_required",
                    "message": "应用需要登录"
                }

            # 检查主要UI元素
            print("\n2. 检查UI元素...")

            # 查找标题
            try:
                heading = page.locator("h1").first.text_content(timeout=10000)
                print(f"   主标题: {heading[:50] if len(heading) > 50 else heading}")
            except:
                print("   ⚠️ 未找到主标题")

            # 检查侧边栏
            try:
                sidebar = page.locator('section[data-testid="stSidebar"]')
                if sidebar.is_visible():
                    print("   ✓ 侧边栏可见")
            except Exception as e:
                print(f"   ✗ 侧边栏检查失败: {e}")

            # 检查选项卡
            try:
                tabs = page.locator('[role="tab"]').all()
                print(f"   ✓ 找到 {len(tabs)} 个选项卡")
                for tab in tabs[:5]:
                    print(f"      - {tab.text_content()}")
            except Exception as e:
                print(f"   ⚠️ 选项卡检查: {e}")

            # 检查计算按钮
            try:
                calc_button = page.locator("button:has-text('Calculate')").first
                if calc_button.is_visible():
                    print("   ✓ 计算按钮可见")
            except:
                print("   ⚠️ 计算按钮未找到")

            # 检查是否有错误
            if console_errors:
                print(f"\n3. 控制台错误 ({len(console_errors)}个):")
                for err in console_errors[:3]:
                    print(f"   - {err[:100]}")
            else:
                print("\n3. ✓ 无控制台错误")

            # 截图
            page.screenshot(path="app_screenshot.png", full_page=True)
            print("\n4. 已保存截图: app_screenshot.png")

            browser.close()

            print("\n" + "=" * 60)
            print("✓ 测试完成 - 应用可以正常访问")
            print("=" * 60)

            return {
                "status": "success",
                "title": title,
                "console_errors": len(console_errors)
            }

        except Exception as e:
            print(f"\n✗ 错误: {str(e)}")
            browser.close()

            page.screenshot(path="app_error.png", full_page=True)
            print("   已保存错误截图: app_error.png")

            return {
                "status": "error",
                "message": str(e)
            }

if __name__ == "__main__":
    result = test_streamlit_app()
    print(f"\n结果: {result}")
