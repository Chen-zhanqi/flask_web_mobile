"""房屋模块"""
'''
@Time    : 2018/4/6 下午12:24
@Author  : scrappy_zhang
@File    : __init__.py.py
'''

from flask import Blueprint

houses = Blueprint('houses', __name__)

from app.house import house