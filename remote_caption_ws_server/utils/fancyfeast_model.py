from transformers import LlavaForConditionalGeneration, AutoProcessor
# from liger_kernel.transformers import apply_liger_kernel_to_llama


class FancyFeastModel:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            if not cls._instance:
                cls._instance = super(FancyFeastModel, cls).__new__(cls)
                cls._instance._load_model()
        return cls._instance

    def _load_model(self):
        # 加载模型和处理器
        # 修改：使用 Hugging Face 支持的模型名称，而非本地路径
        MODEL_PATH = "fancyfeast/llama-joycaption-beta-one-hf-llava"
        self.processor = AutoProcessor.from_pretrained(MODEL_PATH)
        self.model = LlavaForConditionalGeneration.from_pretrained(
            MODEL_PATH,
            torch_dtype="bfloat16",
            device_map="auto",
        )
        self.model.eval()
        # apply_liger_kernel_to_llama(model=self.model.language_model)  # Meow
        print("✅ 模型加载成功！")

    def get_processor(self):
        return self.processor

    def get_model(self):
        return self.model