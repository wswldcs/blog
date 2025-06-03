#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from app import create_app, db
from app.models import User, Post, Category, Tag, Link, Project, Timeline, Comment, SiteConfig
import os

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db, 
        'User': User, 
        'Post': Post, 
        'Category': Category, 
        'Tag': Tag,
        'Link': Link,
        'Project': Project,
        'Timeline': Timeline,
        'Comment': Comment,
        'SiteConfig': SiteConfig
    }

def init_database():
    """初始化数据库"""
    with app.app_context():
        db.create_all()
        print("数据库表创建完成")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
