---
title: "让高度百分比，height:100% 生效的3种方法"
date: "2016-05-12 09:04:14"
categories: ["WEB前端"]
tags: ["html"]
---

# 核心原理；

height:100%这个概念是子节点相对于父容器而言；所以要让此属性生效，必要的一点就是：父容器必须具有具体的高度信息；

直接在<body>的子节点（如div中）写height:100%是不会生效的，因为此时<body>的高度是不确定的，默认是auto；

# 方法一

给从根的父容器到子容器的所有容器都设置好百分比高度信息

比如：

```html
<!DOCTYPE html>
<html lang="zh-cn" style="height:100%;width:100%;overflow:hidden;">
	<head>
		<meta charset="utf-8" />
		<meta http-equiv="X-UA-Compatible" content="IE=9;IE=8;chrome=1" />
		<title>132</title>		
	</head>
	<body style="height:100%;width:100%;padding:0;margin: 0;">

<div style="height:100%;width:100%;background-color:#787878" >

</div>
	</body>
</html>
```

这样从根的Html开始，到字的div结束，全部都具有百分比高度，这样，就都能够获取到高度信息；

# 方法二

给父容器设置具体的高度信息；

比如直接写死在样式中，或者用javascript来设置；

示例，用js使<body>得到高度，从而使其中的div全屏：

```html
<!DOCTYPE html>
<html lang="zh-cn">
	<head>
		<meta charset="utf-8" />
		<meta http-equiv="X-UA-Compatible" content="IE=9;IE=8;chrome=1" />
		<title>132</title>		
	</head>
	<body id="body" style="padding:0;margin: 0;">
<div style="height:100%;width:100%;background-color:#787878" >

</div>
	</body>
	<script type="text/javascript">
		var screenHeight=document.documentElement.clientHeight;
		var screenWidth=document.documentElement.clientWidth;
		var body=document.getElementById('body');
		body.style.width=screenWidth+"px";
		body.style.height=screenHeight+"px";
	</script>
</html>
```

# 方法三

给父容器设置位置信息，让其得到高度信息；

示例，用css使body得到高度，从而使其中的div全屏：

```html
<!DOCTYPE html>
<html lang="zh-cn">
	<head>
		<meta charset="utf-8" />
		<meta http-equiv="X-UA-Compatible" content="IE=9;IE=8;chrome=1" />
		<title>132</title>		
	</head>
	<body style="position:absolute;top:0px;left:0px;right:0px;bottom:0px;padding:0;margin: 0;">
<div style="height:100%;width:100%;background-color:#787878" >

</div>
	</body>
</html>
```
