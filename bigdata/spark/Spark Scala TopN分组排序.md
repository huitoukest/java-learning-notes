---
title: "Spark Scala TopN分组排序"
date: "2016-04-28 11:48:10"
categories: ["Spark相关"]
tags: ["scala", "Spark"]
---

注意：

groupBy和groupByKey是不同的，比如（A，1），（A，2）；使用groupBy之后结果是（A，（（A，1），（A，2）））；

使用groupByKey之后结果是：（A，（1,2））；关键区别就是合并之后是否会自动去掉key信息；

示例：

输入：

```scala
Spark 95
Hadoop 68
Flink 55
Spark 95
Hadoop 98
Flink 85
Kafka 67
Spark 85
Hadoop 98
Flink 82
Kafka 76
Spark 98
Kafka 70
Spark 87
Hadoop 91
```

代码：

```scala
object TopNSecond {
def main(args: Array[String]): Unit = {
val conf=new SparkConf().setAppName("TopNSecond by Scala").setMaster("local");
val sc=new SparkContext(conf);
val data=sc.textFile("D:/tmp/TopNSecond.txt",1);
val lines=data.map{ line => (line.split(" ")(0),line.split(" ")(1).toInt) };
val groups=lines.groupByKey();
val groupsSort=groups.map(tu=>{
val key=tu._1;
val values=tu._2;
val sortValues=values.toList.sortWith(_>_).take(4);
(key,sortValues);
});
groupsSort.sortBy(tu=>tu._1, false, 1).collect().foreach(value=>{
print(value._1);
value._2.foreach(v=>print("\t"+v));
println();
});
sc.stop();
}
}
```

默认是降序排列：

核心思想是相对分组内部排序，然后取前Ｎ个，然后对分组之间进行排序；

输出结果：

```scala
Spark	98	95	95	87
Kafka	76	70	67
Hadoop	98	98	91	68
Flink	85	82	55
```
