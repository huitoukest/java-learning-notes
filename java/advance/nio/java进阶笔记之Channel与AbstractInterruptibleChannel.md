---
title: "java进阶笔记之Channel与AbstractInterruptibleChannel"
date: "2020-07-22 15:05:29"
categories: ["java进阶学习笔记"]
tags: ["java", "进阶笔记", "Channel", "Interruptible", "blockedOn"]
---

# 简介

- 什么是Channel
  - Channel = 通道 = **承上启下的I / O操作入口** ,  即连接点对点的输入输出操作入口。
    通道表示一个打开的到一个实体的连接，如一个硬件设备，文件，网络套接字，或者能够执行一个或多个不同的I / O操作，例如读或写的程序组件。通道要么打开要么关闭。 通道是在创建开放的，一旦关闭则永久关闭。 一旦通道被关闭时，任何试图调用I / O的操作，都抛出 ClosedChannelException.
  - Channel 和 Stream 不同
    - Stream 是单向数据流 , 要么读 , 要么写 .
    - Channel 是输入输出通道 , 支持读写 .
    -  一般而言 Channel 的性能更高 .
  -  Channel 是高度抽象的 , 除了 开启/关闭是通用的 , 其余的操作依赖于具体的实现. ( 后续将继续学习研究 ).
- 关系: AbstractInterruptibleChannel 实现了Channel, InterruptibleChannel接口 .
  - interface Channel extends Closeable  extends AutoCloseable .
  - InterruptibleChannel extends Channel .

# 源码简析

## AutoCloseable 接口

```java
/**
* ps: 用来支持try-with-resources 快捷语法 , 在try代码块执行完毕后 ,其中的资源系统
* 会自动进行释放 , 自动调用 close方法.
*
* @author Josh Bloch
* @since 1.7
*/
public interface AutoCloseable {
    /**
     * 关闭并释放资源
     * ps: 与 java.io.Closeable#close 不同 , 此close多次调用可能有副作用.
     */
    void close() throws Exception;
}
```

## Closeable 接口

```java
package java.io;
 
import java.io.IOException;
 
/**
* 关闭持有的资源
*
* @since 1.5
*/
public interface Closeable extends AutoCloseable {
 
    /**
     * 关闭此流并释放与之关联的所有系统资源.
     * 如果流已经关闭，则调用此方法无效. close() 后使用资源，会抛出IOException.
     *
     * @throws IOException if an I/O error occurs
     */
    public void close() throws IOException;
}
```

## Channel 接口

```java
package java.nio.channels;
 
import java.io.IOException;
import java.io.Closeable;
 
 
/**
* 实现通道的类需要自行 处理并说明 线程安全问题
*
* @author Mark Reinhold
* @author JSR-51 Expert Group
* @since 1.4
*/
 
public interface Channel extends Closeable {
 
    /**
     * Tells whether or not this channel is open.
     */
    public boolean isOpen();
 
    /**
     * 关闭此通道。
     * 信道被关闭后，任何进一步的IO操作将导致ClosedChannelException被抛出。
     * 如果此信道已被关闭，则调用此方法没有效果。此方法可在任何时间被调用。
     * 如果其他线程已经调用它，此时别的线程调用将被阻塞，直到第一次调用完成
     * 后，它会返回, 但对结果无影响。
     */
    public void close() throws IOException;
 
}
```

## InterruptibleChannel 接口

```java
package java.nio.channels;
 
import java.io.IOException;
 
 
/**
* 定义了可以被异步关闭和中断的Channel
 
* @author Mark Reinhold
* @author JSR-51 Expert Group
* @since 1.4
*/
 
public interface InterruptibleChannel
    extends Channel
{
 
    /**
     * ps: 在当前Channel进行阻塞的io操作的线程 , 在close ( 被其他线程) 调用后 ,
     * (阻塞的操作) 将会抛出 AsynchronousCloseException
     *
     * @throws  IOException  If an I/O error occurs
     */
    public void close() throws IOException;
 
}
```

## AbstractInterruptibleChannel

```java
package java.nio.channels.spi;
 
import java.io.IOException;
import java.lang.reflect.Method;
import java.lang.reflect.InvocationTargetException;
import java.nio.channels.*;
import java.security.AccessController;
import java.security.PrivilegedAction;
import sun.nio.ch.Interruptible;
 
 
/**
* 此类实现了基本的异步关闭 以及 channel的中断处理
* 实现Channel时, 必须通过 begin 和 end代码块方法来和io交互.
* 示例:
* boolean completed = false;
* try {
 *     begin();
 *     completed = ...;    // 可能阻塞io的操作
 *     return ...;         // Return result
* } finally {
 *     end(completed);
* }
* completed 参数用来表示当前才做是否完成.
*
* @author Mark Reinhold
* @author JSR-51 Expert Group
* @since 1.4
*/
 
public abstract class AbstractInterruptibleChannel
    implements Channel, InterruptibleChannel
{
 
    private final Object closeLock = new Object();
    private volatile boolean open = true;
 
    protected AbstractInterruptibleChannel() { }
 
    /**
     * 同步的关闭Channel, 如果已经被关闭 ,则直接返回
     */
    public final void close() throws IOException {
        synchronized (closeLock) {
            if (!open)
                return;
            open = false;
            implCloseChannel();
        }
    }
 
    /**
     * 仅仅在Channel未关闭时调用, 不可多次调用.
     */
    protected abstract void implCloseChannel() throws IOException;
 
    public final boolean isOpen() {
        return open;
    }
 
 
    // -- Interruption machinery --
     //ps: 中断的相关处理 , 这里定义了 一个中断的回调 以及中断的线程
    private Interruptible interruptor;
    private volatile Thread interrupted;
 
    /**
     * 标志着 开始一个可能长期阻塞的IO操作. 必须和 end 用try finally快串联起来.
     * ps: 这里首先建了一个 interruptor 实例, 通过 blockedOn()方法将之设置到
     * 当前线程的Thread的 Interruptible 引用上 . 当当前线程的 interrupt 方法
     * 执行时, 会执行Interruptible#interrupt(). 这时就会自动在中断时执行通道
     * 的关闭方法.
     */
    protected final void begin() {
        if (interruptor == null) {
            interruptor = new Interruptible() {
                    public void interrupt(Thread target) {
                        synchronized (closeLock) {
                            if (!open)
                                return;
                            open = false;
                            interrupted = target;
                            try {
                                AbstractInterruptibleChannel.this.implCloseChannel();
                            } catch (IOException x) { }
                        }
                    }};
        }
        blockedOn(interruptor);
        Thread me = Thread.currentThread();
        if (me.isInterrupted())
            interruptor.interrupt(me);
    }
 
    /**
     * 标志这一个IO操作的结束. completed 表示操作是否成功完成.
     8
     */
    protected final void end(boolean completed)
        throws AsynchronousCloseException
    {
        //ps: 不论是否中断 , 将当前线程的Interruptible 引用置空 ( 因为操作已经结束 ).
        blockedOn(null);
        //ps:如果是io操作中被中断, 且是当前线程被中断 , 则抛出ClosedByInterruptException
        Thread interrupted = this.interrupted;
        if (interrupted != null && interrupted == Thread.currentThread()) {
            interrupted = null;
            throw new ClosedByInterruptException();
        }
        //ps:如果没有被中断 , 但是在操作没完成且 Channel已经关闭 , 则
        //抛出 AsynchronousCloseException.
        if (!completed && !open)
            throw new AsynchronousCloseException();
    }
 
 
    // -- sun.misc.SharedSecrets --
    static void blockedOn(Interruptible intr) {         // package-private
        sun.misc.SharedSecrets.getJavaLangAccess().blockedOn(Thread.currentThread(),
                                                             intr);
    }
}
```

## blockedOn说明

此方法在这里实际上就是为Thread 实例中的 Interruptible属性 赋值.

实际上就是最终通过Thread中的blockedOn方法触发.

## Thread#interrupt说明

在线程被中断时, 会调用此方法 . 而此方法就会触发Interruptible 中的interrupt 方法 , 即形成中断时回调interrupt 中封装好的逻辑.

```java
private volatile Interruptible blocker;
private final Object blockerLock = new Object();
 
 
/* Set the blocker field; invoked via sun.misc.SharedSecrets from java.nio code
     */
void blockedOn(Interruptible b) {
    synchronized (blockerLock) {
        blocker = b;
    }
}
 
public void interrupt() {
    if (this != Thread.currentThread())
        checkAccess();
 
    synchronized (blockerLock) {
        Interruptible b = blocker;
        if (b != null) {
            interrupt0();           // Just to set the interrupt flag
            b.interrupt(this);
            return;
        }
    }
    interrupt0();
}
```

# 参见

NIO包的AbstractInterruptibleChannel分析:  https://www.iteye.com/blog/jnullpointer-2119982
Java NIO 那些躲在角落的细节: https://www.oschina.net/question/138146_26027
