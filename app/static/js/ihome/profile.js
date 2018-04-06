function showSuccessMsg() {
    $('.popup_con').fadeIn('fast', function() {
        setTimeout(function(){
            $('.popup_con').fadeOut('fast',function(){}); 
        },1000) 
    });
}

function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

$(document).ready(function () {
    // 在页面加载完毕向后端查询用户的信息
    $.get("/user/users", function(resp){
        // 用户未登录
        if ("4101" == resp.errno) {
            location.href = "/login.html";
        }
        // 查询到了用户的信息
        else if ("0" == resp.errno) {
            $("#user-avatar").attr("src", resp.data.avartar);
            $("#user-name").val(resp.data.name);
            if (resp.data.avatar) {
                $("#user-avatar").attr("src", resp.data.avatar);
            }
        }
    }, "json");
    // 管理上传用户头像表单的行为
    $("#form-avatar").submit(function (e) {
        //1.禁止浏览器对于表单的默认行为
        e.preventDefault();
        //2.发送上传图像ajax请求
        $(this).ajaxSubmit({
            url:"/user/avatar",
            type:"post",
            headers: {
            "X-CSRFToken": getCookie('csrf_token')
            },
            dataType: "json",
            success: function (resp) {
                if (resp.errno == "0") {
                    // 表示上传成功， 将头像图片的src属性设置为图片的url
                    $("#user-avatar").attr("src", resp.data.avatar_url);
                } else if (resp.errno == "4101") {
                    // 表示用户未登录，跳转到登录页面
                    location.href = "/login.html";
                } else {
                    alert(resp.errmsg);
                }
            }
        })
    });
    // 管理用户名修改的逻辑
    $("#form-name").submit(function (e) {
        //1.组织默认表单行为
        e.preventDefault();
        //2.获取用户名参数并校验
        var name = $("#user-name").val();
        if (!name) {
            alert("请填写用户名！");
            return;
        }
        //3.向后端发送数据
        $.ajax({
            url:"/user/name",
            type:"post",
            data: JSON.stringify({name: name}),
            contentType: "application/json",
            headers: {
            "X-CSRFToken": getCookie('csrf_token')
            },
            dataType: "json",
            success: function (data) {
                if ("0" == data.errno) {
                    $(".error-msg").hide();
                    showSuccessMsg();
                } else if ("4001" == data.errno) {
                    $(".error-msg").show();
                } else if ("4101" == data.errno) {
                    location.href = "/login.html";
                }
            }

        })
    })

});

