import yaml

from caption.main import chat_joy_caption
from PIL import Image
from io import BytesIO


def image_recognition(image_path, require_element):
    prompt_box = f"""
    重点识别图片中是否同时包含{require_element}元素：

    # 返回格式如下

    ```yaml
    is_include: |
        Y或N
    ```

    注意 确保：

    - is_include 的值为Y或者N。如果包含则为Y，不包含则为 N。
    	"""
    with open(image_path, "rb") as image_file:
        image_data = image_file.read()

    # 解码Base64字符串
    # 转换为PIL.Image对象
    image = Image.open(BytesIO(image_data))
    result = list(chat_joy_caption(image, prompt_box, temperature=0.6, top_p=0.9, max_new_tokens=512,
                                   log_prompt=True))
    ret = result[-1]

    yaml_str = ret.split("```yaml")[1].split("```")[0].strip()
    analysis = yaml.safe_load(yaml_str)

    return str(analysis['is_include'])
