---
title: "mysql DELIMITER 使用注意"
date: "2016-01-22 11:24:43"
categories: ["数据库"]
tags: ["mysql", "DELIMITER"]
---

DELIMITER可以简单的理解为mysql存储过程开始和结束的一个标志符号;

格式如下:

```sql
DELIMITER ;;
CREATE ......
END
;;
DELIMITER ;
```

注意:

在存储过程结尾的 DELIMITER ;之下,应该还有一个空行;不然mysql的执行可能会报错;
