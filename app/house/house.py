"""城区信息"""
'''
@Time    : 2018/4/6 下午5:17
@Author  : scrappy_zhang
@File    : house.py
'''
# 城区信息数据查询，城区信息数据缓存

import logging
import re
import datetime

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


@houses.route("", methods=['GET'])
def house_list():
    """
    首页搜索房屋
    :return:
    """
    # 获取所有的参数
    args = request.args
    area_id = args.get('aid', '')
    start_date_str = args.get('sd', '')
    end_date_str = args.get('ed', '')

    # booking(订单量), price-inc(低到高), price-des(高到低),
    sort_key = args.get('sk', 'new')
    page = args.get('p', '1')

    # 打印参数
    print("area_id=%s,sd=%s,ed=%s,sk=%s,page=%s" % (area_id, start_date_str, end_date_str, sort_key, page))

    # 参数校验
    try:
        page = int(page)
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    # 对日期进行相关处理
    try:
        start_date = None
        end_date = None
        if start_date_str:
            start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d')
        if end_date_str:
            end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d')
        # 如果开始时间大于或者等于结束时间,就报错
        print(start_date)
        print(end_date)
        if start_date and end_date:
            assert start_date < end_date, Exception('开始时间大于结束时间')
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg='日期错误')

    # 尝试从缓存获取
    try:
        redis_key = "houses_%s_%s_%s_%s" % (area_id, start_date_str, end_date_str, sort_key)
        response_data = redis_store.hget(redis_key, page)
        if response_data:
            logging.info('load data from redis')
            return jsonify(errno=RET.OK, errmsg='获取成功', data=eval(response_data))
    except Exception as e:
        logging.error(e)


    # 如果区域id存在
    if area_id:
        if sort_key == "booking":
            # 订单量从高到低
            houses_query = House.query.filter(House.area_id == area_id).order_by(House.order_count.desc())
        elif sort_key == "price-inc":
            # 价格从低到高
            houses_query = House.query.filter(House.area_id == area_id).order_by(House.price.asc())
        elif sort_key == "price-des":
            # 价格从高到低
            houses_query = House.query.filter(House.area_id == area_id).order_by(House.price.desc())
        else:
            # 默认以最新的排序
            houses_query = House.query.filter(House.area_id == area_id).order_by(House.create_time.desc())
    # 查询数据
    # houses_list = House.query.all()

    # 分页查询数据
    # 查询数据
    else:
        if sort_key == "booking":
            # 订单量从高到低
            houses_query = House.query.order_by(House.order_count.desc())
        elif sort_key == "price-inc":
            # 价格从低到高
            houses_query = House.query.order_by(House.price.asc())
        elif sort_key == "price-des":
            # 价格从高到低
            houses_query = House.query.order_by(House.price.desc())
        else:
            # 默认以最新的排序
            houses_query = House.query.order_by(House.create_time.desc())

    # 使用paginate进行分页
    house_pages = houses_query.paginate(page, constants.HOUSE_LIST_PAGE_CAPACITY, False)
    # 获取当前页对象
    houses_list = house_pages.items
    # 获取总页数
    total_page = house_pages.pages

    # 将查询结果转成字符串
    houses_dict = []
    for house_each in houses_list:
        houses_dict.append(house_each.to_basic_dict())

    # 提示 response_data 用于缓存
    response_data = {"total_page": total_page, "houses": houses_dict}
    # 如果当前page小于总页数,则表明有数据
    if page <= total_page:
        try:
            # 生成缓存用的key
            redis_key = "houses_%s_%s_%s_%s" % (area_id, start_date_str, end_date_str, sort_key)
            # 获取 redis_store 的 pipeline 对象,其可以一次可以做多个redis操作
            pipe = redis_store.pipeline()
            # 开启事务
            pipe.multi()
            # 缓存数据
            pipe.hset(redis_key, page, response_data)
            # 设置保存数据的有效期
            pipe.expire(redis_key, constants.HOUSE_LIST_REDIS_EXPIRES)
            # 提交事务
            pipe.execute()
        except Exception as e:
            logging.error(e)

    # return jsonify(errno=RET.OK, errmsg='请求成功', data={"total_page": 1, "houses": houses_dict})
    return jsonify(errno=RET.OK, errmsg='请求成功', data={"total_page": total_page, "houses": houses_dict})


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
        redis_store.set('house_info_' + house_id, house_dict, constants.HOUSE_DETAIL_REDIS_EXPIRE_SECOND)
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
        redis_store.set('home_page_house_info', houses_dict, constants.HOME_PAGE_DATA_REDIS_EXPIRES)
    except Exception as e:
        logging.error(e)

    # 返回数据
    return jsonify(errno=RET.OK, errmsg='OK', data=houses_dict)
