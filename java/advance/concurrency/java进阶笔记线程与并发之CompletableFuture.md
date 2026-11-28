---
title: "java进阶笔记线程与并发之CompletableFuture.md"
date: "2020-04-05 22:36:38"
categories: ["java进阶学习笔记"]
tags: ["java", "线程与并发", "进阶笔记", "Completable", "多线程"]
---

@[TOC](java进阶笔记线程与并发之CompletableFuture.md)

# 简介

- 什么是CompletableFuture

  - CompletableFuture类实现了CompletionStage和Future接口，于java8中添加，主要加入了大量控制任务执行阶段的链式方法。

- 用法

  - 关于CompletableFuture的用法这里不再讲述（网上的说明已足够详细，不再重复写），可以见参考中的链接。

- 规则小结

  - CompletableFuture 中自带有几个静态方法，可以快速开始运行任务逻辑。

  - 一般方法末尾的 Executor executor表示可以自定义线程池用于执行异步任务，默认使用法人ForkJoinPool.commonPool()

  - 方法命名

    - 一般分为异步和同步两种，且方法名称异步以Async结尾，如runAsync，其它命名的一般为同步执行的方法；

    - thenRun、runXXX - 运行一个片段Runnable ，无返回值；then执行的方法有严格的先后顺序。

    - thenApply、supplyXXX - 有返回值的Supplier

    - xxxOf - 以另外的 CompletableFuture 为参数

    - thenAccept、accept - 接受Consumer来处理上一步的单个结果

    - thenCombin 起处理当前与传入CompletableFuture 的结果

    - xxxBoth 当前与传入的CompletableFuture 根据条件运行给定的Runnable，获取双方结果

    - xxxEither 当前与传入的CompletableFuture其中一个正常完成是运行给定的Runnable

    - whenComplete 任务完成时执行

    - thenCompose  将前一执行结果作为参数传入给定的CompletableFuture中

    - handle 类似thenApply，但是会同时处理异常

    - get、join - 获取执行结果；会阻塞当前线程；

      - join 默认不抛出异常，但是若CompletableFuture执行中抛出了异常，会最终在当前线程抛出

      - get 即Future的get，需要处理受检异常

# CompletableFuture 源码简析

由于其方法众多，但是大部分规律和处理逻辑都相似，这里对部分方法做一个简析.

## allOf / anyOf
返回一个新的CompletableFuture，当所有/其中一个给定的CompletableFutures完成时，完成

## thenAcceptXXX、acceptXXX

返回一个新的CompletionStage，当此阶段正常完成时，将以该阶段的结果作为提供的操作的参数执行。

PS：thenxxx表示有依赖上阶段，且上阶段执行正常。

## whenCompleteXXX

返回一个与此阶段相同结果或异常的新CompletionStage，当此阶段完成时，执行给定操作将使用此阶段的默认同步/异步执行工具执行给定操作

PS：thenxxx表示有依赖上阶段，且无论上阶段是否执行正常。

## xxxCompose

同时接收上一个阶段的结果（类型T），以及一个CompletionStage参数，并组合处理返回一个结果（类型T）

## handle

返回一个新的CompletionStage，当此阶段正常或异常完成时，将使用此阶段的结果和异常作为所提供函数的参数执行。

## GET、join

join与get不同，get表明却有返回值，而join则不用得到返回值。

# 思考
- 避免方法栈的调用层次过深，避免递归的过深的调用，一种方式是将之转换为有顺序依赖的线性调用。当然，尾递归也算一种方式：自动转为循环。
- 对外保留的可用方法是对异步业务逻辑的封装，然而实际实现则拆分的更细，通过抽取公共业务逻辑，实现公共抽象（具体是抽象在特定参数下的某种表现形式)；这里主要抽象为单个、聚合操作两种，并主要对聚合操作做了大量策略重写。

# 参考

CompletableFuture 详解 https://www.jianshu.com/p/6f3ee90ab7d3

Java并发编程(六) CompletableFuture与CompletionStage使用 https://my.oschina.net/JackieRiver/blog/2054472

【juc源码解析 CompletableFuture 】： https://www.cnblogs.com/aniao/p/aniao_cf.html
【ForkJoin框架之CompletableFuture】： https://segmentfault.com/a/1190000019484482
