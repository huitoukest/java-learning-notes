---
title: "ehcache2.x配置文件详解"
date: "2018-04-23 11:15:29"
categories: ["常用配置文件示例"]
tags: ["ehcache", "缓存", "配置", "入门教程"]
---

# 约定
一般ehcache的配置文件名称是ehcache-setting.xml
EHCache是一个非常轻量级的缓冲，是Hibernate的默认缓存。
同时ehcache应该说是java范围内使用最广泛的缓存。同时它也支持分布式缓存。
也提供了磁盘，内存的缓存存储。

# 示例
```xml
<?xml version="1.0" encoding="UTF-8"?>
<ehcache>
    <!-- 指定一个文件目录，当EhCache把数据写到硬盘上时，将把数据写到这个文件目录下 -->
    <diskStore path="java.io.tmpdir"/>
    <!-- 设定缓存的默认数据过期策略 -->
    <defaultCache
            maxElementsInMemory="10000"
            eternal="false"
            overflowToDisk="true"
            timeToIdleSeconds="10"
            timeToLiveSeconds="20"
            diskPersistent="false"
            diskSpoolBufferSizeMB="30"
            maxEntriesLocalDisk="10000000"
            diskExpiryThreadIntervalSeconds="120"
            memoryStoreEvictionPolicy="LRU">
            
             <persistence strategy="localTempSwap"/>
            diskExpiryThreadIntervalSeconds="120"/>
    <cache name="cacheTest"
        maxElementsInMemory="1000"
        eternal="false"
        overflowToDisk="true"
        timeToIdleSeconds="10"
        timeToLiveSeconds="20"/>
</ehcache>
```
ehcache的xsd
```xml
<ehcache xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:noNamespaceSchemaLocation="http://ehcache.org/ehcache.xsd">
    ...
</ehcache>
```
# 说明
- diskStore
diskStore元素：制定一个路径，当EHCache把数据写到硬盘上的时候，
会把数据写到该目录下。user.home - 用户主目录；user.dir - 用户当前工作目录；
java.io.tmpdir - 默认临时文件路径。

- defaultCache
设定缓存的默认数据过期策略。

- cache
设定具体的命名缓存的数据过期策略。

- name
缓存名称。通常为缓存对象的类名；

- maxElementsInMemory
设置基于内存的缓存可存放对象的最大数目；

- maxElementOnDisk
设置基于硬盘的缓存可存放对象的最大数目；

- eternal
如果为true，表示对象永远不会过期，此时会忽略tiemToldleSeconds和timeToLiveSeconds属性
默认为false。

- timeToldleSeconds
设置允许对象处于空闲状态的最长时间，以秒为单位。
当对象最近一次被访问后，如果处于空闲状态的时间超过了
timeToldleSeconds属性值，这个对象就会过期。
当对象过期，EHCache将把它从缓存中清空。只有当eternal属性为false.
该属性才有效。如果该属性的值为0，那么就表示该对象可以无限期地存于缓存中。
即缓存被创建后，最后一次访问时间到缓存失效之时，两者之间的间隔，单位为秒(s)

- timeToLiveSeconds
必须大于timeToldleSeconds属性，才有意义；
当对象自从被存放到缓存中后，如果处于缓存中的时间超过了 timeToLiveSeconds属性值,
这个对象就会过期，EHCache将把它从缓存中清除；
即缓存自创建日期起能够存活的最长时间，单位为秒(s)

- overflowToDisk
如果为true，表示当基于内存的缓存中的对象数目达到了maxElementsInMemory界限后
会把溢出的对象写到基于硬盘的缓存中。
注意，如果缓存的对象要写入到硬盘中的话，则该对象必须实现了Serializable接口才行（也就是序列化）；

- memoryStoreEvictionPolicy
缓存对象清除策略。
有三种：

 1. FIFO：first in first out
先进先出。

 2. LFU：Less Frequently Used
一直以来最少被使用策略，缓存元素有一个hit属性，hit(命中)值最小的将会被清除出缓存。

 3. LRU：least Recenly used
最近最少被使用，缓存的元素有一个时间戳，当缓存的容量满了，
而又需要腾出地方来缓存新的元素的时候，
那么现有缓存元素中时间戳离当前时间最远的元素将被清出缓存。

- diskSpoolBufferSizeMB
写入磁盘的缓冲区大小。
由于diskSpoolBufferSizeMB在内部实际是以字节为单位，
所以最大值是Integer的最大值即2047.99...M，反正不到2G。
所以如果配置的超过2G，将会导致diskSpoolBufferSizeMB为负数，
在put时ehcache误以为磁盘缓存队列已满，每次都执行都会阻塞。

- maxElementsOnDisk
在DiskStore(磁盘存储)中的最大对象数量，如为0，则没有限制

- diskPersistent
是否disk store在虚拟机启动时持久化。默认为false

- diskExpiryThreadIntervalSeconds
Ehcache后台线程专门做Ellment失效监测以及清除工作。
此值不宜设置过低，否则会导致清理线程占用大量CPU资源。
默认值是120秒。

- clearOnFlush
当调用flush()是否清除缓存，默认是。

- maxEntriesLocalHeap
堆内存中最大缓存对象数，0没有限制

# defaultCache说明
defaultCache是ehcache中系统自带的一个默认cache，
其name默认是"default" 并且，手动创建（或者读取使用）"default"的cache时会报错，
其作用是用于**在程序中创建新的cache时，可以使用defaultCache中的默认配置**。
即用addCache时会默认使用defaultcache中的配置.
**所以xml其余的cache配置不会继承defaultCache的配置**
```java
CacheManager.getInstance().getCache("default"); // returns null
```
```xml
private Cache addCache(String cacheName) {
    CacheConfiguration cacheConfiguration = getCacheManager().getConfiguration().getDefaultCacheConfiguration();
    cacheConfiguration.setName(cacheName);
    Cache newCache = new Cache(cacheConfiguration);
    getCacheManager().addCache(newCache);
    return newCache;
}
```

# 注意
参考  http://blog.sina.com.cn/s/blog_4adc4b090102vh1s.html
