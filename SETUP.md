# 🚀 博客系统安装指南

这是一个详细的安装和配置指南，帮助你快速搭建个人博客系统。

## 📋 系统要求

- **操作系统**: Windows 10/11, macOS, Linux
- **Python**: 3.8 或更高版本
- **数据库**: MySQL 5.7+ 或 MariaDB 10.3+
- **内存**: 至少 2GB RAM
- **存储**: 至少 1GB 可用空间

## 🛠️ 安装步骤

### 第一步：准备环境

#### 1.1 安装Python
- 访问 [Python官网](https://python.org) 下载最新版本
- 安装时勾选 "Add Python to PATH"
- 验证安装：
```bash
python --version
pip --version
```

#### 1.2 安装MySQL
- 下载 [MySQL Community Server](https://dev.mysql.com/downloads/mysql/)
- 安装过程中设置root密码为 `1234`（或记住你设置的密码）
- 启动MySQL服务

#### 1.3 创建数据库
```sql
-- 登录MySQL
mysql -u root -p

-- 创建数据库
CREATE DATABASE aublog CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 退出
EXIT;
```

### 第二步：下载项目

#### 2.1 克隆项目（如果有Git）
```bash
git clone https://github.com/wswldcs/aublog.git
cd aublog
```

#### 2.2 或直接下载
- 下载项目ZIP文件
- 解压到你选择的目录
- 进入项目目录

### 第三步：配置环境

#### 3.1 创建虚拟环境
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

#### 3.2 安装依赖
```bash
pip install -r requirements.txt
```

#### 3.3 配置环境变量
复制 `.env` 文件并修改配置：

```bash
# 基础配置
SECRET_KEY=your-super-secret-key-change-this
FLASK_ENV=development

# 数据库配置（修改为你的密码）
DATABASE_URL=mysql+pymysql://root:1234@localhost/aublog

# 博客信息（修改为你的信息）
BLOG_TITLE=你的博客名称
BLOG_SUBTITLE=你的博客副标题
AUTHOR_NAME=你的名字
AUTHOR_EMAIL=your-email@example.com

# 地理位置（修改为你的位置坐标）
AUTHOR_LATITUDE=39.9042
AUTHOR_LONGITUDE=116.4074

# API密钥（可选，后续申请）
WEATHER_API_KEY=
IPINFO_TOKEN=

# 管理员账户（修改密码）
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-secure-password
```

### 第四步：初始化数据库

#### 4.1 运行初始化脚本
```bash
python init_db.py
```

这将创建所有必要的数据表并插入示例数据。

### 第五步：启动应用

#### 5.1 使用启动脚本（Windows推荐）
```bash
start.bat
```

#### 5.2 手动启动
```bash
python run.py
```

### 第六步：访问应用

- **前台首页**: http://localhost:5000
- **管理后台**: http://localhost:5000/admin
- **Flask-Admin**: http://localhost:5000/admin

默认管理员账户：
- 用户名: `admin`
- 密码: `admin123`（或你在.env中设置的密码）

## 🔧 高级配置

### API密钥配置

#### 天气API（可选）
1. 注册 [OpenWeatherMap](https://openweathermap.org/api)
2. 获取免费API密钥
3. 在 `.env` 中设置 `WEATHER_API_KEY`

#### IP地理位置API（可选）
1. 注册 [IPInfo.io](https://ipinfo.io/)
2. 获取免费token
3. 在 `.env` 中设置 `IPINFO_TOKEN`

### 邮件配置（可选）
如需邮件通知功能，在 `.env` 中添加：
```bash
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
```

### 文件上传配置
默认上传目录：`app/static/uploads/`
支持的文件类型：png, jpg, jpeg, gif, webp
最大文件大小：16MB

## 🎨 自定义配置

### 修改主题
编辑 `app/static/css/style.css` 中的CSS变量：
```css
:root {
    --primary-color: #007bff;    /* 主色调 */
    --secondary-color: #6c757d;  /* 次要色调 */
    /* 更多颜色... */
}
```

### 添加自定义页面
1. 在 `app/routes/main.py` 中添加路由
2. 在 `app/templates/` 中创建模板
3. 在导航栏中添加链接

### 修改网站信息
登录管理后台 → 网站配置 → 修改相关信息

## 🚨 常见问题

### Q1: 数据库连接失败
**A**: 检查以下项目：
- MySQL服务是否启动
- 数据库名称是否正确
- 用户名密码是否正确
- 端口是否为3306

### Q2: 依赖安装失败
**A**: 尝试以下解决方案：
```bash
# 升级pip
pip install --upgrade pip

# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/

# 单独安装失败的包
pip install package-name
```

### Q3: 端口被占用
**A**: 修改 `run.py` 中的端口：
```python
app.run(debug=True, host='0.0.0.0', port=5001)  # 改为5001
```

### Q4: 静态文件不显示
**A**: 检查以下项目：
- 文件路径是否正确
- 文件权限是否正确
- 浏览器缓存是否需要清除

### Q5: 上传文件失败
**A**: 确保：
- `app/static/uploads/` 目录存在
- 目录有写入权限
- 文件大小不超过16MB
- 文件类型被支持

## 📱 移动端适配

博客已经做了响应式设计，自动适配移动端。如需进一步优化：

1. 修改 `app/static/css/style.css` 中的媒体查询
2. 调整移动端导航菜单
3. 优化触摸交互

## 🔒 安全建议

### 生产环境部署
1. **修改默认密码**：更改管理员密码
2. **使用HTTPS**：配置SSL证书
3. **设置防火墙**：限制不必要的端口访问
4. **定期备份**：备份数据库和文件
5. **更新依赖**：定期更新Python包

### 密码安全
- 使用强密码（至少12位，包含大小写字母、数字、特殊字符）
- 定期更换密码
- 不要在代码中硬编码密码

## 📞 获取帮助

如果遇到问题：

1. **查看日志**：检查控制台输出的错误信息
2. **搜索文档**：查看Flask官方文档
3. **社区求助**：在相关技术论坛提问
4. **联系作者**：发送邮件到 your-email@example.com

## 🎉 完成！

恭喜！你已经成功搭建了个人博客系统。现在可以：

- ✅ 登录管理后台
- ✅ 发布第一篇文章
- ✅ 自定义网站信息
- ✅ 邀请朋友访问

享受写作和分享的乐趣吧！ 🎊
