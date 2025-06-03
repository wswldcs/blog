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

class SimpleModelView(AdminAuthMixin, ModelView):
    """简化的模型视图"""
    pass

def init_admin(app, db):
    """初始化Flask-Admin（简化版）"""
    admin = Admin(
        app,
        name='博客管理',
        template_mode='bootstrap4',
        index_view=MyAdminIndexView(),
        url='/admin'
    )
    
    # 添加简化的模型视图
    admin.add_view(SimpleModelView(User, db.session, name='用户管理'))
    admin.add_view(SimpleModelView(Post, db.session, name='文章管理'))
    admin.add_view(SimpleModelView(Category, db.session, name='分类管理'))
    admin.add_view(SimpleModelView(Tag, db.session, name='标签管理'))
    admin.add_view(SimpleModelView(Comment, db.session, name='评论管理'))
    admin.add_view(SimpleModelView(Link, db.session, name='友情链接'))
    admin.add_view(SimpleModelView(Project, db.session, name='项目管理'))
    admin.add_view(SimpleModelView(Timeline, db.session, name='时间线'))
    admin.add_view(SimpleModelView(SiteConfig, db.session, name='网站配置'))
    admin.add_view(SimpleModelView(Visitor, db.session, name='访客统计'))
    
    return admin
