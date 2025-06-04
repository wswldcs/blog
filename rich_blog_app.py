#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
功能丰富的个人博客系统
包含：日历、天气、访客信息、社交链接、学习历程、项目展示等完整功能
"""

import os
import json
import requests
import time
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from flask import Flask, render_template_string, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import markdown
import calendar
from geopy.distance import geodesic
from geopy.geocoders import Nominatim

# 创建扩展实例
db = SQLAlchemy()
login_manager = LoginManager()

# 多对多关系表
post_tags = db.Table('post_tags',
    db.Column('post_id', db.Integer, db.ForeignKey('post.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)

def create_app():
    """创建Flask应用"""
    app = Flask(__name__)
    
    # 基本配置
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'rich-blog-secret-2024')
    app.config['POSTS_PER_PAGE'] = 6
    
    # 数据库配置
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
        print(f"✅ 使用Railway MySQL: {database_url[:50]}...")
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///rich_blog.db'
        print("⚠️ 使用SQLite数据库")
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # 博客配置
    app.config['BLOG_TITLE'] = os.environ.get('BLOG_TITLE', 'wswldcs的个人博客')
    app.config['BLOG_SUBTITLE'] = os.environ.get('BLOG_SUBTITLE', '分享技术与生活，记录成长历程')
    app.config['AUTHOR_NAME'] = os.environ.get('AUTHOR_NAME', 'wswldcs')
    app.config['AUTHOR_EMAIL'] = os.environ.get('AUTHOR_EMAIL', 'wswldcs@example.com')
    app.config['AUTHOR_LOCATION'] = os.environ.get('AUTHOR_LOCATION', '中国')
    app.config['AUTHOR_LAT'] = float(os.environ.get('AUTHOR_LAT', '39.9042'))  # 北京纬度
    app.config['AUTHOR_LON'] = float(os.environ.get('AUTHOR_LON', '116.4074'))  # 北京经度
    
    # API配置
    app.config['WEATHER_API_KEY'] = os.environ.get('WEATHER_API_KEY', '')
    app.config['IPAPI_KEY'] = os.environ.get('IPAPI_KEY', '')

    # 文件上传配置
    app.config['UPLOAD_FOLDER'] = 'static/uploads'
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

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
    avatar = db.Column(db.String(200), default='default.jpg')
    bio = db.Column(db.Text)
    location = db.Column(db.String(100))
    website = db.Column(db.String(200))
    github = db.Column(db.String(100))
    twitter = db.Column(db.String(100))
    linkedin = db.Column(db.String(100))
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
    color = db.Column(db.String(7), default='#007bff')
    icon = db.Column(db.String(50), default='fas fa-folder')
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
    like_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    
    tags = db.relationship('Tag', secondary=post_tags, lazy='subquery',
                          backref=db.backref('posts', lazy=True))
    comments = db.relationship('Comment', backref='post', lazy='dynamic', cascade='all, delete-orphan')
    
    def get_html_content(self):
        return markdown.markdown(self.content, extensions=['fenced_code', 'tables', 'toc'])

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    author_name = db.Column(db.String(80), nullable=False)
    author_email = db.Column(db.String(120), nullable=False)
    author_website = db.Column(db.String(200))
    author_ip = db.Column(db.String(45))
    is_approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    tech_stack = db.Column(db.String(200))
    github_url = db.Column(db.String(200))
    demo_url = db.Column(db.String(200))
    image = db.Column(db.String(200))
    is_featured = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(20), default='completed')  # completed, in_progress, planned
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
    category = db.Column(db.String(50), default='friend')  # friend, recommend, tool
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
    category = db.Column(db.String(50), default='education')  # education, work, project, life
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Visitor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(45), nullable=False)
    user_agent = db.Column(db.Text)
    country = db.Column(db.String(100))
    city = db.Column(db.String(100))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    distance_km = db.Column(db.Float)
    visit_count = db.Column(db.Integer, default=1)
    first_visit = db.Column(db.DateTime, default=datetime.utcnow)
    last_visit = db.Column(db.DateTime, default=datetime.utcnow)

class SiteConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# 工具函数
def get_visitor_info(ip_address):
    """获取访客地理信息"""
    try:
        # 使用免费的IP地理位置API
        response = requests.get(f'http://ip-api.com/json/{ip_address}', timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data['status'] == 'success':
                return {
                    'country': data.get('country', ''),
                    'city': data.get('city', ''),
                    'latitude': data.get('lat', 0),
                    'longitude': data.get('lon', 0)
                }
    except:
        pass
    return None

def calculate_distance(lat1, lon1, lat2, lon2):
    """计算两点间距离"""
    try:
        return geodesic((lat1, lon1), (lat2, lon2)).kilometers
    except:
        return 0

def get_weather_info(city='Beijing'):
    """获取天气信息"""
    try:
        # 使用免费天气API
        api_key = app.config.get('WEATHER_API_KEY')
        if not api_key:
            return None

        url = f'http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang=zh_cn'
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
                    is_admin=True,
                    bio='博客管理员，热爱技术分享和生活记录。',
                    location='中国',
                    github='wswldcs',
                    website='https://wswldcs.edu.deal'
                )
                admin.set_password('admin123')
                db.session.add(admin)
                
                # 创建分类（数据分析师主题）
                categories = [
                    {'name': '数据分析', 'description': 'Python、SQL、统计分析技术分享', 'color': '#3b82f6', 'icon': 'fas fa-chart-line'},
                    {'name': '机器学习', 'description': '机器学习算法和模型实践', 'color': '#8b5cf6', 'icon': 'fas fa-brain'},
                    {'name': '数据可视化', 'description': 'Tableau、Python可视化技术', 'color': '#10b981', 'icon': 'fas fa-chart-bar'},
                    {'name': '学习笔记', 'description': '大学四年学习过程记录', 'color': '#f59e0b', 'icon': 'fas fa-graduation-cap'},
                    {'name': '项目实战', 'description': '数据分析项目案例和经验', 'color': '#ef4444', 'icon': 'fas fa-project-diagram'},
                    {'name': '求职经历', 'description': '求职准备和面试经验分享', 'color': '#06b6d4', 'icon': 'fas fa-briefcase'}
                ]
                
                for cat_data in categories:
                    category = Category(**cat_data)
                    db.session.add(category)
                
                # 创建标签（数据分析师技能）
                tags_data = [
                    {'name': 'Python', 'color': '#3776ab'},
                    {'name': 'SQL', 'color': '#336791'},
                    {'name': 'Pandas', 'color': '#150458'},
                    {'name': 'NumPy', 'color': '#013243'},
                    {'name': 'Matplotlib', 'color': '#11557c'},
                    {'name': 'Seaborn', 'color': '#4c72b0'},
                    {'name': 'Scikit-learn', 'color': '#f7931e'},
                    {'name': 'Tableau', 'color': '#e97627'},
                    {'name': 'Excel', 'color': '#217346'},
                    {'name': 'R语言', 'color': '#276dc3'},
                    {'name': '统计学', 'color': '#4ecdc4'},
                    {'name': '数据挖掘', 'color': '#ff6b35'},
                    {'name': '机器学习', 'color': '#8b5cf6'},
                    {'name': '深度学习', 'color': '#6366f1'},
                    {'name': '数据清洗', 'color': '#10b981'},
                    {'name': '数据可视化', 'color': '#f59e0b'},
                    {'name': 'A/B测试', 'color': '#ef4444'},
                    {'name': '业务分析', 'color': '#06b6d4'},
                    {'name': '大学生活', 'color': '#84cc16'},
                    {'name': '求职准备', 'color': '#f97316'}
                ]
                
                for tag_data in tags_data:
                    tag = Tag(**tag_data)
                    db.session.add(tag)
                
                db.session.commit()
                
                # 获取创建的分类和标签
                data_analysis_category = Category.query.filter_by(name='数据分析').first()
                study_category = Category.query.filter_by(name='学习笔记').first()
                job_category = Category.query.filter_by(name='求职经历').first()

                python_tag = Tag.query.filter_by(name='Python').first()
                sql_tag = Tag.query.filter_by(name='SQL').first()
                pandas_tag = Tag.query.filter_by(name='Pandas').first()
                job_tag = Tag.query.filter_by(name='求职准备').first()

                # 创建示例文章（数据分析师求职主题）
                posts_data = [
                    {
                        'title': '我的数据分析师求职之路',
                        'slug': 'my-data-analyst-journey',
                        'summary': '从2021年9月入学到2025年6月毕业，四年大学生涯即将结束，现在正在积极寻找数据分析师的工作机会。',
                        'content': '''# 我的数据分析师求职之路

大家好！我是一名即将于2025年6月毕业的数据科学专业学生，目前正在积极寻找数据分析师的工作机会。

## 🎓 我的大学四年

### 2021年9月 - 初入校园
刚进入大学时，我对数据科学还是一个模糊的概念。通过《统计学原理》和《Python基础》等课程，我开始接触到数据的魅力。

### 2022年 - 技能建设年
- 深入学习Python编程，掌握Pandas、NumPy等数据处理库
- 学习SQL数据库操作，能够熟练进行数据查询和分析
- 接触机器学习基础理论，了解监督学习和无监督学习

### 2023年 - 实践提升年
- 完成多个数据分析项目，包括销售数据分析、用户行为分析等
- 学习Tableau和Python可视化，能够制作专业的数据报告
- 参与学校的数据建模竞赛，获得了宝贵的实战经验

### 2024年 - 深化专业年
- 深入学习机器学习算法，掌握回归、分类、聚类等方法
- 学习A/B测试和统计推断，具备业务分析能力
- 开始关注行业趋势，了解不同行业的数据分析应用

## 💼 求职准备

### 技能清单
- **编程语言**：Python (熟练)、SQL (熟练)、R (了解)
- **数据处理**：Pandas、NumPy、数据清洗、特征工程
- **数据可视化**：Matplotlib、Seaborn、Tableau、Excel
- **机器学习**：Scikit-learn、监督学习、无监督学习
- **统计分析**：描述性统计、假设检验、A/B测试
- **业务理解**：数据驱动决策、业务指标分析

### 项目经验
1. **电商用户行为分析**：使用Python分析用户购买路径，提升转化率15%
2. **销售预测模型**：基于历史数据建立时间序列预测模型，准确率达85%
3. **客户细分分析**：使用聚类算法进行客户分群，优化营销策略

## 🎯 求职目标

我希望能够加入一家重视数据驱动决策的公司，担任数据分析师职位，将我四年来学到的知识应用到实际业务中，用数据创造价值。

## 📞 联系我

如果您有合适的数据分析师职位，欢迎与我联系！我已经准备好迎接新的挑战，为公司的数据驱动发展贡献自己的力量。

---

*这个博客记录了我的学习历程和求职准备，希望能够帮助到同样在数据分析道路上前行的朋友们。*''',
                        'category': job_category,
                        'tags': [python_tag, sql_tag, job_tag],
                        'is_published': True,
                        'is_featured': True
                    },
                    {
                        'title': 'Python数据分析入门指南',
                        'slug': 'python-data-analysis-guide',
                        'summary': '从零开始学习Python数据分析，包括Pandas、NumPy等核心库的使用方法和实践技巧。',
                        'content': '''# Python数据分析入门指南

作为一名数据科学专业的学生，我想分享一下Python数据分析的学习心得。

## 🐍 为什么选择Python？

Python在数据分析领域有着独特的优势：
- 语法简洁易学
- 丰富的数据分析库
- 强大的社区支持
- 与机器学习无缝集成

## 📚 核心库介绍

### Pandas - 数据处理神器
```python
import pandas as pd

# 读取数据
df = pd.read_csv('data.csv')

# 数据探索
df.head()
df.info()
df.describe()

# 数据清洗
df.dropna()  # 删除缺失值
df.fillna(0)  # 填充缺失值
```

### NumPy - 数值计算基础
```python
import numpy as np

# 创建数组
arr = np.array([1, 2, 3, 4, 5])

# 统计计算
np.mean(arr)  # 平均值
np.std(arr)   # 标准差
```

### Matplotlib - 数据可视化
```python
import matplotlib.pyplot as plt

# 绘制折线图
plt.plot(x, y)
plt.title('数据趋势图')
plt.xlabel('时间')
plt.ylabel('数值')
plt.show()
```

## 🎯 学习建议

1. **从基础开始**：先掌握Python基础语法
2. **多做练习**：通过实际项目巩固知识
3. **关注业务**：理解数据背后的业务含义
4. **持续学习**：跟上技术发展趋势

希望这个指南能帮助到正在学习数据分析的朋友们！''',
                        'category': data_analysis_category,
                        'tags': [python_tag, pandas_tag],
                        'is_published': True,
                        'is_featured': False
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
                        'description': '基于Flask的功能完整的个人博客系统，支持文章管理、分类标签、评论系统、访客统计、天气显示等丰富功能。',
                        'tech_stack': 'Python, Flask, MySQL, Bootstrap, JavaScript',
                        'github_url': 'https://github.com/wswldcs/blog',
                        'demo_url': 'https://wswldcs.edu.deal',
                        'is_featured': True,
                        'status': 'completed'
                    },
                    {
                        'name': 'Vue.js 管理后台',
                        'description': '基于Vue.js和Element UI的现代化管理后台系统，支持权限管理、数据可视化等功能。',
                        'tech_stack': 'Vue.js, Element UI, Axios, ECharts',
                        'github_url': 'https://github.com/wswldcs/vue-admin',
                        'is_featured': True,
                        'status': 'in_progress'
                    },
                    {
                        'name': 'Python 爬虫工具',
                        'description': '多线程网页爬虫工具，支持数据清洗、存储和可视化分析。',
                        'tech_stack': 'Python, Scrapy, Pandas, Matplotlib',
                        'github_url': 'https://github.com/wswldcs/spider-tools',
                        'is_featured': False,
                        'status': 'completed'
                    }
                ]

                for proj_data in projects:
                    project = Project(**proj_data)
                    db.session.add(project)

                # 创建友情链接
                links = [
                    {
                        'name': '小明的博客',
                        'url': 'https://example.com',
                        'description': '我的好朋友，专注后端开发',
                        'category': 'friend',
                        'sort_order': 1
                    },
                    {
                        'name': 'GitHub',
                        'url': 'https://github.com',
                        'description': '全球最大的代码托管平台',
                        'category': 'tool',
                        'sort_order': 1
                    },
                    {
                        'name': '阮一峰的网络日志',
                        'url': 'https://www.ruanyifeng.com/blog/',
                        'description': '技术博客，分享前端和编程知识',
                        'category': 'recommend',
                        'sort_order': 1
                    }
                ]

                for link_data in links:
                    link = Link(**link_data)
                    db.session.add(link)

                # 创建学习历程时间线
                timeline_items = [
                    {
                        'title': '开始学习编程',
                        'description': '接触到编程世界，开始学习Python基础语法和编程思维。',
                        'date': datetime(2020, 9, 1).date(),
                        'icon': 'fas fa-play',
                        'color': '#28a745',
                        'category': 'education'
                    },
                    {
                        'title': '学习Flask框架',
                        'description': '深入学习Flask Web框架，掌握后端开发技能。',
                        'date': datetime(2021, 8, 20).date(),
                        'icon': 'fas fa-server',
                        'color': '#6f42c1',
                        'category': 'education'
                    },
                    {
                        'title': '第一个项目上线',
                        'description': '完成并部署了第一个个人项目，获得了宝贵的实战经验。',
                        'date': datetime(2022, 1, 10).date(),
                        'icon': 'fas fa-rocket',
                        'color': '#fd7e14',
                        'category': 'project'
                    },
                    {
                        'title': '博客系统重构',
                        'description': '使用最新技术栈重构个人博客，添加更多功能特性。',
                        'date': datetime(2024, 6, 4).date(),
                        'icon': 'fas fa-tools',
                        'color': '#dc3545',
                        'category': 'project'
                    }
                ]

                for timeline_data in timeline_items:
                    timeline_item = Timeline(**timeline_data)
                    db.session.add(timeline_item)

                db.session.commit()
                print("✅ 数据库初始化成功")
                print("👤 管理员账号: admin")
                print("🔑 管理员密码: admin123")
            
            return True
        except Exception as e:
            print(f"❌ 数据库初始化失败: {e}")
            return False

# 创建应用实例
app = create_app()

# 路由定义
@app.before_request
def track_visitor():
    """跟踪访客信息"""
    if request.endpoint and not request.endpoint.startswith('static'):
        ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        if ip and ip != '127.0.0.1':
            visitor = Visitor.query.filter_by(ip_address=ip).first()
            if visitor:
                visitor.visit_count += 1
                visitor.last_visit = datetime.utcnow()
            else:
                # 获取地理信息
                geo_info = get_visitor_info(ip)
                distance = 0
                if geo_info:
                    distance = calculate_distance(
                        geo_info['latitude'], geo_info['longitude'],
                        app.config['AUTHOR_LAT'], app.config['AUTHOR_LON']
                    )

                visitor = Visitor(
                    ip_address=ip,
                    user_agent=request.user_agent.string,
                    country=geo_info['country'] if geo_info else '',
                    city=geo_info['city'] if geo_info else '',
                    latitude=geo_info['latitude'] if geo_info else 0,
                    longitude=geo_info['longitude'] if geo_info else 0,
                    distance_km=distance
                )

            try:
                db.session.add(visitor)
                db.session.commit()
            except:
                db.session.rollback()

@app.context_processor
def inject_global_vars():
    """注入全局模板变量"""
    # 统计信息
    stats = {
        'total_posts': Post.query.filter_by(is_published=True).count(),
        'total_categories': Category.query.count(),
        'total_tags': Tag.query.count(),
        'total_views': db.session.query(db.func.sum(Post.view_count)).scalar() or 0,
        'total_visitors': Visitor.query.count(),
        'total_comments': Comment.query.filter_by(is_approved=True).count()
    }

    # 最新评论
    recent_comments = Comment.query.filter_by(is_approved=True).order_by(Comment.created_at.desc()).limit(5).all()

    # 热门文章
    popular_posts = Post.query.filter_by(is_published=True).order_by(Post.view_count.desc()).limit(5).all()

    # 当前时间和日历
    now = datetime.now()
    cal = calendar.monthcalendar(now.year, now.month)

    return {
        'stats': stats,
        'recent_comments': recent_comments,
        'popular_posts': popular_posts,
        'current_time': now,
        'calendar_data': cal,
        'month_name': calendar.month_name[now.month],
        'year': now.year
    }

@app.route('/')
def index():
    """首页"""
    # 精选文章
    featured_posts = Post.query.filter_by(is_published=True, is_featured=True).order_by(Post.created_at.desc()).limit(3).all()

    # 最新文章
    recent_posts = Post.query.filter_by(is_published=True).order_by(Post.created_at.desc()).limit(6).all()

    # 分类
    categories = Category.query.all()

    # 热门标签
    tags = Tag.query.limit(15).all()

    # 最新项目
    recent_projects = Project.query.filter_by(is_featured=True).order_by(Project.created_at.desc()).limit(3).all()

    # 友情链接
    friend_links = Link.query.filter_by(category='friend', is_active=True).order_by(Link.sort_order).limit(6).all()

    # 最近访客
    recent_visitors = Visitor.query.order_by(Visitor.last_visit.desc()).limit(10).all()

    return render_template_string(INDEX_TEMPLATE,
                                featured_posts=featured_posts,
                                recent_posts=recent_posts,
                                categories=categories,
                                tags=tags,
                                recent_projects=recent_projects,
                                friend_links=friend_links,
                                recent_visitors=recent_visitors)

@app.route('/blog')
def blog():
    """博客列表"""
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
    """文章详情"""
    post = Post.query.filter_by(slug=slug, is_published=True).first_or_404()

    # 增加浏览量
    post.view_count += 1
    db.session.commit()

    # 相关文章
    related_posts = []
    if post.category_id:
        related_posts = Post.query.filter(
            Post.id != post.id,
            Post.is_published == True,
            Post.category_id == post.category_id
        ).limit(3).all()

    # 评论
    comments = Comment.query.filter_by(post_id=post.id, is_approved=True).order_by(Comment.created_at.asc()).all()

    return render_template_string(POST_TEMPLATE,
                                post=post,
                                related_posts=related_posts,
                                comments=comments)

@app.route('/projects')
def projects():
    """项目展示"""
    featured_projects = Project.query.filter_by(is_featured=True).order_by(Project.sort_order).all()
    other_projects = Project.query.filter_by(is_featured=False).order_by(Project.sort_order).all()

    return render_template_string(PROJECTS_TEMPLATE,
                                featured_projects=featured_projects,
                                other_projects=other_projects)

@app.route('/timeline')
def timeline():
    """学习历程时间线"""
    timeline_items = Timeline.query.order_by(Timeline.date.desc()).all()

    # 按年份分组
    timeline_by_year = {}
    for item in timeline_items:
        year = item.date.year
        if year not in timeline_by_year:
            timeline_by_year[year] = []
        timeline_by_year[year].append(item)

    return render_template_string(TIMELINE_TEMPLATE,
                                timeline_by_year=timeline_by_year)

@app.route('/links')
def links():
    """友情链接和推荐网站"""
    friend_links = Link.query.filter_by(category='friend', is_active=True).order_by(Link.sort_order).all()
    recommend_links = Link.query.filter_by(category='recommend', is_active=True).order_by(Link.sort_order).all()
    tool_links = Link.query.filter_by(category='tool', is_active=True).order_by(Link.sort_order).all()

    return render_template_string(LINKS_TEMPLATE,
                                friend_links=friend_links,
                                recommend_links=recommend_links,
                                tool_links=tool_links)

@app.route('/about')
def about():
    """关于页面"""
    # 获取博主信息
    author = User.query.filter_by(is_admin=True).first()

    # 技能统计
    tech_stats = {
        'Python': 90,
        'JavaScript': 85,
        'Flask': 88,
        'Vue.js': 80,
        'MySQL': 85,
        'Docker': 75,
        'Linux': 82,
        'Git': 90
    }

    return render_template_string(ABOUT_TEMPLATE,
                                author=author,
                                tech_stats=tech_stats)

@app.route('/api/weather')
def api_weather():
    """天气API"""
    city = request.args.get('city', 'Beijing')
    weather_data = get_weather_info(city)
    return jsonify(weather_data) if weather_data else jsonify({'error': 'Unable to fetch weather data'})

@app.route('/api/visitor-stats')
def api_visitor_stats():
    """访客统计API"""
    # 今日访客
    today = datetime.now().date()
    today_visitors = Visitor.query.filter(
        db.func.date(Visitor.last_visit) == today
    ).count()

    # 本周访客
    week_ago = datetime.now() - timedelta(days=7)
    week_visitors = Visitor.query.filter(
        Visitor.last_visit >= week_ago
    ).count()

    # 访客地区分布
    visitor_countries = db.session.query(
        Visitor.country,
        db.func.count(Visitor.id).label('count')
    ).group_by(Visitor.country).order_by(db.desc('count')).limit(10).all()

    return jsonify({
        'today_visitors': today_visitors,
        'week_visitors': week_visitors,
        'total_visitors': Visitor.query.count(),
        'countries': [{'name': country, 'count': count} for country, count in visitor_countries]
    })

@app.route('/login', methods=['GET', 'POST'])
def login():
    """登录"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            session['admin_logged_in'] = True  # 同时设置session
            return redirect(url_for('admin_dashboard'))
        else:
            flash('用户名或密码错误')

    return render_template_string(LOGIN_TEMPLATE)

@app.route('/admin')
@login_required
def admin_dashboard():
    """管理后台首页"""
    # 统计数据
    dashboard_stats = {
        'total_posts': Post.query.count(),
        'published_posts': Post.query.filter_by(is_published=True).count(),
        'draft_posts': Post.query.filter_by(is_published=False).count(),
        'total_comments': Comment.query.count(),
        'pending_comments': Comment.query.filter_by(is_approved=False).count(),
        'total_visitors': Visitor.query.count(),
        'today_visitors': Visitor.query.filter(
            db.func.date(Visitor.last_visit) == datetime.now().date()
        ).count()
    }

    # 最新文章
    recent_posts = Post.query.order_by(Post.created_at.desc()).limit(5).all()

    # 最新评论
    recent_comments = Comment.query.order_by(Comment.created_at.desc()).limit(5).all()

    return render_template_string(ADMIN_DASHBOARD_TEMPLATE,
                                dashboard_stats=dashboard_stats,
                                recent_posts=recent_posts,
                                recent_comments=recent_comments)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.pop('admin_logged_in', None)  # 同时清除session
    return redirect(url_for('index'))

@app.route('/health')
def health():
    return {'status': 'ok', 'app': 'rich_blog_app.py', 'features': 'complete', 'version': '2.0', 'timestamp': datetime.now().isoformat()}

# 模板定义
INDEX_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{{ config.BLOG_TITLE }} - {{ config.BLOG_SUBTITLE }}</title>
    <meta name="description" content="{{ config.BLOG_SUBTITLE }}">
    <meta name="author" content="{{ config.AUTHOR_NAME }}">

    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <!-- Font Awesome -->
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <!-- Google Fonts -->
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">

    <style>
        :root {
            --primary-color: #667eea;
            --secondary-color: #764ba2;
            --accent-color: #f093fb;
            --data-blue: #3b82f6;
            --data-purple: #8b5cf6;
            --data-green: #10b981;
            --data-orange: #f59e0b;
            --data-red: #ef4444;
            --success-color: #4ecdc4;
            --warning-color: #ffe66d;
            --danger-color: #ff6b6b;
            --dark-color: #1e293b;
            --light-color: #f8fafc;
            --gradient-primary: linear-gradient(135deg, var(--data-blue) 0%, var(--data-purple) 100%);
            --gradient-accent: linear-gradient(135deg, var(--accent-color) 0%, var(--primary-color) 100%);
            --gradient-data: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
            --shadow-sm: 0 2px 4px rgba(0,0,0,0.1);
            --shadow-md: 0 4px 6px rgba(0,0,0,0.1);
            --shadow-lg: 0 10px 15px rgba(0,0,0,0.1);
            --shadow-xl: 0 20px 25px rgba(0,0,0,0.1);
            --shadow-glow: 0 0 20px rgba(102, 126, 234, 0.3);
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #1e293b;
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%);
            min-height: 100vh;
            overflow-x: hidden;
        }

        /* 粒子背景 */
        .particles-bg {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: -1;
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%);
        }

        .particle {
            position: absolute;
            background: rgba(102, 126, 234, 0.6);
            border-radius: 50%;
            animation: float 6s ease-in-out infinite;
        }

        @keyframes float {
            0%, 100% { transform: translateY(0px) rotate(0deg); opacity: 0.7; }
            50% { transform: translateY(-20px) rotate(180deg); opacity: 1; }
        }

        /* 超炫酷导航栏 */
        .navbar {
            background: rgba(15, 23, 42, 0.95) !important;
            backdrop-filter: blur(20px);
            border-bottom: 1px solid rgba(102, 126, 234, 0.2);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            padding: 1rem 0;
            position: fixed !important;
            top: 0;
            width: 100%;
            z-index: 1000;
            transition: all 0.3s ease;
        }

        .navbar.scrolled {
            background: rgba(15, 23, 42, 0.98) !important;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
        }

        .navbar-brand {
            font-weight: 700;
            font-size: 1.5rem;
            color: white !important;
            text-shadow: 0 0 10px rgba(102, 126, 234, 0.5);
            transition: all 0.3s ease;
        }

        .navbar-brand:hover {
            color: var(--data-blue) !important;
            text-shadow: 0 0 20px rgba(102, 126, 234, 0.8);
            transform: scale(1.05);
        }

        .navbar-nav .nav-link {
            color: rgba(255,255,255,0.9) !important;
            font-weight: 500;
            margin: 0 0.5rem;
            padding: 0.5rem 1rem !important;
            border-radius: 25px;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }

        .navbar-nav .nav-link::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: var(--gradient-primary);
            transition: all 0.3s ease;
            z-index: -1;
        }

        .navbar-nav .nav-link:hover {
            color: white !important;
            transform: translateY(-2px);
            box-shadow: var(--shadow-glow);
        }

        .navbar-nav .nav-link:hover::before {
            left: 0;
        }

        .navbar-nav .nav-link.active {
            background: var(--gradient-primary);
            color: white !important;
            box-shadow: var(--shadow-glow);
        }

        /* 页面内容顶部间距 */
        .main-content {
            margin-top: 80px;
        }

        /* 超炫酷Hero区域 */
        .hero-section {
            background: var(--gradient-data);
            color: white;
            padding: 150px 0 100px;
            position: relative;
            overflow: hidden;
            min-height: 100vh;
            display: flex;
            align-items: center;
        }

        .hero-section::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background:
                radial-gradient(circle at 20% 80%, rgba(102, 126, 234, 0.3) 0%, transparent 50%),
                radial-gradient(circle at 80% 20%, rgba(139, 92, 246, 0.3) 0%, transparent 50%),
                radial-gradient(circle at 40% 40%, rgba(240, 147, 251, 0.2) 0%, transparent 50%);
        }

        .hero-content {
            position: relative;
            z-index: 2;
        }

        .hero-title {
            font-size: 4rem;
            font-weight: 800;
            margin-bottom: 1.5rem;
            text-shadow: 0 0 30px rgba(0,0,0,0.5);
            background: linear-gradient(45deg, #ffffff, #e0e7ff, #c7d2fe);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            animation: titleGlow 3s ease-in-out infinite alternate;
        }

        @keyframes titleGlow {
            0% { text-shadow: 0 0 30px rgba(102, 126, 234, 0.5); }
            100% { text-shadow: 0 0 50px rgba(139, 92, 246, 0.8); }
        }

        .hero-subtitle {
            font-size: 1.5rem;
            margin-bottom: 2rem;
            opacity: 0.95;
            font-weight: 300;
            letter-spacing: 0.5px;
        }

        .hero-description {
            font-size: 1.1rem;
            margin-bottom: 3rem;
            opacity: 0.9;
            max-width: 600px;
            line-height: 1.8;
        }

        .hero-stats {
            display: flex;
            gap: 2rem;
            margin-top: 3rem;
        }

        .hero-stat {
            text-align: center;
        }

        .hero-stat-number {
            font-size: 2rem;
            font-weight: 700;
            display: block;
        }

        .hero-stat-label {
            font-size: 0.9rem;
            opacity: 0.8;
        }

        /* 卡片样式 */
        .card {
            border: none;
            border-radius: 15px;
            box-shadow: var(--shadow-lg);
            transition: all 0.3s ease;
            background: white;
            overflow: hidden;
        }

        .card:hover {
            transform: translateY(-10px);
            box-shadow: var(--shadow-xl);
        }

        .card-header {
            background: var(--gradient-primary);
            color: white;
            border: none;
            padding: 1.5rem;
        }

        .card-title {
            font-weight: 600;
            margin-bottom: 0.5rem;
        }

        /* 按钮样式 */
        .btn {
            border-radius: 50px;
            font-weight: 500;
            padding: 0.75rem 2rem;
            transition: all 0.3s ease;
            border: none;
        }

        .btn-primary {
            background: var(--gradient-primary);
            color: white;
        }

        .btn-primary:hover {
            background: var(--gradient-accent);
            transform: translateY(-2px);
            box-shadow: var(--shadow-md);
        }

        .btn-outline-primary {
            border: 2px solid var(--primary-color);
            color: var(--primary-color);
            background: transparent;
        }

        .btn-outline-primary:hover {
            background: var(--primary-color);
            color: white;
            transform: translateY(-2px);
        }

        /* 标签样式 */
        .tag {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            margin: 0.25rem;
            border-radius: 50px;
            font-size: 0.875rem;
            text-decoration: none;
            transition: all 0.3s ease;
            font-weight: 500;
        }

        .tag:hover {
            transform: translateY(-2px);
            text-decoration: none;
            box-shadow: var(--shadow-md);
        }

        /* 侧边栏样式 */
        .sidebar {
            background: white;
            border-radius: 15px;
            padding: 2rem;
            box-shadow: var(--shadow-lg);
            margin-bottom: 2rem;
        }

        .sidebar-title {
            font-weight: 600;
            margin-bottom: 1.5rem;
            color: var(--dark-color);
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        /* 天气组件 */
        .weather-widget {
            background: var(--gradient-primary);
            color: white;
            border-radius: 15px;
            padding: 1.5rem;
            text-align: center;
            margin-bottom: 2rem;
        }

        .weather-icon {
            font-size: 3rem;
            margin-bottom: 1rem;
        }

        .weather-temp {
            font-size: 2rem;
            font-weight: 700;
        }

        .weather-desc {
            opacity: 0.9;
            margin-top: 0.5rem;
        }

        /* 日历组件 */
        .calendar-widget {
            background: white;
            border-radius: 15px;
            padding: 1.5rem;
            box-shadow: var(--shadow-lg);
        }

        .calendar-header {
            text-align: center;
            margin-bottom: 1rem;
            font-weight: 600;
            color: var(--dark-color);
        }

        .calendar-grid {
            display: grid;
            grid-template-columns: repeat(7, 1fr);
            gap: 0.5rem;
            text-align: center;
        }

        .calendar-day {
            padding: 0.5rem;
            border-radius: 8px;
            transition: all 0.3s ease;
        }

        .calendar-day:hover {
            background: var(--primary-color);
            color: white;
        }

        .calendar-today {
            background: var(--primary-color);
            color: white;
            font-weight: 600;
        }

        /* 访客信息 */
        .visitor-info {
            background: var(--gradient-accent);
            color: white;
            border-radius: 15px;
            padding: 1.5rem;
            margin-bottom: 2rem;
        }

        .visitor-stat {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.5rem;
        }

        .visitor-stat:last-child {
            margin-bottom: 0;
        }

        /* 项目卡片 */
        .project-card {
            background: white;
            border-radius: 15px;
            padding: 2rem;
            box-shadow: var(--shadow-lg);
            transition: all 0.3s ease;
            height: 100%;
        }

        .project-card:hover {
            transform: translateY(-5px);
            box-shadow: var(--shadow-xl);
        }

        .project-title {
            font-weight: 600;
            margin-bottom: 1rem;
            color: var(--dark-color);
        }

        .project-tech {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin: 1rem 0;
        }

        .tech-badge {
            background: var(--light-color);
            color: var(--dark-color);
            padding: 0.25rem 0.75rem;
            border-radius: 50px;
            font-size: 0.875rem;
            font-weight: 500;
        }

        /* 友情链接 */
        .friend-link {
            display: flex;
            align-items: center;
            padding: 1rem;
            background: white;
            border-radius: 10px;
            text-decoration: none;
            color: var(--dark-color);
            transition: all 0.3s ease;
            margin-bottom: 1rem;
            box-shadow: var(--shadow-sm);
        }

        .friend-link:hover {
            transform: translateX(5px);
            box-shadow: var(--shadow-md);
            color: var(--primary-color);
            text-decoration: none;
        }

        .friend-avatar {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            margin-right: 1rem;
            background: var(--light-color);
            display: flex;
            align-items: center;
            justify-content: center;
        }

        /* 页脚 */
        .footer {
            background: var(--dark-color);
            color: white;
            padding: 3rem 0 2rem;
            margin-top: 5rem;
        }

        .footer-section {
            margin-bottom: 2rem;
        }

        .footer-title {
            font-weight: 600;
            margin-bottom: 1rem;
        }

        .social-links a {
            color: white;
            font-size: 1.5rem;
            margin-right: 1rem;
            transition: all 0.3s ease;
        }

        .social-links a:hover {
            color: var(--primary-color);
            transform: translateY(-2px);
        }

        /* 响应式设计 */
        @media (max-width: 768px) {
            .hero-title {
                font-size: 2.5rem;
            }

            .hero-stats {
                flex-direction: column;
                gap: 1rem;
            }

            .sidebar {
                margin-top: 2rem;
            }
        }

        /* 动画效果 */
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .fade-in-up {
            animation: fadeInUp 0.6s ease-out;
        }

        /* 加载动画 */
        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(255,255,255,.3);
            border-radius: 50%;
            border-top-color: #fff;
            animation: spin 1s ease-in-out infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <!-- 导航栏 -->
    <nav class="navbar navbar-expand-lg navbar-dark sticky-top">
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
                        <a class="nav-link" href="{{ url_for('timeline') }}">
                            <i class="fas fa-history me-1"></i>历程
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="{{ url_for('links') }}">
                            <i class="fas fa-link me-1"></i>友链
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

    <!-- 粒子背景 -->
    <div class="particles-bg" id="particles-bg"></div>

    <!-- 超炫酷Hero区域 -->
    <section class="hero-section">
        <div class="container">
            <div class="row align-items-center">
                <div class="col-lg-6">
                    <div class="hero-content">
                        <h1 class="hero-title fade-in-up">数据分析师</h1>
                        <p class="hero-subtitle fade-in-up">{{ config.AUTHOR_NAME }} · 2025届毕业生</p>
                        <p class="hero-description fade-in-up">
                            从2021年9月踏入大学校园，到2025年6月即将毕业，四年的数据科学学习之旅即将告一段落。
                            现在，我正在寻找数据分析师的工作机会，希望将所学知识应用到实际业务中，
                            用数据驱动决策，创造价值。
                        </p>

                        <div class="hero-stats fade-in-up">
                            <div class="hero-stat">
                                <span class="hero-stat-number">4</span>
                                <span class="hero-stat-label">年学习历程</span>
                            </div>
                            <div class="hero-stat">
                                <span class="hero-stat-number">{{ stats.total_posts }}</span>
                                <span class="hero-stat-label">篇学习笔记</span>
                            </div>
                            <div class="hero-stat">
                                <span class="hero-stat-number">15+</span>
                                <span class="hero-stat-label">项技能掌握</span>
                            </div>
                            <div class="hero-stat">
                                <span class="hero-stat-number">10+</span>
                                <span class="hero-stat-label">个项目经验</span>
                            </div>
                        </div>

                        <div class="mt-4">
                            <a href="{{ url_for('timeline') }}" class="btn btn-primary btn-lg me-3">
                                <i class="fas fa-chart-line me-2"></i>学习历程
                            </a>
                            <a href="{{ url_for('projects') }}" class="btn btn-outline-light btn-lg me-3">
                                <i class="fas fa-code me-2"></i>项目作品
                            </a>
                            <a href="{{ url_for('about') }}" class="btn btn-outline-light btn-lg">
                                <i class="fas fa-download me-2"></i>简历下载
                            </a>
                        </div>
                    </div>
                </div>
                <div class="col-lg-6">
                    <div class="hero-visual text-center">
                        <div class="data-visualization">
                            <canvas id="skillChart" width="400" height="400"></canvas>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- 主要内容区域 -->
    <div class="main-content">
        <div class="container py-5">
            <div class="row">
            <!-- 主内容区 -->
            <div class="col-lg-8">
                <!-- 精选文章 -->
                {% if featured_posts %}
                <section class="mb-5">
                    <div class="d-flex justify-content-between align-items-center mb-4">
                        <h2 class="section-title">
                            <i class="fas fa-star text-warning me-2"></i>精选文章
                        </h2>
                        <a href="{{ url_for('blog') }}" class="btn btn-outline-primary">查看更多</a>
                    </div>

                    <div class="row">
                        {% for post in featured_posts %}
                        <div class="col-md-6 mb-4">
                            <div class="card h-100 fade-in-up">
                                <div class="card-body">
                                    <div class="d-flex justify-content-between align-items-start mb-2">
                                        <h5 class="card-title">
                                            <a href="{{ url_for('post', slug=post.slug) }}" class="text-decoration-none">
                                                {{ post.title }}
                                            </a>
                                        </h5>
                                        {% if post.category %}
                                        <span class="badge" style="background-color: {{ post.category.color }};">
                                            <i class="{{ post.category.icon }} me-1"></i>{{ post.category.name }}
                                        </span>
                                        {% endif %}
                                    </div>

                                    <p class="card-text text-muted">{{ post.summary or post.content[:120] + '...' }}</p>

                                    <div class="d-flex justify-content-between align-items-center">
                                        <small class="text-muted">
                                            <i class="fas fa-calendar-alt me-1"></i>
                                            {{ post.created_at.strftime('%m月%d日') }}
                                            <span class="ms-2">
                                                <i class="fas fa-eye me-1"></i>{{ post.view_count }}
                                            </span>
                                        </small>
                                        <div>
                                            {% for tag in post.tags[:2] %}
                                            <span class="tag" style="background-color: {{ tag.color }}; color: white;">
                                                {{ tag.name }}
                                            </span>
                                            {% endfor %}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        {% endfor %}
                    </div>
                </section>
                {% endif %}

                <!-- 最新文章 -->
                <section class="mb-5">
                    <div class="d-flex justify-content-between align-items-center mb-4">
                        <h2 class="section-title">
                            <i class="fas fa-clock text-primary me-2"></i>最新文章
                        </h2>
                        <a href="{{ url_for('blog') }}" class="btn btn-outline-primary">查看全部</a>
                    </div>

                    <div class="row">
                        {% for post in recent_posts %}
                        <div class="col-md-6 mb-4">
                            <div class="card h-100 fade-in-up">
                                <div class="card-body">
                                    <h6 class="card-title">
                                        <a href="{{ url_for('post', slug=post.slug) }}" class="text-decoration-none">
                                            {{ post.title }}
                                        </a>
                                    </h6>
                                    <p class="card-text small text-muted">{{ post.summary or post.content[:80] + '...' }}</p>
                                    <div class="d-flex justify-content-between align-items-center">
                                        <small class="text-muted">
                                            {{ post.created_at.strftime('%m-%d') }}
                                        </small>
                                        {% if post.category %}
                                        <small class="badge" style="background-color: {{ post.category.color }};">
                                            {{ post.category.name }}
                                        </small>
                                        {% endif %}
                                    </div>
                                </div>
                            </div>
                        </div>
                        {% endfor %}
                    </div>
                </section>

                <!-- 最新项目 -->
                {% if recent_projects %}
                <section class="mb-5">
                    <div class="d-flex justify-content-between align-items-center mb-4">
                        <h2 class="section-title">
                            <i class="fas fa-code text-success me-2"></i>最新项目
                        </h2>
                        <a href="{{ url_for('projects') }}" class="btn btn-outline-primary">查看全部</a>
                    </div>

                    <div class="row">
                        {% for project in recent_projects %}
                        <div class="col-md-4 mb-4">
                            <div class="project-card fade-in-up">
                                <h6 class="project-title">{{ project.name }}</h6>
                                <p class="text-muted small">{{ project.description[:80] + '...' }}</p>
                                <div class="project-tech">
                                    {% for tech in project.get_tech_list()[:3] %}
                                    <span class="tech-badge">{{ tech }}</span>
                                    {% endfor %}
                                </div>
                                <div class="d-flex gap-2">
                                    {% if project.github_url %}
                                    <a href="{{ project.github_url }}" class="btn btn-sm btn-outline-dark" target="_blank">
                                        <i class="fab fa-github"></i>
                                    </a>
                                    {% endif %}
                                    {% if project.demo_url %}
                                    <a href="{{ project.demo_url }}" class="btn btn-sm btn-primary" target="_blank">
                                        <i class="fas fa-external-link-alt"></i>
                                    </a>
                                    {% endif %}
                                </div>
                            </div>
                        </div>
                        {% endfor %}
                    </div>
                </section>
                {% endif %}
            </div>

            <!-- 侧边栏 -->
            <div class="col-lg-4">
                <!-- 实时信息卡片 -->
                <div class="sidebar fade-in-up">
                    <h5 class="sidebar-title">
                        <i class="fas fa-info-circle"></i>实时信息
                    </h5>

                    <!-- 当前时间 -->
                    <div class="mb-3">
                        <div class="d-flex justify-content-between">
                            <span>当前时间</span>
                            <span id="current-time">{{ current_time.strftime('%H:%M:%S') }}</span>
                        </div>
                        <div class="d-flex justify-content-between">
                            <span>今天日期</span>
                            <span>{{ current_time.strftime('%Y年%m月%d日') }}</span>
                        </div>
                    </div>

                    <!-- 天气信息 -->
                    <div class="weather-widget" id="weather-widget">
                        <div class="weather-icon">
                            <i class="fas fa-cloud-sun"></i>
                        </div>
                        <div class="weather-temp" id="weather-temp">加载中...</div>
                        <div class="weather-desc" id="weather-desc">获取天气信息中</div>
                        <div class="mt-2">
                            <small id="weather-location">北京</small>
                        </div>
                    </div>
                </div>

                <!-- 访客统计 -->
                <div class="visitor-info fade-in-up">
                    <h6 class="mb-3">
                        <i class="fas fa-users me-2"></i>访客统计
                    </h6>
                    <div class="visitor-stat">
                        <span>今日访客</span>
                        <span id="today-visitors">{{ stats.total_visitors }}</span>
                    </div>
                    <div class="visitor-stat">
                        <span>总访客数</span>
                        <span>{{ stats.total_visitors }}</span>
                    </div>
                    <div class="visitor-stat">
                        <span>您的位置</span>
                        <span id="visitor-location">获取中...</span>
                    </div>
                    <div class="visitor-stat">
                        <span>与我距离</span>
                        <span id="visitor-distance">计算中...</span>
                    </div>
                </div>

                <!-- 日历组件 -->
                <div class="calendar-widget fade-in-up">
                    <div class="calendar-header">
                        {{ year }}年{{ month_name }}
                    </div>
                    <div class="calendar-grid">
                        <div class="text-muted small">日</div>
                        <div class="text-muted small">一</div>
                        <div class="text-muted small">二</div>
                        <div class="text-muted small">三</div>
                        <div class="text-muted small">四</div>
                        <div class="text-muted small">五</div>
                        <div class="text-muted small">六</div>

                        {% for week in calendar_data %}
                            {% for day in week %}
                                {% if day == 0 %}
                                <div class="calendar-day"></div>
                                {% else %}
                                <div class="calendar-day {% if day == current_time.day %}calendar-today{% endif %}">
                                    {{ day }}
                                </div>
                                {% endif %}
                            {% endfor %}
                        {% endfor %}
                    </div>
                </div>

                <!-- 分类标签 -->
                <div class="sidebar fade-in-up">
                    <h5 class="sidebar-title">
                        <i class="fas fa-folder"></i>文章分类
                    </h5>
                    {% for category in categories %}
                    <a href="{{ url_for('blog', category=category.id) }}"
                       class="tag d-inline-block mb-2"
                       style="background-color: {{ category.color }}; color: white;">
                        <i class="{{ category.icon }} me-1"></i>{{ category.name }}
                    </a>
                    {% endfor %}
                </div>

                <!-- 标签云 -->
                <div class="sidebar fade-in-up">
                    <h5 class="sidebar-title">
                        <i class="fas fa-tags"></i>热门标签
                    </h5>
                    {% for tag in tags %}
                    <a href="{{ url_for('blog', tag=tag.id) }}"
                       class="tag"
                       style="background-color: {{ tag.color }}; color: white;">
                        {{ tag.name }}
                    </a>
                    {% endfor %}
                </div>

                <!-- 友情链接 -->
                {% if friend_links %}
                <div class="sidebar fade-in-up">
                    <h5 class="sidebar-title">
                        <i class="fas fa-heart"></i>友情链接
                    </h5>
                    {% for link in friend_links %}
                    <a href="{{ link.url }}" class="friend-link" target="_blank">
                        <div class="friend-avatar">
                            {% if link.avatar %}
                            <img src="{{ link.avatar }}" alt="{{ link.name }}" class="w-100 h-100 rounded-circle">
                            {% else %}
                            <i class="fas fa-user"></i>
                            {% endif %}
                        </div>
                        <div>
                            <div class="fw-bold">{{ link.name }}</div>
                            {% if link.description %}
                            <small class="text-muted">{{ link.description[:30] + '...' if link.description|length > 30 else link.description }}</small>
                            {% endif %}
                        </div>
                    </a>
                    {% endfor %}
                    <div class="text-center mt-3">
                        <a href="{{ url_for('links') }}" class="btn btn-sm btn-outline-primary">查看更多</a>
                    </div>
                </div>
                {% endif %}

                <!-- 最近访客 -->
                {% if recent_visitors %}
                <div class="sidebar fade-in-up">
                    <h5 class="sidebar-title">
                        <i class="fas fa-globe"></i>最近访客
                    </h5>
                    {% for visitor in recent_visitors[:5] %}
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <div>
                            <small class="fw-bold">{{ visitor.country or '未知' }}</small>
                            {% if visitor.city %}
                            <small class="text-muted">{{ visitor.city }}</small>
                            {% endif %}
                        </div>
                        <small class="text-muted">
                            {% if visitor.distance_km > 0 %}
                            {{ "%.0f"|format(visitor.distance_km) }}km
                            {% endif %}
                        </small>
                    </div>
                    {% endfor %}
                </div>
                {% endif %}
            </div>
        </div>
        </div>
    </div>

    <!-- 页脚 -->
    <footer class="footer">
        <div class="container">
            <div class="row">
                <div class="col-md-4 footer-section">
                    <h5 class="footer-title">{{ config.BLOG_TITLE }}</h5>
                    <p class="text-muted">{{ config.BLOG_SUBTITLE }}</p>
                    <div class="social-links">
                        <a href="https://github.com/{{ config.AUTHOR_NAME }}" target="_blank" title="GitHub">
                            <i class="fab fa-github"></i>
                        </a>
                        <a href="#" target="_blank" title="Twitter">
                            <i class="fab fa-twitter"></i>
                        </a>
                        <a href="#" target="_blank" title="LinkedIn">
                            <i class="fab fa-linkedin"></i>
                        </a>
                        <a href="mailto:{{ config.AUTHOR_EMAIL }}" title="Email">
                            <i class="fas fa-envelope"></i>
                        </a>
                    </div>
                </div>

                <div class="col-md-4 footer-section">
                    <h5 class="footer-title">快速导航</h5>
                    <ul class="list-unstyled">
                        <li><a href="{{ url_for('blog') }}" class="text-muted text-decoration-none">博客文章</a></li>
                        <li><a href="{{ url_for('projects') }}" class="text-muted text-decoration-none">项目展示</a></li>
                        <li><a href="{{ url_for('timeline') }}" class="text-muted text-decoration-none">学习历程</a></li>
                        <li><a href="{{ url_for('links') }}" class="text-muted text-decoration-none">友情链接</a></li>
                        <li><a href="{{ url_for('about') }}" class="text-muted text-decoration-none">关于我</a></li>
                    </ul>
                </div>

                <div class="col-md-4 footer-section">
                    <h5 class="footer-title">站点统计</h5>
                    <ul class="list-unstyled text-muted">
                        <li>文章总数：{{ stats.total_posts }}</li>
                        <li>访客总数：{{ stats.total_visitors }}</li>
                        <li>浏览总数：{{ stats.total_views }}</li>
                        <li>评论总数：{{ stats.total_comments }}</li>
                    </ul>
                </div>
            </div>

            <hr class="my-4">

            <div class="row align-items-center">
                <div class="col-md-6">
                    <p class="text-muted mb-0">
                        © {{ current_time.year }} {{ config.BLOG_TITLE }}. All rights reserved.
                    </p>
                </div>
                <div class="col-md-6 text-md-end">
                    <p class="text-muted mb-0">
                        Powered by Flask & Railway
                    </p>
                </div>
            </div>
        </div>
    </footer>

    <!-- JavaScript -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // 实时时间更新
        function updateTime() {
            const now = new Date();
            const timeString = now.toLocaleTimeString('zh-CN');
            document.getElementById('current-time').textContent = timeString;
        }

        // 每秒更新时间
        setInterval(updateTime, 1000);

        // 获取天气信息
        async function loadWeather() {
            try {
                const response = await fetch('/api/weather?city=Beijing');
                const data = await response.json();

                if (data && !data.error) {
                    const temp = Math.round(data.main.temp);
                    const desc = data.weather[0].description;
                    const location = data.name;

                    document.getElementById('weather-temp').textContent = temp + '°C';
                    document.getElementById('weather-desc').textContent = desc;
                    document.getElementById('weather-location').textContent = location;

                    // 根据天气更新图标
                    const iconElement = document.querySelector('.weather-icon i');
                    const weatherId = data.weather[0].id;
                    if (weatherId < 300) {
                        iconElement.className = 'fas fa-bolt';
                    } else if (weatherId < 600) {
                        iconElement.className = 'fas fa-cloud-rain';
                    } else if (weatherId < 700) {
                        iconElement.className = 'fas fa-snowflake';
                    } else if (weatherId === 800) {
                        iconElement.className = 'fas fa-sun';
                    } else {
                        iconElement.className = 'fas fa-cloud';
                    }
                }
            } catch (error) {
                console.log('天气信息获取失败:', error);
                document.getElementById('weather-temp').textContent = '--°C';
                document.getElementById('weather-desc').textContent = '天气信息暂不可用';
            }
        }

        // 获取访客位置信息
        async function loadVisitorInfo() {
            try {
                // 尝试获取用户地理位置
                if (navigator.geolocation) {
                    navigator.geolocation.getCurrentPosition(async function(position) {
                        const lat = position.coords.latitude;
                        const lon = position.coords.longitude;

                        // 计算与博主的距离
                        const authorLat = {{ config.AUTHOR_LAT }};
                        const authorLon = {{ config.AUTHOR_LON }};
                        const distance = calculateDistance(lat, lon, authorLat, authorLon);

                        document.getElementById('visitor-distance').textContent = Math.round(distance) + ' km';

                        // 获取地理位置名称
                        try {
                            const response = await fetch(`https://api.bigdatacloud.net/data/reverse-geocode-client?latitude=${lat}&longitude=${lon}&localityLanguage=zh`);
                            const data = await response.json();
                            const location = data.city || data.locality || data.countryName || '未知位置';
                            document.getElementById('visitor-location').textContent = location;
                        } catch (error) {
                            document.getElementById('visitor-location').textContent = '位置获取失败';
                        }
                    }, function(error) {
                        document.getElementById('visitor-location').textContent = '位置权限被拒绝';
                        document.getElementById('visitor-distance').textContent = '无法计算';
                    });
                } else {
                    document.getElementById('visitor-location').textContent = '浏览器不支持定位';
                    document.getElementById('visitor-distance').textContent = '无法计算';
                }

                // 获取访客统计
                const statsResponse = await fetch('/api/visitor-stats');
                const statsData = await statsResponse.json();
                document.getElementById('today-visitors').textContent = statsData.today_visitors;

            } catch (error) {
                console.log('访客信息获取失败:', error);
            }
        }

        // 计算两点间距离（Haversine公式）
        function calculateDistance(lat1, lon1, lat2, lon2) {
            const R = 6371; // 地球半径（公里）
            const dLat = (lat2 - lat1) * Math.PI / 180;
            const dLon = (lon2 - lon1) * Math.PI / 180;
            const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                      Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
                      Math.sin(dLon/2) * Math.sin(dLon/2);
            const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
            return R * c;
        }

        // 创建粒子背景
        function createParticles() {
            const particlesContainer = document.getElementById('particles-bg');
            const particleCount = 50;

            for (let i = 0; i < particleCount; i++) {
                const particle = document.createElement('div');
                particle.className = 'particle';

                // 随机大小和位置
                const size = Math.random() * 4 + 2;
                particle.style.width = size + 'px';
                particle.style.height = size + 'px';
                particle.style.left = Math.random() * 100 + '%';
                particle.style.top = Math.random() * 100 + '%';

                // 随机动画延迟
                particle.style.animationDelay = Math.random() * 6 + 's';
                particle.style.animationDuration = (Math.random() * 3 + 3) + 's';

                particlesContainer.appendChild(particle);
            }
        }

        // 导航栏滚动效果
        function handleNavbarScroll() {
            const navbar = document.querySelector('.navbar');
            if (window.scrollY > 50) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }
        }

        // 创建技能雷达图
        function createSkillChart() {
            const canvas = document.getElementById('skillChart');
            if (!canvas) return;

            const ctx = canvas.getContext('2d');
            const centerX = canvas.width / 2;
            const centerY = canvas.height / 2;
            const radius = 150;

            // 技能数据
            const skills = [
                { name: 'Python', value: 90, color: '#3776ab' },
                { name: 'SQL', value: 85, color: '#336791' },
                { name: 'Excel', value: 95, color: '#217346' },
                { name: 'Tableau', value: 80, color: '#e97627' },
                { name: 'R语言', value: 75, color: '#276dc3' },
                { name: 'Machine Learning', value: 70, color: '#ff6b35' },
                { name: 'Statistics', value: 85, color: '#4ecdc4' },
                { name: 'Data Visualization', value: 88, color: '#45b7d1' }
            ];

            // 清除画布
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            // 绘制背景网格
            ctx.strokeStyle = 'rgba(255, 255, 255, 0.2)';
            ctx.lineWidth = 1;
            for (let i = 1; i <= 5; i++) {
                ctx.beginPath();
                ctx.arc(centerX, centerY, (radius / 5) * i, 0, 2 * Math.PI);
                ctx.stroke();
            }

            // 绘制轴线
            const angleStep = (2 * Math.PI) / skills.length;
            for (let i = 0; i < skills.length; i++) {
                const angle = i * angleStep - Math.PI / 2;
                const x = centerX + Math.cos(angle) * radius;
                const y = centerY + Math.sin(angle) * radius;

                ctx.beginPath();
                ctx.moveTo(centerX, centerY);
                ctx.lineTo(x, y);
                ctx.stroke();

                // 绘制技能标签
                ctx.fillStyle = 'white';
                ctx.font = '12px Inter';
                ctx.textAlign = 'center';
                const labelX = centerX + Math.cos(angle) * (radius + 20);
                const labelY = centerY + Math.sin(angle) * (radius + 20);
                ctx.fillText(skills[i].name, labelX, labelY);
            }

            // 绘制技能多边形
            ctx.beginPath();
            for (let i = 0; i < skills.length; i++) {
                const angle = i * angleStep - Math.PI / 2;
                const value = skills[i].value / 100;
                const x = centerX + Math.cos(angle) * radius * value;
                const y = centerY + Math.sin(angle) * radius * value;

                if (i === 0) {
                    ctx.moveTo(x, y);
                } else {
                    ctx.lineTo(x, y);
                }
            }
            ctx.closePath();
            ctx.fillStyle = 'rgba(102, 126, 234, 0.3)';
            ctx.fill();
            ctx.strokeStyle = 'rgba(102, 126, 234, 0.8)';
            ctx.lineWidth = 2;
            ctx.stroke();

            // 绘制技能点
            for (let i = 0; i < skills.length; i++) {
                const angle = i * angleStep - Math.PI / 2;
                const value = skills[i].value / 100;
                const x = centerX + Math.cos(angle) * radius * value;
                const y = centerY + Math.sin(angle) * radius * value;

                ctx.beginPath();
                ctx.arc(x, y, 4, 0, 2 * Math.PI);
                ctx.fillStyle = skills[i].color;
                ctx.fill();
                ctx.strokeStyle = 'white';
                ctx.lineWidth = 2;
                ctx.stroke();
            }
        }

        // 页面加载完成后执行
        document.addEventListener('DOMContentLoaded', function() {
            // 创建粒子背景
            createParticles();

            // 创建技能图表
            createSkillChart();

            // 加载天气和访客信息
            loadWeather();
            loadVisitorInfo();

            // 滚动事件监听
            window.addEventListener('scroll', handleNavbarScroll);

            // 添加滚动动画
            const observerOptions = {
                threshold: 0.1,
                rootMargin: '0px 0px -50px 0px'
            };

            const observer = new IntersectionObserver(function(entries) {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.style.opacity = '1';
                        entry.target.style.transform = 'translateY(0)';
                    }
                });
            }, observerOptions);

            // 观察所有需要动画的元素
            document.querySelectorAll('.fade-in-up').forEach(el => {
                el.style.opacity = '0';
                el.style.transform = 'translateY(30px)';
                el.style.transition = 'all 0.6s ease-out';
                observer.observe(el);
            });

            // 为导航链接添加活动状态
            const currentPath = window.location.pathname;
            document.querySelectorAll('.navbar-nav .nav-link').forEach(link => {
                if (link.getAttribute('href') === currentPath) {
                    link.classList.add('active');
                }
            });
        });
    </script>
</body>
</html>
'''

# 统一的页面基础样式
BASE_STYLES = '''
    <style>
        :root {
            --primary-color: #667eea;
            --secondary-color: #764ba2;
            --accent-color: #f093fb;
            --data-blue: #3b82f6;
            --data-purple: #8b5cf6;
            --data-green: #10b981;
            --data-orange: #f59e0b;
            --data-red: #ef4444;
            --success-color: #4ecdc4;
            --warning-color: #ffe66d;
            --danger-color: #ff6b6b;
            --dark-color: #1e293b;
            --light-color: #f8fafc;
            --gradient-primary: linear-gradient(135deg, var(--data-blue) 0%, var(--data-purple) 100%);
            --gradient-accent: linear-gradient(135deg, var(--accent-color) 0%, var(--primary-color) 100%);
            --gradient-data: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
            --shadow-sm: 0 2px 4px rgba(0,0,0,0.1);
            --shadow-md: 0 4px 6px rgba(0,0,0,0.1);
            --shadow-lg: 0 10px 15px rgba(0,0,0,0.1);
            --shadow-xl: 0 20px 25px rgba(0,0,0,0.1);
            --shadow-glow: 0 0 20px rgba(102, 126, 234, 0.3);
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #f8fafc;
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%);
            min-height: 100vh;
            overflow-x: hidden;
        }

        /* 粒子背景 */
        .particles-bg {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: -1;
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%);
        }

        .particle {
            position: absolute;
            background: rgba(102, 126, 234, 0.6);
            border-radius: 50%;
            animation: float 6s ease-in-out infinite;
        }

        @keyframes float {
            0%, 100% { transform: translateY(0px) rotate(0deg); opacity: 0.7; }
            50% { transform: translateY(-20px) rotate(180deg); opacity: 1; }
        }

        /* 超炫酷导航栏 */
        .navbar {
            background: rgba(15, 23, 42, 0.95) !important;
            backdrop-filter: blur(20px);
            border-bottom: 1px solid rgba(102, 126, 234, 0.2);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            padding: 1rem 0;
            position: fixed !important;
            top: 0;
            width: 100%;
            z-index: 1000;
            transition: all 0.3s ease;
        }

        .navbar.scrolled {
            background: rgba(15, 23, 42, 0.98) !important;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
        }

        .navbar-brand {
            font-weight: 700;
            font-size: 1.5rem;
            color: white !important;
            text-shadow: 0 0 10px rgba(102, 126, 234, 0.5);
            transition: all 0.3s ease;
        }

        .navbar-brand:hover {
            color: var(--data-blue) !important;
            text-shadow: 0 0 20px rgba(102, 126, 234, 0.8);
            transform: scale(1.05);
        }

        .navbar-nav .nav-link {
            color: rgba(255,255,255,0.9) !important;
            font-weight: 500;
            margin: 0 0.5rem;
            padding: 0.5rem 1rem !important;
            border-radius: 25px;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }

        .navbar-nav .nav-link::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: var(--gradient-primary);
            transition: all 0.3s ease;
            z-index: -1;
        }

        .navbar-nav .nav-link:hover {
            color: white !important;
            transform: translateY(-2px);
            box-shadow: var(--shadow-glow);
        }

        .navbar-nav .nav-link:hover::before {
            left: 0;
        }

        .navbar-nav .nav-link.active {
            background: var(--gradient-primary);
            color: white !important;
            box-shadow: var(--shadow-glow);
        }

        /* 页面内容顶部间距 */
        .main-content {
            margin-top: 80px;
            padding: 2rem 0;
        }

        /* 超炫酷卡片 */
        .cool-card {
            background: rgba(30, 41, 59, 0.8);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(102, 126, 234, 0.2);
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
            transition: all 0.3s ease;
            overflow: hidden;
            position: relative;
        }

        .cool-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 2px;
            background: var(--gradient-primary);
        }

        .cool-card:hover {
            transform: translateY(-10px);
            box-shadow: 0 30px 60px rgba(0, 0, 0, 0.4);
            border-color: rgba(102, 126, 234, 0.4);
        }

        /* 按钮样式 */
        .btn-cool {
            background: var(--gradient-primary);
            border: none;
            border-radius: 25px;
            padding: 0.75rem 2rem;
            color: white;
            font-weight: 500;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }

        .btn-cool:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-glow);
            color: white;
        }

        .btn-cool::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
            transition: all 0.5s ease;
        }

        .btn-cool:hover::before {
            left: 100%;
        }

        /* 标签样式 */
        .cool-tag {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            margin: 0.25rem;
            border-radius: 50px;
            font-size: 0.875rem;
            font-weight: 500;
            text-decoration: none;
            transition: all 0.3s ease;
            border: 1px solid rgba(255,255,255,0.2);
        }

        .cool-tag:hover {
            transform: translateY(-2px);
            text-decoration: none;
            box-shadow: var(--shadow-glow);
        }

        /* 页面标题 */
        .page-title {
            font-size: 3rem;
            font-weight: 800;
            text-align: center;
            margin-bottom: 3rem;
            background: linear-gradient(45deg, #ffffff, #e0e7ff, #c7d2fe);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            text-shadow: 0 0 30px rgba(102, 126, 234, 0.5);
        }

        /* 动画效果 */
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .fade-in-up {
            animation: fadeInUp 0.6s ease-out;
        }
    </style>
'''

# 统一的导航栏HTML
NAVBAR_HTML = '''
    <!-- 粒子背景 -->
    <div class="particles-bg" id="particles-bg"></div>

    <!-- 超炫酷导航栏 -->
    <nav class="navbar navbar-expand-lg navbar-dark">
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
                        <a class="nav-link" href="{{ url_for('timeline') }}">
                            <i class="fas fa-history me-1"></i>历程
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="{{ url_for('links') }}">
                            <i class="fas fa-link me-1"></i>友链
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
'''

# 统一的JavaScript
BASE_JAVASCRIPT = '''
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // 创建粒子背景
        function createParticles() {
            const particlesContainer = document.getElementById('particles-bg');
            if (!particlesContainer) return;

            const particleCount = 50;

            for (let i = 0; i < particleCount; i++) {
                const particle = document.createElement('div');
                particle.className = 'particle';

                // 随机大小和位置
                const size = Math.random() * 4 + 2;
                particle.style.width = size + 'px';
                particle.style.height = size + 'px';
                particle.style.left = Math.random() * 100 + '%';
                particle.style.top = Math.random() * 100 + '%';

                // 随机动画延迟
                particle.style.animationDelay = Math.random() * 6 + 's';
                particle.style.animationDuration = (Math.random() * 3 + 3) + 's';

                particlesContainer.appendChild(particle);
            }
        }

        // 导航栏滚动效果
        function handleNavbarScroll() {
            const navbar = document.querySelector('.navbar');
            if (window.scrollY > 50) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }
        }

        // 页面加载完成后执行
        document.addEventListener('DOMContentLoaded', function() {
            // 创建粒子背景
            createParticles();

            // 滚动事件监听
            window.addEventListener('scroll', handleNavbarScroll);

            // 添加滚动动画
            const observerOptions = {
                threshold: 0.1,
                rootMargin: '0px 0px -50px 0px'
            };

            const observer = new IntersectionObserver(function(entries) {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.style.opacity = '1';
                        entry.target.style.transform = 'translateY(0)';
                    }
                });
            }, observerOptions);

            // 观察所有需要动画的元素
            document.querySelectorAll('.fade-in-up').forEach(el => {
                el.style.opacity = '0';
                el.style.transform = 'translateY(30px)';
                el.style.transition = 'all 0.6s ease-out';
                observer.observe(el);
            });

            // 为导航链接添加活动状态
            const currentPath = window.location.pathname;
            document.querySelectorAll('.navbar-nav .nav-link').forEach(link => {
                if (link.getAttribute('href') === currentPath) {
                    link.classList.add('active');
                }
            });
        });
    </script>
'''

# 博客列表页面模板
BLOG_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>博客文章 - {{ config.BLOG_TITLE }}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    ''' + BASE_STYLES + '''
</head>
<body>
    ''' + NAVBAR_HTML + '''

    <!-- 主要内容区域 -->
    <div class="main-content">
        <div class="container">
            <h1 class="page-title fade-in-up">📝 学习笔记</h1>

            <!-- 搜索和筛选 -->
            <div class="row mb-5 fade-in-up justify-content-center">
                <div class="col-md-6">
                    <form method="GET" class="d-flex">
                        <input type="text" name="search" class="form-control me-2"
                               placeholder="🔍 搜索学习笔记..."
                               value="{{ search_query or '' }}"
                               style="background: rgba(30, 41, 59, 0.8); border: 1px solid rgba(102, 126, 234, 0.3); color: white; border-radius: 20px; padding: 0.6rem 1.2rem; font-size: 0.9rem;">
                        <button type="submit" class="btn btn-cool btn-sm">
                            <i class="fas fa-search"></i>
                        </button>
                    </form>
                </div>
                <div class="col-md-3">
                    <select class="form-select form-select-sm"
                            onchange="location.href='{{ url_for('blog') }}?category=' + this.value"
                            style="background: rgba(30, 41, 59, 0.8); border: 1px solid rgba(102, 126, 234, 0.3); color: white; border-radius: 20px; padding: 0.6rem 1.2rem; font-size: 0.9rem;">
                        <option value="">📚 所有分类</option>
                        {% for category in categories %}
                        <option value="{{ category.id }}" {% if current_category == category.id %}selected{% endif %}>
                            {{ category.name }}
                        </option>
                        {% endfor %}
                    </select>
                </div>
            </div>

            <!-- 文章列表 -->
            <div class="row">
                {% for post in posts.items %}
                <div class="col-md-6 mb-4 fade-in-up">
                    <div class="cool-card h-100 p-4">
                        <div class="d-flex align-items-start mb-3">
                            {% if post.category %}
                            <div class="me-3">
                                <i class="{{ post.category.icon }}" style="color: {{ post.category.color }}; font-size: 1.5rem;"></i>
                            </div>
                            {% endif %}
                            <div class="flex-grow-1">
                                <h5 class="mb-2">
                                    <a href="{{ url_for('post', slug=post.slug) }}"
                                       class="text-decoration-none text-white"
                                       style="transition: all 0.3s ease;">
                                        {{ post.title }}
                                    </a>
                                </h5>
                                <p class="text-light opacity-75 mb-3">{{ post.summary or post.content[:120] + '...' }}</p>
                            </div>
                        </div>

                        <!-- 标签 -->
                        {% if post.tags %}
                        <div class="mb-3">
                            {% for tag in post.tags %}
                            <span class="cool-tag" style="background-color: {{ tag.color }}20; color: {{ tag.color }}; border-color: {{ tag.color }}40;">
                                {{ tag.name }}
                            </span>
                            {% endfor %}
                        </div>
                        {% endif %}

                        <div class="d-flex justify-content-between align-items-center">
                            <small class="text-light opacity-75">
                                <i class="fas fa-calendar me-1"></i>{{ post.created_at.strftime('%Y年%m月%d日') }}
                                <i class="fas fa-eye ms-3 me-1"></i>{{ post.view_count }} 次阅读
                            </small>
                            {% if post.category %}
                            <span class="cool-tag" style="background-color: {{ post.category.color }}; color: white; border-color: {{ post.category.color }};">
                                <i class="{{ post.category.icon }} me-1"></i>{{ post.category.name }}
                            </span>
                            {% endif %}
                        </div>
                    </div>
                </div>
                {% endfor %}
            </div>

            <!-- 分页 -->
            {% if posts.pages > 1 %}
            <nav class="mt-5 fade-in-up">
                <ul class="pagination justify-content-center">
                    {% if posts.has_prev %}
                    <li class="page-item">
                        <a class="page-link btn-cool me-2" href="{{ url_for('blog', page=posts.prev_num) }}">
                            <i class="fas fa-chevron-left me-1"></i>上一页
                        </a>
                    </li>
                    {% endif %}

                    {% for page_num in posts.iter_pages() %}
                        {% if page_num %}
                            {% if page_num != posts.page %}
                            <li class="page-item">
                                <a class="page-link cool-tag me-1" href="{{ url_for('blog', page=page_num) }}">{{ page_num }}</a>
                            </li>
                            {% else %}
                            <li class="page-item active">
                                <span class="page-link btn-cool me-1">{{ page_num }}</span>
                            </li>
                            {% endif %}
                        {% else %}
                        <li class="page-item disabled">
                            <span class="page-link cool-tag me-1">…</span>
                        </li>
                        {% endif %}
                    {% endfor %}

                    {% if posts.has_next %}
                    <li class="page-item">
                        <a class="page-link btn-cool ms-2" href="{{ url_for('blog', page=posts.next_num) }}">
                            下一页<i class="fas fa-chevron-right ms-1"></i>
                        </a>
                    </li>
                    {% endif %}
                </ul>
            </nav>
            {% endif %}
        </div>
    </div>

    ''' + BASE_JAVASCRIPT + '''
</body>
</html>
'''

# 项目展示页面模板
PROJECTS_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>项目展示 - {{ config.BLOG_TITLE }}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    ''' + BASE_STYLES + '''
    <style>
        /* 项目卡片特殊样式 */
        .project-card {
            background: rgba(30, 41, 59, 0.9);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(102, 126, 234, 0.3);
            border-radius: 20px;
            padding: 2rem;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
            transition: all 0.3s ease;
            height: 100%;
            position: relative;
            overflow: hidden;
        }

        .project-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: var(--gradient-primary);
        }

        .project-card:hover {
            transform: translateY(-15px);
            box-shadow: 0 30px 60px rgba(0, 0, 0, 0.4);
            border-color: rgba(102, 126, 234, 0.5);
        }

        .project-icon {
            width: 60px;
            height: 60px;
            border-radius: 15px;
            background: var(--gradient-primary);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 1.5rem;
            margin-bottom: 1.5rem;
            box-shadow: var(--shadow-glow);
        }

        .tech-badge {
            display: inline-block;
            padding: 0.4rem 0.8rem;
            margin: 0.25rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 500;
            border: 1px solid rgba(255,255,255,0.2);
            transition: all 0.3s ease;
        }

        .tech-badge:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-glow);
        }

        .project-status {
            position: absolute;
            top: 1rem;
            right: 1rem;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 500;
        }

        .status-completed {
            background: rgba(16, 185, 129, 0.2);
            color: #10b981;
            border: 1px solid rgba(16, 185, 129, 0.3);
        }

        .status-progress {
            background: rgba(245, 158, 11, 0.2);
            color: #f59e0b;
            border: 1px solid rgba(245, 158, 11, 0.3);
        }

        .status-planned {
            background: rgba(107, 114, 128, 0.2);
            color: #6b7280;
            border: 1px solid rgba(107, 114, 128, 0.3);
        }
    </style>
</head>
<body>
    ''' + NAVBAR_HTML + '''

    <!-- 主要内容区域 -->
    <div class="main-content">
        <div class="container">
            <h1 class="page-title fade-in-up">💻 数据分析项目作品集</h1>
            <p class="text-center text-light opacity-75 mb-5 fade-in-up" style="font-size: 1.2rem;">
                展示我在大学四年中完成的数据分析项目<br>
                从数据清洗到机器学习，从可视化到业务洞察
            </p>

            <!-- 精选项目 -->
            {% if featured_projects %}
            <div class="mb-5 fade-in-up">
                <h2 class="text-center mb-4" style="color: #e0e7ff; font-size: 2rem; font-weight: 600;">
                    🌟 精选项目
                </h2>
                <div class="row">
                    {% for project in featured_projects %}
                    <div class="col-md-6 col-lg-4 mb-4 fade-in-up">
                        <div class="project-card">
                            <div class="project-status
                                {% if project.status == 'completed' %}status-completed
                                {% elif project.status == 'in_progress' %}status-progress
                                {% else %}status-planned{% endif %}">
                                {% if project.status == 'completed' %}✅ 已完成
                                {% elif project.status == 'in_progress' %}🚧 进行中
                                {% else %}📋 计划中{% endif %}
                            </div>

                            <div class="project-icon">
                                <i class="fas fa-chart-line"></i>
                            </div>

                            <h5 class="mb-3 text-white">{{ project.name }}</h5>
                            <p class="text-light opacity-75 mb-3">{{ project.description }}</p>

                            <div class="mb-4">
                                {% for tech in project.get_tech_list() %}
                                <span class="tech-badge" style="background-color: rgba(102, 126, 234, 0.2); color: #667eea; border-color: rgba(102, 126, 234, 0.3);">
                                    {{ tech }}
                                </span>
                                {% endfor %}
                            </div>

                            <div class="d-flex gap-2 mt-auto">
                                {% if project.github_url %}
                                <a href="{{ project.github_url }}" class="btn btn-cool btn-sm flex-grow-1" target="_blank">
                                    <i class="fab fa-github me-1"></i>GitHub
                                </a>
                                {% endif %}
                                {% if project.demo_url %}
                                <a href="{{ project.demo_url }}" class="btn btn-cool btn-sm flex-grow-1" target="_blank">
                                    <i class="fas fa-external-link-alt me-1"></i>演示
                                </a>
                                {% endif %}
                            </div>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
            {% endif %}

            <!-- 其他项目 -->
            {% if other_projects %}
            <div class="fade-in-up">
                <h2 class="text-center mb-4" style="color: #e0e7ff; font-size: 2rem; font-weight: 600;">
                    🔧 其他项目
                </h2>
                <div class="row">
                    {% for project in other_projects %}
                    <div class="col-md-6 col-lg-4 mb-4 fade-in-up">
                        <div class="project-card">
                            <div class="project-status
                                {% if project.status == 'completed' %}status-completed
                                {% elif project.status == 'in_progress' %}status-progress
                                {% else %}status-planned{% endif %}">
                                {% if project.status == 'completed' %}✅
                                {% elif project.status == 'in_progress' %}🚧
                                {% else %}📋{% endif %}
                            </div>

                            <div class="project-icon">
                                <i class="fas fa-code"></i>
                            </div>

                            <h6 class="mb-3 text-white">{{ project.name }}</h6>
                            <p class="text-light opacity-75 mb-3 small">{{ project.description }}</p>

                            <div class="mb-4">
                                {% for tech in project.get_tech_list()[:3] %}
                                <span class="tech-badge" style="background-color: rgba(139, 92, 246, 0.2); color: #8b5cf6; border-color: rgba(139, 92, 246, 0.3);">
                                    {{ tech }}
                                </span>
                                {% endfor %}
                            </div>

                            <div class="d-flex gap-2 mt-auto">
                                {% if project.github_url %}
                                <a href="{{ project.github_url }}" class="btn btn-cool btn-sm" target="_blank">
                                    <i class="fab fa-github"></i>
                                </a>
                                {% endif %}
                                {% if project.demo_url %}
                                <a href="{{ project.demo_url }}" class="btn btn-cool btn-sm" target="_blank">
                                    <i class="fas fa-external-link-alt"></i>
                                </a>
                                {% endif %}
                            </div>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
            {% endif %}

            <!-- 技能统计 -->
            <div class="row mt-5 fade-in-up">
                <div class="col-md-3 mb-3">
                    <div class="cool-card text-center p-4">
                        <i class="fas fa-project-diagram text-primary mb-3" style="font-size: 2rem;"></i>
                        <h4 class="text-white">10+</h4>
                        <p class="text-light opacity-75 mb-0">完成项目</p>
                    </div>
                </div>
                <div class="col-md-3 mb-3">
                    <div class="cool-card text-center p-4">
                        <i class="fas fa-database text-success mb-3" style="font-size: 2rem;"></i>
                        <h4 class="text-white">50GB+</h4>
                        <p class="text-light opacity-75 mb-0">处理数据</p>
                    </div>
                </div>
                <div class="col-md-3 mb-3">
                    <div class="cool-card text-center p-4">
                        <i class="fas fa-chart-bar text-warning mb-3" style="font-size: 2rem;"></i>
                        <h4 class="text-white">100+</h4>
                        <p class="text-light opacity-75 mb-0">可视化图表</p>
                    </div>
                </div>
                <div class="col-md-3 mb-3">
                    <div class="cool-card text-center p-4">
                        <i class="fas fa-brain text-danger mb-3" style="font-size: 2rem;"></i>
                        <h4 class="text-white">20+</h4>
                        <p class="text-light opacity-75 mb-0">机器学习模型</p>
                    </div>
                </div>
            </div>
        </div>
    </div>

    ''' + BASE_JAVASCRIPT + '''
</body>
</html>
'''

# 时间线页面模板
TIMELINE_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>学习历程 - {{ config.BLOG_TITLE }}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    ''' + BASE_STYLES + '''
    <style>
        /* 超炫酷时间线样式 */
        .timeline {
            position: relative;
            padding: 3rem 0;
        }

        .timeline::before {
            content: '';
            position: absolute;
            left: 50%;
            top: 0;
            bottom: 0;
            width: 4px;
            background: var(--gradient-primary);
            transform: translateX(-50%);
            border-radius: 2px;
            box-shadow: var(--shadow-glow);
        }

        .timeline-item {
            position: relative;
            margin-bottom: 4rem;
            opacity: 0;
            transform: translateY(50px);
            transition: all 0.6s ease;
        }

        .timeline-item.animate {
            opacity: 1;
            transform: translateY(0);
        }

        .timeline-content {
            background: rgba(30, 41, 59, 0.9);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(102, 126, 234, 0.3);
            border-radius: 20px;
            padding: 2rem;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
            width: 45%;
            position: relative;
            transition: all 0.3s ease;
        }

        .timeline-content::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: var(--gradient-primary);
            border-radius: 20px 20px 0 0;
        }

        .timeline-content:hover {
            transform: translateY(-10px);
            box-shadow: 0 30px 60px rgba(0, 0, 0, 0.4);
            border-color: rgba(102, 126, 234, 0.5);
        }

        .timeline-left .timeline-content {
            margin-left: 55%;
        }

        .timeline-right .timeline-content {
            margin-right: 55%;
        }

        /* 添加箭头指向中心线 */
        .timeline-left .timeline-content::after {
            content: '';
            position: absolute;
            top: 2rem;
            right: -15px;
            width: 0;
            height: 0;
            border: 15px solid transparent;
            border-left-color: rgba(102, 126, 234, 0.3);
        }

        .timeline-right .timeline-content::after {
            content: '';
            position: absolute;
            top: 2rem;
            left: -15px;
            width: 0;
            height: 0;
            border: 15px solid transparent;
            border-right-color: rgba(102, 126, 234, 0.3);
        }

        .timeline-icon {
            position: absolute;
            left: 50%;
            top: 2rem;
            transform: translateX(-50%);
            width: 60px;
            height: 60px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 1.5rem;
            background: var(--gradient-primary);
            box-shadow: var(--shadow-glow);
            border: 3px solid rgba(15, 23, 42, 1);
            z-index: 10;
        }

        .timeline-date {
            position: absolute;
            left: 50%;
            top: 5rem;
            transform: translateX(-50%);
            background: rgba(30, 41, 59, 0.9);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(102, 126, 234, 0.3);
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.3);
            white-space: nowrap;
            font-weight: 500;
        }

        .year-header {
            text-align: center;
            margin: 4rem 0 2rem;
            position: relative;
        }

        .year-title {
            font-size: 2.5rem;
            font-weight: 800;
            background: var(--gradient-primary);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            text-shadow: 0 0 30px rgba(102, 126, 234, 0.5);
            display: inline-block;
            padding: 1rem 2rem;
            border: 2px solid rgba(102, 126, 234, 0.3);
            border-radius: 50px;
            background-color: rgba(30, 41, 59, 0.8);
            backdrop-filter: blur(20px);
        }

        /* 响应式设计 */
        @media (max-width: 768px) {
            .timeline::before {
                left: 30px;
            }

            .timeline-content {
                width: calc(100% - 80px);
                margin-left: 80px !important;
                margin-right: 0 !important;
            }

            .timeline-icon {
                left: 30px;
            }

            .timeline-date {
                left: 30px;
                top: 6rem;
            }
        }
    </style>
</head>
<body>
    ''' + NAVBAR_HTML + '''

    <!-- 主要内容区域 -->
    <div class="main-content">
        <div class="container">
            <h1 class="page-title fade-in-up">🎓 我的数据分析师成长历程</h1>
            <p class="text-center text-light opacity-75 mb-5 fade-in-up" style="font-size: 1.2rem;">
                从2021年9月踏入大学校园，到2025年6月即将毕业<br>
                记录我在数据科学道路上的每一个重要时刻
            </p>

            <div class="timeline">
                {% for year, items in timeline_by_year.items() %}
                <div class="year-header fade-in-up">
                    <div class="year-title">{{ year }}年</div>
                </div>
                {% for item in items %}
                <div class="timeline-item {{ 'timeline-left' if loop.index % 2 == 1 else 'timeline-right' }}">
                    <div class="timeline-icon" style="background: {{ item.color }};">
                        <i class="{{ item.icon }}"></i>
                    </div>
                    <div class="timeline-date">
                        {{ item.date.strftime('%m月%d日') }}
                    </div>
                    <div class="timeline-content">
                        <h5 class="mb-3 text-white">{{ item.title }}</h5>
                        <p class="text-light opacity-75 mb-3">{{ item.description }}</p>
                        <div class="d-flex align-items-center justify-content-between">
                            <span class="cool-tag" style="background-color: {{ item.color }}; color: white; border-color: {{ item.color }};">
                                <i class="{{ item.icon }} me-1"></i>
                                {% if item.category == 'education' %}📚 学习成长
                                {% elif item.category == 'work' %}💼 实习工作
                                {% elif item.category == 'project' %}🚀 项目实战
                                {% elif item.category == 'competition' %}🏆 竞赛获奖
                                {% elif item.category == 'skill' %}💡 技能提升
                                {% else %}🌟 重要时刻{% endif %}
                            </span>
                            {% if item.link %}
                            <a href="{{ item.link }}" class="btn btn-cool btn-sm" target="_blank">
                                <i class="fas fa-external-link-alt me-1"></i>查看详情
                            </a>
                            {% endif %}
                        </div>
                    </div>
                </div>
                {% endfor %}
                {% endfor %}
            </div>

            <!-- 统计信息 -->
            <div class="row mt-5 fade-in-up">
                <div class="col-md-3 mb-3">
                    <div class="cool-card text-center p-4">
                        <i class="fas fa-graduation-cap text-primary mb-3" style="font-size: 2rem;"></i>
                        <h4 class="text-white">4年</h4>
                        <p class="text-light opacity-75 mb-0">大学学习</p>
                    </div>
                </div>
                <div class="col-md-3 mb-3">
                    <div class="cool-card text-center p-4">
                        <i class="fas fa-code text-success mb-3" style="font-size: 2rem;"></i>
                        <h4 class="text-white">15+</h4>
                        <p class="text-light opacity-75 mb-0">技能掌握</p>
                    </div>
                </div>
                <div class="col-md-3 mb-3">
                    <div class="cool-card text-center p-4">
                        <i class="fas fa-project-diagram text-warning mb-3" style="font-size: 2rem;"></i>
                        <h4 class="text-white">10+</h4>
                        <p class="text-light opacity-75 mb-0">项目经验</p>
                    </div>
                </div>
                <div class="col-md-3 mb-3">
                    <div class="cool-card text-center p-4">
                        <i class="fas fa-trophy text-danger mb-3" style="font-size: 2rem;"></i>
                        <h4 class="text-white">5+</h4>
                        <p class="text-light opacity-75 mb-0">竞赛获奖</p>
                    </div>
                </div>
            </div>
        </div>
    </div>

    ''' + BASE_JAVASCRIPT + '''
    <script>
        // 时间线动画
        document.addEventListener('DOMContentLoaded', function() {
            const timelineItems = document.querySelectorAll('.timeline-item');

            const observer = new IntersectionObserver((entries) => {
                entries.forEach((entry, index) => {
                    if (entry.isIntersecting) {
                        setTimeout(() => {
                            entry.target.classList.add('animate');
                        }, index * 200);
                    }
                });
            }, {
                threshold: 0.1,
                rootMargin: '0px 0px -50px 0px'
            });

            timelineItems.forEach(item => {
                observer.observe(item);
            });
        });
    </script>
</body>
</html>
'''

# 友情链接页面模板
LINKS_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>友情链接 - {{ config.BLOG_TITLE }}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    ''' + BASE_STYLES + '''
    <style>
        /* 链接卡片特殊样式 */
        .link-card {
            background: rgba(30, 41, 59, 0.9);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(102, 126, 234, 0.3);
            border-radius: 20px;
            padding: 2rem;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
            transition: all 0.3s ease;
            text-decoration: none;
            color: inherit;
            display: block;
            height: 100%;
            position: relative;
            overflow: hidden;
        }

        .link-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: var(--gradient-primary);
        }

        .link-card:hover {
            transform: translateY(-10px);
            text-decoration: none;
            color: inherit;
            box-shadow: 0 30px 60px rgba(0, 0, 0, 0.4);
            border-color: rgba(102, 126, 234, 0.5);
        }

        .link-avatar {
            width: 70px;
            height: 70px;
            border-radius: 50%;
            background: var(--gradient-primary);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 1.8rem;
            margin: 0 auto 1.5rem;
            box-shadow: var(--shadow-glow);
            border: 3px solid rgba(255, 255, 255, 0.1);
        }

        .link-category {
            text-align: center;
            margin: 4rem 0 2rem;
        }

        .category-title {
            font-size: 2rem;
            font-weight: 700;
            background: var(--gradient-primary);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            display: inline-block;
            padding: 1rem 2rem;
            border: 2px solid rgba(102, 126, 234, 0.3);
            border-radius: 50px;
            background-color: rgba(30, 41, 59, 0.8);
            backdrop-filter: blur(20px);
        }
    </style>
</head>
<body>
    ''' + NAVBAR_HTML + '''

    <!-- 主要内容区域 -->
    <div class="main-content">
        <div class="container">
            <h1 class="page-title fade-in-up">🔗 数据分析师资源导航</h1>
            <p class="text-center text-light opacity-75 mb-5 fade-in-up" style="font-size: 1.2rem;">
                精选数据分析学习资源、工具网站和同行博客<br>
                助力数据分析师职业发展的优质资源合集
            </p>

            <!-- 朋友链接 -->
            {% if friend_links %}
            <div class="link-category fade-in-up">
                <div class="category-title">👥 同行博客</div>
            </div>
            <div class="row mb-5">
                {% for link in friend_links %}
                <div class="col-md-6 col-lg-4 mb-4 fade-in-up">
                    <a href="{{ link.url }}" class="link-card" target="_blank">
                        <div class="link-avatar">
                            {% if link.avatar %}
                            <img src="{{ link.avatar }}" alt="{{ link.name }}" class="w-100 h-100 rounded-circle">
                            {% else %}
                            <i class="fas fa-user-graduate"></i>
                            {% endif %}
                        </div>
                        <h6 class="text-center mb-2 text-white">{{ link.name }}</h6>
                        <p class="text-center text-light opacity-75 small mb-0">{{ link.description or '数据分析师同行博客' }}</p>
                    </a>
                </div>
                {% endfor %}
            </div>
            {% endif %}

            <!-- 学习资源 -->
            {% if recommend_links %}
            <div class="link-category fade-in-up">
                <div class="category-title">📚 学习资源</div>
            </div>
            <div class="row mb-5">
                {% for link in recommend_links %}
                <div class="col-md-6 col-lg-4 mb-4 fade-in-up">
                    <a href="{{ link.url }}" class="link-card" target="_blank">
                        <div class="link-avatar">
                            <i class="fas fa-graduation-cap"></i>
                        </div>
                        <h6 class="text-center mb-2 text-white">{{ link.name }}</h6>
                        <p class="text-center text-light opacity-75 small mb-0">{{ link.description or '优质学习资源' }}</p>
                    </a>
                </div>
                {% endfor %}
            </div>
            {% endif %}

            <!-- 数据分析工具 -->
            {% if tool_links %}
            <div class="link-category fade-in-up">
                <div class="category-title">🛠️ 数据分析工具</div>
            </div>
            <div class="row mb-5">
                {% for link in tool_links %}
                <div class="col-md-6 col-lg-4 mb-4 fade-in-up">
                    <a href="{{ link.url }}" class="link-card" target="_blank">
                        <div class="link-avatar">
                            <i class="fas fa-chart-line"></i>
                        </div>
                        <h6 class="text-center mb-2 text-white">{{ link.name }}</h6>
                        <p class="text-center text-light opacity-75 small mb-0">{{ link.description or '实用数据分析工具' }}</p>
                    </a>
                </div>
                {% endfor %}
            </div>
            {% endif %}

            <!-- 申请友链 -->
            <div class="text-center mt-5 fade-in-up">
                <div class="cool-card p-4 d-inline-block">
                    <h5 class="text-white mb-3">💌 申请友链</h5>
                    <p class="text-light opacity-75 mb-3">
                        如果你也是数据分析师或相关领域的同学，欢迎申请友链交换！
                    </p>
                    <div class="row text-start">
                        <div class="col-md-6">
                            <p class="text-light opacity-75 mb-1"><strong>网站要求：</strong></p>
                            <ul class="text-light opacity-75 small">
                                <li>数据分析/科学相关内容</li>
                                <li>原创内容为主</li>
                                <li>网站稳定访问</li>
                            </ul>
                        </div>
                        <div class="col-md-6">
                            <p class="text-light opacity-75 mb-1"><strong>本站信息：</strong></p>
                            <ul class="text-light opacity-75 small">
                                <li>名称：wswldcs的数据分析之路</li>
                                <li>描述：2025届数据分析师求职博客</li>
                                <li>链接：https://wswldcs.edu.deal</li>
                            </ul>
                        </div>
                    </div>
                    <a href="mailto:your-email@example.com" class="btn btn-cool mt-3">
                        <i class="fas fa-envelope me-2"></i>联系申请友链
                    </a>
                </div>
            </div>
        </div>
    </div>

    ''' + BASE_JAVASCRIPT + '''
</body>
</html>
'''

# 关于页面模板
ABOUT_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>关于我 - {{ config.BLOG_TITLE }}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    ''' + BASE_STYLES + '''
    <style>
        /* 关于页面特殊样式 */
        .about-card {
            background: rgba(30, 41, 59, 0.9);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(102, 126, 234, 0.3);
            border-radius: 20px;
            padding: 2rem;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
            margin-bottom: 2rem;
            position: relative;
            overflow: hidden;
        }

        .about-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: var(--gradient-primary);
        }

        .skill-bar {
            background: rgba(15, 23, 42, 0.8);
            border-radius: 15px;
            height: 12px;
            overflow: hidden;
            margin-bottom: 1rem;
            border: 1px solid rgba(102, 126, 234, 0.2);
        }

        .skill-progress {
            background: var(--gradient-primary);
            height: 100%;
            border-radius: 15px;
            transition: width 2s ease;
            position: relative;
            overflow: hidden;
        }

        .skill-progress::after {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
            animation: shimmer 2s infinite;
        }

        @keyframes shimmer {
            0% { left: -100%; }
            100% { left: 100%; }
        }

        .avatar {
            width: 180px;
            height: 180px;
            border-radius: 50%;
            background: var(--gradient-primary);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 4rem;
            margin: 0 auto 2rem;
            box-shadow: var(--shadow-glow);
            border: 4px solid rgba(255, 255, 255, 0.1);
            position: relative;
            overflow: hidden;
        }

        .avatar::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: linear-gradient(45deg, transparent, rgba(255,255,255,0.1), transparent);
            animation: rotate 3s linear infinite;
        }

        @keyframes rotate {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .social-link {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 50px;
            height: 50px;
            border-radius: 50%;
            background: var(--gradient-primary);
            color: white;
            text-decoration: none;
            margin: 0 0.5rem;
            transition: all 0.3s ease;
            box-shadow: var(--shadow-md);
        }

        .social-link:hover {
            transform: translateY(-5px);
            box-shadow: var(--shadow-glow);
            color: white;
            text-decoration: none;
        }

        .resume-btn {
            background: var(--gradient-primary);
            border: none;
            border-radius: 25px;
            padding: 1rem 2rem;
            color: white;
            font-weight: 600;
            font-size: 1.1rem;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
            text-decoration: none;
            display: inline-block;
        }

        .resume-btn:hover {
            transform: translateY(-3px);
            box-shadow: var(--shadow-glow);
            color: white;
            text-decoration: none;
        }

        .resume-btn::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
            transition: all 0.5s ease;
        }

        .resume-btn:hover::before {
            left: 100%;
        }
    </style>
</head>
<body>
    ''' + NAVBAR_HTML + '''

    <!-- 主要内容区域 -->
    <div class="main-content">
        <div class="container">
            <h1 class="page-title fade-in-up">👨‍💻 关于我</h1>
            <p class="text-center text-light opacity-75 mb-5 fade-in-up" style="font-size: 1.2rem;">
                2025届数据科学专业毕业生，正在寻找数据分析师工作机会<br>
                用数据驱动决策，用技术创造价值
            </p>

            <div class="row">
                <div class="col-lg-4">
                    <div class="about-card text-center fade-in-up">
                        <div class="avatar">
                            {% if author and author.avatar and author.avatar != 'default.jpg' %}
                            <img src="{{ author.avatar }}" alt="{{ author.username }}" class="w-100 h-100 rounded-circle">
                            {% else %}
                            <i class="fas fa-user-graduate"></i>
                            {% endif %}
                        </div>
                        <h3 class="text-white mb-2">{{ config.AUTHOR_NAME }}</h3>
                        <p class="text-light opacity-75 mb-3">数据分析师 · 2025届毕业生</p>
                        <p class="text-light opacity-75 mb-4">{{ author.bio if author else '用数据讲故事，用分析驱动决策' }}</p>

                        <div class="d-flex justify-content-center gap-2 mb-4">
                            <a href="https://github.com/wswldcs" class="social-link" target="_blank">
                                <i class="fab fa-github"></i>
                            </a>
                            <a href="mailto:your-email@example.com" class="social-link" target="_blank">
                                <i class="fas fa-envelope"></i>
                            </a>
                            <a href="https://linkedin.com/in/yourprofile" class="social-link" target="_blank">
                                <i class="fab fa-linkedin"></i>
                            </a>
                            <a href="https://wswldcs.edu.deal" class="social-link" target="_blank">
                                <i class="fas fa-globe"></i>
                            </a>
                        </div>

                        <a href="#" class="resume-btn">
                            <i class="fas fa-download me-2"></i>下载简历
                        </a>
                    </div>
                </div>

                <div class="col-lg-8">
                    <div class="about-card fade-in-up">
                        <h2 class="mb-4 text-white">🎓 我的故事</h2>
                        <div class="text-light opacity-75">
                            <p class="mb-3">
                                你好！我是{{ config.AUTHOR_NAME }}，一名即将于2025年6月毕业的数据科学专业学生。
                                从2021年9月踏入大学校园开始，我就对数据的魅力深深着迷。
                            </p>
                            <p class="mb-3">
                                在过去的四年里，我系统学习了统计学、机器学习、数据挖掘等核心课程，
                                熟练掌握了Python、SQL、Tableau等数据分析工具，
                                完成了多个实际的数据分析项目。
                            </p>
                            <p class="mb-3">
                                我相信数据是现代商业的石油，而数据分析师就是炼油师。
                                我希望能够加入一家重视数据驱动决策的公司，
                                用我的技能帮助企业从数据中发现价值，优化业务流程。
                            </p>
                            <p class="mb-0">
                                这个博客记录了我的学习历程、项目经验和求职准备，
                                希望能够展示我的专业能力，也希望能够帮助到同样在数据分析道路上前行的朋友们。
                            </p>
                        </div>
                    </div>

                    <div class="about-card fade-in-up">
                        <h3 class="mb-4 text-white">💪 技能水平</h3>
                        {% for skill, level in tech_stats.items() %}
                        <div class="mb-3">
                            <div class="d-flex justify-content-between mb-2">
                                <span class="text-white">{{ skill }}</span>
                                <span class="text-light opacity-75">{{ level }}%</span>
                            </div>
                            <div class="skill-bar">
                                <div class="skill-progress" style="width: {{ level }}%;"></div>
                            </div>
                        </div>
                        {% endfor %}
                    </div>

                    <div class="about-card fade-in-up">
                        <h3 class="mb-4 text-white">📞 联系方式</h3>
                        <div class="row">
                            <div class="col-md-6">
                                <p class="text-light opacity-75 mb-2">
                                    <i class="fas fa-envelope me-2 text-primary"></i>{{ config.AUTHOR_EMAIL }}
                                </p>
                                <p class="text-light opacity-75 mb-2">
                                    <i class="fas fa-map-marker-alt me-2 text-success"></i>{{ config.AUTHOR_LOCATION }}
                                </p>
                                <p class="text-light opacity-75 mb-2">
                                    <i class="fas fa-graduation-cap me-2 text-warning"></i>2025年6月毕业
                                </p>
                            </div>
                            <div class="col-md-6">
                                <p class="text-light opacity-75 mb-2">
                                    <i class="fab fa-github me-2 text-info"></i>github.com/wswldcs
                                </p>
                                <p class="text-light opacity-75 mb-2">
                                    <i class="fas fa-globe me-2 text-danger"></i>wswldcs.edu.deal
                                </p>
                                <p class="text-light opacity-75 mb-2">
                                    <i class="fas fa-briefcase me-2 text-purple"></i>正在求职中
                                </p>
                            </div>
                        </div>

                        <div class="text-center mt-4">
                            <p class="text-light opacity-75 mb-3">
                                <strong>如果您有合适的数据分析师职位，欢迎与我联系！</strong>
                            </p>
                            <div class="d-flex justify-content-center gap-3">
                                <a href="mailto:your-email@example.com" class="btn btn-cool">
                                    <i class="fas fa-envelope me-2"></i>发送邮件
                                </a>
                                <a href="#" class="btn btn-cool">
                                    <i class="fab fa-linkedin me-2"></i>LinkedIn
                                </a>
                                <a href="#" class="btn btn-cool">
                                    <i class="fas fa-phone me-2"></i>电话联系
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    ''' + BASE_JAVASCRIPT + '''
    <script>
        // 技能条动画
        document.addEventListener('DOMContentLoaded', function() {
            const skillBars = document.querySelectorAll('.skill-progress');

            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const width = entry.target.style.width;
                        entry.target.style.width = '0%';
                        setTimeout(() => {
                            entry.target.style.width = width;
                        }, 500);
                    }
                });
            }, {
                threshold: 0.5
            });

            skillBars.forEach(bar => {
                observer.observe(bar);
            });
        });
    </script>
</body>
</html>
'''

# 文章详情页面模板
POST_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{{ post.title }} - {{ config.BLOG_TITLE }}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.8.0/styles/github.min.css" rel="stylesheet">
    <style>
        body { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); }
        .navbar { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important; }
        .post-content {
            background: white; border-radius: 15px; padding: 3rem;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1); line-height: 1.8;
        }
        .post-content h1, .post-content h2, .post-content h3 {
            color: #2c3e50; margin-top: 2rem; margin-bottom: 1rem;
        }
        .post-content pre {
            background: #f8f9fa; border-radius: 10px; padding: 1rem;
            border-left: 4px solid #667eea;
        }
        .post-meta {
            background: white; border-radius: 15px; padding: 2rem;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1); margin-bottom: 2rem;
        }
        .related-post {
            background: white; border-radius: 10px; padding: 1.5rem;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1); margin-bottom: 1rem;
            text-decoration: none; color: inherit; display: block;
        }
        .related-post:hover {
            transform: translateY(-3px); text-decoration: none; color: inherit;
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark">
        <div class="container">
            <a class="navbar-brand" href="{{ url_for('index') }}">
                <i class="fas fa-blog me-2"></i>{{ config.BLOG_TITLE }}
            </a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="{{ url_for('index') }}">首页</a>
                <a class="nav-link" href="{{ url_for('blog') }}">博客</a>
                <a class="nav-link" href="{{ url_for('projects') }}">项目</a>
                <a class="nav-link" href="{{ url_for('about') }}">关于</a>
            </div>
        </div>
    </nav>

    <div class="container py-5">
        <div class="row">
            <div class="col-lg-8">
                <div class="post-meta">
                    <h1>{{ post.title }}</h1>
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <span class="text-muted">
                                <i class="fas fa-calendar me-1"></i>{{ post.created_at.strftime('%Y年%m月%d日') }}
                                <i class="fas fa-eye ms-3 me-1"></i>{{ post.view_count }} 次浏览
                                {% if post.category %}
                                <span class="badge ms-3" style="background-color: {{ post.category.color }};">
                                    <i class="{{ post.category.icon }} me-1"></i>{{ post.category.name }}
                                </span>
                                {% endif %}
                            </span>
                        </div>
                    </div>
                    {% if post.tags %}
                    <div class="mt-3">
                        {% for tag in post.tags %}
                        <span class="badge me-1" style="background-color: {{ tag.color }};">
                            {{ tag.name }}
                        </span>
                        {% endfor %}
                    </div>
                    {% endif %}
                </div>

                <div class="post-content">
                    {{ post.get_html_content() | safe }}
                </div>

                <!-- 评论区 -->
                <div class="mt-5">
                    <h3>评论 ({{ comments|length }})</h3>
                    {% for comment in comments %}
                    <div class="card mb-3">
                        <div class="card-body">
                            <div class="d-flex justify-content-between">
                                <strong>{{ comment.author_name }}</strong>
                                <small class="text-muted">{{ comment.created_at.strftime('%Y-%m-%d %H:%M') }}</small>
                            </div>
                            <p class="mt-2">{{ comment.content }}</p>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>

            <div class="col-lg-4">
                <!-- 相关文章 -->
                {% if related_posts %}
                <div class="mb-4">
                    <h5 class="mb-3">相关文章</h5>
                    {% for related in related_posts %}
                    <a href="{{ url_for('post', slug=related.slug) }}" class="related-post">
                        <h6>{{ related.title }}</h6>
                        <small class="text-muted">{{ related.created_at.strftime('%m-%d') }}</small>
                    </a>
                    {% endfor %}
                </div>
                {% endif %}
            </div>
        </div>
    </div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.8.0/highlight.min.js"></script>
    <script>hljs.highlightAll();</script>
</body>
</html>
'''

LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>管理登录 - {{ config.BLOG_TITLE }}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    ''' + BASE_STYLES + '''
    <style>
        body {
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: 'Inter', sans-serif;
        }

        .login-card {
            background: rgba(30, 41, 59, 0.95);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(102, 126, 234, 0.3);
            border-radius: 25px;
            box-shadow: 0 30px 60px rgba(0, 0, 0, 0.4);
            padding: 3rem;
            width: 100%;
            max-width: 450px;
            position: relative;
            overflow: hidden;
        }

        .login-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: var(--gradient-primary);
        }

        .login-icon {
            width: 80px;
            height: 80px;
            border-radius: 50%;
            background: var(--gradient-primary);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 2rem;
            margin: 0 auto 2rem;
            box-shadow: var(--shadow-glow);
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.05); }
        }

        .form-control {
            background: rgba(15, 23, 42, 0.8) !important;
            border: 1px solid rgba(102, 126, 234, 0.3) !important;
            border-radius: 15px !important;
            color: white !important;
            padding: 0.8rem 1.2rem !important;
            transition: all 0.3s ease !important;
        }

        .form-control:focus {
            background: rgba(15, 23, 42, 0.9) !important;
            border-color: rgba(102, 126, 234, 0.6) !important;
            box-shadow: 0 0 20px rgba(102, 126, 234, 0.3) !important;
            color: white !important;
        }

        .form-control::placeholder {
            color: rgba(255, 255, 255, 0.5) !important;
        }

        .form-label {
            color: #e0e7ff;
            font-weight: 500;
            margin-bottom: 0.5rem;
        }

        .login-btn {
            background: var(--gradient-primary);
            border: none;
            border-radius: 15px;
            padding: 0.8rem 2rem;
            color: white;
            font-weight: 600;
            font-size: 1.1rem;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
            width: 100%;
        }

        .login-btn:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-glow);
            color: white;
        }

        .login-btn::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
            transition: all 0.5s ease;
        }

        .login-btn:hover::before {
            left: 100%;
        }

        .alert-danger {
            background: rgba(239, 68, 68, 0.2) !important;
            border: 1px solid rgba(239, 68, 68, 0.3) !important;
            color: #fca5a5 !important;
            border-radius: 15px !important;
        }

        .back-link {
            color: rgba(255, 255, 255, 0.7);
            text-decoration: none;
            transition: all 0.3s ease;
            font-size: 0.9rem;
        }

        .back-link:hover {
            color: #667eea;
            text-decoration: none;
        }
    </style>
</head>
<body>
    ''' + BASE_JAVASCRIPT + '''

    <div class="login-card fade-in-up">
        <div class="login-icon">
            <i class="fas fa-shield-alt"></i>
        </div>

        <h2 class="text-center mb-1 text-white">管理员登录</h2>
        <p class="text-center text-light opacity-75 mb-4">访问博客管理后台</p>

        {% with messages = get_flashed_messages() %}
            {% if messages %}
                {% for message in messages %}
                    <div class="alert alert-danger mb-4">
                        <i class="fas fa-exclamation-triangle me-2"></i>{{ message }}
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        <form method="POST">
            <div class="mb-3">
                <label for="username" class="form-label">
                    <i class="fas fa-user me-2"></i>用户名
                </label>
                <input type="text" class="form-control" id="username" name="username"
                       placeholder="请输入管理员用户名" required>
            </div>
            <div class="mb-4">
                <label for="password" class="form-label">
                    <i class="fas fa-lock me-2"></i>密码
                </label>
                <input type="password" class="form-control" id="password" name="password"
                       placeholder="请输入管理员密码" required>
            </div>
            <button type="submit" class="login-btn">
                <i class="fas fa-sign-in-alt me-2"></i>登录管理后台
            </button>
        </form>

        <div class="text-center mt-4">
            <a href="{{ url_for('index') }}" class="back-link">
                <i class="fas fa-arrow-left me-1"></i>返回首页
            </a>
        </div>
    </div>
</body>
</html>
'''

ADMIN_DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>管理后台 - {{ config.BLOG_TITLE }}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    ''' + BASE_STYLES + '''
    <style>
        .admin-sidebar {
            background: rgba(30, 41, 59, 0.95);
            backdrop-filter: blur(20px);
            border-right: 1px solid rgba(102, 126, 234, 0.3);
            min-height: 100vh;
            position: fixed;
            top: 0;
            left: 0;
            width: 280px;
            z-index: 1000;
            padding: 2rem 0;
        }

        .admin-content {
            margin-left: 280px;
            padding: 2rem;
            min-height: 100vh;
        }

        .sidebar-brand {
            padding: 0 2rem 2rem;
            border-bottom: 1px solid rgba(102, 126, 234, 0.3);
            margin-bottom: 2rem;
        }

        .sidebar-nav {
            list-style: none;
            padding: 0;
            margin: 0;
        }

        .sidebar-nav-item {
            margin-bottom: 0.5rem;
        }

        .sidebar-nav-link {
            display: flex;
            align-items: center;
            padding: 1rem 2rem;
            color: rgba(255, 255, 255, 0.8);
            text-decoration: none;
            transition: all 0.3s ease;
            border-left: 3px solid transparent;
        }

        .sidebar-nav-link:hover,
        .sidebar-nav-link.active {
            color: white;
            background: rgba(102, 126, 234, 0.2);
            border-left-color: #667eea;
            text-decoration: none;
        }

        .sidebar-nav-link i {
            width: 20px;
            margin-right: 1rem;
        }

        .admin-card {
            background: rgba(30, 41, 59, 0.9);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(102, 126, 234, 0.3);
            border-radius: 20px;
            padding: 2rem;
            margin-bottom: 2rem;
            position: relative;
            overflow: hidden;
        }

        .admin-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: var(--gradient-primary);
        }

        .stat-card {
            background: var(--gradient-primary);
            border-radius: 20px;
            padding: 2rem;
            color: white;
            text-align: center;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }

        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: var(--shadow-glow);
        }

        .stat-card::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: linear-gradient(45deg, transparent, rgba(255,255,255,0.1), transparent);
            animation: rotate 3s linear infinite;
        }

        .stat-number {
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }

        .quick-action-btn {
            background: var(--gradient-primary);
            border: none;
            border-radius: 15px;
            padding: 1rem 1.5rem;
            color: white;
            font-weight: 600;
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-block;
            margin: 0.5rem;
        }

        .quick-action-btn:hover {
            transform: translateY(-3px);
            box-shadow: var(--shadow-glow);
            color: white;
            text-decoration: none;
        }

        .table-dark {
            background: rgba(30, 41, 59, 0.9) !important;
            border-color: rgba(102, 126, 234, 0.3) !important;
        }

        .table-dark th,
        .table-dark td {
            border-color: rgba(102, 126, 234, 0.3) !important;
            color: white !important;
        }

        @media (max-width: 768px) {
            .admin-sidebar {
                transform: translateX(-100%);
                transition: transform 0.3s ease;
            }

            .admin-sidebar.show {
                transform: translateX(0);
            }

            .admin-content {
                margin-left: 0;
            }
        }
    </style>
</head>
<body>
    ''' + BASE_JAVASCRIPT + '''

    <!-- 侧边栏 -->
    <div class="admin-sidebar">
        <div class="sidebar-brand">
            <h4 class="text-white mb-0">
                <i class="fas fa-shield-alt me-2"></i>管理后台
            </h4>
            <small class="text-light opacity-75">{{ config.BLOG_TITLE }}</small>
        </div>

        <ul class="sidebar-nav">
            <li class="sidebar-nav-item">
                <a href="#dashboard" class="sidebar-nav-link active" onclick="showSection('dashboard')">
                    <i class="fas fa-tachometer-alt"></i>仪表盘
                </a>
            </li>
            <li class="sidebar-nav-item">
                <a href="#posts" class="sidebar-nav-link" onclick="showSection('posts')">
                    <i class="fas fa-edit"></i>文章管理
                </a>
            </li>
            <li class="sidebar-nav-item">
                <a href="#categories" class="sidebar-nav-link" onclick="showSection('categories')">
                    <i class="fas fa-folder"></i>分类管理
                </a>
            </li>
            <li class="sidebar-nav-item">
                <a href="#projects" class="sidebar-nav-link" onclick="showSection('projects')">
                    <i class="fas fa-project-diagram"></i>项目管理
                </a>
            </li>
            <li class="sidebar-nav-item">
                <a href="#timeline" class="sidebar-nav-link" onclick="showSection('timeline')">
                    <i class="fas fa-clock"></i>时间线管理
                </a>
            </li>
            <li class="sidebar-nav-item">
                <a href="#links" class="sidebar-nav-link" onclick="showSection('links')">
                    <i class="fas fa-link"></i>友链管理
                </a>
            </li>
            <li class="sidebar-nav-item">
                <a href="#profile" class="sidebar-nav-link" onclick="showSection('profile')">
                    <i class="fas fa-user"></i>个人信息
                </a>
            </li>
            <li class="sidebar-nav-item">
                <a href="#settings" class="sidebar-nav-link" onclick="showSection('settings')">
                    <i class="fas fa-cog"></i>系统设置
                </a>
            </li>
            <li class="sidebar-nav-item mt-4">
                <a href="{{ url_for('index') }}" class="sidebar-nav-link">
                    <i class="fas fa-home"></i>返回首页
                </a>
            </li>
            <li class="sidebar-nav-item">
                <a href="{{ url_for('logout') }}" class="sidebar-nav-link">
                    <i class="fas fa-sign-out-alt"></i>退出登录
                </a>
            </li>
        </ul>
    </div>

    <!-- 主要内容区域 -->
    <div class="admin-content">
        <!-- 仪表盘 -->
        <div id="dashboard" class="admin-section">
            <h1 class="text-white mb-4">
                <i class="fas fa-tachometer-alt me-2"></i>管理仪表盘
            </h1>

            <!-- 统计卡片 -->
            <div class="row mb-4">
                <div class="col-md-3 mb-4">
                    <div class="stat-card">
                        <div class="stat-number">{{ dashboard_stats.total_posts }}</div>
                        <div><i class="fas fa-edit me-2"></i>总文章数</div>
                    </div>
                </div>
                <div class="col-md-3 mb-4">
                    <div class="stat-card">
                        <div class="stat-number">{{ dashboard_stats.published_posts }}</div>
                        <div><i class="fas fa-check me-2"></i>已发布</div>
                    </div>
                </div>
                <div class="col-md-3 mb-4">
                    <div class="stat-card">
                        <div class="stat-number">{{ dashboard_stats.total_visitors }}</div>
                        <div><i class="fas fa-users me-2"></i>总访客</div>
                    </div>
                </div>
                <div class="col-md-3 mb-4">
                    <div class="stat-card">
                        <div class="stat-number">{{ dashboard_stats.total_comments }}</div>
                        <div><i class="fas fa-comments me-2"></i>总评论</div>
                    </div>
                </div>
            </div>

            <!-- 快速操作 -->
            <div class="admin-card">
                <h3 class="text-white mb-3">
                    <i class="fas fa-bolt me-2"></i>快速操作
                </h3>
                <a href="#posts" class="quick-action-btn" onclick="showSection('posts')">
                    <i class="fas fa-plus me-2"></i>写新文章
                </a>
                <a href="#projects" class="quick-action-btn" onclick="showSection('projects')">
                    <i class="fas fa-project-diagram me-2"></i>添加项目
                </a>
                <a href="#timeline" class="quick-action-btn" onclick="showSection('timeline')">
                    <i class="fas fa-clock me-2"></i>更新时间线
                </a>
                <a href="#profile" class="quick-action-btn" onclick="showSection('profile')">
                    <i class="fas fa-user me-2"></i>编辑个人信息
                </a>
            </div>

            <!-- 最新内容 -->
            <div class="row">
                <div class="col-md-6">
                    <div class="admin-card">
                        <h5 class="text-white mb-3">
                            <i class="fas fa-newspaper me-2"></i>最新文章
                        </h5>
                        <div class="table-responsive">
                            <table class="table table-dark table-hover">
                                <tbody>
                                    {% for post in recent_posts %}
                                    <tr>
                                        <td>{{ post.title }}</td>
                                        <td class="text-end">
                                            <small class="text-light opacity-75">{{ post.created_at.strftime('%m-%d') }}</small>
                                        </td>
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="admin-card">
                        <h5 class="text-white mb-3">
                            <i class="fas fa-comment me-2"></i>最新评论
                        </h5>
                        <div class="table-responsive">
                            <table class="table table-dark table-hover">
                                <tbody>
                                    {% for comment in recent_comments %}
                                    <tr>
                                        <td>
                                            <strong>{{ comment.author_name }}</strong><br>
                                            <small class="text-light opacity-75">{{ comment.content[:30] }}...</small>
                                        </td>
                                        <td class="text-end">
                                            <small class="text-light opacity-75">{{ comment.created_at.strftime('%m-%d %H:%M') }}</small>
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

        <!-- 文章管理 -->
        <div id="posts" class="admin-section" style="display: none;">
            <h1 class="text-white mb-4">
                <i class="fas fa-edit me-2"></i>文章管理
            </h1>

            <div class="admin-card">
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <h5 class="text-white mb-0">所有文章</h5>
                    <button class="quick-action-btn" onclick="showAddPostForm()">
                        <i class="fas fa-plus me-2"></i>写新文章
                    </button>
                </div>

                <div class="table-responsive">
                    <table class="table table-dark table-hover">
                        <thead>
                            <tr>
                                <th>标题</th>
                                <th>分类</th>
                                <th>状态</th>
                                <th>创建时间</th>
                                <th>操作</th>
                            </tr>
                        </thead>
                        <tbody>
                            <!-- 这里会通过JavaScript动态加载文章列表 -->
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- 个人信息管理 -->
        <div id="profile" class="admin-section" style="display: none;">
            <h1 class="text-white mb-4">
                <i class="fas fa-user me-2"></i>个人信息管理
            </h1>

            <div class="admin-card">
                <h5 class="text-white mb-3">基本信息</h5>
                <form id="profileForm">
                    <div class="row">
                        <div class="col-md-6 mb-3">
                            <label class="form-label text-light">姓名</label>
                            <input type="text" class="form-control" name="name" value="{{ config.AUTHOR_NAME }}">
                        </div>
                        <div class="col-md-6 mb-3">
                            <label class="form-label text-light">邮箱</label>
                            <input type="email" class="form-control" name="email" value="{{ config.AUTHOR_EMAIL }}">
                        </div>
                        <div class="col-md-6 mb-3">
                            <label class="form-label text-light">位置</label>
                            <input type="text" class="form-control" name="location" value="{{ config.AUTHOR_LOCATION }}">
                        </div>
                        <div class="col-md-6 mb-3">
                            <label class="form-label text-light">GitHub用户名</label>
                            <input type="text" class="form-control" name="github" value="wswldcs">
                        </div>
                        <div class="col-12 mb-3">
                            <label class="form-label text-light">个人简介</label>
                            <textarea class="form-control" name="bio" rows="3">用数据讲故事，用分析驱动决策</textarea>
                        </div>
                    </div>
                    <button type="submit" class="quick-action-btn">
                        <i class="fas fa-save me-2"></i>保存更改
                    </button>
                </form>
            </div>
        </div>

        <!-- 时间线管理 -->
        <div id="timeline" class="admin-section" style="display: none;">
            <h1 class="text-white mb-4">
                <i class="fas fa-clock me-2"></i>时间线管理
            </h1>

            <div class="admin-card">
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <h5 class="text-white mb-0">学习历程时间线</h5>
                    <button class="quick-action-btn" onclick="showAddTimelineForm()">
                        <i class="fas fa-plus me-2"></i>添加时间线事件
                    </button>
                </div>

                <div class="table-responsive">
                    <table class="table table-dark table-hover">
                        <thead>
                            <tr>
                                <th>标题</th>
                                <th>日期</th>
                                <th>分类</th>
                                <th>描述</th>
                                <th>操作</th>
                            </tr>
                        </thead>
                        <tbody id="timelineTableBody">
                            <!-- 时间线数据将通过JavaScript加载 -->
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- 友链管理 -->
        <div id="links" class="admin-section" style="display: none;">
            <h1 class="text-white mb-4">
                <i class="fas fa-link me-2"></i>友链管理
            </h1>

            <div class="admin-card">
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <h5 class="text-white mb-0">友情链接</h5>
                    <button class="quick-action-btn" onclick="showAddLinkForm()">
                        <i class="fas fa-plus me-2"></i>添加友链
                    </button>
                </div>

                <div class="table-responsive">
                    <table class="table table-dark table-hover">
                        <thead>
                            <tr>
                                <th>网站名称</th>
                                <th>网站链接</th>
                                <th>分类</th>
                                <th>状态</th>
                                <th>操作</th>
                            </tr>
                        </thead>
                        <tbody id="linksTableBody">
                            <!-- 友链数据将通过JavaScript加载 -->
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- 项目管理 -->
        <div id="projects" class="admin-section" style="display: none;">
            <h1 class="text-white mb-4">
                <i class="fas fa-code me-2"></i>项目管理
            </h1>

            <div class="admin-card">
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <h5 class="text-white mb-0">项目作品集</h5>
                    <button class="quick-action-btn" onclick="showAddProjectForm()">
                        <i class="fas fa-plus me-2"></i>添加项目
                    </button>
                </div>

                <div class="table-responsive">
                    <table class="table table-dark table-hover">
                        <thead>
                            <tr>
                                <th>项目名称</th>
                                <th>技术栈</th>
                                <th>状态</th>
                                <th>精选</th>
                                <th>操作</th>
                            </tr>
                        </thead>
                        <tbody id="projectsTableBody">
                            <!-- 项目数据将通过JavaScript加载 -->
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- 分类管理 -->
        <div id="categories" class="admin-section" style="display: none;">
            <h1 class="text-white mb-4">
                <i class="fas fa-folder me-2"></i>分类管理
            </h1>

            <div class="admin-card">
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <h5 class="text-white mb-0">文章分类</h5>
                    <button class="quick-action-btn" onclick="showAddCategoryForm()">
                        <i class="fas fa-plus me-2"></i>添加分类
                    </button>
                </div>

                <div class="table-responsive">
                    <table class="table table-dark table-hover">
                        <thead>
                            <tr>
                                <th>分类名称</th>
                                <th>描述</th>
                                <th>颜色</th>
                                <th>图标</th>
                                <th>文章数</th>
                                <th>操作</th>
                            </tr>
                        </thead>
                        <tbody id="categoriesTableBody">
                            <!-- 分类数据将通过JavaScript加载 -->
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- 系统设置 -->
        <div id="settings" class="admin-section" style="display: none;">
            <h1 class="text-white mb-4">
                <i class="fas fa-cog me-2"></i>系统设置
            </h1>

            <div class="row">
                <div class="col-md-6">
                    <div class="admin-card">
                        <h5 class="text-white mb-3">
                            <i class="fas fa-globe me-2"></i>网站配置
                        </h5>
                        <form id="siteConfigForm">
                            <div class="mb-3">
                                <label class="form-label text-light">网站标题</label>
                                <input type="text" class="form-control" name="blog_title" id="blogTitle"
                                       style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(102, 126, 234, 0.3); color: white;">
                            </div>
                            <div class="mb-3">
                                <label class="form-label text-light">网站副标题</label>
                                <input type="text" class="form-control" name="blog_subtitle" id="blogSubtitle"
                                       style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(102, 126, 234, 0.3); color: white;">
                            </div>
                            <div class="mb-3">
                                <label class="form-label text-light">网站描述</label>
                                <textarea class="form-control" name="blog_description" id="blogDescription" rows="3"
                                          style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(102, 126, 234, 0.3); color: white;"></textarea>
                            </div>
                            <button type="button" class="btn btn-cool" onclick="saveSiteConfig()">
                                <i class="fas fa-save me-2"></i>保存网站配置
                            </button>
                        </form>
                    </div>
                </div>

                <div class="col-md-6">
                    <div class="admin-card">
                        <h5 class="text-white mb-3">
                            <i class="fas fa-key me-2"></i>API配置
                        </h5>
                        <form id="apiConfigForm">
                            <div class="mb-3">
                                <label class="form-label text-light">天气API密钥</label>
                                <input type="text" class="form-control" name="weather_api_key" id="weatherApiKey"
                                       style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(102, 126, 234, 0.3); color: white;"
                                       placeholder="OpenWeatherMap API Key">
                            </div>
                            <div class="mb-3">
                                <label class="form-label text-light">IP地理位置API密钥</label>
                                <input type="text" class="form-control" name="ipapi_key" id="ipapiKey"
                                       style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(102, 126, 234, 0.3); color: white;"
                                       placeholder="IP-API Key (可选)">
                            </div>
                            <button type="button" class="btn btn-cool" onclick="saveApiConfig()">
                                <i class="fas fa-save me-2"></i>保存API配置
                            </button>
                        </form>
                    </div>

                    <div class="admin-card mt-4">
                        <h5 class="text-white mb-3">
                            <i class="fas fa-database me-2"></i>数据管理
                        </h5>
                        <div class="d-grid gap-2">
                            <button class="btn btn-warning" onclick="exportData()">
                                <i class="fas fa-download me-2"></i>导出数据
                            </button>
                            <button class="btn btn-info" onclick="showImportData()">
                                <i class="fas fa-upload me-2"></i>导入数据
                            </button>
                            <button class="btn btn-danger" onclick="clearCache()">
                                <i class="fas fa-trash me-2"></i>清理缓存
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // 管理后台JavaScript功能
        function showSection(sectionId) {
            // 隐藏所有section
            document.querySelectorAll('.admin-section').forEach(section => {
                section.style.display = 'none';
            });

            // 移除所有active类
            document.querySelectorAll('.sidebar-nav-link').forEach(link => {
                link.classList.remove('active');
            });

            // 显示选中的section
            document.getElementById(sectionId).style.display = 'block';

            // 添加active类到当前链接
            event.target.classList.add('active');

            // 根据section加载相应数据
            if (sectionId === 'posts') {
                loadPosts();
            } else if (sectionId === 'categories') {
                loadCategories();
            } else if (sectionId === 'profile') {
                loadProfile();
            } else if (sectionId === 'projects') {
                loadProjects();
            } else if (sectionId === 'timeline') {
                loadTimeline();
            } else if (sectionId === 'links') {
                loadLinks();
            }
        }

        // 加载文章列表
        async function loadPosts() {
            try {
                const response = await fetch('/api/admin/posts', {
                    credentials: 'same-origin'
                });
                const data = await response.json();

                if (data.posts) {
                    const tbody = document.querySelector('#posts .table tbody');
                    tbody.innerHTML = '';

                    data.posts.forEach(post => {
                        const row = document.createElement('tr');
                        row.innerHTML = `
                            <td>${post.title}</td>
                            <td>${post.category}</td>
                            <td><span class="badge ${post.status === '已发布' ? 'bg-success' : 'bg-warning'}">${post.status}</span></td>
                            <td>${post.created_at}</td>
                            <td>
                                <button class="btn btn-cool btn-sm me-1" onclick="editPost(${post.id})">
                                    <i class="fas fa-edit"></i>
                                </button>
                                <button class="btn btn-danger btn-sm" onclick="deletePost(${post.id})">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </td>
                        `;
                        tbody.appendChild(row);
                    });
                }
            } catch (error) {
                console.error('加载文章失败:', error);
                alert('加载文章失败');
            }
        }

        // 加载分类列表
        async function loadCategories() {
            try {
                const response = await fetch('/api/admin/categories', {
                    credentials: 'same-origin'
                });
                const data = await response.json();

                if (data.categories) {
                    const tbody = document.getElementById('categoriesTableBody');
                    tbody.innerHTML = '';

                    data.categories.forEach(category => {
                        const row = document.createElement('tr');
                        row.innerHTML = `
                            <td>
                                <span style="color: ${category.color};">
                                    <i class="${category.icon} me-2"></i>${category.name}
                                </span>
                            </td>
                            <td class="text-muted">${category.description || '无描述'}</td>
                            <td>
                                <span class="badge" style="background-color: ${category.color}; color: white;">
                                    ${category.color}
                                </span>
                            </td>
                            <td>
                                <i class="${category.icon}" style="color: ${category.color};"></i>
                            </td>
                            <td>
                                <span class="badge bg-info">${category.post_count} 篇</span>
                            </td>
                            <td>
                                <button class="btn btn-cool btn-sm me-1" onclick="editCategory(${category.id})" title="编辑分类">
                                    <i class="fas fa-edit"></i>
                                </button>
                                <button class="btn btn-danger btn-sm" onclick="deleteCategory(${category.id})" title="删除分类">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </td>
                        `;
                        tbody.appendChild(row);
                    });
                }
            } catch (error) {
                console.error('加载分类失败:', error);
            }
        }

        // 显示添加文章表单
        async function showAddPostForm() {
            // 先加载分类数据
            let categoriesOptions = '<option value="">选择分类</option>';
            try {
                const response = await fetch('/api/admin/categories', {
                    method: 'GET',
                    credentials: 'same-origin',  // 确保发送cookies
                    headers: {
                        'Content-Type': 'application/json',
                    }
                });

                console.log('分类API响应状态:', response.status); // 调试用

                if (response.ok) {
                    const data = await response.json();
                    console.log('分类数据:', data); // 调试用

                    if (data.categories && data.categories.length > 0) {
                        data.categories.forEach(category => {
                            categoriesOptions += `<option value="${category.id}">${category.name}</option>`;
                        });
                    } else {
                        console.log('没有找到分类数据');
                    }
                } else {
                    const errorData = await response.json();
                    console.error('分类API错误:', errorData);
                }
            } catch (error) {
                console.error('加载分类失败:', error);
            }

            const formHtml = `
                <div class="modal fade" id="postModal" tabindex="-1">
                    <div class="modal-dialog modal-lg">
                        <div class="modal-content" style="background: rgba(30, 41, 59, 0.95); border: 1px solid rgba(102, 126, 234, 0.3);">
                            <div class="modal-header" style="border-bottom: 1px solid rgba(102, 126, 234, 0.3);">
                                <h5 class="modal-title text-white">添加新文章</h5>
                                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                            </div>
                            <div class="modal-body">
                                <form id="postForm">
                                    <div class="mb-3">
                                        <label class="form-label text-light">标题 *</label>
                                        <input type="text" class="form-control" name="title" required
                                               style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(102, 126, 234, 0.3); color: white;">
                                    </div>
                                    <div class="mb-3">
                                        <label class="form-label text-light">摘要</label>
                                        <textarea class="form-control" name="summary" rows="2"
                                                  style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(102, 126, 234, 0.3); color: white;"
                                                  placeholder="文章摘要（可选）"></textarea>
                                    </div>
                                    <div class="mb-3">
                                        <label class="form-label text-light">内容 *</label>
                                        <textarea class="form-control" name="content" rows="10" required
                                                  style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(102, 126, 234, 0.3); color: white;"
                                                  placeholder="请输入文章内容..."></textarea>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-6">
                                            <label class="form-label text-light">分类</label>
                                            <select class="form-select" name="category_id"
                                                    style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(102, 126, 234, 0.3); color: white;">
                                                ${categoriesOptions}
                                            </select>
                                        </div>
                                        <div class="col-md-6">
                                            <div class="form-check mt-4">
                                                <input class="form-check-input" type="checkbox" name="is_published" id="isPublished">
                                                <label class="form-check-label text-light" for="isPublished">
                                                    立即发布
                                                </label>
                                            </div>
                                        </div>
                                    </div>
                                </form>
                            </div>
                            <div class="modal-footer" style="border-top: 1px solid rgba(102, 126, 234, 0.3);">
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                                <button type="button" class="btn btn-cool" onclick="savePost()">保存文章</button>
                            </div>
                        </div>
                    </div>
                </div>
            `;

            // 移除已存在的模态框
            const existingModal = document.getElementById('postModal');
            if (existingModal) {
                existingModal.remove();
            }

            // 添加新模态框
            document.body.insertAdjacentHTML('beforeend', formHtml);

            // 显示模态框
            const modal = new bootstrap.Modal(document.getElementById('postModal'));
            modal.show();
        }

        // 保存文章
        async function savePost() {
            const form = document.getElementById('postForm');
            const formData = new FormData(form);

            // 验证必填字段
            const title = formData.get('title').trim();
            const content = formData.get('content').trim();

            if (!title) {
                alert('请输入文章标题');
                return;
            }

            if (!content) {
                alert('请输入文章内容');
                return;
            }

            const postData = {
                title: title,
                summary: formData.get('summary').trim(),
                content: content,
                category_id: formData.get('category_id') ? parseInt(formData.get('category_id')) : null,
                is_published: formData.has('is_published')
            };

            console.log('发送的数据:', postData); // 调试用

            try {
                const response = await fetch('/api/admin/posts', {
                    method: 'POST',
                    credentials: 'same-origin',  // 确保发送cookies
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(postData)
                });

                const result = await response.json();
                console.log('服务器响应:', result); // 调试用

                if (response.ok) {
                    alert('文章保存成功！');
                    bootstrap.Modal.getInstance(document.getElementById('postModal')).hide();
                    loadPosts(); // 重新加载文章列表
                } else {
                    alert('保存失败: ' + (result.error || '未知错误'));
                }
            } catch (error) {
                console.error('保存文章失败:', error);
                alert('保存文章失败: ' + error.message);
            }
        }

        // 删除文章
        async function deletePost(postId) {
            if (!confirm('确定要删除这篇文章吗？')) {
                return;
            }

            try {
                const response = await fetch(`/api/admin/posts/${postId}`, {
                    method: 'DELETE'
                });

                const result = await response.json();

                if (response.ok) {
                    alert('文章删除成功！');
                    loadPosts(); // 重新加载文章列表
                } else {
                    alert('删除失败: ' + result.error);
                }
            } catch (error) {
                console.error('删除文章失败:', error);
                alert('删除文章失败');
            }
        }

        // 编辑文章
        async function editPost(postId) {
            try {
                // 获取文章详情
                const response = await fetch(`/api/admin/posts/${postId}`, {
                    credentials: 'same-origin'
                });

                if (!response.ok) {
                    alert('获取文章信息失败');
                    return;
                }

                const data = await response.json();
                const post = data.post;

                // 加载分类数据
                let categoriesOptions = '<option value="">选择分类</option>';
                try {
                    const categoriesResponse = await fetch('/api/admin/categories', {
                        credentials: 'same-origin'
                    });

                    if (categoriesResponse.ok) {
                        const categoriesData = await categoriesResponse.json();
                        if (categoriesData.categories) {
                            categoriesData.categories.forEach(category => {
                                const selected = category.id === post.category_id ? 'selected' : '';
                                categoriesOptions += `<option value="${category.id}" ${selected}>${category.name}</option>`;
                            });
                        }
                    }
                } catch (error) {
                    console.error('加载分类失败:', error);
                }

                const formHtml = `
                    <div class="modal fade" id="editPostModal" tabindex="-1">
                        <div class="modal-dialog modal-lg">
                            <div class="modal-content" style="background: rgba(30, 41, 59, 0.95); border: 1px solid rgba(102, 126, 234, 0.3);">
                                <div class="modal-header" style="border-bottom: 1px solid rgba(102, 126, 234, 0.3);">
                                    <h5 class="modal-title text-white">编辑文章</h5>
                                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                                </div>
                                <div class="modal-body">
                                    <form id="editPostForm">
                                        <input type="hidden" name="post_id" value="${post.id}">
                                        <div class="mb-3">
                                            <label class="form-label text-light">标题 *</label>
                                            <input type="text" class="form-control" name="title" required value="${post.title}"
                                                   style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(102, 126, 234, 0.3); color: white;">
                                        </div>
                                        <div class="mb-3">
                                            <label class="form-label text-light">摘要</label>
                                            <textarea class="form-control" name="summary" rows="2"
                                                      style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(102, 126, 234, 0.3); color: white;"
                                                      placeholder="文章摘要（可选）">${post.summary || ''}</textarea>
                                        </div>
                                        <div class="mb-3">
                                            <label class="form-label text-light">内容 *</label>
                                            <textarea class="form-control" name="content" rows="10" required
                                                      style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(102, 126, 234, 0.3); color: white;"
                                                      placeholder="请输入文章内容...">${post.content}</textarea>
                                        </div>
                                        <div class="row">
                                            <div class="col-md-6">
                                                <label class="form-label text-light">分类</label>
                                                <select class="form-select" name="category_id"
                                                        style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(102, 126, 234, 0.3); color: white;">
                                                    ${categoriesOptions}
                                                </select>
                                            </div>
                                            <div class="col-md-6">
                                                <div class="form-check mt-4">
                                                    <input class="form-check-input" type="checkbox" name="is_published" id="editIsPublished" ${post.is_published ? 'checked' : ''}>
                                                    <label class="form-check-label text-light" for="editIsPublished">
                                                        已发布
                                                    </label>
                                                </div>
                                            </div>
                                        </div>
                                    </form>
                                </div>
                                <div class="modal-footer" style="border-top: 1px solid rgba(102, 126, 234, 0.3);">
                                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                                    <button type="button" class="btn btn-cool" onclick="updatePost()">更新文章</button>
                                </div>
                            </div>
                        </div>
                    </div>
                `;

                // 移除已存在的模态框
                const existingModal = document.getElementById('editPostModal');
                if (existingModal) {
                    existingModal.remove();
                }

                // 添加新模态框
                document.body.insertAdjacentHTML('beforeend', formHtml);

                // 显示模态框
                const modal = new bootstrap.Modal(document.getElementById('editPostModal'));
                modal.show();

            } catch (error) {
                console.error('编辑文章失败:', error);
                alert('编辑文章失败: ' + error.message);
            }
        }

        // 更新文章
        async function updatePost() {
            const form = document.getElementById('editPostForm');
            const formData = new FormData(form);

            // 验证必填字段
            const title = formData.get('title').trim();
            const content = formData.get('content').trim();
            const postId = formData.get('post_id');

            if (!title) {
                alert('请输入文章标题');
                return;
            }

            if (!content) {
                alert('请输入文章内容');
                return;
            }

            const postData = {
                title: title,
                summary: formData.get('summary').trim(),
                content: content,
                category_id: formData.get('category_id') ? parseInt(formData.get('category_id')) : null,
                is_published: formData.has('is_published')
            };

            try {
                const response = await fetch(`/api/admin/posts/${postId}`, {
                    method: 'PUT',
                    credentials: 'same-origin',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(postData)
                });

                const result = await response.json();

                if (response.ok) {
                    alert('文章更新成功！');
                    bootstrap.Modal.getInstance(document.getElementById('editPostModal')).hide();
                    loadPosts(); // 重新加载文章列表
                } else {
                    alert('更新失败: ' + (result.error || '未知错误'));
                }
            } catch (error) {
                console.error('更新文章失败:', error);
                alert('更新文章失败: ' + error.message);
            }
        }

        // 加载个人信息
        async function loadProfile() {
            try {
                const response = await fetch('/api/admin/profile', {
                    credentials: 'same-origin'
                });
                const data = await response.json();

                if (data.profile) {
                    const profile = data.profile;
                    const form = document.getElementById('profileForm');
                    if (form) {
                        form.querySelector('input[name="name"]').value = profile.name || '';
                        form.querySelector('input[name="email"]').value = profile.email || '';
                        form.querySelector('input[name="location"]').value = profile.location || '';
                        form.querySelector('input[name="github"]').value = profile.github || '';
                        form.querySelector('textarea[name="bio"]').value = profile.bio || '';
                    }
                }
            } catch (error) {
                console.error('加载个人信息失败:', error);
            }
        }

        // 保存个人信息
        async function saveProfile() {
            const form = document.getElementById('profileForm');
            const formData = new FormData(form);

            const profileData = {
                name: formData.get('name'),
                email: formData.get('email'),
                location: formData.get('location'),
                github: formData.get('github'),
                bio: formData.get('bio')
            };

            try {
                const response = await fetch('/api/admin/profile', {
                    method: 'PUT',
                    credentials: 'same-origin',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(profileData)
                });

                const result = await response.json();

                if (response.ok) {
                    alert('个人信息保存成功！');
                } else {
                    alert('保存失败: ' + result.error);
                }
            } catch (error) {
                console.error('保存个人信息失败:', error);
                alert('保存个人信息失败');
            }
        }

        // 表单提交处理
        document.addEventListener('DOMContentLoaded', function() {
            const profileForm = document.getElementById('profileForm');
            if (profileForm) {
                profileForm.addEventListener('submit', function(e) {
                    e.preventDefault();
                    saveProfile();
                });

                // 页面加载时加载个人信息
                loadProfile();
            }
        });

        // 加载项目列表
        async function loadProjects() {
            try {
                const response = await fetch('/api/admin/projects', {
                    credentials: 'same-origin'
                });
                const data = await response.json();

                if (data.projects) {
                    const tbody = document.getElementById('projectsTableBody');
                    tbody.innerHTML = '';

                    data.projects.forEach(project => {
                        const row = document.createElement('tr');
                        row.innerHTML = `
                            <td>
                                <strong>${project.name}</strong>
                                <br><small class="text-muted">${project.description}</small>
                            </td>
                            <td>
                                <span class="badge bg-info">${project.technologies || '未设置'}</span>
                            </td>
                            <td>
                                <span class="badge ${getProjectStatusClass(project.status)}">
                                    ${getProjectStatusName(project.status)}
                                </span>
                            </td>
                            <td>
                                <span class="badge ${project.is_featured ? 'bg-warning' : 'bg-secondary'}">
                                    ${project.is_featured ? '精选' : '普通'}
                                </span>
                            </td>
                            <td>
                                <button class="btn btn-cool btn-sm me-1" onclick="editProject(${project.id})" title="编辑项目">
                                    <i class="fas fa-edit"></i>
                                </button>
                                <button class="btn btn-danger btn-sm" onclick="deleteProject(${project.id})" title="删除项目">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </td>
                        `;
                        tbody.appendChild(row);
                    });
                }
            } catch (error) {
                console.error('加载项目失败:', error);
            }
        }

        // 获取项目状态样式类
        function getProjectStatusClass(status) {
            const statusMap = {
                'completed': 'bg-success',
                'in_progress': 'bg-primary',
                'planned': 'bg-secondary'
            };
            return statusMap[status] || 'bg-secondary';
        }

        // 获取项目状态中文名称
        function getProjectStatusName(status) {
            const statusMap = {
                'completed': '已完成',
                'in_progress': '进行中',
                'planned': '计划中'
            };
            return statusMap[status] || status;
        }

        // 加载时间线
        async function loadTimeline() {
            try {
                const response = await fetch('/api/admin/timeline', {
                    credentials: 'same-origin'
                });
                const data = await response.json();

                if (data.timeline) {
                    const tbody = document.getElementById('timelineTableBody');
                    tbody.innerHTML = '';

                    data.timeline.forEach(item => {
                        const row = document.createElement('tr');
                        row.innerHTML = `
                            <td>
                                <i class="${item.icon} me-2" style="color: ${item.color}"></i>
                                ${item.title}
                            </td>
                            <td>${item.date}</td>
                            <td>
                                <span class="badge" style="background-color: ${item.color}">
                                    ${getCategoryName(item.category)}
                                </span>
                            </td>
                            <td>${item.description || '暂无描述'}</td>
                            <td>
                                <button class="btn btn-cool btn-sm me-1" onclick="editTimeline(${item.id})">
                                    <i class="fas fa-edit"></i>
                                </button>
                                <button class="btn btn-danger btn-sm" onclick="deleteTimeline(${item.id})">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </td>
                        `;
                        tbody.appendChild(row);
                    });
                }
            } catch (error) {
                console.error('加载时间线失败:', error);
            }
        }

        // 获取分类中文名称
        function getCategoryName(category) {
            const categoryMap = {
                'education': '学习',
                'work': '工作',
                'project': '项目',
                'life': '生活',
                'achievement': '成就'
            };
            return categoryMap[category] || category;
        }

        // 显示添加时间线表单
        function showAddTimelineForm() {
            const formHtml = `
                <div class="modal fade" id="timelineModal" tabindex="-1">
                    <div class="modal-dialog">
                        <div class="modal-content" style="background: rgba(30, 41, 59, 0.95); border: 1px solid rgba(102, 126, 234, 0.3);">
                            <div class="modal-header" style="border-bottom: 1px solid rgba(102, 126, 234, 0.3);">
                                <h5 class="modal-title text-white">添加时间线事件</h5>
                                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                            </div>
                            <div class="modal-body">
                                <form id="timelineForm">
                                    <div class="mb-3">
                                        <label class="form-label text-light">标题 *</label>
                                        <input type="text" class="form-control" name="title" required
                                               style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(102, 126, 234, 0.3); color: white;"
                                               placeholder="例如：开始学习数据分析">
                                    </div>
                                    <div class="mb-3">
                                        <label class="form-label text-light">日期 *</label>
                                        <input type="date" class="form-control" name="date" required
                                               style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(102, 126, 234, 0.3); color: white;">
                                    </div>
                                    <div class="mb-3">
                                        <label class="form-label text-light">分类</label>
                                        <select class="form-select" name="category"
                                                style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(102, 126, 234, 0.3); color: white;">
                                            <option value="education">学习</option>
                                            <option value="work">工作</option>
                                            <option value="project">项目</option>
                                            <option value="life">生活</option>
                                            <option value="achievement">成就</option>
                                        </select>
                                    </div>
                                    <div class="mb-3">
                                        <label class="form-label text-light">描述</label>
                                        <textarea class="form-control" name="description" rows="3"
                                                  style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(102, 126, 234, 0.3); color: white;"
                                                  placeholder="详细描述这个事件..."></textarea>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-6">
                                            <label class="form-label text-light">颜色</label>
                                            <select class="form-select" name="color"
                                                    style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(102, 126, 234, 0.3); color: white;">
                                                <option value="#667eea">蓝色</option>
                                                <option value="#f093fb">粉色</option>
                                                <option value="#4facfe">天蓝</option>
                                                <option value="#43e97b">绿色</option>
                                                <option value="#fa709a">红色</option>
                                                <option value="#ffecd2">橙色</option>
                                            </select>
                                        </div>
                                        <div class="col-md-6">
                                            <label class="form-label text-light">图标</label>
                                            <select class="form-select" name="icon"
                                                    style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(102, 126, 234, 0.3); color: white;">
                                                <option value="fas fa-graduation-cap">毕业帽</option>
                                                <option value="fas fa-book">书本</option>
                                                <option value="fas fa-briefcase">公文包</option>
                                                <option value="fas fa-code">代码</option>
                                                <option value="fas fa-trophy">奖杯</option>
                                                <option value="fas fa-star">星星</option>
                                                <option value="fas fa-heart">心形</option>
                                            </select>
                                        </div>
                                    </div>
                                </form>
                            </div>
                            <div class="modal-footer" style="border-top: 1px solid rgba(102, 126, 234, 0.3);">
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                                <button type="button" class="btn btn-cool" onclick="saveTimeline()">保存事件</button>
                            </div>
                        </div>
                    </div>
                </div>
            `;

            // 移除已存在的模态框
            const existingModal = document.getElementById('timelineModal');
            if (existingModal) {
                existingModal.remove();
            }

            // 添加新模态框
            document.body.insertAdjacentHTML('beforeend', formHtml);

            // 显示模态框
            const modal = new bootstrap.Modal(document.getElementById('timelineModal'));
            modal.show();
        }

        // 保存时间线事件
        async function saveTimeline() {
            const form = document.getElementById('timelineForm');
            const formData = new FormData(form);

            // 验证必填字段
            const title = formData.get('title').trim();
            const date = formData.get('date');

            if (!title) {
                alert('请输入事件标题');
                return;
            }

            if (!date) {
                alert('请选择日期');
                return;
            }

            const timelineData = {
                title: title,
                date: date,
                category: formData.get('category'),
                description: formData.get('description').trim(),
                color: formData.get('color'),
                icon: formData.get('icon')
            };

            try {
                const response = await fetch('/api/admin/timeline', {
                    method: 'POST',
                    credentials: 'same-origin',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(timelineData)
                });

                const result = await response.json();

                if (response.ok) {
                    alert('时间线事件保存成功！');
                    bootstrap.Modal.getInstance(document.getElementById('timelineModal')).hide();
                    loadTimeline(); // 重新加载时间线列表
                } else {
                    alert('保存失败: ' + (result.error || '未知错误'));
                }
            } catch (error) {
                console.error('保存时间线事件失败:', error);
                alert('保存时间线事件失败: ' + error.message);
            }
        }

        // 删除时间线事件
        async function deleteTimeline(itemId) {
            if (!confirm('确定要删除这个时间线事件吗？')) {
                return;
            }

            try {
                const response = await fetch(`/api/admin/timeline/${itemId}`, {
                    method: 'DELETE',
                    credentials: 'same-origin'
                });

                const result = await response.json();

                if (response.ok) {
                    alert('时间线事件删除成功！');
                    loadTimeline(); // 重新加载时间线列表
                } else {
                    alert('删除失败: ' + result.error);
                }
            } catch (error) {
                console.error('删除时间线事件失败:', error);
                alert('删除时间线事件失败');
            }
        }

        // 编辑时间线事件
        function editTimeline(itemId) {
            alert(`编辑时间线事件功能开发中... (事件ID: ${itemId})`);
        }

        // 加载友链列表
        async function loadLinks() {
            try {
                const response = await fetch('/api/admin/links', {
                    credentials: 'same-origin'
                });
                const data = await response.json();

                if (data.links) {
                    const tbody = document.getElementById('linksTableBody');
                    tbody.innerHTML = '';

                    data.links.forEach(link => {
                        const row = document.createElement('tr');
                        row.innerHTML = `
                            <td>
                                <img src="${link.avatar || '/static/default-avatar.png'}"
                                     alt="${link.name}" class="rounded me-2"
                                     style="width: 24px; height: 24px;">
                                ${link.name}
                            </td>
                            <td>
                                <a href="${link.url}" target="_blank" class="text-info">
                                    ${link.url}
                                </a>
                            </td>
                            <td>
                                <span class="badge bg-info">
                                    ${getLinkCategoryName(link.category)}
                                </span>
                            </td>
                            <td>
                                <span class="badge ${link.is_active ? 'bg-success' : 'bg-secondary'}">
                                    ${link.is_active ? '启用' : '禁用'}
                                </span>
                            </td>
                            <td>
                                <button class="btn btn-cool btn-sm me-1" onclick="editLink(${link.id})">
                                    <i class="fas fa-edit"></i>
                                </button>
                                <button class="btn btn-danger btn-sm" onclick="deleteLink(${link.id})">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </td>
                        `;
                        tbody.appendChild(row);
                    });
                }
            } catch (error) {
                console.error('加载友链失败:', error);
            }
        }

        // 获取友链分类中文名称
        function getLinkCategoryName(category) {
            const categoryMap = {
                'friend': '朋友',
                'recommend': '推荐',
                'tool': '工具',
                'blog': '博客',
                'resource': '资源'
            };
            return categoryMap[category] || category;
        }

        // 显示添加友链表单
        function showAddLinkForm() {
            const formHtml = `
                <div class="modal fade" id="linkModal" tabindex="-1">
                    <div class="modal-dialog">
                        <div class="modal-content" style="background: rgba(30, 41, 59, 0.95); border: 1px solid rgba(102, 126, 234, 0.3);">
                            <div class="modal-header" style="border-bottom: 1px solid rgba(102, 126, 234, 0.3);">
                                <h5 class="modal-title text-white">添加友情链接</h5>
                                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                            </div>
                            <div class="modal-body">
                                <form id="linkForm">
                                    <div class="mb-3">
                                        <label class="form-label text-light">网站名称 *</label>
                                        <input type="text" class="form-control" name="name" required
                                               style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(102, 126, 234, 0.3); color: white;"
                                               placeholder="例如：小明的博客">
                                    </div>
                                    <div class="mb-3">
                                        <label class="form-label text-light">网站链接 *</label>
                                        <input type="url" class="form-control" name="url" required
                                               style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(102, 126, 234, 0.3); color: white;"
                                               placeholder="https://example.com">
                                    </div>
                                    <div class="mb-3">
                                        <label class="form-label text-light">网站描述</label>
                                        <textarea class="form-control" name="description" rows="2"
                                                  style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(102, 126, 234, 0.3); color: white;"
                                                  placeholder="简单描述这个网站..."></textarea>
                                    </div>
                                    <div class="mb-3">
                                        <label class="form-label text-light">头像</label>
                                        <div class="row">
                                            <div class="col-md-8">
                                                <input type="url" class="form-control" name="avatar" id="avatarUrl"
                                                       style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(102, 126, 234, 0.3); color: white;"
                                                       placeholder="头像链接或上传图片">
                                            </div>
                                            <div class="col-md-4">
                                                <input type="file" class="form-control" id="avatarFile" accept="image/*"
                                                       style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(102, 126, 234, 0.3); color: white;">
                                            </div>
                                        </div>
                                        <small class="text-muted">可以输入头像链接或上传图片文件</small>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-6">
                                            <label class="form-label text-light">分类</label>
                                            <select class="form-select" name="category"
                                                    style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(102, 126, 234, 0.3); color: white;">
                                                <option value="friend">朋友</option>
                                                <option value="recommend">推荐</option>
                                                <option value="tool">工具</option>
                                                <option value="blog">博客</option>
                                                <option value="resource">资源</option>
                                            </select>
                                        </div>
                                        <div class="col-md-6">
                                            <label class="form-label text-light">排序权重</label>
                                            <input type="number" class="form-control" name="sort_order" value="0"
                                                   style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(102, 126, 234, 0.3); color: white;"
                                                   placeholder="数字越大越靠前">
                                        </div>
                                    </div>
                                    <div class="form-check mt-3">
                                        <input class="form-check-input" type="checkbox" name="is_active" id="isActive" checked>
                                        <label class="form-check-label text-light" for="isActive">
                                            启用链接
                                        </label>
                                    </div>
                                </form>
                            </div>
                            <div class="modal-footer" style="border-top: 1px solid rgba(102, 126, 234, 0.3);">
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                                <button type="button" class="btn btn-cool" onclick="saveLink()">保存友链</button>
                            </div>
                        </div>
                    </div>
                </div>
            `;

            // 移除已存在的模态框
            const existingModal = document.getElementById('linkModal');
            if (existingModal) {
                existingModal.remove();
            }

            // 添加新模态框
            document.body.insertAdjacentHTML('beforeend', formHtml);

            // 显示模态框
            const modal = new bootstrap.Modal(document.getElementById('linkModal'));
            modal.show();
        }

        // 保存友链
        async function saveLink() {
            const form = document.getElementById('linkForm');
            const formData = new FormData(form);

            // 验证必填字段
            const name = formData.get('name').trim();
            const url = formData.get('url').trim();

            if (!name) {
                alert('请输入网站名称');
                return;
            }

            if (!url) {
                alert('请输入网站链接');
                return;
            }

            let avatarUrl = formData.get('avatar').trim();

            // 检查是否有上传的文件
            const avatarFile = document.getElementById('avatarFile').files[0];
            if (avatarFile) {
                try {
                    // 上传文件
                    const uploadFormData = new FormData();
                    uploadFormData.append('file', avatarFile);

                    const uploadResponse = await fetch('/api/admin/upload', {
                        method: 'POST',
                        credentials: 'same-origin',
                        body: uploadFormData
                    });

                    const uploadResult = await uploadResponse.json();

                    if (uploadResponse.ok) {
                        avatarUrl = uploadResult.file_url;
                    } else {
                        alert('头像上传失败: ' + uploadResult.error);
                        return;
                    }
                } catch (error) {
                    console.error('头像上传失败:', error);
                    alert('头像上传失败: ' + error.message);
                    return;
                }
            }

            const linkData = {
                name: name,
                url: url,
                description: formData.get('description').trim(),
                avatar: avatarUrl,
                category: formData.get('category'),
                sort_order: parseInt(formData.get('sort_order')) || 0,
                is_active: formData.has('is_active')
            };

            try {
                const response = await fetch('/api/admin/links', {
                    method: 'POST',
                    credentials: 'same-origin',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(linkData)
                });

                const result = await response.json();

                if (response.ok) {
                    alert('友链保存成功！');
                    bootstrap.Modal.getInstance(document.getElementById('linkModal')).hide();
                    loadLinks(); // 重新加载友链列表
                } else {
                    alert('保存失败: ' + (result.error || '未知错误'));
                }
            } catch (error) {
                console.error('保存友链失败:', error);
                alert('保存友链失败: ' + error.message);
            }
        }

        // 删除友链
        async function deleteLink(linkId) {
            if (!confirm('确定要删除这个友链吗？')) {
                return;
            }

            try {
                const response = await fetch(`/api/admin/links/${linkId}`, {
                    method: 'DELETE',
                    credentials: 'same-origin'
                });

                const result = await response.json();

                if (response.ok) {
                    alert('友链删除成功！');
                    loadLinks(); // 重新加载友链列表
                } else {
                    alert('删除失败: ' + result.error);
                }
            } catch (error) {
                console.error('删除友链失败:', error);
                alert('删除友链失败');
            }
        }

        // 编辑友链
        async function editLink(linkId) {
            try {
                // 获取友链详情
                const response = await fetch(`/api/admin/links/${linkId}`, {
                    credentials: 'same-origin'
                });

                if (!response.ok) {
                    alert('获取友链信息失败');
                    return;
                }

                const data = await response.json();
                const link = data.link;

                const formHtml = `
                    <div class="modal fade" id="editLinkModal" tabindex="-1">
                        <div class="modal-dialog">
                            <div class="modal-content" style="background: rgba(30, 41, 59, 0.95); border: 1px solid rgba(102, 126, 234, 0.3);">
                                <div class="modal-header" style="border-bottom: 1px solid rgba(102, 126, 234, 0.3);">
                                    <h5 class="modal-title text-white">编辑友情链接</h5>
                                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                                </div>
                                <div class="modal-body">
                                    <form id="editLinkForm">
                                        <input type="hidden" name="link_id" value="${link.id}">
                                        <div class="mb-3">
                                            <label class="form-label text-light">网站名称 *</label>
                                            <input type="text" class="form-control" name="name" required value="${link.name}"
                                                   style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(102, 126, 234, 0.3); color: white;">
                                        </div>
                                        <div class="mb-3">
                                            <label class="form-label text-light">网站链接 *</label>
                                            <input type="url" class="form-control" name="url" required value="${link.url}"
                                                   style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(102, 126, 234, 0.3); color: white;">
                                        </div>
                                        <div class="mb-3">
                                            <label class="form-label text-light">网站描述</label>
                                            <textarea class="form-control" name="description" rows="2"
                                                      style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(102, 126, 234, 0.3); color: white;">${link.description || ''}</textarea>
                                        </div>
                                        <div class="mb-3">
                                            <label class="form-label text-light">头像</label>
                                            <div class="row">
                                                <div class="col-md-8">
                                                    <input type="url" class="form-control" name="avatar" id="editAvatarUrl" value="${link.avatar || ''}"
                                                           style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(102, 126, 234, 0.3); color: white;">
                                                </div>
                                                <div class="col-md-4">
                                                    <input type="file" class="form-control" id="editAvatarFile" accept="image/*"
                                                           style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(102, 126, 234, 0.3); color: white;">
                                                </div>
                                            </div>
                                        </div>
                                        <div class="row">
                                            <div class="col-md-6">
                                                <label class="form-label text-light">分类</label>
                                                <select class="form-select" name="category"
                                                        style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(102, 126, 234, 0.3); color: white;">
                                                    <option value="friend" ${link.category === 'friend' ? 'selected' : ''}>朋友</option>
                                                    <option value="recommend" ${link.category === 'recommend' ? 'selected' : ''}>推荐</option>
                                                    <option value="tool" ${link.category === 'tool' ? 'selected' : ''}>工具</option>
                                                    <option value="blog" ${link.category === 'blog' ? 'selected' : ''}>博客</option>
                                                    <option value="resource" ${link.category === 'resource' ? 'selected' : ''}>资源</option>
                                                </select>
                                            </div>
                                            <div class="col-md-6">
                                                <label class="form-label text-light">排序权重</label>
                                                <input type="number" class="form-control" name="sort_order" value="${link.sort_order || 0}"
                                                       style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(102, 126, 234, 0.3); color: white;">
                                            </div>
                                        </div>
                                        <div class="form-check mt-3">
                                            <input class="form-check-input" type="checkbox" name="is_active" id="editIsActive" ${link.is_active ? 'checked' : ''}>
                                            <label class="form-check-label text-light" for="editIsActive">
                                                启用链接
                                            </label>
                                        </div>
                                    </form>
                                </div>
                                <div class="modal-footer" style="border-top: 1px solid rgba(102, 126, 234, 0.3);">
                                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                                    <button type="button" class="btn btn-cool" onclick="updateLink()">更新友链</button>
                                </div>
                            </div>
                        </div>
                    </div>
                `;

                // 移除已存在的模态框
                const existingModal = document.getElementById('editLinkModal');
                if (existingModal) {
                    existingModal.remove();
                }

                // 添加新模态框
                document.body.insertAdjacentHTML('beforeend', formHtml);

                // 显示模态框
                const modal = new bootstrap.Modal(document.getElementById('editLinkModal'));
                modal.show();

            } catch (error) {
                console.error('编辑友链失败:', error);
                alert('编辑友链失败: ' + error.message);
            }
        }

        // 更新友链
        async function updateLink() {
            const form = document.getElementById('editLinkForm');
            const formData = new FormData(form);

            // 验证必填字段
            const name = formData.get('name').trim();
            const url = formData.get('url').trim();
            const linkId = formData.get('link_id');

            if (!name) {
                alert('请输入网站名称');
                return;
            }

            if (!url) {
                alert('请输入网站链接');
                return;
            }

            let avatarUrl = formData.get('avatar').trim();

            // 检查是否有上传的文件
            const avatarFile = document.getElementById('editAvatarFile').files[0];
            if (avatarFile) {
                try {
                    // 上传文件
                    const uploadFormData = new FormData();
                    uploadFormData.append('file', avatarFile);

                    const uploadResponse = await fetch('/api/admin/upload', {
                        method: 'POST',
                        credentials: 'same-origin',
                        body: uploadFormData
                    });

                    const uploadResult = await uploadResponse.json();

                    if (uploadResponse.ok) {
                        avatarUrl = uploadResult.file_url;
                    } else {
                        alert('头像上传失败: ' + uploadResult.error);
                        return;
                    }
                } catch (error) {
                    console.error('头像上传失败:', error);
                    alert('头像上传失败: ' + error.message);
                    return;
                }
            }

            const linkData = {
                name: name,
                url: url,
                description: formData.get('description').trim(),
                avatar: avatarUrl,
                category: formData.get('category'),
                sort_order: parseInt(formData.get('sort_order')) || 0,
                is_active: formData.has('is_active')
            };

            try {
                const response = await fetch(`/api/admin/links/${linkId}`, {
                    method: 'PUT',
                    credentials: 'same-origin',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(linkData)
                });

                const result = await response.json();

                if (response.ok) {
                    alert('友链更新成功！');
                    bootstrap.Modal.getInstance(document.getElementById('editLinkModal')).hide();
                    loadLinks(); // 重新加载友链列表
                } else {
                    alert('更新失败: ' + (result.error || '未知错误'));
                }
            } catch (error) {
                console.error('更新友链失败:', error);
                alert('更新友链失败: ' + error.message);
            }
        }

        // 编辑文章
        function editPost(postId) {
            alert(`编辑文章功能开发中... (文章ID: ${postId})`);
        }

        // 删除文章
        async function deletePost(postId) {
            if (!confirm('确定要删除这篇文章吗？删除后无法恢复！')) {
                return;
            }

            try {
                const response = await fetch(`/api/admin/posts/${postId}`, {
                    method: 'DELETE',
                    credentials: 'same-origin'
                });

                const result = await response.json();

                if (response.ok) {
                    alert('文章删除成功！');
                    loadPosts(); // 重新加载文章列表
                } else {
                    alert('删除失败: ' + result.error);
                }
            } catch (error) {
                console.error('删除文章失败:', error);
                alert('删除文章失败');
            }
        }

        // 显示添加项目表单
        function showAddProjectForm() {
            const formHtml = `
                <div class="modal fade" id="projectModal" tabindex="-1">
                    <div class="modal-dialog modal-lg">
                        <div class="modal-content" style="background: rgba(30, 41, 59, 0.95); border: 1px solid rgba(102, 126, 234, 0.3);">
                            <div class="modal-header" style="border-bottom: 1px solid rgba(102, 126, 234, 0.3);">
                                <h5 class="modal-title text-white">添加项目</h5>
                                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                            </div>
                            <div class="modal-body">
                                <form id="projectForm">
                                    <div class="mb-3">
                                        <label class="form-label text-light">项目名称 *</label>
                                        <input type="text" class="form-control" name="name" required
                                               style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(102, 126, 234, 0.3); color: white;"
                                               placeholder="例如：数据分析项目">
                                    </div>
                                    <div class="mb-3">
                                        <label class="form-label text-light">项目描述 *</label>
                                        <textarea class="form-control" name="description" rows="3" required
                                                  style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(102, 126, 234, 0.3); color: white;"
                                                  placeholder="详细描述项目功能和特点..."></textarea>
                                    </div>
                                    <div class="mb-3">
                                        <label class="form-label text-light">技术栈</label>
                                        <input type="text" class="form-control" name="technologies"
                                               style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(102, 126, 234, 0.3); color: white;"
                                               placeholder="Python, Pandas, Matplotlib, SQL">
                                    </div>
                                    <div class="row">
                                        <div class="col-md-6">
                                            <label class="form-label text-light">GitHub链接</label>
                                            <input type="url" class="form-control" name="github_url"
                                                   style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(102, 126, 234, 0.3); color: white;"
                                                   placeholder="https://github.com/username/project">
                                        </div>
                                        <div class="col-md-6">
                                            <label class="form-label text-light">演示链接</label>
                                            <input type="url" class="form-control" name="demo_url"
                                                   style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(102, 126, 234, 0.3); color: white;"
                                                   placeholder="https://demo.example.com">
                                        </div>
                                    </div>
                                    <div class="row mt-3">
                                        <div class="col-md-6">
                                            <label class="form-label text-light">项目状态</label>
                                            <select class="form-select" name="status"
                                                    style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(102, 126, 234, 0.3); color: white;">
                                                <option value="completed">已完成</option>
                                                <option value="in_progress">进行中</option>
                                                <option value="planned">计划中</option>
                                            </select>
                                        </div>
                                        <div class="col-md-6">
                                            <div class="form-check mt-4">
                                                <input class="form-check-input" type="checkbox" name="is_featured" id="isFeatured">
                                                <label class="form-check-label text-light" for="isFeatured">
                                                    设为精选项目
                                                </label>
                                            </div>
                                        </div>
                                    </div>
                                </form>
                            </div>
                            <div class="modal-footer" style="border-top: 1px solid rgba(102, 126, 234, 0.3);">
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                                <button type="button" class="btn btn-cool" onclick="saveProject()">保存项目</button>
                            </div>
                        </div>
                    </div>
                </div>
            `;

            // 移除已存在的模态框
            const existingModal = document.getElementById('projectModal');
            if (existingModal) {
                existingModal.remove();
            }

            // 添加新模态框
            document.body.insertAdjacentHTML('beforeend', formHtml);

            // 显示模态框
            const modal = new bootstrap.Modal(document.getElementById('projectModal'));
            modal.show();
        }

        // 保存项目
        async function saveProject() {
            const form = document.getElementById('projectForm');
            const formData = new FormData(form);

            // 验证必填字段
            const name = formData.get('name').trim();
            const description = formData.get('description').trim();

            if (!name) {
                alert('请输入项目名称');
                return;
            }

            if (!description) {
                alert('请输入项目描述');
                return;
            }

            const projectData = {
                name: name,
                description: description,
                technologies: formData.get('technologies').trim(),
                github_url: formData.get('github_url').trim(),
                demo_url: formData.get('demo_url').trim(),
                status: formData.get('status'),
                is_featured: formData.has('is_featured')
            };

            try {
                const response = await fetch('/api/admin/projects', {
                    method: 'POST',
                    credentials: 'same-origin',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(projectData)
                });

                const result = await response.json();

                if (response.ok) {
                    alert('项目保存成功！');
                    bootstrap.Modal.getInstance(document.getElementById('projectModal')).hide();
                    loadProjects(); // 重新加载项目列表
                } else {
                    alert('保存失败: ' + (result.error || '未知错误'));
                }
            } catch (error) {
                console.error('保存项目失败:', error);
                alert('保存项目失败: ' + error.message);
            }
        }

        // 编辑项目
        async function editProject(projectId) {
            try {
                // 获取项目详情
                const response = await fetch(`/api/admin/projects/${projectId}`, {
                    credentials: 'same-origin'
                });

                if (!response.ok) {
                    alert('获取项目信息失败');
                    return;
                }

                const data = await response.json();
                const project = data.project;

                const formHtml = `
                    <div class="modal fade" id="editProjectModal" tabindex="-1">
                        <div class="modal-dialog modal-lg">
                            <div class="modal-content" style="background: rgba(30, 41, 59, 0.95); border: 1px solid rgba(102, 126, 234, 0.3);">
                                <div class="modal-header" style="border-bottom: 1px solid rgba(102, 126, 234, 0.3);">
                                    <h5 class="modal-title text-white">编辑项目</h5>
                                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                                </div>
                                <div class="modal-body">
                                    <form id="editProjectForm">
                                        <input type="hidden" name="project_id" value="${project.id}">
                                        <div class="mb-3">
                                            <label class="form-label text-light">项目名称 *</label>
                                            <input type="text" class="form-control" name="name" required value="${project.name}"
                                                   style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(102, 126, 234, 0.3); color: white;">
                                        </div>
                                        <div class="mb-3">
                                            <label class="form-label text-light">项目描述 *</label>
                                            <textarea class="form-control" name="description" rows="3" required
                                                      style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(102, 126, 234, 0.3); color: white;">${project.description}</textarea>
                                        </div>
                                        <div class="mb-3">
                                            <label class="form-label text-light">技术栈</label>
                                            <input type="text" class="form-control" name="technologies" value="${project.technologies || ''}"
                                                   style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(102, 126, 234, 0.3); color: white;">
                                        </div>
                                        <div class="row">
                                            <div class="col-md-6">
                                                <label class="form-label text-light">GitHub链接</label>
                                                <input type="url" class="form-control" name="github_url" value="${project.github_url || ''}"
                                                       style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(102, 126, 234, 0.3); color: white;">
                                            </div>
                                            <div class="col-md-6">
                                                <label class="form-label text-light">演示链接</label>
                                                <input type="url" class="form-control" name="demo_url" value="${project.demo_url || ''}"
                                                       style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(102, 126, 234, 0.3); color: white;">
                                            </div>
                                        </div>
                                        <div class="row mt-3">
                                            <div class="col-md-6">
                                                <label class="form-label text-light">项目状态</label>
                                                <select class="form-select" name="status"
                                                        style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(102, 126, 234, 0.3); color: white;">
                                                    <option value="completed" ${project.status === 'completed' ? 'selected' : ''}>已完成</option>
                                                    <option value="in_progress" ${project.status === 'in_progress' ? 'selected' : ''}>进行中</option>
                                                    <option value="planned" ${project.status === 'planned' ? 'selected' : ''}>计划中</option>
                                                </select>
                                            </div>
                                            <div class="col-md-6">
                                                <div class="form-check mt-4">
                                                    <input class="form-check-input" type="checkbox" name="is_featured" id="editIsFeatured" ${project.is_featured ? 'checked' : ''}>
                                                    <label class="form-check-label text-light" for="editIsFeatured">
                                                        设为精选项目
                                                    </label>
                                                </div>
                                            </div>
                                        </div>
                                    </form>
                                </div>
                                <div class="modal-footer" style="border-top: 1px solid rgba(102, 126, 234, 0.3);">
                                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                                    <button type="button" class="btn btn-cool" onclick="updateProject()">更新项目</button>
                                </div>
                            </div>
                        </div>
                    </div>
                `;

                // 移除已存在的模态框
                const existingModal = document.getElementById('editProjectModal');
                if (existingModal) {
                    existingModal.remove();
                }

                // 添加新模态框
                document.body.insertAdjacentHTML('beforeend', formHtml);

                // 显示模态框
                const modal = new bootstrap.Modal(document.getElementById('editProjectModal'));
                modal.show();

            } catch (error) {
                console.error('编辑项目失败:', error);
                alert('编辑项目失败: ' + error.message);
            }
        }

        // 更新项目
        async function updateProject() {
            const form = document.getElementById('editProjectForm');
            const formData = new FormData(form);

            // 验证必填字段
            const name = formData.get('name').trim();
            const description = formData.get('description').trim();
            const projectId = formData.get('project_id');

            if (!name) {
                alert('请输入项目名称');
                return;
            }

            if (!description) {
                alert('请输入项目描述');
                return;
            }

            const projectData = {
                name: name,
                description: description,
                technologies: formData.get('technologies').trim(),
                github_url: formData.get('github_url').trim(),
                demo_url: formData.get('demo_url').trim(),
                status: formData.get('status'),
                is_featured: formData.has('is_featured')
            };

            try {
                const response = await fetch(`/api/admin/projects/${projectId}`, {
                    method: 'PUT',
                    credentials: 'same-origin',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(projectData)
                });

                const result = await response.json();

                if (response.ok) {
                    alert('项目更新成功！');
                    bootstrap.Modal.getInstance(document.getElementById('editProjectModal')).hide();
                    loadProjects(); // 重新加载项目列表
                } else {
                    alert('更新失败: ' + (result.error || '未知错误'));
                }
            } catch (error) {
                console.error('更新项目失败:', error);
                alert('更新项目失败: ' + error.message);
            }
        }

        // 删除项目
        async function deleteProject(projectId) {
            if (!confirm('确定要删除这个项目吗？')) {
                return;
            }

            try {
                const response = await fetch(`/api/admin/projects/${projectId}`, {
                    method: 'DELETE',
                    credentials: 'same-origin'
                });

                const result = await response.json();

                if (response.ok) {
                    alert('项目删除成功！');
                    loadProjects(); // 重新加载项目列表
                } else {
                    alert('删除失败: ' + result.error);
                }
            } catch (error) {
                console.error('删除项目失败:', error);
                alert('删除项目失败');
            }
        }

        // 显示添加分类表单
        function showAddCategoryForm() {
            const formHtml = `
                <div class="modal fade" id="categoryModal" tabindex="-1">
                    <div class="modal-dialog">
                        <div class="modal-content" style="background: rgba(30, 41, 59, 0.95); border: 1px solid rgba(102, 126, 234, 0.3);">
                            <div class="modal-header" style="border-bottom: 1px solid rgba(102, 126, 234, 0.3);">
                                <h5 class="modal-title text-white">添加分类</h5>
                                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                            </div>
                            <div class="modal-body">
                                <form id="categoryForm">
                                    <div class="mb-3">
                                        <label class="form-label text-light">分类名称 *</label>
                                        <input type="text" class="form-control" name="name" required
                                               style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(102, 126, 234, 0.3); color: white;"
                                               placeholder="例如：技术分享">
                                    </div>
                                    <div class="mb-3">
                                        <label class="form-label text-light">分类描述</label>
                                        <textarea class="form-control" name="description" rows="2"
                                                  style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(102, 126, 234, 0.3); color: white;"
                                                  placeholder="简单描述这个分类..."></textarea>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-6">
                                            <label class="form-label text-light">分类颜色</label>
                                            <select class="form-select" name="color"
                                                    style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(102, 126, 234, 0.3); color: white;">
                                                <option value="#3b82f6">蓝色</option>
                                                <option value="#8b5cf6">紫色</option>
                                                <option value="#10b981">绿色</option>
                                                <option value="#f59e0b">橙色</option>
                                                <option value="#ef4444">红色</option>
                                                <option value="#06b6d4">青色</option>
                                                <option value="#84cc16">草绿</option>
                                                <option value="#f97316">深橙</option>
                                            </select>
                                        </div>
                                        <div class="col-md-6">
                                            <label class="form-label text-light">分类图标</label>
                                            <select class="form-select" name="icon"
                                                    style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(102, 126, 234, 0.3); color: white;">
                                                <option value="fas fa-folder">文件夹</option>
                                                <option value="fas fa-chart-line">图表</option>
                                                <option value="fas fa-brain">大脑</option>
                                                <option value="fas fa-chart-bar">柱状图</option>
                                                <option value="fas fa-graduation-cap">毕业帽</option>
                                                <option value="fas fa-project-diagram">项目图</option>
                                                <option value="fas fa-briefcase">公文包</option>
                                                <option value="fas fa-code">代码</option>
                                                <option value="fas fa-database">数据库</option>
                                                <option value="fas fa-laptop-code">笔记本</option>
                                            </select>
                                        </div>
                                    </div>
                                </form>
                            </div>
                            <div class="modal-footer" style="border-top: 1px solid rgba(102, 126, 234, 0.3);">
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                                <button type="button" class="btn btn-cool" onclick="saveCategory()">保存分类</button>
                            </div>
                        </div>
                    </div>
                </div>
            `;

            // 移除已存在的模态框
            const existingModal = document.getElementById('categoryModal');
            if (existingModal) {
                existingModal.remove();
            }

            // 添加新模态框
            document.body.insertAdjacentHTML('beforeend', formHtml);

            // 显示模态框
            const modal = new bootstrap.Modal(document.getElementById('categoryModal'));
            modal.show();
        }

        // 保存分类
        async function saveCategory() {
            const form = document.getElementById('categoryForm');
            const formData = new FormData(form);

            // 验证必填字段
            const name = formData.get('name').trim();

            if (!name) {
                alert('请输入分类名称');
                return;
            }

            const categoryData = {
                name: name,
                description: formData.get('description').trim(),
                color: formData.get('color'),
                icon: formData.get('icon')
            };

            try {
                const response = await fetch('/api/admin/categories', {
                    method: 'POST',
                    credentials: 'same-origin',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(categoryData)
                });

                const result = await response.json();

                if (response.ok) {
                    alert('分类保存成功！');
                    bootstrap.Modal.getInstance(document.getElementById('categoryModal')).hide();
                    loadCategories(); // 重新加载分类列表
                } else {
                    alert('保存失败: ' + (result.error || '未知错误'));
                }
            } catch (error) {
                console.error('保存分类失败:', error);
                alert('保存分类失败: ' + error.message);
            }
        }

        // 编辑分类
        function editCategory(categoryId) {
            alert(`编辑分类功能开发中... (分类ID: ${categoryId})`);
        }

        // 删除分类
        async function deleteCategory(categoryId) {
            if (!confirm('确定要删除这个分类吗？删除后该分类下的文章将变为无分类状态。')) {
                return;
            }

            try {
                const response = await fetch(`/api/admin/categories/${categoryId}`, {
                    method: 'DELETE',
                    credentials: 'same-origin'
                });

                const result = await response.json();

                if (response.ok) {
                    alert('分类删除成功！');
                    loadCategories(); // 重新加载分类列表
                } else {
                    alert('删除失败: ' + result.error);
                }
            } catch (error) {
                console.error('删除分类失败:', error);
                alert('删除分类失败');
            }
        }

        // 系统设置功能
        function saveSiteConfig() {
            alert('网站配置保存功能开发中...');
        }

        function saveApiConfig() {
            alert('API配置保存功能开发中...');
        }

        function exportData() {
            alert('数据导出功能开发中...');
        }

        function showImportData() {
            alert('数据导入功能开发中...');
        }

        function clearCache() {
            if (confirm('确定要清理缓存吗？')) {
                alert('缓存清理功能开发中...');
            }
        }
    </script>
</body>
</html>
'''

# ==================== 管理API功能 ====================

# 文章管理API
@app.route('/api/admin/posts', methods=['GET'])
def api_admin_posts():
    if not session.get('admin_logged_in'):
        return jsonify({'error': '未授权'}), 401

    posts = Post.query.order_by(Post.created_at.desc()).all()
    posts_data = []
    for post in posts:
        posts_data.append({
            'id': post.id,
            'title': post.title,
            'slug': post.slug,
            'category': post.category.name if post.category else '无分类',
            'status': '已发布' if post.is_published else '草稿',
            'created_at': post.created_at.strftime('%Y-%m-%d %H:%M'),
            'view_count': post.view_count
        })

    return jsonify({'posts': posts_data})

@app.route('/api/admin/posts/<int:post_id>', methods=['GET'])
def api_get_post(post_id):
    if not session.get('admin_logged_in'):
        return jsonify({'error': '未授权'}), 401

    post = Post.query.get_or_404(post_id)
    post_data = {
        'id': post.id,
        'title': post.title,
        'slug': post.slug,
        'content': post.content,
        'summary': post.summary,
        'category_id': post.category_id,
        'is_published': post.is_published,
        'is_featured': post.is_featured,
        'created_at': post.created_at.strftime('%Y-%m-%d %H:%M'),
        'updated_at': post.updated_at.strftime('%Y-%m-%d %H:%M'),
        'view_count': post.view_count
    }

    return jsonify({'post': post_data})

@app.route('/api/admin/posts', methods=['POST'])
def api_create_post():
    if not session.get('admin_logged_in'):
        return jsonify({'error': '未授权'}), 401

    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': '无效的JSON数据'}), 400

        # 验证必填字段
        if not data.get('title'):
            return jsonify({'error': '标题不能为空'}), 400

        if not data.get('content'):
            return jsonify({'error': '内容不能为空'}), 400

        # 生成slug
        title = data['title'].strip()
        slug = title.lower().replace(' ', '-').replace('，', '-').replace('。', '')
        slug = ''.join(c for c in slug if c.isalnum() or c == '-' or ord(c) > 127)

        # 检查slug是否已存在
        existing_post = Post.query.filter_by(slug=slug).first()
        if existing_post:
            slug = f"{slug}-{int(time.time())}"

        # 获取当前用户ID（使用Flask-Login的current_user或者从session获取）
        if current_user.is_authenticated:
            user_id = current_user.id
        else:
            # 如果Flask-Login没有用户，从数据库获取admin用户
            admin_user = User.query.filter_by(username='admin').first()
            if not admin_user:
                return jsonify({'error': '用户不存在'}), 400
            user_id = admin_user.id

        new_post = Post(
            title=title,
            slug=slug,
            content=data['content'].strip(),
            summary=data.get('summary', '').strip(),
            category_id=data.get('category_id') if data.get('category_id') else None,
            is_published=data.get('is_published', False),
            user_id=user_id,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        db.session.add(new_post)
        db.session.commit()

        return jsonify({'message': '文章创建成功', 'post_id': new_post.id})

    except Exception as e:
        db.session.rollback()
        print(f"创建文章错误: {e}")  # 调试用
        return jsonify({'error': f'创建文章失败: {str(e)}'}), 500

@app.route('/api/admin/posts/<int:post_id>', methods=['PUT'])
def api_update_post(post_id):
    if not session.get('admin_logged_in'):
        return jsonify({'error': '未授权'}), 401

    post = Post.query.get_or_404(post_id)
    data = request.get_json()

    post.title = data['title']
    post.content = data['content']
    post.summary = data.get('summary', '')
    post.category_id = data.get('category_id')
    post.is_published = data.get('is_published', False)
    post.updated_at = datetime.now()

    db.session.commit()

    return jsonify({'message': '文章更新成功'})

@app.route('/api/admin/posts/<int:post_id>', methods=['DELETE'])
def api_delete_post(post_id):
    if not session.get('admin_logged_in'):
        return jsonify({'error': '未授权'}), 401

    post = Post.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()

    return jsonify({'message': '文章删除成功'})

# 分类管理API
@app.route('/api/admin/categories', methods=['GET'])
def api_admin_categories():
    if not session.get('admin_logged_in'):
        return jsonify({'error': '未授权'}), 401

    categories = Category.query.all()
    categories_data = []
    for category in categories:
        categories_data.append({
            'id': category.id,
            'name': category.name,
            'description': category.description,
            'color': category.color,
            'icon': category.icon,
            'post_count': category.posts.count()  # 使用count()方法而不是len()
        })

    return jsonify({'categories': categories_data})

@app.route('/api/admin/categories', methods=['POST'])
def api_create_category():
    if not session.get('admin_logged_in'):
        return jsonify({'error': '未授权'}), 401

    data = request.get_json()

    new_category = Category(
        name=data['name'],
        description=data.get('description', ''),
        color=data.get('color', '#667eea'),
        icon=data.get('icon', 'fas fa-folder')
    )

    db.session.add(new_category)
    db.session.commit()

    return jsonify({'message': '分类创建成功', 'category_id': new_category.id})

@app.route('/api/admin/categories/<int:category_id>', methods=['DELETE'])
def api_delete_category(category_id):
    if not session.get('admin_logged_in'):
        return jsonify({'error': '未授权'}), 401

    category = Category.query.get_or_404(category_id)

    # 将该分类下的文章设为无分类
    posts = Post.query.filter_by(category_id=category_id).all()
    for post in posts:
        post.category_id = None

    db.session.delete(category)
    db.session.commit()

    return jsonify({'message': '分类删除成功'})

# 个人信息管理API
@app.route('/api/admin/profile', methods=['GET'])
def api_get_profile():
    if not session.get('admin_logged_in'):
        return jsonify({'error': '未授权'}), 401

    # 获取当前个人信息
    profile_data = {
        'name': app.config.get('AUTHOR_NAME', ''),
        'email': app.config.get('AUTHOR_EMAIL', ''),
        'location': app.config.get('AUTHOR_LOCATION', ''),
        'github': 'wswldcs',
        'bio': '用数据讲故事，用分析驱动决策',
        'blog_title': app.config.get('BLOG_TITLE', ''),
        'blog_description': app.config.get('BLOG_DESCRIPTION', '')
    }

    return jsonify({'profile': profile_data})

@app.route('/api/admin/profile', methods=['PUT'])
def api_update_profile():
    if not session.get('admin_logged_in'):
        return jsonify({'error': '未授权'}), 401

    data = request.get_json()

    # 更新配置（注意：这里只是临时更新，重启后会恢复）
    # 在实际应用中，应该将这些信息保存到数据库或配置文件
    app.config['AUTHOR_NAME'] = data.get('name', app.config.get('AUTHOR_NAME'))
    app.config['AUTHOR_EMAIL'] = data.get('email', app.config.get('AUTHOR_EMAIL'))
    app.config['AUTHOR_LOCATION'] = data.get('location', app.config.get('AUTHOR_LOCATION'))
    app.config['BLOG_TITLE'] = data.get('blog_title', app.config.get('BLOG_TITLE'))
    app.config['BLOG_DESCRIPTION'] = data.get('blog_description', app.config.get('BLOG_DESCRIPTION'))

    return jsonify({'message': '个人信息更新成功'})

# 项目管理API
@app.route('/api/admin/projects', methods=['GET'])
def api_admin_projects():
    if not session.get('admin_logged_in'):
        return jsonify({'error': '未授权'}), 401

    projects = Project.query.all()
    projects_data = []
    for project in projects:
        projects_data.append({
            'id': project.id,
            'name': project.name,
            'description': project.description,
            'technologies': project.tech_stack,  # 修复字段名
            'github_url': project.github_url,
            'demo_url': project.demo_url,
            'status': project.status,
            'is_featured': project.is_featured,
            'created_at': project.created_at.strftime('%Y-%m-%d') if project.created_at else ''
        })

    return jsonify({'projects': projects_data})

@app.route('/api/admin/projects/<int:project_id>', methods=['GET'])
def api_get_project(project_id):
    if not session.get('admin_logged_in'):
        return jsonify({'error': '未授权'}), 401

    project = Project.query.get_or_404(project_id)
    project_data = {
        'id': project.id,
        'name': project.name,
        'description': project.description,
        'technologies': project.tech_stack,
        'github_url': project.github_url,
        'demo_url': project.demo_url,
        'status': project.status,
        'is_featured': project.is_featured,
        'created_at': project.created_at.strftime('%Y-%m-%d') if project.created_at else ''
    }

    return jsonify({'project': project_data})

@app.route('/api/admin/projects', methods=['POST'])
def api_create_project():
    if not session.get('admin_logged_in'):
        return jsonify({'error': '未授权'}), 401

    data = request.get_json()

    new_project = Project(
        name=data['name'],
        description=data.get('description', ''),
        tech_stack=data.get('technologies', ''),  # 修复字段名
        github_url=data.get('github_url', ''),
        demo_url=data.get('demo_url', ''),
        status=data.get('status', 'planned'),
        is_featured=data.get('is_featured', False),
        created_at=datetime.now()
    )

    db.session.add(new_project)
    db.session.commit()

    return jsonify({'message': '项目创建成功', 'project_id': new_project.id})

@app.route('/api/admin/projects/<int:project_id>', methods=['PUT'])
def api_update_project(project_id):
    if not session.get('admin_logged_in'):
        return jsonify({'error': '未授权'}), 401

    project = Project.query.get_or_404(project_id)
    data = request.get_json()

    # 更新项目信息
    project.name = data.get('name', project.name)
    project.description = data.get('description', project.description)
    project.tech_stack = data.get('technologies', project.tech_stack)
    project.github_url = data.get('github_url', project.github_url)
    project.demo_url = data.get('demo_url', project.demo_url)
    project.status = data.get('status', project.status)
    project.is_featured = data.get('is_featured', project.is_featured)

    db.session.commit()

    return jsonify({'message': '项目更新成功', 'project_id': project.id})

@app.route('/api/admin/projects/<int:project_id>', methods=['DELETE'])
def api_delete_project(project_id):
    if not session.get('admin_logged_in'):
        return jsonify({'error': '未授权'}), 401

    project = Project.query.get_or_404(project_id)
    db.session.delete(project)
    db.session.commit()

    return jsonify({'message': '项目删除成功'})

# 时间线管理API
@app.route('/api/admin/timeline', methods=['GET'])
def api_admin_timeline():
    if not session.get('admin_logged_in'):
        return jsonify({'error': '未授权'}), 401

    timeline_items = Timeline.query.order_by(Timeline.date.asc()).all()  # 改为正序
    timeline_data = []
    for item in timeline_items:
        timeline_data.append({
            'id': item.id,
            'title': item.title,
            'description': item.description,
            'date': item.date.strftime('%Y-%m-%d'),
            'category': item.category,
            'color': item.color,
            'icon': item.icon
        })

    return jsonify({'timeline': timeline_data})

@app.route('/api/admin/timeline', methods=['POST'])
def api_create_timeline():
    if not session.get('admin_logged_in'):
        return jsonify({'error': '未授权'}), 401

    data = request.get_json()

    new_item = Timeline(
        title=data['title'],
        description=data.get('description', ''),
        date=datetime.strptime(data['date'], '%Y-%m-%d').date(),
        category=data.get('category', 'education'),
        color=data.get('color', '#667eea'),
        icon=data.get('icon', 'fas fa-graduation-cap')
    )

    db.session.add(new_item)
    db.session.commit()

    return jsonify({'message': '时间线项目创建成功', 'item_id': new_item.id})

@app.route('/api/admin/timeline/<int:item_id>', methods=['DELETE'])
def api_delete_timeline(item_id):
    if not session.get('admin_logged_in'):
        return jsonify({'error': '未授权'}), 401

    timeline_item = Timeline.query.get_or_404(item_id)
    db.session.delete(timeline_item)
    db.session.commit()

    return jsonify({'message': '时间线项目删除成功'})

# 友链管理API
@app.route('/api/admin/links', methods=['GET'])
def api_admin_links():
    if not session.get('admin_logged_in'):
        return jsonify({'error': '未授权'}), 401

    links = Link.query.order_by(Link.sort_order.desc(), Link.created_at.desc()).all()
    links_data = []
    for link in links:
        links_data.append({
            'id': link.id,
            'name': link.name,
            'url': link.url,
            'description': link.description,
            'avatar': link.avatar,
            'category': link.category,
            'is_active': link.is_active,
            'sort_order': link.sort_order,
            'created_at': link.created_at.strftime('%Y-%m-%d') if link.created_at else ''
        })

    return jsonify({'links': links_data})

@app.route('/api/admin/links/<int:link_id>', methods=['GET'])
def api_get_link(link_id):
    if not session.get('admin_logged_in'):
        return jsonify({'error': '未授权'}), 401

    link = Link.query.get_or_404(link_id)
    link_data = {
        'id': link.id,
        'name': link.name,
        'url': link.url,
        'description': link.description,
        'avatar': link.avatar,
        'category': link.category,
        'is_active': link.is_active,
        'sort_order': link.sort_order,
        'created_at': link.created_at.strftime('%Y-%m-%d') if link.created_at else ''
    }

    return jsonify({'link': link_data})

@app.route('/api/admin/links', methods=['POST'])
def api_create_link():
    if not session.get('admin_logged_in'):
        return jsonify({'error': '未授权'}), 401

    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': '无效的JSON数据'}), 400

        # 验证必填字段
        if not data.get('name'):
            return jsonify({'error': '网站名称不能为空'}), 400

        if not data.get('url'):
            return jsonify({'error': '网站链接不能为空'}), 400

        new_link = Link(
            name=data['name'].strip(),
            url=data['url'].strip(),
            description=data.get('description', '').strip(),
            avatar=data.get('avatar', '').strip(),
            category=data.get('category', 'friend'),
            is_active=data.get('is_active', True),
            sort_order=data.get('sort_order', 0),
            created_at=datetime.now()
        )

        db.session.add(new_link)
        db.session.commit()

        return jsonify({'message': '友链创建成功', 'link_id': new_link.id})

    except Exception as e:
        db.session.rollback()
        print(f"创建友链错误: {e}")  # 调试用
        return jsonify({'error': f'创建友链失败: {str(e)}'}), 500

@app.route('/api/admin/links/<int:link_id>', methods=['PUT'])
def api_update_link(link_id):
    if not session.get('admin_logged_in'):
        return jsonify({'error': '未授权'}), 401

    link = Link.query.get_or_404(link_id)
    data = request.get_json()

    link.name = data.get('name', link.name)
    link.url = data.get('url', link.url)
    link.description = data.get('description', link.description)
    link.avatar = data.get('avatar', link.avatar)
    link.category = data.get('category', link.category)
    link.is_active = data.get('is_active', link.is_active)
    link.sort_order = data.get('sort_order', link.sort_order)

    db.session.commit()

    return jsonify({'message': '友链更新成功'})

@app.route('/api/admin/links/<int:link_id>', methods=['DELETE'])
def api_delete_link(link_id):
    if not session.get('admin_logged_in'):
        return jsonify({'error': '未授权'}), 401

    link = Link.query.get_or_404(link_id)
    db.session.delete(link)
    db.session.commit()

    return jsonify({'message': '友链删除成功'})

# 文件上传API
@app.route('/api/admin/upload', methods=['POST'])
def api_upload_file():
    if not session.get('admin_logged_in'):
        return jsonify({'error': '未授权'}), 401

    if 'file' not in request.files:
        return jsonify({'error': '没有选择文件'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400

    if file and allowed_file(file.filename):
        try:
            # 确保上传目录存在
            upload_folder = app.config['UPLOAD_FOLDER']
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)

            # 生成安全的文件名
            filename = secure_filename(file.filename)
            # 添加时间戳避免重名
            name, ext = os.path.splitext(filename)
            filename = f"{name}_{int(time.time())}{ext}"

            # 保存文件
            file_path = os.path.join(upload_folder, filename)
            file.save(file_path)

            # 返回文件URL
            file_url = f"/static/uploads/{filename}"
            return jsonify({
                'message': '文件上传成功',
                'file_url': file_url,
                'filename': filename
            })

        except Exception as e:
            return jsonify({'error': f'文件上传失败: {str(e)}'}), 500
    else:
        return jsonify({'error': '不支持的文件类型，请上传 PNG、JPG、JPEG、GIF 或 WEBP 格式的图片'}), 400

if __name__ == '__main__':
    print("="*60)
    print("🚀 启动功能丰富的个人博客系统")
    print("📝 包含完整的博客功能和个性化特性")
    print("="*60)
    
    # 初始化数据库
    if init_database(app):
        port = int(os.environ.get('PORT', 8080))
        print(f"🌐 应用启动在端口: {port}")
        app.run(host='0.0.0.0', port=port, debug=False)
    else:
        print("❌ 数据库初始化失败，应用退出")
        exit(1)
