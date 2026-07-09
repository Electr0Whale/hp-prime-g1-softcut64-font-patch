# ARM Softcut64 Firmware Patch Report

## Summary

The simulator evidence rejected hard binary thresholding for dense 12 px Chinese
text. The ARM firmware patch now follows the same safer visual direction:
preserve 8-bit gray coverage, but zero very low coverage below 64.

Target semantics:

```c
coverage = min(coverage, 255);
if (coverage < 64) {
    coverage = 0;
}
```

This avoids `FT_RENDER_MODE_MONO` and keeps the existing one-byte-per-pixel
`FT_PIXEL_MODE_GRAY` compositor contract.

## Patch Shape

Source:

- `extracted\armfir.elf`
- MD5: `9e1ed504c294e70ff478e0bd5553c441`

Output:

- `patched\armfir.softcut64.elf`
- MD5: `32ac6681f1a8287db20fbe33d0035fe7`

Manifest:

- `patched\patch_manifest.arm_softcut64.json`

The patch uses an executable zero-filled cave already present in the ARM load
segment:

- normal stub: file `0x63a628`, VA `0x30c3a5f4`
- inverted stub: file `0x63a63c`, VA `0x30c3a608`

Redirects:

```asm
308db940  b  0x30c3a608   ; inverted coverage path
308db944  b  0x30c3a5f4   ; normal coverage path
```

Normal stub:

```asm
30c3a5f4  cmp    r0, #0x100
30c3a5f8  movge  r0, #0xff
30c3a5fc  cmp    r0, #0x40
30c3a600  movlo  r0, #0
30c3a604  b      0x308db94c
```

Inverted stub:

```asm
30c3a608  cmp    r0, #0x40
30c3a60c  movlo  r0, #0
30c3a610  b      0x308db94c
```

This is cleaner than the earlier ARM `threshold128` patch because it operates
before the shared callback/bitmap split:

- callback span output uses softened `r0`;
- ordinary bitmap output later keeps the original `and r2, r0, #0xff`;
- no Duff-style branch table shifting is needed;
- ELF size and segment sizes remain unchanged.

## Repacked Firmware Artifacts

- `patched_firmware\PRIME_APP.softcut64_poc.DAT`
- `patched_firmware\Prime_FW.softcut64_poc.md5`
- `patched_firmware\repack_report.softcut64.json`

Repack result:

- Repacked `PRIME_APP` MD5: `59c9a785212599acd5b676bf72e6b5c2`
- Embedded `programs/misc/armfir.elf` size: `8230724`
- `APPSLIST.MD5` updated for `armfir.elf`
- outer `Prime_FW.softcut64_poc.md5` updated for `PRIME_APP.DAT`

## Verification

ARM softcut static verifier:

```powershell
& 'python' `
  '<work>\scripts\verify_arm_softcut_artifacts.py' `
  --manifest '<work>\patched\patch_manifest.arm_softcut64.json'
```

Firmware package verifier:

```powershell
& 'python' `
  '<work>\scripts\verify_font_patch_artifacts.py' softcut64
```

Both currently pass. The package verifier confirms:

- patched ELF equals original plus manifest-described bytes only;
- ELF size and magic are unchanged;
- repacked `PRIME_APP` size is unchanged;
- FAT16 still contains `programs/misc/armfir.elf`;
- embedded `armfir.elf` matches `patched\armfir.softcut64.elf`;
- `APPSLIST.MD5` matches the patched ELF;
- outer `Prime_FW.softcut64_poc.md5` matches the repacked DAT.

## Status

This is the current best firmware-side candidate, but it is still static-only.
Do not treat it as a recommended flash image until a separate hardware test and
rollback plan exists.

Recommended next validation:

1. Keep `threshold128/160/192` as rejected visual controls.
2. Use `softcut64` as the first firmware candidate.
3. If hardware recovery is confirmed, test `PRIME_APP.softcut64_poc.DAT` on a
   recoverable G1 unit.
4. If text still looks too soft, create `arm_softcut96` using the same generator
   and compare against `softcut64`.

