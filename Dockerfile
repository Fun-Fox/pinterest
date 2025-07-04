# 使用官方 Python 镜像作为基础镜像
# FROM  python:3.11-slim
FROM  chinayin/playwright:1.52.0-chromium-python3.11

# 设置工作目录
WORKDIR /app

# 将上一个目录下的所有文件复制到容器的 /app 目录下
COPY ../ /app

# RUN ls -l /app

# 安装项目依赖
RUN  pip install -r requirements.txt
# RUN  playwright install chromium
# RUN  playwright install-deps
# 暴露端口
EXPOSE 7861