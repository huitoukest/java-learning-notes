---
title: "Spark的join与cogroup简单示例"
date: "2016-04-08 17:19:47"
categories: ["Spark相关"]
tags: ["Spark", "大数据", "join", "cogroup"]
---

# 1.join

join就是把两个集合根据key,进行内容聚合;

         元组集合A:(1,"Spark"),(2,"Tachyon"),(3,"Hadoop")

元组集合B:(1,100),(2,95),(3,65)                                <!-- 原博客此处为本地占位图片，已忽略 -->

A join B的结果:(1,("Spark",100)),(3,("hadoop",65)),(2,("Tachyon",95))

# 2.cogroup

cogroup就是:

有两个元组Tuple的集合A与B,先对A组集合中key相同的value进行聚合,

                        然后对B组集合中key相同的value进行聚合,之后对A组与B组进行"join"操作;  

示例代码:

    public class CoGroup {

    	public static void main(String[] args) {
    			SparkConf conf=new SparkConf().setAppName("spark WordCount!").setMaster("local");
    			JavaSparkContext sContext=new JavaSparkContext(conf);
    			List<Tuple2<Integer,String>> namesList=Arrays.asList(
    					new Tuple2<Integer, String>(1,"Spark"),
    					new Tuple2<Integer, String>(3,"Tachyon"),
    					new Tuple2<Integer, String>(4,"Sqoop"),
    					new Tuple2<Integer, String>(2,"Hadoop"),
    					new Tuple2<Integer, String>(2,"Hadoop2")
    					);

    			List<Tuple2<Integer,Integer>> scoresList=Arrays.asList(
    					new Tuple2<Integer, Integer>(1,100),
    					new Tuple2<Integer, Integer>(3,70),
    					new Tuple2<Integer, Integer>(3,77),
    					new Tuple2<Integer, Integer>(2,90),
    					new Tuple2<Integer, Integer>(2,80)
    					);			
    			JavaPairRDD<Integer, String> names=sContext.parallelizePairs(namesList);
    			JavaPairRDD<Integer, Integer> scores=sContext.parallelizePairs(scoresList);
    			/**
    			 * <Integer> JavaPairRDD<Integer, Tuple2<Iterable<String>, Iterable<Integer>>>
    			 * org.apache.spark.api.java.JavaPairRDD.cogroup(JavaPairRDD<Integer, Integer> other)
    			 */

```java
			JavaPairRDD<Integer, Tuple2<Iterable<String>, Iterable<Integer>>> nameScores=names.cogroup(scores);			

			nameScores.foreach(new VoidFunction<Tuple2<Integer, Tuple2<Iterable<String>, Iterable<Integer>>>>() {
				private static final long serialVersionUID = 1L;
				int i=1;
				@Override
				public void call(
						Tuple2<Integer, Tuple2<Iterable<String>, Iterable<Integer>>> t)
						throws Exception {
						String string="ID:"+t._1+" , "+"Name:"+t._2._1+" , "+"Score:"+t._2._2;
						string+="     count:"+i;
						System.out.println(string);
						i++;
				}
			});

			sContext.close();
	}
}
```

示例结果:

```java
ID:4 , Name:[Sqoop] , Score:[]     count:1
ID:1 , Name:[Spark] , Score:[100]     count:2
ID:3 , Name:[Tachyon] , Score:[70, 77]     count:3
ID:2 , Name:[Hadoop, Hadoop2] , Score:[90, 80]     count:4
```
