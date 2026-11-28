---
title: "html2canvas网页截图"
date: "2014-09-19 18:05:52"
categories: ["WEB前端"]
tags: ["web", "前端", "javascript", "截图"]
---

html2canvas工具请自行搜索:

将相应的引入的js库的路径改变后存到本地即可使用:

HTML页面一:

```html
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
<html>
<!--此网页演示了html2canvas截图后将截图后的网页追加到了原网页之上 -->
	<head>
	    <!-- base.js实际上是jquery库,html2canvas.js是html2canvas自带的js库 -->
		<script type="text/javascript" src="./WEB-INF/JS/html2canvas.js"></script>
		<script type="text/javascript" src="./WEB-INF/JS/base.js"></script>
		<title>MyHtml.html</title>

		<meta http-equiv="keywords" content="keyword1,keyword2,keyword3">
		<meta http-equiv="description" content="this is my page">
		<meta http-equiv="content-type" content="text/html; charset=UTF-8">

		<!--<link rel="stylesheet" type="text/css" href="./styles.css">-->
<!--需要注意的是,这里一定要等待js库和网页加载完毕后再执行函数  -->
		<script type="text/javascript">
$(function(){
alert("函数调用成功");
	html2canvas(document.body, {
		onrendered : function(canvas) {
			document.body.appendChild(canvas);
		}
	});
});
</script>
		<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
		<style>
.feedback-overlay-black {
	background-color: #000;
	opacity: 0.5;
	position: absolute;
	top: 0;
	left: 0;
	width: 100%;
	height: 100%;
	margin: 0;
}
</style>

		<style>
div {
	padding: 20px;
	margin: 0 auto;
	border: 5px solid black;
}

h1 {
	border-bottom: 2px solid white;
}

h2 {
	background: #efefef;
	padding: 10px;
}
</style>
	</head>
	<body>
		<div style="background: red;">
			<div style="background: green;">
				<div style="background: blue; border-color: white;">
					<div style="background: yellow;">
						<div style="background: orange;">
							<h1>
								Heading
							</h1>
							Text that isn't wrapped in anything.
							<p>
								Followed by some text wrapped in a
								<b><p> paragraph.</b>
							</p>
							Maybe add a
							<a href="#">link</a> or a different style of
							<a href="#" style="background: white;" id="highlight">link
								with a highlight</a>.
							<hr />
							<h2>
								More content
							</h2>
							<div
								style="width: 10px; height: 10px; border-width: 10px; padding: 0;">
								a
							</div>
						</div>
					</div>

				</div>

			</div>
		</div>
		此网页演示了html2canvas截图后将截图后的网页追加到了原网页之上
		<br>
		<br>
		这里可以看作是边界线
		<hr/>
	</body>
</html>
```

第二个示例:

将网页截图下载:

```html
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
<html>
<!--此网页演示了html2canvas网页截图下载 -->
	<head>
	    <!-- base.js实际上是jquery库,html2canvas.js是html2canvas自带的js库 -->
		<script type="text/javascript" src="./WEB-INF/JS/html2canvas.js"></script>
		<script type="text/javascript" src="./WEB-INF/JS/jquery-1.6.2.js"></script>
		<title>MyHtml.html</title>

		<meta http-equiv="keywords" content="keyword1,keyword2,keyword3">
		<meta http-equiv="description" content="this is my page">
		<meta http-equiv="content-type" content="text/html; charset=UTF-8">

		<!--<link rel="stylesheet" type="text/css" href="./styles.css">-->
<!--需要注意的是,这里一定要等待js库和网页加载完毕后再执行函数  -->
<!-- html2canvas()中,第一个参数是要截图的Dom对象，第二个参数时渲染完成后回调的canvas对象。  -->
		<script type="text/javascript">
$(function(){
	print();
});

function print()
{
	html2canvas( $("body") , 
	{
		onrendered: function(canvas) 
		{   
		$('#down_button').attr( 'href' , canvas.toDataURL() ) ;
		$('#down_button').attr( 'download' , 'myjobdeer.png' ) ;
		//$('#down_button').css('display','inline-block');
		}
	});
}

</script>
		<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
	</head>
	<body>
		此网页演示了html2canvas截图后将截图后的网页追加到了原网页之上
		<br>
		<br>
		这里可以看作是边界线
		<hr/>
<a type="button" id="down_button">下载</a>
	</body>
</html>
```
