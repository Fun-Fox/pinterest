import asyncio
from browser_utils import init_browser, close_browser
from crawler import crawl_pinterest
from db_utils import init_db, close_db
from dotenv import load_dotenv

# 加载.env文件中的环境变量
load_dotenv()

async def main() -> None:
    # 初始化数据库
    conn = init_db()

    # 初始化浏览器
    p, browser, context, page = await init_browser()  # 接收async_playwright对象

    # 爬取 Pinterest 页面
    await crawl_pinterest(conn, page)

    # 关闭页面和上下文
    await page.close()
    await context.close()

    # 关闭浏览器
    await close_browser(p, browser)  # 传递async_playwright对象

    # 关闭数据库连接
    close_db(conn)

if __name__ == '__main__':
    asyncio.run(main())