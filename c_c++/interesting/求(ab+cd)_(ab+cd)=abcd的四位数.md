---
title: "求(ab+cd)*(ab+cd)=abcd的四位数"
date: "2013-04-16 15:52:34"
categories: ["c/c++语言", "c语言趣味百例精解"]
tags: ["c", "穷举"]
---

```c
//求(ab+cd)*(ab+cd)=abcd的四位数
#include"stdio.h"
#include"stdlib.h"
int main()
{int a,b;
    for(a=10;a<100;a++)
    for(b=0;b<100;b++)
    if(a*100+b==(a+b)*(a+b))
    printf("%d\n",a*100+b);
    system("pause");}
```

![](assets/8809453_01.png)
