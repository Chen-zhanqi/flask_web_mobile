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
    // TODO: 在页面加载完毕向后端查询用户的信息

    // 管理上传用户头像表单的行为
    $("#form-avatar").submit(function (e) {
        //1.禁止浏览器对于表单的默认行为
        e.preventDefault();
        //2.发送上传图像ajax请求
        $(this).ajaxSubmit({
            url:"/user/avatar",
            type:"post",
            headers:{
                "X-CSRFToken":getCookie("csrf-token")
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
    })
    // TODO: 管理用户名修改的逻辑

})

