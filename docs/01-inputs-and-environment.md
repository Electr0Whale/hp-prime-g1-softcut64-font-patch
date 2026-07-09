# Inputs And Environment

## 必需输入

你需要准备官方 HP Prime G1 20250915 固件目录，至少包含：

```text
PRIME_APP.DAT
PRIME_MASTER.DAT
PRIME_OS.ROM
Prime_FW.md5
```

如果你的目录里还有 `Update.ini`、`release_info_*.html` 等 Connectivity Kit 元数据，`make-flash-package` 会一并复制到输出包里。

本项目不提供这些文件。

## 推荐环境

Windows + PowerShell 7：

```powershell
pwsh --version
python --version
```

Python 3.10+ 即可。脚本只用标准库。

推荐目录变量：

```powershell
$repo = 'D:\Download\hp-prime-g1-softcut64-font-patch'
$fw = 'D:\Download\HP_Prime_Calculator_Firmware_20250915'
$work = 'D:\Download\hpprime-softcut64-work'
```

`$repo` 是本仓库。

`$fw` 是你自己取得的官方固件目录。

`$work` 是本地生成目录。它会包含提取出的字体、patched ELF、patched `PRIME_APP.DAT` 等文件，不应提交到 Git。

## 官方工具

推荐安装 HP Connectivity Kit。当前可行刷入路线依赖它的 G1 本地固件缓存目录：

```text
%USERPROFILE%\Documents\HP Connectivity Kit\固件\PrimeG1
```

不同语言环境下，`固件` 这一层可能显示为本地化名称。可以通过修改该目录里的 `release_info_CHS.html` 并观察更新页面是否同步变化来确认 Connectivity Kit 正在读取该缓存。

## 版本检查

本项目的关键 MD5 是：

```text
PRIME_APP.DAT stock 20250915      663d1f7e4d4279286387f9c29e688f78
armfir.elf stock 20250915         9e1ed504c294e70ff478e0bd5553c441
armfir.elf softcut64              32ac6681f1a8287db20fbe33d0035fe7
PRIME_APP.DAT softcut64 repacked  59c9a785212599acd5b676bf72e6b5c2
```

如果你的官方 `PRIME_APP.DAT` 或提取出的 `armfir.elf` MD5 不一致，不要直接套用本补丁。先重新做静态定位。


