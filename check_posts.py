#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查文章状态
"""

from app import create_app
from app.models import Post

def check_posts():
    """检查文章状态"""
    app = create_app()
    
    with app.app_context():
        posts = Post.query.all()
        
        print("="*50)
        print("文章状态检查")
        print("="*50)
        
        for post in posts:
            print(f"ID: {post.id}")
            print(f"标题: {post.title}")
            print(f"Slug: {post.slug}")
            print(f"已发布: {post.is_published}")
            print(f"精选: {post.is_featured}")
            print(f"作者: {post.author.username if post.author else 'None'}")
            print(f"分类: {post.category.name if post.category else 'None'}")
            print(f"创建时间: {post.created_at}")
            print(f"URL: /post/{post.slug}")
            print("-" * 30)

if __name__ == '__main__':
    check_posts()
