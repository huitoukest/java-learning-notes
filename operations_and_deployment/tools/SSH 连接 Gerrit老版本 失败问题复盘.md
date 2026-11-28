---
title: "SSH 连接 Gerrit老版本 失败问题复盘"
date: "2026-04-09 18:09:38"
categories: []
tags: ["ssh", "运维"]
---

# SSH 连接 Gerrit老版本 失败问题复盘

## 问题概述

**问题类型**: SSH 协议兼容性导致的 Git 远程仓库连接失败

**影响范围**: 无法通过 SSH 协议克隆或推送 Gerrit 代码仓库

**问题现象**:

```bash
ssh_dispatch_run_fatal: Connection to 10.0.0.100 port 2222: incorrect signature
fatal: Could not read remote repository.
```

---

## 环境信息

| 项目         | 示例值          |
| ------------ | --------------- |
| 代码托管平台 | Gerrit          |
| 平台版本     | 2.14.6          |
| 服务器域名   | git.example.com |
| 服务器IP     | 10.0.0.100      |
| SSH 端口     | 2222            |
| 用户名       | developer01     |
| 私钥文件     | ~/.ssh/git_key  |
| 项目名称     | myproject       |
| SSH 客户端   | OpenSSH 10.2p1  |
| OpenSSL 版本 | 3.5.5           |
| 操作系统     | Windows 11      |

---

## 排查思路

### 第一步：验证 SSH 连接基本连通性

**目标**: 确认网络层和 SSH 协议层是否可达

```bash
ssh -T -p 2222 developer01@git.example.com
```

**结果**: 失败，出现 `incorrect signature` 错误

**分析**: 错误发生在 SSH 密钥交换完成之后、认证之前，说明：

- 网络连通性正常
- SSH 协议版本协商成功
- 问题出在密钥签名验证环节

---

### 第二步：检查 SSH 配置和密钥权限

**目标**: 排查常见的 SSH 配置错误

```bash
# 查看 SSH 配置文件
cat ~/.ssh/config

# 查看私钥文件权限
ls -la ~/.ssh/git_key
```

**发现的配置**:

```bash
Host git.example.com
    HostName git.example.com
    User developer01
    Port 2222
    IdentityFile ~/.ssh/git_key
    IdentitiesOnly yes
    KexAlgorithms ecdh-sha2-nistp256,diffie-hellman-group-exchange-sha256
    PubkeyAcceptedAlgorithms ssh-rsa
    HostKeyAlgorithms ssh-ed25519,ssh-rsa
```

**发现的问题**: 私钥权限为 644（应为 600）

```bash
# 修复 Windows 下的文件权限
icacls "C:\Users\user\.ssh\git_key" /inheritance:r /grant:r user:R
```

**结果**: 权限修复后问题依旧

---

### 第三步：获取详细调试日志

**目标**: 定位具体失败点

```bash
ssh -vvv -T -p 2222 developer01@git.example.com 2>&1 | tail -50
```

**关键日志**:

```bash
debug1: SSH2_MSG_KEXINIT received
debug2: KEX algorithms: ecdh-sha2-nistp256,...
debug2: host key algorithms: ssh-ed25519,ssh-rsa
debug1: kex: algorithm: ecdh-sha2-nistp256
debug1: Server host key: ssh-ed25519 SHA256:xxxxx
debug1: Found key in /c/Users/user/.ssh/known_hosts:4
debug2: ssh_ed25519_verify: crypto_sign_ed25519_open failed: -1
ssh_dispatch_run_fatal: Connection to 10.0.0.100 port 2222: incorrect signature
```

**根因定位**: `ssh_ed25519_verify: crypto_sign_ed25519_open failed`

---

### 第四步：版本兼容性分析

**发现**:

- OpenSSH 10.2p1 默认优先使用 ed25519 host key
- Gerrit 2.14.6 (2017年发布) 的 ed25519 签名验证存在兼容性问题
- Windows 环境下 OpenSSL 3.5.5 与老版本 Gerrit 的 Ed25519 实现不兼容

---

## 解决方案

### 方案一：强制使用 ssh-rsa（临时方案）

在所有 SSH 相关命令中添加 `-o HostKeyAlgorithms=ssh-rsa` 参数：

```bash
# 测试 SSH 连接
ssh -o HostKeyAlgorithms=ssh-rsa -T -p 2222 developer01@git.example.com

# Git 克隆
GIT_SSH_COMMAND="ssh -o HostKeyAlgorithms=ssh-rsa" \
    git clone ssh://developer01@git.example.com:2222/myproject

# 拉取/推送代码
GIT_SSH_COMMAND="ssh -o HostKeyAlgorithms=ssh-rsa" \
    git pull origin main
```

### 方案二：下载 commit-msg hook

Gerrit 需要的 commit-msg hook 无法通过 scp 获取（ssh-rsa 模式下 scp 子系统被拒绝），使用 curl 下载：

```bash
curl -s http://git.example.com:8080/tools/hooks/commit-msg \
    -o myproject/.git/hooks/commit-msg
chmod +x myproject/.git/hooks/commit-msg
```

---

## 永久配置建议

为了避免每次手动指定算法，可以在 SSH config 中添加配置：

```ssh-config
Host git.example.com
    HostName git.example.com
    User developer01
    Port 2222
    IdentityFile ~/.ssh/git_key
    IdentitiesOnly yes
    # 强制使用 RSA 算法，兼容老版本 Gerrit
    HostKeyAlgorithms ssh-rsa
```

> **注意**: 这种配置会降低安全性，仅建议在无法升级 Gerrit 版本的情况下使用。

---

## 关键命令速查

| 场景                  | 命令                                                         |
| --------------------- | ------------------------------------------------------------ |
| 测试 SSH 连接         | `ssh -o HostKeyAlgorithms=ssh-rsa -T -p 2222 developer01@git.example.com` |
| 克隆仓库              | `GIT_SSH_COMMAND="ssh -o HostKeyAlgorithms=ssh-rsa" git clone ssh://developer01@git.example.com:2222/myproject` |
| 查看详细日志          | `ssh -vvv -T -p 2222 developer01@git.example.com`            |
| 清除旧 host key       | `ssh-keygen -R "[git.example.com]:2222"`                     |
| 查看 SSH 版本         | `ssh -V`                                                     |
| 查看 OpenSSL 版本     | `openssl version`                                            |
| 下载 hook             | `curl -s http://git.example.com:8080/tools/hooks/commit-msg -o .git/hooks/commit-msg` |
| 修复 Windows 文件权限 | `icacls "C:\Users\user\.ssh\git_key" /inheritance:r /grant:r user:R` |

---

## 根因总结

| 因素             | 说明                                                         |
| ---------------- | ------------------------------------------------------------ |
| **直接原因**     | OpenSSH 10.x 使用 Ed25519 host key，与 Gerrit 2.14.6 的签名验证不兼容 |
| **深层原因**     | OpenSSL 3.5.5 的 Ed25519 实现与老版本 Gerrit 的 SSH 服务端不兼容 |
| **触发条件**     | OpenSSH 10.x 默认优先使用 ed25519 算法（ssh-ed25519）        |
| **影响范围**     | 所有使用 Ed25519 算法连接的 Gerrit 2.14.x 版本               |
| **根本解决方案** | 升级 Gerrit 到支持 Ed25519 的版本（建议 3.0+）               |

---

## 经验教训

1. **协议兼容性要关注版本差**: 新版 SSH 客户端默认算法与旧版服务器可能不兼容
2. **调试信息要仔细看**: `ssh_ed25519_verify failed` 明确指出了 Ed25519 验证失败
3. **Windows 权限特殊处理**: `chmod` 在 Windows 下无效，需用 `icacls`
4. **保留原始日志**: verbose 模式的日志 (-vvv) 是排查 SSH 问题的关键
5. **临时方案要考虑全面**: 指定 ssh-rsa 后 scp 子系统可能被拒绝，需要备选方案获取 hook

---

## 延伸阅读

- [OpenSSH 10.0 Release Notes](https://www.openssh.com/txt/release-10.0) - 了解默认算法变更
- [Gerrit Code Review 2.14 Release Notes](https://www.gerritcodereview.com/2.14.html)
- [SSH Key Algorithm Compatibility](https://man.openbsd.org/ssh_config#HostKeyAlgorithms)
