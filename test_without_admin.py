#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试不包含Flask-Admin的应用
"""

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

def create_test_app():
    """创建测试应用（不包含Flask-Admin）"""
    app = Flask(__name__)
    
    # 配置
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:1234@localhost/aublog'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['BLOG_TITLE'] = 'wswldcs的个人博客'
    app.config['BLOG_SUBTITLE'] = '记录生活，分享技术'
    app.config['AUTHOR_NAME'] = 'wswldcs'
    app.config['AUTHOR_EMAIL'] = 'your-email@example.com'
    app.config['ADMIN_USERNAME'] = 'admin'
    app.config['ADMIN_PASSWORD'] = 'admin123'
    
    # 初始化扩展
    db = SQLAlchemy(app)
    login_manager = LoginManager(app)
    login_manager.login_view = 'main.index'
    
    # 导入模型
    from app.models import User, Post, Category, Tag, Comment
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # 注册蓝图
    from app.routes.main import bp as main_bp
    app.register_blueprint(main_bp)
    
    from app.routes.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
    from app.routes.admin import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/manage')
    
    return app

def test_app():
    """测试应用"""
    print("="*50)
    print("测试不包含Flask-Admin的应用")
    print("="*50)
    
    try:
        print("正在创建应用...")
        app = create_test_app()
        print("✓ 应用创建成功")
        
        with app.app_context():
            from app import db
            db.create_all()
            print("✓ 数据库表创建成功")
            
            # 测试模型关系
            from app.models import Post, Category, User
            
            # 创建测试数据
            user = User.query.filter_by(username='admin').first()
            if not user:
                user = User(username='admin', email='admin@example.com', is_admin=True)
                user.set_password('admin123')
                db.session.add(user)
                db.session.commit()
                print("✓ 创建管理员用户")
            
            category = Category.query.first()
            if not category:
                category = Category(name='测试分类', description='测试用分类')
                db.session.add(category)
                db.session.commit()
                print("✓ 创建测试分类")
            
            # 测试Post模型
            post = Post.query.first()
            if not post:
                post = Post(
                    title='测试文章',
                    slug='test-post',
                    content='这是一篇测试文章',
                    summary='测试摘要',
                    is_published=True,
                    user_id=user.id,
                    category_id=category.id
                )
                db.session.add(post)
                db.session.commit()
                print("✓ 创建测试文章")
            
            # 测试关系访问
            print(f"文章标题: {post.title}")
            print(f"文章作者: {post.author.username}")
            print(f"文章分类: {post.category.name}")
            print("✓ 模型关系测试成功")
        
        print("\n✓ 所有测试通过！")
        print("应用可以正常启动（不包含Flask-Admin）")
        
        return app
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == '__main__':
    app = test_app()
    if app:
        print("\n启动测试服务器...")
        print("访问: http://localhost:5000")
        app.run(debug=True, host='0.0.0.0', port=5000)
