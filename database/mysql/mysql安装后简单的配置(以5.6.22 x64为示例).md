---
title: "mysql安装后简单的配置(以5.6.22 x64为示例)"
date: "2015-12-10 20:24:49"
categories: ["数据库"]
tags: ["mysql", "5.6.22", "修改密码", "配置"]
---

1.不是到是5.7xx的mysql怎么了,我安装了几次没有成功,自己写个5.6绿色版的安装教程,免得以后自己连5.6都安装不来了;

2.下载,安装解压,配置;最好自定义安装的目录,这样方便自己更改设置;

安装完毕之后,安装目录下面有一个data目录,这里面存放的是一些mysql的必要数据,mysql5.7.9以上好像没有了这个文件夹.....

之后再安装目录下面有个.ini文件,用记事本打开,来配置数据库启动的一些必要信息;

一下命令最好在mysql的bin目录下面运行;

我的配置如下,大家可以拷贝使用:

```
[client]
port=3306
default-character-set=utf8

[mysqld]
port=3306

character_set_server=utf8
basedir=D:/Soft_Develop/mysql5.6    
datadir=D:/Soft_Develop/mysql_data/data    

join_buffer_size = 128M
sort_buffer_size = 2M
read_rnd_buffer_size = 2M 

sql_mode=NO_ENGINE_SUBSTITUTION,STRICT_TRANS_TABLES 
```

其中client应该是客户端使用的配置;

mysqld指的是本地mysql运行的时候的配置;

basedir=后面是你mysql的安装目录;

datadir=就是此数据库的data目录;

3.在配置好之后,需要安装mysql的服务:

这个时候一般建议将安装目录下的bin目录的路径;..../mysql5.6.22/bin这个路径加入到path当中,方便输入名称;

不过你直接在此目录下打开cmd面输入命令也行,总之开打cmd输入如下命令:

3.1安装mysql服务的命令如下:

    mysqld --install MySQL --defaults-file="你的.ini配置文件的路径"

理论上只使用mysqld -install会使用默认的配置文件(就是我们上面配置的安装目录下面的.ini文件)安装服务;

3.2安装服务之后,便可以启动服务:

    net start mysql

3.3如果如想要停止服务可以:

    net stop mysql

3.4如果启动服务没有成功,可以移除服务,重新编写配置文件,然后在此安装启动服务,移出命令如下:

    mysqld --remove MySQL

4.如果一直没有搞成功,可以尝试查看控制台的情况:

    mysqld --console

5.安装成之后是需要修改密码的,默认第一次用户名是root,密码为空(即不用输入)

首先登录:

    mysql -uroot -p

在输入密码之后,可以修改密码:

修改密码命令如下:

```
1.use mysql;

2.update user set password=password('你的密码') where user='root';

3.flush privileges;
```

6.附上mysql软件一枚:

<http://download.csdn.net/detail/huitoukest/9345055>

7.修改用户登录权限,允许指定用户从任意ip连接到服务器

```
#允许root用户从任意域名连接到mysql;
GRANT ALL PRIVILEGES ON *.* TO 'root'@'%%' WITH GRANT OPTION;
#立即生效
flush privileges;
```

mysql 42000错误,可以尝试加入密码:

GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' IDENTIFIED BY 'root' WITH GRANT OPTION

8\. 添加用户

    CREATE USER 'nlsper'@'127%' IDENTIFIED BY 'nlsper';

9\. mysql 5.7 之后若添加的用户密码不生效 , 可以更设置

    update mysql.user set authentication_string=password('nlsper') where user='nlsper' and Host = 'localhost';
