---
title: "java进阶之Condition接口"
date: "2019-07-07 08:58:48"
categories: ["j2se", "java进阶学习笔记"]
tags: ["java", "进阶", "Condition", "线程同步", "Lock"]
---

# 简介
Condition Condition 是java5加入的，全限定名 java.util.concurrent.locks.Condition，是一个接口，主要功能是配合Lock是使用，实现对象监视器的功能。Condition 其作用和Object中的wait、notify 和 notifyAll 类似（Object中的这些方法需要配合synchronized使用）。
大致功能如下：
```java
Condition await = Object  wait
Condition signal = Object   notify
Condition signalAll = Object notifyAll 
```
因为一个Lock可以有多个condition，他们分别独立控制锁资源的竞争，比Object自带方法更加精细和高效。

注意：源码分析基于jdk8 202。

# 方法
- void await()  使当前线程等待直到它被唤醒或 interrupted。
-  boolean await(long time,TimeUnit unit) 使当前线程等待被唤醒或中断，或到达指定的等待时间。
-  long awaitNanos(long nanosTimeout)  使当前线程等待被唤醒或中断，返回超时时间的大概剩余值（可能是负数）。
-  void awaitUninterruptibly()  同await() ，但是不响应中断
- boolean awaitUntil(Date deadline)  使当前线程等待信号或中断，或指定的期限结束。
- void signal()  唤醒一个等待线程。  
- void signalAll()  唤醒所有等待线程。  

## 注意
每一个condition的等待与唤醒是对应的，如果await(未指定超时时间)后没有被signal或者signalAll操作，就会导致锁一直被持有，线程被阻塞的情况。

# 示例
这里模拟一个经典的生成消费者模型。
TestUtils.printTime 方法说明：

```text
传入三个参数，第一个是开启的线程数；
第二个是每个线程内循环的次数，
第三个参数是一个回调函数，默认在线程的循环内运行，并传入每次的线程索引编码值以及循环的索引值。
```
TestUtils.printTime 会在其开启的线程运行期间阻塞主线程，并在所有开启线程都运行完毕后再打印执行时间，并执行主线程下的代码。
```java
public class ConditionTest {

    /**
     * 模拟生产者与消费者
     */
    @Test
    public void conditionTest(){
        int maxSize = 10;
        //锁对象
        Lock lock = new ReentrantLock();
        //生产者条件
        Condition producerCondition = lock.newCondition();
        //消费者条件
        Condition consumerCondition = lock.newCondition();
        //产品池
        List<Integer> productPool = new ArrayList((int) (maxSize * 1.5));
        TestUtils.printTime(10,100000,(threadIndex,innerIndex) -> {
            //即定义奇数线程是消费者,其余的为生产者，消费者
            if((threadIndex & 1) == 1 ){
                //lock必须写在try外，以防止unlock 未加锁的线程导致抛出异常
                lock.lock();
                try {
                    //没有产品了
                    while (productPool.size() == 0) {
                        //释放条件直到被环境(缓冲池满了就会被唤醒)
                        consumerCondition.await();
                    }
                    //这个时候由于锁实质上之前是释放的状态，所以再次被唤醒
                    //的时候池中的产品数量已经有很多了，且数量不固定（但是小于max值）
                    productPool.remove(0);
                    producerCondition.signal();
                }finally {
                    lock.unlock();
                }
            }else{
                //生产者
                lock.lock();
                try { 
                    //生产池子满了
                    while (productPool.size() == maxSize) {
                        //生产者释放条件，将锁让与其余想要获取此锁的等待中的线程
                        producerCondition.await();
                    }
                    productPool.add(1);
                    consumerCondition.signal();
                }finally {
                    lock.unlock();
                }
            }
        });
        Assert.assertTrue(productPool.isEmpty());
    }

}
```
在笔者笔记本上执行3s，10个线程，每个循环10w次，5个消费者，5个生产者资源的同步。

# condition接口源码分析
```java
 /**
 * jdk中给了一个使用示例
 * @since 1.5
 * @author Doug Lea
 */
public interface Condition {

    /**
     * 阻塞当前线程，直到signalled or interrupted，相关Lock自动released，此线程出于调度目的被disable
     * 直到以下 情况：
     * 1. 其余线程调用相关condition的signal、 signalAll，且此线程被awakened
     * 2. 此线程被interrupted
     * 无论哪种情况，在此方法返回到当前线程前，此线程都会先重新获取到持有的锁，保证线程持有锁。
     * 在执行此方法前，或者线程挂起的过程中发生了中断，都会抛出异常interrupted，并清除当前线程的中断状态。
     * 此时通常会抛出异常IllegalMonitorStateException，但由具体实现确定。
     * 正常情况下，实现都倾向于先响应中断，此时必须保证signal被重定向到另外一个等待的线程（如果有的话）
     */
    void await() throws InterruptedException;

    /**
     * 和await() 类似，区别是awaitUninterruptibly()在遇到中断时通常只会记录，并不抛出异常。
     */
    void awaitUninterruptibly();
    
    /**
     * 此方法会返回一个大概的纳秒数值，是传入超时时间的剩余值
     * 或者一个小于等于0的值，如果超时了
     * 通过此值可以确定是否以及重新重新等待的时间
     * 通常应用示例：
     * boolean aMethod(long timeout, TimeUnit unit) {
     *   long nanos = unit.toNanos(timeout);
     *   lock.lock();
     *   try {
     *     一直阻塞指定时间后才支持被唤醒使用
     *     while (!conditionBeingWaitedFor()) {
     *       if (nanos <= 0L)
     *         return false;
     *       nanos = theCondition.awaitNanos(nanos);
     *     }
     *     // ...
     *   } finally {
     *     lock.unlock();
     *   }
     * }
     *
     */
    long awaitNanos(long nanosTimeout) throws InterruptedException;

    /**
     * 等同于: awaitNanos(unit.toNanos(time)) > 0
     */
    boolean await(long time, TimeUnit unit) throws InterruptedException;

    /**
     *  同 await，只是时间间隔换为绝对时间
     */
    boolean awaitUntil(Date deadline) throws InterruptedException;

    /**
     * 唤醒一个waiting thread，若有多个，选择一个。
     * 唤醒未持有condition的线程，通常会抛出异常
     * IllegalMonitorStateException
     */
    void signal();

    /**
     * 每个线程都必须在重新获取到lock之后才能从await方法返回
     * Wakes up all waiting threads.
     * If any threads are waiting on this condition then they are
     * all woken up. Each thread must re-acquire the lock before it can
     * return from await.
     *
     * 唤醒未持有condition的线程，通常会抛出异常 IllegalMonitorStateException
     */
    void signalAll();
}
```
