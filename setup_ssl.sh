#!/bin/bash

# SSL证书自动配置脚本
# 使用Let's Encrypt为域名配置免费SSL证书

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 配置变量
DOMAIN="www.wswldcs.edu.deal"
EMAIL="admin@wswldcs.edu.deal"  # 请替换为你的邮箱
WEBROOT="/var/www/certbot"

echo -e "${GREEN}开始配置SSL证书...${NC}"

# 检查是否为root用户
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}请使用root权限运行此脚本${NC}"
    exit 1
fi

echo -e "${YELLOW}1. 安装Certbot...${NC}"
apt update
apt install -y certbot python3-certbot-nginx

echo -e "${YELLOW}2. 创建webroot目录...${NC}"
mkdir -p $WEBROOT

echo -e "${YELLOW}3. 配置临时Nginx配置（用于验证）...${NC}"
cat > /etc/nginx/sites-available/temp-ssl << EOF
server {
    listen 80;
    server_name $DOMAIN;
    
    location /.well-known/acme-challenge/ {
        root $WEBROOT;
    }
    
    location / {
        return 200 "SSL setup in progress...";
        add_header Content-Type text/plain;
    }
}
EOF

# 启用临时配置
ln -sf /etc/nginx/sites-available/temp-ssl /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

echo -e "${YELLOW}4. 获取SSL证书...${NC}"
certbot certonly \
    --webroot \
    --webroot-path=$WEBROOT \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email \
    --domains $DOMAIN

if [ $? -eq 0 ]; then
    echo -e "${GREEN}SSL证书获取成功！${NC}"
    
    echo -e "${YELLOW}5. 配置正式Nginx配置...${NC}"
    # 复制我们的配置文件
    cp /var/www/aublog/nginx/aublog.conf /etc/nginx/sites-available/aublog
    
    # 启用正式配置
    rm -f /etc/nginx/sites-enabled/temp-ssl
    ln -sf /etc/nginx/sites-available/aublog /etc/nginx/sites-enabled/
    
    # 测试配置
    nginx -t && systemctl reload nginx
    
    echo -e "${YELLOW}6. 设置自动续期...${NC}"
    # 添加cron任务自动续期
    (crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet && systemctl reload nginx") | crontab -
    
    echo -e "${GREEN}SSL配置完成！${NC}"
    echo -e "${GREEN}你的网站现在可以通过HTTPS访问：${NC}"
    echo -e "${GREEN}https://$DOMAIN${NC}"
    
else
    echo -e "${RED}SSL证书获取失败！${NC}"
    echo -e "${YELLOW}可能的原因：${NC}"
    echo -e "1. 域名DNS解析未正确指向服务器"
    echo -e "2. 防火墙阻止了80端口"
    echo -e "3. 域名不存在或无法访问"
    echo -e ""
    echo -e "${YELLOW}请检查以下内容：${NC}"
    echo -e "1. 确保域名 $DOMAIN 正确解析到此服务器IP"
    echo -e "2. 确保防火墙开放80和443端口"
    echo -e "3. 确保Nginx正在运行"
    
    # 回退到HTTP配置
    echo -e "${YELLOW}回退到HTTP配置...${NC}"
    cat > /etc/nginx/sites-available/aublog-http << EOF
server {
    listen 80;
    server_name $DOMAIN;
    
    root /var/www/aublog;
    
    client_max_body_size 16M;
    
    location /static {
        alias /var/www/aublog/app/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    location /uploads {
        alias /var/www/aublog/app/static/uploads;
        expires 1y;
        add_header Cache-Control "public";
    }
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    access_log /var/log/nginx/aublog.access.log;
    error_log /var/log/nginx/aublog.error.log;
}
EOF
    
    rm -f /etc/nginx/sites-enabled/temp-ssl
    ln -sf /etc/nginx/sites-available/aublog-http /etc/nginx/sites-enabled/
    nginx -t && systemctl reload nginx
    
    echo -e "${YELLOW}HTTP配置已启用，网站可通过以下地址访问：${NC}"
    echo -e "${YELLOW}http://$DOMAIN${NC}"
    echo -e "${YELLOW}稍后可以重新运行此脚本获取SSL证书${NC}"
fi

echo -e "${GREEN}配置完成！${NC}"
