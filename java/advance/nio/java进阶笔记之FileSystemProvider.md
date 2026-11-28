---
title: "java进阶笔记之FileSystemProvider"
date: "2020-06-27 15:15:10"
categories: ["java进阶学习笔记"]
tags: ["java", "文件", "SystemProvider", "File", "进阶"]
---

# 简介

文件相关的操作最终通过 java.nio.file.spi.FileSystemProvider 来提供 ,其不同的底层系统有不同的实现. 此类主要定义了如何在其对应的文件系统定位和加载文件 , 以及文件中常见的删除 / 拷贝等操作 .

子孙类: AbstractFileSystemProvider / WindowsFileSystemProvider /  JarFileSystemProvider / ZipFileSystemProvider

# 示例

```java
import com.alibaba.fastjson.JSON;
import org.junit.Test;
 
import java.io.IOException;
import java.net.MalformedURLException;
import java.net.URISyntaxException;
import java.nio.file.FileSystems;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.attribute.BasicFileAttributes;
import java.nio.file.spi.FileSystemProvider;
import java.util.concurrent.ThreadLocalRandom;
 
public class FileSystemProviderTest {
    /**
     * ps: 一般是 通过Files 工具来操作  FileSystemProvider , 这里仅仅做部分功能的示例
     * 实际开发一般使用Files.
     * @throws MalformedURLException
     * @throws URISyntaxException
     */
    @Test
    public void test001() throws IOException, URISyntaxException {
        FileSystemProvider provider = FileSystems.getDefault().provider();
        println("getScheme",provider.getScheme());
 
        Path path = Paths.get("/tmp","test01","test02" + ThreadLocalRandom.current().nextInt(9999));
        provider.createDirectory(path);
        BasicFileAttributes fileAttributes = provider.readAttributes(path, BasicFileAttributes.class);
        println("fileAttributes", JSON.toJSONString(fileAttributes));
        provider.deleteIfExists(path);
 
    }
 
    private void println(String title,Object object){
        System.out.println(title + ": " + object);
    }
}
```

输出:

ps: 这里fileAttributes 值输出了一部分属性.

```html
getScheme: file
fileAttributes: {"archive":false,"directory":true,"hidden":false,"other":false,"readOnly":false,"regularFile":false,"symbolicLink":false,"system":false}
```

# 简析

## StandardOpenOption

- 此类主要定义了打开文件的各种操作选项 . 如追加写 / 只读 等等.

```java
package java.nio.file;
 
/**
* Defines the standard open options.
*
* @since 1.7
*/
 
public enum StandardOpenOption implements OpenOption {
    /**
     * Open for read access.
     */
    READ,
 
    /**
     * Open for write access.
     */
    WRITE,
 
    /**
     * 追加写入
     */
    APPEND,
 
    /**
     * WITE模式下可用,从头写入
     */
    TRUNCATE_EXISTING,
 
    /**
     * Create a new file if it does not exist.
     * 若文件不存在则创建. 当处于CREATE_NEW 时此模式不生效.
     */
    CREATE,
 
    /**
     * Create a new file, failing if the file already exists.
     */
    CREATE_NEW,
 
    /**
     * 关闭时删除文件 , 当存在此选项时，实现将在适当的close方法关闭时尽力删除该文件。
     * 如果没有调用close方法 , 则在(正常)的终止JVM时尽力删除此文件.如果在打开一个已
     * 有的符号链接文件时出现了NOFOLLOW_LINKS选项选项，那么它可能会失败(通过抛出
     */
    DELETE_ON_CLOSE,
 
    /**
     * 稀疏文件。当与CREATE_NEW选项一起使用时，该选项会提示新文件将是稀疏的。
     * 当文件系统不支持创建稀疏文件时，将忽略该选项。
     */
    SPARSE,
 
    /**
     * 要求对文件内容 或元数据 的每次更新都 同步地写入底层存储设备
     */
    SYNC,
 
    /**
     * 要求对文件内容的每次更新都 同步地写入底层存储设备。
     */
    DSYNC;
}
```

## BasicFileAttributes

- 此类主要定义了文件中通用的一些属性
  - 具体有很多子孙类
    - java.nio.file.attribute.DosFileAttributes
    -  PosixFileAttributes
    - WindowsFileAttributes
    - WindowsFileAttributes

```java
package java.nio.file.attribute;
 
/**
* 基础的文件属性
*
* @since 1.7
*
* @see BasicFileAttributeView
*/
 
public interface BasicFileAttributes {
 
    /**
     * Returns the time of last modification.
     * 若不支持,则返回1970-01-01T00:00:00Z
     */
    FileTime lastModifiedTime();
 
    /**
     * 返回最后访问时间
     * 若不支持,则返回1970-01-01T00:00:00Z
     */
    FileTime lastAccessTime();
 
    /**
     * 返回创建时间
     * 若不支持,则返回1970-01-01T00:00:00Z
     */
    FileTime creationTime();
 
    /**
     * 返回该文件是否为内容不透明的常规文件。
     */
    boolean isRegularFile();
 
    /**
     * Tells whether the file is a directory.
     */
    boolean isDirectory();
 
    /**
     * Tells whether the file is a symbolic link.
     */
    boolean isSymbolicLink();
 
    /**
     * Tells whether the file is something other than a regular file, directory,
     * or symbolic link.
     */
    boolean isOther();
 
    /**
     * 返回文件大小(以字节为单位)。由于压缩、对稀疏文件的支持或其他原因，文件系
     * 统上的大小可能与实际大小不同。非常规文件的文件大小是特定于实现的，因此未指定。
     */
    long size();
 
    /**
     * 返回唯一标识给定文件的对象，如果文件键不可用，则返回null。在一些平台或文件系统
     * 上，可以使用标识符或标识符的组合来惟一地标识文件。此类标识符对于支持符号链接的
     * 文件系统中的文件树遍历或允许文件作为多个目录中的条目的文件系统中的操作非常重要。
     *
     * 例如，在UNIX文件系统上，设备ID和inode通常用于这种目的。只有在文件系统和文件保
     * 持静态时，此方法返回的文件密钥才能保证是唯一的。文件系统在删除文件后是否重用标识
     * 符取决于实现，因此未指定。可以比较由此方法返回的文件键是否相等，并适合在集合中使
     * 用。如果文件系统和文件保持静态，并且两个文件具有相同的非空文件键，那么它们的文件
     * 键是相等的。
     *
     * @see java.nio.file.Files#walkFileTree
     */
    Object fileKey();
}
```

## FileSystemProvider

```java
package java.nio.file.spi;
 
import java.nio.file.*;
import java.nio.file.attribute.*;
import java.nio.channels.*;
import java.net.URI;
import java.io.InputStream;
import java.io.OutputStream;
import java.io.IOException;
import java.util.*;
import java.util.concurrent.ExecutorService;
import java.security.AccessController;
import java.security.PrivilegedAction;
 
/**
* 文件系统的服务提供程序类。由Files类定义的方法通常会委托给该类的一个实例。
* 默认提供程序由URI schema “文件”标识。 它创建的文件系统提供对Java虚拟机可访问的
* 文件系统的访问。默认提供程序通常是系统默认提供程序，但是如果系统属性java.nio.file.spi
* 被覆盖在这种情况下，提供程序有一个单参数构造函数，其形式参数类型是FileSystemProvider
* 所有其他提供程序都有一个零参数构造函数来初始化提供程序。
* 这个类中的所有方法对于多个并发线程都是安全的。
*
* @since 1.7
*/
 
public abstract class FileSystemProvider {
    // lock using when loading providers
    private static final Object lock = new Object();
 
    // installed providers
    private static volatile List<FileSystemProvider> installedProviders;
 
    // used to avoid recursive loading of instaled providers
    private static boolean loadingProviders  = false;
 
    private static Void checkPermission() {
        SecurityManager sm = System.getSecurityManager();
        if (sm != null)
            sm.checkPermission(new RuntimePermission("fileSystemProvider"));
        return null;
    }
    private FileSystemProvider(Void ignore) { }
 
    /**
     * 初始化该类的新实例。在构造期间，提供程序可以安全地访问与默认提供程序关联的文件，
     * 但需要注意避免循环加载其他已安装的提供程序。如果检测到循环加载已安装的提供程序，
     * 则抛出未指定的错误。
     */
    protected FileSystemProvider() {
        this(checkPermission());
    }
    //ps: 循环加载处文件外的FileSystemProvider 并返回 . (有重复自动取第一个)
    // loads all installed providers
    private static List<FileSystemProvider> loadInstalledProviders() {
        List<FileSystemProvider> list = new ArrayList<FileSystemProvider>();
 
        ServiceLoader<FileSystemProvider> sl = ServiceLoader
            .load(FileSystemProvider.class, ClassLoader.getSystemClassLoader());
 
        // ServiceConfigurationError may be throw here
        for (FileSystemProvider provider: sl) {
            String scheme = provider.getScheme();
 
            // add to list if the provider is not "file" and isn't a duplicate
            if (!scheme.equalsIgnoreCase("file")) {
                boolean found = false;
                for (FileSystemProvider p: list) {
                    if (p.getScheme().equalsIgnoreCase(scheme)) {
                        found = true;
                        break;
                    }
                }
                if (!found) {
                    list.add(provider);
                }
            }
        }
        return list;
    }
 
    /**
     * ps: 加入同步, 加入系统默认FileSystemProvider
     */
    public static List<FileSystemProvider> installedProviders() {
        if (installedProviders == null) {
            // ensure default provider is initialized
            FileSystemProvider defaultProvider = FileSystems.getDefault().provider();
 
            synchronized (lock) {
                if (installedProviders == null) {
                    if (loadingProviders) {
                        throw new Error("Circular loading of installed providers detected");
                    }
                    loadingProviders = true;
 
                    List<FileSystemProvider> list = AccessController
                        .doPrivileged(new PrivilegedAction<List<FileSystemProvider>>() {
                            @Override
                            public List<FileSystemProvider> run() {
                                return loadInstalledProviders();
                        }});
 
                    // insert the default provider at the start of the list
                    list.add(0, defaultProvider);
 
                    installedProviders = Collections.unmodifiableList(list);
                }
            }
        }
        return installedProviders;
    }
 
    /**
     * Returns the URI scheme that identifies this provider.
     */
    public abstract String getScheme();
 
    /**
     * ps: 通过uri和env参数来构建一个新的文件系统 . 如果文件系统已经存在则抛出异常.
     */
    public abstract FileSystem newFileSystem(URI uri, Map<String,?> env)
        throws IOException;
    //ps: 创建的文件系统如果关闭了则抛出异常
    public abstract FileSystem getFileSystem(URI uri);
 
    /**
     * ps: uri转path , 一般都是schema的不同 , 默认是 ' file ',
     * 如果安装了安全管理器，则提供程序实现可能需要检查权限
     */
    public abstract Path getPath(URI uri);
 
    public FileSystem newFileSystem(Path path, Map<String,?> env)
        throws IOException
    {
        throw new UnsupportedOperationException();
    }
 
    /**
     * 打开一个文件，返回从该文件读取的输入流。此方法完全按照文件指定的方式工作。
     * 该方法的默认实现就像调用newByteChannel方法一样打开文件的通道，并构造从
     * 通道读取字节的流。应该在适当的地方重写此方法。
     */
    public InputStream newInputStream(Path path, OpenOption... options)
        throws IOException
    {
        if (options.length > 0) {
            for (OpenOption opt: options) {
                // All OpenOption values except for APPEND and WRITE are allowed
                if (opt == StandardOpenOption.APPEND ||
                    opt == StandardOpenOption.WRITE)
                    throw new UnsupportedOperationException("'" + opt + "' not allowed");
            }
        }
        return Channels.newInputStream(Files.newByteChannel(path, options));
    }
 
    /**
     * 默认创建或者从头开始写入文件内容
     */
    public OutputStream newOutputStream(Path path, OpenOption... options)
        throws IOException
    {
        int len = options.length;
        Set<OpenOption> opts = new HashSet<OpenOption>(len + 3);
        if (len == 0) {
            opts.add(StandardOpenOption.CREATE);
            opts.add(StandardOpenOption.TRUNCATE_EXISTING);
        } else {
            for (OpenOption opt: options) {
                if (opt == StandardOpenOption.READ)
                    throw new IllegalArgumentException("READ not allowed");
                opts.add(opt);
            }
        }
        opts.add(StandardOpenOption.WRITE);
        return Channels.newOutputStream(newByteChannel(path, opts));
    }
 
    /**
     * 打开或创建一个文件用于读取和/或写入，返回一个文件通道来访问该文件。
     * 此方法完全按照FileChannel指定的方式工作。开放的方法。不支持构造文件通道所
     * 需的所有特性的提供程序将抛出UnsupportedOperationException。默认提供程
     * 序是支持文件通道创建所必需的。当未被覆盖时，默认实现将抛 
     * UnsupportedOperationException。
     */
    public FileChannel newFileChannel(Path path,
                                      Set<? extends OpenOption> options,
                                      FileAttribute<?>... attrs)
        throws IOException
    {
        throw new UnsupportedOperationException();
    }
 
    /**
     * 此方法完全按照异步filechannel指定的方式工作. 若不支持则抛出异常
     */
    public AsynchronousFileChannel newAsynchronousFileChannel(Path path,
     Set<? extends OpenOption> options,ExecutorService executor,
      FileAttribute<?>... attrs)
        throws IOException
    {
        throw new UnsupportedOperationException();
    }
 
    /**
     * 打开或创建文件，返回可查找的字节通道来访问该文件。此方法完全按照文件指定的方式工作。
     * newByteChannel(Path, Set, FileAttribute[])方法。
     * ps: SeekableByteChannel允许我们定位到文件的任意位置进行读写
     */
    public abstract SeekableByteChannel newByteChannel(Path path,
        Set<? extends OpenOption> options, FileAttribute<?>... attrs) throws IOException;
 
    /**
     * 打开一个目录，返回一个DirectoryStream以迭代该目录中的条目。
     * 此方法完全按照文件指定的方式工作。newDirectoryStream(路径,
     * DirectoryStream.Filter)方法。
     */
    public abstract DirectoryStream<Path> newDirectoryStream(Path dir,
         DirectoryStream.Filter<? super Path> filter) throws IOException;
 
    /**
     * 创建一个文件夹, 支持指定读写执行等权限属性.
     */
    public abstract void createDirectory(Path dir, FileAttribute<?>... attrs)
        throws IOException;
 
    /**
     * 创建符号链接
     */
    public void createSymbolicLink(Path link, Path target, FileAttribute<?>... attrs)
        throws IOException
    {
        throw new UnsupportedOperationException();
    }
 
    /**
     * 创建(hard)链接
     */
    public void createLink(Path link, Path existing) throws IOException {
        throw new UnsupportedOperationException();
    }
 
    public abstract void delete(Path path) throws IOException;
 
    public boolean deleteIfExists(Path path) throws IOException {
        try {
            delete(path);
            return true;
        } catch (NoSuchFileException ignore) {
            return false;
        }
    }
 
    /**
     * 读取符号链接的目标。此方法完全按照文件指定的方式工作。readSymbolicLink方法。
     * 此方法的默认实现会抛出UnsupportedOperationException。
     */
    public Path readSymbolicLink(Path link) throws IOException {
        throw new UnsupportedOperationException();
    }
 
    /**
     * 将文件复制到目标文件。
     */
    public abstract void copy(Path source, Path target, CopyOption... options)
        throws IOException;
 
    /**
     * Move or rename a file to a target file.
     */
    public abstract void move(Path source, Path target, CopyOption... options)
        throws IOException;
 
    /**
     * Tests if two paths locate the same file.
     */
    public abstract boolean isSameFile(Path path, Path path2)
        throws IOException;
 
    /**
     * Tells whether or not a file is considered hidden.
     */
    public abstract boolean isHidden(Path path) throws IOException;
 
    /**
     * Returns the {@link FileStore} representing the file store where a file
     * is located.
     */
    public abstract FileStore getFileStore(Path path) throws IOException;
 
    /**
     * 检查一个文件的读/写/执行等权限
     */
    public abstract void checkAccess(Path path, AccessMode... modes)
        throws IOException;
 
    /**
     * 返回文件的访问视图. ps://相当于屏蔽底层提供不同类型文件系统访问接口的具体实现
     */
    public abstract <V extends FileAttributeView> V
        getFileAttributeView(Path path, Class<V> type, LinkOption... options);
 
    /**
     * 文件系统中与文件关联的基本属性。基本文件属性是许多文件系统共有的属性，由
     * 此接口定义的强制和可选文件属性组成。
     * 使用的例子:
     * BasicFileAttributes attrs
     *             = Files.readAttributes(file, BasicFileAttributes.class)
     */
    public abstract <A extends BasicFileAttributes> A
        readAttributes(Path path, Class<A> type, LinkOption... options) throws IOException;
 
    /**
     * 以批量操作的形式读取一组文件属性
     */
    public abstract Map<String,Object> readAttributes(Path path, String attributes,
                                                      LinkOption... options)
        throws IOException;
 
    /**
     * Sets the value of a file attribute.
     */
    public abstract void setAttribute(Path path, String attribute,
                                      Object value, LinkOption... options)
        throws IOException;
}
```

# 参见

- linux 稀疏文件（Sparse File） https://blog.csdn.net/cymm_liu/article/details/8760033
