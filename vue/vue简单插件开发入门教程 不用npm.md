---
title: "vue简单插件开发入门教程 不用npm"
date: "2018-04-09 13:14:47"
categories: ["WEB前端"]
tags: ["vue", "插件", "不用npm", "分页", "入门教程"]
---

# 简介
我只是想做一个简单的vue插件，和npm没啥关系，怎么办？这里提供一种思路。
因为vue组件的template数据可以是文本数据，所以这里可以利用这种方式。
因为直接写template字符串不好写，所以将template的数据放在一个html文件中，需要的时候加载即可。

# 示例
以常见的一个分页插件为例：
```javascript
var tools = {
	isNull:function(){
		if (typeof content === 'undefined' || null === content) {
            return true;
        }
        if (typeof content == 'String' && $.trim(content) === '') {
            return true;
        }
        if(content === '0' || content === 0){
            return false;
        }
        if (0 != content && !content) {
            return true;
        }
        return false;
	},
	isPositiveInteger:function(){
		return (new RegExp(/^[1-9]\d*$/).test(content));
	},
	isArray:function(){
		if(tools.isNull(o)){
	      return false;
	  }
	  return Object.prototype.toString.call(o) == '[object Array]';
	},
} 
```
tools 是工具类，读者可以自行实现，其依赖于Jquery。

## template文件
主要注意一点：模板文件的内容必须放在一个容器内，示例中使用的是一个div在存放所有展示内容
```html
<div v-show="show" style="margin-top:-25px;text-align: center;" >
    <span class="" style="margin-top:25px;float: left;margin-left: 20px;">共{{my_pageCount}}页，{{my_totalCount}}条记录</span>
    <ul class="pagination pagination-sm pagination-space">
        <li>
            <a class="btn btn-default" href="#" @click="getPager(1)" :disabled="my_currentPageNumber == 1">首页</a>
        </li>
        <li><a class="btn btn-default" href="#" @click="getPager(my_currentPageNumber -1)" :disabled="my_currentPageNumber <= 1 ">&laquo;</a></li>
        <li><a class="btn btn-default" href="#">{{tools.isNull(my_currentPageNumber) ? 1 : my_currentPageNumber}}</a></li>

        <li><a class="btn btn-default" href="#" @click="getPager(my_currentPageNumber + 1)" :disabled="my_currentPageNumber  >= my_pageCount ">&raquo;</a></li>
        <li >
            <a class="btn btn-default" href="#" @click="getPager(my_pageCount)" :disabled="my_currentPageNumber == my_pageCount">尾页</a>
        </li>
        <li>
            <a href="#" style="padding:0px;margin-left: 15px;">
                <input  class="" type="number" v-model="my_goPage" style="border-color: #ccc;font-size: 12px;font-weight: 400;text-align: center;line-height: 1.5;border: 1px solid transparent;border-radius: 2px;padding: 4px;width: 30px;background: #FEFEFE;color: #000;    padding-left: 1px;padding-right: 1px;" />
            </a>
        </li>
        <li>
            <span  @click="goToCustomPage" style="">
                <i class="fa fa-forward">
                </i>
            </span>
        </li>
        <li>
            <span>
                <i class="fa fa-refresh" @click="refresh++">
                </i>
            </span>
        </li>
    </ul>
    <p  style="float: right;margin-right: 20px;margin-top:25px;">
        <span>每页</span>
        <select style=" width: 45px;"  v-model="my_pageSize" @change="doGetPager">
            <option v-for="item in rowList" :value="item">{{item}}</option>
        </select>
        <span>条</span>
    </p>
</div>
``` 

# js注册文件
在需要使用的页面开头引入vue的js文件之后，即可引此js文件。
``` javascript
new function(){
    var self = this;
    self.getVueComponent = function (url,name,initFunc){
             $.ajax({
                  type : "get",
                  url : url,
                  async : false,
                  dataType:'text',
                  success : function(data){
                      initFunc(name,data);
                  }
             });
    };
    self.initMyPager = function (name,data){
	var props = {
		 'pageSize': {
	              type: Number,
		      default: null
		  },
		  'startPage':{
	              type: Number,
		      default: 1
		  },
		  'rowList':{
		      type: Array,
		      default:  [10,20,30,50]
		  },
		  'show': {
	              type: Boolean,
    		      default: true
		  },
		 //初始化完成后是否调用一次change事件，只有当show的值是true的时候才会调用一次change;
	          'initCall': {
	              type: Boolean,
    		      default: true
		  },
		  //只要当refresh的值发生变化，则刷新当前页面数据
		  'refresh':{
	              type: Number,
		      default: 1
		  },
		  'initData':{
	              type: Number,
		      default: 1
		  },
	};

        Vue.component(name,{
            // 可以请求一个html文件，既然存放模板还是html文件存放比较好
            props: props,
            template: data,
            data: function () {
           	 return {
           	    my_pageSize: 10,
           	    my_currentPageNumber:1,
           	    my_pageCount:1,
           	    my_totalCount:1,
           	    my_goPage:1,
           	    my_init_data:this.initData,
           	    my_refresh:this.refresh,
           	  };
            },
            methods: {
                    doGetPager:function(){
                	var self = this;
        		var callBack = function(pager){
        		    self.my_pageCount = pager.pageCount;
        		    self.my_totalCount = pager.totalCount;
        		    self.my_currentPageNumber = pager.currentPageNumber;
        		}
        		this.$emit('change',this.my_currentPageNumber,this.my_pageSize,callBack);
                    },
        	    getPager: function (pageNumber) {
        		if(pageNumber > this.my_pageCount || pageNumber < 1 || pageNumber == this.my_currentPageNumber){
            			return;
            	    	}
        		this.my_currentPageNumber = pageNumber;
        		this.doGetPager();
        	    },
        	    goToCustomPage:function(){
        		if(this.my_goPage > this.my_pageCount || this.my_goPage < 1){
        		    this.my_goPage = this.my_currentPageNumber;
            			return;
            	    	}
        		this.getPager(this.my_goPage);
        	    },
        	    getPageSize:function(){
                    var ps = 10;
                    if(!tools.isNull(this.pageSize) && tools.isPositiveInteger(this.pageSize)){
                        ps = props.pageSize;
                    }else if(tools.isArray(this.rowList) && this.rowList.length > 0 ){
                        ps = this.rowList[0];
                    }else if(!tools.isNull(this.rowList['default'])){
                        ps = this.rowList['default'][0];
                    }
                    return ps;
        	   },
        	   initPageInfo:function(){
        	       this.my_pageSize = this.getPageSize();	
        	       this.my_currentPageNumber = 1;
        	   },  
    	    },
	        created: function () {
		        this.initPageInfo();
		        if(this.initData == 1 && this.initCall){
	      	    this.doGetPager();
	      	    }
    	    },
    	    mounted:function () {
      	    },
            watch:{
                'refresh':function(currentValue,oldValue){
                    	this.doGetPager();
                },
                'initData':function(currentValue,oldValue){
            	    this.initPageInfo();
            	    if(!tools.isNull(this.initCall) && this.initCall == true){
            		this.doGetPager();
       	    	    };
                }
            }
        });

    };
    //需要注意的是，这里的url就是你项目运行后，获取模板文件的url
    self.getVueComponent(baseUrl + "/plugins/components/pager/pager.html",'my-pager',self.initMyPager);
}();
``` 

# 使用
``` html

``` 

# 说明文档
## 简介
my-pager插件是一个独立的分页插件，但是依赖于common.js文件
使用时先导入Vue的js文件，然后导入common.js(即tools工具类)和pager.js文件

## 属性
- init-data
Number类型，每当其值变化时，将会对my-pager进行初始化，设置初始的页数和每页记录数量。默认值1，组件加载时表示会自动初一次始化数据
- row-list
Array类型，分页的每页记录数量的选择，默认[10,20,30,50]
- page-size
Int类型，初始化时指定的每页记录数量，默认从row-list中取第一个
- refresh
Int类型，每当其值改变时，就重新请求数据，默认1
- init-call
Boolean类型，每当触发init的事件后，是否重新请求数据，默认true

## 事件
- change(pageNumber,pageSize,callBack)
change事件在分页的每页记录数或者当前页数发生变化时，由子组件自动回调
 - pageNumber 当前页数
 - pageSize 每页记录数量
 - callBack(pager)
是一个function,用于change函数被调用后,开发者处理完数据逻辑后,返回相关信息给pager,其参数pager中属性：pageCount,totalCount,currentPageNumber三个属性
这三个属性将会显示到分页插件中。

# 示例
注意：在模板js中写的驼峰格式的属性，在html中调用的时候，必须使用中缀符号-连接的格式调用属性。
row-list    ->    rowList
```html
<script src="jquery.min.js"></script>
<script src="vue.min.js"></script>
<script src="/components/pager/pager.js"></script>
<script src="/common.js"></script>

<my-pager @change="queryMerchantParent" :init="initParentPager" :row-list="[10,20,30]" :init-call="true">
</my-pager>
```
这里示例中的initParentPager的初始值是0不会自动初始化，是1的时候会自动初始化。推荐1。

# 效果
![分页效果](assets/79865034_01.jpeg)
