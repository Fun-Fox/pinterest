import os

from dotenv import load_dotenv
import asyncio
import websockets
import json

load_dotenv()


async def fancy_feast_mcp_server(payload):
    uri = os.getenv("CAPTION_MCP_SERVER_URL")
    try:
        async with websockets.connect(uri) as ws:
            print("已连接到MCP服务器")
            await ws.send(json.dumps(payload))
            response = await ws.recv()
            print("来自服务器的响应:")
            print(json.dumps(json.loads(response), indent=2, ensure_ascii=False))
            return json.loads(response)
    except Exception as e:
        print(f"WebSocket错误: {e}")


async def image_recognition(image_base64, require_element):
    payload = {
        "tool": "generate_image_caption",
        "params": json.dumps({
            "image_base64": image_base64,
            "require_element": require_element
        })
    }
    return await fancy_feast_mcp_server(payload)
