from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user
from flask import redirect, url_for, request
from app.models import User, Post, Category, Tag, Comment, Link, Project, Timeline, SiteConfig, Visitor

class AdminAuthMixin:
    """管理员认证混合类"""
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin
    
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('manage.login', next=request.url))

class MyAdminIndexView(AdminAuthMixin, AdminIndexView):
    """自定义管理员首页"""
    @expose('/')
    def index(self):
        return redirect(url_for('manage.dashboard'))

class UserModelView(AdminAuthMixin, ModelView):
    """用户管理视图"""
    column_list = ['username', 'email', 'is_admin', 'created_at']
    column_searchable_list = ['username', 'email']
    column_filters = ['is_admin', 'created_at']
    form_excluded_columns = ['password_hash', 'posts', 'comments']
    
    def on_model_change(self, form, model, is_created):
        if is_created and form.password.data:
            model.set_password(form.password.data)

class PostModelView(AdminAuthMixin, ModelView):
    """文章管理视图"""
    column_list = ['title', 'is_published', 'is_featured', 'view_count', 'created_at']
    column_searchable_list = ['title', 'content']
    column_filters = ['is_published', 'is_featured', 'created_at']
    form_excluded_columns = ['slug', 'view_count', 'comments']
    column_labels = {
        'is_published': '已发布',
        'is_featured': '精选',
        'view_count': '浏览量',
        'created_at': '创建时间'
    }
    
    def on_model_change(self, form, model, is_created):
        if is_created:
            from app.utils import create_slug
            model.slug = create_slug(model.title)
            model.user_id = current_user.id

class CategoryModelView(AdminAuthMixin, ModelView):
    """分类管理视图"""
    column_list = ['name', 'description', 'created_at']
    column_searchable_list = ['name']

class TagModelView(AdminAuthMixin, ModelView):
    """标签管理视图"""
    column_list = ['name', 'created_at']
    column_searchable_list = ['name']

class CommentModelView(AdminAuthMixin, ModelView):
    """评论管理视图"""
    column_list = ['author_name', 'is_approved', 'created_at']
    column_searchable_list = ['author_name', 'content']
    column_filters = ['is_approved', 'created_at']
    column_labels = {
        'author_name': '评论者',
        'is_approved': '已审核',
        'created_at': '创建时间'
    }

class LinkModelView(AdminAuthMixin, ModelView):
    """友情链接管理视图"""
    column_list = ['name', 'url', 'is_active', 'sort_order', 'created_at']
    column_searchable_list = ['name', 'url']
    column_filters = ['is_active']

class ProjectModelView(AdminAuthMixin, ModelView):
    """项目管理视图"""
    column_list = ['name', 'tech_stack', 'is_featured', 'sort_order', 'created_at']
    column_searchable_list = ['name', 'description']
    column_filters = ['is_featured']

class TimelineModelView(AdminAuthMixin, ModelView):
    """时间线管理视图"""
    column_list = ['title', 'date', 'is_milestone', 'sort_order', 'created_at']
    column_searchable_list = ['title', 'description']
    column_filters = ['is_milestone', 'date']

class SiteConfigModelView(AdminAuthMixin, ModelView):
    """网站配置管理视图"""
    column_list = ['site_title', 'author_name', 'updated_at']
    
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin
    
    def create_model(self, form):
        # 只允许一个配置记录
        if SiteConfig.query.first():
            return False
        return super().create_model(form)

class VisitorModelView(AdminAuthMixin, ModelView):
    """访客统计视图"""
    can_create = False
    can_edit = False
    column_list = ['ip_address', 'country', 'city', 'distance', 'visit_count', 'first_visit', 'last_visit']
    column_searchable_list = ['ip_address', 'country', 'city']
    column_filters = ['country', 'city', 'first_visit', 'last_visit']

def init_admin(app, db):
    """初始化Flask-Admin"""
    admin = Admin(
        app,
        name='博客管理',
        template_mode='bootstrap4',
        index_view=MyAdminIndexView(),
        url='/admin'
    )
    
    # 添加模型视图
    admin.add_view(UserModelView(User, db.session, name='用户管理'))
    admin.add_view(PostModelView(Post, db.session, name='文章管理'))
    admin.add_view(CategoryModelView(Category, db.session, name='分类管理'))
    admin.add_view(TagModelView(Tag, db.session, name='标签管理'))
    admin.add_view(CommentModelView(Comment, db.session, name='评论管理'))
    admin.add_view(LinkModelView(Link, db.session, name='友情链接'))
    admin.add_view(ProjectModelView(Project, db.session, name='项目管理'))
    admin.add_view(TimelineModelView(Timeline, db.session, name='时间线'))
    admin.add_view(SiteConfigModelView(SiteConfig, db.session, name='网站配置'))
    admin.add_view(VisitorModelView(Visitor, db.session, name='访客统计'))
    
    return admin
