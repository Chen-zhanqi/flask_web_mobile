"""视图共用的自定义路由转换器"""
'''
@Time    : 2018/4/1 下午4:46
@Author  : scrappy_zhang
@File    : common.py
'''

from werkzeug.routing import BaseConverter


class RegexConverter(BaseConverter):
    """自定义路由转换器"""

    def __init__(self, url_map, *args):
        super(RegexConverter, self).__init__(url_map)

        self.regex = args[0]
