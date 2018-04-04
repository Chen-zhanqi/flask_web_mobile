"""提供用户中心数据"""

'''
@Time    : 2018/4/4 上午11:12
@Author  : scrappy_zhang
@File    : profile.py
'''

import logging

from app.user import user
from flask import request, current_app, jsonify, g

from app.utils.response_code import RET
from app.utils.image_storage import storage
from app.utils.common import login_required

from app.models import User
from app import db, constants


@user.route('/users')
@login_required
def get_user_profile():
    """
    获取个人信息
    :return:
    """
    # 1.获取当前登录用户id
    user_id = g.user_id
    # 2.查询该用户
    try:
        user = User.query.filter_by(id=user_id).first()
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据查询错误")
    if user is None:
        return jsonify(errno=RET.USERERR, errmsg="用户不存在")

    return jsonify(errno=RET.OK, errmsg="OK", data=user.to_dict())


@user.route("/avatar", methods=['POST'])
@login_required
def upload_avatar():
    """
        上传用户头像
        1.取到客户端上传的文件,并判断
        2.使用七牛上传文件
        3.更新当前用户头像地址信息
        4.返回用户头像地址
        :return:
     """
    # 1.获取要上传的文件
    try:
        avatar_file = request.files.get("avatar").read()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="传入参数有误")

    # 2. 上传文件
    try:
        image_name = storage(avatar_file)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg='上传头像失败')

    # 3. 更新当前用户头像地址信息
    user_id = g.user_id

    try:
        User.query.filter_by(id=user_id).update({'avatar_url': image_name})
        db.session.commit()  # 提交url到数据库
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='图片保存失败')
    else:
        # 4. 返回用户头像地址
        avatar_url = constants.QINIU_DOMIN_PREFIX + image_name
        return jsonify(errno=RET.OK, errmsg='图片上传成功', data={"avatar_url": avatar_url})
