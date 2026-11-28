---
title: "checkbox选中的问题"
date: "2014-09-26 15:14:43"
categories: ["WEB前端"]
tags: ["前端", "checkbox"]
---

一:原生方法

```javascript
<span style="font-size:14px;">  if (document.getElementById("CheckAll").checked === false)
{
var array = document.getElementsByName("checkBoxGroup");                   
for (var i = 0; i < array.length; i++) {
array[i].checked = false;
}
}</span>
```

二:Jquery方法

http://www.cnblogs.com/libingql/archive/2011/11/07/2238663.html

<a href="javascript:;" id="all">全部选择</a>  
<a href="javascript:;" id="delAll">取消选择</a>  
<a href="javascript:;" id="antiAll">反向选择</a>        
<input type="checkbox" name="checkbox1">A  
<input type="checkbox" name="checkbox1"> B  <input type="checkbox" name="checkbox1">C  
<input type="checkbox" name="checkbox1">D  
<input type="checkbox" name="checkbox1">E  
<input type="checkbox" name="checkbox1">F  
---  
**Jquery部分**   //全部选择  
$("#all").click(function(){    
$("input[name='checkbox1']").each(function(){  
$(this).attr("checked",true);  
});    
});  
---  
**Jquery部分：** //取消选择  
$("#delAll").click(function(){    
$("input[name='checkbox1']").each(function(){  
$(this).attr("checked",false);  
});    
});  
---  

**Jquery部分：**   //反向选择  
$("#antiAll").click(function(){  
$("input[name='checkbox1']").each(function(){  
$(this).attr("checked",!this.checked);                
     });  
---  

三:JSP方法

不排除有些时候javascript不好用,或者有些莫名其妙的问题,这个时候用jsp方法最保险

    <input class="none" type="checkbox" name="isShare" id="isShare" value="true" <%=((Integer)request.getAttribute("isShare")==1?"checked='checked'":"")%>></input>

:
