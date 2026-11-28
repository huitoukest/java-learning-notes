---
title: "网页大文本文件的在线加载预览，txt，xml，html等纯文本格式"
date: "2016-05-11 15:37:41"
categories: ["WEB前端"]
tags: ["html", "xml", "文本", "在线预览"]
---

1.如果文本不大，可以通过设置Iframe的src的方式来让浏览器自动获取内容并且排版

但是Iframe的方式并不能够显示xml等包含< > " 等符号；因为其会将之当成html标签；

如果要直接显示包含html标签的文本，那么有两种方式；

一种：使用[<xmp>](http://www.baidu.com/link?url=hotjQGLvQ_PxMdahe4EnIcoxIXumYt5ZE5TyiK0oPx9Z6kZwiK0zFzeXlF2zq6_hMLYz8wQEhWqGcY01SURipa)或者[<textarea>](http://www.baidu.com/link?url=2IqB0TgJkAqtpudEsIe3kfMAno8ODNznCbtp-FY7LCCrPRtepRRxFQ6ixpZHVALhMQGytDMIDeFSiQiuZZl7xK)等类似的标签，将内容放在标签内，这样就能够原样显示；

第二种：自己将内容转义，然后将转义后的内容来显示；

2.如果文本比较大，一次加载完毕那么浏览器可能会比较卡，甚至在某一段时间内会直接卡死

笔者测试：chrome浏览器加载1MB的文本文件的时候卡顿明显，IE和遨游等加载速度快很多；

解决方法：分批转义，分批加载

3.转义后，分批加载核心代码如下

第一步：采用ajax方式将大文本下载到本地

```javascript
$.ajax({
		type: "get",
		url: url,
		data: {},
		dataType: "text",
		timeout: 100000, //超时时间：100秒
		success: function(data){//1m的文本                 
					if(data.length>1024000)
						{
							var originLength=data.length;
							data=data.substring(0,1024000);	        					
							replaceAndAppendData(data,$("#textareaShowTextOfProduct"),10240,function(){
								$("#textareaShowTextOfProduct").append("<br/>...............省略"+(originLength-data.length)+"个长度的内容<br/>");
							});

						}else{
							replaceAndAppendData(data,$("#textareaShowTextOfProduct"),10240);
						}
				 },
		error:function(XMLHttpRequest, textStatus, errorThrown){
		 }
	});
```

第二步，分批次加载，并追加内容到一个DOM容器内

这里转义的符号有大于，小于，换行，双引号，空格；  

```javascript
<span style="white-space:pre">	</span>//循环函数
	var replaceAndAppendDataRe;
	/**
	*替换相关符号，并将之追加在dom节点上
	*count表示将数据分为多少份
	*countLength,每一次处理的数据量
	*callBack执行完毕之后的回调函数
	**/
	function replaceAndAppendData(data,obj,countLength,callBack){
		if(countLength<0) countLength=10240;
		if(countLength>51200) countLength=51200;
		//var countLength=data.length/count;//每一份的长度
		var startStr=0;//当前开始的字符串
		replaceAndAppendDataRe=function(){
				if(startStr<data.length){
					var tmpData=data.substring(startStr,startStr+countLength);
					var startT=new Date().getTime();
					tmpData=tmpData.replace(/</g,"<");
					tmpData=tmpData.replace(/>/g,">");
					tmpData=tmpData.replace(/\"/g,""");
					tmpData=tmpData.replace(/\n/g,"<br/>");
					tmpData=tmpData.replace(/[ ]/g," ");
					var endT=new Date().getTime();
					var spaceT=endT-startT;
					if(spaceT<15) spaceT=15;
					if(spaceT>250){
						countLength=String.parseInt(countLength*0.75+"");
					}
					$(obj).append(tmpData);				
					setTimeout("replaceAndAppendDataRe()",spaceT);
			}else{
				if(typeof callBack!='undefined'&&callBack!=null){
					callBack();
				}
			}	
				startStr=startStr+countLength;
		};
		replaceAndAppendDataRe();
	}
```
