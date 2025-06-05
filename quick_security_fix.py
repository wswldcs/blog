#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速安全修复脚本 - 自动更改管理员凭据
"""

import secrets
import string
from rich_blog_app import app, db, User

def generate_secure_credentials():
    """生成安全凭据"""
    # 生成安全用户名
    username_prefix = "admin_"
    username_suffix = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(8))
    secure_username = username_prefix + username_suffix
    
    # 生成强密码
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    secure_password = ''.join(secrets.choice(alphabet) for _ in range(16))
    
    return secure_username, secure_password

def update_admin_security():
    """自动更新管理员安全设置"""
    print("🔒 自动安全修复工具")
    print("=" * 40)
    
    with app.app_context():
        # 查找管理员
        admin = User.query.filter_by(is_admin=True).first()
        if not admin:
            print("❌ 未找到管理员账户！")
            return None, None
        
        print(f"📋 当前管理员信息：")
        print(f"   用户名: {admin.username}")
        print(f"   邮箱: {admin.email}")
        
        # 生成新凭据
        new_username, new_password = generate_secure_credentials()
        
        # 更新管理员信息
        old_username = admin.username
        admin.username = new_username
        admin.set_password(new_password)
        
        # 更新邮箱为更安全的格式
        if admin.email == "admin@blog.com":
            admin.email = f"{new_username}@wswldcs.edu.deal"
        
        try:
            db.session.commit()
            print("\n✅ 安全更新成功！")
            print("\n🔑 新的登录凭据：")
            print(f"   用户名: {new_username}")
            print(f"   密码: {new_password}")
            print(f"   邮箱: {admin.email}")
            
            print("\n⚠️  重要提醒：")
            print("1. 请立即保存这些新凭据到安全的地方")
            print("2. 旧的登录信息已失效")
            print("3. 请使用新凭据重新登录")
            
            # 保存凭据到文件（仅本次）
            with open('new_admin_credentials.txt', 'w', encoding='utf-8') as f:
                f.write(f"新的管理员登录信息\n")
                f.write(f"==================\n")
                f.write(f"用户名: {new_username}\n")
                f.write(f"密码: {new_password}\n")
                f.write(f"邮箱: {admin.email}\n")
                f.write(f"\n⚠️ 请保存后立即删除此文件！\n")
            
            print(f"\n📄 凭据已临时保存到 new_admin_credentials.txt")
            print("   请保存后立即删除此文件！")
            
            return new_username, new_password
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ 更新失败: {str(e)}")
            return None, None

if __name__ == '__main__':
    username, password = update_admin_security()
    
    if username and password:
        print(f"\n🎉 安全修复完成！")
        print(f"🔗 请使用新凭据登录: https://wswldcs.edu.deal/login")
    else:
        print(f"\n❌ 安全修复失败，请手动处理")
