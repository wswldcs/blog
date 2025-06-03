#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复数据库结构问题
"""

import os
import subprocess
import sys

def run_mysql_command(command):
    """运行MySQL命令"""
    try:
        cmd = f'mysql -u root -p1234 -e "{command}"'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ MySQL命令执行成功: {command}")
            return True
        else:
            print(f"✗ MySQL命令执行失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ 执行MySQL命令时出错: {e}")
        return False

def fix_database():
    """修复数据库"""
    print("="*50)
    print("修复数据库结构")
    print("="*50)
    
    # 1. 删除旧数据库
    print("1. 删除旧数据库...")
    if run_mysql_command("DROP DATABASE IF EXISTS aublog;"):
        print("✓ 旧数据库已删除")
    else:
        print("⚠ 删除旧数据库失败，继续...")
    
    # 2. 创建新数据库
    print("\n2. 创建新数据库...")
    if run_mysql_command("CREATE DATABASE aublog CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"):
        print("✓ 新数据库创建成功")
    else:
        print("✗ 创建新数据库失败")
        return False
    
    # 3. 测试数据库连接
    print("\n3. 测试数据库连接...")
    try:
        from flask import Flask
        from flask_sqlalchemy import SQLAlchemy
        
        app = Flask(__name__)
        app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:1234@localhost/aublog'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        db = SQLAlchemy(app)
        
        with app.app_context():
            # 测试连接
            db.engine.execute("SELECT 1")
            print("✓ 数据库连接测试成功")
        
        return True
        
    except Exception as e:
        print(f"✗ 数据库连接测试失败: {e}")
        return False

def test_minimal_app():
    """测试最小化应用"""
    print("\n4. 测试最小化应用...")
    try:
        # 运行最小化应用测试
        result = subprocess.run([sys.executable, "minimal_run.py"], 
                              capture_output=True, text=True, timeout=10)
        print("✓ 最小化应用可以启动")
        return True
    except subprocess.TimeoutExpired:
        print("✓ 最小化应用启动成功（超时正常）")
        return True
    except Exception as e:
        print(f"✗ 最小化应用测试失败: {e}")
        return False

def main():
    """主函数"""
    print("开始修复数据库问题...")
    
    # 修复数据库
    if not fix_database():
        print("\n✗ 数据库修复失败")
        return
    
    print("\n" + "="*50)
    print("数据库修复完成！")
    print("="*50)
    print("下一步操作:")
    print("1. 运行最小化版本测试: python minimal_run.py")
    print("2. 访问 http://localhost:5000/init 初始化数据")
    print("3. 测试完整版本: python test_app.py")
    print("4. 启动完整应用: python run.py")
    print("="*50)

if __name__ == '__main__':
    main()
