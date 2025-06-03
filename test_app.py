#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试应用启动
"""

try:
    print("正在导入Flask...")
    from flask import Flask
    print("✓ Flask导入成功")
    
    print("正在导入SQLAlchemy...")
    from flask_sqlalchemy import SQLAlchemy
    print("✓ SQLAlchemy导入成功")
    
    print("正在导入其他依赖...")
    from flask_login import LoginManager
    from flask_admin import Admin
    from flask_migrate import Migrate
    print("✓ 其他依赖导入成功")
    
    print("正在创建应用...")
    from app import create_app
    app = create_app()
    print("✓ 应用创建成功")
    
    print("正在测试数据库连接...")
    with app.app_context():
        from app import db
        db.create_all()
        print("✓ 数据库连接成功")
    
    print("\n" + "="*50)
    print("所有测试通过！应用可以正常启动")
    print("="*50)
    
    # 启动应用
    print("启动应用...")
    app.run(debug=True, host='0.0.0.0', port=5000)
    
except ImportError as e:
    print(f"✗ 导入错误: {e}")
    print("请检查依赖是否正确安装")
except Exception as e:
    print(f"✗ 错误: {e}")
    print("请检查配置和代码")
