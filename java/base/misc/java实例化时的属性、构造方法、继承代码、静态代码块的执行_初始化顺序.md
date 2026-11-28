---
title: "java实例化时的属性、构造方法、继承代码、静态代码块的执行/初始化顺序"
date: "2018-05-10 16:43:16"
categories: ["j2se"]
tags: ["java", "实例化", "初始化顺序", "静态代码块", "构造方法初始化顺序"]
---

# 示例
```java
import org.junit.Test;

public class ExtendsTest {

    static class A{
        {
            System.out.println("A_3:init block 1");
        }
        C c = new C("A");
        static {
            System.out.println("A_1:static block 1");
        }
        {
            System.out.println("A_5:init block 2");
        }

        public A(){
            System.out.println("A_6:i am a");
        }
    }
    static class C{
        public C(String tag){
            System.out.println("C:"+ tag +":i am c");
        }
    }
    static  class B  extends A{
        C c = new C("B1");
        {
            System.out.println("B_8:init block ");
        }
        C  c1 = new C("B2");
        static {
            System.out.println("B_2:static block");
        }
        C  c2 = new C("B3");
        {
            System.out.println("B_11:init block2");
        }

        public B(){
            System.out.println("B_13:consctruct");
        }

        {
            System.out.println("B_12:init block3");
        }
    }
    @Test
    public void test001(){
        new B();
    }
}
```
输出结果：
```java
A_1:static block 1
B_2:static block
A_3:init block 1
C:A:i am c
A_5:init block 2
A_6:i am a
C:B1:i am c
B_8:init block 
C:B2:i am c
C:B3:i am c
B_11:init block2
B_12:init block3
B_13:consctruct
```

# 执行顺序
1. 父类中的静态代码块，静态属性
2. 子类/当前类中的静态代码块，静态属性
3. 父类中的属性和初始化代码块(也叫构造代码块，先于构造方法执行)按照顺序执行
4. 父类构造方法
5. 子类/当前类中的初始化代码块和属性按照顺序执行
6. 子类/当前类的构造方法

注意： 1,2作为静态代码是在实例化之前就会执行的代码，且只会执行一次。
3,4,5,6步骤是实例化时候的顺序，且每一次实例化都会依次执行一次。
