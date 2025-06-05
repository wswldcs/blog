#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试管理员功能
"""

import requests
import json

def test_admin_features():
    """测试管理员功能"""
    base_url = "http://127.0.0.1:8080"
    
    # 创建会话
    session = requests.Session()
    
    print("🔐 测试管理员登录...")
    
    # 1. 测试登录
    login_data = {
        'username': 'admin',
        'password': 'admin123'
    }
    
    login_response = session.post(f"{base_url}/login", data=login_data)
    print(f"登录状态码: {login_response.status_code}")
    
    if login_response.status_code == 200:
        print("✅ 登录成功")
        
        # 2. 测试系统设置页面
        print("\n⚙️ 测试系统设置页面...")
        settings_response = session.get(f"{base_url}/admin/settings")
        print(f"设置页面状态码: {settings_response.status_code}")
        
        if settings_response.status_code == 200:
            print("✅ 系统设置页面访问成功")
            if "系统设置" in settings_response.text:
                print("✅ 页面内容正确")
        else:
            print("❌ 系统设置页面访问失败")
        
        # 3. 测试账号管理页面
        print("\n👤 测试账号管理页面...")
        account_response = session.get(f"{base_url}/admin/account")
        print(f"账号管理页面状态码: {account_response.status_code}")
        
        if account_response.status_code == 200:
            print("✅ 账号管理页面访问成功")
            if "账号管理" in account_response.text:
                print("✅ 页面内容正确")
        else:
            print("❌ 账号管理页面访问失败")
        
        # 4. 测试关于页面内容
        print("\n📄 测试关于页面...")
        about_response = session.get(f"{base_url}/about")
        print(f"关于页面状态码: {about_response.status_code}")
        
        if about_response.status_code == 200:
            print("✅ 关于页面访问成功")
        else:
            print("❌ 关于页面访问失败")
        
        # 5. 测试设置保存功能
        print("\n💾 测试设置保存功能...")
        settings_data = {
            'site_title': '测试博客标题',
            'site_subtitle': '测试副标题',
            'author_name': 'wswldcs',
            'author_email': 'test@example.com',
            'github_url': 'https://github.com/wswldcs',
            'about_content': '<h2>测试关于内容</h2><p>这是测试内容</p>'
        }
        
        save_response = session.post(f"{base_url}/admin/settings", data=settings_data)
        print(f"设置保存状态码: {save_response.status_code}")
        
        if save_response.status_code == 200 or save_response.status_code == 302:
            print("✅ 设置保存成功")
        else:
            print("❌ 设置保存失败")
    
    else:
        print("❌ 登录失败")
    
    print("\n🎉 测试完成！")

if __name__ == '__main__':
    test_admin_features()
