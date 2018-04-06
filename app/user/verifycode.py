"""user模块 业务逻辑"""
'''
@Time    : 2018/4/1 上午10:40
@Author  : scrappy_zhang
@File    : views.py
'''

from app.user import user  # 导入user蓝图

from app.utils.captcha.captcha import captcha
from app.utils.response_code import RET

from flask import request, make_response, jsonify, abort

from app import redis_store
from app import constants
from app.models import User

import logging
import re
import random
import json


@user.route('/image_code')
def get_image_code():
    """提供图片验证码
        1.接受请求，获取uuid
        2.生成图片验证码
        3.使用UUID存储图片验证码内容到redis
        4.返回图片验证码
    """
    # 1.接收请求，获取前端的uuid
    uuid = request.args.get('uuid')
    last_uuid = request.args.get('last_uuid')
    if not uuid:
        abort(403)

    # 2.生成验证码
    name, text, image = captcha.generate_captcha()

    # 3. 使用UUID存储图片验证码内容到redis
    try:
        if last_uuid:
            # 上次的uuid若还存在，删除上次的uuid对应的记录
            redis_store.delete('ImageCode:' + last_uuid)

        # 保存本次需要记录的验证码数据
        redis_store.set('ImageCode:' + uuid, text, constants.IMAGE_CODE_REDIS_EXPIRES)
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg=u'保存验证码失败')

    # 4.返回图片验证码
    response = make_response(image)
    response.headers['Content-Type'] = 'image/jpg'
    return response


@user.route("/smscode/", methods=["POST"])
def send_sms_code():
    # 1.获取参数
    # image_code = request.args['text']
    # image_code_id = request.args['id']
    param_dict = json.loads(request.get_data())
    image_code = param_dict['text']
    image_code_id = param_dict['id']
    mobile = param_dict['mobile']
    # 2.验证参数是否为空
    if not all([mobile, image_code, image_code_id]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 3. 验证手机号是否合法
    if not re.match(r"^1[34578][0-9]{9}$", mobile):
        return jsonify(errno=RET.PARAMERR, errmsg="手机号不合法")
    # 3.1 验证手机号是否已注册
    try:
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        logging.error(e)
    else:
        if user is not None:
            return jsonify(errno=RET.DBERR, errmsg='该手机已注册')

    # 4. 验证图片码
    try:
        real_image_code = redis_store.get('ImageCode_' + image_code_id)
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询数据异常")

    # 4.1 判断验证码是否存在
    if not real_image_code:
        return jsonify(errno=RET.DATAERR, errmsg="验证码已过期")
    # 4.2 比较传入的验证码和本地验证码是否一致
    if image_code.lower() != real_image_code.lower():
        return jsonify(errno=RET.DATAERR, errmsg="图片验证码错误")

    # 5.删除本地图片验证码
    try:
        redis_store.delete("ImageCode_"+image_code_id)
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DATAERR, errmsg="删除本地图片验证码失败")
    # 6. 生成短信验证码
    sms_code = "%04d" %random.randint(0, 10000)
    print("要发送的短信验证码:", sms_code)
    # 7.发送短信验证码，由云通讯完成
    return jsonify(errno=RET.OK, errmsg="发送验证码成功")