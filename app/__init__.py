from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_admin import Admin
from config import Config
import os

db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
admin = Admin()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    login.login_view = 'manage.login'
    login.login_message = '请先登录以访问此页面。'
    
    # 创建上传目录
    upload_dir = app.config['UPLOAD_FOLDER']
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    
    # 注册蓝图
    from app.routes.main import bp as main_bp
    app.register_blueprint(main_bp)
    
    from app.routes.admin import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/manage')
    
    from app.routes.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # 初始化Flask-Admin
    from app.admin_views_simple import init_admin
    init_admin(app, db)
    
    # 注册模板过滤器
    from app.utils import register_template_filters
    register_template_filters(app)
    
    return app

from app import models
