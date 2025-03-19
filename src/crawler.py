from src.db_utils import is_image_exist, insert_image
import asyncio
from db_utils import is_image_exist, insert_image
from dotenv import load_dotenv
import os

# 加载.env文件中的环境变量
load_dotenv()


async def on_response(response):
    """监听网络响应，检测特定接口是否加载完成"""
    if 'RelatedModulesResource/get' in response.url:
        print(f'特定接口加载完成: {response.url}')
        # 在这里可以执行接口加载完成后的操作


async def crawl_pinterest(conn, page):
    # 打开页面
    # 确保浏览器和页面未关闭
    if not page.is_closed():
        pinterest_url = os.getenv('PINTEREST_URL', 'https://www.pinterest.com/pin/819655200967018689/')
        await page.goto(pinterest_url)
        print('页面加载完成')
    else:
        print("页面已关闭，无法导航")

    # 第一次加载图片
    images_div = await page.query_selector_all('[data-test-id="pinrep-video"]')
    print(f'在页面上找到 {len(images_div)} 个包含图片的 div 元素')

    await process_images(conn, images_div)

    # 滚动页面以加载更多内容
    print('开始滚动页面以加载更多内容...')
    scroll_count = int(os.getenv('SCROLL_COUNT', 3))  # 滚动次数
    scroll_distance = int(os.getenv('SCROLL_DISTANCE', 1000))  # 滚动距离
    scroll_wait_time = int(os.getenv('SCROLL_WAIT_TIME', 5))  # 滚动等待时间

    for i in range(scroll_count):
        current_scroll_distance = scroll_distance * (i + 1)  # 每次滚动距离累加
        print(f'滚动页面到距离 {current_scroll_distance}px')
        await page.evaluate(f'window.scrollTo(0, {current_scroll_distance})')

        await asyncio.sleep(scroll_wait_time)  # 等待新内容加载
        # 添加网络响应监听器
        page.on('response', on_response)

        # 重新获取所有图片元素，包括新加载的
        new_images_div = await page.query_selector_all('[data-test-id="pinrep-video"]')
        # 处理新加载的图片元素
        await process_images(conn, new_images_div[len(images_div):])

        # 更新 images_div 为最新的元素集合
        # images_div = new_images_div


async def process_images(conn, images_div):
    for i, div in enumerate(images_div):

        img = await div.query_selector('img')
        print(f'img {i + 1} 的链接: {img}')
        if img:
            # 打印img的DOM结构
            print(f'img {i + 1} 的DOM结构: {await img.evaluate("element => element.outerHTML")}')
            srcset = await img.get_attribute('srcset')
            src = await img.get_attribute('src')

            # 解析srcset属性，获取所有比例的图片链接
            if srcset:
                entries = srcset.split(',')
                image_urls = [entry.strip().split(' ') for entry in entries]
                print(f'图片 {i + 1},尺寸最大{image_urls[-1][-1]} 的链接: {image_urls[-1][0]}')
                if not is_image_exist(conn, image_urls[0][0]):
                    # 插入所有比例的图片链接
                    for url, scale in image_urls:
                        insert_image(conn, url)
            else:
                print(f'图片 {i + 1} 没有可用的srcset属性')

                if src:
                    print(f'图片 {i + 1} 的链接: {src}')
                    if not is_image_exist(conn, src):
                        insert_image(conn, src)
                else:
                    print(f'img Dom结构：{img}')
        else:
            print(f'div {i + 1} 中没有找到 img 元素')

