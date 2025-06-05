#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全更改管理员账户信息脚本
"""

import getpass
import re
from rich_blog_app import app, db, User

def validate_password(password):
    """验证密码强度"""
    if len(password) < 8:
        return False, "密码长度至少8位"
    
    if not re.search(r'[A-Z]', password):
        return False, "密码必须包含大写字母"
    
    if not re.search(r'[a-z]', password):
        return False, "密码必须包含小写字母"
    
    if not re.search(r'[0-9]', password):
        return False, "密码必须包含数字"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "密码必须包含特殊字符"
    
    return True, "密码强度良好"

def change_admin_credentials():
    """安全更改管理员凭据"""
    print("🔐 管理员账户安全更改工具")
    print("=" * 50)
    
    with app.app_context():
        # 查找管理员用户
        admin = User.query.filter_by(is_admin=True).first()
        if not admin:
            print("❌ 未找到管理员账户！")
            return
        
        print(f"📋 当前管理员信息：")
        print(f"   用户名: {admin.username}")
        print(f"   邮箱: {admin.email}")
        print(f"   创建时间: {admin.created_at}")
        print()
        
        # 验证当前密码
        current_password = getpass.getpass("🔑 请输入当前管理员密码: ")
        if not admin.check_password(current_password):
            print("❌ 当前密码错误！")
            return
        
        print("✅ 密码验证成功！")
        print()
        
        # 更改用户名
        new_username = input(f"👤 新用户名 (当前: {admin.username}, 回车跳过): ").strip()
        if new_username:
            # 检查用户名是否已存在
            existing = User.query.filter_by(username=new_username).first()
            if existing and existing.id != admin.id:
                print("❌ 用户名已存在！")
                return
            admin.username = new_username
            print(f"✅ 用户名将更改为: {new_username}")
        
        # 更改邮箱
        new_email = input(f"📧 新邮箱 (当前: {admin.email}, 回车跳过): ").strip()
        if new_email:
            # 简单邮箱格式验证
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', new_email):
                print("❌ 邮箱格式不正确！")
                return
            
            # 检查邮箱是否已存在
            existing = User.query.filter_by(email=new_email).first()
            if existing and existing.id != admin.id:
                print("❌ 邮箱已存在！")
                return
            admin.email = new_email
            print(f"✅ 邮箱将更改为: {new_email}")
        
        # 更改密码
        change_password = input("🔒 是否更改密码？(y/N): ").strip().lower()
        if change_password == 'y':
            while True:
                new_password = getpass.getpass("🔑 新密码: ")
                is_valid, message = validate_password(new_password)
                
                if not is_valid:
                    print(f"❌ {message}")
                    continue
                
                confirm_password = getpass.getpass("🔑 确认新密码: ")
                if new_password != confirm_password:
                    print("❌ 两次输入的密码不一致！")
                    continue
                
                admin.set_password(new_password)
                print("✅ 密码将更改为新密码")
                break
        
        # 确认更改
        print()
        print("📋 即将进行的更改：")
        if new_username:
            print(f"   用户名: {admin.username}")
        if new_email:
            print(f"   邮箱: {admin.email}")
        if change_password == 'y':
            print("   密码: 将更改为新密码")
        
        confirm = input("\n❓ 确认进行更改？(y/N): ").strip().lower()
        if confirm == 'y':
            try:
                db.session.commit()
                print("\n🎉 管理员账户信息更改成功！")
                print("\n⚠️  重要提醒：")
                print("   1. 请记住新的登录凭据")
                print("   2. 建议立即测试登录")
                print("   3. 考虑备份数据库")
                
                # 显示新的登录信息
                print(f"\n📝 新的登录信息：")
                print(f"   用户名: {admin.username}")
                print(f"   邮箱: {admin.email}")
                if change_password == 'y':
                    print("   密码: [已更改]")
                
            except Exception as e:
                db.session.rollback()
                print(f"❌ 更改失败: {str(e)}")
        else:
            print("❌ 操作已取消")

if __name__ == '__main__':
    change_admin_credentials()
