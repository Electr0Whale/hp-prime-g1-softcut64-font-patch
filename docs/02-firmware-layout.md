# Firmware Layout

## PRIME_APP.DAT

`PRIME_APP.DAT` 在偏移 `0x2000` 处包含 FAT16 镜像。

关键文件：

```text
programs/misc/armfir.elf
programs/misc/armfir.dat
APPSLIST.MD5
```

已确认的 20250915 G1 布局：

```text
programs/misc/armfir.elf offset 0x0e6e00 size 8230724 md5 9e1ed504c294e70ff478e0bd5553c441
programs/misc/armfir.dat offset 0x8c0600 size 8897536
```

`armfir.elf` 是 ARM 32-bit ELF，加载基址约为 `0x30600000`。对主加载段内位置，常用换算为：

```text
vaddr = 0x30600000 + file_offset - 0x34
```

## 字体资源

`armfir.dat` 内嵌三份 TTF，和官方模拟器 `fonts` 目录里的字体 MD5 一致：

```text
PrimeSansBold.ttf
PrimeSansFull.ttf
PrimeSansMono.ttf
```

早期探索过字体替换，但本路线已经停止资源级方案。原因是用户反馈硬像素和黑块问题来自渲染/覆盖率处理，不适合继续混入字体替换变量。

## FreeType

固件中静态链接 FreeType。分析中看到的模块包括：

```text
ftbase
ftbitmap
ftcache
ftgasp
ftglyph
ftlcdfil
raster
sfnt
smooth
truetype
bdf
```

重要结论是：普通 UI 字体路径走 FreeType `smooth` 灰度 renderer，而不是直接输出 packed 1-bit mono bitmap。

这决定了后续补丁策略：保持 `FT_PIXEL_MODE_GRAY`，不要贸然切 `FT_RENDER_MODE_MONO`。


