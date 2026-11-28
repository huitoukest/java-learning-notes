---
title: "Log4j的配置文件的基本示例"
date: "2014-10-23 12:05:24"
categories: ["常用配置文件示例"]
tags: ["log4j", "配置文件", "示例"]
---

其中#表示行注释,这个配置文件拿过去就能够用,常用的也都具有了:

将文件保存为log4j.properties放到classpath下面,导入log4j的相关包之后就能够使用了

```
#
# Log4J Settings for log4j 1.2.x (via jakarta-commons-logging)
#
# The five logging levels used by Log are (in order):
#
#   1. DEBUG (the least serious)
#   2. INFO
#   3. WARN
#   4. ERROR
#   5. FATAL (the most serious)
```

```
# Set root logger level to WARN and append to stdout
#log4j.rootLogger=INFO, stdout
log4j.rootLogger=INFO,stdout
log4j.appender.stdout=org.apache.log4j.ConsoleAppender
#log4j.appender.stdout.Target=System.out
log4j.appender.stdout.layout=org.apache.log4j.PatternLayout

# Pattern to output the caller's file name and line number.
log4j.appender.stdout.layout.ConversionPattern=%d{yyyy-MM-dd HH:mm:ss}  %c{1} - %m%n

# Print only messages of level ERROR or above in the package noModule.
#log4j.logger.noModule=FATAL

#log4j.logger.com.opensymphony.xwork2=DEBUG
#log4j.logger.org.apache.struts2=DEBUG
```

```
#log4j.debug=true
#log4j.rootLogger=INFO,CONSOLE,STDOUT

#-----CONSOLE-----
#log4j.appender.CONSOLE=org.apache.log4j.ConsoleAppender
#log4j.appender.CONSOLE.layout=org.apache.log4j.PatternLayout
#log4j.appender.CONSOLE.layout.ConversionPattern=%d{yyyy-MM-dd HH:mm:ss}  %c{1} - %m%n

#log4j.appender.CONSOLE=org.apache.log4j.ConsoleAppender
#log4j.appender.CONSOLE.layout=org.apache.log4j.PatternLayout

#-----SQL LOG-----
#log4j.logger.java.sql.Connection=DEBUG
#log4j.logger.java.sql.Statement=DEBUG
#log4j.logger.java.sql.PreparedStatement=DEBUG

#Hibernate
log4j.logger.org.hibernate.tool.hbm2ddl=trace
#log4j.logger.org.hibernate.testing.cache=debug

# SQL Logging - HHH-6833
#log4j.logger.org.hibernate.SQL=debug
#log4j.logger.org.hibernate.hql.internal.ast=debug
#log4j.logger.org.hibernate.sql.ordering.antlr=debug
```
