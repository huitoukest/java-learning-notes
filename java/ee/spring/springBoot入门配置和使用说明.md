---
title: "springBoot入门配置和使用说明"
date: "2018-04-23 13:31:28"
categories: ["java EE SSHM"]
tags: ["springboot", "配置", "说明", "入门"]
---

# 简介
- 创建可以独立运行的 Spring 应用。
- 直接嵌入 Tomcat 或 Jetty 服务器，不需要部署 WAR 文件。
- 提供推荐的基础 POM 文件来简化 Apache Maven 配置。
- 尽可能的根据项目依赖来自动配置 Spring 框架。
- 提供可以直接在生产环境中使用的功能，如性能指标、应用信息和应用健康检查。
- 没有代码生成，也没有 XML 配置文件。

# 快速构建
可以通过[http://start.spring.io/](http://start.spring.io/)网站直接构建springboot基础框架.

# maven构建

## pom依赖
pom文件常见依赖
在springboot开发中,groupId都是org.springframework.boot
| 依赖artifactId | 说明 |
|-------------------|--------|
| spring-boot-starter  |  核心 POM，包含自动配置支持、日志库和对 YAML 配置文件的支持。|
| spring-boot-starter-amqp |   通过 spring-rabbit 支持 AMQP。|
| spring-boot-starter-aop  |  包含 spring-aop 和 AspectJ 来支持面向切面编程（AOP）。|
| spring-boot-starter-batch  |  支持 Spring Batch，包含 HSQLDB。|
| spring-boot-starter-data-jpa  |  包含 spring-data-jpa、spring-orm 和 Hibernate 来支持 JPA。|
| spring-boot-starter-data-mongodb |   包含 spring-data-mongodb 来支持 MongoDB。|
| spring-boot-starter-data-rest  |  通过 spring-data-rest-webmvc 支持以 REST 方式暴露 Spring Data 仓库。|
| spring-boot-starter-jdbc |   支持使用 JDBC 访问数据库。|
| spring-boot-starter-security  |  包含 spring-security。|
| spring-boot-starter-test |   包含常用的测试所需的依赖，如 JUnit、Hamcrest、Mockito 和 spring-test 等。|
| spring-boot-starter-velocity |   支持使用 Velocity 作为模板引擎。|
| spring-boot-starter-web |   支持 Web 应用开发，包含 Tomcat 和 spring-mvc。|
| spring-boot-starter-websocket  |  支持使用 Tomcat 开发 WebSocket 应用。|
| spring-boot-starter-ws  |  支持 Spring Web Services。|
| spring-boot-starter-actuator  |  添加适用于生产环境的功能，如性能指标和监测等功能。|
| spring-boot-starter-remote-shell  |  添加远程 SSH 支持。|
| spring-boot-starter-jetty |   使用 Jetty 而不是默认的 Tomcat 作为应用服务器。|
| spring-boot-starter-log4j  |  添加 Log4j 的支持。|
| spring-boot-starter-logging  |  使用 Spring Boot 默认的日志框架 Logback。|
| spring-boot-starter-tomcat  |  使用 Spring Boot 默认的 Tomcat 作为应用服务器。|

## kotlin开发
kotlin开发pom.xml示例文件
```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <groupId>com.tingfeng</groupId>
    <artifactId>springboottest</artifactId>
    <version>1.0-SNAPSHOT</version>

    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>1.5.8.RELEASE</version>
        <relativePath/>
        <!--  lookup parent from repository  -->
    </parent>
    <properties>
        <kotlin.compiler.incremental>true</kotlin.compiler.incremental>
        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
        <project.reporting.outputEncoding>UTF-8</project.reporting.outputEncoding>
        <java.version>1.8</java.version>
        <kotlin.version>1.1.51</kotlin.version>
        <mysql.version>5.1.38</mysql.version>
        <druid.version>1.1.3</druid.version>
    </properties>
    <dependencies>
        <dependency>
            <groupId>com.alibaba</groupId>
            <artifactId>druid-spring-boot-starter</artifactId>
            <version>${druid.version}</version>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-data-jpa</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-test</artifactId>
            <scope>test</scope>
        </dependency>
        <dependency>
            <groupId>org.jetbrains.kotlin</groupId>
            <artifactId>kotlin-stdlib-jre8</artifactId>
            <version>${kotlin.version}</version>
        </dependency>
        <dependency>
            <groupId>org.jetbrains.kotlin</groupId>
            <artifactId>kotlin-reflect</artifactId>
            <version>${kotlin.version}</version>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-test</artifactId>
            <scope>test</scope>
        </dependency>
        <dependency>
            <groupId>mysql</groupId>
            <artifactId>mysql-connector-java</artifactId>
            <version>${mysql.version}</version>
        </dependency>
    </dependencies>
    <build>
        <sourceDirectory>${project.basedir}/src/main/java</sourceDirectory>
        <testSourceDirectory>${project.basedir}/src/test/java</testSourceDirectory>
        <plugins>
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
            </plugin>
            <plugin>
                <artifactId>kotlin-maven-plugin</artifactId>
                <groupId>org.jetbrains.kotlin</groupId>
                <version>${kotlin.version}</version>
                <configuration>
                    <compilerPlugins>
                        <plugin>spring</plugin>
                    </compilerPlugins>
                    <jvmTarget>1.8</jvmTarget>
                </configuration>
                <executions>
                    <execution>
                        <id>compile</id>
                        <phase>compile</phase>
                        <goals>
                            <goal>compile</goal>
                        </goals>
                    </execution>
                    <execution>
                        <id>test-compile</id>
                        <phase>test-compile</phase>
                        <goals>
                            <goal>test-compile</goal>
                        </goals>
                    </execution>
                </executions>
                <dependencies>
                    <dependency>
                        <groupId>org.jetbrains.kotlin</groupId>
                        <artifactId>kotlin-maven-allopen</artifactId>
                        <version>${kotlin.version}</version>
                    </dependency>
                </dependencies>
            </plugin>
        </plugins>
    </build>
</project>
```

# 热部署
devtools
```xml
<dependency>
      <groupId>org.springframework.boot</groupId>
      <artifactId>spring-boot-devtools</artifactId>
      <scope>provided</scope>
      <!--optional我没弄明白，都说必须为true，但我测试true，false，不加都可以-->
      <optional>true</optional>
</dependency>
```
通过项目主程序入口启动即可，改动以后重新编译就好。

springloaded
Pom.xml中直接在spring-boot插件中添加依赖即可：
```xml
<plugin>
          <groupId>org.springframework.boot</groupId>
          <artifactId>spring-boot-maven-plugin</artifactId>
          <dependencies>
            <!-- spring热部署 -->
            <dependency>
              <groupId>org.springframework</groupId>
              <artifactId>springloaded</artifactId>
              <version>1.2.6.RELEASE</version>
            </dependency>
          </dependencies>
          <configuration>
            <mainClass>cn.springboot.Mainspringboot</mainClass>
          </configuration>
</plugin>
```
运行：

$ mvn clean spring-boot:run
改动后，编译即可实现热部署

这两种方式其实都是spring官网为了spring项目所推出的jar包，加之springBoot框架内嵌服务器的优势，
使得改动后的项目部署变得非常简单；当我使用以后这两种方法以后，
发现真正实现热部署的只是后者，前者只是实现了热启动而已，从控制台日志就可以看出来。

说明
项目使用maven管理:
第一种方式配置文件改动后不能触发热启动
第二种方式配置文件改动后不能触发热部署，会提示一下错误
2017-05-24 11:54:53.276 ERROR 12063 --- [Loader@18b4aac2] org.springsource.loaded.ReloadableType

# springboot配置优先级顺序
优先级从高到低顺序如下,命令行优先级最高.
1. 命令行参数。
通过 System.getProperties() 获取的 Java 系统参数。
2. 操作系统环境变量。
从 java:comp/env 得到的 JNDI 属性。
3. 通过 RandomValuePropertySource 生成的“random.*”属性。
4. 应用 Jar 文件之外的属性文件。
5. 应用 Jar 文件内部的属性文件。
6. 在应用配置 Java 类（包含“@Configuration”注解的 Java 类）中通过“@PropertySource”注解声明的属性文件。
7. 通过“SpringApplication.setDefaultProperties”声明的默认属性。

Spring Boot 的这个配置优先级看似复杂，其实是很合理的。
比如命令行参数的优先级被设置为最高。
这样的好处是可以在测试或生产环境中快速地修改配置参数值，而不需要重新打包和部署应用。

SpringApplication 类默认会把以“--”开头的命令行参数转化成应用中可以使用的配置参数，
如 “--name=Alex” 会设置配置参数 “name” 的值为 “Alex”。
如果不需要这个功能，可以通过 “SpringApplication.setAddCommandLineProperties(false)” 禁用解析命令行参数。

RandomValuePropertySource 可以用来生成测试所需要的各种不同类型的随机值，从而免去了在代码中生成的麻烦。RandomValuePropertySource 可以生成数字和字符串。数字的类型包含 int 和 long，可以限定数字的大小范围。
以“random.”作为前缀的配置属性名称由 RandomValuePropertySource 来生成，如代码
```java
//使用 RandomValuePropertySource 生成的配置属性
user.id=${random.value}
user.count=${random.int}
user.max=${random.long}
user.number=${random.int(100)}
user.range=${random.int[100, 1000]}
```

# springboot配置文件

## Profile-多环境配置
当应用程序需要部署到不同运行环境时，一些配置细节通常会有所不同，最简单的比如日志，
生产日志会将日志级别设置为WARN或更高级别，并将日志写入日志文件，
而开发的时候需要日志级别为DEBUG，日志输出到控制台即可。
Spring Boot的Profile就给我们提供了解决方案，命令带上参数就搞定。

在Spring Boot中多环境配置文件名需要满足`application-{profile}.properties`的格式，其中`{profile}`对应你的环境标识，比如：
- application-dev.properties：开发环境
- application-prod.properties：生产环境

想要使用对应的环境，只需要在application.properties中使用spring.profiles.active属性来设置，
值对应上面提到的{profile}，这里就是指dev、prod这2个。

当然你也可以用命令行启动的时候带上参数：
```shell
java - jar xxx.jar --spring.profiles.active=dev
```

除了可以用profile的配置文件来分区配置我们的环境变量，在代码里，
我们还可以直接用@Profile注解来进行配置，例如数据库配置，这里我们先定义一个接口:
分别定义俩个实现类来实现它
```java
//测试数据库
@Component
@Profile("testdb")
public class TestDBConnector implements DBConnector{
    @Override
    public void configure(){
        System.out.println("testdb");
    }
}

//生产数据库
@Component
@Profile("devdb")
public class DevDBConnector implements DBConnector{
    @Override
    public void configure(){
        System.out.println("devdb");
    }
}
```
通过在配置文件激活具体使用哪个实现类
spring.profiles.active=testdb
然后通过注入DBConnector(注入接口,spring自动选择实现类),就可以用了.
除了spring.profiles.active来激活一个或者多个profile之外，还可以用spring.profiles.include来叠加profile
```json
spring.profiles.active:testdb
spring.profiles.include:proddb,prodmq
```

## properties配置文件
属性文件是最常见的管理配置属性的方式。
Spring Boot 提供的 SpringApplication 类会搜索并加载 application.properties 文件来获取配置属性值。
SpringApplication 类会在下面位置搜索该文件。
1. 当前目录的“/config”子目录。
2. 当前目录。
3. classpath 中的“/config”包。
4. classpath
上面的顺序也表示了该位置上包含的属性文件的优先级。
优先级按照从高到低的顺序排列。
可以通过“spring.config.name”配置属性来指定不同的属性文件名称。
也可以通过“spring.config.location”来添加额外的属性文件的搜索路径。
如果应用中包含多个 profile，可以为每个 profile 定义各自的属性文件，按照“application-{profile}”来命名。
对于配置属性，可以在代码中通过“@Value”来使用，如代码所示。
```java
//通过“@Value”来使用配置属性
@RestController
@EnableAutoConfiguration
public class Application {
	@Value("${name}")
	private String name;
	
	@RequestMapping("/")
	String home() {
		return String.format("Hello %s!", name);
	}
}
//变量 name 的值来自配置属性中的“name”属性。
```

## YAML配置
相对于属性文件来说，YAML 是一个更好的配置文件格式。YAML 在 Ruby on Rails 中得到了很好的应用。
SpringApplication 类也提供了对 YAML 配置文件的支持，只需要添加对 SnakeYAML 的依赖即可。
application.yml 文件的示例。
```yaml
spring:
profiles: development
db:
url: jdbc:hsqldb:file:testdb
username: sa
password:
spring:
profiles: test
db:
url: jdbc:mysql://localhost/test
username: test
password: test
```
通过“@ConfigurationProperties(prefix="db")”注解，配置属性中以“db”为前缀的属性值会被自动绑
定到 Java 类中同名的域上，如 url 域的值会对应属性“db.url”的值。
只需要在应用的配置类中添加“@EnableConfigurationProperties”注解就可以启用该自动绑定功能。
```java
//使用 YAML 文件的 Java 类
@Component
@ConfigurationProperties(prefix="db")
public class DBSettings {
	private String url;
	private String username;
	private String password;
}
```
如果你使用的是1.5以前的版本，那么可以通过locations指定properties文件的位置.
但是1.5版本后就没有这个属性了，添加@Configuration和@PropertySource("classpath:test.properties")后才可以读取。
```java
@configrationProperties(prefix="db",locations="classpath:xxxx.properties")
```
yaml配置文件示例
```yaml
spring:
# 环境 dev|test|pro
profiles:
  active: dev
datasource:
  type: com.alibaba.druid.pool.DruidDataSource
  driver-class-name: com.mysql.jdbc.Driver
  url: jdbc:mysql://127.0.0.1:3306/springboot
  username: root
  password: root
http:
  multipart:
  max-file-size: 100MB
  max-request-size: 100MB
  enabled: true
  resources: # 指定静态资源的路径
      static-locations: classpath:/static/
     #cache-period，静态资源的缓存失效时间，此时间会在http response的时候
     #写入http response的head中让让浏览器按照此时间来缓存,秒，其优先级高于html网页中的设置的meta；
      cache-period: 600 
  redis:
      open: false  # 是否开启redis缓存  true开启  false关闭
      database: 0
      host: redis.open.renren.io
      port: 16379
      password:      # 密码（默认为空）
      timeout: 6000  # 连接超时时长（毫秒）
      pool:
          max-active: 1000  # 连接池最大连接数（使用负值表示没有限制）
          max-wait: -1      # 连接池最大阻塞等待时间（使用负值表示没有限制）
          max-idle: 10      # 连接池中的最大空闲连接
          min-idle: 5      # 连接池中的最小空闲连接
  devtools:
      restart:
          #热部署生效
        enabled: true
          #设置重启的目录
          #additional-paths: src/main/java
          #classpath目录下的WEB-INF文件夹内容修改不重启
        exclude: static/**,
jpa:
  hibernate:
      # 第一次简表create  后面用update
      #ddl-auto: create
      ddl-auto: update
      show-sql: true
  show-sql: true
  #base-package: com.tingfeng.dao
  #repository-impl-postfix: impl
  #entity-manager-factory-ref: entityManagerFactory
  #transaction-manager-ref: transactionManager
server:
  port: 8080
  connection-timeout: 5000
  context-path: /spring
  tomcat:
      uri-encoding: UTF-8
      max-threads: 1000
      min-spare-threads: 30
girl:
  cupSize: B
  age: 18
```
可以配置application-dev.yml / application-pro.yml /application-test.yml用于不同的环境.

## 静态资源/文件配置

- 默认资源映射

其中默认配置的 /** 映射到 /static （或/public、/resources、/META-INF/resources）
其中默认配置的 /webjars/** 映射到 classpath:/META-INF/resources/webjars/
PS：上面的 static、public、resources 等目录都在 classpath: 下面（如 src/main/resources/static）。

读取优先级顺序为：META/resources > resources > static > public

- 自定义资源映射

自定义目录
以增加 /myres/* 映射到 classpath:/myres/* 为例的代码处理为：
实现类继承 WebMvcConfigurerAdapter 并重写方法 addResourceHandlers

```java
package org.springboot.sample.config;

import org.springboot.sample.interceptor.MyInterceptor1;
import org.springboot.sample.interceptor.MyInterceptor2;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.InterceptorRegistry;
import org.springframework.web.servlet.config.annotation.ResourceHandlerRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurerAdapter;

@Configuration
public class MyWebAppConfigurer 
        extends WebMvcConfigurerAdapter {

    @Override
    public void addResourceHandlers(ResourceHandlerRegistry registry) {
        //可以针对具体的资源来设置不同的缓存时间
       //cache-period
        registry.addResourceHandler("/myres/**").addResourceLocations("classpath:/myres/");
        super.addResourceHandlers(registry);
    }

}
```
访问myres 文件夹中的fengjing.jpg 图片的地址为 http://localhost:8080/myres/fengjing.jpg
这样使用代码的方式自定义目录映射，并不影响Spring Boot的默认映射，可以同时使用。

如果我们将/myres/* 修改为 /* 与默认的相同时，则会覆盖系统的配置，可以多次使用 addResourceLocations 添加目录，优先级先添加的高于后添加的。
```java
registry.addResourceHandler("/**").addResourceLocations("classpath:/myres/").addResourceLocations("classpath:/static/");
```
其中 addResourceLocations 的参数是动参，可以这样写 addResourceLocations(“classpath:/img1/”, “classpath:/img2/”, “classpath:/img3/”);

- 使用外部目录
如果我们要指定一个绝对路径的文件夹（如 H:/myimgs/ ），则只需要使用 addResourceLocations 指定即可。
// 可以直接使用addResourceLocations 指定磁盘绝对路径，同样可以配置多个位置，***注意路径写法需要加上file:***
```java
registry.addResourceHandler("/myimgs/**").addResourceLocations("file:H:/myimgs/");
```

- 通过配置文件配置
上面是使用代码来定义静态资源的映射，其实Spring Boot也为我们提供了可以直接在 application.properties（或.yml）中配置的方法。
配置方法如下：

```java
# 默认值为 /**
spring.mvc.static-path-pattern=
# 默认值为 classpath:/META-INF/resources/,classpath:/resources/,classpath:/static/,classpath:/public/ 
spring.resources.static-locations=这里设置要指向的路径，多个使用英文逗号隔开，
```
使用 spring.mvc.static-path-pattern 可以重新定义pattern，如修改为 /myres/** ，则访问static 等目录下的fengjing.jpg文件应该为 http://localhost:8080/myres/fengjing.jpg ，修改之前为 http://localhost:8080/fengjing.jpg
使用 spring.resources.static-locations 可以重新定义 pattern 所指向的路径，支持 classpath: 和 file: （上面已经做过说明） 注意 spring.mvc.static-path-pattern 只可以定义一个，目前不支持多个逗号分割的方式。

- 页面中使用

上面几个例子中也已经说明了怎么访问静态资源，其实在页面中使用不管是jsp还是freemarker，并没有什么特殊之处，也我们平时开发web项目一样即可。
下面是我的index.jsp：
```jsp
<body>
    <img alt="读取默认配置中的图片" src="${pageContext.request.contextPath }/pic.jpg">
    <br/>
    <img alt="读取自定义配置myres中的图片" src="${pageContext.request.contextPath }/myres/fengjing.jpg">
</body>
```

- 使用webjars
先说一下什么是webjars？我们在Web开发中，前端页面中用了越来越多的JS或CSS，如jQuery等等，平时我们是将这些Web资源拷贝到Java的目录下，这种通过人工方式拷贝可能会产生版本误差，拷贝版本错误，前端页面就无法正确展示。
WebJars 就是为了解决这种问题衍生的，将这些Web前端资源打包成Java的Jar包，然后借助Maven这些依赖库的管理，保证这些Web资源版本唯一性。

WebJars 就是将js, css 等资源文件放到 classpath:/META-INF/resources/webjars/ 中，然后打包成jar 发布到maven仓库中。

简单应用

以jQuery为例，文件存放结构为：
```java
META-INF/resources/webjars/jquery/2.1.4/jquery.js
META-INF/resources/webjars/jquery/2.1.4/jquery.min.js
META-INF/resources/webjars/jquery/2.1.4/jquery.min.map
META-INF/resources/webjars/jquery/2.1.4/webjars-requirejs.js
```
Spring Boot 默认将 /webjars/** 映射到 classpath:/META-INF/resources/webjars/ ，结合我们上面讲到的访问资源的规则，便可以得知我们在JSP页面中引入jquery.js的方法为：
```java
<script type="text/javascript" src="${pageContext.request.contextPath }/webjars/jquery/2.1.4/jquery.js"></script>
```
想实现这样，我们只需要在pom.xml 文件中添加jquery的webjars 依赖即可，如下：
```xml
<dependency>
    <groupId>org.webjars</groupId>
    <artifactId>jquery</artifactId>
    <version>2.1.4</version>
</dependency>
```

- 版本号统一管理
但是我们实际开发中，可能会遇到升级版本号的情况，如果我们有100多个页面，几乎每个页面上都有按上面引入jquery.js 那么我们要把版本号更换为3.0.0，一个一个替换显然不是最好的办法。
如何来解决？按如下方法处理即可。

首先在pom.xml 中添加依赖：
```xml
<dependency>
    <groupId>org.webjars</groupId>
    <artifactId>webjars-locator</artifactId>
</dependency>
```

然后增加一个WebJarsController：

```java
package org.springboot.sample.controller;

import javax.servlet.http.HttpServletRequest;

import org.springframework.core.io.ClassPathResource;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseBody;
import org.springframework.web.servlet.HandlerMapping;
import org.webjars.WebJarAssetLocator;

/**
* 处理WebJars，自动读取版本号
*/
@Controller
public class WebJarsController {

    private final WebJarAssetLocator assetLocator = new WebJarAssetLocator();

    @ResponseBody
    @RequestMapping("/webjarslocator/{webjar}/**")
    public ResponseEntity<Object> locateWebjarAsset(@PathVariable String webjar, HttpServletRequest request) {
        try {
            String mvcPrefix = "/webjarslocator/" + webjar + "/"; // This prefix must match the mapping path!
            String mvcPath = (String) request.getAttribute(HandlerMapping.PATH_WITHIN_HANDLER_MAPPING_ATTRIBUTE);
            String fullPath = assetLocator.getFullPath(webjar, mvcPath.substring(mvcPrefix.length()));
            return new ResponseEntity<>(new ClassPathResource(fullPath), HttpStatus.OK);
        } catch (Exception e) {
            return new ResponseEntity<>(HttpStatus.NOT_FOUND);
        }
    }
}
```
最后在页面中使用的方式：
```java
<script type="text/javascript" src="${pageContext.request.contextPath }/webjarslocator/jquery/jquery.js"></script>
```

- 静态资源版本管理

Spring 默认提供了静态资源版本映射的支持。
当我们的资源内容发生改变时，由于浏览器缓存，用户本地的资源还是旧资源，为了防止这种情况发生导致的问题。我们可能会选择在资源文件后面加上参数“版本号”或其他方式。

使用版本号参数，如：
```java
<script type="text/javascript" src="${pageContext.request.contextPath }/js/common.js?v=1.0.1"></script>
```
使用这种方式，当我们文件修改后，手工修改版本号来达到URL文件不被浏览器缓存的目的。同样也存在很多文件都需要修改的问题。或者有的人会增加时间戳的方式，这样我认为是最不可取的，每次浏览器都要请求为服务器增加了不必要的压力。

然而Spring在解决这种问题方面，提供了2种解决方式。

* 资源名称md5方式 *
1. 修改 application.properties 配置文件（或.yml）
```java
spring.resources.chain.strategy.content.enabled=true
spring.resources.chain.strategy.content.paths=/**
```
所有 /** 请求的静态资源都会被处理。

创建 ResourceUrlProviderController 文件
package org.springboot.sample.config;
```java
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.ControllerAdvice;
import org.springframework.web.bind.annotation.ModelAttribute;
import org.springframework.web.servlet.resource.ResourceUrlProvider;

/**
* 处理静态资源URL
*/
@ControllerAdvice
public class ResourceUrlProviderController {

    @Autowired
    private ResourceUrlProvider resourceUrlProvider;

    @ModelAttribute("urls")
    public ResourceUrlProvider urls() {
        return this.resourceUrlProvider;
    }
}
```
在页面中使用的写法
```java
<script type="text/javascript" src="${pageContext.request.contextPath }${urls.getForLookupPath('/js/common.js') }"></script>
```
当我们访问页面后，HTML中实际生成的代码为：
```java
<script type="text/javascript" src="/myspringboot/js/common-c6b7da8fffc9be141b48c073e39c7340.js"></script>
```
其中 /myspringboot 为我这个项目的 contextPath

* 资源版本号方式 *
该方式本人觉得并无多大意义，也不做详细说明，这是对所有资源的统一版本控制，不像上面一个md5是针对文件的。
除了在 application.properties（或.yml）中的配置有所区别，页面使用和md5的一样。
```java
spring.resources.chain.strategy.fixed.enabled=true
spring.resources.chain.strategy.fixed.paths=/js/**,/v1.0.0/**
spring.resources.chain.strategy.fixed.version=v1.0.0
```
这样配置后，以上面 common.js 为例，实际页面中生成的HTML代码为：
```java
<script type="text/javascript" src="/myspringboot/v1.0.0/js/common.js"></script>
```
* md5与版本号方式的处理原理 *
页面中首先会调用urls.getForLookupPath方法，返回一个/v1.0.0/js/common.js或/css/common-c6b7da8fffc9be141b48c073e39c7340.js
然后浏览器发起请求。
当请求的地址为md5方式时，会尝试url中的文件名中是否包含-，如果包含会去掉后面这部分，然后去映射的目录（如/static/）查找/js/common.js文件，如果能找到就返回。

当请求的地址为版本号方式时，会在url中判断是否存在/v1.0.0 ，如果存在，则先从URL中把 /v1.0.0 去掉，然后再去映射目录查找对应文件，找到就返回。

静态资源配置摘录自：http://blog.csdn.net/catoop/article/details/50501706

# 日志相关
## logback
```xml
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
    <include resource="org/springframework/boot/logging/logback/base.xml" />
    <logger name="org.springframework.web" level="INFO"/>
    <logger name="org.springboot.sample" level="TRACE" />

    <!-- 开发、测试环境 -->
    <springProfile name="dev,test">
        <logger name="org.springframework.web" level="INFO"/>
        <logger name="org.springboot.sample" level="INFO" />
        <logger name="io.renren" level="DEBUG" />
    </springProfile>

    <!-- 生产环境 -->
    <springProfile name="pro">
        <logger name="org.springframework.web" level="ERROR"/>
        <logger name="org.springboot.sample" level="ERROR" />
        <logger name="io.renren" level="ERROR" />
    </springProfile>

</configuration>
```

# web开发

## HttpMessageConverter
Spring MVC 中使用 HttpMessageConverter 接口来在 HTTP 请求和响应之间进行消息格式的转换。
默认情况下已经通过 Jackson 支持 JSON 和通过 JAXB 支持 XML 格式。
可以通过创建自定义 HttpMessageConverters 的方式来添加其他的消息格式转换实现。

## 静态文件
默认情况下，Spring Boot 可以对 “/static”、“/public”、“/resources” 或 “/META-INF/resources” 目录下的静态文件提供支持。
同时 Spring Boot 还支持 Webjars。路径“/webjars/**”下的内容会由 webjar 格式的 Jar 包来提供。

# 运维支持Actuator
与开发和测试环境不同的是，当应用部署到生产环境时，需要各种运维相关的功能的支持，包括性能指标、运行信息和应用管理等。
所有这些功能都有很多技术和开源库可以实现。Spring Boot 对这些运维相关的功能进行了整合，形成了一个功能完备和可定制的功能集，称之为 Actuator。
只需要在 POM 文件中增加对 “org.springframe.boot:spring-boot-starter-actuator” 的依赖就可以添加 Actuator。
Actuator 在添加之后，会自动暴露一些 HTTP 服务来提供这些信息。这些 HTTP 服务的说明如表 。

| 名称 |    说明 |    是否包含敏感信息 |
|-------|---------| --------------------------|   
| autoconfig  |   显示 Spring Boot 自动配置的信息。|     是|
| beans  |   显示应用中包含的 Spring bean 的信息。|     是|
| configprops  |   显示应用中的配置参数的实际值。 |    是|
| dump  |   生成一个 thread dump。 |    是|
| env  |   显示从 ConfigurableEnvironment 得到的环境配置信息。|     是|
| health  |   显示应用的健康状态信息。  |   否|
| info |    显示应用的基本信息。 |    否|
| metrics  |   显示应用的性能指标。 |    是|
| mappings |    显示 Spring MVC 应用中通过“| |
| @RequestMapping”添加的路径映射。|     是|
| shutdown  |   关闭应用。 |    是|
| trace   |  显示应用相关的跟踪（trace）信息。|     是|
对于表中的每个服务，通过访问名称对应的 URL 就可以获取到相关的信息。
如访问“/info”就可以获取到 info 服务对应的信息。
服务是否包含敏感信息说明了该服务暴露出来的信息是否包含一些比较敏感的信息，从而确定是否需要添加相应的访问控制，而不是对所有人都公开。
所有的这些服务都是可以配置的，比如通过改变名称来改变相应的 URL。

## health 服务
Spring Boot 默认提供了对应用本身、关系数据库连接、MongoDB、Redis 和 Rabbit MQ 的健康状态的检测功能。
当应用中添加了 DataSource 类型的 bean 时，Spring Boot 会自动在 health 服务中暴露数据库连接的信息。
应用也可以提供自己的健康状态信息，如代码所示。
```java
//自定义 health 服务
@Component
public class AppHealthIndicator implements HealthIndicator {
    @Override
    public Health health() {
        return Health.up().build();
    }
}
``
应用只需要实现 org.springframework.boot.actuate.health.HealthIndicator 接口，并返回一个 org.springframework.boot.actuate.health.Health 对象，
就可以通过 health 服务来获取所暴露的信息。
```json
//health 服务返回的结果
{"status":"UP","app":{"status":"UP"},"db":{"status":"UP","database":"HSQL Database Engine","hello":1}}
```text

## info 服务
info 服务所暴露的信息是完全由应用来确定的。
应用中任何以“info.”开头的配置参数会被自动的由 info 服务来暴露。
只需要往 application.properties 中添加以“info.”开头的参数即可，如代码所示。
```property
info.app_name=My First Spring Boot Application
info.app_version=1.0.0
```text
当访问“/info”时，访问的 JSON 数据如代码所示。
```json
//Info 服务返回的结果
{"app_name":"My First Spring Boot Application","app_version":"1.0.0"}
```text

##  metrics 服务
当访问 metrics 服务时，可以看到 Spring Boot 通过 SystemPublicMetrics 默认提供的一些系统的性能参数值.
包括内存、CPU、Java 类加载和线程等的基本信息。
应用可以记录其他所需要的信息。Spring Boot 默认提供了两种类型的性能指标记录方式：gauge 和 counter。
gauge 用来记录单个绝对数值，counter 用来记录增量或减量值。
比如在一个 Web 应用中，可以用 counter 来记录当前在线的用户数量。
当用户登录时，把 counter 的值加 1；当用户退出时，把 counter 的值减 1。
```java
//自定义的 metrics 服务
@RestController
public class GreetingsController {
         @Autowired
private CounterService counterService;
@RequestMapping("/greet")
public String greet() {
    counterService.increment("myapp.greet.count");
    return "Hello!";
}
}
```text
在代码中添加了对 Spring Boot 提供的 CounterService 的依赖。
当 greet 方法被调用时，会把名称为“myapp.greet.count”的计数器的值加 1。
也就是当用户每次访问“/greet”时，该计算器就会被加 1。除了 CounterService 之外，还可以使用 GaugeService 来记录绝对值。

## 使用 JMX 进行管理
添加 Actuator 后所暴露的 HTTP 服务只能提供只读的信息。
如果需要对应用在运行时进行管理，则需要用到 JMX。
Spring Boot 默认提供了 JMX 管理的支持。只需要通过 JDK 自带的 JConsole 连接到应用的 JMX 服务器，就可以看到在域“org.springframework.boot”中 mbean。
可以通过 Spring 提供的 @ManagedResource、@ManagedAttribute 和 @ManagedOperation 注解来创建应用自己的 mbean。

# 运行和打包

## Spring Boot Maven plugin 配置说明
Spring Boot Maven plugin能够将Spring Boot应用打包为可执行的jar或war文件，然后以通常的方式运行Spring Boot应用。
Spring Boot Maven plugin的最新版本为2017.6.8发布的1.5.4.RELEASE，要求Java 8, Maven 3.2及以后。

Spring Boot Maven plugin的5个Goals
- spring-boot:repackage，默认goal。在mvn package之后，再次打包可执行的jar/war，同时保留mvn package生成的jar/war为.origin
- spring-boot:run，运行Spring Boot应用
- spring-boot:start，在mvn integration-test阶段，进行Spring Boot应用生命周期的管理
- spring-boot:stop，在mvn integration-test阶段，进行Spring Boot应用生命周期的管理
- spring-boot:build-info，生成Actuator使用的构建信息文件build-info.properties

mvn package spring-boot:repackage
Spring Boot Maven plugin的最主要goal就是repackage，其在Maven的package生命周期阶段，
能够**将mvn package生成的软件包，再次打包为可执行的软件包，并将mvn package生成的软件包重命名为*.original**。
基于上述配置，对一个生成Jar软件包的项目执行如下命令。
```shell
mvn package spring-boot:repackage  
```text
可以看到生成的两个jar文件，一个是*.jar，另一个是*.jar.original。
在执行上述命令的过程中，Maven首先在package阶段打包生成*.jar文件；
然后执行spring-boot:repackage重新打包，查找Manifest文件中配置的Main-Class属性，如下所示：

```
Manifest-Version: 1.0  
Implementation-Title: gs-consuming-rest  
Implementation-Version: 0.1.0  
Archiver-Version: Plexus Archiver  
Built-By: exihaxi  
Implementation-Vendor-Id: org.springframework  
Spring-Boot-Version: 1.5.3.RELEASE  
Implementation-Vendor: Pivotal Software, Inc.  
Main-Class: org.springframework.boot.loader.JarLauncher  
Start-Class: com.ericsson.ramltest.MyApplication  
Spring-Boot-Classes: BOOT-INF/classes/  
Spring-Boot-Lib: BOOT-INF/lib/  
Created-By: Apache Maven 3.5.0  
Build-Jdk: 1.8.0_131  
```text
注意，其中的Main-Class属性值为org.springframework.boot.loader.JarLauncher；
Start-Class属性值为com.ericsson.ramltest.MyApplication。

其中com.ericsson.ramltest.MyApplication类中定义了main()方法，是程序的入口。
通常，Spring Boot Maven plugin会在打包过程中自动为Manifest文件设置Main-Class属性，
事实上该属性还可以受Spring Boot Maven plugin的配置属性layout控制的，示例如下。
```xml
<plugin>  
<groupId>org.springframework.boot</groupId>  
<artifactId>spring-boot-maven-plugin</artifactId>  
<version>1.5.4.RELEASE</version>  
<configuration>  
    <mainClass>${start-class}</mainClass>  
    <layout>ZIP</layout>  
</configuration>  
<executions>  

```java
<execution>  
<goals>  
<goal>repackage</goal>  
</goals>  
</execution>  
```
</executions>  
</plugin>  
```text
注意，这里的layout属性值为ZIP。

***layout属性的值可以如下***

- JAR，即通常的可执行jar
 Main-Class: org.springframework.boot.loader.JarLauncher
 
- WAR，即通常的可执行war，需要的servlet容器依赖位于WEB-INF/lib-provided

- ZIP，即DIR，类似于JAR
Main-Class: org.springframework.boot.loader.PropertiesLauncher

- MODULE，将所有的依赖库打包（scope为provided的除外），但是不打包Spring Boot的任何Launcher。

- NONE，将所有的依赖库打包，但是不打包Spring Boot的任何Launcher。

如果省略Main-Class，只写layout，那么会自动使用默认的Main-Class。

4.integration-test（集成测试）阶段中的Spring Boot Maven plugin的start/stop
```xml
<properties>  
<it.skip>false</it.skip>  
</properties>  
<build>  
<plugins>  

```java
<plugin>  
<groupId>org.apache.maven.plugins</groupId>  
<artifactId>maven-failsafe-plugin</artifactId>  
<configuration>  
<skip>${it.skip}</skip>  
</configuration>  
</plugin>  
<plugin>  
<groupId>org.springframework.boot</groupId>  
<artifactId>spring-boot-maven-plugin</artifactId>  
<version>1.5.4.RELEASE</version>  
<executions>  
<execution>  
<id>pre-integration-test</id>  
<goals>  
<goal>start</goal>  
</goals>  
<configuration>  
<skip>${it.skip}</skip>  
</configuration>  
</execution>  
<execution>  
<id>post-integration-test</id>  
<goals>  
<goal>stop</goal>  
</goals>  
<configuration>  
<skip>${it.skip}</skip>  
</configuration>  
</execution>  
</executions>  
</plugin>  
```
</plugins>  
</build>  
```text
注意，it.skip变量用作是否跳过integration-test的标志位。
maven-failsafe-plugin用作integration-test的主要执行目标。
spring-boot-maven-plugin用以为integration-test提供支持。

执行integration-test的Maven命令如下：
mvn verify
或者
mvn verify -Dit.skip=false
```
## jar方式运行

```shell
java -jar xx.jar --server.port=8080
```

可以看出，命令行中连续的两个减号--就是对application.properties`中的属性值进行赋值的标识。
所以java -jar xx.jar --server.port=9090等价于在application.properties中添加属性server.port=9090。
实际上，Spring Boot应用程序有多种设置途径，Spring Boot能从多重属性源获得属性，
包括如下几种：
1. 根目录下的开发工具全局设置属性(当开发工具激活时为`~/.spring-boot-devtools.properties`)。
2. 测试中的@TestPropertySource注解。
3. 测试中的@SpringBootTest#properties注解特性。
4. 命令行参数
5. SPRING_APPLICATION_JSON中的属性(环境变量或系统属性中的内联JSON嵌入)。
6. ServletConfig初始化参数。
7. ServletContext初始化参数。
8. java:comp/env里的JNDI属性
9. JVM系统属性
10. 操作系统环境变量
11. 随机生成的带random.* 前缀的属性（在设置其他属性时，可以应用他们，比如${random.long}）
12. 应用程序以外的application.properties或者appliaction.yml文件
13. 打包在应用程序内的application.properties或者appliaction.yml文件
14. 通过@PropertySource标注的属性源
15. 默认属性(通过`SpringApplication.setDefaultProperties`指定).

这里列表按组优先级排序，也就是说，任何在高优先级属性源里设置的属性都会覆盖
低优先级的相同属性，列如我们上面提到的命令行属性就覆盖了application.properties的属性。

### 默认打包方式
默认会将源代码和依赖的代码打包到一个jar文件中。
```xml
<plugin>
         <groupId>org.springframework.boot</groupId>
         <artifactId>spring-boot-maven-plugin</artifactId>
         <configuration>
         <fork>true</fork>
         </configuration>
  </plugin>
```
使用maven命令 ： mvn package spring-boot:repackage
将会得到源代码包，和源代码与依赖的运行jar包。

### lib和运行jar分开打包的方式
使用maven命令：mvn package 打包。
maven配置文件如下：
```xml
<plugin>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-maven-plugin</artifactId>
        <configuration>
                    <fork>true</fork>
                    <layout>ZIP</layout>
                    <executable>true</executable>
                    <includes>
                        <include>
                            <groupId>nothing</groupId>
                            <artifactId>nothing</artifactId>
                        </include>
                    </includes>
           </configuration>
   </plugin>
```
然后使用命令：
```shell
java -Dloader.path="lib/" -jar ./har-merchant-manage.jar
```
运行，通过置顶lib依赖目录的方式运行。
在jar文件构建之后，我可以看到PropertiesLauncher被用于检查META-INF / MENIFEST中的Main-Class属性
现在，我可以运行该jar如下（在Windows中）：
```shell
java -D loader.path = file：///C：/My/External/Dir,MyApp-0.0.1-SNAPSHOT.jar -jar MyApp-0.0.1-SNAPSHOT.jar 
```
请注意，应用程序jar文件包含在loader.path中。
现在加载了C：\My\External\Dir\config中的application.properties文件。
对于非jar（扩展）文件（例如，静态html文件）也可以由jar访问，因为它位于加载器路径中。
其中java命令 -DXXX用于设置XXX属性值，说明：
```shell
-D<名称>=<值>
                  设置系统属性
```

# Annotation配置

## 入口Main方法
```kotlin
import org.springframework.boot.SpringApplication
import org.springframework.boot.autoconfigure.SpringBootApplication
import org.springframework.boot.autoconfigure.domain.EntityScan
import org.springframework.context.annotation.ComponentScan
import org.springframework.data.jpa.repository.config.EnableJpaRepositories
import org.springframework.transaction.annotation.EnableTransactionManagement

fun main(args: Array<String>){
    SpringApplication.run(AppMain::class.java, *args)
}

@ComponentScan(basePackages= arrayOf("com.tingfeng"))
@EnableJpaRepositories(basePackages= arrayOf("com.tingfeng.dao"))//dao层对应的包路径,使用jpa时需要配置
@EntityScan(basePackages = arrayOf("com.tingfeng.entity"))//entity对应的包路径,使用jpa时需要配置
@SpringBootApplication
@EnableTransactionManagement
class AppMain {
}
```

## JPA相关配置

### baseDao
baseDao只是一个接口,不需要实现类.
```kotlin
import com.tingfeng.Entity.BaseEntity
import org.springframework.data.jpa.repository.JpaRepository
import org.springframework.data.jpa.repository.JpaSpecificationExecutor
import org.springframework.data.repository.NoRepositoryBean

@NoRepositoryBean
interface BaseDao<T : BaseEntity, ID : java.io.Serializable>
    : JpaRepository<T, ID>, JpaSpecificationExecutor<T>
```

## Dao
其余的Dao接口继承BaseDao接口,即可以直接使用JPA功能.
spring jpa会自动构建Dao接口的实现类.

```kotlin
import com.tingfeng.Entity.Account
import org.springframework.stereotype.Repository

@Repository
 interface AccountDao:BaseDao<Account, Long> {

    fun findByName(name:String):List<Account>
}
```
## Entity
Entity的配置类似Hibernate中Entity
```kotlin
import javax.persistence.Entity
import javax.persistence.GeneratedValue
import javax.persistence.Id
import javax.persistence.Table

@Entity
@Table(name="account")
data class Account(@Id @GeneratedValue var id:Long?,
                   var name:String?,
                   var money:Double?
                   ) :BaseEntity() {
    constructor(): this(null,null,null){}
}
```

## webMVC注解配置
```java
@Configuration
@EnableWebMvc
@ComponentScan(
        basePackages = Constants.MVC_PACKAGE_PATH,
        useDefaultFilters = false,
        includeFilters = {@ComponentScan.Filter(type = FilterType.ANNOTATION, value = {Controller.class})}
)
public class MvcConfig extends WebMvcConfigurerAdapter {

    private static final String VIEW_PREFIX = "/";// 视图前缀
    private static final String VIEW_SUFFIX = ".jsp";// 视图后缀
    private static final String VIEW_CONTENT_TYPE = "text/html;charset=UTF-8";//视图的内容类型。
    
    //可以配置消息的格式Message Converters
    @Override
    public void configureMessageConverters(List<HttpMessageConverter<?>> converters) {
        Jackson2ObjectMapperBuilder builder = new Jackson2ObjectMapperBuilder()
                .indentOutput(true)
                .dateFormat(new SimpleDateFormat("yyyy-MM-dd"))
                .modulesToInstall(new ParameterNamesModule());
        converters.add(new MappingJackson2HttpMessageConverter(builder.build()));
        converters.add(new MappingJackson2XmlHttpMessageConverter(builder.xml().build()));
    }
    
    /**
     * 可以配置路径的匹配规则 
     */
    @Override
    public void configurePathMatch(PathMatchConfigurer configurer) {
        configurer
            .setUseSuffixPatternMatch(true)
            .setUseTrailingSlashMatch(false)
            .setUseRegisteredSuffixPatternMatch(true)
            .setPathMatcher(antPathMatcher())
            .setUrlPathHelper(urlPathHelper());
    }

    @Bean
    public UrlPathHelper urlPathHelper() {
        //...
    }

    @Bean
    public PathMatcher antPathMatcher() {
        //...
    }
        

    //等同于<mvc:default-servlet-handler/>，
    @Override
    public void configureDefaultServletHandling(DefaultServletHandlerConfigurer configurer) {
        configurer.enable();
        //configurer.enable("myCustomDefaultServlet");
    }

    @Override
    public void addResourceHandlers(ResourceHandlerRegistry registry) {
        registry.addResourceHandler("/resources/**").addResourceLocations("/public-resources/");
    }
    public void addInterceptors(InterceptorRegistry registry) {
        registry.addInterceptor(new LoginInterceptor()).addPathPatterns("/**").excludePathPatterns("token/login");
        super.addInterceptors(registry);
    }
    /**
     * 配置 视图解析器
     * @return
     */
    @Bean
    public ViewResolver viewResolver(){

        InternalResourceViewResolver resolver = new InternalResourceViewResolver();
        resolver.setCache(true);
        resolver.setPrefix(VIEW_PREFIX);
        resolver.setSuffix(VIEW_SUFFIX);
        resolver.setExposeContextBeansAsAttributes(true);
        resolver.setContentType(VIEW_CONTENT_TYPE);
        return resolver;
    }

    /**
     * 配置静态资源处理
     * @param configurer
     */
    @Override
    public void configureDefaultServletHandling(DefaultServletHandlerConfigurer configurer) {
        configurer.enable();
    }
```
也可以继承WebMvcConfigurationSupport类来配置。

两个类都是来自包org.springframework.web.servlet.config.annotation
两个类都可以实现配置mvc。两者都可以配置视图解析器以及静态资源等
说明：
WebMvcConfigurationSupport 与WebMvcConfigurerAdapter 都可以配MVC,
WebMvcConfigurationSupport 支持的自定义的配置更多更全，WebMvcConfigurerAdapter有的WebMvcConfigurationSupport 都有

添加的拦截器Interceptor必须继承HandlerInterceptor
```java
public class LoginInterceptor implements HandlerInterceptor 
```
spring-boot中的main类中的@EnableWebMvc注解等于扩展了WebMvcConfigurationSupport但
是没有重写任何方法。
配置的方式区别如下：

- @EnableWebMvc+extends WebMvcConfigurationAdapter
在扩展的类中重写父类的方法即可，这种方式会屏蔽springboot的@EnableAutoConfiguration中的设置
- extends WebMvcConfigurationSupport
在扩展的类中重写父类的方法即可，这种方式会屏蔽springboot的@EnableAutoConfiguration中的设置
- extends WebMvcConfigurationAdapter
在扩展的类中重写父类的方法即可，这种方式依旧使用springboot的@EnableAutoConfiguration中的设置

在WebMvcConfigurationSupport（@EnableWebMvc）和@EnableAutoConfiguration这
两种方式都有一些默认的设定 ,而WebMvcConfigurationAdapter则是一个abstract class

@EnableWebMvc
开启MVC配置，相当于
```xml
<?xml version="1.0" encoding="UTF-8"?>
<beans xmlns="http://www.springframework.org/schema/beans"
    xmlns:mvc="http://www.springframework.org/schema/mvc"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="
        http://www.springframework.org/schema/beans
        http://www.springframework.org/schema/beans/spring-beans.xsd
        http://www.springframework.org/schema/mvc
        http://www.springframework.org/schema/mvc/spring-mvc.xsd">

    <mvc:annotation-driven/>
</beans>
```

## 格式转换convert和formatter
分别使用ConverterRegistry和FormatterRegistry
使用注册工厂
```java
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.convert.converter.Converter;
import org.springframework.core.convert.converter.ConverterRegistry;
import javax.annotation.PostConstruct;
import java.util.Arrays;
import java.util.List;

@Configuration
public class MyConverterRegistry {
    @Autowired
    private ConverterRegistry converterRegistry;

    @PostConstruct
    public void init() {
        converterRegistry.addConverter(new StringToListConvert());
    }

    private static  class StringToListConvert implements Converter<String, List<String>> {
        @Override
        public List<String> convert(String source) {
            if (source == null) {
                return Arrays.asList();
            } else {
                String[] split = source.split(",");
                return Arrays.asList(split);
            }
        }
    }
}
```
```java
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Configuration;
import org.springframework.format.Formatter;
import org.springframework.format.FormatterRegistry;

import javax.annotation.PostConstruct;
import java.text.ParseException;
import java.util.List;
import java.util.Locale;

@Configuration
public class MyFormatterRegistry {

    @Autowired
    private FormatterRegistry formatterRegistry;

    @PostConstruct
    public void init() {
        formatterRegistry.addFormatter(new StringDateFormatter());
    }


    public static class StringDateFormatter implements Formatter<List> {
        //解析接口，根据Locale信息解析字符串到T类型的对象；

        @Override
        public List parse(String text, Locale locale) throws ParseException {
            return null;
        }

        //格式化显示接口，将T类型的对象根据Locale信息以某种格式进行打印显示（即返回字符串形式）；
        @Override
        public String print(List object, Locale locale) {
            return "我是格式化的日期";
        }
    }
}
```

WebMvcConfigurerAdapter
```java
import com.lf.web.convert.StringToListConvert;
import com.lf.web.formatter.StringDateFormatter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.annotation.Configuration;
import org.springframework.format.FormatterRegistry;
import org.springframework.web.servlet.ViewResolver;
import org.springframework.web.servlet.config.annotation.DefaultServletHandlerConfigurer;
import org.springframework.web.servlet.config.annotation.EnableWebMvc;
import org.springframework.web.servlet.config.annotation.ViewResolverRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurerAdapter;
import org.springframework.web.servlet.view.InternalResourceViewResolver;

@Configuration
@EnableWebMvc
@ComponentScan//组件扫描
public class WebConfig extends WebMvcConfigurerAdapter {

    @Override
    public void addFormatters(FormatterRegistry registry) {
        super.addFormatters(registry);
        registry.addFormatter(new StringDateFormatter());
        registry.addConverter(new StringToListConvert());
    }
}
```

xml的配置方式
```xml
<?xml version="1.0" encoding="UTF-8"?>
<beans xmlns="http://www.springframework.org/schema/beans"
    xmlns:mvc="http://www.springframework.org/schema/mvc"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="
        http://www.springframework.org/schema/beans
        http://www.springframework.org/schema/beans/spring-beans.xsd
        http://www.springframework.org/schema/mvc
        http://www.springframework.org/schema/mvc/spring-mvc.xsd">

    <mvc:annotation-driven conversion-service="conversionService"/>

    <bean id="conversionService" class="org.springframework.format.support.FormattingConversionServiceFactoryBean">
        <property name="converters">
            <set>
                <bean class="com.web.convert.StringToListConvert"/>
            </set>
        </property>
        <property name="formatters">
            <set>
                <bean class="com.web.formatter.StringDateFormatter"/>
            </set>
        </property>
        <property name="formatterRegistrars">
            <set>
                <bean class="com.web.formatter.StringDateFormatter"/>
            </set>
        </property>
    </bean>

</beans> 
```

## 自定义视图拦截解析器
```java
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.ViewResolver;
import org.springframework.web.servlet.view.JstlView;
import org.springframework.web.servlet.view.UrlBasedViewResolver;
import org.springframework.web.servlet.view.tiles2.TilesConfigurer;
import org.springframework.web.servlet.view.tiles2.TilesView;

@Configuration
public class ViewConfiguration {

    @Bean
    public ViewResolver urlBasedViewResolver() {
        UrlBasedViewResolver viewResolver;
        viewResolver = new UrlBasedViewResolver();
        viewResolver.setOrder(2);
        viewResolver.setPrefix(/WEB-INF/);
        viewResolver.setSuffix(.jsp);
        viewResolver.setViewClass(JstlView.class);
        // for debug envirment
        viewResolver.setCache(false);
        return viewResolver;
    }
    @Bean
    public ViewResolver tilesViewResolver() {
        UrlBasedViewResolver urlBasedViewResolver = new UrlBasedViewResolver();
        urlBasedViewResolver.setOrder(1);
        urlBasedViewResolver.setViewClass(TilesView.class);
        //urlBasedViewResolver.
        return urlBasedViewResolver;
    }
    @Bean
    public TilesConfigurer tilesConfigurer() {
        TilesConfigurer tilesConfigurer = new TilesConfigurer();
        tilesConfigurer.setDefinitions(new String[] { classpath:tiles.xml });
        return tilesConfigurer;
    }
} 
```

## web容器配置
实现WebApplicationInitializer 的作用类似于web.xml中对spring做的配置作用。
```java
import javax.servlet.MultipartConfigElement;
import javax.servlet.ServletContext;
import javax.servlet.ServletException;
import javax.servlet.ServletRegistration.Dynamic;

import org.springframework.web.WebApplicationInitializer;
import org.springframework.web.context.support.AnnotationConfigWebApplicationContext;
import org.springframework.web.servlet.DispatcherServlet;

/**
* 服务器启动入口类
*/
public class WebApplicationStartup implements WebApplicationInitializer {

  private static final String SERVLET_NAME = Spring-mvc;

  private static final long MAX_FILE_UPLOAD_SIZE = 1024 * 1024 * 5; // 5 Mb

  private static final int FILE_SIZE_THRESHOLD = 1024 * 1024; // After 1Mb

  private static final long MAX_REQUEST_SIZE = -1L; // No request size limit

  /**
  * 服务器启动调用此方法，在这里可以做配置 作用与web.xml中配置spring的一些
  础属性相同
  */
  @Override
  public void onStartup(ServletContext servletContext) throws ServletException {
    // 注册springMvc的servlet
    this.addServlet(servletContext);
    // 注册过滤器
    // servletContext.addFilter(arg0, arg1)
    // 注册监听器
    // servletContext.addListener(arg0);
  }

  /**
  * 注册Spring servlet
  *
  * @param servletContext
  */
  private void addServlet(ServletContext servletContext) {
    // 构建一个application context
    AnnotationConfigWebApplicationContext webContext = createWebContext(SpringMVC.class, ViewConfiguration.class);
    // 注册spring mvc 的 servlet
    Dynamic dynamic = servletContext.addServlet(SERVLET_NAME, new DispatcherServlet(webContext));
    // 添加springMVC 允许访问的Controller后缀
    dynamic.addMapping(*.html, *.ajax, *.css, *.js, *.gif, *.jpg, *.png);
    // 全部通过请用 “/”
    // dynamic.addMapping(/);
    dynamic.setLoadOnStartup(1);
    dynamic.setMultipartConfig(new MultipartConfigElement(null, MAX_FILE_UPLOAD_SIZE, MAX_REQUEST_SIZE, FILE_SIZE_THRESHOLD));
  }

  /**
  * 通过自定义的配置类来实例化一个Web Application Context
  *
  * @param annotatedClasses
  * @return
  */
  private AnnotationConfigWebApplicationContext createWebContext(Class<!--?-->... annotatedClasses) {
    AnnotationConfigWebApplicationContext webContext = new AnnotationConfigWebApplicationContext();
    webContext.register(annotatedClasses);

    return webContext;
  }
}
```

## 通用的bean配置方式
通过在类上加入注解@Configuration，spring会自动扫描此类，并读取相关的配置。
类中的方法用@Bean注释，并指定其名称，返回bean的实例，等同于xml文件中的bena单例配置。
可以有多个@Configuration注解的类，多个@Bean注释的方法。
```java
@Configuration
public class ShiroConfig {

    @Bean("sessionManager")
    public SessionManager sessionManager(){
        DefaultWebSessionManager sessionManager = new DefaultWebSessionManager();
        sessionManager.setSessionValidationSchedulerEnabled(true);
        sessionManager.setSessionIdCookieEnabled(true);
        return sessionManager;
    }

    @Bean("securityManager")
    public SecurityManager securityManager(OAuth2Realm oAuth2Realm, SessionManager sessionManager) {
        DefaultWebSecurityManager securityManager = new DefaultWebSecurityManager();
        securityManager.setRealm(oAuth2Realm);
        securityManager.setSessionManager(sessionManager);

        return securityManager;
    }

    @Bean("shiroFilter")
    public ShiroFilterFactoryBean shirFilter(SecurityManager securityManager) {
        ShiroFilterFactoryBean shiroFilter = new ShiroFilterFactoryBean();
        shiroFilter.setSecurityManager(securityManager);

        //oauth过滤
        Map<String, Filter> filters = new HashMap<>();
        filters.put("oauth2", new OAuth2Filter());
        shiroFilter.setFilters(filters);

        Map<String, String> filterMap = new LinkedHashMap<>();
        filterMap.put("/webjars/**", "anon");
        filterMap.put("/druid/**", "anon");
        filterMap.put("/app/**", "anon");
        filterMap.put("/sys/login", "anon");
        filterMap.put("/**/*.css", "anon");
        filterMap.put("/**/*.js", "anon");
        filterMap.put("/**/*.html", "anon");
        filterMap.put("/fonts/**", "anon");
        filterMap.put("/plugins/**", "anon");
        filterMap.put("/swagger/**", "anon");
        filterMap.put("/favicon.ico", "anon");
        filterMap.put("/captcha.jpg", "anon");
        filterMap.put("/", "anon");
        //filterMap.put("/**", "oauth2");
        filterMap.put("/**", "anon");
        shiroFilter.setFilterChainDefinitionMap(filterMap);

        return shiroFilter;
    }

    @Bean("lifecycleBeanPostProcessor")
    public LifecycleBeanPostProcessor lifecycleBeanPostProcessor() {
        return new LifecycleBeanPostProcessor();
    }

    @Bean
    public DefaultAdvisorAutoProxyCreator defaultAdvisorAutoProxyCreator() {
        DefaultAdvisorAutoProxyCreator proxyCreator = new DefaultAdvisorAutoProxyCreator();
        proxyCreator.setProxyTargetClass(true);
        return proxyCreator;
    }

    @Bean
    public AuthorizationAttributeSourceAdvisor authorizationAttributeSourceAdvisor(SecurityManager securityManager) {
        AuthorizationAttributeSourceAdvisor advisor = new AuthorizationAttributeSourceAdvisor();
        advisor.setSecurityManager(securityManager);
        return advisor;
    }
```

# Resource下资源文件读取
对于在Resource下的普通资源文件，如果采用war方式，那么可以采用传统的
读取classpath下的资源文件的方式来读取。
但是如果打成jar微服务包的形式，那么资源文件放在jar包中，读取的时候只能使用读取
jar包中的读取方式才能够获取到文件。
```java
/**
 * 读取流
 * @param inStream
 * @return 字节数组
 * @throws Exception
 */
public static byte[] readStream(InputStream inStream) throws Exception {
    ByteArrayOutputStream outSteam = new ByteArrayOutputStream();
    try {
        byte[] buffer = new byte[1024];
        int len = -1;
        while ((len = inStream.read(buffer)) != -1) {
            outSteam.write(buffer, 0, len);
        }
    }finally {
        if(null != outSteam) {
            outSteam.close();
        }
        if(null != inStream) {
            inStream.close();
        }
    }
    return outSteam.toByteArray();
}

//将Resource目录下的文件读取成为Input，支持读取jar包中的资源文件
public static InputStream getResourcesFileInputStream(String fileRelativePath){
    //获取容器资源解析器
    ResourcePatternResolver resolver = new PathMatchingResourcePatternResolver();
    try {
        //获取所有匹配的文件
        Resource[] resources = resolver.getResources(fileRelativePath);
        Resource resource = null;
        if(resources != null && resources.length > 0){
            resource = resources[0];
        }
        //获得文件流，因为在jar文件中，不能直接通过文件资源路径拿到文件，但是可以在jar包中拿到文件流
        InputStream stream = resource.getInputStream();
        return stream;
    } catch (IOException e) {
        logger.warn("读取文件流失败！" + e);
    }
    return null;
}

/**
 * 现采用普通的方式读取，不行的话就获取整个容器（jar包）中的资源文件
 * @param filePath 文件在Resource目录下的路径和文件名信息
 * @return
 */
public static String getResourceFileContent(String filePath, String charEncoding) throws Exception {
    String url = Thread.currentThread().getContextClassLoader().getResource(filePath).getFile();
    //String url = org.springframework.util.ResourceUtils.getURL("classpath:" + filePath).getFile();
    //InputStream inputStream = ClassLoader.getSystemResourceAsStream(filePath);
    File file = new File(url);
    InputStream inputStream = null;
    if(file.exists() && file.canRead()){
        inputStream = new FileInputStream(file);
    }else{
        inputStream = getResourcesFileInputStream(filePath);
    }
    byte[] bytes = readStream(inputStream);
    String content = new String(bytes,charEncoding);
    return content;
}

```

# 加入SpringCache

## 加入ehcache
- pom依赖加入
```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-cache</artifactId>
</dependency>
<dependency>
    <groupId>net.sf.ehcache</groupId>
    <artifactId>ehcache</artifactId>
</dependency>
```
加入ehcache的依赖和boot-starter-cache依赖后会，需要手动启用缓存，
启用后会自动使用ehcache为默认缓存。
单独配置config

```java
@Configuration
@EnableCaching
public class CachingConfig {
    @Bean
    public CacheManager cacheManager() {
        SimpleCacheManager cacheManager = new SimpleCacheManager();
        cacheManager.setCaches(Arrays.asList(new ConcurrentMapCache("sampleCache")));
        return cacheManager;
    }
}
```
等效xml配置：
```xml
<beans>
     <cache:annotation-driven/>
     <bean id="cacheManager" class="org.springframework.cache.support.SimpleCacheManager">
         <property name="caches">
             <set>
                 <bean class="org.springframework.cache.concurrent.ConcurrentMapCacheFactoryBean">
                     <property name="name" value="sampleCache"/>
                 </bean>
             </set>
         </property>
     </bean>
 </beans>
```

或者直接在SpringBootApplication上注解@EnableCaching
```java
@SpringBootApplication
@EnableCaching
public class Application {
    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }
}
```

- 配置ehcache
spring-boot在配置ehcache后，会默认读取Resources下的ehcache.xml配置文件：
```xml
<ehcache xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:noNamespaceSchemaLocation="http://ehcache.org/ehcache.xsd">

    <diskStore path="java.io.tmpdir"/>
    <!-- defaultCache 是CacheManager#addCacheIfAbsent(String cacheName)时使用 -->
    <defaultCache
            maxElementsInMemory="1000"
            eternal="false"
            timeToIdleSeconds="60"
            timeToLiveSeconds="60"
            overflowToDisk="false"/>

    <cache name="myCache"
           maxElementsOnDisk="20000"
           maxElementsInMemory="2000"
           eternal="true"
           overflowToDisk="true"
           diskPersistent="true"/>

    <cache name="users"
           maxEntriesLocalHeap="200"
           timeToLiveSeconds="30">
    </cache>

</ehcache>
```

- 使用
使用cache的注解中的key和condition等时用的SPEL表达式。
kotlin示例：
```kotlin
@RestController
@RequestMapping("/cache")
@CacheConfig(cacheNames= arrayOf("users")) //如果不配置cacheconfig，那么在cacheable中必须指定value
class CacheController{

    @RequestMapping("cached")
    @Cacheable(key="'cache_d'",condition ="true")
    fun cacheDefault():String{
        return getDateString()
    }

    @RequestMapping("cachem")
    @Cacheable(value = "myCache",key="'cache_m'",condition ="true")
    fun cachem():String{
        return getDateString()
    }

    fun getDateString():String{
        return SimpleDateFormat("yyyy-mm-dd HH:mm:ss.sss").format( Date())
    }
}
```

# 参考

- Spring boot 配置详解
https://www.cnblogs.com/zheting/p/6707036.html

- Spring boot入门
https://www.ibm.com/developerworks/cn/java/j-lo-spring-boot/

- Spring boot静态资源
https://blog.csdn.net/catoop/article/details/50501706
