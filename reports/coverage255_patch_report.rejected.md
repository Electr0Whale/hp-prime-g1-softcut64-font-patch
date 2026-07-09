# Coverage255 Gray Raster Patch

## Purpose

This patch keeps the existing FreeType `smooth` renderer and `FT_PIXEL_MODE_GRAY`
bitmap format, but forces every non-DIRECT gray span written by `gray_hline` to
coverage `0xff`.

It is a first firmware-safe PoC for black/white clear text because it preserves
the current one-byte-per-pixel compositor contract. It does not attempt packed
1-bit `FT_PIXEL_MODE_MONO`.

## Located Function Chain

```text
ft_smooth_render_generic 0x30944344
  -> gray_raster_render  0x3092aa20
     -> gray_convert_glyph 0x3092a8ec
        -> gray_sweep 0x308db9f0
           -> gray_hline 0x308db900
```

`gray_sweep` calls `gray_hline` at:

```asm
308dba40  bl  #0x308db900
308dba78  bl  #0x308db900
308dbab0  bl  #0x308db900
```

## Patch Point

Original code in `gray_hline`:

```asm
308db984  and  r2, r0, #0xff
```

Patched code:

```asm
308db984  orr  r2, r0, #0xff
```

Patch bytes:

```text
file offset 0x2db9b8
old         ff2000e2
new         ff2080e3
```

Effect: the non-DIRECT bitmap write path uses `r2` as the coverage byte for
small spans and the memset value for longer spans. Forcing `r2 = 0xff` turns all
emitted gray spans into full foreground coverage while leaving zero-coverage
areas untouched.

## Outputs

- Patched ELF: `<work>\patched\armfir.coverage255.elf`
- Patch manifest: `<work>\patched\patch_manifest.coverage255.json`
- Repacked app DAT: `<work>\patched_firmware\PRIME_APP.coverage255_poc.DAT`
- Repacked outer MD5: `<work>\patched_firmware\Prime_FW.coverage255_poc.md5`
- Repack report: `<work>\patched_firmware\repack_report.coverage255.json`

## Static Verification

- Original `armfir.elf` MD5: `9e1ed504c294e70ff478e0bd5553c441`
- Patched `armfir.coverage255.elf` MD5: `68367767cadf64024aab3de6a33252c1`
- Patched ELF size is unchanged: `8230724`
- Only two bytes differ, both inside one ARM instruction:
  - `0x2db9ba`: `00 -> 80`
  - `0x2db9bb`: `e2 -> e3`
- Repacked `PRIME_APP.coverage255_poc.DAT` MD5:
  `136b9e75a4ef766e20a2c747f9289314`
- `APPSLIST.MD5` armfir line matches the patched ELF MD5.
- `Prime_FW.coverage255_poc.md5` matches the repacked `PRIME_APP` MD5.

## Limitations

This is not a perceptual threshold at 128. It turns every nonzero gray span
fully black. Very thin edge coverage that would normally be faint gray becomes
solid, so glyphs may look heavier. The advantage is that it is a one-instruction
patch with no format, allocation, pitch, or compositor changes.

The next refinement is a thresholded variant:

```c
coverage = coverage >= threshold ? 255 : 0;
```

That probably needs either a small branch sequence in nearby code space or a
different existing instruction sequence to repurpose.

