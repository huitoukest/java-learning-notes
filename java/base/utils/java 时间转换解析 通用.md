---
title: "java 时间转换解析 通用"
date: "2018-03-14 17:47:40"
categories: ["j2se"]
tags: ["java", "时间转换", "Date"]
---

# 简介
1. 去掉所有非数字字符
2. 按照固定17位格式补足剩余数据
3. 格式化输出

# 实现
```java
import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.Date;

import org.junit.Test;

public class DateTest {
    @Test
    public void getDateTest() {
        String test = "20180301000101999123555";
        System.out.println(getDate(test,null));
        test = "201803";
        System.out.println(getDate(test,null));
    }
    
    public Date getDate(String dateString,Date defaultValue) {
        Date date = defaultValue;
        SimpleDateFormat myFmt=new SimpleDateFormat("yyyyMMddHHmmssSSS");
        dateString = dateString.replaceAll("[^\\d]","");
        if(dateString.length() >= 4) {
            if(dateString.length() > 17) {
                dateString = dateString.substring(0,17);
            }
            StringBuilder sb = new StringBuilder(20);
            sb.append(dateString);
            for(int i = dateString.length() + 1; i < 18 ;i++) {
                if(i == 6 || i == 8) {
                    sb.append(1);
                }else {
                    sb.append(0);
                }
            }
            try {
                date = myFmt.parse(sb.toString());
            } catch (ParseException e) {
                e.printStackTrace();
            }
        }
        return date;
    }
    
}

```

## 输出

```java
Thu Mar 01 00:01:01 CST 2018
Thu Mar 01 00:00:00 CST 2018
```
