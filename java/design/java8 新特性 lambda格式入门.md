---
title: "java8 新特性 lambda格式入门"
date: "2017-03-17 16:53:48"
categories: ["j2se"]
tags: ["lambda", "java新特性"]
---

废话不说，直接上代码，看注释

    import java.util.Arrays;
    import java.util.Collections;
    import java.util.Comparator;
    import java.util.List;
    import java.util.function.Consumer;

    /**
     *
     * lambda完整格式
     * (Type1 param1, Type2 param2, ..., TypeN paramN) -> {
          statment1;
          statment2;
          //.............
          return statmentM;
         }
     * @author huitoukest
     * @version 1.0
     *
     */
    public class Main {
        /**
         *
         * @param args
         */
        public static  void main(String[] args){

            Main main=new Main();
                 main.testLambda01();
                 main.testLambda02();
                 main.testLambda03();
        }
        //匿名类
        public void testLambda01(){
            Thread t2=new Thread(new Runnable() {

                @Override
                public void run() {
                    System.out.println("just test01!");
                }
            });
            t2.start();   
            //省略方法体格式
            Thread t1=new Thread(()->System.out.println("just test02!"));
            t1.start();        
        }

        //排序
        public void testLambda02(){
            List<String> list1=Arrays.asList("1a" ,"0ab"," c");
            list1.sort(new Comparator<String>() {
                @Override
                public int compare(String o1, String o2) {
                    return o1.compareTo(o2);
                }
            });       
            list1.forEach(new Consumer<String>(){
                @Override
                public void accept(String t) {
                    System.out.println(t);
                }});       
            List<String> list=Arrays.asList("b" ,"1","c");
            list.sort((a,b)->a.compareTo(b));
            //省略参数和方法体，自动匹配输入的参数
            list.forEach(System.out::println);
            //或者
            Collections.sort(list, (a,b)->a.compareTo(b));

        }

        /**
         * map映射与stream操作，可以把Stream当成一个高级版本的Iterator
         * 用户只要给出需要对其包含的元素执行什么操作，具体这些操作如何应用到每个元素上，就给Stream就好了！
         */

```java
public void testLambda03(){
List<String> list=Arrays.asList("b" ,"1","c","dd","2");
list.stream()
//省略参数类型，加入方法体
.filter((a)->{ if(a.length()<2) return true; return false;})
.map(a->a+"_")
.forEach((a)->System.out.println(a))
;       
System.out.println();
list.forEach((a)->System.out.println(a));
}
```

```java
//map和list之间的转换
public void java8Test0(){
String[] a = new String[]{"a", "b", "c","","   ",null};
Map<String,Integer> list = Stream.of(a)
.filter(item-> !CheckUtil.isNull(item) && item.trim().length() > 0)
.map(item-> {
MerPayType mp = new MerPayType();
mp.setPayNo(item);
mp.setId((int) (Math.random()*10000));
return  mp;
})
.collect(Collectors.toMap(MerPayType::getPayNo,MerPayType::getId));
Map<Integer,String> map  = list.entrySet().stream().collect(Collectors.toMap(item->item.getValue(),Map.Entry::getKey));
map.forEach((k,v)->System.out.println(k + "," + v));
```

            System.out.println(JSON.toJSONString(list));
        }
