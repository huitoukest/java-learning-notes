---
title: "java 进阶笔记线程与并发之Future简析"
date: "2019-10-21 21:55:19"
categories: ["j2se", "java进阶学习笔记"]
tags: ["java", "进阶笔记", "线程与并发", "Future"]
---

# 简介

Future表示异步计算的结果。方法用于检查计算是否完成，等待计算完成，并检索计算结果。只有当计算完成时，才能使用get方法检索结果，如果需要，可以阻塞它，直到它准备好为止。取消由取消方法执行。还提供了其他方法来确定任务是正常完成还是被取消。一旦计算完成，就不能取消计算。如果为了可取消而不提供可用的结果，可以声明Future作为底层任务的结果返回null。

# 说明

## Future<V> 方法简介

- boolean cancel(boolean mayInterruptIfRunning)

试图关闭正在执行的任务。

  - 如果任务还没开始，执行cancel(...)方法将返回false；

  - 如任务已经启动，执行cancel(true)方法将以中断执行此任务线程的方式来试图停止任务，如果停止成功，返回true；

  - 当任务已经启动，执行cancel(false)方法将不会对正在执行的任务线程产生影响(让线程正常执行到完成)，此时返回false；

  - 当任务已经完成，执行cancel(...)方法将返回false。mayInterruptRunning参数表示是否中断执行中的线程。

- V get()
等待任务完成，并返回结果；会阻塞当前线程直到异步任务完成。

- V get(long timeout, TimeUnit unit)
等待指定时间，超过会抛出超时异常。

- boolean isCancelled()
如果任务完成前被取消，则返回true。

- boolean isDone()
如果任务执行结束，无论是正常结束或是中途取消还是发生异常，都返回true。

## 相关子接口

### Response <T>

Response接口提供用于获取响应操作调用时发送的消息的有效负载和上下文的方法。
对于异步操作调用，它提供了额外的方法来检查请求的状态。get(…)方法可能抛出标准的异常集，其原因可能是RemoteException或WebServiceException，它表示异步方法调用期间发生的错误。

新增方法：

- Map<String,Object> getContext()
获取包含的响应上下文.

### RunnableFuture <V>

一个可以操纵的Future。run方法的成功执行将导致Future的完成，并允许访问其结果。

简单来说就是将执行的逻辑和状态封装到了一起。

新增方法：

- void run()
除非它已被取消，否则将这个Future设置为它的计算结果.

### ScheduledFuture <T>

public interface ScheduledFuture<V>
extends Delayed, Future<V>

一个可以被取消的延迟的有结果的行动。通常，调度的Future是使用ScheduledExecutorService调度任务的结果.

方法说明：

- long getDelay(TimeUnit unit) 在给定的时间单元中，返回与此对象关联的剩余延迟。
  - 剩下的Delay;
  - 0或负值表示Delay已经过去
- compareTo(T o)  Compares this object with the specified object for order.

### RunnableScheduledFuture <V>

public interface RunnableScheduledFuture<V>
extends RunnableFuture<V>, ScheduledFuture<V>

同时包含几个接口的功能，包括调度和run。

方法：

- boolean isPeriodic()
Returns true if this task is 周期性质的.

## 相关子类
### CompletableFuture

封装了异步调用和函数式编程的一些快捷方法，能够在一个异步任务完成的不同阶段进行链式编程风格的数据和结果的处理。

示例：

```java
CompletableFuture.runAsync(() -> {
            System.out.println("1:" + System.currentTimeMillis());
            try {
                Thread.sleep(1000);
            System.out.println("2:" + System.currentTimeMillis());
            } catch (InterruptedException e) {
                e.printStackTrace();
            }
            System.out.println("3:" + System.currentTimeMillis());
        }).thenRunAsync(() -> System.out.println("4:" + System.currentTimeMillis()))
          .thenApply(it -> 1)
          .thenAccept(System.out::println)
          .join();
```

### CountedCompleter

public abstract class CountedCompleter<T> extends ForkJoinTask<T>

可以说是一类特殊的ForkJoinTask，后面再分析。

### ForkJoinTask 、RecursiveAction 、RecursiveTask

适用于ForkJoinPool的Future任务。

### FutureTask

public class FutureTask<V> extends Object implements RunnableFuture<V>

实际上FutureTask 的功能基本等同于RunnableFuture，只是多了两种提交的包装。

- FutureTask(Callable  callable)
- FutureTask(Runnable runnable, V result)
创建一个FutureTask，它将在运行时执行给定的Runnable，并安排get在成功完成时返回给定的结果。

### SwingWorker

javax.swing.SwingWorker

public abstract class SwingWorker<T,V> extends Object implements RunnableFuture<T>

SwingWorker是为以下情况设计的: 您需要在后台线程中运行一个长时间运行的任务，并在完成时或处理时向UI提供更新。SwingWorker的子类必须实现doInBackground()方法来执行后台计算。

# 参考

Java多线程编程：Callable、Future和FutureTask浅析  https://blog.csdn.net/javazejian/article/details/50896505
