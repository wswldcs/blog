# 模板定义文件

# 基础模板
BASE_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{{ config.BLOG_TITLE }}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        :root {
            --primary-color: #667eea;
            --secondary-color: #764ba2;
            --accent-color: #f093fb;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
        }
        
        .bg-gradient-primary {
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
        }
        
        .navbar-brand {
            font-weight: 700;
            font-size: 1.5rem;
        }
        
        .card {
            border: none;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
        }
        
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 20px 40px rgba(0,0,0,0.15);
        }
        
        .btn-primary {
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
            border: none;
        }
        
        .btn-primary:hover {
            background: linear-gradient(135deg, var(--secondary-color) 0%, var(--primary-color) 100%);
            transform: translateY(-2px);
        }
        
        .hero-section {
            min-height: 60vh;
            display: flex;
            align-items: center;
        }
        
        .sidebar {
            background: #f8f9fa;
            border-radius: 15px;
            padding: 30px;
        }
        
        .tag {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            margin: 0.25rem;
            border-radius: 50px;
            font-size: 0.875rem;
            text-decoration: none;
            transition: all 0.3s ease;
        }
        
        .tag:hover {
            transform: translateY(-2px);
            text-decoration: none;
        }
        
        .post-meta {
            color: #6c757d;
            font-size: 0.9rem;
        }
        
        .post-meta i {
            margin-right: 0.5rem;
            color: var(--primary-color);
        }
        
        .stats-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 15px;
            padding: 2rem;
            text-align: center;
            margin-bottom: 1rem;
        }
        
        .stats-card h3 {
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }
        
        .footer {
            background: #2c3e50;
            color: white;
            padding: 3rem 0;
            margin-top: 5rem;
        }
        
        .search-form {
            position: relative;
        }
        
        .search-form .form-control {
            border-radius: 50px;
            padding-left: 3rem;
        }
        
        .search-form .search-icon {
            position: absolute;
            left: 1rem;
            top: 50%;
            transform: translateY(-50%);
            color: #6c757d;
        }
        
        .pagination .page-link {
            border-radius: 50px;
            margin: 0 0.25rem;
            border: none;
            color: var(--primary-color);
        }
        
        .pagination .page-item.active .page-link {
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
            border: none;
        }
    </style>
</head>
<body>
    <!-- 导航栏 -->
    <nav class="navbar navbar-expand-lg navbar-dark bg-gradient-primary sticky-top">
        <div class="container">
            <a class="navbar-brand" href="{{ url_for('index') }}">
                <i class="fas fa-blog me-2"></i>{{ config.BLOG_TITLE }}
            </a>
            
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav me-auto">
                    <li class="nav-item">
                        <a class="nav-link" href="{{ url_for('index') }}">
                            <i class="fas fa-home me-1"></i>首页
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="{{ url_for('blog') }}">
                            <i class="fas fa-blog me-1"></i>博客
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="{{ url_for('projects') }}">
                            <i class="fas fa-code me-1"></i>项目
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="{{ url_for('about') }}">
                            <i class="fas fa-user me-1"></i>关于
                        </a>
                    </li>
                </ul>
                
                <ul class="navbar-nav">
                    <li class="nav-item">
                        <a class="nav-link" href="{{ url_for('login') }}">
                            <i class="fas fa-cog me-1"></i>管理
                        </a>
                    </li>
                </ul>
            </div>
        </div>
    </nav>
    
    <!-- 主要内容 -->
    {% block content %}{% endblock %}
    
    <!-- 页脚 -->
    <footer class="footer">
        <div class="container">
            <div class="row">
                <div class="col-md-6">
                    <h5>{{ config.BLOG_TITLE }}</h5>
                    <p class="text-muted">{{ config.BLOG_SUBTITLE }}</p>
                </div>
                <div class="col-md-6 text-md-end">
                    <div class="social-links">
                        <a href="#" class="text-white me-3"><i class="fab fa-github fa-lg"></i></a>
                        <a href="#" class="text-white me-3"><i class="fab fa-twitter fa-lg"></i></a>
                        <a href="#" class="text-white me-3"><i class="fab fa-linkedin fa-lg"></i></a>
                    </div>
                    <p class="text-muted mt-3">© 2024 {{ config.BLOG_TITLE }}. All rights reserved.</p>
                </div>
            </div>
        </div>
    </footer>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
'''

# 首页模板
INDEX_TEMPLATE = BASE_TEMPLATE.replace('{% block content %}{% endblock %}', '''
    <!-- Hero Section -->
    <section class="hero-section bg-gradient-primary text-white">
        <div class="container">
            <div class="row align-items-center">
                <div class="col-lg-6">
                    <h1 class="display-4 fw-bold mb-4">
                        欢迎来到我的博客
                    </h1>
                    <p class="lead mb-4">
                        {{ config.BLOG_SUBTITLE }}
                    </p>
                    <div class="d-flex gap-3">
                        <a href="{{ url_for('blog') }}" class="btn btn-light btn-lg">
                            <i class="fas fa-blog me-2"></i>阅读博客
                        </a>
                        <a href="{{ url_for('about') }}" class="btn btn-outline-light btn-lg">
                            <i class="fas fa-user me-2"></i>了解我
                        </a>
                    </div>
                </div>
                <div class="col-lg-6 text-center">
                    <i class="fas fa-laptop-code fa-10x opacity-75"></i>
                </div>
            </div>
        </div>
    </section>
    
    <!-- 统计信息 -->
    <section class="py-5">
        <div class="container">
            <div class="row">
                <div class="col-md-3 col-sm-6 mb-4">
                    <div class="stats-card">
                        <h3>{{ stats.total_posts }}</h3>
                        <p class="mb-0">篇文章</p>
                    </div>
                </div>
                <div class="col-md-3 col-sm-6 mb-4">
                    <div class="stats-card">
                        <h3>{{ stats.total_categories }}</h3>
                        <p class="mb-0">个分类</p>
                    </div>
                </div>
                <div class="col-md-3 col-sm-6 mb-4">
                    <div class="stats-card">
                        <h3>{{ stats.total_tags }}</h3>
                        <p class="mb-0">个标签</p>
                    </div>
                </div>
                <div class="col-md-3 col-sm-6 mb-4">
                    <div class="stats-card">
                        <h3>{{ stats.total_views }}</h3>
                        <p class="mb-0">次浏览</p>
                    </div>
                </div>
            </div>
        </div>
    </section>
    
    <!-- 精选文章 -->
    {% if featured_posts %}
    <section class="py-5 bg-light">
        <div class="container">
            <div class="row mb-5">
                <div class="col-12 text-center">
                    <h2 class="display-5 fw-bold">精选文章</h2>
                    <p class="lead text-muted">推荐阅读的优质内容</p>
                </div>
            </div>
            
            <div class="row">
                {% for post in featured_posts %}
                <div class="col-lg-4 col-md-6 mb-4">
                    <div class="card h-100">
                        <div class="card-body">
                            <h5 class="card-title">
                                <a href="{{ url_for('post', slug=post.slug) }}" class="text-decoration-none">
                                    {{ post.title }}
                                </a>
                            </h5>
                            <p class="card-text text-muted">{{ post.summary or post.content[:100] + '...' }}</p>
                            <div class="post-meta">
                                <i class="fas fa-calendar-alt"></i>
                                {{ post.created_at.strftime('%Y-%m-%d') }}
                                {% if post.category %}
                                <span class="ms-3">
                                    <i class="fas fa-folder"></i>
                                    {{ post.category.name }}
                                </span>
                                {% endif %}
                            </div>
                        </div>
                        <div class="card-footer bg-transparent">
                            <a href="{{ url_for('post', slug=post.slug) }}" class="btn btn-primary btn-sm">
                                阅读全文 <i class="fas fa-arrow-right ms-1"></i>
                            </a>
                        </div>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
    </section>
    {% endif %}
    
    <!-- 最新文章和侧边栏 -->
    <section class="py-5">
        <div class="container">
            <div class="row">
                <div class="col-lg-8">
                    <h2 class="mb-4">最新文章</h2>
                    {% for post in recent_posts %}
                    <div class="card mb-4">
                        <div class="card-body">
                            <h5 class="card-title">
                                <a href="{{ url_for('post', slug=post.slug) }}" class="text-decoration-none">
                                    {{ post.title }}
                                </a>
                            </h5>
                            <p class="card-text">{{ post.summary or post.content[:150] + '...' }}</p>
                            <div class="post-meta">
                                <i class="fas fa-calendar-alt"></i>
                                {{ post.created_at.strftime('%Y-%m-%d') }}
                                <span class="ms-3">
                                    <i class="fas fa-eye"></i>
                                    {{ post.view_count }} 次浏览
                                </span>
                                {% if post.category %}
                                <span class="ms-3">
                                    <i class="fas fa-folder"></i>
                                    {{ post.category.name }}
                                </span>
                                {% endif %}
                            </div>
                        </div>
                    </div>
                    {% endfor %}
                    
                    <div class="text-center">
                        <a href="{{ url_for('blog') }}" class="btn btn-primary btn-lg">
                            查看更多文章 <i class="fas fa-arrow-right ms-2"></i>
                        </a>
                    </div>
                </div>
                
                <!-- 侧边栏 -->
                <div class="col-lg-4">
                    <!-- 分类 -->
                    <div class="sidebar mb-4">
                        <h5 class="mb-3">
                            <i class="fas fa-folder me-2"></i>文章分类
                        </h5>
                        {% for category in categories %}
                        <a href="{{ url_for('blog', category=category.id) }}" 
                           class="tag" style="background-color: {{ category.color }}; color: white;">
                            {{ category.name }}
                        </a>
                        {% endfor %}
                    </div>
                    
                    <!-- 标签云 -->
                    <div class="sidebar">
                        <h5 class="mb-3">
                            <i class="fas fa-tags me-2"></i>热门标签
                        </h5>
                        {% for tag in tags %}
                        <a href="{{ url_for('blog', tag=tag.id) }}" 
                           class="tag" style="background-color: {{ tag.color }}; color: white;">
                            {{ tag.name }}
                        </a>
                        {% endfor %}
                    </div>
                </div>
            </div>
        </div>
    </section>
''')

# 登录模板
LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>登录 - {{ config.BLOG_TITLE }}</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
        }
        .login-card {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="row justify-content-center">
            <div class="col-md-6 col-lg-4">
                <div class="login-card p-5">
                    <div class="text-center mb-4">
                        <h2>管理后台登录</h2>
                        <p class="text-muted">{{ config.BLOG_TITLE }}</p>
                    </div>
                    
                    {% with messages = get_flashed_messages() %}
                        {% if messages %}
                            {% for message in messages %}
                                <div class="alert alert-danger">{{ message }}</div>
                            {% endfor %}
                        {% endif %}
                    {% endwith %}
                    
                    <form method="post">
                        <div class="mb-3">
                            <label class="form-label">用户名</label>
                            <input type="text" name="username" class="form-control" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">密码</label>
                            <input type="password" name="password" class="form-control" required>
                        </div>
                        <button type="submit" class="btn btn-primary w-100 mb-3">登录</button>
                    </form>
                    
                    <div class="text-center">
                        <a href="{{ url_for('index') }}" class="text-decoration-none">返回首页</a>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
'''
