# Softband Coverage Patch Report

## Summary

After `threshold128/160/192` proved too hard and `softcut64` proved safe, this
experiment tested a middle option:

```c
coverage = min(coverage, 255);
if (coverage < 64) {
    coverage = 0;
}
if (coverage >= high) {
    coverage = 255;
}
```

The goal is to remove faint edge haze, keep mid gray structure, and make only
strong stroke interiors solid.

## Simulator Variants

Implemented:

- `softband64_192`
- `softband64_224`

Simulator artifacts:

- `patched\patch_manifest.emulator_softband64_192.json`
- `patched\patch_manifest.emulator_softband64_224.json`
- `patched_emulator\HPPrime.softband64_192.exe`
- `patched_emulator\HPPrime.softband64_224.exe`
- `patched_emulator_runtime_softband64_192\HPPrime.exe`
- `patched_emulator_runtime_softband64_224\HPPrime.exe`
- `screenshots\patched\emulator_softband64_192_apps.png`
- `screenshots\patched\emulator_softband64_224_apps.png`
- `patched\emulator_softband64_192_verification.json`
- `patched\emulator_softband64_224_verification.json`

`softband64_192` is visibly sharper but starts to look heavy in dense glyphs.
`softband64_224` is the better balanced simulator result: stronger than
`softcut64`, but less block-prone than `softband64_192`.

Selected ROI comparison:

| ROI | baseline largest solid | softcut64 | softband64_192 | softband64_224 | threshold128 |
| --- | ---: | ---: | ---: | ---: | ---: |
| `label_function` | 12 | 12 | 28 | 24 | 144 |
| `label_spreadsheet` | 36 | 36 | 136 | 88 | 192 |
| `label_statistics` | 44 | 44 | 92 | 92 | 300 |
| `label_datasampler` | 20 | 20 | 104 | 44 | 192 |

## ARM Firmware Variant

`softband64_224` has been migrated to `armfir.elf`.

Artifacts:

- `patched\patch_manifest.arm_softband64_224.json`
- `patched\armfir.softband64_224.elf`
- `patched\arm_softband64_224_verification.json`
- `patched_firmware\PRIME_APP.softband64_224_poc.DAT`
- `patched_firmware\Prime_FW.softband64_224_poc.md5`
- `patched_firmware\repack_report.softband64_224.json`

Output MD5s:

- ELF: `4fab549b39082b0b3302957d4df87ca5`
- repacked `PRIME_APP`: `7deaf10ab29409157e47c6699c3ea1ad`

ARM patch shape:

```asm
308db940  b  0x30c3a620   ; inverted coverage path
308db944  b  0x30c3a5f4   ; normal coverage path
```

Normal stub:

```asm
30c3a5f4  cmp    r0, #0x100
30c3a5f8  movge  r0, #0xff
30c3a5fc  cmp    r0, #0x40
30c3a600  movlo  r0, #0
30c3a604  cmp    r0, #0xe0
30c3a608  movhs  r0, #0xff
30c3a60c  b      0x308db94c
```

Inverted stub:

```asm
30c3a620  cmp    r0, #0x40
30c3a624  movlo  r0, #0
30c3a628  cmp    r0, #0xe0
30c3a62c  movhs  r0, #0xff
30c3a630  b      0x308db94c
```

## Verification

Simulator:

```powershell
& 'python' `
  '<work>\scripts\verify_emulator_softband_artifacts.py' `
  --manifest '<work>\patched\patch_manifest.emulator_softband64_224.json'
```

ARM ELF:

```powershell
& 'python' `
  '<work>\scripts\verify_arm_softband_artifacts.py' `
  --manifest '<work>\patched\patch_manifest.arm_softband64_224.json'
```

Firmware package:

```powershell
& 'python' `
  '<work>\scripts\verify_font_patch_artifacts.py' softband64_224
```

All currently pass. The package verifier confirms that FAT16 is readable,
`programs/misc/armfir.elf` matches the patched ELF, `APPSLIST.MD5` matches the
embedded ELF, and the outer firmware MD5 matches the repacked DAT.

## Current Ranking

- `softcut64`: safest candidate; least likely to create black blocks.
- `softband64_224`: sharper candidate; useful if `softcut64` still looks too
  soft on hardware.
- `softband64_192`: too heavy for dense Chinese text; keep as comparison.
- `threshold128/160/192`: rejected for final visual use.

