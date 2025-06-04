#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
功能丰富的个人博客系统
包含：日历、天气、访客信息、社交链接、学习历程、项目展示等完整功能
"""

import os
import json
import requests
from datetime import datetime, timedelta
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
            <div class="row mb-5 fade-in-up">
                <div class="col-md-8">
                    <form method="GET" class="d-flex">
                        <input type="text" name="search" class="form-control me-3"
                               placeholder="🔍 搜索我的学习笔记..."
                               value="{{ search_query or '' }}"
                               style="background: rgba(30, 41, 59, 0.8); border: 1px solid rgba(102, 126, 234, 0.3); color: white; border-radius: 25px; padding: 0.75rem 1.5rem;">
                        <button type="submit" class="btn btn-cool">
                            <i class="fas fa-search me-2"></i>搜索
                        </button>
                    </form>
                </div>
                <div class="col-md-4">
                    <select class="form-select"
                            onchange="location.href='{{ url_for('blog') }}?category=' + this.value"
                            style="background: rgba(30, 41, 59, 0.8); border: 1px solid rgba(102, 126, 234, 0.3); color: white; border-radius: 25px; padding: 0.75rem 1.5rem;">
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
    <style>
        body { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); }
        .navbar { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important; }
        .project-card {
            background: white; border-radius: 15px; padding: 2rem;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1); transition: all 0.3s ease; height: 100%;
        }
        .project-card:hover { transform: translateY(-10px); }
        .tech-badge {
            background: #f8f9fa; color: #495057; padding: 0.25rem 0.75rem;
            border-radius: 50px; font-size: 0.875rem; margin: 0.25rem;
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
        <h1 class="mb-4">项目展示</h1>

        <!-- 精选项目 -->
        {% if featured_projects %}
        <h2 class="mb-4">精选项目</h2>
        <div class="row mb-5">
            {% for project in featured_projects %}
            <div class="col-md-6 col-lg-4 mb-4">
                <div class="project-card">
                    <h5 class="mb-3">{{ project.name }}</h5>
                    <p class="text-muted">{{ project.description }}</p>
                    <div class="mb-3">
                        {% for tech in project.get_tech_list() %}
                        <span class="tech-badge">{{ tech }}</span>
                        {% endfor %}
                    </div>
                    <div class="d-flex gap-2">
                        {% if project.github_url %}
                        <a href="{{ project.github_url }}" class="btn btn-outline-dark btn-sm" target="_blank">
                            <i class="fab fa-github me-1"></i>GitHub
                        </a>
                        {% endif %}
                        {% if project.demo_url %}
                        <a href="{{ project.demo_url }}" class="btn btn-primary btn-sm" target="_blank">
                            <i class="fas fa-external-link-alt me-1"></i>演示
                        </a>
                        {% endif %}
                    </div>
                    <div class="mt-2">
                        <small class="text-muted">
                            状态:
                            {% if project.status == 'completed' %}
                            <span class="badge bg-success">已完成</span>
                            {% elif project.status == 'in_progress' %}
                            <span class="badge bg-warning">进行中</span>
                            {% else %}
                            <span class="badge bg-secondary">计划中</span>
                            {% endif %}
                        </small>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
        {% endif %}

        <!-- 其他项目 -->
        {% if other_projects %}
        <h2 class="mb-4">其他项目</h2>
        <div class="row">
            {% for project in other_projects %}
            <div class="col-md-6 col-lg-4 mb-4">
                <div class="project-card">
                    <h6 class="mb-3">{{ project.name }}</h6>
                    <p class="text-muted small">{{ project.description }}</p>
                    <div class="mb-3">
                        {% for tech in project.get_tech_list()[:3] %}
                        <span class="tech-badge">{{ tech }}</span>
                        {% endfor %}
                    </div>
                    <div class="d-flex gap-2">
                        {% if project.github_url %}
                        <a href="{{ project.github_url }}" class="btn btn-outline-dark btn-sm" target="_blank">
                            <i class="fab fa-github"></i>
                        </a>
                        {% endif %}
                        {% if project.demo_url %}
                        <a href="{{ project.demo_url }}" class="btn btn-primary btn-sm" target="_blank">
                            <i class="fas fa-external-link-alt"></i>
                        </a>
                        {% endif %}
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
        {% endif %}
    </div>
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

        .timeline-item:nth-child(odd) .timeline-content {
            margin-left: 55%;
        }

        .timeline-item:nth-child(even) .timeline-content {
            margin-right: 55%;
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
                <div class="timeline-item">
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
    <style>
        body { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); }
        .navbar { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important; }
        .link-card {
            background: white; border-radius: 15px; padding: 1.5rem;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1); transition: all 0.3s ease;
            text-decoration: none; color: inherit; display: block; height: 100%;
        }
        .link-card:hover {
            transform: translateY(-5px); text-decoration: none; color: inherit;
            box-shadow: 0 20px 40px rgba(0,0,0,0.15);
        }
        .link-avatar {
            width: 60px; height: 60px; border-radius: 50%;
            background: linear-gradient(135deg, #667eea, #764ba2);
            display: flex; align-items: center; justify-content: center;
            color: white; font-size: 1.5rem; margin-bottom: 1rem;
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
                <a class="nav-link" href="{{ url_for('links') }}">友链</a>
                <a class="nav-link" href="{{ url_for('about') }}">关于</a>
            </div>
        </div>
    </nav>

    <div class="container py-5">
        <h1 class="mb-5">友情链接</h1>

        <!-- 朋友链接 -->
        {% if friend_links %}
        <h2 class="mb-4">朋友们</h2>
        <div class="row mb-5">
            {% for link in friend_links %}
            <div class="col-md-6 col-lg-4 mb-4">
                <a href="{{ link.url }}" class="link-card" target="_blank">
                    <div class="link-avatar">
                        {% if link.avatar %}
                        <img src="{{ link.avatar }}" alt="{{ link.name }}" class="w-100 h-100 rounded-circle">
                        {% else %}
                        <i class="fas fa-user"></i>
                        {% endif %}
                    </div>
                    <h5 class="mb-2">{{ link.name }}</h5>
                    <p class="text-muted small">{{ link.description or '暂无描述' }}</p>
                </a>
            </div>
            {% endfor %}
        </div>
        {% endif %}

        <!-- 推荐网站 -->
        {% if recommend_links %}
        <h2 class="mb-4">推荐网站</h2>
        <div class="row mb-5">
            {% for link in recommend_links %}
            <div class="col-md-6 col-lg-4 mb-4">
                <a href="{{ link.url }}" class="link-card" target="_blank">
                    <div class="link-avatar">
                        <i class="fas fa-star"></i>
                    </div>
                    <h5 class="mb-2">{{ link.name }}</h5>
                    <p class="text-muted small">{{ link.description or '暂无描述' }}</p>
                </a>
            </div>
            {% endfor %}
        </div>
        {% endif %}

        <!-- 工具网站 -->
        {% if tool_links %}
        <h2 class="mb-4">实用工具</h2>
        <div class="row">
            {% for link in tool_links %}
            <div class="col-md-6 col-lg-4 mb-4">
                <a href="{{ link.url }}" class="link-card" target="_blank">
                    <div class="link-avatar">
                        <i class="fas fa-tools"></i>
                    </div>
                    <h5 class="mb-2">{{ link.name }}</h5>
                    <p class="text-muted small">{{ link.description or '暂无描述' }}</p>
                </a>
            </div>
            {% endfor %}
        </div>
        {% endif %}
    </div>
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
    <style>
        body { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); }
        .navbar { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important; }
        .about-card {
            background: white; border-radius: 15px; padding: 2rem;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1); margin-bottom: 2rem;
        }
        .skill-bar {
            background: #f8f9fa; border-radius: 10px; height: 10px;
            overflow: hidden; margin-bottom: 1rem;
        }
        .skill-progress {
            background: linear-gradient(135deg, #667eea, #764ba2);
            height: 100%; border-radius: 10px; transition: width 1s ease;
        }
        .avatar {
            width: 150px; height: 150px; border-radius: 50%;
            background: linear-gradient(135deg, #667eea, #764ba2);
            display: flex; align-items: center; justify-content: center;
            color: white; font-size: 3rem; margin: 0 auto 2rem;
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
            <div class="col-lg-4">
                <div class="about-card text-center">
                    <div class="avatar">
                        {% if author and author.avatar and author.avatar != 'default.jpg' %}
                        <img src="{{ author.avatar }}" alt="{{ author.username }}" class="w-100 h-100 rounded-circle">
                        {% else %}
                        <i class="fas fa-user"></i>
                        {% endif %}
                    </div>
                    <h3>{{ config.AUTHOR_NAME }}</h3>
                    <p class="text-muted">{{ author.bio if author else '热爱技术的开发者' }}</p>

                    <div class="d-flex justify-content-center gap-3 mt-3">
                        {% if author and author.github %}
                        <a href="https://github.com/{{ author.github }}" class="btn btn-outline-dark" target="_blank">
                            <i class="fab fa-github"></i>
                        </a>
                        {% endif %}
                        {% if author and author.twitter %}
                        <a href="https://twitter.com/{{ author.twitter }}" class="btn btn-outline-info" target="_blank">
                            <i class="fab fa-twitter"></i>
                        </a>
                        {% endif %}
                        {% if author and author.linkedin %}
                        <a href="https://linkedin.com/in/{{ author.linkedin }}" class="btn btn-outline-primary" target="_blank">
                            <i class="fab fa-linkedin"></i>
                        </a>
                        {% endif %}
                        {% if author and author.website %}
                        <a href="{{ author.website }}" class="btn btn-outline-success" target="_blank">
                            <i class="fas fa-globe"></i>
                        </a>
                        {% endif %}
                    </div>
                </div>
            </div>

            <div class="col-lg-8">
                <div class="about-card">
                    <h2 class="mb-4">关于我</h2>
                    <p>你好！我是{{ config.AUTHOR_NAME }}，一名热爱技术的开发者。</p>
                    <p>我专注于Web开发，喜欢学习新技术，乐于分享技术心得和生活感悟。这个博客是我记录学习历程、分享技术经验的地方。</p>
                    <p>希望我的分享能对你有所帮助，也欢迎与我交流讨论！</p>
                </div>

                <div class="about-card">
                    <h3 class="mb-4">技能水平</h3>
                    {% for skill, level in tech_stats.items() %}
                    <div class="mb-3">
                        <div class="d-flex justify-content-between mb-1">
                            <span>{{ skill }}</span>
                            <span>{{ level }}%</span>
                        </div>
                        <div class="skill-bar">
                            <div class="skill-progress" style="width: {{ level }}%;"></div>
                        </div>
                    </div>
                    {% endfor %}
                </div>

                <div class="about-card">
                    <h3 class="mb-4">联系方式</h3>
                    <div class="row">
                        <div class="col-md-6">
                            <p><i class="fas fa-envelope me-2"></i>{{ config.AUTHOR_EMAIL }}</p>
                            <p><i class="fas fa-map-marker-alt me-2"></i>{{ config.AUTHOR_LOCATION }}</p>
                        </div>
                        <div class="col-md-6">
                            {% if author and author.github %}
                            <p><i class="fab fa-github me-2"></i>{{ author.github }}</p>
                            {% endif %}
                            {% if author and author.website %}
                            <p><i class="fas fa-globe me-2"></i>{{ author.website }}</p>
                            {% endif %}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
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
    <style>
        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .login-card {
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            padding: 3rem;
            width: 100%;
            max-width: 400px;
        }
    </style>
</head>
<body>
    <div class="login-card">
        <h2 class="text-center mb-4">管理员登录</h2>
        {% with messages = get_flashed_messages() %}
            {% if messages %}
                {% for message in messages %}
                    <div class="alert alert-danger">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        <form method="POST">
            <div class="mb-3">
                <label for="username" class="form-label">用户名</label>
                <input type="text" class="form-control" id="username" name="username" required>
            </div>
            <div class="mb-3">
                <label for="password" class="form-label">密码</label>
                <input type="password" class="form-control" id="password" name="password" required>
            </div>
            <button type="submit" class="btn btn-primary w-100">登录</button>
        </form>
        <div class="text-center mt-3">
            <a href="{{ url_for('index') }}" class="text-muted">返回首页</a>
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
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="{{ url_for('admin_dashboard') }}">
                <i class="fas fa-cog me-2"></i>管理后台
            </a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="{{ url_for('index') }}">
                    <i class="fas fa-home me-1"></i>返回首页
                </a>
                <a class="nav-link" href="{{ url_for('logout') }}">
                    <i class="fas fa-sign-out-alt me-1"></i>退出
                </a>
            </div>
        </div>
    </nav>

    <div class="container py-4">
        <h1 class="mb-4">管理后台</h1>

        <div class="row">
            <div class="col-md-3 mb-4">
                <div class="card text-center">
                    <div class="card-body">
                        <h3 class="text-primary">{{ dashboard_stats.total_posts }}</h3>
                        <p class="mb-0">总文章数</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3 mb-4">
                <div class="card text-center">
                    <div class="card-body">
                        <h3 class="text-success">{{ dashboard_stats.published_posts }}</h3>
                        <p class="mb-0">已发布</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3 mb-4">
                <div class="card text-center">
                    <div class="card-body">
                        <h3 class="text-warning">{{ dashboard_stats.total_visitors }}</h3>
                        <p class="mb-0">总访客</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3 mb-4">
                <div class="card text-center">
                    <div class="card-body">
                        <h3 class="text-info">{{ dashboard_stats.total_comments }}</h3>
                        <p class="mb-0">总评论</p>
                    </div>
                </div>
            </div>
        </div>

        <div class="row">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5 class="mb-0">最新文章</h5>
                    </div>
                    <div class="card-body">
                        {% for post in recent_posts %}
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <span>{{ post.title }}</span>
                            <small class="text-muted">{{ post.created_at.strftime('%m-%d') }}</small>
                        </div>
                        {% endfor %}
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5 class="mb-0">最新评论</h5>
                    </div>
                    <div class="card-body">
                        {% for comment in recent_comments %}
                        <div class="mb-2">
                            <strong>{{ comment.author_name }}</strong>
                            <p class="mb-1 small">{{ comment.content[:50] }}...</p>
                            <small class="text-muted">{{ comment.created_at.strftime('%m-%d %H:%M') }}</small>
                        </div>
                        {% endfor %}
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
'''

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
