---
title: "java进阶之unsafe与CAS操作简介"
date: "2018-05-07 11:34:23"
categories: ["j2se", "java进阶学习笔记"]
tags: ["unsafe", "cas操作", "内存屏障", "compareAndSwap", "java进阶"]
---

# 简介
## Unsafe
Unsafe类属于在sun.misc包下，不属于Java标准包。
但是很多Java的基础类库，比如Netty、Cassandra、Hadoop、Kafka等都使用此类。
Unsafe类因为是native方法，直接调用底层，所以效率很高，在增强Java语言底层操
作能力方面起了很大的作用。当然，**因为其直接操作内存**，有点不受JVM管束，所以
官方建议除了JAVA自带的API内部使用，是不建议开发人员直接使用的。

## CAS操作
Compare And Swap(CAS)简单的说就是比较并交换。
CAS 操作包含三个操作数 —— 内存位置（V）、预期原值（A）和新值(B)。如果内存位置的值与预期原值相匹配，那么处理器会自动将该位置值更新为新值。否则，处理器不做任何操作。无论哪种情况，它都会在 CAS 指令之前返回该位置的值。Java并发包(java.util.concurrent)中大量使用了CAS操作,涉及到并发的地方都调用了sun.misc.Unsafe类中的Comparexxx方法进行CAS操作。

Volatile修饰的成员变量在每次被线程访问时，都强迫从主内存中重读该成员变量的值。并且，当成员变量发生变化时，线程将变化值回写到主内存。这样不同的线程看到的变量的值总是相同的，或者说volatile修饰的变量值发生变化时对于另外的线程是可见的。

**通过volatile和CAS机制，我们可以实现乐观锁的功能。**
编程中的锁可以分为两类：悲观锁和乐观锁。悲观锁的主要观点是限制入口，每次只能有一个线程访问，好像真的有一把锁，谁得到了谁才能够执行自己的操作，但是这样会导致大量的线程阻塞，比较耗费资源，也适用于同步代码快本身就占用大量资源或者会长时间运行的情况。
而乐观锁则认为冲突是很少的，所以开放入口，让每个线程自己去检查当前是否有其余的线程在运行，如果没有则自己运行，如果有则等待，**这样在冲突较少或者同步代码块占用资源较少的的情况下，乐观锁的效率会非常的高**。
而通过volatile和CAS机制就是实现此乐观锁的一种方式，当然也有人觉得这种方式并没有真正意义上的阻塞线程，并不存在锁操作，所以也被认为是无锁同步的一种方式。

因为**java的CAS实现是调用的Java本地方法(JNI)，是直接由cpu硬件支持的原子操作**，这使得java程序通过CAS来运行的效率会非常高。

# 方法说明

Unsafe类使用了单例模式，需要通过一个静态方法getUnsafe()来获取。但Unsafe类做了限制，如果是直接调用的话，它会抛出一个SecurityException异常；
在JDk1.8或之前只有由主类加载器加载的类才能调用这个方法。其源码如下：
```java
public static Unsafe getUnsafe() {
    Class var0 = Reflection.getCallerClass();
    if(!VM.isSystemDomainLoader(var0.getClassLoader())) {
        throw new SecurityException("Unsafe");
    } else {
        return theUnsafe;
    }
}
```
当然，可以使用反射的方法来使用：
```java
 Field f = Unsafe.class.getDeclaredField("theUnsafe");
 f.setAccessible(true);
 Unsafe unsafe = (Unsafe) f.get(null);
```

在JDK1.9之后此类已经开放使用了：
java9中，Unsafe变成了jdk.internal.misc下的包，同时包含了一个静态方法，可以直接拿到theUnsafe对象。
```java
package jdk.internal.misc;

public static Unsafe getUnsafe() {
    return theUnsafe;
}
```

通过unsafe来构建java对象：
通过unsafe构建时，无论构造方法是不是private的类都可以实例化。
```java
//unsafe = Unsafe的实例对象
Singleton singleton= (Singleton) unsafe.allocateInstance(Singleton.class);
```

Unsafe类提供了以下这些功能：

- 内存管理

包括分配内存、释放内存等
该部分包括了allocateMemory（分配内存）、reallocateMemory（重新分配内存）、copyMemory（拷贝内存）、freeMemory（释放内存 ）、getAddress（获取内存地址）、addressSize、pageSize、getInt（获取内存地址指向的整数）、getIntVolatile（获取内存地址指向的整数，并支持volatile语义）、putInt（将整数写入指定内存地址）、putIntVolatile（将整数写入指定内存地址，并支持volatile语义）、putOrderedInt（将整数写入指定内存地址、有序或者有延迟的方法）等方法。

getXXX和putXXX中是对内存中各种数据的读写方法，其中getXXXVolatile和getXXX，前者支持Volatile语义，后者不支持，而普通操作也get类似。
get操作同时可以获取某一个类中某一个属性在非堆内存中的位置,因为在非堆中，这个属性需要满足下面两个属性之一：
这个属性是一个静态属性 。
这个属性是一个volatile修饰的属性。
(非堆内存又被称为方法区，一般都保存静态属性和常量池和JVM内部处理或优化所需的内存等)

通过copyMemory方法，我们可以实现一个通用的对象的浅拷贝。
copyMemory使用示例：
https://www.cnblogs.com/suxuan/p/4948608.html

而在写方法中,putXXX,putOrderXXX,putXXXVolatile的性能也是依次从高到低。
分配内存和读写值：
```java
Unsafe unsafe = getUnsafe();
final int size = 100;
//分配内存，并返回地址，size表示字节数，即分配了100个字节的内存
final long addr = unsafe.allocateMemory( size );
try{
    System.out.println( "当前分配的内存首地址： " + addr );
    //由于一个Int类型占用4个字节，所以100个字节长度实际上最多表示一个25个长度的Int数组
    for ( int i = 0; i < size / 4; i++ )
    {
        unsafe.putInt( addr + i * 4, 123);
        if ( unsafe.getInt( addr + i * 4 ) != 123 ) {
            System.out.println("内存值写入失败，地址偏移量是：" + i);
        }
    }
    //循环打印数据前3个数
    for ( long i = 0; i < 3; ++i ){
        int result = unsafe.getInt( addr + i * 4 );
        System.out.println( " i = " + i  + ",result is:" + result);
    }
}finally{
    //必须在finally中释放内存
    unsafe.freeMemory( addr );
}
```
输出：
```java
当前分配的内存首地址： 428555056
 i = 0,result is:123
 i = 1,result is:123
 i = 2,result is:123
```

- 类似反射、对象、变量操作
Unsafe提供了很多类似反射的操作：
allocateInstance() 可以直接生成对象实例，且无需调用构造方法和其它初始化方法。
这在对象反序列化的时候会很有用，能够重建和设置final字段，而不需要调用构造方法。
staticFieldOffset（静态域偏移）、defineClass（定义类）、defineAnonymousClass（定义匿名类）、ensureClassInitialized（确保类初始化）、objectFieldOffset（对象域偏移）等方法。
通过这些方法我们可以获取对象的指针，通过对指针进行偏移，我们可以直接修改指针指向的数据（即使它们是私有的），包括JVM已经认定为垃圾、可以进行回收的对象。

- 数组操作
这部分包括了arrayBaseOffset（获取数组第一个元素的偏移地址）、arrayIndexScale（获取数组中元素的增量地址）等方法。arrayBaseOffset与arrayIndexScale配合起来使用，就可以定位数组中每个元素在内存中的位置。
java中默认的数组下标是Integer类型的，所以最大数组长度是Integer.MAX_VALUE，而使用Unsafe类的内存分配方法可以实现超大数组。当然这样的数组实际上风险很大，内存和分配和回收都有可能会发生异常。
```java
@Test
    public void test003(){
        Unsafe unsafe = getUnsafe();
        long longArrayOffset = unsafe.arrayBaseOffset(long[].class);
        final long[] ar = new long[ 1000 ];
        final int index = ar.length - 1;
        ar[ index ] = -1; //FFFF FFFF FFFF FFFF
        System.out.println( "Before change = " + Long.toHexString( ar[ index ] ));
        for ( long i = 0; i < 8; ++i )
        { //long类型占用8个字节，这里每一次循环向ar[ index ]这个long对象中的一个字节中写入内容0
            unsafe.putByte( ar, longArrayOffset + 8L * index + i, (byte) 0);
            System.out.println( "After change: i = " + i + ", val = " + Long.toHexString( ar[ index ] ));
        }
    }
```
输出：
```java
Before change = ffffffffffffffff
After change: i = 0, val = ffffffffffffff00
After change: i = 1, val = ffffffffffff0000
After change: i = 2, val = ffffffffff000000
After change: i = 3, val = ffffffff00000000
After change: i = 4, val = ffffff0000000000
After change: i = 5, val = ffff000000000000
After change: i = 6, val = ff00000000000000
After change: i = 7, val = 0
```

- 锁功能、CAS操作
类似与compareAndSwapXXX的操作都是一个原子操作，也就是说cpu在执行cas时，对这一块内存是独占排他的。在并发包中很多操作真正执行的也是cas，并发包中的类并发性能比使用 synchronized 关键字好也在于此：锁的粒度小了许多并且少了线程上下文切换。（synchronized 操作需要切换线程的上下文，所以比较耗费资源）
java的很多AtomicXXX原子类都是通过CAS操作来实现的，比如AtomicInteger。
同时Unsafe中还包括了monitorEnter、tryMonitorEnter、monitorExit、compareAndSwapInt、compareAndSwap等方法。
其中monitorEnter、tryMonitorEnter、monitorExit已经被标记为deprecated，不建议使用。
compareAndSwapInt方法：
```java
/**
* 比较obj的offset处内存位置中的值和期望的值，如果相同则更新。此更新是不可中断的，
  即使原子性的。
* @param obj 需要更新的对象
* @param offset obj中整型field的偏移量
* @param expect 希望field中存在的值
* @param update 如果期望值expect与field的当前值相同，设置filed的值为这个新值
* @return 如果field的值被更改返回true
*/
public native boolean compareAndSwapInt(Object obj, long offset, int expect, int update);
```

- 线程的阻塞与唤醒：park、unpark
park、unpark方法是并发包中锁的基础，通过park将线程一直阻塞直到超时或者中断等条件出现。unpark可以唤醒一个park的线程，使其恢复正常。
而LockSupport类中的park与unpark方法对unsafe中的park与unpark方法做了封装，LockSupport类中有各种版本pack方法，但最终都调用了Unsafe.park()方法。

- 内存屏障
内存屏障，也称内存栅栏，内存栅障，屏障指令等， 是一类同步屏障指令，是CPU或编译器在对内存随机访问的操作中的一个同步点，使得此点之前的所有读写操作都执行后才可以开始执行此点之后的操作。之所以这样，实际上是因为cpu的缓存中的变量值和内存中的变量值在多线程情况下可能不一致。
Unsafe中包括了loadFence、storeFence、fullFence来进行内存屏障操作。而Unsafe. putOrderedObject，Unsafe. putOrderedInt，Unsafe. putOrderedLong这三个方法，JDK会在执行这三个方法时插入StoreStore内存屏障，避免发生写操作重排序。
内存屏障是在Java 8新引入的，用于定义内存屏障，避免代码重排序。
loadFence() 表示该方法之前的所有load操作在内存屏障之前完成。
storeFence()表示该方法之前的所有store操作在内存屏障之前完成。
fullFence()表示该方法之前的所有load、store操作在内存屏障之前完成。

# 参考
常用方法：
https://www.cnblogs.com/smileorsilence/p/7993741.html
unsafe常用操作：
https://www.cnblogs.com/suxuan/p/4948608.html
