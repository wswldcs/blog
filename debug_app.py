#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试应用启动问题
"""

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_admin import Admin

def create_debug_app():
    """创建调试应用"""
    app = Flask(__name__)
    
    # 基本配置
    app.config['SECRET_KEY'] = 'debug-secret-key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:1234@localhost/aublog'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # 初始化扩展
    db = SQLAlchemy(app)
    login_manager = LoginManager(app)
    
    # 简单的路由
    @app.route('/')
    def index():
        return '''
        <h1>🎉 调试应用启动成功！</h1>
        <p>Flask应用正常运行</p>
        <p>数据库连接正常</p>
        <p><a href="/test-admin">测试Flask-Admin</a></p>
        '''
    
    # 测试Flask-Admin
    try:
        admin = Admin(app, name='测试管理', url='/test-admin')
        print("✓ Flask-Admin初始化成功")
    except Exception as e:
        print(f"✗ Flask-Admin初始化失败: {e}")
    
    return app, db

if __name__ == '__main__':
    print("="*50)
    print("调试应用启动")
    print("="*50)
    
    try:
        app, db = create_debug_app()
        
        with app.app_context():
            db.create_all()
            print("✓ 数据库表创建成功")
        
        print("✓ 应用创建成功")
        print("启动服务器...")
        print("访问: http://localhost:5000")
        print("="*50)
        
        app.run(debug=True, host='0.0.0.0', port=5000)
        
    except Exception as e:
        print(f"✗ 启动失败: {e}")
        import traceback
        traceback.print_exc()
