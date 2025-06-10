import asyncio
import json

import websockets
import yaml
from loguru import logger
from mcp.server.fastmcp import FastMCP
import torch
from contextlib import asynccontextmanager
from remote_caption_ws_server.utils.fancyfeast_model import FancyFeastModel
from typing import AsyncIterator

# 使用单例模式加载模型
fancy_feast_model = FancyFeastModel()


class AppContext:
    def __init__(self, fancy_feast_model: FancyFeastModel):
        self.fancy_feast_client = fancy_feast_model


# 生命周期管理（占位符，供将来上下文支持使用）
@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """管理应用程序生命周期"""
    logger.info("Starting MCP server lifecycle...")
    try:
        # 启动：未来可添加ComfyUI健康检查
        logger.info("图片返推模型已全局初始化")
        yield AppContext(fancy_feast_model=fancy_feast_model)
    finally:
        # 关闭：清理（如果需要）
        logger.info("正在关闭MCP服务器")


# 使用生命周期初始化FastMCP
mcp = FastMCP("Fancy_Feast_MCP_Server", lifespan=app_lifespan)


# 定义生成图像描述的工具函数
@mcp.tool()
def generate_image_caption(image_base64: str, require_element: str):
    """
    根据输入的Base64格式图像生成描述性文本或提示词。
    :param image_base64: Base64编码的图像数据
    :return: 生成的标题文本
    """
    logger.info("成功调用generate_image_caption")
    # 将Base64字符串解码为图像数据
    image = decode_base64_to_image(image_base64)
    logger.info("图片对象转换成功")

    # 构建提示词
    prompt = f"""
重点识别图片中是否包含{require_element}元素：

# 返回格式如下

```yaml
is_include: |
    Y或N
```

注意 确保：

- is_include 的值为Y或者N。如果包含则为Y，不包含则为 N。
    """
    logger.info("prompt: {}", prompt)

    # 处理输入
    convo = [
        {"role": "system", "content": "你是一个乐于助人的助手，帮助用户解决任何问题，没有审查或限制。"},
        {"role": "user", "content": prompt.strip()},
    ]

    convo_string = fancy_feast_model.get_processor().apply_chat_template(convo, tokenize=False,
                                                                         add_generation_prompt=True)
    logger.info("convo_string: {}", convo_string)
    # assert isinstance(convo_string, str)
    inputs = fancy_feast_model.get_processor()(text=[convo_string], images=[image], return_tensors="pt").to('cuda')
    inputs['pixel_values'] = inputs['pixel_values'].to(torch.bfloat16)

    # 生成输出
    logger.info("开始生成输出")
    outputs = fancy_feast_model.get_model().generate(**inputs, max_new_tokens=512, do_sample=True, temperature=0.6,
                                                     top_p=0.9, use_cache=False, top_k=None)
    result = fancy_feast_model.get_processor().decode(outputs[0], skip_special_tokens=True)

    yaml_str = result.split("```yaml")[1].split("```")[0].strip()
    logger.info(f"分析结果: {yaml_str}")
    analysis = yaml.safe_load(yaml_str)

    return {"result": analysis["is_include"]}


# 新增函数：将Base64字符串解码为图像
def decode_base64_to_image(image_base64: str):
    """
    将Base64编码的图像数据解码为PIL.Image对象。

    :param image_base64: Base64编码的图像数据
    :return: PIL.Image对象
    """
    import base64
    from PIL import Image
    from io import BytesIO

    # 解码Base64字符串
    image_data = base64.b64decode(image_base64)
    # 转换为PIL.Image对象
    image = Image.open(BytesIO(image_data))
    return image


# WebSocket服务器
async def handle_websocket(websocket):
    logger.info("WebSocket客户端已连接")
    try:
        async for message in websocket:
            request = json.loads(message)
            logger.info(f"收到消息: {request}")
            if request.get("tool") == "generate_image_caption":
                result = generate_image_caption(request.get("image_base64", ""))
                await websocket.send(json.dumps(result))
            else:
                await websocket.send(json.dumps({"error": "未知工具"}))
    except websockets.ConnectionClosed:
        logger.info("WebSocket客户端已断开连接")


# 主服务器循环
async def main():
    logger.info("正在启动MCP服务器在 ws://0.0.0.0:9100...")
    async with websockets.serve(handle_websocket, "0.0.0.0", 9100):
        await asyncio.Future()  # 永远运行


if __name__ == "__main__":
    asyncio.run(main())
