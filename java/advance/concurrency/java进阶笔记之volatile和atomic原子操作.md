---
title: "java进阶笔记之volatile和atomic原子操作"
date: "2019-03-24 15:55:08"
categories: ["j2se", "java进阶学习笔记"]
tags: ["java", "进阶", "volatile", "atomic", "笔记"]
---

# 前言

## 概念简介
| 简称|  全称 |  说明   |
| -------- | --------- | ----------------------------- |
| CAS | Compare and Swap | 比较并交换 |
| JUC | java.util.concurrent | java的一个类包，主要用于并发控制 |
## 概念说明
在现代计算机的cpu中，cpu对数据的读写取分为两个步奏，
第一步：cpu从cpu自带的高速缓存(可能有L1、L2甚至L3等多级高速缓存)中查询对象，如果找到即使用。
第二步：如果第一步中cpu没有读取到数据，那么就会从内存中来读取需要的数据。

# cpu缓存
从最古老的cpu可能没有缓存，到单核cpu带单缓存，到多核cpu带单缓存，最后到多核cpu带多级缓存，
现代cpu主流是多核多级缓存。如果是单核cpu，则其缓存必然只有一个核心使用，而多核cpu如果只有单缓存
则也只有其一个核心使用，但是现代的多核多缓存则是每个核心可能有自己独立的缓存部分，此缓存部分不能
被其余的核心所读写，同时cpu核心保存有其缓存值的状态：已被修改、有效、无效、共享等。

# volatitle
jvm的内存模型分为：**主内存**和**工作内存**，每个线程对应一个工作内存，并共享主内存的数据；
这里的主内存实际上就是物理内存，而工作内存则是对主内存中值的副本，所有线程对数据的操作默认都是对工作内存的数据进行操作。
不同线程之间也无法直接访问对方工作内存中的变量，线程之间的通信通过(间接)读写主内存的值来完成。
所以jvm中线程操作变量如下：
- 普通变量
读操作会优先读取工作内存的数据，如果工作内存中不存在，则从主内存中拷贝一份数据到工作内存中并进行读写。
- volatile变量
读操作时JVM会把工作内存中对应的值设为无效，从主内存中读取数据;
写操作时JVM会把工作内存中对应的数据刷新到主内存中，如此其它线程就可以读取变量的最新值。

volatile原理：
volatile修饰的变量实际上是cpu在读写数据的时候会(如果是共享的变量)跳过自己的高速缓存而直接对内存进行操作。
所以其修饰的变量值能够被各个线程共享到最新的值，但是因为没有了高速缓存的命中，所以效率会很低。

# atomic原子操作
在java 的java.util.concurrent.atomic包下有很多原子操作类，特点即其方法具有原子性。
这些方法一般都是采用的case操作：
```
CAS操作有3个操作数，内存值V，旧的预期值A，要修改的新值B。
当且仅当预期值A和内存值V相同时，将内存值V修改为B，否则什么都不做。
```
通过循环case操作，直到操作成功，来使得方法具有原子性。
其中，**case替换的值是volatile修饰的值**，这样就使得其在多线程的情况下依然正确运行。

case操作的问题：
ABA问题。但是如果一个值原来是A，变成了B，又更新变成了A，那么使用CAS进行检查时会发现它的值没有发生变化，
但是实际上却变化了，所以只要保证每次新设置的值都和以前的值不同，则可以避免这个问题。
从Java1.5开始JDK的atomic包里提供了一个类AtomicStampedReference来解决ABA问题。

## 常见atomic类
- 基础数据类型的atomic类
包括AtomicBoolean、AtomicInteger、AtomicLong；
这些类型都是对基础数据值的原子操作。
其内部实现不是简单的使用synchronized，而是一个更为高效的方式CAS (compare and swap) + volatile和native方法，
从而避免了synchronized的高开销，执行效率大为提升。其实例各自提供对相应类型单个变量的访问和更新。
每个类也为该类型提供适当的实用工具方法。

- 数组类型的Atomic类
包括AtomicIntegerArray、AtomicLongArray、AtomicReferenceArray<E>；
使用原子方式对int和long以及指定对象的数组操作；
这些对数组的操作是通过native方法实现。数组变量进行volatile没有意义，因此set/get就需要unsafe来做了，
通过index来指定操作元素来保证数组中的每一个值的原子性。

- 通过反射更新类字段的Atomic
包括AtomicIntegerFieldUpdater<T> 、AtomicLongFieldUpdater<T>、AtomicReferenceFieldUpdater<T,V>，
它们分别可以对指定类的volatile修饰的int字段、long字段以及指定类型的字段进行原子操作；
它们都是基于反射的实用工具，可以提供对关联字段类型的访问，可用于获取任意选定volatile字段上的compareAndSet操作。
它们主要用于原子数据结构中，该结构中同一节点的几个 volatile 字段都独立受原子更新控制。
注意：
 - 字段必须是volatile类型的
 - 字段的描述类型（修饰符public/protected/default/private）是与调用者与操作对象字段的关系一致。
也就是说 调用者能够直接操作对象字段，那么就可以反射进行原子操作。
但是对于父类的字段，子类是不能直接操作的，尽管子类可以访问父类的字段。
 - 只能是实例变量，不能是类变量，也就是说不能加static关键字。
 - 只能是可修改变量，不能是final变量，因为final的语义就是不可修改。
实际上final的语义和volatile是有冲突的，这两个关键字不能同时存在。
 - 对于AtomicIntegerFieldUpdater 和AtomicLongFieldUpdater 只能修改int/long类型的字段，不能修改其包装类型（Integer/Long）。
如果要修改包装类型就需要使用AtomicReferenceFieldUpdater 。

- 引用类型的Atomic类
 - AtomicMarkableReference<V>
以原子操作操作其带有标记位的对象引用。
 - AtomicReference<V>
以原子的方式更新对象的引用。
 - AtomicStampedReference<V>
其维护带有整数标志的对象引用，以此位置对维护的值做更新。
其整数标志一般用版本号或者时间序列为值，以此可以解决ABA问题。

# 更多参考
http://www.cnblogs.com/xrq730/p/7048693.html
https://www.cnblogs.com/shoshana-kong/p/9066888.html
https://blog.csdn.net/heyutao007/article/details/19975665
https://www.cnblogs.com/onlywujun/articles/3529572.html
https://www.cnblogs.com/Java3y/p/8947240.html
