---
title: "java进阶笔记之List"
date: "2018-04-24 17:35:54"
categories: ["j2se", "java进阶学习笔记"]
tags: ["java", "list", "linkedList", "ArrayList"]
---

# 简介
java的List类是一个接口，其继承自Collection接口。
List中的元素是有序的，且是可重复的。
List中只能存放引用类型。
而常用的有实现有：

-  ArrayList
线程不安全，底层是数组实现，查改快，增删慢。
默认容量10.
扩容机制：

 - 当 ArrayList 的元素个数小于 6 时，容量达到最大时，元素容量会扩增至 12；
 - 当 ArrayList 的元素个数大于等于 6 时，创建一个当前元素个数的1.5倍
(不同java版本可能扩容的倍数不同)的新数组。

然后将老数据复制到新数组。

- LinkedList
线程不安全，底层是链表实现，查改慢，增删快。
扩容机制：通过链表实时添加节点。
**注意：由于是链表操作，所以用索引操作，或者调用有索引参数的方法时，包括
使用contains方法，都会大幅度降低速度。所以大部分情况下，还是ArrayList的速度快。**

链表操作因为是动态分配内存，ArrayList中的数组是初始化分配内存，所以当ArrayList的初始容量
设置的足够大时，即便是增加操作也是ArrayList的速度将会更快。
而对于删除操作，链表只有删除头部数据的情况比较快，其余情况不一定不ArrayList快。

- Vector
线程安全，底层数组实现，查改快，增删慢。
默认容量10.
扩容机制：

 - 创建一个当前元素个数的2倍(不同java版本可能扩容的倍数不同)的新数组。

然后将老数据复制到新数组。
说明：Vector中的public方法都添加了synchronized关键字，以确保方法同步。
```java
int newCapacity = (capacityIncrement > 0) ?(oldCapacity + capacityIncrement) : (oldCapacity * 2); 
```

# 常用方法

- contains
List中的contains方法，实际是循环调用容器中元素的equals方法，所以如果需要自定义实现
容器中元素的equals方法。

- subList
List.subList(int fromIndex, int toIndex) 方法返回 List 在 fromIndex 与 toIndex 范围内的子集。
注意是左闭右开，[fromIndex,toIndex)。
注意：subList 返回的扔是 List 原来的引用，所以对subList中元素的操作会影响到原List中的元素：
```java
public List<E> subList(int start, int end) {
    if (start >= 0 && end <= size()) {
        if (start <= end) {
            if (this instanceof RandomAccess) {
                return new SubAbstractListRandomAccess<E>(this, start, end);
            }
            return new SubAbstractList<E>(this, start, end);
        }
        throw new IllegalArgumentException();
    }
    throw new IndexOutOfBoundsException();
}
```

SubAbstractListRandomAccess 最终也是继承 SubAbstractList,
SubAbstractList：
```java
    SubAbstractList(AbstractList<E> list, int start, int end) {
        fullList = list;
        modCount = fullList.modCount;
        offset = start;
        size = end - start;
    }
```

# 实战与性能

- List中的remove
remove方法可以接受int  index或者Object作为对象。
**注意：**
这里的int index并不会被自动装箱，所以移出的是索引。
如果需要溢出一个包装类型的对象，需要手动创建一个引用对象，而不是传入
基础数据类型让java自动装箱。

- ArrayList
ArrayList的初始容量：
如果不设定初始容量，而实际需求容量有太大，那么大部分的时间可能浪费在扩容上。
ArrayList的遍历:
选中数组形式的遍历比foreach循环效率更高(但是因为同样快，一般影响不大)。
```java
@Test
public void testArrayList(){
        long start = System.currentTimeMillis();      
     //如果不设定初始容量，而实际需求容量有太大，
     //那么大部分的时间可能浪费在扩容上。
        List<Integer> list = new ArrayList();
        for(int i = 0; i < 10000000 ;i++){
            list.add(i+1);
        }
        System.out.println("use time:" + (System.currentTimeMillis() - start) / 1000.0);
        System.out.println("list size:" + list.size());
        list.remove(0);//这里不会自动装箱，直接移除index是0的对象
        System.out.println("list size:" + list.get(0));
        list.remove(Integer.valueOf(0));//这里不会自动拆箱，直接移除值是0的Integer等值对象。
        System.out.println("list size:" + list.get(0));//因为没有内容是0的对象，所以输出2。
    start = System.currentTimeMillis();
    list = new ArrayList(100000);
    for(int i = 0; i < 10000000 ;i++){
        list.add(i+1);
    }
    System.out.println("use time:" + (System.currentTimeMillis() - start) / 1000.0);
}
```
输出结果：
```java
use time:4.195
list size:10000000
list size:2
list size:2
use time:0.458
```

两种循环比较：
```java
public void testArrayListRead(){
    long start = System.currentTimeMillis();
    List<Integer> list = new ArrayList(1000000);
    for(int i = 0; i < 10000000 ;i++){
        list.add(i+1);
    }
    System.out.println("use time:" + (System.currentTimeMillis() - start) / 1000.0);
    System.out.println("list size:" + list.size());
    start = System.currentTimeMillis();
    for(int i = 0; i < 10000000 ;i++){
        list.get(i);
    }
    System.out.println("use time:" + (System.currentTimeMillis() - start) / 1000.0);
    start = System.currentTimeMillis();
    for(Integer item:list){

    }
    System.out.println("use time:" + (System.currentTimeMillis() - start) / 1000.0);
}
```
```java
use time:4.212
list size:10000000
use time:0.005
use time:0.033
```

- LinkedList
LinkedList对增单纯的增加操作效率仍然不高。
对于链表实现的LinkedList而言，效率超级低。

```java
long start = System.currentTimeMillis();
List<Integer> linkedlist = new LinkedList<Integer>();
for(int i = 0; i < 1000000 ;i++){
    linkedlist.add(i+1);
}
System.out.println("use time:" + (System.currentTimeMillis() - start) / 1000.0);
System.out.println("list size:" + linkedlist.size());

start = System.currentTimeMillis();
//读取测试，数组的读取方式，对于链表实现的LinkedList而言，效率超级低
for(int i = 0; i < 100000 ;i++){
    linkedlist.get(i);
}
System.out.println("use time:" + (System.currentTimeMillis() - start) / 1000.0);

start = System.currentTimeMillis();
Iterator<Integer> iterator = linkedlist.iterator();
while (iterator.hasNext()){
    iterator.next();
}
System.out.println("use time:" + (System.currentTimeMillis() - start) / 1000.0);

start = System.currentTimeMillis();
List<Integer> arrayList = new ArrayList<Integer>(100000);
for(int i = 0; i < 1000000 ;i++){
    arrayList.add(i+1);
}
System.out.println("use time:" + (System.currentTimeMillis() - start) / 1000.0);

start = System.currentTimeMillis();
for(int i = 0; i < 1000000 ;i++){
    arrayList.get(i);
}

System.out.println("use time:" + (System.currentTimeMillis() - start) / 1000.0);

```

输出结果：
```java
use time:0.092
list size:1000000
use time:13.892
use time:0.014
use time:0.057
use time:0.008
```

- 同时增删测试
可以看到，只有头部删除，尾部增加这种操作LinkedList才有绝对优势，
其余操作大部分是ArrayList速度更快。

```java
@Test
public void addRemoveTest(){

    long start = System.currentTimeMillis();
    List<Integer> linkedlist = new LinkedList<Integer>();
    int size = 0;
    for(int i = 0; i < 100000 ;i++){
        if(i % 7 == 0 && i > 0) {
            linkedlist.remove(0); //use time:0.013
            //linkedlist.remove(Math.random() * size); //use time:2.118
            size --;
        }else{
            linkedlist.add(i);
            size ++;
        }
    }
    System.out.println("use time:" + (System.currentTimeMillis() - start) / 1000.0);
    start = System.currentTimeMillis();
    List<Integer> arrayList = new ArrayList<Integer>(10000);
    size = 0;
    for(int i = 0; i < 100000 ;i++){
        if(i % 7 == 0 && i > 0) {
            arrayList.remove(0);//use time:0.116
            //arrayList.remove(Math.random() * size);//use time:0.459
            size --;
        }else{
            arrayList.add(i);
            size ++;
        }
    }
    System.out.println("use time:" + (System.currentTimeMillis() - start) / 1000.0);

}
```

# List的复制
目前java.util.Collections.copy()，System.arraycopy()，list.addAll()等都是浅复制，即无法复制List容器中的对象。

- 深度复制
通过序列化可以深度复制。
```java

public static <T> List<T> deepCopy(List<T> src) throws IOException, ClassNotFoundException {
     
    ByteArrayOutputStream byteOut = new ByteArrayOutputStream();
    ObjectOutputStream out = new ObjectOutputStream(byteOut);
    out.writeObject(src);
   
    ByteArrayInputStream byteIn = new ByteArrayInputStream(byteOut.toByteArray());
    ObjectInputStream in = new ObjectInputStream(byteIn);
    @SuppressWarnings("unchecked")
    List<T> dest = (List<T>) in.readObject();
    return dest;
}  
```
