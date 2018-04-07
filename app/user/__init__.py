"""用户模块"""
'''
@Time    : 2018/4/1 上午10:38
@Author  : scrappy_zhang
@File    : __init__.py.py
'''

from flask import Blueprint

user = Blueprint('user', __name__)

from app.user import verifycode, profile, passport, user_order
