#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生产环境配置
"""

import os
from datetime import timedelta

class ProductionConfig:
    """生产环境配置"""
    
    # 基本配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-production-secret-key-change-this'
    
    # 数据库配置
    MYSQL_HOST = os.environ.get('MYSQL_HOST') or 'localhost'
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT') or 3306)
    MYSQL_USER = os.environ.get('MYSQL_USER') or 'root'
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD') or '1234'
    MYSQL_DATABASE = os.environ.get('MYSQL_DATABASE') or 'aublog'
    
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?charset=utf8mb4'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'connect_args': {
            'connect_timeout': 10,
            'charset': 'utf8mb4'
        }
    }
    
    # 博客配置
    BLOG_TITLE = os.environ.get('BLOG_TITLE') or '我的个人博客'
    BLOG_SUBTITLE = os.environ.get('BLOG_SUBTITLE') or '分享技术与生活'
    BLOG_DESCRIPTION = os.environ.get('BLOG_DESCRIPTION') or '一个专注于技术分享的个人博客'
    BLOG_KEYWORDS = os.environ.get('BLOG_KEYWORDS') or 'Python,Flask,Web开发,技术博客'
    BLOG_AUTHOR = os.environ.get('BLOG_AUTHOR') or '博主'
    BLOG_EMAIL = os.environ.get('BLOG_EMAIL') or 'admin@example.com'
    
    # 域名配置
    BLOG_DOMAIN = os.environ.get('BLOG_DOMAIN') or 'sub.wswldcs.edu.deal'
    BLOG_URL = f'https://{BLOG_DOMAIN}'

    # 允许的主机名
    ALLOWED_HOSTS = [
        'sub.wswldcs.edu.deal',
        'wswldcs.blog.io',
        'localhost',
        '127.0.0.1'
    ]
    
    # 文件上传配置
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'}
    
    # 会话配置
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_SECURE = True  # 生产环境使用HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # 安全配置
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600
    
    # 缓存配置
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300
    
    # 日志配置
    LOG_LEVEL = 'INFO'
    LOG_FILE = '/var/log/aublog/app.log'
    
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
        
        # 配置日志
        import logging
        from logging.handlers import RotatingFileHandler
        
        if not app.debug and not app.testing:
            # 确保日志目录存在
            log_dir = os.path.dirname(app.config['LOG_FILE'])
            if not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
            
            # 配置文件日志
            file_handler = RotatingFileHandler(
                app.config['LOG_FILE'],
                maxBytes=10240000,  # 10MB
                backupCount=10
            )
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
            ))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)
            
            app.logger.setLevel(logging.INFO)
            app.logger.info('博客应用启动')
