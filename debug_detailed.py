#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细调试脚本
逐步导入模块来定位问题
"""

import os
import sys
import traceback

def test_step(step_name, test_func):
    """测试步骤"""
    print(f"\n{step_name}...")
    try:
        result = test_func()
        print(f"✓ {step_name}成功")
        return result
    except Exception as e:
        print(f"✗ {step_name}失败: {e}")
        traceback.print_exc()
        return None

def step1_basic_imports():
    """步骤1: 基础导入"""
    from flask import Flask
    from flask_sqlalchemy import SQLAlchemy
    from flask_login import LoginManager
    from flask_admin import Admin
    return True

def step2_create_app():
    """步骤2: 创建基础应用"""
    from flask import Flask
    from flask_sqlalchemy import SQLAlchemy
    from flask_login import LoginManager
    
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test-key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:1234@localhost/aublog'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db = SQLAlchemy(app)
    login_manager = LoginManager(app)
    
    return app, db

def step3_import_models():
    """步骤3: 导入模型"""
    # 先设置环境变量
    os.environ['DATABASE_URL'] = 'mysql+pymysql://root:1234@localhost/aublog'
    
    from app.models import User, Post, Category, Tag, Comment
    return True

def step4_import_routes():
    """步骤4: 导入路由"""
    from app.routes import main, api
    return True

def step5_import_admin_routes():
    """步骤5: 导入管理员路由"""
    from app.routes import admin
    return True

def step6_import_admin_views():
    """步骤6: 导入管理员视图"""
    from app import admin_views
    return True

def step7_create_full_app():
    """步骤7: 创建完整应用"""
    from app import create_app
    app = create_app()
    return app

def main():
    """主函数"""
    print("="*60)
    print("详细调试 - 逐步定位问题")
    print("="*60)
    
    # 测试步骤
    steps = [
        ("步骤1: 基础导入", step1_basic_imports),
        ("步骤2: 创建基础应用", step2_create_app),
        ("步骤3: 导入模型", step3_import_models),
        ("步骤4: 导入主路由", step4_import_routes),
        ("步骤5: 导入管理员路由", step5_import_admin_routes),
        ("步骤6: 导入管理员视图", step6_import_admin_views),
        ("步骤7: 创建完整应用", step7_create_full_app),
    ]
    
    for step_name, step_func in steps:
        result = test_step(step_name, step_func)
        if result is None:
            print(f"\n✗ 在 {step_name} 处发现问题！")
            break
    else:
        print("\n✓ 所有步骤都通过了！")
        print("应用应该可以正常启动。")

if __name__ == '__main__':
    main()
