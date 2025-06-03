#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
域名检查工具
"""

import socket
import subprocess
import sys

def check_domain(domain):
    """检查域名解析状态"""
    print(f"检查域名: {domain}")
    print("=" * 50)
    
    # 1. 检查域名解析
    try:
        ip = socket.gethostbyname(domain)
        print(f"✅ 域名解析成功: {domain} -> {ip}")
        return ip
    except socket.gaierror as e:
        print(f"❌ 域名解析失败: {e}")
        return None

def check_port(ip, port):
    """检查端口是否开放"""
    if not ip:
        return False
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((ip, port))
        sock.close()
        
        if result == 0:
            print(f"✅ 端口 {port} 开放")
            return True
        else:
            print(f"❌ 端口 {port} 关闭")
            return False
    except Exception as e:
        print(f"❌ 端口检查失败: {e}")
        return False

def run_nslookup(domain):
    """运行nslookup命令"""
    try:
        result = subprocess.run(['nslookup', domain], 
                              capture_output=True, text=True, timeout=10)
        print(f"\nnslookup结果:")
        print(result.stdout)
        if result.stderr:
            print(f"错误: {result.stderr}")
    except Exception as e:
        print(f"nslookup失败: {e}")

def main():
    domains = [
        'www.wswldcs.edu.deal',
        'wswldcs.edu.deal',
        'wswldcs.blog'
    ]
    
    for domain in domains:
        print(f"\n{'='*60}")
        ip = check_domain(domain)
        
        if ip:
            # 检查常用端口
            check_port(ip, 80)   # HTTP
            check_port(ip, 443)  # HTTPS
            check_port(ip, 22)   # SSH
        
        # 运行nslookup
        run_nslookup(domain)
        print()

if __name__ == '__main__':
    main()
