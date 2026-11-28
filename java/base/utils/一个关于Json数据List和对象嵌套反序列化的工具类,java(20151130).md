---
title: "一个关于Json数据List和对象嵌套反序列化的工具类,java(20151130)"
date: "2015-11-27 17:16:46"
categories: ["j2se"]
tags: ["json", "java"]
---

背景说明: 本示例中用的是fastJson来解析具体的事务;

简介:

1. 目前支持一个json普通对象字符串反序列化,数组对象反序列化,普通对象中含有其他对象或者数组对象的反序列化;

           2.支持对List嵌套的反序列化,比如将[ [XXXX],[XXXX]  ] 反序列化成为 List<List<?>>;

问题:

        当json数据遇到嵌套,我找了一段时间都没有找到很好的解决办法,所以自己写了这个工具来解析相关json字符串,并使之还原为一个对象;

        这时候如果直接反序列化可能报错:not close json text, token : ,

        比如遇到如下json数据:

```java
[
{
"id": 123, 
"name": 1111, 
"point": [
{
"x": 1, 
"y": 1
}, 
{
"x": 2, 
"y": 2
}
]
}, 
{
"id": 123, 
"name": 1111, 
"points": [
{
"x": 5, 
"y": 1
}, 
{
"x": 562, 
"y": 2
}, 
{
"x": 20, 
"y": 26
}
]
}, 
{
"id": 123, 
"name": 1111, 
"points": [
{
"x": 9, 
"y": 132
}, 
{
"x": 2, 
"y": 2
}
]
}
]
```

                       对应的类如下:

```java
public class A {
    public String id;
    public String name;
    List<Point> points;
}
```

```java
public class Point {
public Double x;
public Double y;
}
```

由上面的json数据,可以看到:

               整个json数据实际上是一个类A的数组;数组A的属性points实际上是一个类Point的数组;在这样的情况下,很多json工具并不能够直接进行反序列化;

如此,huitoukest编写了工具来解决这类问题,工具如下:

         编写一个支持类Annotation:

    import java.lang.annotation.ElementType;
    import java.lang.annotation.Retention;
    import java.lang.annotation.RetentionPolicy;
    import java.lang.annotation.Target;

    /**
     * 指定当前json字符串对应反序列化的方式JsonPropertyType
     * JsonList,JsonObject,Base,Transient
     * 当JsonPropertyType.Base的时候,将会按照默认识别的类型使用,即此时的cls属性不会生效
     * JsonList,JsonObject表示此对象是一个json对象数组或者对象;
     * 选择Transient的时候,cls属性不会生效,此属性不进行反序列化操作
     */
    @Target(ElementType.FIELD)
    @Retention(RetentionPolicy.RUNTIME)
    public @interface JsonFieldProperty{

    	/**
    	 * 指定一个类型是JsonPropertyType的,表现为JsonPropertyType=默认为JsonPropertyType.Base的Annotation
    	 * @return
    	 */
    	JsonPropertyType JsonPropertyType() default JsonPropertyType.Base;
    	/**
    	 * 指定一个类型是Class的,表现为cls=默认为String.class的Annotation
    	 * @return
    	 */
    	Class cls() default String.class;
    	/**
         * 指定当前属性的类型
         *

```java
*/
public enum JsonPropertyType{   	  
	JsonList,JsonObject,Base,Transient;
	};
```

    }

编写一个工具类:

```java
import java.lang.annotation.Annotation;
import java.lang.reflect.Field;
import java.util.ArrayList;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import com.alibaba.fastjson.JSON;
import com.alibaba.fastjson.JSONArray;
import com.alibaba.fastjson.JSONException;
import com.alibaba.fastjson.JSONObject;
```

    public class JsonUtils_wg {
    	/**
    	 * bean中的属性只能够是如下几种包装类型;
    	 * 已经用Annotation注释的list和object;
    	 */
    	private static final String type_boolean="class java.lang.Boolean",
    			   type_date="class java.util.Date",
    			   type_float="class java.lang.Float",
    			   type_double="class java.lang.Double",
    			   type_long="class java.lang.Long",
    			   type_integer="class java.lang.Integer",
    			   type_string="class java.lang.String";
    	/**
    	 * 查看一个字符串是否是一[开头,即是否有可能是数组;
    	 */
    	private static final Pattern pattern = Pattern.compile("^([\\s]{0,}\\[).*");

    	/**
    	 *
    	 * @param jsonString json字符串
    	 * @param cls 需要转换的class类
    	 * @return
    	 * @throws IllegalArgumentException
    	 * @throws IllegalAccessException
    	 * @throws InstantiationException
    	 */

```java
	public static List<? extends Object> parseToArray(String jsonString,Class cls) throws IllegalAccessException, IllegalArgumentException, InstantiationException{
		 JSONArray jsonArr = JSON.parseArray(jsonString);
		 List<Object> list=new ArrayList<Object>();
		 Object o;
		 for(int i=0;i<jsonArr.size();i++){
			 String jarString=jsonArr.getString(i);
			 Matcher matcher = pattern.matcher(jarString);
			 if(matcher.find()){//如果数组中包含的仍然是一个数组
				 try{
				 List<?> tmp=parseToArray(jarString, cls);
				 list.add(tmp);
				 }catch(JSONException e){
					 o=parseToObject(jarString, cls);				 
					 list.add(o);
				 }
			 }else{
				 o=parseToObject(jarString, cls);				 
				  list.add(o);
			 }		   			 		 
		 }
		 return list;
}

	public static Object parseToObject(String string,Class cls) throws InstantiationException, IllegalAccessException{
		Object o=cls.newInstance();
		 JSONObject jsonObj=(JSONObject) JSONObject.parse(string);
			 Field[] fields=cls.getFields();
			 for(int j=0;j<fields.length;j++){
				 Field field=fields[j];
				 field.setAccessible(true);
				 Annotation[] annotations=field.getAnnotations();
				 //为自定义的Annotation赋值
				 JsonFieldProperty jsonFieldProperty=null;
				 for(int a=0;a<annotations.length;a++){
					 if(annotations[a] instanceof JsonFieldProperty){
						 jsonFieldProperty=(JsonFieldProperty)annotations[a];
						 break;
					 }
				 }
				 Object tmp=null;
				 if(jsonFieldProperty==null||jsonFieldProperty.JsonPropertyType()==null||jsonFieldProperty.JsonPropertyType()==JsonPropertyType.Base){
					 tmp=jsonObj.get(field.getName());
					 String typeString=field.getGenericType().toString();
					 if(tmp!=null)
					 {
					   		if(typeString.equals(type_boolean)){
					   			field.set(o, jsonObj.getBoolean(field.getName()));
					   		}else if(typeString.equals(type_date)){
					   			field.set(o, jsonObj.getDate(field.getName()));						  
							}else if(typeString.equals(type_integer)){
								field.set(o, jsonObj.getInteger(field.getName()));
							}else if(type_long.equals(typeString)){
								field.set(o, jsonObj.getLong(field.getName()));
							}else if(typeString.equals(type_float)){
								field.set(o, jsonObj.getFloat(field.getName()));
							}else if(typeString.equals(type_double)){
								field.set(o, jsonObj.getDouble(field.getName()));
							}else if(typeString.equals(type_string)){
								field.set(o, jsonObj.getString(field.getName()));
							}else{
								field.set(o, tmp);
								}
					}
				 }else if(jsonFieldProperty.JsonPropertyType()==JsonPropertyType.JsonObject){
					 tmp=jsonObj.getString(field.getName());
					 if(tmp!=null)
					 field.set(o,parseToObject(tmp.toString(), jsonFieldProperty.cls()));
				 }else if(jsonFieldProperty.JsonPropertyType()==JsonPropertyType.JsonList){
					 tmp=jsonObj.getString(field.getName());
					 if(tmp!=null)
					 field.set(o,parseToArray(tmp.toString(), jsonFieldProperty.cls()));
				 }					 				 
			 }
		 return o;
	}
}
```

使用方法,在需要将一个json字符串转换为List或者普通对象的时候,

1.加上JsonFieldProperty注解,

2.之后使用JsonUtils_wg工具来进行相应的转换即可:

    @JsonFieldProperty(JsonPropertyType=JsonPropertyType.JsonList,cls=Point.class)
        public List<Point> points;

注意:

         1.本例中使用的fasjson作为解析类,需要的童鞋可以自己改为相应的类;

         2.此序列化是通过属性的名称和注解来完成了,所以属性最好设置为public,可以不要getter和setter方法,如果setter和getter方法中名字和属性不对应的需要注意可能的错误;

         3\. 此工具只支持包装类和普通对象以及对象数组,不支持基础数据类型,并且限定包装类为Date,String,Long,Integer,Double,Float,Boolean这几种,不然可能会出现问题

    4.如果那个大神有空将通过方法来完成反序列化的功能实现,然后留言给我一个连接那就更好了...              
