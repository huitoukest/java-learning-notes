---
title: "使用Eclipse插件连接配置Mapreduce说明与教程(hadoop-eclipse-plugin 2.6)"
date: "2016-03-18 13:41:38"
categories: ["hadoop相关"]
tags: ["Mapreduce", "hadoop", "Eclipse插件"]
---

1.前言

网上的很多教程都是基于hadoop单机或者是伪分布式的,在HA集群的hadoop是有些不一样的;

所以写个hadoop-eclipse-plugin连接HA hadoop 集群的说明;

2.查看hadoop配置文件并配置DFS Master

查看hadoop/etc/hadoop下的配置文件;

hdfs-site.xml  \----->找到dfs.namenode.rpc-address.hadoop-test.nn1;

```
<property>
<name>dfs.namenode.rpc-address.hadoop-test.nn1</name>
<value>hadoop0:9000</value>
<description>
RPC address for nomenode1 of hadoop-test
</description>
</property>
```

这里的hadoop-test是你的nameservice的名称;或者说是hadoop集群的此hdfs的路径前缀;

和core-site.xml中的fs.defaultFs相对应:

```
<property>
<name>fs.defaultFS</name>
<value>hdfs://hadoop-test</value>
<!-- 指向namenode：host：port -->
</property>
```

在HA hadoop中,fs.defaultFs指的实际上是一个虚拟的hdfs路径;不用加端口号;

这里的hadoop0是hostname; 我们需要的是找到此hostname和端口号9000;

利用这个hostname和端口号填写到hadoop-Eclipse插件的DFS Master中;对应的host和post;

![]()  

**注意:** 此插件默认端口号是9000;如果hdfs-site.xml中的相应端口不是这个,最好改为9000,而不是用别的端口号;

好像使用别的端口号会发生错误;

3.查看hadoop配置文件并配置Map/Reduce(v2) Master  

![]()  

找到yarn-site.xml--->yarn.resourcemanager.scheduler.address

找到其对应的host与端口号;

```
<property>
<description>The address of the scheduler interface.</description>
<name>yarn.resourcemanager.scheduler.address</name>
<value>${yarn.resourcemanager.hostname}:8030</value>
</property>
```

${yarn.resourcemanager.hostname}  
这里是host,其值即是yarn.resourcemanager.hostname属性的值,内容是host;

如同127.0.0.1

之后将对应的host与post填入Map/Reduce(v2) Master;

然后保存,转到Project Explorer,点击你新建的名称,这里是180;然后点击F5刷新下,就出出现hdfs的目录界面;

![]()  

4.注意

如果发生java.io.IOException: Could not locate executable null\bin\winutils.exe in the Hadoop binaries.

    在java代码,在连接hadoop或者执行MapReduce之前,执行

System._setProperty_("hadoop.home.dir", "D:/hadoop-2.6.4");  

D:/hadoop-2.6.4为hadoop解压目录;  

    ,同时将相关的winutils.exe文件复制到hadoop的bin目录下面即可以;
