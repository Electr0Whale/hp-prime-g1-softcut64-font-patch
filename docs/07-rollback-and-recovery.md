# Rollback And Recovery

## 先准备回滚包

刷入 patched 包前，必须准备 stock package。

最简单方式是用官方固件目录作为回滚 package，或复制一份：

```powershell
$stock = "$work\flash_package_stock"
New-Item -ItemType Directory -Force -Path $stock | Out-Null
Copy-Item -LiteralPath "$fw\*" -Destination $stock -Recurse -Force
```

验证 stock package 内部 `Prime_FW.md5` 是否匹配：

```powershell
& "$repo\tools\connectivity-cache\Verify-PrimeG1CachePackage.ps1" `
  -CachePath $stock `
  -ExpectedPrimeAppMd5 '663d1f7e4d4279286387f9c29e688f78'
```

## 回滚 Connectivity Kit 缓存到 stock

关闭 HP Connectivity Kit 后运行：

```powershell
$cache = Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'HP Connectivity Kit\固件\PrimeG1'

& "$repo\tools\connectivity-cache\Install-PrimeG1CachePackage.ps1" `
  -PackagePath $stock `
  -CachePath $cache `
  -BackupRoot "$work\cache_backups"
```

重新打开 Connectivity Kit，用同一个更新入口刷回官方固件。

## 恢复原缓存备份

如果你只想恢复刷 patched 前的缓存目录：

```powershell
& "$repo\tools\connectivity-cache\Restore-PrimeG1CacheBackup.ps1" `
  -BackupPath "$work\cache_backups\PrimeG1_before_patch_YYYYMMDD_HHMMSS" `
  -CachePath $cache
```

注意：恢复缓存不等于回滚计算器固件。它只是把电脑上的 Connectivity Kit 缓存文件恢复。

## 刷入失败时

如果更新中断、设备不启动、或字体严重不可读：

1. 不要继续尝试新的实验包。
2. 保留 USB 连接，重新打开 Connectivity Kit。
3. 如果设备进入 Recovery Mode，让 Connectivity Kit 继续识别它。
4. 把 CK 缓存切换到 stock package。
5. 重新执行官方固件更新。
6. 如果设备无响应，按官方文档使用背面 reset 孔复位，再重试 stock 更新。
7. 换 USB 口、换线、避免 USB Hub。

## 何时必须回滚

出现以下任一情况，优先回滚：

- 启动异常；
- Connectivity Kit 无法识别；
- Home/CAS/菜单不可读；
- 12px 中文出现明显黑块或大面积粘连；
- 输入框或软键文字错位；
- 重启后异常复现；
- 用户数据无法正常备份或恢复。

## 不要做的事

- 不要在失败状态下继续刷更多实验变体。
- 不要把 G1 包用于 G2。
- 不要把 patched `PRIME_APP.DAT` 改名上传给别人。
- 不要跳过 MD5 验证。


