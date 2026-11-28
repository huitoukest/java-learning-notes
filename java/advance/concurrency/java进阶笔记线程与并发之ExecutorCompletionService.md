---
title: "java进阶笔记线程与并发之ExecutorCompletionService"
date: "2020-04-06 17:01:55"
categories: ["java进阶学习笔记"]
tags: ["java", "多线程", "并发编程", "Executor", "Completion"]
---

# 简介

- ExecutorCompletionService类是CompletionService接口的实现，ExecutorCompletionService内部管理者一个已完成任务的阻塞队列（可以自定义），ExecutorCompletionService引用了一个Executor, 用来执行任务

- submit()方法最终会委托给内部的executor去执行任务
- take/poll方法的工作都委托给内部的已完成任务阻塞队列
  - take 如果阻塞队列中有已完成的任务, take方法就返回任务的结果, 否则阻塞等待任务完成
  - poll方法不同
    - poll方法不会阻塞等待结果，获取时如果是没有结果，则返回null，可以执行在指定时间内等待

使用场景与注意：

- 在提交一个批次任务后，获取并使用这些任务的结果时使用。
- 和自己记录所有提交的任务的future不同，ExecutorCompletionService倾向于按照任务的完成先后顺序给予结果，而码者一般按照任务的先后顺序，所以理论上ExecutorCompletionService等待的时间更少，处理效率更高。
- 但是： 因为其会记录线程执行的结果，所以如果执行了但是没有使用，则会造成线程结果的堆积，造成内存泄露。
- 为什么会泄露 ？
  - 因为结果不是强制处理的，是可以堆积在内存中持续增长的。

# 使用示例

```java
@Test
    public void test(){
        ExecutorService executor = Executors.newFixedThreadPool(10);
        ExecutorCompletionService<Integer> executorCompletionService = new ExecutorCompletionService(executor);
        IntStream.range(0,10).forEach(it -> executorCompletionService.submit(() -> it));
        IntStream.range(0,10).forEach(it -> {
            try {
                int value = executorCompletionService.take().get();
                System.out.print(value);
            } catch (InterruptedException e) {
                e.printStackTrace();
            } catch (ExecutionException e) {
                e.printStackTrace();
            }
        });
    }
```

```java
//结果输出的值并不确定，和执行完成的顺序有关
1203457689
```

# 源码简析

基于jdk1.8.

## CompletionService

ps://  ExecutorCompletionService 完成的结果队列如果自定义，可以考虑加入一个最大长度的限制。在生成环境中给予提示、警告、错误三种阈值，并记录相应日志或者提示，防止内存泄露并及时处理。

```java
/**
* 将异步任务的生产和完成的结果处理做解耦，按照任务的完成顺序
* 处理，例如来管理异步i/o.
* 内存一致性： 任务提交先与线程中的操作，线程中操作闲鱼take返回
*/
public interface CompletionService<V> {
    /**
     * 提交一个任务
     */
    Future<V> submit(Callable<V> task);
 
    /**
     * 执行任务并返回预置结果
     */
    Future<V> submit(Runnable task, V result);
 
    /**
     * 等待直到任务完成返回结果，同时移除原存储的结果
     * @throws InterruptedException if interrupted while waiting
     */
    Future<V> take() throws InterruptedException;
 
    /**
     * 等待并移出下一个Future，或者返回null
     *
     * @return the Future representing the next completed task, or
     *         {@code null} if none are present
     */
    Future<V> poll();
 
    /**
     * 同poll，但是运行定义有最大等待时间
     */
    Future<V> poll(long timeout, TimeUnit unit) throws InterruptedException;
}
```

## ExecutorCompletionService

```java
package java.util.concurrent;
 
/**
* 该类是轻量的，适合处理临时任务
*/
public class ExecutorCompletionService<V> implements CompletionService<V> {
    private final Executor executor;
    private final AbstractExecutorService aes;
    //ps:完成结果队列，容易内存泄露
    private final BlockingQueue<Future<V>> completionQueue;
 
    /**
     * QueueingFuture 加入了完成任务时加入队列的功能，见down()
     */
    private class QueueingFuture extends FutureTask<Void> {
        QueueingFuture(RunnableFuture<V> task) {
            super(task, null);
            this.task = task;
        }
        protected void done() { completionQueue.add(task); }
        private final Future<V> task;
    }
 
    private RunnableFuture<V> newTaskFor(Callable<V> task) {
        if (aes == null)
            return new FutureTask<V>(task);
        else
            return aes.newTaskFor(task);
    }
 
    private RunnableFuture<V> newTaskFor(Runnable task, V result) {
        if (aes == null)
            return new FutureTask<V>(task, result);
        else
            return aes.newTaskFor(task, result);
    }
 
    /**
     * ps: 特别判断了参数是否是 AbstractExecutorService 类型
     * @throws NullPointerException if executor is {@code null}
     */
    public ExecutorCompletionService(Executor executor) {
        if (executor == null)
            throw new NullPointerException();
        this.executor = executor;
        this.aes = (executor instanceof AbstractExecutorService) ?
            (AbstractExecutorService) executor : null;
        this.completionQueue = new LinkedBlockingQueue<Future<V>>();
    }
 
    /**
     * 自定义的完成队列，但是可能在使用add加入是报错（如果实现的不匹配的话）
     */
    public ExecutorCompletionService(Executor executor,
                                     BlockingQueue<Future<V>> completionQueue) {
        if (executor == null || completionQueue == null)
            throw new NullPointerException();
        this.executor = executor;
        this.aes = (executor instanceof AbstractExecutorService) ?
            (AbstractExecutorService) executor : null;
        this.completionQueue = completionQueue;
    }
    //ps: 统一原则，统一转为RunnableFuture，统一处理
    public Future<V> submit(Callable<V> task) {
        if (task == null) throw new NullPointerException();
        RunnableFuture<V> f = newTaskFor(task);
        executor.execute(new QueueingFuture(f));
        return f;
    }
 
    public Future<V> submit(Runnable task, V result) {
        if (task == null) throw new NullPointerException();
        RunnableFuture<V> f = newTaskFor(task, result);
        executor.execute(new QueueingFuture(f));
        return f;
    }
    //ps: 直接使用了队列的take
    public Future<V> take() throws InterruptedException {
        return completionQueue.take();
    }
 
    public Future<V> poll() {
        return completionQueue.poll();
    }
 
    public Future<V> poll(long timeout, TimeUnit unit)
            throws InterruptedException {
        return completionQueue.poll(timeout, unit);
    }
 
}
```
