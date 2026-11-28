---
title: "Jquery easyUI treeGride用js初始化后不显示树结构的解决方案"
date: "2015-12-23 09:40:28"
categories: ["WEB前端"]
tags: ["easyui", "treeGride", "不显示", "树"]
---

问题:

      已知treeGride 1.44以及之前的版本中,用js的方式加载json数据来初始化一个treeGride可能会出现没有树结构的情况;

原因以及解决方法:

     js初始化时候,treeField中指定的字段,一定要在columns中出现,如果没有出现,则不会有树形结构;

     如下列子中:treeField:'name'和columns:[[  
{title:'Task Name',field:'name',width:180}中字段name的对应;

      其要求的数据格式如下:

```javascript
[{
"id":1,
"name":"C",
"size":"",
"date":"02/19/2010",
"children":[{
"id":2,
"name":"Program Files",
"size":"120 MB",
"date":"03/20/2010",
"children":[{
"id":22,
"name":"MySQL",
"size":"",
"date":"01/13/2010",
"state":"closed",
"children":[{
"id":221,
"name":"my.ini",
"size":"10 KB",
"date":"02/26/2009"
}]
}]
},{
"id":3,
"name":"eclipse",
"size":"",
"date":"01/20/2010",
"children":[{
"id":31,
"name":"eclipse.exe",
"size":"56 KB",
"date":"05/19/2009"
}]
}]
}]
```

用js方式初始化如下,其中数据data_data代表上面那种树形结构的数据:

```javascript
$('#tt').treegrid({
	data:data_data,
	idField:'id',
	treeField:'name',
	columns:[[
		{title:'Task Name',field:'name',width:180},
		{field:'persons',title:'Persons',width:60,align:'right'},
		{field:'begin',title:'Begin Date',width:80},
		{field:'end',title:'End Date',width:80}
	]]
});
```
