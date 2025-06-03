from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import Post, Category, Tag, User, Comment, Link, Project, Timeline, SiteConfig, Visitor
from app.utils import get_visitor_info, calculate_distance
from datetime import datetime
import requests

bp = Blueprint('main', __name__)

@bp.before_request
def track_visitor():
    """跟踪访客信息"""
    if request.endpoint and not request.endpoint.startswith('static'):
        ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        if ip:
            visitor = Visitor.query.filter_by(ip_address=ip).first()
            if visitor:
                visitor.visit_count += 1
                visitor.last_visit = datetime.utcnow()
            else:
                # 获取访客地理信息
                visitor_info = get_visitor_info(ip)
                visitor = Visitor(
                    ip_address=ip,
                    user_agent=request.user_agent.string,
                    country=visitor_info.get('country'),
                    city=visitor_info.get('city'),
                    latitude=visitor_info.get('latitude'),
                    longitude=visitor_info.get('longitude'),
                    distance=visitor_info.get('distance')
                )
                db.session.add(visitor)
            db.session.commit()

@bp.route('/')
def index():
    """首页"""
    page = request.args.get('page', 1, type=int)
    posts = Post.query.filter_by(is_published=True).order_by(Post.created_at.desc()).paginate(
        page=page, per_page=current_app.config['POSTS_PER_PAGE'], error_out=False)
    
    featured_posts = Post.query.filter_by(is_published=True, is_featured=True).limit(3).all()
    recent_posts = Post.query.filter_by(is_published=True).order_by(Post.created_at.desc()).limit(5).all()
    categories = Category.query.all()
    tags = Tag.query.all()
    
    # 获取网站配置
    site_config = SiteConfig.query.first()
    
    # 统计信息
    stats = {
        'total_posts': Post.query.filter_by(is_published=True).count(),
        'total_categories': Category.query.count(),
        'total_tags': Tag.query.count(),
        'total_visitors': Visitor.query.count()
    }
    
    return render_template('index.html', 
                         posts=posts, 
                         featured_posts=featured_posts,
                         recent_posts=recent_posts,
                         categories=categories,
                         tags=tags,
                         site_config=site_config,
                         stats=stats)

@bp.route('/blog')
def blog():
    """博客列表页"""
    page = request.args.get('page', 1, type=int)
    category_id = request.args.get('category', type=int)
    tag_id = request.args.get('tag', type=int)
    search = request.args.get('search', '')
    
    query = Post.query.filter_by(is_published=True)
    
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    if tag_id:
        query = query.filter(Post.tags.any(Tag.id == tag_id))
    
    if search:
        query = query.filter(Post.title.contains(search) | Post.content.contains(search))
    
    posts = query.order_by(Post.created_at.desc()).paginate(
        page=page, per_page=current_app.config['POSTS_PER_PAGE'], error_out=False)
    
    categories = Category.query.all()
    tags = Tag.query.all()
    
    return render_template('blog.html', 
                         posts=posts, 
                         categories=categories, 
                         tags=tags,
                         current_category=category_id,
                         current_tag=tag_id,
                         search_query=search)

@bp.route('/post/<slug>')
def post(slug):
    """文章详情页"""
    post = Post.query.filter_by(slug=slug, is_published=True).first_or_404()
    
    # 增加浏览量
    post.view_count += 1
    db.session.commit()
    
    # 获取相关文章
    related_posts = []
    if post.category_id:
        related_posts = Post.query.filter(
            Post.id != post.id,
            Post.is_published == True,
            Post.category_id == post.category_id
        ).limit(3).all()
    
    # 获取评论
    comments = Comment.query.filter_by(post_id=post.id, is_approved=True).order_by(Comment.created_at.asc()).all()
    
    return render_template('post.html', 
                         post=post, 
                         related_posts=related_posts,
                         comments=comments)

@bp.route('/about')
def about():
    """关于页面"""
    site_config = SiteConfig.query.first()
    return render_template('about.html', site_config=site_config)

@bp.route('/projects')
def projects():
    """项目展示页"""
    featured_projects = Project.query.filter_by(is_featured=True).order_by(Project.sort_order).all()
    other_projects = Project.query.filter_by(is_featured=False).order_by(Project.sort_order).all()
    
    return render_template('projects.html', 
                         featured_projects=featured_projects,
                         other_projects=other_projects)

@bp.route('/timeline')
def timeline():
    """学习历程时间线"""
    timeline_items = Timeline.query.order_by(Timeline.date.desc()).all()
    return render_template('timeline.html', timeline_items=timeline_items)

@bp.route('/links')
def links():
    """友情链接"""
    links = Link.query.filter_by(is_active=True).order_by(Link.sort_order).all()
    return render_template('links.html', links=links)
