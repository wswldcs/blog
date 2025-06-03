#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最小化运行版本
逐步添加功能来定位问题
"""

import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# 创建Flask应用
app = Flask(__name__)

# 配置
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:1234@localhost/aublog'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化扩展
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# 关联表
post_tags = db.Table('post_tags',
    db.Column('post_id', db.Integer, db.ForeignKey('post.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)

# 模型定义
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    posts = db.relationship('Post', backref='category', lazy='dynamic')

class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    content = db.Column(db.Text, nullable=False)
    summary = db.Column(db.Text)
    is_published = db.Column(db.Boolean, default=False)
    is_featured = db.Column(db.Boolean, default=False)
    view_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    
    tags = db.relationship('Tag', secondary=post_tags, lazy='subquery',
                          backref=db.backref('posts', lazy=True))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 路由
@app.route('/')
def index():
    posts = Post.query.filter_by(is_published=True).order_by(Post.created_at.desc()).limit(5).all()
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>wswldcs的个人博客</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container py-5">
            <div class="text-center mb-5">
                <h1 class="display-4">🎉 最小化博客启动成功！</h1>
                <p class="lead">基础功能正常运行</p>
            </div>
            
            <div class="row">
                <div class="col-md-8 mx-auto">
                    <div class="card">
                        <div class="card-body">
                            <h5 class="card-title">✅ 系统状态</h5>
                            <ul class="list-group list-group-flush">
                                <li class="list-group-item">✓ Flask应用运行正常</li>
                                <li class="list-group-item">✓ 数据库连接成功</li>
                                <li class="list-group-item">✓ 模型关系正常</li>
                                <li class="list-group-item">✓ 用户认证配置完成</li>
                            </ul>
                        </div>
                    </div>
                    
                    <div class="card mt-4">
                        <div class="card-body">
                            <h5 class="card-title">📊 数据统计</h5>
                            <p>文章数量: <strong>{Post.query.count()}</strong></p>
                            <p>分类数量: <strong>{Category.query.count()}</strong></p>
                            <p>标签数量: <strong>{Tag.query.count()}</strong></p>
                            <p>用户数量: <strong>{User.query.count()}</strong></p>
                        </div>
                    </div>
                    
                    <div class="card mt-4">
                        <div class="card-body">
                            <h5 class="card-title">🔗 快速链接</h5>
                            <a href="/login" class="btn btn-primary me-2">管理员登录</a>
                            <a href="/init" class="btn btn-success me-2">初始化数据</a>
                            <a href="/test" class="btn btn-info">测试功能</a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    '''

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('登录成功！', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('用户名或密码错误', 'error')
    
    return '''
    <div class="container py-5">
        <div class="row justify-content-center">
            <div class="col-md-4">
                <div class="card">
                    <div class="card-body">
                        <h5 class="card-title">管理员登录</h5>
                        <form method="POST">
                            <div class="mb-3">
                                <label class="form-label">用户名</label>
                                <input type="text" name="username" class="form-control" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">密码</label>
                                <input type="password" name="password" class="form-control" required>
                            </div>
                            <button type="submit" class="btn btn-primary w-100">登录</button>
                        </form>
                        <div class="mt-3">
                            <a href="/" class="btn btn-link">返回首页</a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    '''

@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('需要管理员权限', 'error')
        return redirect(url_for('index'))
    
    return f'''
    <div class="container py-5">
        <h1>管理员仪表板</h1>
        <p>欢迎，{current_user.username}！</p>
        <a href="/logout" class="btn btn-danger">登出</a>
        <a href="/" class="btn btn-secondary">返回首页</a>
    </div>
    '''

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('已登出', 'info')
    return redirect(url_for('index'))

@app.route('/init')
def init_data():
    try:
        # 创建管理员用户
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin', email='admin@example.com', is_admin=True)
            admin.set_password('admin123')
            db.session.add(admin)
        
        # 创建分类
        if not Category.query.first():
            categories = [
                Category(name='技术分享', description='编程技术相关'),
                Category(name='生活随笔', description='日常生活感悟')
            ]
            for cat in categories:
                db.session.add(cat)
        
        # 创建标签
        if not Tag.query.first():
            tags = [Tag(name='Python'), Tag(name='Flask'), Tag(name='Web开发')]
            for tag in tags:
                db.session.add(tag)
        
        db.session.commit()
        return '<h1>✓ 初始化数据成功！</h1><a href="/">返回首页</a>'
    except Exception as e:
        return f'<h1>✗ 初始化失败: {e}</h1><a href="/">返回首页</a>'

@app.route('/test')
def test_relations():
    try:
        # 测试模型关系
        posts = Post.query.all()
        result = '<h1>模型关系测试</h1>'
        
        for post in posts:
            result += f'<p>文章: {post.title}</p>'
            if post.category:
                result += f'<p>分类: {post.category.name}</p>'
            if post.author:
                result += f'<p>作者: {post.author.username}</p>'
            result += '<hr>'
        
        result += '<a href="/">返回首页</a>'
        return result
    except Exception as e:
        return f'<h1>✗ 测试失败: {e}</h1><a href="/">返回首页</a>'

if __name__ == '__main__':
    print("="*50)
    print("启动最小化博客应用")
    print("="*50)
    print("访问地址: http://localhost:5000")
    print("管理员登录: http://localhost:5000/login")
    print("初始化数据: http://localhost:5000/init")
    print("测试功能: http://localhost:5000/test")
    print("="*50)
    
    with app.app_context():
        db.create_all()
        print("✓ 数据库表创建完成")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
