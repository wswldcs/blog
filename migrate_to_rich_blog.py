#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移脚本：从简单博客迁移到功能丰富的博客系统
"""

import os
import pymysql
from datetime import datetime

def migrate_database():
    """迁移数据库结构"""
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
        
        # 删除所有表，重新创建
        print("🗑️ 清理旧表...")
        
        # 获取所有表名
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        # 禁用外键检查
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        
        # 删除所有表
        for table in tables:
            table_name = table[0]
            cursor.execute(f"DROP TABLE IF EXISTS `{table_name}`")
            print(f"  ✅ 删除表: {table_name}")
        
        # 启用外键检查
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        
        print("✅ 旧表清理完成")
        
        # 创建新的表结构
        print("🔧 创建新表结构...")
        
        # 用户表
        cursor.execute("""
        CREATE TABLE `user` (
            `id` int NOT NULL AUTO_INCREMENT,
            `username` varchar(80) NOT NULL,
            `email` varchar(120) NOT NULL,
            `password_hash` varchar(200) NOT NULL,
            `is_admin` tinyint(1) DEFAULT '0',
            `avatar` varchar(200) DEFAULT 'default.jpg',
            `bio` text,
            `location` varchar(100),
            `website` varchar(200),
            `github` varchar(100),
            `twitter` varchar(100),
            `linkedin` varchar(100),
            `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (`id`),
            UNIQUE KEY `username` (`username`),
            UNIQUE KEY `email` (`email`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        # 分类表
        cursor.execute("""
        CREATE TABLE `category` (
            `id` int NOT NULL AUTO_INCREMENT,
            `name` varchar(80) NOT NULL,
            `description` text,
            `color` varchar(7) DEFAULT '#007bff',
            `icon` varchar(50) DEFAULT 'fas fa-folder',
            `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (`id`),
            UNIQUE KEY `name` (`name`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        # 标签表
        cursor.execute("""
        CREATE TABLE `tag` (
            `id` int NOT NULL AUTO_INCREMENT,
            `name` varchar(50) NOT NULL,
            `color` varchar(7) DEFAULT '#6c757d',
            `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (`id`),
            UNIQUE KEY `name` (`name`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        # 文章表
        cursor.execute("""
        CREATE TABLE `post` (
            `id` int NOT NULL AUTO_INCREMENT,
            `title` varchar(200) NOT NULL,
            `content` text NOT NULL,
            `summary` text,
            `slug` varchar(200) NOT NULL,
            `featured_image` varchar(200),
            `is_published` tinyint(1) DEFAULT '0',
            `is_featured` tinyint(1) DEFAULT '0',
            `view_count` int DEFAULT '0',
            `like_count` int DEFAULT '0',
            `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
            `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            `user_id` int NOT NULL,
            `category_id` int,
            PRIMARY KEY (`id`),
            UNIQUE KEY `slug` (`slug`),
            KEY `user_id` (`user_id`),
            KEY `category_id` (`category_id`),
            CONSTRAINT `post_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`),
            CONSTRAINT `post_ibfk_2` FOREIGN KEY (`category_id`) REFERENCES `category` (`id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        # 文章标签关联表
        cursor.execute("""
        CREATE TABLE `post_tags` (
            `post_id` int NOT NULL,
            `tag_id` int NOT NULL,
            PRIMARY KEY (`post_id`, `tag_id`),
            KEY `tag_id` (`tag_id`),
            CONSTRAINT `post_tags_ibfk_1` FOREIGN KEY (`post_id`) REFERENCES `post` (`id`),
            CONSTRAINT `post_tags_ibfk_2` FOREIGN KEY (`tag_id`) REFERENCES `tag` (`id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        # 评论表
        cursor.execute("""
        CREATE TABLE `comment` (
            `id` int NOT NULL AUTO_INCREMENT,
            `content` text NOT NULL,
            `author_name` varchar(80) NOT NULL,
            `author_email` varchar(120) NOT NULL,
            `author_website` varchar(200),
            `author_ip` varchar(45),
            `is_approved` tinyint(1) DEFAULT '0',
            `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
            `post_id` int NOT NULL,
            PRIMARY KEY (`id`),
            KEY `post_id` (`post_id`),
            CONSTRAINT `comment_ibfk_1` FOREIGN KEY (`post_id`) REFERENCES `post` (`id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        # 项目表
        cursor.execute("""
        CREATE TABLE `project` (
            `id` int NOT NULL AUTO_INCREMENT,
            `name` varchar(100) NOT NULL,
            `description` text NOT NULL,
            `tech_stack` varchar(200),
            `github_url` varchar(200),
            `demo_url` varchar(200),
            `image` varchar(200),
            `is_featured` tinyint(1) DEFAULT '0',
            `status` varchar(20) DEFAULT 'completed',
            `sort_order` int DEFAULT '0',
            `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (`id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        # 链接表
        cursor.execute("""
        CREATE TABLE `link` (
            `id` int NOT NULL AUTO_INCREMENT,
            `name` varchar(100) NOT NULL,
            `url` varchar(200) NOT NULL,
            `description` text,
            `avatar` varchar(200),
            `category` varchar(50) DEFAULT 'friend',
            `is_active` tinyint(1) DEFAULT '1',
            `sort_order` int DEFAULT '0',
            `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (`id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        # 时间线表
        cursor.execute("""
        CREATE TABLE `timeline` (
            `id` int NOT NULL AUTO_INCREMENT,
            `title` varchar(200) NOT NULL,
            `description` text NOT NULL,
            `date` date NOT NULL,
            `icon` varchar(50) DEFAULT 'fas fa-star',
            `color` varchar(7) DEFAULT '#007bff',
            `category` varchar(50) DEFAULT 'education',
            `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (`id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        # 访客表
        cursor.execute("""
        CREATE TABLE `visitor` (
            `id` int NOT NULL AUTO_INCREMENT,
            `ip_address` varchar(45) NOT NULL,
            `user_agent` text,
            `country` varchar(100),
            `city` varchar(100),
            `latitude` float,
            `longitude` float,
            `distance_km` float,
            `visit_count` int DEFAULT '1',
            `first_visit` datetime DEFAULT CURRENT_TIMESTAMP,
            `last_visit` datetime DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (`id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        # 站点配置表
        cursor.execute("""
        CREATE TABLE `site_config` (
            `id` int NOT NULL AUTO_INCREMENT,
            `key` varchar(100) NOT NULL,
            `value` text,
            `description` text,
            `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
            `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            PRIMARY KEY (`id`),
            UNIQUE KEY `key` (`key`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        connection.commit()
        print("✅ 新表结构创建完成")
        
        cursor.close()
        connection.close()
        
        print("🎉 数据库迁移完成！")
        print("现在可以运行 rich_blog_app.py 来初始化数据")
        
        return True
        
    except Exception as e:
        print(f"❌ 数据库迁移失败: {e}")
        return False

if __name__ == '__main__':
    print("="*60)
    print("🔄 开始数据库迁移")
    print("📝 从简单博客迁移到功能丰富的博客系统")
    print("="*60)
    
    if migrate_database():
        print("\n✅ 迁移成功！请运行以下命令启动新博客：")
        print("python rich_blog_app.py")
    else:
        print("\n❌ 迁移失败！请检查数据库连接和权限")
