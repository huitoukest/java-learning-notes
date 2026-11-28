---
title: "java进阶笔记之Paths与FileSystems"
date: "2020-06-24 09:15:17"
categories: ["java进阶学习笔记"]
tags: ["java", "进阶", "Paths", "FileSystems"]
---

# 简介

- Paths中封装了活动Path的工具方法 , 其实现默认依赖于FileSystems , 是Path操作的增强工具类.
  - 使用Paths时会使用FileSystem默认的文件分隔符操作.
  - ps: 在win 系统中 同样支持 " / " 文件分隔符 .
- FileSystems FileSystem的工厂类, 主要是提供了系统常用的文件系统的快捷方法, 并且支持加载自定义的文件系统.

# 示例

```java
import org.junit.Test;
 
import java.io.IOException;
import java.nio.file.*;
 
public class PathsTest {
    @Test
    public void baseTest() throws IOException, InterruptedException {
        Path path = Paths.get("/tmp","test01","test02");
        println("toString",path.toString());
        println("toUri",path.toUri());
        path = Paths.get("/tmp","/test01","/test02");
        println("toString",path.toString());
        path = Paths.get("");
        println("toString",path.toString());
        int byteToGb  = 1024 * 1024 * 1024;
        for (FileStore store: FileSystems.getDefault().getFileStores()) {
              long total = store.getTotalSpace() / byteToGb;
              long used = (store.getTotalSpace() - store.getUnallocatedSpace()) / byteToGb;
              long avail = store.getUsableSpace() / byteToGb;
              System.out.format("%-20s %12d %12d %12d%n", store, total, used, avail);
        }
        System.out.println(".name..........................");
        for (String name: FileSystems.getDefault().supportedFileAttributeViews()) {
            System.out.format("%15s\n",name);
        }
 
        //使用glob模式匹配
        path = Paths.get("/tmp","123.java");
        PathMatcher pathMatcher = FileSystems.getDefault().getPathMatcher("glob:*.java");
        println("pathMatch",pathMatcher.matches(path));
        pathMatcher = FileSystems.getDefault().getPathMatcher("glob:**.java");
        println("pathMatch2",pathMatcher.matches(path));
 
    }
    private void println(String title,Object object){
        System.out.println(title + ": " + object);
    }
}
```

**输出:**

注意: window10系统 , jre1.8 .

```html
toString: \tmp\test01\test02
toUri: file:///D:/tmp/test01/test02/
toString: \tmp\test01\test02
toString:
XiTong (C:)                    79           49           30
RuanJian (D:)                 142          127           15
ZiLiao (E:)                   214          192           22
XiaZai (F:)                   200          172           28
YingYin (G:)                  236          203           32
.name..........................
          owner
            dos
            acl
          basic
           user
pathMatch: false
pathMatch2: true
```

# 简析

## Paths

### 源码

```java
package java.nio.file;
 
import java.nio.file.spi.FileSystemProvider;
import java.net.URI;
 
/**
*
* @since 1.7
*/
 
public final class Paths {
    private Paths() { }
 
    /**
     * @see FileSystem#getPath
     */
    public static Path get(String first, String... more) {
        return FileSystems.getDefault().getPath(first, more);
    }
 
    /**
     * Converts the given URI to a {@link Path} object.
     * 将给定的URI转换为路径对象。
     * 此方法遍历已安装的提供程序，以定位由给定URI的URI方案标识的提供程序。
     * URI方案的比较不考虑情况。如果找到提供程序，则调用其getPath方法来转换URI。
     * 在URI方案“file”标识的默认提供程序的情况下，给定的URI有一个非空路径组件，
     * 以及未定义的查询和片段组件。权限组件是否存在取决于平台。返回的路径与默认文
     * 件系统相关联。默认提供程序为java.io提供了类似的往返保证.
     * 只要原始路径、URI和新路径都是在同一个Java虚拟机中创建的(可能是不同的调
     * 用),对于一个给定的路径p，它保证
     * Paths.get (p.toUri ()).equals (p.toAbsolutePath ())
     * ps: 默认查找uri的provider , 并根据provider返回对应的Path.
     * @param   uri
     *          the URI to convert
     * @return  the resulting {@code Path}
     * @throws  IllegalArgumentException
     *          uri的scheme = null
     * @throws  FileSystemNotFoundException
     *          The file system, identified by the URI, does not exist and
     *          cannot be created automatically, or the provider identified by
     *          the URI's scheme component is not installed
     * @throws  SecurityException
     *          if a security manager is installed and it denies an unspecified
     *          permission to access the file system
     */
    public static Path get(URI uri) {
        String scheme =  uri.getScheme();
        if (scheme == null)
            throw new IllegalArgumentException("Missing scheme");
 
        // check for default provider to avoid loading of installed providers
        if (scheme.equalsIgnoreCase("file"))
            return FileSystems.getDefault().provider().getPath(uri);
 
        // try to find provider
        for (FileSystemProvider provider: FileSystemProvider.installedProviders()) {
            if (provider.getScheme().equalsIgnoreCase(scheme)) {
                return provider.getPath(uri);
            }
        }
 
        throw new FileSystemNotFoundException("Provider \"" + scheme + "\" not installed");
    }
}
```

## FileSystems

### 方法说明

- defaultFileSystem

### 源码

```java
package java.nio.file;
 
import java.nio.file.spi.FileSystemProvider;
import java.net.URI;
import java.io.IOException;
import java.security.AccessController;
import java.security.PrivilegedAction;
import java.util.*;
import java.lang.reflect.Constructor;
 
/**
* 这是file systems 的一个工厂方法集.通过 getDefault 方法获取系统默认的文件系统.
* 调用任何方法时,都会一导致FileSystemProvider被加载. 默认使用 URI scheme "file"
* 的相关provider 来创建FileSystem , 其提供了java 虚拟机的可访问的文件系统.
* 如果加载默认流程失败,则抛出异常.
*
* 首次调用时,通过FileSystemProvider#installedProviders来加载和定位所有安装
* 的文件系统.java.nio.file.spi.FileSystemProvider可以加载jar包下
* META-INF/services 目录下的FileSystemProvider. 通过
* FileSystemProvider#getScheme()来确定使用的FileSystemProvider.
* 构造provider期间 ,必须避免循环加载别的provider.(不然容易形成循环依赖).
*
* 这个类还定义了允许在定位提供程序时指定 类加载器 的工厂方法。与已安装的提供程序
* 一样，提供程序类是通过将提供程序配置文件放在资源目录META-INF/servic中来标识的。
* 如果一个线程开始加载已安装的文件系统提供程序，而另一个线程调用了同样尝试加载提供
* 程序的方法，那么该方法将阻塞，直到加载完成。
*
* @since 1.7
*/
 
public final class FileSystems {
    private FileSystems() {
    }
 
    // lazy initialization of default file system
    private static class DefaultFileSystemHolder {
        static final FileSystem defaultFileSystem = defaultFileSystem();
 
        // returns default file system
        private static FileSystem defaultFileSystem() {
            // load default provider
            FileSystemProvider provider = AccessController
                .doPrivileged(new PrivilegedAction<FileSystemProvider>() {
                    public FileSystemProvider run() {
                        return getDefaultProvider();
                    }
                });
 
            // return file system
            return provider.getFileSystem(URI.create("file:///"));
        }
 
        // returns default provider
        // 可以通过环境变量设置默认的SystemProvider
        private static FileSystemProvider getDefaultProvider() {
            FileSystemProvider provider = sun.nio.fs.DefaultFileSystemProvider.create();
 
            // if the property java.nio.file.spi.DefaultFileSystemProvider is
            // set then its value is the name of the default provider (or a list)
            String propValue = System
                .getProperty("java.nio.file.spi.DefaultFileSystemProvider");
            if (propValue != null) {
                for (String cn: propValue.split(",")) {
                    try {
                        Class<?> c = Class
                            .forName(cn, true, ClassLoader.getSystemClassLoader());
                        //ps: 反射获取对应参数的构造方法,并通过系统默认provider来构建指定的
                        //FileSystemProvider
                        Constructor<?> ctor = c
                            .getDeclaredConstructor(FileSystemProvider.class);
                        provider = (FileSystemProvider)ctor.newInstance(provider);
 
                        // must be "file"
                        if (!provider.getScheme().equals("file"))
                            throw new Error("Default provider must use scheme 'file'");
 
                    } catch (Exception x) {
                        throw new Error(x);
                    }
                }
            }
            return provider;
        }
    }
 
    /**
     * 创建默认的FileSystem , 默认文件夹是取环境变量 user.dir 的值.
     * 第一次调用时会定位默认的FileSystemProvider.
     * 默认对应的URI的scheme是"file". 多个默认加载器默认是comma .
     * 通过 URI是 "file:///" 类型的能取到默认file system.
     * @return  the default file system
     */
    public static FileSystem getDefault() {
        return DefaultFileSystemHolder.defaultFileSystem;
    }
 
    /**
     * 查找URI对应的FileSystem
     */
    public static FileSystem getFileSystem(URI uri) {
        String scheme = uri.getScheme();
        for (FileSystemProvider provider: FileSystemProvider.installedProviders()) {
            if (scheme.equalsIgnoreCase(provider.getScheme())) {
                return provider.getFileSystem(uri);
            }
        }
        throw new ProviderNotFoundException("Provider \"" + scheme + "\" not found");
    }
 
    /**
     * Constructs a new file system that is identified by a {@link URI}
     * 通过URI的getScheme的scheme来找对对应的file system
     * 比如这里创建一个内存文件系统:
     *   Map<String,String> env = new HashMap<>();
     *   env.put("capacity", "16G");
     *   env.put("blockSize", "4k");
     *   FileSystem fs = FileSystems.newFileSystem(URI.create("memory:///?name=logfs"), env);
     *
     * @param   env 这个Map提供一些属性参数, 可以为空
     * @return  a new file system
     * ps: 文件系统close之后 , 可以再次创建
     * @throws  FileSystemAlreadyExistsException
     *          if the file system has already been created
     * @throws  ProviderNotFoundException
     *          if a provider supporting the URI scheme is not installed
     * @throws  IOException
     *          if an I/O error occurs creating the file system
     * @throws  SecurityException
     *          if a security manager is installed and it denies an unspecified
     *          permission required by the file system provider implementation
     */
    public static FileSystem newFileSystem(URI uri, Map<String,?> env)
        throws IOException
    {
        return newFileSystem(uri, env, null);
    }
 
    /**
     * Constructs a new file system that is identified by a {@link URI}
     */
    public static FileSystem newFileSystem(URI uri, Map<String,?> env, ClassLoader loader)
        throws IOException
    {
        String scheme = uri.getScheme();
 
        // check installed providers
        for (FileSystemProvider provider: FileSystemProvider.installedProviders()) {
            if (scheme.equalsIgnoreCase(provider.getScheme())) {
                return provider.newFileSystem(uri, env);
            }
        }
 
        // if not found, use service-provider loading facility
        if (loader != null) {
            ServiceLoader<FileSystemProvider> sl = ServiceLoader
                .load(FileSystemProvider.class, loader);
            for (FileSystemProvider provider: sl) {
                if (scheme.equalsIgnoreCase(provider.getScheme())) {
                    return provider.newFileSystem(uri, env);
                }
            }
        }
 
        throw new ProviderNotFoundException("Provider \"" + scheme + "\" not found");
    }
 
    /**
     * Constructs a new  FileSystem to access the contents of a file as a
     * file system.
     */
    public static FileSystem newFileSystem(Path path,
                                           ClassLoader loader)
        throws IOException
    {
        if (path == null)
            throw new NullPointerException();
        Map<String,?> env = Collections.emptyMap();
 
        // check installed providers
        for (FileSystemProvider provider: FileSystemProvider.installedProviders()) {
            try {
                return provider.newFileSystem(path, env);
            } catch (UnsupportedOperationException uoe) {
            }
        }
 
        // if not found, use service-provider loading facility
        if (loader != null) {
            ServiceLoader<FileSystemProvider> sl = ServiceLoader
                .load(FileSystemProvider.class, loader);
            for (FileSystemProvider provider: sl) {
                try {
                    return provider.newFileSystem(path, env);
                } catch (UnsupportedOperationException uoe) {
                }
            }
        }
 
        throw new ProviderNotFoundException("Provider not found");
    }
}
```

## FileSystem

文件系统的抽象封装,使得其支持更加丰富的文件系统.

以前的File只是单个的文件 , 而 这里表示的是存储格式  + 访问与操作规则构成的文件系统

### 重要方法

**getPathMatcher**:

```java
PathMatcher pathMatcher = FileSystems.getDefault().getPathMatcher("glob:java?.exe");
```

支持glob匹配规则: 参见[Java NIO中的Glob模式](https://blog.csdn.net/chszs/article/details/46482571)

注意:

- 当语法是“regex”时，模式组件就是java.util.regex定义的正则表达式.

- 对于glob和regex语法，匹配细节(比如匹配是否区分大小写)依赖于实现，因此没有指定。

### 源码

```java
import java.nio.file.attribute.*;
import java.nio.file.spi.FileSystemProvider;
import java.util.Set;
import java.io.Closeable;
import java.io.IOException;
 
/**
* Provides an interface to a file system and is the factory for objects to
* access files and other objects in the file system.
* 提供了一个文件系统的接口, 同时也是访问文件系统中对象的一个工厂.
*
* 文件系统差别很大。在某些情况下，文件系统是具有一个顶级根目录的文件的单一层次结构。
* 在其他情况下，它可能有几个不同的文件层次结构，每个都有自己的顶级根目录。方法可以用
* 于遍历文件系统中的根目录。一个文件系统通常由一个或多个底层的 FileStore文件存储组
* 成，它们为文件提供存储空间。这些文件存储在它们所支持的特性以及它们与文件关联的文件
* 属性或元数据方面也可能有所不同。
*
* 文件系统在创建时是打开的，可以通过调用其close()方法来关闭它。一旦关闭，任何进一步
* 访问文件系统中的对象的尝试都会导致抛出{@link ClosedFileSystemException}。不
* 能关闭由默认FileSystemProvider provider创建的文件系统。
*
* 一个文件系统可以以只读/只写等模式打开.
* 文件系统是多线程并发安全的.
*
* 可以在任何时候调用close方法来关闭文件系统，但是文件系统是否异步关闭是特定于提供者
* 的，因此不指定。换句话说，如果一个线程正在访问文件系统中的对象，而另一个线程调用
* 了close方法，那么它可能需要阻塞，直到第一个操作完成。关闭文件系统会导致关闭所有
* 打开的通道、监视服务和其他与文件系统相关的Closeable对象。
*
* @since 1.7
*/
 
public abstract class FileSystem
    implements Closeable
{
    protected FileSystem() {
    }
 
    /**
     * Returns the provider that created this file system.
     */
    public abstract FileSystemProvider provider();
 
    /**
     * Closes this file system.
     * 关闭后再使用则会抛出异常.
     */
    @Override
    public abstract void close() throws IOException;
 
    /**
     * Tells whether or not this file system is open.
     * File systems created by the default provider are always open.
     */
    public abstract boolean isOpen();
 
    /**
     * Tells whether or not this file system allows only read-only access to
     * its file stores.
     */
    public abstract boolean isReadOnly();
 
    /**
     * 返回用字符串表示的名称分隔符。名称分隔符用于分隔路径字符串中的名称。
     * 实现可能支持多个名称分隔符，在这种情况下，此方法返回特定于实现的默认
     * 名称分隔符。这个分隔符在调用path#toString()方法创建路径字符串时使用。
     * 在默认提供程序的情况下，此方法返回与java.io.File#separator相同
     * 的分隔符。
     * @return  The name separator
     */
    public abstract String getSeparator();
 
    /**
     * 返回此文件系统的root路径 , 会默认调用安全管理器检查( 若没有权限访问 则不会返回)
     * ps: 如windows 系统上返回: C:\ ,D:\ 等盘符.
     */
    public abstract Iterable<Path> getRootDirectories();
 
    /**
     * 返回一个对象，以遍历基础文件存储。返回的迭代器的元素是这个文件系统
     * 的FileStores。元素的顺序没有定义，并且在Java虚拟机的生命周期中，文
     * 件存储可能会改变。当I/O错误发生时，可能是因为无法访问文件存储，那
     * 么迭代器不会返回它。
     * 在默认提供程序的情况下，并且安装了安全管理器，安全管理器将被调用来
     * 检查RuntimePermission(“getFileStoreAttributes”)。
     * 如果拒绝，那么迭代器不会返回任何文件存储。另外，安全管理器的
     * SecurityManager#checkRead(String)方法被调用来检查对文件存储最
     * 顶层目录的读访问。如果拒绝，则迭代器不会返回文件存储。权限检查是在获得
     * 迭代器时进行的还是在迭代期间进行的取决于系统。
     * FileStore 就是各个文件存储的信息, 比如windows的各个盘符以及其大小
     * /格式/权限等信息.
     * @return  An object to iterate over the backing file stores
     */
    public abstract Iterable<FileStore> getFileStores();
 
    /**
     * 返回这个文件系统支持的文件属性视图的FileAttributeView#name的集合。
     * 需要支持BasicFileAttributeView，因此该集合至少包含一个元素“basic”。
     * supportsFileAttributeView(String) 方法可以用来测试底层的
     * FileStore是否支持由文件属性视图识别的文件属性。
     * 文件视图类型: 如 basic = 基础类型 ; posix = posix文件视图;
     *  dos = dos 文件视图 .... ; 即以何种类型的文件查看方式来查看文件.
     * @return  An unmodifiable set of the names of the supported file attribute
     *          views
     */
    public abstract Set<String> supportedFileAttributeViews();
 
    /**
     * 对于默认提供程序，将根据平台或虚拟文件系统级别的路径定义解析路径字符串。
     * 例如，操作系统可能不允许在文件名中出现特定的字符，但是特定的底层文件存储
     * 区可能对合法字符集施加不同的或额外的限制。
     * 当路径字符串不能转换为路径时，此方法抛出{@link InvalidPathException}。
     * ps: 不是依赖于文件系统来校验路径的真实性 , 而是依赖于文件系统的规则来解
     * 析和拼装路径并验证有效性.
     */
    public abstract Path getPath(String first, String... more);
 
    /**
     * 通过给定的字符串返回匹配的文件,通常有对于glob和regex语法的两种风格.
     */
    public abstract PathMatcher getPathMatcher(String syntaxAndPattern);
 
    /**
     * 返回此文件系统的UserPrincipalLookupService(可选操作).
     * 一般用来操作用户或者用户组
     * 例如将文件owner改为'joe':
     *     UserPrincipalLookupService lookupService = 
     *             FileSystems.getDefault().getUserPrincipalLookupService();
     *     Files.setOwner(path, lookupService.lookupPrincipalByName("joe"));
     *
     * @throws  UnsupportedOperationException
     *          If this {@code FileSystem} does not does have a lookup service
     */
    public abstract UserPrincipalLookupService getUserPrincipalLookupService();
 
    /**
     * 构造一个新的WatchService(可选操作)。
     * 此方法构造一个新的监视服务，可用于监视已注册对象的更改和事件。
     * @return  a new watch service
     *
     * @throws  UnsupportedOperationException
     *        如果这个文件系统不支持监视文件系统对象的变化和事件。
     *           默认提供程序创建的文件系统不会引发此异常。
     * @throws  IOException
     *          If an I/O error occurs
     */
    public abstract WatchService newWatchService() throws IOException;
}
```
