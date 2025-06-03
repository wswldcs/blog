#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移初始化脚本
"""

from flask_migrate import init, migrate, upgrade
from app import create_app, db
import os

def init_migrations():
    """初始化数据库迁移"""
    app = create_app()
    
    with app.app_context():
        # 检查migrations目录是否存在
        if not os.path.exists('migrations'):
            print("初始化数据库迁移...")
            init()
            print("迁移初始化完成")
        else:
            print("迁移目录已存在")
        
        # 创建迁移文件
        print("创建迁移文件...")
        migrate(message='Initial migration')
        print("迁移文件创建完成")
        
        # 应用迁移
        print("应用迁移...")
        upgrade()
        print("迁移应用完成")

if __name__ == '__main__':
    init_migrations()
