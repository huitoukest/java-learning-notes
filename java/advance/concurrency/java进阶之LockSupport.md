---
title: "java进阶之LockSupport"
date: "2018-05-14 17:34:59"
categories: ["j2se", "java进阶学习笔记"]
tags: ["LockSupport", "unsafe", "线程阻塞", "java进阶"]
---

# 简介
LockSupport是java.util.concurrent.locks包下的类，功能是对线程进行阻塞和唤醒。
LockSupport中以park开头的方法来阻塞当前线程，unpark来唤醒被阻塞的线程。
和传统的wait/notify机制不同的是，wait/notify是对当前线程阻塞和唤醒一个线程(而不能具体指定)；
而LockSupport阻塞当前对象，但是**唤醒时却可以唤醒指定线程，并且阻塞和唤醒的顺序任意**。

同时LockSupport是被用来创建锁和其他同步工具类的基本线程阻塞原语。

# 示例

## 基本用法
使用LockSupport来进行基本的阻塞和唤醒。
```java
@Test
public  void test001()throws Exception {
    Thread A = new Thread(new Runnable() {
        @Override
        public void run() {
            System.out.println("我需要等待条件A达成后再执行，开始阻塞");
            LockSupport.park();
            System.out.println("条件A已经达到，线程继续运行");
        }
    });
    A.start();
    //睡眠一秒钟，保证线程A已经阻塞
    Thread.sleep(1000);
    System.out.println("条件A已经达到，唤醒线程");
    LockSupport.unpark(A);
}
```
输出：
```text
我需要等待条件A达成后再执行，开始阻塞
条件A已经达到，唤醒线程
条件A已经达到，线程继续运行
```

## 阻塞的先后顺序
因为LockSupport实际上是通过许可机制来实现阻塞和唤醒的，所以先unpark后park会使得
线程不会被阻塞，但是会正常执行。
```java
@Test
    public void test002(){
        Thread thread = Thread.currentThread();
        LockSupport.unpark(thread);//释放许可
        LockSupport.park();// 获取许可
        System.out.println("out");//输出out
    }
```

## LockSupport响应中断
当现场调用interrupt方法中断线程后，被 LockSupport.park()阻塞的线程将会响应操作，此线程
将会继续向下执行且不会抛出错误。
**此时线程虽然被唤醒且不报错，但是中断状态为true（Thread.currentThread().isInterrupted() == true）。**
```java
public void test003()throws Exception {
        Thread a = new Thread(new Runnable() {
            @Override
            public void run() {
                System.out.println("开始阻塞");
                LockSupport.park();
                //将会输出结果： isInterrupted:true
                System.out.println("isInterrupted:" + Thread.currentThread().isInterrupted());
            }
        });
        a.start();
        //睡眠一秒钟，保证线程A已经阻塞
        Thread.sleep(1000);
        a.interrupt();
    }
```

## 指定parkblocker
parkblocker实在LockSupport中的一个volatitle修饰的一个Object对象，用来
保存当前的线程是被谁阻塞的，主要用于线程的监控和分析，
可以通过LockSupport的getBlocker获取到阻塞的对象

```java
  String blockerName = "线程停滞者";
        Thread A = new Thread(new Runnable() {
            @Override
            public void run() {
                LockSupport.park(blockerName);
            }
        });
        A.setName("测试线程");
        A.start();
```

# 源码简析
LockSupport类上的java doc描写了一个示例：
FIFOMutex ，此类维护一个先进先出的队列，
通过对队列中的成员依次的加锁和唤醒操作，实现和先进先出的非重入锁功能。
```java
class FIFOMutex {
    private final AtomicBoolean locked = new AtomicBoolean(false);
    private final Queue<Thread> waiters
      = new ConcurrentLinkedQueue<Thread>();
    public void lock() {
      boolean wasInterrupted = false;
      Thread current = Thread.currentThread();
      waiters.add(current);
      // Block while not first in queue or cannot acquire lock
      while (waiters.peek() != current ||
             !locked.compareAndSet(false, true)) {
        LockSupport.park(this);
        if (Thread.interrupted()) // ignore interrupts while waiting
          wasInterrupted = true;
      }
      waiters.remove();
      if (wasInterrupted) // reassert interrupt status on exit
        current.interrupt();
    }
    public void unlock() {
      locked.set(false);
      LockSupport.unpark(waiters.peek());
    }
  }}
```

LockSupport 中中到了unsafe类，此类全名sun.misc.Unsafe，
可以直接操控内存，被JDK广泛用于自己的包中，如java.nio和java.util.concurrent。
但是不建议在生产环境中使用这个类。因为这个API十分不安全、不轻便、而且不稳定。
LockSupport的方法底层都是调用Unsafe的方法实现。
```java
package java.util.concurrent.locks;
import sun.misc.Unsafe;

/**
 用于创建锁和其余同步类的线程阻塞原语，
它通过一个信号量机制(permit)来阻塞和唤醒线程
FIFOMutex 。。。。
 */
public class LockSupport {
    private LockSupport() {} // Cannot be instantiated.

    private static void setBlocker(Thread t, Object arg) {
        // Even though volatile, hotspot doesn't need a write barrier here.
        UNSAFE.putObject(t, parkBlockerOffset, arg);
    }

    /**
     * 
     */
    public static void unpark(Thread thread) {
        if (thread != null)
            UNSAFE.unpark(thread);
    }

    /**
     先设置blocker，在block后再阻塞对象，当对象不再阻塞后将block设置null
     * @since 1.6
     */
    public static void park(Object blocker) {
        Thread t = Thread.currentThread();
        setBlocker(t, blocker);
        UNSAFE.park(false, 0L);
        setBlocker(t, null);
    }

    /**
     * Disables the current thread for thread scheduling purposes, for up to
     * the specified waiting time, unless the permit is available.
     * @param blocker the synchronization object responsible for this
     *        thread parking
     * @param nanos the maximum number of nanoseconds to wait
     * @since 1.6
     */
    public static void parkNanos(Object blocker, long nanos) {
        if (nanos > 0) {
            Thread t = Thread.currentThread();
            setBlocker(t, blocker);
            UNSAFE.park(false, nanos);
            setBlocker(t, null);
        }
    }

    /**
     * @param deadline the absolute time, in milliseconds from the Epoch,
     *        to wait until
     * @since 1.6
     */
    public static void parkUntil(Object blocker, long deadline) {
        Thread t = Thread.currentThread();
        setBlocker(t, blocker);
        UNSAFE.park(true, deadline);
        setBlocker(t, null);
    }

    /**
     *  返回最近的线程的阻塞对象，没有则返回null
     * @since 1.6
     */
    public static Object getBlocker(Thread t) {
        if (t == null)
            throw new NullPointerException();
        return UNSAFE.getObjectVolatile(t, parkBlockerOffset);
    }

    public static void park() {
        UNSAFE.park(false, 0L);
    }

    public static void parkNanos(long nanos) {
        if (nanos > 0)
            UNSAFE.park(false, nanos);
    }

    public static void parkUntil(long deadline) {
        UNSAFE.park(true, deadline);
    }

    /** 返回一个伪随机数，用于初始化或者更新secondary 到的种子值
     */
    static final int nextSecondarySeed() {
        int r;
        Thread t = Thread.currentThread();
        if ((r = UNSAFE.getInt(t, SECONDARY)) != 0) {
            r ^= r << 13;   // xorshift
            r ^= r >>> 17;
            r ^= r << 5;
        }
        else if ((r = java.util.concurrent.ThreadLocalRandom.current().nextInt()) == 0)
            r = 1; // avoid zero
        UNSAFE.putInt(t, SECONDARY, r);
        return r;
    }

    // Hotspot implementation via intrinsics API
    private static final sun.misc.Unsafe UNSAFE;
    private static final long parkBlockerOffset;
    private static final long SEED;
    private static final long PROBE;
    private static final long SECONDARY;
    static {
        try {
            UNSAFE = sun.misc.Unsafe.getUnsafe();
            Class<?> tk = Thread.class;
            parkBlockerOffset = UNSAFE.objectFieldOffset
                (tk.getDeclaredField("parkBlocker"));
            SEED = UNSAFE.objectFieldOffset
                (tk.getDeclaredField("threadLocalRandomSeed"));
            PROBE = UNSAFE.objectFieldOffset
                (tk.getDeclaredField("threadLocalRandomProbe"));
            SECONDARY = UNSAFE.objectFieldOffset
                (tk.getDeclaredField("threadLocalRandomSecondarySeed"));
        } catch (Exception ex) { throw new Error(ex); }
    }

}
```

- parkBlockerOffset
parkBlockerOffset 就是parkBlocker在内存中地址偏移量，
通过UNSAFE可以直接得到此值。
sun.misc.Unsafe里把关于对象字段访问的方法抽象出来，
它提供了objectFieldOffset()方法用于获取某个字段相对 Java对象的“起始地址”的偏移量，
也提供了getInt、getLong、getObject等方法可以使用此偏移量来访问某个Java 对象的某个字段。
这里之所以不使用getter和setter方法是因为当此线程在被阻塞的情况下，parkBlocker才
会被赋值，而因为在阻塞之后对线程对象中的方法调用都是不会有响应的，通过这种内存寻找
到方法，来间接调用。

- unsafe的park和unpark
从源码中可以看到，LockSupport的大部分实现都是基于unsafe的。
其中unsafe的park和unpark底层维护一个二义性的_counter来保存一个许可，
需要注意的是这个许可是一次性的，unpark操作设置该值为1，park操作检查该值是否为1，
为1直接返回，不为1，则阻塞。

# 参考
https://www.jianshu.com/p/ceb8870ef2c5
https://blog.csdn.net/opensure/article/details/53349698
