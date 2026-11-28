---
title: "Ubuntu14.04.2下nginx1.6和sticky1.1模块的安装与简单配置"
date: "2016-02-01 17:48:58"
categories: ["Linux/windows"]
tags: ["ubuntu", "nginx", "linux", "sticky"]
---

# 前言

写作日期:20160201


接触Ubuntu和linux时间很短,为了配置nginx学习了一点,打算先写入博客,以后不再走重复的路,顺便帮助下他人;

# 准备

首先安装好ubuntu14.04.2版本系统,并下载相关的一些包文件;

包括:

Sticky1.1

Nginx1.6

两个最主要的包,以及一些编译需要的支持包;

openssl-1.0.1.tar.gz   

注意:openssl的版本不能过高,不然可能会出现问题,推荐使用博主提供的版本

zlib-1.2.8.tar.gz

pcre-8.35.zip 注意:prece不是prece2;

还有些我们需要的开发包可在线获取,在终端以管理员身份输入如下命令:

(使用su root 或者sudo su root可以获取root权限)

sudo apt-get install build-essential libpcre3-dev libssl-dev libxslt-dev libgd2-xpm-dev libgeoip-dev

Sudo apt-get install yum

同样如果缺少一些包,可以使用上诉模式尝试获取:

包括上面的openssl,可以使用sudo apt-get install openssl获取;

如果需要更多的模块支持,可以自行下载nginx的模块包;

# 解压软件包

对于.tar.gz文件,采用tar zxvf XXX方式解压到当前目录,如tar zxvf openssl-1.0.1.tar.gz;

分别将上诉的.gz文件解压完毕;

对于zip文件可以采用unzip XX方式解压到当前目录,如unzip pcre-8.35.zip;

解压后的软件包中,可以进入软件包解压的源目录,执行的命令;

./configure

make && make install

# 编译nginx

以root权限,进入nginx解压后的源目录中;

cd nginx-1.6.0

    ./configure 	--prefix=/usr/local/nginx --sbin-path=/usr/local/nginx/nginx --conf-path=/usr/local/nginx/nginx.conf --pid-path=/usr/local/nginx/nginx.pid --with-http_ssl_module --with-zlib=../zlib-1.2.8 --with-openssl=../openssl-1.0.1  --add-module=../nginx-sticky-module-1.1

命令解释:

cd nginx-1.6.0 进入nginx-1.6.0目录

./configure  \--prefix=/usr/local/nginx  指定安装目录为/usr/local/nginx

\--sbin-path=/usr/local/nginx/nginx

指定nginx可执行文件位置/usr/local/nginx/nginx

\--conf-path=/usr/local/nginx/nginx.conf

指定配置文件的位置/usr/local/nginx/nginx.conf

\--pid-path=/usr/local/nginx/nginx.pid

指定pid的文件路径

\--with-http_ssl_module

加入支持包,如果本机已经安装,可以不指出其源目录

\--with-zlib=../zlib-1.2.8

加入支持包,如果本机没有,必须出其源目录

\--with-openssl=../openssl-1.0.1

\--add-module=../nginx-sticky-module-1.1

加入支持模块,后面是模块解压目录的路径

注意:

在加入sticky之前,需要对sticky的源码做一些修改,不然可能会报错,建议首先运行一次,如果报错每通过,再进行修改重试;编译的时间长短和机子的配置有关,博主三代i5感觉要编译几分钟时间;

上面的命令是不换行的,只是为了显示效果才换行,每个\--XXX命令之前需要空一格;

然后分别执行编译源码,和编译安装的命令

make

make install

# 修改sticky

编译时出现错误：

cc1: warnings being treated as errors

ngx_http_sticky_module.c: In function ‘ngx_http_get_sticky_peer’:

/ngx_http_sticky_module.c:333: 警告：赋值时将整数赋给指针，未作类型转换

ake[1]: *** [objs/addon/nginx-sticky-module-1.1/ngx_http_sticky_module.o] 错误 1

根据资料 把ngx_http_sticky_misc.c 的281行修改如下

原digest->len = ngx_sock_ntop(in,digest->data, len, 1);

改后digest->len = ngx_sock_ntop(in,sizeof(struct sockaddr_in),digest->data, len, 1);

对nginx-sticky-module-1.1/ngx_http_sticky_module.c文件也进行修改（主要是1.9.x版本会出现这问题)

第6行添加c语言头文件:

# include <nginx.h>

第340行左右修改（iphp->rrp.current = iphp->selected_peer;）

为：

# if defined(nginx_version) && nginx_version >= 1009000

iphp->rrp.current = peer;

# else

iphp->rrp.current = iphp->selected_peer;

# endif

修改完毕之后,重新编译安装即可;

# nginx的简单命令

找到nginx的安装目录,找到你编译好的可执行文件,获取root权限;

1、 启动、停止Nginx

A、 启动命令

/usr/local/nginx/sbin/nginx

直接输入可执行文件的路径即可启动nginx,如果是在其当前目录下,可以直接输入文件名;

B、 停止命令

/usr/local/nginx/sbin/nginx -s stop

C、 检查配置文件

  # /usr/local/nginx/sbin/nginx -t -c /usr/local/nginx/conf/nginx.conf

D、 查看nginx版本及完整版本

/usr/local/nginx/sbin/nginx –v

nginx version: nginx/1.6.0

/usr/local/nginx/sbin/nginx –V

博主建议先查看先版本是否正确,然后再运行;

# ngixn的简单配置

Ubuntu下的配置文件中需要去掉#才不会报错,而在win下#表示注释;

          我们可以找到编译时指定的/usr/local/nginx/nginx.conf文件,开打修改;

          也可以删除掉此文件然后替换;不过替换和修改都相应的文件操作权限;

可以使用chmod  +u+777 文件名,来赋予当前用户操作权限;

如

chmod  +u+777 /usr/local/nginx/nginx.conf

则将当前用户赋予操作此文件的权限;

或者chmod +u+rwx 文件名;也可以

如果还是不能够使用外部编辑器编辑或者替换,可以直接使用root权限登录在命令行修改:

如linux通用的vi /usr/local/nginx/nginx.conf

表示用vi编辑器来编辑nginx.conf;

不过博主感觉vi太难用了,目前还不会用,推荐初学者使用Ubuntu的nano编辑器;

输入 nano /usr/local/nginx/nginx.conf可以编辑nginx.conf;

编辑完毕之后按住ctrl+X可以退出,之后按住y表示保存,然后点击enter保存文件名即可;

具体的建议读者查找资料,我感觉linux的编辑器上后难度太高了,不好用;

在修改完毕配置文件之后可以启动nginx,如果nginx正在运行可以使用nginx -s reload来重载配置文件;也可以先停止,再启动;nginx的配置不是几句话的事情,博主便不再多言,反正网上资料也挺多的;

顺便提下,Ubuntu的软件中心本来是自带nginx,但是版本比较低,可以通过sudo  apt-get install nginx安装到本地,但是不带sticky模块;

资料如下:

<http://wiki.ubuntu.com.cn/Nginx>

## nginx简单配置如下:

```
#Nginx所用用户和组，window下不指定
#user  niumd niumd;  
#工作的子进程数量（通常等于CPU数量或者2倍于CPU）
worker_processes  4; 
#错误日志存放路径
error_log  logs/error.log  info; 
#指定pid存放文件
pid        logs/nginx.pid;
events {
#使用网络IO模型linux建议epoll，FreeBSD建议采用kqueue，window下不指定。
#use epoll;  
#允许最大连接数
worker_connections  2048;
}

http {
include       mime.types;
default_type  application/octet-stream;
access_log  logs/access.log;
fastcgi_intercept_errors on;
```

```
client_header_timeout  3m;
client_body_timeout    3m;
send_timeout           3m;

client_header_buffer_size    1k;
large_client_header_buffers  4 4k;

sendfile        on;
tcp_nopush      on;
tcp_nodelay     on;

#keepalive_timeout  75 20;
#keepalive_timeout  0;

#include    gzip.conf;
#include    proxy.conf;
gzip               on;
gzip_min_length    1000;
gzip_types           text/plain text/css application/javascript application/x-javascript;

proxy_redirect          off;
proxy_set_header        Host $host;
proxy_set_header        X-Real-IP $remote_addr;
proxy_set_header        X-Forwarded-For   $proxy_add_x_forwarded_for;
client_max_body_size    10m;
client_body_buffer_size 128k;
proxy_connect_timeout   300;
proxy_send_timeout      300;
proxy_read_timeout      300;
proxy_buffer_size       4k;
proxy_buffers           4 32k;
proxy_busy_buffers_size 64k;
proxy_temp_file_write_size 64k;
```

```
upstream localhost{
ip_hash;
server localhost:8081 weight=3;
server localhost:8082 weight=3;
}

server {
listen       8080;  #监听8080端口
server_name  localhost;  
#将jsp的请求转移到tomcat里面
location ~ .*$ {
proxy_connect_timeout   3;
proxy_send_timeout      30;
proxy_read_timeout      30;
proxy_pass http://localhost;
proxy_set_header   Host    $host;
proxy_set_header   X-Real-IP   $remote_addr; 
proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for; 
}
}
}
```

## 更多nginx配置:

```
#定义Nginx运行的用户和用户组
user www www;

#nginx进程数，建议设置为等于CPU总核心数。
worker_processes 8;

#全局错误日志定义类型，[ debug | info | notice | warn | error | crit ]
error_log /var/log/nginx/error.log info;

#进程文件
pid /var/run/nginx.pid;

#一个nginx进程打开的最多文件描述符数目，理论值应该是最多打开文件数（系统的值ulimit -n）与nginx进程数相除，但是nginx分配请求并不均匀，所以建议与ulimit -n的值保持一致。
worker_rlimit_nofile 65535;

#工作模式与连接数上限
events
{
#参考事件模型，use [ kqueue | rtsig | epoll | /dev/poll | select | poll ]; epoll模型是Linux 2.6以上版本内核中的高性能网络I/O模型，如果跑在FreeBSD上面，就用kqueue模型。
use epoll;
#单个进程最大连接数（最大连接数=连接数*进程数）
worker_connections 65535;
}

#设定http服务器
http
{
include mime.types; #文件扩展名与文件类型映射表
default_type application/octet-stream; #默认文件类型
#charset utf-8; #默认编码
server_names_hash_bucket_size 128; #服务器名字的hash表大小
client_header_buffer_size 32k; #上传文件大小限制
large_client_header_buffers 4 64k; #设定请求缓
client_max_body_size 8m; #设定请求缓
sendfile on; #开启高效文件传输模式，sendfile指令指定nginx是否调用sendfile函数来输出文件，对于普通应用设为 on，如果用来进行下载等应用磁盘IO重负载应用，可设置为off，以平衡磁盘与网络I/O处理速度，降低系统的负载。注意：如果图片显示不正常把这个改成off。
autoindex on; #开启目录列表访问，合适下载服务器，默认关闭。
tcp_nopush on; #防止网络阻塞
tcp_nodelay on; #防止网络阻塞
keepalive_timeout 120; #长连接超时时间，单位是秒

#FastCGI相关参数是为了改善网站的性能：减少资源占用，提高访问速度。下面参数看字面意思都能理解。
fastcgi_connect_timeout 300;
fastcgi_send_timeout 300;
fastcgi_read_timeout 300;
fastcgi_buffer_size 64k;
fastcgi_buffers 4 64k;
fastcgi_busy_buffers_size 128k;
fastcgi_temp_file_write_size 128k;

#gzip模块设置
gzip on; #开启gzip压缩输出
gzip_min_length 1k; #最小压缩文件大小
gzip_buffers 4 16k; #压缩缓冲区
gzip_http_version 1.0; #压缩版本（默认1.1，前端如果是squid2.5请使用1.0）
gzip_comp_level 2; #压缩等级
gzip_types text/plain application/x-javascript text/css application/xml;
#压缩类型，默认就已经包含text/html，所以下面就不用再写了，写上去也不会有问题，但是会有一个warn。
gzip_vary on;
#limit_zone crawler $binary_remote_addr 10m; #开启限制IP连接数的时候需要使用

upstream blog.ha97.com {
#upstream的负载均衡，weight是权重，可以根据机器配置定义权重。weigth参数表示权值，权值越高被分配到的几率越大。
server 192.168.80.121:80 weight=3;
server 192.168.80.122:80 weight=2;
server 192.168.80.123:80 weight=3;
}

#虚拟主机的配置
server
{
#监听端口
listen 80;
#域名可以有多个，用空格隔开
server_name www.ha97.com ha97.com;
index index.html index.htm index.php;
root /data/www/ha97;
location ~ .*\.(php|php5)?$
{
fastcgi_pass 127.0.0.1:9000;
fastcgi_index index.php;
include fastcgi.conf;
}
#图片缓存时间设置
location ~ .*\.(gif|jpg|jpeg|png|bmp|swf)$
{
expires 10d;
}
#JS和CSS缓存时间设置
location ~ .*\.(js|css)?$
{
expires 1h;
}
#日志格式设定
log_format access '$remote_addr - $remote_user [$time_local] "$request" '
'$status $body_bytes_sent "$http_referer" '
'"$http_user_agent" $http_x_forwarded_for';
#定义本虚拟主机的访问日志
access_log /var/log/nginx/ha97access.log access;

#对 "/" 启用反向代理
location / {
proxy_pass http://127.0.0.1:88;
proxy_redirect off;
proxy_set_header X-Real-IP $remote_addr;
#后端的Web服务器可以通过X-Forwarded-For获取用户真实IP
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
#以下是一些反向代理的配置，可选。
proxy_set_header Host $host;
client_max_body_size 10m; #允许客户端请求的最大单文件字节数
client_body_buffer_size 128k; #缓冲区代理缓冲用户端请求的最大字节数，
proxy_connect_timeout 90; #nginx跟后端服务器连接超时时间(代理连接超时)
proxy_send_timeout 90; #后端服务器数据回传时间(代理发送超时)
proxy_read_timeout 90; #连接成功后，后端服务器响应时间(代理接收超时)
proxy_buffer_size 4k; #设置代理服务器（nginx）保存用户头信息的缓冲区大小
proxy_buffers 4 32k; #proxy_buffers缓冲区，网页平均在32k以下的设置
proxy_busy_buffers_size 64k; #高负荷下缓冲大小（proxy_buffers*2）
proxy_temp_file_write_size 64k;
#设定缓存文件夹大小，大于这个值，将从upstream服务器传
}

#设定查看Nginx状态的地址
location /NginxStatus {
stub_status on;
access_log on;
auth_basic "NginxStatus";
auth_basic_user_file conf/htpasswd;
#htpasswd文件的内容可以用apache提供的htpasswd工具来产生。
}

#本地动静分离反向代理配置
#所有jsp的页面均交由tomcat或resin处理
location ~ .(jsp|jspx|do)?$ {
proxy_set_header Host $host;
proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_pass http://127.0.0.1:8080;
}
#所有静态文件由nginx直接读取不经过tomcat或resin
location ~ .*.(htm|html|gif|jpg|jpeg|png|bmp|swf|ioc|rar|zip|txt|flv|mid|doc|ppt|pdf|xls|mp3|wma)$
{ expires 15d; }
location ~ .*.(js|css)?$
{ expires 1h; }
}
}
```

# 相关支持包和博文文档下载

[ http://download.csdn.net/detail/huitoukest/9424898](http://download.csdn.net/detail/huitoukest/9424898)

# 附上更多资料

[http://www.nginx.cn/](http://www.nginx.cn/)

[http://tengine.taobao.org/](http://tengine.taobao.org/)
