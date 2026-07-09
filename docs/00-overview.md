# Overview

## 目标

本项目记录一次 HP Prime G1 官方 20250915 固件的参数级字体清晰化实验。

最终目标不是替换字体文件，也不是重写 UI 渲染器，而是在 FreeType 灰度光栅输出路径上做最小补丁，让低分辨率文字少一点浅灰糊边。

最终采用的候选是 `softcut64`：

```c
coverage = min(coverage, 255);
if (coverage < 64) {
    coverage = 0;
}
```

这个方案保留官方的 8-bit 灰度 bitmap 布局，因此比 `FT_RENDER_MODE_MONO` 或硬阈值更不容易破坏现有 compositor。

## 路线摘要

1. 从官方 `PRIME_APP.DAT` 的 FAT16 镜像里提取 `programs/misc/armfir.elf`。
2. 静态分析固件里内置的 FreeType。
3. 定位 `smooth` renderer 的灰度覆盖率输出路径。
4. 在 ARM `gray_hline` 附近把 coverage 送入小型 stub。
5. stub 保留 `>= 256` 到 `255` 的 clamp，只把 `<64` 的弱覆盖清零。
6. 把 patched `armfir.elf` 原大小写回 `PRIME_APP.DAT`。
7. 更新 FAT 内部 `APPSLIST.MD5` 和外层 `Prime_FW.md5`。
8. 使用 HP Connectivity Kit 的 G1 本地固件缓存入口刷入验证。

## 当前结论

`softcut64` 是当前最稳妥的参数级候选。

硬阈值类方案已经被视觉验证否决：12px 中文和密集 UI 文本会出现黑块、笔画粘连、局部不可辨认。`softband64_224` 是更锐利的实验候选，但它比 `softcut64` 更重，不作为首刷路线。

资源级字体替换不再推进。本项目不包含 `FZXIANGSU12.TTF` 替换流程。

## 适用范围

- 机型：HP Prime G1。
- 固件：官方 20250915。
- 目标文件：`PRIME_APP.DAT` 内部 `programs/misc/armfir.elf`。
- 不适用：HP Prime G2、i.MX6ULL/`uuu` 刷机路径、非 20250915 的未知固件。

## 公开仓库边界

仓库只包含：

- 文档；
- 复现脚本；
- patch manifest；
- 分析报告；
- 对比截图。

仓库不包含：

- 官方固件；
- 官方模拟器；
- Connectivity Kit 二进制；
- 提取出的 HP 字体；
- patched ELF、DAT、ROM 或 EXE。

这样做的目的很简单：别人可以审计和复现这条路线，但每个人必须在自己机器上用自己合法取得的官方文件生成 patched 包。


