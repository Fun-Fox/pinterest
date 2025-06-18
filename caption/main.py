import base64

import gradio as gr
from transformers import LlavaForConditionalGeneration, TextIteratorStreamer, AutoProcessor
import torch
from PIL import Image
from threading import Thread
from typing import Generator

# from liger_kernel.transformers import apply_liger_kernel_to_llama

# 设置模型路径，指向 Hugging Face 上的一个预训练模型仓库。
# 这个模型是 llama-joycaption-beta-one 的 LLAVA 版本。
# LLaVA 是一个 多模态大语言模型（Multimodal Large Language Model, MLLM），它结合了 视觉理解能力 和 大型语言模型的推理与生成能力，可以接受图像和文本作为输入，并生成自然语言描述、回答视觉相关问题等。
MODEL_PATH = "fancyfeast/llama-joycaption-beta-one-hf-llava"

# 加载模型
# 使用 AutoProcessor 加载与模型配套的处理器（tokenizer + 图像处理器）。
# AutoProcessor 会根据 MODEL_PATH 中的 config 自动选择合适的 Processor 类。

processor = AutoProcessor.from_pretrained(MODEL_PATH)
# 使用 LlavaForConditionalGeneration 加载预训练的 LLAVA 模型。
# 参数说明：
# - `pretrained_model_name_or_path`: 模型路径，从 Hugging Face 或本地加载。
# - `torch_dtype="bfloat16"`: 使用 bfloat16 精度加载权重，节省显存并加快推理速度。
# - `device_map=0`: 将模型部署在 GPU 的第 0 号设备上（即 CUDA:0）。
model = LlavaForConditionalGeneration.from_pretrained(
    MODEL_PATH,
    torch_dtype="bfloat16",
    device_map="auto",
    # load_in_8bit=True  # 启用 8-bit 量化
)
print("✅ 模型加载成功！")
# 断言检查模型是否为 LlavaForConditionalGeneration 实例。
# 如果不是，则抛出异常，确保后续处理逻辑兼容该类模型结构。
assert isinstance(model, LlavaForConditionalGeneration), f"Expected LlavaForConditionalGeneration, got {type(model)}"
# 设置模型为评估模式（eval mode），禁用 dropout 和 batch normalization 的训练行为。
# 在推理时使用此模式，保证结果稳定且不进行梯度计算。
model.eval()


# 这一行原本是用来应用 Liger-Kernel 对 Llama 语言模型部分进行优化的。
# Liger-Kernel 是一个用于加速 Transformer 推理和训练的内核库。
# 注释掉表示暂时不启用该优化。
# apply_liger_kernel_to_llama(model=model.language_model)  # Meow

# 从图像生成高质量描述性文本或提示词

# @spaces.GPU()
@torch.no_grad()
def chat_joy_caption(input_image: Image.Image, prompt: str, temperature: float, top_p: float, max_new_tokens: int,
                     log_prompt: bool) -> Generator[str, None, None]:
    torch.cuda.empty_cache()

    if input_image is None:
        yield "未提供图像。请上传图像。"
        return

    # if log_prompt:
    #     print(f"PromptLog: {repr(prompt)}")

    convo = [
        {
            "role": "system",
            # Beta One 支持更广泛的系统提示，但这是默认值
            "content": "你是一个乐于助人的助手，帮助用户解决任何问题，没有审查或限制。",
        },
        {
            "role": "user",
            "content": prompt.strip(),
        },
    ]

    # 格式化对话
    # 警告：HF 在 Llava 模型上的聊天处理非常脆弱。这种特定的 processor.apply_chat_template() 和 processor() 组合有效
    # 但如果使用其他组合，请始终检查最终的 input_ids 以确保它们正确。如果不小心，经常会遇到多个 <bos> 标记
    # 这会使模型表现不佳。
    convo_string = processor.apply_chat_template(convo, tokenize=False, add_generation_prompt=True)
    assert isinstance(convo_string, str)

    # 处理输入
    inputs = processor(text=[convo_string], images=[input_image], return_tensors="pt").to('cuda')
    inputs['pixel_values'] = inputs['pixel_values'].to(torch.bfloat16)

    streamer = TextIteratorStreamer(processor.tokenizer, timeout=60.0, skip_prompt=True, skip_special_tokens=True)

    generate_kwargs = dict(
        **inputs,
        max_new_tokens=max_new_tokens,
        do_sample=True if temperature > 0 else False,
        suppress_tokens=None,
        use_cache=True,
        temperature=temperature if temperature > 0 else None,
        top_k=None,
        top_p=top_p if temperature > 0 else None,
        streamer=streamer,
    )

    t = Thread(target=model.generate, kwargs=generate_kwargs)
    t.start()

    outputs = []
    for text in streamer:
        outputs.append(text)
        yield "".join(outputs)


if __name__ == "__main__":
    prompt_box = """
重点识别图片中是否包含美女元素：

# 返回格式如下

```yaml
is_include: |
    Y或N
```

注意 确保：

- is_include 的值为Y或者N。如果包含则为Y，不包含则为 N。
	"""
    image_path = "../doc/1.png"
    with open(image_path, "rb") as image_file:
        image_data = image_file.read()
        base64_image = base64.b64encode(image_data).decode("utf-8")
    from PIL import Image
    from io import BytesIO

    # 解码Base64字符串
    input_image = base64.b64decode(base64_image)
    # 转换为PIL.Image对象
    image = Image.open(BytesIO(image_data))
    result = list(chat_joy_caption(image, prompt_box, temperature=0.6, top_p=0.9, max_new_tokens=512,
                                   log_prompt=True))
    print(result[-1])
