---
title: "Ubuntu 14和 Win7 下NFS服务器与客户端配置(Ubuntu 14.04.02)"
date: "2016-02-22 10:46:52"
categories: ["Linux/windows"]
tags: ["linux", "ubuntu", "nfs"]
---

# 1.Ubuntu14下nfs服务器配置

## 1.安装相关支持的软件包

$ sudo apt-get install nfs-kernel-server  
$ sudo apt-get install nfs-common

$ sudo apt-get install rpcbind

这里需要注意的是:portmap被rpcbi替换了,当然如果别的linux版本可能还是portmap;

## 2.配置/etc/exports

$ sudo nano /etc/exports  
文本末添加  
/home/work *(rw,sync,no_root_squash)  
注意:这里的/home/work指的是你要共享的目录,后面的*(rw,sync,no_root_squash)中的*表示可以方位的ip,括号内是访问者拥有的权限;

例如:/home/share 192.168.2.*(rw,sync,no_root_squash)

之后保存退出;可以用vim或者vi来编辑,都一样;之后最好改变此文件的权限让之可以读取;

可以使用chmod 命令;

## 3.启动服务

$ cd /etc/init.d/

$ sudo rpcbind start

如果服务已经启动,可以使用rpcbind restart重启

$ sudo nfs-kernel-server start

因为下载的是nfs-kernel-server包,所以用的nfs-kernel-server restart,有的版本下载的nfs包,则使用nfs start命令;

## 4.查看nfs服务

$ sudo showmount  -e

或者 $ sudo showmount –a

root@ubuntu:/etc/init.d# showmount  -a

All mount points on ubuntu:

192.168.1.122:/home/share

## 5.加载nfs文件服务到客户端

mount -t nfs 192.168.1.130:/home/share /nfsmnt -o nolock

其中: 192.168.1.130:/home/share /nfsmnt是你nfs服务器端ip地址与目录

/nfsmnt是加载客户端,即本地的位置;

-o nolock是可选项;

# 2.win7(旗舰版和企业版)下nfs客户端搭建

进入:控制面板->程序->打开或关闭windows功能;找到nfs相关选项,打开;

之后进入cmd:

输入showmount –e nfs服务器地址;

可以查看相关nfs共享:

之后用mount命令加载服务到制定盘符,以下示例中为加载到本地N盘中;

其中N盘式虚拟的一个盘符,对应nfs服务器位置;

C:\Windows\System32>showmount -e 192.168.1.130

导出列表在 192.168.1.130:

/home/share                        192.168.1.*

C:\Windows\System32>mount 192.168.1.130:/home/share N:

N: 现已成功连接到 192.168.1.130:/home/share

命令已成功完成。
