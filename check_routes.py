from rich_blog_app import app

with app.app_context():
    print('Registered routes:')
    for rule in app.url_map.iter_rules():
        print(f'{rule.rule} -> {rule.endpoint} ({rule.methods})')
