#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查数据库内容
"""

import pymysql

def check_database():
    """检查数据库内容"""
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
        print("🔗 连接到数据库成功")
        
        # 检查各个表的数据
        tables = [
            ('user', '用户'),
            ('category', '分类'),
            ('tag', '标签'),
            ('post', '文章'),
            ('project', '项目'),
            ('link', '链接'),
            ('timeline', '时间线'),
            ('visitor', '访客')
        ]
        
        for table_name, table_desc in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"📊 {table_desc}表 ({table_name}): {count} 条记录")
            
            if count > 0 and table_name in ['user', 'post', 'category']:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
                rows = cursor.fetchall()
                print(f"   前3条记录:")
                for row in rows:
                    print(f"   {row}")
                print()
        
        cursor.close()
        connection.close()
        
        return True
        
    except Exception as e:
        print(f"❌ 数据库检查失败: {e}")
        return False

if __name__ == '__main__':
    print("="*60)
    print("🔍 检查数据库内容")
    print("="*60)
    check_database()
