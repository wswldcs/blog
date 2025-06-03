# 部署指南

## 🚀 快速部署到云服务器

### 前提条件

1. **云服务器**：Ubuntu 20.04+ 或 CentOS 8+
2. **域名**：`sub.wswldcs.edu.deal` 已解析到服务器IP
3. **端口**：开放80、443、22端口

### 一键部署

```bash
# 1. 连接到服务器
ssh root@YOUR_SERVER_IP

# 2. 下载部署脚本
wget https://raw.githubusercontent.com/wswldcs/blog/main/deploy.sh

# 3. 运行部署脚本
chmod +x deploy.sh
./deploy.sh

# 4. 配置SSL证书（可选但推荐）
chmod +x setup_ssl.sh
./setup_ssl.sh
```

### 手动部署步骤

#### 1. 系统准备

```bash
# 更新系统
apt update && apt upgrade -y

# 安装必要软件
apt install -y python3 python3-pip python3-venv nginx mysql-server git supervisor
```

#### 2. 创建数据库

```bash
# 登录MySQL
mysql -u root -p

# 创建数据库和用户
CREATE DATABASE aublog CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'aublog_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON aublog.* TO 'aublog_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

#### 3. 部署应用

```bash
# 创建应用目录
mkdir -p /var/www/aublog
cd /var/www/aublog

# 克隆代码
git clone https://github.com/wswldcs/blog.git .

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
nano .env  # 编辑配置
```

#### 4. 初始化数据库

```bash
# 设置环境变量
export FLASK_APP=run.py
export FLASK_ENV=production

# 初始化数据库
python3 init_db.py
```

#### 5. 配置Gunicorn

```bash
# 创建Gunicorn配置
cat > gunicorn.conf.py << EOF
bind = "127.0.0.1:8000"
workers = 4
worker_class = "sync"
timeout = 30
keepalive = 2
max_requests = 1000
preload_app = True
user = "www-data"
group = "www-data"
pidfile = "/var/run/gunicorn/aublog.pid"
accesslog = "/var/log/aublog/access.log"
errorlog = "/var/log/aublog/error.log"
loglevel = "info"
EOF
```

#### 6. 配置Supervisor

```bash
# 创建日志目录
mkdir -p /var/log/aublog
mkdir -p /var/run/gunicorn
chown -R www-data:www-data /var/log/aublog
chown -R www-data:www-data /var/run/gunicorn

# 创建Supervisor配置
cat > /etc/supervisor/conf.d/aublog.conf << EOF
[program:aublog]
command=/var/www/aublog/venv/bin/gunicorn -c /var/www/aublog/gunicorn.conf.py run:app
directory=/var/www/aublog
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/aublog/supervisor.log
environment=FLASK_ENV=production
EOF

# 重启Supervisor
supervisorctl reread
supervisorctl update
supervisorctl start aublog
```

#### 7. 配置Nginx

```bash
# 复制Nginx配置
cp /var/www/aublog/nginx/aublog.conf /etc/nginx/sites-available/aublog

# 启用站点
ln -sf /etc/nginx/sites-available/aublog /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# 测试配置
nginx -t

# 重启Nginx
systemctl reload nginx
```

#### 8. 配置SSL证书

```bash
# 安装Certbot
apt install -y certbot python3-certbot-nginx

# 获取证书
certbot --nginx -d sub.wswldcs.edu.deal

# 设置自动续期
crontab -e
# 添加以下行：
# 0 12 * * * /usr/bin/certbot renew --quiet && systemctl reload nginx
```

## 🐳 Docker部署

### 使用Docker Compose

```bash
# 1. 克隆代码
git clone https://github.com/wswldcs/blog.git
cd blog

# 2. 配置环境变量
cp .env.example .env
nano .env

# 3. 启动服务
docker-compose up -d

# 4. 查看日志
docker-compose logs -f
```

### 单独使用Docker

```bash
# 1. 构建镜像
docker build -t aublog .

# 2. 运行容器
docker run -d \
  --name aublog \
  -p 8000:8000 \
  -e MYSQL_HOST=your_mysql_host \
  -e MYSQL_PASSWORD=your_password \
  aublog
```

## 🌐 域名配置

### DNS设置

在你的域名管理面板中：

1. **A记录**：`sub.wswldcs.edu.deal` → `YOUR_SERVER_IP`
2. **CNAME记录**（可选）：`www.sub.wswldcs.edu.deal` → `sub.wswldcs.edu.deal`

### 验证域名解析

```bash
# 检查域名解析
nslookup sub.wswldcs.edu.deal
dig sub.wswldcs.edu.deal

# 检查网站访问
curl -I http://sub.wswldcs.edu.deal
```

## 🔧 配置管理

### 环境变量说明

| 变量 | 说明 | 示例 |
|------|------|------|
| `SECRET_KEY` | Flask密钥 | `your-secret-key` |
| `MYSQL_HOST` | 数据库主机 | `localhost` |
| `MYSQL_PASSWORD` | 数据库密码 | `your-password` |
| `BLOG_DOMAIN` | 博客域名 | `sub.wswldcs.edu.deal` |

### 默认管理员账号

- **用户名**：`admin`
- **密码**：`admin123`
- **管理后台**：`https://sub.wswldcs.edu.deal/manage`

⚠️ **重要**：部署后请立即修改管理员密码！

## 📊 监控和维护

### 查看日志

```bash
# 应用日志
tail -f /var/log/aublog/app.log

# Nginx日志
tail -f /var/log/nginx/aublog.access.log
tail -f /var/log/nginx/aublog.error.log

# Supervisor日志
tail -f /var/log/aublog/supervisor.log
```

### 服务管理

```bash
# 重启应用
supervisorctl restart aublog

# 重启Nginx
systemctl reload nginx

# 查看服务状态
supervisorctl status
systemctl status nginx
```

### 数据库备份

```bash
# 备份数据库
mysqldump -u aublog_user -p aublog > backup_$(date +%Y%m%d_%H%M%S).sql

# 恢复数据库
mysql -u aublog_user -p aublog < backup_file.sql
```

## 🚨 故障排除

### 常见问题

1. **502 Bad Gateway**
   - 检查Gunicorn是否运行：`supervisorctl status aublog`
   - 检查端口8000是否被占用：`netstat -tlnp | grep 8000`

2. **数据库连接失败**
   - 检查MySQL服务：`systemctl status mysql`
   - 验证数据库配置：检查`.env`文件

3. **SSL证书问题**
   - 检查域名解析：`nslookup sub.wswldcs.edu.deal`
   - 重新获取证书：`certbot --nginx -d sub.wswldcs.edu.deal`

4. **静态文件404**
   - 检查文件权限：`chown -R www-data:www-data /var/www/aublog`
   - 检查Nginx配置：`nginx -t`

### 性能优化

1. **启用Gzip压缩**
2. **配置CDN**
3. **数据库索引优化**
4. **Redis缓存**

## 📞 技术支持

如果遇到问题，请：

1. 查看日志文件
2. 检查服务状态
3. 验证配置文件
4. 在GitHub提交Issue

---

🎉 **部署完成后，你的博客将在 `https://sub.wswldcs.edu.deal` 上线！**
