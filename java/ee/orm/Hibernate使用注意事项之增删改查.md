---
title: "Hibernate使用注意事项之增删改查"
date: "2014-09-23 13:52:01"
categories: ["java EE SSHM"]
tags: ["数据库", "乱码", "jdbc", "hibernate"]
---

**一:嵌套查询示例:**

    select pt from PubTemp pt where pt.isshare = 1  and  (pt.tplName like '%测试%' or pt.author like '%测试%')

或者使用in查询:

    String searchHql="select pt from PubTemp pt where pt.pubTempGroup.groupId="+groupId+" and pt.isshare = 1"
                        + and pubtemp.tplId in (select pubtemp2.tplId from PubTemp pubtemp2 "
    		    +"where pubtemp2.tplName like ? or pubtemp2.author like ?)";

**二:中文查询无效果** ,但是java程序中和数据库均无乱码,或字符编码不同的问题

mysql数据库:jdbc连接如下:url="jdbc:mysql://127.0.0.1:3306/xhslapp?useUnicode=true&characterEncoding=UTF-8"

              一定要在连接串上指明:

    ?useUnicode=true&characterEncoding=UTF-8
