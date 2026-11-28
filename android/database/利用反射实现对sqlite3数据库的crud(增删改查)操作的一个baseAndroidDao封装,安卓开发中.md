---
title: "利用反射实现对sqlite3数据库的crud(增删改查)操作的一个baseAndroidDao封装,安卓开发中"
date: "2016-01-06 16:30:10"
categories: ["android操作"]
tags: ["android", "baseDao", "sqlite3"]
---

# 1.说明

博主主要是做java web后台这一块,但是偶尔做点安卓,发现安卓上没有像Hibernate这种orm框架(....其实也没有去找),

又觉得每次增删改查都自己写代码的话肯定是非常麻烦的,所以就写了一个简单的baseAndroidDao来封装一些简单的增删改查操作;

需要注意的是,此框架并非一个健全的orm框架,功能简单,而且这些功能必须采用博主约定的方式才能正确运行;

# 2.具体实现

例举现在有一个javaBean如下,其如同Hibernate中的实体,但是却只是通过属性来存取值(博主嫌麻烦....没有用getter和setter那种标准方式,而且基本够用...)

```java
public class User extends BaseEntity {

public Long Id;	
public String Login_Name;
public String Password;
public String Real_Name;
public Long State;
public String Uid;
@Entity_FieldProperty(FieldType=FieldType.JsonObject,cls=Sys_User_Info.class)
public Sys_User_Info UserInfo;
	@Override
	public Long getId() {
		return Id;
	}
}
```

约定一:所有实体(用来存储和数据库表数据相对应的bean)必须继承BaseEntity类,

约定二:同时属性的名称必须和数据库中的字段相一致;不过,主键必须是Long Id(不区分大小写),数据库中将会以_id字段存储;

约定三:只支持Boolean,Date,Long,String,Integer,List,Objec,Float,Double这几个包装类的属性,不支持数组类型;

约定四.通过Entity_FieldProperty注解来实现对List,bean对象,静态对象的控制;

说明:这些约定都是很好改的.....如有需要可以下载之后自己该,最好是改成类似Hibernate那种注解识别id的方式,然后给博主发一份过来嘿嘿;

其中BaseEntity主要是封装一些对Entity的操作....具体代码如下(其实这些东东封装到Dao中,然后用Dao对Entity操作时最好的,这样Entity也不用继承BaseEntity)

以后有时间博主会重写结构然后更新(现在结构很垃圾..耦合重...),但是利用反射的核心代码不会这么变,所以大家可以看看:

    /**
     * Entity约定:
     * 0.主键的名称必须是id,不分大小写,数据库中以_id存储
     * 1.只支持Boolean,Date,Long,String,Integer,List,Objec,Float,Double这几个包装类的属性,不支持数组类型
     * 2.其它属性的值,不支持自动赋值与使用
     * 3.通过Entity_FieldProperty注解来实现对List,bean对象,静态对象的控制;
     * @author dview
     *
     */
    public abstract class BaseEntity {
    	/**
    	 * 下面规定允许的数据类型
    	 */		
    	@JSONField(serialize=false)
    	private final String type_boolean="class java.lang.Boolean",
    		   type_date="class java.util.Date",
    		   type_float="class java.lang.Float",
    		   type_double="class java.lang.Double",
    		   type_long="class java.lang.Long",
    		   type_integer="class java.lang.Integer",
    		   type_string="class java.lang.String";
    	@JSONField(serialize=false)
    	public final static String primaryKeyName="_id";

    	/**
    	 * 判断一个属性是否是静态变量,此类暂时不用
    	 * @param field
    	 */
    	@JSONField(serialize=false)
    	public boolean isStaticField(Field field){
    		  boolean isStatic = Modifier.isStatic(field.getModifiers());
    		  return isStatic;
    	}
    	/**
    	 * 为本实体类赋值
    	 * @throws IllegalArgumentException
    	 * @throws IllegalAccessException
    	 */
    	@JSONField(serialize=false)
    	private void setFieldValue(Cursor c) throws IllegalAccessException, IllegalArgumentException{
    		 if(c==null) return;
    			Class<?> clazz=this.getClass();
    			Field[] fs=clazz.getDeclaredFields();		
    			for(Field f:fs){
    				int index=0;//cursor游标中的索引,某个字段
    				try{
    				f.setAccessible(true);//强制获取,设置值
    				Annotation[] as=f.getAnnotations();
    				Class<?> fclass=null;
    				FieldType fType=null;
    				   for(int i=0;i<as.length;i++){
    					   Annotation a=as[i];
    					   if(a instanceof Entity_FieldProperty){
    						   Entity_FieldProperty ef=(Entity_FieldProperty)a;
    						   if(ef!=null){
    						   fclass=ef.cls();
    						   fType=ef.FieldType();
    						   }
    						   break;
    					   }
    				   }
    				 String typeString=f.getGenericType().toString();
    				 String name=f.getName();
    				 if(name.toLowerCase(Locale.ENGLISH).equals("id"))
    				 {
    					 name=primaryKeyName;
    				 }
    				  index=c.getColumnIndex(name);
    				  if(index==-1)
    					  continue;
    				   //按照基础六类属性来处理
    				   if(fType==null||fType==FieldType.Base){
    					   		if(typeString.equals(type_boolean)){
    					   			int result=c.getInt(index);
    					   			f.set(this, (Boolean)(result==1));
    					   		}else if(typeString.equals(type_date)){
    							  Long m=c.getLong(index);
    							  if(m!=null)
    							   {
    								  f.set(this, new Date(m));
    							   }else{
    								   f.set(this,null);
    							   }							  
    							}else if(typeString.equals(type_integer)){
    								 f.set(this,c.getInt(index));
    							}else if(type_long.equals(typeString)){
    								f.set(this,c.getLong(index));
    							}else if(typeString.equals(type_float)){
    								f.set(this,c.getFloat(index));
    							}else if(typeString.equals(type_double)){
    								f.set(this,c.getDouble(index));
    							}else{
    								 f.set(this,c.getString(index));
    							}
    				   }else if(fType==FieldType.Transient){
    				       continue;
    				   }else if(fType==FieldType.JsonObject){
    					   Object jobj=null;
    					   if(c.getString(index)!=null)
    					   JsonUtils_wg.parseToObject(c.getString(index), fclass);
    					   f.set(this,jobj);
    				   }else if(fType==FieldType.JsonList){
    					   List<?> objs = null;
    					   if(c.getString(index)!=null)
    					   objs=JsonUtils_wg.parseToArray(c.getString(index), fclass);
    					   f.set(this,objs);
    				   }
    				} catch (Exception e) {
    					Log.e(this.getClass().getName(), e.toString());
    					e.printStackTrace();
    				    continue;
    				}//end try
    			}//end for
    	}
       /**
        * 以键值对的方式,返回单签类的,属性的名称和之所对应的值
        * @return
        * @param isChangeIdString 是否改变属性名称为id的键为BaseEntity.primaryKeyName所代表的属性值
        * @throws IllegalArgumentException
        * @throws IllegalAccessException
        */

```java
@JSONField(serialize=false)
private Map<String,Object> getFieldValue(boolean isChangeIdString) throws IllegalAccessException, IllegalArgumentException{
	   Map<String,Object> maps=new HashMap<String,Object>();
	   Class<?> clazz=this.getClass();
	   Field[] fs=clazz.getDeclaredFields();		
	   for(Field field:fs){
		   field.setAccessible(true);
		   Annotation[] as=field.getAnnotations();
		   Class<?> fclass=null;
		   FieldType fType=null;
		   for(int i=0;i<as.length;i++){
			   Annotation a=as[i];
			   if(a instanceof Entity_FieldProperty){
				   Entity_FieldProperty ef=(Entity_FieldProperty)a;
				   if(ef!=null){
					   fclass=ef.cls();
					   fType=ef.FieldType();
				   }
				   break;
			   }
		   }
		   String typeString=field.getGenericType().toString();
		   String name=field.getName();
		   if(name.toLowerCase(Locale.ENGLISH).equals("id")&&isChangeIdString)
			 {
				 name=primaryKeyName;
			 }
		   //按照基础六类属性来处理
		   if(fType==null||fType==FieldType.Base){		  
			   if(field.get(this)==null){
					  maps.put(name, null);
				  }else if(typeString.equals(type_boolean)){
					  if((Boolean)field.get(this))
				       {
						  maps.put(name,1);
				       }
				        else{
				        	maps.put(name,0);
					  }
				  }else if(typeString.equals(type_date)){
					  Date d=(Date) field.get(this);
					  maps.put(name, d.getTime());
				  }else {
					  maps.put(name,field.get(this));  
				  }		   
		   }else if(fType==FieldType.Transient){
		       continue; 
		   }else if(fType==FieldType.JsonObject){
			   if(field.get(this)==null)
			   {
				   maps.put(name,"{}");
			   }else{
				   String jsonString=JSON.toJSONString(field.get(this));
				   maps.put(name,jsonString);  
			   }
		   }else if(fType==FieldType.JsonList){
			   if(field.get(this)==null)
			   {
				   maps.put(name,"[]");
			   }else{
				   String jsonString=JSON.toJSONString(field.get(this));
				   maps.put(name,jsonString);  
			   }
		   }
	   }	
	   return maps;
}
	//通过Cursor自动将值赋值到实体
	@JSONField(serialize=false)
	public void initFromCursor(Cursor c) throws IllegalAccessException, IllegalArgumentException{
		setFieldValue(c);						
	}
```

    	@JSONField(serialize=false)
    	public ContentValues getContentValues() throws IllegalAccessException, IllegalArgumentException
    	{
    		ContentValues cv;
    		cv=new ContentValues();
    		Map<String,Object> maps=getFieldValue(true);
    		Set<String> keys=maps.keySet();		
    		for(String s:keys){
    			try{  Object obj=maps.get(s);			
    				  String typeString=obj.getClass().getName();
    				  if(obj==null){
    					  cv.put(s,"");
    				  }else if(typeString.equals(type_boolean)){
    					  cv.put(s,(Boolean)(obj));  
    				  }else if(typeString.equals(type_date)){
    					  cv.put(s,((Date)(obj)).getTime());  
    					}else if(typeString.equals(type_integer)){
    						cv.put(s,(Integer)(obj));  
    					}else if(type_long.equals(typeString)){
    						cv.put(s,((Long)(obj)));  
    					}else if(typeString.equals(type_float)){
    						cv.put(s,(Float)(obj));  
    					}else if(typeString.equals(type_double)){
    						cv.put(s,(Double)(obj));  
    					}else if(typeString.equals(type_string)){
    						cv.put(s,(String)(obj));
    					}else{
    						cv.put(s,JSON.toJSONString(obj));  
    					}
    			} catch (Exception e) {
    				Log.e(this.getClass().getName(), e.toString());
    				e.printStackTrace();
    			    continue;
    			}		
    		}//end for
    		return cv;
    	}
    	/**
    	 * 返回该类属性的键值对,键和值均为String类型
    	 * @return
    	 * @throws IllegalAccessException
    	 * @throws IllegalArgumentException
    	 */

```java
	@JSONField(serialize=false)
	public Map<String,Object> getMapValues() throws IllegalAccessException, IllegalArgumentException
	{
	   return getFieldValue(false);	
	}
```

    	@JSONField(serialize=false)
    	public void saveToDataBase(String tableName,SQLiteDatabase db) throws Exception{		
    		if(getId()==0)
    			throw new Exception("存储的_id号码不能够是0,请稍后再试!");
    		Map<String,Object> maps=getFieldValue(true);
    		Set<String> keys=maps.keySet();		
    		Object[] objs=new Object[keys.size()];
    		String q="";
    		String sql="insert into "+tableName.trim()+"(";
    		int i=0;
    		for(String s:keys){
    			Object obj=maps.get(s);
    			 if(i!=0)
    			  {
    				  sql+=",";
    			      q+=",";
    			  }
    			  sql+=s;
    			  q+="?";
    			  objs[i]=obj;
    			i++;			
    		}
    		sql+=") values ("+q+")";
    		db.execSQL(sql, objs);
    	}	

    	@JSONField(serialize=false)
    	public void updateToDataBase(String tableName,SQLiteDatabase db) throws Exception{
    		if(getId()==0)
    			throw new Exception("更新的_id号码不能够是0,请稍后再试!");
    		this.updateToDataBaseByColumn(tableName, db, primaryKeyName);
    	}
    	/**
    	 *
    	 * @param tableName
    	 * @param db
    	 * @param columnName 指定此此表的一个列名称,更新所有相同的记录
    	 * @throws Exception
    	 */
    	@JSONField(serialize=false)
    	public void updateToDataBaseByColumn(String tableName,SQLiteDatabase db,String columnName) throws Exception{
    		if(columnName==null)
    			throw new Exception("更新的columnName不能够是null,请稍后再试!");
    		Map<String,Object> maps=getFieldValue(true);
    		Set<String> keys=maps.keySet();		
    		Object[] objs=new Object[keys.size()+1];
    		String sql="update "+tableName.trim()+" set ";
    		int i=0;
    		for(String s:keys){
    			Object obj=maps.get(s);
    			if(i!=0)
    			  {
    				  sql+=",";
    			  }
    			  sql+=s+"=?";		  
    			  objs[i]=obj;
    			  if(s.equals(columnName)){
    	              objs[keys.size()]=obj;
    			  }
    			i++;			
    		}		
    		sql=sql+" where "+columnName+"=?";		
    		db.execSQL(sql, objs);  
    		 //data.close();
    	}

    	/**
    	 *
    	 * @param tableName
    	 * @param data
    	 * @param notUpdateColumns 不需要跟新的字段,区分大小写
    	 * @throws Exception
    	 */

```java
	@JSONField(serialize=false)
	public void updateToDataBase(String tableName,SQLiteDatabase db,String[] notUpdateColumns) throws Exception{
		if(getId()==0)
			throw new Exception("更新的_id号码不能够是0,请稍后再试!");		
		Map<String,Object> maps=getFieldValue(true);
		Set<String> keys=maps.keySet();		
		Object[] objs;
		Map<String,Object> updateMap=new HashMap<String,Object>();
		String sql="update "+tableName.trim()+" set ";
		int i=0;
		for(String s:keys){//筛选出来需要更新的数据
			  boolean need=true;
		      if(notUpdateColumns!=null)
			  for(String c:notUpdateColumns){
					if(c.equals(s))
					{
						need=false;
						break;
					}
				}
		      if(need){
		    	  updateMap.put(s,maps.get(s));
		      }
}		
		Set<String> key=updateMap.keySet();
		objs=new Object[key.size()+1];
		i=0;
		for(String s:key){
			Object value=updateMap.get(s);
			if(i!=0)
			  {
				  sql+=",";
			  }
			  sql+=s+"=?";
			  objs[i]=value;
			  if(s.equals(primaryKeyName))
			  {	objs[key.size()]=value; }
		  i++;
		}		
		sql=sql+" where "+primaryKeyName+"=?";	
		db.execSQL(sql, objs);
	}

	@Override
	public boolean equals(Object o) {
		if(this.getClass().getName().equals(o.getClass().getName())&&this.getId()-((BaseEntity)o).getId()==0)
			return true;
		return super.equals(o);
	}
```

```java
	@Override
	public int hashCode() {
		return getId().intValue();
	}	

	public abstract Long getId();

}
```

其中Entity_FieldProperty这个注解主要是帮助我们对对象和List进行存储以及读取,说白了就是简单的将之转化为json字符串,然后进行相关的序列号与反序列化;

至于List嵌套和对象嵌套的反序列化,可以查看博文<http://blog.csdn.net/huitoukest/article/details/50071867>

    /**
     * 指定当前Entity中的属性的属性,即自生的类别和转换的方式
     * @author dview76
     * 当FieldType.Base的时候,将会按照默认识别的类型使用,即此时的cls属性不会生效
     * JsonList,JsonObject,Base,Transient
     * JsonList,JsonObject表示此对象需要转换为一个json对象或者字符串;
     * Transient表示此对象,不进行数据库的存和取操作,选择Transient的时候,cls属性不会生效
     */
    @Target(ElementType.FIELD)
    @Retention(RetentionPolicy.RUNTIME)
    public @interface Entity_FieldProperty {

    	/**
    	 * 指定一个类型是FieldType的,表现为FieldType=默认为FieldType.Base的Annotation
    	 * @return
    	 */
    	FieldType FieldType() default FieldType.Base;
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
public enum FieldType{   	  
	JsonList,JsonObject,Base,Transient;
	};
```

    }

之后是主角BaseAndroidDao,其实就是增删改查方法的封装:

约定如下:此dao中不会管理事务;

    /**
     * Dao中不会管理事务,事务在Service层中进行管理
     * @author dview
     *
     */
    public class BaseAndroidDao<T extends BaseEntity> {
    	private String tableName;
    	private  DataBaseManager dbManager;
    	public BaseAndroidDao(String tableName) {
    		super();
    		this.dbManager=DataBaseManager.getInstance();
    		this.tableName = tableName;
    	}

    	public SQLiteDatabase openDataBase(){
    		  return dbManager.openDatabase();
    	}

    	public void closeDataBase(){
    		dbManager.closeDatabase();
    	}

    	/**
    	 * 得到当前的最大的id号码的值
    	 * @param db
    	 * @return
    	 */
    	public Long getMaxId(SQLiteDatabase db){
    		Cursor c=null;  	
    		c=this.getCursor(db,tableName,null,"select max("+T.primaryKeyName+") ", null,null,null,null,null);
        	if(c.moveToNext()){
        		return c.getLong(c.getColumnIndex(T.primaryKeyName));
        	}else return null;
    	}

    	/**
    	 * 得到当前的最小的id号码的值
    	 * @param db
    	 * @return
    	 */
    	public Long getMinId(SQLiteDatabase db){
    		Cursor c=null;  	
    		c=this.getCursor(db,tableName,null,"select min("+T.primaryKeyName+") ", null,null,null,null,null);
        	if(c.moveToNext()){
        		return c.getLong(0);
        	}else return null;
    	}

    	/**
    	 * 得到当前的的记录总数
    	 * @param db
    	 * @return
    	 */
    	public Long getCount(SQLiteDatabase db){
    		Cursor c=null;  	
    		c=this.getCursor(db,tableName,null,"select count(*) ", null,null,null,null,null);
        	if(c.moveToNext()){
        		return c.getLong(0);
        	}else return null;
    	}
    	/**
    	 * 返回所保存到数据库中的列表
    	 * @param entity
    	 * @return
    	 */
    	protected List<String> getEntityColumnNameList(Class<?> cls){
    		   List<String> list=new ArrayList<String>();
    		   Class<?> clazz=cls;
    		   Field[] fs=clazz.getDeclaredFields();		
    		   String filedName=null;
    		   for(Field field:fs){
    			   field.setAccessible(true);
    			   filedName=field.getName();
    			   Annotation[] as=field.getAnnotations();
    			   Class fclass=null;
    			   FieldType fType=null;
    			   for(int i=0;i<as.length;i++){
    				   Annotation a=as[i];
    				   if(a instanceof Entity_FieldProperty){
    					   Entity_FieldProperty ef=(Entity_FieldProperty)a;
    					   if(ef!=null){
    						   fclass=ef.cls();
    						   fType=ef.FieldType();
    						}
    					   break;
    				   }
    			   }
    			   if(fType==null||fType!=FieldType.Transient)
    			   list.add(filedName);
    		   }
    		   return list;
    	}

    	/*
    	 *得到除开指定名称的属性列
    	 */
    	public String[] getEntityColumnNames(Class<?> cls,Boolean isRepacePrimaryKeyName,String... exceptCoulums){
    		List<String> nameList=getEntityColumnNameList(cls);
    		if(isRepacePrimaryKeyName==null){
    			isRepacePrimaryKeyName=true;
    		}
    		if(exceptCoulums!=null){
    			for(String s:exceptCoulums){
    				nameList.remove(s);
    			}
    		}
    		String[] names=new String[nameList.size()];
    		for(int i=0;i<nameList.size();i++){
    			names[i]=nameList.get(i);
    			if(names[i].toLowerCase(Locale.ENGLISH).equals("id")){
    				names[i]=BaseEntity.primaryKeyName;
    			}
    		}
    		return names;
    	}

    	/**失败返回null
    	 *  传入代Id值的Entity的值实例
    	 * @param t 返回t
    	 * @return
    	 * @throws Exception
    	 */
    	public T get(SQLiteDatabase db,T t) throws Exception{	    	  
        	if(t==null) return null;
        	Cursor c=null;
        	try {   		
    			c=this.getCursor(db,tableName, null, T.primaryKeyName+"=?", new String[]{t.getId()+""}, null, null, null,null);
    	    	if(c.moveToNext())
    	    	{ t.initFromCursor(c);
    	    	  return t;
    	    	}else{
    	    		return null;
    	    	}
    		} catch (Exception e) {
    			Log.e(this.getClass().getName()+"T get:",e.toString());
    			throw e;
    		}finally{
    			if(c!=null) c.close();			
    		}   		       	
    	}
    	/**手动的条件搜索
    	 * @return
    	 * @throws Exception
    	 */
    	public T get(SQLiteDatabase db,Class<T> cls,String[] columns,String selection, String[] selectionArgs, String orderBy) throws Exception{	    	  
        	Cursor c=null;
        	try {   		
    			c=this.getCursor(db,tableName,columns, selection, selectionArgs, null, null, orderBy,"0,1");
    	    	if(c.moveToNext())
    	    	{ T t=cls.newInstance();
    	    	  t.initFromCursor(c);
    	    	  return t;
    	    	}else{
    	    		return null;
    	    	}
    		} catch (Exception e) {
    			Log.e(this.getClass().getName()+"T get:",e.toString());
    			throw e;
    		}finally{
    			if(c!=null) c.close();			
    		}   		       	
    	}

    	/**失败返回null
    	 *  传入代Id值的Entity的值实例
    	 * @param t 返回t
    	 * @param exceptCoulums 不需要取出的数据列的名称
    	 * @return
    	 * @throws Exception
    	 */

```java
	public T get(SQLiteDatabase db,T t,String... exceptCoulums) throws Exception{	    	  
	if(t==null) return null;
	Cursor c=null;
	try {
		String[] names=getEntityColumnNames(t.getClass(), true,exceptCoulums);
			c=this.getCursor(db,tableName,names, T.primaryKeyName+"=?", new String[]{t.getId()+""}, null, null, null,null);
	    	if(c.moveToNext())
	    	{ t.initFromCursor(c);
	    	  return t;
	    	}else{
	    		return null;
	    	}
		} catch (Exception e) {
			Log.e(this.getClass().getName()+"T get:",e.toString());
			throw e;
		}finally{
			if(c!=null) c.close();			
		}   		       	
	}
```

    	/**
    	 *
    	 * 失败返回空数组
    	 * @param db
    	 * @param cls
    	 * @param selection
    	 * @param selectionArgs
    	 * @param orderBy
    	 * @param limit select * from table_name limit N,M //N序号从0开始
    	 * @param exceptCoulums 指定不从数据库取出的列
    	 * @return
    	 * @throws Exception
    	 */
    	 public List<T> getList(SQLiteDatabase db,Class<T> cls,String selection, String[] selectionArgs, String orderBy,String limit,String... exceptCoulums) throws Exception{
    		 List<T> ts=new ArrayList<T>();
    		 Cursor c = null;
    		 try {
    			 String[] names=getEntityColumnNames(cls, true, exceptCoulums);
    			 c=this.getCursor(db,tableName,names, selection, selectionArgs, null, null, orderBy,limit);
    			 while(c.moveToNext()){
    				 T t=cls.newInstance();
    				 t.initFromCursor(c);
    				 if(!ts.contains(t))
    				 ts.add(t);
    			 }		
    		} catch (Exception e) {
    			Log.e("getList:"+cls.getName(),e.toString());
    			throw e;
    		}finally{
    			 if(c!=null) c.close();				
    		}
    		 return ts;
    	    }
    	/**
    	 * 失败返回空数组
    	 * @param db
    	 * @param cls
    	 *@param selection
    	 * @param selectionArgs
    	 * @param orderBy
    	 * @param limit select * from table_name limit N,M //N序号从0开始
    	 * @return
    	 * @throws Exception
    	 */
    	 public List<T> getList(SQLiteDatabase db,Class<T> cls,String selection, String[] selectionArgs, String orderBy,String limit) throws Exception{
    		 List<T> ts=new ArrayList<T>();
    		 Cursor c = null;
    		 try {
    			c=this.getCursor(db,tableName, null, selection, selectionArgs, null, null, orderBy,limit);
    			 while(c.moveToNext()){
    				 T t=cls.newInstance();
    				 t.initFromCursor(c);
    				 if(!ts.contains(t))
    				 ts.add(t);
    			 }		
    		} catch (Exception e) {
    			Log.e("getList:"+cls.getName(),e.toString());
    			throw e;
    		}finally{
    			 if(c!=null) c.close();				
    		}
    		 return ts;
    	    }
    	 /**
    	  * 获取数据库中的所有的记录
    	  * @param db
    	  * @param cls
    	  * @return
    	  * @throws Exception
    	  */
    	 public List<T> getList(SQLiteDatabase db,Class<T> cls) throws Exception{
    		 List<T> ts=new ArrayList<T>();
    		 Cursor c = null;
    		 try {
    			c=this.getCursor(db,tableName, null,null,null, null, null,null,null);
    			 while(c.moveToNext()){
    				 T t=cls.newInstance();
    				 t.initFromCursor(c);
    				 if(!ts.contains(t))
    				 ts.add(t);
    			 }		
    		} catch (Exception e) {
    			Log.e("getList:"+cls.getName(),e.toString());
    			throw e;
    		}finally{
    			 if(c!=null) c.close();				
    		}
    		 return ts;
    	    }

    	 /**
    	  *
    	  * @param t
    	  * @return 插入返回1
    	 * @throws Exception
    	  */

```java
	 public void saveOrUpdate(SQLiteDatabase db,T t) throws Exception{
		 Cursor c = null;
		 try {
			c=this.getCursor(db,tableName, null, T.primaryKeyName+"=?", new String[]{t.getId()+""}, null, null, null,null);
		    	if(c.moveToNext())
		    	{//如果已经存在,则更新,否则insert
		    		t.updateToDataBase(tableName,db);
		    	    return;
		    	}		      
			 t.saveToDataBase(tableName,db);
			 return;
		} catch (Exception e) {
			Log.e("saveOrUpdate:"+t.getClass().getName(),e.toString());
			throw e;
		}finally{
			if(c!=null) c.close();
		}
	 }
```

    	 /**
    	  *
    	  * @param t
    	  * @return 插入返回1
    	  * @param columnName 如果指定的字段,有相同的值存在于数据库,那么就更新数据库,否则保存
    	  * @throws Exception
    	  */
    	 public void saveOrUpdate(SQLiteDatabase db,T t,String columnName) throws Exception{
    		 Cursor c = null;
    		 try {
    			c=this.getCursor(db,tableName, null, columnName+"=?", new String[]{t.getClass().getField(columnName).get(t)+""}, null, null, null,null);
    		    	if(c.moveToNext())
    		    	{//如果已经存在,则更新,否则insert
    		    		t.updateToDataBaseByColumn(tableName, db, columnName);
    		    	    return;
    		    	}		      
    			 t.saveToDataBase(tableName,db);
    			 return;
    		} catch (Exception e) {
    			Log.e("saveOrUpdate:"+t.getClass().getName(),e.toString());
    			throw e;
    		}finally{
    			if(c!=null) c.close();
    		}
    	 }

    	 /**
    	  * 先删除,后保存,没有则不删除
    	  * @param db
    	  * @param t
    	  * @throws Exception
    	  */
    	 public void deleteAndSave(SQLiteDatabase db,T t) throws Exception{
    		 try {
    			 this.delete(db, t.getId()+"");
    			 this.save(db, t);
    		} catch (Exception e) {
    			Log.e("saveOrUpdate:"+t.getClass().getName(),e.toString());
    			throw e;
    		}
    	 }

    	 /**
    	  *
    	  * @param db
    	  * @param list
    	  * @return
    	 * @throws Exception
    	  */
    	public void saveOrUpdateList(SQLiteDatabase db,List<T> list) throws Exception{
    		try{
    			for(T t:list){
    				saveOrUpdate(db, t);					
    			}
    		}catch(Exception e){
    			throw new Exception("saveOrUpdateList: "+" Fail");
    		}
    	}

    	/**
    	 *
    	 * @param db
    	 * @param list
    	 * @param column 指定列的值相同就更新,否则就保存
    	 * @throws Exception
    	 */
    	public void saveOrUpdateList(SQLiteDatabase db,List<T> list,String column) throws Exception{
    		try{
    			for(T t:list){
    				saveOrUpdate(db, t,column);					
    			}
    		}catch(Exception e){
    			throw new Exception("saveOrUpdateList: "+" Fail");
    		}
    	}

    	/**
    	  *删除后保存所有
    	  * @param db
    	  * @param list
    	  * @return
    	 * @throws Exception
    	  */
    	public void deleteAndSaveList(SQLiteDatabase db,List<T> list) throws Exception{
    		try{
    			for(T t:list){
    				deleteAndSave(db, t);					
    			}
    		}catch(Exception e){
    			throw new Exception("saveOrUpdateList: "+" Fail");
    		}
    	}

    	 public int update(SQLiteDatabase db,T t) throws Exception{
    		 try {
    			t.updateToDataBase(tableName,db);
        	    return 2;
    		} catch (Exception e) {
    			Log.e("update:"+t.getClass().getName(),e.toString());
    			throw e;
    		}
    	 }
    	 /**
    	  *
    	  * @param t
    	  * @param notUpdateColumns 不需要更新的字段名称的数组
    	  * @return
    	 * @throws Exception
    	  */
    	 public int update(SQLiteDatabase db,T t,String[] notUpdateColumns) throws Exception{
    		 try {
    			t.updateToDataBase(tableName,db,notUpdateColumns);
        	    return 2;
    		} catch (Exception e) {
    			Log.e("update:"+t.getClass().getName(),e.toString());
    			throw e;
    		}
    	 }

    	public int save(SQLiteDatabase db,T t) throws Exception{
    		 try {		
    			 t.saveToDataBase(tableName, db);
    			 return 1;
    		} catch (Exception e) {
    			Log.e("save:"+t.getClass().getName(),e.toString());
    			throw e;
    		}
    	 }

    	 public int delete(SQLiteDatabase db,String id) throws Exception{
    		 if(id.equals("0"))
    				throw new Exception("删除的_id号码不能够是0,请稍后再试!");  
    		 try {
    	   		this.delete(db,tableName, id);
    	   		return 1;
    		} catch (Exception e) {
    			Log.e("delete:"+this.getClass().getName(),e.toString());
    			throw e;
    		}
    	 }

    	 public int deleteList(SQLiteDatabase db,String ids) throws Exception{
    		   try {
    			   String whereClause=" "+T.primaryKeyName+" in (?)";
    			   String[] whereArgs=new String[]{ids};
    			   this.delete(db,tableName, whereClause, whereArgs);
    		    return 1;
    		   } catch (Exception e) {
    				Log.e("deleteList:"+this.getClass().getName(),e.toString());
    				throw e;
    		}
    	 }

    	 public int deleteAll(SQLiteDatabase db) throws Exception{
    		 try {
    			 this.delete(db,tableName, null,null);
    		    return 1;
    		   } catch (Exception e) {
    				Log.e("deleteAll:"+this.getClass().getName(),e.toString());
    				throw e;
    		}
    	 }	

    	 /**
    	  * 返回搜索的cursor;
    	  * @param db
    	  * @param sqlString
    	  * @param selectionArgs sql中?占位符的参数
    	  * @return
    	  */
    	 public Cursor getCursor(SQLiteDatabase db,String sqlString,String[] selectionArgs){
    		 return db.rawQuery(sqlString,selectionArgs);
    	 }

    	 /**
    	  *
    	  * @param db
    	  * @param sqlString
    	  * @param selectionArgs sql中?占位符的参数
    	  * @param columns 需要出去的列的名称,没有会赋值null;取出的列只支持float/string/blob/string/null这几种类型;
    	  * *其中二进制会转换成为byte[]类型;除开这些类型外,系统会默认用string来取出数据
    	  * @return List<Object[]>
    	  */
    	 public List<Object[]> getColumns(SQLiteDatabase db,String sqlString,String[] selectionArgs,String...columns){
    		 List<Object[]> list=new ArrayList<Object[]>();
    		 Object[] objs=null;
    		 Cursor cursor=getCursor(db, sqlString, selectionArgs);
    		 while(cursor.moveToNext()){
    		    objs=new Object[columns.length];
    		    try{
    			    for(int i=0;i<columns.length;i++){
    			    	String ss=columns[i];
    			        int index=cursor.getColumnIndex(ss);
    			        if(index==-1)
    			        continue;
    			    	int columnType =cursor.getType(index);
    			    	switch (columnType) {
    			    	case Cursor.FIELD_TYPE_NULL:
    			    		 objs[i]=null;
    			    		 break;		    	
    					case Cursor.FIELD_TYPE_INTEGER:
    						objs[i]=cursor.getInt(index);
    						 break;
    					case Cursor.FIELD_TYPE_BLOB:
    						objs[i]=cursor.getBlob(index);
    						break;
    					case Cursor.FIELD_TYPE_FLOAT:
    						objs[i]=cursor.getFloat(index);
    						break;
    					case Cursor.FIELD_TYPE_STRING:
    						objs[i]=cursor.getString(index);
    					break;
    					default:
    						objs[i]=cursor.getString(index);
    						break;
    					}		    	
    			    }
    			    list.add(objs);
    		    }catch(ClassCastException e){
    		    	e.printStackTrace();
    		    	Log.e("BaseAndroidDao:getColumns:",e.toString());
    		    }		    
    		 }
    		 return list;
    	 }

    	    public Cursor getCursor(SQLiteDatabase db,String table, String[] columns, String selection, String[] selectionArgs, String groupBy, String having, String orderBy,String limit) {
    	        Cursor cursor = db.query(table, columns, selection, selectionArgs, groupBy, having, orderBy,limit);
    	    	  return cursor;
    	    	}

    	    	public void execSQL(SQLiteDatabase db,String sql){
    	    		 db.execSQL(sql);
    	    	}

    	    	public void execSQL(SQLiteDatabase db,String sql,Object[] objs){
    	    		db.execSQL(sql,objs);
    	    	}

    	    	/**
    	    	 * 调用原生的insert方法,不推荐
    	    	 * @param tableName
    	    	 * @param cv
    	    	 * @return
    	    	 */
    	    	public long insert(SQLiteDatabase db,String tableName,ContentValues cv)
    	    	{
    	    		long row = db.insert(tableName, null, cv);
    	    		return row;
    	    	}
    	    	/**
    	    	 * 调用自己写的方法,insert into person(name,phone) values (?,?)
    	    	 * @param p
    	    	 */

```java
	    	public void save(SQLiteDatabase db,String sql,Object[] objs)  
	    	{
	    	 db.execSQL(sql, objs);  
	    	}  

	    	public void update(SQLiteDatabase db,String sql,Object[] objs){
	    		 db.execSQL(sql, objs);  
	    	}

	    	//删除操作 
	    	public void delete(SQLiteDatabase db,String tableName,String id) 
	    	{
	    		String where =BaseEntity.primaryKeyName + "=?"; 
	    		String[] whereValue ={id}; 
	    		db.delete(tableName, where, whereValue);
	    	}

	    	//删除操作 
	    	public void delete(SQLiteDatabase db,String table, String whereClause, String[] whereArgs) 
	    	{ 
	    		db.delete(table, whereClause, whereArgs); 
	    	}
```

```java
	    	//修改操作 
	    	public void update(SQLiteDatabase db,String tableName,int id, ContentValues cv) 
	    	{ 
	    		String where = BaseEntity.primaryKeyName+ "=?"; 
	    		String[] whereValue = { Integer.toString(id) }; 
	    		db.update(tableName, cv, where, whereValue); 
	    	}

	    	//修改操作 
	    	public void update(SQLiteDatabase db,String tableName,ContentValues cv, String where,String[] whereValue) 
	    	{ 
	    			db.update(tableName, cv, where, whereValue); 
	    	}

		public String getTableName() {
			return tableName;
		}

		public void setTableName(String tableName) {
			this.tableName = tableName;
		}	

}
```

这里DataBaseManager实际上是一个管理数据库连接的类,不需要的可以忽略,详情见:<http://blog.csdn.net/huitoukest/article/details/50469236>

# 3:使用示例:

```java
public class LoginTypeService {
private String tableName="loginType";
private BaseAndroidDao<LoginType> baseDao;

public LoginTypeService(){
	   baseDao=new BaseAndroidDao<LoginType>(tableName);
}

public LoginType getLoginType(){
	   LoginType lt=new LoginType();
	   lt.setId(1L);
	 SQLiteDatabase db = null;
	   try {
		   db=baseDao.openDataBase();
		   lt=baseDao.get(db, lt);
			   return lt;
		} catch (Exception e) {
			return null;
		}finally{
			baseDao.closeDataBase();
		}
}

public boolean saveOrUpdate(LoginType loginType){
	   if(loginType==null||loginType.getId()==null)
		   return false;
	   SQLiteDatabase db = null;
	   try {
		   db=baseDao.openDataBase();
		   db.beginTransaction();
		   baseDao.saveOrUpdate(db, loginType);
		   db.setTransactionSuccessful();
			   return true;
		} catch (Exception e) {
			return false;
		}finally{
			if(db!=null)
			db.endTransaction();
			baseDao.closeDataBase();
		}

}

}
```

注意:Service层,就是是控制层来负责事务的管理;
