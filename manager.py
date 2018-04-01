"""manager"""
'''
@Time    : 2018/4/1 上午10:38
@Author  : scrappy_zhang
@File    : manager.py
'''
import os


from flask_script import Manager
from app import db
from flask_migrate import Migrate, MigrateCommand
from app import create_app


app = create_app(os.getenv('IHOME_CONFIG') or 'default')

manager = Manager(app)
migrate = Migrate(app, db)

manager.add_command('db', MigrateCommand)

if __name__ == '__main__':
    print(app.url_map)
    manager.run()
