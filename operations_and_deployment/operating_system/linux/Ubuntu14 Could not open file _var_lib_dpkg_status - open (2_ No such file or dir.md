---
title: "Ubuntu14 Could not open file /var/lib/dpkg/status - open (2: No such file or directory)"
date: "2016-02-24 11:30:24"
categories: ["Linux/windows"]
tags: ["ubuntu error"]
---

如果不小心删除了/var/lib/dpkg下的所有文件,可以尝试如下的解决方案:

1.如果连dpkg目录都删除了,首先建立目录 mkdir /var/lib/dpkg

2.将机器中自带的dpkg的status备份文件拷贝到/var/lib/dpkg/status

sudo cp /var/backups/dpkg.status.0 /var/lib/dpkg/status

3.在/var/lib/dpkg目录下建立如下文件或文件夹

文件:available status-old  available-old  lock  status  
文件夹:alternatives  info    parts updates triggers

文件建立命令:touch XXXX

4.sudo apt-get update
