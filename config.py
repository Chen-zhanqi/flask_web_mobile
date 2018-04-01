"""配置文件"""
'''
@Time    : 2018/4/1 上午10:37
@Author  : scrappy_zhang
@File    : config.py
'''

import os
import redis


BASEDIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # 秘钥
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard to guess string'
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    IHOME_MAIL_SUBJECT_PREFIX = '[iHome]'
    IHOME_MAIL_SENDER = 'iHome Admin <a7478317@163.com>'
    IHOME_ADMIN = os.environ.get('IHOME_ADMIN') or 'a7478317@163.com'

    # SQLALCHEMY_TRACK_MODIFICATION = False
    # 配置redis数据库
    REDIS_HOST = '127.0.0.1'
    REDIS_PORT = '6379'

    # 配置session数据存储到redis数据库
    SESSION_TYPE = 'redis'
    # 指定存储session数据的redis的位置
    SEESION_REDIS = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT)
    # 开启session数据的签名，意思是让session数据不以明文形式存储
    SESSION_USE_SIGNER = True
    # 設置session的会话的超时时长 ：一天
    PERMANENT_SESSION_LIFETIME = 3600 * 24


    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    """开发模式下的配置"""
    DEBUG = True
    MAIL_SERVER = 'smtp.163.com'
    MAIL_PORT = 25
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or 'a7478317'
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or 'hitzzy123'
    # SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
    #                           'sqlite:///' + os.path.join(BASEDIR, 'data-dev.sqlite')
    # 使用mysql
    # 配置mysql数据库:开发中使用真实IP
    SQLALCHEMY_DATABASE_URI = 'mysql://root:hitzzy@127.0.0.1:3306/ihome'
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    # SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
    #                           'sqlite:///' + os.path.join(BASEDIR, 'data-test.sqlite')
    SQLALCHEMY_DATABASE_URI = 'mysql://root:hitzzy@127.0.0.1:3306/ihome_test'


class ProductionConfig(Config):
    """生产环境配置"""
    # SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
    #                           'sqlite:///' + os.path.join(BASEDIR, 'data.sqlite')
    SQLALCHEMY_DATABASE_URI = 'mysql://root:hitzzy@127.0.0.1:3306/ihome_production'


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,

    'default': DevelopmentConfig
}
