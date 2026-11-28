---
title: "MapReduce在Eclipse上调试(利用Tool20160324)"
date: "2016-03-24 10:29:17"
categories: ["hadoop相关"]
tags: ["hadoop", "MapReduce", "ToolRunner"]
---

# 1.目前Mapreduce的调试有如下几种方法

1.打包类,手动上传到hadoop部署环境运行;

2.使用hadoop的Eclipse插件;

3.使用toolRunner工具类;

本文介绍第三种;

# 2.原理

实现调试的核心内容是让MapReduce能够引入使用第三方jar包(包括自己写的类编译成的jar包);

要想让mapreduce程序引用第三方jar文件, 可以采用如下方式:

  1. 通过命令行参数传递jar文件, 如-libjars等;
  2. 直接在conf中设置, 如conf.set(“tmpjars”,*.jar), jar文件用逗号隔开;
  3. 利用分布式缓存, 如DistributedCache.addArchiveToClassPath(path, job), 此处的path必须是hdfs, 即自己讲jar上传到hdfs上, 然后将路径加入到分布式缓存中;
  4. 第三方jar文件和自己的程序打包到一个jar文件中, 程序通过job.getJar()将获得整个文件并将其传至hdfs上. (很笨重)
  5. 在每台机器的$HADOOP_HOME/lib目录中加入jar文件. (不推荐)

本文采用的是conf.set("tmpjars",XXX)的方式;

# 3.实现类

笔者已经将现实细节做成一个工具类:

    import java.io.File;
    import java.io.FileInputStream;
    import java.io.FileOutputStream;
    import java.io.IOException;
    import java.io.PrintStream;
    import java.io.UnsupportedEncodingException;
    import java.net.URLDecoder;
    import java.util.HashMap;
    import java.util.Map;
    import java.util.Set;
    import java.util.jar.JarEntry;
    import java.util.jar.JarOutputStream;
    import java.util.jar.Manifest;

    import mapreduce.MagicRunner;

    import org.apache.commons.cli.CommandLine;
    import org.apache.commons.cli.CommandLineParser;
    import org.apache.commons.cli.GnuParser;
    import org.apache.commons.cli.Option;
    import org.apache.commons.cli.OptionBuilder;
    import org.apache.commons.cli.Options;
    import org.apache.commons.cli.ParseException;
    import org.apache.commons.logging.Log;
    import org.apache.commons.logging.LogFactory;
    import org.apache.hadoop.conf.Configuration;
    import org.apache.hadoop.fs.FileSystem;
    import org.apache.hadoop.fs.Path;
    import org.apache.hadoop.util.GenericOptionsParser;
    import org.apache.hadoop.util.Tool;
    /**
     *
     * @author dview76
     * 主要作用是将本地Mapreduce以及所依赖的jar包上传到hdfs中;
     * 然后运行分布式任务;
     */
    public class MapReduceUtils {
    		private String jarDir_3rdPart = "lib";
    		private String classPath = "bin";
    		/**
    		 * classPath的绝对路径
    		 */
    		private String classPathAbsolutePath="";
    		private String[] args=null;

    		/**
    		 * 当前包含与依赖的所有har包的名称(Key)和路径(value),防止jar包重复
    		 */
    		private Map<String,String> jarsMap=new HashMap<String,String>();
    		/**
    		 *tmpdir的实际位置
    		 *On Windows: java.io.tmpdir:[C:\DOCUME~1\joshua\LOCALS~1\Temp\]
    		 *On Solaris: java.io.tmpdir:[/var/tmp/]
    		 *On Linux: java.io.tmpdir: [/tmp]
    		 *On Mac OS X: java.io.tmpdir: [/tmp]
    		 */
    		private  final String TEMP_DIR = System.getProperty("java.io.tmpdir");
    		private  Log log = LogFactory.getLog(MagicRunner.class);
    		private Tool tool=null;
    		private File tmpJarFile=null;
    		/**
    		 * @param hadoopHome本地的hadoop目录
    		 * @param tool 实现tool的工具类
    		 * @param args main函数的args
    		 * @param classes classPath的路径 注意:如果此文件夹不需要被包含到classpath
    		 * @param jardir_3rdpart 第三方jar包路径,多个包以逗号分隔
    		 * @return
    		 * @throws Exception
    		 */
    		private MapReduceUtils(Tool tool, String[] args, String classes, String jardir_3rdpart) throws Exception{
    			this.jarDir_3rdPart = jardir_3rdpart;
    			this.classPath = classes;
    			this.args= args;
    			this.classPathAbsolutePath=new File(this.classPath).getAbsolutePath();	
    			this.tool=tool;
    		}
    		private int run() throws Exception {
    			try{
    				//第一步,将classPath中的的jar文件加入到list中;
    				addClassPathJarsToMap(this.classPath);
    				//第二步,将第三方指定jar包加入到list中;
    				add3rdPartJarsToMap(this.jarDir_3rdPart);
    				//第三步,将用户命令行参数中指定的jar包加入到list中;
    				configLibJars(this.args);
    			}finally{
    				printGenericCommandUsage(System.out);
    			}
    			//第四部,创建零时jar文件包
    		 try{
    				String tmpJarPath=createTempJar();
    				tmpJarFile=new File(tmpJarPath);
    				Configuration conf= tool.getConf();
    				if (conf == null) {
    					conf = new Configuration(true);
    				}
    				GenericOptionsParser parser = new GenericOptionsParser(conf,args);
    				addTmpJar(tmpJarPath,conf);
    				tool.setConf(conf);
    				String[] toolArgs = parser.getRemainingArgs();			
    				return tool.run(toolArgs);
    			}finally{			
    				//在此次虚拟机运行任务完毕的时候,执行addShutdownHook中的任务;
    				Runtime.getRuntime().addShutdownHook(new Thread() {
    					@Override
    					public void run() {
    						if(tmpJarFile!=null&&tmpJarFile.exists())
    						 tmpJarFile.delete();
    					}
    				});
    			}
    		}

    		public static int run (Tool tool, String[] args, String classPath, String jardir_3rdpart) throws Exception{
    			MapReduceUtils mapReduceUtils=new MapReduceUtils(tool, args, classPath, jardir_3rdpart);
    		    return mapReduceUtils.run();	
    		}

    		public static int run (Tool tool, String[] args, String classPath) throws Exception{
    			MapReduceUtils mapReduceUtils=new MapReduceUtils(tool, args, classPath,null);
    		    return mapReduceUtils.run();	
    		}
    		/**
    		 * 默认classPath是bin目录;
    		 * @param tool
    		 * @param args
    		 * @return
    		 * @throws Exception
    		 */
    		public static int run (Tool tool, String[] args) throws Exception{
    			MapReduceUtils mapReduceUtils=new MapReduceUtils(tool, args,"bin",null);
    		    return mapReduceUtils.run();	
    		}

    		/**
    		 * 和本地classpath不同的是,此参数是由逗号分隔的jar或者文件夹的集合
    		 * @param jarDir_3rdPart2
    		 */
    		private void add3rdPartJarsToMap(String jarDir_3rdPartPath) {
    			if(jarDir_3rdPartPath==null) return;
    			String[] paths=jarDir_3rdPartPath.split(",");
    			if(jarDir_3rdPartPath==null||jarDir_3rdPartPath.trim().length()<1)
    				return;
    			for(String p:paths){
    				File file=new File(p);
    				if(!file.exists()) continue;
    				addJarsToMap(p, jarsMap);
    			}

    		}
    		/**
    		 * 将classPath中的的jar文件加入到list中
    		 * @param classPath
    		 */
    		private void addClassPathJarsToMap(String classPath){
    			addJarsToMap(classPath, jarsMap);
    		}
    		/**
    		 * 将指定path对应的jar/class文件或者文件夹中的jar/class文件添加到map中,
    		 * @param path
    		 */
    		private void addJarsToMap(String path,Map<String,String> map){
    			if(path==null||path.trim().length()<1)
    				return;
    			File file=new File(path);
    			if(!file.exists())
    				return;
    			if(file.isDirectory()){
    				File[] fs=file.listFiles();
    				for(File f:fs){
    					addJarsToMap(f.getPath(), map);
    				}
    			}else{
    			     	if(path.endsWith(".jar")){
    			     		map.put(getFileName(path),path);
    			     	}else if(path.endsWith(".class")){			     		
    			     		map.put(path, this.classPathAbsolutePath);
    			     	}
    			}
    		}

    		private String getFileName(String path){
    			String fileSeparator=System.getProperty("file.separator");
    			String tmp=path;
    			String name="";
    			if(fileSeparator.equals("\\"))
    			{
    				String[] pp=path.split("\\\\");
    				if(pp.length>1)
    				{
    					name=pp[pp.length-1];
    				}else{
    					name=pp[0];
    				}

    			}else {
    				name=path.substring(tmp.lastIndexOf("/")+1);
    			}
    			return name;
    		}

    		private  void addTmpJar(String jarPath, Configuration conf) throws IOException {  
    		    System.setProperty("path.separator", ":");  
    		    FileSystem fs = FileSystem.getLocal(conf);  
    		    String newJarPath = new Path(jarPath).makeQualified(fs).toString();  
    		    String tmpjars = conf.get("tmpjars");  
    		    if (tmpjars == null || tmpjars.length() == 0) {  
    		        conf.set("tmpjars", newJarPath);  
    		    } else {  
    		        conf.set("tmpjars", tmpjars + "," + newJarPath);  
    		    }  
    		}  
    		/**
    		 * 将命令行中指定的libjar加入到classpath中,指定的jar集合以逗号分割;
    		 * @param args
    		 * @return
    		 * @throws ParseException
    		 */
    		private  void configLibJars(String[] args) throws ParseException {
    			String[] fileArr = null;
    			CommandLine commandLine = getCommandLine(args);
    			if (commandLine.hasOption("libjars")) {
    				String files = commandLine.getOptionValue("libjars");
    				log.info("find libjars :" + files);
    				fileArr = files.split(",");
    			}
    			for (int i = 0; fileArr != null && i < fileArr.length; i++) {
    				addJarsToMap(fileArr[i], jarsMap);
    			}
    		}

    		/**
    		 * 将命令行参数转换为相关的类
    		 * @param args
    		 * @return
    		 * @throws ParseException
    		 */
    		private  CommandLine getCommandLine(String[] args) throws ParseException {
    			CommandLineParser parser = new GnuParser();
    			@SuppressWarnings("static-access")
    			Option libjars = OptionBuilder.withArgName("paths").hasArg().withDescription("comma separated jar files to include in the classpath.")
    					.create("libjars");
    			Options opts = new Options();
    			opts.addOption(libjars);
    			CommandLine commandLine = parser.parse(opts, args, true);
    			return commandLine;
    		}
    		/**
    		 * 创建一个零时的jar文件;
    		 * 此jar文件中包括指定classpath中的jar文件
    		 * 命令行/依赖等指定的jar文件以及自定的源代码编译而成的class文件
    		 * @return 返回临时jar文件路径
    		 * @throws IOException
    		 */
    		private  String createTempJar() throws IOException {
    			Manifest manifest = new Manifest();
    			manifest.getMainAttributes().putValue("Manifest-Version", "1.0");
    			final File jarFile = File.createTempFile("MagicRunnerJob", ".jar", new File(TEMP_DIR));	      
    			//向一个jar文件中写入数据
    			JarOutputStream out = new JarOutputStream(new FileOutputStream(jarFile), manifest);
    			Set<String> jarNames=jarsMap.keySet();
    			for(String name:jarNames){
    				if(!name.endsWith(".jar"))
    				{//非jar文件的写入需要创建相关的文件夹
    					String value=jarsMap.get(name);
    					String string=new File(name).getAbsolutePath();
    					String path=string.substring(string.indexOf(value)+value.length()+1);
    					writeToTempJar(out,new File(name),path);
    				}else{
    					String path=jarsMap.get(name);
    					writeToTempJar(out, new File(path),name);
    				}
    			}
    			out.flush();
    			out.close();
    			String toReturn = jarFile.toURI().toString();
    			return processJarPath(toReturn);
    		}
    		/**
    		 * 得到jar文件的路径,去掉file等前缀
    		 * @param toReturn
    		 * @return
    		 * @throws UnsupportedEncodingException
    		 */
    		private static String processJarPath(String toReturn) throws UnsupportedEncodingException {
    			if (toReturn.startsWith("file:\\")) {
    				toReturn = toReturn.substring("file:\\".length());
    			}
    			if (toReturn.startsWith("file:")) {
    				toReturn = toReturn.substring("file:".length());
    			}
    			toReturn = toReturn.replaceAll("\\+", "%2B");
    			toReturn = URLDecoder.decode(toReturn, "UTF-8");
    			return toReturn.replaceAll("!.*$", "");
    		}
    		/**
    		 * 将rootDir文件或者文件夹中的所有内容压缩到out中
    		 */
    		private  void writeToTempJar(JarOutputStream out, File file, String relativepath) throws IOException {
    			if (file.isDirectory()) {
    				File[] fl = file.listFiles();
    				if (relativepath.length() > 0) {
    					relativepath = relativepath + "/";
    				}
    				for (int i = 0; i < fl.length; i++) {
    					writeToTempJar(out, fl[i], relativepath + fl[i].getName());
    				}
    			} else {
    				out.putNextEntry(new JarEntry(relativepath));
    				FileInputStream in = new FileInputStream(file);
    				byte[] buffer = new byte[2048];
    				int n = in.read(buffer);
    				while (n != -1) {
    					out.write(buffer, 0, n);
    					n = in.read(buffer);
    				}
    				in.close();
    			}
    		}

    		private void printGenericCommandUsage(PrintStream out) {
    			out.println("Generic options supported are");
    			out.println("-libjars <comma separated list of jars>    "
    					+ "This item must at first!!!!\nspecify comma separated jar files to include in the classpath.");
    			out.println("-conf <configuration file>     specify an application configuration file");
    			out.println("-D <property=value>            use value for given property");
    			out.println("-fs <local|namenode:port>      specify a namenode");
    			out.println("-jt <local|jobtracker:port>    specify a job tracker");
    			out.println("-files <comma separated list of files>    " + "specify comma separated files to be copied to the map reduce cluster");
    			out.println("-archives <comma separated list of archives>    " + "specify comma separated archives to be unarchived"
    					+ " on the compute machines.\n");
    			out.println("The general command line syntax is");

```java
			out.println("bin/hadoop command [genericOptions] [commandOptions]\n");
		}
}
```

# 4.最后,可能的异常

在hadoop插件或者此类中运行都可能发生如下异常:

Exception in thread "main" java.lang.UnsatisfiedLinkError: org.apache.hadoop.io.nativeio.NativeIO$Windows.access0(Ljava/lang/String;I)Z

如果是在hadoop查看中,出了将插件对应的winutils.exe等文件复制到本地hadoop的bin目录中;

其次两种方式都需要在源码中增加一个类:

此类来自hadoop的源代码org.apache.hadoop.io.nativeio

我们需要修改

public static boolean access(String path, AccessRight desiredAccess)  
        throws IOException {  
      return access0(path, desiredAccess.accessRight());      
    }

中的return 为return true;  

    /**
     * Licensed to the Apache Software Foundation (ASF) under one
     * or more contributor license agreements.  See the NOTICE file
     * distributed with this work for additional information
     * regarding copyright ownership.  The ASF licenses this file
     * to you under the Apache License, Version 2.0 (the
     * "License"); you may not use this file except in compliance
     * with the License.  You may obtain a copy of the License at
     *
     *     http://www.apache.org/licenses/LICENSE-2.0
     *
     * Unless required by applicable law or agreed to in writing, software
     * distributed under the License is distributed on an "AS IS" BASIS,
     * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
     * See the License for the specific language governing permissions and
     * limitations under the License.
     */
    package org.apache.hadoop.io.nativeio;

    import java.io.File;
    import java.io.FileDescriptor;
    import java.io.FileInputStream;
    import java.io.FileOutputStream;
    import java.io.IOException;
    import java.io.RandomAccessFile;
    import java.lang.reflect.Field;
    import java.nio.ByteBuffer;
    import java.nio.MappedByteBuffer;
    import java.nio.channels.FileChannel;
    import java.util.Map;
    import java.util.concurrent.ConcurrentHashMap;

    import org.apache.hadoop.classification.InterfaceAudience;
    import org.apache.hadoop.classification.InterfaceStability;
    import org.apache.hadoop.conf.Configuration;
    import org.apache.hadoop.fs.CommonConfigurationKeys;
    import org.apache.hadoop.fs.HardLink;
    import org.apache.hadoop.io.IOUtils;
    import org.apache.hadoop.io.SecureIOUtils.AlreadyExistsException;
    import org.apache.hadoop.util.NativeCodeLoader;
    import org.apache.hadoop.util.Shell;
    import org.apache.hadoop.util.PerformanceAdvisory;
    import org.apache.commons.logging.Log;
    import org.apache.commons.logging.LogFactory;

    import sun.misc.Unsafe;

    import com.google.common.annotations.VisibleForTesting;

    /**
     * JNI wrappers for various native IO-related calls not available in Java.
     * These functions should generally be used alongside a fallback to another
     * more portable mechanism.
     */

```java
@InterfaceAudience.Private
@InterfaceStability.Unstable
public class NativeIO {
    public static class POSIX {
        // Flags for open() call from bits/fcntl.h
        public static final int O_RDONLY   =    00;
        public static final int O_WRONLY   =    01;
        public static final int O_RDWR     =    02;
        public static final int O_CREAT    =  0100;
        public static final int O_EXCL     =  0200;
        public static final int O_NOCTTY   =  0400;
        public static final int O_TRUNC    = 01000;
        public static final int O_APPEND   = 02000;
        public static final int O_NONBLOCK = 04000;
        public static final int O_SYNC   =  010000;
        public static final int O_ASYNC  =  020000;
        public static final int O_FSYNC = O_SYNC;
        public static final int O_NDELAY = O_NONBLOCK;

        // Flags for posix_fadvise() from bits/fcntl.h
        /* No further special treatment.  */
        public static final int POSIX_FADV_NORMAL = 0;
        /* Expect random page references.  */
        public static final int POSIX_FADV_RANDOM = 1;
        /* Expect sequential page references.  */
        public static final int POSIX_FADV_SEQUENTIAL = 2;
        /* Will need these pages.  */
        public static final int POSIX_FADV_WILLNEED = 3;
        /* Don't need these pages.  */
        public static final int POSIX_FADV_DONTNEED = 4;
        /* Data will be accessed once.  */
        public static final int POSIX_FADV_NOREUSE = 5;
```

        /* Wait upon writeout of all pages
           in the range before performing the
           write.  */
        public static final int SYNC_FILE_RANGE_WAIT_BEFORE = 1;
        /* Initiate writeout of all those
           dirty pages in the range which are
           not presently under writeback.  */
        public static final int SYNC_FILE_RANGE_WRITE = 2;

        /* Wait upon writeout of all pages in
           the range after performing the
           write.  */
        public static final int SYNC_FILE_RANGE_WAIT_AFTER = 4;

        private static final Log LOG = LogFactory.getLog(NativeIO.class);

        private static boolean nativeLoaded = false;
        private static boolean fadvisePossible = true;
        private static boolean syncFileRangePossible = true;

        static final String WORKAROUND_NON_THREADSAFE_CALLS_KEY =
          "hadoop.workaround.non.threadsafe.getpwuid";
        static final boolean WORKAROUND_NON_THREADSAFE_CALLS_DEFAULT = true;

        private static long cacheTimeout = -1;

        private static CacheManipulator cacheManipulator = new CacheManipulator();

        public static CacheManipulator getCacheManipulator() {
          return cacheManipulator;
        }

        public static void setCacheManipulator(CacheManipulator cacheManipulator) {
          POSIX.cacheManipulator = cacheManipulator;
        }

        /**
         * Used to manipulate the operating system cache.
         */
        @VisibleForTesting
        public static class CacheManipulator {
          public void mlock(String identifier, ByteBuffer buffer,
              long len) throws IOException {
            POSIX.mlock(buffer, len);
          }

          public long getMemlockLimit() {
            return NativeIO.getMemlockLimit();
          }

          public long getOperatingSystemPageSize() {
            return NativeIO.getOperatingSystemPageSize();
          }

          public void posixFadviseIfPossible(String identifier,
            FileDescriptor fd, long offset, long len, int flags)
                throws NativeIOException {
            NativeIO.POSIX.posixFadviseIfPossible(identifier, fd, offset,
                len, flags);
          }

          public boolean verifyCanMlock() {
            return NativeIO.isAvailable();
          }
        }

        /**
         * A CacheManipulator used for testing which does not actually call mlock.
         * This allows many tests to be run even when the operating system does not
         * allow mlock, or only allows limited mlocking.
         */
        @VisibleForTesting
        public static class NoMlockCacheManipulator extends CacheManipulator {
          public void mlock(String identifier, ByteBuffer buffer,
              long len) throws IOException {
            LOG.info("mlocking " + identifier);
          }

          public long getMemlockLimit() {
            return 1125899906842624L;
          }

          public long getOperatingSystemPageSize() {
            return 4096;
          }

          public boolean verifyCanMlock() {
            return true;
          }
        }

        static {
          if (NativeCodeLoader.isNativeCodeLoaded()) {
            try {
              Configuration conf = new Configuration();
              workaroundNonThreadSafePasswdCalls = conf.getBoolean(
                WORKAROUND_NON_THREADSAFE_CALLS_KEY,
                WORKAROUND_NON_THREADSAFE_CALLS_DEFAULT);

              initNative();
              nativeLoaded = true;

              cacheTimeout = conf.getLong(
                CommonConfigurationKeys.HADOOP_SECURITY_UID_NAME_CACHE_TIMEOUT_KEY,
                CommonConfigurationKeys.HADOOP_SECURITY_UID_NAME_CACHE_TIMEOUT_DEFAULT) *
                1000;
              LOG.debug("Initialized cache for IDs to User/Group mapping with a " +
                " cache timeout of " + cacheTimeout/1000 + " seconds.");

            } catch (Throwable t) {
              // This can happen if the user has an older version of libhadoop.so
              // installed - in this case we can continue without native IO
              // after warning
              PerformanceAdvisory.LOG.debug("Unable to initialize NativeIO libraries", t);
            }
          }
        }

        /**
         * Return true if the JNI-based native IO extensions are available.
         */
        public static boolean isAvailable() {
          return NativeCodeLoader.isNativeCodeLoaded() && nativeLoaded;
        }

        private static void assertCodeLoaded() throws IOException {
          if (!isAvailable()) {
            throw new IOException("NativeIO was not loaded");
          }
        }

        /** Wrapper around open(2) */
        public static native FileDescriptor open(String path, int flags, int mode) throws IOException;
        /** Wrapper around fstat(2) */
        private static native Stat fstat(FileDescriptor fd) throws IOException;

        /** Native chmod implementation. On UNIX, it is a wrapper around chmod(2) */
        private static native void chmodImpl(String path, int mode) throws IOException;

        public static void chmod(String path, int mode) throws IOException {
          if (!Shell.WINDOWS) {
            chmodImpl(path, mode);
          } else {
            try {
              chmodImpl(path, mode);
            } catch (NativeIOException nioe) {
              if (nioe.getErrorCode() == 3) {
                throw new NativeIOException("No such file or directory",
                    Errno.ENOENT);
              } else {
                LOG.warn(String.format("NativeIO.chmod error (%d): %s",
                    nioe.getErrorCode(), nioe.getMessage()));
                throw new NativeIOException("Unknown error", Errno.UNKNOWN);
              }
            }
          }
        }

        /** Wrapper around posix_fadvise(2) */
        static native void posix_fadvise(
          FileDescriptor fd, long offset, long len, int flags) throws NativeIOException;

        /** Wrapper around sync_file_range(2) */
        static native void sync_file_range(
          FileDescriptor fd, long offset, long nbytes, int flags) throws NativeIOException;

        /**
         * Call posix_fadvise on the given file descriptor. See the manpage
         * for this syscall for more information. On systems where this
         * call is not available, does nothing.
         *
         * @throws NativeIOException if there is an error with the syscall
         */
        static void posixFadviseIfPossible(String identifier,
            FileDescriptor fd, long offset, long len, int flags)
            throws NativeIOException {
          if (nativeLoaded && fadvisePossible) {
            try {
              posix_fadvise(fd, offset, len, flags);
            } catch (UnsupportedOperationException uoe) {
              fadvisePossible = false;
            } catch (UnsatisfiedLinkError ule) {
              fadvisePossible = false;
            }
          }
        }

        /**
         * Call sync_file_range on the given file descriptor. See the manpage
         * for this syscall for more information. On systems where this
         * call is not available, does nothing.
         *
         * @throws NativeIOException if there is an error with the syscall
         */
        public static void syncFileRangeIfPossible(
            FileDescriptor fd, long offset, long nbytes, int flags)
            throws NativeIOException {
          if (nativeLoaded && syncFileRangePossible) {
            try {
              sync_file_range(fd, offset, nbytes, flags);
            } catch (UnsupportedOperationException uoe) {
              syncFileRangePossible = false;
            } catch (UnsatisfiedLinkError ule) {
              syncFileRangePossible = false;
            }
          }
        }

        static native void mlock_native(
            ByteBuffer buffer, long len) throws NativeIOException;

        /**
         * Locks the provided direct ByteBuffer into memory, preventing it from
         * swapping out. After a buffer is locked, future accesses will not incur
         * a page fault.
         *
         * See the mlock(2) man page for more information.
         *
         * @throws NativeIOException
         */
        static void mlock(ByteBuffer buffer, long len)
            throws IOException {
          assertCodeLoaded();
          if (!buffer.isDirect()) {
            throw new IOException("Cannot mlock a non-direct ByteBuffer");
          }
          mlock_native(buffer, len);
        }

        /**
         * Unmaps the block from memory. See munmap(2).
         *
         * There isn't any portable way to unmap a memory region in Java.
         * So we use the sun.nio method here.
         * Note that unmapping a memory region could cause crashes if code
         * continues to reference the unmapped code.  However, if we don't
         * manually unmap the memory, we are dependent on the finalizer to
         * do it, and we have no idea when the finalizer will run.
         *
         * @param buffer    The buffer to unmap.
         */
        public static void munmap(MappedByteBuffer buffer) {
          if (buffer instanceof sun.nio.ch.DirectBuffer) {
            sun.misc.Cleaner cleaner =
                ((sun.nio.ch.DirectBuffer)buffer).cleaner();
            cleaner.clean();
          }
        }

        /** Linux only methods used for getOwner() implementation */
        private static native long getUIDforFDOwnerforOwner(FileDescriptor fd) throws IOException;
        private static native String getUserName(long uid) throws IOException;

        /**
         * Result type of the fstat call
         */
        public static class Stat {
          private int ownerId, groupId;
          private String owner, group;
          private int mode;

          // Mode constants
          public static final int S_IFMT = 0170000;      /* type of file */
          public static final int   S_IFIFO  = 0010000;  /* named pipe (fifo) */
          public static final int   S_IFCHR  = 0020000;  /* character special */
          public static final int   S_IFDIR  = 0040000;  /* directory */
          public static final int   S_IFBLK  = 0060000;  /* block special */
          public static final int   S_IFREG  = 0100000;  /* regular */
          public static final int   S_IFLNK  = 0120000;  /* symbolic link */
          public static final int   S_IFSOCK = 0140000;  /* socket */
          public static final int   S_IFWHT  = 0160000;  /* whiteout */
          public static final int S_ISUID = 0004000;  /* set user id on execution */
          public static final int S_ISGID = 0002000;  /* set group id on execution */
          public static final int S_ISVTX = 0001000;  /* save swapped text even after use */
          public static final int S_IRUSR = 0000400;  /* read permission, owner */
          public static final int S_IWUSR = 0000200;  /* write permission, owner */
          public static final int S_IXUSR = 0000100;  /* execute/search permission, owner */

          Stat(int ownerId, int groupId, int mode) {
            this.ownerId = ownerId;
            this.groupId = groupId;
            this.mode = mode;
          }

          Stat(String owner, String group, int mode) {
            if (!Shell.WINDOWS) {
              this.owner = owner;
            } else {
              this.owner = stripDomain(owner);
            }
            if (!Shell.WINDOWS) {
              this.group = group;
            } else {
              this.group = stripDomain(group);
            }
            this.mode = mode;
          }

          @Override
          public String toString() {
            return "Stat(owner='" + owner + "', group='" + group + "'" +
              ", mode=" + mode + ")";
          }

          public String getOwner() {
            return owner;
          }
          public String getGroup() {
            return group;
          }
          public int getMode() {
            return mode;
          }
        }

        /**
         * Returns the file stat for a file descriptor.
         *
         * @param fd file descriptor.
         * @return the file descriptor file stat.
         * @throws IOException thrown if there was an IO error while obtaining the file stat.
         */

```java
public static Stat getFstat(FileDescriptor fd) throws IOException {
Stat stat = null;
if (!Shell.WINDOWS) {
stat = fstat(fd); 
stat.owner = getName(IdCache.USER, stat.ownerId);
stat.group = getName(IdCache.GROUP, stat.groupId);
} else {
try {
stat = fstat(fd);
} catch (NativeIOException nioe) {
if (nioe.getErrorCode() == 6) {
throw new NativeIOException("The handle is invalid.",
Errno.EBADF);
} else {
LOG.warn(String.format("NativeIO.getFstat error (%d): %s",
nioe.getErrorCode(), nioe.getMessage()));
throw new NativeIOException("Unknown error", Errno.UNKNOWN);
}
}
}
return stat;
}

private static String getName(IdCache domain, int id) throws IOException {
Map<Integer, CachedName> idNameCache = (domain == IdCache.USER)
? USER_ID_NAME_CACHE : GROUP_ID_NAME_CACHE;
String name;
CachedName cachedName = idNameCache.get(id);
long now = System.currentTimeMillis();
if (cachedName != null && (cachedName.timestamp + cacheTimeout) > now) {
name = cachedName.name;
} else {
name = (domain == IdCache.USER) ? getUserName(id) : getGroupName(id);
if (LOG.isDebugEnabled()) {
String type = (domain == IdCache.USER) ? "UserName" : "GroupName";
LOG.debug("Got " + type + " " + name + " for ID " + id +
" from the native implementation");
}
cachedName = new CachedName(name, now);
idNameCache.put(id, cachedName);
}
return name;
}

static native String getUserName(int uid) throws IOException;
static native String getGroupName(int uid) throws IOException;

private static class CachedName {
final long timestamp;
final String name;

public CachedName(String name, long timestamp) {
this.name = name;
this.timestamp = timestamp;
}
}

private static final Map<Integer, CachedName> USER_ID_NAME_CACHE =
new ConcurrentHashMap<Integer, CachedName>();

private static final Map<Integer, CachedName> GROUP_ID_NAME_CACHE =
new ConcurrentHashMap<Integer, CachedName>();

private enum IdCache { USER, GROUP }

public final static int MMAP_PROT_READ = 0x1; 
public final static int MMAP_PROT_WRITE = 0x2; 
public final static int MMAP_PROT_EXEC = 0x4; 

public static native long mmap(FileDescriptor fd, int prot,
boolean shared, long length) throws IOException;

public static native void munmap(long addr, long length)
throws IOException;
}

private static boolean workaroundNonThreadSafePasswdCalls = false;
```

      public static class Windows {
        // Flags for CreateFile() call on Windows
        public static final long GENERIC_READ = 0x80000000L;
        public static final long GENERIC_WRITE = 0x40000000L;

        public static final long FILE_SHARE_READ = 0x00000001L;
        public static final long FILE_SHARE_WRITE = 0x00000002L;
        public static final long FILE_SHARE_DELETE = 0x00000004L;

        public static final long CREATE_NEW = 1;
        public static final long CREATE_ALWAYS = 2;
        public static final long OPEN_EXISTING = 3;
        public static final long OPEN_ALWAYS = 4;
        public static final long TRUNCATE_EXISTING = 5;

        public static final long FILE_BEGIN = 0;
        public static final long FILE_CURRENT = 1;
        public static final long FILE_END = 2;

        public static final long FILE_ATTRIBUTE_NORMAL = 0x00000080L;

        /** Wrapper around CreateFile() on Windows */
        public static native FileDescriptor createFile(String path,
            long desiredAccess, long shareMode, long creationDisposition)
            throws IOException;

        /** Wrapper around SetFilePointer() on Windows */
        public static native long setFilePointer(FileDescriptor fd,
            long distanceToMove, long moveMethod) throws IOException;

        /** Windows only methods used for getOwner() implementation */
        private static native String getOwner(FileDescriptor fd) throws IOException;

        /** Supported list of Windows access right flags */
        public static enum AccessRight {
          ACCESS_READ (0x0001),      // FILE_READ_DATA
          ACCESS_WRITE (0x0002),     // FILE_WRITE_DATA
          ACCESS_EXECUTE (0x0020);   // FILE_EXECUTE

          private final int accessRight;
          AccessRight(int access) {
            accessRight = access;
          }

          public int accessRight() {
            return accessRight;
          }
        };

        /** Windows only method used to check if the current process has requested
         *  access rights on the given path. */
        private static native boolean access0(String path, int requestedAccess);

        /**
         * Checks whether the current process has desired access rights on
         * the given path.
         *
         * Longer term this native function can be substituted with JDK7
         * function Files#isReadable, isWritable, isExecutable.
         *
         * @param path input path
         * @param desiredAccess ACCESS_READ, ACCESS_WRITE or ACCESS_EXECUTE
         * @return true if access is allowed
         * @throws IOException I/O exception on error
         */
        public static boolean access(String path, AccessRight desiredAccess)
            throws IOException {
          //return access0(path, desiredAccess.accessRight());
          return true;
        }

        /**
         * Extends both the minimum and maximum working set size of the current
         * process.  This method gets the current minimum and maximum working set
         * size, adds the requested amount to each and then sets the minimum and
         * maximum working set size to the new values.  Controlling the working set
         * size of the process also controls the amount of memory it can lock.
         *
         * @param delta amount to increment minimum and maximum working set size
         * @throws IOException for any error
         * @see POSIX#mlock(ByteBuffer, long)
         */
        public static native void extendWorkingSetSize(long delta) throws IOException;

        static {
          if (NativeCodeLoader.isNativeCodeLoaded()) {
            try {
              initNative();
              nativeLoaded = true;
            } catch (Throwable t) {
              // This can happen if the user has an older version of libhadoop.so
              // installed - in this case we can continue without native IO
              // after warning
              PerformanceAdvisory.LOG.debug("Unable to initialize NativeIO libraries", t);
            }
          }
        }
      }

      private static final Log LOG = LogFactory.getLog(NativeIO.class);

      private static boolean nativeLoaded = false;

      static {
        if (NativeCodeLoader.isNativeCodeLoaded()) {
          try {
            initNative();
            nativeLoaded = true;
          } catch (Throwable t) {
            // This can happen if the user has an older version of libhadoop.so
            // installed - in this case we can continue without native IO
            // after warning
            PerformanceAdvisory.LOG.debug("Unable to initialize NativeIO libraries", t);
          }
        }
      }

      /**
       * Return true if the JNI-based native IO extensions are available.
       */
      public static boolean isAvailable() {
        return NativeCodeLoader.isNativeCodeLoaded() && nativeLoaded;
      }

      /** Initialize the JNI method ID and class ID cache */
      private static native void initNative();

      /**
       * Get the maximum number of bytes that can be locked into memory at any
       * given point.
       *
       * @return 0 if no bytes can be locked into memory;
       *         Long.MAX_VALUE if there is no limit;
       *         The number of bytes that can be locked into memory otherwise.
       */
      static long getMemlockLimit() {
        return isAvailable() ? getMemlockLimit0() : 0;
      }

      private static native long getMemlockLimit0();

      /**
       * @return the operating system's page size.
       */
      static long getOperatingSystemPageSize() {
        try {
          Field f = Unsafe.class.getDeclaredField("theUnsafe");
          f.setAccessible(true);
          Unsafe unsafe = (Unsafe)f.get(null);
          return unsafe.pageSize();
        } catch (Throwable e) {
          LOG.warn("Unable to get operating system page size.  Guessing 4096.", e);
          return 4096;
        }
      }

      private static class CachedUid {
        final long timestamp;
        final String username;
        public CachedUid(String username, long timestamp) {
          this.timestamp = timestamp;
          this.username = username;
        }
      }
      private static final Map<Long, CachedUid> uidCache =
          new ConcurrentHashMap<Long, CachedUid>();
      private static long cacheTimeout;
      private static boolean initialized = false;

      /**
       * The Windows logon name has two part, NetBIOS domain name and
       * user account name, of the format DOMAIN\UserName. This method
       * will remove the domain part of the full logon name.
       *
       * @param Fthe full principal name containing the domain
       * @return name with domain removed
       */
      private static String stripDomain(String name) {
        int i = name.indexOf('\\');
        if (i != -1)
          name = name.substring(i + 1);
        return name;
      }

      public static String getOwner(FileDescriptor fd) throws IOException {
        ensureInitialized();
        if (Shell.WINDOWS) {
          String owner = Windows.getOwner(fd);
          owner = stripDomain(owner);
          return owner;
        } else {
          long uid = POSIX.getUIDforFDOwnerforOwner(fd);
          CachedUid cUid = uidCache.get(uid);
          long now = System.currentTimeMillis();
          if (cUid != null && (cUid.timestamp + cacheTimeout) > now) {
            return cUid.username;
          }
          String user = POSIX.getUserName(uid);
          LOG.info("Got UserName " + user + " for UID " + uid
              + " from the native implementation");
          cUid = new CachedUid(user, now);
          uidCache.put(uid, cUid);
          return user;
        }
      }

      /**
       * Create a FileInputStream that shares delete permission on the
       * file opened, i.e. other process can delete the file the
       * FileInputStream is reading. Only Windows implementation uses
       * the native interface.
       */
      public static FileInputStream getShareDeleteFileInputStream(File f)
          throws IOException {
        if (!Shell.WINDOWS) {
          // On Linux the default FileInputStream shares delete permission
          // on the file opened.
          //
          return new FileInputStream(f);
        } else {
          // Use Windows native interface to create a FileInputStream that
          // shares delete permission on the file opened.
          //
          FileDescriptor fd = Windows.createFile(
              f.getAbsolutePath(),
              Windows.GENERIC_READ,
              Windows.FILE_SHARE_READ |
                  Windows.FILE_SHARE_WRITE |
                  Windows.FILE_SHARE_DELETE,
              Windows.OPEN_EXISTING);
          return new FileInputStream(fd);
        }
      }

      /**
       * Create a FileInputStream that shares delete permission on the
       * file opened at a given offset, i.e. other process can delete
       * the file the FileInputStream is reading. Only Windows implementation
       * uses the native interface.
       */
      public static FileInputStream getShareDeleteFileInputStream(File f, long seekOffset)
          throws IOException {
        if (!Shell.WINDOWS) {
          RandomAccessFile rf = new RandomAccessFile(f, "r");
          if (seekOffset > 0) {
            rf.seek(seekOffset);
          }
          return new FileInputStream(rf.getFD());
        } else {
          // Use Windows native interface to create a FileInputStream that
          // shares delete permission on the file opened, and set it to the
          // given offset.
          //
          FileDescriptor fd = NativeIO.Windows.createFile(
              f.getAbsolutePath(),
              NativeIO.Windows.GENERIC_READ,
              NativeIO.Windows.FILE_SHARE_READ |
                  NativeIO.Windows.FILE_SHARE_WRITE |
                  NativeIO.Windows.FILE_SHARE_DELETE,
              NativeIO.Windows.OPEN_EXISTING);
          if (seekOffset > 0)
            NativeIO.Windows.setFilePointer(fd, seekOffset, NativeIO.Windows.FILE_BEGIN);
          return new FileInputStream(fd);
        }
      }

      /**
       * Create the specified File for write access, ensuring that it does not exist.
       * @param f the file that we want to create
       * @param permissions we want to have on the file (if security is enabled)
       *
       * @throws AlreadyExistsException if the file already exists
       * @throws IOException if any other error occurred
       */
      public static FileOutputStream getCreateForWriteFileOutputStream(File f, int permissions)
          throws IOException {
        if (!Shell.WINDOWS) {
          // Use the native wrapper around open(2)
          try {
            FileDescriptor fd = NativeIO.POSIX.open(f.getAbsolutePath(),
                NativeIO.POSIX.O_WRONLY | NativeIO.POSIX.O_CREAT
                    | NativeIO.POSIX.O_EXCL, permissions);
            return new FileOutputStream(fd);
          } catch (NativeIOException nioe) {
            if (nioe.getErrno() == Errno.EEXIST) {
              throw new AlreadyExistsException(nioe);
            }
            throw nioe;
          }
        } else {
          // Use the Windows native APIs to create equivalent FileOutputStream
          try {
            FileDescriptor fd = NativeIO.Windows.createFile(f.getCanonicalPath(),
                NativeIO.Windows.GENERIC_WRITE,
                NativeIO.Windows.FILE_SHARE_DELETE
                    | NativeIO.Windows.FILE_SHARE_READ
                    | NativeIO.Windows.FILE_SHARE_WRITE,
                NativeIO.Windows.CREATE_NEW);
            NativeIO.POSIX.chmod(f.getCanonicalPath(), permissions);
            return new FileOutputStream(fd);
          } catch (NativeIOException nioe) {
            if (nioe.getErrorCode() == 80) {
              // ERROR_FILE_EXISTS
              // 80 (0x50)
              // The file exists
              throw new AlreadyExistsException(nioe);
            }
            throw nioe;
          }
        }
      }

      private synchronized static void ensureInitialized() {
        if (!initialized) {
          cacheTimeout =
              new Configuration().getLong("hadoop.security.uid.cache.secs",
                  4*60*60) * 1000;
          LOG.info("Initialized cache for UID to User mapping with a cache" +
              " timeout of " + cacheTimeout/1000 + " seconds.");
          initialized = true;
        }
      }

      /**
       * A version of renameTo that throws a descriptive exception when it fails.
       *
       * @param src                  The source path
       * @param dst                  The destination path
       *
       * @throws NativeIOException   On failure.
       */
      public static void renameTo(File src, File dst)
          throws IOException {
        if (!nativeLoaded) {
          if (!src.renameTo(dst)) {
            throw new IOException("renameTo(src=" + src + ", dst=" +
              dst + ") failed.");
          }
        } else {
          renameTo0(src.getAbsolutePath(), dst.getAbsolutePath());
        }
      }

      public static void link(File src, File dst) throws IOException {
        if (!nativeLoaded) {
          HardLink.createHardLink(src, dst);
        } else {
          link0(src.getAbsolutePath(), dst.getAbsolutePath());
        }
      }

      /**
       * A version of renameTo that throws a descriptive exception when it fails.
       *
       * @param src                  The source path
       * @param dst                  The destination path
       *
       * @throws NativeIOException   On failure.
       */
      private static native void renameTo0(String src, String dst)
          throws NativeIOException;

      private static native void link0(String src, String dst)
          throws NativeIOException;

      /**
       * Unbuffered file copy from src to dst without tainting OS buffer cache
       *
       * In POSIX platform:
       * It uses FileChannel#transferTo() which internally attempts
       * unbuffered IO on OS with native sendfile64() support and falls back to
       * buffered IO otherwise.
       *
       * It minimizes the number of FileChannel#transferTo call by passing the the
       * src file size directly instead of a smaller size as the 3rd parameter.
       * This saves the number of sendfile64() system call when native sendfile64()
       * is supported. In the two fall back cases where sendfile is not supported,
       * FileChannle#transferTo already has its own batching of size 8 MB and 8 KB,
       * respectively.
       *
       * In Windows Platform:
       * It uses its own native wrapper of CopyFileEx with COPY_FILE_NO_BUFFERING
       * flag, which is supported on Windows Server 2008 and above.
       *
       * Ideally, we should use FileChannel#transferTo() across both POSIX and Windows
       * platform. Unfortunately, the wrapper(Java_sun_nio_ch_FileChannelImpl_transferTo0)
       * used by FileChannel#transferTo for unbuffered IO is not implemented on Windows.
       * Based on OpenJDK 6/7/8 source code, Java_sun_nio_ch_FileChannelImpl_transferTo0
       * on Windows simply returns IOS_UNSUPPORTED.
       *
       * Note: This simple native wrapper does minimal parameter checking before copy and
       * consistency check (e.g., size) after copy.
       * It is recommended to use wrapper function like
       * the Storage#nativeCopyFileUnbuffered() function in hadoop-hdfs with pre/post copy
       * checks.
       *
       * @param src                  The source path
       * @param dst                  The destination path
       * @throws IOException
       */

```java
public static void copyFileUnbuffered(File src, File dst) throws IOException {
if (nativeLoaded && Shell.WINDOWS) {
copyFileUnbuffered0(src.getAbsolutePath(), dst.getAbsolutePath());
} else {
FileInputStream fis = null;
FileOutputStream fos = null;
FileChannel input = null;
FileChannel output = null;
try {
fis = new FileInputStream(src);
fos = new FileOutputStream(dst);
input = fis.getChannel();
output = fos.getChannel();
long remaining = input.size();
long position = 0;
long transferred = 0;
while (remaining > 0) {
transferred = input.transferTo(position, remaining, output);
remaining -= transferred;
position += transferred;
}
} finally {
IOUtils.cleanup(LOG, output);
IOUtils.cleanup(LOG, fos);
IOUtils.cleanup(LOG, input);
IOUtils.cleanup(LOG, fis);
}
}
}

private static native void copyFileUnbuffered0(String src, String dst)
throws NativeIOException;
}
```

# 5.调用方式

```java
package mapreduce;

import java.io.IOException;
import java.util.StringTokenizer;

import org.apache.commons.configuration.ConfigurationException;
import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.conf.Configured;
import org.apache.hadoop.fs.Path;
import org.apache.hadoop.io.IntWritable;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Job;
import org.apache.hadoop.mapreduce.Mapper;
import org.apache.hadoop.mapreduce.Reducer;
import org.apache.hadoop.mapreduce.lib.input.FileInputFormat;
import org.apache.hadoop.mapreduce.lib.output.FileOutputFormat;
import org.apache.hadoop.util.Tool;

import com.tingfeng.utilpackage.hadoop.mapreduce.MapReduceUtils;

public class WordCount  extends Configured implements Tool {

	public static class TokenizerMapper extends Mapper<Object, Text, Text, IntWritable> {

		private final static IntWritable one = new IntWritable(1);
		private Text word = new Text();

		public void map(Object key, Text value, Context context) throws IOException, InterruptedException {
			StringTokenizer itr = new StringTokenizer(value.toString());
			while (itr.hasMoreTokens()) {
				word.set(itr.nextToken());
				context.write(word, one);
			}
			new ConfigurationException();
		}
	}

	public static class IntSumReducer extends Reducer<Text, IntWritable, Text, IntWritable> {
		private IntWritable result = new IntWritable();

		public void reduce(Text key, Iterable<IntWritable> values, Context context) throws IOException, InterruptedException {
			int sum = 0;
			for (IntWritable val : values) {
				sum += val.get();
			}
			result.set(sum);
			context.write(key, result);
		}
	}

	public static void main(String[] args) throws Exception {
		MapReduceUtils.run(new WordCount(), args);
	}

	@Override
	public int run(String[] otherArgs) throws Exception {

		Configuration conf;
		conf= getConf();
		if (otherArgs.length != 2) {
			System.err.println("Usage: wordcount <in> <out>");
			System.exit(2);
		}
		Job job = new Job(conf, "word count");
		job.setJarByClass(WordCount.class);
		job.setMapperClass(TokenizerMapper.class);
		job.setCombinerClass(IntSumReducer.class);
		job.setReducerClass(IntSumReducer.class);
		job.setOutputKeyClass(Text.class);
		job.setOutputValueClass(IntWritable.class);
		FileInputFormat.addInputPath(job, new Path(otherArgs[0]));
		FileOutputFormat.setOutputPath(job, new Path(otherArgs[1]));
		return job.waitForCompletion(true) ? 0 : 1;
	}	
}
```

# 6.ToolRunner

如果不上传相关的jar包,可以试试ToolRunner方法;

public static void main(String[] args) throws Exception {  
Configuration conf = new Configuration();  
ToolRunner.run(conf, new MultiMapMain(), args); // 调用run方法  
//MapReduceUtils.run(new MultiMapMain(), args);  
}

public class MultiMapMain extends Configuration implements Tool   
