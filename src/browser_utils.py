import os
from playwright.async_api import async_playwright
from dotenv import load_dotenv

# 加载.env文件中的环境变量
load_dotenv()

__all__ = ['parse_cookie_string', 'init_browser', 'close_browser']

def parse_cookie_string(cookie_str: str) -> list:
    """解析从浏览器复制的cookie字符串，返回Playwright所需的cookie列表"""
    cookies = []
    for pair in cookie_str.split(';'):
        if '=' in pair:
            key, value = pair.strip().split('=', 1)
            cookies.append({"name": key, "value": value, "url": "https://www.pinterest.com"})
    return cookies

async def init_browser():
    p = await async_playwright().__aenter__()  # 手动管理async_playwright的生命周期
    # 启动浏览器，根据环境变量HEADLESS决定是否启用有头模式
    headless = os.getenv('HEADLESS', 'True').lower() == 'true'
    browser = await p.chromium.launch(headless=headless)
    context = await browser.new_context()

    # 解析并设置cookies
    cookie_str = os.getenv('COOKIE_STRING')
    if cookie_str:
        cookies = parse_cookie_string(cookie_str)
        await context.add_cookies(cookies)
        print('Cookies 设置成功')
    else:
        print('未找到环境变量中的 COOKIE_STRING')

    # 打开页面
    page = await context.new_page()
    return p, browser, context, page  # 返回async_playwright对象以便后续手动关闭

async def close_browser(p, browser):
    await browser.close()
    await p.stop()  # 使用 stop() 方法关闭 async_playwright 对象
    print('浏览器和Playwright资源已关闭')