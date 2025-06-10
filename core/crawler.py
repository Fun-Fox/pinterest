import asyncio
import time

from core.db_utils import is_image_exist, insert_image
from dotenv import load_dotenv
import os
import json

from core.image_utils import ImageUtils

# 加载.env文件中的环境变量
load_dotenv()

__all__ = ['crawl_pinterest_page']


# async def handle_response(response):
#     """
#     处理网络响应，检测特定接口是否加载完成
#     :param response: 网络响应对象
#     :param logging: 日志记录器对象
#     """
#     if 'RelatedModulesResource/get' in response.url:
#         logging.debug(f'特定接口加载完成: {response.url}')


async def crawl_pinterest_page(conn, page, logging, task_dir, pinterest_url="",collected_page_nums=10):
    """
   爬取 Pinterest 页面内容
   :param conn: 数据库连接对象
   :param page: Playwright 页面对象
   :param logging: 日志记录器对象
   :param task_dir: 任务执行记录文件夹
   """
    # 加载设置
    if pinterest_url != "":
        pinterest_url = pinterest_url

    # 打开页面
    if not page.is_closed():
        await page.goto(pinterest_url)
        logging.info('页面加载完成')
    else:
        logging.error("页面已关闭，无法导航")
        return

    css_selector = '[data-test-id="pinrep-video"]'
    # 第一次加载图片
    images_div = await page.query_selector_all(css_selector)
    if len(images_div)==0:
        images_div = await page.query_selector_all(css_selector)
        css_selector='[data-test-id="non-story-pin-image"]'

    logging.debug(f'在页面上找到 {len(images_div)} 个包含图片的 div 元素')

    await process_images(conn, images_div, logging, task_dir)

    # 滚动页面以加载更多内容
    logging.debug('开始滚动页面以加载更多内容...')
    scroll_count = collected_page_nums  # 滚动次数
    scroll_distance = int(os.getenv('SCROLL_DISTANCE', 1000))  # 滚动距离
    scroll_wait_time = int(os.getenv('SCROLL_WAIT_TIME', 5))  # 滚动等待时间

    for i in range(scroll_count):
        current_scroll_distance = scroll_distance * (i + 1)
        logging.debug(f'滚动页面到距离 {current_scroll_distance}px')
        await page.evaluate(f'window.scrollTo(0, {current_scroll_distance})')

        await asyncio.sleep(scroll_wait_time)
        # page.on('response', handle_response)

        new_images_div = await page.query_selector_all(css_selector)
        await process_images(conn, new_images_div[len(images_div):], logging, task_dir)


async def process_images(conn, images_div, logging, task_dir):
    """
    处理图片元素并保存到数据库
    :param conn: 数据库连接对象
    :param images_div: 包含图片的 div 元素列表
    :param logging: 日志记录器对象
    :param task_dir:任务文件夹
    """
    for i, div in enumerate(images_div):
        img = await div.query_selector('img')
        logging.debug(f'img {i + 1} 的链接: {img}')
        if img:
            logging.debug(f'img {i + 1} 的DOM结构: {await img.evaluate("element => element.outerHTML")}')
            srcset = await img.get_attribute('srcset')
            src = await img.get_attribute('src')

            if srcset:
                entries = srcset.split(',')
                image_urls = [entry.strip().split(' ') for entry in entries]
                max_image = image_urls[-1][0]

                row = is_image_exist(conn, image_urls[-1][0])
                image_name = image_urls[-1][0].split("/")[-1]
                if row is None:
                    for url, scale in image_urls:
                        insert_image(conn, url, task_dir, scale)
                    image_util = ImageUtils(os.getenv("PROXY_URL"))
                    logging.info(f'图片 {i + 1},尺寸最大{image_urls[-1][-1]} 的链接: {image_urls[-1][0]}')
                    await image_util.download_and_resize_image(
                        task_dir,
                        logging,
                        max_image,
                        image_name=image_name  # 使用时间戳和序号作为图片名称
                    )
                else:
                    logging.info(
                        f'图片 {image_name}\n已经在任务:“{os.path.basename(row[1])}”文件夹采集过')
            else:
                logging.debug(f'图片 {i + 1} 没有可用的srcset属性')
                row = is_image_exist(conn, src)
                image_name = src.split("/")[-1]
                if src:
                    if row is None:
                        image_util = ImageUtils(os.getenv("PROXY_URL"))
                        insert_image(conn, src, task_dir)
                        await image_util.download_and_resize_image(
                            task_dir,
                            logging,
                            src,
                            image_name=image_name  # 使用时间戳和序号作为图片名称
                        )
                    else:
                        logging.info(f'图片 {image_name}已经在任务目录“{os.path.basename(row[1])}”下载过')
                else:
                    logging.debug(f'img Dom结构：{img}')

        else:
            logging.debug(f'div {i + 1} 中没有找到 img 元素')
