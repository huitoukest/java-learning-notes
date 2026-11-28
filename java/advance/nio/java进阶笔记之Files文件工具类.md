---
title: "java进阶笔记之Files文件工具类"
date: "2021-01-20 16:03:12"
categories: ["java进阶学习笔记"]
tags: ["java", "Files", "文件", "进阶笔记"]
---

# 简介

Files  是JDK1.7 之后系统封装的对文件操作的工具类 .

# 示例

# 源码简析

ps: 直接调用FileSystemProvider方法实现的简单逻辑将不再注释 ,  可以查看上篇: java进阶笔记之FileSystemProvider .

## 重要方法

- walkFileTree
  1. 遍历整个文件/文件夹树. 如果读取属性时发生IO异常则调用FileVisitor#visitFileFailed方法.
      ps: 默认实现是SimpleFileVisitor , 直接抛出异常. 也可以自定义实现,一般是记录日志并忽略异常.
  2. 默认不读取符号链接内容, 防止路径循环依赖.可以配置使用符号链接, 并配置检测循环依赖.
  3. 可以通过maxDepth来设置访问的层级.0表示只有启动文件被访问,Integer#MAX_VALUE表示所有级别.
  4. 当安装了安全管理器并且它拒绝访问某个文件(或目录)时，就会忽略(访问)它，
- Stream\<String\> lines(Path path)  方法是惰性填充流数据的, 可以读取大(大于4G)文件
- List\<String\> readAllLines(Path path) 会将内容读取到内存中 , 不适用与大文件的读取 , 要求小于4G.

## 源码

```java
package java.nio.file;
 
import ...; // 导入省略
 
/**
* 这个类完全由操作文件、目录或其他类型文件的静态方法组成。
* 在大多数情况下，这里定义的方法将委托给相关的 file system provider
* 来执行文件操作。
*
* @since 1.7
*/
 
public final class Files {
    private Files() { }
 
    /**
     * 返回委托的FileSystemProvider
     */
    private static FileSystemProvider provider(Path path) {
        return path.getFileSystem().provider();
    }
 
    /**
     * 通过将受检IO异常转为不受检的IO异常 , 将Closeable 对象转为 Runnable 对象.
     */
    private static Runnable asUncheckedRunnable(Closeable c) {
        return () -> {
            try {
                c.close();
            } catch (IOException e) {
                throw new UncheckedIOException(e);
            }
        };
    }
 
    // -- File contents --
    public static InputStream newInputStream(Path path, OpenOption... options)
        throws IOException
    {
        return provider(path).newInputStream(path, options);
    }
 
    public static OutputStream newOutputStream(Path path, OpenOption... options)
        throws IOException
    {
        return provider(path).newOutputStream(path, options);
    }
 
    public static SeekableByteChannel newByteChannel(Path path,
                                                     Set<? extends OpenOption> options,
                                                     FileAttribute<?>... attrs)
        throws IOException
    {
        return provider(path).newByteChannel(path, options, attrs);
    }
 
 
    public static SeekableByteChannel newByteChannel(Path path, OpenOption... options)
        throws IOException
    {
        Set<OpenOption> set = new HashSet<OpenOption>(options.length);
        Collections.addAll(set, options);
        return newByteChannel(path, set);
    }
 
    // -- Directories --
 
    private static class AcceptAllFilter
        implements DirectoryStream.Filter<Path>
    {
        private AcceptAllFilter() { }
 
        @Override
        public boolean accept(Path entry) { return true; }
 
        static final AcceptAllFilter FILTER = new AcceptAllFilter();
    }
 
    public static DirectoryStream<Path> newDirectoryStream(Path dir)
        throws IOException
    {
        return provider(dir).newDirectoryStream(dir, AcceptAllFilter.FILTER);
    }
    /**
     * ps:// 这里传入 * 因为不会创建匹配器, 在全匹配时效率更高
     */
    public static DirectoryStream<Path> newDirectoryStream(Path dir, String glob)
        throws IOException
    {
        // avoid creating a matcher if all entries are required.
        if (glob.equals("*"))
            return newDirectoryStream(dir);
 
        // create a matcher and return a filter that uses it.
        FileSystem fs = dir.getFileSystem();
        final PathMatcher matcher = fs.getPathMatcher("glob:" + glob);
        DirectoryStream.Filter<Path> filter = new DirectoryStream.Filter<Path>() {
            @Override
            public boolean accept(Path entry)  {
                return matcher.matches(entry.getFileName());
            }
        };
        return fs.provider().newDirectoryStream(dir, filter);
    }
 
    public static DirectoryStream<Path> newDirectoryStream(Path dir,
        DirectoryStream.Filter<? super Path> filter)
        throws IOException
    {
        return provider(dir).newDirectoryStream(dir, filter);
    }
 
    //ps:// 创建文件后自动关闭.
    public static Path createFile(Path path, FileAttribute<?>... attrs)
        throws IOException
    {
        EnumSet<StandardOpenOption> options =
            EnumSet.<StandardOpenOption>of(StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);
        newByteChannel(path, options, attrs).close();
        return path;
    }
 
    /**
     * 文件夹不存在则原子创建 , 否则抛出异常.
     */
    public static Path createDirectory(Path dir, FileAttribute<?>... attrs)
        throws IOException
    {
        provider(dir).createDirectory(dir, attrs);
        return dir;
    }
 
    /**
     * 通过先创建所有不存在的父目录来创建一个目录。
     * 如果由于目录已经存在而无法创建，不会抛出异常。(如果已存在且是文件会抛出异常)
     * 如果此方法失败，那么它可能会在创建一些(而不是全部)父目录之后失败。
     *
     */
    public static Path createDirectories(Path dir, FileAttribute<?>... attrs)
        throws IOException
    {
        // 尝试创建文件夹
        try {
            createAndCheckIsDirectory(dir, attrs);
            return dir;
        } catch (FileAlreadyExistsException x) {
            // 如果文件存在但是不是文件夹 ,则抛出异常
            throw x;
        } catch (IOException x) {
            // parent may not exist or other reason
        }
        SecurityException se = null;
        try {
            dir = dir.toAbsolutePath();
        } catch (SecurityException x) {
            // 如果没有权限来获取绝对路径
            se = x;
        }
        // 这里从子节点往父节点依次查找, 知道找到个存在的父路径
        Path parent = dir.getParent();
        while (parent != null) {
            try {
                provider(parent).checkAccess(parent);
                break;
            } catch (NoSuchFileException x) {
                // does not exist
            }
            parent = parent.getParent();
        }
 
        if (parent == null) {
            // 如果路径是相对的,则parent可能为空
            // 如果se 等于null 即没有权限获取绝对路径
            if (se == null) {
                throw new FileSystemException(dir.toString(), null,
                    "Unable to determine if root directory exists");
            } else {
                throw se;
            }
        }
 
        // 这里dir 是我们输入的路径 , 所以 parent.relativize(dir) 就是
        // 物理找到的存在的路径parent 与 dir 之间的相对路径 . 而for 循环默认
        // 调用 Path的iterator()方法来迭代 , 循环创建从parent到dir之间的所有
        // 文件夹(路径) , 当然如果其中有个路径是文件且已经存在则仍然抛出异常
        Path child = parent;
        for (Path name: parent.relativize(dir)) {
            child = child.resolve(name);
            createAndCheckIsDirectory(child, attrs);
        }
        return dir;
    }
 
    /**
     * 由createdirectory用于尝试创建目录。如果目录已经存在，则为no-op
     * ps://就是对单个路径的创建的抛出异常的一种封装 ( 如果是文件夹且存在则忽略,
     * 是文件则抛出异常)
     */
    private static void createAndCheckIsDirectory(Path dir,
                                                  FileAttribute<?>... attrs)
        throws IOException
    {
        try {
            createDirectory(dir, attrs);
        } catch (FileAlreadyExistsException x) {
            if (!isDirectory(dir, LinkOption.NOFOLLOW_LINKS))
                throw x;
        }
    }
 
    /**
     * 在指定的目录中创建一个新的空文件，使用给定的前缀和后缀字符串来生成它的名称。
     * 生成的路径与给定目录的文件系统相关联。关于如何构造文件名称的细节依赖于实现，
     * 因此没有指定。在可能的情况下，使用前缀和后缀以与java.io.File
     * 的createTempFile(String,String,File)}方法相同的方式构造候选名称。
     * 与文件一样。方法，这个方法只是临时文件工具的一部分。在作为工作文件使用时，
     * 结果文件可以使用StandardOpenOption#DELETE_ON_CLOSE DELETE_ON_CLOSE
     * 选项打开，以便在调用适当的close方法时删除该文件。或者，一个Runtime#addShutdownHook
     * 或者java.io.File#deleteOnExit机制可以用来自动删除文件。
     * 当没有指定文件属性时，生成的文件可能对java.io.File#createTempFile(String,String, file)
     * 方法创建的文件具有更严格的访问权限。
     *
     * ps:// 若不指定prefix 则默认取环境变量java.io.tmpdir的值作为基础的tmp目录,
     * 如果没有配置则依赖于系统
     * Files.createTempDirectory(Paths.get("/tmp"),"333") =
     *        \tmp\3334172134219839174290
     */
    public static Path createTempFile(Path dir,
                                      String prefix,
                                      String suffix,
                                      FileAttribute<?>... attrs)
        throws IOException
    {
        return TempFileHelper.createTempFile(Objects.requireNonNull(dir),
                                             prefix, suffix, attrs);
    }
 
    public static Path createTempFile(String prefix,
                                      String suffix,
                                      FileAttribute<?>... attrs)
        throws IOException
    {
        return TempFileHelper.createTempFile(null, prefix, suffix, attrs);
    }
 
    public static Path createTempDirectory(Path dir,
                                           String prefix,
                                           FileAttribute<?>... attrs)
        throws IOException
    {
        return TempFileHelper.createTempDirectory(Objects.requireNonNull(dir),
                                                  prefix, attrs);
    }
 
    public static Path createTempDirectory(String prefix,
                                           FileAttribute<?>... attrs)
        throws IOException
    {
        return TempFileHelper.createTempDirectory(null, prefix, attrs);
    }
 
    /**
     * Creates a symbolic link to a target
     */
    public static Path createSymbolicLink(Path link, Path target,
                                          FileAttribute<?>... attrs)
        throws IOException
    {
        provider(link).createSymbolicLink(link, target, attrs);
        return link;
    }
 
    /**
     * Creates a new link (directory entry) for an existing file
     */
    public static Path createLink(Path link, Path existing) throws IOException {
        provider(link).createLink(link, existing);
        return link;
    }
 
    public static void delete(Path path) throws IOException {
        provider(path).delete(path);
    }
 
    public static boolean deleteIfExists(Path path) throws IOException {
        return provider(path).deleteIfExists(path);
    }
 
    // -- Copying and moving files --
 
    /**
     * Copy a file to a target file.
     * ps: //这里如果是相同的文件系统则直接copy , 如果不同则使用CopyMoveHelper
     * CopyMoveHelper 实际上就是手动通过stream方式读写文件达到copy的功能.
     */
    public static Path copy(Path source, Path target, CopyOption... options)
        throws IOException
    {
        FileSystemProvider provider = provider(source);
        if (provider(target) == provider) {
            // same provider
            provider.copy(source, target, options);
        } else {
            // different providers
            CopyMoveHelper.copyToForeignTarget(source, target, options);
        }
        return target;
    }
 
    /**
     * Move or rename a file to a target file.
     */
    public static Path move(Path source, Path target, CopyOption... options)
        throws IOException
    {
        FileSystemProvider provider = provider(source);
        if (provider(target) == provider) {
            // same provider
            provider.move(source, target, options);
        } else {
            // different providers
            CopyMoveHelper.moveToForeignTarget(source, target, options);
        }
        return target;
    }
 
    // -- 其它操作 --
 
    /**
     * Reads the target of a symbolic link .
     */
    public static Path readSymbolicLink(Path link) throws IOException {
        return provider(link).readSymbolicLink(link);
    }
 
    /**
     * Returns the FileStore representing the file store where a file
     * is located.
     */
    public static FileStore getFileStore(Path path) throws IOException {
        return provider(path).getFileStore(path);
    }
 
    /**
     * Tests if two paths locate the same file.
     */
    public static boolean isSameFile(Path path, Path path2) throws IOException {
        return provider(path).isSameFile(path, path2);
    }
 
    /**
     * Tells whether or not a file is considered hidden .
     */
    public static boolean isHidden(Path path) throws IOException {
        return provider(path).isHidden(path);
    }
 
    // 延迟加载和安装的 文件类型的探测器
    private static class FileTypeDetectors{
        static final FileTypeDetector defaultFileTypeDetector =
            createDefaultFileTypeDetector();
        static final List<FileTypeDetector> installeDetectors =
            loadInstalledDetectors();
 
        // creates the default file type detector
        private static FileTypeDetector createDefaultFileTypeDetector() {
            return AccessController
                .doPrivileged(new PrivilegedAction<FileTypeDetector>() {
                    @Override public FileTypeDetector run() {
                        return sun.nio.fs.DefaultFileTypeDetector.create();
                }});
        }
 
        // loads all installed file type detectors
        private static List<FileTypeDetector> loadInstalledDetectors() {
            return AccessController
                .doPrivileged(new PrivilegedAction<List<FileTypeDetector>>() {
                    @Override public List<FileTypeDetector> run() {
                        List<FileTypeDetector> list = new ArrayList<>();
                        ServiceLoader<FileTypeDetector> loader = ServiceLoader
                            .load(FileTypeDetector.class, ClassLoader.getSystemClassLoader());
                        for (FileTypeDetector detector: loader) {
                            list.add(detector);
                        }
                        return list;
                }});
        }
    }
 
    /**
     * 返回值是RFC 2045: Multipurpose Internet Mail Extensions (MIME)第一部分:
     * Internet消息体的格式所定义的多用途Internet邮件扩展(MIME)内容类型的值的字符串形式。
     * 根据RFC中的语法，保证字符串是可解析的。
     */
    public static String probeContentType(Path path)
        throws IOException
    {
        // try installed file type detectors
        for (FileTypeDetector detector: FileTypeDetectors.installeDetectors) {
            String result = detector.probeContentType(path);
            if (result != null)
                return result;
        }
 
        // fallback to default
        return FileTypeDetectors.defaultFileTypeDetector.probeContentType(path);
    }
 
    // -- File Attributes --
 
    /**
     * Returns a file attribute view of a given type.
     *     Path path = ...
     *     AclFileAttributeView view = Files.getFileAttributeView(path,
     *                 AclFileAttributeView.class);
     *     if (view != null) {
     *      .....
     */
    public static <V extends FileAttributeView> V getFileAttributeView(Path path,
      Class<V> type,LinkOption... options)
    {
        return provider(path).getFileAttributeView(path, type, options);
    }
 
    /**
     * 以批量操作的形式读取文件的属性。
     */
    public static <A extends BasicFileAttributes> A readAttributes(Path path,
                                                                   Class<A> type,
                                                                   LinkOption... options)
        throws IOException
    {
        return provider(path).readAttributes(path, type, options);
    }
 
    /**
     * 设置文件属性的值。
     */
    public static Path setAttribute(Path path, String attribute, Object value,
                                    LinkOption... options)
        throws IOException
    {
        provider(path).setAttribute(path, attribute, value, options);
        return path;
    }
 
    /**
     * 读取文件属性的值。
     */
    public static Object getAttribute(Path path, String attribute,
                                      LinkOption... options)
        throws IOException
    {
        // only one attribute should be read
        if (attribute.indexOf('*') >= 0 || attribute.indexOf(',') >= 0)
            throw new IllegalArgumentException(attribute);
        Map<String,Object> map = readAttributes(path, attribute, options);
        assert map.size() == 1;
        String name;
        int pos = attribute.indexOf(':');
        if (pos == -1) {
            name = attribute;
        } else {
            name = (pos == attribute.length()) ? "" : attribute.substring(pos+1);
        }
        return map.get(name);
    }
 
    /**
     * 以批量操作的形式读取一组文件属性。
     */
    public static Map<String,Object> readAttributes(Path path, String attributes,
                                                    LinkOption... options)
        throws IOException
    {
        return provider(path).readAttributes(path, attributes, options);
    }
 
    /**
     * 返回文件的POSIX文件权限
     */
    public static Set<PosixFilePermission> getPosixFilePermissions(Path path,
                                                                   LinkOption... options)
        throws IOException
    {
        return readAttributes(path, PosixFileAttributes.class, options).permissions();
    }
 
    /**
     * Sets a file's POSIX permissions.
     */
    public static Path setPosixFilePermissions(Path path,
                                               Set<PosixFilePermission> perms)
        throws IOException
    {
        PosixFileAttributeView view =
            getFileAttributeView(path, PosixFileAttributeView.class);
        if (view == null)
            throw new UnsupportedOperationException();
        view.setPermissions(perms);
        return path;
    }
 
    /**
     * Returns the owner of a file.
     */
    public static UserPrincipal getOwner(Path path, LinkOption... options) throws IOException {
        FileOwnerAttributeView view =
            getFileAttributeView(path, FileOwnerAttributeView.class, options);
        if (view == null)
            throw new UnsupportedOperationException();
        return view.getOwner();
    }
 
    /**
     * Updates the file owner.
     */
    public static Path setOwner(Path path, UserPrincipal owner)
        throws IOException
    {
        FileOwnerAttributeView view =
            getFileAttributeView(path, FileOwnerAttributeView.class);
        if (view == null)
            throw new UnsupportedOperationException();
        view.setOwner(owner);
        return path;
    }
 
    /**
     * Tests whether a file is a symbolic link.
     */
    public static boolean isSymbolicLink(Path path) {
        try {
            return readAttributes(path,
                                  BasicFileAttributes.class,
                                  LinkOption.NOFOLLOW_LINKS).isSymbolicLink();
        } catch (IOException ioe) {
            return false;
        }
    }
 
    /**
     * Tests whether a file is a directory.
     *          method denies read access to the file.
     */
    public static boolean isDirectory(Path path, LinkOption... options) {
        try {
            return readAttributes(path, BasicFileAttributes.class, options).isDirectory();
        } catch (IOException ioe) {
            return false;
        }
    }
 
    /**
     * 测试文件是否为内容不透明的常规文件。
     */
    public static boolean isRegularFile(Path path, LinkOption... options) {
        try {
            return readAttributes(path, BasicFileAttributes.class, options).isRegularFile();
        } catch (IOException ioe) {
            return false;
        }
    }
 
    /**
     * Returns a file's last modified time.
     */
    public static FileTime getLastModifiedTime(Path path, LinkOption... options)
        throws IOException
    {
        return readAttributes(path, BasicFileAttributes.class, options).lastModifiedTime();
    }
 
    /**
     * Updates a file's last modified time attribute.
     */
    public static Path setLastModifiedTime(Path path, FileTime time)
        throws IOException
    {
        getFileAttributeView(path, BasicFileAttributeView.class)
            .setTimes(time, null, null);
        return path;
    }
 
    /**
     * Returns the size of a file (in bytes).
     */
    public static long size(Path path) throws IOException {
        return readAttributes(path, BasicFileAttributes.class).size();
    }
 
    // -- Accessibility --
 
    /**
     * Returns {@code false} if NOFOLLOW_LINKS is present.
     */
    private static boolean followLinks(LinkOption... options) {
        boolean followLinks = true;
        for (LinkOption opt: options) {
            if (opt == LinkOption.NOFOLLOW_LINKS) {
                followLinks = false;
                continue;
            }
            if (opt == null)
                throw new NullPointerException();
            throw new AssertionError("Should not get here");
        }
        return followLinks;
    }
 
    /**
     * Tests whether a file exists.
     */
    public static boolean exists(Path path, LinkOption... options) {
        try {
            if (followLinks(options)) {
                provider(path).checkAccess(path);
            } else {
                // attempt to read attributes without following links
                readAttributes(path, BasicFileAttributes.class,
                               LinkOption.NOFOLLOW_LINKS);
            }
            // file exists
            return true;
        } catch (IOException x) {
            // does not exist or unable to determine if file exists
            return false;
        }
 
    }
 
    /**
     * Tests whether the file located by this path does not exist.
     */
    public static boolean notExists(Path path, LinkOption... options) {
        try {
            if (followLinks(options)) {
                provider(path).checkAccess(path);
            } else {
                // attempt to read attributes without following links
                readAttributes(path, BasicFileAttributes.class,
                               LinkOption.NOFOLLOW_LINKS);
            }
            // file exists
            return false;
        } catch (NoSuchFileException x) {
            // file confirmed not to exist
            return true;
        } catch (IOException x) {
            return false;
        }
    }
 
    /**
     * Used by isReadbale, isWritable, isExecutable to test access to a file.
     */
    private static boolean isAccessible(Path path, AccessMode... modes) {
        try {
            provider(path).checkAccess(path, modes);
            return true;
        } catch (IOException x) {
            return false;
        }
    }
 
    /**
     * Tests whether a file is readable.
     */
    public static boolean isReadable(Path path) {
        return isAccessible(path, AccessMode.READ);
    }
 
    /**
     * Tests whether a file is writable.
     */
    public static boolean isWritable(Path path) {
        return isAccessible(path, AccessMode.WRITE);
    }
 
    /**
     * Tests whether a file is executable.
     */
    public static boolean isExecutable(Path path) {
        return isAccessible(path, AccessMode.EXECUTE);
    }
 
    // -- 递归相关操作 --
 
    /**
     * 遍历文件树.
     * 对于遇到的每个文件，这个方法尝试读取它的java.nio.file.attribute.BasicFileAttributes。
     * 如果文件不是一个目录，那么使用文件属性调用FileVisitor#visitFile方法。
     * 如果文件属性由于I/O异常无法读取，那么使用I/O异常调用FileVisitor#visitFileFailed方法。
     *
     * 如果该文件是一个目录，并且该目录不能被打开，那么visitFileFailed方法被调用与I/O异常，
     * 之后，文件树遍历继续，在默认情况下，在该目录的下一个兄弟。
     * 在目录成功打开的地方，则访问目录中的条目及其后代。当所有的条目都已被访问，或者在目录的
     * 迭代过程中出现I/O错误，那么该目录将被关闭，并调用访问者的FileVisitor
     * #postVisitDirectory 方法。默认情况下，文件树遍历将在目录的下一个同级继续进行。
     *
     * 默认情况下，这种方法不会自动跟随符号链接。如果 options参数包含 FileVisitOption
     * #FOLLOW_LINKS FOLLOW_LINKS 选项，则后面跟着符号链接。当下面的链接无法读取目标的
     * 属性时，该方法尝试获取链接的BasicFileAttributes。如果可以读取它们，则使用链接的属
     * 性调用visitFile方法(否则按照上面指定的方式调用visitFileFailed方法)。
     *
     * 如果options 参数包含FileVisitOption#FOLLOW_LINKS FOLLOW_LINKS选项，那么该方法
     * 将跟踪访问过的目录，以便可以检测到循环。当目录中有一个条目是该目录的祖先时，就会出现循环。
     * 循环检测通过记录java.nio.file.attribute来完成。如果文件键不可用，通过调用
     * isSameFile方法来测试一个目录是否与一个祖先的文件相同。当检测到一个循环时，
     * 它被视为一个I/O错误，并且FileVisitor#visitFileFailed 方法被调用的实
     * 例FileSystemLoopException。
     *
     * 参数maxDepth是要访问的目录的最大级别数。值0表示只有启动文件被访问，除非被安全管理器拒绝。
     * 可以使用Integer#MAX_VALUE表示应该访问所有级别。对于在maxDepth中遇到的所有文件，
     * 包括目录，visitFile方法被调用，除非无法读取基本文件属性，在这种情况下，
     * visitFileFailed方法被调用。
     * 如果访问者返回null的结果，则抛出NullPointerException。
     *
     * 当安装了安全管理器并且它拒绝访问某个文件(或目录)时，就会忽略它，
     * 不会为该文件(或目录)调用访问者。
     */
    public static Path walkFileTree(Path start,
                                    Set<FileVisitOption> options,
                                    int maxDepth,
                                    FileVisitor<? super Path> visitor)
        throws IOException
    {
        /**
         * Create a FileTreeWalker to walk the file tree, invoking the visitor
         * for each event.
         */
        try (FileTreeWalker walker = new FileTreeWalker(options, maxDepth)) {
            FileTreeWalker.Event ev = walker.walk(start);
            do {
                FileVisitResult result;
                switch (ev.type()) {
                    case ENTRY :
                        IOException ioe = ev.ioeException();
                        if (ioe == null) {
                            assert ev.attributes() != null;
                            result = visitor.visitFile(ev.file(), ev.attributes());
                        } else {
                            result = visitor.visitFileFailed(ev.file(), ioe);
                        }
                        break;
 
                    case START_DIRECTORY :
                        result = visitor.preVisitDirectory(ev.file(), ev.attributes());
 
                        // if SKIP_SIBLINGS and SKIP_SUBTREE is returned then
                        // there shouldn't be any more events for the current
                        // directory.
                        if (result == FileVisitResult.SKIP_SUBTREE ||
                            result == FileVisitResult.SKIP_SIBLINGS)
                            walker.pop();
                        break;
 
                    case END_DIRECTORY :
                        result = visitor.postVisitDirectory(ev.file(), ev.ioeException());
 
                        // SKIP_SIBLINGS is a no-op for postVisitDirectory
                        if (result == FileVisitResult.SKIP_SIBLINGS)
                            result = FileVisitResult.CONTINUE;
                        break;
 
                    default :
                        throw new AssertionError("Should not get here");
                }
 
                if (Objects.requireNonNull(result) != FileVisitResult.CONTINUE) {
                    if (result == FileVisitResult.TERMINATE) {
                        break;
                    } else if (result == FileVisitResult.SKIP_SIBLINGS) {
                        walker.skipRemainingSiblings();
                    }
                }
                ev = walker.next();
            } while (ev != null);
        }
 
        return start;
    }
 
    public static Path walkFileTree(Path start, FileVisitor<? super Path> visitor)
        throws IOException
    {
        return walkFileTree(start,
                            EnumSet.noneOf(FileVisitOption.class),
                            Integer.MAX_VALUE,
                            visitor);
    }
 
 
    // -- 简单使用的实用方法 --
 
    // buffer size used for reading and writing
    private static final int BUFFER_SIZE = 8192;
 
    /**
     * Opens a file for reading, returning a BufferedReader
     */
    public static BufferedReader newBufferedReader(Path path, Charset cs)
        throws IOException
    {
        CharsetDecoder decoder = cs.newDecoder();
        Reader reader = new InputStreamReader(newInputStream(path), decoder);
        return new BufferedReader(reader);
    }
 
    /**
     * @since 1.8
     */
    public static BufferedReader newBufferedReader(Path path) throws IOException {
        return newBufferedReader(path, StandardCharsets.UTF_8);
    }
 
    public static BufferedWriter newBufferedWriter(Path path, Charset cs,
                                                   OpenOption... options)
        throws IOException
    {
        CharsetEncoder encoder = cs.newEncoder();
        Writer writer = new OutputStreamWriter(newOutputStream(path, options), encoder);
        return new BufferedWriter(writer);
    }
 
    /**
     * @since 1.8
     */
    public static BufferedWriter newBufferedWriter(Path path, OpenOption... options) throws IOException {
        return newBufferedWriter(path, StandardCharsets.UTF_8, options);
    }
 
    /**
     * Reads all bytes from an input stream and writes them to an output stream.
     * ps:// 利用缓存读写 , 一般不会有内存溢出情况
     */
    private static long copy(InputStream source, OutputStream sink)
        throws IOException
    {
        long nread = 0L;
        byte[] buf = new byte[BUFFER_SIZE];
        int n;
        while ((n = source.read(buf)) > 0) {
            sink.write(buf, 0, n);
            nread += n;
        }
        return nread;
    }
 
    /**
     * Copies all bytes from an input stream to a file. On return, the input
     * stream will be at end of stream.
     */
    public static long copy(InputStream in, Path target, CopyOption... options)
        throws IOException
    {
        // ensure not null before opening file
        Objects.requireNonNull(in);
 
        // check for REPLACE_EXISTING
        boolean replaceExisting = false;
        for (CopyOption opt: options) {
            if (opt == StandardCopyOption.REPLACE_EXISTING) {
                replaceExisting = true;
            } else {
                if (opt == null) {
                    throw new NullPointerException("options contains 'null'");
                }  else {
                    throw new UnsupportedOperationException(opt + " not supported");
                }
            }
        }
 
        // attempt to delete an existing file
        SecurityException se = null;
        if (replaceExisting) {
            try {
                deleteIfExists(target);
            } catch (SecurityException x) {
                se = x;
            }
        }
 
        // attempt to create target file. If it fails with
        // FileAlreadyExistsException then it may be because the security
        // manager prevented us from deleting the file, in which case we just
        // throw the SecurityException.
        OutputStream ostream;
        try {
            ostream = newOutputStream(target, StandardOpenOption.CREATE_NEW,
                                              StandardOpenOption.WRITE);
        } catch (FileAlreadyExistsException x) {
            if (se != null)
                throw se;
            // someone else won the race and created the file
            throw x;
        }
 
        // do the copy
        try (OutputStream out = ostream) {
            return copy(in, out);
        }
    }
 
    /**
     * Copies all bytes from a file to an output stream.
     */
    public static long copy(Path source, OutputStream out) throws IOException {
        // ensure not null before opening file
        Objects.requireNonNull(out);
 
        try (InputStream in = newInputStream(source)) {
            return copy(in, out);
        }
    }
 
    /**
     * 要分配的数组的最大大小。一些虚拟机在数组中保留一些头字。
     * 尝试分配更大的数组可能会导致OutOfMemoryError:请求的数组大小超过VM限制
     * Integer是4个字节,32个比特位, 最大使用内存小于4G.
     */
    private static final int MAX_BUFFER_SIZE = Integer.MAX_VALUE - 8;
 
    /**
     * 从输入流中读取所有字节。使用  initialSize提示流将拥有多少字节。
     */
    private static byte[] read(InputStream source, int initialSize) throws IOException {
        int capacity = initialSize;
        byte[] buf = new byte[capacity];
        int nread = 0;
        int n;
        for (;;) {
            // read to EOF which may read more or less than initialSize (eg: file
            // is truncated while we are reading)
            while ((n = source.read(buf, nread, capacity - nread)) > 0)
                nread += n;
 
            // if last call to source.read() returned -1, we are done
            // otherwise, try to read one more byte; if that failed we're done too
            if (n < 0 || (n = source.read()) < 0)
                break;
 
            // one more byte was read; need to allocate a larger buffer
            if (capacity <= MAX_BUFFER_SIZE - capacity) {
                capacity = Math.max(capacity << 1, BUFFER_SIZE);
            } else {
                if (capacity == MAX_BUFFER_SIZE)
                    throw new OutOfMemoryError("Required array size too large");
                capacity = MAX_BUFFER_SIZE;
            }
            buf = Arrays.copyOf(buf, capacity);
            buf[nread++] = (byte)n;
        }
        return (capacity == nread) ? buf : Arrays.copyOf(buf, nread);
    }
 
    /**
     * Reads all the bytes from a file.
     */
    public static byte[] readAllBytes(Path path) throws IOException {
        try (SeekableByteChannel sbc = Files.newByteChannel(path);
             InputStream in = Channels.newInputStream(sbc)) {
            long size = sbc.size();
            if (size > (long)MAX_BUFFER_SIZE)
                throw new OutOfMemoryError("Required array size too large");
 
            return read(in, (int)size);
        }
    }
 
    /**
     * Read all lines from a file.
     * 默认的换行标识符: 回车 / 换行  / 回车后跟着换行.
     */
    public static List<String> readAllLines(Path path, Charset cs) throws IOException {
        try (BufferedReader reader = newBufferedReader(path, cs)) {
            List<String> result = new ArrayList<>();
            for (;;) {
                String line = reader.readLine();
                if (line == null)
                    break;
                result.add(line);
            }
            return result;
        }
    }
 
    /**
     * @since 1.8
     */
    public static List<String> readAllLines(Path path) throws IOException {
        return readAllLines(path, StandardCharsets.UTF_8);
    }
 
    /**
     * Writes bytes to a file.
     */
    public static Path write(Path path, byte[] bytes, OpenOption... options)
        throws IOException
    {
        // ensure bytes is not null before opening file
        Objects.requireNonNull(bytes);
 
        try (OutputStream out = Files.newOutputStream(path, options)) {
            int len = bytes.length;
            int rem = len;
            while (rem > 0) {
                int n = Math.min(rem, BUFFER_SIZE);
                out.write(bytes, (len-rem), n);
                rem -= n;
            }
        }
        return path;
    }
 
    /**
     * 将文本写入文件。每一行都是一个char序列，并按顺序写入文件，每一行都由平台的
     * 行分隔符(由系统属性line.separator定义)结束。使用指定的字符集将字符编码为字节。
     */
    public static Path write(Path path, Iterable<? extends CharSequence> lines,
                             Charset cs, OpenOption... options)
        throws IOException
    {
        // ensure lines is not null before opening file
        Objects.requireNonNull(lines);
        CharsetEncoder encoder = cs.newEncoder();
        OutputStream out = newOutputStream(path, options);
        try (BufferedWriter writer = new BufferedWriter(new OutputStreamWriter(out, encoder))) {
            for (CharSequence line: lines) {
                writer.append(line);
                writer.newLine();
            }
        }
        return path;
    }
 
    /**
     * Write lines of text to a file.
     *
     * @since 1.8
     */
    public static Path write(Path path,
                             Iterable<? extends CharSequence> lines,
                             OpenOption... options)
        throws IOException
    {
        return write(path, lines, StandardCharsets.UTF_8, options);
    }
 
    // -- Stream APIs --
 
    /**
     *
     * 返回一个惰性填充的流，其中的元素是目录中的条目。该清单不是递归的。
     * 流的元素是Path对象，这些对象是由Path#resolve(Path)根据dir获得的
     * 目录条目的名称。一些文件系统维护到目录本身和目录的父目录的特殊链接。
     * 不包括表示这些链接的条目。
     * 流是弱一致性的。它是线程安全的，但是在迭代时不会冻结目录，因此它可能
     * (也可能不会)反映从该方法返回后对目录的更新。
     * @since   1.8
     */
    public static Stream<Path> list(Path dir) throws IOException {
        DirectoryStream<Path> ds = Files.newDirectoryStream(dir);
        try {
            final Iterator<Path> delegate = ds.iterator();
 
            // Re-wrap DirectoryIteratorException to UncheckedIOException
            Iterator<Path> it = new Iterator<Path>() {
                @Override
                public boolean hasNext() {
                    try {
                        return delegate.hasNext();
                    } catch (DirectoryIteratorException e) {
                        throw new UncheckedIOException(e.getCause());
                    }
                }
                @Override
                public Path next() {
                    try {
                        return delegate.next();
                    } catch (DirectoryIteratorException e) {
                        throw new UncheckedIOException(e.getCause());
                    }
                }
            };
 
            return StreamSupport.stream(Spliterators.spliteratorUnknownSize(it, Spliterator.DISTINCT), false)
                                .onClose(asUncheckedRunnable(ds));
        } catch (Error|RuntimeException e) {
            try {
                ds.close();
            } catch (IOException ex) {
                try {
                    e.addSuppressed(ex);
                } catch (Throwable ignore) {}
            }
            throw e;
        }
    }
 
    /**
     * 遍历文件tree
     * @since   1.8
     */
    public static Stream<Path> walk(Path start,
                                    int maxDepth,
                                    FileVisitOption... options)
        throws IOException
    {
        FileTreeIterator iterator = new FileTreeIterator(start, maxDepth, options);
        try {
            return StreamSupport.stream(Spliterators.spliteratorUnknownSize(iterator, Spliterator.DISTINCT), false)
                                .onClose(iterator::close)
                                .map(entry -> entry.file());
        } catch (Error|RuntimeException e) {
            iterator.close();
            throw e;
        }
    }
 
    /**
     * @since   1.8
     */
    public static Stream<Path> walk(Path start, FileVisitOption... options) throws IOException {
        return walk(start, Integer.MAX_VALUE, options);
    }
 
    /**
     * 加入了Filter的遍历
     * @since   1.8
     */
    public static Stream<Path> find(Path start,
                                    int maxDepth,
                                    BiPredicate<Path, BasicFileAttributes> matcher,
                                    FileVisitOption... options)
        throws IOException
    {
        FileTreeIterator iterator = new FileTreeIterator(start, maxDepth, options);
        try {
            return StreamSupport.stream(Spliterators.spliteratorUnknownSize(iterator, Spliterator.DISTINCT), false)
                                .onClose(iterator::close)
                                .filter(entry -> matcher.test(entry.file(), entry.attributes()))
                                .map(entry -> entry.file());
        } catch (Error|RuntimeException e) {
            iterator.close();
            throw e;
        }
    }
 
    /**
     * 以 Stream 的形式从文件中读取所有行。与 readAllLines(Path, Charset) 不同，
     * 此方法不会将所有行读入list ，而是在流被消耗时惰性地填充。
     * 使用指定的字符集将文件中的字节解码成字符，并且支持由readAllLines指定的同一行
     * 终止符。
     * 在此方法返回后，当从文件读取时，或者读取格式不正确或不可映射的字节序列时发生的任何
     * 后续I/O异常都被包装在一个UncheckedIOException中，将从java.util.stream抛出。
     * 导致读取发生的方法。如果关闭文件时抛出IOException，它也被包装为UncheckedIOException。
     * 返回的流封装了一个Reader。如果需要及时处理文件系统资源，则应该使
     * 用try-with-resources构造来确保流的stream#close方法在流操作完成后被调用。
     *
     * @since   1.8
     */
    public static Stream<String> lines(Path path, Charset cs) throws IOException {
        BufferedReader br = Files.newBufferedReader(path, cs);
        try {
            return br.lines().onClose(asUncheckedRunnable(br));
        } catch (Error|RuntimeException e) {
            try {
                br.close();
            } catch (IOException ex) {
                try {
                    e.addSuppressed(ex);
                } catch (Throwable ignore) {}
            }
            throw e;
        }
    }
 
    /**
     * @since 1.8
     */
    public static Stream<String> lines(Path path) throws IOException {
        return lines(path, StandardCharsets.UTF_8);
    }
}
 
```

# 参见

- https://www.cnblogs.com/ixenos/p/5851976.html
- 可移植操作系统接口 Portable Operating System Interface，缩写为POSIX
  - https://baike.baidu.com/item/可移植操作系统接口/12718298?fromtitle=POSIX
