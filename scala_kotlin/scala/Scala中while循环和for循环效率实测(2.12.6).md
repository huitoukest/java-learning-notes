---
title: "Scala中while循环和for循环效率实测(2.12.6)"
date: "2018-08-23 16:17:49"
categories: ["scalakotlin"]
tags: ["scala", "while", "for", "循环"]
---

# 代码

```scala
object LoopTest {

  def main(args: Array[String]): Unit = {
    val size = 10000000;
    printTime(whileTest(size))
    printTime(forTest(size))
  }

  def printTime(call : => Unit):Unit = {
    val startTime = System.currentTimeMillis()
    call
    println()
    println(s"use time : ${System.currentTimeMillis() - startTime}")
  }

  def whileTest(size: Int):Unit = {
      var s = 0
      var j = 0
      while ( s < size){
        s += 1
        j += 1
      }
      print(s"while s:$s")
  }

  def forTest(size: Int):Unit = {
    var s = 0
    for ( j <- 0 until  size){
        s += 1
    }
    print(s"for s:$s")
  }

}
```

# 结果
```scala
while s:10000000
use time : 351
for s:10000000
use time : 21
```
