# 🚀 Railway部署指南

## 快速部署步骤

### 1. 准备Railway账号
1. 访问 [Railway.app](https://railway.app)
2. 使用GitHub账号登录

### 2. 部署项目
1. 点击 "New Project"
2. 选择 "Deploy from GitHub repo"
3. 选择 `wswldcs/blog` 仓库
4. Railway会自动检测Dockerfile并开始部署

### 3. 配置数据库
1. 在项目中添加MySQL插件
2. 等待数据库创建完成
3. 数据库连接信息会自动配置

### 4. 设置环境变量
在Railway项目设置中添加：
```
FLASK_ENV=production
SECRET_KEY=your-super-secret-key-here
```

### 5. 配置自定义域名
1. 在Railway项目设置中点击"Domains"
2. 添加域名：`www.wswldcs.edu.deal`
3. 在DNSPod中配置CNAME记录：
   - 主机记录：www
   - 记录类型：CNAME
   - 记录值：your-project.railway.app
   - TTL：600

### 6. 验证部署
- 访问Railway提供的临时域名测试
- 访问自定义域名确认配置正确
- 登录管理后台（admin/admin123）

## 🎯 部署完成！

你的博客现在可以通过以下地址访问：
- **Railway域名**：https://your-project.railway.app
- **自定义域名**：https://www.wswldcs.edu.deal

## 📝 发布技术总结文章

现在你可以：
1. 登录管理后台：https://www.wswldcs.edu.deal/admin
2. 点击"文章管理" → "添加文章"
3. 发布你的开发总结文章

## 🔧 后续维护

- 定期备份数据库
- 监控应用性能
- 更新依赖包
- 添加新功能
