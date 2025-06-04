#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Railway最小化启动脚本
"""

import os
from flask import Flask, render_template_string

def create_minimal_app():
    """创建最小化Flask应用"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'minimal-key')
    
    @app.route('/')
    def index():
        return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>{{ title }}</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body { 
                    font-family: Arial, sans-serif; 
                    max-width: 800px; 
                    margin: 0 auto; 
                    padding: 20px;
                    background: #f5f5f5;
                }
                .container {
                    background: white;
                    padding: 40px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    text-align: center;
                }
                h1 { color: #333; margin-bottom: 10px; }
                .subtitle { color: #666; margin-bottom: 30px; }
                .info { 
                    background: #e8f4fd; 
                    padding: 20px; 
                    border-radius: 5px; 
                    margin: 20px 0;
                    text-align: left;
                }
                .success { color: #28a745; }
                .env-info { font-family: monospace; font-size: 12px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚀 {{ title }}</h1>
                <p class="subtitle">{{ subtitle }}</p>
                
                <div class="info">
                    <h3>✅ 应用状态</h3>
                    <p class="success">Flask应用运行正常！</p>
                    <p><strong>端口:</strong> {{ port }}</p>
                    <p><strong>环境:</strong> {{ env }}</p>
                </div>
                
                <div class="info">
                    <h3>🔧 环境变量</h3>
                    <div class="env-info">
                        {% for key, value in env_vars.items() %}
                        <p><strong>{{ key }}:</strong> {{ value }}</p>
                        {% endfor %}
                    </div>
                </div>
                
                <div class="info">
                    <h3>📋 下一步</h3>
                    <p>1. 确认应用运行正常 ✅</p>
                    <p>2. 配置MySQL数据库连接</p>
                    <p>3. 添加自定义域名</p>
                    <p>4. 部署完整博客功能</p>
                </div>
            </div>
        </body>
        </html>
        ''', 
        title=os.environ.get('BLOG_TITLE', '我的个人博客'),
        subtitle=os.environ.get('BLOG_SUBTITLE', '分享技术与生活'),
        port=os.environ.get('PORT', '8080'),
        env=os.environ.get('FLASK_ENV', 'development'),
        env_vars={
            'DATABASE_URL': os.environ.get('DATABASE_URL', '未设置')[:50] + '...' if os.environ.get('DATABASE_URL') else '未设置',
            'BLOG_DOMAIN': os.environ.get('BLOG_DOMAIN', '未设置'),
            'SECRET_KEY': '已设置' if os.environ.get('SECRET_KEY') else '未设置'
        })
    
    @app.route('/health')
    def health():
        return {'status': 'ok', 'message': 'Application is running'}
    
    return app

def main():
    """主函数"""
    print("🚀 启动Railway最小化应用...")
    
    # 创建应用
    app = create_minimal_app()
    
    # 获取端口
    port = int(os.environ.get('PORT', 8080))
    
    print(f"🌐 应用将在端口 {port} 启动")
    print(f"🔗 PORT环境变量: {os.environ.get('PORT', '未设置')}")
    print(f"🔗 DATABASE_URL: {'已设置' if os.environ.get('DATABASE_URL') else '未设置'}")
    
    # 启动应用
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == '__main__':
    main()
