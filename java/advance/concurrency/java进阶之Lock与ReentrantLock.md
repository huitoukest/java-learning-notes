---
title: "java进阶之Lock与ReentrantLock"
date: "2019-06-07 16:10:48"
categories: ["j2se", "java进阶学习笔记"]
tags: ["java", "Lock", "ReentrantLock", "锁"]
---

# 简介

Lock与ReentrantLock都是java.util.concurrent.locks包中常用的接口和类。

其中ReentrantLock是Lock最常见的一个实现类。

# Lock

Lock是一个接口：

```java

public interface Lock {

    //获取锁，会'休眠'到当前线程成功获取

    void lock();

    /**

     * 获取锁，和lock不同的是：由于这里是显示中断，所以优先处理中断相应，即当一个线程在获取锁之前

     * 被中断了，优先响应此重点，则抛出中断异常（而不是先获取锁）

     */

    void lockInterruptibly() throws InterruptedException;

    /**

     * 如果该锁没有被另一个线程保持，则获取锁并且立即返回 true 值；

     * 如果该锁被另外一个线程持有，立即返回false；

     */

    boolean tryLock();

    //tryLock等效于tryLock(0, TimeUnit.SECONDS)

    boolean tryLock(long time, TimeUnit unit) throws InterruptedException;

    /**

     * 释放锁，一般实现类功能会更强，一般会有如下功能：

     *  限制释放锁的线程（如果不是持有锁的线程可能会抛出异常）

     */

    void unlock();

    /**

     * 返回一个新的Condition实例，它必须是绑定到当前Lock实例的。

     * 在等待此Condition实例前，lock实例只能被当前线程持有。

     * Condition是一种广义上的条件队列。他为线程提供了一种更为灵活的等待/唤醒模式；

     * Condition和Lock的实例一一对应。

     */

    Condition newCondition();

}

```

Lock 使用方法：

```java

Lock lock = xxx;

lock.lock();

try{

    //处理任务

}catch(Exception ex){



}finally{

    //释放锁

    lock.unlock();

}

```

# ReentrantLock

ReentrantLock具有公平和非公平两种模式，也各有优缺点：

公平锁是严格的以FIFO的方式进行锁的竞争，但是非公平锁是无序的锁竞争，刚释放锁的线程很大程度上能比较快的获取到锁，队列中的线程只能等待，所以非公平锁可能会有“饥饿”的问题。但是重复的锁获取能减小线程之间的切换，而公平锁则是需要频繁的线程切换，这样对操作系统的影响是比较大的，所以非公平锁的吞吐量是大于公平锁的，这也是为什么JDK将非公平锁作为默认的实现

## 使用注意

1. 获取锁与释放锁一一对应，只有某线程释放与获取成功的次数相同时，才会真正的释放此锁，否则只是锁的重入计数器值减去1。

2. 公平锁和非公平锁，是针对获取锁而言的，如果一个锁是公平的，那么锁的获取顺序就应该符合（获取锁）请求上的绝对时间顺序，满足FIFO（但是对应线程而言并不一定是公平的）。

3. 公平锁每次都是从同步队列中的第一个节点获取到锁；非公平性锁则不一定，有可能刚释放锁的线程能再次获取到锁。

## 源码简单析

基于jdk8 202版本。

```java

package java.util.concurrent.locks;

import java.util.concurrent.TimeUnit;

import java.util.Collection;



/**

* 是和synchronized功能基本相同的一个可重入互斥锁，且有扩展功能。

*

* 如果当前线程锁定，未释放锁，则立即返回，可通过isHeldByCurrentThread和getHoldCount方法判断

*

* 构造时候，可以选择是否公平的参数。公平锁的多线程下吞吐量会比非公平的小很多。且锁的公平性质不能保证线程的公平性。

* 总是以加锁的状态来序列化，反序列的对象也总是释放锁的状态。

* 此锁最多支持2147483647个递归锁

* 相同的线程。试图超过此限制会导致

* {@link Error}从锁定方法抛出。

* @since 1.5

* @author Doug Lea

*/

public class ReentrantLock implements Lock, java.io.Serializable {

    private static final long serialVersionUID = 7373984872572414699L;

    /** 保持具体的同步机制 */

    private final Sync sync;

    /**

    * 此lock的同步控制基础类，其子类有公平与非公平的实现，

    * 使用ASQ状态表示锁定的持有数量

    */

    abstract static class Sync extends AbstractQueuedSynchronizer {

        private static final long serialVersionUID = -5179523762034025860L;

        abstract void lock();



        /**

        * 提供执行非公平的tryLock，tryAcquire 被子类实现，但都需要非公平的

        * try for trylock method

        */

        final boolean nonfairTryAcquire(int acquires) {

            final Thread current = Thread.currentThread();

            //ASQ中方法，获取当前同步状态，这里的c表示锁重入的数量

            int c = getState();

            //没有线程持有锁

            if (c == 0) {

                //如果设置成功

                if (compareAndSetState(0, acquires)) {

                    setExclusiveOwnerThread(current);

                    return true;

                }

            }

            //当前线程持有锁

            else if (current == getExclusiveOwnerThread()) {

                int nextc = c + acquires;

                //递归重入锁超过最大次数限制

                if (nextc < 0) // overflow

                throw new Error("Maximum lock count exceeded");

                setState(nextc);

                return true;

            }

            return false;

        }



        protected final boolean tryRelease(int releases) {

            int c = getState() - releases;

            //只能是当前线程是持有锁的线程是才能释放锁

            if (Thread.currentThread() != getExclusiveOwnerThread())

            throw new IllegalMonitorStateException();

            boolean free = false;

            //只有重入的数量减少到0，表示真正的释放锁

            if (c == 0) {

                free = true;

                setExclusiveOwnerThread(null);

            }

            setState(c);

            return free;

        }



        protected final boolean isHeldExclusively() {

            // While we must in general read state before owner,

            // we don't need to do so to check if current thread is owner

            return getExclusiveOwnerThread() == Thread.currentThread();

        }



        final ConditionObject newCondition() {

            return new ConditionObject();

        }



        // Methods relayed from outer class



        final Thread getOwner() {

            return getState() == 0 ? null : getExclusiveOwnerThread();

        }

        //只要不是（当前）线程持有锁，那么返回的数量就是0

        final int getHoldCount() {

            return isHeldExclusively() ? getState() : 0;

        }



        final boolean isLocked() {

            return getState() != 0;

        }



        /**

        * Reconstitutes the instance from a stream (that is, deserializes it).

        */

        private void readObject(java.io.ObjectInputStream s)

        throws java.io.IOException, ClassNotFoundException {

            s.defaultReadObject();

            setState(0); // reset to unlocked state

        }

    }



    /**

    * 非公平锁的实现

    * Sync object for non-fair locks

    */

    static final class NonfairSync extends Sync {

        private static final long serialVersionUID = 7316153563782823691L;



        /**

        * 实现Lock功能，获取锁，若失败则调用acquire方法

        * Performs lock.  Try immediate barge, backing up to normal

        * acquire on failure.

        */

        final void lock() {

            if (compareAndSetState(0, 1))

            setExclusiveOwnerThread(Thread.currentThread());

            else

            acquire(1);

        }



        protected final boolean tryAcquire(int acquires) {

            return nonfairTryAcquire(acquires);

        }

    }



    /**

    * 公平锁的实现

    * Sync object for fair locks

    */

    static final class FairSync extends Sync {

        private static final long serialVersionUID = -3000897897090466540L;



        final void lock() {

            acquire(1);

        }



        /**

        * tryAcquire的公平实现，只有递归调用、无锁竞争者、或首次时可才提供访问权限

        */

        protected final boolean tryAcquire(int acquires) {

            final Thread current = Thread.currentThread();

            int c = getState();

            if (c == 0) {

                // 若锁没有被任何线程锁拥有，“当前线程”是不是CLH队列中的第一个线程线程， 若是的话，则获取该锁，设置锁的状态，并切设置锁的拥有者为“当前线程”。

                if (!hasQueuedPredecessors() &&

                compareAndSetState(0, acquires)) {

                    setExclusiveOwnerThread(current);

                    return true;

                }

            }

            else if (current == getExclusiveOwnerThread()) {

                int nextc = c + acquires;

                if (nextc < 0)

                throw new Error("Maximum lock count exceeded");

                setState(nextc);

                return true;

            }

            return false;

        }

    }



    /**

    * 默认使用非公平锁的方案

    */

    public ReentrantLock() {

        sync = new NonfairSync();

    }

    public ReentrantLock(boolean fair) {

        sync = fair ? new FairSync() : new NonfairSync();

    }



    /**

    * Acquires the lock.

    * 获取锁，

    * 1. 如果未被其余线程占有锁，则立即获取并返回，计数器置1

    * 2. 如果已经被当前线程占有，立即返回，hold计数器加1

    * 3. 若被其余线程占有锁，则阻塞等待

    */

    public void lock() {

        sync.lock();

    }



    /**

    * 和lock类似，但是优先响应线程中端，而不是先获取锁再判断中断的状态

    */

    public void lockInterruptibly() throws InterruptedException {

        sync.acquireInterruptibly(1);

    }



    /**

    * 立即返回结果，获取成功返回true，失败返回false

    */

    public boolean tryLock() {

        return sync.nonfairTryAcquire(1);

    }



    /** 同tryLock()，但是在超时时间内会等待，然后成功或者超时时间后会返回结果

    * @throws InterruptedException if the current thread is interrupted

    * @throws NullPointerException if the time unit is null

    */

    public boolean tryLock(long timeout, TimeUnit unit)

    throws InterruptedException {

        return sync.tryAcquireNanos(1, unit.toNanos(timeout));

    }



    /**

    * 释放锁，被多次lock（）的锁同样需要unlock同样的次数，

    * 才会使当前线程真正的释放锁

    * @throws IllegalMonitorStateException if the current thread does not

    *         hold this lock

    */

    public void unlock() {

        sync.release(1);

    }



    /**

    * @return the Condition object

    */

    public Condition newCondition() {

        return sync.newCondition();

    }



    /**

    * @return the number of holds on this lock by the current thread,

    *         or zero if this lock is not held by the current thread

    */

    public int getHoldCount() {

        return sync.getHoldCount();

    }



    /**

    * @return true if current thread holds this lock and false otherwise

    */

    public boolean isHeldByCurrentThread() {

        return sync.isHeldExclusively();

    }



    /**

    * 查询此Lock是否被任何线程所持有，用于检测系统状态，而不是用来做同步控制

    */

    public boolean isLocked() {

        return sync.isLocked();

    }



    public final boolean isFair() {

        return sync instanceof FairSync;

    }



    /**

    * @return the owner, or null if not owned

    */

    protected Thread getOwner() {

        return sync.getOwner();

    }



    /**

    * 查询是否有任何线程等待获取此锁。

    */

    public final boolean hasQueuedThreads() {

        return sync.hasQueuedThreads();

    }



    /**

    * 查询给定线程是否正在等待获取此锁。

    * @throws NullPointerException if the thread is null

    */

    public final boolean hasQueuedThread(Thread thread) {

        return sync.isQueued(thread);

    }



    /**

    * 返回一个等待获取锁的线程的大致数量，因为此数量是动态变化的（所以不准确）

    * 此方法主要用于监测系统状态，而不是用于线程同步

    */

    public final int getQueueLength() {

        return sync.getQueueLength();

    }



    /**

    * 返回一个包含可能等待获取此锁的线程的集合。

    * 由于实际的线程组在构建此结果时可能会动态更改，因此返回的集合是不准确的。

    * 返回的集合的元素没有特定的顺序。

    * 此方法的目的是方便子类构造（以便于提供更广泛的监控措施）。

    */

    protected Collection<Thread> getQueuedThreads() {

        return sync.getQueuedThreads();

    }



    /**

    * 查询是否有任何线程在与此锁关联的给定条件下等待。

    * 注意，因为超时和中断可能发生在任何时间，一个 true收益并不能保证未来

    * 的 signal将唤醒any线程。

    * 这种方法的设计主要是用于监测系统状态。

    */

    public boolean hasWaiters(Condition condition) {

        if (condition == null)

        throw new NullPointerException();

        if (!(condition instanceof AbstractQueuedSynchronizer.ConditionObject))

        throw new IllegalArgumentException("not owner");

        return sync.hasWaiters((AbstractQueuedSynchronizer.ConditionObject)condition);

    }



    /**

    * 返回一个当前等待此condition的大致数量，是一个上限值，非准确数量。

    */

    public int getWaitQueueLength(Condition condition) {

        if (condition == null)

        throw new NullPointerException();

        if (!(condition instanceof AbstractQueuedSynchronizer.ConditionObject))

        throw new IllegalArgumentException("not owner");

        return sync.getWaitQueueLength((AbstractQueuedSynchronizer.ConditionObject)condition);

    }



    /**

    * 返回等待此condition的线程的大致集合

    */

    protected Collection<Thread> getWaitingThreads(Condition condition) {

        if (condition == null)

        throw new NullPointerException();

        if (!(condition instanceof AbstractQueuedSynchronizer.ConditionObject))

        throw new IllegalArgumentException("not owner");

        return sync.getWaitingThreads((AbstractQueuedSynchronizer.ConditionObject)condition);

    }



    /**

    * 返回一个确定此锁的字符串，以及它的锁状态。括号内的状态，包括字符串

    *  "Unlocked"或字符串 "Locked by"随后拥有线程的 name。

    */

    public String toString() {

        Thread o = sync.getOwner();

        return super.toString() + ((o == null) ?

        "[Unlocked]" :

        "[Locked by thread " + o.getName() +         "]");

    }

}



```

### 说明

- hasQueuedPredecessors()

是通过判断"当前线程"是不是在CLH队列（可以理解为就是一个即节点是线程对象的队列）的队首，来返回AQS中是不是有比“当前线程”等待更久的线程。
