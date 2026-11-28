# java 目录说明

Java 学习笔记：基础、进阶并发/NIO、设计、Java EE 与架构设计。

## 文章索引

### advance/base

- [java进阶之unsafe与CAS操作简介](<advance/base/java进阶之unsafe与CAS操作简介.md>) — Unsafe类属于在sun.misc包下，不属于Java标准包。（unsafe、cas操作、内存屏障、compareAndSwap）
- [java进阶笔记之java语言类层次结构概览](<advance/base/java进阶笔记之java语言类层次结构概览.md>) — 本文主要简介java语言中常用类/接口/jvm的结构。（java、层次、结构、高级）
- [java进阶笔记之List](<advance/base/java进阶笔记之List.md>) — java的List类是一个接口，其继承自Collection接口。（java、list、linkedList、ArrayList）
- [java进阶笔记之Queue队列分析](<advance/base/java进阶笔记之Queue队列分析.md>) — Queue是一种线性的数据队列结构，其一般只允许在队列数据的前端front，也称为头部head和（java、queue、队列、入门）
- [java进阶笔记之Set(HashSet和TreeSet和LinkedHashSet等)](<advance/base/java进阶笔记之Set(HashSet和TreeSet和LinkedHashSet等).md>) — java的set用于存放值不重复的对象，其结构如图。（java、hashSet、TreeSet、LinkedHashSet）
- [java进阶笔记之字符串String,StringBuilder,StringBuffer区别和分析](<advance/base/java进阶笔记之字符串String,StringBuilder,StringBuffer区别和分析.md>) — String,StringBuilder,StringBuffer都是CharSequence接口的实现。（java、String、StringBuilder、StringBuffer）
- [java进阶笔记之常用（通用）Map（Hash，Tree，Linked，Properties等）](<advance/base/java进阶笔记之常用（通用）Map（Hash，Tree，Linked，Properties等）.md>) — Map是将键映射到值 key-value 的对象。（java、map、hashMap、hashTable）
- [java进阶笔记之数组分析](<advance/base/java进阶笔记之数组分析.md>) — 在我看来，java中的数组可以理解为是一个没有物理class类，（java、数组、入门、分析）
- [java进阶笔记之枚举Enum](<advance/base/java进阶笔记之枚举Enum.md>) — java.lang.Enum类是从jdk1.5开始诞生的。（java、枚举、enum、进阶笔记）
- [java进阶笔记之装箱(boxing)和拆箱(unboxing)操作](<advance/base/java进阶笔记之装箱(boxing)和拆箱(unboxing)操作.md>) — 简而言之装箱就是将基本数据类型转换为包装器类型；拆箱就是将包装器类型转换为基本数据类型。（java、装箱、拆箱、boxing）

### advance/concurrency

- [java AbstractOwnableSynchronizer与AbstractQueuedSynchronizer简析](<advance/concurrency/java AbstractOwnableSynchronizer与AbstractQueuedSynchronizer简析.md>) — AbstractQueuedSynchronizer全限定名java.util.concurrent.locks.AbstractQueuedSynchronizer，继承自jav（ASQ、AbstractQueuedSynchronizer、java进阶、Condition）
- [java 进阶笔记线程与并发之AbstractExecutorService](<advance/concurrency/java 进阶笔记线程与并发之AbstractExecutorService.md>) — 一个正常的submit、invokeAny 和 invokeAll 方法的通用实现。（java、进阶笔记、线程与并发、AbstractExecutorService）
- [java 进阶笔记线程与并发之Executor、ExecutorService简析](<advance/concurrency/java 进阶笔记线程与并发之Executor、ExecutorService简析.md>) — Executor和ExecutorService都是接口，他们主要完成一个工作：执行和管理任务。（executor、executorService、java、concurrent）
- [java 进阶笔记线程与并发之ForkJoinPool简析](<advance/concurrency/java 进阶笔记线程与并发之ForkJoinPool简析.md>) — ForkJoinPool是一个线程池，支持特有的的ForkJoinTask，对于ForkJoinTask任务，通过特定的for与join方法可以优化调度策略，提高效率。（java、进阶笔记、ForkJoinPool、线程与并发）
- [java 进阶笔记线程与并发之Future简析](<advance/concurrency/java 进阶笔记线程与并发之Future简析.md>) — Future表示异步计算的结果。方法用于检查计算是否完成，等待计算完成，并检索计算结果。只有当计算完成时，才能使用get方法检索结果，如果需要，可以阻塞它，直到它准备好为止。取消由（java、进阶笔记、线程与并发、Future）
- [java 进阶笔记线程与并发之线程计数与同步工具](<advance/concurrency/java 进阶笔记线程与并发之线程计数与同步工具.md>) — 常见的线程计数和信息同步工具如下：（java、多线程、计数器、同步器）
- [java进阶之Condition接口](<advance/concurrency/java进阶之Condition接口.md>) — Condition Condition 是java5加入的，全限定名 java.util.concurrent.locks.Condition，是一个接口，主要功能是配合Lock是（java、进阶、Condition、线程同步）
- [java进阶之LockSupport](<advance/concurrency/java进阶之LockSupport.md>) — LockSupport是java.util.concurrent.locks包下的类，功能是对线程进行阻塞和唤醒。（LockSupport、unsafe、线程阻塞、java进阶）
- [java进阶之Lock与ReentrantLock](<advance/concurrency/java进阶之Lock与ReentrantLock.md>) — Lock与ReentrantLock都是java.util.concurrent.locks包中常用的接口和类。（java、Lock、ReentrantLock、锁）
- [java进阶之synchronized学习](<advance/concurrency/java进阶之synchronized学习.md>) — java中的锁有两种，一种是以依赖于JVM的synchronized，还有一种是依赖于底层硬件的cpu指令CAS实现的Lock。（java、同步锁、synchronized、进阶）
- [java进阶笔记之volatile和atomic原子操作](<advance/concurrency/java进阶笔记之volatile和atomic原子操作.md>) — | 简称| 全称 | 说明 |（java、进阶、volatile、atomic）
- [java进阶笔记之多线程:Thread类](<advance/concurrency/java进阶笔记之多线程_Thread类.md>) — java中的线程是jvm中虚拟的一个进程中的多个执行序列，线程执行并不一定是并行执行，可能是均分cpu（java、多线程、thread、进阶）
- [java进阶笔记之线程池](<advance/concurrency/java进阶笔记之线程池.md>) — 对于线程池，网上的资料非常的多，本文不准备重复介绍和说明，而仅仅对重点和注意事项说明。（java、线程池、ThreadPoolExecutor、Executors）
- [java进阶笔记线程与并发之CompletableFuture.md](<advance/concurrency/java进阶笔记线程与并发之CompletableFuture.md>) — @TOCjava进阶笔记线程与并发之CompletableFuture.md（java、线程与并发、进阶笔记、Completable）
- [java进阶笔记线程与并发之CountedCompleter](<advance/concurrency/java进阶笔记线程与并发之CountedCompleter.md>) — CountedCompleter是ForkJoinTask的一个子类。（java、进阶笔记、线程与并发、CountedCompleter）
- [java进阶笔记线程与并发之ExecutorCompletionService](<advance/concurrency/java进阶笔记线程与并发之ExecutorCompletionService.md>) — - ExecutorCompletionService类是CompletionService接口的实现，ExecutorCompletionService内部管理者一个已完成任务的（java、多线程、并发编程、Executor）
- [java进阶笔记线程与并发之StampedLock](<advance/concurrency/java进阶笔记线程与并发之StampedLock.md>) — - StampedLock 是ReadWriteLock的一种实现，不支持重入（容易死锁），适用于读多写少的场景。（java、多线程、并发编程、StampedLock）
- [java进阶笔记线程与并发之高性能随机数ThreadLocalRandom](<advance/concurrency/java进阶笔记线程与并发之高性能随机数ThreadLocalRandom.md>) — - java的随机数均根据seed生成，而新的seed由老的seed生成。（java、多线程、random、ThreadLocal）

### advance/nio

- [java进阶笔记之Channel与AbstractInterruptibleChannel](<advance/nio/java进阶笔记之Channel与AbstractInterruptibleChannel.md>) — - 什么是Channel（java、进阶笔记、Channel、Interruptible）
- [java进阶笔记之FileSystemProvider](<advance/nio/java进阶笔记之FileSystemProvider.md>) — 文件相关的操作最终通过 java.nio.file.spi.FileSystemProvider 来提供 ,其不同的底层系统有不同的实现. 此类主要定义了如何在其对应的文件系统定位（java、文件、SystemProvider、File）
- [java进阶笔记之Files文件工具类](<advance/nio/java进阶笔记之Files文件工具类.md>) — Files 是JDK1.7 之后系统封装的对文件操作的工具类 .（java、Files、文件、进阶笔记）
- [java进阶笔记之Path](<advance/nio/java进阶笔记之Path.md>) — Path 是jdk1.7 推出的专用于访问文件的一种路径抽象.（java、进阶笔记、Path）
- [java进阶笔记之Paths与FileSystems](<advance/nio/java进阶笔记之Paths与FileSystems.md>) — - Paths中封装了活动Path的工具方法 , 其实现默认依赖于FileSystems , 是Path操作的增强工具类.（java、进阶、Paths、FileSystems）
- [java进阶笔记之URI与URL.md](<advance/nio/java进阶笔记之URI与URL.md>) — URL 和URI无物理上的直接联系 不是继承和实现 .（进阶笔记、URI、URL、URN）

### base/misc

- [java实例化时的属性、构造方法、继承代码、静态代码块的执行/初始化顺序](<base/misc/java实例化时的属性、构造方法、继承代码、静态代码块的执行_初始化顺序.md>) — import org.junit.Test;（java、实例化、初始化顺序、静态代码块）
- [NoClassDefFoundError com/sun/media/imageio/stream/RawImageInputStream StreamSegmentMapper ...](<base/misc/NoClassDefFoundError com_sun_media_imageio_stream_RawImageInputStream StreamSegm.md>) — 问题原因：此类是缺少java jai中的图像处理类，此类并且没有包含在标准的jdk中。（j2se）
- [原码，补码，反码和常见二进制位运算](<base/misc/原码，补码，反码和常见二进制位运算.md>) — - 原码（原码、反码、补码、位运算）

### base/utils

- [java 时间转换解析 通用](<base/utils/java 时间转换解析 通用.md>) — 1. 去掉所有非数字字符（java、时间转换、Date）
- [java_模拟dos文件夹树](<base/utils/java_模拟dos文件夹树.md>) — 最新代码见:<http://blog.csdn.net/huitoukest/article/details/50516026>（java、文件、递归）
- [java图片验证码包括文字和图片的旋转](<base/utils/java图片验证码包括文字和图片的旋转.md>) — java图片验证码包括文字图片的旋转:（验证码、图片、旋转）
- [java生成图片验证码二,加入透明颜色,各种干扰线,干扰点,干扰框,旋转,随机位置](<base/utils/java生成图片验证码二,加入透明颜色,各种干扰线,干扰点,干扰框,旋转,随机位置.md>) — public class VerificationCode {（验证码、图片、java）
- [一个关于Json数据List和对象嵌套反序列化的工具类,java(20151130)](<base/utils/一个关于Json数据List和对象嵌套反序列化的工具类,java(20151130).md>) — 背景说明: 本示例中用的是fastJson来解析具体的事务;（json、java）
- [中国二代居民身份证校验_编码正确性校验 java实现](<base/utils/中国二代居民身份证校验_编码正确性校验 java实现.md>) — 身份证18位分别代表的含义，身份证15位升级到18位，原来年用2位且没有最后一位，从左到右方分别表示（身份证、校验）
- [人民币大小写转换 java 实现](<base/utils/人民币大小写转换 java 实现.md>) — 参考:http://blog.csdn.net/guaishushu1ss/article/details/76757405（java、大小写、转换、人民币）
- [带有范围权重信息的随机数列表   java8实现 2](<base/utils/带有范围权重信息的随机数列表 java8实现 2.md>) — 其定义可以参考http://blog.csdn.net/huitoukest/article/details/79449076（随机数、范围、权重、红包算法）
- [带有范围权重信息的随机数列表  java8实现1](<base/utils/带有范围权重信息的随机数列表 java8实现1.md>) — 注意： 第二种优化的实现方式见 http://blog.csdn.net/huitoukest/article/details/79474767（随机数、权重、列表、红包算法）
- [用java模拟dos树结构(tree命令)第二弹](<base/utils/用java模拟dos树结构(tree命令)第二弹.md>) — 上一次的模拟地址:（java、dos、tree、树）

### design

- [java23种设计模式简结](<design/java23种设计模式简结.md>) — 我觉得设计模式的本质还是面向对象编程的思想,而需要达成的编程目的即解耦和复用.（设计模式、java）
- [java8 lambda表达式之 Stream常用方法](<design/java8 lambda表达式之 Stream常用方法.md>) — 前言:废话不错,一切都在代码中.（java、java新特性、Stream）
- [java8 新特性 lambda格式入门](<design/java8 新特性 lambda格式入门.md>) — 废话不说，直接上代码，看注释（lambda、java新特性）

### ee/mq

- [springboot amqp rabiitmq 使用fastjson自定义MessageConverter](<ee/mq/springboot amqp rabiitmq 使用fastjson自定义MessageConverter.md>) — 支持byte 、CharSequence 两种类型直接传输 ，其余对象直接用fastjson转为json字符串传输 。（MQ、springboot、amqp、fastjson）

### ee/orm

- [Hibernate4 一个baseDao的封装,包含一些通用的增删改查方法](<ee/orm/Hibernate4 一个baseDao的封装,包含一些通用的增删改查方法.md>) — 网上有很多封装的不错的baseDao,但是不一定适合,所以把自己用了这段时间的baseDao拿出来,一方面自己以后用着方便,一方面大家有需要可以拿去用;（hibernate、baseDao）
- [Hibernate使用注意事项之增删改查](<ee/orm/Hibernate使用注意事项之增删改查.md>) — 一:嵌套查询示例:（数据库、乱码、jdbc、hibernate）
- [struts2 convention plugin  学习笔记零配置学习笔记本 huitoukest](<ee/orm/struts2 convention plugin 学习笔记零配置学习笔记本 huitoukest.md>) — 1、struts2自2.1以后推荐使用Convention Plugin支持struts零配置支持引入jar：struts2-convention-plugin-2.x.x.jar（struts2、convention、plugin、ssh）
- [在Hibernate中的一个对tree树节点查询封装的通用工具类](<ee/orm/在Hibernate中的一个对tree树节点查询封装的通用工具类.md>) — 1.前言（java、hibernate、树）

### ee/spring

- [springBoot入门配置和使用说明](<ee/spring/springBoot入门配置和使用说明.md>) — - 创建可以独立运行的 Spring 应用。（springboot、配置、说明、入门）
- [Spring中Adivisor和Aspect的区别（自我理解）](<ee/spring/Spring中Adivisor和Aspect的区别（自我理解）.md>) — — 方/切 面（Aspect）：一个关注点的模块化，这个关注点实现可能另外横切多个对象。事务管理是J2EE应用中一个很好的横切关注点例子。方面用Spring的Advisor或拦截器（ssh、aop）
- [异常解决：java.lang.IllegalStateException: Failed to introspect Class](<ee/spring/异常解决：java.lang.IllegalStateException_ Failed to introspect Class.md>) — @TOCjava.lang.IllegalStateException: Failed to introspect Class（UnsatisfiedDependencyException、introspect、AppClassLoader、java）

### ee/web

- [(java office转pdf) MS Office2010、WPS2015、OpenOffice4用Java将Office文档转换为PDF，WIN7 64位系统](<ee/web/(java office转pdf) MS Office2010、WPS2015、OpenOffice4用Java将Office文档转换为PDF，WIN7 64位.md>) — 2023的更多选择：（ms office、openoffice、WPS2015、PDF）
- [j2ee,jsp,servlet文件下载服务器端](<ee/web/j2ee,jsp,servlet文件下载服务器端.md>) — 1.getOutputStream has already been called for this response（服务器、servlet、j2ee）
- [office转pdf（在线预览）思路（java示例）](<ee/web/office转pdf（在线预览）思路（java示例）.md>) — 实现手段可以参见openoffice转pdf或者别的软件，网上有具体的转换手段，我这里不多说；（openoffice、office、pdf）
