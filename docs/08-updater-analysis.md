# Updater Analysis

## 背景

早期尝试过使用 standalone `Updater.exe` 直接选择本地目录刷入。原版 Updater 在选择目录后显示 `No updates are available`。

推测原因包括：

- 版本号相同导致 no-update gate；
- standalone Updater 对本地目录文件名有旧格式过滤；
- Connectivity Kit 和 standalone Updater 的入口逻辑不同。

## 文件名过滤

反汇编显示 standalone Updater 早期本地目录扫描路径接受旧文件名：

```text
APPSDISK.DAT
BESTAARM.ROM
MASTER.DAT
```

而官方 20250915 包使用：

```text
PRIME_APP.DAT
PRIME_OS.ROM
PRIME_MASTER.DAT
```

因此曾尝试两条线：

- 把 package 改成旧文件名；
- patch Updater 让它接受 PrimeG1 新文件名。

## 版本/no-update gate

还定位到 no-update 相关分支，实验中尝试让其绕过版本比较。

仓库保留了相关 xref 和 manifest：

```text
reports/updater_no_updates_xrefs.json
reports/connkit_no_updates_xrefs.json
tools/updater-experiments/
```

这些文件只用于记录探索过程，不是推荐路线。

## 实测结果

patched standalone Updater 在本地直接闪退。

原版 standalone Updater 仍显示无可用更新。

因此 standalone Updater 路线被否决。

## 最终采用路线

用户实测修改：

```text
Documents\HP Connectivity Kit\固件\PrimeG1\release_info_CHS.html
```

后，Connectivity Kit 更新页面同步显示修改内容。这说明官方 Connectivity Kit 更新入口确实读取该本地缓存。

最终路线改为：

1. 生成 patched `PRIME_APP.DAT`；
2. 重新计算 `Prime_FW.md5`；
3. 替换 Connectivity Kit 的 G1 本地固件缓存；
4. 从官方 Connectivity Kit 入口触发更新。

这比继续 patch standalone Updater 更稳。


