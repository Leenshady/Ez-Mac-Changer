@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

set VENV_NAME=venv_build
set SCRIPT_NAME=main.py
set EXE_NAME=Ez-Mac-Changer
set REQUIREMENTS=requirements.txt

:: 设置 pip 超时和重试
set PIP_TIMEOUT=60
set PIP_RETRIES=5

echo ========== 1. 检查/创建虚拟环境 ==========
if exist "%VENV_NAME%\Scripts\activate.bat" (
    echo 检测到已存在的虚拟环境：%VENV_NAME%，将直接使用。
) else (
    echo 未找到虚拟环境，正在创建 %VENV_NAME% ...
    python -m venv %VENV_NAME%
    if !errorlevel! neq 0 (
        echo [错误] 创建虚拟环境失败，请确保 Python 3.8 已安装并可用。
        pause
        exit /b 1
    )
)

echo 激活虚拟环境...
call %VENV_NAME%\Scripts\activate
if %errorlevel% neq 0 (
    echo [错误] 激活虚拟环境失败。
    pause
    exit /b 1
)

echo ========== 2. 安装 pipreqs 并生成依赖清单 ==========
echo 安装 pipreqs（多镜像重试）...
call :install_package pipreqs
if %errorlevel% neq 0 (
    echo [错误] 无法安装 pipreqs，终止。
    pause
    exit /b 1
)

echo 正在扫描项目源码，生成 %REQUIREMENTS% ...
pipreqs ./ --encoding=utf8 --force
if %errorlevel% neq 0 (
    echo [警告] pipreqs 生成失败，将创建基础依赖文件。
    echo netifaces > %REQUIREMENTS%
) else (
    echo 生成的依赖内容：
    type %REQUIREMENTS%
    :: 确保 netifaces 在依赖列表中（如果缺失则追加）
    findstr /i "netifaces" %REQUIREMENTS% >nul
    if !errorlevel! neq 0 (
        echo 依赖中未找到 netifaces，手动追加...
        echo netifaces >> %REQUIREMENTS%
    )
)

echo ========== 3. 安装项目依赖（强制包含 netifaces）==========
echo 安装项目依赖...
call :install_requirements

echo ========== 4. 安装 PyInstaller 并打包（显式包含 netifaces）==========
echo 安装 PyInstaller...
call :install_package pyinstaller

echo 打包 %SCRIPT_NAME% 为 exe（强制包含 netifaces）...
pyinstaller -w --onefile --hidden-import netifaces -n %EXE_NAME% %SCRIPT_NAME%
if %errorlevel% neq 0 (
    echo [错误] 打包失败。
    pause
    exit /b 1
)

echo 打包成功！exe 文件位于 dist 目录中。

echo ========== 5. 清理虚拟环境（可选） ==========
echo 是否删除虚拟环境 %VENV_NAME%？(y/n)
set /p DELETE_VENV=
if /i "!DELETE_VENV!"=="y" (
    echo 正在删除虚拟环境...
    deactivate
    rmdir /s /q %VENV_NAME%
    echo 虚拟环境已删除。
) else (
    echo 保留虚拟环境，下次运行可快速复用。
)

echo ========== 所有步骤完成 ==========
pause
goto :eof

:: 函数：安装单个包（多镜像重试）
:install_package
set PACKAGE=%1
echo 尝试安装 %PACKAGE% ...
for %%M in (
    "https://pypi.tuna.tsinghua.edu.cn/simple"
    "https://mirrors.aliyun.com/pypi/simple/"
    "https://pypi.org/simple"
) do (
    echo 使用镜像 %%~M
    pip install %PACKAGE% -i %%~M --timeout=%PIP_TIMEOUT% --retries=%PIP_RETRIES%
    if !errorlevel! equ 0 (
        echo %PACKAGE% 安装成功。
        exit /b 0
    )
)
echo [错误] 所有镜像均无法安装 %PACKAGE%。
exit /b 1

:: 函数：安装 requirements（多镜像重试）
:install_requirements
for %%M in (
    "https://pypi.tuna.tsinghua.edu.cn/simple"
    "https://mirrors.aliyun.com/pypi/simple/"
    "https://pypi.org/simple"
) do (
    echo 使用镜像 %%~M 安装依赖...
    pip install -r %REQUIREMENTS% -i %%~M --timeout=%PIP_TIMEOUT% --retries=%PIP_RETRIES%
    if !errorlevel! equ 0 (
        echo 依赖安装成功。
        exit /b 0
    )
)
echo [错误] 所有镜像均无法安装依赖。
exit /b 1