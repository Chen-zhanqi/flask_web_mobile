"""注册功能实现"""
'''
@Time    : 2018/4/6 上午10:02
@Author  : scrappy_zhang
@File    : passport.py
'''

import logging

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
    print("进入了register")
    # 1.获取参数 手机号 密码 短信验证码
    dict_json = request.get_json()
    if not dict_json:
        return jsonify(errno=RET.PARAMERR, errmsg='参数不完整')
    print(dict_json)
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
    if real_sms_code.decode() != str(sms_code):
        return jsonify(errno=RET.DATAERR, errmsg='短信验证码无效')

    # 删除短信验证码
    try:
        redis_store.delete('SMSCode_' + mobile)
    except Exception as e:
        logging.error(e)

    # 5. 将用户数据保存到数据库
    new_user = User(mobile=mobile, name=mobile)
    new_user.password_hash = password

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


