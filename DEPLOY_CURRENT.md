# 当前域名配置部署指南

## 🌐 域名状态

✅ **主域名**：`www.wswldcs.edu.deal` → `127.0.0.1` (已解析)  
❌ **目标域名**：`wswldcs.blog` (不存在)  
⏳ **DNS传播**：TTL 600秒，正在传播中  

## 🚀 立即可用的部署方案

### 方案1：本地测试（当前可用）

由于域名指向127.0.0.1，你可以立即在本地测试：

```bash
# 启动博客
cd E:\blog\aublog
python run.py

# 访问地址
http://www.wswldcs.edu.deal:5000
```

### 方案2：修改DNS指向云服务器

如果你有云服务器，需要在DNSPod中修改A记录：

```
类型: A
主机记录: www
记录值: [你的服务器IP]
TTL: 600
```

### 方案3：使用免费云平台

#### Railway部署（推荐）

1. **访问Railway**：https://railway.app
2. **GitHub登录**
3. **New Project** → **Deploy from GitHub repo**
4. **选择** `wswldcs/blog`
5. **配置环境变量**：
   ```
   FLASK_ENV=production
   SECRET_KEY=your-secret-key
   BLOG_DOMAIN=your-app.railway.app
   BLOG_TITLE=我的个人博客
   ```
6. **等待部署完成**

Railway会提供域名如：`aublog-production.railway.app`

#### Render部署

1. **访问Render**：https://render.com
2. **连接GitHub仓库**
3. **配置Web Service**：
   - Name: `aublog`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn run:app`

## 🔧 DNS配置建议

### 当前问题

你的DNS配置：`www.wswldcs.edu.deal` → `wswldcs.blog`

但是 `wswldcs.blog` 域名不存在，所以解析到了127.0.0.1。

### 解决方案

#### 选项A：指向云服务器

```
类型: A
主机记录: www
记录值: [云服务器IP]
TTL: 600
```

#### 选项B：指向免费平台

如果使用Railway/Render等平台：

```
类型: CNAME
主机记录: www
记录值: your-app.railway.app
TTL: 600
```

#### 选项C：使用GitHub Pages

```
类型: CNAME
主机记录: www
记录值: wswldcs.github.io
TTL: 600
```

## 🌟 推荐部署流程

### 立即行动（5分钟）

1. **Railway部署**：
   - 访问 https://railway.app
   - 连接GitHub仓库 `wswldcs/blog`
   - 自动部署获得临时域名

2. **测试功能**：
   - 使用Railway提供的域名测试所有功能
   - 确保博客正常运行

### 长期配置（1小时）

1. **购买云服务器**（可选）：
   - 阿里云/腾讯云最低配置即可
   - 获取公网IP地址

2. **修改DNS配置**：
   ```
   类型: A
   主机记录: www
   记录值: [服务器IP或平台域名]
   TTL: 600
   ```

3. **部署到服务器**：
   ```bash
   # 在服务器上执行
   wget https://raw.githubusercontent.com/wswldcs/blog/main/deploy.sh
   chmod +x deploy.sh
   ./deploy.sh
   ```

4. **配置SSL证书**：
   ```bash
   # 在服务器上执行
   wget https://raw.githubusercontent.com/wswldcs/blog/main/setup_ssl.sh
   chmod +x setup_ssl.sh
   ./setup_ssl.sh
   ```

## 🔍 域名检查工具

使用项目中的检查工具：

```bash
python check_domain.py
```

这会检查所有相关域名的解析状态。

## 📞 下一步建议

### 立即执行

1. **Railway部署**：获得稳定的在线地址
2. **功能测试**：确保所有功能正常

### 可选执行

1. **购买云服务器**：获得更多控制权
2. **配置自定义域名**：使用你的域名
3. **SSL证书配置**：启用HTTPS

## 🎯 最终目标

- **域名**：https://www.wswldcs.edu.deal
- **功能**：完整的博客系统
- **管理**：https://www.wswldcs.edu.deal/manage
- **SSL**：Let's Encrypt免费证书

## 📋 当前可访问地址

- **本地测试**：http://www.wswldcs.edu.deal:5000
- **GitHub仓库**：https://github.com/wswldcs/blog
- **部署文档**：https://github.com/wswldcs/blog/blob/main/DEPLOYMENT.md

---

🚀 **选择一个方案开始部署吧！**
