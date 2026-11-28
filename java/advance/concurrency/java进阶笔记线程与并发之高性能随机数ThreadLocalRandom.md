---
title: "java进阶笔记线程与并发之高性能随机数ThreadLocalRandom"
date: "2020-04-09 18:11:23"
categories: ["java进阶学习笔记"]
tags: ["java", "多线程", "random", "ThreadLocal", "进阶笔记"]
---

# 简介

- java的随机数均根据seed生成，而新的seed由老的seed生成。
- java.util.Random 线程安全，但是在高并发情况下，需要对seed做同步处理，所以冲突越高，性能越低。
- ThreadLocalRandom 在多线程冲突时，具有更高的随机数产生性能。
  - 基本原理是运行时将seed放到(当前)Thread的变量:  threadLocalRandomSeed  中，然后独立维护线程相关的seed，这样就不存在线程间的冲突，所以性能更高。
- **ThreadLocalRandom 的实例禁止跨线程共享，如果共享会导致不同线程生成相同随机数**。

# 示例

```java
//产生一个随机数
ThreadLocalRandom.current().nextInt(100)
```

**java8 实际测试效果**：

| 线程数量 | 线程内循环生产次数 | random耗时(毫秒) | ThreadLocalRandom耗时(毫秒) |
| -------- | ------------------ | ---------------- | --------------------------- |
| 1        | 1w                 | 6                | 11                          |
| 10       | 1w                 | 16               | 15                          |
| 10       | 10w                | 101              | 65                          |
| 50       | 1w                 | 56               | 54                          |
| 50       | 10w                | 509              | 115                         |
| 100      | 1w                 | 105              | 80                          |
| 100      | 10w                | 1115             | 131                         |

- 可以看到产生的多线程冲突越多，则random的性能越低，在极短时间内产生的数量在50w时是一个分水岭。

## 不同线程产生重复相同随机数的问题

```java
import java.util.Random;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.ThreadLocalRandom;
 
public class ThreadLocalRandomTask {
    private static Random random = ThreadLocalRandom.current();
 
    public static void main(String[] args) {
        ExecutorService taskPool = Executors.newCachedThreadPool();
        for(int n = 1; n < 10; n++) {
            taskPool.submit(() ->  System.out.println(random.nextInt()));
        }
        taskPool.shutdown();
    }
}
```

- 在ThreadLocalRandom 被多线程共享实例时，多个线程之间，调用相同次数产生的随机数相同。
  - ThreadLocalRandom.current() 表示初始化了主线程的随机数seed
  - random.nextInt() 会获取当前线程的seed，但是这里并未初始化（所以没有值，会默认初始化）
    - 多线程内初始化时seed值相同，所以产生的随机数相同
- ps： 这里因为线程复用的问题，可能会有多个重复的随机数产生。（但是多次运行后的相同次产生的随机数均固定）。
  - 因为伪随机 +  seed值相同

# 源码简析

基于jdk 1.8。

ThreadLocalRandom extends Random，使用方法大致相同。

```java
package java.util.concurrent;
 
import java.io.ObjectStreamField;
import java.util.Random;
import java.util.Spliterator;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicLong;
import java.util.function.DoubleConsumer;
import java.util.function.IntConsumer;
import java.util.function.LongConsumer;
import java.util.stream.DoubleStream;
import java.util.stream.IntStream;
import java.util.stream.LongStream;
import java.util.stream.StreamSupport;
import sun.misc.VM;
 
/**
* ThreadLocalRandom的实例在密码上是不安全的，安全敏感的程序应该使用
* java.security中的SecureRandom
* @since 1.7
* @author Doug Lea
*/
public class ThreadLocalRandom extends Random {
    /*
     * 使用一个静态实例来访问Thread中的threadLocalRandomSeed值 = seed值。
     */
 
    /** 生成每个线程的初始化/探测字段 */
    private static final AtomicInteger probeGenerator =
        new AtomicInteger();
 
    /**
     * The next seed for default constructors.
     */
    private static final AtomicLong seeder = new AtomicLong(initialSeed());
    //初始化一个种子，值是固定的
    private static long initialSeed() {
        String sec = VM.getSavedProperty("java.util.secureRandomSeed");
        if (Boolean.parseBoolean(sec)) {
            byte[] seedBytes = java.security.SecureRandom.getSeed(8);
            long s = (long)(seedBytes[0]) & 0xffL;
            for (int i = 1; i < 8; ++i)
                s = (s << 8) | ((long)(seedBytes[i]) & 0xffL);
            return s;
        }
        return (mix64(System.currentTimeMillis()) ^
                mix64(System.nanoTime()));
    }
 
    /**
     * The seed increment
     */
    private static final long GAMMA = 0x9e3779b97f4a7c15L;
 
    /**
     * The increment for generating probe values
     */
    private static final int PROBE_INCREMENT = 0x9e3779b9;
 
    /**
     * The increment of seeder per new instance
     */
    private static final long SEEDER_INCREMENT = 0xbb67ae8584caa73bL;
 
    // Constants from SplittableRandom
    private static final double DOUBLE_UNIT = 0x1.0p-53;  // 1.0  / (1L << 53)
    private static final float  FLOAT_UNIT  = 0x1.0p-24f; // 1.0f / (1 << 24)
 
    /** Rarely-used holder for the second of a pair of Gaussians */
    private static final ThreadLocal<Double> nextLocalGaussian =
        new ThreadLocal<Double>();
 
    private static long mix64(long z) {
        z = (z ^ (z >>> 33)) * 0xff51afd7ed558ccdL;
        z = (z ^ (z >>> 33)) * 0xc4ceb9fe1a85ec53L;
        return z ^ (z >>> 33);
    }
 
    private static int mix32(long z) {
        z = (z ^ (z >>> 33)) * 0xff51afd7ed558ccdL;
        return (int)(((z ^ (z >>> 33)) * 0xc4ceb9fe1a85ec53L) >>> 32);
    }
 
    /**
     * Field used only during singleton initialization.
     * True when constructor completes.
     */
    boolean initialized;
 
    /** Constructor used only for static singleton */
    private ThreadLocalRandom() {
        initialized = true; // false during super() call
    }
 
    /** The common ThreadLocalRandom */
    static final ThreadLocalRandom instance = new ThreadLocalRandom();
 
    /**
     * 初始化，主要是获取当前线程并设置当前线程对应的seed和probe探针值
     * 每次获取后，（跨Thread）seed值都会变化（加上了增量SEEDER_INCREMENT）
     */
    static final void localInit() {
        int p = probeGenerator.addAndGet(PROBE_INCREMENT);
        int probe = (p == 0) ? 1 : p; // skip 0
        long seed = mix64(seeder.getAndAdd(SEEDER_INCREMENT));
        Thread t = Thread.currentThread();
        UNSAFE.putLong(t, SEED, seed);
        UNSAFE.putInt(t, PROBE, probe);
    }
 
    /**
     * 如果获取值 = 0，则初始化，否则直接使用静态实例
     */
    public static ThreadLocalRandom current() {
        if (UNSAFE.getInt(Thread.currentThread(), PROBE) == 0)
            localInit();
        return instance;
    }
 
    /**
     * 无效操作
     */
    public void setSeed(long seed) {
        // only allow call from super() constructor
        if (initialized)
            throw new UnsupportedOperationException();
    }
    //生成当前线程对应的下一个seed，并保存到对应Thread，种子加上固定的
    //增量值 GAMMA
    final long nextSeed() {
        Thread t; long r; // read and update per-thread seed
        UNSAFE.putLong(t = Thread.currentThread(), SEED,
                       r = UNSAFE.getLong(t, SEED) + GAMMA);
        return r;
    }
 
    // We must define this, but never use it.
    protected int next(int bits) {
        return (int)(mix64(nextSeed()) >>> (64 - bits));
    }
 
    // IllegalArgumentException messages
    static final String BadBound = "bound must be positive";
    static final String BadRange = "bound must be greater than origin";
    static final String BadSize  = "size must be non-negative";
 
    /**
     * The form of nextLong used by LongStream Spliterators.  If
     * origin is greater than bound, acts as unbounded form of
     * nextLong, else as bounded form.
     * 如果 origin >= bound 则不使用值大小限定。
     * //ps: 如果是2的n此幂，则取差值利用位运算获取比差值小，然后算出随机数r
     *
     * @param origin the least value, unless greater than bound
     * @param bound the upper bound (exclusive), must not equal origin
     * @return a pseudorandom value
     */
    final long internalNextLong(long origin, long bound) {
        long r = mix64(nextSeed());
        if (origin < bound) {
            long n = bound - origin, m = n - 1;
            if ((n & m) == 0L)  // power of two
                r = (r & m) + origin;
            else if (n > 0L) {  // reject over-represented candidates
                //确保非负数，产生随机数每次变小相加直到符合条件
                for (long u = r >>> 1;            // ensure nonnegative
                     u + m - (r = u % n) < 0L;    // rejection check
                     u = mix64(nextSeed()) >>> 1) // retry
                    ;
                r += origin;
            }
            else {
                //r不再范围内，则重新生成
                //ps://bound为正，origin为负，可能导致超过Long最大值，这时随机生成范围内的值
                while (r < origin || r >= bound)
                    r = mix64(nextSeed());
            }
        }
        return r;
    }
 
    final int internalNextInt(int origin, int bound) {
        int r = mix32(nextSeed());
        if (origin < bound) {
            int n = bound - origin, m = n - 1;
            if ((n & m) == 0)
                r = (r & m) + origin;
            else if (n > 0) {
                for (int u = r >>> 1;
                     u + m - (r = u % n) < 0;
                     u = mix32(nextSeed()) >>> 1)
                    ;
                r += origin;
            }
            else {
                while (r < origin || r >= bound)
                    r = mix32(nextSeed());
            }
        }
        return r;
    }
 
    /**
     * double 内部使用的nextLong()
     */
    final double internalNextDouble(double origin, double bound) {
        double r = (nextLong() >>> 11) * DOUBLE_UNIT;
        if (origin < bound) {
            r = r * (bound - origin) + origin;
            if (r >= bound) // correct for rounding
                r = Double.longBitsToDouble(Double.doubleToLongBits(bound) - 1);
        }
        return r;
    }
 
    public int nextInt() {
        return mix32(nextSeed());
    }
 
    public int nextInt(int bound) {
        if (bound <= 0)
            throw new IllegalArgumentException(BadBound);
        int r = mix32(nextSeed());
        int m = bound - 1;
        if ((bound & m) == 0) // power of two
            r &= m;
        else { // reject over-represented candidates
            for (int u = r >>> 1;
                 u + m - (r = u % bound) < 0;
                 u = mix32(nextSeed()) >>> 1)
                ;
        }
        return r;
    }
 
    public int nextInt(int origin, int bound) {
        if (origin >= bound)
            throw new IllegalArgumentException(BadRange);
        return internalNextInt(origin, bound);
    }
 
    public long nextLong() {
        return mix64(nextSeed());
    }
 
    public long nextLong(long bound) {
        if (bound <= 0)
            throw new IllegalArgumentException(BadBound);
        long r = mix64(nextSeed());
        long m = bound - 1;
        if ((bound & m) == 0L) // power of two
            r &= m;
        else { // reject over-represented candidates
            for (long u = r >>> 1;
                 u + m - (r = u % bound) < 0L;
                 u = mix64(nextSeed()) >>> 1)
                ;
        }
        return r;
    }
 
    public long nextLong(long origin, long bound) {
        if (origin >= bound)
            throw new IllegalArgumentException(BadRange);
        return internalNextLong(origin, bound);
    }
 
    public double nextDouble() {
        return (mix64(nextSeed()) >>> 11) * DOUBLE_UNIT;
    }
 
    public double nextDouble(double bound) {
        if (!(bound > 0.0))
            throw new IllegalArgumentException(BadBound);
        double result = (mix64(nextSeed()) >>> 11) * DOUBLE_UNIT * bound;
        return (result < bound) ?  result : // correct for rounding
            Double.longBitsToDouble(Double.doubleToLongBits(bound) - 1);
    }
 
    public double nextDouble(double origin, double bound) {
        if (!(origin < bound))
            throw new IllegalArgumentException(BadRange);
        return internalNextDouble(origin, bound);
    }
 
    //ps: //正数或者0 = false，负数 = true，
    //恰好默认数值因为符号位的原因，负数比正数多一个数，所以正好平衡。
    public boolean nextBoolean() {
        return mix32(nextSeed()) < 0;
    }
 
    public float nextFloat() {
        return (mix32(nextSeed()) >>> 8) * FLOAT_UNIT;
    }
 
    public double nextGaussian() {
        // Use nextLocalGaussian instead of nextGaussian field
        Double d = nextLocalGaussian.get();
        if (d != null) {
            nextLocalGaussian.set(null);
            return d.doubleValue();
        }
        double v1, v2, s;
        do {
            v1 = 2 * nextDouble() - 1; // between -1 and 1
            v2 = 2 * nextDouble() - 1; // between -1 and 1
            s = v1 * v1 + v2 * v2;
        } while (s >= 1 || s == 0);
        double multiplier = StrictMath.sqrt(-2 * StrictMath.log(s)/s);
        nextLocalGaussian.set(new Double(v2 * multiplier));
        return v1 * multiplier;
    }
 
    // stream methods, coded in a way intended to better isolate for
    // maintenance purposes the small differences across forms.
 
    /**
     * 从intStream中拆出int数据以得到IntStream（限定了streamSize)
     * @since 1.8
     */
    public IntStream ints(long streamSize) {
        if (streamSize < 0L)
            throw new IllegalArgumentException(BadSize);
        return StreamSupport.intStream
            (new RandomIntsSpliterator
             (0L, streamSize, Integer.MAX_VALUE, 0),
             false);
    }
 
    public IntStream ints() {
        return StreamSupport.intStream
            (new RandomIntsSpliterator
             (0L, Long.MAX_VALUE, Integer.MAX_VALUE, 0),
             false);
    }
 
    public IntStream ints(long streamSize, int randomNumberOrigin,
                          int randomNumberBound) {
        if (streamSize < 0L)
            throw new IllegalArgumentException(BadSize);
        if (randomNumberOrigin >= randomNumberBound)
            throw new IllegalArgumentException(BadRange);
        return StreamSupport.intStream
            (new RandomIntsSpliterator
             (0L, streamSize, randomNumberOrigin, randomNumberBound),
             false);
    }
 
    public IntStream ints(int randomNumberOrigin, int randomNumberBound) {
        if (randomNumberOrigin >= randomNumberBound)
            throw new IllegalArgumentException(BadRange);
        return StreamSupport.intStream
            (new RandomIntsSpliterator
             (0L, Long.MAX_VALUE, randomNumberOrigin, randomNumberBound),
             false);
    }
 
    public LongStream longs(long streamSize) {
        if (streamSize < 0L)
            throw new IllegalArgumentException(BadSize);
        return StreamSupport.longStream
            (new RandomLongsSpliterator
             (0L, streamSize, Long.MAX_VALUE, 0L),
             false);
    }
 
    public LongStream longs() {
        return StreamSupport.longStream
            (new RandomLongsSpliterator
             (0L, Long.MAX_VALUE, Long.MAX_VALUE, 0L),
             false);
    }
 
    public LongStream longs(long streamSize, long randomNumberOrigin,
                            long randomNumberBound) {
        if (streamSize < 0L)
            throw new IllegalArgumentException(BadSize);
        if (randomNumberOrigin >= randomNumberBound)
            throw new IllegalArgumentException(BadRange);
        return StreamSupport.longStream
            (new RandomLongsSpliterator
             (0L, streamSize, randomNumberOrigin, randomNumberBound),
             false);
    }
 
    public LongStream longs(long randomNumberOrigin, long randomNumberBound) {
        if (randomNumberOrigin >= randomNumberBound)
            throw new IllegalArgumentException(BadRange);
        return StreamSupport.longStream
            (new RandomLongsSpliterator
             (0L, Long.MAX_VALUE, randomNumberOrigin, randomNumberBound),
             false);
    }
 
    public DoubleStream doubles(long streamSize) {
        if (streamSize < 0L)
            throw new IllegalArgumentException(BadSize);
        return StreamSupport.doubleStream
            (new RandomDoublesSpliterator
             (0L, streamSize, Double.MAX_VALUE, 0.0),
             false);
    }
 
    public DoubleStream doubles() {
        return StreamSupport.doubleStream
            (new RandomDoublesSpliterator
             (0L, Long.MAX_VALUE, Double.MAX_VALUE, 0.0),
             false);
    }
 
 
    public DoubleStream doubles(long streamSize, double randomNumberOrigin,
                                double randomNumberBound) {
        if (streamSize < 0L)
            throw new IllegalArgumentException(BadSize);
        if (!(randomNumberOrigin < randomNumberBound))
            throw new IllegalArgumentException(BadRange);
        return StreamSupport.doubleStream
            (new RandomDoublesSpliterator
             (0L, streamSize, randomNumberOrigin, randomNumberBound),
             false);
    }
 
    public DoubleStream doubles(double randomNumberOrigin, double randomNumberBound) {
        if (!(randomNumberOrigin < randomNumberBound))
            throw new IllegalArgumentException(BadRange);
        return StreamSupport.doubleStream
            (new RandomDoublesSpliterator
             (0L, Long.MAX_VALUE, randomNumberOrigin, randomNumberBound),
             false);
    }
 
    /**
     * 用于int流的Spliterator。我们将四个int版本多路复用到一个类中，
     * 方法是将一个小于原点的绑定视为无界，并将“infinite”视为等同于
     * Long.MAX_VALUE。对于分割，它使用标准的二除法。这个类的长版本
     * 和双版本除了类型之外是相同的。
     * ps://等学习stream再深入了解，这里当成一个支持类即可
     */
    static final class RandomIntsSpliterator implements Spliterator.OfInt {
        long index;
        final long fence;
        final int origin;
        final int bound;
        RandomIntsSpliterator(long index, long fence,
                              int origin, int bound) {
            this.index = index; this.fence = fence;
            this.origin = origin; this.bound = bound;
        }
 
        public RandomIntsSpliterator trySplit() {
            long i = index, m = (i + fence) >>> 1;
            return (m <= i) ? null :
                new RandomIntsSpliterator(i, index = m, origin, bound);
        }
 
        public long estimateSize() {
            return fence - index;
        }
 
        public int characteristics() {
            return (Spliterator.SIZED | Spliterator.SUBSIZED |
                    Spliterator.NONNULL | Spliterator.IMMUTABLE);
        }
 
        public boolean tryAdvance(IntConsumer consumer) {
            if (consumer == null) throw new NullPointerException();
            long i = index, f = fence;
            if (i < f) {
                consumer.accept(ThreadLocalRandom.current().internalNextInt(origin, bound));
                index = i + 1;
                return true;
            }
            return false;
        }
 
        public void forEachRemaining(IntConsumer consumer) {
            if (consumer == null) throw new NullPointerException();
            long i = index, f = fence;
            if (i < f) {
                index = f;
                int o = origin, b = bound;
                ThreadLocalRandom rng = ThreadLocalRandom.current();
                do {
                    consumer.accept(rng.internalNextInt(o, b));
                } while (++i < f);
            }
        }
    }
 
    /**
     * Spliterator for long streams.
     */
    static final class RandomLongsSpliterator implements Spliterator.OfLong {
        long index;
        final long fence;
        final long origin;
        final long bound;
        RandomLongsSpliterator(long index, long fence,
                               long origin, long bound) {
            this.index = index; this.fence = fence;
            this.origin = origin; this.bound = bound;
        }
 
        public RandomLongsSpliterator trySplit() {
            long i = index, m = (i + fence) >>> 1;
            return (m <= i) ? null :
                new RandomLongsSpliterator(i, index = m, origin, bound);
        }
 
        public long estimateSize() {
            return fence - index;
        }
 
        public int characteristics() {
            return (Spliterator.SIZED | Spliterator.SUBSIZED |
                    Spliterator.NONNULL | Spliterator.IMMUTABLE);
        }
 
        public boolean tryAdvance(LongConsumer consumer) {
            if (consumer == null) throw new NullPointerException();
            long i = index, f = fence;
            if (i < f) {
                consumer.accept(ThreadLocalRandom.current().internalNextLong(origin, bound));
                index = i + 1;
                return true;
            }
            return false;
        }
 
        public void forEachRemaining(LongConsumer consumer) {
            if (consumer == null) throw new NullPointerException();
            long i = index, f = fence;
            if (i < f) {
                index = f;
                long o = origin, b = bound;
                ThreadLocalRandom rng = ThreadLocalRandom.current();
                do {
                    consumer.accept(rng.internalNextLong(o, b));
                } while (++i < f);
            }
        }
 
    }
 
    /**
     * Spliterator for double streams.
     */
    static final class RandomDoublesSpliterator implements Spliterator.OfDouble {
        long index;
        final long fence;
        final double origin;
        final double bound;
        RandomDoublesSpliterator(long index, long fence,
                                 double origin, double bound) {
            this.index = index; this.fence = fence;
            this.origin = origin; this.bound = bound;
        }
 
        public RandomDoublesSpliterator trySplit() {
            long i = index, m = (i + fence) >>> 1;
            return (m <= i) ? null :
                new RandomDoublesSpliterator(i, index = m, origin, bound);
        }
 
        public long estimateSize() {
            return fence - index;
        }
 
        public int characteristics() {
            return (Spliterator.SIZED | Spliterator.SUBSIZED |
                    Spliterator.NONNULL | Spliterator.IMMUTABLE);
        }
 
        public boolean tryAdvance(DoubleConsumer consumer) {
            if (consumer == null) throw new NullPointerException();
            long i = index, f = fence;
            if (i < f) {
                consumer.accept(ThreadLocalRandom.current().internalNextDouble(origin, bound));
                index = i + 1;
                return true;
            }
            return false;
        }
 
        public void forEachRemaining(DoubleConsumer consumer) {
            if (consumer == null) throw new NullPointerException();
            long i = index, f = fence;
            if (i < f) {
                index = f;
                double o = origin, b = bound;
                ThreadLocalRandom rng = ThreadLocalRandom.current();
                do {
                    consumer.accept(rng.internalNextDouble(o, b));
                } while (++i < f);
            }
        }
    }
 
    /**
     * 探针是保存在当前线程中的，调用ThreadLocalRandom.current()初始化
     */
    static final int getProbe() {
        return UNSAFE.getInt(Thread.currentThread(), PROBE);
    }
 
    /**
     * 伪随机生成新探针值
     */
    static final int advanceProbe(int probe) {
        probe ^= probe << 13;   // xorshift
        probe ^= probe >>> 17;
        probe ^= probe << 5;
        UNSAFE.putInt(Thread.currentThread(), PROBE, probe);
        return probe;
    }
 
    /**
     * Returns the pseudo-randomly initialized or updated secondary seed.
     */
    static final int nextSecondarySeed() {
        int r;
        Thread t = Thread.currentThread();
        if ((r = UNSAFE.getInt(t, SECONDARY)) != 0) {
            r ^= r << 13;   // xorshift
            r ^= r >>> 17;
            r ^= r << 5;
        }
        else {
            localInit();
            if ((r = (int)UNSAFE.getLong(t, SEED)) == 0)
                r = 1; // avoid zero
        }
        UNSAFE.putInt(t, SECONDARY, r);
        return r;
    }
 
    // Serialization support
 
    private static final long serialVersionUID = -5851777807851030925L;
 
    /**
     * @serialField rnd long
     *              seed for random computations
     * @serialField initialized boolean
     *              always true
     */
    private static final ObjectStreamField[] serialPersistentFields = {
            new ObjectStreamField("rnd", long.class),
            new ObjectStreamField("initialized", boolean.class),
    };
 
    private void writeObject(java.io.ObjectOutputStream s)
        throws java.io.IOException {
 
        java.io.ObjectOutputStream.PutField fields = s.putFields();
        fields.put("rnd", UNSAFE.getLong(Thread.currentThread(), SEED));
        fields.put("initialized", true);
        s.writeFields();
    }
 
    private Object readResolve() {
        return current();
    }
 
    // Unsafe mechanics
    private static final sun.misc.Unsafe UNSAFE;
    private static final long SEED;
    private static final long PROBE;
    private static final long SECONDARY;
    static {
        try {
            UNSAFE = sun.misc.Unsafe.getUnsafe();
            Class<?> tk = Thread.class;
            SEED = UNSAFE.objectFieldOffset
                (tk.getDeclaredField("threadLocalRandomSeed"));
            PROBE = UNSAFE.objectFieldOffset
                (tk.getDeclaredField("threadLocalRandomProbe"));
            SECONDARY = UNSAFE.objectFieldOffset
                (tk.getDeclaredField("threadLocalRandomSecondarySeed"));
        } catch (Exception e) {
            throw new Error(e);
        }
    }
}
```
