---
title: "java进阶笔记之数组分析"
date: "2018-05-04 10:51:28"
categories: ["j2se", "java进阶学习笔记"]
tags: ["java", "数组", "入门", "分析"]
---

# java中的数组是什么？
在我看来，java中的数组可以理解为是一个没有物理class类，
但是可实例化对象且有自己类型的一个对象，并且是Object的子类。
```text
或者说java中的数组除了没有对应的class文件和不可继承外，和别的java对象并无区别.
```
注意：

C语言中数组名确实代表数组首元素的地址。
但java中数组都是对象，数组名就代表这个数组对象，而不是它的首地址。
所以println(数组)时输出的是对象的类型和地址。

- 没有对应的物理class类
java中是没有的，但是一些其余的jvm语言，比如scala和kotlin上可以通过Array建立数组。

- 可实例化
可以用new的方式进行对象的实例化

- 实例化后的对象有特定类型
```java
public void testBoolean(){
    long n = 1;
    int[] a = new int[123];
    System.out.println(a.equals(n)); //false
    System.out.println(a.getClass()); //class [I
}
//但是这里是无法通过class [I 来new出一个数组的。
```
- 是Object的子类
```java
public void testArray01(){
    Object array ;
    int[] a = new int[123];
    array = a;
    System.out.println(array.getClass()); //class [I
    System.out.println(array.toString()); //[I@32a1bec0
}
```

# 数组的实例化方式
数组实质上是一个容器，而创建的时，以装载内容的类型加中括号的方式代表对应的数组类。
然后创建方式就和普通对象一样了，不过数组创建时必须指定容器大小：即数组长度，
或者通过直接初始化内容的方式让java自动算计其容器大小。
比如装载内容的类型是K，那么K数组的创建方式就是K[]  kObject = new K[123];

java同时提供一种兼容c/c++风格的数组创建方式，就是定义数组句柄/引用名称的时候，
可以把中括号放在名称的后面。
K  kObject[] = new K[123];

```java
@Test
public void testArrayCreate(){
    // 创建数组，如果在创建的同时不初始化数组则必须指定其大小
    int[] array0 = new int[3];

    // 创建数组时，不指定数组大小则必须在创建的同时初始化数组
    int[] array1 = new int[]{0,1,2};
    
    //创建时直接初始化
    int[] array3 = {1,2,3};

    int array4[] = new int[4];

}
```

注意：
**Java的数组只能以32位带符号整数int为长度和下标.**

现在Oracle的Java开发组也在积极考虑如何让数组类型能支持long的长度/下标，
而c#和c++这些虽然语法上支持long类型，但是实际上使用的是截断long高位而使用的低位的
值作为长度。

# 多维数组
java中可以建立多维数组，用中括号的数量来代表数组的维度。
```java
@Test
public void testArrayM(){
    //四维数组
    int num4[][][][] = {
            {
                {{0,1,2},{3,4,5,6}}
            },
            {
                {{7,8,9},{10,11,12,13,14}}
            }
    };
    //给数组里面数字赋值或替换
    //例如 :
    num4[1][0][0][0] = 111; // 赋值
    for (int i = 0; i < num4.length; i++) {
        for (int j = 0; j < num4[i].length; j++) {
            for (int k = 0; k < num4[i][j].length; k++) {
                for (int l = 0; l < num4[i][j][k].length; l++) {
                    System.out.print(" " + num4[i][j][k][l]);
                }
                System.out.println();
            }
        }
    }
}

```
输出结果如下：
```java
 0 1 2
 3 4 5 6
 111 8 9
 10 11 12 13 14
```

# 数组的类型
常见的数组其运行时的class如下：
```java
@Test
public void testArrayType(){
    System.out.println(new byte[0].getClass()); //class [B
    System.out.println(new Byte[0].getClass()); //class [Ljava.lang.Byte;
    System.out.println(new short[0].getClass()); //class [S
    System.out.println(new Short[0].getClass()); //class [Ljava.lang.Short;
    System.out.println(new int[0].getClass()); //class [I
    System.out.println(new Integer[0].getClass());//class [Ljava.lang.Integer;
    System.out.println(new long[0].getClass());//class [J
    System.out.println(new Long[0].getClass());//class [Ljava.lang.Long;
    System.out.println(new float[0].getClass());//class [F
    System.out.println(new Float[0].getClass());//class [Ljava.lang.Float;
    System.out.println(new double[0].getClass());//class [D
    System.out.println(new Double[0].getClass());//class [Ljava.lang.Double;
    System.out.println(new boolean[0].getClass());//class [Z
    System.out.println(new Boolean[0].getClass());//class [Ljava.lang.Boolean;
    System.out.println(new char[0].getClass());//class [C
    System.out.println(new Character[0].getClass());//class [Ljava.lang.Character;
    System.out.println(new String[0].getClass());//class [Ljava.lang.String;
    System.out.println(new TestArray[0].getClass()); //class [LTestArray;
}
```

# java数组是协变的
协变：如果A是B的子类，那么A[]是B[]的子类。
比如：
Number[] num = new Integer[10];
num[0] = 2.1;
这样的语句可以通过编译，而在运行时会错误。
因为java SE5之前还没有泛型，但很多代码迫切需要泛型来解决问题，所以为了达到类似效果，
数组被设计为接受协变，但数组记录有其对应的类型信息，所以为了安全还是会在运行时检查具体的类型。
数组的协变也是java多态的一种表现形式。

# 数组的拷贝

- 循环手动拷贝
速度很慢，但是可以自主把握是深度拷贝还是浅拷贝

- System.arraycopy
这个是系统提供的拷贝方式，属于浅拷贝）
对于非基本类型而言，它拷贝的是对象的引用。
对于数组而言，它是深拷贝，对于数组中每个引用对象而言是浅拷贝。
这个方法不是用java语言写的，而是底层用c或者c++实现的，因而速度会比较快。
public static native void arraycopy(Object src, int srcPos,Object dest, int destPos,int length);
通过源代码我们可以看到，关键字native说明它不是用java语言写的，而是调用其他语言的代码。

- Arrays.copyOf
调用了System.arraycopy，也是浅拷贝）
对于数组和寄出类型数组而言，它是深拷贝；对于数组中每个引用对象而言是浅拷贝。
```java
public static byte[] copyOfRange(byte[] original, int from, int to) {
   int newLength = to - from;
   if (newLength < 0)
       throw new IllegalArgumentException(from + " > " + to);
       byte[] copy = new byte[newLength];
       System.arraycopy(original, from, copy, 0,
              Math.min(original.length - from, newLength));
        return copy;
    }
```
```java
public void testClone(){
    Integer[] a = new Integer[10];
    a[0] = new Integer(555);
    //copyOf方法
    Integer[] copy = Arrays.copyOf(a, a.length * 2);
    System.out.println(a[0] == copy[0] ); //true
}
```

- Object.clone
clone()对于对象而言，它是深拷贝.
但是对于数组而言，它是深拷贝，对于数组中每个引用对象而言是浅拷贝。
调用clone时，确实会创建一个新的数组对象，但是因为数组中保存的对象引用仍然是
原数组中对象的引用，所以相当于浅拷贝。

# 常用工具java.util.Arrays
- public static int binarySearch(Object[] a, Object key)
用二分查找算法在给定数组中搜索给定值的对象(Byte,Int,double等)。
数组在调用前必须排序好的。
如果查找值包含在数组中，则返回搜索键的索引；否则返回 (-(插入点) - 1)。

- public static boolean equals(long[] a, long[] a2)
如果两个指定的 long 型数组彼此相等，则返回 true。
如果两个数组包含相同数量的元素，并且两个数组中的所有相应元素对都是相等的，则认为这两个数组是相等的。
换句话说，如果两个数组以相同顺序包含相同的元素，则两个数组是相等的。
同样的方法适用于所有的其他基本数据类型（Byte，short，Int等）。

- public static void fill(int[] a, int val)
将指定的 int 值分配给指定 int 型数组指定范围中的每个元素。
同样的方法适用于所有的其他基本数据类型（Byte，short，Int等）。

- public static void sort(Object[] a)
对指定对象数组根据其元素的自然顺序进行升序排列。
同样的方法适用于所有的其他基本数据类型（Byte，short，Int等）。
