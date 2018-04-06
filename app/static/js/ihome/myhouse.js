$(document).ready(function(){
    // 对于发布房源，只有认证后的用户才可以，所以先判断用户的实名认证状态
    // 查询用户的实名认证信息
    $.get("user/auth", function (resp) {
        if (resp.errno == "0") {
            // 判断是否有认证信息
            if (!(resp.data.real_name && resp.data.id_card)) {
                $(".auth-warn").show();
            }else {
                // 如果用户已实名认证,那么就去请求之前发布的房源
                $.get("user/houses", function (resp) {
                    if (resp.errno == "0") {
                        $("#houses-list").html(template("houses-list-tmpl", {"houses": resp.data}))
                    }
                })
            }
        }else if (resp.errno == "4101") {
            location.href = "/login.html"
        }else {
            alert(resp.errmsg)
        }
    })
})
