# PowerShell启动脚本
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "        wswldcs的个人博客启动脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查Python是否安装
try {
    $pythonVersion = python --version 2>$null
    Write-Host "✓ Python已安装: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ 错误: 未找到Python，请先安装Python 3.8+" -ForegroundColor Red
    Read-Host "按任意键退出"
    exit 1
}

# 检查虚拟环境是否存在
if (-not (Test-Path "venv")) {
    Write-Host "创建虚拟环境..." -ForegroundColor Yellow
    python -m venv venv --without-pip
    if ($LASTEXITCODE -ne 0) {
        Write-Host "✗ 创建虚拟环境失败，尝试其他方法..." -ForegroundColor Red
        # 尝试使用virtualenv
        pip install virtualenv
        virtualenv venv
        if ($LASTEXITCODE -ne 0) {
            Write-Host "✗ 创建虚拟环境失败" -ForegroundColor Red
            Read-Host "按任意键退出"
            exit 1
        }
    }
    Write-Host "✓ 虚拟环境创建成功" -ForegroundColor Green
} else {
    Write-Host "✓ 虚拟环境已存在" -ForegroundColor Green
}

# 激活虚拟环境
Write-Host "激活虚拟环境..." -ForegroundColor Yellow
if (Test-Path "venv\Scripts\Activate.ps1") {
    & "venv\Scripts\Activate.ps1"
} elseif (Test-Path "venv\Scripts\activate.bat") {
    & "venv\Scripts\activate.bat"
} else {
    Write-Host "✗ 无法找到虚拟环境激活脚本" -ForegroundColor Red
    Read-Host "按任意键退出"
    exit 1
}

# 升级pip
Write-Host "升级pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# 检查requirements.txt是否存在
if (-not (Test-Path "requirements.txt")) {
    Write-Host "✗ 未找到requirements.txt文件" -ForegroundColor Red
    Read-Host "按任意键退出"
    exit 1
}

# 安装依赖
Write-Host "安装依赖包..." -ForegroundColor Yellow
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ 安装依赖包失败，尝试使用国内镜像..." -ForegroundColor Red
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
    if ($LASTEXITCODE -ne 0) {
        Write-Host "✗ 依赖包安装失败" -ForegroundColor Red
        Read-Host "按任意键退出"
        exit 1
    }
}
Write-Host "✓ 依赖包安装成功" -ForegroundColor Green

# 检查.env文件是否存在
if (-not (Test-Path ".env")) {
    Write-Host "⚠ 未找到.env文件，请确保已正确配置环境变量" -ForegroundColor Yellow
    Write-Host "您可以复制.env文件并修改其中的配置" -ForegroundColor Yellow
    Read-Host "按任意键继续"
}

# 检查MySQL连接
Write-Host "检查MySQL连接..." -ForegroundColor Yellow
try {
    mysql -u root -p1234 -e "SELECT 1;" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ MySQL连接成功" -ForegroundColor Green
        
        # 创建数据库
        Write-Host "创建数据库..." -ForegroundColor Yellow
        mysql -u root -p1234 -e "CREATE DATABASE IF NOT EXISTS aublog CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ 数据库创建成功" -ForegroundColor Green
        } else {
            Write-Host "⚠ 数据库可能已存在" -ForegroundColor Yellow
        }
    } else {
        Write-Host "✗ MySQL连接失败，请检查MySQL服务是否启动，密码是否正确" -ForegroundColor Red
        Write-Host "如果密码不是1234，请修改.env文件中的DATABASE_URL" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠ 无法连接MySQL，请确保MySQL已安装并启动" -ForegroundColor Yellow
}

# 询问是否初始化示例数据
Write-Host ""
$initData = Read-Host "是否初始化示例数据？(y/n)"
if ($initData -eq "y" -or $initData -eq "Y") {
    Write-Host "初始化示例数据..." -ForegroundColor Yellow
    python init_db.py
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ 示例数据初始化成功" -ForegroundColor Green
    } else {
        Write-Host "⚠ 示例数据初始化失败，可能数据已存在" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "启动博客应用..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "访问地址: http://localhost:5000" -ForegroundColor Green
Write-Host "管理后台: http://localhost:5000/admin" -ForegroundColor Green
Write-Host "默认管理员: admin / admin123" -ForegroundColor Green
Write-Host ""
Write-Host "按 Ctrl+C 停止服务器" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 启动Flask应用
python run.py

Read-Host "按任意键退出"
