---
title: "windows下通过软连接创建/模拟 '伪' linux文件系统"
date: "2018-04-11 11:41:54"
categories: ["Linux/windows"]
tags: ["windows", "软连接", "linux", "文件系统"]
---

# 前言
基于一般JEE开发在window下，而部署在linux下的情况。如果windows下的文件系统结构和linux下类似，那么能带来不少的方便，部署的时候也不用修改相关的参数。

注意：
- 文件定位
已知在java中，对于以/开头的文件将会默认定位到当前盘符的更目录路径。
例如：new File("/home")，如果此程序位置在windows下的E盘，那么其绝对路径就是E:/home目录。
此规则使用与tomcat等jee容器和普通jar程序。

 - 文件分隔符
在windows下，***默认 / 和 \ 都是文件分隔符***。所以直接使用linux下的文件分割符号/可以兼容两种环境。

# 思路
- 选取一个盘符建立相关文件夹。
- 在其余盘符建立此盘符的文件链接。
那么在此种情况下，无论软件运行于哪一个盘符。
最终获取的路径均是文件链接后的路径。
而软链接后的路径又有系统能够识别是否是链接，
对于程序而言都是“真实的文件路径”

示例：在E盘创建home、var、tmp目录,并建立相关链接。
这里将根目录的tmp目录同时链接到/home/tmp下
在cmd命令下：
```
C:\WINDOWS\system32>E:
E:\>mkdir home

mklink /j "C:\home" "E:\home"
mklink /j "D:\home" "E:\home"
mklink /j "F:\home" "E:\home"
mklink /j "G:\home" "E:\home"

mkdir var

mklink /j "C:\var" "E:\var"
mklink /j "D:\var" "E:\var"
mklink /j "F:\var" "E:\var"
mklink /j "G:\var" "E:\var"

cd home
mkdir tmp

mklink /j "E:\tmp" "E:\home\tmp"
mklink /j "C:\tmp" "E:\tmp"
mklink /j "D:\tmp" "E:\tmp"
mklink /j "F:\tmp" "E:\tmp"
mklink /j "G:\tmp" "E:\tmp"
```  

注意：在powershell下可能命令不兼容。此命令需要以管理员模式运行。
此命令运行于win10，win7下成功，其余windows可能会有兼容性问题，但是解决的思路不变。

# mklink

```
E:\home>mklink
创建符号链接。

MKLINK [[/D] | [/H] | [/J]] Link Target

        /D      创建目录符号链接。默认为文件
                符号链接。
        /H      创建硬链接而非符号链接。
        /J      创建目录联接。
        Link    指定新的符号链接名称。
        Target  指定新链接引用的路径
                (相对或绝对)。
```
