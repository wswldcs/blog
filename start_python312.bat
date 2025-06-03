@echo off
echo ========================================
echo        wswldcs的个人博客启动脚本
echo        使用Python 3.12
echo ========================================
echo.

REM 设置Python路径
set PYTHON_PATH=E:\python\python.exe
set PIP_PATH=E:\python\Scripts\pip.exe

REM 检查Python是否存在
if not exist "%PYTHON_PATH%" (
    echo 错误: 未找到Python 3.12，路径: %PYTHON_PATH%
    echo 请检查Python 3.12的安装路径
    pause
    exit /b 1
)

REM 显示Python版本
echo 检查Python版本...
"%PYTHON_PATH%" --version

REM 检查虚拟环境是否存在
if not exist "venv312" (
    echo 创建Python 3.12虚拟环境...
    "%PYTHON_PATH%" -m venv venv312
    if errorlevel 1 (
        echo 错误: 创建虚拟环境失败
        pause
        exit /b 1
    )
    echo 虚拟环境创建成功
) else (
    echo 虚拟环境已存在
)

REM 激活虚拟环境
echo 激活虚拟环境...
call venv312\Scripts\activate.bat

REM 升级pip
echo 升级pip...
venv312\Scripts\python.exe -m pip install --upgrade pip

REM 检查requirements.txt是否存在
if not exist "requirements.txt" (
    echo 错误: 未找到requirements.txt文件
    pause
    exit /b 1
)

REM 安装依赖
echo 安装依赖包...
venv312\Scripts\pip.exe install -r requirements.txt
if errorlevel 1 (
    echo 安装依赖包失败，尝试使用国内镜像...
    venv312\Scripts\pip.exe install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
    if errorlevel 1 (
        echo 错误: 依赖包安装失败
        pause
        exit /b 1
    )
)
echo 依赖包安装成功

REM 检查.env文件是否存在
if not exist ".env" (
    echo 警告: 未找到.env文件，请确保已正确配置环境变量
    echo 您可以复制.env文件并修改其中的配置
    pause
)

REM 检查MySQL连接
echo 检查MySQL连接...
mysql -u root -p1234 -e "SELECT 1;" >nul 2>&1
if errorlevel 1 (
    echo 警告: MySQL连接失败，请检查MySQL服务是否启动，密码是否正确
    echo 如果密码不是1234，请修改.env文件中的DATABASE_URL
) else (
    echo MySQL连接成功
    echo 创建数据库...
    mysql -u root -p1234 -e "CREATE DATABASE IF NOT EXISTS aublog CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" >nul 2>&1
    echo 数据库创建完成
)

REM 询问是否初始化示例数据
echo.
set /p init_data="是否初始化示例数据？(y/n): "
if /i "%init_data%"=="y" (
    echo 初始化示例数据...
    venv312\Scripts\python.exe init_db.py
    if errorlevel 1 (
        echo 警告: 示例数据初始化失败，可能数据已存在
    ) else (
        echo 示例数据初始化成功
    )
)

echo.
echo ========================================
echo 启动博客应用...
echo ========================================
echo 访问地址: http://localhost:5000
echo 管理后台: http://localhost:5000/admin
echo 默认管理员: admin / admin123
echo.
echo 按 Ctrl+C 停止服务器
echo ========================================
echo.

REM 启动Flask应用
venv312\Scripts\python.exe run.py

pause
