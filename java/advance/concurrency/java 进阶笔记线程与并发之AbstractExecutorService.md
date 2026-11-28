---
title: "java 进阶笔记线程与并发之AbstractExecutorService"
date: "2019-10-21 21:53:07"
categories: ["j2se", "java进阶学习笔记"]
tags: ["java", "进阶笔记", "线程与并发", "AbstractExecutorService"]
---

# 简介
一个正常的submit、invokeAny 和 invokeAll 方法的通用实现。

# 源码简析
## RunnableFuture
```java
/**
 * 成功执行run()，才会使Future完成，并得到它的结果。
 * @see FutureTask
 * @see Executor
 * @since 1.6
 * @author Doug Lea
 * @param <V> The result type returned by this Future's {@code get} method
 */
public interface RunnableFuture<V> extends Runnable, Future<V> {
    /**
     * Sets this Future to the result of its computation
     * unless it has been cancelled.
     */
    void run();
}

```

## AbstractExecutorService

```java
package java.util.concurrent;
import java.util.*;

/**
 * 提供了ExecutorService的执行方法的一些默认实现。
 * 此类使用 newTaskFor 返回的 RunnableFuture 实现 submit、invokeAny 和 invokeAll 方法，
 * 默认情况下，RunnableFuture 是此包中提供的 FutureTask 类。
 * @since 1.5
 * @author Doug Lea
 */
public abstract class AbstractExecutorService implements ExecutorService {

    /**
     * Returns a {@code RunnableFuture} for the given runnable and default
     * value.
     *
     * @param runnable the runnable task being wrapped
     * @param value the default value for the returned future
     * @param <T> the type of the given value
     * @return a  RunnableFuture,它将运行Runnable中的任务，且生成给的的值，
     * 提供取消任务的功能 
     * @since 1.6
     */
    protected <T> RunnableFuture<T> newTaskFor(Runnable runnable, T value) {
        return new FutureTask<T>(runnable, value);
    }

    /**
     * @since 1.6
     */
    protected <T> RunnableFuture<T> newTaskFor(Callable<T> callable) {
        return new FutureTask<T>(callable);
    }
    
    /**
     * @throws RejectedExecutionException {@inheritDoc}
     * @throws NullPointerException       {@inheritDoc}
     */
    public Future<?> submit(Runnable task) {
        if (task == null) throw new NullPointerException();
        RunnableFuture<Void> ftask = newTaskFor(task, null);
        execute(ftask);
        return ftask;
    }
    
    /**
     * @throws RejectedExecutionException {@inheritDoc}
     * @throws NullPointerException       {@inheritDoc}
     */
    public <T> Future<T> submit(Runnable task, T result) {
        if (task == null) throw new NullPointerException();
        RunnableFuture<T> ftask = newTaskFor(task, result);
        execute(ftask);
        return ftask;
    }

    /**
     * @throws RejectedExecutionException {@inheritDoc}
     * @throws NullPointerException       {@inheritDoc}
     */
    public <T> Future<T> submit(Callable<T> task) {
        if (task == null) throw new NullPointerException();
        RunnableFuture<T> ftask = newTaskFor(task);
        execute(ftask);
        return ftask;
    }

    /**
     * invokeAny的主要机制
     */
    private <T> T doInvokeAny(Collection<? extends Callable<T>> tasks,
                              boolean timed, long nanos)
        throws InterruptedException, ExecutionException, TimeoutException {
        if (tasks == null)
            throw new NullPointerException();
        //ps:复用，提高性能
        int ntasks = tasks.size();
        if (ntasks == 0)
            throw new IllegalArgumentException();
        //ps: 设置ntasks作为初始容量
        ArrayList<Future<T>> futures = new ArrayList<Future<T>>(ntasks);
        //维护一个阻塞队列，完成的任务加入阻塞队列，所以有完成的任务时立即返回
        //否则将会阻塞等待 直到队列中有阻塞任务的加入
        ExecutorCompletionService<T> ecs =
            new ExecutorCompletionService<T>(this);
        
        // 为了提高效率，特别是在并行度有限的执行器中，在提交更多任务之前，
       //请检查以前提交的任务是否已经完成。这种交错和异常机制造成了主循环的混乱。
        try {
            // 记录异常，这样如果我们不能获得任何结果，我们就可以抛出我们得到的最后一个异常.
            ExecutionException ee = null;
           //计算截止时间
            final long deadline = timed ? System.nanoTime() + nanos : 0L;
            Iterator<? extends Callable<T>> it = tasks.iterator();

            // Start one task for sure; the rest incrementally
           //ps: 这里先提交一个任务，然后继续处理
            futures.add(ecs.submit(it.next()));
            --ntasks;
            int active = 1;
            //  ps: 循环的作用，在还没有任务完成时，循环启动新的任务。
           // 这里的超时只会在启动所有任务且有任务未运行完毕时候才会判断，所以时间不能太短
            for (;;) {
                //非阻塞获取一个Future
                Future<T> f = ecs.poll();
                if (f == null) {
                    if (ntasks > 0) {
                        --ntasks;
                        futures.add(ecs.submit(it.next()));
                        ++active;
                    }
                    else if (active == 0)
                        break;
                    else if (timed) {
                        f = ecs.poll(nanos, TimeUnit.NANOSECONDS);
                        if (f == null)
                            throw new TimeoutException();
                        nanos = deadline - System.nanoTime();
                    }
                   //ps : 若f == null 且 剩余任务<=0 ,且没有正在运行的任务，
                   // 且timed==false,则调用ecs.take()，阻塞等待获取
                    else
                        f = ecs.take();
                }
                //ps:说明任务已经完成了至少一个,返回对应结果或者抛出异常
                if (f != null) {
                    --active;
                    try {
                        return f.get();
                    } catch (ExecutionException eex) {
                        ee = eex;
                    } catch (RuntimeException rex) {
                        ee = new ExecutionException(rex);
                    }
                }
            }

            if (ee == null)
                ee = new ExecutionException();
            throw ee;

        } finally {
            //ps： 尝试关闭未完成的任务，已完成的不受影响
            for (int i = 0, size = futures.size(); i < size; i++)
                futures.get(i).cancel(true);
        }
    }
    // 一直等待结果，没有超时
    public <T> T invokeAny(Collection<? extends Callable<T>> tasks)
        throws InterruptedException, ExecutionException {
        try {
            return doInvokeAny(tasks, false, 0);
        } catch (TimeoutException cannotHappen) {
            assert false;
            return null;
        }
    }
    
    public <T> T invokeAny(Collection<? extends Callable<T>> tasks,
                           long timeout, TimeUnit unit)
        throws InterruptedException, ExecutionException, TimeoutException {
        return doInvokeAny(tasks, true, unit.toNanos(timeout));
    }
    //ps：源码为啥这里没注释了。。。
    //循环开启任务，循环保存结果（阻塞）
    public <T> List<Future<T>> invokeAll(Collection<? extends Callable<T>> tasks)
        throws InterruptedException {
        if (tasks == null)
            throw new NullPointerException();
        ArrayList<Future<T>> futures = new ArrayList<Future<T>>(tasks.size());
        boolean done = false;
        try {
            for (Callable<T> t : tasks) {
                RunnableFuture<T> f = newTaskFor(t);
                futures.add(f);
                execute(f);
            }
            for (int i = 0, size = futures.size(); i < size; i++) {
                Future<T> f = futures.get(i);
                //ps: 这里之所以同步的使用future.get()来阻塞，是因为
               //任务大部分是异步运行，除开任务的逻辑本身耗时足够少。若是同步，则相当于顺序执行。
                if (!f.isDone()) {
                    try {
                        f.get();
                    } catch (CancellationException ignore) {
                    } catch (ExecutionException ignore) {
                    }
                }
            }
            done = true;
            return futures;
        } finally {
            if (!done)
                for (int i = 0, size = futures.size(); i < size; i++)
                    futures.get(i).cancel(true);
        }
    }
    ps: 为什么没和上面方法一起封装，也许是为了极限的性能
    public <T> List<Future<T>> invokeAll(Collection<? extends Callable<T>> tasks,
                                         long timeout, TimeUnit unit)
        throws InterruptedException {
        if (tasks == null)
            throw new NullPointerException();
        long nanos = unit.toNanos(timeout);
        ArrayList<Future<T>> futures = new ArrayList<Future<T>>(tasks.size());
        boolean done = false;
        try {
            for (Callable<T> t : tasks)
                futures.add(newTaskFor(t));

            final long deadline = System.nanoTime() + nanos;
            final int size = futures.size();

            // Interleave time checks and calls to execute in case
            // executor doesn't have any/much parallelism.
            for (int i = 0; i < size; i++) {
                execute((Runnable)futures.get(i));
                nanos = deadline - System.nanoTime();
                if (nanos <= 0L)
                    return futures;
            }

            for (int i = 0; i < size; i++) {
                Future<T> f = futures.get(i);
                if (!f.isDone()) {
                    if (nanos <= 0L)
                        return futures;
                    try {
                        f.get(nanos, TimeUnit.NANOSECONDS);
                    } catch (CancellationException ignore) {
                    } catch (ExecutionException ignore) {
                    } catch (TimeoutException toe) {
                        return futures;
                    }
                    nanos = deadline - System.nanoTime();
                }
            }
            done = true;
            return futures;
        } finally {
            if (!done)
                for (int i = 0, size = futures.size(); i < size; i++)
                    futures.get(i).cancel(true);
        }
    }

}

```
