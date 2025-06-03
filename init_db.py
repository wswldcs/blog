#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库初始化脚本
创建数据库表并插入示例数据
"""

from app import create_app, db
from app.models import (User, Post, Category, Tag, Comment, Link, Project, 
                       Timeline, SiteConfig, Visitor)
from datetime import datetime, date
import os

def init_database():
    """初始化数据库"""
    app = create_app()
    
    with app.app_context():
        print("正在创建数据库表...")
        db.create_all()
        
        # 创建管理员用户
        create_admin_user(app)
        
        # 创建示例数据
        create_sample_data()
        
        print("数据库初始化完成！")

def create_admin_user(app):
    """创建管理员用户"""
    admin = User.query.filter_by(username=app.config['ADMIN_USERNAME']).first()
    if not admin:
        admin = User(
            username=app.config['ADMIN_USERNAME'],
            email=app.config['AUTHOR_EMAIL'],
            is_admin=True
        )
        admin.set_password(app.config['ADMIN_PASSWORD'])
        db.session.add(admin)
        print(f"创建管理员用户: {admin.username}")
    else:
        print("管理员用户已存在")

def create_sample_data():
    """创建示例数据"""
    # 创建分类
    create_categories()
    
    # 创建标签
    create_tags()
    
    # 创建文章
    create_posts()
    
    # 创建友情链接
    create_links()
    
    # 创建项目
    create_projects()
    
    # 创建时间线
    create_timeline()
    
    # 创建网站配置
    create_site_config()
    
    # 提交所有更改
    db.session.commit()

def create_categories():
    """创建分类"""
    categories_data = [
        {'name': '技术分享', 'description': '编程技术相关文章'},
        {'name': '生活随笔', 'description': '日常生活感悟'},
        {'name': '学习笔记', 'description': '学习过程记录'},
        {'name': '项目展示', 'description': '个人项目介绍'},
        {'name': '工具推荐', 'description': '实用工具分享'}
    ]
    
    for cat_data in categories_data:
        if not Category.query.filter_by(name=cat_data['name']).first():
            category = Category(**cat_data)
            db.session.add(category)
            print(f"创建分类: {category.name}")

def create_tags():
    """创建标签"""
    tags_data = [
        'Python', 'Flask', 'Web开发', 'JavaScript', 'CSS', 'HTML',
        '数据库', 'MySQL', 'Git', 'Linux', '算法', '数据结构',
        '机器学习', '人工智能', '前端', '后端', 'API', 'REST',
        '微服务', 'Docker', '云计算', '网络安全', '性能优化',
        '代码规范', '设计模式', '架构设计'
    ]
    
    for tag_name in tags_data:
        if not Tag.query.filter_by(name=tag_name).first():
            tag = Tag(name=tag_name)
            db.session.add(tag)
            print(f"创建标签: {tag.name}")

def create_posts():
    """创建示例文章"""
    admin = User.query.filter_by(is_admin=True).first()
    tech_category = Category.query.filter_by(name='技术分享').first()
    life_category = Category.query.filter_by(name='生活随笔').first()
    
    posts_data = [
        {
            'title': '欢迎来到我的博客',
            'slug': 'welcome-to-my-blog',
            'content': '''# 欢迎来到我的博客

这是我的第一篇博客文章！在这里，我将分享我的技术学习心得、生活感悟和项目经验。

## 关于这个博客

这个博客是使用 **Flask** 框架开发的，具有以下特性：

- 响应式设计，支持移动端
- 支持 Markdown 语法
- 代码高亮显示
- 评论系统
- 标签和分类管理
- 搜索功能

## 技术栈

- **后端**: Python + Flask
- **前端**: Bootstrap 5 + jQuery
- **数据库**: MySQL
- **部署**: GitHub Pages

希望大家喜欢这个博客，欢迎留言交流！

```python
def hello_world():
    print("Hello, World!")
    return "欢迎来到我的博客"
```

感谢您的访问！''',
            'summary': '欢迎来到我的个人博客！这里将分享技术心得和生活感悟。',
            'category': tech_category,
            'tags': ['Python', 'Flask', 'Web开发'],
            'is_published': True,
            'is_featured': True
        },
        {
            'title': 'Flask Web开发入门指南',
            'slug': 'flask-web-development-guide',
            'content': '''# Flask Web开发入门指南

Flask 是一个轻量级的 Python Web 框架，非常适合初学者学习 Web 开发。

## 安装 Flask

```bash
pip install Flask
```

## 创建第一个应用

```python
from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello, Flask!'

if __name__ == '__main__':
    app.run(debug=True)
```

## 路由和视图函数

Flask 使用装饰器来定义路由：

```python
@app.route('/user/<name>')
def user(name):
    return f'Hello, {name}!'
```

## 模板系统

Flask 使用 Jinja2 模板引擎：

```html
<!DOCTYPE html>
<html>
<head>
    <title>{{ title }}</title>
</head>
<body>
    <h1>{{ heading }}</h1>
    <p>{{ content }}</p>
</body>
</html>
```

这只是 Flask 的基础知识，还有很多高级特性等待探索！''',
            'summary': 'Flask 是一个优秀的 Python Web 框架，本文介绍了 Flask 的基础用法。',
            'category': tech_category,
            'tags': ['Python', 'Flask', 'Web开发', '后端'],
            'is_published': True,
            'is_featured': True
        },
        {
            'title': '我的编程学习之路',
            'slug': 'my-programming-journey',
            'content': '''# 我的编程学习之路

回顾我的编程学习历程，从零基础到现在，充满了挑战和收获。

## 初识编程

我第一次接触编程是在大学期间，当时学的是 C 语言。记得第一个程序就是经典的 "Hello, World!"：

```c
#include <stdio.h>

int main() {
    printf("Hello, World!\\n");
    return 0;
}
```

## 转向 Python

后来我发现了 Python，被它的简洁语法深深吸引：

```python
print("Hello, World!")
```

同样的功能，Python 只需要一行代码！

## Web 开发之路

学会 Python 基础后，我开始学习 Web 开发，接触了：

- HTML/CSS/JavaScript
- Flask 框架
- 数据库操作
- 前端框架

## 持续学习

编程是一个需要持续学习的领域，我的学习方法：

1. **多动手实践** - 理论结合实践
2. **阅读优秀代码** - 学习他人的编程思路
3. **参与开源项目** - 提升协作能力
4. **写技术博客** - 总结和分享

## 给初学者的建议

- 不要害怕犯错，错误是最好的老师
- 多写代码，熟能生巧
- 保持好奇心，持续学习
- 加入技术社区，与他人交流

编程改变了我的思维方式，也为我打开了新世界的大门。希望每个初学者都能在编程的路上找到属于自己的乐趣！''',
            'summary': '分享我从零基础到现在的编程学习历程，以及给初学者的一些建议。',
            'category': life_category,
            'tags': ['学习', '编程', '经验分享'],
            'is_published': True,
            'is_featured': False
        }
    ]
    
    for post_data in posts_data:
        if not Post.query.filter_by(slug=post_data['slug']).first():
            # 获取标签
            tag_names = post_data.pop('tags', [])
            tags = Tag.query.filter(Tag.name.in_(tag_names)).all()
            
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
            print(f"创建文章: {post.title}")

def create_links():
    """创建友情链接"""
    links_data = [
        {
            'name': 'GitHub',
            'url': 'https://github.com',
            'description': '全球最大的代码托管平台',
            'sort_order': 1
        },
        {
            'name': 'Stack Overflow',
            'url': 'https://stackoverflow.com',
            'description': '程序员问答社区',
            'sort_order': 2
        },
        {
            'name': 'Python官网',
            'url': 'https://python.org',
            'description': 'Python编程语言官方网站',
            'sort_order': 3
        },
        {
            'name': 'Flask文档',
            'url': 'https://flask.palletsprojects.com',
            'description': 'Flask框架官方文档',
            'sort_order': 4
        }
    ]
    
    for link_data in links_data:
        if not Link.query.filter_by(name=link_data['name']).first():
            link = Link(**link_data)
            db.session.add(link)
            print(f"创建友链: {link.name}")

def create_projects():
    """创建项目"""
    projects_data = [
        {
            'name': '个人博客系统',
            'description': '基于Flask开发的个人博客系统，支持文章管理、评论系统、标签分类等功能。采用响应式设计，支持移动端访问。',
            'tech_stack': 'Python,Flask,MySQL,Bootstrap,jQuery',
            'github_url': 'https://github.com/wswldcs/aublog',
            'demo_url': 'https://wswldcs.github.io',
            'is_featured': True,
            'sort_order': 1
        },
        {
            'name': 'Todo任务管理',
            'description': '简单的任务管理应用，支持任务的增删改查、优先级设置、完成状态管理等功能。',
            'tech_stack': 'Python,Flask,SQLite,HTML,CSS',
            'github_url': 'https://github.com/wswldcs/todo-app',
            'is_featured': False,
            'sort_order': 2
        },
        {
            'name': '天气查询工具',
            'description': '基于第三方API的天气查询工具，支持城市搜索、天气预报、历史天气等功能。',
            'tech_stack': 'JavaScript,HTML,CSS,API',
            'github_url': 'https://github.com/wswldcs/weather-app',
            'demo_url': 'https://wswldcs.github.io/weather-app',
            'is_featured': False,
            'sort_order': 3
        }
    ]
    
    for project_data in projects_data:
        if not Project.query.filter_by(name=project_data['name']).first():
            project = Project(**project_data)
            db.session.add(project)
            print(f"创建项目: {project.name}")

def create_timeline():
    """创建时间线"""
    timeline_data = [
        {
            'title': '开始学习编程',
            'description': '在大学期间第一次接触编程，学习C语言基础语法和算法。',
            'date': date(2021, 9, 1),
            'icon': 'fas fa-graduation-cap',
            'color': 'primary',
            'is_milestone': True,
            'sort_order': 1
        },
        {
            'title': '学习Python',
            'description': '开始学习Python编程语言，被其简洁的语法深深吸引。',
            'date': date(2022, 3, 15),
            'icon': 'fab fa-python',
            'color': 'success',
            'is_milestone': False,
            'sort_order': 2
        },
        {
            'title': 'Web开发入门',
            'description': '学习HTML、CSS、JavaScript，开始接触Web开发技术。',
            'date': date(2022, 8, 20),
            'icon': 'fas fa-code',
            'color': 'info',
            'is_milestone': False,
            'sort_order': 3
        },
        {
            'title': '学习Flask框架',
            'description': '深入学习Flask Web框架，完成第一个Web应用项目。',
            'date': date(2023, 2, 10),
            'icon': 'fas fa-flask',
            'color': 'warning',
            'is_milestone': True,
            'sort_order': 4
        },
        {
            'title': '创建个人博客',
            'description': '使用Flask开发个人博客系统，开始技术分享之路。',
            'date': date(2024, 1, 1),
            'icon': 'fas fa-blog',
            'color': 'danger',
            'is_milestone': True,
            'sort_order': 5
        }
    ]
    
    for timeline_item in timeline_data:
        if not Timeline.query.filter_by(title=timeline_item['title']).first():
            item = Timeline(**timeline_item)
            db.session.add(item)
            print(f"创建时间线: {item.title}")

def create_site_config():
    """创建网站配置"""
    if not SiteConfig.query.first():
        config = SiteConfig(
            site_title='wswldcs的个人博客',
            site_subtitle='记录生活，分享技术，探索世界',
            author_name='wswldcs',
            author_bio='一个热爱编程和技术的开发者，喜欢分享知识，记录成长历程。专注于Python Web开发，对新技术充满好奇心。',
            email='your-email@example.com',
            github_url='https://github.com/wswldcs',
            footer_text='© 2024 wswldcs. All rights reserved. Powered by Flask.'
        )
        db.session.add(config)
        print("创建网站配置")

if __name__ == '__main__':
    init_database()
