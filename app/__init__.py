"""应用初始化"""

'''
@Time    : 2018/4/1 上午10:37
@Author  : scrappy_zhang
@File    : __init__.py.py
'''

from flask import Flask
import pymysql
pymysql.install_as_MySQLdb()
from flask_sqlalchemy import SQLAlchemy
import redis

from flask_wtf.csrf import CSRFProtect
from flask_session import Session
from flask_bootstrap import Bootstrap
from flask_mail import Mail

from config import config
from app.utils.common import RegexConverter

db = SQLAlchemy()
bootstrap = Bootstrap()
mail = Mail()

# 创建可以被外界导入的连接到redis数据库的对象
redis_store = None


def create_app(config_name):
    app = Flask(__name__)
    # 加载配置
    app.config.from_object(config[config_name])

    # 创建各模块对象
    config[config_name].init_app(app)
    db.init_app(app)
    mail.init_app(app)
    bootstrap.init_app(app)

    global redis_store
    # decode_responses=True: 解决获取的值类型是bytes字节问题
    redis_store = redis.StrictRedis(host=config[config_name].REDIS_HOST, port=config[config_name].REDIS_PORT, db=0, decode_responses=True)

    # 开启CSRF保护
    CSRFProtect(app)

    # 使用session在flask扩展实现将session数据存储在redis
    Session(app)

    # 需要现有路由转换器，后面html_blue中才可以直接匹配
    app.url_map.converters['re'] = RegexConverter

    # 注册蓝本
    from app.user import user
    app.register_blueprint(user, url_prefix='/user')
    #注册自定义静态文件蓝本
    from app.web_html import html_blue
    app.register_blueprint(html_blue)

    return app