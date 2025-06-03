import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'mysql+pymysql://root:1234@localhost/aublog'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 博客配置
    BLOG_TITLE = os.environ.get('BLOG_TITLE') or 'wswldcs的个人博客'
    BLOG_SUBTITLE = os.environ.get('BLOG_SUBTITLE') or '记录生活，分享技术'
    AUTHOR_NAME = os.environ.get('AUTHOR_NAME') or 'wswldcs'
    AUTHOR_EMAIL = os.environ.get('AUTHOR_EMAIL') or 'your-email@example.com'
    
    # 地理位置配置（你的位置）
    AUTHOR_LATITUDE = float(os.environ.get('AUTHOR_LATITUDE') or '39.9042')  # 北京
    AUTHOR_LONGITUDE = float(os.environ.get('AUTHOR_LONGITUDE') or '116.4074')
    
    # API配置
    WEATHER_API_KEY = os.environ.get('WEATHER_API_KEY') or ''  # OpenWeatherMap API
    IPINFO_TOKEN = os.environ.get('IPINFO_TOKEN') or ''  # IPInfo.io token
    
    # 分页配置
    POSTS_PER_PAGE = 10
    
    # 上传配置
    UPLOAD_FOLDER = os.path.join(basedir, 'app', 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # 管理员配置
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME') or 'admin'
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD') or 'admin123'  # 请在生产环境中更改
