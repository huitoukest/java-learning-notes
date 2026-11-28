---
title: "安卓数据库连接解决办法 ,避免 sqlite3 database is locked"
date: "2016-01-06 15:45:58"
categories: ["android操作"]
tags: ["android", "sqlite3", "数据库"]
---

# 1.说明

android的sqlite3数据库中,好像是因为数据库锁的机制问题,无法对同一个数据库同时进行写操作,所以可能爆出database is locked 的错误;

综合网上资料,觉得用单例模式,全局保持一个连接比较实用;

# 2.具体代码

首先具体连接数据库的代码如下:

    public class DataBaseOpenHelper extends android.database.sqlite.SQLiteOpenHelper{
    	private final static int DATABASE_VERSION = 2;
    	public DataBaseOpenHelper(Context context) {
    		this(context, "dview242.db", null,DATABASE_VERSION);	
    	}
    	/**
    	 *
    	 * @param context
    	 * @param name 数据库的名称
    	 */

```sql
	public DataBaseOpenHelper(Context context, String name) {
		this(context, name, null,DATABASE_VERSION);	
	}

	public DataBaseOpenHelper(Context context, String name, CursorFactory factory) {
		this(context, name, factory,DATABASE_VERSION);	
	}
	public DataBaseOpenHelper(Context context, String name, CursorFactory factory,int version){
		super(context, name, factory,version);
	}

	//创建table 
	@Override
	public void onCreate(SQLiteDatabase db) { 
		//decimal(19,0),sqlite不直接支持date类型的存储(支持创建),所以使用decimal(19,0)类型来保存;
		String userSql="create table user(_id decimal(19,0) primary key,State decimal(19,0),Uid text,Login_Name text,UserInfo text,Password text,Real_Name text,rememberMe integer,autoLogin integer)";
		db.execSQL(userSql); 

	} 

	@Override
	public void onUpgrade(SQLiteDatabase db, int oldVersion, int newVersion) { 
		String s="DROP TABLE IF EXISTS ";
		String userSql=s+"user";	
```

```java
		db.execSQL(userSql);
		onCreate(db); 
	} 

	@Override
	public synchronized void close() {
		super.close();
	} 
}
```

然后,用一个单例来管理此连接,并保证同一时间只有一个连接且只有一个读或者写的操作;

```java
public class DataBaseManager {
	private static DataBaseManager instance;
@SuppressWarnings("unused")
	private static DataBaseOpenHelper databaseHelper;
private AtomicInteger mOpenCounter = new AtomicInteger();

@SuppressLint("NewApi")
	public static synchronized void initializeInstance(Context c) {
if (instance == null) {
instance = new DataBaseManager();
databaseHelper =new DataBaseOpenHelper(c);
if(Build.VERSION.SDK_INT>17)
{ 
	databaseHelper.setWriteAheadLoggingEnabled(true);
}
}
}

public static synchronized DataBaseManager getInstance() {
if (instance == null) {
throw new IllegalStateException(DataBaseManager.class.getSimpleName() +
" is not initialized, call initializeInstance(..) method first.");
}
return instance;
}

public synchronized SQLiteDatabase openDatabase() {
if(mOpenCounter.incrementAndGet() == 1) {
return  databaseHelper.getWritableDatabase();
}
return null;
}

public synchronized void closeDatabase() {
if(mOpenCounter.decrementAndGet() == 0) {
	databaseHelper.close();
}
}  

}
```

# 3.使用方式:

在第一个启动的activity或者application中,调用dbManager.initializeInstance(getApplicationContext());来初始化一次即可;

之后,调用DataBaseManager getInstance()货获取DataBaseManager实例,

即可以在控制层使用,读操作无需开启事务;但是写操作一定要记得开启和关闭事务:

```java
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
```

# 注意:

baseDao中的open和close调用的DataBaseManager中的open和close;

如果仍然遇到失败或者 database is locked 错误,请检查是否数据库的打开和关闭次数是否一致(即你是否忘记关闭数据库了);

同时检查是否忘记关闭事务(即db.setTransactionSuccessful()和db.endTransaction()方法);
