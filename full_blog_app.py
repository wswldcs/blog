#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Railway完整博客应用 - 功能丰富版本
"""

import os
from flask import Flask, render_template_string, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import markdown

# 模板定义
INDEX_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{{ config.BLOG_TITLE }}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        :root {
            --primary-color: #667eea;
            --secondary-color: #764ba2;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
        }

        .bg-gradient-primary {
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
        }

        .navbar-brand {
            font-weight: 700;
            font-size: 1.5rem;
        }

        .card {
            border: none;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
        }

        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 20px 40px rgba(0,0,0,0.15);
        }

        .btn-primary {
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
            border: none;
        }

        .btn-primary:hover {
            background: linear-gradient(135deg, var(--secondary-color) 0%, var(--primary-color) 100%);
            transform: translateY(-2px);
        }

        .hero-section {
            min-height: 60vh;
            display: flex;
            align-items: center;
        }

        .sidebar {
            background: #f8f9fa;
            border-radius: 15px;
            padding: 30px;
        }

        .tag {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            margin: 0.25rem;
            border-radius: 50px;
            font-size: 0.875rem;
            text-decoration: none;
            transition: all 0.3s ease;
        }

        .tag:hover {
            transform: translateY(-2px);
            text-decoration: none;
        }

        .post-meta {
            color: #6c757d;
            font-size: 0.9rem;
        }

        .post-meta i {
            margin-right: 0.5rem;
            color: var(--primary-color);
        }

        .stats-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 15px;
            padding: 2rem;
            text-align: center;
            margin-bottom: 1rem;
        }

        .stats-card h3 {
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }

        .footer {
            background: #2c3e50;
            color: white;
            padding: 3rem 0;
            margin-top: 5rem;
        }
    </style>
</head>
<body>
    <!-- 导航栏 -->
    <nav class="navbar navbar-expand-lg navbar-dark bg-gradient-primary sticky-top">
        <div class="container">
            <a class="navbar-brand" href="{{ url_for('index') }}">
                <i class="fas fa-blog me-2"></i>{{ config.BLOG_TITLE }}
            </a>

            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>

            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav me-auto">
                    <li class="nav-item">
                        <a class="nav-link" href="{{ url_for('index') }}">
                            <i class="fas fa-home me-1"></i>首页
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="{{ url_for('blog') }}">
                            <i class="fas fa-blog me-1"></i>博客
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="{{ url_for('projects') }}">
                            <i class="fas fa-code me-1"></i>项目
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="{{ url_for('about') }}">
                            <i class="fas fa-user me-1"></i>关于
                        </a>
                    </li>
                </ul>

                <ul class="navbar-nav">
                    <li class="nav-item">
                        <a class="nav-link" href="{{ url_for('login') }}">
                            <i class="fas fa-cog me-1"></i>管理
                        </a>
                    </li>
                </ul>
            </div>
        </div>
    </nav>

    <!-- Hero Section -->
    <section class="hero-section bg-gradient-primary text-white">
        <div class="container">
            <div class="row align-items-center">
                <div class="col-lg-6">
                    <h1 class="display-4 fw-bold mb-4">
                        欢迎来到我的博客
                    </h1>
                    <p class="lead mb-4">
                        {{ config.BLOG_SUBTITLE }}
                    </p>
                    <div class="d-flex gap-3">
                        <a href="{{ url_for('blog') }}" class="btn btn-light btn-lg">
                            <i class="fas fa-blog me-2"></i>阅读博客
                        </a>
                        <a href="{{ url_for('about') }}" class="btn btn-outline-light btn-lg">
                            <i class="fas fa-user me-2"></i>了解我
                        </a>
                    </div>
                </div>
                <div class="col-lg-6 text-center">
                    <i class="fas fa-laptop-code fa-10x opacity-75"></i>
                </div>
            </div>
        </div>
    </section>

    <!-- 统计信息 -->
    <section class="py-5">
        <div class="container">
            <div class="row">
                <div class="col-md-3 col-sm-6 mb-4">
                    <div class="stats-card">
                        <h3>{{ stats.total_posts }}</h3>
                        <p class="mb-0">篇文章</p>
                    </div>
                </div>
                <div class="col-md-3 col-sm-6 mb-4">
                    <div class="stats-card">
                        <h3>{{ stats.total_categories }}</h3>
                        <p class="mb-0">个分类</p>
                    </div>
                </div>
                <div class="col-md-3 col-sm-6 mb-4">
                    <div class="stats-card">
                        <h3>{{ stats.total_tags }}</h3>
                        <p class="mb-0">个标签</p>
                    </div>
                </div>
                <div class="col-md-3 col-sm-6 mb-4">
                    <div class="stats-card">
                        <h3>{{ stats.total_views }}</h3>
                        <p class="mb-0">次浏览</p>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- 精选文章 -->
    {% if featured_posts %}
    <section class="py-5 bg-light">
        <div class="container">
            <div class="row mb-5">
                <div class="col-12 text-center">
                    <h2 class="display-5 fw-bold">精选文章</h2>
                    <p class="lead text-muted">推荐阅读的优质内容</p>
                </div>
            </div>

            <div class="row">
                {% for post in featured_posts %}
                <div class="col-lg-4 col-md-6 mb-4">
                    <div class="card h-100">
                        <div class="card-body">
                            <h5 class="card-title">
                                <a href="{{ url_for('post', slug=post.slug) }}" class="text-decoration-none">
                                    {{ post.title }}
                                </a>
                            </h5>
                            <p class="card-text text-muted">{{ post.summary or post.content[:100] + '...' }}</p>
                            <div class="post-meta">
                                <i class="fas fa-calendar-alt"></i>
                                {{ post.created_at.strftime('%Y-%m-%d') }}
                                {% if post.category %}
                                <span class="ms-3">
                                    <i class="fas fa-folder"></i>
                                    {{ post.category.name }}
                                </span>
                                {% endif %}
                            </div>
                        </div>
                        <div class="card-footer bg-transparent">
                            <a href="{{ url_for('post', slug=post.slug) }}" class="btn btn-primary btn-sm">
                                阅读全文 <i class="fas fa-arrow-right ms-1"></i>
                            </a>
                        </div>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
    </section>
    {% endif %}

    <!-- 最新文章和侧边栏 -->
    <section class="py-5">
        <div class="container">
            <div class="row">
                <div class="col-lg-8">
                    <h2 class="mb-4">最新文章</h2>
                    {% for post in recent_posts %}
                    <div class="card mb-4">
                        <div class="card-body">
                            <h5 class="card-title">
                                <a href="{{ url_for('post', slug=post.slug) }}" class="text-decoration-none">
                                    {{ post.title }}
                                </a>
                            </h5>
                            <p class="card-text">{{ post.summary or post.content[:150] + '...' }}</p>
                            <div class="post-meta">
                                <i class="fas fa-calendar-alt"></i>
                                {{ post.created_at.strftime('%Y-%m-%d') }}
                                <span class="ms-3">
                                    <i class="fas fa-eye"></i>
                                    {{ post.view_count }} 次浏览
                                </span>
                                {% if post.category %}
                                <span class="ms-3">
                                    <i class="fas fa-folder"></i>
                                    {{ post.category.name }}
                                </span>
                                {% endif %}
                            </div>
                        </div>
                    </div>
                    {% endfor %}

                    <div class="text-center">
                        <a href="{{ url_for('blog') }}" class="btn btn-primary btn-lg">
                            查看更多文章 <i class="fas fa-arrow-right ms-2"></i>
                        </a>
                    </div>
                </div>

                <!-- 侧边栏 -->
                <div class="col-lg-4">
                    <!-- 分类 -->
                    <div class="sidebar mb-4">
                        <h5 class="mb-3">
                            <i class="fas fa-folder me-2"></i>文章分类
                        </h5>
                        {% for category in categories %}
                        <a href="{{ url_for('blog', category=category.id) }}"
                           class="tag" style="background-color: {{ category.color }}; color: white;">
                            {{ category.name }}
                        </a>
                        {% endfor %}
                    </div>

                    <!-- 标签云 -->
                    <div class="sidebar">
                        <h5 class="mb-3">
                            <i class="fas fa-tags me-2"></i>热门标签
                        </h5>
                        {% for tag in tags %}
                        <a href="{{ url_for('blog', tag=tag.id) }}"
                           class="tag" style="background-color: {{ tag.color }}; color: white;">
                            {{ tag.name }}
                        </a>
                        {% endfor %}
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- 页脚 -->
    <footer class="footer">
        <div class="container">
            <div class="row">
                <div class="col-md-6">
                    <h5>{{ config.BLOG_TITLE }}</h5>
                    <p class="text-muted">{{ config.BLOG_SUBTITLE }}</p>
                </div>
                <div class="col-md-6 text-md-end">
                    <div class="social-links">
                        <a href="#" class="text-white me-3"><i class="fab fa-github fa-lg"></i></a>
                        <a href="#" class="text-white me-3"><i class="fab fa-twitter fa-lg"></i></a>
                        <a href="#" class="text-white me-3"><i class="fab fa-linkedin fa-lg"></i></a>
                    </div>
                    <p class="text-muted mt-3">© 2024 {{ config.BLOG_TITLE }}. All rights reserved.</p>
                </div>
            </div>
        </div>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
'''

ADMIN_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>管理后台 - {{ config.BLOG_TITLE }}</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    <nav class="navbar navbar-dark bg-dark">
        <div class="container-fluid">
            <span class="navbar-brand">
                <i class="fas fa-cog me-2"></i>管理后台
            </span>
            <div>
                <a href="{{ url_for('index') }}" class="btn btn-outline-light btn-sm me-2">
                    <i class="fas fa-home me-1"></i>返回首页
                </a>
                <a href="{{ url_for('logout') }}" class="btn btn-outline-danger btn-sm">
                    <i class="fas fa-sign-out-alt me-1"></i>退出
                </a>
            </div>
        </div>
    </nav>

    <div class="container-fluid py-4">
        <div class="row">
            <div class="col-12">
                <div class="d-flex justify-content-between align-items-center mb-4">
                    <h1>文章管理</h1>
                    <button class="btn btn-primary" onclick="alert('功能开发中，敬请期待！')">
                        <i class="fas fa-plus me-2"></i>新建文章
                    </button>
                </div>

                <div class="card">
                    <div class="card-body">
                        <div class="table-responsive">
                            <table class="table table-hover">
                                <thead>
                                    <tr>
                                        <th>标题</th>
                                        <th>分类</th>
                                        <th>状态</th>
                                        <th>浏览量</th>
                                        <th>创建时间</th>
                                        <th>操作</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for post in posts %}
                                    <tr>
                                        <td>
                                            <a href="{{ url_for('post', slug=post.slug) }}" target="_blank" class="text-decoration-none">
                                                {{ post.title }}
                                            </a>
                                        </td>
                                        <td>
                                            {% if post.category %}
                                            <span class="badge" style="background-color: {{ post.category.color }};">
                                                {{ post.category.name }}
                                            </span>
                                            {% else %}
                                            <span class="text-muted">未分类</span>
                                            {% endif %}
                                        </td>
                                        <td>
                                            {% if post.is_published %}
                                            <span class="badge bg-success">已发布</span>
                                            {% else %}
                                            <span class="badge bg-secondary">草稿</span>
                                            {% endif %}
                                            {% if post.is_featured %}
                                            <span class="badge bg-warning text-dark ms-1">精选</span>
                                            {% endif %}
                                        </td>
                                        <td>{{ post.view_count }}</td>
                                        <td>{{ post.created_at.strftime('%Y-%m-%d %H:%M') }}</td>
                                        <td>
                                            <button class="btn btn-sm btn-outline-primary" onclick="alert('功能开发中！')">
                                                <i class="fas fa-edit"></i>
                                            </button>
                                            <button class="btn btn-sm btn-outline-danger" onclick="alert('功能开发中！')">
                                                <i class="fas fa-trash"></i>
                                            </button>
                                        </td>
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
'''

# 简化的其他模板
BLOG_TEMPLATE = LOGIN_TEMPLATE = PROJECTS_TEMPLATE = ABOUT_TEMPLATE = INDEX_TEMPLATE

# 创建扩展实例
db = SQLAlchemy()
login_manager = LoginManager()

# 多对多关系表
post_tags = db.Table('post_tags',
    db.Column('post_id', db.Integer, db.ForeignKey('post.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)

def create_blog_app():
    """创建博客应用"""
    app = Flask(__name__)
    
    # 基本配置
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'blog-secret-key-2024')
    app.config['POSTS_PER_PAGE'] = 5
    
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
    
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.Text)
    color = db.Column(db.String(7), default='#007bff')  # 颜色代码
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    posts = db.relationship('Post', backref='category', lazy='dynamic')

class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    color = db.Column(db.String(7), default='#6c757d')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    summary = db.Column(db.Text)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    featured_image = db.Column(db.String(200))
    is_published = db.Column(db.Boolean, default=False)
    is_featured = db.Column(db.Boolean, default=False)
    view_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    
    tags = db.relationship('Tag', secondary=post_tags, lazy='subquery',
                          backref=db.backref('posts', lazy=True))
    comments = db.relationship('Comment', backref='post', lazy='dynamic', cascade='all, delete-orphan')
    
    def get_html_content(self):
        """将Markdown转换为HTML"""
        return markdown.markdown(self.content, extensions=['fenced_code', 'tables', 'toc'])

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    author_name = db.Column(db.String(80), nullable=False)
    author_email = db.Column(db.String(120), nullable=False)
    author_website = db.Column(db.String(200))
    is_approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    tech_stack = db.Column(db.String(200))  # 技术栈，逗号分隔
    github_url = db.Column(db.String(200))
    demo_url = db.Column(db.String(200))
    image = db.Column(db.String(200))
    is_featured = db.Column(db.Boolean, default=False)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def get_tech_list(self):
        return [tech.strip() for tech in self.tech_stack.split(',') if tech.strip()]

class Link(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    avatar = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Timeline(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date = db.Column(db.Date, nullable=False)
    icon = db.Column(db.String(50), default='fas fa-star')
    color = db.Column(db.String(7), default='#007bff')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

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
                
                # 创建分类
                categories = [
                    {'name': '技术分享', 'description': '编程技术和开发经验', 'color': '#007bff'},
                    {'name': '生活随笔', 'description': '日常生活和个人感悟', 'color': '#28a745'},
                    {'name': '学习笔记', 'description': '学习过程中的记录和总结', 'color': '#ffc107'},
                    {'name': '项目实战', 'description': '实际项目开发经验', 'color': '#dc3545'}
                ]
                
                for cat_data in categories:
                    category = Category(**cat_data)
                    db.session.add(category)
                
                # 创建标签
                tags = [
                    {'name': 'Python', 'color': '#3776ab'},
                    {'name': 'Flask', 'color': '#000000'},
                    {'name': 'JavaScript', 'color': '#f7df1e'},
                    {'name': 'Vue.js', 'color': '#4fc08d'},
                    {'name': 'MySQL', 'color': '#4479a1'},
                    {'name': '前端', 'color': '#61dafb'},
                    {'name': '后端', 'color': '#68217a'},
                    {'name': '全栈', 'color': '#ff6b6b'}
                ]
                
                for tag_data in tags:
                    tag = Tag(**tag_data)
                    db.session.add(tag)
                
                db.session.commit()
                
                # 获取创建的分类和标签
                tech_category = Category.query.filter_by(name='技术分享').first()
                life_category = Category.query.filter_by(name='生活随笔').first()
                python_tag = Tag.query.filter_by(name='Python').first()
                flask_tag = Tag.query.filter_by(name='Flask').first()
                
                # 创建示例文章
                posts_data = [
                    {
                        'title': '欢迎来到我的博客',
                        'slug': 'welcome',
                        'summary': '这是我的第一篇博客文章，介绍了博客的技术栈和功能特性。',
                        'content': '''# 欢迎来到我的博客！

这是我的第一篇博客文章。感谢你的访问！

## 技术栈

这个博客使用以下技术构建：

- **Flask** - Python Web框架
- **MySQL** - 数据库
- **Bootstrap 5** - 前端框架
- **Railway** - 部署平台

## 功能特性

- 📝 文章管理系统
- 🏷️ 分类标签功能
- 💬 评论系统
- 🔍 搜索功能
- 📊 统计信息
- 🎨 响应式设计

希望你喜欢这个博客！''',
                        'category': tech_category,
                        'tags': [python_tag, flask_tag],
                        'is_published': True,
                        'is_featured': True
                    }
                ]
                
                for post_data in posts_data:
                    tags = post_data.pop('tags', [])
                    post = Post(
                        title=post_data['title'],
                        slug=post_data['slug'],
                        content=post_data['content'],
                        summary=post_data['summary'],
                        category=post_data['category'],
                        is_published=post_data['is_published'],
                        is_featured=post_data['is_featured'],
                        user_id=admin.id
                    )
                    post.tags = tags
                    db.session.add(post)
                
                # 创建示例项目
                projects = [
                    {
                        'name': '个人博客系统',
                        'description': '基于Flask的功能完整的个人博客系统，支持文章管理、分类标签、评论系统等功能。',
                        'tech_stack': 'Python, Flask, MySQL, Bootstrap',
                        'github_url': 'https://github.com/wswldcs/blog',
                        'is_featured': True
                    }
                ]
                
                for proj_data in projects:
                    project = Project(**proj_data)
                    db.session.add(project)
                
                db.session.commit()
                print("✅ 默认数据创建成功")
                print("👤 管理员账号: admin")
                print("🔑 管理员密码: admin123")
            
            return True
        except Exception as e:
            print(f"❌ 数据库初始化失败: {e}")
            return False

# 创建应用
app = create_blog_app()

# 添加路由
@app.route('/')
def index():
    """首页"""
    # 获取精选文章
    featured_posts = Post.query.filter_by(is_published=True, is_featured=True).limit(3).all()
    # 获取最新文章
    recent_posts = Post.query.filter_by(is_published=True).order_by(Post.created_at.desc()).limit(5).all()
    # 获取分类
    categories = Category.query.all()
    # 获取热门标签
    tags = Tag.query.limit(10).all()

    # 统计信息
    stats = {
        'total_posts': Post.query.filter_by(is_published=True).count(),
        'total_categories': Category.query.count(),
        'total_tags': Tag.query.count(),
        'total_views': db.session.query(db.func.sum(Post.view_count)).scalar() or 0
    }

    return render_template_string(INDEX_TEMPLATE,
                                featured_posts=featured_posts,
                                recent_posts=recent_posts,
                                categories=categories,
                                tags=tags,
                                stats=stats)

@app.route('/blog')
def blog():
    """博客列表页"""
    page = request.args.get('page', 1, type=int)
    category_id = request.args.get('category', type=int)
    tag_id = request.args.get('tag', type=int)
    search = request.args.get('search', '')

    query = Post.query.filter_by(is_published=True)

    if category_id:
        query = query.filter_by(category_id=category_id)

    if tag_id:
        query = query.filter(Post.tags.any(Tag.id == tag_id))

    if search:
        query = query.filter(Post.title.contains(search) | Post.content.contains(search))

    posts = query.order_by(Post.created_at.desc()).paginate(
        page=page, per_page=app.config['POSTS_PER_PAGE'], error_out=False)

    categories = Category.query.all()
    tags = Tag.query.all()

    return render_template_string(BLOG_TEMPLATE,
                                posts=posts,
                                categories=categories,
                                tags=tags,
                                current_category=category_id,
                                current_tag=tag_id,
                                search_query=search)

@app.route('/post/<slug>')
def post(slug):
    """文章详情页"""
    post = Post.query.filter_by(slug=slug, is_published=True).first_or_404()

    # 增加浏览量
    post.view_count += 1
    db.session.commit()

    # 获取相关文章
    related_posts = []
    if post.category_id:
        related_posts = Post.query.filter(
            Post.id != post.id,
            Post.is_published == True,
            Post.category_id == post.category_id
        ).limit(3).all()

    # 获取评论
    comments = Comment.query.filter_by(post_id=post.id, is_approved=True).order_by(Comment.created_at.asc()).all()

    return render_template_string(POST_TEMPLATE,
                                post=post,
                                related_posts=related_posts,
                                comments=comments)

@app.route('/projects')
def projects():
    """项目展示页"""
    featured_projects = Project.query.filter_by(is_featured=True).order_by(Project.sort_order).all()
    other_projects = Project.query.filter_by(is_featured=False).order_by(Project.sort_order).all()

    return render_template_string(PROJECTS_TEMPLATE,
                                featured_projects=featured_projects,
                                other_projects=other_projects)

@app.route('/about')
def about():
    """关于页面"""
    return render_template_string(ABOUT_TEMPLATE)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """登录"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('admin'))
        else:
            flash('用户名或密码错误')

    return render_template_string(LOGIN_TEMPLATE)

@app.route('/admin')
@login_required
def admin():
    """管理后台"""
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return render_template_string(ADMIN_TEMPLATE, posts=posts)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/health')
def health():
    return {'status': 'ok', 'app': 'full_blog_app.py', 'database': 'connected' if os.environ.get('DATABASE_URL') else 'sqlite'}

if __name__ == '__main__':
    print("="*60)
    print("🚀 启动Railway完整博客应用")
    print("📝 这是功能丰富的博客系统")
    print("="*60)
    
    # 初始化数据库
    if init_database(app):
        port = int(os.environ.get('PORT', 8080))
        print(f"🌐 应用启动在端口: {port}")
        app.run(host='0.0.0.0', port=port, debug=False)
    else:
        print("❌ 数据库初始化失败，应用退出")
        exit(1)
