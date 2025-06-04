#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Railway超简单测试应用
"""

import os
from flask import Flask

# 创建Flask应用
app = Flask(__name__)

@app.route('/')
def hello():
    port = os.environ.get('PORT', '8080')
    return f'''
    <html>
    <head><title>Railway测试</title></head>
    <body style="font-family: Arial; text-align: center; padding: 50px;">
        <h1>🚀 Railway简单测试应用运行中！</h1>
        <p>应用正在端口 {port} 运行</p>
        <p>时间: {__import__('datetime').datetime.now()}</p>
        <hr>
        <h3>环境变量检查:</h3>
        <p>PORT: {os.environ.get('PORT', '未设置')}</p>
        <p>DATABASE_URL: {'已设置' if os.environ.get('DATABASE_URL') else '未设置'}</p>
        <p>FLASK_ENV: {os.environ.get('FLASK_ENV', '未设置')}</p>
    </body>
    </html>
    '''

@app.route('/health')
def health():
    return {'status': 'ok', 'port': os.environ.get('PORT', '8080')}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print("="*50)
    print("🚀 启动Railway简单测试应用")
    print(f"📡 端口: {port}")
    print(f"🔗 PORT环境变量: {os.environ.get('PORT', '未设置')}")
    print("✅ 这是simple_test.py，不是railway_simple.py")
    print("="*50)
    app.run(host='0.0.0.0', port=port, debug=False)
