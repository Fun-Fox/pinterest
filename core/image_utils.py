import os
from io import BytesIO
from PIL import Image
from dotenv import load_dotenv
import aiohttp
from aiohttp_socks import ProxyConnector

# 加载.env文件中的环境变量
load_dotenv()
# # 获取当前脚本的绝对路径
# current_file_path = os.path.abspath(__file__)
# # 推导项目根目录（假设项目根目录是当前脚本的祖父目录）
# project_root = os.path.dirname(os.path.dirname(current_file_path))

__all__ = ["ImageUtils"]


class ImageUtils:
    def __init__(self, proxy_url=None):
        """
        初始化 ImageUtils 类
        :param proxy_url: 代理服务器 URL（可选）
        """
        self.proxy_url = proxy_url

    async def download_and_resize_image(self, task_dir, logging, url, image_name=None):
        """
        下载并调整图片尺寸
        :param url: 图片 URL
        :param image_name: 保存的图片名称（可选）
        :return: 下载是否成功
        """
        if image_name is None:
            image_name = url.split('/')[-1]
        image_dir = task_dir
        save_path = os.path.join(image_dir, f"{image_name}")
        if os.path.exists(save_path):
            logging.info(f"图片 {image_name} 已经下载并存在")
            return True

        if self.proxy_url:
            connector = ProxyConnector.from_url(self.proxy_url)
        else:
            connector = None
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
                'Referer': 'https://www.pinterest.com/'
            }
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(url, headers=headers, timeout=10) as response:
                    if response.status == 200:
                        image_data = BytesIO(await response.read())
                        image = Image.open(image_data)

                        # if image_name is None:
                        #     image_name = url.split('/')[-1]
                        # image_dir = task_dir
                        # # print(image_dir)
                        # # if image_dir and not os.path.exists(image_dir):
                        # #     os.makedirs(image_dir)
                        # save_path = os.path.join(image_dir, f"{image_name}")
                        image.save(save_path)
                        logging.info(f"图片下载成功")
                        return True
                    else:
                        logging.error(f'下载图片失败，状态码: {response.status}')
                        return False
        except Exception as e:
            logging.error(f'下载图片时出错: {e}')
            return False

#
# if __name__ == "__main__":
#     import asyncio  # 导入 asyncio 模块


# async def main():
#     image_util = ImageUtils("http://127.0.0.1:10809")
#     await image_util.download_and_resize_image(
#         "https://i.pinimg.com/originals/bb/19/8c/bb198c05ec2c07221c7be8d5ab696694.jpg",
#     )


# asyncio.run(main())  # 使用 asyncio.run 执行异步函数
