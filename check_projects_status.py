from rich_blog_app import app, Project

with app.app_context():
    projects = Project.query.all()
    print('所有项目:')
    for p in projects:
        print(f'ID: {p.id}, 名称: {p.name}, 精选: {p.is_featured}')
    
    print('\n精选项目:')
    featured_projects = Project.query.filter_by(is_featured=True).all()
    for p in featured_projects:
        print(f'ID: {p.id}, 名称: {p.name}')
    
    if not featured_projects:
        print('没有精选项目，将显示占位内容')
