import gradio as gr
from transformers import LlavaForConditionalGeneration, TextIteratorStreamer, AutoProcessor
import torch
from PIL import Image
from threading import Thread
from typing import Generator
# from liger_kernel.transformers import apply_liger_kernel_to_llama



LOGO_SRC = """data:image/svg+xml;base64,PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjwhRE9DVFlQRSBzdmcgUFVCTElDICItLy9XM0MvL0RURCBTVkcgMS4xLy9FTiIgImh0dHA6Ly93d3cudzMub3JnL0dyYXBoaWNzL1NWRy8xLjEvRFREL3N2ZzExLmR0ZCI+Cjxzdmcgd2lkdGg9IjEwMCUiIGhlaWdodD0iMTAwJSIgdmlld0JveD0iMCAwIDUzOCA1MzUiIHZlcnNpb249IjEuMSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIiB4bWxuczp4bGluaz0iaHR0cDovL3d3dy53My5vcmcvMTk5OS94bGluayIgeG1sOnNwYWNlPSJwcmVzZXJ2ZSIgeG1sbnM6c2VyaWY9Imh0dHA6Ly93d3cuc2VyaWYuY29tLyIgc3R5bGU9ImZpbGwtcnVsZTpldmVub2RkO2NsaXAtcnVsZTpldmVub2RkO3N0cm9rZS1saW5lam9pbjpyb3VuZDtzdHJva2UtbWl0ZXJsaW1pdDoyOyI+CiAgICA8ZyB0cmFuc2Zvcm09Im1hdHJpeCgxLDAsMCwxLC0xNDcuODcxLDAuMDAxOTA4NjMpIj4KICAgICAgICA8cGF0aCBkPSJNMTk1LjY3LDIyMS42N0MxOTYuNzMsMjA1LjM3IDIwMC4yOCwxODkuNzYgMjA3LjkxLDE3NS4zN0MyMjcuOTgsMTM3LjUxIDI1OS4zMywxMTQuODggMzAyLjAxLDExMS42M0MzMzQuMTUsMTA5LjE4IDM2Ni41OSwxMTAuNiAzOTguODksMTEwLjNDNDAwLjUzLDExMC4yOCA0MDIuMTYsMTEwLjMgNDA0LjQsMTEwLjNDNDA0LjQsMTAxLjk5IDQwNC41Niw5NC4wNSA0MDQuMjMsODYuMTJDNDA0LjE4LDg0Ljg0IDQwMi4xNSw4My4xMyA0MDAuNjYsODIuNDlDMzgzLjIzLDc1LjAyIDM3My4wNSw1OS43OSAzNzMuOTYsNDAuOTZDMzc1LjA5LDE3LjU0IDM5MS40NywyLjY2IDQxMC42NSwwLjM3QzQzNy44OSwtMi44OSA0NTUuNTYsMTUuODQgNDU5LjI2LDM0LjY5QzQ2Mi45Niw1My41NyA0NTIuMTgsNzYuOTMgNDMyLjgxLDgyLjY2QzQzMS42NCw4My4wMSA0MzAuMzMsODUuMjMgNDMwLjI4LDg2LjYyQzQzMC4wMyw5NC4yNiA0MzAuMTYsMTAxLjkyIDQzMC4xNiwxMTAuM0w0MzUuNjMsMTEwLjNDNDYzLjc5LDExMC4zIDQ5MS45NiwxMTAuMjggNTIwLjEyLDExMC4zQzU3NC44NCwxMTAuMzYgNjIzLjA0LDE0OC4zNSA2MzUuNjcsMjAxLjU1QzYzNy4yMywyMDguMTMgNjM3LjgzLDIxNC45MyA2MzguODksMjIxLjY3QzY2MC40MywyMjQuOTQgNjc1LjE5LDIzNi42MiA2ODIuMzYsMjU3LjRDNjgzLjU5LDI2MC45NyA2ODQuNjUsMjY0LjgyIDY4NC42NywyNjguNTRDNjg0Ljc3LDI4My4zNCA2ODUuNzYsMjk4LjMxIDY4My45NCwzMTIuOTFDNjgwLjg5LDMzNy4yOSA2NjIuODYsMzUzLjM2IDYzOC40NywzNTUuODJDNjM1LjE0LDM4NS4wOCA2MjEuOTEsNDA5LjQxIDYwMC40NSw0MjkuMjFDNTgxLjYsNDQ2LjYxIDU1OS4xNCw0NTcuNSA1MzMuNTcsNDU5LjE4QzUwOC4xOCw0NjAuODQgNDgyLjY0LDQ2MC4yIDQ1Ny4xNiw0NjAuMzhDNDM1LjE2LDQ2MC41MyA0MTMuMTcsNDYwLjM0IDM5MS4xNyw0NjAuNTNDMzg4Ljc2LDQ2MC41NSAzODUuOTUsNDYxLjU2IDM4NC4wMyw0NjMuMDRDMzcxLjU0LDQ3Mi42MiAzNTkuMTMsNDgyLjMxIDM0Ni45Miw0OTIuMjVDMzM4Ljk0LDQ5OC43NSAzMzEuMzksNTA1Ljc3IDMyMy41Niw1MTIuNDZDMzE3LjQ1LDUxNy42OCAzMTAuOTMsNTIyLjQ0IDMwNS4xMSw1MjcuOTVDMzAxLjE5LDUzMS42NiAyOTYuNTIsNTMzLjE3IDI5MS42OSw1MzQuMzZDMjg1LjY1LDUzNS44NSAyNzkuMjIsNTI5LjEzIDI3OS4wMSw1MjEuMTlDMjc4LjgsNTEyLjg2IDI3OC45NSw1MDQuNTMgMjc4Ljk0LDQ5Ni4xOUwyNzguOTQsNDU2LjY5QzIzMi44Miw0MzguMTYgMjAzLjU2LDQwNi4yMyAxOTUuMDcsMzU2LjA4QzE5My4yNiwzNTUuNzUgMTkwLjg0LDM1NS40MSAxODguNDgsMzU0Ljg2QzE2Ny40NiwzNDkuOTEgMTU1LjA0LDMzNi4wMiAxNTAuNzIsMzE1LjYyQzE0Ni45OCwyOTcuOTkgMTQ2LjksMjc5LjY3IDE1MC42MSwyNjIuMDlDMTU1LjU1LDIzOC42OCAxNzEuNDIsMjI1LjU5IDE5NS42NiwyMjEuNjdMMTk1LjY3LDIyMS42N1pNMzA4LjA3LDQ4Ny44MkMzMTUuOTQsNDgxLjEzIDMyMi44NSw0NzUuMTMgMzI5LjksNDY5LjNDMzQ0LjM5LDQ1Ny4zMSAzNTguOSw0NDUuMzYgMzczLjU0LDQzMy41NkMzNzUuMTcsNDMyLjI1IDM3Ny42OCw0MzEuNCAzNzkuNzksNDMxLjM5QzQxNC43OCw0MzEuMjYgNDQ5Ljc4LDQzMS4zOCA0ODQuNzcsNDMxLjI0QzUwMC4zOSw0MzEuMTggNTE2LjEzLDQzMS43NiA1MzEuNjIsNDMwLjE2QzU3Ni45Miw0MjUuNDkgNjA5LjI0LDM4Ny43NyA2MDguOTUsMzQ0Ljg0QzYwOC42OCwzMDUuNTIgNjA4LjkzLDI2Ni4xOSA2MDguODcsMjI2Ljg2QzYwOC44NywyMjMuMjIgNjA4LjU4LDIxOS41NSA2MDcuOTksMjE1Ljk2QzYwMy4xMSwxODYuMjkgNTg4LjYxLDE2My4zMyA1NjEuMzIsMTQ5LjMyQzU0OS4wNCwxNDMuMDIgNTM2LjE1LDEzOS4yOSA1MjIuMjIsMTM5LjI5QzQ1My45LDEzOS4zMiAzODUuNTgsMTM5LjIgMzE3LjI2LDEzOS4zNUMzMDkuMiwxMzkuMzcgMzAwLjk2LDEzOS44OSAyOTMuMTEsMTQxLjZDMjU0LjE5LDE1MC4wNyAyMjUuMzMsMTg1LjY5IDIyNS4wMywyMjUuNDJDMjI0LjgsMjU2LjA4IDIyNC44NiwyODYuNzQgMjI0Ljk5LDMxNy40QzIyNS4wNSwzMzAuNTMgMjI0Ljc0LDM0My43NiAyMjYuMTgsMzU2Ljc3QzIyOC43NCwzODAuMDUgMjQwLjYsMzk4LjYyIDI1OC43OSw0MTIuOTNDMjczLjA0LDQyNC4xNCAyODkuNjMsNDMwLjAyIDMwNy42MSw0MzEuNTVDMzA3LjgyLDQzMi4wMyAzMDguMDYsNDMyLjMzIDMwOC4wNiw0MzIuNjNDMzA4LjA4LDQ1MC42IDMwOC4wOCw0NjguNTcgMzA4LjA4LDQ4Ny44MUwzMDguMDcsNDg3LjgyWk00MzUuNzksNDMuMzNDNDM1Ljk1LDMzLjQyIDQyNy42MSwyNC42NSA0MTcuOCwyNC40QzQwNi43NiwyNC4xMiAzOTguMjUsMzIuMDUgMzk4LjEzLDQyLjc0QzM5OC4wMSw1My4wNCA0MDYuNiw2Mi4xMiA0MTYuNDIsNjIuMDhDNDI3LjExLDYyLjA0IDQzNS42MSw1My44MSA0MzUuNzgsNDMuMzNMNDM1Ljc5LDQzLjMzWiIgc3R5bGU9ImZpbGw6cmdiKDczLDQ3LDExOCk7ZmlsbC1ydWxlOm5vbnplcm87Ii8+CiAgICAgICAgPHBhdGggZD0iTTQxOS4zLDM5MS42M0MzNzQuNDYsMzkwLjQgMzQxLjUxLDM3Mi42MyAzMTguMDEsMzM3LjcxQzMxNS42NywzMzQuMjMgMzEzLjc3LDMzMC4wNCAzMTMuMSwzMjUuOTVDMzExLjg0LDMxOC4yOCAzMTYuNTMsMzExLjcgMzIzLjcyLDMwOS40NkMzMzAuNjYsMzA3LjI5IDMzOC4zMiwzMTAuMSAzNDEuOTgsMzE3LjAzQzM0OS4xNSwzMzAuNjMgMzU5LjE2LDM0MS4zNSAzNzIuMywzNDkuMzFDNDAxLjMyLDM2Ni44OSA0NDQuNTYsMzYzLjcgNDcwLjYxLDM0Mi4zNUM0NzkuMSwzMzUuMzkgNDg2LjA4LDMyNy40MSA0OTEuNTUsMzE3Ljk3QzQ5NS4wNSwzMTEuOTMgNTAwLjIsMzA4LjE4IDUwNy40NywzMDguOTVDNTEzLjczLDMwOS42MSA1MTguODYsMzEyLjg4IDUyMC4xMiwzMTkuMjFDNTIwLjksMzIzLjEzIDUyMC43MywzMjguMjIgNTE4LjgzLDMzMS41NUM1MDAuNjMsMzYzLjMyIDQ3My41NSwzODIuOTUgNDM3LjI5LDM4OS4zN0M0MzAuNDQsMzkwLjU4IDQyMy40OCwzOTEuMTIgNDE5LjI5LDM5MS42M0w0MTkuMywzOTEuNjNaIiBzdHlsZT0iZmlsbDpyZ2IoMjUwLDEzOSwxKTtmaWxsLXJ1bGU6bm9uemVybzsiLz4KICAgICAgICA8cGF0aCBkPSJNNDYyLjcxLDI0MC4xOUM0NjIuOCwyMTYuOTEgNDgwLjI0LDE5OS43OSA1MDQuMDEsMTk5LjY3QzUyNi41NywxOTkuNTUgNTQ0Ljg5LDIxOC4wNyA1NDQuNTEsMjQxLjM0QzU0NC4xOCwyNjEuODUgNTMwLjA5LDI4MS45NiA1MDEuOTEsMjgxLjIzQzQ4MC42OCwyODAuNjggNDYyLjE1LDI2My44IDQ2Mi43MSwyNDAuMkw0NjIuNzEsMjQwLjE5WiIgc3R5bGU9ImZpbGw6cmdiKDI1MCwxMzksMSk7ZmlsbC1ydWxlOm5vbnplcm87Ii8+CiAgICAgICAgPHBhdGggZD0iTTM3MC45OSwyNDAuMDhDMzcxLDI2Mi43OSAzNTIuNTMsMjgxLjM1IDMyOS44OSwyODEuMzdDMzA3LjA1LDI4MS40IDI4OC45NiwyNjMuNDIgMjg4Ljk2LDI0MC42OEMyODguOTYsMjE4LjE0IDMwNi43MywyMDAgMzI5LjE2LDE5OS42MkMzNTIuMDIsMTk5LjI0IDM3MC45OCwyMTcuNTcgMzcwLjk5LDI0MC4wOFoiIHN0eWxlPSJmaWxsOnJnYigyNTAsMTM5LDEpO2ZpbGwtcnVsZTpub256ZXJvOyIvPgogICAgPC9nPgo8L3N2Zz4K"""

TITLE = f"""<style>
  .joy-header   {{display:flex; align-items:center; justify-content:center;
                 gap:16px; margin:4px 0 12px;}}
  .joy-header h1{{margin:0; font-size:1.9rem; line-height:1.2;}}
  .joy-header p {{margin:2px 0 0; font-size:0.9rem; color:#666;}}
  .joy-header img{{height:56px;}}
</style>

<div class="joy-header">
  <img src="{LOGO_SRC}" alt="JoyCaption logo">
  <div>
    <h1>JoyCaption <span style="font-weight:400">Beta&nbsp;One</span></h1>
    <p>图像描述生成模型 &nbsp;|&nbsp; build mb3500zp</p>
  </div>
</div>
<hr>"""

DESCRIPTION = """
<div>
<h2>快速开始</h2>
<ol>
  <li><strong>上传或拖放</strong>一张图片到左侧面板。</li>
  <li>选择一个<strong>标题类型</strong>，并可选地调整<strong>标题长度</strong>。</li>
  <li>（可选）展开“额外选项”折叠面板，并勾选影响生成内容的复选框。</li>
  <li>（可选）打开“生成设置”以调整 <code>temperature</code>, <code>top-p</code> 或 <code>max&nbsp;tokens</code>。</li>
  <li>点击 <kbd>生成标题</kbd> 按钮。  
      发送给模型的提示词会显示在“提示”框中（可编辑），  
      生成的标题会流式输出到“标题”框中。</li>
</ol>

<!-- ───────────────────── 标题类型说明 ──────────────────── -->
<h2>标题类型</h2>
<table>
  <tr><th>模式</th><th>用途</th></tr>
  <tr><td><strong>描述性</strong></td>
      <td>正式、详细的文字描述。</td></tr>
  <tr><td><strong>描述性（随意）</strong></td>
      <td>与描述性类似，但语气更友好、口语化。</td></tr>
  <tr><td><strong>直截了当</strong></td>
      <td>客观、简洁，比描述性更简练。</td></tr>
  <tr><td><strong>Stable Diffusion 提示词</strong></td>
      <td>反向工程出一张能生成该图像的 SD/T2I 提示词。<br><em>⚠︎ 实验功能 – 约有 3% 的概率出现错误。</em></td></tr>
  <tr><td><strong>MidJourney</strong></td>
      <td>同上，但适配 MidJourney 的提示风格。<br><em>⚠︎ 实验功能 – 约有 3% 的概率出现错误。</em></td></tr>
  <tr><td><strong>Danbooru 标签列表</strong></td>
      <td>严格按照 Danbooru 规范逗号分隔标签（artist:, copyright: 等）。仅小写_下划线。<br><em>⚠︎ 实验功能 – 约有 3% 的概率出现错误。</em></td></tr>
  <tr><td><strong>e621 标签列表</strong></td>
      <td>按字母顺序排列的 e621 风格标签：artist:、copyright:、character:、species:、meta: 等前缀，然后是通用标签。<br><em>⚠︎ 实验功能 – 约有 3% 的概率出现错误。</em></td></tr>
  <tr><td><strong>Rule34 标签列表</strong></td>
      <td>按字母顺序排列的 Rule34 标签：artist/copyright/character 前缀优先。<br><em>⚠︎ 实验功能 – 约有 3% 的概率出现错误。</em></td></tr>
  <tr><td><strong>Booru 类似标签列表</strong></td>
      <td>宽松格式的标签列表，适合不需要特定 Booru 格式时使用。<br><em>⚠︎ 实验功能 – 约有 3% 的概率出现错误。</em></td></tr>
  <tr><td><strong>艺术评论家</strong></td>
      <td>对构图、象征意义、风格、色彩运用、光线等进行艺术评论。</td></tr>
  <tr><td><strong>产品列表</strong></td>
      <td>像商品推广文案一样描述图像中的物体。</td></tr>
  <tr><td><strong>社交媒体帖子</strong></td>
      <td>适用于 Instagram 或 BlueSky 等平台的吸引人标题。</td></tr>
</table>

<p style="margin-top:0.6em">
  <strong>关于 Booru 模式备注：</strong>它们针对动漫/插画类图像优化，在真实照片或高度抽象的艺术作品上准确性可能下降。
</p>

<!-- ───────────────────── 额外选项与生成参数说明 ───────────────── -->
<h3>额外选项</h3>
<p>这些复选框可以微调模型应提及或避免的内容：
照明、相机角度、美学评分、粗俗语言等。  
在点击 <kbd>生成标题</kbd> 前切换这些选项；提示框内容会实时更新。</p>

<h3>生成设置</h3>
<ul>
  <li><strong>温度</strong> – 控制随机性。  
      0&nbsp;=&nbsp;确定性；数值越高 =&nbsp;结果越多样。</li>
  <li><strong>Top-p</strong> – 核采样阈值。较低 =&nbsp;更安全，较高 =&nbsp;更自由。</li>
  <li><strong>最大新 Token 数量</strong> – 限制模型输出长度，达到上限后停止生成。</li>
</ul>

<p>欢迎尝试各种设置，如果您发现任何 bug 或有新功能建议，请随时提交 issue！</p>
<hr>
<p>🚨🚨🚨 如果勾选了“通过记录您的文本查询来帮助改进 JoyCaption”，您输入的文本将被记录，并可能会用于改进 JoyCaption 数据集。  
不会记录图像、用户数据等内容，只记录文本查询。我无法看到您发送的图像，也不希望看到。  
了解用户希望 JoyCaption 处理哪些类型的指令和查询将有助于构建公开的数据集。  
模型本身始终是完全开源且可在 HuggingFace 以外的空间自由使用。  
当然，我也无法控制或访问 HuggingFace 收集的内容。</p>
</div>
"""


CAPTION_TYPE_MAP = {
    "描述性": [
        "为这幅图像写一个详细的描述。",
        "用 {word_count} 个单词或更少的单词为这幅图像写一个详细的描述。",
        "为这幅图像写一个 {length} 的详细描述。",
    ],
    "描述性（随意）": [
        "用随意的语气为这幅图像写一个描述性的标题。",
        "在 {word_count} 个单词内用随意的语气为这幅图像写一个描述性的标题。",
        "用随意的语气为这幅图像写一个 {length} 的描述性标题。",
    ],
    "直截了当": [
        "为这幅图像写一个直截了当的标题。以主要主题和媒介开头。提及关键元素——人物、物体、景色——使用自信、肯定的语言。关注具体的细节，如颜色、形状、纹理和空间关系。展示元素如何互动。省略情绪和推测性语言。如果存在文本，准确引用。注意任何水印、签名或压缩伪影。不要提及缺失的内容、分辨率或不可观察的细节。变化你的句子结构，保持描述简洁，不要以“这张图片是…”或类似的措辞开头。",
        "在 {word_count} 个单词内为这幅图像写一个直截了当的标题。以主要主题和媒介开头。提及关键元素——人物、物体、景色——使用自信、肯定的语言。关注具体的细节，如颜色、形状、纹理和空间关系。展示元素如何互动。省略情绪和推测性语言。如果存在文本，准确引用。注意任何水印、签名或压缩伪影。不要提及缺失的内容、分辨率或不可观察的细节。变化你的句子结构，保持描述简洁，不要以“这张图片是…”或类似的措辞开头。",
        "为这幅图像写一个 {length} 的直截了当的标题。以主要主题和媒介开头。提及关键元素——人物、物体、景色——使用自信、肯定的语言。关注具体的细节，如颜色、形状、纹理和空间关系。展示元素如何互动。省略情绪和推测性语言。如果存在文本，准确引用。注意任何水印、签名或压缩伪影。不要提及缺失的内容、分辨率或不可观察的细节。变化你的句子结构，保持描述简洁，不要以“这张图片是…”或类似的措辞开头。",
    ],
    "稳定扩散提示": [
        "输出一个与真实稳定扩散提示无法区分的稳定扩散提示。",
        "在 {word_count} 个单词或更少的单词内输出一个与真实稳定扩散提示无法区分的稳定扩散提示。",
        "输出一个 {length} 的与真实稳定扩散提示无法区分的稳定扩散提示。",
    ],
    "MidJourney": [
        "为这幅图像写一个 MidJourney 提示。",
        "在 {word_count} 个单词内为这幅图像写一个 MidJourney 提示。",
        "为这幅图像写一个 {length} 的 MidJourney 提示。",
    ],
    "Danbooru 标签列表": [
        "生成仅包含逗号分隔的 Danbooru 标签（小写_下划线）。严格顺序：`artist:`，`copyright:`，`character:`，`meta:`，然后是通用标签。包括计数（1girl），外观，服装，配饰，姿势，表情，动作，背景。使用精确的 Danbooru 语法。没有额外的文本。",
        "生成仅包含逗号分隔的 Danbooru 标签（小写_下划线）。严格顺序：`artist:`，`copyright:`，`character:`，`meta:`，然后是通用标签。包括计数（1girl），外观，服装，配饰，姿势，表情，动作，背景。使用精确的 Danbooru 语法。没有额外的文本。{word_count} 个单词或更少。",
        "生成仅包含逗号分隔的 Danbooru 标签（小写_下划线）。严格顺序：`artist:`，`copyright:`，`character:`，`meta:`，然后是通用标签。包括计数（1girl），外观，服装，配饰，姿势，表情，动作，背景。使用精确的 Danbooru 语法。没有额外的文本。{length} 长度。",
    ],
    "e621 标签列表": [
        "为这幅图像写一个按字母顺序排列的 e621 标签列表。以艺术家、版权、角色、物种、元数据和传说标签（如果有的话）开头，前缀分别为 'artist:'，'copyright:'，'character:'，'species:'，'meta:' 和 'lore:'。然后是所有通用标签。",
        "为这幅图像写一个按字母顺序排列的 e621 标签列表。以艺术家、版权、角色、物种、元数据和传说标签（如果有的话）开头，前缀分别为 'artist:'，'copyright:'，'character:'，'species:'，'meta:' 和 'lore:'。然后是所有通用标签。不超过 {word_count} 个单词。",
        "为这幅图像写一个 {length} 的按字母顺序排列的 e621 标签列表。以艺术家、版权、角色、物种、元数据和传说标签（如果有的话）开头，前缀分别为 'artist:'，'copyright:'，'character:'，'species:'，'meta:' 和 'lore:'。然后是所有通用标签。",
    ],
    "Rule34 标签列表": [
        "为这幅图像写一个按字母顺序排列的 Rule34 标签列表。以艺术家、版权、角色和元数据标签（如果有的话）开头，前缀分别为 'artist:'，'copyright:'，'character:' 和 'meta:'。然后是所有通用标签。",
        "为这幅图像写一个按字母顺序排列的 Rule34 标签列表。以艺术家、版权、角色和元数据标签（如果有的话）开头，前缀分别为 'artist:'，'copyright:'，'character:' 和 'meta:'。然后是所有通用标签。不超过 {word_count} 个单词。",
        "为这幅图像写一个 {length} 的按字母顺序排列的 Rule34 标签列表。以艺术家、版权、角色和元数据标签（如果有的话）开头，前缀分别为 'artist:'，'copyright:'，'character:' 和 'meta:'。然后是所有通用标签。",
    ],
    "Booru 类似标签列表": [
        "为这幅图像写一个 Booru 类似标签列表。",
        "在 {word_count} 个单词内为这幅图像写一个 Booru 类似标签列表。",
        "为这幅图像写一个 {length} 的 Booru 类似标签列表。",
    ],
    "艺术评论家": [
        "像艺术评论家一样分析这幅图像，提供关于其构图、风格、象征意义、色彩运用、光线等信息。",
        "像艺术评论家一样分析这幅图像，提供关于其构图、风格、象征意义、色彩运用、光线等信息。不超过 {word_count} 个单词。",
        "像艺术评论家一样分析这幅图像，提供关于其构图、风格、象征意义、色彩运用、光线等信息。保持 {length}。",
    ],
    "产品列表": [
        "为这幅图像写一个产品列表式的标题。",
        "为这幅图像写一个产品列表式的标题。不超过 {word_count} 个单词。",
        "为这幅图像写一个 {length} 的产品列表式标题。",
    ],
    "社交媒体帖子": [
        "为这幅图像写一个用于社交媒体帖子的标题。",
        "为这幅图像写一个用于社交媒体帖子的标题。限制标题为 {word_count} 个单词。",
        "为这幅图像写一个 {length} 的用于社交媒体帖子的标题。",
    ],
}

NAME_OPTION = "如果图像中有一个人物/角色，你必须称他们为 {name}。"


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
def build_prompt(caption_type: str, caption_length: str | int, extra_options: list[str], name_input: str) -> str:
	# 选择正确的模板行在 CAPTION_TYPE_MAP 中
	if caption_length == "any":
		map_idx = 0
	elif isinstance(caption_length, str) and caption_length.isdigit():
		map_idx = 1  # 数字单词计数模板
	else:
		map_idx = 2  # 长度描述符模板

	prompt = CAPTION_TYPE_MAP[caption_type][map_idx]

	if extra_options:
		prompt += " " + " ".join(extra_options)

	return prompt.format(
		name=name_input or "{NAME}",
		length=caption_length,
		word_count=caption_length,
	)


def toggle_name_box(selected_options: list[str]):
	"""仅在选择特定选项时显示名称文本框。"""
	return gr.update(visible=NAME_OPTION in selected_options)


# @spaces.GPU()
@torch.no_grad()
def chat_joycaption(input_image: Image.Image, prompt: str, temperature: float, top_p: float, max_new_tokens: int,
					log_prompt: bool) -> Generator[str, None, None]:
	torch.cuda.empty_cache()

	if input_image is None:
		yield "未提供图像。请上传图像。"
		return

	if log_prompt:
		print(f"PromptLog: {repr(prompt)}")

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


with gr.Blocks() as demo:
	gr.HTML(TITLE)

	with gr.Row():
		with gr.Column():
			input_image = gr.Image(type="pil", label="输入图像", height=512, width=512)

			caption_type = gr.Dropdown(
				choices=list(CAPTION_TYPE_MAP.keys()),
				value="描述性",
				label="标题类型",

			)

			caption_length = gr.Dropdown(
				choices=["任意", "非常短", "短", "中等长度", "长", "非常长"] +
						[str(i) for i in range(20, 261, 10)],
				label="标题长度",
				value="长",
			)

			with gr.Accordion("额外选项", open=False):
				extra_options = gr.CheckboxGroup(
					choices=[
						NAME_OPTION,
						"不要包含关于无法更改的人/角色的信息（如种族、性别等），但仍需包含可更改的属性（如发型）。",
                        "包含有关照明的信息。",
                        "包含有关相机角度的信息。",
                        "包含有关是否存在水印的信息。",
                        "包含有关是否存在 JPEG 伪影的信息。",
                        "如果是照片，必须包含有关可能使用的相机和细节（如光圈、快门速度、ISO 等）的信息。",
                        "不要包含任何色情内容；保持 PG 级。",
                        "不要提及图像的分辨率。",
                        "你必须包含对图像主观美学质量的评价，从低到非常高。",
                        "包含有关图像构图风格的信息，例如引导线、三分法则或对称性。",
                        "不要提及图像中的任何文本。",
                        "指定景深和背景是否聚焦或模糊。",
                        "如果适用，提及可能使用的人工或自然光源。",
                        "不要使用任何模棱两可的语言。",
                        "包含图像是否为安全、暗示性或不安全的信息。",
                        "只描述图像最重要的元素。",
                        "如果是艺术品，不要包含艺术家的名字或作品标题。",
                        "识别图像的方向（肖像、风景或正方形）和明显的纵横比。",
                        "使用粗俗俚语和脏话，例如（但不限于）“fucking”，“slut”，“cock”等。",
                        "不要使用礼貌的委婉语——采用直白、随意的表达方式。",
                        "包含有关任何人物/角色年龄的信息（如果适用）。",
                        "提及图像描绘的是极端特写、特写、中景特写、中景、牛仔镜头、中景宽镜头、全景或极端全景。",
                        "不要提及图像的情绪/感受等。",
                        "明确指定视角高度（眼平、低角虫眼、鸟瞰、无人机、屋顶等）。",
                        "如果有水印，你必须提及它。",
                        "你的回答将被用于文本到图像模型，因此避免使用无用的元短语，如“这张图片显示...”，“你正在看...”等。",
                    ],
                    label="选择一个或多个",
                )

				name_input = gr.Textbox(label="人物 / 角色名称", visible=False)

				with gr.Accordion("生成设置", open=False):
					temperature_slider = gr.Slider(
						minimum=0.0, maximum=2.0, value=0.6, step=0.05,
						label="温度",
						info="较高的值使输出更随机，较低的值使输出更确定。"
					)
					top_p_slider = gr.Slider(
						minimum=0.0, maximum=1.0, value=0.9, step=0.01,
						label="Top-p"
					)
					max_tokens_slider = gr.Slider(
						minimum=1, maximum=2048, value=512, step=1,
						label="最大新令牌",
						info="生成的最大令牌数。如果达到此限制，模型将停止生成。"
					)

				log_prompt = gr.Checkbox(value=True, label="通过记录您的文本查询来帮助改进 JoyCaption")

			with gr.Column():
				prompt_box = gr.Textbox(lines=4, label="提示", interactive=True)

				# 仅在选择特定选项时显示名称输入框
				extra_options.change(
					toggle_name_box,
					inputs=extra_options,
					outputs=name_input,
				)

				# 当任何输入更改时自动更新提示框
				for ctrl in (caption_type, caption_length, extra_options, name_input):
					ctrl.change(
						build_prompt,
						inputs=[caption_type, caption_length, extra_options, name_input],
						outputs=prompt_box,
					)

				run_button = gr.Button("生成标题")

				output_caption = gr.Textbox(label="标题")

		run_button.click(
			chat_joycaption,
			inputs=[input_image, prompt_box, temperature_slider, top_p_slider, max_tokens_slider, log_prompt],
			outputs=output_caption,
		)

		# 初始提示
		prompt_box.value = build_prompt(caption_type.value, caption_length.value, extra_options.value, name_input.value)

		gr.Markdown(DESCRIPTION)

	if __name__ == "__main__":
		demo.launch()