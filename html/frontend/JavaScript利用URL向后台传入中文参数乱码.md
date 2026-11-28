---
title: "JavaScript利用URL向后台传入中文参数乱码"
date: "2014-09-22 10:59:05"
categories: ["WEB前端"]
tags: ["javascript", "编码"]
---

前台的javascript代码,假设这里前台的编码是UTF-8的格式:

其中shuju_url="pub!list.action?content="+"我是传递的参数";

    //shuju_url是包含中文参数的一个URL;

    shuju_url=encodeURI(encodeURI(shuju_url));

后台java代码:

content就是向后台传递的那个参数;

    content=URLDecoder.decode(content,"UTF-8");
