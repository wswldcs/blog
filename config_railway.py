#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Railway环境配置
"""

import os
from datetime import timedelta

class RailwayConfig:
    """Railway环境配置"""
    
    # 基本配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'railway-secret-key-change-this'
    
    # 数据库配置 - 优先使用Railway的DATABASE_URL
    DATABASE_URL = os.environ.get('DATABASE_URL')
    
    if DATABASE_URL:
        # Railway MySQL数据库
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
    else:
        # 备用SQLite配置
        SQLALCHEMY_DATABASE_URI = 'sqlite:///blog.db'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # 博客配置
    BLOG_TITLE = os.environ.get('BLOG_TITLE') or '我的个人博客'
    BLOG_SUBTITLE = os.environ.get('BLOG_SUBTITLE') or '分享技术与生活'
    BLOG_DESCRIPTION = os.environ.get('BLOG_DESCRIPTION') or '一个专注于技术分享的个人博客'
    BLOG_KEYWORDS = os.environ.get('BLOG_KEYWORDS') or 'Python,Flask,Web开发,技术博客'
    BLOG_AUTHOR = os.environ.get('BLOG_AUTHOR') or '博主'
    BLOG_EMAIL = os.environ.get('BLOG_EMAIL') or 'admin@example.com'
    
    # 域名配置
    BLOG_DOMAIN = os.environ.get('BLOG_DOMAIN') or 'localhost'
    BLOG_URL = f'https://{BLOG_DOMAIN}'
    
    # 文件上传配置
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'}
    
    # 会话配置
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_SECURE = False  # Railway会处理HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # 安全配置
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600
    
    # 其他配置
    DEBUG = False
    TESTING = False
    
    # API配置
    WEATHER_API_KEY = os.environ.get('WEATHER_API_KEY') or ''
    
    @staticmethod
    def init_app(app):
        """初始化应用配置"""
        # 确保上传目录存在
        upload_folder = app.config['UPLOAD_FOLDER']
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder, exist_ok=True)
