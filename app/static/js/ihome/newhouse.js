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
    // TODO: 处理房屋基本信息提交的表单数据

    // TODO: 处理图片表单的数据

})