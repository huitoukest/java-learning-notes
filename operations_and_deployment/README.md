# operations_and_deployment 目录说明

运维相关：操作系统、Nginx 配置、常用配置文件与问题复盘。

## 文章索引

### config

- [ehcache2.x配置文件详解](<config/ehcache2.x配置文件详解.md>) — 一般ehcache的配置文件名称是ehcache-setting.xml（ehcache、缓存、配置、入门教程）
- [Log4j的配置文件的基本示例](<config/Log4j的配置文件的基本示例.md>) — 其中#表示行注释,这个配置文件拿过去就能够用,常用的也都具有了:（log4j、配置文件、示例）
- [log4j配置说明和示例](<config/log4j配置说明和示例.md>) — Log4J的配置文件Configuration File就是用来设置记录器的级别、存放器和（log4j、日志、配置、说明）

### nginx

- [nginx中文件路径映射配置注意事项：alias与root说明](<nginx/nginx中文件路径映射配置注意事项：alias与root说明.md>) — 在配置文件映射的时候，如果使用了正则表达式，那么可能会出现无法访问文件，nginx可能会将所有的（nginx、反向代理）

### operating_system/linux

- [Cygwin中如何像在Ubuntu中一样安装软件](<operating_system/linux/Cygwin中如何像在Ubuntu中一样安装软件.md>) — 1.通过cygwin客户端安装必须的软件支持包wget tar gawk bzip2（apt-cyg、cygwin）
- [Linux下ssh免密码登录配置(20160309)](<operating_system/linux/Linux下ssh免密码登录配置(20160309).md>) — 本文以Ubuntu14系统为示例,在安装好相应的ssh server和client之后,默认支持ssh免密码登录;假如现在有两台机器A和B,A想登录B的时候免密码ssh登录;（linux、ssh、免密码）
- [Ubuntu 14和 Win7 下NFS服务器与客户端配置(Ubuntu 14.04.02)](<operating_system/linux/Ubuntu 14和 Win7 下NFS服务器与客户端配置(Ubuntu 14.04.02).md>) — $ sudo apt-get install nfs-kernel-server（linux、ubuntu、nfs）
- [Ubuntu14 Could not open file /var/lib/dpkg/status - open (2: No such file or directory)](<operating_system/linux/Ubuntu14 Could not open file _var_lib_dpkg_status - open (2_ No such file or dir.md>) — 如果不小心删除了/var/lib/dpkg下的所有文件,可以尝试如下的解决方案:（ubuntu error）
- [Ubuntu14.04.2下nginx1.6和sticky1.1模块的安装与简单配置](<operating_system/linux/Ubuntu14.04.2下nginx1.6和sticky1.1模块的安装与简单配置.md>) — 写作日期:20160201（ubuntu、nginx、linux、sticky）
- [windows下通过软连接创建/模拟 '伪' linux文件系统](<operating_system/linux/windows下通过软连接创建_模拟 '伪' linux文件系统.md>) — 基于一般JEE开发在window下，而部署在linux下的情况。如果windows下的文件系统结构和linux下类似，那么能带来不少的方便，部署的时候也不用修改相关的参数。（windows、软连接、linux、文件系统）

### tools

- [SSH 连接 Gerrit老版本 失败问题复盘](<tools/SSH 连接 Gerrit老版本 失败问题复盘.md>) — 问题类型: SSH 协议兼容性导致的 Git 远程仓库连接失败（ssh、运维）
