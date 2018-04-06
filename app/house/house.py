"""城区信息"""
'''
@Time    : 2018/4/6 下午5:17
@Author  : scrappy_zhang
@File    : house.py
'''
# 城区信息数据查询，城区信息数据缓存

import logging
import re

from flask import request, jsonify, g, session

from app.house import houses

from app.models import Area, House, Facility, HouseImage
from app import db

from app.utils.response_code import RET
from app.utils.image_storage import storage
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


@houses.route('', methods=['POST'])
@login_required
def save_new_house():
    """
    前端发送过来的json数据
    {
        "title":"",
        "price":"",
        "area_id":"1",
        "address":"",
        "room_count":"",
        "acreage":"",
        "unit":"",
        "capacity":"",
        "beds":"",
        "deposit":"",
        "min_days":"",
        "max_days":"",
        "facility":["7","8"]
    }

    :return:
    """
    # 1.获取用户id
    user_id = g.user_id
    # 2. 获取数据
    json_dict = request.get_json()
    if not json_dict:
        return jsonify(errno=RET.PARAMERR, errmsg='请输入参数')
    # 3.参数校验
    title = json_dict.get('title')  # 房屋标题
    price = json_dict.get('price')  # 每晚价格
    address = json_dict.get('address')  # 所在城区
    area_id = json_dict.get('area_id')  # 详细地址
    room_count = json_dict.get('room_count')  # 出租房间数目
    acreage = json_dict.get('acreage')  # 房屋面积
    unit = json_dict.get('unit')  # 户型描述
    capacity = json_dict.get('capacity')  # 宜住人数
    beds = json_dict.get('beds')  # 卧床配置
    deposit = json_dict.get('deposit')  # 押金数额
    min_days = json_dict.get('min_days')  # 最少入住天数
    max_days = json_dict.get('max_days')  # 最多入住天数

    if not all(
            [title, price, address, area_id, room_count, acreage, unit, capacity, beds, deposit, min_days, max_days]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数缺失')

    # 数字信息处理，保证信息小数点后两位不丢失
    try:
        price = int(float(price) * 100)
        deposit = int(float(deposit) * 100)
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    # 4. 设置数据到模型
    house = House()
    house.user_id = user_id
    house.area_id = area_id
    house.title = title
    house.price = price
    house.address = address
    house.room_count = room_count
    house.acreage = acreage
    house.unit = unit
    house.capacity = capacity
    house.beds = beds
    house.deposit = deposit
    house.min_days = min_days
    house.max_days = max_days

    # 5. 设置设施信息
    facility = json_dict.get('facility')
    if facility:
        facilities = Facility.query.filter(Facility.id.in_(facility)).all()
        house.facilities = facilities
    # 6.向数据库提交信息
    try:
        db.session.add(house)
        db.session.commit()
    except Exception as e:
        logging.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='保存房屋信息失败')

    return jsonify(errno=RET.OK, errmsg='OK', data={'house_id': house.id})


@houses.route('/<int:house_id>/images', methods=['POST'])
@login_required
def upload_house_pic(house_id):
    """
    上传房源图片
    :param house_id: 房源id
    :return:
    """
    # 1. 获取图片文件
    image_file = request.files.get('house_image')
    if not image_file:
        return jsonify(errno=RET.PARAMERR, errmsg="未选择图片")

    # 2. 尝试查询房屋数据
    try:
        house = House.query.filter_by(id=house_id).first()
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询房屋数据失败')
    if not house:
        return jsonify(errno=RET.NODATA, errmsg='未查询到对应房屋')

    # 3. 使用七牛上传图片
    image_data = image_file.read()
    try:
        image_name = storage(image_data)
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg="上传图片失败")

    # 4. 判断房屋是否有主图片，如果没有，则设置
    if not house.index_image_url:
        house.index_image_url = image_name
        db.session.add(house)

    # 5. 生成房屋图片模型并保存至数据数据库
    house_image = HouseImage()
    house_image.house_id = house_id
    house_image.url = image_name

    try:
        db.session.add(house_image)
        db.session.commit()
    except Exception as e:
        logging.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存房屋图片失败")
    # 删除缓存的前五房屋信息
    try:
        redis_store.delete("home_page_house_info")
    except Exception as e:
        logging.error(e)
        db.session.rollback(e)
        return jsonify(errno=RET.DBERR, errmsg="删除首页房屋缓存失败")
    # 返回数据
    image_url = constants.QINIU_DOMIN_PREFIX + image_name
    return jsonify(errno=RET.OK, errmsg='OK', data={'url': image_url})


@houses.route('/<int:house_id>')
def house_detail(house_id):
    """
    房屋详情
    :param house_id:
    :return:
    """
    # 前端在房屋详情页面展示时，如果浏览页面的用户不是该房屋的房东，则展示预定按钮，否则不展示，
    # 所以需要后端返回登录用户的user_id
    # 尝试获取用户登录的信息，若登录，则返回给前端登录用户的user_id，否则返回user_id=-1
    # 判断参数是否有值
    if not house_id:
        return jsonify(errno=RET.PARAMERR, errmsg='参数缺失')

    user_id = session.get('user_id', -1)

    # 先从redis缓存中取
    try:
        house_info = redis_store.get('house_info_' + house_id)
    except Exception as e:
        house_info = None
        logging.error(e)

    # 如果有值,那么返回数据
    if house_info:
        logging.info('get house info from redis')
        return jsonify(errno=RET.OK, errmsg='OK', data={"user_id": user_id, "house": eval(house_info)})

    # 没有从缓存中取到,查询数据)库
    house = House.query.filter_by(id=house_id).first()
    if not house:
        return jsonify(errno=RET.NODATA, errmsg='未查询到房屋信息')

    # 将数据缓存到redis中
    house_dict = house.to_full_dict()
    try:
        redis_store.set('house_info_'+house_id, house_dict, constants.HOUSE_DETAIL_REDIS_EXPIRE_SECOND)
    except Exception as e:
        logging.error(e)

    # 返回数据
    return jsonify(errno=RET.OK, errmsg='OK', data={"user_id": user_id, "house": house_dict})


@houses.route('/index')
def house_index():
    """
    获取首页推荐房屋信息
    :return:
    """
    # 先从redis中加载数据
    try:
        house_info = redis_store.get('home_page_house_info')
    except Exception as e:
        house_info = None
        logging.error(e)
    if house_info:
        return jsonify(errno=RET.OK, errmsg='OK', data=eval(house_info))

    # 从数组库中加载数据
    try:
        index_houses = House.query.order_by(House.order_count.desc()).limit(constants.HOME_PAGE_MAX_HOUSES).all()
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据查询失败')

    # 如果数据库中没有数据
    if not index_houses:
        return jsonify(errno=RET.NODATA, errmsg='未查询到数据')

    # 拼接到数组中
    houses_dict = []
    for house in index_houses:
        houses_dict.append(house.to_basic_dict())

    # 缓存到redis中
    try:
        redis_store.set('home_page_house_info', houses_dict,constants.HOME_PAGE_DATA_REDIS_EXPIRES)
    except Exception as e:
        logging.error(e)

    # 返回数据
    return jsonify(errno=RET.OK, errmsg='OK', data=houses_dict)