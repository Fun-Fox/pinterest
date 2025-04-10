@echo off
REM 运行 main.py 并捕获输出
python main.py
REM 打印输出
echo %errorlevel%