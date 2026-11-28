---
title: "log4j配置说明和示例"
date: "2017-11-25 21:53:58"
categories: ["常用配置文件示例"]
tags: ["log4j", "日志", "配置", "说明"]
---

# 简介
Log4J的配置文件(Configuration File)就是用来设置记录器的级别、存放器和
布局的，它可接key=value格式的设置或xml格式的设置信息。
Log4j有三个主要的组件：Loggers(记录器)，Appenders (输出源)和Layouts(布局)。
此外,还有一些通用的概念如 level和 继承,additivity等.

类似的日志框架还有logback和log4j2,其中log4j2的性能最好,logback性能最差.
但是log4j2在缓存不足时可能存在日志丢失的问题.

## 环境配置
一般使用log4j需要与logging配合使用：
commons-logging-1.0.4.jar
log4j-1.2.15.jar
配置文件一般命名log4j.properties

# level
level是日志输出的级别,共有5级：
日志只会记录数值小于等于当前级别的日志.
- FATAL        0  
- ERROR      3  
- WARN        4  
- INFO          6  
- DEBUG      7

rootLogger的默认日志级别是Level.DEBUG

# Logger(记录器)
```properties
log4j.rootLogger  =  [ level ]  ,  appenderName1 ,  appenderName2 ,  …
log4j.logger.aty.log.service.A=DEBUG, testA
```
***logger指定日志的输出级别和对应的append(可以有多个)***.
log4j.logger.aty.log.service.A 其实对应的log是class aty.log.service.A中的
private static Logger logger = Logger.getLogger(A.class);
其中log4j.rootLogger是根logger,其作用可以查看[配置继承](#配置继承),
testA这里是append的名称

log4j默认是使用类名或者包名来查找logger的。
***log4j允许我们自己定义logger的名称。***
```java
public class A {  
    private static Logger logger = Logger.getLogger("atyAlogger");    
    public void run() {  
        logger.error("log in A.java");  
    }  
}  
```
配置文件中的logger必须和代码中的logger同名才能生效.
```properties
#use atyAlogger as appender name.  
log4j.logger.atyAlogger=DEBUG, testA  
```

# appender
***appender用来指定logger的输出目的地***(位置,文件名和输出的日志级别方式等.)
通过log4j.appender.XX可以定义自定义appender,名称是XX.
```properties
log4j.appender.testA=org.apache.log4j.FileAppender  #获取自定义的logger名称testA,配置输出方式
log4j.appender.testA.Threshold=warn    #配置单独的输出级别
log4j.appender.testA.ImmediateFlush=true    
log4j.appender.testA.Append=true    
log4j.appender.testA.File=c:/a.log
log4j.appender.testA.layout=org.apache.log4j.PatternLayout  
 #配置输出的名称
log4j.appender.testA.layout.ConversionPattern=[%d{yyyy-MM-dd HH:mm:ss,SSS}]-[%t]-[%X{ip}]-[%l]-[%p] %m%n
```

## Appendr实现
系统自带集中Appendr的实现,即自带有日志输出的几种方式,我们需要为对应的logger选择输出实现,包括rootLogger.
org.apache.log4j.ConsoleAppender（控制台），
org.apache.log4j.FileAppender（文件），
org.apache.log4j.DailyRollingFileAppender（指定周期(天/月/年等)产生一个日志文件），
org.apache.log4j.RollingFileAppender（文件大小到达指定尺寸的时候产生一个新的文件），
org.apache.log4j.WriterAppender（将日志信息以流格式发送到任意指定的地方）

## Appender配置
不同的Appender有不同的子项可以配置,具体如下:

- ConsoleAppender
Threshold=WARN：指定日志信息的最低输出级别，默认为DEBUG。
ImmediateFlush=true：表示所有消息都会被立即输出，设为false则不输出，默认值是true。
Target=System.err：默认值是System.out。

- FileAppender选项
Threshold=WARN：指定日志信息的最低输出级别，默认为DEBUG。
ImmediateFlush=true：表示所有消息都会被立即输出，设为false则不输出，默认值是true。
Append=false：true表示消息增加到指定文件中，false则将消息覆盖指定的文件内容，默认值是true。
File=D:/logs/logging.log4j：指定消息输出到logging.log4j文件中。

- DailyRollingFileAppender选项
Threshold=WARN：指定日志信息的最低输出级别，默认为DEBUG。
ImmediateFlush=true：表示所有消息都会被立即输出，设为false则不输出，默认值是true。
Append=false：true表示消息增加到指定文件中，false则将消息覆盖指定的文件内容，默认值是true。
File=D:/logs/logging.log4j：指定当前消息输出到logging.log4j文件中。
DatePattern='.'yyyy-MM：每月滚动一次日志文件，即每月产生一个新的日志文件。
当前月的日志文件名为logging.log4j，前一个月的日志文件名为logging.log4j.yyyy-MM。
另外，也可以指定按周、天、时、分等来滚动日志文件，对应的格式如下：
1)'.'yyyy-MM：每月
2)'.'yyyy-ww：每周
3)'.'yyyy-MM-dd：每天
4)'.'yyyy-MM-dd-a：每天两次
5)'.'yyyy-MM-dd-HH：每小时
6)'.'yyyy-MM-dd-HH-mm：每分钟
默认log4j会先将日志放到log4j.appender.R.File的文件中,1分钟左右将
内容刷新到DatePattern指定的文件中.

- RollingFileAppender选项
Threshold=WARN：指定日志信息的最低输出级别，默认为DEBUG。
ImmediateFlush=true：表示所有消息都会被立即输出，设为false则不输出，默认值是true。
Append=false：true表示消息增加到指定文件中，false则将消息覆盖指定的文件内容，默认值是true。
File=D:/logs/logging.log4j：指定消息输出到logging.log4j文件中。
MaxFileSize=100KB：后缀可以是KB, MB 或者GB。
在日志文件到达该大小时，将会自动滚动，即将原来的内容移到logging.log4j.1文件中。
MaxBackupIndex=2：指定可以产生的滚动文件的最大数，
例如，设为2则可以产生logging.log4j.1，logging.log4j.2两个滚动文件和一个logging.log4j文件。

# additivity
配置是否logger(输出)内容,是否输出到当前日志到上一级别的logger中
```properties
log4j.additivity.aty.log.service.A= false  
```
可以避免日志打印到rootLogger中。如果这里设置成true，那么A.java中的日志既会输出到根Logger中，也会输出到testA中。

# layout（Layout）
layout中是配置的日志信息的格式(布局)信息
```properties
 #log4j.appender.appenderName.layout=className
log4j.appender.appenderName.layout  =  fully.qualified.name.of.layout.class 
log4j.appender.appenderName.layout.option1  =  value1 
… 
log4j.appender.appenderName.layout.optionN  =  valueN 
```
## 系统自带的输出格式如下
- org.apache.log4j.HTMLLayout
以HTML表格形式布局
特有选项:
LocationInfo=true：输出java文件名称和行号，默认值是false。
Title=My Logging： 默认值是Log4J Log Messages。
- org.apache.log4j.PatternLayout
可以灵活地指定布局模式
特有选项:
ConversionPattern=%m%n：设定以怎样的格式显示消息。
- org.apache.log4j.SimpleLayout
包含日志信息的级别和信息字符串
- org.apache.log4j.TTCCLayout
包含日志产生的时间、线程、类别等等信息

## 参数格式化
- %M  输出产生日志信息的方法名。
- %m  输出代码中指定的具体日志信息
- %p   输出优先级，即DEBUG，INFO，WARN，ERROR，FATAL
- %r    输出自应用启动到输出该log信息耗费的毫秒数
- %c   输出所属的类目category，通常就是所在类的全名
- %t    输出产生该日志事件的线程名
- %n   输出一个回车换行符，Windows平台为“\r\n”，Unix平台为“\n”
- %d   输出日志时间点的日期或时间，默认格式为ISO8601，也可以在其后指定格式，比如：%d{yyy MMM dd HH:mm:ss , SSS}
输出类似：2002年10月18日  22 ： 10 ： 28 ， 921  
- %l   输出日志事件的发生位置，包括类目名、发生的线程，以及在代码中的行数。举例：Testlog4.main(TestLog4.java: 10 )
- %L  输出代码中的行号。
- %F  输出日志消息产生时所在的文件名称。
- %x  输出和当前线程相关联的NDC(嵌套诊断环境)，尤其用到像java servlets这样的多客户多线程的应用中
- %%  输出一个"%"字符。

可以在%与模式字符之间加上修饰符来控制其最小宽度、最大宽度、和文本的对齐方式。如：
1)%20c：指定输出category的名称，最小的宽度是20，如果category的名称小于20的话，默认的情况下右对齐。
2)%-20c:指定输出category的名称，最小的宽度是20，如果category的名称小于20的话，”-”号指定左对齐。
3)%.30c:指定输出category的名称，最大的宽度是30，如果category的名称大于30的话，就会将左边多出的字符截掉，但小于30的话也不会有空格。
4)%20.30c:如果category的名称小于20就补空格，并且右对齐，如果其名称长于30字符，就从左边交远销出的字符截掉。

# 配置继承
log4j日志框架logger是存在继承关系的，我们一般都会在log4j.properties文件中定义log4j.rootLogger。
其他所有logger都继承自这个rootLooger.如果没有对logger配置单独的输出,那么就会使用默认的rootLogger
的输出.

log4j日志框架logger是存在继承关系的，我们一般都会在log4j.properties文件中定义log4j.rootLogger。其他所有logger都继承自这个rootLooger
如我们上面的类aty.log.service.A中使用了logger来写日志。
那么log4j会先查找名称是"aty.log.service.A"的logger，如果没有找到，
向上查找名称是"aty.log.service"的logger，如果还没有找到那么继续向上查找，
查找的最顶层就是rootLogger。
这就是log4j中logger的继承关系。
rootLogger一定要在配置，其他特定类或者特定包的logger可以不用配置。
知道了这个继承特性之后，如果我们要aty.log.dao包下所有的类都打印到同一个日志文件，那么可以进行如下配置。

```properties
log4j.logger.aty.log.dao=DEBUG, daoAppender  
log4j.appender.daoAppender=org.apache.log4j.FileAppender  
log4j.appender.daoAppender.Threshold=warn    
log4j.appender.daoAppender.ImmediateFlush=true    
log4j.appender.daoAppender.Append=true    
log4j.appender.daoAppender.File=c:/dao.log  
log4j.appender.daoAppender.layout=org.apache.log4j.PatternLayout  
log4j.appender.daoAppender.layout.ConversionPattern=[%d{yyyy-MM-dd HH:mm:ss,SSS}]-[%t]-[%X{ip}]-[%l]-[%p] %m%n  
log4j.additivity.aty.log.dao= false  
```
这样aty.log.dao包先的类默认会输出到daoAppender 中.

# 代码中配置
在代码中初始化Logger:
1) 在程序中调用BasicConfigurator.configure()方法：给根记录器增加一个ConsoleAppender，输出格
式通过PatternLayout设为"%-4r [%t] %-5p %c %x - %m%n".
2) 配置放在文件里，通过命令行参数传递文件名字，通过PropertyConfigurator.configure(args[x])解析并配置；
3) 配置放在文件里，通过环境变量传递文件名等信息，利用log4j默认的初始化过程解析并配置；
4) 配置放在文件里，通过应用服务器配置传递文件名等信息，利用一个特殊的servlet来完成配置。
```java
public  class  TestLog4j  {
    public  static  void  main(String[] args)  {
        PropertyConfigurator.configure( " D:/Code/conf/log4j.properties " );
        Logger logger  =  Logger.getLogger(TestLog4j. class );
        logger.debug( " debug " );
        logger.error( " error " );
    } 
}
```

# properties配置方式
示例配置文件如下:
此Log4j配置文件实现了输出到控制台、文件、回滚文件、发送日志邮件、输出到数据库日志表、自定义标签等全套功能。
```properties
log4j.rootLogger=DEBUG,console,dailyFile,im
log4j.additivity.org.apache=true
# 控制台(console)
log4j.appender.console=org.apache.log4j.ConsoleAppender
log4j.appender.console.Threshold=DEBUG
log4j.appender.console.ImmediateFlush=true
log4j.appender.console.Target=System.err
log4j.appender.console.layout=org.apache.log4j.PatternLayout
log4j.appender.console.layout.ConversionPattern=%d %-5p [%c] - %m - [%l]%n

# 日志文件(logFile)
log4j.appender.logFile=org.apache.log4j.FileAppender
log4j.appender.logFile.Threshold=DEBUG
log4j.appender.logFile.ImmediateFlush=true
log4j.appender.logFile.Append=true
log4j.appender.logFile.File=D:/logs/log.log4j
log4j.appender.logFile.layout=org.apache.log4j.PatternLayout
log4j.appender.logFile.layout.ConversionPattern=[%-5p] %d(%r) --> [%t] %l: %m %x %n

# 回滚文件(rollingFile)
log4j.appender.rollingFile=org.apache.log4j.RollingFileAppender
log4j.appender.rollingFile.Threshold=DEBUG
log4j.appender.rollingFile.ImmediateFlush=true
log4j.appender.rollingFile.Append=true
log4j.appender.rollingFile.File=D:/logs/log.log4j
log4j.appender.rollingFile.MaxFileSize=200KB
log4j.appender.rollingFile.MaxBackupIndex=50
log4j.appender.rollingFile.layout=org.apache.log4j.PatternLayout
log4j.appender.rollingFile.layout.ConversionPattern=[%-5p] %d(%r) --> [%t] %l: %m %x %n

# 定期回滚日志文件(dailyFile)
log4j.appender.dailyFile=org.apache.log4j.DailyRollingFileAppender
log4j.appender.dailyFile.Threshold=DEBUG
log4j.appender.dailyFile.ImmediateFlush=true
log4j.appender.dailyFile.Append=true
log4j.appender.dailyFile.File=D:/logs/log.log4j
log4j.appender.dailyFile.DatePattern='.'yyyy-MM-dd
log4j.appender.dailyFile.layout=org.apache.log4j.PatternLayout
log4j.appender.dailyFile.layout.ConversionPattern=[%-5p] %d(%r) --> [%t] %l: %m %x %n

# 应用于socket
log4j.appender.socket=org.apache.log4j.RollingFileAppender
log4j.appender.socket.RemoteHost=localhost
log4j.appender.socket.Port=5001
log4j.appender.socket.LocationInfo=true
# Set up for Log Factor 5
log4j.appender.socket.layout=org.apache.log4j.PatternLayout
log4j.appender.socket.layout.ConversionPattern=[%-5p] %d(%r) --> [%t] %l: %m %x %n

# Log Factor 5 Appender
log4j.appender.LF5_APPENDER=org.apache.log4j.lf5.LF5Appender
log4j.appender.LF5_APPENDER.MaxNumberOfRecords=2000

# 发送日志到指定邮件
# 这里mail使用自带的logger  org.apache.log4j.net.SMTPAppender
log4j.appender.mail=org.apache.log4j.net.SMTPAppender
log4j.appender.mail.Threshold=FATAL
log4j.appender.mail.BufferSize=10
log4j.appender.mail.From = xxx@mail.com
log4j.appender.mail.SMTPHost=mail.com
log4j.appender.mail.Subject=Log4J Message
log4j.appender.mail.To= xxx@mail.com
log4j.appender.mail.layout=org.apache.log4j.PatternLayout
log4j.appender.mail.layout.ConversionPattern=[%-5p] %d(%r) --> [%t] %l: %m %x %n

# 应用于数据库
# 自带的数据库logger  org.apache.log4j.jdbc.JDBCAppender
log4j.appender.database=org.apache.log4j.jdbc.JDBCAppender
log4j.appender.database.URL=jdbc:mysql://localhost:3306/test
log4j.appender.database.driver=com.mysql.jdbc.Driver
log4j.appender.database.user=root
log4j.appender.database.password=
log4j.appender.database.sql=INSERT INTO LOG4J (Message) VALUES('=[%-5p] %d(%r) --> [%t] %l: %m %x %n')
log4j.appender.database.layout=org.apache.log4j.PatternLayout
log4j.appender.database.layout.ConversionPattern=[%-5p] %d(%r) --> [%t] %l: %m %x %n

# 自定义Appender
# 代码中获取的logger net.cybercorlin.util.logger.appender.IMAppender,使用默认输出级别,rootLogger的级别
log4j.appender.im = net.cybercorlin.util.logger.appender.IMAppender
log4j.appender.im.host = mail.cybercorlin.net
log4j.appender.im.username = username
log4j.appender.im.password = password
log4j.appender.im.recipient = corlin@cybercorlin.net
log4j.appender.im.layout=org.apache.log4j.PatternLayout
log4j.appender.im.layout.ConversionPattern=[%-5p] %d(%r) --> [%t] %l: %m %x %n
```

# xml方式配置

## 结构示意
列出了常用的结构.
```properties
xml declaration and DTD  
 |  
log4j:configuration  
 |  
 +-- appender (name, class)  
 |     |  
 |     +-- param (name, value)  
 |     +-- layout (class)  
 |           |  
 |           +-- param (name, value)  
 +-- logger (name, additivity)  
 |     |  
 |     +-- level (class, value)  
 |     |     |  
 |     |     +-- param (name, value)  
 |     +-- appender-ref (ref)  
 +-- root  
       |  
       +-- param (name, class)  
       +-- level  
       |     |  
       |     +-- param (name, value)  
       +-- appender-ref (ref)   
```

## XML结构/元素简介

### xml declaration and DTD

xml配置文件的头部包括两个部分：xml声明和DTD声明。头部的格式如下：
```properties
<?xml version="1.0" encoding="UTF-8" ?>
<!DOCTYPE log4j:configuration SYSTEM "log4j.dtd">
```

### log4j:configuration (root element)
xmlns:log4j [#FIXED attribute] : 定义log4j的名字空间，取定值"http://jakarta.apache.org/log4j/"
appender [* child] : 一个appender子元素定义一个日志输出目的地
logger [* child] : 一个logger子元素定义一个日志写出器
root [? child] : root子元素定义了root logger

### appender
appender元素定义一个日志输出目的地。
name [#REQUIRED attribute] : 定义appender的名字，以便被后文引用
class [#REQUIRED attribute] : 定义appender对象所属的类的全名
param [* child] : 创建appender对象时传递给类构造方法的参数
layout [? child] : 该appender使用的layout对象

### layout
layout元素定义与某一个appender相联系的日志格式化器。
class [#REQUIRED attribute] : 定义layout对象所属的类的全名
param [* child] : 创建layout对象时传递给类构造方法的参数

### logger
logger元素定义一个日志输出器。
name [#REQUIRED attribute] : 定义logger的名字，以便被后文引用
additivity [#ENUM attribute] : 取值为"true"（默认）或者"false"，是否继承父logger的属性
level [? child] : 定义该logger的日志级别
appender-ref [* child] : 定义该logger的输出目的地

### root
root元素定义根日志输出器root logger。
param [* child] : 创建root logger对象时传递给类构造方法的参数
level [? child] : 定义root logger的日志级别
appender-ref [* child] : 定义root logger的输出目的地

### level
level元素定义logger对象的日志级别。
class [#IMPLIED attribute] : 定义level对象所属的类，默认情况下是"org.apache.log4j.Level类
value [#REQUIRED attribute] : 为level对象赋值。可能的取值从小到大依次为"all"、"debug"、"info"、"warn"、"error"、"fatal"和"off"。当值为"off"时表示没有任何日志信息被输出
param [* child] : 创建level对象时传递给类构造方法的参数

### appender-ref
appender-ref元素引用一个appender元素的名字，为logger对象增加一个appender。
ref [#REQUIRED attribute] : 一个appender元素的名字的引用
appender-ref元素没有子元素

### param
param元素在创建对象时为类的构造方法提供参数。
它可以成为appender、layout、filter、errorHandler、level、categoryFactory和root等元素的子元素。
name and value [#REQUIRED attributes] : 提供参数的一组名值对
param元素没有子元素

### filter
包括选择过滤器和设置过滤条件，可选择的过滤器包括：LogLevelMatchFilter、LogLevelRangeFilter、和StringMatchFilter

- LogLevelMatchFilter
过滤条件包括LogLevelToMatch和AcceptOnMatch（true|false）
只有当log信息的LogLevel值与LogLevelToMatch相同，且AcceptOnMatch为true时才会匹配。

- LogLevelRangeFilter
过滤条件包括LogLevelMin、LogLevelMax和AcceptOnMatch
只有当log信息的LogLevel在LogLevelMin、LogLevelMax之间同时AcceptOnMatch为true时才会匹配。

- StringMatchFilter
过滤条件包括StringToMatch和AcceptOnMatch
只有当log信息的LogLevel值与StringToMatch对应的LogLevel值与相同， 且AcceptOnMatch为true时会匹配。

过滤条件处理机制类似于IPTABLE的Responsibility chain，（即先deny、再allow）不过执行顺序刚好相反
后写的条件会被先执行

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE log4j:configuration SYSTEM "log4j.dtd">
 
<log4j:configuration>
    <!-- 将日志信息输出到控制台 -->
    <appender name="ConsoleAppender" class="org.apache.log4j.ConsoleAppender">
        <!-- 设置日志输出的样式 -->
        <layout class="org.apache.log4j.PatternLayout">
            <!-- 设置日志输出的格式 -->
            <param name="ConversionPattern" value="[%d{yyyy-MM-dd HH:mm:ss:SSS}] [%-5p] [method:%l]%n%m%n%n" />
        </layout>
        <!--过滤器设置输出的级别-->
        <filter class="org.apache.log4j.varia.LevelRangeFilter">
            <!-- 设置日志输出的最小级别 -->
            <param name="levelMin" value="WARN" />
            <!-- 设置日志输出的最大级别 -->
            <param name="levelMax" value="ERROR" />
            <!-- 设置日志输出的xxx，默认是false -->
            <param name="AcceptOnMatch" value="true" />
        </filter>
    </appender>
 
    <!-- 将日志信息输出到文件，但是当文件的大小达到某个阈值的时候，日志文件会自动回滚 -->
    <appender name="RollingFileAppender" class="org.apache.log4j.RollingFileAppender">
        <!-- 设置日志信息输出文件全路径名 -->
        <param name="File" value="D:/log4j/RollingFileAppender.log" />
        <!-- 设置是否在重新启动服务时，在原有日志的基础添加新日志 -->
        <param name="Append" value="true" />
        <!-- 设置保存备份回滚日志的最大个数 -->
        <param name="MaxBackupIndex" value="10" />
        <!-- 设置当日志文件达到此阈值的时候自动回滚，单位可以是KB，MB，GB，默认单位是KB -->
        <param name="MaxFileSize" value="10KB" />
        <!-- 设置日志输出的样式 -->
        <layout class="org.apache.log4j.PatternLayout">
            <!-- 设置日志输出的格式 -->
            <param name="ConversionPattern" value="[%d{yyyy-MM-dd HH:mm:ss:SSS}] [%-5p] [method:%l]%n%m%n%n" />
        </layout>
    </appender>
 
    <!-- 将日志信息输出到文件，可以配置多久产生一个新的日志信息文件 -->
    <appender name="DailyRollingFileAppender" class="org.apache.log4j.DailyRollingFileAppender">
        <!-- 设置日志信息输出文件全路径名 -->
        <param name="File" value="D:/log4j/DailyRollingFileAppender.log" />
        <!-- 设置日志每分钟回滚一次，即产生一个新的日志文件 -->
        <param name="DatePattern" value="'.'yyyy-MM-dd-HH-mm'.log'" />
        <!-- 设置日志输出的样式 -->
        <layout class="org.apache.log4j.PatternLayout">
            <!-- 设置日志输出的格式 -->
            <param name="ConversionPattern" value="[%d{yyyy-MM-dd HH:mm:ss:SSS}] [%-5p] [method:%l]%n%m%n%n" />
        </layout>
    </appender>
 
    <!--
     注意：
     1：当additivity="false"时，root中的配置就失灵了，不遵循缺省的继承机制
     2：logger中的name非常重要，它代表记录器的包的形式，有一定的包含关系，试验表明
        2-1：当定义的logger的name同名时，只有最后的那一个才能正确的打印日志
        2-2：当对应的logger含有包含关系时，比如：name=test.log4j.test8 和 name=test.log4j.test8.UseLog4j，则2-1的情况是一样的
        2-3：logger的name表示所有的包含在此名的所有记录器都遵循同样的配置，name的值中的包含关系是指记录器的名称哟！注意啦！
     3：logger中定义的level和appender中的filter定义的level的区间取交集
     4：如果appender中的filter定义的 levelMin > levelMax ，则打印不出日志信息
     -->
 
    <!-- 指定logger的设置，additivity指示是否遵循缺省的继承机制-->
    <logger name="test.log4j.test8.UseLog4j" additivity="false">
        <level value ="WARN"/>
        <appender-ref ref="DailyRollingFileAppender"/>
    </logger>
 
    <!--指定logger的设置，additivity指示是否遵循缺省的继承机制 -->
    <logger name="test.log4j.test8.UseLog4j_" additivity="false">
        <level value ="ERROR"/>
        <appender-ref ref="RollingFileAppender"/>
    </logger>
 
    <!-- 根logger的设置-->
    <root>
        <level value ="INFO"/>
        <appender-ref ref="ConsoleAppender"/>
        <!--<appender-ref ref="DailyRollingFileAppender"/>-->
        <!--  想要添加多个appender-ref时,依次添加appender-ref的节点即可 -->
    </root>
 
</log4j:configuration>
```

# 参考和引用
本文主要是对当前的一些log4j的资料做整理,参考一些资料如下
- https://www.cnblogs.com/godtrue/p/6444158.html
- http://huchangan2005.iteye.com/blog/1681994
- http://blog.csdn.net/kangojian/article/details/7290085
- https://www.cnblogs.com/kevin-yuan/archive/2012/11/23/2784610.html

# 推荐
[slf4j log4j logback关系详解和相关用法](https://www.cnblogs.com/Sinte-Beuve/p/5758971.html)
