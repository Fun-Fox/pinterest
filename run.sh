#!/bin/bash

# 查找可用端口
PORT=7861
while true; do
    if ! netstat -an | grep -q ":$PORT "; then
        break
    fi
    PORT=$((PORT + 1))
done

# 将端口号传递给 main.py
python main.py --port $PORT

# 打印实际使用的端口号
echo "启动成功，端口号: $PORT"