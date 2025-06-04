#!/bin/bash

# 博客应用启动脚本

echo "🚀 启动博客应用..."

# 设置环境变量
export FLASK_ENV=production
export PORT=${PORT:-8080}

# 启动应用
python rich_blog_app.py
