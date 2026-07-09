# External Projects

探索中参考过两个公开项目：

- `zephray/prinux`
- `Repeerc/Linux-For-HPPrime-V2`

它们对理解 HP Prime 硬件和引导生态有帮助，但没有直接解决本项目的字体补丁问题。

## zephray/prinux

价值：

- 说明 HP Prime 存在较深的硬件/启动链研究基础；
- 可作为理解设备分代、内存布局和外设差异的背景资料；
- 对“不要把 G2/i.MX6ULL 的刷机方法套到 G1”有提醒意义。

限制：

- 目标是 Linux/启动链方向，不是官方 `armfir.elf` 的 FreeType 字体渲染路径；
- 不能直接给出 `PRIME_APP.DAT` FAT16 内部重打包流程；
- 不能替代本项目对 20250915 G1 `armfir.elf` 的静态定位。

## Repeerc/Linux-For-HPPrime-V2

价值：

- 更贴近 HP Prime Linux 启动/替代系统路线；
- 有助于理解不同硬件版本的刷机差异；
- 可作为恢复和硬件识别背景材料。

限制：

- 主要服务 Linux-for-HPPrime，不是官方固件参数级 patch；
- 版本和硬件路线可能与 G1 官方 20250915 包不一致；
- 不提供本项目需要的 FreeType `smooth` renderer patch 点。

## 对本项目的实际帮助

这两个项目帮助确认：

- 不应混用 G1/G2 刷机方案；
- 本项目应保持为官方固件内的最小二进制 patch；
- 不应引入替代 OS、bootloader 或新渲染器来解决字体灰边问题。

最终 patch 仍然来自对官方 `armfir.elf` 的局部逆向，而不是外部项目代码移植。


