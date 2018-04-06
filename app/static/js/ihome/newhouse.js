function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}
// Flask：使用 Jinja2 模板引擎，实现 Python 代码与 html 互通
// 前端：使用 art-template，实现 js 代码与 html 互通
$(document).ready(function(){
    // $('.popup_con').fadeIn('fast');
    // $('.popup_con').fadeOut('fast');

    //  在页面加载完毕之后获取区域信息
    $.get("/house/areas", function (resp) {
        if ("0" == resp.errno) {
            // 表示查询到了数据,修改前端页面
            // for (var i=0; i<resp.data.length; i++) {
            //     // 向页面中追加标签
            //     var areaId = resp.data[i].aid;
            //     var areaName = resp.data[i].aname;
            //     $("#area-id").append('<option value="'+ areaId +'">'+ areaName +'</option>');
            // }
            // 1. 初始化模板
            rendered_html = template("areas-tmpl", {areas:resp.data});
            // 2. 将模板设置到指定的标签内
            $("#area-id").html(rendered_html)

        } else {
            alert(resp.errmsg);
        }
    }, "json");
    // 处理房屋基本信息提交的表单数据
    $("#form-house-info").submit(function (e) {
        e.preventDefault();
        // 房屋表单信息
        var formData = {};
        $(this).serializeArray().map(function (x) { formData[x.name] = x.value });
        // 房屋设施信息
        var facility = [];
        $("input:checkbox:checked[name=facility]").each(function(i, x){ facility[i]=x.value });
        formData.facility = facility;

        $.ajax({
            url: "/house",
            type: "POST",
            data: JSON.stringify(formData),
            contentType:"application/json",
            dataType: "json",
            headers: {
                "X-CSRFToken": getCookie("csrf_token")
            },
            success: function (resp) {
                if ("4101" == resp.errno) {
                    location.href = "/login.html";
                } else if ("0" == resp.errno) {
                    // 后端保存数据成功
                    // 隐藏基本信息的表单
                    $("#form-house-info").hide();
                    // 显示上传图片的表单
                    $("#form-house-image").show();
                    // 设置图片表单对应的房屋编号那个隐藏字段
                    $("#house-id").val(resp.data.house_id);
                } else {
                    alert(resp.errmsg);
                }
            }
        })
    });
    // 处理图片表单的数据
    $("#form-house-image").submit(function (e) {
        e.preventDefault();
        var house_id = $("#house-id").val();
        // 使用jquery.form插件，对表单进行异步提交，通过这样的方式，可以添加自定义的回调函数
        $(this).ajaxSubmit({
            url: "/house/"+house_id+"/images",
            type: "post",
            headers: {
                "X-CSRFToken": getCookie("csrf_token")
            },
            success: function (resp) {
                if ("4101" == resp.errno) {
                    location.href = "/login.html";
                } else if ("0" == resp.errno) {
                    // 在前端中添加一个img标签，展示上传的图片
                    $(".house-image-cons").append('<img src="'+ resp.data.url+'">');
                } else {
                    alert(resp.errmsg);
                }
            }
        })
    })

});