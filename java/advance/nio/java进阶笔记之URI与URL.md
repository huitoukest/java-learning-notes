---
title: "java进阶笔记之URI与URL.md"
date: "2020-06-11 14:10:09"
categories: ["java进阶学习笔记"]
tags: ["进阶笔记", "URI", "URL", "URN"]
---

# 简介

URL 和URI无物理上的直接联系( 不是继承和实现 ).

- URL = Universal Resource Locator = 统一资定位符  ( jdk1.0出现)

  - 通过网络来定位和访问某资源的标识符.

  - 网络资源位置通常包括用于访问服务器的协议(如http、ftp等)、服务器的主机名或者IP地址、以及资源文件在该服务器上的路径。

    - 可以定位和访问比如文件 ,  数据 等.

  - URL的语法表示形式为：

    ```html
    protocol://userInfo@host:port/path?query#fragment
     
    协议://用户信息@主机名:端口/路径?查询#片段
    ```

    - URL中的用户信息(userInfo)是服务器的登录信息，这部分信息是可选的。如果这部分信息存在，一般会包含一个用户名，极少情况下会包含一个口令。实际上URL携带用户信息是不安全的。
      - 示例:  http://username:password@api.somesite.com/test/blah?something=123
    - 片段(fragment)表示远程服务器资源的某个特定的部分。假如服务器资源是一个HTML文档，此片段标识符将制定为该HTML文档的一个锚(Anchor)。如果远程资源是一个XML文档，那么这个片段标识符是一个XPointer。(如果用Markdown写过博客就知道，添加了导航目录之后，片段就是目录将要导航到的目的章节)
    - 相对URL
      - 如果相对URL以"/"开头，那么它是相对于文档的根目录，而不是当前的文档。
    - 转义后的URL可能和之前 not equal
      - http://foo.com/hello world/ and http://foo.com/hello%20world would be considered not equal to each other.

- URI = Universal Resource Identifier = 统一资源标志符 (jdk1.4 出现)

  - 核心是表明资源的唯一性, 是一个资源的字符串表示 , 它有其定义的格式

  - URI的语法构成是：一个模式和一个模式特定部分

    - scheme:scheme specific part

  - URI 可以简单理解为 是对URL 去除了访问方式的 保留唯一标识 ( 可能有访问地址) 的抽象.

  - URI常见模式

    - data：链接中直接包含经过BASE64编码的数据。
    - file：本地磁盘上的文件。
    - ftp：FTP服务器。
    - http：使用超文本传输协议。
    - mailto：电子邮件的地址。
    - magnet：可以通过对等网络(端对端P2P，如BitTorrent)下载的资源。
    - telnet：基于Telnet的服务的连接。
    - urn：统一资源名(Uniform Resource Name)。

  - java中还大量使用了一些非标准的定制模式，如rmi、jar、jndi、doc、jdbc等

  - URI中的模式特定部分没有固定的语法，不过，很多时候都是采用一种层次结构形式，如：

    ```html
    //授权机构/路径?查询参数 
    //authority/path?query
    ```

  - URI构成内容: scheme,scheme-specific-part,authority,user-info,host,port,path,query,fragment

    - 示例

      ```html
      mailto:java-net@java.sun.com
      news:comp.lang.java
      urn:isbn:096139210x
      https://docs.oracle.com/javase/1.3/docs/guide/collections/designfaq.html#28
      ```

- URN关联关系
  - URI可被视为定位符（URL），名称（URN）或两者兼备。统一资源名（URN）如同一个人的名称，而统一资源定位符（URL）代表一个人的住址(和访问方式)。换言之，URN定义某事物的身份，而URL提供查找该事物的方法。

# URL

## 成员简介

### 变量&常量

- String protocol = 访问协议 : 如 http
- String authority = The authority part of this URL
  - 默认authority = host + ":" + port
- String userInfo =  The userinfo part of this URL
- String file =  path + query
- String ref = fragment 对应值
- 默认协议: BUILTIN_HANDLERS_PREFIX = "sun.net.www.protocol"
- 默认path: protocolPathProp = "java.protocol.handler.pkgs"

### 构造方法

- 绝对路径的创建方法

```java
    /**
     * 此构造函数不对输入执行任何验证
     * @param      protocol   the name of the protocol to use.
     * @param      host       the name of the host.
     * @param      port       the port number on the host. 如果值为-1,
     *                        则使用protocol对应的默认端口号
     * @param      file       the file on the host
     * @param      handler    the stream handler for the URL. 如果为null , 则使用  
     *                           protocol 对应默认的handler
     * @exception  MalformedURLException  if an unknown protocol is specified.
     *     没有给port 或者URLStreamHandler 不匹配给定URL 则抛出
     */
    public URL(String protocol, String host, int port, String file,
               URLStreamHandler handler) throws MalformedURLException { ..... }
```

- 相对路径的创建方法

```java
/**
     * @param      context   the context in which to parse the specification.
     * @param      spec      the {@code String} to parse as a URL.
     * @param      handler   the stream handler for the URL.
     */
    public URL(URL context, String spec, URLStreamHandler handler)
        throws MalformedURLException
    { ... }
```

### 普通方法

- 对于 query ; path ;  userInfo ; authority ; port ; protocol ; host ; file ; ref 等属性的get方法.
- toString 和 toExternalForm

```java
     /**
     * 返回URL最完整的信息
     */
    public String toString() {
        return toExternalForm();
    }
 
    /**
     * 构建一个能代笔此URL的字符串
     */
    public String toExternalForm() {
        return handler.toExternalForm(this);
    }
```

- **toURI()**

```java
     /**
     * 返回一个与此URL等价的{@link java.net.URI}。这个方法的运行方
     * 式与{@code new URI (This . tostring())}相同。注意，任何符
     * 合RFC2396的URL实例都可以转换为URI。但是，一些不严格符合要求的url不能转换为URI。
     * @return    a URI instance equivalent to this URL.
     * @since 1.5
     */
    public URI toURI() throws URISyntaxException {
        return new URI (toString());
    }   
```

**获得连接**

```java
    /**
     * 返回一个{@link java.net.URLConnection URLConnection}实例，
     * 该实例表示到由{@code URL}引用的远程对象的连接。
     * 每次调用该URL的协议处理程序的{@linkplain java.net
     * .URLConnection URLConnection}方法时，都会创建一个新的实例
     * {@linkplain java.net.URLConnection URLConnection}。
     * 应该注意的是，URLConnection实例在创建时并不建立实际的网络连接。
     * 只有在调用{@linkplain java.net.URLConnection#connect()
     * URLConnection.connect()}时才会发生这种情况。
     *
     * 如果对于URL的协议(如HTTP或JAR)，存在一个公共的、专用的URLConnection子类，
     * 它属于以下包之一或它们的子包之一:java.lang,java.io, java.net, 则返回的连
     * 接将是那个子类的。例如，对于HTTP，将返回一个HttpURLConnection
     */
    public URLConnection openConnection() throws java.io.IOException {
        return handler.openConnection(this);
    }
 
    /**
     * 通过代理建立连接
     * @since      1.5
     */
    public URLConnection openConnection(Proxy proxy)
        throws java.io.IOException { ... }
```

**访问**

```java
/**
     * Opens a connection to this {@code URL} and returns an
     * {@code InputStream} for reading from that connection.
     */
    public final InputStream openStream() throws java.io.IOException {
        return openConnection().getInputStream();
    }

```

```java
    // ps: 通过设置和实现 ContentHandlerFactory 可以自定义处理内容返回指定对象
    //, 默认同样返回InputStream ; 例如根据不同的HTTP MIME TYPE 处理不同的类容
    public final Object getContent() throws java.io.IOException {
        return openConnection().getContent();
    }
    public final Object getContent(Class[] classes) throws java.io.IOException {
        return openConnection().getContent(classes);
    }

```

**StreamHandlerFactory**

```java
    /**
     * 设置应用程序的{@code URLStreamHandlerFactory}。
     * 在给定的Java虚拟机中，最多可以调用该方法一次。
     * {@code URLStreamHandlerFactory}实例用于从协议名称构造流协议处理程序。
     * 如果存在安全管理器，此方法首先调用安全管理器的{@code checkSetFactory}方法
     * 以确保允许操作。这可能会导致SecurityException。
     */
    public static void setURLStreamHandlerFactory(URLStreamHandlerFactory fac) {
        synchronized (streamHandlerLock) {
            if (factory != null) {
                throw new Error("factory already defined");
            }
            SecurityManager security = System.getSecurityManager();
            if (security != null) {
                security.checkSetFactory();
            }
            handlers.clear();
            factory = fac;
        }
    }

```

## demo示例

```java
import org.junit.Test;
 
import java.net.MalformedURLException;
import java.net.URL;
 
public class URLTest {
    @Test
    public void test001() throws MalformedURLException {
        URL url = new URL("http://username:password@api.somesite.com/test/blah?something=123#fra");
        println("authority" ,url.getAuthority());
        println("file", url.getFile());
        println("dPort", url.getDefaultPort());
        println("path", url.getPath());
        println("protocol", url.getProtocol());
        println("query", url.getQuery());
        println("ref", url.getRef());
        println("host", url.getHost());
        println("userInfo", url.getUserInfo());
        println("userInfo", url.getUserInfo());
        println("toString", url.toString());
        println("toExternalForm", url.toExternalForm());
 
        System.out.println(".............................");
 
        URL reUrl = new URL(url,"/relative");
        println("path", reUrl.getPath());
        println("file", reUrl.getFile());
        println("toString", reUrl.toString());
        println("toExternalForm", reUrl.toExternalForm());
    }
 
    private void println(String title,Object object){
        System.out.println(title + ": " + object);
    }
}

```

输出:

```html
authority: username:password@api.somesite.com
file: /test/blah?something=123
dPort: 80
path: /test/blah
protocol: http
query: something=123
ref: fra
host: api.somesite.com
userInfo: username:password
userInfo: username:password
toString: http://username:password@api.somesite.com/test/blah?something=123#fra
toExternalForm: http://username:password@api.somesite.com/test/blah?something=123#fra
.............................
path: /relative
file: /relative
toString: http://username:password@api.somesite.com/relative
toExternalForm: http://username:password@api.somesite.com/relative

```

# URI

URI实例是一个结构化的字符串，它支持比较、规范化、解析和相对化等语法上与模式无关的操作。

## 核心方法

### 成员&变量

```java
    // Components of all URIs: [<scheme>:]<scheme-specific-part>[#<fragment>]
    private transient String scheme;            // null ==> relative URI
    private transient String fragment;
    // Hierarchical URI components: [//<authority>]<path>[?<query>]
    private transient String authority;         // Registry or server
    // Server-based authority: [<userInfo>@]<host>[:<port>]
    private transient String userInfo;
    private transient String host;              // null ==> registry-based
    private transient int port = -1;            // -1 ==> undefined
    // Remaining components of hierarchical URIs
    private transient String path;              // null ==> opaque
    private transient String query;
    // The remaining fields may be computed on demand
    private volatile transient String schemeSpecificPart;

```

### 构造

```java
    public URI(String str) throws URISyntaxException {
        new Parser(str).parse(false);
    }
    //ps: ssp = scheme-specific-part , 即协议和路径的分隔符
    public URI(String scheme, String ssp, String fragment)
        throws URISyntaxException
    {
        new Parser(toString(scheme, ssp,
                            null, null, null, -1,
                            null, null, fragment))
            .parse(false);
    }
 
    public static URI create(String str) {
        try {
            return new URI(str);
        } catch (URISyntaxException x) {
            throw new IllegalArgumentException(x.getMessage(), x);
        }
    }
    //ps: 各种拼装, 然后又解析, 效率不高
    public URI(String scheme,
               String userInfo, String host, int port,
               String path, String query, String fragment)
        throws URISyntaxException
    {
        String s = toString(scheme, null,
                            null, userInfo, host, port,
                            path, query, fragment);
        checkPath(s, scheme, path);
        new Parser(s).parse(true);
    }

```

构造方法实际上调用的都是 Parser 的构造方法; Parser中提供了解析各个成员的方法以及获取结果值 .

### 一般方法

```java
parseServerAuthority ->  调用Parser 中对应方法解析

  ```

**normalize()**

```java
    /**
     * 正常化这个URI的路径。如果这个URI是不透明的，或者它的路径已经是正常形式，则返回这个URI。
     * 否则，将构造一个与此URI相同的新URI
     * @return一个与此URI等价的URI，但其路径为正常形式
     */

```
public URI normalize() {
return normalize(this);
}
```

```

**resolve()**

```java
/**
* ps: 传入绝对URI , 将当前绝对/相对地址处理为绝对地址的URI
* @return 绝对地址的URI
*/
public URI resolve(URI uri) {
    return resolve(this, uri);
}
public URI resolve(String str) {
    return resolve(URI.create(str));
}

```

**relativize()**

```java
/**
* ps: 当前URI相对于传入URI的相对地址URL
*/
public URI relativize(URI uri) {
    return relativize(this, uri);
}

```

**toURL**

```java
public URL toURL()

```
throws MalformedURLException {
if (!isAbsolute())
throw new IllegalArgumentException("URI is not absolute");
return new URL(toString());
```java
}

```

 

## demo示例

```java
import java.net.MalformedURLException;
import java.net.URI;
import java.net.URISyntaxException;

public class URITest {

```
@Test
public void test001() throws MalformedURLException, URISyntaxException {
//URL转义中: %22 = 双引号
URI uri = new URI("ftp://username:password@api.somesite.com:99/test/blah?something=%22123%22#fra");
println("getAuthority" ,uri.getAuthority());
println("getFragment", uri.getFragment());
println("getHost", uri.getHost());
println("getPath", uri.getPath());
println("getPort", uri.getPort());
println("getQuery", uri.getQuery());
println("getRawAuthority", uri.getRawAuthority());
println("getRawFragment", uri.getRawFragment());
println("getRawPath", uri.getRawPath());
println("getRawQuery", uri.getRawQuery());
println("getRawSchemeSpecificPart", uri.getRawSchemeSpecificPart());
println("getRawUserInfo", uri.getRawUserInfo());
println("toASCIIString", uri.toASCIIString());
println("toString", uri.toString());
println("toURL", uri.toURL());
println("isAbsolute", uri.isAbsolute());

System.out.println(".............................");

URI reUri = URI.create("/relative");
println("toString", reUri.toString());
//基于uri补全reUri为绝对地址
reUri = uri.resolve(reUri);
println("toString", reUri.toString());
}

private void println(String title,Object object){
System.out.println(title + ": " + object);
}
```

```

 

输出结果:

```java
getAuthority: username:password@api.somesite.com:99
getFragment: fra
getHost: api.somesite.com
getPath: /test/blah
getPort: 99
getQuery: something="123"
getRawAuthority: username:password@api.somesite.com:99
getRawFragment: fra
getRawPath: /test/blah
getRawQuery: something=%22123%22
getRawSchemeSpecificPart: //username:password@api.somesite.com:99/test/blah?something=%22123%22
getRawUserInfo: username:password
toASCIIString: ftp://username:password@api.somesite.com:99/test/blah?something=%22123%22#fra
toString: ftp://username:password@api.somesite.com:99/test/blah?something=%22123%22#fra
toURL: ftp://username:password@api.somesite.com:99/test/blah?something=%22123%22#fra
isAbsolute: true
.............................
toString: /relative
toString: ftp://username:password@api.somesite.com:99/relative

```

 

**得到URL的一些方法**

```java
URL systemResource = ClassLoader.getSystemResource(String name)

Enumeration<URL> systemResources = ClassLoader.getSystemResources(String name)

URL resource = UrlMain.class.getResource(String name)

URL resource = UrlMain.class.getClassLoader().getResource(String name)

Enumeration<URL> resources = UrlMain.class.getClassLoader().getResources(String name)

```

# 参见

- Java网络编程-URI和URL https://www.cnblogs.com/throwable/p/9740425.html
- Java中的资源，URI，URL，路径和文件有什么区别 https://cloud.tencent.com/developer/ask/56385
