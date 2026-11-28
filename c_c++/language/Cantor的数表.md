---
title: "Cantor的数表"
date: "2013-03-16 15:42:30"
categories: ["c/c++语言"]
tags: ["c", "算法"]
---

```c
#include"stdio.h"
#include"stdlib.h"
int main()
{int i,n,k;
    k=1;
    scanf("%d",&n);
    for(i=0;n-i>0;i++)
    {n=n-i;
        k=-k;//纪录其排序的顺序
    }
    i=i-n+1;
    if(k<0)
    {int t=i;i=n;n=t;}
    printf("\n%d/%d\n",n,i);
    system("pause");
}

/*
#include"stdio.h"
#include"stdlib.h"
int main()
{int i,n,k;
    do{k=1;
        scanf("%d",&n);
        for(i=0;n-i>0;i++)
        {n=n-i;
            k=-k;//纪律其排序的顺序
            printf("n=%-2d/k=%-4d",n,i);
            if(k%5==0)
            printf("\n");
        }
        i=i-n+1;
        if(k<0)
        {int t=i;i=n;n=t;}
        printf("\n%d/%d\n",n,i);}
    while(getchar()!='n');
    system("pause");
}
*/
```
