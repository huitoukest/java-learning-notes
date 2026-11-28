---
title: "使用JS实现HTML限定图像最大尺寸并等比例显示"
date: "2016-04-16 17:23:15"
categories: ["WEB前端"]
tags: ["html", "jquery", "图片"]
---

调用js函数，传入Jquery对象即可：

```javascript
function setImgAdaptContainer(imgSelector,containerSelector){
						var _img=$(imgSelector);
						var container=$(containerSelector);
						setImgAdaptContainerByObj(_img,container);
					}
					function setImgAdaptContainerByObj(imgObj,containerObj){
						var _img=imgObj;
						var container=containerObj;
						var containerHeight=container.height()*0.99;
						var containerWidth=container.width()*0.99;
						var imgHeight=0;
						var imgWidth=0;
							_img.removeAttr('height'); _img.removeAttr('width');
							imgHeight=_img.height();
							imgWidth=_img.width();

						if(imgHeight/imgWidth<containerHeight/containerWidth)
						{
						_img.css('height','auto');
						_img.css('width','99%');
						}else{
							_img.css('height','99%');
							_img.css('width','auto');
						}						
					}
```
