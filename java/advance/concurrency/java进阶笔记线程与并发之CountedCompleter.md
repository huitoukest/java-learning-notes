---
title: "java进阶笔记线程与并发之CountedCompleter"
date: "2019-10-21 22:11:48"
categories: ["j2se", "java进阶学习笔记"]
tags: ["java", "进阶笔记", "线程与并发", "CountedCompleter"]
---

# 说明
CountedCompleter是ForkJoinTask的一个子类。

其可以简单理解为处理业务和数量有关的一些FJT，一般分为如下几类：

- 和数量无关，一般不使用CountedCompleter
- 一个： findAny、searchFirst这种操作，只要在集合、流中找到一个就表示整个任务完成的
- 指定数量的： 比如有的业务需要触发多次完成的。
- 可能需要有序完成的，有序完成可以通过CountedCompleter的完成器来委婉的实现此功能。

定义：

- FJT = ForkJoinTask

- FJP = ForkJoinPool

说明： 需要看如何使用的，直接查看下面的官方示例。

# 源码

```java
/**
* 这是一个FJT，会在任务完成时检查是否有等待的任务，若没有则触发一个完成动作。
* 总的来说，与其他形式的forkjointask相比，CountedCompleters在存在子任务停滞
* 和阻塞的情况下更健壮，但对编程的直觉较差。CountedCompleter的使用类似于其他基
* 于完成的组件(例如 java.nio.channels.CompletionHandler)，除了需要多个挂
* 起的完成来触发完成操作 onCompletion(CountedCompleter)，而不是一个。
* 除非另外初始化，否则 getPendingCount pending count从0开始，但是可以使用 link
* setPendingCount、addToPendingCount和compareAndSetPendingCount(原子地)更
* 改。在调用 tryComplete时，如果挂起的动作计数为非零，则递减;否则，将执行完成操作，
* 如果这个完成器本身有一个完成器，则继续使用它的完成器。与相关的同步组件
* (如 java.util.concurrent.Phaser 和 java.util.concurrent.Semaphore ）相同。
* 这些方法只影响内部计数;他们没有建立任何进一步的内部簿记。特别是，未完成任务的标识没有
* 得到维护。如下所示，您可以创建子类来记录一些或所有挂起的任务或它们的结果。如下所示，
* 还提供了支持自定义完成遍历的实用程序方法。但是，因为CountedCompleters只提供了基
* 本的同步机制，所以创建进一步的抽象子类来维护链接、字段和其他适合于一组相关用法的支
* 持方法可能是有用的。
*
* 具体的CountedCompleter类必须定义方法{@link #compute}，在大多数情况下(如下所
* 示)，在返回之前应该调用{@code tryComplete()}一次。该类还可以选择性地覆盖方法
* {@link #onCompletion(CountedCompleter)}来在正常完成时执行一个动作，以及方
* 法{@link #onExceptionalCompletion(Throwable, CountedCompleter)}来在任
* 何异常时执行一个动作。
*
* CountedCompleters通常不产生结果，在这种情况下，它们通常被声明为
* {@code CountedCompleter}，并且总是返回{@code null}作为结果值。在其他情况下，
* 您应该覆盖方法{@link #getRawResult}来提供来自{@code join()、invoke()}和相
* 关方法的结果。通常，该方法应该返回CountedCompleter对象的一个字段(或一个或多个字
* 段的函数)的值，该对象在完成时保存结果。默认情况下，方法{@link #setRawResult}在
* CountedCompleters中不起作用。重写此方法以维护包含结果数据的其他对象或字段是可能
* 的，但很少适用。
*
* 一个CountedCompleter本身没有一个completer(即，其中{@link #getCompleter}返
* 回{@code null})可以作为一个常规的ForkJoinTask与这个增加的功能。
* 但是，任何有另一个completer的completer只是作为其他计算的内部助手，所以它自己的任
 * 务状态(如{@link    * ForkJoinTask#isDone}等方法中报告的)是任意的;这种状态只有
* 在显式调用{@link #complete}、{@link ForkJoinTask#cancel}、
* {@link ForkJoinTask# complete(Throwable)}或方法{@code compute}异常完成时
* 才会改变。在任何异常完成之后，如果存在一个任务的完成器，并且它还没有完成，则可以将异
* 常传递给任务的完成器(以及它的完成器，等等)。类似地，取消内部的CountedCompleter只
* 会对该完井器产生局部影响，所以通常不会有用。
*
* <p> 用例 </b>
* bookkeeping=簿记；
* 并行递归分解。CountedCompleters可能被安排在与{@link RecursiveAction}类似的树
* 中，尽管设置它们所涉及的结构通常是不同的。这里，每个任务的完成者是计算树中的父任务。
* 即使它们需要更多的簿记，当将可能耗时的操作(不能进一步细分)应用到数组或集合的每个元素
* 时，CountedCompleters可能是更好的选择;特别是当某些元素完成操作所需的时间与其他元
* 素明显不同时，这可能是由于内部变化(例如I/O)，也可能是由于诸如垃圾收集之类的辅助效果。
* 因为CountedCompleters提供了它们自己的延续，其他线程不需要阻塞来执行它们。
*
* 例如，下面是一个类的初始版本，它使用两个递归分解来将工作划分为单个部分(叶子任务)。即使
* 将工作划分为单独的调用，基于树的技术通常也比直接fork叶子任务更好，因为它们减少了线程间
* 的通信并改善了负载平衡。在递归情况下，每对要完成的叶子任务的第二个触发其父任务的完成(
* 因为没有执行结果组合，所以方法{@code onCompletion}的默认无操作实现没有被覆盖)。
* 静态实用程序方法设置基本任务并调用它(这里使用{@link ForkJoinPool#commonPool()
* }隐式地调用它)。
*
*
* 触发器。有些CountedCompleters本身并不是fork的，而是作为其他设计中的管道的一部分;
* 包括那些完成一个或多个异步任务触发另一个异步任务的部分。例如:
* For example:
*
* class HeaderBuilder extends CountedCompleter<...> { ... }
* class BodyBuilder extends CountedCompleter<...> { ... }
* class PacketSender extends CountedCompleter<...> {
 *   PacketSender(...) { super(null, 1); ... } // 在第二次完成时触发onCompletion
 *   public void compute() { } // never called
 *   public void onCompletion(CountedCompleter<?> caller) { sendPacket(); }
* }
* // sample use:
* PacketSender p = new PacketSender();
* new HeaderBuilder(p, ...).fork();
* new BodyBuilder(p, ...).fork();
* }
*
* @since 1.8
* @author Doug Lea
*/
public abstract class CountedCompleter<T> extends ForkJoinTask<T> {
    private static final long serialVersionUID = 5232453752276485070L;
 
    /** This task's completer, or null if none */
    //PS:一个链表结构，完成的触发顺序则是先进后出的模式
    final CountedCompleter<?> completer;
    /** 在完成前等待的任务数量 */
    volatile int pending;
 
    /**
     * PS: 传入的completer一般是‘父’任务的实例引用
     * @param completer this task's completer, or {@code null} if none
     * @param 初始PendingCount
     */
    protected CountedCompleter(CountedCompleter<?> completer,
                               int initialPendingCount) {
        this.completer = completer;
        this.pending = initialPendingCount;
    }
 
    protected CountedCompleter(CountedCompleter<?> completer) {
        this.completer = completer;
    }
    protected CountedCompleter() {
        this.completer = null;
    }
 
    /**
     * 这个任务完成的主要计算。
     */
    public abstract void compute();
 
    /**
     * 调用了无条件complete或者在调用tryComplete时，如果等待的任务数量是0，则触发此方法。
     * 默认情况下，此方法不执行任何操作。您可以通过检查给定调用方参数的标识来区分情况。
     * 如果不等于this，那么它通常是一个子任务，可能包含要组合的结果(和/或到其他结果的链接)。
     *
     * @param caller the task invoking this method (which may
     * be this task itself)
     */
    public void onCompletion(CountedCompleter<?> caller) {
    }
 
    /**
     * 调用方法completeexception (Throwable)或方法compute抛出异常时执行操作，
     * 且此任务尚未正常完成。进入这个方法时，这个任务FJTk#iscompletedwrong。
     * 这个方法的返回值控制了进一步的传播:如果 true 并且这个任务有一个未完成的完成
     * 器，那么这个完成器也会异常地完成，与这个完成器有相同的异常。这个方法的默认实
     * 现只返回 true。
     * @param ex the exception
     * @param caller the task invoking this method (which may
     * be this task itself)
     * @return {@code true} if this exception should be propagated to this
     * task's completer, if one exists
     */
    public boolean onExceptionalCompletion(Throwable ex, CountedCompleter<?> caller) {
        return true;
    }
 
    /**
     * 返回在此任务的构造函数中建立的完成器, or null if none.
     *
     * @return the completer
     */
    public final CountedCompleter<?> getCompleter() {
        return completer;
    }
 
    /**
     * return当前等待的数量
     *
     * @return the current pending count
     */
    public final int getPendingCount() {
        return pending;
    }
 
    /**
     * @param count the count
     */
    public final void setPendingCount(int count) {
        pending = count;
    }
 
    /**
     * (原子地)将给定的值添加到挂起的计数
     * @param delta the value to add
     */
    public final void addToPendingCount(int delta) {
        U.getAndAddInt(this, PENDING, delta);
    }
 
    /**
     * 只有在当前持有给定的期望值时，才会(原子地)将挂起的计数设置为给定的计数。
     *
     * @param expected the expected value
     * @param count the new value
     * @return {@code true} if successful
     */
    public final boolean compareAndSetPendingCount(int expected, int count) {
        return U.compareAndSwapInt(this, PENDING, expected, count);
    }
 
    /**
     * If the pending count is nonzero, (atomically) decrements it.
     *
     * @return the initial (undecremented) pending count holding on entry
     * to this method
     */
    public final int decrementPendingCountUnlessZero() {
        int c;
        do {} while ((c = pending) != 0 &&
                     !U.compareAndSwapInt(this, PENDING, c, c - 1));
        return c;
    }
 
    /**
     * Returns the root of the current computation; i.e., this
     * task if it has no completer, else its completer's root.
     * PS: 遍历单向链表，找到root节点
     * @return the root of the current computation
     */
    public final CountedCompleter<?> getRoot() {
        CountedCompleter<?> a = this, p;
        while ((p = a.completer) != null)
            a = p;
        return a;
    }
 
    /**
     * 如果挂起的计数为非零，则减少计数;否则调用 onCompletion(CountedCompleter)，
     * 然后类似地尝试完成此任务的completer(如果存在的话)，否则将此任务标记为完成。
     * PS：a.onCompletion(s); 表示完成的当前的任务，s = a 这里指向父任务
     *     如果父任务==null，则完成整个任务链的任务；否则重新进入循环执行逻辑
     */
    public final void tryComplete() {
        CountedCompleter<?> a = this, s = a;
        for (int c;;) {
            if ((c = a.pending) == 0) {
                a.onCompletion(s);
                if ((a = (s = a).completer) == null) {
                    s.quietlyComplete();
                    return;
                }
            }
            else if (U.compareAndSwapInt(a, PENDING, c, c - 1))
                return;
        }
    }
 
    /**
     * PS： 类似于tryComplete，但是在不需要调用每个‘子’任务的onCompletion方法时，
     * 可以使用此方法
     */
    public final void propagateCompletion() {
        CountedCompleter<?> a = this, s = a;
        for (int c;;) {
            if ((c = a.pending) == 0) {
                if ((a = (s = a).completer) == null) {
                    s.quietlyComplete();
                    return;
                }
            }
            else if (U.compareAndSwapInt(a, PENDING, c, c - 1))
                return;
        }
    }
 
    /**
     * 当获得多个子任务的任何一个(而不是所有)结果时，此方法可能非常有用。
     * 但是，在不覆盖 setRawResult 的常见(也是推荐的)情况下，
     * completeroot();可以更简单地获得这种效果。
     *  PS：适用于findAny这种场景
     *
     * @param rawResult the raw result
     */
    public void complete(T rawResult) {
        CountedCompleter<?> p;
        setRawResult(rawResult);
        onCompletion(this);
        quietlyComplete();
        if ((p = completer) != null)
            p.tryComplete();
    }
 
    /**
     * 如果此任务的挂起计数为零，则返回此任务;否则递减其挂起计数并返回  null。
     * 此方法被设计为在完成遍历循环中与 nextComplete一起使用。
     *
     * @return this task, if pending count was zero, else {@code null}
     */
    public final CountedCompleter<?> firstComplete() {
        for (int c;;) {
            if ((c = pending) == 0)
                return this;
            else if (U.compareAndSwapInt(this, PENDING, c, c - 1))
                return null;
        }
    }
 
    /**
     * 如果此任务没有完成器，则调用FJT#quiet complete并返回null
     * 或者，如果完成器的挂起计数非零，则减除该挂起计数并返回 null
     * 否则，返回完成器。
     * 此方法可用于同构任务层次结构的完成遍历循环的一部分:
     *
     * <pre> {@code
     * for (CountedCompleter<?> c = firstComplete();
     *      c != null;
     *      c = c.nextComplete()) {
     *   // ... process c ...
     * }}</pre>
     * PS： 简单来说，就是遍历查找完成的任务。
     * @return the completer, or {@code null} if none
     */
    public final CountedCompleter<?> nextComplete() {
        CountedCompleter<?> p;
        if ((p = completer) != null)
            return p.firstComplete();
        else {
            quietlyComplete();
            return null;
        }
    }
 
    /**
     * 等效于getRoot().quietlyComplete()
     * PS: 遍历到root的completer，执行其quietlyComplete方法
     */
    public final void quietlyCompleteRoot() {
        for (CountedCompleter<?> a = this, p;;) {
            if ((p = a.completer) == null) {
                a.quietlyComplete();
                return;
            }
            a = p;
        }
    }
 
    /**
     * 如果当前task尚未完成，则尝试去运行指定数量的未运行的完成路径上的任务
     * (如果已知存在该任务)
     *
     * @param maxTasks the maximum number of tasks to process.  If
     *                 less than or equal to zero, then no tasks are
     *                 processed.
     */
    public final void helpComplete(int maxTasks) {
        Thread t; ForkJoinWorkerThread wt;
        if (maxTasks > 0 && status >= 0) {
            if ((t = Thread.currentThread()) instanceof ForkJoinWorkerThread)
                (wt = (ForkJoinWorkerThread)t).pool.
                    helpComplete(wt.workQueue, this, maxTasks);
            else
                ForkJoinPool.common.externalHelpComplete(this, maxTasks);
        }
    }
 
    /**
     * 支持FJT的异常传播
     */
    void internalPropagateException(Throwable ex) {
        CountedCompleter<?> a = this, s = a;
        while (a.onExceptionalCompletion(ex, s) &&
               (a = (s = a).completer) != null && a.status >= 0 &&
               a.recordExceptionalCompletion(ex) == EXCEPTIONAL)
            ;
    }
 
    /**
     * 为CountedCompleters实现执行约定
     */
    protected final boolean exec() {
        compute();
        return false;
    }
 
    /**
     * 一般会覆盖重写实现
     *
     * @return the result of the computation
     */
    public T getRawResult() { return null; }
 
    /**
     * 包含结果的CountedCompleters可以选择使用的方法来帮助维护结果数据。
     * 默认情况下，什么也不做。不建议重写。但是，如果重写此方法以更新现有对
     * 象或字段，则通常必须将其定义为线程安全的.
     */
    protected void setRawResult(T t) { }
 
    // Unsafe mechanics
    private static final sun.misc.Unsafe U;
    private static final long PENDING;
    static {
        try {
            U = sun.misc.Unsafe.getUnsafe();
            PENDING = U.objectFieldOffset
                (CountedCompleter.class.getDeclaredField("pending"));
        } catch (Exception e) {
            throw new Error(e);
        }
    }
}
```

## 示例一

```java
 
  /**
  * 可以注意到，在递归情况下，任务在for它的右任务之后什么也不做，因此可以在返回之前直接调用它的左
  * 任务，从而改进这种设计。(这类似于尾部递归移除。)此外，由于任务在执行其左任务时返回(而不是通
  * 过调用{@code tryComplete})，挂起计数被设置为1:
  */
  class MyOperation<E> { void apply(E e) { ... }  }
 
  class ForEach<E> extends CountedCompleter<Void> {
 
    public static <E> void forEach(E[] array, MyOperation<E> op) {
      new ForEach<E>(null, array, op, 0, array.length).invoke();
    }
 
    final E[] array; final MyOperation<E> op; final int lo, hi;
    ForEach(CountedCompleter<?> p, E[] array, MyOperation<E> op, int lo, int hi) {
      super(p);
      this.array = array; this.op = op; this.lo = lo; this.hi = hi;
    }
 
    public void compute() { // version 1
      if (hi - lo >= 2) {
        int mid = (lo + hi) >>> 1;
        //PS: 这里手动设置等待的任务，实质上就是等待左右两个部分的任务进行fork
        setPendingCount(2); // must set pending count before fork
        new ForEach(this, array, op, mid, hi).fork(); // right child
        new ForEach(this, array, op, lo, mid).fork(); // left child
     }
      else if (hi > lo)
        op.apply(array[lo]);
      tryComplete();
    }
  }
 
//改进版本：
class ForEach<E> ...
    public void compute() { // version 2
       if (hi - lo >= 2) {
        int mid = (lo + hi) >>> 1;
        setPendingCount(1); // only one pending
        new ForEach(this, array, op, mid, hi).fork(); // right child
        new ForEach(this, array, op, lo, mid).compute(); // direct invoke
      }
      else {
        if (hi > lo)
          op.apply(array[lo]);
        tryComplete();
      }
    }
}</pre>
```

## 示例一再改进

```java
/* 作为进一步的改进，请注意左边的任务甚至不需要存在。
* 我们可以使用原始任务进行迭代，并为每个fork添加一个挂起计数，而不是创建一个新任务。
* 此外，由于此树中没有任何任务实现{@link #onCompletion(CountedCompleter)}方法，
* 所以{@code tryComplete()}可以替换为{@link #propagateCompletion}。
*/
//PS： 这里通过循环实质上分解了 原来‘左’边的任务，而‘右’边的任务，则通过new ForEach自身
//的compute自行处理（即当成全部任务递归分解）。
class ForEach<E> ...
    public void compute() { // version 3
      int l = lo,  h = hi;
      while (h - l >= 2) {
        int mid = (l + h) >>> 1;
        addToPendingCount(1);
        new ForEach(this, array, op, mid, h).fork(); // right child
        h = mid;
      }
      if (h > l)
        op.apply(array[l]);
      propagateCompletion();
    }
}
 
//应用的一个搜索，在分段搜索中，找到一个，就结束。
class Searcher<E> extends CountedCompleter<E> {
    final E[] array; final AtomicReference<E> result; final int lo, hi;
    Searcher(CountedCompleter<?> p, E[] array, AtomicReference<E> result, int lo, int hi) {
      super(p);
      this.array = array; this.result = result; this.lo = lo; this.hi = hi;
    }
    public E getRawResult() { return result.get(); }
    public void compute() { // similar to ForEach version 3
      int l = lo,  h = hi;
      while (result.get() == null && h >= l) {
        if (h - l >= 2) {
          int mid = (l + h) >>> 1;
          addToPendingCount(1);
          new Searcher(this, array, result, mid, h).fork();
          h = mid;
        }
        else {
          E x = array[l];
          if (matches(x) && result.compareAndSet(null, x))
            quietlyCompleteRoot(); // root task is now joinable
          break;
        }
      }
      tryComplete(); // normally complete whether or not found
    }
    boolean matches(E e) { ... } // return true if found
 
    public static <E> E search(E[] array) {
        return new Searcher<E>(null, array, new AtomicReference<E>(), 0, array.length).invoke();
    }
}}
```

## 示例简化的MapReduce

```java
//PS: 这种简化的MapReduce适用于无顺序要求的分解与归纳操作
//将所有别的节点当成兄弟节点；都可以直接进行归纳操作。
 class MyMapper<E> { E apply(E v) {  ...  } }
 class MyReducer<E> { E apply(E x, E y) {  ...  } }
class MapReducer<E> extends CountedCompleter<E> {
    final E[] array; final MyMapper<E> mapper;
    final MyReducer<E> reducer; final int lo, hi;
    MapReducer<E> sibling;
    E result;
    MapReducer(CountedCompleter<?> p, E[] array, MyMapper<E> mapper,
               MyReducer<E> reducer, int lo, int hi) {
      super(p);
      this.array = array; this.mapper = mapper;
      this.reducer = reducer; this.lo = lo; this.hi = hi;
    }
    public void compute() {
      if (hi - lo >= 2) {
        int mid = (lo + hi) >>> 1;
        MapReducer<E> left = new MapReducer(this, array, mapper, reducer, lo, mid);
        MapReducer<E> right = new MapReducer(this, array, mapper, reducer, mid, hi);
        left.sibling = right;
        right.sibling = left;
        setPendingCount(1); // only right is pending
        right.fork();
        left.compute();     // directly execute left
      }
      else {
        if (hi > lo)
            result = mapper.apply(array[lo]);
        tryComplete();
      }
    }
    public void onCompletion(CountedCompleter<?> caller) {
      if (caller != this) {
        MapReducer<E> child = (MapReducer<E>)caller;
        MapReducer<E> sib = child.sibling;
        if (sib == null || sib.result == null)
          result = child.result;
        else
          result = reducer.apply(child.result, sib.result);
      }
    }
    public E getRawResult() { return result; }
 
    public static <E> E mapReduce(E[] array, MyMapper<E> mapper, MyReducer<E> reducer) {
      return new MapReducer<E>(null, array, mapper, reducer,
                               0, array.length).invoke();
    }
}}
 
//PS: 改进版，通过next来连接MapReducer，使之有序。
 
class MapReducer<E> extends CountedCompleter<E> { // version 2
    final E[] array; final MyMapper<E> mapper;
    final MyReducer<E> reducer; final int lo, hi;
    MapReducer<E> forks, next; // record subtask forks in list
    E result;
    MapReducer(CountedCompleter<?> p, E[] array, MyMapper<E> mapper,
               MyReducer<E> reducer, int lo, int hi, MapReducer<E> next) {
      super(p);
      this.array = array; this.mapper = mapper;
      this.reducer = reducer; this.lo = lo; this.hi = hi;
      this.next = next;
    }
    public void compute() {
      int l = lo,  h = hi;
      while (h - l >= 2) {
        int mid = (l + h) >>> 1;
        addToPendingCount(1);
        (forks = new MapReducer(this, array, mapper, reducer, mid, h, forks)).fork();
        h = mid;
      }
      if (h > l)
        result = mapper.apply(array[l]);
      // process completions by reducing along and advancing subtask links
      for (CountedCompleter<?> c = firstComplete(); c != null; c = c.nextComplete()) {
        for (MapReducer t = (MapReducer)c, s = t.forks;  s != null; s = t.forks = s.next)
          t.result = reducer.apply(t.result, s.result);
      }
    }
    public E getRawResult() { return result; }
 
    public static <E> E mapReduce(E[] array, MyMapper<E> mapper, MyReducer<E> reducer) {
      return new MapReducer<E>(null, array, mapper, reducer,
                               0, array.length, null).invoke();
    }
}}
```

# 更多参考

[ForkJoin框架之CountedCompleter](https://segmentfault.com/a/1190000019555458)
