from rich_blog_app import app, Project

with app.app_context():
    projects = Project.query.all()
    print('Projects in database:')
    for p in projects:
        print(f'ID: {p.id}, Name: {p.name}, Featured: {p.is_featured}')
    
    if not projects:
        print('No projects found in database')
