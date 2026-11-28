---
title: "java进阶笔记之Queue队列分析"
date: "2018-05-02 14:40:48"
categories: ["j2se", "java进阶学习笔记"]
tags: ["java", "queue", "队列", "入门", "介绍"]
---

# Queue简介
Queue是一种线性的数据(队列)结构，其一般只允许在队列数据的前端(front，也称为头部head)和
数据的后端(rear，也称为尾部tail)进行数据操作。

Queue队列一般存在FIFO和LIFO两种：

- FIFO
最先插入的元素将是最先被删除的元素；
反之最后插入的元素将是最后被删除的元素；
FIFO（FIFO—first in first out）队列一般又称为“先进先出”队列。

- LIFO
后插入队列的元素先出队列，此队列有限处理最近数据。
LIFO（last in first out）后进先出队列。

在java5中新增加了java.util.Queue接口，用以支持队列的常见操作。
Queue接口继承自java.util.Collection接口。

Queue的常用实现：
Deque, LinkedList, PriorityQueue, BlockingQueue 等类。

Queue 用来存放 等待处理元素 的集合，这种场景一般用于缓冲、并发访问。

# 常见Queue的特点
- Queue

```java
public interface Queue<E> extends Collection<E> {
    boolean add(E e); // 添加元素到队列中，相当于进入队尾排队。
    boolean offer(E e); //添加元素到队列中，相当于进入队尾排队。

    E remove(); //移除队头元素
    E poll(); //移除队头元素
    E element(); //获取但不移除队列头的元素
    E peek(); //获取但不移除队列头的元素
} 
```

- Deque
    Deque(double ended queue)也是一个接口，它继承了Queue的接口规范。

```text
Deque规定了双向（又称为双端）队列的规范，即支持在队列的两端插入和移除元素。
LinkedList和ArrayDeque都是实现Deque接口，
他们俩都是双向队列.Deque中复写了一些基础而来的接口方法，方便以后查阅和扩展。
```

```java
public interface Deque<E> extends Queue<E> {
    /*head、tail operation methods*/
    void addFirst(E e);
    void addLast(E e);
    boolean offerFirst(E e);
    boolean offerLast(E e);
    E removeFirst();
    E removeLast();
    E pollFirst();
    E pollLast();
    E getFirst();
    E getLast();
    E peekFirst();
    E peekLast();
    boolean removeFirstOccurrence(Object o);
    boolean removeLastOccurrence(Object o);
    // *** Queue methods ***
    boolean add(E e);
    boolean offer(E e);
    E remove();
    E poll();
    E element();
    E peek();
    // *** Stack methods ***
    void push(E e);
    E pop();
    // *** Collection methods ***
    boolean remove(Object o);
    boolean contains(Object o);
    public int size();
    Iterator<E> iterator();
    Iterator<E> descendingIterator();
}
```

- AbstractQueue
AbstractQueue提供了Queue的操作实现的基础。AbstractQueue可以作为不允许
元素为null时，Queue的简单实现。add，remove，element方法分别基于offer，  
poll，peek的实现，但是当队列为null时，抛出异常，而不是返回false或null。

实现类   | 是否线程安全| 是否阻塞 | 实现原理和特点
---- | --- | -----
LinkedList | 否 | 否|  双向链表实现，所以容量是Integer的最大值
ConcurrentLinkedQueue | 是 | 否 | 线程安全的LinkedList ，采用CAS算法保证线程安全
ArrayBlockingQueue | 是 | 是 | 基于数组的阻塞队列实现，在ArrayBlockingQueue内部，维护了一个定长数组，以便缓存队列中的数据对象。需要在队列初始化时需要指定数组大小。其增删等CRUD方法都使用同一个类锁ReentrantLock。
LinkedBlockingQueue | 是 | 是 | 基于链表的阻塞队列，生产者端和消费者端分别采用了独立的锁来控制数据同步，所以并发性能较高，但是如果构造一个LinkedBlockingQueue对象，而没有指定其容量大小，LinkedBlockingQueue会默认一个类似无限大小的容量（Integer.MAX_VALUE），这样的话，如果生产者的速度一旦大于消费者的速度，也许还没有等到队列满阻塞产生，系统内存就有可能已被消耗殆尽了。
PriorityBlockingQueue | 是 | 是 | PriorityBlockingQueue里面存储的对象必须是实现Comparable接口。队列通过这个接口的compare方法确定对象的priority。 规则是：当前和其他对象比较，如果compare方法返回负数，那么在队列里面的优先级就比较高。  值得注意的是：如果将PriorityBlockingQueue队列中的全部元素循环打印出来，你会发现里面的元素并不是全部按优先级排序的，但是队列头部元素的优先级肯定是最高的。默认情况下元素采取自然顺序排列，实现compare下是用升序排序。
DelayQueue | 是 | 是 |  延迟队列，存放实现了Delayed接口的对象，只有到期后才能取出元素。
PriorityQueue | 否 | 否 | 非线程安全的非阻塞优先级队列。
ArrayDqueue |  否 | 否 | 双端队列。
SynchronousQueue | 是 | 是 |  每一个put操作必须等待一个take操作，否则不能继续添加元素。SynchronousQueue可以看成是一个传球手，负责把生产者线程处理的数据直接传递给消费者线程。队列本身并不存储任何元素，非常适合于传递性场景。SynchronousQueue的吞吐量高于LinkedBlockingQueue 和 ArrayBlockingQueue。
LinkedTransferQueue | | | LinkedTransferQueue是一个由链表结构组成的无界阻塞TransferQueue队列
注意：

1. ArrayBlockingQueue与LinkedBlockingQueue

 - 锁的实现不同
ArrayBlockingQueue实现的队列中的锁是没有分离的，即生产和消费用的是同一个锁，
由此也意味着两者无法真正并行运行。
LinkedBlockingQueue实现的队列中的锁是分离的，即生产用的是putLock，消费是takeLock。

 - 内部元素操作不同
ArrayBlockingQueue实现的队列中在生产和消费的时候，是直接将对象插入或移除的，
即不会产生任何额外的对象实例。
LinkedBlockingQueue实现的队列中在生产和消费的时候，需要把对象转换为Node进行插入或移除，
这在长时间内需要高效并发地处理大批量数据的系统中，对GC和性能会有一定影响。

 - 队列初始化方式不同
ArrayBlockingQueue实现的队列中必须指定队列的大小。
LinkedBlockingQueue实现的队列中可以不指定队列的大小，默认是Integer.MAX_VALUE。

ArrayBlockingQueue：
```java
private final Condition notFull;
private final Condition notEmpty;
public ArrayBlockingQueue(int capacity, boolean fair) {
        //省略其他代码
        notEmpty = lock.newCondition();
        notFull = lock.newCondition();
    }
public void put(E e) throws InterruptedException {
        checkNotNull(e);
        final ReentrantLock lock = this.lock;
        lock.lockInterruptibly();
        try {
            while (count == items.length)
                notFull.await();
            insert(e);
        } finally {
            lock.unlock();
        }
}
public E take() throws InterruptedException {
        final ReentrantLock lock = this.lock;
        lock.lockInterruptibly();
        try {
            while (count == 0)
                notEmpty.await();
            return extract();
  } finally {
            lock.unlock();
        }
}
private void insert(E x) {
        items[putIndex] = x;
        putIndex = inc(putIndex);
        ++count;
        notEmpty.signal();
    }

public final void await() throws InterruptedException {
            if (Thread.interrupted())
                throw new InterruptedException();
            Node node = addConditionWaiter();
            int savedState = fullyRelease(node);
            int interruptMode = 0;
            while (!isOnSyncQueue(node)) {
                LockSupport.park(this);
                if ((interruptMode = checkInterruptWhileWaiting(node)) != 0)
                    break;
            }
            if (acquireQueued(node, savedState) && interruptMode != THROW_IE)
                interruptMode = REINTERRUPT;
            if (node.nextWaiter != null) // clean up if cancelled
                unlinkCancelledWaiters();
            if (interruptMode != 0)
            reportInterruptAfterWait(interruptMode);
        }
```

setBlocker先保存下将要阻塞的线程，然后调用LockSupport.park阻塞当前线程。
```java
public static void park(Object blocker) {
        Thread t = Thread.currentThread();
        setBlocker(t, blocker);
        unsafe.park(false, 0L);
        setBlocker(t, null);
    }
```

unsafe.park是一个native方法。
```java
public native void park(boolean isAbsolute, long time);
```
调用lock.lockInterruptibly或获取锁，但是当此线程在持有此锁的时间段内，
其余的线程再次调用lock.lockInterruptibly则会导致原持有线程报错：InterruptedException
相当于lock.lockInterruptibly是一个线程中断信号。

park这个方法会阻塞当前线程，只有以下四种情况中的一种发生时，该方法才会返回。

 1. 与park对应的unpark执行或已经执行时。注意：已经执行是指unpark先执行，然后再执行的park。
 2. 线程被中断时。
 3. 如果参数中的time不是零，等待了指定的毫秒数时。
 4. 发生异常现象时。这些异常事先无法确定。

2. PriorityBlockingQueue中的priority(优先级)
在每次取完队列头时候， PriorityBlockingQueue都会对剩余的元素做一次调整，
这样就能保证每次队列头的元素都是优先级最高的元素。
所以PriorityBlockingQueue适用于自定义优先级的阻塞队列。

3. Delay延迟队列
DelayQueue是一个无界的BlockingQueue，用于放置实现了Delayed接口的对象，其中的对象只能
在其到期时才能从队列中取走。这种队列是有序的，即队头对象的延迟到期时间最长。
注意：不能将null元素放置到这种队列中。
Delayed，一种混合风格的接口，用来标记那些应该在给定延迟时间之后执行的对象。
此接口的实现必须定义一个 compareTo 方法，该方法提供与此接口的 getDelay 方法一致的排序。

4. LinkedTransferQueue
LinkedTransferQueue是一个由链表结构组成的无界阻塞TransferQueue队列。
相对于其他阻塞队列多了tryTransfer和transfer方法。
transfer方法：如果当前有消费者正在等待接收元素（消费者使用take()方法或带时间限制的poll()方法时），
transfer方法可以把生产者传入的元素立刻transfer（传输）给消费者。
如果没有消费者在等待接收元素，transfer方法会将元素存放在队列的tail节点，并等到该元素被消费者消费了才返回。
transfer方法的关键代码如下：
```java
Node pred = tryAppend(s, haveData);
return awaitMatch(s, pred, e, (how == TIMED), nanos);
```
第一行代码是试图把存放当前元素的s节点作为tail节点。
第二行代码是让CPU自旋等待消费者消费元素。
因为自旋会消耗CPU，所以自旋一定的次数后使用Thread.yield()方法来暂停当前正在执行的线程，并执行其他线程。
tryTransfer方法：是用来试探下生产者传入的元素是否能直接传给消费者。
如果没有消费者等待接收元素，则返回false。
和transfer方法的区别是tryTransfer方法无论消费者是否接收，方法立即返回。
而transfer方法是必须等到消费者消费了才返回。
对于带有时间限制的tryTransfer(E e, long timeout, TimeUnit unit)方法，则是试图把生产者传入的元素
直接传给消费者，但是如果没有消费者消费该元素则等待指定的时间再返回，
如果超时还没消费元素，则返回false，如果在超时时间内消费了元素，则返回true。

# 常见方法

<thead>

```text
<th>接口</th>
<th>方法</th>
<th>失败响应</th>
<th>说明</th>
```
</thead>
<tbody>

```java
<td rowspan="5">集合操作<br>Collection</td>
<td>	boolean remove(Object o)	</td>
<td> </td>
<td>移除第一次出现的指定元素</td>
```

```java
<td> boolean contains(Object o) </td>
<td> </td>
<td>如果包含指定元素，则返回 true </td>
```

```java
<td>public int size() </td>
<td> </td>
<td>返回此双端队列的元素数</td>
```

```java
<td>Iterator iterator() </td>
<td> </td>
<td>返回以恰当顺序在此双端队列的元素上进行迭代的迭代器 </td>
```

```java
<td>Iterator<E> descendingIterator()</td>
<td> </td>
<td>返回以逆向顺序在此双端队列的元素上进行迭代的迭代器 </td>
```

堆栈操作Stack
void push(E e)
抛出异常
将一个元素推入此双端队列所表示的堆栈

E pop()
抛出异常
从此双端队列所表示的堆栈中弹出一个元素

队列操作Queue
boolean add(E e)
抛出异常
将指定元素插入此双端队列所表示的队列

boolean offer(E e)
返回false
将指定元素插入此双端队列所表示的队列

E remove()
抛出异常
获取并移除此双端队列所表示的队列的头部

E poll()
返回null
获取并移除此双端队列所表示的队列的头部

E element()
抛出异常
获取，但不移除此双端队列所表示的队列的头部

E peek()
返回null
获取，但不移除此双端队列所表示的队列的头部

双端队列操作DeQueue
void addFirst(E e)
抛出异常
将指定元素插入此双端队列的开头

void addLast(E e)
抛出异常
将指定元素插入此双端队列的末尾

boolean offerFirst(E e)
返回false
将指定的元素插入此双端队列的开头

boolean offerLast(E e)
返回false
将指定的元素插入此双端队列的末尾

E removeFirst()
若队列为空，抛出异常
获取并移除此双端队列第一个元素

E removeLast()
若队列为空，抛出异常
获取并移除此双端队列的最后一个元素

E pollFirst()
如果此双端队列为空，则返回 null
获取并移除此双端队列的第一个元素；

E pollLast();
如果此双端队列为空，则返回 null
获取并移除此双端队列的最后一个元素；

E getFirst()
抛出异常
获取，但不移除此双端队列的第一个元素

E getLast()
抛出异常
获取，但不移除此双端队列的最后一个元素

E peekFirst()
返回null
获取，但不移除此双端队列的第一个元素

E peekLast()
返回null
获取，但不移除此双端队列的最后一个元素

boolean removeFirstOccurrence(Object o)

从此双端队列移除第一次出现的指定元素

boolean removeLastOccurrence(Object o)

从此双端队列移除最后一次出现的指定元素

</tbody>

# 参考
https://blog.csdn.net/wuseyukui/article/details/68609089
https://www.cnblogs.com/xinhuaxuan/p/6382253.html
http://ifeve.com/java-blocking-queue/
