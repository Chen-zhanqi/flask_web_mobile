"""城区信息"""
'''
@Time    : 2018/4/6 下午5:17
@Author  : scrappy_zhang
@File    : house.py
'''
# 城区信息数据查询，城区信息数据缓存

import logging
import re

from flask import jsonify

from app.house import houses

from app.models import Area
from app import db

from app.utils.response_code import RET
from app import redis_store
from app import constants
from app.utils.common import login_required


@houses.route("/areas")
def get_areas_info():
    """
    查询城区信息
    :return:
    """
    # 0.先从缓存中去取，如果缓存中没有，再去数据库中取
    try:
        areas = redis_store.get('area_info')
    except Exception as e:
        logging.error(e)
        areas = None
    # 0.1 如果不为空，做查询操作
    if areas and len(re.findall(r'aid', areas)) > 0:
        return jsonify(errno=RET.OK, errmsg='获取成功', data=eval(areas))

    # 1.查询数据库
    try:
        areas = Area.query.all()
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='获取城区信息失败')
    # 2.组成字典，以便json
    areas_list = []
    for area in areas:
        areas_list.append(area.to_dict())

    # 0.2 存储json_areas数据到redis缓存中
    try:
        redis_store.set('area_info', areas_list, constants.AREA_INFO_REDIS_EXPIRES)
    except Exception as e:
        logging.error(e)

    # 3. 返回数据
    return jsonify(errno=RET.OK, errmsg='获取成功', data=areas_list)



