#!/bin/bash

# 博客部署脚本
# 使用方法: ./deploy.sh

set -e

echo "开始部署博客..."

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 配置变量
APP_NAME="aublog"
APP_DIR="/var/www/$APP_NAME"
SERVICE_NAME="aublog"
NGINX_CONF="/etc/nginx/sites-available/$APP_NAME"
DOMAIN="sub.wswldcs.edu.deal"

# 检查是否为root用户
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}请使用root权限运行此脚本${NC}"
    exit 1
fi

echo -e "${YELLOW}1. 更新系统包...${NC}"
apt update && apt upgrade -y

echo -e "${YELLOW}2. 安装必要的软件包...${NC}"
apt install -y python3 python3-pip python3-venv nginx mysql-server git supervisor

echo -e "${YELLOW}3. 创建应用目录...${NC}"
mkdir -p $APP_DIR
cd $APP_DIR

echo -e "${YELLOW}4. 克隆代码仓库...${NC}"
if [ -d ".git" ]; then
    git pull origin main
else
    git clone https://github.com/wswldcs/blog.git .
fi

echo -e "${YELLOW}5. 创建Python虚拟环境...${NC}"
python3 -m venv venv
source venv/bin/activate

echo -e "${YELLOW}6. 安装Python依赖...${NC}"
pip install -r requirements.txt

echo -e "${YELLOW}7. 配置环境变量...${NC}"
cat > .env << EOF
FLASK_APP=run.py
FLASK_ENV=production
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=aublog_user
MYSQL_PASSWORD=$(openssl rand -base64 32)
MYSQL_DATABASE=aublog
BLOG_TITLE=我的个人博客
BLOG_SUBTITLE=分享技术与生活
BLOG_DOMAIN=$DOMAIN
EOF

echo -e "${YELLOW}8. 配置MySQL数据库...${NC}"
MYSQL_ROOT_PASSWORD=$(openssl rand -base64 32)
MYSQL_APP_PASSWORD=$(grep MYSQL_PASSWORD .env | cut -d'=' -f2)

mysql -e "CREATE DATABASE IF NOT EXISTS aublog CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql -e "CREATE USER IF NOT EXISTS 'aublog_user'@'localhost' IDENTIFIED BY '$MYSQL_APP_PASSWORD';"
mysql -e "GRANT ALL PRIVILEGES ON aublog.* TO 'aublog_user'@'localhost';"
mysql -e "FLUSH PRIVILEGES;"

echo -e "${YELLOW}9. 初始化数据库...${NC}"
export FLASK_APP=run.py
export FLASK_ENV=production
source .env
python3 -c "
from app import create_app, db
from app.models import User, Category, Tag, Post
import os

app = create_app('config_production.ProductionConfig')
with app.app_context():
    db.create_all()
    
    # 创建默认管理员用户
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            email='admin@example.com',
            is_admin=True
        )
        admin.set_password('admin123')  # 请在部署后立即修改密码
        db.session.add(admin)
        
        # 创建默认分类
        if not Category.query.first():
            default_category = Category(name='默认分类', description='默认分类')
            db.session.add(default_category)
        
        db.session.commit()
        print('数据库初始化完成')
"

echo -e "${YELLOW}10. 配置Gunicorn...${NC}"
cat > gunicorn.conf.py << EOF
bind = "127.0.0.1:8000"
workers = 4
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2
max_requests = 1000
max_requests_jitter = 100
preload_app = True
daemon = False
user = "www-data"
group = "www-data"
pidfile = "/var/run/gunicorn/aublog.pid"
accesslog = "/var/log/aublog/access.log"
errorlog = "/var/log/aublog/error.log"
loglevel = "info"
EOF

echo -e "${YELLOW}11. 配置Supervisor...${NC}"
mkdir -p /var/log/aublog
mkdir -p /var/run/gunicorn
chown -R www-data:www-data /var/log/aublog
chown -R www-data:www-data /var/run/gunicorn

cat > /etc/supervisor/conf.d/$SERVICE_NAME.conf << EOF
[program:$SERVICE_NAME]
command=$APP_DIR/venv/bin/gunicorn -c $APP_DIR/gunicorn.conf.py run:app
directory=$APP_DIR
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/aublog/supervisor.log
environment=FLASK_ENV=production
EOF

echo -e "${YELLOW}12. 配置Nginx...${NC}"
cat > $NGINX_CONF << EOF
server {
    listen 80;
    server_name $DOMAIN;
    
    # 重定向到HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $DOMAIN;
    
    # SSL配置 (需要配置SSL证书)
    # ssl_certificate /path/to/certificate.crt;
    # ssl_certificate_key /path/to/private.key;
    
    # 临时使用HTTP (生产环境请配置SSL)
    listen 80;
    
    root $APP_DIR;
    
    # 静态文件
    location /static {
        alias $APP_DIR/app/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # 上传文件
    location /uploads {
        alias $APP_DIR/app/static/uploads;
        expires 1y;
        add_header Cache-Control "public";
    }
    
    # 应用代理
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
    
    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # 日志
    access_log /var/log/nginx/$APP_NAME.access.log;
    error_log /var/log/nginx/$APP_NAME.error.log;
}
EOF

# 启用站点
ln -sf $NGINX_CONF /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

echo -e "${YELLOW}13. 设置文件权限...${NC}"
chown -R www-data:www-data $APP_DIR
chmod -R 755 $APP_DIR

echo -e "${YELLOW}14. 启动服务...${NC}"
supervisorctl reread
supervisorctl update
supervisorctl start $SERVICE_NAME

nginx -t && systemctl reload nginx
systemctl enable nginx
systemctl enable supervisor

echo -e "${GREEN}部署完成！${NC}"
echo -e "${GREEN}访问地址: http://$DOMAIN${NC}"
echo -e "${YELLOW}默认管理员账号: admin${NC}"
echo -e "${YELLOW}默认管理员密码: admin123 (请立即修改)${NC}"
echo -e "${YELLOW}管理后台: http://$DOMAIN/manage${NC}"

echo -e "${YELLOW}注意事项:${NC}"
echo -e "1. 请立即修改管理员密码"
echo -e "2. 配置SSL证书以启用HTTPS"
echo -e "3. 定期备份数据库"
echo -e "4. 监控日志文件: /var/log/aublog/"
