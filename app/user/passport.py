"""注册功能实现"""
'''
@Time    : 2018/4/6 上午10:02
@Author  : scrappy_zhang
@File    : passport.py
'''

import logging
import re

from app.user import user
from flask import request, jsonify, session

from app.utils.response_code import RET
from app import redis_store

from app.models import User
from app import db


@user.route('/users', methods=['POST'])
def register():
    """
    1. 获取参数
    2. 判断是否为空
    3. 获取redis保存的短信验证码
    4. 验证对比,并删除验证码
    5. 将用户数据保存到数据库,并缓存到Session
    6. 返回用户信息
    :return:
    """
    # 1.获取参数 手机号 密码 短信验证码
    dict_json = request.get_json()
    if not dict_json:
        return jsonify(errno=RET.PARAMERR, errmsg='参数不完整')
    mobile = dict_json['mobile']
    sms_code = dict_json['phonecode']
    password = dict_json['password']

    # 2. 判断是否参数为空
    if not all([mobile, sms_code, password]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数不完整')

    # 3.获取redis中保存的短信验证码
    try:
        real_sms_code = redis_store.get('SMSCode_' + mobile)
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='短信验证码读取异常')

    if not real_sms_code:
        return jsonify(errno=RET.DATAERR, errmsg='短信验证码已过期')

    # 4. 验证对比,并删除验证码
    if real_sms_code != str(sms_code):
        return jsonify(errno=RET.DATAERR, errmsg='短信验证码无效')

    # 删除短信验证码
    try:
        redis_store.delete('SMSCode_' + mobile)
    except Exception as e:
        logging.error(e)

    # 5. 将用户数据保存到数据库
    new_user = User(mobile=mobile, name=mobile)
    new_user.password = password

    try:
        db.session.add(new_user)
        db.session.commit()
    except Exception as e:
        logging.error(e)
        db.rollback()
        return jsonify(errno=RET.DATAEXIST, errmsg='手机号已存在')
        # 缓存到session
    session['user_id'] = new_user.id
    session['mobile'] = mobile
    session['name'] = mobile

    # 返回用户信息
    return jsonify(errno=RET.OK, errmsg='OK')


# 登录 /session
@user.route('/sessions', methods=['POST'])
def login():
    """
    1.获取参数
    2.判断参数是否有值
    3.判断手机号是否合法
    4.查询数据库用户信息
    5.用户不存在判断
    6.校验密码
    7.使用session保存用户信息
    :return:
    """

    # 1.获取参数
    dict_json = request.get_json()
    mobile = dict_json.get('mobile')
    password = dict_json.get('password')
    # 2.判断参数是否有值
    if not all([mobile, password]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")

    # 3.判断手机号是否合法
    if not re.match(u"^1[34578]\d{9}$", mobile):
        return jsonify(errno=RET.PARAMERR, errmsg="手机号格式不正确")

    # 4.查询数据库用户信息
    try:
        login_user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库查询错误')

    # 5.用户不存在判断
    if login_user is None:
        return jsonify(errno=RET.USERERR, errmsg='用户不存在')

    # 6.校验密码
    if not login_user.check_password(password):
        return jsonify(errno=RET.LOGINERR, errmsg='密码错误')

    # 7.使用session保存用户信息
    session['user_id'] = login_user.id
    session['mobile'] = login_user.mobile
    session['name'] = login_user.name

    return jsonify(errno=RET.OK, errmsg='登录成功')
