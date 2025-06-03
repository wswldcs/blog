#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版启动文件
"""

from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

# 创建Flask应用
app = Flask(__name__)

# 配置
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:1234@localhost/aublog'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化数据库
db = SQLAlchemy(app)

# 简单的模型
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# 路由
@app.route('/')
def index():
    posts = Post.query.order_by(Post.created_at.desc()).limit(5).all()
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>wswldcs的个人博客</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container py-5">
            <div class="text-center mb-5">
                <h1 class="display-4">🎉 博客启动成功！</h1>
                <p class="lead">恭喜！你的个人博客已经成功运行</p>
            </div>
            
            <div class="row">
                <div class="col-md-8 mx-auto">
                    <div class="card">
                        <div class="card-body">
                            <h5 class="card-title">✅ 系统状态</h5>
                            <ul class="list-group list-group-flush">
                                <li class="list-group-item">✓ Flask应用运行正常</li>
                                <li class="list-group-item">✓ 数据库连接成功</li>
                                <li class="list-group-item">✓ 模型创建完成</li>
                                <li class="list-group-item">✓ 路由配置正确</li>
                            </ul>
                        </div>
                    </div>
                    
                    <div class="card mt-4">
                        <div class="card-body">
                            <h5 class="card-title">🚀 下一步操作</h5>
                            <ol>
                                <li>停止当前应用 (Ctrl+C)</li>
                                <li>运行完整版本: <code>python run.py</code></li>
                                <li>访问管理后台: <a href="/admin" target="_blank">http://localhost:5000/admin</a></li>
                                <li>开始创建你的第一篇文章</li>
                            </ol>
                        </div>
                    </div>
                    
                    <div class="card mt-4">
                        <div class="card-body">
                            <h5 class="card-title">📊 数据库信息</h5>
                            <p>文章数量: <strong>{len(posts)}</strong></p>
                            <p>数据库: <strong>aublog</strong></p>
                            <p>状态: <strong>连接正常</strong></p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    '''

@app.route('/test-db')
def test_db():
    try:
        # 创建表
        db.create_all()
        
        # 测试插入数据
        if Post.query.count() == 0:
            test_post = Post(
                title='测试文章',
                content='这是一篇测试文章，用于验证数据库功能是否正常。'
            )
            db.session.add(test_post)
            db.session.commit()
        
        posts = Post.query.all()
        return f'数据库测试成功！共有 {len(posts)} 篇文章。'
    except Exception as e:
        return f'数据库测试失败: {str(e)}'

if __name__ == '__main__':
    print("="*50)
    print("启动简化版博客应用")
    print("="*50)
    print("访问地址: http://localhost:5000")
    print("数据库测试: http://localhost:5000/test-db")
    print("按 Ctrl+C 停止服务器")
    print("="*50)
    
    with app.app_context():
        db.create_all()
    
    app.run(debug=True, host='0.0.0.0', port=5000)
