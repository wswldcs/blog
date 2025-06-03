# 🎉 wswldcs的个人博客

一个功能丰富、界面优美的个人博客系统，基于Flask框架开发。

## ✨ 特性

### 🎨 前端特性
- **响应式设计** - 完美适配桌面端和移动端
- **现代化UI** - 基于Bootstrap 5，界面简洁美观
- **主题切换** - 支持明暗主题切换
- **动画效果** - 使用AOS库实现滚动动画
- **代码高亮** - Prism.js代码语法高亮

### 📝 博客功能
- **文章管理** - 支持Markdown语法，在线编辑发布
- **分类标签** - 灵活的文章分类和标签系统
- **搜索功能** - 全文搜索，快速找到相关内容
- **评论系统** - 支持访客评论，管理员审核
- **文章统计** - 浏览量统计，热门文章推荐

### 🌟 特色功能
- **日历组件** - 按日期浏览文章
- **天气信息** - 实时天气显示
- **访客统计** - 地理位置和距离计算
- **友情链接** - 友站链接管理
- **项目展示** - 个人项目作品展示
- **学习历程** - 时间线形式展示成长轨迹
- **社交链接** - 多平台社交媒体链接

### 🔧 管理功能
- **后台管理** - Flask-Admin管理界面
- **文件上传** - 支持图片等文件上传
- **数据统计** - 访问统计和数据分析
- **配置管理** - 网站配置在线修改

## 🛠️ 技术栈

### 后端
- **Python 3.8+**
- **Flask** - Web框架
- **SQLAlchemy** - ORM数据库操作
- **Flask-Login** - 用户认证
- **Flask-Admin** - 后台管理
- **Flask-Migrate** - 数据库迁移

### 前端
- **Bootstrap 5** - UI框架
- **jQuery** - JavaScript库
- **AOS** - 滚动动画
- **Prism.js** - 代码高亮
- **Chart.js** - 数据可视化
- **Font Awesome** - 图标库

### 数据库
- **MySQL** - 主数据库
- **SQLite** - 开发环境可选

## 🚀 快速开始

### 环境要求
- Python 3.8+
- MySQL 5.7+
- Git

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/wswldcs/aublog.git
cd aublog
```

2. **创建虚拟环境**
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **配置数据库**
```bash
# 创建MySQL数据库
mysql -u root -p
CREATE DATABASE aublog CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

5. **配置环境变量**
```bash
# 复制环境变量文件
cp .env.example .env
# 编辑.env文件，配置数据库连接等信息
```

6. **初始化数据库**
```bash
python init_db.py
```

7. **运行应用**
```bash
python run.py
```

8. **访问应用**
- 前台: http://localhost:5000
- 后台: http://localhost:5000/admin
- 管理员登录: admin / admin123

## 📁 项目结构

```
aublog/
├── app/                    # 应用主目录
│   ├── __init__.py        # 应用初始化
│   ├── models.py          # 数据模型
│   ├── admin_views.py     # 管理后台视图
│   ├── utils.py           # 工具函数
│   ├── routes/            # 路由模块
│   │   ├── main.py        # 主要路由
│   │   ├── admin.py       # 管理路由
│   │   └── api.py         # API路由
│   ├── templates/         # 模板文件
│   │   ├── base.html      # 基础模板
│   │   ├── index.html     # 首页
│   │   ├── blog.html      # 博客列表
│   │   ├── post.html      # 文章详情
│   │   └── admin/         # 管理模板
│   └── static/            # 静态文件
│       ├── css/           # 样式文件
│       ├── js/            # JavaScript文件
│       └── images/        # 图片文件
├── config.py              # 配置文件
├── run.py                 # 应用启动文件
├── init_db.py            # 数据库初始化
├── requirements.txt       # 依赖包列表
├── .env                  # 环境变量
└── README.md             # 项目说明
```

## ⚙️ 配置说明

### 环境变量配置 (.env)

```bash
# 基础配置
SECRET_KEY=your-secret-key
FLASK_ENV=development

# 数据库配置
DATABASE_URL=mysql+pymysql://root:password@localhost/aublog

# 博客信息
BLOG_TITLE=你的博客标题
BLOG_SUBTITLE=博客副标题
AUTHOR_NAME=你的名字
AUTHOR_EMAIL=your-email@example.com

# 地理位置（你的位置坐标）
AUTHOR_LATITUDE=39.9042
AUTHOR_LONGITUDE=116.4074

# API密钥
WEATHER_API_KEY=your-openweathermap-api-key
IPINFO_TOKEN=your-ipinfo-token

# 管理员账户
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-password
```

### API密钥获取

1. **天气API** - 注册 [OpenWeatherMap](https://openweathermap.org/api)
2. **IP地理位置** - 注册 [IPInfo.io](https://ipinfo.io/)

## 📱 功能截图

### 首页
- 精美的英雄区域
- 统计数据展示
- 精选文章推荐
- 最新文章列表

### 博客页面
- 文章列表展示
- 搜索和筛选
- 分页导航
- 侧边栏组件

### 文章详情
- Markdown渲染
- 代码高亮
- 评论系统
- 相关文章推荐

### 管理后台
- 数据统计仪表板
- 文章管理
- 评论审核
- 系统配置

## 🔧 自定义配置

### 修改主题颜色
编辑 `app/static/css/style.css` 中的CSS变量：

```css
:root {
    --primary-color: #007bff;
    --secondary-color: #6c757d;
    /* 更多颜色配置... */
}
```

### 添加新功能
1. 在 `app/models.py` 中定义数据模型
2. 在 `app/routes/` 中添加路由
3. 创建对应的模板文件
4. 运行数据库迁移

## 📦 部署

### GitHub Pages部署
1. 将项目推送到GitHub
2. 在仓库设置中启用GitHub Pages
3. 选择部署分支

### 服务器部署
```bash
# 使用Gunicorn部署
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

### Docker部署
```bash
# 构建镜像
docker build -t aublog .

# 运行容器
docker run -p 5000:5000 aublog
```

## 🤝 贡献

欢迎提交Issue和Pull Request！

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 📞 联系方式

- **作者**: wswldcs
- **邮箱**: your-email@example.com
- **GitHub**: https://github.com/wswldcs

## 🙏 致谢

感谢以下开源项目：
- [Flask](https://flask.palletsprojects.com/)
- [Bootstrap](https://getbootstrap.com/)
- [Font Awesome](https://fontawesome.com/)
- [AOS](https://michalsnik.github.io/aos/)
- [Prism.js](https://prismjs.com/)

---

⭐ 如果这个项目对你有帮助，请给个Star支持一下！
