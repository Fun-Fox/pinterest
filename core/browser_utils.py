import json
import os
from playwright.async_api import async_playwright, ProxySettings
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


async def init_browser(logging):
    p = await async_playwright().__aenter__()  # 手动管理async_playwright的生命周期
    # 启动浏览器，根据环境变量HEADLESS决定是否启用有头模式
    headless = os.getenv('HEADLESS', 'True').lower() == 'true'
    # 设置User-Agent和其他浏览器指纹相关参数
    user_agent = os.getenv('USER_AGENT',
                           'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
    # 如果代理配置存在，则加入代理设置

    proxy_settings = None
    if os.getenv('PROXY_URL'):
        proxy_settings = ProxySettings(server=os.getenv('PROXY_URL'))

    browser = await p.chromium.launch(headless=headless)
    # 设置 viewport（屏幕宽度和高度）
    viewport_width = int(os.getenv('VIEWPORT_WIDTH', 1920))  # 默认宽度为 1920
    viewport_height = int(os.getenv('VIEWPORT_HEIGHT', 1000))  # 默认高度为 1080

    context = await browser.new_context(
        user_agent=user_agent,
        proxy=proxy_settings,
        viewport={"width": viewport_width, "height": viewport_height}  # 设置 viewport
    )

    # 解析并设置cookies
    if os.path.exists("setting.json"):
        with open("setting.json", "r") as f:
            settings = json.load(f)
        cookie_str = settings.get("COOKIE_STRING")
    else:
        cookie_str = os.getenv('COOKIE_STRING')

    if cookie_str:
        cookies = parse_cookie_string(cookie_str)
        await context.add_cookies(cookies)
        logging.info('Cookies 设置成功')
    else:
        logging.warning('未找到环境变量中的 COOKIE_STRING')

    # 打开页面
    page = await context.new_page()
    return p, browser, context, page  # 返回async_playwright对象以便后续手动关闭


async def close_browser(p, browser, logging):
    await browser.close()
    await p.stop()  # 使用 stop() 方法关闭 async_playwright 对象
    logging.info('浏览器和Playwright资源已关闭')
