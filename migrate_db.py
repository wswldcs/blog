#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移脚本
添加缺失的列
"""

import pymysql
from app import create_app

def check_column_exists(cursor, table_name, column_name):
    """检查列是否存在"""
    cursor.execute(f"""
        SELECT COUNT(*) 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = 'aublog' 
        AND TABLE_NAME = '{table_name}' 
        AND COLUMN_NAME = '{column_name}'
    """)
    return cursor.fetchone()[0] > 0

def migrate_database():
    """迁移数据库"""
    print("="*50)
    print("数据库迁移")
    print("="*50)
    
    try:
        # 连接数据库
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='1234',
            database='aublog',
            charset='utf8mb4'
        )
        
        cursor = connection.cursor()
        print("✓ 数据库连接成功")
        
        # 检查并添加缺失的列
        migrations = [
            {
                'table': 'post',
                'column': 'featured_image',
                'sql': 'ALTER TABLE post ADD COLUMN featured_image VARCHAR(200) NULL'
            },
            {
                'table': 'user',
                'column': 'password_hash',
                'sql': 'ALTER TABLE user MODIFY COLUMN password_hash VARCHAR(255)'
            }
        ]
        
        for migration in migrations:
            table = migration['table']
            column = migration['column']
            sql = migration['sql']
            
            if not check_column_exists(cursor, table, column):
                print(f"添加列 {table}.{column}...")
                cursor.execute(sql)
                print(f"✓ 列 {table}.{column} 添加成功")
            else:
                print(f"✓ 列 {table}.{column} 已存在")
        
        # 提交更改
        connection.commit()
        print("✓ 数据库迁移完成")
        
        cursor.close()
        connection.close()
        
        return True
        
    except Exception as e:
        print(f"✗ 数据库迁移失败: {e}")
        return False

def test_migration():
    """测试迁移结果"""
    print("\n测试迁移结果...")
    
    try:
        app = create_app()
        with app.app_context():
            from app.models import Post
            
            # 尝试查询Post
            posts = Post.query.limit(1).all()
            print("✓ Post模型查询成功")
            
            return True
            
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False

def main():
    """主函数"""
    if migrate_database():
        if test_migration():
            print("\n🎉 数据库迁移成功！")
            print("现在可以运行应用了:")
            print("python run.py")
        else:
            print("\n⚠ 迁移完成但测试失败，可能需要重新创建数据库")
    else:
        print("\n❌ 迁移失败，建议重新创建数据库:")
        print("mysql -u root -p1234 -e \"DROP DATABASE IF EXISTS aublog;\"")
        print("mysql -u root -p1234 -e \"CREATE DATABASE aublog CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;\"")
        print("python init_db.py")

if __name__ == '__main__':
    main()
