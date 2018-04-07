"""订单处理"""
'''
@Time    : 2018/4/6 下午9:43
@Author  : scrappy_zhang
@File    : orders.py
'''
import logging
import datetime

from app.order import order
from app.utils.common import login_required
from app.utils.response_code import RET

from app.models import Order, House
from app import db
from app import redis_store

from flask import request, jsonify, g


@order.route('', methods=["POST"])
@login_required
def add_order():
    """
    添加订单
    :return:
    """
    # 1. 获取到当前用户的id
    user_id = g.user_id

    # 2. 获取到传入的参数
    params = request.get_json()
    house_id = params.get('house_id')
    start_date_str = params.get('start_date')
    end_date_str = params.get('end_date')

    # 3. 校验参数
    if not all([house_id, start_date_str, end_date_str]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')
    try:
        start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = datetime.datetime.strptime(end_date_str, "%Y-%m-%d")
        assert start_date < end_date, Exception('开始日期大于结束日期')
        # 计算出入住天数
        days = (end_date - start_date).days
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    # 4. 判断房屋是否存在
    house = House.query.get(house_id)
    if not house:
        return jsonify(errno=RET.NODATA, errmsg='房屋不存在')

    # 5. 判断房屋是否是当前登录用户的
    if user_id == house.user_id:
        return jsonify(errno=RET.ROLEERR, errmsg='不能预订自己的房屋')

    # 6. 查询是否存在冲突的订单
    try:
        filters = [Order.house_id == house_id, Order.begin_date < end_date, Order.end_date > start_date]
        count = Order.query.filter(*filters).count()
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据查询错误')
    if count > 0:
        return jsonify(errno=RET.DATAERR, errmsg='该房屋已被预订')
    amount = days * house.price

    # 7. 生成订单的模型
    new_order = Order()
    new_order.user_id = user_id
    new_order.house_id = house_id
    new_order.begin_date = start_date
    new_order.end_date = end_date
    new_order.days = days
    new_order.house_price = house.price
    new_order.amount = amount

    try:
        db.session.add(new_order)
        db.session.commit()
    except Exception as e:
        logging.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='数据保存出错')

    return jsonify(errno=RET.OK, errmsg='OK', data={"order_id": new_order.id})


# 接单和拒单
@order.route('/<order_id>/status', methods=['PUT'])
@login_required
def set_order_status(order_id):

    # 1. 获取当前用户id
    user_id = g.user_id

    # 2. 获取参数&判断参数
    params = request.get_json()
    action = params.get('action')
    if action not in ("accept", "reject"):
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    # 3. 通过订单id查询出订单模型
    try:
        order = Order.query.filter(Order.id == order_id, Order.status == "WAIT_ACCEPT").first()
        house = order.house
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询数据错误')

    # 判断订单是否存在并且当前房屋的用户id是当前用户的id
    if not order or house.user_id != user_id:
        return jsonify(errno=RET.NODATA, errmsg='数据有误')

    if action == "accept":
        # 7.接单
        order.status = "WAIT_COMMENT"
    elif action == "reject":
        # 7.获取拒单原因
        reason = params.get("reason")
        if not reason:
            return jsonify(errno=RET.PARAMERR, errmsg="未填写拒单原因")

        # 设置状态为拒单并且设置拒单原因
        order.status = "REJECTED"
        order.comment = reason

    # 8.保存到数据库
    try:
        db.session.add(order)
        db.session.commit()
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg="保存订单状态失败")

    return jsonify(errno=RET.OK, errmsg="OK")


@order.route('/<order_id>/comment', methods=["PUT"])
@login_required
def set_order_comment(order_id):
    """
    评论订单
    :param order_id:
    :return:
    """

    # 获取参数&判断参数
    params = request.get_json()
    comment = params.get('comment')
    if not comment:
        return jsonify(errno=RET.PARAMERR, errmsg='请输入评论内容')

    # 通过订单id查询出订单模型
    try:
        wait_comment_order = Order.query.filter(Order.id == order_id, Order.status == "WAIT_COMMENT").first()
        wait_comment_house = wait_comment_order.house
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询数据错误')

    # 更新数据
    wait_comment_house.order_count += 1
    wait_comment_order.status = "COMPLETE"
    wait_comment_order.comment = comment

    # 更新数据库
    try:
        db.session.commit()
    except Exception as e:
        logging.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='更新数据库失败')

    # 删除redis中缓存的房屋详情信息,因为房屋详情信息已经更新
    try:
        redis_store.delete('house_info_' + wait_comment_house.id)
    except Exception as e:
        logging.error(e)

    return jsonify(errno=RET.OK, errmsg='OK')