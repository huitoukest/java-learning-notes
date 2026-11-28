---
title: "Cygwin中如何像在Ubuntu中一样安装软件"
date: "2016-02-24 14:00:13"
categories: ["Linux/windows"]
tags: ["apt-cyg", "cygwin"]
---

1.通过cygwin客户端安装必须的软件支持包wget tar gawk bzip2

在windows的命令行cmd下:

    cd C:\cygwin64
    setup-x86_64 -q -P wget,tar,qawk,bzip2,subversion,vim

注意:此安装客户端位setupX86_64.exe,你需要到cygwin官网自己下载exe文件,安装,然后拷贝到相关安装后的目录;

2.安装apt-cyg

    wget http://apt-cyg.googlecode.com/svn/trunk/apt-cyg -P /bin chmod.exe +x /bin/apt-cyg

此命令表示将http://apt-cyg.googlecode.com/svn/trunk/apt-cyg中的apt-cyg拷贝到本地/bin目录下;然后赋予可执行权限;

注意:googlecode可能被河蟹了,自己翻墙可以搞定,笔者会在文末附上下载链接,自己手动拷贝后,赋予可执行权限也行

或者使用以下命令:

    # svn --force export http://apt-cyg.googlecode.com/svn/trunk/ /bin/
    # chmod +x /bin/apt-cyg

3.替换apt-cyg镜像源

    apt-cyg -m http://mirrors.163.com/cygwin/

4.更新镜像源

    apt-cyg update

5.安装其他软件

这里的apt-cyg基本和Ubuntu中的apt-get的使用方法是一致的;

比如安装mysql server的命令如下:

    apt-cyg install mysql-server

apt-cyg下载链接:

htt去p://p掉an.bai我du.co们m/s/1nudcgTb  
