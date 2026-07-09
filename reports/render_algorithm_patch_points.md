# HP Prime G1 Render Algorithm Patch Points

Source ELF:

`<work>\extracted\armfir.elf`

MD5:

`9e1ed504c294e70ff478e0bd5553c441`

## Result

The normal font path is FreeType's `smooth` renderer, not a mono renderer. The
exact grayscale bitmap setup and AA raster parameter points are now located.

No executable bytes were patched.

## Renderer Path

- `smooth` renderer class: file `0x6bc4a0`, VA `0x30cbc46c`
- `smooth.render_glyph`: VA `0x3091bd98`, file `0x31bdcc`
- shared `ft_smooth_render_generic` equivalent: VA `0x30944344`, file `0x344378`
- gray raster render function from the raster class: VA `0x3092aa20`, file `0x32aa54`

The wrapper at `0x3091bd98` maps `FT_RENDER_MODE_LIGHT` to
`FT_RENDER_MODE_NORMAL` and passes `required_mode = 0`.

```asm
3091bd9c  cmp    r2, #1
3091bda4  moveq  r2, #0
3091bda8  str    ip, [sp]
3091bdac  bl     #0x30944344
```

## Exact Algorithm Points

`r4` is `slot + 0x4c`, the `FT_Bitmap` address. Therefore `[r4, #0x12]` is
`slot->bitmap.pixel_mode` at total slot offset `0x5e`.

```asm
30944578  mov   r1, #2          ; FT_PIXEL_MODE_GRAY
30944580  mov   r2, #0x100      ; num_grays = 256
30944584  strb  r1, [r4, #0x12] ; bitmap->pixel_mode
30944588  strh  r2, [r4, #0x10] ; bitmap->num_grays
```

The raster params are also exact:

```asm
309445b8  mov   r1, #1
309445bc  strd  r0, r1, [sp, #0x48]
```

This stores `params.source = outline` and
`params.flags = FT_RASTER_FLAG_AA`.

The normal non-LCD path then calls the raster renderer through `blx r2`:

```asm
30944830  add  sb, sb, #0x34
30944834  ldm  sb, {r0, r2}
30944838  add  r1, sp, #0x44
3094483c  blx  r2
```

## Why The Simple Mono Patch Fails

The linked raster function is the gray raster. It rejects non-AA rendering:

```asm
3092aa38  ldr    r0, [r6, #8] ; params.flags
3092aa3c  tst    r0, #1       ; FT_RASTER_FLAG_AA
3092aa40  moveq  r0, #0x13
3092aa44  beq    #0x3092ab04
```

So changing `params.flags` from `1` to `0` is not a mono switch; it makes
rendering fail with `Cannot_Render_Glyph` / `Invalid_Mode`.

Changing only `FT_PIXEL_MODE_GRAY` to `FT_PIXEL_MODE_MONO` is also unsafe. The
buffer is still allocated as one byte per pixel and filled by the gray raster,
so the compositor would see metadata for packed 1-bit data while receiving an
8-bit gray buffer.

## Practical Next Patch Direction

The best next algorithm-level patch is not `FT_RENDER_MODE_MONO`. It is to keep
`FT_PIXEL_MODE_GRAY`, keep `FT_RASTER_FLAG_AA`, and threshold gray coverage to
`0` or `255` inside the gray raster's coverage output path. This preserves the
existing bitmap layout and avoids packed 1-bit compositor risk.

The remaining unresolved point is locating the exact optimized ARM function
corresponding to FreeType `gray_hline` or `gray_render_span`.

