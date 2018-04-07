"""订单模块"""
'''
@Time    : 2018/4/6 下午12:23
@Author  : scrappy_zhang
@File    : __init__.py.py
'''

from flask import Blueprint

order = Blueprint('order', __name__)

from app.order import orders