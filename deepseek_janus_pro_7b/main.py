import torch
from transformers import AutoModelForCausalLM
from janus.models import MultiModalityCausalLM, VLChatProcessor
from janus.utils.io import load_pil_images


def load_model(model_path):
    """加载并初始化模型和处理器"""
    vl_chat_processor = VLChatProcessor.from_pretrained(model_path)
    tokenizer = vl_chat_processor.tokenizer

    vl_gpt = AutoModelForCausalLM.from_pretrained(
        model_path, trust_remote_code=True
    )
    vl_gpt = vl_gpt.to(torch.bfloat16).cuda().eval()

    return vl_chat_processor, vl_gpt, tokenizer


def to_image_understanding(question, image, vl_chat_processor, vl_gpt, tokenizer):
    """分析图像并回答问题"""
    # 创建对话结构
    conversation = [
        {
            "role": "<|User|>",
            "content": f"<image_placeholder>\n{question}",
            "images": [image],
        },
        {
            "role": "<|Assistant|>",
            "content": ""
        },
    ]

    # 处理输入数据
    pil_images = load_pil_images(conversation)
    prepare_inputs = vl_chat_processor(
        conversations=conversation, images=pil_images, force_batchify=True
    ).to(vl_gpt.device)

    # 生成回答
    inputs_embeds = vl_gpt.prepare_inputs_embeds(**prepare_inputs)
    outputs = vl_gpt.language_model.generate(
        inputs_embeds=inputs_embeds,
        attention_mask=prepare_inputs.attention_mask,
        pad_token_id=tokenizer.eos_token_id,
        bos_token_id=tokenizer.bos_token_id,
        eos_token_id=tokenizer.eos_token_id,
        max_new_tokens=512,
        do_sample=False,
        use_cache=True
    )

    answer = tokenizer.decode(outputs[0].cpu().tolist(), skip_special_tokens=True)
    print(f"视觉模型回复的信息：{answer}")
    return answer


if __name__ == "__main__":
    # 模型初始化
    model_path = "deepseek-ai/Janus-Pro-7B"
    vl_chat_processor, vl_gpt, tokenizer = load_model(model_path)

    # 问题定义
    question = """
    判断图像中是否有水印
    # 输出格式如下：
    - 有水印就输出1
    - 没有水印就输出0
    """

    # 图像分析
    image = ""  # 需要传入图像数据
    to_image_understanding(question, image, vl_chat_processor, vl_gpt, tokenizer)
