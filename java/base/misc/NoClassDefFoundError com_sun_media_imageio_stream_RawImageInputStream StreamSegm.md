---
title: "NoClassDefFoundError com/sun/media/imageio/stream/RawImageInputStream StreamSegmentMapper ..."
date: "2018-02-08 15:27:53"
categories: ["j2se"]
tags: []
---

问题原因：此类是缺少java jai中的图像处理类，此类并且没有包含在标准的jdk中。   
解决方案：   
1.将运行环境改为jar试试，亲测jre1.7可用（jar7中是带有此类的）；   
2.手动下载jai_imageio-1.1.1.jar文件加入运行环境（或者用maven引入）;
