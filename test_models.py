#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试模型定义
"""

import os
import sys

def test_models():
    """测试模型导入和定义"""
    try:
        print("正在测试模型导入...")
        
        # 设置环境变量
        os.environ['DATABASE_URL'] = 'mysql+pymysql://root:1234@localhost/aublog'
        
        # 导入Flask和扩展
        from flask import Flask
        from flask_sqlalchemy import SQLAlchemy
        from flask_login import LoginManager
        
        # 创建应用
        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'test-key'
        app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:1234@localhost/aublog'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        # 初始化扩展
        db = SQLAlchemy(app)
        login_manager = LoginManager(app)
        
        print("✓ Flask应用创建成功")
        
        # 在应用上下文中测试模型
        with app.app_context():
            # 手动定义模型来测试
            from datetime import datetime
            
            # 关联表
            post_tags = db.Table('post_tags',
                db.Column('post_id', db.Integer, db.ForeignKey('post.id'), primary_key=True),
                db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
            )
            
            class User(db.Model):
                id = db.Column(db.Integer, primary_key=True)
                username = db.Column(db.String(80), unique=True, nullable=False)
                email = db.Column(db.String(120), unique=True, nullable=False)
                is_admin = db.Column(db.Boolean, default=False)
                
                posts = db.relationship('Post', backref='author', lazy='dynamic')
            
            class Category(db.Model):
                id = db.Column(db.Integer, primary_key=True)
                name = db.Column(db.String(80), unique=True, nullable=False)
                
                posts = db.relationship('Post', backref='category', lazy='dynamic')
            
            class Tag(db.Model):
                id = db.Column(db.Integer, primary_key=True)
                name = db.Column(db.String(50), unique=True, nullable=False)
            
            class Post(db.Model):
                id = db.Column(db.Integer, primary_key=True)
                title = db.Column(db.String(200), nullable=False)
                content = db.Column(db.Text, nullable=False)
                
                user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
                category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
                
                tags = db.relationship('Tag', secondary=post_tags, lazy='subquery',
                                      backref=db.backref('posts', lazy=True))
            
            print("✓ 模型定义成功")
            
            # 创建表
            db.create_all()
            print("✓ 数据库表创建成功")
            
            # 测试模型关系
            print("正在测试模型关系...")
            
            # 创建测试数据
            user = User(username='test', email='test@example.com')
            category = Category(name='测试分类')
            tag = Tag(name='测试标签')
            
            db.session.add(user)
            db.session.add(category)
            db.session.add(tag)
            db.session.commit()
            
            post = Post(title='测试文章', content='测试内容', user_id=user.id, category_id=category.id)
            post.tags.append(tag)
            
            db.session.add(post)
            db.session.commit()
            
            print("✓ 测试数据创建成功")
            
            # 测试关系访问
            print(f"文章标题: {post.title}")
            print(f"文章作者: {post.author.username}")
            print(f"文章分类: {post.category.name}")
            print(f"文章标签: {[tag.name for tag in post.tags]}")
            
            print("✓ 模型关系测试成功")
            
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("="*50)
    print("模型测试")
    print("="*50)
    
    if test_models():
        print("\n✓ 所有测试通过！")
    else:
        print("\n✗ 测试失败！")
