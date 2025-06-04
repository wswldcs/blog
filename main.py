#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Railway主应用 - 简单测试版本
"""

import os
from flask import Flask

print("="*60)
print("🚀 启动Railway主应用 (main.py) - 版本2.0")
print("✅ 这不是railway_simple.py")
print("✅ 这是一个简单的Flask应用，不连接数据库")
print("✅ railway_simple.py已被删除")
print("✅ 强制使用新的Procfile配置")
print("="*60)

# 创建Flask应用
app = Flask(__name__)

@app.route('/')
def hello():
    port = os.environ.get('PORT', '8080')
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Railway测试成功</title>
        <meta charset="utf-8">
        <style>
            body {{ 
                font-family: Arial, sans-serif; 
                text-align: center; 
                padding: 50px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                margin: 0;
            }}
            .container {{
                background: rgba(255,255,255,0.1);
                padding: 40px;
                border-radius: 20px;
                backdrop-filter: blur(10px);
                max-width: 600px;
                margin: 0 auto;
            }}
            h1 {{ margin-bottom: 20px; }}
            .success {{ color: #4CAF50; font-weight: bold; }}
            .info {{ 
                background: rgba(255,255,255,0.2); 
                padding: 20px; 
                border-radius: 10px; 
                margin: 20px 0;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 Railway部署成功！</h1>
            <p class="success">✅ 应用正常运行</p>
            
            <div class="info">
                <h3>📊 应用信息</h3>
                <p><strong>端口:</strong> {port}</p>
                <p><strong>文件:</strong> main.py</p>
                <p><strong>状态:</strong> 运行正常</p>
            </div>
            
            <div class="info">
                <h3>🔧 环境变量</h3>
                <p><strong>PORT:</strong> {os.environ.get('PORT', '未设置')}</p>
                <p><strong>DATABASE_URL:</strong> {'已设置' if os.environ.get('DATABASE_URL') else '未设置'}</p>
                <p><strong>FLASK_ENV:</strong> {os.environ.get('FLASK_ENV', '未设置')}</p>
            </div>
            
            <div class="info">
                <h3>🎯 下一步</h3>
                <p>1. ✅ 基础应用运行成功</p>
                <p>2. 🔄 配置MySQL数据库</p>
                <p>3. 🌐 添加自定义域名</p>
                <p>4. 📝 部署完整博客功能</p>
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/health')
def health():
    return {{
        'status': 'ok', 
        'port': os.environ.get('PORT', '8080'),
        'app': 'main.py',
        'message': 'Railway deployment successful'
    }}

@app.route('/test')
def test():
    return '''
    <h1>🧪 测试页面</h1>
    <p>如果你能看到这个页面，说明应用运行正常！</p>
    <a href="/">返回首页</a>
    '''

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print(f"🌐 应用启动在端口: {port}")
    print(f"🔗 访问地址: http://0.0.0.0:{port}")
    print("✅ main.py 启动成功")
    app.run(host='0.0.0.0', port=port, debug=False)
