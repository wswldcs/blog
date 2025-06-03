#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
部署脚本
用于将博客部署到生产环境
"""

import os
import sys
import subprocess
import shutil
from datetime import datetime

def run_command(command, cwd=None):
    """运行命令"""
    print(f"执行命令: {command}")
    try:
        result = subprocess.run(command, shell=True, cwd=cwd, 
                              capture_output=True, text=True, check=True)
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"命令执行失败: {e}")
        if e.stderr:
            print(f"错误信息: {e.stderr}")
        return False

def backup_database():
    """备份数据库"""
    print("正在备份数据库...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"backup/blog_backup_{timestamp}.sql"
    
    # 创建备份目录
    os.makedirs("backup", exist_ok=True)
    
    # 备份MySQL数据库
    command = f"mysqldump -u root -p1234 aublog > {backup_file}"
    if run_command(command):
        print(f"数据库备份成功: {backup_file}")
        return True
    else:
        print("数据库备份失败")
        return False

def update_dependencies():
    """更新依赖"""
    print("正在更新依赖...")
    commands = [
        "pip install --upgrade pip",
        "pip install -r requirements.txt --upgrade"
    ]
    
    for command in commands:
        if not run_command(command):
            return False
    
    print("依赖更新完成")
    return True

def run_migrations():
    """运行数据库迁移"""
    print("正在运行数据库迁移...")
    commands = [
        "flask db upgrade"
    ]
    
    for command in commands:
        if not run_command(command):
            return False
    
    print("数据库迁移完成")
    return True

def collect_static():
    """收集静态文件"""
    print("正在收集静态文件...")
    
    # 这里可以添加静态文件压缩、合并等操作
    # 例如压缩CSS、JS文件
    
    print("静态文件收集完成")
    return True

def restart_service():
    """重启服务"""
    print("正在重启服务...")
    
    # 这里根据实际部署环境调整
    # 例如重启Gunicorn、Nginx等
    commands = [
        # "sudo systemctl restart aublog",
        # "sudo systemctl restart nginx"
    ]
    
    for command in commands:
        if command.strip():  # 跳过空命令
            if not run_command(command):
                return False
    
    print("服务重启完成")
    return True

def deploy():
    """主部署函数"""
    print("=" * 50)
    print("开始部署博客应用")
    print("=" * 50)
    
    steps = [
        ("备份数据库", backup_database),
        ("更新依赖", update_dependencies),
        ("运行迁移", run_migrations),
        ("收集静态文件", collect_static),
        ("重启服务", restart_service)
    ]
    
    for step_name, step_func in steps:
        print(f"\n步骤: {step_name}")
        print("-" * 30)
        
        if not step_func():
            print(f"部署失败: {step_name}")
            return False
    
    print("\n" + "=" * 50)
    print("部署完成！")
    print("=" * 50)
    return True

def quick_deploy():
    """快速部署（跳过备份）"""
    print("=" * 50)
    print("快速部署模式")
    print("=" * 50)
    
    steps = [
        ("更新依赖", update_dependencies),
        ("收集静态文件", collect_static),
        ("重启服务", restart_service)
    ]
    
    for step_name, step_func in steps:
        print(f"\n步骤: {step_name}")
        print("-" * 30)
        
        if not step_func():
            print(f"部署失败: {step_name}")
            return False
    
    print("\n" + "=" * 50)
    print("快速部署完成！")
    print("=" * 50)
    return True

def rollback():
    """回滚到上一个版本"""
    print("=" * 50)
    print("回滚功能")
    print("=" * 50)
    
    # 这里可以实现版本回滚逻辑
    print("回滚功能待实现...")
    
def show_status():
    """显示应用状态"""
    print("=" * 50)
    print("应用状态")
    print("=" * 50)
    
    # 检查服务状态
    commands = [
        "ps aux | grep python",
        # "sudo systemctl status aublog",
        # "sudo systemctl status nginx"
    ]
    
    for command in commands:
        if command.strip():
            print(f"\n{command}:")
            run_command(command)

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法:")
        print("  python deploy.py deploy     - 完整部署")
        print("  python deploy.py quick      - 快速部署")
        print("  python deploy.py rollback   - 回滚")
        print("  python deploy.py status     - 查看状态")
        return
    
    command = sys.argv[1].lower()
    
    if command == "deploy":
        deploy()
    elif command == "quick":
        quick_deploy()
    elif command == "rollback":
        rollback()
    elif command == "status":
        show_status()
    else:
        print(f"未知命令: {command}")

if __name__ == "__main__":
    main()
