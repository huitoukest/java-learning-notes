---
title: "java进阶笔记之线程池"
date: "2019-06-02 10:18:41"
categories: ["j2se", "java进阶学习笔记"]
tags: ["java", "线程池", "ThreadPoolExecutor", "Executors"]
---

# 前言
对于线程池，网上的资料非常的多，本文不准备重复介绍和说明，而仅仅对重点和注意事项说明。

# 线程池中一些概念说明
线程的创建、销毁都是需要消耗系统资源的，而线程池可以复用池中的线程，所以可能大幅减少这两个步奏带来的资源开销，从而提高效率。

## 逻辑
任务提交时，判断的顺序为 corePoolSize –> workQueue –> maximumPoolSiz

## 配置说明

### workQueue参数
workQueue 中一般有三种：SynchronousQueue、LinkedBlockingQueue、ArrayBlockingQueue。

-  SynchronousQueue
SynchronousQueue 内部没有容量，但是由于一个插入操作总是对应一个移除操作 ，所以可以理解为其在添加的元素没有被线程消费时会直接阻塞当前调用线程。

- LinkedBlockingQueue
无界队列，链表实现，将线程池的最大线程数量限制为maximumPoolSize。当队列长度达到设置的最大值后，将会阻塞当前调用线程。

-  ArrayBlockingQueue
有界队列，此队列按 FIFO（先进先出）原则对元素进行操作， 线程池的最大线程数量限制为maximumPoolSize。当队列长度达到设置的最大值后，将会阻塞当前调用线程。

### threadFactory

它是ThreadFactory类型的变量，是产生thread的一个工厂类，用来创建新线程。默认使用Executors.defaultThreadFactory() 来创建线程。

Executors.defaultThreadFactory():
    Each new thread is created as a non-daemon thread with priority set to the smaller of Thread.NORM_PRIORITY and the maximum priority permitted in the thread group. New threads have names accessible via Thread.getName() of pool-N-thread-M, where N is the sequence number of this factory, and M is the sequence number of the thread created by this factory.

使用默认的ThreadFactory来创建线程时，会使新创建的线程具有相同的NORM_PRIORITY优先级并且是非守护线程，同时也设置了线程的名称。

```java
public interface ThreadFactory {
 
    /**
     * Constructs a new {@code Thread}.  Implementations may also initialize
     * priority, name, daemon status, {@code ThreadGroup}, etc.
     *
     * @param r a runnable to be executed by new thread instance
     * @return constructed thread, or {@code null} if the request to
     *         create a thread is rejected
     */
    Thread newThread(Runnable r);
}
```

此工厂提供了对一个线程的priority, name, daemon status, ThreadGroup的信息初始化。

```java
// ThreadGroup 的默认配置
SecurityManager s = System.getSecurityManager();
             group = (s != null) ? s.getThreadGroup() : Thread.currentThread().getThreadGroup();
```

java.lang.SecurityManager.getThreadGroup() ：

Returns the thread group into which to instantiate any new thread being created at the time this is being called. By default, it returns the thread group of the current thread. This should be overridden by a specific security manager to return the appropriate thread group.  

方法返回该线程组成实例化在此被称为时间被创建任何新的线程。默认情况下，它返回当前线程的线程组。这应该由特定的安全管理覆盖到返回适当的线程组。

### RejectedExecutionHandler
它是表示线程池的饱和策略。如果阻塞队列满了并且没有空闲的线程，这时如果继续提交任务，就需要采取一种策略处理该任务。线程池提供了4种策略：
AbortPolicy：直接抛出异常，这是**默认**策略；
CallerRunsPolicy：用调用者所在的线程来执行任务；
DiscardOldestPolicy：丢弃阻塞队列中靠最前的任务，并执行当前任务；
DiscardPolicy：直接丢弃任务；

## 逻辑与方法

### Worker类

线程池中的每一个线程被封装成一个Worker对象，ThreadPool维护的其实就是一组Worker对象。
```java
private final class Worker  extends AbstractQueuedSynchronizer  implements Runnable
```
### submit和execute方法
submit有返回值，Future 类型，通过 Future  对象能够获取到线程执行的情况信息 。 execute方法没有返回值。
说明：
submit底层调用的还是execute，但是提交的任务不是原本的Runnable实例，而是在Runnable的基础上封装了一层为RunnableFuture。此 RunnableFuture 的run方法被重写，包裹了原有Run逻辑，对所有的Throwable类型进行捕获，并把异常通过setException保存在内部变量outcome里面。所以线程池执行的过程中异常不会被抛出。当submit被RunnableFuture.get的时候。会在report方法调用过程中抛出这个未检查异常，如果run没有执行完毕则会阻塞到run执行完毕后返回对应的结果！

### shutdown 方法
shutdown方法要将线程池切换到SHUTDOWN状态，并调用interruptIdleWorkers方法请求中断所有空闲的worker，最后调用tryTerminate尝试结束线程池。即正在执行的任务会继续执行下去，线程池不能够接受新的任务，没有被执行的则中断。

### shutdownNow 方法
将线程池的状态设置为STOP；中断所有工作线程，无论是否是空闲的；取出阻塞队列中没有被执行的任务并返回。shutdownNow方法执行完之后调用tryTerminate方法。即正在执行的任务则被停止，线程池不能够接受新的任务，没被执行任务的则返回。

### getLargestPoolSize方法
线程池曾经创建过的最大线程数量。通过这个数据可以知道线程池是否满过，也就是达到了maximumPoolSize；

### awaitTermination(long, TimeUnit) 方法
如果已经shutdown了则阻塞当前调用线程直到线程池中的任务执行完毕或超时，如果没有shutdown则会阻塞当前调用线程直到超时

### 线程池扩展
在ThreadPoolExecutor类中提供了几个空方法，如beforeExecute方法，afterExecute方法和terminated方法，可以继承后扩展这些方法在执行前或执行后增加一些新的操作。

## Executors线程池简介
Executors中封装了一些静态的快捷创建线程池的方法，由于其隐藏了很多参数细节，平时不推荐使用，但是需要了解。推荐使用new ThreadPoolExecutor(...)的方式创建线程池。

- newFixedThreadPool
创建一个固定大小的线程池，阻塞队列长度默认Integer.MAX_VALUE，keeyAliveTime=0（只要线程个数比核心线程个数多并且当前空闲则回收）。
注意：阻塞队列太大会引起OOM;核心线程会常驻内存，可能会造成资源浪费。

- newSingleThreadExecutor
只有1个线程的的线程池，其余等同于newFixedThreadPool。
注意：由于最多只有一个线程运行，可能有大量任务堆积在队列中。

- newCachedThreadPool
按需创建线程的线程池，最大线程数为Integer.MAX_VALUE，阻塞队列最大长度1，keeyAliveTime=60 只要线程60s内空闲则回收。
注意：可能创建大量线程降低效率，引发OOM。

- newScheduledThreadPool
创建一个最小线程个数corePoolSize，最大为Integer.MAX_VALUE，阻塞队列为DelayedWorkQueue的线程池。此线程池支持定时以及周期性执行任务的需求。

# 更多三方参考
[线程池说明](https://www.cnblogs.com/liuzhihu/p/8177371.html)
[SynchronousQueue]( https://www.cnblogs.com/duanxz/p/3252267.html)

[线程池分析](http://ifeve.com/java-threadpool/)
[三种阻塞队列的区别]( https://www.cnblogs.com/feiyun126/p/7686302.html)
