# Risk And Scope

## 法律和分发边界

不要发布：

- 官方固件；
- 官方模拟器；
- Connectivity Kit；
- 提取出的 HP 字体；
- patched `armfir.elf`；
- patched `PRIME_APP.DAT`；
- patched `Updater.exe`。

可以发布：

- 文档；
- patch manifest；
- 脚本；
- 分析报告；
- 自己生成的说明性截图。

每个用户应使用自己合法取得的官方文件，在本机生成 patched 包。

## 技术风险

该补丁虽然很小，但仍然是固件修改。

主要风险：

- 设备无法启动；
- 更新中断；
- UI 字体异常；
- Connectivity Kit 无法识别；
- 数据丢失；
- 后续官方更新覆盖或拒绝更新。

降低风险的办法：

- 刷前备份计算器数据；
- 保留 stock package；
- 保留 CK 缓存备份；
- 先验证 MD5；
- 只在可恢复的 G1 上测试；
- 首次测试只刷 `softcut64`，不要同时混入其他改动。

## 版本风险

补丁点是 20250915 G1 `armfir.elf` 的固定文件偏移和虚拟地址。

如果任一输入 MD5 不一致，必须停止：

```text
PRIME_APP.DAT 663d1f7e4d4279286387f9c29e688f78
armfir.elf    9e1ed504c294e70ff478e0bd5553c441
```

不要在其他版本上套用这些偏移。

## 为什么不做资源级方案

资源级替换会引入新变量：

- glyph metric；
- hinting；
- fallback；
- 字符覆盖范围；
- UI 布局；
- 字体授权；
- 与官方字体缓存/加载逻辑的兼容性。

当前问题已经能在 coverage 输出层得到更小、更可审计的控制，所以资源级方案停止。

## 为什么不做 mono renderer

真正 mono renderer 很可能改变 bitmap packing。现有 compositor 可能按 8-bit 灰度 buffer 读取，导致黑块、错位或空白。

`softcut64` 的价值正在于：改变视觉 coverage，但不改变 buffer contract。


