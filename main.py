import asyncio
import json
import logging
import os
import time

import gradio as gr
from src import init_browser, close_browser, crawl_pinterest, init_db, close_db
from dotenv import load_dotenv

# 加载.env文件中的环境变量
load_dotenv()
logging.basicConfig(filename=os.getenv('CRAWLER_LOG'), level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', encoding='utf-8')

def save_settings(cookie_string, pinterest_url):
    # 校验 URL 是否包含 /pin
    if '/pin' not in pinterest_url:
        return "采集路径不符合规格，URL 必须包含 /pin"
    
    settings = {
        "COOKIE_STRING": cookie_string,
        "PINTEREST_URL": pinterest_url
    }
    with open("setting.json", "w") as f:
        json.dump(settings, f)
    return "数据采集设置保存成功"

def load_settings():
    if os.path.exists("setting.json"):
        with open("setting.json", "r") as f:
            settings = json.load(f)
        return settings.get("COOKIE_STRING", ""), settings.get("PINTEREST_URL", "")
    return "", ""

def read_log_file():
    log_file_path = os.getenv("CRAWLER_LOG")
    if os.path.exists(log_file_path):
        with open(log_file_path, 'r',encoding='utf-8') as f:
            # 将文件指针移动到文件末尾
            f.seek(0, 2)
            while True:
                # 读取新内容
                new_content = f.read()
                if new_content:
                    # 过滤出INFO级别的日志
                    info_logs = [line for line in new_content.splitlines() if 'INFO' in line]
                    yield '\n'.join(info_logs)
                else:
                    # 如果没有新内容，等待一段时间再检查
                    time.sleep(1)
    else:
        yield "未找到日志文件"

async def main():
    # 加载设置
    cookie_string, pinterest_url = load_settings()
    if not cookie_string or not pinterest_url:
        logging.warning("请先设置COOKIE_STRING(Cookie信息) 和 PINTEREST_URL(数据采集URL) ")
        return

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

    # 读取并显示图片
    image_dir = os.getenv("IMAGE_DIR")  # 假设图片保存在images目录下
    if os.path.exists(image_dir):
        images = [os.path.join(image_dir, f) for f in os.listdir(image_dir) if f.endswith(('.png', '.jpg', '.jpeg'))]
        if images:
            logging.info(f"Found {len(images)} images in {image_dir}")
            return images[:10]  # 只返回前10个图片
    logging.warning("No images found in the specified directory.")
    return []

def find_available_port(start_port=7861):
    import socket
    port = start_port
    while True:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return port
        except OSError:
            port += 1

if __name__ == '__main__':
    # 集成所有功能的 Gradio 界面
    with gr.Blocks() as demo:
        # 添加全局说明区域
        gr.Markdown("""
        ### Pinterest 图片下载器
        这是一个用于从Pinterest下载图片的工具。请按照以下步骤操作：
        1. 在【采集设置】页面输入您的 浏览器Cookie 和 需要采集的页面地址 ，点击“保存设置”以保存您的配置。
        3. 在【执行采集】页面，点击执行，等待执行成功后，查看采集完成的图片。
        4. 在【采集日志】页面查看爬虫的运行日志。
        """)
        
        with gr.Tab("采集设置"):
            gr.Markdown("### Pinterest 采集设置")
            gr.Markdown("在此页面输入您的 浏览器Cookie 和 采集页面地址 以保存设置。")
            gr.Markdown("示例(采集页面地址)：https://www.pinterest.com/pin/819655200967018689/")
            with gr.Row():
                cookie_input = gr.Textbox(label="COOKIE_STRING(浏览器Cookie)")
                url_input = gr.Textbox(label="PINTEREST_URL(采集页面地址)")
            save_button = gr.Button("保存设置")
            save_output = gr.Textbox(label="保存结果")
            save_button.click(
                fn=save_settings,
                inputs=[cookie_input, url_input],
                outputs=save_output
            )
        with gr.Tab("执行采集"):
            gr.Markdown("### 执行采集")
            gr.Markdown("执行采集完成后, 在此页面查看前 10 张采集的图片。并显示资源下载链接")
            image_button = gr.Button("执行采集")
            image_output = gr.Gallery(label="采集的图片", columns=5)
            image_button.click(
                fn=main,
                inputs=[],
                outputs=image_output
            )
        with gr.Tab("采集日志"):
            gr.Markdown("### 采集日志")
            gr.Markdown("在此页面查看采集的最新日志。")
            log_button = gr.Button("查看日志")
            log_output = gr.Textbox(label="日志输出")
            log_button.click(
                fn=read_log_file,
                inputs=[],
                outputs=log_output
            )

    # 启动 Gradio 界面
    port = find_available_port()
    demo.launch(allowed_paths=[os.getenv("IMAGE_DIR")], server_port=port)

    # 运行爬虫
    asyncio.run(main())