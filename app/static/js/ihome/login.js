function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}
//登出操作
function logout() {
    $.ajax({
        url:"/user/session",
        type:"delete",
        header:{
            "X-CSRFToken":getCookie("csrf_token")
        },
        dataType:"json",
        success:function (resp) {
            if ("0" == resp.errno){
                location.href = "/index.html";
            }
        }
    })
}

$(document).ready(function() {
    $("#mobile").focus(function(){
        $("#mobile-err").hide();
    });
    $("#password").focus(function(){
        $("#password-err").hide();
    });
    // 登录表单提交操作
    $(".form-login").submit(function(e){
        //1.阻止默认的表单行为
        e.preventDefault();
        //2.获取参数值
        mobile = $("#mobile").val();
        passwd = $("#password").val();
        //3.参数完整性校验
        if (!mobile) {
            $("#mobile-err span").html("请填写正确的手机号！");
            $("#mobile-err").show();
            return;
        } 
        if (!passwd) {
            $("#password-err span").html("请填写密码!");
            $("#password-err").show();
            return;
        }
        //4.提取表单数据
        var data = {};
        $(".form-login").serializeArray().map(function (x) {
            data[x.name] = x.value
        });
        //5.表单数据转化为json
        var jsonData = JSON.stringify(data);
        $.ajax({
            url:"/user/session",
            type:"POST",
            data:jsonData,
            contentType:"application/json",
            dataType:"json",
            headers:{
            "X-CSRFTOKEN":getCookie("csrf_token")
            },
            success: function (resp) {
                if ("0" == resp.errno) {
                    // 登录成功，跳转到主页
                    location.href = "/";
                    return;
                }
                else {
                    // 其他错误信息，在页面中展示
                    $("#password-err span").html(data.errmsg);
                    $("#password-err").show();
                    return;
                }
            }
        })
    });
})
