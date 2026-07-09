# Threshold128 Gray Raster Patch

## Purpose

This patch keeps FreeType's `smooth` renderer, `FT_RASTER_FLAG_AA`, and
`FT_PIXEL_MODE_GRAY`, but changes the ordinary gray bitmap output path from
8-bit antialiasing to binary coverage:

```c
coverage = coverage >= 128 ? 255 : 0;
```

It preserves the existing one-byte-per-pixel bitmap contract, so it avoids the
packed 1-bit bitmap risk of `FT_RENDER_MODE_MONO`.

## Located Function Chain

```text
ft_smooth_render_generic 0x30944344
  -> gray_raster_render  0x3092aa20
     -> gray_convert_glyph 0x3092a8ec
        -> gray_sweep 0x308db9f0
           -> gray_hline 0x308db900
```

The normal non-LCD path sets `FT_RASTER_FLAG_AA` only, so the gray raster's
direct span callback is not expected to be used for normal glyph bitmaps. The
patch therefore targets `gray_hline`'s ordinary target-bitmap path.

## Patch Point

Original ordinary bitmap path:

```asm
308db980  ldr      r3, [ip, #0x1d4]
308db984  and      r2, r0, #0xff
308db988  mul      r0, r3, r5
308db98c  ldr      ip, [ip, #0x1d0]
308db990  cmp      r1, #8
308db994  sub      r0, ip, r0
308db998  add      r0, r0, r4
308db99c  addlo    pc, pc, r1, lsl #2
308db9a0  b        #0x308db9e4
```

Patched path:

```asm
308db980  cmp      r1, #8
308db984  lsr      r2, r0, #7
308db988  rsb      r2, r2, r2, lsl #8
308db98c  ldr      r3, [ip, #0x1d4]
308db990  mul      r0, r3, r5
308db994  ldr      ip, [ip, #0x1d0]
308db998  sub      r0, ip, r0
308db99c  add      r0, r0, r4
308db9a0  addlo    pc, pc, r1, lsl #2
308db9a4  b        #0x308db9e4
```

`lsr r2, r0, #7` maps clamped coverage `0..127` to `0` and `128..255` to `1`.
`rsb r2, r2, r2, lsl #8` maps that `0/1` value to `0/255`.

Because the inserted instructions consume the original jump-table entry at
`0x308db9a0`, the small-span branch table is shifted by one ARM word. The branch
targets were adjusted so `count == 0` still returns, `count == 1..7` still writes
the correct number of bytes, and `count >= 8` still uses the long-span fill path.

Patch bytes:

```text
file offset 0x2db9b4
old d4319ce5 ff2000e2 930500e0 d0c19ce5 080051e3 00004ce0 040080e0 01f18f30 0f0000ea 7c80bde8 0b0000ea 090000ea 070000ea 050000ea 030000ea 010000ea ffffffea
new 080051e3 a023a0e1 022462e0 d4319ce5 930500e0 d0c19ce5 00004ce0 040080e0 01f18f30 0e0000ea 7c80bde8 0a0000ea 080000ea 060000ea 040000ea 020000ea 000000ea
```

## Outputs

- Patched ELF: `<work>\patched\armfir.threshold128.elf`
- Patch manifest: `<work>\patched\patch_manifest.threshold128.json`
- Repacked app DAT: `<work>\patched_firmware\PRIME_APP.threshold128_poc.DAT`
- Repacked outer MD5: `<work>\patched_firmware\Prime_FW.threshold128_poc.md5`
- Repack report: `<work>\patched_firmware\repack_report.threshold128.json`

## Static Verification

- Original `armfir.elf` MD5: `9e1ed504c294e70ff478e0bd5553c441`
- Patched `armfir.threshold128.elf` MD5: `88ffcb28ec1cb8244aefe0ca06646100`
- Patched ELF size is unchanged: `8230724`
- Differences are confined to file offsets `0x2db9b4..0x2db9f6`.
- Repacked `PRIME_APP.threshold128_poc.DAT` MD5:
  `bac89f6afdf3eebdb35561776933e0a0`
- FAT16 still parses after repack.
- Embedded `programs/misc/armfir.elf` MD5 matches the patched ELF MD5.
- `APPSLIST.MD5` armfir line matches the patched ELF MD5.
- `Prime_FW.threshold128_poc.md5` matches the repacked `PRIME_APP` MD5.

## Limitations

This is a firmware-side static PoC only. It has not been run in the official
simulator or on hardware.

The patch targets the ordinary gray bitmap output path. If some future path uses
FreeType gray raster direct span callbacks, those callback spans still receive
the original 8-bit coverage. The normal `smooth` glyph path found here sets only
`FT_RASTER_FLAG_AA`, not `FT_RASTER_FLAG_DIRECT`, so this limitation should not
affect normal text rendering.

The threshold is fixed at `128`. A lower threshold, such as `96`, would make
glyphs heavier; a higher threshold, such as `160`, would make them thinner. A
runtime-tunable threshold would need a larger hook or a data literal that can be
safely referenced from this hot path.

