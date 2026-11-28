---
title: "java 进阶笔记线程与并发之ForkJoinPool简析"
date: "2019-10-21 21:49:22"
categories: ["j2se", "java进阶学习笔记"]
tags: ["java", "进阶笔记", "ForkJoinPool", "线程与并发"]
---

# 简介

ForkJoinPool是一个线程池，支持特有的的ForkJoinTask，对于ForkJoinTask任务，通过特定的for与join方法可以优化调度策略，提高效率。

# 使用

通常，我们继承使用ForkJoinTask任务的子类：

- RecursiveAction：用于没有返回结果的任务。
- RecursiveTask ：用于有返回结果的任务。

通过，在子任务类的compute()中，我们将子任务进行拆分（一般使用递归的方法，也可以循环按照range拆分），然后在此方法中fork、join返回最终结果。

一般而言，ForkJoinPool适用于计算密集型的非阻塞性任务，能够更加高效的利用cpu。

其中fork与join方法简介：

- fork **把任务推入当前工作线程的工作队列里**
- join 简单来说就是，若非 ForkJoinThread 线程中，则阻塞等待任务完成。若是在ForkJoinThread 线程，则优先完成自己工作队列中的任务，然后尝试完成其它ForkJoinThread 线程工作队列的任务。

除了每个工作线程自己拥有的工作队列以外，`ForkJoinPool` 自身也拥有工作队列，这些工作队列的用来接收由外部线程（非 `ForkJoinThread` 线程）提交过来的任务，而这些工作队列被称为 *submitting queue*.

## 测试demo

这里使用常见的循环、stream sum、传统线程池、ForkJoinPool 递归子任务的多种方法，对实际性能做一个测试。

```java
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.*;
import java.util.function.Supplier;
import java.util.stream.Collectors;
import java.util.stream.IntStream;
 
 
public class ForkJoinPoolTest {
 
 
    static class SumTask extends RecursiveTask<Integer>{
        //子任务计算的最小值,任务时间和效率和分割的尺度有关，这里测MIN_COUNT=1w时，约15ms
        //而MIN_COUNT=10w时，10ms左右.
        private static final int  MIN_COUNT = 100000;
        private List<Integer> array;
        private int start;
        private int end;
        //1=传统方式，其它=递归子任务方式
        private int type;
 
        public SumTask(List<Integer> array,int start,int end,int type){
            this.array = array;
            this.start =start;
            this.end = end;
            this.type = type;
        }
 
        //核心方法，主要功能就是
        @Override
        protected Integer compute() {
            //如果子任务大于则拆分，小于则直接计算
            if(type == 1 || end - start <= MIN_COUNT) {
                return IntStream.rangeClosed(start, end)
                        .map(it -> array.get(it))
                        .sum();
            }else {
                //折半拆分
                int mid = (start + end) / 2;
                SumTask leftTask = new SumTask(array,start,mid,2);
                SumTask right = new SumTask(array,mid + 1,end,2);
                leftTask.fork();
                right.fork();
                return leftTask.join() + right.join();
            }
        }
    }
 
    @Test
    public void test(){
        //测试计算1~500w累加结果，值会溢出超过int范围
        int maxValue = 5000000;
        List<Integer> array = IntStream.rangeClosed(1,maxValue)
                .mapToObj(it -> Integer.valueOf(it))
                .collect(Collectors.toList());
        //1.
        printTime("原始方法",() -> {
            int sum = 0;
            for(int  i = 0 ; i < maxValue ; i ++){
                sum += array.get(i);
            }
            return sum;
        });
       //2.
        printTime("steam int普通相加",() -> array.stream().mapToInt(it -> it.intValue()).sum());
        //3.
        printTime("parallel int相加",() -> array.stream().parallel().mapToInt(it -> it.intValue()).sum());
        //4.
        printTime("parallelStream相加",() -> array.parallelStream().mapToInt(it -> it.intValue()).sum());
        //5.
        printTime("reduce Integer相加",() -> array.stream().reduce((a, b) -> a + b).get());
        //6.
        printTime("parallelStream reduce Integer相加",() -> array.parallelStream().reduce((a, b) -> a + b).get());
        //7.
        printTime("forkJoinPool parallel awaitTermination groupingBy相加",() -> {
            ForkJoinPool forkJoinPool = new ForkJoinPool();
 
            Map<Integer,List<Integer>> map = array.stream()
                    .collect(Collectors.groupingBy(it -> it % 100));
            List<ForkJoinTask<Integer>> tasks = map.keySet().parallelStream().map(it -> map.get(it))
                    .map(it -> forkJoinPool.submit(new SumTask(it,0,it.size() - 1,1)))
                    .collect(Collectors.toList());
            try {
                forkJoinPool.shutdown();
                forkJoinPool.awaitTermination(1,TimeUnit.DAYS);
            } catch (InterruptedException e) {
                e.printStackTrace();
            }
            return tasks.stream().map(it -> {
                try {
                    return it.get();
                } catch (Exception e) {
                   throw new RuntimeException(e);
                }
            }).mapToInt(it -> it.intValue()).sum();
        });
 
        int minCount = 10000;
        //8.
        printTime("forkJoinPool 用awaitTermination相加",() -> {
            ForkJoinPool forkJoinPool = new ForkJoinPool();
            List<ForkJoinTask<Integer>> tasks = new ArrayList<>(maxValue);
            for(int i = 0 ; i < maxValue ; i = i + minCount){
                tasks.add(forkJoinPool.submit(new SumTask(array,i,i + minCount - 1,1)));
            }
 
            try {
                forkJoinPool.shutdown();
                forkJoinPool.awaitTermination(1,TimeUnit.DAYS);
            } catch (InterruptedException e) {
                e.printStackTrace();
            }
            return tasks.stream().map(it -> {
                try {
                    return it.get();
                } catch (Exception e) {
                    throw new RuntimeException(e);
                }
            }).mapToInt(it -> it.intValue()).sum();
        });
 
        //9.
        printTime("forkJoinPool recommend ",() -> new ForkJoinPool().invoke(new SumTask(array,0,maxValue - 1,2)));
 
    }
 
 
    private void printTime(String title,Supplier<Integer> supplier){
        long startTime = System.currentTimeMillis();
 
        int sum = supplier.get();
        System.out.print(title + ":\t");
        System.out.print(sum);
        System.out.println("\tuse time:" + (System.currentTimeMillis() - startTime));
    }
}
```

输出的结果如下：

```javascript
原始方法:    1647668640    use time:17
steam int普通相加:    1647668640    use time:18
parallel int相加:    1647668640    use time:47
parallelStream相加:    1647668640    use time:29
reduce Integer相加:    1647668640    use time:1227
parallelStream reduce Integer相加:    1647668640    use time:68
forkJoinPool parallel awaitTermination groupingBy相加:    1647668640    use time:327
forkJoinPool 用awaitTermination相加:    1647668640    use time:15
forkJoinPool recommend :    1647668640    use time:11
```

## 测试小结

- 默认的parallelStream 比直接使用的相加还慢，猜测可能与默认的任务并发拆分机制有关（可能拆分的过细，导致线程调度的时间过多）
- parallelStream比parallel方法后再操作效率高
- reduce 手动实现sum，因为每次需要对数据做拆箱操作，性能较低。
- 手动拆分任务，用传统的线程池并行完成任务的性能比单线程和系统自带的parallelStream高
- forkJoinPool 推荐的递归建立子任务的方式性能最高
- 无论是传统的手动拆分任务，还是forkJoinPool的递归拆分，任务的拆分尺度，最小任务的拿捏，都会对性能有较大的影响。

# 源码简析

以下ForkJoinPool简称为FJP，ForkJoinTask简称为FJT。

## ForkJoinTask

```java
import java.io.Serializable;
import java.util.Collection;
import java.util.List;
import java.util.RandomAccess;
import java.lang.ref.WeakReference;
import java.lang.ref.ReferenceQueue;
import java.util.concurrent.Callable;
import java.util.concurrent.CancellationException;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.Future;
import java.util.concurrent.RejectedExecutionException;
import java.util.concurrent.RunnableFuture;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;
import java.util.concurrent.locks.ReentrantLock;
import java.lang.reflect.Constructor;
 
/**
* 这是一个在FJP中运行的抽象任务类。一个FJT和线程类似，但是比线程更加轻量级。
* 在FJP中，大量的任务也许实际上只用了少量的线程，这是使用它的一些限制。
* 此类允许继承并支持实现for/join在线程中的新机制。
* 此任务中应该避免同步和阻塞方法，
*
* 若FJT中可能阻塞，则需思考如下：
 *  1. 完成少数，若任务依赖与阻塞or IO，事件类型任务别加入。
 *  2. 为尽量减少对资源的影响，任务应小;理想情况下，只执行(可能的)阻塞操作.
 *  3. 除非使用ForkJoinPool.ManagedBlocker，否则必须保证阻塞任务数量小于FJP的可用线程数，以保证性能。
*
* 用于等待完成和提取任务结果的主要方法是 join，
* 方法invoke 在语义上等价于 fork();join()，但总是尝试在当前线程中开始执行。
* invokeAll方法会并行调用任务，并自动将他们fork()；join()；
*
*
* ForkJoinTask类通常不直接子类化。而是使用 RecursiveAction用于不返回结果的大多数计算，
* RecursiveTask用于返回结果的计算，CountedCompleter用于那些完成的操作触发其他操作的计算.
*
* 方法join仅适用于非循环依赖的任务，即计算行为可描述为有向无环图（DAG）。否则可能会死锁。
* 但是此框架支持其它方法和技术，如Phaser、helpQuiesce、complete，这些方法可以用于非静态的DAG问题构造。
* 为了支持这些方法可以使用setForkJoinTaskTag、compareAndSetForkJoinTaskTag等方法。
*
* FJT应该执行相对小的计算量，通过递归分解为小任务，一般分为100 到 1w个基本计算步奏的任务量。
* 任务太大会导致并行无法提高吞吐量，太小会导致内存和内部任务维护开销超过处理开销。
*
* 这个类为Runnable和Callable提供了adapt方法，当FJT与其他类型的任务混合执行时，
* 可以使用这些方法。当所有任务都是这种形式时，考虑使用在asyncMode中构造的池。
*
* @since 1.7
* @author Doug Lea
*/
public abstract class ForkJoinTask<V> implements Future<V>, Serializable {
 
    /*
     * 这个类的方法分为三类：
     * 1. 基本状态的维护.
     * 2. 执行和等待完成.
     * 3. 用户级方法，这些方法还报告结果。
     */
 
    /*
     * status字段保存了运行的状态字节位打包到了一个int中，
     * 以最小化内存占用并确保原子性（通过CAS)。
     * 状态初始值为0，在完成之前接收非负的值，在此基础上，Status(用DONE_MASK进行处理)持有NORMAL、
     * cancel或exception值.其他线程正在进行阻塞等待的任务将SIGNAL bit.
     * 完成一个被盗的任务与信号集唤醒任何服务员通过notifyAll。
     * 尽管在某些目的上不是最优的，但是我们使用基本的内置wait/notify来
     * 利用jvm中的“monitor inflation”，否则我们将需要模拟它，
     * 以避免为每个任务增加更多的簿记开销.我们希望这些监视器是“胖”的，
     * 即，不要使用偏向锁或thin-lock技术，所以使用一些奇怪的编码习惯来避免它们，
     * 主要是通过安排每个同步块执行一个等待、notifyAll或两者都执行。
     *
     * 这些控制位只占用状态字段的上半部分(16位)。较低的位用于用户定义的标记。
     */
 
    /** The run status of this task */
    volatile int status; // accessed directly by pool and workers
    static final int DONE_MASK   = 0xf0000000;  // mask out non-completion bits
    static final int NORMAL      = 0xf0000000;  // must be negative
    static final int CANCELLED   = 0xc0000000;  // must be < NORMAL
    static final int EXCEPTIONAL = 0x80000000;  // must be < CANCELLED
    static final int SIGNAL      = 0x00010000;  // must be >= 1 << 16
    static final int SMASK       = 0x0000ffff;  // short bits for tags
 
    /**
     * 标记完成,并唤醒等待加入此任务的线程.
     *
     * @param completion 值是下列之一： NORMAL, CANCELLED, EXCEPTIONAL
     * @return completion status on exit
     */
    private int setCompletion(int completion) {
        for (int s;;) {
            //负数表示未完成
            if ((s = status) < 0)
                return s;
            //s | completion,应该是保留completion和系统的高位的控制位状态
            if (U.compareAndSwapInt(this, STATUS, s, s | completion)) {
                //高位有值，表示完成:NORMAL, CANCELLED, EXCEPTIONAL
                //ps：这里应该是用来判断是否是SIGNAL，是则唤醒
                if ((s >>> 16) != 0)
                    synchronized (this) { notifyAll(); }
                return completion;
            }
        }
    }
 
    /**
     * 偷取任务执行的主要方法。除非完成，调用exec和记录完成时的状态，
     * 否则不等待完成。
     *
     * @return status on exit from this method
     */
    final int doExec() {
        int s; boolean completed;
        if ((s = status) >= 0) {
            try {
                completed = exec();
            } catch (Throwable rex) {
                return setExceptionalCompletion(rex);
            }
            if (completed)
                s = setCompletion(NORMAL);
        }
        return s;
    }
 
    /**
     * 如果未完成，则设计为SIGNAL状态，并执行Object.wait(timeout).
     * 无法得知任务在结束时是否完成，忽略中断。
     *
     * @param timeout using Object.wait conventions.
     */
    final void internalWait(long timeout) {
        int s;
        //ps: 若未完成，这里将之CAS设置status为SIGNAL状态
        if ((s = status) >= 0 && // force completer to issue notify
            U.compareAndSwapInt(this, STATUS, s, s | SIGNAL)) {
            synchronized (this) {
                if (status >= 0)
                    try { wait(timeout); } catch (InterruptedException ie) { }
                else
                    notifyAll();
            }
        }
    }
 
    /**
     * 直到完成之前，阻塞非工作线程.
     * @return status upon completion
     */
    private int externalAwaitDone() {
        //ps: 特殊处理CountedCompleter线程
        int s = ((this instanceof CountedCompleter) ? // try helping
                 ForkJoinPool.common.externalHelpComplete(
                     (CountedCompleter<?>)this, 0) :
                 ForkJoinPool.common.tryExternalUnpush(this) ? doExec() : 0);
        if (s >= 0 && (s = status) >= 0) {
            boolean interrupted = false;
            do {
                if (U.compareAndSwapInt(this, STATUS, s, s | SIGNAL)) {
                    synchronized (this) {
                        if (status >= 0) {
                            try {
                                //一直等待，直到唤醒
                                wait(0L);
                            } catch (InterruptedException ie) {
                                interrupted = true;
                            }
                        }
                        else
                            notifyAll();
                    }
                }
            } while ((s = status) >= 0);
            if (interrupted)
                Thread.currentThread().interrupt();
        }
        return s;
    }
 
    /**
     * Blocks a non-worker-thread until completion or interruption.
     */
    private int externalInterruptibleAwaitDone() throws InterruptedException {
        int s;
        if (Thread.interrupted())
            throw new InterruptedException();
        if ((s = status) >= 0 &&
            (s = ((this instanceof CountedCompleter) ?
                  ForkJoinPool.common.externalHelpComplete(
                      (CountedCompleter<?>)this, 0) :
                  ForkJoinPool.common.tryExternalUnpush(this) ? doExec() :
                  0)) >= 0) {
            while ((s = status) >= 0) {
                if (U.compareAndSwapInt(this, STATUS, s, s | SIGNAL)) {
                    synchronized (this) {
                        if (status >= 0)
                            wait(0L);
                        else
                            notifyAll();
                    }
                }
            }
        }
        return s;
    }
 
    /**
     * 实现join、get、quietlyJoin。直接处理已经完成、外部等待和unfork+exec的情况。
     * 其他的转发到ForkJoinPool.awaitJoin。
     * ps:
     *  1. 小于0，已经完成，直接返回状态。
     *  2. 当前线程若是工作线程，调用其tryUnpush(this)方法，若返回true，
     *     调用 s = doExec()，若 s < 0，直接返回wt.pool.awaitJoin(w, this, 0L) 。
     *  3. 若当前线程不是工作线程：externalAwaitDone()。
     * @return status upon completion
     */
    private int doJoin() {
        int s; Thread t; ForkJoinWorkerThread wt; ForkJoinPool.WorkQueue w;
        return (s = status) < 0 ? s :
            ((t = Thread.currentThread()) instanceof ForkJoinWorkerThread) ?
            (w = (wt = (ForkJoinWorkerThread)t).workQueue).
            tryUnpush(this) && (s = doExec()) < 0 ? s :
            wt.pool.awaitJoin(w, this, 0L) :
            externalAwaitDone();
    }
 
    /**
     * Implementation for invoke, quietlyInvoke.
     * ps: 没结束的工作线程，就在队列中加入任务执行；否则阻塞等待
     * @return status upon completion
     */
    private int doInvoke() {
        int s; Thread t; ForkJoinWorkerThread wt;
        return (s = doExec()) < 0 ? s :
            ((t = Thread.currentThread()) instanceof ForkJoinWorkerThread) ?
            (wt = (ForkJoinWorkerThread)t).pool.
            awaitJoin(wt.workQueue, this, 0L) :
            externalAwaitDone();
    }
 
    // Exception table support
 
    /**
     * 任务引发的异常表，以启用调用者的报告。
     * 因为异常很少，所以我们不直接将它们保存在task对象中，
     * 而是使用weak ref表。注意，取消异常不会出现在表中，而是记录为状态值。
     *
     * Note: 这些静态数据在下面的静态块中初始化.
     */
    private static final ExceptionNode[] exceptionTable;
    private static final ReentrantLock exceptionTableLock;
    private static final ReferenceQueue<Object> exceptionTableRefQueue;
 
    /**
     * Fixed capacity for exceptionTable.
     * 固定容量的异常表
     */
    private static final int EXCEPTION_MAP_CAPACITY = 32;
 
    /**
     * Key-value nodes for exception table.  The chained hash table
     * uses identity comparisons, full locking, and weak references
     * for keys. The table has a fixed capacity because it only
     * maintains task exceptions long enough for joiners to access
     * them, so should never become very large for sustained
     * periods. However, since we do not know when the last joiner
     * completes, we must use weak references and expunge them. We do
     * so on each operation (hence full locking). Also, some thread in
     * any ForkJoinPool will call helpExpungeStaleExceptions when its
     * pool becomes isQuiescent.
     */
    static final class ExceptionNode extends WeakReference<ForkJoinTask<?>> {
        final Throwable ex;
        ExceptionNode next;
        final long thrower;  // 使用id，而不是依赖来避免弱循环。
        final int hashCode;  // 在弱ref消失之前存储任务hashCode
        ExceptionNode(ForkJoinTask<?> task, Throwable ex, ExceptionNode next) {
            super(task, exceptionTableRefQueue);
            this.ex = ex;
            this.next = next;
            this.thrower = Thread.currentThread().getId();
            this.hashCode = System.identityHashCode(task);
        }
    }
 
    /**
     * 记录异常，并设置状态。
     * @return status on exit
     */
    final int recordExceptionalCompletion(Throwable ex) {
        int s;
        if ((s = status) >= 0) {
            int h = System.identityHashCode(this);
            final ReentrantLock lock = exceptionTableLock;
            lock.lock();
            try {
                expungeStaleExceptions();
                ExceptionNode[] t = exceptionTable;
                int i = h & (t.length - 1);
                for (ExceptionNode e = t[i]; ; e = e.next) {
                    if (e == null) {
                        t[i] = new ExceptionNode(this, ex, t[i]);
                        break;
                    }
                    if (e.get() == this) // already present
                        break;
                }
            } finally {
                lock.unlock();
            }
            s = setCompletion(EXCEPTIONAL);
        }
        return s;
    }
 
    /**
     * 记录异常并可能传播。
     *
     * @return status on exit
     */
    private int setExceptionalCompletion(Throwable ex) {
        int s = recordExceptionalCompletion(ex);
        if ((s & DONE_MASK) == EXCEPTIONAL)
            internalPropagateException(ex);
        return s;
    }
 
    /**
     * 预留钩子方法：带有完成器的的任务的异常传播支持。
     */
    void internalPropagateException(Throwable ex) {
    }
 
    /**
     * Cancels，忽略cancel引发的任何异常。
     * 在工作程序和池关闭期间使用。Cancel被指定不抛出任何异常，
     * 但是如果它抛出任何异常，我们在关闭期间没有追索权，所以要防范这种情况。
     */
    static final void cancelIgnoringExceptions(ForkJoinTask<?> t) {
        if (t != null && t.status >= 0) {
            try {
                t.cancel(false);
            } catch (Throwable ignore) {
            }
        }
    }
 
    /**
     * Removes exception node and clears status.
     */
    private void clearExceptionalCompletion() {
        int h = System.identityHashCode(this);
        final ReentrantLock lock = exceptionTableLock;
        lock.lock();
        try {
            ExceptionNode[] t = exceptionTable;
            int i = h & (t.length - 1);
            ExceptionNode e = t[i];
            ExceptionNode pred = null;
            while (e != null) {
                ExceptionNode next = e.next;
                if (e.get() == this) {
                    if (pred == null)
                        t[i] = next;
                    else
                        pred.next = next;
                    break;
                }
                pred = e;
                e = next;
            }
            expungeStaleExceptions();
            status = 0;
        } finally {
            lock.unlock();
        }
    }
 
    /**
     * 返回给定任务的可重掷异常(如果可用)。
     * 为了提供准确的堆栈跟踪，如果当前线程没有抛出异常，
     * 我们将尝试创建一个与抛出异常类型相同的新异常，
     * 但是将记录的异常作为其原因。如果没有这样的构造函数，
     * 我们将尝试使用无arg构造函数，后面跟着initCause，以达到相同的效果。
     * 如果这些方法都不适用，或者由于其他异常导致的任何失败，
     * 我们将返回记录的异常，这仍然是正确的，尽管它可能包含误导的堆栈跟踪。
     *
     * @return the exception, or null if none
     */
    private Throwable getThrowableException() {
        if ((status & DONE_MASK) != EXCEPTIONAL)
            return null;
        int h = System.identityHashCode(this);
        ExceptionNode e;
        final ReentrantLock lock = exceptionTableLock;
        lock.lock();
        try {
            expungeStaleExceptions();
            ExceptionNode[] t = exceptionTable;
            e = t[h & (t.length - 1)];
            while (e != null && e.get() != this)
                e = e.next;
        } finally {
            lock.unlock();
        }
        Throwable ex;
        if (e == null || (ex = e.ex) == null)
            return null;
        if (e.thrower != Thread.currentThread().getId()) {
            Class<? extends Throwable> ec = ex.getClass();
            try {
                Constructor<?> noArgCtor = null;
                Constructor<?>[] cs = ec.getConstructors();// public ctors only
                for (int i = 0; i < cs.length; ++i) {
                    Constructor<?> c = cs[i];
                    Class<?>[] ps = c.getParameterTypes();
                    if (ps.length == 0)
                        noArgCtor = c;
                    else if (ps.length == 1 && ps[0] == Throwable.class) {
                        Throwable wx = (Throwable)c.newInstance(ex);
                        return (wx == null) ? ex : wx;
                    }
                }
                if (noArgCtor != null) {
                    Throwable wx = (Throwable)(noArgCtor.newInstance());
                    if (wx != null) {
                        wx.initCause(ex);
                        return wx;
                    }
                }
            } catch (Exception ignore) {
            }
        }
        return ex;
    }
 
    /**
     * 拉取腐化陈旧的依赖并移除，仅在持有锁时调用。
     */
    private static void expungeStaleExceptions() {
        for (Object x; (x = exceptionTableRefQueue.poll()) != null;) {
            if (x instanceof ExceptionNode) {
                int hashCode = ((ExceptionNode)x).hashCode;
                ExceptionNode[] t = exceptionTable;
                int i = hashCode & (t.length - 1);
                ExceptionNode e = t[i];
                ExceptionNode pred = null;
                while (e != null) {
                    ExceptionNode next = e.next;
                    if (e == x) {
                        if (pred == null)
                            t[i] = next;
                        else
                            pred.next = next;
                        break;
                    }
                    pred = e;
                    e = next;
                }
            }
        }
    }
 
    /**
     * If lock is available, poll stale refs and remove them.
     * 在FJP变得不活跃时调用。（ps:任务数量逐渐小于内置线程数量时）
     */
    static final void helpExpungeStaleExceptions() {
        final ReentrantLock lock = exceptionTableLock;
        if (lock.tryLock()) {
            try {
                expungeStaleExceptions();
            } finally {
                lock.unlock();
            }
        }
    }
 
    /**
     * A version of "sneaky throw" to relay exceptions
     */
    static void rethrow(Throwable ex) {
        if (ex != null)
            ForkJoinTask.<RuntimeException>uncheckedThrow(ex);
    }
 
    /**
     * 静谧抛出异常的一部分。
     * 依赖泛型限制来逃避编译器关于重新抛出未检查异常的限制。
     */
    @SuppressWarnings("unchecked") static <T extends Throwable>
        void uncheckedThrow(Throwable t) throws T {
        throw (T)t; // rely on vacuous cast
    }
 
    /**
     * 抛出与给定状态关联的异常(如果有)。
     */
    private void reportException(int s) {
        if (s == CANCELLED)
            throw new CancellationException();
        if (s == EXCEPTIONAL)
            rethrow(getThrowableException());
    }
 
    // public methods
 
    /**
     * 安排在当前任务运行的池中异步执行此任务(如果适用)，或者使用FJP#commonPool()
     * (如果不使用 inForkJoinPool)。除非一个任务已经完成且被重新初始化，不然fork一个
     * 任务多次就是错误的。除非在调用join或相关方法之前，或者调用isDone返回true，
     * 否则对该任务的状态或它所操作的任何数据的后续修改不一定能被执行它的线程一致地观察到。
     * ps： 这里实际上就是
     *  1. 若是工作线程则加入工作线程的任务队列
     *  2. 否则externalPush(this),加入到提交任务队列;
     * @return {@code this}, to simplify usage
     */
    public final ForkJoinTask<V> fork() {
        Thread t;
        if ((t = Thread.currentThread()) instanceof ForkJoinWorkerThread)
            ((ForkJoinWorkerThread)t).workQueue.push(this);
        else
            ForkJoinPool.common.externalPush(this);
        return this;
    }
 
    /**
     * 当isDoen已经完成，返回计算的结果。此方法与get()的不同之处在于，
     * 异常的完成结果是RuntimeException或Error，
     * 而不是ExecutionException，并且调用线程的中断不会通过抛出
     * InterruptedException导致方法突然返回。
     *
     * @return the computed result
     */
    public final V join() {
        int s;
        if ((s = doJoin() & DONE_MASK) != NORMAL)
            reportException(s);
        return getRawResult();
    }
 
    /**
     * 开始执行此任务，如果需要，等待其完成，并返回其结果，
     * 如果底层计算执行此任务，则抛出(未选中的) RuntimeException或Error。
     *
     * @return the computed result
     */
    public final V invoke() {
        int s;
        if ((s = doInvoke() & DONE_MASK) != NORMAL)
            reportException(s);
        return getRawResult();
    }
 
    /**
     * fork给定的任务，当为每个任务保存 isDone或遇到(未选中的)异常时返回，
     * 在这种情况下，将重新抛出异常。如果多个任务遇到异常，则此方法将抛出这些异常中的任何一个。
     * 如果任何任务遇到异常，另一个任务可能被取消。但是，个别任务的执行状态不能在异常返回时得到保证。
     * 可以使用 getException()和相关方法获取每个任务的状态，
     * 以检查它们是否已被取消、正常完成或异常完成或未处理。
     *
     * @param t1 the first task
     * @param t2 the second task
     * @throws NullPointerException if any task is null
     */
    public static void invokeAll(ForkJoinTask<?> t1, ForkJoinTask<?> t2) {
        int s1, s2;
        t2.fork();
        if ((s1 = t1.doInvoke() & DONE_MASK) != NORMAL)
            t1.reportException(s1);
        if ((s2 = t2.doJoin() & DONE_MASK) != NORMAL)
            t2.reportException(s2);
    }
 
    /**
     * ps： 同invokeAll。
     * 其中一个调用doInvoke() 来阻塞当前线程并等待任务(整个池中)完成，其余的调用fork()；
     * 相当于fork来加入任务到工作队列。
     * @param tasks the tasks
     * @throws NullPointerException if any task is null
     */
    public static void invokeAll(ForkJoinTask<?>... tasks) {
        Throwable ex = null;
        int last = tasks.length - 1;
        for (int i = last; i >= 0; --i) {
            ForkJoinTask<?> t = tasks[i];
            if (t == null) {
                if (ex == null)
                    ex = new NullPointerException();
            }
            else if (i != 0)
                t.fork();
            else if (t.doInvoke() < NORMAL && ex == null)
                ex = t.getException();
        }
        for (int i = 1; i <= last; ++i) {
            ForkJoinTask<?> t = tasks[i];
            if (t != null) {
                if (ex != null)
                    t.cancel(false);
                else if (t.doJoin() < NORMAL)
                    ex = t.getException();
            }
        }
        if (ex != null)
            rethrow(ex);
    }
 
    /**
     *
     * @param tasks the collection of tasks
     * @param <T> the type of the values returned from the tasks
     * @return 任务参数，以简化使用
     * @throws NullPointerException if tasks or any element are null
     */
    public static <T extends ForkJoinTask<?>> Collection<T> invokeAll(Collection<T> tasks) {
        if (!(tasks instanceof RandomAccess) || !(tasks instanceof List<?>)) {
            invokeAll(tasks.toArray(new ForkJoinTask<?>[tasks.size()]));
            return tasks;
        }
        @SuppressWarnings("unchecked")
        List<? extends ForkJoinTask<?>> ts =
            (List<? extends ForkJoinTask<?>>) tasks;
        Throwable ex = null;
        int last = ts.size() - 1;
        for (int i = last; i >= 0; --i) {
            ForkJoinTask<?> t = ts.get(i);
            if (t == null) {
                if (ex == null)
                    ex = new NullPointerException();
            }
            else if (i != 0)
                t.fork();
            else if (t.doInvoke() < NORMAL && ex == null)
                ex = t.getException();
        }
        for (int i = 1; i <= last; ++i) {
            ForkJoinTask<?> t = ts.get(i);
            if (t != null) {
                if (ex != null)
                    t.cancel(false);
                else if (t.doJoin() < NORMAL)
                    ex = t.getException();
            }
        }
        if (ex != null)
            rethrow(ex);
        return tasks;
    }
 
    /**
     * 如果任务已经完成或者无法被取消，则操作会失败。若成功，且此任务尚未启动，则
     * 禁止此任务执行。该方法成功返回后，除非对任务重新初始化，否则调用isCancel、
     * isDone、cancel、join等将会导致CancellationException.
     *
     * 个方法可以在子类中被重写，但是如果是这样，仍然必须确保这些属性保持不变。
     * 特别是，cancel方法本身不能抛出异常。
     *
     * 此方法被设计为由其他任务调用。要终止当前任务，只需从其计算方法返回
     * 或抛出未检查异常，或调用 completeexception (Throwable)。
     *
     * @param 这个值在默认实现中没有效果，因为中断不用于控制取消.
     * @return {@code true} if this task is now cancelled
     */
    public boolean cancel(boolean mayInterruptIfRunning) {
        return (setCompletion(CANCELLED) & DONE_MASK) == CANCELLED;
    }
 
    public final boolean isDone() {
        return status < 0;
    }
 
    public final boolean isCancelled() {
        return (status & DONE_MASK) == CANCELLED;
    }
 
    /**
     * Returns {@code true} if this task threw an exception or was cancelled.
     *
     * @return {@code true} if this task threw an exception or was cancelled
     */
    public final boolean isCompletedAbnormally() {
        return status < NORMAL;
    }
 
    /**
     * Returns {@code true} if this task completed without throwing an
     * exception and was not cancelled.
     *
     * @return {@code true} if this task completed without throwing an
     * exception and was not cancelled
     */
    public final boolean isCompletedNormally() {
        return (status & DONE_MASK) == NORMAL;
    }
 
    /**
     * Returns the exception thrown by the base computation, or a
     * {@code CancellationException} if cancelle，
     * 如果task尚未完成，返回null
     *
     * @return the exception, or {@code null} if none
     */
    public final Throwable getException() {
        int s = status & DONE_MASK;
        return ((s >= NORMAL)    ? null :
                (s == CANCELLED) ? new CancellationException() :
                getThrowableException());
    }
 
    /**
     *
     * 完成任务的异常，若尚未终止或者取消，会导致join和相关操作抛出给定异常。
     * 此方法可以用于指定异常在匿名任务中，或者强制完成可能无法完成的任务。
     * 这个方法是可覆盖的，但是被覆盖的版本必须调用super实现来维护保证。
     * @param ex the exception to throw. If this exception is not a
     * {@code RuntimeException} or {@code Error}, the actual exception
     * thrown will be a {@code RuntimeException} with cause {@code ex}.
     */
    public void completeExceptionally(Throwable ex) {
        setExceptionalCompletion((ex instanceof RuntimeException) ||
                                 (ex instanceof Error) ? ex :
                                 new RuntimeException(ex));
    }
 
    /**
     * 将方法设置为完成状态，如果尚未中止或取消，则返回给定值，
     * 作为随后调用join和相关操作的结果。
     * ps： 手动设置任务的返回值
     *
     * @param value the result value for this task
     */
    public void complete(V value) {
        try {
            setRawResult(value);
        } catch (Throwable rex) {
            setExceptionalCompletion(rex);
            return;
        }
        setCompletion(NORMAL);
    }
 
    /**
     * 静默完成，未手动设置返回值
     *
     * @since 1.8
     */
    public final void quietlyComplete() {
        setCompletion(NORMAL);
    }
 
    /**
     * 如果需要，等待计算完成，然后检索其结果。
     *
     * @return the computed result
     * @throws CancellationException if the computation was cancelled
     * @throws ExecutionException if the computation threw an
     * exception
     * @throws InterruptedException if the current thread is not a
     * member of a ForkJoinPool and was interrupted while waiting
     */
    public final V get() throws InterruptedException, ExecutionException {
        int s = (Thread.currentThread() instanceof ForkJoinWorkerThread) ?
            doJoin() : externalInterruptibleAwaitDone();
        Throwable ex;
        if ((s &= DONE_MASK) == CANCELLED)
            throw new CancellationException();
        if (s == EXCEPTIONAL && (ex = getThrowableException()) != null)
            throw new ExecutionException(ex);
        return getRawResult();
    }
 
    /**
     * Waits if necessary for at most the given time for the computation
     * to complete, and then retrieves its result, if available.
     *
     * @param timeout the maximum time to wait
     * @param unit the time unit of the timeout argument
     * @return the computed result
     * @throws CancellationException if the computation was cancelled
     * @throws ExecutionException if the computation threw an
     * exception
     * @throws InterruptedException if the current thread is not a
     * member of a ForkJoinPool and was interrupted while waiting
     * @throws TimeoutException if the wait timed out
     */
    public final V get(long timeout, TimeUnit unit)
        throws InterruptedException, ExecutionException, TimeoutException {
        int s;
        long nanos = unit.toNanos(timeout);
        if (Thread.interrupted())
            throw new InterruptedException();
        if ((s = status) >= 0 && nanos > 0L) {
            long d = System.nanoTime() + nanos;
            long deadline = (d == 0L) ? 1L : d; // avoid 0
            Thread t = Thread.currentThread();
            if (t instanceof ForkJoinWorkerThread) {
                ForkJoinWorkerThread wt = (ForkJoinWorkerThread)t;
                s = wt.pool.awaitJoin(wt.workQueue, this, deadline);
            }
            else if ((s = ((this instanceof CountedCompleter) ?
                           ForkJoinPool.common.externalHelpComplete(
                               (CountedCompleter<?>)this, 0) :
                           ForkJoinPool.common.tryExternalUnpush(this) ?
                           doExec() : 0)) >= 0) {
                long ns, ms; // measure in nanosecs, but wait in millisecs
                while ((s = status) >= 0 &&
                       (ns = deadline - System.nanoTime()) > 0L) {
                    if ((ms = TimeUnit.NANOSECONDS.toMillis(ns)) > 0L &&
                        U.compareAndSwapInt(this, STATUS, s, s | SIGNAL)) {
                        synchronized (this) {
                            if (status >= 0)
                                wait(ms); // OK to throw InterruptedException
                            else
                                notifyAll();
                        }
                    }
                }
            }
        }
        if (s >= 0)
            s = status;
        if ((s &= DONE_MASK) != NORMAL) {
            Throwable ex;
            if (s == CANCELLED)
                throw new CancellationException();
            if (s != EXCEPTIONAL)
                throw new TimeoutException();
            if ((ex = getThrowableException()) != null)
                throw new ExecutionException(ex);
        }
        return getRawResult();
    }
 
    /**
     * join此任务，而不返回其结果或抛出其异常。当某些任务已被取消或已中止时，
     * 处理任务集合时，此方法可能有用。
     */
    public final void quietlyJoin() {
        doJoin();
    }
 
    /**
     * 开始执行此任务，并在必要时等待其完成，而不返回结果或抛出异常.
     */
    public final void quietlyInvoke() {
        doInvoke();
    }
 
    /**
     * 可能会执行任务，直到托管当前任务的池 ForkJoinPool#isQuiescent是静默的。
     * 这种方法可能在许多任务fork但没有显式join的设计中使用，因此在处理所有任务之前执行它们。
     */
    public static void helpQuiesce() {
        Thread t;
        if ((t = Thread.currentThread()) instanceof ForkJoinWorkerThread) {
            ForkJoinWorkerThread wt = (ForkJoinWorkerThread)t;
            wt.pool.helpQuiescePool(wt.workQueue);
        }
        else
            ForkJoinPool.quiesceCommonPool();
    }
 
    /**
     * 重置任务状态，一般用于在循环中执行预构造的子任务树时。
     *
     * 完成此方法后，isDone()返回false， getException() 返回null。
     * 但是，getRawResult 返回的值不受影响。要清除这个值，可以调用setRawResult(null)。
     */
    public void reinitialize() {
        if ((status & DONE_MASK) == EXCEPTIONAL)
            clearExceptionalCompletion();
        else
            status = 0;
    }
 
    /**
     * 返回当前持有的任务执行的池，如果该任务在任何fork连接池之外执行，则返回null。
     *
     * @see #inForkJoinPool
     * @return the pool, or {@code null} if none
     */
    public static ForkJoinPool getPool() {
        Thread t = Thread.currentThread();
        return (t instanceof ForkJoinWorkerThread) ?
            ((ForkJoinWorkerThread) t).pool : null;
    }
 
    /**
     * @return {@code true} if the current thread is a {@link
     * ForkJoinWorkerThread} executing as a ForkJoinPool computation,
     * or {@code false} otherwise
     */
    public static boolean inForkJoinPool() {
        return Thread.currentThread() instanceof ForkJoinWorkerThread;
    }
 
    /**
     * 试图取消此任务的执行计划。如果该任务是当前线程最近fork的任务，
     * 并且尚未在另一个线程中开始执行，则此方法通常会成功(但不能保证)。
     * 这种方法在安排任务的替代local processing可能很有用，
     * 这些任务本来可以被窃取，但没有被窃取。
     * ps: 该任务不再被线程池调度,则开发者可以自行安排其执行的线程和时机。
     *
     * @return {@code true} if unforked
     */
    public boolean tryUnfork() {
        Thread t;
        return (((t = Thread.currentThread()) instanceof ForkJoinWorkerThread) ?
                ((ForkJoinWorkerThread)t).workQueue.tryUnpush(this) :
                ForkJoinPool.common.tryExternalUnpush(this));
    }
 
    /**
     * 返回当前线程forked但是未执行完毕的任务大致数量。
     * 这个值对于是fork其他任务的启发式决策可能很有用。
     * ps： 若是工作线程，则使用工作线程队列数量。
     * 否则使用提交队列数量。
     * @return the number of tasks
     */
    public static int getQueuedTaskCount() {
        Thread t; ForkJoinPool.WorkQueue q;
        if ((t = Thread.currentThread()) instanceof ForkJoinWorkerThread)
            q = ((ForkJoinWorkerThread)t).workQueue;
        else
            q = ForkJoinPool.commonSubmitterQueue();
        return (q == null) ? 0 : q.queueSize();
    }
 
    /**
     * ps：返回工作线程持有的提交任务队列的任务估计值，用于forkjoin池中任务分发
     * 的启发式决策。
     *
     * @return the surplus number of tasks, which may be negative
     */
    public static int getSurplusQueuedTaskCount() {
        return ForkJoinPool.getSurplusQueuedTaskCount();
    }
 
    // (待)扩展方法
 
    /**
     * 返回将由join返回的结果，即使该任务异常完成，
     * 如果不知道该任务已经完成，则返回 null。此方法旨在帮助调试，并支持扩展。
     * 不鼓励在任何其他情况下使用它。
     *
     * @return the result, or {@code null} if not completed
     */
    public abstract V getRawResult();
 
    /**
     * 强制返回给定的值。此方法旨在支持扩展，一般不应以其他方式调用。
     * @param value the value
     */
    protected abstract void setRawResult(V value);
 
    /**
     * 立即执行此任务的基本操作，如果从此方法返回时保证该任务已正常完成，
     * 则返回true。否则，此方法可能返回false，以指示此任务不一定完成(或不知道是否完成)，
     * 例如在需要显式调用完成方法的异步操作中。此方法还可能抛出(未选中的)异常，
     * 以指示异常退出。此方法旨在支持扩展，一般不应以其他方式调用。
     *
     * @return {@code true} if this task is known to have completed normally
     */
    protected abstract boolean exec();
 
    /**
     * 返回由当前线程排队但尚未执行的任务，但不会取消调度或执行该任务(如果
     * 当前线程是立即可用的)。不能保证此任务将在接下来实际轮询或执行。
     * 相反，即使任务存在，但如果不与其他线程争用，则无法访问该方法，该方法也
     * 可能返回null。这种方法主要是为了支持扩展而设计的，否则不太可能有用。
     *
     * @return the next task, or {@code null} if none are available
     */
    protected static ForkJoinTask<?> peekNextLocalTask() {
        Thread t; ForkJoinPool.WorkQueue q;
        if ((t = Thread.currentThread()) instanceof ForkJoinWorkerThread)
            q = ((ForkJoinWorkerThread)t).workQueue;
        else
            q = ForkJoinPool.commonSubmitterQueue();
        return (q == null) ? null : q.peek();
    }
 
    /**
     * 取消调度并返回当前线程排队但尚未执行的下一个任务(如果当前线程在fork join池中运
     * 行)，而不执行该任务。这种方法主要是为了支持扩展而设计的，否则不太可能有用
     *
     * @return the next task, or {@code null} if none are available
     */
    protected static ForkJoinTask<?> pollNextLocalTask() {
        Thread t;
        return ((t = Thread.currentThread()) instanceof ForkJoinWorkerThread) ?
            ((ForkJoinWorkerThread)t).workQueue.nextLocalTask() :
            null;
    }
 
    /**
     * 如果当前线程在一个FJP中运行，取消调度并返回，而不执行当前线程排队但尚未
     * 执行的下一个任务(如果有一个任务可用)，或者如果没有可用任务(如果可用，
     * 则由其他线程分叉的任务)。可用性可能是暂时的，因此{@code null}结果并
     * 不一定意味着此任务正在操作的池处于静止状态。这种方法主要是为了支持
     * 扩展而设计的，否则不太可能有用。
     *
     * @return a task, or {@code null} if none are available
     */
    protected static ForkJoinTask<?> pollTask() {
        Thread t; ForkJoinWorkerThread wt;
        return ((t = Thread.currentThread()) instanceof ForkJoinWorkerThread) ?
            (wt = (ForkJoinWorkerThread)t).pool.nextTaskFor(wt.workQueue) :
            null;
    }
 
    // tag operations
 
    /**
     * @return the tag for this task
     * @since 1.8
     */
    public final short getForkJoinTaskTag() {
        return (short)status;
    }
 
    /**
     * Atomically sets the tag value for this task.
     * @param tag the tag value
     * @return the previous value of the tag
     * @since 1.8
     */
    public final short setForkJoinTaskTag(short tag) {
        for (int s;;) {
            if (U.compareAndSwapInt(this, STATUS, s = status,
                                    (s & ~SMASK) | (tag & SMASK)))
                return (short)s;
        }
    }
 
    /**
     * 原子地、有条件地设置此任务的标记值。在其他应用程序中，标记可用于在图形上操
     * 作的任务中作为访问标记，比如在处理之前检查方法:{@code if  (task.compareAndSetForkJoinTaskTag(((short)0， (short)1))}，
     * 否则将退出，因为节点已经被访问。
     * @param e the expected tag value
     * @param tag the new tag value
     * @return {@code true} if successful; i.e., the current value was
     * equal to e and is now tag.
     * @since 1.8
     */
    public final boolean compareAndSetForkJoinTaskTag(short e, short tag) {
        for (int s;;) {
            if ((short)(s = status) != e)
                return false;
            if (U.compareAndSwapInt(this, STATUS, s,
                                    (s & ~SMASK) | (tag & SMASK)))
                return true;
        }
    }
 
    /**
     * 当在ForkJoinPool中使用RunnableFuture时，它实现了与AbstractExecutorService约束的兼容.
     * ps: 就是个适配器
     */
    static final class AdaptedRunnable<T> extends ForkJoinTask<T>
        implements RunnableFuture<T> {
        final Runnable runnable;
        T result;
        AdaptedRunnable(Runnable runnable, T result) {
            if (runnable == null) throw new NullPointerException();
            this.runnable = runnable;
            this.result = result; // OK to set this even before completion
        }
        public final T getRawResult() { return result; }
        public final void setRawResult(T v) { result = v; }
        public final boolean exec() { runnable.run(); return true; }
        public final void run() { invoke(); }
        private static final long serialVersionUID = 5232453952276885070L;
    }
 
    /**
     * Adaptor for Runnables without results
     */
    static final class AdaptedRunnableAction extends ForkJoinTask<Void>
        implements RunnableFuture<Void> {
        final Runnable runnable;
        AdaptedRunnableAction(Runnable runnable) {
            if (runnable == null) throw new NullPointerException();
            this.runnable = runnable;
        }
        public final Void getRawResult() { return null; }
        public final void setRawResult(Void v) { }
        public final boolean exec() { runnable.run(); return true; }
        public final void run() { invoke(); }
        private static final long serialVersionUID = 5232453952276885070L;
    }
 
    /**
     * Adaptor for Runnables in which failure forces worker exception
     */
    static final class RunnableExecuteAction extends ForkJoinTask<Void> {
        final Runnable runnable;
        RunnableExecuteAction(Runnable runnable) {
            if (runnable == null) throw new NullPointerException();
            this.runnable = runnable;
        }
        public final Void getRawResult() { return null; }
        public final void setRawResult(Void v) { }
        public final boolean exec() { runnable.run(); return true; }
        void internalPropagateException(Throwable ex) {
            rethrow(ex); // rethrow outside exec() catches.
        }
        private static final long serialVersionUID = 5232453952276885070L;
    }
 
    /**
     * Adaptor for Callables
     */
    static final class AdaptedCallable<T> extends ForkJoinTask<T>
        implements RunnableFuture<T> {
        final Callable<? extends T> callable;
        T result;
        AdaptedCallable(Callable<? extends T> callable) {
            if (callable == null) throw new NullPointerException();
            this.callable = callable;
        }
        public final T getRawResult() { return result; }
        public final void setRawResult(T v) { result = v; }
        public final boolean exec() {
            try {
                result = callable.call();
                return true;
            } catch (Error err) {
                throw err;
            } catch (RuntimeException rex) {
                throw rex;
            } catch (Exception ex) {
                throw new RuntimeException(ex);
            }
        }
        public final void run() { invoke(); }
        private static final long serialVersionUID = 2838392045355241008L;
    }
 
 
    public static ForkJoinTask<?> adapt(Runnable runnable) {
        return new AdaptedRunnableAction(runnable);
    }
 
    public static <T> ForkJoinTask<T> adapt(Runnable runnable, T result) {
        return new AdaptedRunnable<T>(runnable, result);
    }
 
    public static <T> ForkJoinTask<T> adapt(Callable<? extends T> callable) {
        return new AdaptedCallable<T>(callable);
    }
 
    // Serialization support
 
    private static final long serialVersionUID = -7721805057305804111L;
 
    /**
     * 将任务序列化输出到指定流
     * @param s the stream
     * @throws java.io.IOException if an I/O error occurs
     * @serialData the current run status and the exception thrown
     * during execution, or {@code null} if none
     */
    private void writeObject(java.io.ObjectOutputStream s)
        throws java.io.IOException {
        s.defaultWriteObject();
        s.writeObject(getException());
    }
 
    /**
     * 从一个stream反序列化对象
     * @param s the stream
     * @throws ClassNotFoundException if the class of a serialized object
     *         could not be found
     * @throws java.io.IOException if an I/O error occurs
     */
    private void readObject(java.io.ObjectInputStream s)
        throws java.io.IOException, ClassNotFoundException {
        s.defaultReadObject();
        Object ex = s.readObject();
        if (ex != null)
            setExceptionalCompletion((Throwable)ex);
    }
 
    // Unsafe mechanics
    private static final sun.misc.Unsafe U;
    private static final long STATUS;
 
    static {
        exceptionTableLock = new ReentrantLock();
        exceptionTableRefQueue = new ReferenceQueue<Object>();
        exceptionTable = new ExceptionNode[EXCEPTION_MAP_CAPACITY];
        try {
            U = sun.misc.Unsafe.getUnsafe();
            Class<?> k = ForkJoinTask.class;
            STATUS = U.objectFieldOffset
                (k.getDeclaredField("status"));
        } catch (Exception e) {
            throw new Error(e);
        }
    }
 
}
```

## RecursiveAction

```java
package java.util.concurrent;
 
/**
* 递归无结果的 ForkJoinTask。该类建立约定，将无结果操作参数化为 Void
* ForkJoinTask。 null是Void类型的惟一有效值，所以像join这样的方法在
* 完成时总是返回 null。
* 用法示例。。。。。
* @since 1.7
* @author Doug Lea
*/
public abstract class RecursiveAction extends ForkJoinTask<Void> {
    private static final long serialVersionUID = 5232453952276485070L;
 
    /**
     * The main computation performed by this task.
     */
    protected abstract void compute();
 
    /**
     * Always returns {@code null}.
     *
     * @return {@code null} always
     */
    public final Void getRawResult() { return null; }
 
    /**
     * Requires null completion value.
     */
    protected final void setRawResult(Void mustBeNull) { }
 
    /**
     * Implements execution conventions for RecursiveActions.
     */
    protected final boolean exec() {
        compute();
        return true;
    }
 
}
```

### 示例一 SortTask

这里是一个简单但完整的ForkJoin排序，它对给定的  long[] 数组进行排序:

这里是一个归并排序的思想，先按照中位拆分，直到最小单位THRESHOLD时停止并排序，然后对结果进行合并。

合并时先拷贝指定区域内，”相对有序的数字“，然后重新排序。由于合并和任务的内存消耗，属于用空间换时间。

```java
static class SortTask extends RecursiveAction {
    final long[] array; final int lo, hi;
    SortTask(long[] array, int lo, int hi) {
      this.array = array; this.lo = lo; this.hi = hi;
    }
    SortTask(long[] array) { this(array, 0, array.length); }
    protected void compute() {
      if (hi - lo < THRESHOLD)
        sortSequentially(lo, hi);
      else {
        //ps： 位移，除以2，求中位数
        int mid = (lo + hi) >>> 1;
        invokeAll(new SortTask(array, lo, mid),
                  new SortTask(array, mid, hi));
        merge(lo, mid, hi);
      }
    }
    // implementation details follow: 最小的分片数据数量
    static final int THRESHOLD = 1000;
    void sortSequentially(int lo, int hi) {
      Arrays.sort(array, lo, hi);
    }
    void merge(int lo, int mid, int hi) {
      long[] buf = Arrays.copyOfRange(array, lo, mid);
      for (int i = 0, j = lo, k = mid; i < buf.length; j++)
        array[j] = (k == hi || buf[i] < array[k]) ?
          buf[i++] : array[k++];
    }
}}
```

### 示例二 IncrementTask

将数组的指定区域内的值Increment。

```java
class IncrementTask extends RecursiveAction {
    final long[] array; final int lo, hi;
    IncrementTask(long[] array, int lo, int hi) {
      this.array = array; this.lo = lo; this.hi = hi;
    }
    protected void compute() {
      if (hi - lo < THRESHOLD) {
        for (int i = lo; i < hi; ++i)
          array[i]++;
      }
      else {
        int mid = (lo + hi) >>> 1;
        invokeAll(new IncrementTask(array, lo, mid),
                  new IncrementTask(array, mid, hi));
      }
    }
}}
```

### 示例三 改进代码

下面的示例演示了一些改进和习惯用法，这些改进和习惯用法可能会带来更好的性能:

RecursiveActions不需要完全递归，只要它们保持基本的分治方法即可。

下面是一个类，它通过将重复除法的右边除以2(将右边的任务每次划分为2部分)，并使用 next引用链跟踪它们，从而对双数组中每个元素的平方求和。它使用基于方法 getSurplusQueuedTaskCount 的动态阈值，但是通过直接对未窃取的任务执行叶子操作而不是进一步细分来平衡潜在的过度分区。

```java
double sumOfSquares(ForkJoinPool pool, double[] array) {
    int n = array.length;
    Applyer a = new Applyer(array, 0, n, null);
    pool.invoke(a);
    return a.result;
}
 
class Applyer extends RecursiveAction {
    final double[] array;
    final int lo, hi;
    double result;
    Applyer next; // keeps track of right-hand-side tasks
    Applyer(double[] array, int lo, int hi, Applyer next) {
      this.array = array; this.lo = lo; this.hi = hi;
      this.next = next;
    }
    //数组从低位到高位，依次执行
    double atLeaf(int l, int h) {
      double sum = 0;
      for (int i = l; i < h; ++i) // perform leftmost base step
        sum += array[i] * array[i];
      return sum;
    }
 
    protected void compute() {
      int l = lo;
      int h = hi;
      Applyer right = null;
      //如果有任务，且任务数量小于等于3，就一直分发任务，分为left/right两部分
      while (h - l > 1 && getSurplusQueuedTaskCount() <= 3) {
        int mid = (l + h) >>> 1;
        right = new Applyer(array, mid, h, right);
        right.fork();
        h = mid;
      }
      //将left部分的值加载一起求和
      double sum = atLeaf(l, h);
      //再计算right部分值，加上left求和
      while (right != null) {
        if (right.tryUnfork()) // directly calculate if not stolen
          sum += right.atLeaf(right.lo, right.hi);
        else {
          right.join();
          sum += right.result;
        }
        right = right.next;
      }
      result = sum;
    }
}
```

## RecursiveTask

```java
package java.util.concurrent;
 
/**
* @since 1.7
* @author Doug Lea
*/
public abstract class RecursiveTask<V> extends ForkJoinTask<V> {
    private static final long serialVersionUID = 5232453952276485270L;
 
    /**
     * The result of the computation.
     */
    V result;
 
    /**
     * The main computation performed by this task.
     * @return the result of the computation
     */
    protected abstract V compute();
 
    public final V getRawResult() {
        return result;
    }
 
    protected final void setRawResult(V value) {
        result = value;
    }
 
    /**
     * Implements execution conventions for RecursiveTask.
     */
    protected final boolean exec() {
        result = compute();
        return true;
    }
 
}
```

### 示例 Fibonacci

这里采用线性求解的方式更好，因为可以利用已有的结果；

在多线程的任务分发机制下：因为内存消耗和任务分解的过小的原因，性能可能会很差。

```java
class Fibonacci extends RecursiveTask<Integer> {
    final int n;
    Fibonacci(int n) { this.n = n; }
    Integer compute() {
      if (n <= 1)
        return n;
      Fibonacci f1 = new Fibonacci(n - 1);
      f1.fork();
      Fibonacci f2 = new Fibonacci(n - 2);
      return f2.compute() + f1.join();
    }
}}
```

## ForkJoinPool

### 线程池说明

- 一些线程池状态字段的小结

  - asyncMode
    - true = 构造参数，适用于不使用join的事件任务模式

  - runState

- 工作队列和线程池中**通用的**常量字段说明
  - Bounds  -  边界相关
    - int SMASK = 0xffff
      - 低位的两个字节，最大值65535
    - int MAX_CAP = 0x7fff
      - 相比比SMASK而言，只用到了31个比特位，少一个bit位。
    - int EVENMASK = 0xfffe
      - 16进制 e 的最低位为0
    - int SQMASK = 0x007e
      - 0x007e = bit（01111110）只用到了中间6个比特位
  - 工作队列的掩码和单元。scanState和ctl sp子字段
    - int SCANNING = 1
      - 当运行的时候 = false。
    - int INACTIVE = 1 << 31
      - 正整数
    - int SS_SEQ = 1 << 16
      - 版本号
  - ForkJoinPool的模式位。配置和WorkQueue.config
    - int MODE_MASK = 0xffff << 16
      - 右移动16后，这里只用到数字高17 - 32位的比特位；但是因为首位是符号位，所以是负数
    - int LIFO_QUEUE = 0
      - 栈结构的队列索引位置记录
    - int FIFO_QUEUE = 1 << 16
      - 先进先出的队列的索引位置记录
    - int SHARED_QUEUE = 1 << 31
  - 一些实例属性
    - volatile long ctl;
      - 最主要的pool的控制字段，将下面信息按16bit为一组封装在一个long中，AC和TC初始化时取的是parallelism负数，后续代码可以直接判断正负，为负代表还没有达到目标数量。另外ctl低32位有个技巧可以直接用sp=(int)ctl取得，为负代表存在空闲worker。
      - AC: 活动的worker数量；
      - TC: 总共的worker数量；
      - SS: WorkQueue状态，第一位表示active的还是inactive，其余十五位表示版本号(对付ABA)；
      - ID: 这里保存了一个WorkQueue在WorkQueue[]的下标，和其他worker通过字段stackPred组成一个TreiberStack。后文讲的栈顶，指这里下标所在的WorkQueue。
    - volatile int runState;
      - 记录线程池的当前运行的状态，除了SHUTDOWN是负数，其他都是正数。
      - STARTED
      - STOP
      - TERMINATED
      - SHUTDOWN
      - RSLOCK
      - RSIGNAL
    - final int config;
      - 配置arallelism和mode，供后续读取。
      - mode可选FIFO_QUEUE和LIFO_QUEUE，默认是LIFO_QUEUE。
    - int indexSeed;
      - 生成工作（任务的）索引
    - volatile WorkQueue[] workQueues;  主要的工作队列注册位置
    - volatile AtomicLong stealCounter; （正在）偷取的任务数，也用于异步（模式）监控

### 工作队列说明

- class WorkQueue 中的常量
  - int INITIAL_QUEUE_CAPACITY = 1 << 13
    - 队列的初始容量，队列长度必须是2的幂，这样索引的最大值是2的幂-1，其按位与等于取模，可以快速计算
  - MAXIMUM_QUEUE_CAPACITY = 1 << 26
    - 队列数组的（最后一次扩容前的）最大大小
    - 64M
- class WorkQueue 中的变量
  - volatile int scanState
    - 偶数表示RUNNING
    - 奇数表示SCANNING
    - 负数表示inactive
  - int stackPred;
    - FJP的栈结构读取的方式的前置节点（索引）
  - int nsteals;
    - 偷取的任务数量
  - int hint;
    - 随机的偷取的索引
  - int config;
    -  当前工作队列的的index和模式，不等于FJP的config
  - volatile int qlock;
    - 当前队列的（被偷取任务）时的锁定状态
    -  1: locked,
    - < 0: terminate;
    - 0 未锁定状态
  - volatile int base;
    -  // 轮询的下一个poll的索引;用于（被其余的）多线程偷取任务，所以加入volatile 修饰。
  -  int top；
    - 顶部的索引，实际上是当前线程完成任务时和push的依据索引。
  - ForkJoinTask<?>[] array;
    - 当前工作队列保存的所有的任务，延迟分配
  - final ForkJoinPool pool;
    - 任务运行的池子
  - final ForkJoinWorkerThread owner;
    -  记录当前对应的工作线程；
    - 在共享模式下，为null
  - volatile Thread parker;
    - owner during call to park;
    - else null
  - volatile ForkJoinTask<?> currentJoin;
    - 正在等待join中的任务
  - volatile ForkJoinTask<?> currentSteal;
    - 主要用于帮助偷取任务

- 一些补充说明

```text
摘录于： https://www.jianshu.com/p/de025df55363
ForkJoinPool里有三个重要的角色：
 
    ForkJoinWorkerThread（下文简称worker）：包装Thread；
    WorkQueue：任务队列，双向；
    ForkJoinTask：worker执行的对象，实现了Future。两种类型，一种叫submission，另一种就叫task。
 
ForkJoinPool使用数组保存所有WorkQueue（下文经常出现的WorkQueue[]），每个worker有属于自己的WorkQueue，但不是每个WorkQueue都有对应的worker。
 
    没有worker的WorkQueue：保存的是submission，来自外部提交，在WorkQueue[]的下标是偶数；
    属于worker的WorkQueue：保存的是task，在WorkQueue[]的下标是奇数。
 
WorkQueue是一个双端队列，同时支持LIFO(last-in-first-out)的push和pop操作，和FIFO(first-in-first-out)的poll操作，分别操作top端和base端。worker操作自己的WorkQueue是LIFO操作(可选FIFO)，除此之外，worker会尝试steal其他WorkQueue里的任务，这个时候执行的是FIFO操作。
 
分开两端取任务的好处：
 
    LIFO操作只有对应的worker才能执行，push和pop不需要考虑并发；
    拆分时，越大的任务越在WorkQueue的base端，尽早分解，能够尽快进入计算。
 
```

### 源码

```java
package java.util.concurrent;
 
import java.lang.Thread.UncaughtExceptionHandler;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collection;
import java.util.Collections;
import java.util.List;
import java.util.concurrent.AbstractExecutorService;
import java.util.concurrent.Callable;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Future;
import java.util.concurrent.RejectedExecutionException;
import java.util.concurrent.RunnableFuture;
import java.util.concurrent.ThreadLocalRandom;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicLong;
import java.security.AccessControlContext;
import java.security.ProtectionDomain;
import java.security.Permissions;
 
/**
* 这是一个执行ForkJoinTask的ExecutorService，提供了任务的提交、管理、监控功能。
* 当设置asyncMode=true在构造时，其也适用于不使用join的事件任务模式。
*
* 一个静态的commonPool适用于大多数app，其可以被任何FJT使用（并不一定要提交到特点的线程池）
*
* 一个FJP可以构造是指定并行级别，一般其等于可用的（物理）线程数。
* 嵌套ManagedBlocker接口支持阻塞同步类型的适应。
*
* 最大运行线程数 32767，试图创建大于此数量时将会抛出异常IllegalArgumentException。
*
* 当内部资源用尽，或者shut down时，提交任务将会抛出RejectedExecutionException异常。
*
* @since 1.7
* @author Doug Lea
*/
@sun.misc.Contended
public class ForkJoinPool extends AbstractExecutorService {
 
    /*
     * Implementation Overview
     *
     * WorkQueues
     * ==========
     * 大多数操作都发生在工作窃取队列中（内嵌的WorkQueue）
     * "qlock" 字段，在shutdown时未锁定，值为-1.未锁时，此时是仍可以表
     * 现为顺序写入，但是在不成功是使用CAS操作。
     *
     * Management
     * ==========
     * 窃取工作的主要吞吐量优势源于分散控制——工作线程通常从他们自己或彼此那里
     * 以每秒超过10亿的速度执行任务。池本身创建、激活(启用扫描任务和运行任务)、
     * 禁用、阻塞和终止线程，所有这些操作都只需要很少的中心信息。我们只能全局跟
     * 踪或维护少数几个属性，因此我们将它们封装到少量变量中，通常在不阻塞或锁定
     * 的情况下维护原子性。几乎所有本质上的原子控制状态都保存在两个volatile变量中，
     * 到目前为止，这两个变量最常被读取(而不是写入)作为状态和一致性检查。字段“ctl”
     * 包含64位信息，用于自动决定是否添加、停用、(在事件队列上)排队、退出队列和/或
     * 重新激活工作人员。为了启用这种打包，我们将最大并行度限制为(1<<15)-1(这远
     * 远超出了正常的操作范围)，以允许id、计数及其负数(用于阈值设置)适合16位子字段。
     *
     * 字段“runState”持有可锁定的状态位(启动、停止等)，还保护对工作队列数组的更新。
     * 当用作锁时，它通常只用于一些指令(惟一的例外是一次性数组初始化和不常见的大小调整)，
     * 所以在最多进行一次短暂的旋转之后，它几乎总是可用的。但是要特别小心，在旋转之后，
     * 方法awaitRunStateLock(只有在初始CAS失败时才调用)在内置监视器上使用
     * wait/notify机制来阻塞(很少)。对于高度争用的锁来说，这将是一个糟糕的主意，但是
     * 大多数池在自旋限制之后运行时都没有锁争用，所以这是一个比较保守的选择。因为我们没
     * 有一个内部对象作为监视器使用，所以“stealCounter”(一个AtomicLong)在可用时使
     * 用(它也必须延迟初始化;见externalSubmit)。
     *
     * “runState”和“ctl”的用法只在一种情况下交互:
     * 决定添加一个工作线程(请参阅tryAddWorker)，在这种情况下，ctl CAS在锁被持有时执行。
     * 记录工作队列。工作队列记录在“工作队列”数组中。数组在第一次使用时创建(请参阅externalSubmit)，
     * 并在必要时展开。在记录新工人和未记录终止工人时，数组的更新由runState锁相互保护，但
     * 是数组是并发可读的，并且可以直接访问。我们还确保数组引用本身的读取不会变得太陈旧。为
     * 了简化基于索引的操作，数组大小总是2的幂，所有读取器必须容忍空槽。工作队列的索引为奇数。
     * 共享(提交)队列的索引是偶数的，最多为64个插槽，以限制增长，即使数组需要扩展以添加更多
     * 的worker。以这种方式将它们组合在一起可以简化和加快任务扫描。
     *
     * 所有工作线程的创建都是按需的，由任务提交、终止工作的替换和/或阻塞工作的补偿触发。但是，
     * 所有其他支持代码都是为了与其他策略一起工作而设置的。为了确保我们不保留会阻止GC的工作
     * 线程引用，所有对工作队列的访问都是通过对工作队列数组的索引进行的(这是这里一些混乱代码
     * 结构的来源之一)。本质上，workQueues数组充当一个弱引用机制。因此，例如，ctl的
     * stack top子字段存储索引，而不是引用。
     *
     * 排队闲置线程。与HPC工作窃取框架不同，我们不能让工作人员在无法立即找到任务的
     * 情况下无限期地扫描任务，并且除非出现可用的任务，否则我们不能启动/恢复工作人员。
     * 另一方面，当提交或生成新任务时，我们必须快速地促使它们采取行动。在许多情况下，
     * 启动worker的加速时间是影响整体性能的主要限制因素，而JIT编译和分配在程序启
     * 动时又加剧了这一限制因素。所以我们尽可能地简化它。
     *
     * ...
     */
 
    // Static utilities - 静态部分
 
    /**
     * 如果存在安全管理器，请确保调用者具有修改线程的权限。
     */
    private static void checkPermission() {
        SecurityManager security = System.getSecurityManager();
        if (security != null)
            security.checkPermission(modifyThreadPermission);
    }
 
    // Nested classes
 
    /**
     * 创建新的ForkJoinWorkerThread的工厂。必须为ForkJoinWorkerThread子类
     * 定义和使用ForkJoinWorkerThread来扩展基本功能或初始化具有不同上下文的线程。
     */
    public static interface ForkJoinWorkerThreadFactory {
        /**
         * Returns a new worker thread operating in the given pool.
         *
         * @param pool the pool this thread works in
         * @return the new worker thread
         * @throws NullPointerException if the pool is null
         */
        public ForkJoinWorkerThread newThread(ForkJoinPool pool);
    }
 
    /**
     * Default ForkJoinWorkerThreadFactory implementation; creates a
     * new ForkJoinWorkerThread.
     */
    static final class DefaultForkJoinWorkerThreadFactory
        implements ForkJoinWorkerThreadFactory {
        public final ForkJoinWorkerThread newThread(ForkJoinPool pool) {
            return new ForkJoinWorkerThread(pool);
        }
    }
 
    /**
     *  用于替换从WorkQueue.tryRemoveAndExec中的内部队列插槽中删除的本地连接目标
     * 的人工任务。除了拥有唯一标识外，我们实际上不需要代理来做任何事情。
     */
    static final class EmptyTask extends ForkJoinTask<Void> {
        private static final long serialVersionUID = -7721805057305804111L;
        EmptyTask() { status = ForkJoinTask.NORMAL; } // force done
        public final Void getRawResult() { return null; }
        public final void setRawResult(Void x) {}
        public final boolean exec() { return true; }
    }
 
    // Constants shared across ForkJoinPool and WorkQueue
 
    // Bounds
    static final int SMASK        = 0xffff;        // short bits == max index
    static final int MAX_CAP      = 0x7fff;        // max #workers - 1
    static final int EVENMASK     = 0xfffe;        // even short bits
    static final int SQMASK       = 0x007e;        // max 64 (even) slots
 
    // Masks and units for WorkQueue.scanState and ctl sp subfield
    static final int SCANNING     = 1;             // false when running tasks
    static final int INACTIVE     = 1 << 31;       // must be negative
    static final int SS_SEQ       = 1 << 16;       // version count
 
    // Mode bits for ForkJoinPool.config and WorkQueue.config
    static final int MODE_MASK    = 0xffff << 16;  // top half of int
    static final int LIFO_QUEUE   = 0;
    static final int FIFO_QUEUE   = 1 << 16;
    static final int SHARED_QUEUE = 1 << 31;       // must be negative
 
    /**
     * 支持工作窃取和外部任务提交的队列。参见上面的描述和算法。
     * 大多数平台上的性能对工作队列及其数组的实例的位置非常敏感——我们绝对不希望多个工作
     * 队列实例或多个队列数组共享缓存线。@Contended注释警告jvm尝试隔离实例。
     */
    @sun.misc.Contended
    static final class WorkQueue {
 
        /**
         * 初始化时窃取工作队列数组的容量。必须是2的幂;至少4个，但是应该更大一些，
         * 以减少或消除队列之间的cacheline共享。目前，它要大得多，因为jvm经常将
         * 数组放置在共享GC簿记的位置(特别是cardmarks)，这样每次写访问都会遇到
         * 严重的内存争用，这是一个部分解决方案。
         */
        static final int INITIAL_QUEUE_CAPACITY = 1 << 13;
 
        /**
         * 267/5000
         * 队列数组的最大大小。必须有两个小于或等于1的幂<<(31 -数组入口的宽度)，以
         * 确保缺少对索引计算的概括，但定义为一个略小于此的值，以帮助用户在系统饱和之
         * 前捕获失控的程序。
         */
        static final int MAXIMUM_QUEUE_CAPACITY = 1 << 26; // 64M
 
        // Instance fields
        volatile int scanState;    // versioned, <0: inactive; odd:scanning
        int stackPred;             // pool stack (ctl) predecessor
        int nsteals;               // number of steals
        int hint;                  // randomization and stealer index hint
        int config;                // pool index and mode
        volatile int qlock;        // 1: locked, < 0: terminate; else 0
        volatile int base;         // index of next slot for poll
        int top;                   // index of next slot for push
        ForkJoinTask<?>[] array;   // the elements (initially unallocated)
        final ForkJoinPool pool;   // the containing pool (may be null)
        final ForkJoinWorkerThread owner; // owning thread or null if shared
        volatile Thread parker;    // == owner during call to park; else null
        volatile ForkJoinTask<?> currentJoin;  // task being joined in awaitJoin
        volatile ForkJoinTask<?> currentSteal; // mainly used by helpStealer
 
        WorkQueue(ForkJoinPool pool, ForkJoinWorkerThread owner) {
            this.pool = pool;
            this.owner = owner;
            // Place indices in the center of array (that is not yet allocated)
            base = top = INITIAL_QUEUE_CAPACITY >>> 1;
        }
 
        /**
         * Returns an exportable index (used by ForkJoinWorkerThread).
         */
        final int getPoolIndex() {
            return (config & 0xffff) >>> 1; // ignore odd/even tag bit
        }
 
        /**
         * Returns the approximate number of tasks in the queue.
         */
        final int queueSize() {
            int n = base - top;       // non-owner callers must read base first
            return (n >= 0) ? 0 : -n; // ignore transient negative
        }
 
        /**
         * 通过检查接近空队列是否至少有一个无人认领的任务，
         * 可以比queueSize更准确地估计该队列是否有任务。
         */
        final boolean isEmpty() {
            ForkJoinTask<?>[] a; int n, m, s;
            return ((n = base - (s = top)) >= 0 ||
                    (n == -1 &&           // possibly one task
                     ((a = array) == null || (m = a.length - 1) < 0 ||
                      U.getObject
                      (a, (long)((m & (s - 1)) << ASHIFT) + ABASE) == null)));
        }
 
        /**
         * push一个任务，仅仅被队列的排他模式拥有者调用。
         * (共享队列版本嵌入到externalPush方法中。)
         * @param task the task. Caller must ensure non-null.
         * @throws RejectedExecutionException if array cannot be resized
         */
        final void push(ForkJoinTask<?> task) {
            ForkJoinTask<?>[] a; ForkJoinPool p;
            int b = base, s = top, n;
            if ((a = array) != null) {    // ignore if queue removed
                int m = a.length - 1;     // fenced write for task visibility
                U.putOrderedObject(a, ((m & s) << ASHIFT) + ABASE, task);
                U.putOrderedInt(this, QTOP, s + 1);
                if ((n = s - b) <= 1) {//如果原来没有任务
                    if ((p = pool) != null)
                        p.signalWork(p.workQueues, this);
                }
                else if (n >= m) //否则判断数量看是否大于数组的长度-1，是则扩容数组
                    growArray();
            }
        }
 
        /**
         * 初始化或加倍数组的容量。在调整大小的过程中，可以通过所有者调用，也可以通过锁来调用。
         */
        final ForkJoinTask<?>[] growArray() {
            ForkJoinTask<?>[] oldA = array;
            //ps: 这里直接扩容一倍，并判断是否超过最大限定值，超过则抛出异常
            int size = oldA != null ? oldA.length << 1 : INITIAL_QUEUE_CAPACITY;
            if (size > MAXIMUM_QUEUE_CAPACITY)
                throw new RejectedExecutionException("Queue capacity exceeded");
            int oldMask, t, b;
            ForkJoinTask<?>[] a = array = new ForkJoinTask<?>[size];
            if (oldA != null && (oldMask = oldA.length - 1) >= 0 &&
                (t = top) - (b = base) > 0) {
                int mask = size - 1;
                do { //模拟轮询从旧数组，推到新数组
                    ForkJoinTask<?> x;
                    int oldj = ((b & oldMask) << ASHIFT) + ABASE;
                    int j    = ((b &    mask) << ASHIFT) + ABASE;
                    x = (ForkJoinTask<?>)U.getObjectVolatile(oldA, oldj);
                    if (x != null &&
                        U.compareAndSwapObject(oldA, oldj, x, null))
                        U.putObjectVolatile(a, j, x);
                } while (++b != t);
            }
            return a;
        }
 
        /**
         * 如果存在下一个任务，则用先进先出的顺序带出一个。
         *  Call only by owner in unshared queues.
         */
        final ForkJoinTask<?> pop() {
            ForkJoinTask<?>[] a; ForkJoinTask<?> t; int m;
            if ((a = array) != null && (m = a.length - 1) >= 0) {
                for (int s; (s = top - 1) - base >= 0;) {
                    long j = ((m & s) << ASHIFT) + ABASE;
                    if ((t = (ForkJoinTask<?>)U.getObject(a, j)) == null)
                        break;
                    if (U.compareAndSwapObject(a, j, t, null)) {
                        U.putOrderedInt(this, QTOP, s);
                        return t;
                    }
                }
            }
            return null;
        }
 
        /**
         * 如果b是队列的基数，并且可以无争用地认领任务，则按FIFO顺序接受任务。
         * 专门的版本出现在ForkJoinPool方法扫描和helpStealer。
         */
        final ForkJoinTask<?> pollAt(int b) {
            ForkJoinTask<?> t; ForkJoinTask<?>[] a;
            if ((a = array) != null) {
                int j = (((a.length - 1) & b) << ASHIFT) + ABASE;
                if ((t = (ForkJoinTask<?>)U.getObjectVolatile(a, j)) != null &&
                    base == b && U.compareAndSwapObject(a, j, t, null)) {
                    base = b + 1;
                    return t;
                }s
            }
            return null;
        }
 
        /**
         * Takes next task, if one exists, in FIFO order.
         */
        final ForkJoinTask<?> poll() {
            ForkJoinTask<?>[] a; int b; ForkJoinTask<?> t;
            while ((b = base) - top < 0 && (a = array) != null) {
                int j = (((a.length - 1) & b) << ASHIFT) + ABASE;
                t = (ForkJoinTask<?>)U.getObjectVolatile(a, j);
                if (base == b) {
                    if (t != null) {
                        if (U.compareAndSwapObject(a, j, t, null)) {
                            base = b + 1;
                            return t;
                        }
                    }
                    else if (b + 1 == top) // now empty
                        break;
                }
            }
            return null;
        }
 
        /**
         * Takes next task, if one exists, in order specified by mode.
         */
        final ForkJoinTask<?> nextLocalTask() {
            return (config & FIFO_QUEUE) == 0 ? pop() : poll();
        }
 
        /**
         * Returns next task, if one exists, in order specified by mode.
         */
        final ForkJoinTask<?> peek() {
            ForkJoinTask<?>[] a = array; int m;
            if (a == null || (m = a.length - 1) < 0)
                return null;
            int i = (config & FIFO_QUEUE) == 0 ? top - 1 : base;
            int j = ((i & m) << ASHIFT) + ABASE;
            return (ForkJoinTask<?>)U.getObjectVolatile(a, j);
        }
 
        /**
         * Pops the given task only if it is at the current top.
         * (A shared version is available only via FJP.tryExternalUnpush)
        */
        final boolean tryUnpush(ForkJoinTask<?> t) {
            ForkJoinTask<?>[] a; int s;
            if ((a = array) != null && (s = top) != base &&
                U.compareAndSwapObject
                (a, (((a.length - 1) & --s) << ASHIFT) + ABASE, t, null)) {
                U.putOrderedInt(this, QTOP, s);
                return true;
            }
            return false;
        }
 
        /**
         * Removes and cancels all known tasks, ignoring any exceptions.
         */
        final void cancelAll() {
            ForkJoinTask<?> t;
            if ((t = currentJoin) != null) {
                currentJoin = null;
                ForkJoinTask.cancelIgnoringExceptions(t);
            }
            if ((t = currentSteal) != null) {
                currentSteal = null;
                ForkJoinTask.cancelIgnoringExceptions(t);
            }
            while ((t = poll()) != null)
                ForkJoinTask.cancelIgnoringExceptions(t);
        }
 
        // Specialized execution methods
 
        /**
         * Polls and runs tasks until empty.
         */
        final void pollAndExecAll() {
            for (ForkJoinTask<?> t; (t = poll()) != null;)
                t.doExec();
        }
 
        /**
         * Removes and executes all local tasks. If LIFO, invokes
         * pollAndExecAll. Otherwise implements a specialized pop loop
         * to exec until empty.
         */
        final void execLocalTasks() {
            int b = base, m, s;
            ForkJoinTask<?>[] a = array;
            if (b - (s = top - 1) <= 0 && a != null &&
                (m = a.length - 1) >= 0) {
                if ((config & FIFO_QUEUE) == 0) {
                    for (ForkJoinTask<?> t;;) {
                        if ((t = (ForkJoinTask<?>)U.getAndSetObject
                             (a, ((m & s) << ASHIFT) + ABASE, null)) == null)
                            break;
                        U.putOrderedInt(this, QTOP, s);
                        t.doExec();
                        if (base - (s = top - 1) > 0)
                            break;
                    }
                }
                else
                    pollAndExecAll();
            }
        }
 
        /**
         * Executes the given task and any remaining local tasks.
         */
        final void runTask(ForkJoinTask<?> task) {
            if (task != null) {
                scanState &= ~SCANNING; // mark as busy
                (currentSteal = task).doExec();
                U.putOrderedObject(this, QCURRENTSTEAL, null); // release for GC
                execLocalTasks();
                ForkJoinWorkerThread thread = owner;
                if (++nsteals < 0)      // collect on overflow
                    transferStealCount(pool);
                scanState |= SCANNING;
                if (thread != null)
                    thread.afterTopLevelExec();
            }
        }
 
        /**
         * Adds steal count to pool stealCounter if it exists, and resets.
         */
        final void transferStealCount(ForkJoinPool p) {
            AtomicLong sc;
            if (p != null && (sc = p.stealCounter) != null) {
                int s = nsteals;
                nsteals = 0;            // if negative, correct for overflow
                sc.getAndAdd((long)(s < 0 ? Integer.MAX_VALUE : s));
            }
        }
 
        /**
         * 如果存在，则从队列中移除并执行给定的任务或任何其他已取消的任务。
         * 仅供awaitJoin使用。
         * @return true if queue empty and task not known to be done
         */
        final boolean tryRemoveAndExec(ForkJoinTask<?> task) {
            ForkJoinTask<?>[] a; int m, s, b, n;
            if ((a = array) != null && (m = a.length - 1) >= 0 &&
                task != null) {
                while ((n = (s = top) - (b = base)) > 0) {
                    for (ForkJoinTask<?> t;;) {      // traverse from s to b
                        long j = ((--s & m) << ASHIFT) + ABASE;
                        if ((t = (ForkJoinTask<?>)U.getObject(a, j)) == null)
                            return s + 1 == top;     // shorter than expected
                        else if (t == task) {
                            boolean removed = false;
                            if (s + 1 == top) {      // pop
                                if (U.compareAndSwapObject(a, j, task, null)) {
                                    U.putOrderedInt(this, QTOP, s);
                                    removed = true;
                                }
                            }
                            else if (base == b)      // replace with proxy
                                removed = U.compareAndSwapObject(
                                    a, j, task, new EmptyTask());
                            if (removed)
                                task.doExec();
                            break;
                        }
                        else if (t.status < 0 && s + 1 == top) {
                            if (U.compareAndSwapObject(a, j, t, null))
                                U.putOrderedInt(this, QTOP, s);
                            break;                  // was cancelled
                        }
                        if (--n == 0)
                            return false;
                    }
                    if (task.status < 0)
                        return false;
                }
            }
            return true;
        }
 
        /**
         * 如果在与给定任务相同的CC计算中，以共享或拥有模式弹出任务。仅供helpComplete使用。
         */
        final CountedCompleter<?> popCC(CountedCompleter<?> task, int mode) {
            int s; ForkJoinTask<?>[] a; Object o;
            if (base - (s = top) < 0 && (a = array) != null) {
                long j = (((a.length - 1) & (s - 1)) << ASHIFT) + ABASE;
                if ((o = U.getObjectVolatile(a, j)) != null &&
                    (o instanceof CountedCompleter)) {
                    CountedCompleter<?> t = (CountedCompleter<?>)o;
                    for (CountedCompleter<?> r = t;;) {
                        if (r == task) {
                            if (mode < 0) { // must lock
                                if (U.compareAndSwapInt(this, QLOCK, 0, 1)) {
                                    if (top == s && array == a &&
                                        U.compareAndSwapObject(a, j, t, null)) {
                                        U.putOrderedInt(this, QTOP, s - 1);
                                        U.putOrderedInt(this, QLOCK, 0);
                                        return t;
                                    }
                                    U.compareAndSwapInt(this, QLOCK, 1, 0);
                                }
                            }
                            else if (U.compareAndSwapObject(a, j, t, null)) {
                                U.putOrderedInt(this, QTOP, s - 1);
                                return t;
                            }
                            break;
                        }
                        else if ((r = r.completer) == null) // try parent
                            break;
                    }
                }
            }
            return null;
        }
 
        /**
         * 在与给定任务相同的CC计算中窃取和运行一个任务(如果存在并且可以不争用)。
         * 否则返回方法helpComplete使用的校验和/控制值。
         * Steals and runs a task in the same CC computation as the
         * given task if one exists and can be taken without
         * contention. Otherwise returns a checksum/control value for
         * use by method helpComplete.
         *
         * @return 1 if successful, 2 if retryable (lost to another
         * stealer), -1 if non-empty but no matching task found, else
         * the base index, forced negative.
         */
        final int pollAndExecCC(CountedCompleter<?> task) {
            int b, h; ForkJoinTask<?>[] a; Object o;
            if ((b = base) - top >= 0 || (a = array) == null)
                h = b | Integer.MIN_VALUE;  // to sense movement on re-poll
            else {
                long j = (((a.length - 1) & b) << ASHIFT) + ABASE;
                if ((o = U.getObjectVolatile(a, j)) == null)
                    h = 2;                  // retryable
                else if (!(o instanceof CountedCompleter))
                    h = -1;                 // unmatchable
                else {
                    CountedCompleter<?> t = (CountedCompleter<?>)o;
                    for (CountedCompleter<?> r = t;;) {
                        if (r == task) {
                            if (base == b &&
                                U.compareAndSwapObject(a, j, t, null)) {
                                base = b + 1;
                                t.doExec();
                                h = 1;      // success
                            }
                            else
                                h = 2;      // lost CAS
                            break;
                        }
                        else if ((r = r.completer) == null) {
                            h = -1;         // unmatched
                            break;
                        }
                    }
                }
            }
            return h;
        }
 
        /**
         * Returns true if owned and not known to be blocked.
         */
        final boolean isApparentlyUnblocked() {
            Thread wt; Thread.State s;
            return (scanState >= 0 &&
                    (wt = owner) != null &&
                    (s = wt.getState()) != Thread.State.BLOCKED &&
                    s != Thread.State.WAITING &&
                    s != Thread.State.TIMED_WAITING);
        }
 
        // Unsafe mechanics. Note that some are (and must be) the same as in FJP
        private static final sun.misc.Unsafe U;
        private static final int  ABASE;
        private static final int  ASHIFT;
        private static final long QTOP;
        private static final long QLOCK;
        private static final long QCURRENTSTEAL;
        static {
            try {
                U = sun.misc.Unsafe.getUnsafe();
                Class<?> wk = WorkQueue.class;
                Class<?> ak = ForkJoinTask[].class;
                QTOP = U.objectFieldOffset
                    (wk.getDeclaredField("top"));
                QLOCK = U.objectFieldOffset
                    (wk.getDeclaredField("qlock"));
                QCURRENTSTEAL = U.objectFieldOffset
                    (wk.getDeclaredField("currentSteal"));
                ABASE = U.arrayBaseOffset(ak);
                int scale = U.arrayIndexScale(ak);
                if ((scale & (scale - 1)) != 0)
                    throw new Error("data type scale not a power of two");
                ASHIFT = 31 - Integer.numberOfLeadingZeros(scale);
            } catch (Exception e) {
                throw new Error(e);
            }
        }
    }
 
    // static fields (initialized in static initializer below)
 
    /**
     * Creates a new ForkJoinWorkerThread. This factory is used unless
     * overridden in ForkJoinPool constructors.
     */
    public static final ForkJoinWorkerThreadFactory
        defaultForkJoinWorkerThreadFactory;
 
    /**
     * Permission required for callers of methods that may start or
     * kill threads.
     */
    private static final RuntimePermission modifyThreadPermission;
 
    /**
     * Common (static) pool. Non-null for public use unless a static
     * construction exception, but internal usages null-check on use
     * to paranoically avoid potential initialization circularities
     * as well as to simplify generated code.
     */
    static final ForkJoinPool common;
 
    /**
     * 常见的并行性。为了在禁用公共池线程时允许更简单的使用和管理，
     * 我们允许底层的公共线程。并行度字段为0，但在这种情况下仍然将并行度报告为1，
     * 以反映产生的调用运行机制。
     */
    static final int commonParallelism;
 
    /**
     * trycompensation中的备用线程结构限制。
     */
    private static int commonMaxSpares;
 
    /**
     * Sequence number for creating workerNamePrefix.
     */
    private static int poolNumberSequence;
 
    /**
     * Returns the next sequence number. We don't expect this to
     * ever contend, so use simple builtin sync.
     */
    private static final synchronized int nextPoolId() {
        return ++poolNumberSequence;
    }
 
    // static configuration constants
 
    /**
     * 初始超时值(以纳秒为单位)，用于触发暂停以等待新工作的线程。
     * 在超时时，线程将尝试减少工作人员的数量。该值应该足够大，
     * 以避免过度积极收缩在大多数瞬态停机(长GCs等)。
     */
    private static final long IDLE_TIMEOUT = 2000L * 1000L * 1000L; // 2sec
 
    /**
     * 对空闲超时的容忍，以应对计时器不足
     */
    private static final long TIMEOUT_SLOP = 20L * 1000L * 1000L;  // 20ms
 
    /**
     * 在静态初始化期间commonMaxSpares的初始值。这个值远远超出了正常的需求，
     * 但也远远低于MAX_CAP和典型的OS线程限制，因此允许jvm在耗尽所需资源之前捕获误用/滥用。
     */
    private static final int DEFAULT_COMMON_MAX_SPARES = 256;
 
    /**
     * 在阻塞之前旋转等待的次数。自旋(在waitrunstatelock和awaitWork中)当前使用随机自旋。
     * 如果/当类似mwait的intrinsics成为可用时，它们可能会允许更安静的旋转。
     * 自旋的值必须是2的幂，至少是4。当前值会在一小部分典型的上下文切换时间内引起旋转，
     * 考虑到典型的不需要阻塞的可能性，这是值得的。
     */
    private static final int SPINS  = 1 << 11;
 
    /**
     * Increment for seed generators. See class ThreadLocal for explanation.
     */
    private static final int SEED_INCREMENT = 0x9e3779b9;
 
    /*
     * Bits and masks for field ctl, packed with 4 16 bit subfields:
     * AC: Number of active running workers minus target parallelism
     * TC: Number of total workers minus target parallelism
     * SS: version count and status of top waiting thread
     * ID: poolIndex of top of Treiber stack of waiters
     *
     * When convenient, we can extract the lower 32 stack top bits
     * (including version bits) as sp=(int)ctl.  The offsets of counts
     * by the target parallelism and the positionings of fields makes
     * it possible to perform the most common checks via sign tests of
     * fields: When ac is negative, there are not enough active
     * workers, when tc is negative, there are not enough total
     * workers.  When sp is non-zero, there are waiting workers.  To
     * deal with possibly negative fields, we use casts in and out of
     * "short" and/or signed shifts to maintain signedness.
     *
     * Because it occupies uppermost bits, we can add one active count
     * using getAndAddLong of AC_UNIT, rather than CAS, when returning
     * from a blocked join.  Other updates entail multiple subfields
     * and masking, requiring CAS.
     */
 
    // Lower and upper word masks
    private static final long SP_MASK    = 0xffffffffL;
    private static final long UC_MASK    = ~SP_MASK;
 
    // Active counts
    private static final int  AC_SHIFT   = 48;
    private static final long AC_UNIT    = 0x0001L << AC_SHIFT;
    private static final long AC_MASK    = 0xffffL << AC_SHIFT;
 
    // Total counts
    private static final int  TC_SHIFT   = 32;
    private static final long TC_UNIT    = 0x0001L << TC_SHIFT;
    private static final long TC_MASK    = 0xffffL << TC_SHIFT;
    private static final long ADD_WORKER = 0x0001L << (TC_SHIFT + 15); // sign
 
    // runState bits: SHUTDOWN must be negative, others arbitrary powers of two
    private static final int  RSLOCK     = 1;
    private static final int  RSIGNAL    = 1 << 1;
    private static final int  STARTED    = 1 << 2;
    private static final int  STOP       = 1 << 29;
    private static final int  TERMINATED = 1 << 30;
    private static final int  SHUTDOWN   = 1 << 31;
 
    // Instance fields
    volatile long ctl;                   // main pool control
    volatile int runState;               // lockable status
    final int config;                    // parallelism, mode
    int indexSeed;                       // to generate worker index
    volatile WorkQueue[] workQueues;     // main registry
    final ForkJoinWorkerThreadFactory factory;
    final UncaughtExceptionHandler ueh;  // per-worker UEH
    final String workerNamePrefix;       // to create worker name string
    volatile AtomicLong stealCounter;    // also used as sync monitor
 
    /**
     * Acquires the runState lock; returns current (locked) runState.
     */
    private int lockRunState() {
        int rs;
        return ((((rs = runState) & RSLOCK) != 0 ||
                 !U.compareAndSwapInt(this, RUNSTATE, rs, rs |= RSLOCK)) ?
                awaitRunStateLock() : rs);
    }
 
    /**
     * Spins and/or blocks until runstate lock is available.  See
     * above for explanation.
     */
    private int awaitRunStateLock() {
        Object lock;
        boolean wasInterrupted = false;
        for (int spins = SPINS, r = 0, rs, ns;;) {
            if (((rs = runState) & RSLOCK) == 0) {
                if (U.compareAndSwapInt(this, RUNSTATE, rs, ns = rs | RSLOCK)) {
                    if (wasInterrupted) {
                        try {
                            Thread.currentThread().interrupt();
                        } catch (SecurityException ignore) {
                        }
                    }
                    return ns;
                }
            }
            else if (r == 0)
                r = ThreadLocalRandom.nextSecondarySeed();
            else if (spins > 0) {
                r ^= r << 6; r ^= r >>> 21; r ^= r << 7; // xorshift
                if (r >= 0)
                    --spins;
            }
            else if ((rs & STARTED) == 0 || (lock = stealCounter) == null)
                Thread.yield();   // initialization race
            else if (U.compareAndSwapInt(this, RUNSTATE, rs, rs | RSIGNAL)) {
                synchronized (lock) {
                    if ((runState & RSIGNAL) != 0) {
                        try {
                            lock.wait();
                        } catch (InterruptedException ie) {
                            if (!(Thread.currentThread() instanceof
                                  ForkJoinWorkerThread))
                                wasInterrupted = true;
                        }
                    }
                    else
                        lock.notifyAll();
                }
            }
        }
    }
 
    /**
     * Unlocks and sets runState to newRunState.
     *
     * @param oldRunState a value returned from lockRunState
     * @param newRunState the next value (must have lock bit clear).
     */
    private void unlockRunState(int oldRunState, int newRunState) {
        if (!U.compareAndSwapInt(this, RUNSTATE, oldRunState, newRunState)) {
            Object lock = stealCounter;
            runState = newRunState;              // clears RSIGNAL bit
            if (lock != null)
                synchronized (lock) { lock.notifyAll(); }
        }
    }
 
    // Creating, registering and deregistering workers
 
    /**
     * Tries to construct and start one worker. Assumes that total
     * count has already been incremented as a reservation.  Invokes
     * deregisterWorker on any failure.
     *
     * @return true if successful
     */
    private boolean createWorker() {
        ForkJoinWorkerThreadFactory fac = factory;
        Throwable ex = null;
        ForkJoinWorkerThread wt = null;
        try {
            if (fac != null && (wt = fac.newThread(this)) != null) {
                wt.start();
                return true;
            }
        } catch (Throwable rex) {
            ex = rex;
        }
        deregisterWorker(wt, ex);
        return false;
    }
 
    /**
     * Tries to add one worker, incrementing ctl counts before doing
     * so, relying on createWorker to back out on failure.
     *
     * @param c incoming ctl value, with total count negative and no
     * idle workers.  On CAS failure, c is refreshed and retried if
     * this holds (otherwise, a new worker is not needed).
     */
    private void tryAddWorker(long c) {
        boolean add = false;
        do {
            long nc = ((AC_MASK & (c + AC_UNIT)) |
                       (TC_MASK & (c + TC_UNIT)));
            if (ctl == c) {
                int rs, stop;                 // check if terminating
                if ((stop = (rs = lockRunState()) & STOP) == 0)
                    add = U.compareAndSwapLong(this, CTL, c, nc);
                unlockRunState(rs, rs & ~RSLOCK);
                if (stop != 0)
                    break;
                if (add) {
                    createWorker();
                    break;
                }
            }
        } while (((c = ctl) & ADD_WORKER) != 0L && (int)c == 0);
    }
 
    /**
     * Callback from ForkJoinWorkerThread constructor to establish and
     * record its WorkQueue.
     *
     * @param wt the worker thread
     * @return the worker's queue
     */
    final WorkQueue registerWorker(ForkJoinWorkerThread wt) {
        UncaughtExceptionHandler handler;
        wt.setDaemon(true);                           // configure thread
        if ((handler = ueh) != null)
            wt.setUncaughtExceptionHandler(handler);
        WorkQueue w = new WorkQueue(this, wt);
        int i = 0;                                    // assign a pool index
        int mode = config & MODE_MASK;
        int rs = lockRunState();
        try {
            WorkQueue[] ws; int n;                    // skip if no array
            if ((ws = workQueues) != null && (n = ws.length) > 0) {
                int s = indexSeed += SEED_INCREMENT;  // unlikely to collide
                int m = n - 1;
                i = ((s << 1) | 1) & m;               // odd-numbered indices
                if (ws[i] != null) {                  // collision
                    int probes = 0;                   // step by approx half n
                    int step = (n <= 4) ? 2 : ((n >>> 1) & EVENMASK) + 2;
                    while (ws[i = (i + step) & m] != null) {
                        if (++probes >= n) {
                            workQueues = ws = Arrays.copyOf(ws, n <<= 1);
                            m = n - 1;
                            probes = 0;
                        }
                    }
                }
                w.hint = s;                           // use as random seed
                w.config = i | mode;
                w.scanState = i;                      // publication fence
                ws[i] = w;
            }
        } finally {
            unlockRunState(rs, rs & ~RSLOCK);
        }
        wt.setName(workerNamePrefix.concat(Integer.toString(i >>> 1)));
        return w;
    }
 
    /**
     * Final callback from terminating worker, as well as upon failure
     * to construct or start a worker.  Removes record of worker from
     * array, and adjusts counts. If pool is shutting down, tries to
     * complete termination.
     *
     * @param wt the worker thread, or null if construction failed
     * @param ex the exception causing failure, or null if none
     */
    final void deregisterWorker(ForkJoinWorkerThread wt, Throwable ex) {
        WorkQueue w = null;
        if (wt != null && (w = wt.workQueue) != null) {
            WorkQueue[] ws;                           // remove index from array
            int idx = w.config & SMASK;
            int rs = lockRunState();
            if ((ws = workQueues) != null && ws.length > idx && ws[idx] == w)
                ws[idx] = null;
            unlockRunState(rs, rs & ~RSLOCK);
        }
        long c;                                       // decrement counts
        do {} while (!U.compareAndSwapLong
                     (this, CTL, c = ctl, ((AC_MASK & (c - AC_UNIT)) |
                                           (TC_MASK & (c - TC_UNIT)) |
                                           (SP_MASK & c))));
        if (w != null) {
            w.qlock = -1;                             // ensure set
            w.transferStealCount(this);
            w.cancelAll();                            // cancel remaining tasks
        }
        for (;;) {                                    // possibly replace
            WorkQueue[] ws; int m, sp;
            if (tryTerminate(false, false) || w == null || w.array == null ||
                (runState & STOP) != 0 || (ws = workQueues) == null ||
                (m = ws.length - 1) < 0)              // already terminating
                break;
            if ((sp = (int)(c = ctl)) != 0) {         // wake up replacement
                if (tryRelease(c, ws[sp & m], AC_UNIT))
                    break;
            }
            else if (ex != null && (c & ADD_WORKER) != 0L) {
                tryAddWorker(c);                      // create replacement
                break;
            }
            else                                      // don't need replacement
                break;
        }
        if (ex == null)                               // help clean on way out
            ForkJoinTask.helpExpungeStaleExceptions();
        else                                          // rethrow
            ForkJoinTask.rethrow(ex);
    }
 
    // Signalling
 
    /**
     * Tries to create or activate a worker if too few are active.
     *
     * @param ws the worker array to use to find signallees
     * @param q a WorkQueue --if non-null, don't retry if now empty
     */
    final void signalWork(WorkQueue[] ws, WorkQueue q) {
        long c; int sp, i; WorkQueue v; Thread p;
        while ((c = ctl) < 0L) {                       // too few active
            if ((sp = (int)c) == 0) {                  // no idle workers
                if ((c & ADD_WORKER) != 0L)            // too few workers
                    tryAddWorker(c);
                break;
            }
            if (ws == null)                            // unstarted/terminated
                break;
            if (ws.length <= (i = sp & SMASK))         // terminated
                break;
            if ((v = ws[i]) == null)                   // terminating
                break;
            int vs = (sp + SS_SEQ) & ~INACTIVE;        // next scanState
            int d = sp - v.scanState;                  // screen CAS
            long nc = (UC_MASK & (c + AC_UNIT)) | (SP_MASK & v.stackPred);
            if (d == 0 && U.compareAndSwapLong(this, CTL, c, nc)) {
                v.scanState = vs;                      // activate v
                if ((p = v.parker) != null)
                    U.unpark(p);
                break;
            }
            if (q != null && q.base == q.top)          // no more work
                break;
        }
    }
 
    /**
     * Signals and releases worker v if it is top of idle worker
     * stack.  This performs a one-shot version of signalWork only if
     * there is (apparently) at least one idle worker.
     *
     * @param c incoming ctl value
     * @param v if non-null, a worker
     * @param inc the increment to active count (zero when compensating)
     * @return true if successful
     */
    private boolean tryRelease(long c, WorkQueue v, long inc) {
        int sp = (int)c, vs = (sp + SS_SEQ) & ~INACTIVE; Thread p;
        if (v != null && v.scanState == sp) {          // v is at top of stack
            long nc = (UC_MASK & (c + inc)) | (SP_MASK & v.stackPred);
            if (U.compareAndSwapLong(this, CTL, c, nc)) {
                v.scanState = vs;
                if ((p = v.parker) != null)
                    U.unpark(p);
                return true;
            }
        }
        return false;
    }
 
    // Scanning for tasks
 
    /**
     * Top-level runloop for workers, called by ForkJoinWorkerThread.run.
     */
    final void runWorker(WorkQueue w) {
        w.growArray();                   // allocate queue
        int seed = w.hint;               // initially holds randomization hint
        int r = (seed == 0) ? 1 : seed;  // avoid 0 for xorShift
        for (ForkJoinTask<?> t;;) {
            if ((t = scan(w, r)) != null)
                w.runTask(t);
            else if (!awaitWork(w, r))
                break;
            r ^= r << 13; r ^= r >>> 17; r ^= r << 5; // xorshift
        }
    }
 
    /**
     * 扫描并试图窃取顶级任务。随机扫描在一个随机的位置开始,在明显的争用,
     * 否则继续线性直到达到连续两个空经过校验和相同的所有队列(总结每个队列,
     * 每个基本指数,在每个偷),此时工人试图灭活然后re-scans,试图重新激活(本
     * 身或其他工人)如果找到一个任务;否则返回null等待工作。以其他方式扫描尽
     * 可能少的内存，以减少对其他扫描线程的干扰。
     *
     * @param w the worker (via its WorkQueue)
     * @param r a random seed
     * @return a task, or null if none found
     */
    private ForkJoinTask<?> scan(WorkQueue w, int r) {
        WorkQueue[] ws; int m;
        if ((ws = workQueues) != null && (m = ws.length - 1) > 0 && w != null) {
            int ss = w.scanState;                     // initially non-negative
            for (int origin = r & m, k = origin, oldSum = 0, checkSum = 0;;) {
                WorkQueue q; ForkJoinTask<?>[] a; ForkJoinTask<?> t;
                int b, n; long c;
                if ((q = ws[k]) != null) {
                    if ((n = (b = q.base) - q.top) < 0 &&
                        (a = q.array) != null) {      // non-empty
                        long i = (((a.length - 1) & b) << ASHIFT) + ABASE;
                        if ((t = ((ForkJoinTask<?>)
                                  U.getObjectVolatile(a, i))) != null &&
                            q.base == b) {
                            if (ss >= 0) {
                                if (U.compareAndSwapObject(a, i, t, null)) {
                                    q.base = b + 1;
                                    if (n < -1)       // signal others
                                        signalWork(ws, q);
                                    return t;
                                }
                            }
                            else if (oldSum == 0 &&   // try to activate
                                     w.scanState < 0)
                                tryRelease(c = ctl, ws[m & (int)c], AC_UNIT);
                        }
                        if (ss < 0)                   // refresh
                            ss = w.scanState;
                        r ^= r << 1; r ^= r >>> 3; r ^= r << 10;
                        origin = k = r & m;           // move and rescan
                        oldSum = checkSum = 0;
                        continue;
                    }
                    checkSum += b;
                }
                if ((k = (k + 1) & m) == origin) {    // continue until stable
                    if ((ss >= 0 || (ss == (ss = w.scanState))) &&
                        oldSum == (oldSum = checkSum)) {
                        if (ss < 0 || w.qlock < 0)    // already inactive
                            break;
                        int ns = ss | INACTIVE;       // try to inactivate
                        long nc = ((SP_MASK & ns) |
                                   (UC_MASK & ((c = ctl) - AC_UNIT)));
                        w.stackPred = (int)c;         // hold prev stack top
                        U.putInt(w, QSCANSTATE, ns);
                        if (U.compareAndSwapLong(this, CTL, c, nc))
                            ss = ns;
                        else
                            w.scanState = ss;         // back out
                    }
                    checkSum = 0;
                }
            }
        }
        return null;
    }
 
    /**
     * 可能阻塞正在等待任务被窃取的worker w，或者在该worker终止时返回false。
     * 如果灭活w已导致池变为静态，则检查池是否终止，并且，只要这不是惟一的工作者，
     * 就会等待指定的时间。在超时时，如果ctl没有更改，则终止该工作程序，
     * 这将唤醒另一个工作程序，从而可能重复此过程。
     *
     * @param w the calling worker
     * @param r a random seed (for spins)
     * @return false if the worker should terminate
     */
    private boolean awaitWork(WorkQueue w, int r) {
        if (w == null || w.qlock < 0)                 // w is terminating
            return false;
        for (int pred = w.stackPred, spins = SPINS, ss;;) {
            if ((ss = w.scanState) >= 0)
                break;
            else if (spins > 0) {
                r ^= r << 6; r ^= r >>> 21; r ^= r << 7;
                if (r >= 0 && --spins == 0) {         // randomize spins
                    WorkQueue v; WorkQueue[] ws; int s, j; AtomicLong sc;
                    if (pred != 0 && (ws = workQueues) != null &&
                        (j = pred & SMASK) < ws.length &&
                        (v = ws[j]) != null &&        // see if pred parking
                        (v.parker == null || v.scanState >= 0))
                        spins = SPINS;                // continue spinning
                }
            }
            else if (w.qlock < 0)                     // recheck after spins
                return false;
            else if (!Thread.interrupted()) {
                long c, prevctl, parkTime, deadline;
                int ac = (int)((c = ctl) >> AC_SHIFT) + (config & SMASK);
                if ((ac <= 0 && tryTerminate(false, false)) ||
                    (runState & STOP) != 0)           // pool terminating
                    return false;
                if (ac <= 0 && ss == (int)c) {        // is last waiter
                    prevctl = (UC_MASK & (c + AC_UNIT)) | (SP_MASK & pred);
                    int t = (short)(c >>> TC_SHIFT);  // shrink excess spares
                    if (t > 2 && U.compareAndSwapLong(this, CTL, c, prevctl))
                        return false;                 // else use timed wait
                    parkTime = IDLE_TIMEOUT * ((t >= 0) ? 1 : 1 - t);
                    deadline = System.nanoTime() + parkTime - TIMEOUT_SLOP;
                }
                else
                    prevctl = parkTime = deadline = 0L;
                Thread wt = Thread.currentThread();
                U.putObject(wt, PARKBLOCKER, this);   // emulate LockSupport
                w.parker = wt;
                if (w.scanState < 0 && ctl == c)      // recheck before park
                    U.park(false, parkTime);
                U.putOrderedObject(w, QPARKER, null);
                U.putObject(wt, PARKBLOCKER, null);
                if (w.scanState >= 0)
                    break;
                if (parkTime != 0L && ctl == c &&
                    deadline - System.nanoTime() <= 0L &&
                    U.compareAndSwapLong(this, CTL, c, prevctl))
                    return false;                     // shrink pool
            }
        }
        return true;
    }
 
    // Joining tasks
 
    /**
     * 试图在目标的计算范围内窃取和运行任务。
     * 用顶级算法的一个变体，仅限于以给定任务为祖先的任务:它更喜欢从工作者自己
     * 的队列(通过popCC)弹出并运行符合条件的任务。否则，它会扫描其他进程，
     * 在争用或执行时随机移动，根据校验和(通过返回代码frob pollAndExecCC)
     * 决定放弃。maxTasks参数支持外部使用;内部调用使用0，允许无界的步骤(外部调用捕捉非正值)。
     *
     * @param w caller
     * @param maxTasks if non-zero, the maximum number of other tasks to run
     * @return task status on exit
     */
    final int helpComplete(WorkQueue w, CountedCompleter<?> task,
                           int maxTasks) {
        WorkQueue[] ws; int s = 0, m;
        if ((ws = workQueues) != null && (m = ws.length - 1) >= 0 &&
            task != null && w != null) {
            int mode = w.config;                 // for popCC
            int r = w.hint ^ w.top;              // arbitrary seed for origin
            int origin = r & m;                  // first queue to scan
            int h = 1;                           // 1:ran, >1:contended, <0:hash
            for (int k = origin, oldSum = 0, checkSum = 0;;) {
                CountedCompleter<?> p; WorkQueue q;
                if ((s = task.status) < 0)
                    break;
                if (h == 1 && (p = w.popCC(task, mode)) != null) {
                    p.doExec();                  // run local task
                    if (maxTasks != 0 && --maxTasks == 0)
                        break;
                    origin = k;                  // reset
                    oldSum = checkSum = 0;
                }
                else {                           // poll other queues
                    if ((q = ws[k]) == null)
                        h = 0;
                    else if ((h = q.pollAndExecCC(task)) < 0)
                        checkSum += h;
                    if (h > 0) {
                        if (h == 1 && maxTasks != 0 && --maxTasks == 0)
                            break;
                        r ^= r << 13; r ^= r >>> 17; r ^= r << 5; // xorshift
                        origin = k = r & m;      // move and restart
                        oldSum = checkSum = 0;
                    }
                    else if ((k = (k + 1) & m) == origin) {
                        if (oldSum == (oldSum = checkSum))
                            break;
                        checkSum = 0;
                    }
                }
            }
        }
        return s;
    }
 
    /**
     * 试图为给定任务的窃取者定位和执行任务，或者反过来，跟踪
     * currentSteal—> currentJoin链接，寻找在给定任务的后代上工作的线程，
     * 并使用非空队列来窃取和执行任务。在等待连接时对这个方法的第一次调用通常
     * 需要进行扫描/搜索(这是可以的，因为连接者没有更好的事情要做)，但是这个
     * 方法会在workers中留下提示来加快后续调用。
     *
     * @param w caller
     * @param task the task to join
     */
    private void helpStealer(WorkQueue w, ForkJoinTask<?> task) {
        WorkQueue[] ws = workQueues;
        int oldSum = 0, checkSum, m;
        if (ws != null && (m = ws.length - 1) >= 0 && w != null &&
            task != null) {
            do {                                       // restart point
                checkSum = 0;                          // for stability check
                ForkJoinTask<?> subtask;
                WorkQueue j = w, v;                    // v is subtask stealer
                descent: for (subtask = task; subtask.status >= 0; ) {
                    for (int h = j.hint | 1, k = 0, i; ; k += 2) {
                        if (k > m)                     // can't find stealer
                            break descent;
                        if ((v = ws[i = (h + k) & m]) != null) {
                            if (v.currentSteal == subtask) {
                                j.hint = i;
                                break;
                            }
                            checkSum += v.base;
                        }
                    }
                    for (;;) {                         // help v or descend
                        ForkJoinTask<?>[] a; int b;
                        checkSum += (b = v.base);
                        ForkJoinTask<?> next = v.currentJoin;
                        if (subtask.status < 0 || j.currentJoin != subtask ||
                            v.currentSteal != subtask) // stale
                            break descent;
                        if (b - v.top >= 0 || (a = v.array) == null) {
                            if ((subtask = next) == null)
                                break descent;
                            j = v;
                            break;
                        }
                        int i = (((a.length - 1) & b) << ASHIFT) + ABASE;
                        ForkJoinTask<?> t = ((ForkJoinTask<?>)
                                             U.getObjectVolatile(a, i));
                        if (v.base == b) {
                            if (t == null)             // stale
                                break descent;
                            if (U.compareAndSwapObject(a, i, t, null)) {
                                v.base = b + 1;
                                ForkJoinTask<?> ps = w.currentSteal;
                                int top = w.top;
                                do {
                                    U.putOrderedObject(w, QCURRENTSTEAL, t);
                                    t.doExec();        // clear local tasks too
                                } while (task.status >= 0 &&
                                         w.top != top &&
                                         (t = w.pop()) != null);
                                U.putOrderedObject(w, QCURRENTSTEAL, ps);
                                if (w.base != w.top)
                                    return;            // can't further help
                            }
                        }
                    }
                }
            } while (task.status >= 0 && oldSum != (oldSum = checkSum));
        }
    }
 
    /**
     * 尝试减少活动计数(有时是隐式的)，并可能释放或创建一个补偿worker，
     * 为阻塞做准备。在争用、检测到过时、不稳定或终止时返回false(调用者可重试)。
     *
     * @param w caller
     */
    private boolean tryCompensate(WorkQueue w) {
        boolean canBlock;
        WorkQueue[] ws; long c; int m, pc, sp;
        if (w == null || w.qlock < 0 ||           // caller terminating
            (ws = workQueues) == null || (m = ws.length - 1) <= 0 ||
            (pc = config & SMASK) == 0)           // parallelism disabled
            canBlock = false;
        else if ((sp = (int)(c = ctl)) != 0)      // release idle worker
            canBlock = tryRelease(c, ws[sp & m], 0L);
        else {
            int ac = (int)(c >> AC_SHIFT) + pc;
            int tc = (short)(c >> TC_SHIFT) + pc;
            int nbusy = 0;                        // validate saturation
            for (int i = 0; i <= m; ++i) {        // two passes of odd indices
                WorkQueue v;
                if ((v = ws[((i << 1) | 1) & m]) != null) {
                    if ((v.scanState & SCANNING) != 0)
                        break;
                    ++nbusy;
                }
            }
            if (nbusy != (tc << 1) || ctl != c)
                canBlock = false;                 // unstable or stale
            else if (tc >= pc && ac > 1 && w.isEmpty()) {
                long nc = ((AC_MASK & (c - AC_UNIT)) |
                           (~AC_MASK & c));       // uncompensated
                canBlock = U.compareAndSwapLong(this, CTL, c, nc);
            }
            else if (tc >= MAX_CAP ||
                     (this == common && tc >= pc + commonMaxSpares))
                throw new RejectedExecutionException(
                    "Thread limit exceeded replacing blocked worker");
            else {                                // similar to tryAddWorker
                boolean add = false; int rs;      // CAS within lock
                long nc = ((AC_MASK & c) |
                           (TC_MASK & (c + TC_UNIT)));
                if (((rs = lockRunState()) & STOP) == 0)
                    add = U.compareAndSwapLong(this, CTL, c, nc);
                unlockRunState(rs, rs & ~RSLOCK);
                canBlock = add && createWorker(); // throws on exception
            }
        }
        return canBlock;
    }
 
    /**
     * Helps and/or blocks until the given task is done or timeout.
     *
     * @param w caller
     * @param task the task
     * @param deadline for timed waits, if nonzero
     * @return task status on exit
     */
    final int awaitJoin(WorkQueue w, ForkJoinTask<?> task, long deadline) {
        int s = 0;
        if (task != null && w != null) {
            ForkJoinTask<?> prevJoin = w.currentJoin;
            U.putOrderedObject(w, QCURRENTJOIN, task);
            CountedCompleter<?> cc = (task instanceof CountedCompleter) ?
                (CountedCompleter<?>)task : null;
            for (;;) {
                if ((s = task.status) < 0)
                    break;
                if (cc != null)
                    helpComplete(w, cc, 0);
                else if (w.base == w.top || w.tryRemoveAndExec(task))
                    helpStealer(w, task);
                if ((s = task.status) < 0)
                    break;
                long ms, ns;
                if (deadline == 0L)
                    ms = 0L;
                else if ((ns = deadline - System.nanoTime()) <= 0L)
                    break;
                else if ((ms = TimeUnit.NANOSECONDS.toMillis(ns)) <= 0L)
                    ms = 1L;
                if (tryCompensate(w)) {
                    task.internalWait(ms);
                    U.getAndAddLong(this, CTL, AC_UNIT);
                }
            }
            U.putOrderedObject(w, QCURRENTJOIN, prevJoin);
        }
        return s;
    }
 
    // Specialized scanning
 
    /**
     * 返回一个(可能)非空的窃取队列，如果在扫描期间发现一个队列；否则为else null。
     * 如果调用者在尝试使用队列时该方法为空，则必须重试此方法。
     */
    private WorkQueue findNonEmptyStealQueue() {
        WorkQueue[] ws; int m;  // one-shot version of scan loop
        int r = ThreadLocalRandom.nextSecondarySeed();
        if ((ws = workQueues) != null && (m = ws.length - 1) >= 0) {
            for (int origin = r & m, k = origin, oldSum = 0, checkSum = 0;;) {
                WorkQueue q; int b;
                if ((q = ws[k]) != null) {
                    if ((b = q.base) - q.top < 0)
                        return q;
                    checkSum += b;
                }
                if ((k = (k + 1) & m) == origin) {
                    if (oldSum == (oldSum = checkSum))
                        break;
                    checkSum = 0;
                }
            }
        }
        return null;
    }
 
    /**
     * 运行任务直到{@code isQuiescent()}。我们利用活动计数ctl维护，
     * 但不是在找不到任务时阻塞，而是重新扫描，直到其他所有人也找不到任务。
     */
    final void helpQuiescePool(WorkQueue w) {
        ForkJoinTask<?> ps = w.currentSteal; // save context
        for (boolean active = true;;) {
            long c; WorkQueue q; ForkJoinTask<?> t; int b;
            w.execLocalTasks();     // run locals before each scan
            if ((q = findNonEmptyStealQueue()) != null) {
                if (!active) {      // re-establish active count
                    active = true;
                    U.getAndAddLong(this, CTL, AC_UNIT);
                }
                if ((b = q.base) - q.top < 0 && (t = q.pollAt(b)) != null) {
                    U.putOrderedObject(w, QCURRENTSTEAL, t);
                    t.doExec();
                    if (++w.nsteals < 0)
                        w.transferStealCount(this);
                }
            }
            else if (active) {      // decrement active count without queuing
                long nc = (AC_MASK & ((c = ctl) - AC_UNIT)) | (~AC_MASK & c);
                if ((int)(nc >> AC_SHIFT) + (config & SMASK) <= 0)
                    break;          // bypass decrement-then-increment
                if (U.compareAndSwapLong(this, CTL, c, nc))
                    active = false;
            }
            else if ((int)((c = ctl) >> AC_SHIFT) + (config & SMASK) <= 0 &&
                     U.compareAndSwapLong(this, CTL, c, c + AC_UNIT))
                break;
        }
        U.putOrderedObject(w, QCURRENTSTEAL, ps);
    }
 
    /**
     * 获取并移除给定工作线程的本地任务或窃取的任务。
     *
     * @return a task, if available
     */
    final ForkJoinTask<?> nextTaskFor(WorkQueue w) {
        for (ForkJoinTask<?> t;;) {
            WorkQueue q; int b;
            if ((t = w.nextLocalTask()) != null)
                return t;
            if ((q = findNonEmptyStealQueue()) == null)
                return null;
            if ((b = q.base) - q.top < 0 && (t = q.pollAt(b)) != null)
                return t;
        }
    }
 
    /**
     * 当程序员、框架、工具或语言很少或完全不了解任务粒度时，返回用于任务划分的廉价启发式向导。
     * 从本质上讲，通过提供这种方法，我们只询问用户开销与预期吞吐量及其差异之间的权衡，而不询
     * 问划分任务的精细程度。
     * 在稳定状态的严格(树形结构)计算中，每个线程都可以窃取足够的任务，以使其他线程保持活动状
     * 态。归纳起来，如果所有线程都遵循相同的规则，那么每个线程应该只提供固定数量的任务。
     *
     * 有用的最小常数是1。但是使用1的值需要在每次偷取时立即补充以维持足够的任务，这是不可行的。
     * 此外，所提供任务的分区/粒度应该最小化偷取率，这通常意味着接近计算树顶部的线程应该比接近
     * 计算树底部的线程生成更多。在完全稳定状态下，每个线程的计算树大致处于相同的级别。然而，
     * 产生额外的任务会摊销进度的不确定性和扩散的假设。
     *
     * 因此，用户将希望使用大于1的值(但不要太大)，以消除暂时的短缺和对冲不平衡的进展;以抵消额
     * 外任务开销的成本。我们让用户选择一个阈值来与此调用的结果进行比较，以指导决策，但建议使
     * 用诸如3这样的值。
     * 当所有线程都处于活动状态时，严格地在局部估计剩余通常是可以的。在稳定状态下，如果一个线
     * 程保持两个剩余任务，那么其他线程也会保持。我们可以使用估计的队列长度。然而，在某些非稳
     * 态条件下(斜坡上升、斜坡下降、其他档位)，这种策略本身就会导致严重的错误估计。我们可以通
     * 过进一步考虑“空闲”线程的数量来检测其中的许多，已知这些线程没有任何排队的任务，因此可以
     * 通过(#idle/#active)线程的因素进行补偿。
     */
    static int getSurplusQueuedTaskCount() {
        Thread t; ForkJoinWorkerThread wt; ForkJoinPool pool; WorkQueue q;
        if (((t = Thread.currentThread()) instanceof ForkJoinWorkerThread)) {
            int p = (pool = (wt = (ForkJoinWorkerThread)t).pool).
                config & SMASK;
            int n = (q = wt.workQueue).top - q.base;
            int a = (int)(pool.ctl >> AC_SHIFT) + p;
            return n - (a > (p >>>= 1) ? 0 :
                        a > (p >>>= 1) ? 1 :
                        a > (p >>>= 1) ? 2 :
                        a > (p >>>= 1) ? 4 :
                        8);
        }
        return 0;
    }
 
    //  Termination
 
    /**
     * 可能启动和/或完成终止。
     *
     * @param now if true, unconditionally terminate, else only
     * if no work and no active workers
     * @param enable if true, enable shutdown when next possible
     * @return true if now terminating or terminated
     */
    private boolean tryTerminate(boolean now, boolean enable) {
        int rs;
        if (this == common)                       // cannot shut down
            return false;
        if ((rs = runState) >= 0) {
            if (!enable)
                return false;
            rs = lockRunState();                  // enter SHUTDOWN phase
            unlockRunState(rs, (rs & ~RSLOCK) | SHUTDOWN);
        }
 
        if ((rs & STOP) == 0) {
            if (!now) {                           // check quiescence
                for (long oldSum = 0L;;) {        // repeat until stable
                    WorkQueue[] ws; WorkQueue w; int m, b; long c;
                    long checkSum = ctl;
                    if ((int)(checkSum >> AC_SHIFT) + (config & SMASK) > 0)
                        return false;             // still active workers
                    if ((ws = workQueues) == null || (m = ws.length - 1) <= 0)
                        break;                    // check queues
                    for (int i = 0; i <= m; ++i) {
                        if ((w = ws[i]) != null) {
                            if ((b = w.base) != w.top || w.scanState >= 0 ||
                                w.currentSteal != null) {
                                tryRelease(c = ctl, ws[m & (int)c], AC_UNIT);
                                return false;     // arrange for recheck
                            }
                            checkSum += b;
                            if ((i & 1) == 0)
                                w.qlock = -1;     // try to disable external
                        }
                    }
                    if (oldSum == (oldSum = checkSum))
                        break;
                }
            }
            if ((runState & STOP) == 0) {
                rs = lockRunState();              // enter STOP phase
                unlockRunState(rs, (rs & ~RSLOCK) | STOP);
            }
        }
 
        int pass = 0;                             // 3 passes to help terminate
        for (long oldSum = 0L;;) {                // or until done or stable
            WorkQueue[] ws; WorkQueue w; ForkJoinWorkerThread wt; int m;
            long checkSum = ctl;
            if ((short)(checkSum >>> TC_SHIFT) + (config & SMASK) <= 0 ||
                (ws = workQueues) == null || (m = ws.length - 1) <= 0) {
                if ((runState & TERMINATED) == 0) {
                    rs = lockRunState();          // done
                    unlockRunState(rs, (rs & ~RSLOCK) | TERMINATED);
                    synchronized (this) { notifyAll(); } // for awaitTermination
                }
                break;
            }
            for (int i = 0; i <= m; ++i) {
                if ((w = ws[i]) != null) {
                    checkSum += w.base;
                    w.qlock = -1;                 // try to disable
                    if (pass > 0) {
                        w.cancelAll();            // clear queue
                        if (pass > 1 && (wt = w.owner) != null) {
                            if (!wt.isInterrupted()) {
                                try {             // unblock join
                                    wt.interrupt();
                                } catch (Throwable ignore) {
                                }
                            }
                            if (w.scanState < 0)
                                U.unpark(wt);     // wake up
                        }
                    }
                }
            }
            if (checkSum != oldSum) {             // unstable
                oldSum = checkSum;
                pass = 0;
            }
            else if (pass > 3 && pass > m)        // can't further help
                break;
            else if (++pass > 1) {                // try to dequeue
                long c; int j = 0, sp;            // bound attempts
                while (j++ <= m && (sp = (int)(c = ctl)) != 0)
                    tryRelease(c, ws[sp & m], AC_UNIT);
            }
        }
        return true;
    }
 
    // External operations
 
    /**
     * 完整版的externalPush，处理不常见的情况，以及在第一次向池提交第
     * 一个任务时执行二次初始化。它还可以检测到外部线程的首次提交，如果
     * 索引队列为空或争用，则创建一个新的共享队列。
     *
     * @param task the task. Caller must ensure non-null.
     */
    private void externalSubmit(ForkJoinTask<?> task) {
        int r;                                    // initialize caller's probe
        if ((r = ThreadLocalRandom.getProbe()) == 0) {
            ThreadLocalRandom.localInit();
            r = ThreadLocalRandom.getProbe();
        }
        for (;;) {
            WorkQueue[] ws; WorkQueue q; int rs, m, k;
            boolean move = false;
            if ((rs = runState) < 0) {
                tryTerminate(false, false);     // help terminate
                throw new RejectedExecutionException();
            }
            else if ((rs & STARTED) == 0 ||     // initialize
                     ((ws = workQueues) == null || (m = ws.length - 1) < 0)) {
                int ns = 0;
                rs = lockRunState();
                try {
                    if ((rs & STARTED) == 0) {
                        U.compareAndSwapObject(this, STEALCOUNTER, null,
                                               new AtomicLong());
                        // create workQueues array with size a power of two
                        int p = config & SMASK; // ensure at least 2 slots
                        int n = (p > 1) ? p - 1 : 1;
                        n |= n >>> 1; n |= n >>> 2;  n |= n >>> 4;
                        n |= n >>> 8; n |= n >>> 16; n = (n + 1) << 1;
                        workQueues = new WorkQueue[n];
                        ns = STARTED;
                    }
                } finally {
                    unlockRunState(rs, (rs & ~RSLOCK) | ns);
                }
            }
            else if ((q = ws[k = r & m & SQMASK]) != null) {
                if (q.qlock == 0 && U.compareAndSwapInt(q, QLOCK, 0, 1)) {
                    ForkJoinTask<?>[] a = q.array;
                    int s = q.top;
                    boolean submitted = false; // initial submission or resizing
                    try {                      // locked version of push
                        if ((a != null && a.length > s + 1 - q.base) ||
                            (a = q.growArray()) != null) {
                            int j = (((a.length - 1) & s) << ASHIFT) + ABASE;
                            U.putOrderedObject(a, j, task);
                            U.putOrderedInt(q, QTOP, s + 1);
                            submitted = true;
                        }
                    } finally {
                        U.compareAndSwapInt(q, QLOCK, 1, 0);
                    }
                    if (submitted) {
                        signalWork(ws, q);
                        return;
                    }
                }
                move = true;                   // move on failure
            }
            else if (((rs = runState) & RSLOCK) == 0) { // create new queue
                q = new WorkQueue(this, null);
                q.hint = r;
                q.config = k | SHARED_QUEUE;
                q.scanState = INACTIVE;
                rs = lockRunState();           // publish index
                if (rs > 0 &&  (ws = workQueues) != null &&
                    k < ws.length && ws[k] == null)
                    ws[k] = q;                 // else terminated
                unlockRunState(rs, rs & ~RSLOCK);
            }
            else
                move = true;                   // move if busy
            if (move)
                r = ThreadLocalRandom.advanceProbe(r);
        }
    }
 
    /**
     * Tries to add the given task to a submission queue at
     * submitter's current queue. Only the (vastly) most common path
     * is directly handled in this method, while screening for need
     * for externalSubmit.
     *
     * @param task the task. Caller must ensure non-null.
     */
    final void externalPush(ForkJoinTask<?> task) {
        WorkQueue[] ws; WorkQueue q; int m;
        int r = ThreadLocalRandom.getProbe();
        int rs = runState;
        if ((ws = workQueues) != null && (m = (ws.length - 1)) >= 0 &&
            (q = ws[m & r & SQMASK]) != null && r != 0 && rs > 0 &&
            U.compareAndSwapInt(q, QLOCK, 0, 1)) {
            ForkJoinTask<?>[] a; int am, n, s;
            if ((a = q.array) != null &&
                (am = a.length - 1) > (n = (s = q.top) - q.base)) {
                int j = ((am & s) << ASHIFT) + ABASE;
                U.putOrderedObject(a, j, task);
                U.putOrderedInt(q, QTOP, s + 1);
                U.putOrderedInt(q, QLOCK, 0);
                if (n <= 1)
                    signalWork(ws, q);
                return;
            }
            U.compareAndSwapInt(q, QLOCK, 1, 0);
        }
        externalSubmit(task);
    }
 
    /**
     * Returns common pool queue for an external thread.
     */
    static WorkQueue commonSubmitterQueue() {
        ForkJoinPool p = common;
        int r = ThreadLocalRandom.getProbe();
        WorkQueue[] ws; int m;
        return (p != null && (ws = p.workQueues) != null &&
                (m = ws.length - 1) >= 0) ?
            ws[m & r & SQMASK] : null;
    }
 
    /**
     * Performs tryUnpush for an external submitter: Finds queue,
     * locks if apparently non-empty, validates upon locking, and
     * adjusts top. Each check can fail but rarely does.
     */
    final boolean tryExternalUnpush(ForkJoinTask<?> task) {
        WorkQueue[] ws; WorkQueue w; ForkJoinTask<?>[] a; int m, s;
        int r = ThreadLocalRandom.getProbe();
        if ((ws = workQueues) != null && (m = ws.length - 1) >= 0 &&
            (w = ws[m & r & SQMASK]) != null &&
            (a = w.array) != null && (s = w.top) != w.base) {
            long j = (((a.length - 1) & (s - 1)) << ASHIFT) + ABASE;
            if (U.compareAndSwapInt(w, QLOCK, 0, 1)) {
                if (w.top == s && w.array == a &&
                    U.getObject(a, j) == task &&
                    U.compareAndSwapObject(a, j, task, null)) {
                    U.putOrderedInt(w, QTOP, s - 1);
                    U.putOrderedInt(w, QLOCK, 0);
                    return true;
                }
                U.compareAndSwapInt(w, QLOCK, 1, 0);
            }
        }
        return false;
    }
 
    /**
     * Performs helpComplete for an external submitter.
     */
    final int externalHelpComplete(CountedCompleter<?> task, int maxTasks) {
        WorkQueue[] ws; int n;
        int r = ThreadLocalRandom.getProbe();
        return ((ws = workQueues) == null || (n = ws.length) == 0) ? 0 :
            helpComplete(ws[(n - 1) & r & SQMASK], task, maxTasks);
    }
 
    // Exported methods
 
    // Constructors
 
    /**
     * 创建并行度等于{@link java.lang的{@code ForkJoinPool}。运行时
     * #availableProcessors}，使用{@linkplain #defaultForkJoinWorkerThreadFactory
     * 默认线程工厂}，没有UncaughtExceptionHandler，非异步后进先出处理模式。
     *
     * @throws SecurityException if a security manager exists and
     *         the caller is not permitted to modify threads
     *         because it does not hold {@link
     *         java.lang.RuntimePermission}{@code ("modifyThread")}
     */
    public ForkJoinPool() {
        this(Math.min(MAX_CAP, Runtime.getRuntime().availableProcessors()),
             defaultForkJoinWorkerThreadFactory, null, false);
    }
 
    /**
     * 使用指定的并行级别创建{@code ForkJoinPool}、{@linkplain
     * #defaultForkJoinWorkerThreadFactory默认线程工厂}、没有UncaughtExceptionHandler
     * 和非异步后进先出处理模式。
     *
     * @param parallelism the parallelism level
     * @throws IllegalArgumentException if parallelism less than or
     *         equal to zero, or greater than implementation limit
     * @throws SecurityException if a security manager exists and
     *         the caller is not permitted to modify threads
     *         because it does not hold {@link
     *         java.lang.RuntimePermission}{@code ("modifyThread")}
     */
    public ForkJoinPool(int parallelism) {
        this(parallelism, defaultForkJoinWorkerThreadFactory, null, false);
    }
 
    /**
     * Creates a {@code ForkJoinPool} with the given parameters.
     *
     * asyncMode如果为真，则为从未连接的分叉任务建立本地先进先出调度模式。
     * 在工作线程只处理事件式异步任务的应用程序中，此模式可能比默认的基于本地堆栈的模式更合适。
     * handler默认=null；
     * @throws IllegalArgumentException if parallelism less than or
     *         equal to zero, or greater than implementation limit
     * @throws NullPointerException if the factory is null
     * @throws SecurityException if a security manager exists and
     *         the caller is not permitted to modify threads
     *         because it does not hold {@link
     *         java.lang.RuntimePermission}{@code ("modifyThread")}
     */
    public ForkJoinPool(int parallelism,
                        ForkJoinWorkerThreadFactory factory,
                        UncaughtExceptionHandler handler,
                        boolean asyncMode) {
        this(checkParallelism(parallelism),
             checkFactory(factory),
             handler,
             asyncMode ? FIFO_QUEUE : LIFO_QUEUE,
             "ForkJoinPool-" + nextPoolId() + "-worker-");
        checkPermission();
    }
 
    private static int checkParallelism(int parallelism) {
        if (parallelism <= 0 || parallelism > MAX_CAP)
            throw new IllegalArgumentException();
        return parallelism;
    }
 
    private static ForkJoinWorkerThreadFactory checkFactory
        (ForkJoinWorkerThreadFactory factory) {
        if (factory == null)
            throw new NullPointerException();
        return factory;
    }
 
    /**
     * Creates a {@code ForkJoinPool} with the given parameters, without
     * any security checks or parameter validation.  Invoked directly by
     * makeCommonPool.
     */
    private ForkJoinPool(int parallelism,
                         ForkJoinWorkerThreadFactory factory,
                         UncaughtExceptionHandler handler,
                         int mode,
                         String workerNamePrefix) {
        this.workerNamePrefix = workerNamePrefix;
        this.factory = factory;
        this.ueh = handler;
        this.config = (parallelism & SMASK) | mode;
        long np = (long)(-parallelism); // offset ctl counts
        this.ctl = ((np << AC_SHIFT) & AC_MASK) | ((np << TC_SHIFT) & TC_MASK);
    }
 
    /**
     * 返回公共池实例。这个池是静态构建的;它的运行状态不受试图{@link #shutdown}或{@link
     * #shutdownNow}的影响。但是，这个池和任何正在进行的处理将在程序{@link System#exit}
     * 后自动终止。任何依赖异步任务处理在程序终止之前完成的程序都应该调用{@code commonPool()。
     * {@link # awaitquiescent awaitQuiescence}，退出前。
     *
     * @return the common pool instance
     * @since 1.8
     */
    public static ForkJoinPool commonPool() {
        // assert common != null : "static init error";
        return common;
    }
 
    // Execution methods
 
    /**
     * 执行给定的任务，完成后返回结果。如果计算遇到未检查的异常或错误，将作为调用的
     * 结果重新抛出。重新抛出的异常与常规异常的行为方式相同，但在可能的情况下，包含
     * 当前线程和实际遇到异常的线程的堆栈跟踪(例如使用{@code ex.printStackTrace()}
     * 显示);最低限度只显示后者。
     *
     * @param task the task
     * @param <T> the type of the task's result
     * @return the task's result
     * @throws NullPointerException if the task is null
     * @throws RejectedExecutionException if the task cannot be
     *         scheduled for execution
     */
    public <T> T invoke(ForkJoinTask<T> task) {
        if (task == null)
            throw new NullPointerException();
        externalPush(task);
        return task.join();
    }
 
    /**
     * 安排(异步)执行给定的任务。
     *
     * @param task the task
     * @throws NullPointerException if the task is null
     * @throws RejectedExecutionException if the task cannot be
     *         scheduled for execution
     */
    public void execute(ForkJoinTask<?> task) {
        if (task == null)
            throw new NullPointerException();
        externalPush(task);
    }
 
    // AbstractExecutorService methods
 
    /**
     * @throws NullPointerException if the task is null
     * @throws RejectedExecutionException if the task cannot be
     *         scheduled for execution
     */
    public void execute(Runnable task) {
        if (task == null)
            throw new NullPointerException();
        ForkJoinTask<?> job;
        if (task instanceof ForkJoinTask<?>) // avoid re-wrap
            job = (ForkJoinTask<?>) task;
        else
            job = new ForkJoinTask.RunnableExecuteAction(task);
        externalPush(job);
    }
 
    /**
     * Submits a ForkJoinTask for execution.
     *
     * @param task the task to submit
     * @param <T> the type of the task's result
     * @return the task
     * @throws NullPointerException if the task is null
     * @throws RejectedExecutionException if the task cannot be
     *         scheduled for execution
     */
    public <T> ForkJoinTask<T> submit(ForkJoinTask<T> task) {
        if (task == null)
            throw new NullPointerException();
        externalPush(task);
        return task;
    }
 
    /**
     * @throws NullPointerException if the task is null
     * @throws RejectedExecutionException if the task cannot be
     *         scheduled for execution
     */
    public <T> ForkJoinTask<T> submit(Callable<T> task) {
        ForkJoinTask<T> job = new ForkJoinTask.AdaptedCallable<T>(task);
        externalPush(job);
        return job;
    }
 
    /**
     * @throws NullPointerException if the task is null
     * @throws RejectedExecutionException if the task cannot be
     *         scheduled for execution
     */
    public <T> ForkJoinTask<T> submit(Runnable task, T result) {
        ForkJoinTask<T> job = new ForkJoinTask.AdaptedRunnable<T>(task, result);
        externalPush(job);
        return job;
    }
 
    /**
     * @throws NullPointerException if the task is null
     * @throws RejectedExecutionException if the task cannot be
     *         scheduled for execution
     */
    public ForkJoinTask<?> submit(Runnable task) {
        if (task == null)
            throw new NullPointerException();
        ForkJoinTask<?> job;
        if (task instanceof ForkJoinTask<?>) // avoid re-wrap
            job = (ForkJoinTask<?>) task;
        else
            job = new ForkJoinTask.AdaptedRunnableAction(task);
        externalPush(job);
        return job;
    }
 
    /**
     * @throws NullPointerException       {@inheritDoc}
     * @throws RejectedExecutionException {@inheritDoc}
     */
    public <T> List<Future<T>> invokeAll(Collection<? extends Callable<T>> tasks) {
        // In previous versions of this class, this method constructed
        // a task to run ForkJoinTask.invokeAll, but now external
        // invocation of multiple tasks is at least as efficient.
        ArrayList<Future<T>> futures = new ArrayList<>(tasks.size());
 
        boolean done = false;
        try {
            for (Callable<T> t : tasks) {
                ForkJoinTask<T> f = new ForkJoinTask.AdaptedCallable<T>(t);
                futures.add(f);
                externalPush(f);
            }
            for (int i = 0, size = futures.size(); i < size; i++)
                ((ForkJoinTask<?>)futures.get(i)).quietlyJoin();
            done = true;
            return futures;
        } finally {
            if (!done)
                for (int i = 0, size = futures.size(); i < size; i++)
                    futures.get(i).cancel(false);
        }
    }
 
    /**
     * Returns the factory used for constructing new workers.
     *
     * @return the factory used for constructing new workers
     */
    public ForkJoinWorkerThreadFactory getFactory() {
        return factory;
    }
 
    /**
     * Returns the handler for internal worker threads that terminate
     * due to unrecoverable errors encountered while executing tasks.
     *
     * @return the handler, or {@code null} if none
     */
    public UncaughtExceptionHandler getUncaughtExceptionHandler() {
        return ueh;
    }
 
    /**
     * Returns the targeted parallelism level of this pool.
     *
     * @return the targeted parallelism level of this pool
     */
    public int getParallelism() {
        int par;
        return ((par = config & SMASK) > 0) ? par : 1;
    }
 
    /**
     * Returns the targeted parallelism level of the common pool.
     *
     * @return the targeted parallelism level of the common pool
     * @since 1.8
     */
    public static int getCommonPoolParallelism() {
        return commonParallelism;
    }
 
    /**
     * 返回已启动但尚未终止的工作线程的数量。这个方法返回的结果可能与
     * {@link #getParallelism}不同，后者创建线程是为了在其他线程
     * 被协作阻塞时维护并行性。
     *
     * @return the number of worker threads
     */
    public int getPoolSize() {
        return (config & SMASK) + (short)(ctl >>> TC_SHIFT);
    }
 
    /**
     * 如果此池对从未连接的分叉任务使用本地先进先出调度模式，则返回true。
     *
     * @return {@code true} if this pool uses async mode
     */
    public boolean getAsyncMode() {
        return (config & FIFO_QUEUE) != 0;
    }
 
    /**
     * 返回未阻塞的工作线程数量的估计值，这些工作线程正在等待连接任务或其他托管同步。
     * 这种方法可能会高估正在运行的线程的数量。
     *
     * @return the number of worker threads
     */
    public int getRunningThreadCount() {
        int rc = 0;
        WorkQueue[] ws; WorkQueue w;
        if ((ws = workQueues) != null) {
            for (int i = 1; i < ws.length; i += 2) {
                if ((w = ws[i]) != null && w.isApparentlyUnblocked())
                    ++rc;
            }
        }
        return rc;
    }
 
    /**
     * 返回当前正在窃取或执行任务的线程数量的估计值。此方法可能高估了活动线程的数量。
     *
     * @return the number of active threads
     */
    public int getActiveThreadCount() {
        int r = (config & SMASK) + (int)(ctl >> AC_SHIFT);
        return (r <= 0) ? 0 : r; // suppress momentarily negative values
    }
 
    /**
     * 如果所有工作线程当前都处于空闲状态，则返回 true。 空闲工作线程是指无法获得
     * 要执行的任务的线程，因为没有任何任务可以从其他线程中窃取，并且没有对池的挂起
     * 提交。这种方法是保守的;它可能不会在所有线程空闲时立即返回 true，但是
     * 如果线程保持非活动状态，它最终会返回true。
     *
     * @return {@code true} if all threads are currently idle
     */
    public boolean isQuiescent() {
        return (config & SMASK) + (int)(ctl >> AC_SHIFT) <= 0;
    }
 
    /**
     * 返回另一个线程从一个线程的工作队列中窃取的任务总数的估计值。报告的值
     * 低估了池非静止状态下的实际偷取总数。这个值对于监视和调优fork/join程
     * 序可能很有用:通常，窃取计数应该足够高，以保持线程繁忙，但是次数应该足够低，
     * 以避免线程之间的开销和争用。
     *
     * @return the number of steals
     */
    public long getStealCount() {
        AtomicLong sc = stealCounter;
        long count = (sc == null) ? 0L : sc.get();
        WorkQueue[] ws; WorkQueue w;
        if ((ws = workQueues) != null) {
            for (int i = 1; i < ws.length; i += 2) {
                if ((w = ws[i]) != null)
                    count += w.nsteals;
            }
        }
        return count;
    }
 
    /**
     * 返回工作线程当前在队列中持有的任务总数的估计值(但不包括提交到池中尚未开始
     * 执行的任务)。这个值只是一个近似值，通过遍历池中的所有线程获得。该方法对于
     * 任务粒度的调整可能是有用的。
     *
     * @return the number of queued tasks
     */
    public long getQueuedTaskCount() {
        long count = 0;
        WorkQueue[] ws; WorkQueue w;
        if ((ws = workQueues) != null) {
            for (int i = 1; i < ws.length; i += 2) {
                if ((w = ws[i]) != null)
                    count += w.queueSize();
            }
        }
        return count;
    }
 
    /**
     * 返回提交到此池的尚未开始执行的任务数量的估计值。
     * 这种方法可能花费的时间与提交的次数成比例（ps: 遍历获取的次数）。
     *
     * @return the number of queued submissions
     */
    public int getQueuedSubmissionCount() {
        int count = 0;
        WorkQueue[] ws; WorkQueue w;
        if ((ws = workQueues) != null) {
            for (int i = 0; i < ws.length; i += 2) {
                if ((w = ws[i]) != null)
                    count += w.queueSize();
            }
        }
        return count;
    }
 
    /**
     * 如果提交给这个池的任何任务尚未开始执行，则返回  true。
     * ps: 即有任务在等待(排队)提交
     * @return {@code true} if there are any queued submissions
     */
    public boolean hasQueuedSubmissions() {
        WorkQueue[] ws; WorkQueue w;
        if ((ws = workQueues) != null) {
            for (int i = 0; i < ws.length; i += 2) {
                if ((w = ws[i]) != null && !w.isEmpty())
                    return true;
            }
        }
        return false;
    }
 
    /**
     * 删除并返回下一个可用的未执行提交。此方法可用于在具有多个池的系统中重新
     * 分配工作的该类的扩展。
     *
     * @return the next submission, or {@code null} if none
     */
    protected ForkJoinTask<?> pollSubmission() {
        WorkQueue[] ws; WorkQueue w; ForkJoinTask<?> t;
        if ((ws = workQueues) != null) {
            for (int i = 0; i < ws.length; i += 2) {
                if ((w = ws[i]) != null && (t = w.poll()) != null)
                    return t;
            }
        }
        return null;
    }
 
    /**
     * 从调度队列中删除所有未执行的提交和分叉任务，并将它们添加到给定集合中，
     * 而不更改它们的执行状态。这些可能包括人工生成或包装的任务。此方法被设
     * 计为仅在池处于静止状态时调用。在其他时间调用可能不会删除所有任务。在
     * 试图将元素添加到集合c时遇到的失败可能会导致在抛出关联异常时，元素既
     * 有可能不在集合中，也可能在集合中。如果在操作过程中修改了指
     * 定的集合，则此操作的行为未定义。
     *
     * @param c the collection to transfer elements into
     * @return the number of elements transferred
     */
    protected int drainTasksTo(Collection<? super ForkJoinTask<?>> c) {
        int count = 0;
        WorkQueue[] ws; WorkQueue w; ForkJoinTask<?> t;
        if ((ws = workQueues) != null) {
            for (int i = 0; i < ws.length; ++i) {
                if ((w = ws[i]) != null) {
                    while ((t = w.poll()) != null) {
                        c.add(t);
                        ++count;
                    }
                }
            }
        }
        return count;
    }
 
    /**
     * 返回一个字符串，该字符串标识这个池及其状态，包括运行状态、并行度级别以及工作者和任务计数的指示。
     *
     * @return a string identifying this pool, as well as its state
     */
    public String toString() {
        // Use a single pass through workQueues to collect counts
        long qt = 0L, qs = 0L; int rc = 0;
        AtomicLong sc = stealCounter;
        long st = (sc == null) ? 0L : sc.get();
        long c = ctl;
        WorkQueue[] ws; WorkQueue w;
        if ((ws = workQueues) != null) {
            for (int i = 0; i < ws.length; ++i) {
                if ((w = ws[i]) != null) {
                    int size = w.queueSize();
                    if ((i & 1) == 0)
                        qs += size;
                    else {
                        qt += size;
                        st += w.nsteals;
                        if (w.isApparentlyUnblocked())
                            ++rc;
                    }
                }
            }
        }
        int pc = (config & SMASK);
        int tc = pc + (short)(c >>> TC_SHIFT);
        int ac = pc + (int)(c >> AC_SHIFT);
        if (ac < 0) // ignore transient negative
            ac = 0;
        int rs = runState;
        String level = ((rs & TERMINATED) != 0 ? "Terminated" :
                        (rs & STOP)       != 0 ? "Terminating" :
                        (rs & SHUTDOWN)   != 0 ? "Shutting down" :
                        "Running");
        return super.toString() +
            "[" + level +
            ", parallelism = " + pc +
            ", size = " + tc +
            ", active = " + ac +
            ", running = " + rc +
            ", steals = " + st +
            ", tasks = " + qt +
            ", submissions = " + qs +
            "]";
    }
 
    /**
     * 可能会启动有序关闭，在此过程中执行以前提交的任务，但不接受任何新任务。
     * 如果这是 commonPool，则调用对执行状态没有影响。如果已经关闭，
     * 则没有其他影响。在此方法过程中同时提交的任务可能被拒绝，也可能不被拒绝。
     *
     * @throws SecurityException if a security manager exists and
     *         the caller is not permitted to modify threads
     *         because it does not hold {@link
     *         java.lang.RuntimePermission}{@code ("modifyThread")}
     */
    public void shutdown() {
        checkPermission();
        tryTerminate(false, true);
    }
 
    /**
     * 可能尝试取消和/或停止所有任务，并拒绝随后提交的所有任务。如果这是 commonPool，
     * 则调用对执行状态没有影响，如果已经关闭，则没有其他影响。否则，在此方法过程中正
     * 在提交或同时执行的任务可能被拒绝，也可能不被拒绝。此方法取消现有的和未执行的任
     * 务，以便允许在存在任务依赖项时终止。
     * 因此，该方法总是返回一个空列表(与其他执行器的情况不同)。
     *
     * @return an empty list
     * @throws SecurityException if a security manager exists and
     *         the caller is not permitted to modify threads
     *         because it does not hold {@link
     *         java.lang.RuntimePermission}{@code ("modifyThread")}
     */
    public List<Runnable> shutdownNow() {
        checkPermission();
        tryTerminate(true, true);
        return Collections.emptyList();
    }
 
    /**
     * 如果所有任务都在shut down后完成，则返回 true。
     *
     * @return {@code true} if all tasks have completed following shut down
     */
    public boolean isTerminated() {
        return (runState & TERMINATED) != 0;
    }
 
    /**
     * 如果终止过程已经开始但尚未完成，则返回 true。此方法可能对调试有用。
     * 报告的 true在shutdown后的一段足够长的时间内返回，可能表明提交的
     * 任务忽略或抑制了中断，或者正在等待I/O，导致该执行程序无法正确终止。
     * (参见 ForkJoinTask类的咨询说明，说明任务通常不应包含阻
     * 塞操作。但如果他们这样做了，就必须在中断时中止。)
     *
     * @return {@code true} if terminating but not yet terminated
     */
    public boolean isTerminating() {
        int rs = runState;
        return (rs & STOP) != 0 && (rs & TERMINATED) == 0;
    }
 
    /**
     * Returns {@code true} if this pool has been shut down.
     *
     * @return {@code true} if this pool has been shut down
     */
    public boolean isShutdown() {
        return (runState & SHUTDOWN) != 0;
    }
 
    /**
     *  阻塞等待任务完成，等价于awaitQuiescence(long, TimeUnit)}
     *
     * @param timeout the maximum time to wait
     * @param unit the time unit of the timeout argument
     * @return {@code true} if this executor terminated and
     *         {@code false} if the timeout elapsed before termination
     * @throws InterruptedException if interrupted while waiting
     */
    public boolean awaitTermination(long timeout, TimeUnit unit)
        throws InterruptedException {
        if (Thread.interrupted())
            throw new InterruptedException();
        if (this == common) {
            awaitQuiescence(timeout, unit);
            return false;
        }
        long nanos = unit.toNanos(timeout);
        if (isTerminated())
            return true;
        if (nanos <= 0L)
            return false;
        long deadline = System.nanoTime() + nanos;
        synchronized (this) {
            for (;;) {
                if (isTerminated())
                    return true;
                if (nanos <= 0L)
                    return false;
                long millis = TimeUnit.NANOSECONDS.toMillis(nanos);
                wait(millis > 0L ? millis : 1L);
                nanos = deadline - System.nanoTime();
            }
        }
    }
 
    /**
     * 如果由在这个池中运行的ForkJoinTask调用，就相当于{@link ForkJoinTask#helpQuiesce}。
     * 否则，将等待和/或尝试协助执行任务，直到此池{@link #isQuiescent}或指定的超时过期。
     *
     * @param timeout the maximum time to wait
     * @param unit the time unit of the timeout argument
     * @return {@code true} if quiescent; {@code false} if the
     * timeout elapsed.
     */
    public boolean awaitQuiescence(long timeout, TimeUnit unit) {
        long nanos = unit.toNanos(timeout);
        ForkJoinWorkerThread wt;
        Thread thread = Thread.currentThread();
        if ((thread instanceof ForkJoinWorkerThread) &&
            (wt = (ForkJoinWorkerThread)thread).pool == this) {
            helpQuiescePool(wt.workQueue);
            return true;
        }
        long startTime = System.nanoTime();
        WorkQueue[] ws;
        int r = 0, m;
        boolean found = true;
        while (!isQuiescent() && (ws = workQueues) != null &&
               (m = ws.length - 1) >= 0) {
            if (!found) {
                if ((System.nanoTime() - startTime) > nanos)
                    return false;
                Thread.yield(); // cannot block
            }
            found = false;
            for (int j = (m + 1) << 2; j >= 0; --j) {
                ForkJoinTask<?> t; WorkQueue q; int b, k;
                if ((k = r++ & m) <= m && k >= 0 && (q = ws[k]) != null &&
                    (b = q.base) - q.top < 0) {
                    found = true;
                    if ((t = q.pollAt(b)) != null)
                        t.doExec();
                    break;
                }
            }
        }
        return true;
    }
 
    /**
     * Waits and/or attempts to assist performing tasks indefinitely
     * until the {@link #commonPool()} {@link #isQuiescent}.
     */
    static void quiesceCommonPool() {
        common.awaitQuiescence(Long.MAX_VALUE, TimeUnit.NANOSECONDS);
    }
 
    /**
     * 为正在运行的任务扩展托管并行性的接口。 in {@link ForkJoinPool}s.
     *
     * ManagedBlocker提供了两个方法。如果不需要阻塞，方法 isReleasable 必须返回true。
     * 方法 block在必要时阻塞当前线程(可能在实际阻塞之前内部调用 isReleasable)。
     * 这些操作是由调用 ForkJoinPool#managedBlock(ManagedBlocker) 的任何线程执行的。
     * 这个API中不寻常的方法提供了可能(但通常不会)长时间阻塞的同步器。类似地，它们允许更有
     * 效的内部处理情况，在这种情况下，可能需要(但通常不需要)额外的工作人员来确保足够的并行
     * 性。为此，方法 isReleasable 的实现必须能够重复调用。
     *
     * <p>For example, here is a ManagedBlocker based on a
     * ReentrantLock:
     *  <pre> {@code
     * class ManagedLocker implements ManagedBlocker {
     *   final ReentrantLock lock;
     *   boolean hasLock = false;
     *   ManagedLocker(ReentrantLock lock) { this.lock = lock; }
     *   public boolean block() {
     *     if (!hasLock)
     *       lock.lock();
     *     return true;
     *   }
     *   public boolean isReleasable() {
     *     return hasLock || (hasLock = lock.tryLock());
     *   }
     * }}</pre>
     *
     * <p>Here is a class that possibly blocks waiting for an
     * item on a given queue:
     *  <pre> {@code
     * class QueueTaker<E> implements ManagedBlocker {
     *   final BlockingQueue<E> queue;
     *   volatile E item = null;
     *   QueueTaker(BlockingQueue<E> q) { this.queue = q; }
     *   public boolean block() throws InterruptedException {
     *     if (item == null)
     *       item = queue.take();
     *     return true;
     *   }
     *   public boolean isReleasable() {
     *     return item != null || (item = queue.poll()) != null;
     *   }
     *   public E getItem() { // call after pool.managedBlock completes
     *     return item;
     *   }
     * }}</pre>
     */
    public static interface ManagedBlocker {
        /**
         * 可能阻塞当前线程，例如等待锁或者condition。
         *
         * @return {@code true} 如果不需要额外的阻塞
         * (i.e., if isReleasable would return true)
         * @throws InterruptedException if interrupted while waiting
         * (the method is not required to do so, but is allowed to)
         */
        boolean block() throws InterruptedException;
 
        /**
         * Returns {@code true} if blocking is unnecessary.
         * @return {@code true} if blocking is unnecessary
         */
        boolean isReleasable();
    }
 
    /**
     * 运行给定的可能阻塞的任务。当 ForkJoinTask#inForkJoinPool()在一个ForkJoinPool
     * 中运行时，这个方法可能会安排一个空闲线程被激活，如果需要的话，以确保足够的并行性，而
     * 当前线程被阻塞在 ManagedBlocker#block blocker.block()。
     * 这个方法反复调用 blocker.isReleasable() 和{@code blocker.block()，直到其中一
     * 个方法返回 true。每个对 blocker.block()的调用之前都有一个对 blocker.isReleasable()
     * 的调用，该调用返回false。
     *
     * <p>If not running in a ForkJoinPool, this method is
     * behaviorally equivalent to
     *  <pre> {@code
     * while (!blocker.isReleasable())
     *   if (blocker.block())
     *     break;}</pre>
     *
     * If running in a ForkJoinPool, the pool may first be expanded to
     * ensure sufficient parallelism available during the call to
     * {@code blocker.block()}.
     *
     * @param blocker the blocker task
     * @throws InterruptedException if {@code blocker.block()} did so
     */
    public static void managedBlock(ManagedBlocker blocker)
        throws InterruptedException {
        ForkJoinPool p;
        ForkJoinWorkerThread wt;
        Thread t = Thread.currentThread();
        if ((t instanceof ForkJoinWorkerThread) &&
            (p = (wt = (ForkJoinWorkerThread)t).pool) != null) {
            WorkQueue w = wt.workQueue;
            while (!blocker.isReleasable()) {
                if (p.tryCompensate(w)) {
                    try {
                        do {} while (!blocker.isReleasable() &&
                                     !blocker.block());
                    } finally {
                        U.getAndAddLong(p, CTL, AC_UNIT);
                    }
                    break;
                }
            }
        }
        else {
            do {} while (!blocker.isReleasable() &&
                         !blocker.block());
        }
    }
 
    // AbstractExecutorService overrides.  These rely on undocumented
    // fact that ForkJoinTask.adapt returns ForkJoinTasks that also
    // implement RunnableFuture.
 
    protected <T> RunnableFuture<T> newTaskFor(Runnable runnable, T value) {
        return new ForkJoinTask.AdaptedRunnable<T>(runnable, value);
    }
 
    protected <T> RunnableFuture<T> newTaskFor(Callable<T> callable) {
        return new ForkJoinTask.AdaptedCallable<T>(callable);
    }
 
    // Unsafe mechanics
    private static final sun.misc.Unsafe U;
    private static final int  ABASE;
    private static final int  ASHIFT;
    private static final long CTL;
    private static final long RUNSTATE;
    private static final long STEALCOUNTER;
    private static final long PARKBLOCKER;
    private static final long QTOP;
    private static final long QLOCK;
    private static final long QSCANSTATE;
    private static final long QPARKER;
    private static final long QCURRENTSTEAL;
    private static final long QCURRENTJOIN;
 
    static {
        // initialize field offsets for CAS etc
        try {
            U = sun.misc.Unsafe.getUnsafe();
            Class<?> k = ForkJoinPool.class;
            CTL = U.objectFieldOffset
                (k.getDeclaredField("ctl"));
            RUNSTATE = U.objectFieldOffset
                (k.getDeclaredField("runState"));
            STEALCOUNTER = U.objectFieldOffset
                (k.getDeclaredField("stealCounter"));
            Class<?> tk = Thread.class;
            PARKBLOCKER = U.objectFieldOffset
                (tk.getDeclaredField("parkBlocker"));
            Class<?> wk = WorkQueue.class;
            QTOP = U.objectFieldOffset
                (wk.getDeclaredField("top"));
            QLOCK = U.objectFieldOffset
                (wk.getDeclaredField("qlock"));
            QSCANSTATE = U.objectFieldOffset
                (wk.getDeclaredField("scanState"));
            QPARKER = U.objectFieldOffset
                (wk.getDeclaredField("parker"));
            QCURRENTSTEAL = U.objectFieldOffset
                (wk.getDeclaredField("currentSteal"));
            QCURRENTJOIN = U.objectFieldOffset
                (wk.getDeclaredField("currentJoin"));
            Class<?> ak = ForkJoinTask[].class;
            ABASE = U.arrayBaseOffset(ak);
            int scale = U.arrayIndexScale(ak);
            if ((scale & (scale - 1)) != 0)
                throw new Error("data type scale not a power of two");
            ASHIFT = 31 - Integer.numberOfLeadingZeros(scale);
        } catch (Exception e) {
            throw new Error(e);
        }
 
        commonMaxSpares = DEFAULT_COMMON_MAX_SPARES;
        defaultForkJoinWorkerThreadFactory =
            new DefaultForkJoinWorkerThreadFactory();
        modifyThreadPermission = new RuntimePermission("modifyThread");
 
        common = java.security.AccessController.doPrivileged
            (new java.security.PrivilegedAction<ForkJoinPool>() {
                public ForkJoinPool run() { return makeCommonPool(); }});
        int par = common.config & SMASK; // report 1 even if threads disabled
        commonParallelism = par > 0 ? par : 1;
    }
 
    /**
     * 根据通过系统属性指定的用户设置，创建并返回公共池。
     */
    private static ForkJoinPool makeCommonPool() {
        int parallelism = -1;
        ForkJoinWorkerThreadFactory factory = null;
        UncaughtExceptionHandler handler = null;
        try {  // ignore exceptions in accessing/parsing properties
            String pp = System.getProperty
                ("java.util.concurrent.ForkJoinPool.common.parallelism");
            String fp = System.getProperty
                ("java.util.concurrent.ForkJoinPool.common.threadFactory");
            String hp = System.getProperty
                ("java.util.concurrent.ForkJoinPool.common.exceptionHandler");
            if (pp != null)
                parallelism = Integer.parseInt(pp);
            if (fp != null)
                factory = ((ForkJoinWorkerThreadFactory)ClassLoader.
                           getSystemClassLoader().loadClass(fp).newInstance());
            if (hp != null)
                handler = ((UncaughtExceptionHandler)ClassLoader.
                           getSystemClassLoader().loadClass(hp).newInstance());
        } catch (Exception ignore) {
        }
        if (factory == null) {
            if (System.getSecurityManager() == null)
                factory = defaultForkJoinWorkerThreadFactory;
            else // use security-managed default
                factory = new InnocuousForkJoinWorkerThreadFactory();
        }
        if (parallelism < 0 && // default 1 less than #cores
            (parallelism = Runtime.getRuntime().availableProcessors() - 1) <= 0)
            parallelism = 1;
        if (parallelism > MAX_CAP)
            parallelism = MAX_CAP;
        return new ForkJoinPool(parallelism, factory, handler, LIFO_QUEUE,
                                "ForkJoinPool.commonPool-worker-");
    }
 
    /**
     *  一个良性的工作线程工厂
     */
    static final class InnocuousForkJoinWorkerThreadFactory
        implements ForkJoinWorkerThreadFactory {
 
        /**
         * An ACC to restrict permissions for the factory itself.
         * The constructed workers have no permissions set.
         */
        private static final AccessControlContext innocuousAcc;
        static {
            Permissions innocuousPerms = new Permissions();
            innocuousPerms.add(modifyThreadPermission);
            innocuousPerms.add(new RuntimePermission(
                                   "enableContextClassLoaderOverride"));
            innocuousPerms.add(new RuntimePermission(
                                   "modifyThreadGroup"));
            innocuousAcc = new AccessControlContext(new ProtectionDomain[] {
                    new ProtectionDomain(null, innocuousPerms)
                });
        }
 
        public final ForkJoinWorkerThread newThread(ForkJoinPool pool) {
            return (ForkJoinWorkerThread.InnocuousForkJoinWorkerThread)
                java.security.AccessController.doPrivileged(
                    new java.security.PrivilegedAction<ForkJoinWorkerThread>() {
                    public ForkJoinWorkerThread run() {
                        return new ForkJoinWorkerThread.
                            InnocuousForkJoinWorkerThread(pool);
                    }}, innocuousAcc);
        }
    }
 
}
```

# 更多

源码来自于jdk8.

## 参考资料

[如何使用 ForkJoinPool 以及原理](http://blog.dyngr.com/blog/2016/09/15/java-forkjoinpool-internals)  http://blog.dyngr.com/blog/2016/09/15/java-forkjoinpool-internals/

[JAVA多线程系列--ForkJoinPool详解](https://blog.csdn.net/niyuelin1990/article/details/78658251)  https://blog.csdn.net/niyuelin1990/article/details/78658251

jdk-1.8-ForkJoinPool实现原理上下册： https://www.jianshu.com/p/de025df55363 和  https://www.jianshu.com/p/44b09f52a225
