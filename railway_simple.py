#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Railway简化启动脚本 - 使用SQLite
"""

import os
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# 创建扩展实例
db = SQLAlchemy()
login = LoginManager()

def create_simple_app():
    """创建简化的Flask应用"""
    app = Flask(__name__)

    # 基本配置
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'railway-secret-key')

    # MySQL数据库配置
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        # Railway MySQL数据库
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    else:
        # 本地MySQL配置
        mysql_host = os.environ.get('MYSQL_HOST', 'localhost')
        mysql_user = os.environ.get('MYSQL_USER', 'root')
        mysql_password = os.environ.get('MYSQL_PASSWORD', '1234')
        mysql_database = os.environ.get('MYSQL_DATABASE', 'aublog')
        app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}/{mysql_database}'

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_timeout': 20,
        'max_overflow': 0
    }
    
    # 博客配置
    app.config['BLOG_TITLE'] = os.environ.get('BLOG_TITLE', '我的个人博客')
    app.config['BLOG_SUBTITLE'] = os.environ.get('BLOG_SUBTITLE', '分享技术与生活')
    app.config['BLOG_DOMAIN'] = os.environ.get('BLOG_DOMAIN', 'localhost')
    
    # 初始化扩展
    db.init_app(app)
    login.init_app(app)
    login.login_view = 'login'
    
    return app

# 简化的用户模型
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    
    def set_password(self, password):
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)

# 简化的文章模型
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    is_published = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

def init_database(app):
    """初始化数据库"""
    with app.app_context():
        try:
            print("🔗 数据库连接信息:")
            print(f"   DATABASE_URL: {os.environ.get('DATABASE_URL', '未设置')}")
            print(f"   SQLALCHEMY_DATABASE_URI: {app.config['SQLALCHEMY_DATABASE_URI']}")

            # 测试数据库连接
            with db.engine.connect() as conn:
                conn.execute(db.text('SELECT 1'))
            print("✅ 数据库连接成功")

            # 创建所有表
            db.create_all()
            print("✅ 数据库表创建成功")

            # 创建默认管理员
            if not User.query.first():
                print("🔧 创建默认数据...")
                admin = User(
                    username='admin',
                    email='admin@example.com',
                    is_admin=True
                )
                admin.set_password('admin123')
                db.session.add(admin)

                # 创建示例文章
                post = Post(
                    title='欢迎来到我的博客',
                    content='这是第一篇文章，使用MySQL数据库！',
                    slug='welcome',
                    is_published=True
                )
                db.session.add(post)

                db.session.commit()
                print("✅ 默认数据创建成功")
                print("📝 管理员账号: admin")
                print("🔑 管理员密码: admin123")
            else:
                print("✅ 数据库已有数据，跳过初始化")

            return True
        except Exception as e:
            print(f"❌ 数据库初始化失败: {e}")
            import traceback
            traceback.print_exc()
            return False

def create_routes(app):
    """创建路由"""
    from flask import render_template_string, request, redirect, url_for, flash
    from flask_login import login_user, logout_user, login_required, current_user
    
    @login.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    @app.route('/')
    def index():
        posts = Post.query.filter_by(is_published=True).all()
        return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>{{ config.BLOG_TITLE }}</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
                .header { text-align: center; margin-bottom: 40px; }
                .post { margin-bottom: 30px; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }
                .nav { margin-bottom: 20px; }
                .nav a { margin-right: 15px; text-decoration: none; color: #007bff; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{{ config.BLOG_TITLE }}</h1>
                <p>{{ config.BLOG_SUBTITLE }}</p>
            </div>
            <div class="nav">
                <a href="/">首页</a>
                {% if current_user.is_authenticated %}
                    <a href="/admin">管理</a>
                    <a href="/logout">退出</a>
                {% else %}
                    <a href="/login">登录</a>
                {% endif %}
            </div>
            {% for post in posts %}
            <div class="post">
                <h2>{{ post.title }}</h2>
                <p>{{ post.content }}</p>
                <small>发布时间: {{ post.created_at.strftime('%Y-%m-%d %H:%M') }}</small>
            </div>
            {% endfor %}
            {% if not posts %}
            <p>暂无文章</p>
            {% endif %}
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
        <head><title>登录</title></head>
        <body style="font-family: Arial; max-width: 400px; margin: 100px auto; padding: 20px;">
            <h2>登录</h2>
            <form method="post">
                <p><input type="text" name="username" placeholder="用户名" required style="width: 100%; padding: 10px; margin: 5px 0;"></p>
                <p><input type="password" name="password" placeholder="密码" required style="width: 100%; padding: 10px; margin: 5px 0;"></p>
                <p><button type="submit" style="width: 100%; padding: 10px; background: #007bff; color: white; border: none;">登录</button></p>
            </form>
            <p><a href="/">返回首页</a></p>
        </body>
        </html>
        ''')
    
    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('index'))
    
    @app.route('/admin')
    @login_required
    def admin():
        if not current_user.is_admin:
            return "权限不足", 403
        
        posts = Post.query.all()
        return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head><title>管理后台</title></head>
        <body style="font-family: Arial; max-width: 800px; margin: 0 auto; padding: 20px;">
            <h2>管理后台</h2>
            <p><a href="/">返回首页</a> | <a href="/logout">退出</a></p>
            <h3>所有文章</h3>
            {% for post in posts %}
            <div style="border: 1px solid #ddd; padding: 15px; margin: 10px 0;">
                <h4>{{ post.title }} {% if post.is_published %}(已发布){% else %}(草稿){% endif %}</h4>
                <p>{{ post.content[:100] }}...</p>
            </div>
            {% endfor %}
        </body>
        </html>
        ''', posts=posts)

def main():
    """主函数"""
    print("🚀 启动Railway简化博客应用...")
    
    # 创建应用
    app = create_simple_app()
    
    # 初始化数据库
    if not init_database(app):
        print("❌ 数据库初始化失败，退出")
        sys.exit(1)
    
    # 创建路由
    create_routes(app)
    
    # 获取端口 - Railway通常使用PORT环境变量
    port = int(os.environ.get('PORT', 8080))

    print(f"🌐 应用将在端口 {port} 启动")
    print("🔧 简化版博客已启动")
    print(f"🔗 Railway PORT环境变量: {os.environ.get('PORT', '未设置')}")

    # 启动应用
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == '__main__':
    main()
