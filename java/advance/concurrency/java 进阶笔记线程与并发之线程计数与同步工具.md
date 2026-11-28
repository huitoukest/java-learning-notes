---
title: "java 进阶笔记线程与并发之线程计数与同步工具"
date: "2020-04-05 22:42:19"
categories: ["java进阶学习笔记"]
tags: ["java", "多线程", "计数器", "同步器", "栅栏"]
---

# 简介

常见的线程计数和信息同步工具如下：

CountDownLatch（一次性栅栏）、Semaphore（信号量）、CyclicBarrier（循环同步栅栏）、Exchanger（线程间交换器）和Phaser（灵活可重用同步栅栏）。

# 示例

```java
import org.junit.Test;
 
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.stream.IntStream;
 
/**
* 线程计数器与信息同步工具 基于java8
**/
public class ThreadCounterTest {
 
    /**
     * 常用于一个事件多个线程处理的确认全部完成的机制。
     * @throws InterruptedException
     */
    @Test
    public void countDownLatchTest() throws InterruptedException {
        AtomicInteger value = new AtomicInteger();
        CountDownLatch countDownLatch = new CountDownLatch(200);
        IntStream.range(0,200).mapToObj(it ->
                new Thread(() -> {
                    IntStream.range(0,100).forEach(j -> value.incrementAndGet());
                    countDownLatch.countDown();
                })).forEach(it -> it.start());
        //如果不加入，单元测试中，一般由于线程提前结束，value的值 <  20000
        countDownLatch.await();
        //print 20000
        System.out.println(value.get());
    }
 
    /**
     * Semaphore 用于同一个时间，不同线程能同时运行的最大数量。
     * 通过许可机制来实现同时并发的逻辑控制。可以理解为水龙头，最大水流量控制机制。
     * @throws InterruptedException
     */
    @Test
    public void semaphoreTest() throws InterruptedException {
        Semaphore semaphore = new Semaphore(5);
        AtomicInteger current = new AtomicInteger();
        AtomicInteger max = new AtomicInteger();
        CountDownLatch countDownLatch = new CountDownLatch(200);
        IntStream.range(0,200).mapToObj(it ->
                new Thread(() -> {
                    try {
                        semaphore.acquire(1);
                        if(max.get() < current.incrementAndGet()){
                            max.set(current.get());
                            //will print the max value is less or eq 5
                            System.out.println(max);
                        }
                        //模拟耗时任务
                        Thread.sleep(5);
                    } catch (Exception e) {
                        e.printStackTrace();
                    }finally {
                        countDownLatch.countDown();
                        current.decrementAndGet();
                        semaphore.release(1);
                    }
                })).forEach(it -> it.start());
        countDownLatch.await();
    }
 
    /**
     * 可以重复使用，每次等待计数值达到x，然后通过并重置才是开始下一轮等待处理。
     * 可以理解为装箱运输、分批处理模式。
     */
    @Test
    public void cyclicBarrierTest() throws InterruptedException {
        AtomicInteger value = new AtomicInteger();
        //trigger while value in 3,6,9
        CyclicBarrier cyclicBarrier = new CyclicBarrier(3,() -> System.out.println("  trigger action : " + value.get()));
        CountDownLatch countDownLatch = new CountDownLatch(9);
        IntStream.range(0,9).mapToObj(it ->
                new Thread(() -> {
                    value.incrementAndGet();
                    try {
                        cyclicBarrier.await();
                    } catch (Exception e) {
                        e.printStackTrace();
                    }
                    //value over 3,max is 9
                    System.out.println("end cyclic:" + value.get());
                    countDownLatch.countDown();
                })).forEach(it -> it.start());
        countDownLatch.await();
    }
 
    /**
     * Exchanger类源于java.util.concurrent包，它可以在两个线程之间传输数据,在两个线程到达交换点后开始交互数据。
     * 这里模拟当前线程和新开的线程交互数据
     */
    @Test
    public void exchangerTest() throws TimeoutException, InterruptedException {
        int value = -1;
        System.out.println("value = " + value);
        Exchanger exchanger = new Exchanger();
        new Thread(() -> {
            int valueB = ThreadLocalRandom.current().nextInt();
            try {
                System.out.println("valueB = " + valueB);
                valueB = (int) exchanger.exchange(valueB);
            } catch (InterruptedException e) {
                e.printStackTrace();
            }
            System.out.println("valueB = " + valueB);
        }).start();
        value = (int) exchanger.exchange(value,1,TimeUnit.MINUTES);
        System.out.println("value = " + value);
    }
 
     //多次复用
    @Test
    public void exchangerMultipleTest() throws TimeoutException, InterruptedException {
        //假设默认值为1、2、3，随机交换然后顺序打印
        Exchanger exchanger = new Exchanger();
        AtomicInteger atomicInteger = new AtomicInteger(0);
        IntStream.range(0,6).parallel().forEach(it -> {
            new Thread(() -> {
                try {
                    int value = (Integer) exchanger.exchange(it);
                    while(atomicInteger.get() != it){
                        Thread.sleep(10);
                    }
                    atomicInteger.incrementAndGet();
                    System.out.print(value);
                } catch (InterruptedException e) {
                    e.printStackTrace();
                }
            }).start();
        });
        while (atomicInteger.get() < 6){
            Thread.sleep(100);
        }
    }
 
    /**
     * Phaser模拟CountDownLatch
     */
    class CountDownLatchB {
        private Phaser phaser;
 
        public CountDownLatchB(int parties){
            phaser = new Phaser(parties);
        }
 
        public void countDown(){
            phaser.arrive();
        }
 
        public void await(){
            phaser.awaitAdvance(0);
        }
    }
 
    /**
     * Phaser（灵活可重用同步栅栏） 支持自定义线程的注册、释放，以及Phaser的嵌套。
     */
    @Test
    public void phaserTest(){
        AtomicInteger value = new AtomicInteger();
        CountDownLatchB countDownLatch = new CountDownLatchB(200);
        IntStream.range(0,200).mapToObj(it ->
                new Thread(() -> {
                    IntStream.range(0,100).forEach(j -> value.incrementAndGet());
                    countDownLatch.countDown();
                })).forEach(it -> it.start());
        countDownLatch.await();
        //print 20000
        System.out.println(value.get());
    }
```

# 源码简析

## CountDownLatch

```java
/**
* 初始化一个count值，调用countDown时，count减1。当count等于0 之前，调用await方法
* 会阻塞当前线程。是线程安全的的计数器。count无法被重置。
* ......
* @since 1.5
* @author Doug Lea
*/
public class CountDownLatch {
    /**
     * 通过使用AQS的state值来持久化count。
     */
    private static final class Sync extends AbstractQueuedSynchronizer {
        private static final long serialVersionUID = 4982264981922014374L;
 
        Sync(int count) {
            setState(count);
        }
 
        int getCount() {
            return getState();
        }
         //PS: 实质上await等方法调用此方法来获取状态值
        protected int tryAcquireShared(int acquires) {
            return (getState() == 0) ? 1 : -1;
        }
         //PS: 每次count数量-1，并case更新数值，直到数量为0.
        protected boolean tryReleaseShared(int releases) {
            // Decrement count; signal when transition to zero
            for (;;) {
                int c = getState();
                if (c == 0)
                    return false;
                int nextc = c-1;
                if (compareAndSetState(c, nextc))
                    return nextc == 0;
            }
        }
    }
 
    private final Sync sync;
 
    public CountDownLatch(int count) {
        if (count < 0) throw new IllegalArgumentException("count < 0");
        this.sync = new Sync(count);
    }
 
    /**
     * 阻塞当前现在，直到count=0 或者线程被中断。
     */
    public void await() throws InterruptedException {
        sync.acquireSharedInterruptibly(1);
    }
 
    /**
     * 阻塞当前现在，直到count=0 或者线程被中断或者超时。
     */
    public boolean await(long timeout, TimeUnit unit)
        throws InterruptedException {
        return sync.tryAcquireSharedNanos(1, unit.toNanos(timeout));
    }
 
    /**
     * 若count大于0,则减1。
     */
    public void countDown() {
        sync.releaseShared(1);
    }
 
    /**
     * Returns the current count.
     */
    public long getCount() {
        return sync.getCount();
    }
 
    /**
     * @return a string identifying this latch, as well as its state
     */
    public String toString() {
        return super.toString() + "[Count = " + sync.getCount() + "]";
    }
}
```

## Semaphore

```java
/**
* semaphore管理一个虚拟的许可集合，调用acquire则获取一个许可，或者阻塞直到获取。
* 调用release则释放一个许可。实际上，通过一个count数量来进行实现控制。
* semaphore常用于控制对某个资源的并发访问的线程的数量。
* semaphore构造方法，默认构建非公平的计数信号量机制。
* 构造方法中当fair等于true时，创建具有给定许可数的计数信号量并设置为公平信号量；
*
* @since 1.5
* @author Doug Lea
*/
public class Semaphore implements java.io.Serializable {
    private static final long serialVersionUID = -3222578661600680210L;
    /** All mechanics via AbstractQueuedSynchronizer subclass */
    private final Sync sync;
 
    /**
     * Synchronization implementation for semaphore.  Uses AQS state
     * to represent permits. Subclassed into fair and nonfair
     * versions.
     */
    abstract static class Sync extends AbstractQueuedSynchronizer {
        private static final long serialVersionUID = 1192457210091910933L;
 
        Sync(int permits) {
            setState(permits);
        }
 
        final int getPermits() {
            return getState();
        }
 
        final int nonfairTryAcquireShared(int acquires) {
            for (;;) {
                int available = getState();
                int remaining = available - acquires;
                if (remaining < 0 ||
                    compareAndSetState(available, remaining))
                    return remaining;
            }
        }
 
        protected final boolean tryReleaseShared(int releases) {
            for (;;) {
                int current = getState();
                int next = current + releases;
                if (next < current) // overflow
                    throw new Error("Maximum permit count exceeded");
                if (compareAndSetState(current, next))
                    return true;
            }
        }
 
        final void reducePermits(int reductions) {
            for (;;) {
                int current = getState();
                int next = current - reductions;
                if (next > current) // underflow
                    throw new Error("Permit count underflow");
                if (compareAndSetState(current, next))
                    return;
            }
        }
         //许可，状态重置为0
        final int drainPermits() {
            for (;;) {
                int current = getState();
                if (current == 0 || compareAndSetState(current, 0))
                    return current;
            }
        }
    }
 
    /**
     * NonFair version
     */
    static final class NonfairSync extends Sync {
        private static final long serialVersionUID = -2694183684443567898L;
 
        NonfairSync(int permits) {
            super(permits);
        }
 
        protected int tryAcquireShared(int acquires) {
            return nonfairTryAcquireShared(acquires);
        }
    }
 
    /**
     * Fair version
     */
    static final class FairSync extends Sync {
        private static final long serialVersionUID = 2014338818796000944L;
 
        FairSync(int permits) {
            super(permits);
        }
         //PS: 相对于非公平版，主要加入判断是否有前置等待线程
        protected int tryAcquireShared(int acquires) {
            for (;;) {
                if (hasQueuedPredecessors())
                    return -1;
                int available = getState();
                int remaining = available - acquires;
                if (remaining < 0 ||
                    compareAndSetState(available, remaining))
                    return remaining;
            }
        }
    }
 
    public Semaphore(int permits) {
        sync = new NonfairSync(permits);
    }
    public Semaphore(int permits, boolean fair) {
        sync = fair ? new FairSync(permits) : new NonfairSync(permits);
    }
    public void acquire() throws InterruptedException {
        sync.acquireSharedInterruptibly(1);
    }
    public void acquireUninterruptibly() {
        sync.acquireShared(1);
    }
 
    /**
     * PS: 尝试获取一个许可，非公平实现，仅当此时有一个可用许可时返回true
     */
    public boolean tryAcquire() {
        return sync.nonfairTryAcquireShared(1) >= 0;
    }
    public boolean tryAcquire(long timeout, TimeUnit unit)
        throws InterruptedException {
        return sync.tryAcquireSharedNanos(1, unit.toNanos(timeout));
    }
 
    /**
     * PS： 释放一个许可，并不要求此线程必须先获得许可。
     */
    public void release() {
        sync.releaseShared(1);
    }
 
    /**
     * Acquires the given number of permits from this semaphore,
     * blocking until all are available
     */
    public void acquire(int permits) throws InterruptedException {
        if (permits < 0) throw new IllegalArgumentException();
        sync.acquireSharedInterruptibly(permits);
    }
 
    /**
     * Acquires the given number of permits from this semaphore,
     * blocking until all are available.
     */
    public void acquireUninterruptibly(int permits) {
        if (permits < 0) throw new IllegalArgumentException();
        sync.acquireShared(permits);
    }
 
    /**
     * Acquires the given number of permits from this semaphore, only
     * if all are available at the time of invocation.
     */
    public boolean tryAcquire(int permits) {
        if (permits < 0) throw new IllegalArgumentException();
        return sync.nonfairTryAcquireShared(permits) >= 0;
    }
    public boolean tryAcquire(int permits, long timeout, TimeUnit unit)
        throws InterruptedException {
        if (permits < 0) throw new IllegalArgumentException();
        return sync.tryAcquireSharedNanos(permits, unit.toNanos(timeout));
    }
 
    /**
     * Releases the given number of permits, returning them to the semaphore.
     */
    public void release(int permits) {
        if (permits < 0) throw new IllegalArgumentException();
        sync.releaseShared(permits);
    }
 
    /**
     * Returns the current number of permits available in this semaphore.
     */
    public int availablePermits() {
        return sync.getPermits();
    }
 
    /**
     * @return the number of permits acquired
     */
    public int drainPermits() {
        return sync.drainPermits();
    }
 
    /**
     * 减少可用许可证的数量。此方法在使用信号量跟踪不可用资源的子类中非常有用。
     * 此方法与 acquire的不同之处在于它不会阻塞许可的等待。
     */
    protected void reducePermits(int reduction) {
        if (reduction < 0) throw new IllegalArgumentException();
        sync.reducePermits(reduction);
    }
 
    public boolean isFair() {
        return sync instanceof FairSync;
    }
 
    /**
     * 查询是否有线程正在等待获取。注意，因为取消可能在任何时候发生，
     * 返回 true并不保证任何其他线程将获得。该方法主要用于监控系统状态。
     */
    public final boolean hasQueuedThreads() {
        return sync.hasQueuedThreads();
    }
 
    /**
     * 返回等待获取的线程数量的估计值。
     */
    public final int getQueueLength() {
        return sync.getQueueLength();
    }
 
    protected Collection<Thread> getQueuedThreads() {
        return sync.getQueuedThreads();
    }
 
    public String toString() {
        return super.toString() + "[Permits = " + sync.getPermits() + "]";
    }
}
```

## CyclicBarrier

```java
package java.util.concurrent;
import java.util.concurrent.locks.Condition;
import java.util.concurrent.locks.ReentrantLock;
 
/**
* 一个同步助手：它允许一组线程彼此等待到达一个共同的障碍点。cyclicbarrier在包
* 含固定大小的线程的程序中非常有用，这些线程有时必须彼此等待。这个屏障被称为循环
* 屏障，因为它可以在等待的线程被释放后重新使用。
* 附带的Runnable，该命令在每个屏障点上运行一次，在最后一个线程到达之后，
* 但是在释放任何线程之前。这个屏障动作对于在任何一方继续之前更新共享状态非常有用。
*
* @since 1.5
* @see CountDownLatch
*
* @author Doug Lea
*/
public class CyclicBarrier {
    /**
     * 屏障的每次使用都表示为一个生成实例。
     * 无论何时触发屏障或重置屏障，都会更改生成。可以有许多代与线程
     * 相关的使用障碍,由于不确定的方式锁可能被分配到等待线程,但一次只能激活一个。
     */
    private static class Generation {
        boolean broken = false;
    }
 
    /** The lock for guarding barrier entry */
    private final ReentrantLock lock = new ReentrantLock();
    /** Condition to wait on until tripped */
    private final Condition trip = lock.newCondition();
    /** The number of parties */
    private final int parties;
    /* The command to run when tripped */
    private final Runnable barrierCommand;
    /** The current generation */
    private Generation generation = new Generation();
 
    /**
     * 等待直到此数达到0
     */
    private int count;
 
    /**
     * 唤醒所有等待线程
     */
    private void nextGeneration() {
        // signal completion of last generation
        trip.signalAll();
        // set up next generation
        count = parties;
        generation = new Generation();
    }
 
    /**
     * Sets current barrier generation as broken and wakes up everyone.
     * Called only while holding lock.
     * PS： 被中断的处理
     */
    private void breakBarrier() {
        generation.broken = true;
        count = parties;
        trip.signalAll();
    }
 
    /**
     * Main barrier code, covering the various policies.
     */
    private int dowait(boolean timed, long nanos)
        throws InterruptedException, BrokenBarrierException,
               TimeoutException {
        final ReentrantLock lock = this.lock;
        lock.lock();
        try {
            final Generation g = generation;
 
            if (g.broken)
                throw new BrokenBarrierException();
 
            if (Thread.interrupted()) {
                breakBarrier();
                throw new InterruptedException();
            }
            //count - index + 1 = 第几个达到屏障的线程
            int index = --count;
            if (index == 0) {  // tripped，如果都到达了，执行动作并生成新一代
                boolean ranAction = false;
                try {
                    final Runnable command = barrierCommand;
                    if (command != null)
                        command.run();
                    ranAction = true;
                    nextGeneration();//执行过一次就生成下一个
                    return 0;
                } finally {
                    if (!ranAction)
                        breakBarrier();
                }
            }
            //直接使用条件等待，直到生成新一代（即这一代都到达了）
            // loop until tripped, broken, interrupted, or timed out
            for (;;) {
                try {
                    if (!timed)
                        trip.await();
                    else if (nanos > 0L)
                        nanos = trip.awaitNanos(nanos);
                } catch (InterruptedException ie) {
                    if (g == generation && ! g.broken) {
                        breakBarrier();
                        throw ie;
                    } else {
                        // We're about to finish waiting even if we had not
                        // been interrupted, so this interrupt is deemed to
                        // "belong" to subsequent execution.
                        Thread.currentThread().interrupt();
                    }
                }
 
                if (g.broken)
                    throw new BrokenBarrierException();
                //如果没有到新一代，就自旋等待
                if (g != generation)
                    return index;
 
                if (timed && nanos <= 0L) {
                    breakBarrier();
                    throw new TimeoutException();
                }
            }
        } finally {
            lock.unlock();
        }
    }
 
    public CyclicBarrier(int parties, Runnable barrierAction) {
        if (parties <= 0) throw new IllegalArgumentException();
        this.parties = parties;
        this.count = parties;
        this.barrierCommand = barrierAction;
    }
 
    public CyclicBarrier(int parties) {
        this(parties, null);
    }
 
    /**
     * @return 返回需要跨越此屏障的参与方的数量
     */
    public int getParties() {
        return parties;
    }
 
    /**
     */
    public int await() throws InterruptedException, BrokenBarrierException {
        try {
            return dowait(false, 0L);
        } catch (TimeoutException toe) {
            throw new Error(toe); // cannot happen
        }
    }
 
    public int await(long timeout, TimeUnit unit)
        throws InterruptedException,
               BrokenBarrierException,
               TimeoutException {
        return dowait(true, unit.toNanos(timeout));
    }
 
    /**
     * @return 如果一个或多个参与方在构建或最后一次重置后由于中断或超时而突破此屏障，
     * 或者由于异常导致屏障动作则返回false
     */
    public boolean isBroken() {
        final ReentrantLock lock = this.lock;
        lock.lock();
        try {
            return generation.broken;
        } finally {
            lock.unlock();
        }
    }
 
    /**
     * 将屏障重置为其初始状态。如果任何一方当前正在屏障处等待，
     * 他们将返回一个 BrokenBarrierException。请注意，在因
     * 其他原因造成的破损发生后进行复位可能比较复杂;线程需要以
     * 其他方式重新同步，并选择一种方式执行重置。
     * 最好是为后续使用创建一个新的屏障。
     */
    public void reset() {
        final ReentrantLock lock = this.lock;
        lock.lock();
        try {
            breakBarrier();   // break the current generation
            nextGeneration(); // start a new generation
        } finally {
            lock.unlock();
        }
    }
 
    /**
      * 返回当前在屏障处阻塞的队伍数量，此方法主要用于调试和断言。
     */
    public int getNumberWaiting() {
        final ReentrantLock lock = this.lock;
        lock.lock();
        try {
            return parties - count;
        } finally {
            lock.unlock();
        }
    }
}
 
```

## Exchanger

```java
package java.util.concurrent;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import java.util.concurrent.locks.LockSupport;
 
/**
* 一个同步点，在这个点上，线程可以在对中配对和交换元素。
* 每个线程在进入exchange方法时呈现一些对象，与合作伙伴线程匹配，
* 并在返回时接收其合作伙伴的对象。交换器可以看作是SynchronousQueue的双向形式。
* 交换器可能在遗传算法和管道设计等应用中很有用。
*
* @since 1.5
* @author Doug Lea and Bill Scherer and Michael Scott
*/
public class Exchanger<V> {
 
    /*
     * 我们可以安全地重用每个线程节点，而不是每次都重新创建它们，因为插槽在指向节点
     * 和指向null之间交替进行，所以不会遇到ABA问题。但是，我们需要注意在不同的使用
     * 之间重新设置它们
     * ps://竞技场在这里表示线程竞争的一个内存（或者说高速缓存）数据，其值从0开始
     * 逐渐增大，值越大竞争理论上线程冲突越少，所以在线程默认从最大索引值倒序取值
     * 识图竞争成功，同时索引非线性减少，而是使用各种方法使得其取到往冲突更小的索引
     * 所以这里竞技场的主要功能是是为了减少冲突和复用资源。
     *
     * 基本上所有的实现都是在方法slotExchange和arenaExchange中实现的。
     * 它们具有相似的总体结构，但在太多的细节上存在差异，无法合并。
     * slotExchange方法使用单个交换器字段“槽”，而不是竞技场阵列元素。
     * 然而，它仍然需要最小的碰撞检测来触发竞技场建设。(最麻烦的部分是确保中断状
     * 态和interruptedexception在调用这两个方法的转换期间正确出现。这是通过
     * 使用null返回作为一个标记来重新检查中断状态来实现的。
     *
     */
 
    /**
     * 两个插槽在竞争块之间的字节距离，保存的位移的值，至少等于一个高速缓存空间大小。
     */
    private static final int ASHIFT = 7;
 
    /**
     * The maximum supported arena index. The maximum allocatable
     * arena size is MMASK + 1. Must be a power of two minus one, less
     * than (1<<(31-ASHIFT)). The cap of 255 (0xff) more than suffices
     * for the expected scaling limits of the main algorithms.
     * 支持的最大的竞技场的索引
     */
    private static final int MMASK = 0xff;
 
    /**
     * Unit for sequence/version bits of bound field. Each successful
     * change to the bound also adds SEQ.
     * 绑定字段的序列/版本位的单位。每个成功的绑定更改都将添加SEQ。
     */
    private static final int SEQ = MMASK + 1;
 
    /** The number of CPUs, for sizing and spin control */
    private static final int NCPU = Runtime.getRuntime().availableProcessors();
 
    /**
     * The maximum slot index of the arena: The number of slots that
     * can in principle hold all threads without contention, or at
     * most the maximum indexable value.
     * 竞技场的最大插槽索引:原则上可以容纳所有线程而不发生争用的插槽的数量，
     * 或者最多是可索引的最大值。
     */
    static final int FULL = (NCPU >= (MMASK << 1)) ? MMASK : NCPU >>> 1;
 
    /**
     * The bound for spins while waiting for a match. The actual
     * number of iterations will on average be about twice this value
     * due to randomization. Note: Spinning is disabled when NCPU==1.
     * 等待竞争时的自旋。由于随机化，实际的迭代次数平均大约是这个值的两倍。
     * 注意:当NCPU==1时禁用自旋。
     */
    private static final int SPINS = 1 << 10;
 
    /**
     * 表示空参数/从公共方法返回的值。因为API最初不允许null参数，
     * 而它本来应该允许null参数。
     */
    private static final Object NULL_ITEM = new Object();
 
    /**
     * 内部交换方法在超时时返回的标记值，以避免需要这些方法的单独定时版本。
     */
    private static final Object TIMED_OUT = new Object();
 
    /**
     * 节点持有部分交换的数据，以及其他每个线程的park地址。
     * 通过@sun.misc.Contended标记争用以减少内存争用。
     */
    @sun.misc.Contended static final class Node {
        int index;              // Arena index
        int bound;              // Last recorded value of Exchanger.bound
        int collides;           // Number of CAS failures at current bound
        int hash;               // Pseudo-random for spins
        Object item;            // This thread's current item
        volatile Object match;  // Item provided by releasing thread
        volatile Thread parked; // Set to this thread when parked, else null
    }
 
    /** 定义参与者：对应的线程本地类 */
    static final class Participant extends ThreadLocal<Node> {
        public Node initialValue() { return new Node(); }
    }
 
    /**
     * Per-thread state
     */
    private final Participant participant;
 
    /**
     * Elimination array; null until enabled (within slotExchange).
     * Element accesses use emulation of volatile gets and CAS.
     */
    private volatile Node[] arena;
 
    /**
     * 在检测到争用之前使用的插槽
     */
    private volatile Node slot;
 
    /**
     * The index of the largest valid arena position, OR'ed with SEQ
     * number in high bits, incremented on each update.  The initial
     * update from 0 to SEQ is used to ensure that the arena array is
     * constructed only once.
     * 最大有效竞技场位置的索引，或用高位的SEQ数字表示的索引，在每次更新时递增。
     * 从0到SEQ的初始更新被用来确保竞技场数组只被构造一次。
     */
    private volatile int bound;
 
    /**
     * 启用竞技场交换功能
     * @param item the (non-null) item to exchange
     * @param timed true if the wait is timed
     * @param ns if timed, the maximum wait time, else 0L
     * @return the other thread's item; or null if interrupted; or
     * TIMED_OUT if timed and timed out
     */
    private final Object arenaExchange(Object item, boolean timed, long ns) {
        Node[] a = arena;
        //ps: 从threadL获取当成参与的节点
        Node p = participant.get();
        for (int i = p.index;;) {                      // access slot at i
            int b, m, c; long j;                       // j is raw array offset
            //ps: 从竞争的节点中获取一个
            Node q = (Node)U.getObjectVolatile(a, j = (i << ASHIFT) + ABASE);
            //ps: case成功则设置q节点交互后的数据，并得到q的地址，唤醒对应线程，返回q中的值给当前线程
            if (q != null && U.compareAndSwapObject(a, j, q, null)) {
                Object v = q.item;                     // release
                q.match = item;
                Thread w = q.parked;
                if (w != null)
                    U.unpark(w);
                return v;
            }
            //ps：q is null = 参与节点q尚未达到交换点设置信息
            //ps：i < bound 小于上界值,达到后会重置状态
            else if (i <= (m = (b = bound) & MMASK) && q == null) {
                p.item = item;                         // offer
                //ps:将p节点信息case设置
                if (U.compareAndSwapObject(a, j, null, p)) {
                    long end = (timed && m == 0) ? System.nanoTime() + ns : 0L;
                    Thread t = Thread.currentThread(); // wait
                    //ps:当前线程会自旋等待
                    for (int h = p.hash, spins = SPINS;;) {
                        Object v = p.match;
                        if (v != null) {
                            U.putOrderedObject(p, MATCH, null);
                            p.item = null;             // clear for next use
                            p.hash = h;
                            return v;
                        }//匹配成功则返回，否则自旋次数大于0时
                        else if (spins > 0) {
                            h ^= h << 1; h ^= h >>> 3; h ^= h << 10; // xorshift
                            if (h == 0)                // initialize hash
                                h = SPINS | (int)t.getId();
                            else if (h < 0 &&          // approx 50% true
                                     (--spins & ((SPINS >>> 1) - 1)) == 0)
                                Thread.yield();        // two yields per wait
                        }//线程yield让渡资源
                        else if (U.getObjectVolatile(a, j) != p)
                            spins = SPINS;       // releaser hasn't set match yet
                        else if (!t.isInterrupted() && m == 0 &&
                                 (!timed ||
                                  (ns = end - System.nanoTime()) > 0L)) {
                            U.putObject(t, BLOCKER, this); // emulate LockSupport
                            p.parked = t;              // minimize window
                            if (U.getObjectVolatile(a, j) == p)
                                U.park(false, ns);
                            p.parked = null;
                            U.putObject(t, BLOCKER, null);
                        }
                        else if (U.getObjectVolatile(a, j) == p &&
                                 U.compareAndSwapObject(a, j, p, null)) {
                            if (m != 0)                // try to shrink
                                U.compareAndSwapInt(this, BOUND, b, b + SEQ - 1);
                            p.item = null;
                            p.hash = h;
                            i = p.index >>>= 1;        // descend
                            if (Thread.interrupted())
                                return null;
                            if (timed && m == 0 && ns <= 0L)
                                return TIMED_OUT;
                            break;                     // expired; restart
                        }
                    }
                }
                else
                    p.item = null;                     // clear offer
            }
            else {//ps:index达到上界值，则开始重置数据
                if (p.bound != b) {                    // stale; reset
                    p.bound = b;
                    p.collides = 0;
                    i = (i != m || m == 0) ? m : m - 1;
                }
                else if ((c = p.collides) < m || m == FULL ||
                         !U.compareAndSwapInt(this, BOUND, b, b + SEQ + 1)) {
                    p.collides = c + 1;
                    i = (i == 0) ? m : i - 1;          // cyclically traverse
                }
                else
                    i = m + 1;                         // grow
                p.index = i;
            }
        }
    }
 
    /**
     * Exchange function used until arenas enabled. See above for explanation.
     *
     * @param item the item to exchange
     * @param timed true if the wait is timed
     * @param ns if timed, the maximum wait time, else 0L
     * @return the other thread's item; or null if either the arena
     * was enabled or the thread was interrupted before completion; or
     * TIMED_OUT if timed and timed out
     */
    private final Object slotExchange(Object item, boolean timed, long ns) {
        Node p = participant.get();
        Thread t = Thread.currentThread();
        if (t.isInterrupted()) // preserve interrupt status so caller can recheck
            return null;
 
        for (Node q;;) {
            if ((q = slot) != null) {
                if (U.compareAndSwapObject(this, SLOT, q, null)) {
                    Object v = q.item;
                    q.match = item;
                    Thread w = q.parked;
                    if (w != null)
                        U.unpark(w);
                    return v;
                }
                // create arena on contention, but continue until slot null
                if (NCPU > 1 && bound == 0 &&
                    U.compareAndSwapInt(this, BOUND, 0, SEQ))
                    arena = new Node[(FULL + 2) << ASHIFT];
            }
            else if (arena != null)
                return null; // caller must reroute to arenaExchange
            else {
                p.item = item;
                if (U.compareAndSwapObject(this, SLOT, null, p))
                    break;
                p.item = null;
            }
        }
 
        // await release
        int h = p.hash;
        long end = timed ? System.nanoTime() + ns : 0L;
        int spins = (NCPU > 1) ? SPINS : 1;
        Object v;
        while ((v = p.match) == null) {
            if (spins > 0) {
                h ^= h << 1; h ^= h >>> 3; h ^= h << 10;
                if (h == 0)
                    h = SPINS | (int)t.getId();
                else if (h < 0 && (--spins & ((SPINS >>> 1) - 1)) == 0)
                    Thread.yield();
            }
            else if (slot != p)
                spins = SPINS;
            else if (!t.isInterrupted() && arena == null &&
                     (!timed || (ns = end - System.nanoTime()) > 0L)) {
                U.putObject(t, BLOCKER, this);
                p.parked = t;
                if (slot == p)
                    U.park(false, ns);
                p.parked = null;
                U.putObject(t, BLOCKER, null);
            }
            else if (U.compareAndSwapObject(this, SLOT, p, null)) {
                v = timed && ns <= 0L && !t.isInterrupted() ? TIMED_OUT : null;
                break;
            }
        }
        U.putOrderedObject(p, MATCH, null);
        p.item = null;
        p.hash = h;
        return v;
    }
 
    /**
     * Creates a new Exchanger.
     */
    public Exchanger() {
        participant = new Participant();
    }
 
    /**
     * 等待另外一个线程达到交换的节点，然后返回交换得到的数据
     * 如果另外一个线程早已等待，则被当前线程调度唤醒并，当前线程立即返回。
     *
     * @param x the object to exchange
     * @return the object provided by the other thread
     * @throws InterruptedException if the current thread was
     *         interrupted while waiting
     */
    @SuppressWarnings("unchecked")
    public V exchange(V x) throws InterruptedException {
        Object v;
        Object item = (x == null) ? NULL_ITEM : x; // translate null args
        if ((arena != null ||
             (v = slotExchange(item, false, 0L)) == null) &&
            ((Thread.interrupted() || // disambiguates null return
              (v = arenaExchange(item, false, 0L)) == null)))
            throw new InterruptedException();
        return (v == NULL_ITEM) ? null : (V)v;
    }
 
    /**
     * ps: 到处硬编码，为了性能没啥复用，编译阶段明显优化不够
     */
    @SuppressWarnings("unchecked")
    public V exchange(V x, long timeout, TimeUnit unit)
        throws InterruptedException, TimeoutException {
        Object v;
        Object item = (x == null) ? NULL_ITEM : x;
        long ns = unit.toNanos(timeout);
        if ((arena != null ||
             (v = slotExchange(item, true, ns)) == null) &&
            ((Thread.interrupted() ||
              (v = arenaExchange(item, true, ns)) == null)))
            throw new InterruptedException();
        if (v == TIMED_OUT)
            throw new TimeoutException();
        return (v == NULL_ITEM) ? null : (V)v;
    }
 
    // Unsafe mechanics
    private static final sun.misc.Unsafe U;
    private static final long BOUND;
    private static final long SLOT;
    private static final long MATCH;
    private static final long BLOCKER;
    private static final int ABASE;
    static {
        int s;
        try {
            U = sun.misc.Unsafe.getUnsafe();
            Class<?> ek = Exchanger.class;
            Class<?> nk = Node.class;
            Class<?> ak = Node[].class;
            Class<?> tk = Thread.class;
            BOUND = U.objectFieldOffset
                (ek.getDeclaredField("bound"));
            SLOT = U.objectFieldOffset
                (ek.getDeclaredField("slot"));
            MATCH = U.objectFieldOffset
                (nk.getDeclaredField("match"));
            BLOCKER = U.objectFieldOffset
                (tk.getDeclaredField("parkBlocker"));
            s = U.arrayIndexScale(ak);
            // ABASE absorbs padding in front of element 0
            ABASE = U.arrayBaseOffset(ak) + (1 << ASHIFT);
 
        } catch (Exception e) {
            throw new Error(e);
        }
        if ((s & (s-1)) != 0 || s > (1 << ASHIFT))
            throw new Error("Unsupported array scale");
    }
 
}
 
```

### exchanger 官方示例

ps://两个线程，一个填充，一个清空。填满或者清空时通过数据交互来通知对方，互相处理对方给予的buffer。

```java
class FillAndEmpty {
    Exchanger<DataBuffer> exchanger = new Exchanger<DataBuffer>();
    DataBuffer initialEmptyBuffer = ... a made-up type
    DataBuffer initialFullBuffer = ...
 
    class FillingLoop implements Runnable {
      public void run() {
        DataBuffer currentBuffer = initialEmptyBuffer;
        try {
          while (currentBuffer != null) {
            addToBuffer(currentBuffer);
            if (currentBuffer.isFull())
              currentBuffer = exchanger.exchange(currentBuffer);
          }
        } catch (InterruptedException ex) { ... handle ... }
      }
    }
    class EmptyingLoop implements Runnable {
      public void run() {
        DataBuffer currentBuffer = initialFullBuffer;
        try {
          while (currentBuffer != null) {
            takeFromBuffer(currentBuffer);
            if (currentBuffer.isEmpty())
              currentBuffer = exchanger.exchange(currentBuffer);
          }
        } catch (InterruptedException ex) { ... handle ...}
      }
    }
 
    void start() {
      new Thread(new FillingLoop()).start();
      new Thread(new EmptyingLoop()).start();
    }
}}
```

## Phaser

ps: phaser源码

```java
package java.util.concurrent;
 
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;
import java.util.concurrent.atomic.AtomicReference;
import java.util.concurrent.locks.LockSupport;
 
/**
* ps: 与其它同步器相比而言，更加的灵活。可以随时修改同步的数量。
*
*
* TASKS_PER_PHASER的最佳值主要取决于预期的同步率。低至4的值可能适合于非常小
* 的每阶段任务主体(因此具有很高的速率)，或者高至数百的值适合于非常大的任务主体。
* 实现说明:此实现将最大参与方数量限制为65535。试图注册其他参与方将导致{@code
* IllegalStateException}。但是，您可以并且应该创建分层相量来容纳任意大的参与者集。
*
* @since 1.7
* @author Doug Lea
*/
public class Phaser {
    /*
     * 这个类实现了X10“时钟”的扩展。感谢Vijay Saraswat提出了这个想法，
     * 感谢Vivek Sarkar提供了扩展功能的增强。
     */
 
    /**
     * Primary state representation, holding four bit-fields:
     * state的不同位置保存的内容：
     * unarrived  -- the number of parties yet to hit barrier (bits  0-15)
     * parties    -- the number of parties to wait            (bits 16-31)
     * phase      -- the generation of the barrier            (bits 32-62)
     * terminated -- set if barrier is terminated             (bit  63 / sign)
     *
     * Except that a phaser with no registered parties is
     * distinguished by the otherwise illegal state of having zero
     * parties and one unarrived parties (encoded as EMPTY below).
     *
     * To efficiently maintain atomicity, these values are packed into
     * a single (atomic) long. Good performance relies on keeping
     * state decoding and encoding simple, and keeping race windows
     * short.
     *
     * All state updates are performed via CAS except initial
     * registration of a sub-phaser (i.e., one with a non-null
     * parent).  In this (relatively rare) case, we use built-in
     * synchronization to lock while first registering with its
     * parent.
     *
     * The phase of a subphaser is allowed to lag that of its
     * ancestors until it is actually accessed -- see method
     * reconcileState.
     */
    private volatile long state;
 
    private static final int  MAX_PARTIES     = 0xffff;
    private static final int  MAX_PHASE       = Integer.MAX_VALUE;
    private static final int  PARTIES_SHIFT   = 16;
    private static final int  PHASE_SHIFT     = 32;
    private static final int  UNARRIVED_MASK  = 0xffff;      // to mask ints
    private static final long PARTIES_MASK    = 0xffff0000L; // to mask longs
    private static final long COUNTS_MASK     = 0xffffffffL;
    private static final long TERMINATION_BIT = 1L << 63;
 
    // some special values
    private static final int  ONE_ARRIVAL     = 1;
    private static final int  ONE_PARTY       = 1 << PARTIES_SHIFT;
    private static final int  ONE_DEREGISTER  = ONE_ARRIVAL|ONE_PARTY;
    private static final int  EMPTY           = 1;
 
    // The following unpacking methods are usually manually inlined
 
    private static int unarrivedOf(long s) {
        int counts = (int)s;
        return (counts == EMPTY) ? 0 : (counts & UNARRIVED_MASK);
    }
 
    private static int partiesOf(long s) {
        return (int)s >>> PARTIES_SHIFT;
    }
 
    private static int phaseOf(long s) {
        return (int)(s >>> PHASE_SHIFT);
    }
 
    private static int arrivedOf(long s) {
        int counts = (int)s;
        return (counts == EMPTY) ? 0 :
            (counts >>> PARTIES_SHIFT) - (counts & UNARRIVED_MASK);
    }
 
    /**
     * The parent of this phaser, or null if none
     */
    private final Phaser parent;
 
    /**
     * The root of phaser tree. Equals this if not in a tree.
     */
    private final Phaser root;
 
    /**
     * Heads of Treiber stacks for waiting threads. To eliminate
     * contention when releasing some threads while adding others, we
     * use two of them, alternating across even and odd phases.
     * Subphasers share queues with root to speed up releases.
     */
    private final AtomicReference<QNode> evenQ;
    private final AtomicReference<QNode> oddQ;
 
    private AtomicReference<QNode> queueFor(int phase) {
        return ((phase & 1) == 0) ? evenQ : oddQ;
    }
 
    /**
     * Returns message string for bounds exceptions on arrival.
     */
    private String badArrive(long s) {
        return "Attempted arrival of unregistered party for " +
            stateToString(s);
    }
 
    /**
     * Returns message string for bounds exceptions on registration.
     */
    private String badRegister(long s) {
        return "Attempt to register more than " +
            MAX_PARTIES + " parties for " + stateToString(s);
    }
 
    /**
     * 方法的主要实现到达和注销。手动调整，以加快和尽量减少竞争窗口的常
     * 见情况下，只是减少未到达的领域。
     * @param adjust value to subtract from state;
     *               ONE_ARRIVAL for arrive,
     *               ONE_DEREGISTER for arriveAndDeregister
     */
    private int doArrive(int adjust) {
        final Phaser root = this.root;
        for (;;) {
            long s = (root == this) ? state : reconcileState();
            int phase = (int)(s >>> PHASE_SHIFT);
            if (phase < 0)
                return phase;
            int counts = (int)s;
            int unarrived = (counts == EMPTY) ? 0 : (counts & UNARRIVED_MASK);
            if (unarrived <= 0)
                throw new IllegalStateException(badArrive(s));
            if (UNSAFE.compareAndSwapLong(this, stateOffset, s, s-=adjust)) {
                if (unarrived == 1) {
                    long n = s & PARTIES_MASK;  // base of next state
                    int nextUnarrived = (int)n >>> PARTIES_SHIFT;
                    if (root == this) {
                        if (onAdvance(phase, nextUnarrived))
                            n |= TERMINATION_BIT;
                        else if (nextUnarrived == 0)
                            n |= EMPTY;
                        else
                            n |= nextUnarrived;
                        int nextPhase = (phase + 1) & MAX_PHASE;
                        n |= (long)nextPhase << PHASE_SHIFT;
                        UNSAFE.compareAndSwapLong(this, stateOffset, s, n);
                        releaseWaiters(phase);
                    }
                    else if (nextUnarrived == 0) { // propagate deregistration
                        phase = parent.doArrive(ONE_DEREGISTER);
                        UNSAFE.compareAndSwapLong(this, stateOffset,
                                                  s, s | EMPTY);
                    }
                    else
                        phase = parent.doArrive(ONE_ARRIVAL);
                }
                return phase;
            }
        }
    }
 
    /**
     * Implementation of register, bulkRegister
     *
     * @param registrations number to add to both parties and
     * unarrived fields. Must be greater than zero.
     */
    private int doRegister(int registrations) {
        // adjustment to state
        long adjust = ((long)registrations << PARTIES_SHIFT) | registrations;
        final Phaser parent = this.parent;
        int phase;
        for (;;) {
            long s = (parent == null) ? state : reconcileState();
            int counts = (int)s;
            int parties = counts >>> PARTIES_SHIFT;
            int unarrived = counts & UNARRIVED_MASK;
            if (registrations > MAX_PARTIES - parties)
                throw new IllegalStateException(badRegister(s));
            phase = (int)(s >>> PHASE_SHIFT);
            if (phase < 0)
                break;
            if (counts != EMPTY) {                  // not 1st registration
                if (parent == null || reconcileState() == s) {
                    if (unarrived == 0)             // wait out advance
                        root.internalAwaitAdvance(phase, null);
                    else if (UNSAFE.compareAndSwapLong(this, stateOffset,
                                                       s, s + adjust))
                        break;
                }
            }
            else if (parent == null) {              // 1st root registration
                long next = ((long)phase << PHASE_SHIFT) | adjust;
                if (UNSAFE.compareAndSwapLong(this, stateOffset, s, next))
                    break;
            }
            else {
                synchronized (this) {               // 1st sub registration
                    if (state == s) {               // recheck under lock
                        phase = parent.doRegister(1);
                        if (phase < 0)
                            break;
                        // finish registration whenever parent registration
                        // succeeded, even when racing with termination,
                        // since these are part of the same "transaction".
                        while (!UNSAFE.compareAndSwapLong
                               (this, stateOffset, s,
                                ((long)phase << PHASE_SHIFT) | adjust)) {
                            s = state;
                            phase = (int)(root.state >>> PHASE_SHIFT);
                            // assert (int)s == EMPTY;
                        }
                        break;
                    }
                }
            }
        }
        return phase;
    }
 
    /**
     * Resolves lagged phase propagation from root if necessary.
     * Reconciliation normally occurs when root has advanced but
     * subphasers have not yet done so, in which case they must finish
     * their own advance by setting unarrived to parties (or if
     * parties is zero, resetting to unregistered EMPTY state).
     *
     * @return reconciled state
     */
    private long reconcileState() {
        final Phaser root = this.root;
        long s = state;
        if (root != this) {
            int phase, p;
            // CAS to root phase with current parties, tripping unarrived
            while ((phase = (int)(root.state >>> PHASE_SHIFT)) !=
                   (int)(s >>> PHASE_SHIFT) &&
                   !UNSAFE.compareAndSwapLong
                   (this, stateOffset, s,
                    s = (((long)phase << PHASE_SHIFT) |
                         ((phase < 0) ? (s & COUNTS_MASK) :
                          (((p = (int)s >>> PARTIES_SHIFT) == 0) ? EMPTY :
                           ((s & PARTIES_MASK) | p))))))
                s = state;
        }
        return s;
    }
 
    /**
     * Creates a new phaser with no initially registered parties, no
     * parent, and initial phase number 0. Any thread using this
     * phaser will need to first register for it.
     */
    public Phaser() {
        this(null, 0);
    }
 
    /**
     * Creates a new phaser with the given number of registered
     * unarrived parties, no parent, and initial phase number 0.
     *
     * @param parties the number of parties required to advance to the
     * next phase
     * @throws IllegalArgumentException if parties less than zero
     * or greater than the maximum number of parties supported
     */
    public Phaser(int parties) {
        this(null, parties);
    }
 
    /**
     * Equivalent to {@link #Phaser(Phaser, int) Phaser(parent, 0)}.
     *
     * @param parent the parent phaser
     */
    public Phaser(Phaser parent) {
        this(parent, 0);
    }
 
    /**
     * ps: 有parent则将当前phaser指向相同的roor，如果没有则自己是root。
     * 统一使用与访问原则。
     *
     * @param parent the parent phaser
     * @param parties the number of parties required to advance to the
     * next phase
     * @throws IllegalArgumentException if parties less than zero
     * or greater than the maximum number of parties supported
     */
    public Phaser(Phaser parent, int parties) {
        if (parties >>> PARTIES_SHIFT != 0)
            throw new IllegalArgumentException("Illegal number of parties");
        int phase = 0;
        this.parent = parent;
        if (parent != null) {
            final Phaser root = parent.root;
            this.root = root;
            this.evenQ = root.evenQ;
            this.oddQ = root.oddQ;
            if (parties != 0)
                phase = parent.doRegister(1);
        }
        else {
            this.root = this;
            this.evenQ = new AtomicReference<QNode>();
            this.oddQ = new AtomicReference<QNode>();
        }
        this.state = (parties == 0) ? (long)EMPTY :
            ((long)phase << PHASE_SHIFT) |
            ((long)parties << PARTIES_SHIFT) |
            ((long)parties);
    }
 
    public int register() {
        return doRegister(1);
    }
 
    /**
     * 手动装入指定数量的子阶段（以便出发阶段完成）
     */
    public int bulkRegister(int parties) {
        if (parties < 0)
            throw new IllegalArgumentException();
        if (parties == 0)
            return getPhase();
        return doRegister(parties);
    }
 
    /**
     * 到达这个相位，不要等别人到达。未注册的一方调用此方法是使用错误。
     * 然而，这个错误可能会导致{@code IllegalStateException}只有
     * 在这个相量的后续操作中，如果有的话。
     *
     * @return the arrival phase number, or a negative value if terminated
     * @throws IllegalStateException if not terminated and the number
     * of unarrived parties would become negative
     */
    public int arrive() {
        return doArrive(ONE_ARRIVAL);
    }
 
    /**
     * 到达该相位器(phaser)并取消该相位器，无需等待其他phaser到达。
     *
     * @return the arrival phase number, or a negative value if terminated
     * @throws IllegalStateException if not terminated and the number
     * of registered or unarrived parties would become negative
     */
    public int arriveAndDeregister() {
        return doArrive(ONE_DEREGISTER);
    }
 
    /**
     *
     * @return the arrival phase number, or the (negative)
     * {@linkplain #getPhase() current phase} if terminated
     * @throws IllegalStateException if not terminated and the number
     * of unarrived parties would become negative
     */
    public int arriveAndAwaitAdvance() {
        // Specialization of doArrive+awaitAdvance eliminating some reads/paths
        final Phaser root = this.root;
        for (;;) {
            long s = (root == this) ? state : reconcileState();
            int phase = (int)(s >>> PHASE_SHIFT);
            if (phase < 0)
                return phase;
            int counts = (int)s;
            int unarrived = (counts == EMPTY) ? 0 : (counts & UNARRIVED_MASK);
            if (unarrived <= 0)
                throw new IllegalStateException(badArrive(s));
            if (UNSAFE.compareAndSwapLong(this, stateOffset, s,
                                          s -= ONE_ARRIVAL)) {
                if (unarrived > 1)
                    return root.internalAwaitAdvance(phase, null);
                if (root != this)
                    return parent.arriveAndAwaitAdvance();
                long n = s & PARTIES_MASK;  // base of next state
                int nextUnarrived = (int)n >>> PARTIES_SHIFT;
                if (onAdvance(phase, nextUnarrived))
                    n |= TERMINATION_BIT;
                else if (nextUnarrived == 0)
                    n |= EMPTY;
                else
                    n |= nextUnarrived;
                int nextPhase = (phase + 1) & MAX_PHASE;
                n |= (long)nextPhase << PHASE_SHIFT;
                if (!UNSAFE.compareAndSwapLong(this, stateOffset, s, n))
                    return (int)(state >>> PHASE_SHIFT); // terminated
                releaseWaiters(phase);
                return nextPhase;
            }
        }
    }
 
    /**
     * Awaits the phase of this phaser to advance from the given phase
     * value, returning immediately if the current phase is not equal
     * to the given phase value or this phaser is terminated.
     *
     * @param phase an arrival phase number, or negative value if
     * terminated; this argument is normally the value returned by a
     * previous call to {@code arrive} or {@code arriveAndDeregister}.
     * @return the next arrival phase number, or the argument if it is
     * negative, or the (negative) {@linkplain #getPhase() current phase}
     * if terminated
     */
    public int awaitAdvance(int phase) {
        final Phaser root = this.root;
        long s = (root == this) ? state : reconcileState();
        int p = (int)(s >>> PHASE_SHIFT);
        if (phase < 0)
            return phase;
        if (p == phase)
            return root.internalAwaitAdvance(phase, null);
        return p;
    }
 
    /**
     * Awaits the phase of this phaser to advance from the given phase
     * value, throwing {@code InterruptedException} if interrupted
     * while waiting, or returning immediately if the current phase is
     * not equal to the given phase value or this phaser is
     * terminated.
     *
     * @param phase an arrival phase number, or negative value if
     * terminated; this argument is normally the value returned by a
     * previous call to {@code arrive} or {@code arriveAndDeregister}.
     * @return the next arrival phase number, or the argument if it is
     * negative, or the (negative) {@linkplain #getPhase() current phase}
     * if terminated
     * @throws InterruptedException if thread interrupted while waiting
     */
    public int awaitAdvanceInterruptibly(int phase)
        throws InterruptedException {
        final Phaser root = this.root;
        long s = (root == this) ? state : reconcileState();
        int p = (int)(s >>> PHASE_SHIFT);
        if (phase < 0)
            return phase;
        if (p == phase) {
            QNode node = new QNode(this, phase, true, false, 0L);
            p = root.internalAwaitAdvance(phase, node);
            if (node.wasInterrupted)
                throw new InterruptedException();
        }
        return p;
    }
 
    /**
     * Awaits the phase of this phaser to advance from the given phase
     * value or the given timeout to elapse, throwing {@code
     * InterruptedException} if interrupted while waiting, or
     * returning immediately if the current phase is not equal to the
     * given phase value or this phaser is terminated.
     *
     * @param phase an arrival phase number, or negative value if
     * terminated; this argument is normally the value returned by a
     * previous call to {@code arrive} or {@code arriveAndDeregister}.
     * @param timeout how long to wait before giving up, in units of
     *        {@code unit}
     * @param unit a {@code TimeUnit} determining how to interpret the
     *        {@code timeout} parameter
     * @return the next arrival phase number, or the argument if it is
     * negative, or the (negative) {@linkplain #getPhase() current phase}
     * if terminated
     * @throws InterruptedException if thread interrupted while waiting
     * @throws TimeoutException if timed out while waiting
     */
    public int awaitAdvanceInterruptibly(int phase,
                                         long timeout, TimeUnit unit)
        throws InterruptedException, TimeoutException {
        long nanos = unit.toNanos(timeout);
        final Phaser root = this.root;
        long s = (root == this) ? state : reconcileState();
        int p = (int)(s >>> PHASE_SHIFT);
        if (phase < 0)
            return phase;
        if (p == phase) {
            QNode node = new QNode(this, phase, true, true, nanos);
            p = root.internalAwaitAdvance(phase, node);
            if (node.wasInterrupted)
                throw new InterruptedException();
            else if (p == phase)
                throw new TimeoutException();
        }
        return p;
    }
 
    /**
     * Forces this phaser to enter termination state.  Counts of
     * registered parties are unaffected.  If this phaser is a member
     * of a tiered set of phasers, then all of the phasers in the set
     * are terminated.  If this phaser is already terminated, this
     * method has no effect.  This method may be useful for
     * coordinating recovery after one or more tasks encounter
     * unexpected exceptions.
     */
    public void forceTermination() {
        // Only need to change root state
        final Phaser root = this.root;
        long s;
        while ((s = root.state) >= 0) {
            if (UNSAFE.compareAndSwapLong(root, stateOffset,
                                          s, s | TERMINATION_BIT)) {
                // signal all threads
                releaseWaiters(0); // Waiters on evenQ
                releaseWaiters(1); // Waiters on oddQ
                return;
            }
        }
    }
 
    /**
     * Returns the current phase number. The maximum phase number is
     * {@code Integer.MAX_VALUE}, after which it restarts at
     * zero. Upon termination, the phase number is negative,
     * in which case the prevailing phase prior to termination
     * may be obtained via {@code getPhase() + Integer.MIN_VALUE}.
     *
     * @return the phase number, or a negative value if terminated
     */
    public final int getPhase() {
        return (int)(root.state >>> PHASE_SHIFT);
    }
 
    /**
     * Returns the number of parties registered at this phaser.
     *
     * @return the number of parties
     */
    public int getRegisteredParties() {
        return partiesOf(state);
    }
 
    /**
     * Returns the number of registered parties that have arrived at
     * the current phase of this phaser. If this phaser has terminated,
     * the returned value is meaningless and arbitrary.
     *
     * @return the number of arrived parties
     */
    public int getArrivedParties() {
        return arrivedOf(reconcileState());
    }
 
    /**
     * Returns the number of registered parties that have not yet
     * arrived at the current phase of this phaser. If this phaser has
     * terminated, the returned value is meaningless and arbitrary.
     *
     * @return the number of unarrived parties
     */
    public int getUnarrivedParties() {
        return unarrivedOf(reconcileState());
    }
 
    /**
     * Returns the parent of this phaser, or {@code null} if none.
     *
     * @return the parent of this phaser, or {@code null} if none
     */
    public Phaser getParent() {
        return parent;
    }
 
    /**
     * Returns the root ancestor of this phaser, which is the same as
     * this phaser if it has no parent.
     *
     * @return the root ancestor of this phaser
     */
    public Phaser getRoot() {
        return root;
    }
 
    /**
     * Returns {@code true} if this phaser has been terminated.
     *
     * @return {@code true} if this phaser has been terminated
     */
    public boolean isTerminated() {
        return root.state < 0L;
    }
 
    /**
     * 返回true表示终止，返回false表示正常执行。
     */
    protected boolean onAdvance(int phase, int registeredParties) {
        return registeredParties == 0;
    }
 
    /**
     * Returns a string identifying this phaser, as well as its
     * state.  The state, in brackets, includes the String {@code
     * "phase = "} followed by the phase number, {@code "parties = "}
     * followed by the number of registered parties, and {@code
     * "arrived = "} followed by the number of arrived parties.
     *
     * @return a string identifying this phaser, as well as its state
     */
    public String toString() {
        return stateToString(reconcileState());
    }
 
    /**
     * Implementation of toString and string-based error messages
     */
    private String stateToString(long s) {
        return super.toString() +
            "[phase = " + phaseOf(s) +
            " parties = " + partiesOf(s) +
            " arrived = " + arrivedOf(s) + "]";
    }
 
    // Waiting mechanics
 
    /**
     * Removes and signals threads from queue for phase.
     */
    private void releaseWaiters(int phase) {
        QNode q;   // first element of queue
        Thread t;  // its thread
        AtomicReference<QNode> head = (phase & 1) == 0 ? evenQ : oddQ;
        while ((q = head.get()) != null &&
               q.phase != (int)(root.state >>> PHASE_SHIFT)) {
            if (head.compareAndSet(q, q.next) &&
                (t = q.thread) != null) {
                q.thread = null;
                LockSupport.unpark(t);
            }
        }
    }
 
    /**
     * Variant of releaseWaiters that additionally tries to remove any
     * nodes no longer waiting for advance due to timeout or
     * interrupt. Currently, nodes are removed only if they are at
     * head of queue, which suffices to reduce memory footprint in
     * most usages.
     *
     * @return current phase on exit
     */
    private int abortWait(int phase) {
        AtomicReference<QNode> head = (phase & 1) == 0 ? evenQ : oddQ;
        for (;;) {
            Thread t;
            QNode q = head.get();
            int p = (int)(root.state >>> PHASE_SHIFT);
            if (q == null || ((t = q.thread) != null && q.phase == p))
                return p;
            if (head.compareAndSet(q, q.next) && t != null) {
                q.thread = null;
                LockSupport.unpark(t);
            }
        }
    }
 
    /** The number of CPUs, for spin control */
    private static final int NCPU = Runtime.getRuntime().availableProcessors();
 
    /**
     * The number of times to spin before blocking while waiting for
     * advance, per arrival while waiting. On multiprocessors, fully
     * blocking and waking up a large number of threads all at once is
     * usually a very slow process, so we use rechargeable spins to
     * avoid it when threads regularly arrive: When a thread in
     * internalAwaitAdvance notices another arrival before blocking,
     * and there appear to be enough CPUs available, it spins
     * SPINS_PER_ARRIVAL more times before blocking. The value trades
     * off good-citizenship vs big unnecessary slowdowns.
     */
    static final int SPINS_PER_ARRIVAL = (NCPU < 2) ? 1 : 1 << 8;
 
    /**
     * Possibly blocks and waits for phase to advance unless aborted.
     * Call only on root phaser.
     *
     * @param phase current phase
     * @param node if non-null, the wait node to track interrupt and timeout;
     * if null, denotes noninterruptible wait
     * @return current phase
     */
    private int internalAwaitAdvance(int phase, QNode node) {
        // assert root == this;
        releaseWaiters(phase-1);          // ensure old queue clean
        boolean queued = false;           // true when node is enqueued
        int lastUnarrived = 0;            // to increase spins upon change
        int spins = SPINS_PER_ARRIVAL;
        long s;
        int p;
        while ((p = (int)((s = state) >>> PHASE_SHIFT)) == phase) {
            if (node == null) {           // spinning in noninterruptible mode
                int unarrived = (int)s & UNARRIVED_MASK;
                if (unarrived != lastUnarrived &&
                    (lastUnarrived = unarrived) < NCPU)
                    spins += SPINS_PER_ARRIVAL;
                boolean interrupted = Thread.interrupted();
                if (interrupted || --spins < 0) { // need node to record intr
                    node = new QNode(this, phase, false, false, 0L);
                    node.wasInterrupted = interrupted;
                }
            }
            else if (node.isReleasable()) // done or aborted
                break;
            else if (!queued) {           // push onto queue
                AtomicReference<QNode> head = (phase & 1) == 0 ? evenQ : oddQ;
                QNode q = node.next = head.get();
                if ((q == null || q.phase == phase) &&
                    (int)(state >>> PHASE_SHIFT) == phase) // avoid stale enq
                    queued = head.compareAndSet(q, node);
            }
            else {
                try {
                    ForkJoinPool.managedBlock(node);
                } catch (InterruptedException ie) {
                    node.wasInterrupted = true;
                }
            }
        }
 
        if (node != null) {
            if (node.thread != null)
                node.thread = null;       // avoid need for unpark()
            if (node.wasInterrupted && !node.interruptible)
                Thread.currentThread().interrupt();
            if (p == phase && (p = (int)(state >>> PHASE_SHIFT)) == phase)
                return abortWait(phase); // possibly clean up on abort
        }
        releaseWaiters(phase);
        return p;
    }
 
    /**
     * Wait nodes for Treiber stack representing wait queue
     */
    static final class QNode implements ForkJoinPool.ManagedBlocker {
        final Phaser phaser;
        final int phase;
        final boolean interruptible;
        final boolean timed;
        boolean wasInterrupted;
        long nanos;
        final long deadline;
        volatile Thread thread; // nulled to cancel wait
        QNode next;
 
        QNode(Phaser phaser, int phase, boolean interruptible,
              boolean timed, long nanos) {
            this.phaser = phaser;
            this.phase = phase;
            this.interruptible = interruptible;
            this.nanos = nanos;
            this.timed = timed;
            this.deadline = timed ? System.nanoTime() + nanos : 0L;
            thread = Thread.currentThread();
        }
 
        public boolean isReleasable() {
            if (thread == null)
                return true;
            if (phaser.getPhase() != phase) {
                thread = null;
                return true;
            }
            if (Thread.interrupted())
                wasInterrupted = true;
            if (wasInterrupted && interruptible) {
                thread = null;
                return true;
            }
            if (timed) {
                if (nanos > 0L) {
                    nanos = deadline - System.nanoTime();
                }
                if (nanos <= 0L) {
                    thread = null;
                    return true;
                }
            }
            return false;
        }
 
        public boolean block() {
            if (isReleasable())
                return true;
            else if (!timed)
                LockSupport.park(this);
            else if (nanos > 0L)
                LockSupport.parkNanos(this, nanos);
            return isReleasable();
        }
    }
 
    // Unsafe mechanics
 
    private static final sun.misc.Unsafe UNSAFE;
    private static final long stateOffset;
    static {
        try {
            UNSAFE = sun.misc.Unsafe.getUnsafe();
            Class<?> k = Phaser.class;
            stateOffset = UNSAFE.objectFieldOffset
                (k.getDeclaredField("state"));
        } catch (Exception e) {
            throw new Error(e);
        }
    }
}
 
```

# 参考

Java Concurrency代码实例之五-同步工具: https://zhuanlan.zhihu.com/p/27829595

exchanger源码分析： https://blog.csdn.net/wutian713/article/details/77574056

exchanger源码解析： https://www.cnblogs.com/wangzhongqiu/p/8568689.html

死磕 java同步系列之Phaser源码解析： https://www.cnblogs.com/tong-yuan/p/11614755.html
