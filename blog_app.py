#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Railway博客应用 - 完整版本
"""

import os
from flask import Flask, render_template_string, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# 创建扩展实例
db = SQLAlchemy()
login_manager = LoginManager()

def create_blog_app():
    """创建博客应用"""
    app = Flask(__name__)
    
    # 基本配置
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'blog-secret-key-2024')
    
    # 数据库配置
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
        print(f"✅ 使用Railway MySQL: {database_url[:50]}...")
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
        print("⚠️ 使用SQLite数据库")
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # 博客配置
    app.config['BLOG_TITLE'] = os.environ.get('BLOG_TITLE', '我的个人博客')
    app.config['BLOG_SUBTITLE'] = os.environ.get('BLOG_SUBTITLE', '分享技术与生活')
    
    # 初始化扩展
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    
    return app

# 数据库模型
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    is_published = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

def init_database(app):
    """初始化数据库"""
    with app.app_context():
        try:
            print("🔧 初始化数据库...")
            db.create_all()
            
            # 创建默认管理员
            if not User.query.first():
                admin = User(
                    username='admin',
                    email='admin@blog.com',
                    is_admin=True
                )
                admin.set_password('admin123')
                db.session.add(admin)
                
                # 创建示例文章
                post = Post(
                    title='欢迎来到我的博客',
                    content='''
                    <h2>欢迎！</h2>
                    <p>这是我的第一篇博客文章。</p>
                    <p>这个博客使用以下技术构建：</p>
                    <ul>
                        <li>Flask - Python Web框架</li>
                        <li>MySQL - 数据库</li>
                        <li>Railway - 部署平台</li>
                    </ul>
                    <p>感谢访问！</p>
                    ''',
                    slug='welcome',
                    is_published=True
                )
                db.session.add(post)
                
                db.session.commit()
                print("✅ 默认数据创建成功")
                print("👤 管理员账号: admin")
                print("🔑 管理员密码: admin123")
            
            return True
        except Exception as e:
            print(f"❌ 数据库初始化失败: {e}")
            return False

def create_routes(app):
    """创建路由"""
    
    @app.route('/')
    def index():
        posts = Post.query.filter_by(is_published=True).order_by(Post.created_at.desc()).all()
        return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>{{ config.BLOG_TITLE }}</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; line-height: 1.6; }
                .header { text-align: center; margin-bottom: 40px; padding: 20px; background: #f8f9fa; border-radius: 10px; }
                .post { margin-bottom: 30px; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }
                .post-title { color: #333; margin-bottom: 10px; }
                .post-meta { color: #666; font-size: 14px; margin-bottom: 15px; }
                .post-content { color: #444; }
                .admin-link { position: fixed; top: 20px; right: 20px; background: #007bff; color: white; padding: 10px; border-radius: 5px; text-decoration: none; }
                .no-posts { text-align: center; color: #666; margin: 40px 0; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{{ config.BLOG_TITLE }}</h1>
                <p>{{ config.BLOG_SUBTITLE }}</p>
            </div>
            
            {% if posts %}
                {% for post in posts %}
                <article class="post">
                    <h2 class="post-title">{{ post.title }}</h2>
                    <div class="post-meta">发布于 {{ post.created_at.strftime('%Y-%m-%d %H:%M') }}</div>
                    <div class="post-content">{{ post.content|safe }}</div>
                </article>
                {% endfor %}
            {% else %}
                <div class="no-posts">
                    <h3>暂无文章</h3>
                    <p>请登录管理后台添加文章</p>
                </div>
            {% endif %}
            
            <a href="{{ url_for('login') }}" class="admin-link">管理后台</a>
        </body>
        </html>
        ''', posts=posts)
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            user = User.query.filter_by(username=username).first()
            
            if user and user.check_password(password):
                login_user(user)
                return redirect(url_for('admin'))
            else:
                flash('用户名或密码错误')
        
        return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>登录 - {{ config.BLOG_TITLE }}</title>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial, sans-serif; max-width: 400px; margin: 100px auto; padding: 20px; }
                .form-group { margin-bottom: 15px; }
                label { display: block; margin-bottom: 5px; }
                input[type="text"], input[type="password"] { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
                button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
                .alert { color: red; margin-bottom: 15px; }
            </style>
        </head>
        <body>
            <h2>登录管理后台</h2>
            {% with messages = get_flashed_messages() %}
                {% if messages %}
                    {% for message in messages %}
                        <div class="alert">{{ message }}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            <form method="post">
                <div class="form-group">
                    <label>用户名:</label>
                    <input type="text" name="username" required>
                </div>
                <div class="form-group">
                    <label>密码:</label>
                    <input type="password" name="password" required>
                </div>
                <button type="submit">登录</button>
            </form>
            <p><a href="{{ url_for('index') }}">返回首页</a></p>
        </body>
        </html>
        ''')
    
    @app.route('/admin')
    @login_required
    def admin():
        posts = Post.query.order_by(Post.created_at.desc()).all()
        return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>管理后台 - {{ config.BLOG_TITLE }}</title>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial, sans-serif; max-width: 1000px; margin: 0 auto; padding: 20px; }
                .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; }
                .btn { background: #007bff; color: white; padding: 8px 16px; text-decoration: none; border-radius: 4px; }
                .btn-danger { background: #dc3545; }
                table { width: 100%; border-collapse: collapse; }
                th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
                th { background: #f8f9fa; }
                .status { padding: 4px 8px; border-radius: 4px; font-size: 12px; }
                .published { background: #d4edda; color: #155724; }
                .draft { background: #f8d7da; color: #721c24; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>管理后台</h1>
                <div>
                    <a href="{{ url_for('new_post') }}" class="btn">新建文章</a>
                    <a href="{{ url_for('logout') }}" class="btn btn-danger">退出</a>
                </div>
            </div>
            
            <h2>文章列表</h2>
            <table>
                <thead>
                    <tr>
                        <th>标题</th>
                        <th>状态</th>
                        <th>创建时间</th>
                        <th>操作</th>
                    </tr>
                </thead>
                <tbody>
                    {% for post in posts %}
                    <tr>
                        <td>{{ post.title }}</td>
                        <td>
                            <span class="status {{ 'published' if post.is_published else 'draft' }}">
                                {{ '已发布' if post.is_published else '草稿' }}
                            </span>
                        </td>
                        <td>{{ post.created_at.strftime('%Y-%m-%d %H:%M') }}</td>
                        <td>
                            <a href="{{ url_for('edit_post', id=post.id) }}">编辑</a>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            
            <p><a href="{{ url_for('index') }}">返回首页</a></p>
        </body>
        </html>
        ''', posts=posts)
    
    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('index'))

    @app.route('/new_post', methods=['GET', 'POST'])
    @login_required
    def new_post():
        if request.method == 'POST':
            title = request.form['title']
            content = request.form['content']
            slug = request.form['slug']
            is_published = 'is_published' in request.form

            post = Post(title=title, content=content, slug=slug, is_published=is_published)
            db.session.add(post)
            db.session.commit()
            flash('文章创建成功！')
            return redirect(url_for('admin'))

        return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>新建文章 - {{ config.BLOG_TITLE }}</title>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
                .form-group { margin-bottom: 15px; }
                label { display: block; margin-bottom: 5px; font-weight: bold; }
                input[type="text"], textarea { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
                textarea { height: 200px; resize: vertical; }
                button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
                .checkbox { width: auto; margin-right: 5px; }
                .alert { color: green; margin-bottom: 15px; }
            </style>
        </head>
        <body>
            <h1>新建文章</h1>
            {% with messages = get_flashed_messages() %}
                {% if messages %}
                    {% for message in messages %}
                        <div class="alert">{{ message }}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            <form method="post">
                <div class="form-group">
                    <label>标题:</label>
                    <input type="text" name="title" required>
                </div>
                <div class="form-group">
                    <label>URL别名:</label>
                    <input type="text" name="slug" required>
                </div>
                <div class="form-group">
                    <label>内容:</label>
                    <textarea name="content" required></textarea>
                </div>
                <div class="form-group">
                    <label>
                        <input type="checkbox" name="is_published" class="checkbox"> 立即发布
                    </label>
                </div>
                <button type="submit">创建文章</button>
                <a href="{{ url_for('admin') }}" style="margin-left: 10px;">返回管理</a>
            </form>
        </body>
        </html>
        ''')

    @app.route('/edit_post/<int:id>', methods=['GET', 'POST'])
    @login_required
    def edit_post(id):
        post = db.session.get(Post, id)
        if not post:
            flash('文章不存在')
            return redirect(url_for('admin'))

        if request.method == 'POST':
            post.title = request.form['title']
            post.content = request.form['content']
            post.slug = request.form['slug']
            post.is_published = 'is_published' in request.form
            db.session.commit()
            flash('文章更新成功！')
            return redirect(url_for('admin'))

        return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>编辑文章 - {{ config.BLOG_TITLE }}</title>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
                .form-group { margin-bottom: 15px; }
                label { display: block; margin-bottom: 5px; font-weight: bold; }
                input[type="text"], textarea { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
                textarea { height: 200px; resize: vertical; }
                button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
                .checkbox { width: auto; margin-right: 5px; }
                .alert { color: green; margin-bottom: 15px; }
            </style>
        </head>
        <body>
            <h1>编辑文章</h1>
            {% with messages = get_flashed_messages() %}
                {% if messages %}
                    {% for message in messages %}
                        <div class="alert">{{ message }}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            <form method="post">
                <div class="form-group">
                    <label>标题:</label>
                    <input type="text" name="title" value="{{ post.title }}" required>
                </div>
                <div class="form-group">
                    <label>URL别名:</label>
                    <input type="text" name="slug" value="{{ post.slug }}" required>
                </div>
                <div class="form-group">
                    <label>内容:</label>
                    <textarea name="content" required>{{ post.content }}</textarea>
                </div>
                <div class="form-group">
                    <label>
                        <input type="checkbox" name="is_published" class="checkbox" {{ 'checked' if post.is_published else '' }}> 发布状态
                    </label>
                </div>
                <button type="submit">更新文章</button>
                <a href="{{ url_for('admin') }}" style="margin-left: 10px;">返回管理</a>
            </form>
        </body>
        </html>
        ''', post=post)

    @app.route('/health')
    def health():
        return {'status': 'ok', 'app': 'blog_app.py', 'database': 'connected' if os.environ.get('DATABASE_URL') else 'sqlite'}

# 创建应用
app = create_blog_app()
create_routes(app)

if __name__ == '__main__':
    print("="*60)
    print("🚀 启动Railway博客应用")
    print("📝 这是完整的博客系统")
    print("="*60)
    
    # 初始化数据库
    if init_database(app):
        port = int(os.environ.get('PORT', 8080))
        print(f"🌐 应用启动在端口: {port}")
        app.run(host='0.0.0.0', port=port, debug=False)
    else:
        print("❌ 数据库初始化失败，应用退出")
        exit(1)
