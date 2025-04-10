import asyncio
import json
import logging
import os
import time
import zipfile
from datetime import datetime
import gradio as gr
from core import init_browser, close_browser, crawl_pinterest_page, init_db, close_db
from dotenv import load_dotenv
import argparse

# 加载.env文件中的环境变量
load_dotenv()

current_dir = os.path.dirname(os.path.abspath(__file__))


def get_crawler_cookie():
    """
    获取保存的爬虫 Cookie 字符串
    :return: 返回从 setting.json 文件中读取的 Cookie 字符串，如果文件不存在或没有 Cookie 信息，则返回空字符串
    """
    if os.path.exists("setting.json"):
        with open("setting.json", "r") as f:
            try:
                settings = json.load(f)
                if not settings:  # 判断 settings 是否为空字典
                    return ""
                return settings.get("COOKIE_STRING", "")
            except json.JSONDecodeError:  # 处理文件内容格式错误的情况
                return ""
    return ""


async def start_crawler(url, page_nums):
    """
    主函数，负责执行 Pinterest 图片采集任务
    :param url: Pinterest 采集页面的 URL 地址
    :param page_nums: 需要采集的页面分页数量
    :return: 返回采集到的图片列表，如果采集失败则返回 None
    """
    # 生成任务ID并创建文件夹
    task_id = time.strftime("%Y年%m月%d日%H时%M分%S秒", time.localtime(time.time()))
    task_dir = os.path.join(current_dir, os.getenv("TASK_DIR", "tasks"), task_id)

    os.makedirs(task_dir, exist_ok=True)
    # 设置日志文件路径
    log_file_path = os.path.join(task_dir, os.getenv("CRAWLER_LOG", "crawler.log"))

    logging.basicConfig(filename=log_file_path, level=os.getenv("LOG_LEVEL", "INFO"),
                        format='%(asctime)s - %(levelname)s - %(message)s', encoding='utf-8')
    logging.debug(f"日志文件路径为：{log_file_path}")
    logging.info("开始采集")

    # 加载设置
    cookie_string = get_crawler_cookie()
    if not cookie_string or not url:
        logging.info("请先设置 Cookie信息 和 数据采集URL ")
        return None

    # 初始化数据库
    conn = init_db()
    # 初始化浏览器
    p, browser, context, page = await init_browser(logging)  # 接收async_playwright对象
    logging.info("初始化浏览器完成")
    # 爬取 Pinterest 页面
    await crawl_pinterest_page(conn, page, logging, task_dir, url, page_nums)

    # 关闭页面和上下文
    await page.close()
    await context.close()

    # 关闭浏览器
    await close_browser(p, browser, logging)  # 传递async_playwright对象

    # 关闭数据库连接
    close_db(conn)

    # 读取并显示图片
    image_dir = task_dir

    if os.path.exists(image_dir):
        images = [os.path.join(image_dir, f) for f in os.listdir(image_dir) if f.endswith(('.png', '.jpg', '.jpeg'))]
        if images:
            logging.info(f"总计找到 {len(images)} 个图片 在 {os.path.basename(image_dir)}")
            if len(images) < int(os.getenv("IMAGE_PRE_VIEW_NUMS")):
                return images
            return images[:int(os.getenv("IMAGE_PRE_VIEW_NUMS"))]  # 返回任务目录和前10个图片
    logging.warning("未找到图片")
    return []


def find_available_port(start_port=7861):
    """
    查找可用的端口号
    :param start_port: 起始端口号，默认为 7861
    :return: 返回找到的第一个可用端口号
    """
    import psutil
    port = start_port
    while True:
        connections = psutil.net_connections()
        if not any(conn.laddr.port == port for conn in connections):
            return port
        port += 1


def execute_task(url, page_nums):
    """
    执行采集任务并返回结果
    :param url: Pinterest 采集页面的 URL 地址
    :param page_nums: 需要采集的页面分页数量
    :return: 返回采集到的图片列表，如果 URL 格式不正确则返回 None
    """
    # 禁用按钮
    image_button.interactive = False
    rule = ['www.pinterest.com', 'http']
    for i in rule:
        if i not in url:
            gr.Warning("请输入正确的采集页面地址")
            return
        # 执行任务
    result = asyncio.run(start_crawler(url, page_nums))
    # 启用按钮
    image_button.interactive = True
    return result


# ====== 下面全是界面逻辑 ======
def save_crawler_settings(cookie_string):
    """
    保存爬虫设置到 setting.json 文件
    :param cookie_string: 浏览器 Cookie 字符串
    :return: 保存结果信息
    """
    settings = {
        "COOKIE_STRING": cookie_string,
    }
    with open("setting.json", "w", encoding='utf-8') as file:
        json.dump(settings, file, ensure_ascii=False, indent=4)
    return "数据采集设置保存成功"


def find_latest_task_dir(task_dir):
    """
    找到 TASK_DIR 目录下时间最近的子文件夹
    :param task_dir: 任务目录路径
    :return: 最近的任务文件夹路径
    """
    if not os.path.exists(task_dir):
        return None

    # 获取所有子文件夹
    sub_dirs = [d for d in os.listdir(task_dir) if os.path.isdir(os.path.join(task_dir, d))]

    # 解析文件夹名称并找到最近的一个
    latest_dir = None
    latest_time = None
    for d in sub_dirs:
        try:
            # 解析文件夹名称（task_id）为时间戳
            dir_time = datetime.strptime(d, "%Y年%m月%d日%H时%M分%S秒")
            if latest_time is None or dir_time > latest_time:
                latest_time = dir_time
                latest_dir = d
        except ValueError:
            continue  # 忽略不符合格式的文件夹

    if latest_dir:
        return os.path.join(task_dir, latest_dir)
    return None


def read_crawler_logs():
    """
    读取并返回爬虫日志文件内容
    :return: 包含 INFO 级别日志的字符串
    """

    latest_task_dir = find_latest_task_dir(os.path.join(current_dir, os.getenv("TASK_DIR")))
    if not latest_task_dir:
        return "无任务记录"

    log_file_path = os.path.join(latest_task_dir, os.getenv("CRAWLER_LOG"))
    # log_file_path = os.path.join(current_dir, os.getenv("CRAWLER_LOG", "crawler.log"))
    if os.path.exists(log_file_path):
        with open(log_file_path, 'r', encoding='utf-8') as f:
            new_content = f.read()
            if new_content:
                info_logs = [line for line in new_content.splitlines() if 'INFO' in line]
                return '\n'.join(info_logs)
    else:
        return "未找到日志文件"


def refresh_file_explorer():
    """
    刷新文件资源管理器
    :return: 返回最新的文件列表
    """
    task_dir = os.path.join(current_dir, os.getenv("TASK_DIR", "tasks"))
    return [os.path.join(task_dir, f) for f in os.listdir(task_dir)]


def refresh_zip_files():
    """
    刷新 .zip 文件列表
    :return: 返回最新的 .zip 文件列表
    """
    zip_dir = os.getenv("ZIP_DIR", "zips")
    zip_path = os.path.join(current_dir, zip_dir)
    if not os.path.exists(zip_path):
        os.makedirs(zip_path, exist_ok=True)
    return [os.path.join(zip_path, f) for f in os.listdir(zip_path) if f.endswith('.zip')]


def zip_folder(folder_path, zip_path):
    """
    将文件夹打包为 .zip 文件
    :param folder_path: 文件夹路径
    :param zip_path: .zip 文件路径
    """
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                cname = os.path.relpath(str(file_path), str(folder_path))
                zipf.write(str(file_path), cname)


def download_folder(folder_paths):
    """
    将选中的文件夹打包为 .zip 文件并提供下载链接
    :param folder_paths: 选中的文件夹路径列表
    :return: .zip 文件路径
    """
    if not folder_paths:
        return None  # 用户未选择任何文件夹

    # 只处理第一个选中的文件夹
    folder_path = folder_paths[0]
    if not os.path.isdir(folder_path):
        return None

    # 读取环境变量指定的目录
    zip_dir = os.getenv("ZIP_DIR")
    zip_path = os.path.join(current_dir, zip_dir, f"{os.path.basename(folder_path)}.zip")
    os.makedirs(os.path.dirname(zip_path), exist_ok=True)
    zip_folder(folder_path, zip_path)
    return zip_path


if __name__ == '__main__':
    # 集成所有功能的 Gradio 界面
    # ====== 下面全是界面布局 ======
    with gr.Blocks() as app:
        # 添加全局说明区域
        gr.Markdown("""
        # Pinterest图片采集工具
        """)
        gr.Markdown("""
        ### 
        这是一个用于从Pinterest下载图片的工具。请按照以下步骤操作：
        - 在【采集设置】页面输入您的 浏览器Cookie 和 需要采集的页面地址 ，点击“保存设置”以保存您的配置。
        - 在【执行采集】页面，点击执行，等待执行成功后，左侧查看采集完成的图片样例，右侧查看执行日志
        - 在【采集任务记录】页面查看历史人物记录，并下载链接。
        """)

        with gr.Tab("采集设置"):
            gr.Markdown("""
            - 登录Pinterest 网址：https://www.pinterest.com
            - Ctrl+Shift+i 打开浏览器开发者工具
            - 切换【网络】tab，选择请求，复制Cookie
            - 粘贴Cookie 点击保存。
            """)
            with gr.Row():
                cookie_input = gr.Textbox(label="COOKIE_STRING(浏览器Cookie)", value=get_crawler_cookie, max_lines=10)
            save_output = gr.Textbox(label="保存结果")
            save_button = gr.Button("保存设置")
            save_button.click(
                fn=save_crawler_settings,
                inputs=[cookie_input],
                outputs=save_output
            )
        with gr.Tab("执行采集"):
            gr.Markdown(
                f"""
                - 输入采集页面地址
                    - 支持以下格式：
                        - https://www.pinterest.com/pin/1234567890
                        - https://www.pinterest.com
                        - https://www.pinterest.com/search/pins/?q=%E6%89%8B%E6%9C%BA&rs=rs&source_id=M9rKxgxg&eq=&etslf=820
                - 点击【执行采集】按钮，开始采集
                - 左侧可预览前{os.getenv("IMAGE_PRE_VIEW_NUMS")}张采集的图片
                - 右侧可查看采集的日志""")
            with gr.Row():
                pinterest_url = gr.Textbox(label="待采集页面URL地址", max_lines=1)
                collected_page_nums = gr.Number(label="页面采集分页数量(建议不要大于10,避免封锁账号或IP)", value=5)
            image_button = gr.Button("执行采集", interactive=True)  # 初始状态为可用
            with gr.Row():
                image_output = gr.Gallery(label="采集的图片", columns=10)
                log_output = gr.Textbox(label="采集日志", value=read_crawler_logs, lines=10, max_lines=15,
                                        every=5)  # 实时输出日志

            image_button.click(
                fn=execute_task,
                inputs=[pinterest_url, collected_page_nums],
                outputs=image_output
            )

        with gr.Tab("采集任务记录"):
            gr.Markdown("可查看已经执行的所有采集任务下载素材，支持下载")
            with gr.Row():
                with gr.Column():
                    file_explorer = gr.FileExplorer(
                        label="已经执行任务-执行记录文件夹（以执行开始时间命名）",
                        glob="**/*",  # 匹配所有文件和文件夹
                        root_dir=os.path.join(current_dir, os.getenv("TASK_DIR")),  # 设置根目录为 TASK_DIR
                        every=1,
                        height=300,
                    )
                    refresh_btn = gr.Button("刷新任务目录")


                    def update_file_explorer():
                        return gr.FileExplorer(root_dir="")


                    def update_file_explorer_2():
                        return gr.FileExplorer(root_dir=os.path.join(current_dir, os.getenv("TASK_DIR")))


                    refresh_btn.click(update_file_explorer, outputs=file_explorer).then(update_file_explorer_2,
                                                                                        outputs=file_explorer)

                download_output = gr.File(label="已经完成打包,zip下载链接（已打包的可以直接下载）",
                                          value=refresh_zip_files,
                                          height=100,
                                          every=10)  # 实时刷新 .zip 文件列表
            download_button = gr.Button("选中其中1个文件夹进行打包")

            download_button.click(
                fn=download_folder,  # 调用下载函数
                inputs=file_explorer,  # 获取选中的文件夹路径
                outputs=download_output  # 提供下载链接
            )

        # 使用 argparse 解析命令行参数
        parser = argparse.ArgumentParser()
        parser.add_argument('--port', type=int, default=7861, help='Gradio 应用监听的端口号')
        args = parser.parse_args()

        # 启动 Gradio 界面
        app.launch(share=False, allowed_paths=[os.getenv("TASK_DIR", "tasks")], server_port=args.port)
