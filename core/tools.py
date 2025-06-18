import yaml

from deepseek_janus_pro_7b.main import load_model, to_image_understanding


def image_understanding(image_path, require_element):
    question = f"""
    重点识别图片中是否同时包含{require_element}元素：

    # 返回格式如下

    ```yaml
    is_include: |
        Y或N
    ```

    注意 确保：

    - is_include 的值为Y或者N。如果包含则为Y，不包含则为 N。
    """
    # 模型初始化
    model_path = "deepseek-ai/Janus-Pro-7B"
    vl_chat_processor, vl_gpt, tokenizer = load_model(model_path)

    # 图像分析
    image = image_path  # 需要传入图像数据
    ret = to_image_understanding(question, image, vl_chat_processor, vl_gpt, tokenizer)

    yaml_str = ret.split("```yaml")[1].split("```")[0].strip()
    analysis = yaml.safe_load(yaml_str)

    return str(analysis['is_include'])