from flask import Blueprint, request, jsonify, current_app
from app import db
from app.models import Post, Comment, Visitor, SiteConfig
from app.utils import get_weather_info, get_visitor_info
from datetime import datetime, timedelta
import json

bp = Blueprint('api', __name__)

@bp.route('/weather')
def weather():
    """获取天气信息API"""
    city = request.args.get('city', 'Beijing')
    weather_data = get_weather_info(city)

    if weather_data:
        return jsonify({
            'success': True,
            'data': weather_data
        })
    else:
        # 返回模拟天气数据
        return jsonify({
            'success': True,
            'data': {
                'city': city,
                'temperature': 22,
                'description': '晴朗',
                'humidity': 65,
                'wind_speed': 3.2,
                'icon': '01d'
            }
        })

@bp.route('/visitor-info')
def visitor_info():
    """获取访客信息API"""
    ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    visitor = Visitor.query.filter_by(ip_address=ip).first()
    
    if visitor:
        return jsonify({
            'success': True,
            'data': {
                'country': visitor.country,
                'city': visitor.city,
                'distance': visitor.distance,
                'visit_count': visitor.visit_count
            }
        })
    else:
        return jsonify({
            'success': False,
            'message': '访客信息不可用'
        })

@bp.route('/stats')
def stats():
    """获取网站统计信息"""
    # 总统计
    total_posts = Post.query.filter_by(is_published=True).count()
    total_visitors = Visitor.query.count()
    total_views = db.session.query(db.func.sum(Post.view_count)).scalar() or 0
    total_comments = Comment.query.filter_by(is_approved=True).count()
    
    # 最近7天的访客统计
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_visitors = Visitor.query.filter(Visitor.last_visit >= seven_days_ago).count()
    
    # 最受欢迎的文章
    popular_posts = Post.query.filter_by(is_published=True).order_by(Post.view_count.desc()).limit(5).all()
    
    return jsonify({
        'success': True,
        'data': {
            'total_posts': total_posts,
            'total_visitors': total_visitors,
            'total_views': total_views,
            'total_comments': total_comments,
            'recent_visitors': recent_visitors,
            'popular_posts': [
                {
                    'title': post.title,
                    'slug': post.slug,
                    'view_count': post.view_count
                } for post in popular_posts
            ]
        }
    })

@bp.route('/comment', methods=['POST'])
def add_comment():
    """添加评论API"""
    data = request.get_json()
    
    if not data:
        return jsonify({
            'success': False,
            'message': '无效的请求数据'
        }), 400
    
    # 验证必填字段
    required_fields = ['post_id', 'author_name', 'author_email', 'content']
    for field in required_fields:
        if not data.get(field):
            return jsonify({
                'success': False,
                'message': f'缺少必填字段: {field}'
            }), 400
    
    # 验证文章是否存在
    post = Post.query.get(data['post_id'])
    if not post or not post.is_published:
        return jsonify({
            'success': False,
            'message': '文章不存在'
        }), 404
    
    # 创建评论
    comment = Comment(
        post_id=data['post_id'],
        author_name=data['author_name'],
        author_email=data['author_email'],
        author_website=data.get('author_website', ''),
        content=data['content'],
        is_approved=False  # 需要审核
    )
    
    db.session.add(comment)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': '评论已提交，等待审核'
    })

@bp.route('/search')
def search():
    """搜索API"""
    query = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    if not query:
        return jsonify({
            'success': False,
            'message': '搜索关键词不能为空'
        }), 400
    
    # 搜索文章
    posts = Post.query.filter(
        Post.is_published == True,
        db.or_(
            Post.title.contains(query),
            Post.content.contains(query),
            Post.summary.contains(query)
        )
    ).order_by(Post.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'success': True,
        'data': {
            'posts': [
                {
                    'id': post.id,
                    'title': post.title,
                    'slug': post.slug,
                    'summary': post.summary or post.content[:200] + '...',
                    'created_at': post.created_at.isoformat(),
                    'category': post.category.name if post.category else None,
                    'view_count': post.view_count
                } for post in posts.items
            ],
            'pagination': {
                'page': posts.page,
                'pages': posts.pages,
                'per_page': posts.per_page,
                'total': posts.total,
                'has_next': posts.has_next,
                'has_prev': posts.has_prev
            }
        }
    })

@bp.route('/calendar')
def calendar():
    """获取日历数据API"""
    year = request.args.get('year', datetime.now().year, type=int)
    month = request.args.get('month', datetime.now().month, type=int)
    
    # 获取指定月份的文章
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)
    
    posts = Post.query.filter(
        Post.is_published == True,
        Post.created_at >= start_date,
        Post.created_at < end_date
    ).all()
    
    # 按日期分组
    calendar_data = {}
    for post in posts:
        day = post.created_at.day
        if day not in calendar_data:
            calendar_data[day] = []
        calendar_data[day].append({
            'title': post.title,
            'slug': post.slug
        })
    
    return jsonify({
        'success': True,
        'data': {
            'year': year,
            'month': month,
            'posts': calendar_data
        }
    })
