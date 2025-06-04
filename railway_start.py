#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Railway专用启动脚本
"""

import os
import sys
from app import create_app, db
from app.models import User, Category, Tag
from config_railway import RailwayConfig

def init_database():
    """初始化数据库"""
    try:
        # 创建所有表
        db.create_all()
        print("✅ 数据库表创建成功")
        
        # 检查是否需要创建默认数据
        if not User.query.first():
            print("🔧 创建默认管理员用户...")
            admin = User(
                username='admin',
                email='admin@example.com',
                is_admin=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
            
            # 创建默认分类
            if not Category.query.first():
                default_category = Category(
                    name='默认分类',
                    description='默认分类'
                )
                db.session.add(default_category)
            
            # 创建默认标签
            if not Tag.query.first():
                default_tags = [
                    Tag(name='Python', description='Python相关'),
                    Tag(name='Flask', description='Flask框架'),
                    Tag(name='Web开发', description='Web开发技术')
                ]
                for tag in default_tags:
                    db.session.add(tag)
            
            db.session.commit()
            print("✅ 默认数据创建成功")
            print("📝 默认管理员账号: admin")
            print("🔑 默认管理员密码: admin123")
        else:
            print("✅ 数据库已存在数据，跳过初始化")
            
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        return False
    
    return True

def main():
    """主函数"""
    print("🚀 启动Railway博客应用...")
    
    # 创建应用，使用Railway配置
    app = create_app(RailwayConfig)
    
    # 初始化数据库
    with app.app_context():
        if not init_database():
            print("❌ 数据库初始化失败，退出")
            sys.exit(1)
    
    # 获取端口
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    
    print(f"🌐 应用将在端口 {port} 启动")
    print(f"🔧 调试模式: {'开启' if debug else '关闭'}")
    
    # 启动应用
    app.run(host='0.0.0.0', port=port, debug=debug)

if __name__ == '__main__':
    main()
