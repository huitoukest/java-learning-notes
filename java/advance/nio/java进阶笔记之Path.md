---
title: "java进阶笔记之Path"
date: "2020-06-15 21:28:26"
categories: ["java进阶学习笔记"]
tags: ["java", "进阶笔记", "Path"]
---

# 背景

Path 是jdk1.7 推出的专用于访问文件的一种路径抽象.

- 位于包 java.nio.file .
- public interface Path extends Comparable\<Path\>, Iterable\<Path\>, Watchable

- 一种可用于在文件系统中定位文件的对象。它通常表示一个系统相关的文件路径。

- path 可以表示一个根、一个根和一系列名称，或者仅仅是一个或多个名称元素。

- 使用空路径访问文件相当于访问文件系统的默认目录

- 这个接口扩展了  Watchable接口，这样位于路径的目录可以是register registered，带有WatchService 和被监视目录中的条目。
- **警告:** 此接口仅供开发自定义文件系统实现的人员实现。方法可以在将来的版本中添加到这个接口。

- Path和Files类一起用于操作文件、目录和其他类型的文件。

- **并发性:** 该接口的实现是不可变的，并且对多个并发线程的使用是**安全**的。

# 简析

ps: 文件的 watchService 是阻塞式的, 所以不存在空自旋带来的性能损耗.

## demo示例

```java
import org.junit.Test;
 
import java.io.File;
import java.io.IOException;
import java.nio.file.*;
 
public class PathTest {
    @Test
    public void baseTest() throws IOException, InterruptedException {
        Path path = Paths.get("/tmp","test01","test02");
        println("toString",path.toString());
        println("toUri",path.toUri());
        println("getNameCount",path.getNameCount());
        println("getName",path.getName(1));
        println("getRoot",path.getRoot());
        println("getParent",path.getParent());
        println("toAbsolutePath",path.toAbsolutePath());
        println("...","...");
        path.iterator().forEachRemaining(it -> {
            println("iterator",it.toString());
        });
        WatchService watchService = FileSystems.getDefault().newWatchService();
        Files.createDirectories(path);
        new Thread(() -> {
            try {
                Thread.sleep(2000);
                File file = path.resolve("file01").toFile();
                file.createNewFile();
                Thread.sleep(2000);
                file.delete();
            } catch (Exception e) {
                e.printStackTrace();
            }
        }).start();
 
        //路径不存在会保存
        path.register(watchService, new WatchEvent.Kind<?>[]{StandardWatchEventKinds.ENTRY_CREATE,StandardWatchEventKinds.ENTRY_DELETE});
        boolean flag = true;
        while (flag) {
            WatchKey key = watchService.take();
            for (WatchEvent<?> event : key.pollEvents()) {
                //获取path下变动的的文件名
                String fileName = event.context().toString();
                println("fileWatcher,eventType: " + event.kind().name(),fileName);
                if(StandardWatchEventKinds.ENTRY_DELETE.equals(event.kind())){
                    flag = false;
                }
                key.reset();
            }
 
            System.out.println("...WatchKey ... cycle once..");
        }
        Thread.sleep(2000);
        println("end...","");
    }
    private void println(String title,Object object){
        System.out.println(title + ": " + object);
    }
}
```

**输出**:

```html
toString: \tmp\test01\test02
toUri: file:///D:/tmp/test01/test02/
getNameCount: 3
getName: test01
getRoot: \
getParent: \tmp\test01
toAbsolutePath: D:\tmp\test01\test02
...: ...
iterator: tmp
iterator: test01
iterator: test02
fileWatcher,eventType: ENTRY_CREATE: file01
...WatchKey ... cycle once..
fileWatcher,eventType: ENTRY_DELETE: file01
...WatchKey ... cycle once..
end...:
```

## 源码简析

```java
/**
* @since 1.7
* @see Paths
*/
public interface Path
    extends Comparable<Path>, Iterable<Path>, Watchable
{
    /**
     * @return  返回创建当前对象的文件系统
     */
    FileSystem getFileSystem();
 
    /**
     * 判断路径是否是绝对路径
     */
    boolean isAbsolute();
 
    /**
     * 返回rootPath , 或者 null ( 如果没有)
     */
    Path getRoot();
 
    /**
     * 返回Path的文件/文件夹 名称 .文件名是Path中路径最远的元素. 或者 null 如果Path中
     * 没有任何元素
     */
    Path getFileName();
 
    /**
     * 如果此Path有一个或者多个元素,但是没有Parent , 则等同与调用表达式:
     * subpath(0, getNameCount()-1);
     */
    Path getParent();
 
    /**
     * 即Path中层次的深度, 默认为 只有根元素是 返回 0
     * 如: /a/b/c = 2
     */
    int getNameCount();
 
    /**
     * 返回第index + 1层的路径值.
     */
    Path getName(int index);
 
    /**
     * 截取path , 默认根元素是 index=0
     */
    Path subpath(int beginIndex, int endIndex);
 
    /**
     * Tests if this path starts with the given path.
     * 文件系统不同,则返回false
     */
    boolean startsWith(Path other);
 
    /**
     * Tests if this path starts with a  Path constructed by converting
     * 注意: /foo/ab  start whith /foo  not /fo
     */
    boolean startsWith(String other);
 
    /**
     * Tests if this path ends with the given path.
     *
     * 如果给定路径有N个元素，没有根元素; 而这条路径有N个或更多的元素，那么如果
     * 每条路径的最后N个元素，从离根最远的元素开始，相等，那么这条路径结束于给定的路径。
     * ps: 即当前路径是相对的, 且从叶子路径逆序作比较均和给定路径相等 , 则返回true.
     * 如果 FileSystem 不同 , 返回false
     */
    boolean endsWith(Path other);
 
    /**
     * Tests if this path ends with a code Path
     * 例如，在UNIX上，路径"foo/bar"以"foo/bar"和"bar"结尾。
     * 它不以“r”或“/bar”结尾。注意，后面的分隔符没有考虑在内，所以在路
     * 径“foo/bar”上调用这个方法并使用字符串“bar/”返回true。
     */
    boolean endsWith(String other);
 
    /**
     * 返回删除冗余名称元素的此路径。
     * 此方法的精确定义依赖于实现，但通常它派生于此路径，此路径不包含冗余的name元素。
     * 在许多文件系统中，“ .”和“..” 是用于指示当前目录和父目录的特殊名称。在这样的
     * 文件系统中，所有出现的“. ”都被认为是多余的。如果一个".. "前面有一个
     * 非".. "然后这两个名称都被认为是多余的(识别这些名称的过程会重复，直到不再适用)。
     * 此方法不访问文件系统;该路径可能无法找到已存在的文件。消除“. ."和路径的前一个
     * 名称可能导致路径中所定位的文件与原始路径不同。如果前面的名称是符号链接，就会
     * 出现这种情况。
     * @see #getParent
     * @see #toRealPath
     */
    Path normalize();
 
    // -- resolution and relativization --
 
    /**
     * Resolve the given path against this path.
     * 如果other是绝对路径,则直接返回; 否则和当前路径组装为绝对路径.
     */
    Path resolve(Path other);
 
    Path resolve(String other);
 
    /**
     * 根据相同的父目录组织地址;
     * 如果没有相同的路径则返回  empty path.
     * eg: this = dir1/dir2/foo ; other = bar , re = dir1/dir2/bar
     *
     * @see #resolve(Path)
     */
    Path resolveSibling(Path other);
 
    Path resolveSibling(String other);
 
    /**
     * Constructs a relative path between this path and a given path.
     * 在此路径和给定路径之间构造相对路径。
     * 例如，在UNIX上，如果这个路径是“/a/b”，而给定的路径是“/a/b/c/d”，那么得到
     * 的相对路径就是“c/d” ; 如果此路径和给定路径没有根组件，则可以构造相对路径。
     * 如果只有一个路径具有根组件，则不能构造相对路径。如果两个路径都有一个根组件，
     * 那么如果可以构造一个相对路径，那么它是依赖于实现的。如果此路径和给定路径相
     * 等，则返回一个空路径。
     * 对于任意两条归一化路径p和q，其中q没有根分量，
     * p.relativize (p.resolve (q)) .equals (q)
     * 当支持符号链接时，结果路径(根据此路径解析)是否生成可用于定位相同文件的路径取
     * 决于实现。例如，如果这个路径是“/a/b”，给定的路径是“/a/x”，那么得到的相对路
     * 径可能是“../x”。如果"b"是一个符号链接，那么实现取决于"a/b/.. ""将与"/a/x"
     * 定位相同的文件。
     */
    Path relativize(Path other);
 
    /**
     * Returns a URI to represent this path.
     * 返回一个URI , 能代表此path, 一般用绝对路径.
     * Path可以理解为是一个特定于文件系统的复合URI
     */
    URI toUri();
 
    /**
     * 通过文件系统的实现将之转为
     */
    Path toAbsolutePath();
 
    /**
     * 返回现有文件的真实路径。绝对路径.
     * 这个方法的精确定义依赖于实现，但通常它派生于这个路径，一个绝对路径，它将
     * isSameFile 文件定位为这个路径，但是名称元素表示目录和文件的实际名称。
     * 例如，在文件系统上的文件名比较不区分大小写的情况下，name元素以其实际大小
     * 写表示名称。此外，生成的路径删除了冗余的name元素。
     * 如果这个路径是相对的，那么首先获得它的绝对路径，toAbsolutePath方法一样。
     *  options 数组可以用来表示符号链接的处理方式。默认情况下，符号链接被解析
     * 到最终目标。如果选项LinkOption#NOFOLLOW_LINKS存在，那么这个方法不会
     * 解析符号链接。
     * 当不解析符号链接且前面的名称是符号链接时，只有在保证结果路径将定位到与此
     * 路径相同的文件时，名称才会被删除。
     *
     */
    Path toRealPath(LinkOption... options) throws IOException;
 
    /**
     * 如果此Path是通过File得到的,又通过此path#toFile创建了File
     * 则这两个File可能并不equals.
     */
    File toFile();
 
    // -- watchable --
 
    /**
     * 用一个监视服务注册此路径中找到的文件。
     * 在此版本中，此路径定位一个已存在的目录。该目录向监视服务注册，以便可以
     * 监视目录中的条目。参数是要注册的事件，可以包含以下事件:
     *  standardwatcheventtypes 下的
     *    #ENTRY_CREATE ENTRY_CREATE  已创建或移动到目录中的条目
     *  #ENTRY_DELETE ENTRY_DELETE} 条目被删除或移出目录
     *  #ENTRY_MODIFY ENTRY_MODIFY} 目录中的条目被修改
     * 这些事件的WatchEvent#context是该路径所定位的目录和定位被创建、删除
     * 或修改的目录条目的路径之间的相对路径。
     * 事件集可能包括enum standardwatcheventtypes未定义的其他实现特定事件。
     * 参数指定限定目录注册方式的修饰符。此版本没有定义任何标准修饰符。它可能包含
     * 实现特定的修饰符。
     * 如果一个文件是通过符号链接在手表服务中注册的，那么在注册后如果watch 继续
     * 依赖符号链接的存在，那么它是特定于实现的。
     *
     * @param   watcher
     *          the watch service to which this object is to be registered
     * @param   events
     *          the events for which this object should be registered
     * @param   modifiers
     *          修改对象注册方式的修饰符(如果有的话)
     *
     * @return  a key representing the registration of this object with the
     *          given watch service
     */
    @Override
    WatchKey register(WatchService watcher,
                      WatchEvent.Kind<?>[] events,
                      WatchEvent.Modifier... modifiers)
        throws IOException;
 
    @Override
    WatchKey register(WatchService watcher,
                      WatchEvent.Kind<?>... events)
        throws IOException;
 
    // -- Iterable --
 
    /**
     * 在此路径的name元素上返回一个迭代器。
     * 迭代器返回的第一个元素表示目录层次结构中最接近根的name元素，第二个元素是下一
     * 个最接近根的元素，依此类推。最后返回的元素是此路径所表示的文件或目录的名称。如
     * 果存在 getRoot组件，则迭代器不会返回该组件。
     * ps: 相当于根据Path 和分隔符截取字符串 , 没有使用文件系统
     * @return  an iterator over the name elements of this path.
     */
    @Override
    Iterator<Path> iterator();
 
    // -- compareTo/equals/hashCode --
 
    /**
     * 按照字母顺序比较两个路径
     */
    @Override
    int compareTo(Path other);
 
    /**
     * Tests this path for equality with the given object.
     * 如果 FileSystem 不同, 则返回false ; 否则比较
     */
    boolean equals(Object other);
 
    int hashCode();
 
    /**
     * 返回能代表这个Path的String
     */
    String toString();
}
```
