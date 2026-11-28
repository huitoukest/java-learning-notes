---
title: "java进阶笔记之枚举Enum"
date: "2018-11-09 22:26:53"
categories: ["java EE SSHM", "java进阶学习笔记"]
tags: ["java", "枚举", "enum", "进阶笔记"]
---

# 简介
java.lang.Enum类是从jdk1.5开始诞生的。
枚举的的equals方法被重写为==方法，因为枚举实际上是"线程安全的单例模式"。
Enum是所有枚举类型的基类，当我们新建一个枚举类的时候，默认会继承Enum类。

# Enum源码简析
Enum的构造方法是protected的，并且我们无法直接调用，但是编译器会做出相关的响应。
```java
public abstract class Enum<E extends Enum<E>>
        implements Comparable<E>, Serializable {

    private final String name;
    public final String name() {
        return name;
    }
    //实际保存的枚举项从0开始的索引值
    private final int ordinal;
    public final int ordinal() {
        return ordinal;
    }
    protected Enum(String name, int ordinal) {
        this.name = name;
        this.ordinal = ordinal;
    }
    public String toString() {
        return name;
    }
    public final boolean equals(Object other) {
        return this==other;
    }
    public final int hashCode() {
        return super.hashCode();
    }

    protected final Object clone() throws CloneNotSupportedException {
        throw new CloneNotSupportedException();
    }
    public final int compareTo(E o) {
        Enum<?> other = (Enum<?>)o;
        Enum<E> self = this;
        if (self.getClass() != other.getClass() && // optimization
            self.getDeclaringClass() != other.getDeclaringClass())
            throw new ClassCastException();
        return self.ordinal - other.ordinal;
    }
    @SuppressWarnings("unchecked")
    public final Class<E> getDeclaringClass() {
        Class<?> clazz = getClass();
        Class<?> zuper = clazz.getSuperclass();
        return (zuper == Enum.class) ? (Class<E>)clazz : (Class<E>)zuper;
    }
    public static <T extends Enum<T>> T valueOf(Class<T> enumType,
                                                String name) {
        T result = enumType.enumConstantDirectory().get(name);
        if (result != null)
            return result;
        if (name == null)
            throw new NullPointerException("Name is null");
        throw new IllegalArgumentException(
            "No enum constant " + enumType.getCanonicalName() + "." + name);
    }
    /**
     * enum classes cannot have finalize methods.
     */
    protected final void finalize() { }
    private void readObject(ObjectInputStream in) throws IOException,
        ClassNotFoundException {
        throw new InvalidObjectException("can't deserialize enum");
    }

    private void readObjectNoData() throws ObjectStreamException {
        throw new InvalidObjectException("can't deserialize enum");
    }
}

```

## 使用Enum建立单例模式
**推荐使用Enum方式建立单例**
```java
public enum SingleTon{
        INSTANCE;
        public void myMethod(){
            System.out.println("123");
        }
    }
```
当然，也可以加入更复杂的逻辑：
```java
public  enum SingleTon{
        INSTANCE;
        private Object aaa;
        //JVM会保证同一个类下的同一枚举项的构造方法只调用一次
        SingleTon(){
            aaa = new Object();
        }
        public void myMethod(){
            System.out.println(aaa.toString());
        }
    }
```
Java规范中规定，每一个枚举类型极其定义的枚举变量在JVM中都是唯一的，因此在枚举类型的序列化和反序列化上，Java做了特殊的处理。
在序列化的时候Java仅仅是将枚举对象的name属性输出到结果中，反序列化的时候则是通过 java.lang.Enum 的 valueOf() 方法来根据名字查找枚举对象。
也就是说，以下面枚举为例，序列化的时候只将 INSTANCE这个名称输出，反序列化的时候再通过这个名称，查找对于的枚举类型，因此反序列化后的实例也会和之前被序列化的对象实例相同。

# 枚举的集合
java提供了两个枚举集合:EnumSet和EnumMap,这两个集合对于枚举的读写效率较高。
其中EnumSet表示元素必须是 某一个枚举的枚举项,而EnumMap表示Key值必须是某一枚举的枚举项,它们的效率 相对于其它Set和Map要高一些.

但是EnumSet中保存的枚举数量最好别超过64个,超过后效率会降低.
实际上EnumSet是一个抽象类,其具体实现有两个类:
EnumSet的实现类RegularEnumSet,JumboEnumSet：
RegularEnumSet源码:
```java
public boolean add(E e) {
        typeCheck(e);
        long oldElements = elements;
        elements |= (1L << ((Enum)e).ordinal());
        return elements != oldElements;
}
```
从Add方法的源码可以看出add方法实际只是对长整型数据element做了一个操作，也就是说EnumSet实际上将枚举值保存在一个长整型数据上。
每个枚举值占用一bit。而Long类型占用4个字节,64个二进制位.超过64个了就用EnumSet的另一个实现JumboEnumSet。

EnumSet的all方法会调用noneof方法,而noneof方法中会调用具体的实现类来返回EnumSet实例,在noneof中进行了返回的具体实例的类选择.
JumboEnumSet会在枚举数量大于64个的时候被调用,这时候:
其会先按照64个一组对内容拆分,然后再将每个组映射到一个Long类型数字的每个位.所以速度会比RegularEnumSet慢很多.
