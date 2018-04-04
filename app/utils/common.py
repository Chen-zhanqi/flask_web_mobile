"""视图共用的自定义路由转换器"""
'''
@Time    : 2018/4/1 下午4:46
@Author  : scrappy_zhang
@File    : common.py
'''

from werkzeug.routing import BaseConverter
import functools

from flask import session, jsonify, g
from app.utils.response_code import RET


class RegexConverter(BaseConverter):
    """自定义路由转换器"""

    def __init__(self, url_map, *args):
        super(RegexConverter, self).__init__(url_map)

        self.regex = args[0]


# 登录验证装饰器
def login_required(f):
    """
    用户是否登录判断装饰器
    :param f: 其装饰的函数
    :return: 装饰器
    """

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        # 从session中获取当前用户id
        user_id = session.get("user_id")

        # 如果user_id为None代表用户没有登录,直接返回未登录信息
        if user_id is None:
            return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")
        else:
            # 否则使用全局g变量记录当前用户id，并调用被装饰的函数
            g.user_id = user_id
            return f(*args, **kwargs)

    return wrapper
