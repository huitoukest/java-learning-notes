---
title: "异常解决：java.lang.IllegalStateException: Failed to introspect Class"
date: "2019-02-28 09:37:45"
categories: ["java EE SSHM"]
tags: ["UnsatisfiedDependencyException", "introspect", "AppClassLoader", "java", "ClassLoader"]
---

@[TOC](java.lang.IllegalStateException: Failed to introspect Class)
# 异常详情
Exception encountered during context initialization - cancelling refresh attempt: org.springframework.beans.factory.UnsatisfiedDependencyException: Error creating bean with name xxxxx

Lookup method resolution failed; nested exception is java.lang.IllegalStateException: Failed to introspect Class [classA] from ClassLoader [sun.misc.Launcher$AppClassLoader@14dad5dc]

# 原因
此异常原因是因为classA中使用了项目没有导入的类，从而导致类加载失败。一般来说如果使用了没有依赖的类应该会报ClassNotFindException的错误，但是如果只是导入却没有使用的使用可能就会报此错误。
通常此错误见与使用maven框架配置了第三方类的scope是provided的情况下。笔者在使用spring boot、maven时导致此错误。

# 解决办法
检查classA类中可能存在的没有依赖的类或者包，将之导入（或者加入maven依赖、或调整依赖的包中的依赖的scope），总之使其类加载器能够在当期classPath找到此类即可。
