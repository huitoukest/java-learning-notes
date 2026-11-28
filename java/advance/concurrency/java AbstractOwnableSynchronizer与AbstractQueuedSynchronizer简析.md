---
title: "java AbstractOwnableSynchronizer与AbstractQueuedSynchronizer简析"
date: "2019-08-27 17:21:42"
categories: ["java进阶学习笔记"]
tags: ["ASQ", "AbstractQueuedSynchronizer", "java进阶", "Condition"]
---

# 简介
AbstractQueuedSynchronizer全限定名java.util.concurrent.locks.AbstractQueuedSynchronizer，继承自java.util.concurrent.locks.AbstractOwnableSynchronizer。

# AbstractOwnableSynchronizer 源码简析
从源码来看，AbstractOwnableSynchronizer 主要提供了一个功能，就是设置和获取某个排他同步模式下的所有者线程。
AbstractOwnableSynchronizer有非常多的实现。
```java
/**
 * AbstractOwnableSynchronizer 是一个只能被一个线程排他拥有的同步者
 * 此类是创建lock与同步所有权相关概念的基础类，此类自身并不管理或使用这些信息
 * 但是，其子类和工具类可能被用于  辅助控制监控权限和提供诊断
 * @since 1.6
 * @author Doug Lea
 */
public abstract class AbstractOwnableSynchronizer
    implements java.io.Serializable {
    private static final long serialVersionUID = 3737899427754241961L;
    protected AbstractOwnableSynchronizer() { }
    /**
     * 排他同步模式下的所有者线程
     */
    private transient Thread exclusiveOwnerThread;

    /**
     * 设置当前拥有独占访问权限的线程。
     * null 参数指示没有线程拥有访问权限。
     * 此方法不会强制实施任何同步或 volatile字段访问。
     * @param thread 需要设置的所有者线程
     */
    protected final void setExclusiveOwnerThread(Thread thread) {
        exclusiveOwnerThread = thread;
    }

    /**
     * 返回上一次设置的线程，或者null ，此方法不提供同步或者volatile修饰功能
     * @return the owner thread
     */
    protected final Thread getExclusiveOwnerThread() {
        return exclusiveOwnerThread;
    }
}
```

## AbstractQueuedSynchronizer 简介

## AbstractQueuedSynchronizer源码简析

### AbstractQueuedSynchronizer类注释译
ps:
1. 同步队列节点分为独占节点和共享节点。对于独占节点，必须独占节点释放后，后继节点才能运行。
而对于共享节点而言，共享节点后的共享节点(符合数量等子类要求）都可以同时运行，共享节点后
的独占节点则会被阻塞。

2. 独占模式：即state值在0和1之前来回切换，保证同一时间只能有一个线程是处于活动的，其他线程都被阻塞.
3. 共享模式：state值在整数区间内，如果state值<0则阻塞，否则则不阻塞

4. AQS中阻塞队列采用的是用双向链表保存，用prve和next相互链接。
而AQS中条件队列是使用单向列表保存的，用nextWaiter来连接。
等待队列和同步队列，只是使用了Node的不同（字段来）链接(应该是为了编码方便，所以只造了一个Node类)。

5. 每次new一个Condition并使用ASQ的await方法时就会向等待队列中插入一个Node，唤醒则是将之转移
到同步队列中。

6. 每个节点都有一个等待状态，但是同步队列只有一个队列状态。

```java
/**
* 提供了一个为实现阻塞锁和依赖于FIFO等待队列的和同步器（如信号量，事件等）相关的框架。
* 此类被设计为一个大多数同步器的基础类，它们都依赖于一个原子值来表示状态。
* 子类必须定义一些protected方法来改变这些状态，同时定义当此对象被获取或者释放的时候 这些状态代表的意义。
* 考虑到这些，这个类中的其余方法实现所有的排队和阻塞机制。子类可以维护其他的状态字段，
* 但是仅使用getState、setState、compareAndSetState，方法来维护更新原子值。

* 子类应该被定义为实现其封闭类的，实现它们的内置类的同步属性法没有public内部类的helper类。
* 类AbstractQueuedSynchronizer未实现任何的同步接口，取而代之的是定义了如acquireInterruptibly这种
* 方法，它们可以适当的调用，且通过具体的锁和相关的同步器通去实现他们的方法。
 *
 * 这个类同时支持独占排它模式和共享模式。在排它模式中尝试获取时，其它尝试获取的线程将无法成功。
 * 共享模式下则可能被多个线程成功（但不必定）获取。此类无法 ‘明白’ 这些差异(指共享和独占模式的差异)，除非是在一个同步机制场景下：
 * 当一个共享模式获取成功时，下一个等待线程（如果存在）还必须确定它是否也可以获取。
 *  
* 在不同模式下等待的线程共享一个相同的FIFO队列。
* 通常，实现的子类只支持其中一种模式，但是这两种模式都可以发挥作用，
* 例如在readwritelock 中。只支持独占或共享模式的子类不需要定义支持未使用模式的方法。
* 
* 此类定义了一个内置的ConditionObject类，它作为一个Condition的实现被使用，通过子类支持独占模式
* 为方法 isHeldExclusively 报告同步器是否相对于前线程是排它持有的，方法release通过调用getState得到
* 当前值来完全地释放当前对象，而acquire提供了保存的状态值，最终将此对象恢复到其先前获得的状态。
* 否则不会有AbstractQueuedSynchronizer创造的这些条件，因此，如果不能满足这个约束，
* 就不要使用它。{@link ConditionObject}的行为当然取决于它的同步器实现的语义。
*
* 这个类为内置队列提供了检查，仪表、监控方法，也为condition对象提供了类似方法。
* 可以根据需要使用 AbstractQueuedSynchronizer将它们导出到类中，用于它们的同步机制。
 *
* 该类的序列化保存值存储底层原子整数维护状态，因此反序列化对象有空的线程队列。
* 通常，子类序列化需要定义一个readObject方法来将此对象恢复到已知的初始化状态。
 * 使用：
 * 为了将此类作为一个同步器的基础类使用，重定义如下方法，适当的通过检查和使用
* getState、setState、compareAndSetState来合并同步器的状态：
* tryAcquire
* tryRelease
* tryAcquireShared
* tryReleaseShared
* isHeldExclusively
* 这些方法都默认抛出异常UnsupportedOperationException 
* 实现这些方法必须保证内部的线程安全，且一般而言耗时短而不阻塞，
* 定义这些方式是使用此类的推荐方法。所有其余的方式都被定义为final，
* 因为它们不能独立更改。
* 
* 你也许同时发现了从AbstractOwnableSynchronizer继承而来的一些方法，用来保持
* 跟踪线程拥有的排它同步器。推荐使用这些方法，这些监控和诊断工具能辅助使用者
* 确保哪一个线程持有锁。
*
* 尽管此类是建立在一个内置的FIFO队列上，但它并不强制要求执行FIFO接收策略。
* 核心的排它同步器来自于：
* 获取:
 *     while (!tryAcquire(arg)) {
 *      若未排队则进入队列，可能阻塞当前线程
 *     }
 *
 * Release:
 *     if (tryRelease(arg))
 *        unblock 队列首的线程。
* (共享模式也类似，但可能涉及级联的更新信号)
* 因为在进入队列前通过调用acquire就已经检查了，一个最新的获取线程可能
* 抢在其他被阻挡和排队的线程前面。然后，如果你想要，你可以定义tryAcquire方法或者
* tryAcquireShared方法来通过内部调用一个或多个检查方法来禁用抢占功能，
* 从而提供一个fair FIFO获取顺序。特别是，大多数同步器能够定义tryAcquire返回false，
* 当hasQueuedPredecessors（一个为非公平同步器设计的方法）返回true的时候。其它变化也有可能。
 *
 * 吞吐量和可伸缩性通常在默认的barging（闯入）(也称为贪心、拒绝和 队列-避免)策略中最高。
* 虽然不能保证这是公平的或无饥饿的，但是允许较早的队列线程在较晚的队列线程之前重新争用，
* 并且每次重新争用都有无偏倚的机会对传入的线程成功争用。
*  而且，当这里的获得不是通常意义上的“循环”，它们可以执行多次调用 tryAcquire，
*  并在阻塞之前穿插其他计算。当独占同步只被短暂地持有时，这就提供了自旋的大部分好处，
* 而当独占同步不被短暂持有时，则无需承担大部分责任。
* 如果需要，您可以通过前面的调用来增强这一点，以获得带有“fast-path”检查的方法，
* 可能需要预先检查 hasContended和/或 hasQueuedThreads，
* 只有在同步器可能不存在争用时才这样做。
*
* 这个类通过分离其同步的部分，为同步提供了一个高效和可扩展的基础，
* 同步的部分依赖于state状态，获取和释放的参数，以及一个内置的FIFO等待队列。
* 不仅如此，你还可以通过使用java.util.concurrent.atomic包下的类这种更底层的方式建立同步器，
* 你可以自定义Queue队列以及LockSupport的阻塞支持。
 * @since 1.5
 * @author Doug Lea
 */
```
### AQS类注释示例一

```java
// 一下是类注释上的示例，这里单独罗列
/ **
* 这里是一个不可重入的互斥锁类，它使用值0来表示unlocked 状态，值1表示
* locked状态。虽然非重入锁并不严格要求记录当前所有者线程，但是这个类这样做是为了使使用更容易监控。
* 它还支持条件conditions 并公开其中一种检测方法
 */
 class Mutex implements Lock, java.io.Serializable {
 // Our internal helper class
    private static class Sync extends AbstractQueuedSynchronizer {
      // 记录是否是 locked state
     protected boolean isHeldExclusively() {
        return getState() == 1;
      }
 
     // Acquires the lock if state is zero
      public boolean tryAcquire(int acquires) {
        assert acquires == 1; // Otherwise unused
        if (compareAndSetState(0, 1)) {
          setExclusiveOwnerThread(Thread.currentThread());
          return true;
        }
        return false;
      }
 
      // 释放锁 by setting state to zero
      protected boolean tryRelease(int releases) {
        assert releases == 1; // Otherwise unused
        if (getState() == 0) throw new IllegalMonitorStateException();
        setExclusiveOwnerThread(null);
        setState(0);
       return true;
      }
 
      // Provides a Condition
      Condition newCondition() { return new ConditionObject(); }
 
      // Deserializes properly，反序列化属性
      private void readObject(ObjectInputStream s)
          throws IOException, ClassNotFoundException {
        s.defaultReadObject();
        setState(0); // reset to unlocked state
      }
    }

    // The sync object does all the hard work. We just forward to it.
    private final Sync sync = new Sync();

    public void lock()                { sync.acquire(1); }
    public boolean tryLock()          { return sync.tryAcquire(1); }
    public void unlock()              { sync.release(1); }
    public Condition newCondition()   { return sync.newCondition(); }
    public boolean isLocked()         { return sync.isHeldExclusively(); }
    public boolean hasQueuedThreads() { return sync.hasQueuedThreads(); }
    public void lockInterruptibly() throws InterruptedException {
      sync.acquireInterruptibly(1);
    }
    public boolean tryLock(long timeout, TimeUnit unit)
        throws InterruptedException {
      return sync.tryAcquireNanos(1, unit.toNanos(timeout));
    }
  }}
```

### ASQ自带类注释示例2

```java
/**
* 这是一个闩锁类，类似于  java.util.concurrent，不同的是它只需要一个code信号来触发。
* 因为此锁存器是非排他的，所以它使用共享的获取和释放方法。
* 即多个线程共同获取共享资源，共同被释放。
* 实际上，这里使用值1表示被(多个线程)共享，值0表示不被共享。
 */
  class BooleanLatch {
    private static class Sync extends AbstractQueuedSynchronizer {
      //只要返回的!=0 则可以获取锁，否则AQS会调用unsafe的park挂起线程                                 
      boolean isSignalled() { return getState() != 0; }

      protected int tryAcquireShared(int ignore) {
        return isSignalled() ? 1 : -1;
      }
      protected boolean tryReleaseShared(int ignore) { 
       //设置当前AQS队列的状态为1；返回true—表示在共享模式下，解除锁状态成功。
        setState(1);
        return true;
      }
    }
    private final Sync sync = new Sync();
   // 提供给BooleanLatch的使用者，通过判定AQS队列的state状态，确认是否已经发出“信号”
    public boolean isSignalled() { return sync.isSignalled(); }
  //唤醒共享节点
    public void signal()         { sync.releaseShared(1); }
 //阻塞共享节点
    public void await() throws InterruptedException {
      sync.acquireSharedInterruptibly(1);
    }
  }}
```

### ASQ源码

```java
//开始真正的源码查阅
public abstract class AbstractQueuedSynchronizer
    extends AbstractOwnableSynchronizer
    implements java.io.Serializable {

    private static final long serialVersionUID = 7373984972572414691L;

    /**
     * Creates a new {@code AbstractQueuedSynchronizer} instance
     * with initial synchronization state of zero.
     */
    protected AbstractQueuedSynchronizer() { }
    //这里定义了一个Node类，提出来单独查阅
    static final class Node {... } 
/**
 * 等待队列的head Node，仅通过方法设置初始化，若head已经存在，
 * 它的等待状态将被保证不会CANCELLED.
 */
private transient volatile Node head;

/**
 * Tail of the wait queue, lazily initialized.
 * 仅通过加入新等待节点的方法进入队列.
 */
private transient volatile Node tail;

/**
 * 同步的状态.
 */
private volatile int state;

/**
 * 返回当前同步状态，只读.
 * @return current state value
 */
protected final int getState() {
    return state;
}

/**
 * 设置同步状态
 */
protected final void setState(int newState) {
    state = newState;
}

/**
 * 原子更新状态
 * 
 * @param expect the expected value
 * @param update the new value
 * @return true，或者except值错不符，则false.
 */
protected final boolean compareAndSetState(int expect, int update) {
    // See below for intrinsics setup to support this
    return unsafe.compareAndSwapInt(this, stateOffset, expect, update);
}

// Queuing utilities

/**
 * 对自旋而言比定时标记更快的纳秒数。粗略的估计足以在非常短的超时情况下提高响应能力。
 */
static final long spinForTimeoutThreshold = 1000L;

/**
 * 插入队列，返回队列前置节点
 * @param node the node to insert
 * @return node's predecessor
 */
private Node enq(final Node node) {
    for (;;) {
        Node t = tail;
        if (t == null) { // Must initialize，尾为空，则其=head。
            if (compareAndSetHead(new Node()))
                tail = head;
        } else {
            node.prev = t;
            if (compareAndSetTail(t, node)) {
                t.next = node;
                return t;
            }
        }
    }
}

/**
 * 为当前线程和给定模式创建和排队节点.
 * mode支持排它和共享模式
 * @param mode Node.EXCLUSIVE for exclusive, Node.SHARED for shared
 * @return the new node
 */
private Node addWaiter(Node mode) {
    Node node = new Node(Thread.currentThread(), mode);
    // Try the fast path of enq; backup to full enq on failure
    Node pred = tail;
    if (pred != null) {
        node.prev = pred; 
        // 原子方式设置尾部节点的next
        if (compareAndSetTail(pred, node)) {
            pred.next = node;
            return node;
        }
    }
    enq(node);
    return node;
}

/**
 * 将队列头设置为节点，从而退出队列。仅通过获取方法调用。
 * 此外，为了GC和抑制不必要的信号和遍历，还将空出未使用的字段.
 * @param node the node
 */
private void setHead(Node node) {
    head = node;
    node.thread = null;
    node.prev = null;
}

/**
 * 若节点的继任者存在，则唤醒
 * @param node the node
 */
private void unparkSuccessor(Node node) {
    /*
     * 如果状态为负(即(可能需要信号)在收到信号之前，试着清除信号的含义。
     * 如果此操作失败或状态被等待线程更改，则没有问题。
     */
    int ws = node.waitStatus;
    if (ws < 0)
        compareAndSetWaitStatus(node, ws, 0);

    /*
     * Thread to unpark被保存在后续节点中，它通常只是下一个节点。
     *  但是，如果取消或明显为空，则从tail向后遍历以找到实际的非取消后继.
     */
    Node s = node.next;
    if (s == null || s.waitStatus > 0) {
        s = null;
        for (Node t = tail; t != null && t != node; t = t.prev)
            if (t.waitStatus <= 0)
                s = t;
    }
    if (s != null)
        LockSupport.unpark(s.thread);
}

/**
 * 共享模式下的释放操作：
 * Release action for shared mode -- 信号后继者，并确保传播。
 * (注意:对于独占模式，release只相当于在需要信号时调用head的unpark继任人。)
 * ps: 即共享模式下，如果是(头节点)独占节点，则唤醒头节点一个；如果是初始态
 * 则表示是共享节点，则设置为传播状态
 */
private void doReleaseShared() {
    /*
     * 确保释放传播，即使有其他正在进行的获取/释放。
     * 这就像往常一样，如果head需要信号，就会试图解开它的后继者。
     * 但如果没有，则将status设置为PROPAGATE，以确保在释放之后传播将继续。
     * 此外，我们必须循环，以防在执行此操作时添加了新节点。
     * 此外，与unpark继任人的其他用途不同，我们需要知道CAS重置状态是否失败，是否重新检查.
     */
    for (;;) {
        Node h = head;
        if (h != null && h != tail) {
            int ws = h.waitStatus;
            if (ws == Node.SIGNAL) {
                if (!compareAndSetWaitStatus(h, Node.SIGNAL, 0))
                    continue;            // loop to recheck cases
                unparkSuccessor(h);
            }
            else if (ws == 0 &&
                     !compareAndSetWaitStatus(h, 0, Node.PROPAGATE))
                continue;                // loop on failed CAS
        }
        if (h == head)                   // loop if head changed
            break;
    }
}

/**
 * 设置队列的头部，并检查后续队列是否可以在共享模式下等待，
 * 如果设置了propagate > 0或propagate status，则将进行传播.
 *
 * @param node the node
 * @param propagate the return value from a tryAcquireShared
 */
private void setHeadAndPropagate(Node node, int propagate) {
    Node h = head; // Record old head for check below
    setHead(node);
    /* 
     * 尝试向下一个队列节点释放信号，当：
     *  传播由调用方指明，或通过前置操作（注： 这使用等待状态的符号检查，因为 PROPAGATE 状态可能会转换为 SIGNAL）
     *  被记录（在setHead前后，作为等待状态）
     *  并且
     * 下个节点在共享模式下等待，或者我们不知道，因为它显示为空 
     * 它们的两种保守的检查可能造成不必要的唤醒，但是仅当它们处于多个竞争时（获取或者释放）
     * 所以在现在或不久后最需要信号。
     */
    if (propagate > 0 || h == null || h.waitStatus < 0 ||
        (h = head) == null || h.waitStatus < 0) {
        Node s = node.next;
        if (s == null || s.isShared())
            doReleaseShared();
    }
}

// Utilities for various versions of acquire

/**
 * cancel一个正在进行的acquire意图
 * @param node the node
 */
private void cancelAcquire(Node node) {
    // Ignore if node doesn't exist
    if (node == null)
        return;

    node.thread = null;

    // Skip cancelled predecessors 跳过被cancel的前继node，找到一个有效的前继节点pred
    Node pred = node.prev;
    while (pred.waitStatus > 0)
        node.prev = pred = pred.prev;
    //将node的waitStatus置为CANCELLED，predNext是未切分的节点。若不是，则以下case操作
    //将会失败，此情况下，我们将会丢失和其它线程的竞争或者信号，因此此操作有必要
    // predNext is the apparent node to unsplice. CASes below will
    // fail if not, in which case, we lost race vs another cancel
    // or signal, so no further action is necessary.
    Node predNext = pred.next;
    
    // Can use unconditional write instead of CAS here.
    // After this atomic step, other Nodes can skip past us.
    // Before, we are free of interference from other threads.
    node.waitStatus = Node.CANCELLED;
    //如果node是tail，更新tail为pred，并使pred.next指向null
    // If we are the tail, remove ourselves.
    if (node == tail && compareAndSetTail(node, pred)) {
        compareAndSetNext(pred, predNext, null);
    } else {
        // If successor needs signal, try to set pred's next-link
        // so it will get one. Otherwise wake it up to propagate.
        //5. 如果node既不是tail，又不是head的后继节点
        //则将node的前继节点的waitStatus置为SIGNAL
        //并使node的前继节点指向node的后继节点
        int ws;
        if (pred != head &&
            ((ws = pred.waitStatus) == Node.SIGNAL ||
             (ws <= 0 && compareAndSetWaitStatus(pred, ws, Node.SIGNAL))) &&
            pred.thread != null) {
            Node next = node.next;
            if (next != null && next.waitStatus <= 0)
                compareAndSetNext(pred, predNext, next);
        } else {
            //如果node是head的后继节点，则直接唤醒node的后继节点
            unparkSuccessor(node);
        }

        node.next = node; // help GC
    }
}

/** 
 * 为一个acquire失败的节点检查和更新状态，
 * 若此线程应被block，return true。
 * 这是所有acquire循环的主要控制信号，要求pred == node.prev。
 * 尝试 使用CAS将节点状态由INITIAL设置成SIGNAL，表示当前线程阻塞，成功则返回true。
 * @param pred node's predecessor holding status
 * @param node the node
 * @return {@code true} if thread should block
 */
private static boolean shouldParkAfterFailedAcquire(Node pred, Node node) {
    int ws = pred.waitStatus;
    if (ws == Node.SIGNAL)
        /*
         * 这个节点pre已经设置了请求释放的信号的状态，因此它(当前节点)可以安全地park.
         * ps： 即前置节点是独占模式，且已经唤醒，后继节点没必要循环获取(锁)了。
         *   需要等待前置节点释放后，再唤醒后继节点。
         */
        return true;
    if (ws > 0) {
        /* 前置节点结束了，忽略前置节点并重试，找到一个非结束或取消的前置
         * Predecessor was cancelled. Skip over predecessors and
         * indicate retry.
         */
        do {
            node.prev = pred = pred.prev;
        } while (pred.waitStatus > 0);
        pred.next = node;
    } else {
        /* 如果前置节点是0或者PROPAGATE，都明确表示我们需要一个唤醒信号。
         * 但是，此模式下不需要阻塞后继节点。返回false，确保重试获取前不会被阻塞。
         * waitStatus must be 0 or PROPAGATE.  Indicate that we
         * need a signal, but don't park yet.  Caller will need to
         * retry to make sure it cannot acquire before parking.
         */
        compareAndSetWaitStatus(pred, ws, Node.SIGNAL);
    }
    return false;
}

/**
 * Convenience method to interrupt current thread.
 */
static void selfInterrupt() {
    Thread.currentThread().interrupt();
}

/**
 * Convenience method to park and then check if interrupted
 *
 * @return {@code true} if interrupted
 */
private final boolean parkAndCheckInterrupt() {
    LockSupport.park(this);
    return Thread.interrupted();
}

/*
 * 不同的获取风格，在独占/共享模式中各不相同。
 * 大同小异，但并不相同。由于异常机制(包括确保我们在尝试获取抛出异常时取消)
 * 和其他控件之间的交互，只有少量的参数是共通的，至少不会对性能造成太大影响。
 */
/**
 * 获取队列中已存在线程的独占不可中断模式。用于条件等待方法以及获取。
 * ps：排队获取锁，直到异常或者成功
 * @param node the node
 * @param arg the acquire argument
 * @return {@code true} if interrupted while waiting
 */
final boolean acquireQueued(final Node node, int arg) {
    boolean failed = true;
    try {
        boolean interrupted = false;
        //循环获取
        for (;;) {
            final Node p = node.predecessor();
            //前置节点是头节点才开始获取
           // 如果成功获取同步状态，即可以获得独占式锁
            if (p == head && tryAcquire(arg)) {
                //队列头指针用指向当前节点
                setHead(node);
                p.next = null; // help GC
                failed = false;
                return interrupted;
            }
            //获取锁失败，线程进入等待状态等待获取独占式锁
           //如果当前线程应该被park(前置节点状态是唤醒后继节点时)，则挂起线程
           //减少cpu损耗
            if (shouldParkAfterFailedAcquire(p, node) &&
                parkAndCheckInterrupt())
                interrupted = true;
        }
    } finally {
        if (failed)
            cancelAcquire(node);
    }
}

/**
 * ps：同队列获取，中断模式下的获取
 *  区别是当parkAndCheckInterrupt返回true时即线程阻塞时该线程被中断，代码抛出被中断异常。
 * Acquires in exclusive interruptible mode.
 * @param arg the acquire argument
 */
private void doAcquireInterruptibly(int arg)
    throws InterruptedException {
    final Node node = addWaiter(Node.EXCLUSIVE);
    boolean failed = true;
    try {
        for (;;) {
            final Node p = node.predecessor();
            if (p == head && tryAcquire(arg)) {
                setHead(node);
                p.next = null; // help GC
                failed = false;
                return;
            }
            if (shouldParkAfterFailedAcquire(p, node) &&
                parkAndCheckInterrupt())
                throw new InterruptedException();
        }
    } finally {
        if (failed)
            cancelAcquire(node);
    }
}

/**
 * Acquires in exclusive timed mode.
 *
 * @param arg the acquire argument
 * @param nanosTimeout max wait time
 * @return {@code true} if acquired
 */
private boolean doAcquireNanos(int arg, long nanosTimeout)
        throws InterruptedException {
    if (nanosTimeout <= 0L)
        return false;
    //计算出截止时间
    final long deadline = System.nanoTime() + nanosTimeout;
    final Node node = addWaiter(Node.EXCLUSIVE);
    boolean failed = true;
    try {
        for (;;) {
            final Node p = node.predecessor();
            if (p == head && tryAcquire(arg)) {
                setHead(node);
                p.next = null; // help GC
                failed = false;
                return true;
            }
            // 重新计算超时时间
            nanosTimeout = deadline - System.nanoTime();
            if (nanosTimeout <= 0L)
                return false;
            //线程阻塞等待, spinForTimeoutThreshold 为定义的自旋的对比时间（1000）
            //因为当前线程节点的前驱状态可能不是SIGNAL，那么在当前这一轮循环中线程不会被挂起，
            //然后更新超时时间，开始新一轮的尝试,否则就阻塞，直到到达截止时间。
            if (shouldParkAfterFailedAcquire(p, node) &&
                nanosTimeout > spinForTimeoutThreshold)
                LockSupport.parkNanos(this, nanosTimeout);
            if (Thread.interrupted())
                throw new InterruptedException();
        }
    } finally {
        if (failed)
            cancelAcquire(node);
    }
}

/** 
 * 共享模式下的获取
 * Acquires in shared uninterruptible mode.
 * @param arg the acquire argument
 */
private void doAcquireShared(int arg) {
    final Node node = addWaiter(Node.SHARED);
    boolean failed = true;
    try {
        boolean interrupted = false;
        for (;;) {
            final Node p = node.predecessor();
            if (p == head) {
                //这里获取的是共享的线程数
                int r = tryAcquireShared(arg);
                if (r >= 0) {
                    //当该节点的前驱节点是头结点且成功获取同步状态
                    setHeadAndPropagate(node, r);
                    p.next = null; // help GC
                    if (interrupted)
                        selfInterrupt();
                    failed = false;
                    return;
                }
            }
            if (shouldParkAfterFailedAcquire(p, node) &&
                parkAndCheckInterrupt())
                interrupted = true;
        }
    } finally {
        if (failed)
            cancelAcquire(node);
    }
}

/**
 * Acquires in shared interruptible mode.
 * @param arg the acquire argument
 */
private void doAcquireSharedInterruptibly(int arg)
    throws InterruptedException {
    final Node node = addWaiter(Node.SHARED);
    boolean failed = true;
    try {
        for (;;) {
            final Node p = node.predecessor();
            if (p == head) {
                int r = tryAcquireShared(arg);
                if (r >= 0) {
                    setHeadAndPropagate(node, r);
                    p.next = null; // help GC
                    failed = false;
                    return;
                }
            }
            if (shouldParkAfterFailedAcquire(p, node) &&
                parkAndCheckInterrupt())
                throw new InterruptedException();
        }
    } finally {
        if (failed)
            cancelAcquire(node);
    }
}

/**
 * Acquires in shared timed mode.
 *
 * @param arg the acquire argument
 * @param nanosTimeout max wait time
 * @return {@code true} if acquired
 */
private boolean doAcquireSharedNanos(int arg, long nanosTimeout)
        throws InterruptedException {
    if (nanosTimeout <= 0L)
        return false;
    final long deadline = System.nanoTime() + nanosTimeout;
    final Node node = addWaiter(Node.SHARED);
    boolean failed = true;
    try {
        for (;;) {
            final Node p = node.predecessor();
            if (p == head) {
                int r = tryAcquireShared(arg);
                if (r >= 0) {
                    setHeadAndPropagate(node, r);
                    p.next = null; // help GC
                    failed = false;
                    return true;
                }
            }
            nanosTimeout = deadline - System.nanoTime();
            if (nanosTimeout <= 0L)
                return false;
            if (shouldParkAfterFailedAcquire(p, node) &&
                nanosTimeout > spinForTimeoutThreshold)
                LockSupport.parkNanos(this, nanosTimeout);
            if (Thread.interrupted())
                throw new InterruptedException();
        }
    } finally {
        if (failed)
            cancelAcquire(node);
    }
}

// Main exported methods

/**
 * 尝试在独占模式下获取，此方法应该先查询当前对象的状态是否允许在独占模式下获取，
 * 若果可以则获取。
 * 此方法总是被当前线程调用，此方法如果返回失败，则获取方法可能会对线程进行排队（如果线程尚未排队)
 * 直到从其它线程发出释放信号。这可用于实现方法Lock.tryLock()
 * @param arg ：获取参数。这个值总是传递给获取方法的值，或者是在进入条件wait时保存的值。
 * 否则，该值是未解释的，可以表示您喜欢的任何内容
 * @return {@code true} if successful. Upon success, this object has
 *         been acquired.
 * @throws IllegalMonitorStateException if acquiring would place this
 *         synchronizer in an illegal state. This exception must be
 *         thrown in a consistent fashion for synchronization to work
 *         correctly.
 * @throws UnsupportedOperationException if exclusive mode is not supported
 */
protected boolean tryAcquire(int arg) {
    throw new UnsupportedOperationException();
}

/**
 * Attempts to set the state to reflect a release in exclusive mode.
 * @throws UnsupportedOperationException if exclusive mode is not supported
 */
protected boolean tryRelease(int arg) {
    throw new UnsupportedOperationException();
}

/**
 * Attempts to acquire in shared mode. This method should query if
 * the state of the object permits it to be acquired in the shared
 * mode, and if so to acquire it.
 */
protected int tryAcquireShared(int arg) {
    throw new UnsupportedOperationException();
}

/**
 * Attempts to set the state to reflect a release in shared mode.
 */
protected boolean tryReleaseShared(int arg) {
    throw new UnsupportedOperationException();
}

/**
 * Returns {@code true} if synchronization is held exclusively with
 * respect to the current (calling) thread.  This method is invoked
 * upon each call to a non-waiting {@link ConditionObject} method.
 * (Waiting methods instead invoke {@link #release}.)
 */
protected boolean isHeldExclusively() {
    throw new UnsupportedOperationException();
}

/**
 * 尝试获取锁，如果尝试获取失败，则继续进入队列排队获取
 * acquireQueued 返回中断状态，如果中断则恢复中断
 */
public final void acquire(int arg) {
    if (!tryAcquire(arg) &&
        acquireQueued(addWaiter(Node.EXCLUSIVE), arg))
        selfInterrupt();
}

public final void acquireInterruptibly(int arg)
        throws InterruptedException {
    if (Thread.interrupted())
        throw new InterruptedException();
    if (!tryAcquire(arg))
        doAcquireInterruptibly(arg);
}


public final boolean tryAcquireNanos(int arg, long nanosTimeout)
        throws InterruptedException {
    if (Thread.interrupted())
        throw new InterruptedException();
    return tryAcquire(arg) ||
        doAcquireNanos(arg, nanosTimeout);
}

/**
 * Releases in exclusive mode.  Implemented by unblocking one or
 * more threads if tryRelease returns true.
 * This method can be used to implement method {@link Lock#unlock}.
 * @param arg 释放的参数。此值被传递给 tryRelease，但在其他情况下未被解释，可以表示您喜欢的任何内容。
 * @return the value returned from {@link #tryRelease}
 */
public final boolean release(int arg) {
    if (tryRelease(arg)) {
        Node h = head;
        if (h != null && h.waitStatus != 0)
            unparkSuccessor(h);
        return true;
    }
    return false;
}

/**
 * 以共享模式获取，忽略中断。首先调用至少一次{@link # tryacquiremred}，成功后返回。
 * 否则，线程将排队，可能反复阻塞和解除阻塞，调用{@link # tryacquiremred}直到成功。
 * tryAcquireShared 返回之前实际的共享线程数量
 * @param arg the acquire argument.  This value is conveyed to
 *        {@link #tryAcquireShared} but is otherwise uninterpreted
 *        and can represent anything you like.
 */
public final void acquireShared(int arg) {
    if (tryAcquireShared(arg) < 0)
        doAcquireShared(arg);
}

/**
 */
public final void acquireSharedInterruptibly(int arg)
        throws InterruptedException {
    if (Thread.interrupted())
        throw new InterruptedException();
    if (tryAcquireShared(arg) < 0)
        doAcquireSharedInterruptibly(arg);
}


public final boolean tryAcquireSharedNanos(int arg, long nanosTimeout)
        throws InterruptedException {
    if (Thread.interrupted())
        throw new InterruptedException();
    return tryAcquireShared(arg) >= 0 ||
        doAcquireSharedNanos(arg, nanosTimeout);
}

public final boolean releaseShared(int arg) {
    if (tryReleaseShared(arg)) {
        doReleaseShared();
        return true;
    }
    return false;
}

// 队列检测的相关方法

/**
 * 查询是否有线程正在等待获取。注意，由于中断和超时导致的取消可能随时发生，
 * {@code true}返回并不保证任何其他线程曾经获得。
 *
 * <p>In this implementation, this operation returns in constant time.
 *
 * @return {@code true} if there may be other threads waiting to acquire
 */
public final boolean hasQueuedThreads() {
    return head != tail;
}

/**
 * 查询是否有线程争用过此同步器;也就是说，如果获取方法曾经被阻塞。
 *
 * <p>In this implementation, this operation returns in
 * constant time.
 *
 * @return {@code true} if there has ever been contention
 */
public final boolean hasContended() {
    return head != null;
}

/**
 * 返回队列中的第一个(等待时间最长的)线程，如果当前没有线程排队，则返回 null。
 *
 * 在此实现中，此操作通常以常数时间返回，但如果其他线程同时修改队列，则可能在争用时迭代
 *
 * @return the first (longest-waiting) thread in the queue, or
 *         {@code null} if no threads are currently queued
 */
public final Thread getFirstQueuedThread() {
    // handle only fast path, else relay
    return (head == tail) ? null : fullGetFirstQueuedThread();
}

/** 
 * 获取第一个排队线程，当fastpath失败时调用getFirstQueuedThread的版本
 * 先从尝试直接获取head，否则从后往前遍历获取
 */
private Thread fullGetFirstQueuedThread() {
    /* 第一个节点通常是head.next。尝试获取它的线程字段，确保一致读取:
     * 如果线程字段为null或s.prev,则其不再是head，
     * 然后一些其他线程在我们的保持读取一致性时并发地执行setHead。
     * 在遍历之前，我们尝试了两次
     */
    Node h, s;
    Thread st;
    //ps: 这个线程一般是head->next，这里需要保证多线程读一致性：
    //head非空,head.netx非空,s.pre等于head，s.thread非空
   //这里连续执行了两次，没有封装，估计是考虑内联代码的性能更高；
  //在冲突不高，或者一般情况，两次能够命中大部分操作
   //这里的四个判断之间可能有其它线程setHead，然后条件就会不成立
    if (((h = head) != null && (s = h.next) != null &&
         s.prev == head && (st = s.thread) != null) ||
        ((h = head) != null && (s = h.next) != null &&
         s.prev == head && (st = s.thread) != null))
        return st;

    /*
     * Head的下一个字段可能还没有设置，或者在setHead之后已经取消设置。
     * 所以我们必须检查tail是否是第一个节点。如果没有，我们继续，从尾部到头部安全地找到第一个，保证终止。
     * ps：这里从后往前遍历到第一个head外的线程。
     */
    Node t = tail;
    Thread firstThread = null;
    while (t != null && t != head) {
        Thread tt = t.thread;
        if (tt != null)
            firstThread = tt;
        t = t.prev;
    }
    return firstThread;
}

/**
 *  从后往前遍历队列查找此线程是否在排队
 *
 * @param thread the thread
 * @return {@code true} if the given thread is on the queue
 * @throws NullPointerException if the thread is null
 */
public final boolean isQueued(Thread thread) {
    if (thread == null)
        throw new NullPointerException();
    for (Node p = tail; p != null; p = p.prev)
        if (p.thread == thread)
            return true;
    return false;
}

/**
 *  队列里第一个等待的结点是否是独占模式。目前仅探索式的用在读写锁中。Returns {@code true} if the apparent first queued thread, if one
 *  ps:这里未考虑setHead并发问题
 */
final boolean apparentlyFirstQueuedIsExclusive() {
    Node h, s;
    return (h = head) != null &&
        (s = h.next)  != null &&
        !s.isShared()         &&
        s.thread != null;
}

/**
 * 查询是否有任何线程等待获取的时间超过当前线程.
 * 即是否有前置排队节点
 * @return {@code true} if there is a queued thread preceding the
 *         current thread, and {@code false} if the current thread
 *         is at the head of the queue or the queue is empty
 * @since 1.7
 */
public final boolean hasQueuedPredecessors() {
    // The correctness of this depends on head being initialized
    // before tail and on head.next being accurate if the current
    // thread is first in queue.
    Node t = tail; // Read fields in reverse initialization order
    Node h = head;
    Node s;
    return h != t &&
        ((s = h.next) == null || s.thread != Thread.currentThread());
}


// Instrumentation and monitoring methods

/**
 * 返回等待获取的线程数的估计值。这个值只是一个估计值，
 * 因为当这个方法遍历内部数据结构时，线程的数量可能会动态变化。
 * 该方法用于监控系统状态，不用于同步控制.
 * 
 * @return the estimated number of threads waiting to acquire
 */
public final int getQueueLength() {
    int n = 0;
    for (Node p = tail; p != null; p = p.prev) {
        if (p.thread != null)
            ++n;
    }
    return n;
}

/** 
 * 返回一个集合，其包含正在等待获取的线程，此为大致结果，并不精确。
 * 此方法的设计目的是方便构造提供更广泛监视设施的子类
 *
 * @return the collection of threads
 */
public final Collection<Thread> getQueuedThreads() {
    ArrayList<Thread> list = new ArrayList<Thread>();
    for (Node p = tail; p != null; p = p.prev) {
        Thread t = p.thread;
        if (t != null)
            list.add(t);
    }
    return list;
}

/**
 * 获取独占模式下的等待线程集合.
 *
 * @return the collection of threads
 */
public final Collection<Thread> getExclusiveQueuedThreads() {
    ArrayList<Thread> list = new ArrayList<Thread>();
    for (Node p = tail; p != null; p = p.prev) {
        if (!p.isShared()) {
            Thread t = p.thread;
            if (t != null)
                list.add(t);
        }
    }
    return list;
}

/**
 * 获取共享模式下的等待线程集合
 * 
 * @return the collection of threads
 */
public final Collection<Thread> getSharedQueuedThreads() {
    ArrayList<Thread> list = new ArrayList<Thread>();
    for (Node p = tail; p != null; p = p.prev) {
        if (p.isShared()) {
            Thread t = p.thread;
            if (t != null)
                list.add(t);
        }
    }
    return list;
}

/**
 * Returns a string identifying this synchronizer, as well as its state.
 * The state, in brackets, includes the String {@code "State ="}
 * followed by the current value of {@link #getState}, and either
 * {@code "nonempty"} or {@code "empty"} depending on whether the
 * queue is empty.
 *
 * @return a string identifying this synchronizer, as well as its state
 */
public String toString() {
    int s = getState();
    String q  = hasQueuedThreads() ? "non" : "";
    return super.toString() +
        "[State = " + s + ", " + q + "empty queue]";
}


// Internal support methods for Conditions

/** 
 * ps：判断此节点（线程）是否在同步队列中
 * 如果一个节点(始终是最初放置在条件队列中的节点)现在正等待
 * 在同步队列上重新获取，将返回true。
 * @param node the node
 * @return true if is reacquiring
 */
final boolean isOnSyncQueue(Node node) {
    if (node.waitStatus == Node.CONDITION || node.prev == null)
        return false;
    if (node.next != null) // If has successor, it must be on queue
        return true;
    /* 
     * ps: 除开上面两种情况，节点一般在队尾附近
     * node.prev可以是非空的，但还不能放在队列上，因为将其放在队列上的CAS可能会失败。
     * 所以我们必须从尾部开始，以确保它确实做到了。在对这个方法的调用中，它总是在尾部附近，
     * 除非CAS失败(这是不太可能的)，否则它就会在那里，所以我们很少进行过多的遍历。
     */
    return findNodeFromTail(node);
}

/**
 * 从后往前遍历，存在则返回true.
 * @return true if present
 */
private boolean findNodeFromTail(Node node) {
    Node t = tail;
    for (;;) {
        if (t == node)
            return true;
        if (t == null)
            return false;
        t = t.prev;
    }
}

/**
 * 将一个node从条件队列移动到同步队列，成功则返回true
 * @param node the node
 * @return true if successfully transferred (else the node was
 * cancelled before signal)
 */
final boolean transferForSignal(Node node) {
    /*
     * 如果无法更改等待状态，则节点已取消。
     */
    if (!compareAndSetWaitStatus(node, Node.CONDITION, 0))
        return false;
    
    /*
     * 将节点分割到队列，并尝试设置pre的等待状态，以指示线程(可能)正在等待。
     * 如果取消或尝试设置等待状态失败，则唤醒并重新同步(在这种情况下，等待状态可能是暂时错误的，并且不会造成任何危害)。
     */
    //进入队列返回前置节点，如果前驱节点被取消或者更改waitStatus状态为SIGNAL失败，
    //说明前驱失效，则唤醒在锁同步等待队列当前节点
    Node p = enq(node);
    int ws = p.waitStatus;
    if (ws > 0 || !compareAndSetWaitStatus(p, ws, Node.SIGNAL))
        LockSupport.unpark(node.thread);
    return true;
}

/**
 * 转移节点去同步队列，若有必要，在取消等待后。如果线程在发出信号之前被取消，则返回true。
 * @param node the node
 * @return true if cancelled before the node was signalled
 */
final boolean transferAfterCancelledWait(Node node) {
    //设置成功0，则进入队列，为初始态
    if (compareAndSetWaitStatus(node, Node.CONDITION, 0)) {
        enq(node);
        return true;
    }
    /*
     * 如果上面设置失败，说明节点已经被signal唤醒，由于signal操作会将节点加入同步队列，我们只需自旋等待即可.
     */
    while (!isOnSyncQueue(node))
        Thread.yield();
    return false;
}

/**
 * 使用当前状态值调用release;返回保存的状态。取消节点并在失败时抛出异常.
 * @param node the condition node for this wait
 * @return 以前的同步状态
 */
final int fullyRelease(Node node) {
    boolean failed = true;
    try {
        int savedState = getState();
        if (release(savedState)) {
            failed = false;
            return savedState;
        } else {
            throw new IllegalMonitorStateException();
        }
    } finally {
        if (failed)
            node.waitStatus = Node.CANCELLED;
    }
}

// 条件测量方法

/**
 * 查询给定条件对象是否使用此同步器作为其锁.
 *
 * @param condition the condition
 * @return {@code true} if owned
 * @throws NullPointerException if the condition is null
 */
public final boolean owns(ConditionObject condition) {
    return condition.isOwnedBy(this);
}

/**
 * 查询是否有线程正在等待与此同步器关联的给定条件。
 * 注意，由于超时和中断可能随时发生，true返回并不保证将来的信号将唤醒任何线程。
 * 该方法主要用于系统状态监测.
 * @param condition the condition
 * @return {@code true} if there are any waiting threads
 * @throws IllegalMonitorStateException if exclusive synchronization
 *         is not held
 * @throws IllegalArgumentException 如果给定的条件与此同步器不关联
 * @throws NullPointerException if the condition is null
 */
public final boolean hasWaiters(ConditionObject condition) {
    if (!owns(condition))
        throw new IllegalArgumentException("Not owner");
    return condition.hasWaiters();
}

/**
 * 返回大致等待的数量.
 * @param condition the condition
 * @return the estimated number of waiting threads
 * @throws IllegalMonitorStateException if exclusive synchronization
 *         is not held
 * @throws IllegalArgumentException if the given condition is
 *         not associated with this synchronizer
 * @throws NullPointerException if the condition is null
 */
public final int getWaitQueueLength(ConditionObject condition) {
    if (!owns(condition))
        throw new IllegalArgumentException("Not owner");
    return condition.getWaitQueueLength();
}

/**
 * 返回一个大致地等待的线程的集合。
 *
 * @param condition the condition
 * @return the collection of threads
 * @throws IllegalMonitorStateException if exclusive synchronization
 *         is not held
 * @throws IllegalArgumentException if the given condition is
 *         not associated with this synchronizer
 * @throws NullPointerException if the condition is null
 */
public final Collection<Thread> getWaitingThreads(ConditionObject condition) {
    if (!owns(condition))
        throw new IllegalArgumentException("Not owner");
    return condition.getWaitingThreads();
}
//放到后面单独理出
public class ConditionObject implements Condition, java.io.Serializable { ... }

    /**
     * 设置去支持compareAndSet.我们需要在这里采用原生实现。
     * 为了将来的扩展场景。we cannot explicitly subclass AtomicInteger，
     *  另一方面这将会是高效和有效的。所以，为了更小的弊端，我们原生实现使用
     * hotspot的内置API.并且在这一点上，对于其余的CASable 属性也等同处理，否则
     * 可以通过原子属性更新器实现了。
     * 
     */
    private static final Unsafe unsafe = Unsafe.getUnsafe();
    private static final long stateOffset;
    private static final long headOffset;
    private static final long tailOffset;
    private static final long waitStatusOffset;
    private static final long nextOffset;
   //这里获取了每个字段相对于java对象地址的偏移量
    static {
        try {
            stateOffset = unsafe.objectFieldOffset
                (AbstractQueuedSynchronizer.class.getDeclaredField("state"));
            headOffset = unsafe.objectFieldOffset
                (AbstractQueuedSynchronizer.class.getDeclaredField("head"));
            tailOffset = unsafe.objectFieldOffset
                (AbstractQueuedSynchronizer.class.getDeclaredField("tail"));
            waitStatusOffset = unsafe.objectFieldOffset
                (Node.class.getDeclaredField("waitStatus"));
            nextOffset = unsafe.objectFieldOffset
                (Node.class.getDeclaredField("next"));
        } catch (Exception ex) { throw new Error(ex); }
    }

    /**
     * CAS head field. Used only by enq.更新队首Node
     */
    private final boolean compareAndSetHead(Node update) {
        return unsafe.compareAndSwapObject(this, headOffset, null, update);
    }

    /**
     * CAS tail field. Used only by enq.更新队尾Node
     */
    private final boolean compareAndSetTail(Node expect, Node update) {
        return unsafe.compareAndSwapObject(this, tailOffset, expect, update);
    }

    /**
     * CAS waitStatus field of a node.CAS更新节点状态
     */
    private static final boolean compareAndSetWaitStatus(Node node,
                                                         int expect,
                                                         int update) {
        return unsafe.compareAndSwapInt(node, waitStatusOffset,
                                        expect, update);
    }

    /**
     * CAS next field of a node.设置下一个Node
     */
    private static final boolean compareAndSetNext(Node node,
                                                   Node expect,
                                                   Node update) {
        return unsafe.compareAndSwapObject(node, nextOffset, expect, update);
    }
}

```

### ASQ中的Node类
可以简单理解为此Node类，就是为了ASQ中构建一个排队获取资源(锁）的队列。
1. waitStatus： 0 = 初始，小于0为有效状态（可被唤醒)，大于0是取消态（需要移出对应线程)

```java
    /**
     * Wait queue node class.
     * 等待队列Node类
     * 这个等待队列是"CLH" (Craig, Landin, and Hagersten) 锁队列。
     * CLH锁都普遍被用于自旋锁。我们将之用于阻塞中的同步器，但却使用了相同的策略
     * 在它的前置节点上持有一些线程信息。在每一个Node中的"status"字段记录了一个线程是否应该被阻塞。
     * 当它的前置节点被释放时，它会收到信号。否则，队列的每个节点都充当一个特定的通知样式监视器，
     * 用于保存单个等待线程。状态字段不控制线程是否被授予锁等，如果一个线程处在队首，它会尝试获取锁。
     * 但是领先并不保证成功，它只是给予竞争的权利。所以当前释放的竞争线程可能还需要重新等待。
     * 
     * 要加入一个CLH锁，你原子的将之插入队尾。要退出队列，你仅需要设置head属性。
     * +------+ prev +-----+ +-----+
     * head | | <---- | | <---- | | tail
     * +------+ +-----+ +-----+
     *
     * 插入CLH队列只需要在“tail”上执行一个原子操作，因此存在一个简单的原子点，
     * 用于划分从未排队到排队。类似地，退出队列只涉及更新“head”。
     * 然而，节点需要做更多的工作来确定谁是他们的继任者，其中一部分部分原因是
     * 要处理由于超时和中断而可能发生的取消。
     *
     * “prev”链接(在原来的CLH锁中没有使用)主要用于处理取消。
     * 如果一个节点被取消，它的继承节点(通常)会重新链接到一个未取消的继承节点。
     * 有关自旋锁的类似机制的解释，请参阅Scott和Scherer的论文at
     * http://www.cs.rochester.edu/u/scott/synchronization/
     *
     * 我们通用使用"next"链接来实现阻塞机制。每个node的线程id保存在他们的自身的node中，
     * 因此，前一个节点通过遍历下一个链接来确定它是哪个线程，从而向下一个节点发出唤醒信号。.
     * 继任者的确定必须避免使用新排队的节点来设置其前任的“下一个”字段的竞争。
    *  当节点的后继出现null时，通过从原子更新的“tail”向后检查，可以在必要时解决这个问题。
    * (或者，换句话说，next-links是一种优化，因此我们通常不需要向后扫描。)   
     *
     * 取消为基本算法引入了保守性。因为我们必须轮询其他节点的取消，
     * 所以我们可能会忽略被取消的节点是在前面还是在后面。
     * 处理这一问题的方法是，总是在取消时unparking 后继者，
     * 使他们能够稳定地依靠新的前置节点，除非我们能确认一个未取消的前置节点来承担这个责任。
     * 
     *  CLH队列需要一个虚拟头节点来启动。但是，我们不会在构建过程中创建它们，
     * 因为如果从来没有争用，就会浪费精力。相反，在节点构造后，head和tail指针将会在并在第一次争用时设置。
     *
     * 等待条件的线程使用相同的节点，但使用额外的链接。
     * 条件只需要在简单(非并发)链接队列中链接节点，因为它们只在独占时才被访问。
     * 在等待时，将节点插入到条件队列中。信号一发出，节点就被转移到主队列。
     * 状态字段的一个特殊值用于标记节点所在的队列。
     * 感谢Dave Dice、Mark Moir、Victor Luchangco、Bill Scherer和Michael Scott，以及JSR-166专家组的成员，为本课程的设计提供了有用的想法、讨论和批评
     */
    static final class Node {
        /** 节点在共享模式下等待的标记 */
        static final Node SHARED = new Node();
        /** 节点在排它模式下等待的标记 */
        static final Node EXCLUSIVE = null;

        /** waitStatus value to 表明线程已经 cancelled */
        static final int CANCELLED = 1;
        /** waitStatus value to 表明继任线程需要 unparking */
        static final int SIGNAL = -1;
        /** waitStatus value to 表明现在在 condition 下等待 */
        static final int CONDITION = -2;
        /**
         * waitStatus value to 表明下一个共享同步器应该被无条件传播
         */
        static final int PROPAGATE = -3;
        
        /**
         * 状态字段，只接收以下值：
         *  SIGNAL： 即将或者已经是此节点的继承者，且被blocked。所以当前节点必须unpark
         * 它的继承者 ，当自身被释放或者cancels。为了避免竞争，获取方法必须首先表明
         * 他们需要一个信号 ，然后重新尝试原子获取。如果失败了，则阻塞。
         * CANCELLED:  当前节点cancelled，因为超时orinterrupt。
         * 节点无法离开此状态。特别的，具有已取消节点的线程将不再阻塞。
         * CONDITION:  此节点当前正在条件队列中，它不会被作为一个同步队列
         * 的节点被使用直到被转移，此时状态值将置为0。（这里使用此值和此字段的其余用法
         * 无关，只是为了简化机器编码） 。
         * PROPAGATE：一个释放分享应该被传播到其它的节点，这是一个集合（仅为头节点）
         * 在做释放分享操作时能保证传播的继续，即使此时还有别的操作已经介入。
         * 0 ： 非以上状态
         *
         * 数值的排列是为了简化使用。非负值表示节点不需要发出信号。
         * 因此，大多数代码不需要检查特定的值，只需要检查符号。
         *
         * 对于普通同步节点，字段初始化为0，对于条件节点，字段初始化为条件。
         * 使用CAS(或者在可能的情况下，使用无条件的volatile写)修改它。
         */
        volatile int waitStatus;
        
        /**
         * 链接到当前节点/线程所依赖的用于检查等待状态的前辈节点。
         * 在排队时分配，只有在退出排队时才为空(为了GC)。
         * 此外，在取消前一个节点时，我们会在找到一个未取消的节点时短路，
         * 因为头节点从来没有被取消过:一个节点只有在成功获取后才成为头节点。
         * 被取消的线程永远不会成功获取，并且线程只取消自己，而不取消任何其他节点。
         */
        volatile Node prev;

        /**
         * 链接到当前节点/线程的后续节点，在当前节点释放时被unparks时。
         * 在排队过程中分配，在绕过已取消的前置节点时进行调整，在退出队列时为空(为了GC)。
         * 进入队列操作之后才分配前任的下一个节点，所以看到一个空的next字段并不一定意味着节点在队列的末尾。
         * 然而，如果下一个字段显示为空，我们可以从尾部扫描prev以进行双重检查。
         * 取消节点的下一个字段被设置为指向节点本身，而不是null，以简化isOnSyncQueue的工作。
         */
        volatile Node next;

        /**
         * 进入此节点队列的线程。在构造时初始化，使用后为空。
         */
        volatile Thread thread;
        
        /**
        *  链接到正在condition的等待状态的下一个节点，或共享的特殊值。
        * 因为条件队列只有在独占模式下才能访问，所以我们只需要一个简单的链接队列
        * 来在节点等待条件时保存节点。然后将它们转移到队列中重新获取。
        * 由于条件只能是独占的，所以我们使用特殊值来表示共享模式来保存字段。
         */
        Node nextWaiter;

        /**
         * Returns true if node is waiting in shared mode.
         */
        final boolean isShared() {
            return nextWaiter == SHARED;
        }

        /**
         * 返回前置节点，如果为空则抛出NullPointerException。
         * 当前置不能为空时使用。可以省略null检查，但它目前是用来帮助VM的。
         * @return the predecessor of this node
         */
        final Node predecessor() throws NullPointerException {
            Node p = prev;
            if (p == null)
                throw new NullPointerException();
            else
                return p;
        }
        //初始化head或者共享标记
        Node() { // Used to establish initial head or SHARED marker
        }

        Node(Thread thread, Node mode) { // Used by addWaiter
            this.nextWaiter = mode;
            this.thread = thread;
        }

        Node(Thread thread, int waitStatus) { // Used by Condition
            this.waitStatus = waitStatus;
            this.thread = thread;
        }
    }
```

### ASQ 中的ConditionObject
```java
/**
 * 作为锁实现基础的AbstractQueuedSynchronizer的条件实现
 * 该类的方法文档从锁和条件用户的角度描述了机制，而不是行为规范。
 * 该类的导出版本通常需要伴随描述依赖于关联的条件语义的相关文档。

 * 此类可序列化，但是所有字段均为transient，所以反序列化不会有waiters。
 */
public class ConditionObject implements Condition, java.io.Serializable {
    private static final long serialVersionUID = 1173984872572414699L;
    /** First node of condition queue. */
    private transient Node firstWaiter;
    /** Last node of condition queue. */
    private transient Node lastWaiter;

    /**
     * Creates a new {@code ConditionObject} instance.
     */
    public ConditionObject() { }

    // Internal methods

    /**
     * Adds a new waiter to wait queue.
     * 这里未使用cas，因为通常使用condition的前提必须是在独占模式的lock下。
     * @return its new wait node
     */
    private Node addConditionWaiter() {
        Node t = lastWaiter;
        // If lastWaiter is cancelled, clean out.
        if (t != null && t.waitStatus != Node.CONDITION) {
            unlinkCancelledWaiters();
            t = lastWaiter;
        }
        Node node = new Node(Thread.currentThread(), Node.CONDITION);
        if (t == null)
            firstWaiter = node;
        else
            t.nextWaiter = node;
        lastWaiter = node;
        return node;
    }

    /**
     * 删除和转移节点，直到到达不可取消的一个或null。
    * 从signal中分离出来，部分原因是为了鼓励编译器在没有等待器的情况下内联。
     * 把节点first转移到condition所属的AQS等待队列中，若失败, 从前往后遍历获取等待节点，直到成功。
     * ps: 这里相当于Object中的唤醒一个线程,独占模式下应该是FIFO原则，这里标记了唤醒的信号，在同步队列中进行真正的唤醒
     * @param first (non-null) the first node on condition queue
     */
    private void doSignal(Node first) {
        do {
            //若为空，则到队尾，则没有等待队列
            if ( (firstWaiter = first.nextWaiter) == null)
                lastWaiter = null;
           //若从等待队列中转义到同步队列中，则没有了nextWaiter
            first.nextWaiter = null;
        } while (!transferForSignal(first) &&
                 (first = firstWaiter) != null);
    }

    /**
     * 移出或者转移所有节点，ps: 相当于Object中唤醒所有节点的信号发送
     * @param first (non-null) the first node on condition queue
     */
    private void doSignalAll(Node first) {
        lastWaiter = firstWaiter = null;
        do {
            Node next = first.nextWaiter;
            first.nextWaiter = null;
            transferForSignal(first);
            first = next;
        } while (first != null);
    }

    /**
     * 仅在持锁时调用，从条件队列中分离已取消的等待节点的链接。
     * 当在条件等待期间发生取消时或者添加一个新的节点的时候发现尾节点已被取消时调用此函数，
     * 在没有信号的情况下，需要使用这种方法来避免垃圾保留。
     * 因此，尽管它可能需要一个完整的遍历，但只有在没有信号的情况下超时或取消才会起作用。
     * 它遍历所有节点，而不是停在一个特定的目标上，以断开到垃圾节点的所有指针的链接，
     * 而不需要在取消风暴期间进行多次重新遍历
     */
    private void unlinkCancelledWaiters() {
        Node t = firstWaiter;
        //trail，若此阶段未取消，则是前置的前置节点，否则就是前置节点。
        Node trail = null;
       // 从前往后遍历，处理所有t.waitStatus != Node.CONDITION的状态
       // 同时处理lastWaiter的值。
        while (t != null) {
            Node next = t.nextWaiter;
            if (t.waitStatus != Node.CONDITION) {
                t.nextWaiter = null;
                if (trail == null)
                    firstWaiter = next;
                else
                    trail.nextWaiter = next;
                if (next == null)
                    lastWaiter = trail;
            }
            else
                trail = t;
            t = next;
        }
    }

    // public methods

    /**
     * 将等待时间最长的线程(如果存在的话)从该条件的等待队列移动到拥有锁的等待队列。
     *
     * @throws IllegalMonitorStateException if {@link #isHeldExclusively}
     *         returns {@code false}
     */
    public final void signal() {
        if (!isHeldExclusively())
            throw new IllegalMonitorStateException();
        Node first = firstWaiter;
        if (first != null)
            doSignal(first);
    }

    /**
     * Moves all threads from the wait queue for this condition to
     * the wait queue for the owning lock.
     *
     * @throws IllegalMonitorStateException if {@link #isHeldExclusively}
     *         returns {@code false}
     */
    public final void signalAll() {
        if (!isHeldExclusively())
            throw new IllegalMonitorStateException();
        Node first = firstWaiter;
        if (first != null)
            doSignalAll(first);
    }

    /**
     * 一直阻塞，记录中断状态(不抛出线程中断异常)
     */
    public final void awaitUninterruptibly() {
        Node node = addConditionWaiter();
        int savedState = fullyRelease(node);
        boolean interrupted = false;
        while (!isOnSyncQueue(node)) {
            LockSupport.park(this);
            if (Thread.interrupted())
                interrupted = true;
        }
        if (acquireQueued(node, savedState) || interrupted)
            selfInterrupt();
    }

    /*
     * 对于可中断等待，我们需要跟踪是否抛出InterruptedException(如果在条件阻塞时中断)，
     * 而不是重新中断当前线程(如果在阻塞等待重新获取时中断)。
     */
    
    /** 此模式意味着在退出等待时重新中断。 */
    private static final int REINTERRUPT =  1;
    /** 模式意味着在退出等待时抛出InterruptedException */
    private static final int THROW_IE    = -1;
    
    /**
     *检查是否有中断，如果在信号之前中断，返回THROW_IE;如果在信号之后中断，返回REINTERRUPT;
    * 如果没有中断，返回0。
     */
    private int checkInterruptWhileWaiting(Node node) {
        return Thread.interrupted() ?
            (transferAfterCancelledWait(node) ? THROW_IE : REINTERRUPT) :
            0;
    }

    /**
     * Throws InterruptedException, reinterrupts current thread, or
     * does nothing, depending on mode.
     */
    private void reportInterruptAfterWait(int interruptMode)
        throws InterruptedException {
        if (interruptMode == THROW_IE)
            throw new InterruptedException();
        else if (interruptMode == REINTERRUPT)
            selfInterrupt();
    }

    /**
     * Implements interruptible condition wait.
     *  If current thread is interrupted, throw InterruptedException.
     *  Save lock state returned by getState .
     * Invoke release with saved state as argument,
     *      throwing IllegalMonitorStateException if it fails.
     *  Block until signalled or interrupted.
     *  Reacquire by invoking specialized version of
     *      acquire with saved state as argument.
     * If interrupted while blocked in step 4, throw InterruptedException.
     */
    public final void await() throws InterruptedException {
        if (Thread.interrupted())
            throw new InterruptedException();
        Node node = addConditionWaiter();
        int savedState = fullyRelease(node);
        int interruptMode = 0;
        //如果当前节点没有在同步队列中，则阻塞，直到进入同步队列
        while (!isOnSyncQueue(node)) {
            LockSupport.park(this);
            if ((interruptMode = checkInterruptWhileWaiting(node)) != 0)
                break;
        }
        //通过将保存的状态作为参数来重获取
        // 如果成为同步队列的链表头部(ps：进入同步队列后自旋，直到成功)，则开始判断中断状态
        if (acquireQueued(node, savedState) && interruptMode != THROW_IE)
            interruptMode = REINTERRUPT;
        if (node.nextWaiter != null) // clean up if cancelled
            unlinkCancelledWaiters();
        if (interruptMode != 0)
            reportInterruptAfterWait(interruptMode);
    }

    /**
     * 带有超时时间的await
     */
    public final long awaitNanos(long nanosTimeout)
            throws InterruptedException {
        if (Thread.interrupted())
            throw new InterruptedException();
        Node node = addConditionWaiter();
        int savedState = fullyRelease(node);
        final long deadline = System.nanoTime() + nanosTimeout;
        int interruptMode = 0;
        while (!isOnSyncQueue(node)) {
            if (nanosTimeout <= 0L) {
                transferAfterCancelledWait(node);
                break;
            }
            if (nanosTimeout >= spinForTimeoutThreshold)
                LockSupport.parkNanos(this, nanosTimeout);
            if ((interruptMode = checkInterruptWhileWaiting(node)) != 0)
                break;
            nanosTimeout = deadline - System.nanoTime();
        }
        if (acquireQueued(node, savedState) && interruptMode != THROW_IE)
            interruptMode = REINTERRUPT;
        if (node.nextWaiter != null)
            unlinkCancelledWaiters();
        if (interruptMode != 0)
            reportInterruptAfterWait(interruptMode);
        return deadline - System.nanoTime();
    }

    /**
     * Implements absolute timed condition wait.
     */
    public final boolean awaitUntil(Date deadline)
            throws InterruptedException {
        long abstime = deadline.getTime();
        if (Thread.interrupted())
            throw new InterruptedException();
        Node node = addConditionWaiter();
        int savedState = fullyRelease(node);
        boolean timedout = false;
        int interruptMode = 0;
        while (!isOnSyncQueue(node)) {
            if (System.currentTimeMillis() > abstime) {
                timedout = transferAfterCancelledWait(node);
                break;
            }
            LockSupport.parkUntil(this, abstime);
            if ((interruptMode = checkInterruptWhileWaiting(node)) != 0)
                break;
        }
        if (acquireQueued(node, savedState) && interruptMode != THROW_IE)
            interruptMode = REINTERRUPT;
        if (node.nextWaiter != null)
            unlinkCancelledWaiters();
        if (interruptMode != 0)
            reportInterruptAfterWait(interruptMode);
        return !timedout;
    }

    /**
     * Implements timed condition wait.
     */
    public final boolean await(long time, TimeUnit unit)
            throws InterruptedException {
        long nanosTimeout = unit.toNanos(time);
        if (Thread.interrupted())
            throw new InterruptedException();
        Node node = addConditionWaiter();
        int savedState = fullyRelease(node);
        final long deadline = System.nanoTime() + nanosTimeout;
        boolean timedout = false;
        int interruptMode = 0;
        while (!isOnSyncQueue(node)) {
            if (nanosTimeout <= 0L) {
                timedout = transferAfterCancelledWait(node);
                break;
            }
            if (nanosTimeout >= spinForTimeoutThreshold)
                LockSupport.parkNanos(this, nanosTimeout);
            if ((interruptMode = checkInterruptWhileWaiting(node)) != 0)
                break;
            nanosTimeout = deadline - System.nanoTime();
        }
        if (acquireQueued(node, savedState) && interruptMode != THROW_IE)
            interruptMode = REINTERRUPT;
        if (node.nextWaiter != null)
            unlinkCancelledWaiters();
        if (interruptMode != 0)
            reportInterruptAfterWait(interruptMode);
        return !timedout;
    }

    //  support for instrumentation

    /**
     * 如果该条件是由给定的同步对象创建的，则返回true.
     *
     * @return {@code true} if owned
     */
    final boolean isOwnedBy(AbstractQueuedSynchronizer sync) {
        return sync == AbstractQueuedSynchronizer.this;
    }

    /**
     * 查询是否有线程在此condition下等待。
     * Implements {@link AbstractQueuedSynchronizer#hasWaiters(ConditionObject)}.
     *
     * @return {@code true} if there are any waiting threads
     * @throws IllegalMonitorStateException if {@link #isHeldExclusively}
     *         returns {@code false}
     */
    protected final boolean hasWaiters() {
        if (!isHeldExclusively())
            throw new IllegalMonitorStateException();
        for (Node w = firstWaiter; w != null; w = w.nextWaiter) {
            if (w.waitStatus == Node.CONDITION)
                return true;
        }
        return false;
    }

    /**
     * 返回此condition下的等待线程的大致数量.
     * Implements {@link AbstractQueuedSynchronizer#getWaitQueueLength(ConditionObject)}.
     *
     * @return the estimated number of waiting threads
     * @throws IllegalMonitorStateException if {@link #isHeldExclusively}
     *         returns {@code false}
     */
    protected final int getWaitQueueLength() {
        if (!isHeldExclusively())
            throw new IllegalMonitorStateException();
        int n = 0;
        for (Node w = firstWaiter; w != null; w = w.nextWaiter) {
            if (w.waitStatus == Node.CONDITION)
                ++n;
        }
        return n;
    }
    
    /**
     * 返回包含可能在此条件下等待的线程的集合.
     * Implements {@link AbstractQueuedSynchronizer#getWaitingThreads(ConditionObject)}.
     *
     * @return the collection of threads
     * @throws IllegalMonitorStateException if {@link #isHeldExclusively}
     *         returns {@code false}
     */
    protected final Collection<Thread> getWaitingThreads() {
        if (!isHeldExclusively())
            throw new IllegalMonitorStateException();
        ArrayList<Thread> list = new ArrayList<Thread>();
        for (Node w = firstWaiter; w != null; w = w.nextWaiter) {
            if (w.waitStatus == Node.CONDITION) {
                Thread t = w.thread;
                if (t != null)
                    list.add(t);
            }
        }
        return list;
    }
}
```

# 更多资料
CAS与ASQ： https://www.cnblogs.com/dream-to-pku/p/9186126.html
ASQ内部CLH队列： https://www.cnblogs.com/yanlong300/p/10953185.html
自旋锁、排队自旋锁、MCS锁、CLH锁： https://blog.csdn.net/fei33423/article/details/30316377
深入理解ASQ： http://ifeve.com/introduce-abstractqueuedsynchronizer/
