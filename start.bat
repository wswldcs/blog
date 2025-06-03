@echo off
echo ========================================
echo        wswldcs的个人博客启动脚本
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

REM 检查虚拟环境是否存在
if not exist "venv" (
    echo 创建虚拟环境...
    python -m venv venv
    if errorlevel 1 (
        echo 错误: 创建虚拟环境失败
        pause
        exit /b 1
    )
)

REM 激活虚拟环境
echo 激活虚拟环境...
call venv\Scripts\activate.bat

REM 检查requirements.txt是否存在
if not exist "requirements.txt" (
    echo 错误: 未找到requirements.txt文件
    pause
    exit /b 1
)

REM 安装依赖
echo 安装依赖包...
pip install -r requirements.txt
if errorlevel 1 (
    echo 错误: 安装依赖包失败
    pause
    exit /b 1
)

REM 检查.env文件是否存在
if not exist ".env" (
    echo 警告: 未找到.env文件，请确保已正确配置环境变量
    echo 您可以复制.env.example并重命名为.env，然后修改其中的配置
    pause
)

REM 检查数据库是否已初始化
echo 检查数据库...
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all(); print('数据库检查完成')"

REM 询问是否初始化示例数据
echo.
set /p init_data="是否初始化示例数据？(y/n): "
if /i "%init_data%"=="y" (
    echo 初始化示例数据...
    python init_db.py
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
python run.py

pause
