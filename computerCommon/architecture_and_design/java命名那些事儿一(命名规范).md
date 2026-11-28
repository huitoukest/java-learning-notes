---
title: "java命名那些事儿一(命名规范).md"
date: "2022-08-21 17:22:54"
categories: ["通用概念与算法与设计"]
tags: ["java", "jvm", "开发语言", "命名", "规范"]
---

程序界两大难题，缓存一致性与命名那些事儿。本文为命名规范整理；下文为命名单词速查，整理了一些常见的命名使用到的单词。
# 基本规范

- 标识符：标识符由任意顺序的大小写字母(a-z,A-Z),数字(0-9)下划线(_)和美元符号($)组成，标识符常用来给类、对象、变量、方法、接口、自定义数据类型等命名的。

- java关键字

注意：不能把java关键字作为标识符。 从java10 开始 var 关键字可用于局部变量修饰。

  - 用于数据类型

    boolean、byte、char、 double、 float、int、long、new、short、void、instanceof

  - 用于语句

    break、case、 catch、 continue、 default 、do、 else、 for、 if、return、switch、try、 while、 finally、 throw、this、 super

  - 用于修饰

    abstract、final、native、private、 protected、public、static、synchronized、transient、 volatile

  - 用于方法、类、接口、包和异常

    class、 extends、 implements、interface、 package、import、throws

  - 其它 future、 generic、 operator、 outer、rest、var 、goto、const、null

- 包名默认全部小写，单词之间以 点号隔开。

- 类名，默认为驼峰风格（**UpperCamelCase**），首字母大写

- 变量，默认为驼峰风格（**LowerCamelCase**），首字母小写

- 常量，默认为蛇形风格(**snake_case**), 字母全部大写，单字之间以下划线连接

# 优雅命名约定

## 好的命名

1. 见名知义，无歧义，适合环境
   - 名称需要准确表达其数据含义或者功能
   - 反例：
     - Long a = xxx；使用了无意义的名称
     - Long userIdList = xxx；具有歧义，类型为Long 即单个数据，但是名称使用List结尾
     - User对象中，具有开始讲话与停止讲话，定义为： startTalk() 与 stopSpeak() ；不适合环境；
2. 无冗余信息
   - 如果上下文中已经包含了限定/环境信息，则无需再次申明
   - 反例：
     - User对象中的成员变量 userId、 接口命名 IUserService (如果已经定义为接口，则没有必要使用前缀I表示类型)
3. 无类型编码
   - 不需要在名称中加入当前数据的类型信息，第二点细分
     -  正例： String mobile = xxx；
     - 反例： String mobileStr = xxx；
4. 团队开发时保持风格统一
   - 例如某种行为使用相同的单词开头，如查询数据库时若返回为单个内容，则使用 getOne作为方法名称开头，而不是直接使用get，则团队中成员风格 保持一致。
   - 约定大于不禁止
   - 反例：
     - 类似功能具有多种命名风格（应该统一约定一种风格，如都使用  getXXByXX 的风格）
       - getUserById
       - queryMobileById
       - takeAddressById
5. 支持检索
   - 命名，尤其是可能对外有输入输出交互的命名最好是**明确直接定义**的，而不是(动态)生成的或者通过上下文直接获取而使用的，没有直接定义的名称非常难以检索。

## 工程

- 一般为单词小写，中划线隔开；顺序为组织/个人/父项目标识(可省略)-功能命名
  - eg： commons-collections、spring-boot-actuator、druid

## 包

**结构**

- indi：多人完成，版权属于发起者
  - indi.发起者名.项目名.模块名*.*.\*
- pers ：独自完成，公开，版权主要属于个人。
  - pers.个人名.项目名.模块名*.*.*
- priv ： 独自完成，非公开，版权属于个人。
  - priv.个人名.项目名.模块名*.*.*
- team：团队项目指由团队发起，并由该团队开发的项目，版权属于该团队所有。
  - team.团队名.项目名.模块名*.*.*
- com：由个人/公司发起，版权由项目发起的个人/公司所有。
  - com.公司名.项目名.模块名*.*.*
- org: 机构/组织
  - org.公司名.项目名.模块名*.*.*

**功能**

一般是表示内部存放的子包、类的功能，按照功能命名即可。

如 util 包下为 xxxUtil.java 类。

## 类

- **抽象类**命名根据**好的命名**规则第二点，最好使用自身意义的名称，而不是在类的名称中带有额外的标记；抽象类与接口不同，抽象类使用时是用继承的方式，类似于模板模式，其中的抽象方法也应该是对象的固有行为，属性为固有特征（可以理解为少了某一个行为都不是当前这类对象了）；接口则是某一种公共的行为，是一种特征，这种行为更多特定的、扩展的行为，使用的是实现的方式，乃是辐射模式（可以理解为这个行为不影响当前对象的根本类别）；java中接口可以同时实现多个而抽象类只能继承一个。

三角形的定义：三角形(triangle)是由同一平面内不在同一直线上的三条线段‘首尾’顺次连接所组成的封闭图形。

  - 正例： Triangle（抽象类，三角形） ，Obtuse（钝角，接口）  、红色边（RedSide） ->  ObtuseRedSideTriangle（实现类，钝角红边三角形）

    ```java
    public class ObtuseRedSideTriangle extends Triangle implements Obtuse,RedSide { ... }
    ```

  - 综上，抽象类的命名最好直接使用其对象原有名称，不需要附加什么额外标志

    - 但是由于历史或者团队风格，或者希望在阅读时强调其抽象特性，则推荐使用 Abstract 或 Base 开头；尤其**推荐使用Abstract开头**  ， 其表达的意思更加明确，而且有很多Base开头的类并不是抽象类。

- **异常类**命名使用Exception结尾；异常类并没有特殊的关键字修复，所以其类型特征体现在了类的名称中。

```java
public class NoSuchMethodException extends RuntimeException {}
```

- **测试类**命名以它要测试的类的名称开始，以Test结尾

```java
public class AnnotationUtilsTest {}
```

- **工具类**
  - util = 通用工具，**只**包含静态方法的工具，通常为某一个数据类型、大类别的多个公共方法的封装
    - 也有jdk 中的 Arrays类这种以及spring中的StringUtils风格命名，考虑到类一般为单数且需要见名知义，所以推荐使用 xxxUtil方式命名类
  - tool = 结合**当前项目相关**的工具，**只**包含静态方法的工具
  - kit = 和tool类似；
  - helper = 含有成员变量与非静态方法的工具类，通常是某一个特定功能功能场景的相关工具；
    - 例如  StringTemplateRenderHelper = 字符串模板渲染的Helper, 整个类中所有的工具和方法都是完成 讲一个 字符串通过模板渲染的方式渲染为 类容；不同于util，例如StringUtil 是对所有字符串处理中，公共方法的封装，有很多对字符串的通用处理（而不是像Helper 是封装针对某一个特定功能的一些方法）
  - 结合面相对象的思想来看（继承、扩展、复用），工具类推荐使用普通类 + 单例的方式，其性能和静态方法差不多，甚至更好；但是从使用使用方便来看，使用静态方法更加方便，这种方式也是目前主流的方式；结合当前的实际情况与团队风格来考虑；
- **枚举**
  - 依据**好的命名-第二点**，枚举类名**不**建议带上 Enum 后缀。（这里和阿里巴巴规范建议的不同）
  - 枚举成员名称需要全大写，单词间用下划线隔开。
- **类名使用 UpperCamelCase 风格**
  - 以下情形例外： DO / BO / DTO / VO / AO / PO / UID 等
  - 正例： MarcoPolo / UserDO / XmlService / TcpUdpDeal / TaPromotion
  - 反例： macroPolo / UserDo / XMLService / TCPUDPDeal / TAPromotion
- **处理特定功能类**
  - 如Handler，Predicate，Validator    表示处理器，校验器，断言这些类工厂还有配套的方法名如handle，predicate，validate。
- **接口**
  -  对于一个抽象功能定义而不是具体对象时建议定义为接口；命名不需要在开头这接口加入I或者Inter标志，这样违反了DRY原则。
  - 建议使用抽象定义的名词或者形容词作为接口。
  - 默认类是可以实现多个接口的，或者说接口是可以被多继承的，接口是对一个具体行为的抽象，建议一个接口中只定义一个行为，这样方便复用也方便使用（尤其在使用lambda时）。

```java
public interface Playe { play(); }
public interface Mp3Reader { read(String filePath); }
public class Mp3Player implements Mp3Reader,Play{ xxx }
```

- 接口类中的**方法和属性不要加任何修饰符号**（public 也不要加）
  - 保持代码的简洁性，并加上有效的 Javadoc 注释。尽量不要在接口里定义变量，如果一定要定义变量，肯定是与接口方法相关，并且是整个应用的基础常量。
  - 正例： 接口方法签名 void commit();
    - 接口基础常量 String COMPANY = "alibaba";
  - 反例： 接口方法定义 public abstract void f();
    - 说明： JDK8 中接口允许有默认实现，那么这个 default 方法，是对所有实现类都有价值的默
      认实现
- 如果是形容能力的接口名称，取对应的形容词为接口名（通常是–able 的形式） 。
  - 正例： AbstractTranslator 实现 Translatable 接口

- 对于 Service 和 DAO 类，基于 SOA 的理念，暴露出来的服务一定是接口，内部的实现类用 Impl 的后缀与接口区别。
  - 正例： CacheServiceImpl 实现 CacheService 接口。

## 变量＆常量

- 方法名、参数名、成员变量、局部变量都统一使用 **lowerCamelCase **风格，必须遵从
**驼峰**形式。

  - 正例： localValue / getHttpMessage() / inputUserId
- **常量**命名全部大写，单词间用下划线隔开，力求语义表达完整清楚，不要嫌名字长。
  - 正例： MAX_STOCK_COUNT
  - 反例： MAX_COUNT

- 代码中的命名均不能以下划线或美元符号开始，也不能以下划线或美元符号结束。

- 反例： _name / __name / $name / name_ / name$ / name__

- **禁用**拼音与英文混合的方式，更不允许直接使用中文的方式

  - 如果确实***没有适合***的英语名称可以使用***纯拼音***，但是**尽量避免**使用拼音命名。

-  类型与中括号紧挨相连来表示数组
  - 正例： 定义整形数组 int[] arrayDemo;
  - 反例： 在 main 参数中，使用 String args[]来定义。

- POJO 类中布尔类型的变量，**都不要加 is 前缀**，否则部分框架解析会引起序列化错误。

  ```html
  反例： 定义为基本数据类型 Boolean isDeleted 的属性，它的方法也是 isDeleted()， RPC
  框架在反向解析的时候， “误以为” 对应的属性名称是 deleted，导致属性获取不到，进而抛
  出异常。
  ```

-   在 long 或者 Long 赋值时， 数值后使用**大写的 L**，不能是小写的 l，小写容易跟数字1 混淆，造成误解。

  - 说明： Long a = 2l; 写的是数字的 21，还是 Long 型的 2

- **不要使用一个常量类维护所有常量**， 要按常量功能进行归类，分开维护。

  - 说明： 大而全的常量类， 杂乱无章， 使用查找功能才能定位到修改的常量，不利于理解和维护。
  - 正例： 缓存相关常量放在类 CacheConsts 下； 系统配置相关常量放在类 ConfigConsts 下。

- **常量的复用**层次有五层：跨应用共享常量、应用内共享常量、子工程内共享常量、包内共享常量、类内共享常量。

```html
  1） 跨应用共享常量：放置在二方库中，通常是 client.jar 中的 constant 目录下。
  2） 应用内共享常量：放置在一方库中， 通常是子模块中的 constant 目录下。
      反例： 易懂变量也要统一定义成应用内共享常量，两位攻城师在两个类中分别定义了表示“是”的变量：
      类 A 中： public static final String YES = "yes";
      类 B 中： public static final String YES = "y";
      A.YES.equals(B.YES)，预期是 true，但实际返回为 false，导致线上问题。
  3） 子工程内部共享常量：即在当前子工程的 constant 目录下。
  4） 包内共享常量：即在当前包下单独的 constant 目录下。
  5） 类内共享常量：直接在类内部 private static final 定义。
```

- 临时变量/中间变量
  - 通常在处理一些数据时，尤其是lambda表达式中会有一系列的数据处理，此时我们只关心过程和结果，而不关心数据的类型时，则考虑使用此类变量
  - 在单个变量的时候，使用如it 、item、tmp 这些（在scala中通常使用下划线或者直接省略，java中不建议这样），其中it、item通常为当前函数式方法传入的参数、tmp通常为函数式方法中创建的一个临时对象；如果处理时有多个变量、或者有多层嵌套则建议**对每个都使用有意义的名称**以区分。

```java
示例 userList.stream().filter(it -> it.getUserName().length() > 1).collect(Collectors.toList())
```

## 方法

- 方法应该是一个动词，表示一种行为，需要明确表达方法的功能；
  - 反例： 在 getUserById(Long id) 方法中做更新数据库的操作， 则方法名称和功能不匹配，方法做了查询用户之外的操作。

- Service/DAO 层方法命名规约

```html
1） 获取单个对象的方法用 get 做前缀。
2） 获取多个对象的方法用 list 做前缀，复数形式结尾如： listObjects。
    对于分页查询，可以使用 page 作为前缀，表示分页查询，通常同时返回当前记录总数与当前页的 。
    对于搜索类模糊查询偶尔也使用 search/find作为前缀，但是考虑到其更多是一种获取对象的手段，不宜作为前缀。
3） 获取统计值的方法用 count 做前缀。
4） 插入的方法用 save/insert 做前缀。
5） 删除的方法用 remove/delete 做前缀。
6） 修改的方法用 update 做前缀。
```

- 方法的**名称尽量短且不重复**描述条件的情况下描述其功能，否则可以考虑命名不是特别具体而是结合注释与参数来作为一个整体来描述清除整个功能
  - **当参数达到4个或者以上时，建议优化-封装**参数到一个bean中

```java
反例：
    User getUserByNameAndEmailAndPhoneAndAddressAndCreatedTime(String name,String email,String phone,String address,Date createdTime);
正例：
    User getUserByPhone(String name,String phone);
    User getUser(String name,String email,String phone,String address,Date createdTime);
当参数达到4个或者以上时，建议优化-封装参数到一个bean中：
    User getUser(UserQueryParam userQueryParam);
public class UserQueryParam{
    private String name;
    private String email;
    private String phone;
    private String address;
    private Date createdTime;
    ......
}
```

## 其它

- 如果模块、 接口、类、方法使用了设计模式，在命名时需体现出具体模式。说明： 将设计模式体现在名字中，有利于阅读者快速理解架构设计理念。
  - 正例：
    - public class OrderFactory;
    - public class LoginProxy;
    - public class ResourceObserver;

- 领域模型命名规约

```html
1） 数据对象： xxxDO， xxxEntity，xxx 即为数据表名。
2） 数据传输对象： xxxDTO， xxx 为业务领域相关的名称。
3） 展示对象： xxxVO， xxx 一般为网页名称。
4） POJO 是 DO/DTO/BO/VO 的统称，禁止命名成 xxxPOJO。
```

# 参见

- 阿里巴巴 Java 开发手册 V1.4.0
