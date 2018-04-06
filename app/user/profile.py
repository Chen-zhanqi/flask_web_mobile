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

from app.models import User, House
from app import db, constants


@user.route('/users', methods=['GET'])
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
        login_user = User.query.filter_by(id=user_id).first()
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据查询错误")
    if user is None:
        return jsonify(errno=RET.USERERR, errmsg="用户不存在")

    return jsonify(errno=RET.OK, errmsg="OK", data=login_user.to_dict())


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


@user.route("/name", methods=['POST'])
@login_required
def set_user_name():
    """
    设置用户名
    1.获取前端提交的数据,并判断数据是否有值
    2.查询出指定user并更新 `name` 属性
    3.返回修改结果
    :return:
    """
    # 1.获取前端数据
    json_dict = request.get_json()
    name = json_dict['name']
    if name is None:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 2.查询出指定user并更新name属性
    try:
        User.query.filter_by(id=g.user_id).update({'name': name})
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='更新数据出错')
    else:
        # 3.返回修改结果
        return jsonify(errno=RET.OK, errmsg='修改成功')


@user.route("/auth", methods=['POST'])
@login_required
def set_auth():
    """
    实名认证
    :return:
    """
    # 1. 获取参数并校验
    json_dict = request.get_json()
    real_name = json_dict['real_name']
    id_card = json_dict['id_card']
    if not all([real_name, id_card]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')
    # 2. 获取当前用户id并更新数据
    user_id = g.user_id
    try:
        User.query.filter_by(id=user_id).update({'real_name': real_name, 'id_card': id_card})
        db.session.commit()
    except Exception as e:
        logging.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='认证信息保存失败')
    else:
        return jsonify(errno=RET.OK, errmsg='认证信息保存成功')


@user.route('/user/auth')
@login_required
def get_auth():
    """
    获取用户实名认证信息
    :return:
    """
    # 1. 获取用户id
    user_id = g.user_id
    # 2. 查询用户信息
    try:
        login_user = User.query.filter_by(id=user_id).first()
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据查询错误')

    # 如果用户不存在
    if login_user is None:
        return jsonify(errno=RET.SESSIONERR, errmsg='用户不存在')
    # 3. 返回信息
    return jsonify(errno=RET.OK, errmsg='OK', data=login_user.auth_to_dict())


@user.route('/houses')
@login_required
def user_houses():
    """
    获取用户房源信息
    :return:
    """
    # 1.获取用户id
    user_id = g.user_id
    # 2.查询用户房源信息
    try:
        houses = House.query.filter(House.user_id == user_id).all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询数据失败")

    house_li = []
    for house in houses:
        house_li.append(house.to_basic_dict())
    # 3. 返回数据
    return jsonify(errno=RET.OK, errmsg="OK", data=house_li)

