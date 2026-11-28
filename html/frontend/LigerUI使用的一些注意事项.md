---
title: "LigerUI使用的一些注意事项"
date: "2014-09-28 10:02:33"
categories: ["WEB前端"]
tags: ["WebUI框架", "前端", "javascript"]
---

LigerUI使用的一些注意事项:

# 第一点:基本使用注意

      LigerUI中有很多的控件,其中空间有参数/事件/方法 三个属性:

参数:可以理解成为构成这个空间的基础属性,属于前端;

事件:控件渲染过程中自动执行的一些内容;

方法:对控件本身或者对控件的内容(后台交互而来或前台预先准备的)控制;

    所有如果需要对控件加载的内容控制,那么只有通过方法:

例一:

```javascript
<span style="font-size:12px;">var groupTree;
	$(function(){//获取当前项目分类的Tree           
		  groupTree=$("#groupName").ligerComboBox({
	         valueField : 'id',
	         textField: 'text',
	         selectBoxWidth: 178,
	         selectBoxHeight: '50%',
	         treeLeafOnly: false,
	         tree : {
		url: 'pubtempgroup!getLAPPComboxTempGroup.action?'+ $.param( {
					pid : '0'
					}),
		checkbox: true, 
		ajaxType: 'get',
	idFieldName :'id',
				textFieldName:'text',
				parentIDFieldName: 'pid',
			 },
			 onSelected:function (value,text){
	        	 $("#groupIds").val(value);

	         }
	    });
	    initCheckName();
		$.metadata.setType("attr", "validate");
	    ligerForm = $("#setForm").ligerForm();
		deafultValidate($("#setForm"));
	    Validator = $("#setForm").validate();
	    //初始化选中
	    groupTree.selectValue(groupIdsString);
	});
```

```javascript
	$(function(){
		var tmp=groupTree.get("tree");
alert(tmp.checkbox);
		});</span>
```

上面这段代码最终alert出来的结果是true;

实际上,groupTree.get("");这个方法获得的是一个属性;是构成这个LigerComboBox的构成属性;也就是说这里的

     Tree实际上代表的是如下的一个代码片段,而不是Tree得到的后台的实际的内容,所以如果这里alert(tmp.data),将会得到一个null值:

      虽然其确实收到了后台反馈回来的data,但是由于构成的代码片段中没有data,所有null.          

```javascript
{
		url: 'pubtempgroup!getLAPPComboxTempGroup.action?'+ $.param( {
					pid : '0'
					}),
		checkbox: true, 
		ajaxType: 'get',
	idFieldName :'id',
				textFieldName:'text',
				parentIDFieldName: 'pid',
			 }
```

例二:

      如果想要控制控件加载的数据内容,唯一可行的就是通过控件的某些方法:

      如例一中的:

          //初始化选中
    	    groupTree.selectValue(groupIdsString);

       通过方法,可以初始化ligerComboBox中数据的初默认选中:

# 第二点,组合控件:

      就如同LigerComboBox下拉列表数一样,如果一个控件实际上是由其它控件组成的;那么最好通过其本身控件的方法来控制其加载的内容,或者属性参数等等;

      如同例一中,如果将里面的Tree取出来,然后调用Tree空间的方法如何呢? 代码如下:

```javascript
$(function(){
		var tree=groupTree.get("tree");
alert(tree.getData());
		});
```

实际上会报错找不到getData()这个方法,虽然getData()确实是tree空间的一个方法;

猜测原因,tree本身就是LigerComboBox的一个属性,已经不再是原来的Tree空间了;

或者这里的tree是其它组件的一个部分,所以其本身也是受其他空间的方法控制的,自己的方法再次回失效;

    所以如果这里用:

    alert(groupTree.getValue());

就能够看到Tree加载所依赖的主键数据;
