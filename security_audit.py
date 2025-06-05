#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
博客安全审计和加固脚本
"""

import os
import re
import hashlib
import secrets
from rich_blog_app import app, db, User

def generate_secure_password(length=16):
    """生成安全密码"""
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password

def check_security_issues():
    """检查安全问题"""
    print("🔍 博客安全审计报告")
    print("=" * 60)
    
    issues = []
    recommendations = []
    
    with app.app_context():
        # 检查管理员账户
        admin = User.query.filter_by(is_admin=True).first()
        if admin:
            print(f"👤 管理员账户检查：")
            print(f"   用户名: {admin.username}")
            print(f"   邮箱: {admin.email}")
            
            # 检查弱用户名
            weak_usernames = ['admin', 'administrator', 'root', 'user', 'test']
            if admin.username.lower() in weak_usernames:
                issues.append(f"❌ 用户名 '{admin.username}' 过于常见，容易被猜测")
                recommendations.append("更改为不易猜测的用户名")
            
            # 检查密码（通过尝试常见密码）
            weak_passwords = [
                'admin123', 'password', '123456', 'admin', 'root', 
                'password123', '12345678', 'qwerty', 'abc123'
            ]
            
            for weak_pwd in weak_passwords:
                if admin.check_password(weak_pwd):
                    issues.append(f"❌ 使用了弱密码: {weak_pwd}")
                    recommendations.append("立即更改为强密码（至少12位，包含大小写字母、数字、特殊字符）")
                    break
        
        # 检查数据库配置
        print(f"\n🗄️  数据库配置检查：")
        db_url = app.config.get('SQLALCHEMY_DATABASE_URI', '')
        if 'password=1234' in db_url or 'password=root' in db_url:
            issues.append("❌ 数据库使用弱密码")
            recommendations.append("更改数据库密码为强密码")
        
        # 检查调试模式
        if app.debug:
            issues.append("❌ 生产环境启用了调试模式")
            recommendations.append("在生产环境中关闭调试模式")
        
        # 检查密钥配置
        secret_key = app.config.get('SECRET_KEY', '')
        if not secret_key or len(secret_key) < 32:
            issues.append("❌ SECRET_KEY 过短或未设置")
            recommendations.append("设置长度至少32位的随机SECRET_KEY")
        
        # 检查文件权限（如果在Linux环境）
        if os.name == 'posix':
            app_file = 'rich_blog_app.py'
            if os.path.exists(app_file):
                stat = os.stat(app_file)
                if stat.st_mode & 0o077:
                    issues.append("❌ 应用文件权限过于宽松")
                    recommendations.append("设置适当的文件权限 (chmod 644)")
    
    # 输出结果
    print(f"\n📊 安全检查结果：")
    if issues:
        print(f"🚨 发现 {len(issues)} 个安全问题：")
        for i, issue in enumerate(issues, 1):
            print(f"   {i}. {issue}")
        
        print(f"\n💡 安全建议：")
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec}")
    else:
        print("✅ 未发现明显的安全问题")
    
    return issues, recommendations

def generate_security_config():
    """生成安全配置"""
    print(f"\n🔧 生成安全配置：")
    
    # 生成强密码
    strong_password = generate_secure_password(16)
    print(f"💪 建议的强密码: {strong_password}")
    
    # 生成SECRET_KEY
    secret_key = secrets.token_hex(32)
    print(f"🔑 建议的SECRET_KEY: {secret_key}")
    
    # 生成数据库密码
    db_password = generate_secure_password(20)
    print(f"🗄️  建议的数据库密码: {db_password}")
    
    return {
        'admin_password': strong_password,
        'secret_key': secret_key,
        'db_password': db_password
    }

def create_security_checklist():
    """创建安全检查清单"""
    checklist = """
🔒 博客安全检查清单
==================

□ 立即更改管理员用户名和密码
□ 使用强密码（至少12位，包含大小写字母、数字、特殊字符）
□ 更改数据库密码
□ 设置强SECRET_KEY
□ 关闭生产环境的调试模式
□ 定期备份数据库
□ 监控登录日志
□ 启用HTTPS（SSL证书）
□ 设置防火墙规则
□ 定期更新系统和依赖包
□ 限制管理后台访问IP（如果可能）
□ 启用登录失败锁定机制
□ 定期更改密码
□ 删除或隐藏敏感信息的代码注释

🚨 紧急安全措施（立即执行）：
1. 运行 python change_admin_credentials.py 更改管理员凭据
2. 更改数据库密码
3. 检查GitHub仓库，确保没有敏感信息
4. 监控服务器访问日志
"""
    
    with open('security_checklist.txt', 'w', encoding='utf-8') as f:
        f.write(checklist)
    
    print(f"\n📋 安全检查清单已保存到 security_checklist.txt")
    return checklist

if __name__ == '__main__':
    # 执行安全审计
    issues, recommendations = check_security_issues()
    
    # 生成安全配置
    security_config = generate_security_config()
    
    # 创建安全检查清单
    create_security_checklist()
    
    print(f"\n⚠️  重要提醒：")
    print("1. 立即更改默认的管理员凭据")
    print("2. 使用生成的强密码")
    print("3. 定期检查和更新安全设置")
    print("4. 监控异常登录活动")
    print("\n🔧 下一步操作：")
    print("   运行: python change_admin_credentials.py")
