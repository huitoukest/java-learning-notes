---
title: "Scala快排List和Array数组效率实测"
date: "2018-08-25 20:58:23"
categories: ["scalakotlin"]
tags: ["排序", "scala", "快排"]
---

# 代码
```scala
package com.tingfeng.scala.test

import scala.annotation.tailrec
import scala.util.{Random, Sorting}

/**
  * 快速排序测试
  */
object SortTest {

  /**
    * 初始化一个数组，产生随机数字填充
    * @param size
    * @return
    */
  def initRandomList(size :Int):List[Int]={
    val random = new Random()
    def initList(size :Int,random: Random):List[Int] = size match {
      case 0 => Nil
      case 1 => List(random.nextInt())
      case s:Int =>
        val value = s / 2
        if( s % 2 == 0) {
          initList(value,random) ++ initList(value,random)
        }else{
          initList(value,random) ++ initList(value + 1,random)
        }
    }
    initList(size,random)
  }

  /**
    * 打印出使用的时间
    * @param call
    */
  def printTime(call : => Unit,tag: String = ""){
    val startTime = System.currentTimeMillis()
    println(tag)
    call
    println
    println(s"use time : ${System.currentTimeMillis() - startTime}\n")
  }

  /**
    * 交换数组中两个位置的值，经过测试这种按位与的方式比普通建立变量交换的效率更高
    * @param array
    * @param x
    * @param y
    */
  def swap(array: Array[Int],x:Int,y:Int):Unit ={
      val t = array(x) ^ array(y)
      array(x) = t ^ array(x)
      array(y) = t ^ array(y)
  }

  /**
    * 将传入的值直接返回,并且执行逻辑
    * @param call
    * @param any
    * @tparam A
    */
  def doThing[A<:Any](any: A,call: A => Unit):A = {
      call(any)
      any
  }

  /**
    * 打印列表
    */
  def printList[A<%Seq[Any]](seq:A,size :Int = 10):Unit={
    seq.splitAt(size)._1.foreach(it => print(s"$it,"))
  }

  def shuffleIntSeq(seq: Array[Int],size: Int):Unit={
      val random = new Random()
      val maxSize = size/2
      for(i <- 0 to maxSize){
          swap(seq,i,maxSize + random.nextInt(maxSize))
      }
  }

  def main(args: Array[String]): Unit = {
    val size = 5000000
    val printSize = 10
    val list = initRandomList(size)
    //打印出钱100个，和List快速排序的时间花费
    printTime(printList[List[Int]](qSortList(list),Math.min(10,size)),"qSortList")

    val array = list.toArray
    printTime(printList[Array[Int]](doThing[Array[Int]](array,Sorting.quickSort),Math.min(printSize,size)),"Sorting.quickSort")
    shuffleIntSeq(array,size)
    printTime(printList[Array[Int]](doThing[Array[Int]](array,qSortArray1),Math.min(printSize,size)),"qSortArray1")
    shuffleIntSeq(array,size)
    printTime(printList[Array[Int]](doThing[Array[Int]](array,qSortArray2),Math.min(printSize,size)),"qSortArray2")
    shuffleIntSeq(array,size)
    printTime(printList[Array[Int]](doThing[Array[Int]](array,qSortArray3),Math.min(printSize,size)),"qSortArray3")
    shuffleIntSeq(array,size)
    printTime(printList[Array[Int]](doThing[Array[Int]](array,qSortArray4),Math.min(printSize,size)),"qSortArray4")
  }


  /**
    * 对List快速排序
    * @param list
    * @return
    */
  def qSortList(list: List[Int]):List[Int] = list match {
    case Nil => Nil
    case head :: other =>
      val (left, right) = other.partition(_ < head)
      (qSortList(left) :+ head) ++ qSortList(right)
  }

  /**
    * 通过每次比较数组‘head’值与其余值的方式直接实现
    * 比‘head’小的值移动到其前，比‘head’大的移动到其之后
    * @param array
    */

  def qSortArray1(array: Array[Int]):Unit = {
    def sort(ay : Array[Int],start: Int,end: Int):Unit={
      if(start >= end) {
        return
      }
      val head = ay(start)
      var spliteIndex = start
      for (i <- start + 1 to end){
        if(ay(i) < head){
          swap(array,spliteIndex,i)
          spliteIndex += 1
        }
      }
      if(start != spliteIndex){
        sort(ay, start, spliteIndex)
      }
      if(start == spliteIndex){
        spliteIndex += 1
      }
      if(spliteIndex != end){
        sort(ay, spliteIndex, end)
      }
    }
    sort(array,0,array.size - 1)
  }

  /**
    * 将数据以中线拆分左右两部分，交换值，使得右边值比左边大，
    * 再以左或者右边交换的界限分为两部分做递归
    * @param array
    */
  def qSortArray2(array: Array[Int]) {
    def sort(l: Int, r: Int) {
      val pivot = array((l + r) / 2)
      var lv = l; var rv = r
      while (lv <= rv) {
        while (array(lv) < pivot) lv += 1
        while (array(rv) > pivot) rv -= 1
        if (lv <= rv) {
          swap(array,lv, rv)
          lv += 1
          rv -= 1
        }
      }
      if (l < rv) sort(l, rv)
      if (rv < r) sort(lv, r)
    }
    sort(0, array.length - 1)
  }

  /**
    * 系统自带的过滤函数,无法排序成功，因为filter返回的是引用
    * @param xs
    * @return
    */
  def qSortArray3(xs: Array[Int]): Array[Int] ={
    if (xs.length <= 1){
      xs
    }else {
      val pivot = xs(xs.length / 2)
      val left = xs filter (pivot > _)
      val cu = xs filter (pivot == _ )
      val right = xs filter (pivot < _ )
      Array.concat(
        qSortArray3(left),cu,qSortArray3(right))
    }
  }

  /**
    * 系统自带的分割函数,无法排序成功，因为partition返回的是引用，数据量大的时候会栈溢出失败
    * @param xs
    * @return
    */
  def qSortArray4(array: Array[Int]): Array[Int] ={
    if (array.length <= 1){
      array
    }else {
      val head = array(0)
      val (left,right) = array.tail partition  (_ < head )
      Array.concat(qSortArray4(left),Array(head),qSortArray4(right))
    }
  }
}

```

# 测试结果
```scala
qSortList
-2147483293,-2147483096,-2147481318,-2147480959,-2147479572,-2147479284,-2147478285,-2147477579,-2147476191,-2147475936,
use time : 28808

Sorting.quickSort
-2147483293,-2147483096,-2147481318,-2147480959,-2147479572,-2147479284,-2147478285,-2147477579,-2147476191,-2147475936,
use time : 773

qSortArray1
-2147483293,-2147483096,-2147481318,-2147480959,-2147479572,-2147479284,-2147478285,-2147477579,-2147476191,-2147475936,
use time : 1335

qSortArray2
-2147483293,-2147483096,-2147481318,-2147480959,-2147479572,-2147479284,-2147478285,-2147477579,-2147476191,-2147475936,
use time : 629

qSortArray3
508128328,554399267,876118465,968407914,1274954088,1550124974,296879812,2125832312,1874291320,965362519,
use time : 10617

qSortArray4
865409973,-645195021,-735017922,-1893119148,1838343395,1038029591,-560471115,-182627393,-228613831,220531987,
use time : 6904


Process finished with exit code 0

```

环境：版本Scala2.12.6 ， win10 ，ryzen5 1600 ， 8G
