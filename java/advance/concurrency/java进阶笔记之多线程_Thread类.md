---
title: "java进阶笔记之多线程:Thread类"
date: "2019-03-24 17:49:58"
categories: ["j2se", "java进阶学习笔记"]
tags: ["java", "多线程", "thread", "进阶", "笔记"]
---

# 简介
java中的线程是jvm中虚拟的一个进程中的多个执行序列，线程执行并不一定是并行执行，可能是均分cpu
的时间块来在执行各个线程的代码，由于时间块足够小，所以表现为多个线程在“同时”运行。
# 线程状态
每个线程都有自己的运行状态。
1. 新建状态
用new关键字和Thread类或其子类**新建立一个线程对象后，该线程对象就处于新生状态**。处于新生状态的线程有自己的内存空间，通过调用start方法进入就绪状态（runnable）。
**注意：**不能对已经启动的线程再次调用start()方法，否则会出现Java.lang.IllegalThreadStateException异常。
2. 就绪状态
**处于就绪状态的线程已经具备了运行条件，但还没有分配到CPU**。其处于线程就绪队列（尽管是采用队列形式，事实上，把它称为可运行池而不是可运行队列。因为cpu的调度不一定是按照先进先出的顺序来调度的），等待系统为其分配CPU。等待状态并不是执行状态，当系统选定一个等待执行的Thread对象后，它就会从等待执行状态进入执行状态，系统挑选的动作称之为“cpu调度”。一旦获得CPU，线程就进入运行状态并自动调用自己的run方法。
3. 运行状态
**处于就绪状态的线程，如果获得了cpu的调度，就会从就绪状态变为运行状态**，执行run()方法中的任务。如果该线程失去了cpu资源，就会又从运行状态变为就绪状态。也可以对在运行状态的线程调用yield()方法，它就会让出cpu资源，再次变为就绪状态。
4. 阻塞状态
**处于运行状态的线程在某些情况下，线程让出CPU并暂时停止自己的运行，进入阻塞状态**。 在阻塞状态的线程不能进入就绪队列。只有当引起阻塞的原因消除时，如睡眠时间已到，或等待的I/O设备空闲下来，线程便转入就绪状态，重新到就绪队列中排队等待，被系统选中后从原来停止的位置开始继续运行
5. 死亡状态
**当线程的run()方法执行完，或者被强制性地终止，就认为它死去**。这个线程对象也许是活的，但是，它已经不是一个单独执行的线程。线程一旦死亡，就不能复生。 如果在一个死去的线程上调用start()方法，会抛出java.lang.IllegalThreadStateException异常。

# 常见方法
## 当前线程操作
- Thread.currentThread()
获取当前线程，通过此方法可以调用当前线程的一些特有功能
- Thread.sleep
使当前线程睡眠即阻塞指定时间，调用后当前线程进入阻塞状态。同时只有被中断或者达到时间后自动唤醒进入运行状态。
注意：Thread.sleep调用后的线程阻塞时，会持有线程相关的对象锁。
-

## 线程通信
线程中的通信操作很多方法位于Object类，包括wait()、notify()和notifyAll()，这些方法都必须在synchronized块中执行，否则会抛出IllegalMonitorStateException。
ps：为什么必须在synchronized块中执行？
为了保证调用这几个方法的逻辑是原子性的，这样可避免先notify再wait的一直阻塞的情况发生。
```java
1.1  A线程  判断条件K = true
2.1  B线程  判断条件K = false
2.2  B线程  notify
1.2  A线程  wait
由于没有同步，这里条件K被两个线程读取到了不同的值，并且交叉执行。
```
- wait() 方法
wait方法调用后，当前线程会进入阻塞状态并且释放相关的对象锁，同时进入一个线程等待池中。
只有达到时间或者被唤醒时重新进入运行状态。
- notify() 方法
notify方法只唤醒一个等待（对象的）线程并使该线程开始执行。所以如果有多个线程等待一个对象，这个方法只会唤醒其中一个线程，无法手动指定具体唤醒的线程。
- notifyAll() 方法
notifyAll 会唤醒所有等待(对象的)线程，尽管哪一个线程将会第一个处理取决于操作系统的实现。如果当前情况下有多个线程需要被唤醒，推荐使用notifyAll 方法。

# 线程相关内存
- 程序计数器
程序计数器在JVM中所起的作用就是用于存放当前线程接下来将要执行的字节码指令、分支、循环、跳转、异常处理等信息。
- Java虚拟机栈(堆栈)
Java虚拟机栈也是线程私有的，它的生命周期与线程相同，是在JVM运行时所创建的，在线程中，方法在执行的时候都会创建一个名为栈的数据结构，主要用于存放局部变量表、操作栈、动态链接、方法出口等信息
- 本地方法栈
Java中提供了调用本地方法的接口，在线程的执行过程中，经常会碰到调用JNI方法的情况，比如网络通信、文件操作的底层，甚至是String的intern等都是JNI方法，JVM为本地方法所划分的内存区域便是本地方法栈，这块内存区域其自由度非常高，完全靠不同的JVM厂商来实现，Java虚拟机规范并未给出强制的规定，同样它也是线程私有的内存区域。
- 堆内存
堆内存是JVM中最大的一块内存区域，被所有的线程所共享，Java在运行期间创建的所有对象几乎都存放在该内存区域，该内存区域也是垃圾回收器重点照顾的区域，因此有些时候堆内存被称为“GC堆”。堆内存一般会被细分为新生代和老年代，更细致的划分为Eden区、From Survivor区和To Survivor区。
**注意**：
 - 可以通过新建Thread对象时或者java启动是设定线程参数stacksize指定线程的栈空间大小。
 - 堆栈的速度仅次于寄存器和高速缓存，比堆和其余外置存储更快。一般寄存器只要存放指令一次操作的数据，高速缓存则是内存的部分拷贝。

# 线程同步简介
通过前文可以知道，当一个数据被多个线程所共享的时候，由于每个线程使用的数据都是共享数据的一个拷贝，如果数据的同步不及时，则会导致**共享数据在同一刻时间内在不同线程拥有不同的拷贝值**。
为了保证数据的统一和准确，所以有时我们需要做线程或者说数据同步的工作，来保证数据的正确。

## 使用volatile关键字
被volatile关键字修饰的变量，会在每次使用时都和共享数据做同步， 保证数据是最新的。
此方式适合单个变量或者对象的同步。

## synchronized 关键字
被synchronized修饰的方法、代码块会变成同步代码块，即同一时间内只有一个线程执行代码块内部的代码。
如此，来保证代码逻辑和数据的正确性。

## ReentrantLock 关键字
通过 来手动控制加锁与释放锁，加锁与释放锁之间的代码块也保持互斥性，即同一时间内只有一个线程执行此间代码。
```java
ReentrantLock() : 创建一个ReentrantLock实例 
        lock() : 获得锁 
        unlock() : 释放锁 
```

## 通过阻塞或者cas机制手动实现
核心思想也是保证同一时刻只有一个线程运行指定代码块，如LinkedBlockingQueue或者AtomicInteger计数线程来实现或者使用Semaphore直接控制并发线程数。

# 源码简析
thread类中我们简单查看下几个常用和重要的方法的源码。

## 初始化 init 方法
init 是线程初始化方法，在构造方法中最终会调用此方法来初始化对应的数据。
```java 
 //g是线程组，target被调用RUN方法的目标对象，name线程的名字，stackSize用于新线程分配所需堆栈大小
    private void init(ThreadGroup g, Runnable target, String name,  long stackSize) {  
    Thread parent = currentThread();
    //获得系统的安全管理器
    SecurityManager security = System.getSecurityManager();
    if (g == null) {
        //安全检查
        if (security != null) {
        g = security.getThreadGroup();
        }
       //设置线程组
        if (g == null) {
        g = parent.getThreadGroup();
        }
    }
    /* checkAccess regardless of whether or not threadgroup is
           explicitly passed in. */
    //检查是否允许调用线程修改线程组参数
    g.checkAccess();
    /* 是否有权限访问
     * Do we have the required permissions?
     */
    if (security != null) {
        if (isCCLOverridden(getClass())) {
            security.checkPermission(SUBCLASS_IMPLEMENTATION_PERMISSION);
        }
    }
        g.addUnstarted();
    //线程组
    this.group = g;
    //是否守护线程
    this.daemon = parent.isDaemon();
    this.priority = parent.getPriority();
    this.name = name.toCharArray();
    if (security == null || isCCLOverridden(parent.getClass()))
        this.contextClassLoader = parent.getContextClassLoader();
    else
        this.contextClassLoader = parent.contextClassLoader;
    this.inheritedAccessControlContext = AccessController.getContext();
    this.target = target;
    setPriority(priority);
        if (parent.inheritableThreadLocals != null)
        this.inheritableThreadLocals =
        ThreadLocal.createInheritedMap(parent.inheritableThreadLocals);
        /* Stash the specified stack size in case the VM cares */
        this.stackSize = stackSize;
        /* Set thread ID */
        tid = nextThreadID();
    }
```
## start方法
我们一般是通过start方法来使得一个线程进入就绪状态，而实际上start中调用了start0方法来完成此功能。
```java
 public synchronized void start() {
      //验证线程的状态，如果线程已启动则抛异常
        if (threadStatus != 0)
            throw new IllegalThreadStateException();
      //向线程组里添加此线程
        group.add(this);
       //使线程进入可执行（runnable状态）的状态
        start0();
        //如果验证停止前于开始
        if (stopBeforeStart) {
        stop0(throwableFromStop);
    }
    }
```

## run方法
如果传入的Runnable不为空则执行器代码逻辑。

```java
 public void run() {
    if (target != null) {
        target.run();
    }
    }
```

## exit 方法
run方法中的逻辑执行完毕后，会自动调用exit方法。
```java
 private void exit() {
    if (group != null) {
        group.remove(this);
        group = null;
    }
    target = null;
        threadLocals = null;
        inheritableThreadLocals = null;
        inheritedAccessControlContext = null;
        blocker = null;
        uncaughtExceptionHandler = null;
    }
```

## join 方法
join方法的作用是调用此方法后，当前线程(此行代码)之后的代码将会在线程执行完毕，或者超过指定时间之后执行。
所以，在多线程中需要谨慎使用，如果是在多线程的内部使用join方法则会使之变成单线程执行的情况。
```java
public final void join() throws InterruptedException {
    join(0);
}

public final synchronized void join(long millis)
throws InterruptedException {
    long base = System.currentTimeMillis();
    long now = 0;

    if (millis < 0) {
        throw new IllegalArgumentException("timeout value is negative");
    }
    //isAlive 用来判断当前线程是否启动并且正在运行
    if (millis == 0) {
        while (isAlive()) {
            wait(0);
        }
    } else {
        while (isAlive()) {
            long delay = millis - now;
            if (delay <= 0) {
                break;
            }
            wait(delay);
            now = System.currentTimeMillis() - base;
        }
    }
}
```

## start0
start0()会调用本机的操作系统函数，因为多线程需要底层操作系统的支持
```java
private native void start0();
```
# 参考
https://www.cnblogs.com/snow-flower/p/6114765.html
https://blog.csdn.net/qq_42145871/article/details/81950949
