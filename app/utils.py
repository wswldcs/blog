import requests
import math
from flask import current_app
from datetime import datetime
import re

def get_visitor_info(ip_address):
    """获取访客地理信息"""
    try:
        # 使用ipinfo.io获取地理信息
        token = current_app.config.get('IPINFO_TOKEN')
        if token:
            url = f"https://ipinfo.io/{ip_address}?token={token}"
        else:
            url = f"https://ipinfo.io/{ip_address}"
        
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            
            # 解析经纬度
            loc = data.get('loc', '').split(',')
            latitude = float(loc[0]) if len(loc) > 0 and loc[0] else None
            longitude = float(loc[1]) if len(loc) > 1 and loc[1] else None
            
            # 计算与博主的距离
            distance = None
            if latitude and longitude:
                author_lat = current_app.config.get('AUTHOR_LATITUDE')
                author_lng = current_app.config.get('AUTHOR_LONGITUDE')
                if author_lat and author_lng:
                    distance = calculate_distance(latitude, longitude, author_lat, author_lng)
            
            return {
                'country': data.get('country'),
                'city': data.get('city'),
                'latitude': latitude,
                'longitude': longitude,
                'distance': distance
            }
    except Exception as e:
        print(f"Error getting visitor info: {e}")
    
    return {}

def calculate_distance(lat1, lon1, lat2, lon2):
    """计算两点间的距离（公里）"""
    try:
        # 使用Haversine公式计算距离
        R = 6371  # 地球半径（公里）
        
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        distance = R * c
        return round(distance, 2)
    except:
        return None

def get_weather_info(city='Beijing'):
    """获取天气信息"""
    try:
        api_key = current_app.config.get('WEATHER_API_KEY')
        if not api_key:
            return None
        
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang=zh_cn"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            return {
                'temperature': round(data['main']['temp']),
                'description': data['weather'][0]['description'],
                'icon': data['weather'][0]['icon'],
                'humidity': data['main']['humidity'],
                'pressure': data['main']['pressure'],
                'wind_speed': data['wind']['speed']
            }
    except Exception as e:
        print(f"Error getting weather info: {e}")
    
    return None

def create_slug(title):
    """从标题创建URL友好的slug"""
    # 移除特殊字符，保留中文、英文、数字
    slug = re.sub(r'[^\w\s-]', '', title.strip())
    # 替换空格为连字符
    slug = re.sub(r'[-\s]+', '-', slug)
    return slug.lower()

def truncate_text(text, length=150):
    """截断文本"""
    if len(text) <= length:
        return text
    return text[:length] + '...'

def format_datetime(dt, format='%Y-%m-%d %H:%M'):
    """格式化日期时间"""
    if dt:
        return dt.strftime(format)
    return ''

def register_template_filters(app):
    """注册模板过滤器"""
    
    @app.template_filter('datetime')
    def datetime_filter(dt, format='%Y-%m-%d %H:%M'):
        return format_datetime(dt, format)
    
    @app.template_filter('date')
    def date_filter(dt):
        return format_datetime(dt, '%Y-%m-%d')
    
    @app.template_filter('truncate')
    def truncate_filter(text, length=150):
        return truncate_text(text, length)
    
    @app.template_filter('markdown')
    def markdown_filter(text):
        import markdown
        return markdown.markdown(text, extensions=['codehilite', 'fenced_code', 'tables'])

    @app.template_filter('strftime')
    def strftime_filter(dt, format='%Y'):
        if dt:
            return dt.strftime(format)
        return ''

    @app.template_filter('nl2br')
    def nl2br_filter(text):
        """将换行符转换为HTML的<br>标签"""
        if text:
            from markupsafe import Markup
            return Markup(text.replace('\n', '<br>'))
        return ''

def allowed_file(filename, allowed_extensions={'png', 'jpg', 'jpeg', 'gif', 'webp'}):
    """检查文件扩展名是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def get_file_size(file_path):
    """获取文件大小（MB）"""
    try:
        import os
        size = os.path.getsize(file_path)
        return round(size / (1024 * 1024), 2)
    except:
        return 0
