---
title: "java进阶之synchronized学习"
date: "2019-08-27 17:31:28"
categories: ["java进阶学习笔记"]
tags: ["java", "同步锁", "synchronized", "进阶"]
---

# 简介

java中的锁有两种，一种是以依赖于JVM的synchronized，还有一种是依赖于底层硬件的(cpu指令)CAS实现的Lock。

synchronized，多线程下的同步关键字，自动"加锁"且自动"解锁"，一般不会有死锁的情况产生。

被synchronized修饰的代码或者代码块会互斥执行，且每次执行完synchronized修饰的代码后，其中被锁住的对象（以及其对象中的变量）会使用主存中的最新值（因为JMM(Java Memory Model) happens-before规则支持：对一个锁的解锁，happens-before于随后对这个锁的加锁）。

synchronized具有重入性，支持嵌套调用。每个对象拥有一个计数器，当线程获取该对象锁后，计数器就会加一，释放锁后就会将计数器减一。

说明： 测试代码基于JDK8 202.

# 使用方法

synchronized可以修饰方法或者代码块，修饰代码块是需要提供一个非null的对象作为锁的KEY。

## 修饰非静态方法

当synchronized作用在方法上时，锁住的便是对象实例（this) ， 是当前对象。

示例：

```java
public class SynchronizedTest {
 
    static class Data{
        public static  int  value = 0;
        public synchronized void add(){
            value ++;
        }
    }
    @Test
    public void test() throws InterruptedException {
        CountDownLatch countDownLatch = new CountDownLatch(2000);
        IntStream.range(0,2000).mapToObj(it ->
            new Thread(() -> {
                    IntStream.range(0,1000).forEach(j ->{
                            new Data().add();
                    } );
                countDownLatch.countDown();
        })).forEach(it -> it.start());
        countDownLatch.await();
        //输出1989338，值不等于 2000 * 1000
        System.out.println(Data.value);
 
        CountDownLatch countDownLatch2 = new CountDownLatch(2000);
        Data data = new Data();
        Data.value = 0;
        IntStream.range(0,2000).mapToObj(it ->
                new Thread(() -> {
                    IntStream.range(0,1000).forEach(j ->{
                        data.add();
                    } );
                    countDownLatch2.countDown();
                })).forEach(it -> it.start());
        countDownLatch2.await();
        //输出2000 * 1000
        System.out.println(data.value);
    }
}
```

## 修饰静态方法

修饰静态方法时，等同于锁的对象是当前的class类，此时相当于该类的一个全局锁。

Class数据存在于永久带或者元数据空间(PermGen与Metaspace)。

```java
    static class Data{
        public static  int  value = 0;
        public synchronized void add(){
            value ++;
        }
        public static synchronized  void addStatic(){
            value ++;
        }
    }
 
    @Test
    public void staticMethodTest() throws InterruptedException {
        CountDownLatch countDownLatch = new CountDownLatch(2000);
        IntStream.range(0,2000).mapToObj(it ->
                new Thread(() -> {
                    IntStream.range(0,1000).forEach(j ->{
                        Data.addStatic();
                    } );
                    countDownLatch.countDown();
                })).forEach(it -> it.start());
        countDownLatch.await();
        //输出2000000
        System.out.println(Data.value);
    }
```

## 修饰代码块

修饰代码块时需要传入一个修饰的锁的KEY对象，常见的对象有this、xxx.class、某个普通对象。只有当不同线程遇到的KEY对象都相同（内存地址相同），互斥与同步的效果才会生效。

- 使用this ， 代码块内部效果基本等同于修饰非静态方法
- 使用xxx.class 对象 ，代码块内部 效果基本等同于修饰静态方法
- 使用某个普通对象，对象不变时具有代码块内部锁效果生效

示例：

```java
  static class Data{
        public static  int  value = 0;
        public synchronized void add(){
            value ++;
        }
        public static synchronized  void addStatic(){
            value ++;
        }
    }
 
    @Test
    public void codeBlockTest() throws InterruptedException {
        CountDownLatch countDownLatch = new CountDownLatch(2000);
        IntStream.range(0,2000).mapToObj(it ->
                new Thread(() -> {
                    IntStream.range(0,1000).forEach(j ->{
                        //由于每次都会生成新的字符串对象
                        //他们的内存地址不同，所以锁达不到想要的效果
                        synchronized ("12345" + Data.class.getName()){
                            Data.value ++ ;
                        }
                    } );
                    countDownLatch.countDown();
                })).forEach(it -> it.start());
        countDownLatch.await();
        //小于2000000，锁效果失败
        System.out.println(Data.value);
    }
```

# 分析

## 原理简析

网上有详细的分析文章，这里只是简单说明一下，详情可以查看参考。

每一个java对象都拥有自己的监视器monitor，当其中某个代码或者自身被synchronized修饰后访问此内容的时候都必须先获得此对象的监视器，如果成功则执行具体逻辑；否则改线程进入Blocked状态，当监视器被占有者释放后，在同步队列中的线程就会有机会重新获取该监视器。

使用synchronized修饰后，在jvm执行的基本流程如下：

1. 执行monitorenter指令（互斥）
2. 获得成功后执行代码
3. 执行monitorexit释放监视器

当多个线程一起访问某个对象监视器的时候，对象监视器会将这些请求存储在不同的容器中。

- Contention List：竞争队列，所有请求锁的线程首先被放在这个竞争队列中

- Entry List：Contention List中那些有资格成为候选资源的线程被移动到Entry List中

- Wait Set：哪些调用wait方法被阻塞的线程被放置在这里

- OnDeck：任意时刻，最多只有一个线程正在竞争锁资源，该线程被成为OnDeck

- Owner：当前已经获取到所资源的线程被称为Owner

-  !Owner：当前释放锁的线程

synchronized 严格来说是一个悲观锁，即当前线程获取到锁的时候同时也会阻塞其他线程获取该锁，这种锁适用于方法执行时间长的情况。因为synchronized在线程竞争的时候有一个阻塞与唤醒锁带来的性能开销，所以方法的执行时间越长则锁的性能开销所占用的资源消耗的比例就会越小。

## synchronized的happens-before

参见[java内存模型以及happens-before规则](https://www.jianshu.com/p/d52fea0d6ba5)

结果是：上一次加锁后修改的对象、变量的值对于下一次加锁的对象可见（即是存在与主内存而不是线程的缓存区域的值，效果类似于volatile变量)。

## synchronized 的"进化"

### 锁的存储

在HotSpot虚拟机中, 对象在内存中的布局分为三块区域: 对象头, 示例数据和对其填充.

对象头中包含两部分: MarkWord 和 类型指针.

如果是数组对象的话, 对象头还有一部分是存储数组的长度.

多线程下synchronized的加锁就是对同一个对象的对象头中的MarkWord中的变量进行CAS操作.

**MarkWord**

Mark Word用于存储对象自身的运行时数据, 如HashCode, GC分代年龄, 锁状态标志, 线程持有的锁, 偏向线程ID等等.占用内存大小与虚拟机位长一致(32位JVM -> MarkWord是32位, 64位JVM->MarkWord是64位).

**类型指针**

类型指针指向对象的类元数据, 虚拟机通过这个指针确定该对象是哪个类的实例.

**对象头的长度**

| 长度     | 内容                   | 说明                           |
| -------- | ---------------------- | ------------------------------ |
| 32/64bit | MarkWord               | 存储对象的hashCode或锁信息等   |
| 32/64bit | Class Metadada Address | 存储对象类型数据的指针         |
| 32/64bit | Array Length           | 数组的长度(如果当前对象是数组) |

​    如果是数组对象的话, 虚拟机用3个字节(32/64bit + 32/64bit + 32/64bit)存储对象头; 如果是普通对象的话, 虚拟机用2字节存储对象头(32/64bit + 32/64bit).

### 锁的状态

在java5 时期，synchronized 只有重量级锁一种方式来实现互斥的加锁与释放锁，在java6的synchronized 进行了大量的优化，大大提高了性能。优化后的synchronized 有如下几种状态：

1. 无锁状态
2. 偏向锁状态 （ 默认开启偏向锁）
3. 轻量级锁状态
4. 重量级锁状态

这四种状态可以从1升级到4，但是不能降级，只能单向升级。

#### 偏向锁

偏向锁主要适用于一个线程运行时的情况，获取锁是检查锁状态以及MarkWord中是保存当前线程ID，是则获取成功，否则升级为CAS锁来竞争此锁。（即获取锁的线程是不会主动释放锁的，而且其余线程需要竞争时有其余的线程来升级锁状态造成被动释放的。使用偏向锁的原因：经验表明, 其实大部分情况下, 都会是同一个线程进入同一块同步代码块的，即多个线程间的冲突一般不高。

#### 轻量锁

轻量锁是通过CAS实现的，CAS实现一般会在外部用一个"无限"循环的操作来持续尝试获取锁，无线循环又被成为自旋，所以这里的轻量锁，实质上就是一个自旋锁。

当自旋的次数达到了限制次数后，如果竞争锁的线程仍然没有获取到锁，则锁会升级为重量锁状态。

#### 重量级锁

重量级锁实质上就是对象监视器的获取了，因为会阻塞（使用OS的Mutex Lock）其余的线程，所以响应的时间变慢，但是在一个线程持有锁的期间，其余的线程不会向轻量锁一样因为自旋而消耗cpu，所以适用于执行时间长、追求吞吐量的同步场景。

# 更多参考

synchronized原理与分析：

[synchronized和Lock的JVM底层实现](https://blog.csdn.net/chenssy/article/details/54883355)

[让你彻底理解Synchronized](https://www.jianshu.com/p/d53bf830fa09)

[Java6及以上版本对synchronized的优化](https://www.cnblogs.com/wuqinglong/p/9945618.html)

[Linux的MuteLex](https://blog.csdn.net/u013022032/article/details/51991610)
