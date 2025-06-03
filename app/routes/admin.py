from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.models import User, Post, Category, Tag, Comment, Link, Project, Timeline, SiteConfig
from app.utils import create_slug, allowed_file
import os
from datetime import datetime

bp = Blueprint('manage', __name__)

def admin_required(f):
    """管理员权限装饰器"""
    from functools import wraps

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('需要管理员权限', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """管理员登录"""
    if current_user.is_authenticated:
        return redirect(url_for('manage.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password) and user.is_admin:
            login_user(user, remember=True)
            flash('登录成功！', 'success')
            return redirect(url_for('manage.dashboard'))
        else:
            flash('用户名或密码错误', 'error')
    
    return render_template('admin/login.html')

@bp.route('/logout')
@login_required
def logout():
    """管理员登出"""
    logout_user()
    flash('已成功登出', 'info')
    return redirect(url_for('main.index'))

@bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """管理员仪表板"""
    # 统计数据
    stats = {
        'total_posts': Post.query.count(),
        'published_posts': Post.query.filter_by(is_published=True).count(),
        'draft_posts': Post.query.filter_by(is_published=False).count(),
        'total_comments': Comment.query.count(),
        'pending_comments': Comment.query.filter_by(is_approved=False).count(),
        'total_categories': Category.query.count(),
        'total_tags': Tag.query.count()
    }
    
    # 最近的文章
    recent_posts = Post.query.order_by(Post.created_at.desc()).limit(5).all()
    
    # 待审核的评论
    pending_comments = Comment.query.filter_by(is_approved=False).order_by(Comment.created_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html', 
                         stats=stats, 
                         recent_posts=recent_posts,
                         pending_comments=pending_comments)

@bp.route('/posts')
@login_required
@admin_required
def posts():
    """文章管理"""
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False)
    
    return render_template('admin/posts.html', posts=posts)

@bp.route('/posts/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_post():
    """新建文章"""
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        summary = request.form.get('summary')
        category_id = request.form.get('category_id', type=int)
        tag_ids = request.form.getlist('tag_ids', type=int)
        is_published = 'is_published' in request.form
        is_featured = 'is_featured' in request.form
        
        # 创建slug
        slug = create_slug(title)
        
        # 检查slug是否已存在
        existing_post = Post.query.filter_by(slug=slug).first()
        if existing_post:
            slug = f"{slug}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        post = Post(
            title=title,
            slug=slug,
            content=content,
            summary=summary,
            category_id=category_id if category_id else None,
            is_published=is_published,
            is_featured=is_featured,
            user_id=current_user.id
        )
        
        # 添加标签
        if tag_ids:
            tags = Tag.query.filter(Tag.id.in_(tag_ids)).all()
            post.tags = tags
        
        db.session.add(post)
        db.session.commit()
        
        flash('文章创建成功！', 'success')
        return redirect(url_for('manage.posts'))
    
    categories = Category.query.all()
    tags = Tag.query.all()
    
    return render_template('admin/post_form.html', 
                         categories=categories, 
                         tags=tags,
                         post=None)

@bp.route('/posts/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_post(id):
    """编辑文章"""
    post = Post.query.get_or_404(id)
    if request.method == 'POST':
        post.title = request.form.get('title')
        post.content = request.form.get('content')
        post.summary = request.form.get('summary')
        post.category_id = request.form.get('category_id', type=int) or None

        tag_ids = request.form.getlist('tag_ids', type=int)
        if tag_ids:
            tags = Tag.query.filter(Tag.id.in_(tag_ids)).all()
            post.tags = tags
        else:
            post.tags = []

        # 修复复选框处理 - 复选框勾选时发送'on'，未勾选时不发送
        post.is_published = 'is_published' in request.form
        post.is_featured = 'is_featured' in request.form
        post.updated_at = datetime.utcnow()

        db.session.commit()
        
        flash('文章更新成功！', 'success')
        return redirect(url_for('manage.posts'))
    
    categories = Category.query.all()
    tags = Tag.query.all()
    
    return render_template('admin/post_form.html', 
                         post=post, 
                         categories=categories, 
                         tags=tags)

@bp.route('/posts/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_post(id):
    """删除文章"""
    post = Post.query.get_or_404(id)
    db.session.delete(post)
    db.session.commit()
    
    flash('文章已删除', 'info')
    return redirect(url_for('manage.posts'))

@bp.route('/upload', methods=['POST'])
@login_required
@admin_required
def upload_file():
    """文件上传"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': '没有选择文件'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': '没有选择文件'})
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # 添加时间戳避免重名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
        filename = timestamp + filename
        
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # 返回文件URL
        file_url = url_for('static', filename=f'uploads/{filename}')
        
        return jsonify({
            'success': True,
            'url': file_url,
            'filename': filename
        })
    
    return jsonify({'success': False, 'message': '不支持的文件类型'})
