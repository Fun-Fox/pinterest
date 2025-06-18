
## AI挑图功能额外说明

目前AI挑图功能未支持docker打包，请直接下载代码进行部署运行

依赖于llama-joycaption-beta-one-hf-llava 所有需要下载模型

```
# 安装图片反推模型（图片打标）依赖
cd remote_caption_ws_server
pip install -r requirements.txt
playwright install chromium

# 下载LLaVA模型
set HF_ENDPOINT=https://hf-mirror.com
# 下载模型到 项目 目录下
huggingface-cli download fancyfeast/llama-joycaption-beta-one-hf-llava --repo-type=model --local-dir /fancyfeast/llama-joycaption-beta-one-hf-llava

# 安装PyTorch
pip install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu128
pip install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu128

# 安装Triton
#https://zhuanlan.zhihu.com/p/27131210741
#pip install -U triton-windows
#https://blog.csdn.net/a486259/article/details/146451953
#pip install liger-kernel --no-dependencies
```