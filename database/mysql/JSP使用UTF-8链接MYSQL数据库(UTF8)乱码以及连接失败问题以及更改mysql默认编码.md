---
title: "JSP使用UTF-8链接MYSQL数据库(UTF8)乱码以及连接失败问题以及更改mysql默认编码"
date: "2014-06-01 10:19:52"
categories: ["数据库"]
tags: ["数据库", "mysql", "乱码", "utf-8", "jsp"]
---

JSP使用UTF-8链接MYSQL数据库(UTF8)乱码以及连接失败问题：  

前言，服了这些大公司，做的数据库都不人性化。。。我忙了很久才搞定的说

csdn好像传不了图片了。。。本来想来几张的，大家将就。。。

# 1.在windows下mysql的数据库是utf8编码的时候，连接失败(注意mysql中不是UTF-8，而是utf8)

### **情况，显示？在网页上(网页设置的UTF-8编码)**

用户ID号码 | 用户名称 | 用户密码 | 用户地址  
---|---|---|---  
47 | g? | 1243 | null  
48 | ? | 1243 | null  
49 | ?123 | 1243 | null  
50 | ?23 | 1243 | null  
51 | ?3 | 1243 | null  

### **在数据库设定客户端的语言为GBK可以显示，猜测是内部采用utf8编码，设定之后会自定转换成为GBK编码：**

mysql> set names gbk  
    -> ;  
Query OK, 0 rows affected (0.00 sec)  

mysql> select * from user;  
+\--------+\-----------+\--------------+\------------+  
| userid | username  | userpassword | useradress |  
+\--------+\-----------+\--------------+\------------+  
|      1 | 我          | NULL         | NULL       |  
|      2 | ?2        | 1243         | NULL       |  
|      3 | ??37fg459 | 1243         | NULL       |  

### **当然，用utf8编码的换，一定会乱码的，猜测是windows默认编码是GBK，所以utf是显示不了的。**

mysql> set names utf8;  
Query OK, 0 rows affected (0.00 sec)  

mysql> select * from user;  
+\--------+\-----------+\--------------+\------------+  
| userid | username  | userpassword | useradress |  
+\--------+\-----------+\--------------+\------------+  
|      1 | 鎴?       | NULL         | NULL       |  
|      2 | ?2        | 1243         | NULL       |  
|      3 | ??37fg459 | 1243         | NULL       |  
|      4 | 澶?       | 1243         | NULL       |  

下面说一下解决的方法：

# 2.第一步检查数据库的编码方式：

### 打开数据库的命令行，输入命令  status;

     mysql> status;  
\--------------  
D:\mysql_6.0\bin\mysql.exe  Ver 14.15 Distrib 6.0.11-alpha, for Win64 (unknown)  

Connection id:          72  
Current database:       contacts  
Current user:           root@localhost  
SSL:                    Not in use  
Using delimiter:        ;  
Server version:         6.0.11-alpha-community MySQL Community Server (GPL)  
Protocol version:       10  
Connection:             localhost via TCP/IP  
Server characterset:    utf8  
Db     characterset:    utf8  
Client characterset:    utf8  
Conn.  characterset:    utf8  
TCP port:               3306  
Uptime:                 9 hours 25 min 53 sec  

Threads: 7  Questions: 749  Slow queries: 0  Opens: 23  Flush tables: 1  Open ta  
bles: 2  Queries per second avg: 0.22  
\--------------

### 还有个命令也可以查看：   show variables like "%char%"

mysql> show variables like "%char%";  
+\--------------------------+\------------------------------+  
| Variable_name            | Value                        |  
+\--------------------------+\------------------------------+  
| character_set_client     | utf8                         |  
| character_set_connection | utf8                         |  
| character_set_database   | utf8                         |  
| character_set_filesystem | binary                       |  
| character_set_results    | utf8                         |  
| character_set_server     | utf8                         |  
| character_set_system     | utf8                         |  
| character_sets_dir       | D:\mysql_6.0\share\charsets\ |  
+\--------------------------+\------------------------------+  
8 rows in set (0.00 sec)  

基本上编码做到楼主这个程度，可以确定数据库的默认编码没有问题了。

## 3.检查数据库的编码，输入命令：

show create database mydata，这里mydata指的是一个数据库的名称。  

mysql> show create database mydata;  
+\----------+\--------------------------------------------------------------------  
\--------------+  
| Database | Create Database  
              |  
+\----------+\--------------------------------------------------------------------  
\--------------+  
| mydata   | CREATE DATABASE `mydata` /*!40100 DEFAULT CHARACTER SET utf8 COLLAT  
E utf8_bin */ |  
+\----------+\--------------------------------------------------------------------  
\--------------+  
1 row in set (0.00 sec)  

### 4.检查数据库中表和列的编码，在选择一个数据库之后在命令行输入如下命令：

user在这里是一个表名字

show create table user;  

mysql> show create table user;  
+\-------+\-----------------------------------------------------------------------  
\-----------------------------------------------------------------------------  
\-----------------+  
| Table | Create Table  

                 |  
+\-------+\-----------------------------------------------------------------------  
\--------------------------------------------------------------------------  
\-----------------+  
| user  | CREATE TABLE `user` (  
`UserID` int(11) NOT NULL AUTO_INCREMENT,  
`username` varchar(20) COLLATE utf8_bin NOT NULL,  
`userpassword` varchar(20) COLLATE utf8_bin NOT NULL,  
`address` varchar(100) COLLATE utf8_bin DEFAULT NULL,  
PRIMARY KEY (`UserID`),  
UNIQUE KEY `UserName` (`username`),  
UNIQUE KEY `username_2` (`username`)  
) ENGINE=InnoDB AUTO_INCREMENT=72 DEFAULT CHARSET=utf8 COLLATE=utf8_bin |  
+\-------+\-----------------------------------------------------------------------  
\-------------------------------------------------------------------------------  
\-----------------+  
1 row in set (0.00 sec)  

之后检查，每一列后面的编码是不是utf8，同时看表格后边的charset=多少 ,collate后面指定的编码方式，指的是数据库搜索的时候使用的匹配编码规则。

做到3和4中的情况,基本可以确定数据库和表格中的编码是没有任何的问题了。其余的问题只能够处在jsp中以及jsp和数据库的连接之中。

### 5.检查jsp中的代码是否全部是UTF-8的方式。

**第一步：**

对于jsp页面本身：

<%@page contentType="text/html ; charset=UTF-8 "  pageEncoding="UTF-8" %>  

**第二步：**

对于html页面本身：

<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">  

**第三步：**

jsp:request.setCharacterEncoding("UTF-8");  
jsp:response.setCharacterEncoding("UTF-8");  

做到如上，基本上jsp中的代码完全没有问题了，保证都是UTF-8.

### 6.检查连接过程是否出现问题，楼主就是这里出了问题，结果找了很久。。。

在jsp中链接数据库的时候：

Connection conn = DriverManager.getConnection("jdbc:mysql://localhost/mydata?user=root&password=password1&useUnicode=true&characterEncoding=UTF-8");  

注：这里mydata是数据库名称

    localhost是本机host

    root是连接数据库的用户名

    password1是连接数据库的密码

    useUnicode=true&characterEncoding=UTF-8指定了连接使用的编码方式

楼主曾经也想过在连接没用 useUnicode=true&characterEncoding=UTF-8 的凡事，在连接之后 用set names utf8的方式，但是没有成功。

以上，问题完全解决了，以防万一，建议大家讲IDE的编码设置为UTF-8,什么eclipse myeclipse netbeanse 你懂的。。。。

### 7.在servl中的设置：

request.setCharacterEncoding("UTF-8");  
response.setCharacterEncoding("UTF-8");  
response.setContentType("text/html;charset=UTF-8");  

# MYSQL数据库已经其中的表和列如果一开始编码不是UTF-8，要设置成为UTF-8可以采用如下的方式。

### 注意：如果表中存在数据，有可能发生错误。

### 1.将数据库的编码改为UTF-8

Alter DATABASE 'test' DEFAULT CHARACTER SET utf8 COLLATE utf8_bin  

以上命令就是将test数据库的编码设为utf8.  

### 2.将表的编码改为UTF-8

Alter TABLE 'category' DEFAULT CHARACTER SET utf8 COLLATE utf8_bin  

以上命令就是将一个表category的编码改为utf8.  

### 3.将表中字段(每一列)的编码改为UTF-8

Alter TABLE 'test' CHANGE 'dd' 'dd' VARCHAR( 45 ) CHARACTER SET utf8 COLLATE utf8_bin NOT NULL  

以上命令就是将test表中 dd的字段编码改为utf8.  

此命令在需要特殊编码的字段也可以指定此字段为特殊编码，如中文中一些符号utf8中没有,可以将某一字段设置为GBK，即可以存储此符号，但是记得存取数据的时候要转码

### 4.设置其他(默认)编码：

在mySQL安装目录，打开mysql.ini,将所有character后边的编码改成utf8，这样就改变的创建新数据库和表的时候的默认编码，MYSQL重启不失效。

## 用如SQL Font等软件链接乱码:

1.连接的字符串选择为当前运行系统默认显示的编码,一般windows是GBK

2.打开数据库后如果乱码,将数据库的编码设置为其原本方式,如果数据库是utf8,那么设置为utf8,不过一般这一步是自动的

3.使用mysql font5.3版本可能乱码等问题,建议用mysql5.1版本.
