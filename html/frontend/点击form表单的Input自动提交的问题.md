---
title: "点击form表单的Input自动提交的问题"
date: "2014-09-25 11:58:31"
categories: ["WEB前端"]
tags: ["前端", "表单"]
---

```
<form>
	<input id="search_content" type="text" class="search_sr" />
	 <input id="search" type="image" class="search_an" src="/lappstyle/images/search.png" />
</form>
```

需要说明的是,当一个表单中存在如上的格式的时候,表单会自动提交到form所指定的页面,如果没有制定

会提交到当前页面;

解决方法: 去掉form直接使用<input> 或者更改 from表单连接 或者更改

    <input id="search" type="image" 为图片
