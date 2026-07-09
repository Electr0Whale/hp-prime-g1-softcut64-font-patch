# Research Log

## 1. 固件展开

确认 `PRIME_APP.DAT` 在偏移 `0x2000` 处包含 FAT16。提取出：

```text
programs/misc/armfir.elf
programs/misc/armfir.dat
```

`armfir.elf` 是 ARM 32-bit ELF，大小 `8230724`，MD5 `9e1ed504c294e70ff478e0bd5553c441`。

`armfir.dat` 内含三份 PrimeSans TTF，和模拟器字体目录一致。

## 2. 字体替换探索

最初考虑过把页面中约 `14px x 12px` 的字体替换成外部 12px 中文字体。后续用户明确停止资源级方案，因此本项目不再推进字体替换。

保留结论：字体文件存在且可提取，但替换会引入 metric、fallback、hinting 和授权变量，不适合作为本轮参数级实验。

## 3. FreeType 参数路线

最初计划找 `FT_Load_Glyph` / `FT_Render_Glyph` 参数，尝试：

```text
FT_LOAD_TARGET_MONO
FT_LOAD_MONOCHROME
FT_RENDER_MODE_MONO
```

分析后发现真正 mono 输出可能改变 bitmap packing，而官方 compositor 很可能仍按灰度 bitmap 读取。因此转向 gray coverage patch。

## 4. FreeType smooth renderer

定位到普通字体路径使用 FreeType `smooth` renderer：

```text
ft_smooth_render_generic -> gray_raster_render -> gray_hline
```

`FT_PIXEL_MODE_GRAY` 和 `num_grays = 256` 设置点明确。直接关 AA 会导致 gray raster 返回错误，不是可用的 mono 开关。

## 5. 硬阈值 PoC

先做了 `coverage255` 和 `threshold128/160/192`，证明可以控制 coverage 输出并保持 8-bit buffer contract。

结果：视觉太硬，12px 中文会出现黑块和粘连，被否决。

## 6. softcut/softband

随后测试：

```text
softcut64
softcut96
softband64_192
softband64_224
```

`softcut64` 作为最稳妥实机候选。`softband64_224` 作为更锐利的实验候选保留，但不作为首刷。

## 7. ARM 迁移

把模拟器中的 `softcut64` 语义迁移到 ARM `armfir.elf`。最终补丁只改：

```text
0x63a628 normal stub
0x63a63c inverted stub
0x2db974 branch redirect
0x2db978 branch redirect
```

ELF 大小不变，只有 manifest 记录字节变化。

## 8. 重打包

把 patched `armfir.elf` 写回 `PRIME_APP.DAT` 内部 FAT16 的原文件位置。随后更新：

```text
APPSLIST.MD5
Prime_FW.md5
```

repacked `PRIME_APP.DAT` MD5 为：

```text
59c9a785212599acd5b676bf72e6b5c2
```

## 9. standalone Updater

分析过 standalone `Updater.exe`，定位到旧文件名过滤和 no-update/version gate。生成过 patch manifest，但 patched Updater 本地实测闪退，因此此路线被否决。

## 10. Connectivity Kit 缓存路线

用户验证修改本地 CK 缓存中的 CHS HTML 后，更新页面同步显示修改内容。最终采用官方 Connectivity Kit 入口读取本地 `PrimeG1` 缓存的路线。

这是当前从“生成 patched 包”推进到“可以实机刷入验证”的主线。

