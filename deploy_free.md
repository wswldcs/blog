# 免费部署方案

由于域名配置问题，我们提供以下免费部署方案：

## 🆓 方案一：Railway部署（推荐）

Railway提供免费的托管服务，自动分配域名。

### 步骤：

1. **注册Railway账号**
   - 访问：https://railway.app
   - 使用GitHub账号登录

2. **部署项目**
   - 点击 "New Project"
   - 选择 "Deploy from GitHub repo"
   - 选择 `wswldcs/blog` 仓库
   - 点击 "Deploy Now"

3. **配置环境变量**
   ```
   FLASK_ENV=production
   SECRET_KEY=your-secret-key-change-this
   MYSQL_HOST=mysql.railway.internal
   MYSQL_USER=root
   MYSQL_PASSWORD=your-password
   MYSQL_DATABASE=aublog
   BLOG_TITLE=我的个人博客
   BLOG_DOMAIN=your-app.railway.app
   ```

4. **添加MySQL数据库**
   - 在项目中点击 "New"
   - 选择 "Database" → "MySQL"
   - 复制连接信息到环境变量

5. **获取域名**
   - 部署完成后，Railway会提供一个域名
   - 格式：`your-app-name.railway.app`

## 🆓 方案二：Render部署

1. **注册Render账号**
   - 访问：https://render.com
   - 使用GitHub账号登录

2. **创建Web Service**
   - 点击 "New" → "Web Service"
   - 连接GitHub仓库 `wswldcs/blog`
   - 配置：
     - Name: `aublog`
     - Environment: `Python 3`
     - Build Command: `pip install -r requirements.txt`
     - Start Command: `gunicorn run:app`

3. **添加环境变量**
   - 在设置中添加环境变量
   - 配置数据库连接

4. **添加数据库**
   - 创建PostgreSQL数据库
   - 获取连接字符串

## 🆓 方案三：Vercel部署

1. **注册Vercel账号**
   - 访问：https://vercel.com
   - 使用GitHub账号登录

2. **导入项目**
   - 点击 "New Project"
   - 导入 `wswldcs/blog` 仓库

3. **配置**
   - Framework Preset: Other
   - Build Command: `pip install -r requirements.txt`
   - Output Directory: `./`

## 🆓 方案四：Heroku部署

1. **注册Heroku账号**
   - 访问：https://heroku.com
   - 创建免费账号

2. **安装Heroku CLI**
   ```bash
   # Windows
   # 下载并安装：https://devcenter.heroku.com/articles/heroku-cli
   ```

3. **部署**
   ```bash
   heroku login
   heroku create aublog-wswldcs
   git push heroku main
   ```

## 🌐 临时域名方案

如果你想立即测试，可以使用以下方案：

### 使用ngrok（本地测试）

1. **下载ngrok**
   - 访问：https://ngrok.com
   - 下载Windows版本

2. **启动博客**
   ```bash
   python run.py
   ```

3. **启动ngrok**
   ```bash
   ngrok http 5000
   ```

4. **获取公网地址**
   - ngrok会提供一个临时的公网地址
   - 格式：`https://xxxxx.ngrok.io`

### 使用localhost.run

```bash
# 启动博客
python run.py

# 在另一个终端运行
ssh -R 80:localhost:5000 localhost.run
```

## 🔧 域名问题解决

如果你想使用自己的域名 `sub.wswldcs.edu.deal`，需要：

### 1. 检查域名注册商

- 确认域名是否已正确注册
- 检查DNS设置权限

### 2. 配置DNS记录

在域名管理面板中添加：
```
类型: A
名称: sub.wswldcs.edu.deal
值: YOUR_SERVER_IP
TTL: 300
```

### 3. 验证DNS传播

```bash
# 检查DNS传播
nslookup sub.wswldcs.edu.deal 8.8.8.8
dig sub.wswldcs.edu.deal @8.8.8.8
```

### 4. 等待DNS传播

DNS更改可能需要24-48小时才能全球生效。

## 📞 推荐行动

**立即可行的方案：**

1. **Railway部署**（最简单）
   - 5分钟内上线
   - 自动分配域名
   - 免费额度充足

2. **ngrok测试**（最快）
   - 1分钟内可访问
   - 适合演示和测试

**长期方案：**

1. 解决域名DNS配置问题
2. 购买云服务器部署
3. 配置自定义域名

你想先尝试哪个方案？我可以提供详细的操作指导！
