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

import logging


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