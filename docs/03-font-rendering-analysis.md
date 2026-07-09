# Font Rendering Analysis

## 定位结果

固件普通字体路径进入 FreeType `smooth` renderer。

已定位的关键地址：

```text
smooth renderer class        file 0x6bc4a0 VA 0x30cbc46c
smooth.render_glyph          file 0x31bdcc VA 0x3091bd98
ft_smooth_render_generic     file 0x344378 VA 0x30944344
gray_raster_render           file 0x32aa54 VA 0x3092aa20
gray_hline                   file 0x2db934 VA 0x308db900
```

灰度 bitmap 设置点：

```asm
30944578  mov   r1, #2          ; FT_PIXEL_MODE_GRAY
30944580  mov   r2, #0x100      ; num_grays = 256
30944584  strb  r1, [r4, #0x12] ; bitmap->pixel_mode
30944588  strh  r2, [r4, #0x10] ; bitmap->num_grays
```

AA raster 参数点：

```asm
309445b8  mov   r1, #1
309445bc  strd  r0, r1, [sp, #0x48]
```

这里存的是 `FT_Raster_Params.flags = FT_RASTER_FLAG_AA`。

## 为什么不直接关 AA

把 `FT_RASTER_FLAG_AA` 清零不是 mono 开关。固件里的 gray raster 检查 AA flag，不带 AA 会返回错误：

```asm
3092aa38  ldr    r0, [r6, #8]
3092aa3c  tst    r0, #1
3092aa40  moveq  r0, #0x13
3092aa44  beq    #0x3092ab04
```

因此“关 AA”会更接近渲染失败，而不是得到清晰 mono 字体。

## 为什么不直接用 FT_RENDER_MODE_MONO

`FT_RENDER_MODE_MONO` 可能让 FreeType 输出 packed 1-bit bitmap。现有 UI compositor 很可能仍按 8-bit 灰度 bitmap 读取 slot buffer。

这会带来几个风险：

- packed bits 被当作 byte coverage 读；
- pitch/width 解释错位；
- 局部空白或黑块；
- 菜单和输入框文字不可读。

所以本项目没有把 mono render 作为最终参数级路线。

## 可控点

更安全的控制点是 gray raster 的 coverage 输出。

调用链：

```text
ft_smooth_render_generic
  -> gray_raster_render
     -> gray_convert_glyph
        -> gray_sweep
           -> gray_hline
```

只要在 `gray_hline` 写入/回调前修改 coverage，外层仍然看到原来的 `FT_PIXEL_MODE_GRAY` 和一字节 coverage buffer。

这就是 `softcut64` 的核心。


