@echo off
echo 正在打包 folder_renamer.py 为 exe 文件...
echo.

REM 检查是否安装了 pyinstaller
python -m pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo 未安装 PyInstaller，正在安装...
    python -m pip install pyinstaller
    echo.
)

REM 使用 spec 文件打包
echo 开始打包...
pyinstaller --clean folder_renamer.spec

if %errorlevel% equ 0 (
    echo.
    echo 打包成功！
    echo 可执行文件位于: distolder_renamer.exe
) else (
    echo.
    echo 打包失败，请检查错误信息
)

pause
