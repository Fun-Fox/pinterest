import aiohttp
from pathlib import Path
from io import BytesIO
from PIL import Image
from dotenv import load_dotenv
import os

# 加载.env文件中的环境变量
load_dotenv()

async def download_and_resize_image(session, url, save_path):
    """下载图片并调整尺寸"""
    try:
        # 配置请求头，模拟浏览器访问并添加 Referer
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
            'Referer': 'https://www.pinterest.com/'
        }

        # 发送请求
        async with session.get(url, headers=headers, timeout=10) as response:
            if response.status == 200:
                # 从二进制数据加载图片
                image_data = BytesIO(await response.read())
                image = Image.open(image_data)

                # 保存调整后的图片
                image.save(save_path)
                print(f"图片已下载，保存至 {save_path}")
                return True
            else:
                print(f'下载图片失败，状态码: {response.status}')
                return False
    except Exception as e:
        print(f'下载图片时出错: {e}')
        return False