#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速启动脚本
自动安装依赖并启动博客
"""

import os
import sys
import subprocess
import platform

def run_command(command, shell=True):
    """运行命令"""
    print(f"执行: {command}")
    try:
        result = subprocess.run(command, shell=shell, check=True, 
                              capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"命令执行失败: {e}")
        if e.stderr:
            print(f"错误: {e.stderr}")
        return False

def check_python():
    """检查Python版本"""
    try:
        version = sys.version_info
        if version.major >= 3 and version.minor >= 8:
            print(f"✓ Python版本: {version.major}.{version.minor}.{version.micro}")
            return True
        else:
            print(f"✗ Python版本过低: {version.major}.{version.minor}.{version.micro}")
            print("需要Python 3.8或更高版本")
            return False
    except:
        print("✗ 无法检测Python版本")
        return False

def install_dependencies():
    """安装依赖"""
    print("\n正在安装依赖包...")
    
    # 升级pip
    if not run_command(f"{sys.executable} -m pip install --upgrade pip"):
        print("pip升级失败，继续安装依赖...")
    
    # 安装依赖
    if run_command(f"{sys.executable} -m pip install -r requirements.txt"):
        print("✓ 依赖安装成功")
        return True
    else:
        print("使用国内镜像重试...")
        if run_command(f"{sys.executable} -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/"):
            print("✓ 依赖安装成功")
            return True
        else:
            print("✗ 依赖安装失败")
            return False

def check_mysql():
    """检查MySQL连接"""
    print("\n检查MySQL连接...")
    try:
        import pymysql
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='1234',
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            # 创建数据库
            cursor.execute("CREATE DATABASE IF NOT EXISTS aublog CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print("✓ 数据库创建成功")
        
        connection.close()
        return True
    except ImportError:
        print("⚠ PyMySQL未安装，正在安装...")
        if run_command(f"{sys.executable} -m pip install PyMySQL"):
            return check_mysql()  # 递归重试
        return False
    except Exception as e:
        print(f"⚠ MySQL连接失败: {e}")
        print("请确保MySQL服务已启动，用户名为root，密码为1234")
        return False

def init_data():
    """初始化数据"""
    print("\n初始化数据库...")
    try:
        from init_db import init_database
        init_database()
        print("✓ 数据初始化成功")
        return True
    except Exception as e:
        print(f"⚠ 数据初始化失败: {e}")
        return False

def start_app():
    """启动应用"""
    print("\n" + "="*50)
    print("启动博客应用...")
    print("="*50)
    print("访问地址: http://localhost:5000")
    print("管理后台: http://localhost:5000/admin")
    print("默认管理员: admin / admin123")
    print("按 Ctrl+C 停止服务器")
    print("="*50)
    
    try:
        from run import app
        app.run(debug=True, host='0.0.0.0', port=5000)
    except Exception as e:
        print(f"启动失败: {e}")
        return False

def main():
    """主函数"""
    print("="*50)
    print("wswldcs的个人博客 - 快速启动")
    print("="*50)
    
    # 检查Python版本
    if not check_python():
        input("按回车键退出...")
        return
    
    # 检查requirements.txt
    if not os.path.exists('requirements.txt'):
        print("✗ 未找到requirements.txt文件")
        input("按回车键退出...")
        return
    
    # 安装依赖
    if not install_dependencies():
        print("✗ 依赖安装失败")
        input("按回车键退出...")
        return
    
    # 检查MySQL
    mysql_ok = check_mysql()
    
    # 初始化数据
    if mysql_ok:
        init_ok = init_data()
        if not init_ok:
            print("⚠ 数据初始化失败，但可以继续启动应用")
    else:
        print("⚠ MySQL连接失败，某些功能可能不可用")
    
    # 启动应用
    try:
        start_app()
    except KeyboardInterrupt:
        print("\n应用已停止")
    except Exception as e:
        print(f"启动失败: {e}")
        input("按回车键退出...")

if __name__ == '__main__':
    main()
