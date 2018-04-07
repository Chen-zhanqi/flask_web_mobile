"""用户订单查询"""
'''
@Time    : 2018/4/6 下午10:16
@Author  : scrappy_zhang
@File    : user_order.py
'''
import logging

from app.user import user
from flask import request, current_app, jsonify, g

from app.utils.response_code import RET
from app.utils.common import login_required

from app.models import House, Order
from app import db, constants

@user.route('/orders')
@login_required
def user_orders():
    """
    查询订单,通过参数判断要查询房东/房客的订单
    :return:
    """
    # 1. 获取用户参数
    user_id = g.user_id
    role = request.args.get('role')
    # 2. 校验参数
    if not role:
        return jsonify(errno=RET.PARAMERR, errmsg='参数有误')

    if role == "custom":
        # 查询当前自己下了哪些订单
        orders_list = Order.query.filter_by(user_id=user_id).order_by(Order.create_time.desc())
    else:
        # 查询自己房屋都有哪些订单
        houses_self = House.query.filter_by(user_id=user_id).all()
        house_ids = [house.id for house in houses_self]
        orders_list = Order.query.filter(Order.house_id.in_(house_ids)).order_by(Order.create_time.desc())

    orders_dict = []

    for order_each in orders_list:
        orders_dict.append(order_each.to_dict())
    return jsonify(errno=RET.OK, errmsg="请求成功", data={"orders": orders_dict})