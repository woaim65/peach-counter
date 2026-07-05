@echo off
chcp 65001>nul
echo ==============================
echo   🍑 桃数统计 - 启动器
echo ==============================
echo.

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 没找到 Python，请先装 Python 3.8+
    echo 下载：https://www.python.org/downloads/
    echo 装的时候记得勾 "Add Python to PATH"
    pause
    exit /b
)

echo [OK] Python 已安装，检查依赖...
pip install opencv-python numpy -q
if errorlevel 1 (
    echo [错误] 装依赖失败
    pause
    exit /b
)

echo [OK] 启动程序...
echo.
python "%~dp0peach_counter.py"
pause