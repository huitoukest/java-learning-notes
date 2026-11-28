---
title: "java进阶笔记线程与并发之StampedLock"
date: "2020-04-08 17:59:35"
categories: ["java进阶学习笔记"]
tags: ["java", "多线程", "并发编程", "StampedLock"]
---

# 简介

- StampedLock 是ReadWriteLock的一种实现，不支持重入（容易死锁），适用于读多写少的场景。
- StampedLock 在读取的节点是并发唤醒的，在读取上的性能理论上更高。
- 一旦读写操作在1:1甚至以上，则synchronized的性能将更高，ReentrantReadWriteLock的性能急剧下降，StampedLock 性能缓慢下降。一般推荐使用synchronized，而读取占比非常高的常见建议自定义乐观锁实现。
- 方法

  - long writeLock()  阻塞获取排它写锁

  - tryWriteLock() 尝试获取排它写锁

  - public long tryWriteLock(long time, TimeUnit unit)

  - public long writeLockInterruptibly() throws InterruptedException

  - public long readLock()  读锁，非排它

  - public long tryOptimisticRead() 尝试乐观方式获取读取锁，当成功返回一个stamp，否则返回0L

  - public boolean validate(long stamp)

    - 持有锁或者改stamp未被独占则返回true
    - 如果 stamp == 0 ，则返回false

  - public long tryConvertToWriteLock(long stamp)

    -

  - 如果锁状态与给定的戳记匹配，则执行以下操作之一。如果戳记表示持有写锁，则返回它。或者，如果有读锁，如果写锁可用，则释放读锁并返回写戳。或者，如果是乐观读，则仅在立即可用时才返回写戳记。此方法在所有其他情况下都返回零。

- public long tryConvertToReadLock(long stamp)

    - public long tryConvertToOptimisticRead(long stamp)
    - 如果锁状态与给定的戳记匹配，则执行以下操作之一。如果戳记表示持有写锁，则释放它并获得读锁。或者，如果是读锁，则返回它。或者，如果一个乐观读操作获得了一个读锁，并且只有在立即可用的情况下才返回一个读戳。此方法在所有其他情况下都返回零。

# 使用示例

官方示例：

```java
class Point {
    private double x, y;
    private final StampedLock sl = new StampedLock();
 
    void move(double deltaX, double deltaY) { // 排它锁示例
        long stamp = sl.writeLock();
        try {
            x += deltaX;
            y += deltaY;
        } finally {
            sl.unlockWrite(stamp);
        }
    }
 
    double distanceFromOrigin() { // 只读锁
        long stamp = sl.tryOptimisticRead();
        double currentX = x, currentY = y;
        if (!sl.validate(stamp)) {
            stamp = sl.readLock();
            try {
                currentX = x;
                currentY = y;
            } finally {
                sl.unlockRead(stamp);
            }
        }
        return Math.sqrt(currentX * currentX + currentY * currentY);
    }
    //读锁升级
    void moveIfAtOrigin(double newX, double newY) {
        // Could instead start with optimistic, not read mode
        long stamp = sl.readLock();
        try {
            while (x == 0.0 && y == 0.0) {
                long ws = sl.tryConvertToWriteLock(stamp);
                if (ws != 0L) {
                    //转换成功则使用返回的stamp
                    stamp = ws;
                    x = newX;
                    y = newY;
                    break;
                } else {
                    sl.unlockRead(stamp);
                    stamp = sl.writeLock();
                }
            }
        } finally {
            sl.unlock(stamp);
        }
    }
}
```

# 想法

- 对于有顺序要求的数据处理，可以使用排队机制（同锁里面的链表、队列）
- 对于冲突的线程，避免频繁尝试获取独占资源，采用获取资格后排队处理
- 独占和非独占操作共同处理时，独占阻塞其它所有处理，非独占则唤醒所有非独占操作。

注： 找到一个文章将原理说的详细明了，见参见。

# 参见

java多线程进阶（十一）—— J.U.C之locks框架：StampedLock： https://segmentfault.com/a/1190000015808032?utm_source=tag-newest

Java 8 StampedLock，ReadWriteLock以及synchronized的比较： https://zhuanlan.zhihu.com/p/33422168
