function hrefBack() {
    history.go(-1);
}

function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

function decodeQuery(){
    var search = decodeURI(document.location.search);
    return search.replace(/(^\?)/, '').split('&').reduce(function(result, item){
        values = item.split('=');
        result[values[0]] = values[1];
        return result;
    }, {});
}

function showErrorMsg() {
    $('.popup_con').fadeIn('fast', function() {
        setTimeout(function(){
            $('.popup_con').fadeOut('fast',function(){}); 
        },1000) 
    });
}

$(document).ready(function(){
    // 判断用户是否登录
    $.get('/user/session', function (resp) {
        if ("0" != resp.errno) {
            location.href = '/'
        }
    }, 'json');
    $(".input-daterange").datepicker({
        format: "yyyy-mm-dd",
        startDate: "today",
        language: "zh-CN",
        autoclose: true
    });
    $(".input-daterange").on("changeDate", function(){
        var startDate = $("#start-date").val();
        var endDate = $("#end-date").val();

        if (startDate && endDate && startDate > endDate) {
            showErrorMsg("日期有误，请重新选择!");
        } else {
            var sd = new Date(startDate);
            var ed = new Date(endDate);
            days = (ed - sd)/(1000*3600*24) + 1;
            var price = $(".house-text>p>span").html();
            var amount = days * parseFloat(price);
            $(".order-amount>span").html(amount.toFixed(2) + "(共"+ days +"晚)");
        }
    });
    var queryData = decodeQuery();
    var houseId = queryData["hid"];

    // 获取房屋的基本信息
    $.get("/house/" + houseId, function(resp){
        if (0 == resp.errno) {
            $(".house-info>img").attr("src", resp.data.house.img_urls[0]);
            $(".house-text>h3").html(resp.data.house.title);
            $(".house-text>p>span").html((resp.data.house.price/100.0).toFixed(0));
        }
    });
    // 订单提交
    $(".submit-btn").on("click", function() {
        if ($(".order-amount>span").html()) {
            //1. 使按钮失效，防止重复点击提交订单
            $(this).prop("disabled", true);
            //2. 获取参数
            var startDate = $("#start-date").val();
            var endDate = $("#end-date").val();
            var data = {
                "house_id":houseId,
                "start_date":startDate,
                "end_date":endDate
            };
            //3. 发送请求
            $.ajax({
                url:"/order",
                type:"POST",
                data: JSON.stringify(data),
                contentType: "application/json",
                dataType: "json",
                headers:{
                    "X-CSRFToken":getCookie("csrf_token")
                },
                success: function (resp) {
                    $(this).prop("disabled", false);
                    if ("4101" == resp.errno) {
                        location.href = "/login.html";
                    } else if ("4004" == resp.errno) {
                        alert("房间已被抢定，请重新选择日期！");
                    } else if ("0" == resp.errno) {
                        location.href = "/orders.html";
                    }
                }
            });
        }
    });
});
