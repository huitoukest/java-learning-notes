---
title: "java 进阶笔记线程与并发之Executor、ExecutorService简析"
date: "2019-08-31 17:09:31"
categories: ["java进阶学习笔记"]
tags: ["executor", "executorService", "java", "concurrent", "进阶笔记"]
---

# 简介
Executor和ExecutorService都是接口，他们主要完成一个工作：执行和管理任务。
即任务怎么运行、运行的结果、运行的统一启动与停止等等的管理。

在java中，一个任务在**同步时**通常是一个方法，一个逻辑片段。
但是更多情况，指的是**异步**执行的一段数据和逻辑。通常，我们将之封装为Thread，然后运行。
但是这样有一个缺点：即任务的执行、管理 和 任务的定义耦合了在一起。

# Executor 简析
Executor 只是任务的提交和运行与任务的定义的解耦，对于任务组的管理则没有定义。

## Executor 源码

```java
/*
 * ORACLE 专有/保密. 使用以许可条款为准。
/*
 * 由Doug Lea在JCP JSR-166专家组成员的帮助下编写，
 * 并发布到公共领域，如http://creativecommons.org/publicdomain/zero/1.0/所述
 */

package java.util.concurrent;

/**
 *  这是个执行提交的Runnable任务的对象。
 * 这个接口提供了一个解耦的方法，即将任务提交和任务运行分离的机制，
 * 包括线程的使用、调度等。Executor被普通用于替代显示的线程的创建.
 * 例如，不想通过调用new Thread(new(RunnableTask())).start()来创建每个任务的话，
 * 你应该试试:
 *
 * Executor executor = anExecutor;
 * executor.execute(new RunnableTask1());
 * executor.execute(new RunnableTask2());
 * ...
 *
 * 然后，此接口并不严格要求执行必须是异步的，在一些简单情况下，
 * 一个执行者可以通过用户所在线程立即运行提交（的代码）:
 *
 * class DirectExecutor implements Executor {
 *   public void execute(Runnable r) {
 *     r.run();
 *   }}
 *
 * 更多情况则是任务运行在其它的线程，而非用户调用线程。More typically, tasks are executed in some thread other
 * 执行者为每个任务新起一个线程：
 * class ThreadPerTaskExecutor implements Executor {
 *   public void execute(Runnable r) {
 *     new Thread(r).start();
 *    }
 * }}
 *
 * 许多Executor的实现对任务的调度方式和时间施加了某种限制。Many {@code Executor} implementations impose some sort of
 * 下面的执行器将任务的提交序列提交到第二个执行器，演示了复合执行器.
 * 自带示例：SerialExecutor  ( 单独提出，参见后文）

 * Executor同包下提供了一个实现类ExecutorService，
 * 它是一个更多功能扩展的接口。类ThreadPoolExecutor提供了一个线程池实现的扩展。
 * Executors类则提供了这些扩展的一些工厂方法。
 * 
 * 内存一致性效果: Runnable的提交一定发生在开始执行之前，执行可能是在另一个线程中。
 * @since 1.5
 * @author Doug Lea
 */
public interface Executor {
    /**
     * 在将来的某个时候执行给定的命令。
     * 该命令可以在新线程、线程池或调用线程中执行，由Executor的实现决定。
     *
     * @param command the runnable task
     * @throws RejectedExecutionException 如果无法接受此任务执行
     * @throws NullPointerException if command is null
     */
    void execute(Runnable command);
}
```

## 自带示例
```java
import java.util.ArrayDeque;
import java.util.Queue;
import java.util.concurrent.Executor;
//ps: 这是一个依赖于其它执行器的一个串行执行器
//它自身主要做一个队列的FIFO的功能，通过同步使任务顺序的提交到依赖的执行器
public class SerialExecutor implements Executor {
    final Queue<Runnable> tasks = new ArrayDeque<Runnable>();
    final Executor executor;
    Runnable active;

    SerialExecutor(Executor executor) {
        this.executor = executor;
    }

    public synchronized void execute(final Runnable r) {
        tasks.offer(new Runnable() {
            public void run() {
                try {
                    r.run();
                } finally {
                    scheduleNext();
                }
            }
        });
        if (active == null) {
            scheduleNext();
        }
    }

    protected synchronized void scheduleNext() {
        if ((active = tasks.poll()) != null) {
            executor.execute(active);
        }
    }
}
```

# ExecutorService 简析

接口 java.util.concurrent.ExecutorService继承自Executor，主要扩展了对组任务的管理功能，
以及任务的执行状态跟踪。主要是通过传入Callable，返回Future来对任务的状态和结果做管理。

ps： 通过Executor的execute由于木有结果，所以其中的异常和中断需要自行处理，如果不处理，
则可能造成异常信息的丢失。
而对于ExecutorService 的submit与invoke机制，则返回Future，可以更有效的将“异步转为同步”，
异常处理可以放到调用者当前线程的结果处来处理，一般不会有异常丢失的情况发生。

## 源码
```java
package java.util.concurrent;
import ava.util.List;
import java.util.Collection;

/**
 *这是一个Executor,它提供了管理终止的方法，以及能够产生Future来跟踪一个
 * 或者多个匿名任务的进度的方法。
 *
 * 一个ExecutorService 可以被shutdown，如此它会拒绝新任务。
 * submit方法将会创建并返回一个Future对象，它可以用于终止或者等待任务的完成。
 *
 *...省略一大段
 * 
 * 内存一致性：提交必须先于任务执行，任务执行happen-before Future.get()。 
 *
 * @since 1.5
 * @author Doug Lea
 */
public interface ExecutorService extends Executor {

    /**
     * 启动有序关闭，在此过程中执行先前提交的任务，但不接受任何新任务。
     * 如果已经关闭，调用不会产生额外的效果. 
     * 此方法立即执行，不阻塞，不等待以前提交的任务完成执行，如需要，
     * 使用方法awaitTermination完成阻塞等待。
     *
     * @throws SecurityException 如果存在安全管理器，且（想）修改用户不能修改的线程。
     */
    void shutdown();

    /**
     * 尝试停止所有正在执行的任务，停止等待任务的处理，并返回正在等待执行的任务列表。 
     * 不保证一定能立即停止正在执行的任务，例如，典型的实现将通过Thread.interrupt()取消，
     * 所以无法响应中断的任何任务永远不会终止。
     * @return list of tasks that never commenced execution
     * @throws SecurityException if...
     */
    List<Runnable> shutdownNow();

    /**
     * 这里返回的是此Executor是否关闭（而不是其中的任务）
     * @return {@code true} if this executor has been shut down
     */
    boolean isShutdown();

    /**
     * 返回所有的任务是否都关闭（或完成）
     *
     * @return {@code true} if all tasks have completed following shut down
     */
    boolean isTerminated();

    /**
     * 阻塞等待，直到以下几种情况之一发送则阻塞完毕： 
     * 1. 所有任务都完成或者关闭 
     * 2. 当前线程被中断 
     * 3. 超时
     * @param timeout the maximum time to wait
     * @param unit the time unit of the timeout argument
     * @return true = 时间内任务都全部执行完毕或者终止。
     *         false = 超时前任务还未执行完毕或终止。
     * @throws InterruptedException if interrupted while waiting
     */
    boolean awaitTermination(long timeout, TimeUnit unit)
        throws InterruptedException;

    /**
     * 提交一个带有返回值的任务，返回一个未决结果的Future。
     * Future的get方法将会返回任务成功完成后的结果。
     *
     * 注意： Executors类包括一组方法，可以将一些其他常见的类似对象的对象，
     * 例如PrivilegedAction转换为Callable表单，以便它们可以提交。 
     * @param task the task to submit
     * @param <T> the type of the task's result
     * @return a Future representing pending completion of the task
     * @throws RejectedExecutionException if the task cannot be
     *         scheduled for execution
     * @throws NullPointerException if the task is null
     */
    <T> Future<T> submit(Callable<T> task);

    /**
     * Future.get()将在task执行完毕后返回给定的result对象。
     *
     * @param task the task to submit
     * @param result the result to return
     * @param <T> the type of the result
     * @return a Future representing pending completion of the task
     * @throws RejectedExecutionException if the task cannot be
     *         scheduled for execution
     * @throws NullPointerException if the task is null
     */
    <T> Future<T> submit(Runnable task, T result);

    /**
     * 提交一个可运行的任务执行，并返回一个表示该任务的未来。 成功完成时，Future.get()方法将返回null 
     *
     * @param task the task to submit
     * @return a Future representing pending completion of the task
     * @throws RejectedExecutionException if the task cannot be
     *         scheduled for execution
     * @throws NullPointerException if the task is null
     */
    Future<?> submit(Runnable task);

    /**
     * 执行给定的任务，当所有所有任务都完成时，返回一个Future列表来持有任务的状态和结果。
     * 返回的每个元素的Future.isDone is true。
     * 注意，一个完成的任务可以正常终止，也可以通过抛出异常终止。
     * 如果在执行此操作时修改了给定集合，则此方法的结果是未定义的。
     * 返回的任务的顺序就是传入的容器的迭代器元素的顺序。
     * @param tasks the collection of tasks
     * @param <T> the type of the values returned from the tasks
     * @return a list of Futures representing the tasks, in the same
     *         sequential order as produced by the iterator for the
     *         given task list, each of which has completed
     * @throws InterruptedException if interrupted while waiting, in
     *         which case unfinished tasks are cancelled
     * @throws NullPointerException if tasks or any of its elements are {@code null}
     * @throws RejectedExecutionException if any task cannot be
     *         scheduled for execution
     */
    <T> List<Future<T>> invokeAll(Collection<? extends Callable<T>> tasks)
        throws InterruptedException;

    /**
     * 当所有任务完成或者超时了，返回的列表中的每个Future.isDone is true。
     * 在返回之前，未完成的任务将会被取消。
     *
     * @param tasks the collection of tasks
     * @param timeout the maximum time to wait
     * @param unit the time unit of the timeout argument
     * @param <T> the type of the values returned from the tasks
     * @return a list of Futures representing the tasks, in the same
     *         sequential order as produced by the iterator for the
     *         given task list. If the operation did not time out,
     *         each task will have completed. If it did time out, some
     *         of these tasks will not have completed.
     * @throws InterruptedException if interrupted while waiting, in
     *         which case unfinished tasks are cancelled
     * @throws NullPointerException if tasks, any of its elements, or
     *         unit are {@code null}
     * @throws RejectedExecutionException if any task cannot be scheduled
     *         for execution
     */
    <T> List<Future<T>> invokeAll(Collection<? extends Callable<T>> tasks,
                                  long timeout, TimeUnit unit)
        throws InterruptedException;

    /**
     * 执行给定任务，返回一个完成的结果。返回前，尚未完成的任务将被取消。
     * ps：并未说明实际执行的任务数量，估计留给子类处理。
     * @param tasks the collection of tasks
     * @param <T> the type of the values returned from the tasks
     * @return the result returned by one of the tasks
     * @throws InterruptedException if interrupted while waiting
     * @throws NullPointerException if tasks or any element task
     *         subject to execution is {@code null}
     * @throws IllegalArgumentException if tasks is empty
     * @throws ExecutionException if no task successfully completes
     * @throws RejectedExecutionException if tasks cannot be scheduled
     *         for execution
     */
    <T> T invokeAny(Collection<? extends Callable<T>> tasks)
        throws InterruptedException, ExecutionException;

    /**
     * 返回在指定时间内完成的一个任务结果。
     * @param tasks the collection of tasks
     * @param timeout the maximum time to wait
     * @param unit the time unit of the timeout argument
     * @param <T> the type of the values returned from the tasks
     * @return the result returned by one of the tasks
     * @throws InterruptedException if interrupted while waiting
     * @throws NullPointerException if tasks, or unit, or any element
     *         task subject to execution is {@code null}
     * @throws TimeoutException if the given timeout elapses before
     *         any task successfully completes
     * @throws ExecutionException if no task successfully completes
     * @throws RejectedExecutionException if tasks cannot be scheduled
     *         for execution
     */
    <T> T invokeAny(Collection<? extends Callable<T>> tasks,
                    long timeout, TimeUnit unit)
        throws InterruptedException, ExecutionException, TimeoutException;
}

```

# 最后
源码来自java8.
