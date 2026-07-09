# Connectivity Kit 本地缓存刷入 softcut64

## 当前状态

已将 HP Connectivity Kit 的本地 G1 固件缓存改为 softcut64：

```text
%USERPROFILE%\Documents\HP Connectivity Kit\固件\PrimeG1
```

其中：

```text
PRIME_APP.DAT     = softcut64 patched PRIME_APP.DAT
PRIME_MASTER.DAT  = 官方原版
PRIME_OS.ROM      = 官方原版
Prime_FW.md5      = 按当前缓存实际文件重算
Update.ini        = 官方原版写入映射
```

softcut64 `PRIME_APP.DAT` MD5：

```text
59c9a785212599acd5b676bf72e6b5c2
```

## 刷入前校验

运行：

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File "<work>\connectivity_cache_patch\Verify-ConnectivityCacheSoftcut64.ps1"
```

必须看到：

```text
Connectivity cache is prepared for softcut64 update.
```

## 刷入步骤

1. 关闭当前已经打开的更新弹窗。
2. 关闭并重新打开 HP Connectivity Kit，避免它沿用旧缓存。
3. 连接 HP Prime G1，确认 Calculators pane 能识别。
4. 先备份计算器数据。
5. 从官方 Connectivity Kit 入口进入固件更新：

```text
Calculators pane -> 右键计算器 -> Update firmware
```

或使用你已经验证可显示本地 CHS 说明页的“检查更新/更新固件”入口。

6. 确认页面仍显示你修改过的 CHS 说明文本；这说明它正在读取该本地缓存目录。
7. 点击更新。
8. 更新过程中不要断开 USB，不要按 reset，不要关闭 Connectivity Kit。
9. 等待计算器进入 Recovery Mode、写入完成并重启。

## 回滚到官方固件

如需回滚，先把本地缓存切回 stock：

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File "<work>\connectivity_cache_patch\Set-PrimeG1CacheStock.ps1"
```

然后重新打开 HP Connectivity Kit，用同一个官方更新入口刷入。

回滚后如果要重新准备 softcut64 缓存：

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File "<work>\connectivity_cache_patch\Set-PrimeG1CacheSoftcut64.ps1"
```

## 原始缓存备份

已备份到：

```text
<work>\connectivity_cache_patch\PrimeG1_before_softcut64_20260710_051613
```

原样恢复脚本：

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File "<work>\connectivity_cache_patch\Restore-PrimeG1Cache.ps1"
```

注意：该原样备份保留了你测试时修改过的 `release_info_CHS.html`，所以更推荐用 `Set-PrimeG1CacheStock.ps1` 做固件回滚准备。


