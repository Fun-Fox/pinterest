@echo off
REM 查找可用端口
setlocal enabledelayedexpansion
set PORT=7861
:find_port
for /f "tokens=5" %%a in ('netstat -an ^| find ":%PORT%"') do (
    if "%%a"=="0.0.0.0:%PORT%" (
        set /a PORT+=1
        goto find_port
    )
)

REM 将端口号传递给 main.py
python main.py --port %PORT%

REM 打印实际使用的端口号
echo 启动成功，端口号: %PORT%
REM 打印输出
echo %errorlevel%