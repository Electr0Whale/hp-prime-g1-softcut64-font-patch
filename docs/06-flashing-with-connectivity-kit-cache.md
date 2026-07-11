# Flashing With Connectivity Kit Cache

> Status note: the newer `lut32_ease150 + Sarasa CJK MaxCoverage` package has
> been generated, statically verified, and installed into a local Connectivity
> Kit cache. Manual hardware validation is still pending; this is not a claim of
> a successful device flash. See `docs/19-sarasa-cjk-lut32-ease150.md`.

当前推荐刷入路线是 HP Connectivity Kit 的 G1 本地固件缓存。

这条路线来自实测：修改缓存目录中的中文 release HTML 后，Connectivity Kit 更新页面同步显示了修改内容，说明更新 UI 会读取该缓存。

## 前提

先完成 `docs/05-reproduce-your-own-patch.md`，得到：

```text
$work\flash_package_softcut64
```

该目录应包含：

```text
PRIME_APP.DAT       patched softcut64
PRIME_MASTER.DAT    official stock
PRIME_OS.ROM        official stock
Prime_FW.md5        updated for patched PRIME_APP.DAT
```

## 验证 flash package

```powershell
& "$repo\tools\connectivity-cache\Verify-PrimeG1CachePackage.ps1" `
  -CachePath "$work\flash_package_softcut64" `
  -ExpectedPrimeAppMd5 '59c9a785212599acd5b676bf72e6b5c2'
```

## 安装到 Connectivity Kit 缓存

关闭 HP Connectivity Kit 后运行：

```powershell
$cache = Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'HP Connectivity Kit\固件\PrimeG1'

& "$repo\tools\connectivity-cache\Install-PrimeG1CachePackage.ps1" `
  -PackagePath "$work\flash_package_softcut64" `
  -CachePath $cache `
  -BackupRoot "$work\cache_backups"
```

脚本会先备份原缓存，再复制 patched package。对于实机候选，建议进一步采用同盘 staging、完整 13 行 MD5 验证和目录交换；任何异常都应恢复原缓存，不能在未验证完成时直接覆盖唯一缓存副本。

再次验证：

```powershell
& "$repo\tools\connectivity-cache\Verify-PrimeG1CachePackage.ps1" `
  -CachePath $cache `
  -ExpectedPrimeAppMd5 '59c9a785212599acd5b676bf72e6b5c2'
```

## 刷入步骤

1. 关闭所有旧的更新弹窗。
2. 重新打开 HP Connectivity Kit。
3. 用稳定 USB 数据线连接 HP Prime G1。
4. 确认 Connectivity Kit 能识别计算器。
5. 先备份计算器数据。
6. 从 Connectivity Kit 中进入固件更新：

```text
Calculators pane -> right click calculator -> Update firmware
```

或使用已经验证会读取本地 CHS release 页面内容的更新入口。

7. 确认更新说明页来自本地缓存。
8. 开始更新。
9. 更新过程中不要断开 USB，不要关闭 Connectivity Kit，不要按 reset。
10. 等待计算器进入 Recovery Mode、写入完成并重启。

## 刷入后检查

立即检查：

- 设备能否启动到 Home；
- Connectivity Kit 是否仍能识别；
- Home/CAS/菜单/软键是否可读；
- 中文 12px 文本是否有黑块或粘连；
- 数学符号是否缺笔画或错位；
- 输入框、菜单切换、关机重启是否正常。

填写 `docs/11-hardware-test-checklist.md`。

## 为什么不用 patched standalone Updater

探索中确实定位并尝试过 standalone `Updater.exe` 的文件名过滤和版本/no-update 分支，但 patched Updater 在本地实测直接闪退。当前不推荐它作为刷入路径。

相关记录见 `docs/08-updater-analysis.md`。

