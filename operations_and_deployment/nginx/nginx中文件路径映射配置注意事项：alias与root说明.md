---
title: "nginx中文件路径映射配置注意事项：alias与root说明"
date: "2018-02-11 18:05:58"
categories: ["java EE SSHM"]
tags: ["nginx", "反向代理"]
---

# 注意

在配置文件映射的时候，如果使用了正则表达式，那么可能会出现无法访问文件，nginx可能会将所有的

文件都映射成为文件夹，导致文件映射失败的情况出现；

**所以，进行文件映射的时候，最好不要使用正则表达式。**

# root和alias区别

root是当前代理项目的url的**相对路径** ；

location /manage/tmp/ {  

root E:/home/uploadFile/tmp/;

}

实际访问路径：/manage/tmp/E:/home/uploadFile/tmp/；

alias是**绝对路径** ；

location /manage/tmp/ {  

alias E:/home/uploadFile/tmp/;

}

实际访问路径：E:/home/uploadFile/tmp/;

# 配置示例

```
#user  nobody;
worker_processes  1;

events {
worker_connections  100;
}

http {
include       mime.types;
default_type  application/octet-stream;

sendfile        on;
#keepalive_timeout  0;
keepalive_timeout  65;
server {
listen       8080;
server_name  localhost 127.0.0.1 192.168.50.11;

#charset koi8-r;

#access_log  logs/host.access.log  main;
		#一些静态资源可以采用如下配置:
		#~* 开头表示不区分大小写的正则匹配，文件映射别用正则表达式容易出现问题
		location ~* ^/(WEB-INF)/ { #这个很重要，不然用户就可以访问了 
deny all;
}

		#设定访问静态文件直接读取不经过tomcat 
		location /manage/tmp/ {
			alias   E:/home/uploadFile/tmp/;
			if ($request_filename ~* ^.*?\.(txt|doc|pdf|rar|gz|zip|docx|exe|xlsx|ppt|pptx)$){
				add_header Content-Disposition: 'attachment;';
}        
			autoindex     on;
			autoindex_exact_size   off;
			autoindex_localtime    on;
expires      2s;
		}

		location /manage/upload/ {
			alias   E:/home/uploadFile/;
			if ($request_filename ~* ^.*?\.(txt|doc|pdf|rar|gz|zip|docx|exe|xlsx|ppt|pptx)$){
				add_header Content-Disposition: 'attachment;';
}
			autoindex     on;
			autoindex_exact_size   off;
			autoindex_localtime    on;
expires      2s;
			proxy_set_header   Host    $host;
			proxy_set_header   X-Real-IP   $remote_addr;
			proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
		}

		location ~* .*/manage/((?!upload/|tmp/).)*$ {
			proxy_pass http://localhost:8090;
		}

error_page   500 502 503 504  /50x.html; 
location = /50x.html {
root   html; 
}
}

}
```
