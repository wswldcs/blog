#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自定义管理员凭据设置工具
允许用户自由设置用户名和密码
"""

import getpass
import re
from rich_blog_app import app, db, User

def validate_username(username):
    """验证用户名"""
    if len(username) < 3:
        return False, "用户名长度至少3位"
    
    if len(username) > 50:
        return False, "用户名长度不能超过50位"
    
    if not re.match(r'^[a-zA-Z0-9_-]+$', username):
        return False, "用户名只能包含字母、数字、下划线和连字符"
    
    if username.lower() in ['admin', 'administrator', 'root', 'user', 'test', 'guest']:
        return False, f"用户名 '{username}' 过于常见，建议使用更独特的名称"
    
    return True, "用户名格式正确"

def validate_password(password):
    """验证密码强度"""
    issues = []
    
    if len(password) < 8:
        issues.append("密码长度至少8位")
    
    if not re.search(r'[a-z]', password):
        issues.append("需要包含小写字母")
    
    if not re.search(r'[A-Z]', password):
        issues.append("需要包含大写字母")
    
    if not re.search(r'[0-9]', password):
        issues.append("需要包含数字")
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>_+-=]', password):
        issues.append("建议包含特殊字符")
    
    # 检查常见弱密码
    weak_passwords = [
        'password', '123456', '12345678', 'qwerty', 'abc123',
        'password123', 'admin123', '111111', '000000', 'iloveyou'
    ]
    
    if password.lower() in weak_passwords:
        issues.append("这是常见的弱密码，请选择更安全的密码")
    
    if issues:
        return False, "; ".join(issues)
    
    # 计算密码强度
    strength = 0
    if len(password) >= 8: strength += 1
    if len(password) >= 12: strength += 1
    if re.search(r'[a-z]', password): strength += 1
    if re.search(r'[A-Z]', password): strength += 1
    if re.search(r'[0-9]', password): strength += 1
    if re.search(r'[!@#$%^&*(),.?":{}|<>_+-=]', password): strength += 1
    
    strength_levels = {
        0: "极弱",
        1: "很弱", 
        2: "弱",
        3: "一般",
        4: "良好",
        5: "强",
        6: "很强"
    }
    
    return True, f"密码强度: {strength_levels.get(strength, '未知')}"

def validate_email(email):
    """验证邮箱格式"""
    if not email:
        return True, "邮箱为可选项"
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False, "邮箱格式不正确"
    
    return True, "邮箱格式正确"

def custom_admin_setup():
    """自定义管理员设置"""
    print("🔧 自定义管理员凭据设置工具")
    print("=" * 50)
    print("您可以自由设置想要的用户名和密码")
    print()
    
    with app.app_context():
        # 查找当前管理员
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
        while True:
            current_password = getpass.getpass("🔑 请输入当前管理员密码进行验证: ")
            if admin.check_password(current_password):
                print("✅ 密码验证成功！")
                break
            else:
                print("❌ 密码错误，请重试")
                retry = input("是否继续尝试？(y/N): ").strip().lower()
                if retry != 'y':
                    print("操作已取消")
                    return
        
        print()
        print("🎯 现在您可以设置新的管理员信息")
        print()
        
        # 设置新用户名
        while True:
            new_username = input(f"👤 请输入新用户名 (当前: {admin.username}): ").strip()
            
            if not new_username:
                print("❌ 用户名不能为空")
                continue
            
            # 验证用户名
            is_valid, message = validate_username(new_username)
            if not is_valid:
                print(f"❌ {message}")
                continue
            
            # 检查是否已存在
            existing = User.query.filter_by(username=new_username).first()
            if existing and existing.id != admin.id:
                print(f"❌ 用户名 '{new_username}' 已存在，请选择其他用户名")
                continue
            
            print(f"✅ {message}")
            break
        
        # 设置新密码
        while True:
            print(f"\n🔒 请设置新密码")
            print("密码要求：至少8位，包含大小写字母、数字，建议包含特殊字符")
            new_password = getpass.getpass("🔑 请输入新密码: ")
            
            if not new_password:
                print("❌ 密码不能为空")
                continue
            
            # 验证密码
            is_valid, message = validate_password(new_password)
            if not is_valid:
                print(f"❌ {message}")
                continue
            
            # 确认密码
            confirm_password = getpass.getpass("🔑 请再次输入新密码确认: ")
            if new_password != confirm_password:
                print("❌ 两次输入的密码不一致，请重试")
                continue
            
            print(f"✅ {message}")
            break
        
        # 设置新邮箱（可选）
        while True:
            new_email = input(f"📧 请输入新邮箱 (当前: {admin.email}, 回车保持不变): ").strip()
            
            if not new_email:
                new_email = admin.email
                break
            
            # 验证邮箱
            is_valid, message = validate_email(new_email)
            if not is_valid:
                print(f"❌ {message}")
                continue
            
            # 检查是否已存在
            existing = User.query.filter_by(email=new_email).first()
            if existing and existing.id != admin.id:
                print(f"❌ 邮箱 '{new_email}' 已存在，请选择其他邮箱")
                continue
            
            print(f"✅ {message}")
            break
        
        # 显示即将更改的信息
        print()
        print("📋 即将更改的管理员信息：")
        print(f"   用户名: {admin.username} → {new_username}")
        print(f"   密码: [已设置新密码]")
        print(f"   邮箱: {admin.email} → {new_email}")
        print()
        
        # 最终确认
        confirm = input("❓ 确认进行更改？(y/N): ").strip().lower()
        if confirm != 'y':
            print("❌ 操作已取消")
            return
        
        # 执行更改
        try:
            admin.username = new_username
            admin.set_password(new_password)
            admin.email = new_email
            
            db.session.commit()
            
            print()
            print("🎉 管理员信息更改成功！")
            print()
            print("🔑 新的登录信息：")
            print(f"   用户名: {new_username}")
            print(f"   密码: [您设置的密码]")
            print(f"   邮箱: {new_email}")
            print()
            print("⚠️  重要提醒：")
            print("1. 请记住新的登录凭据")
            print("2. 旧的登录信息已失效")
            print("3. 建议立即测试登录")
            print("4. 请妥善保管新的凭据")
            print()
            print(f"🔗 登录地址: https://wswldcs.edu.deal/login")
            
            # 询问是否保存到文件
            save_to_file = input("\n💾 是否将新凭据保存到临时文件？(y/N): ").strip().lower()
            if save_to_file == 'y':
                with open('my_admin_credentials.txt', 'w', encoding='utf-8') as f:
                    f.write(f"我的管理员登录信息\n")
                    f.write(f"==================\n")
                    f.write(f"用户名: {new_username}\n")
                    f.write(f"密码: {new_password}\n")
                    f.write(f"邮箱: {new_email}\n")
                    f.write(f"更新时间: {admin.created_at}\n")
                    f.write(f"\n⚠️ 请保存后立即删除此文件！\n")
                
                print("📄 凭据已保存到 my_admin_credentials.txt")
                print("   请保存后立即删除此文件！")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ 更改失败: {str(e)}")

def show_password_tips():
    """显示密码设置建议"""
    print("\n💡 密码设置建议：")
    print("1. 使用您容易记住但他人难以猜测的密码")
    print("2. 可以使用有意义的短语 + 数字 + 特殊字符")
    print("3. 例如: MyBlog2025! 或 DataAnalyst@2025")
    print("4. 避免使用生日、姓名等个人信息")
    print("5. 定期更换密码（建议3-6个月）")

if __name__ == '__main__':
    show_password_tips()
    print()
    custom_admin_setup()
