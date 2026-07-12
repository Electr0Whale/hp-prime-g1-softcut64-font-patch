# Round4 Hardware Validation Packages

This is the practical handoff point after the LUT fine-tune preview.  The
packages are prepared locally for hardware validation, but they are not included
in this repository because they contain HP firmware files.

## Local Prepared Package Set

On the working machine, the local package root is:

```text
D:\Download\HPPrimeFontPatch_Work\hardware_validation\font_optimization_round4_lut_finetune
```

It contains these Connectivity Kit cache-ready package directories:

```text
flash_package_lut24_ease140
flash_package_lut32_ease135
flash_package_lut32_ease150
flash_package_lut32_ease170
flash_package_lut40_ease150
```

Each package contains:

```text
PRIME_APP.DAT
PRIME_MASTER.DAT
PRIME_OS.ROM
Prime_FW.md5
release_info*.html
release_info.txt
version_20250915
```

The package set also contains:

```text
README.md
ROUND4_TEST_RESULTS_TEMPLATE.md
Verify-Round4LutPackages.ps1
Set-Round4PrimeG1CacheVariant.ps1
MD5SUMS.txt
SHA256SUMS.txt
validation_manifest.json
```

## Prepared MD5s

| Variant | PRIME_APP.DAT MD5 |
| --- | --- |
| `lut24_ease140` | `88868bf2a056c53aec743e5ef19cbbcd` |
| `lut32_ease135` | `13e7afa153cf4658ce54473ae1049ef8` |
| `lut32_ease150` | `ff1433c4b422a1a6cf30c9c1389dd9a0` |
| `lut32_ease170` | `edc2de5e73bb85cd3f4d59a96b7b18f1` |
| `lut40_ease150` | `21910427215ce54270b86bbe75074a74` |

## Verify Local Packages

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File "D:\Download\HPPrimeFontPatch_Work\hardware_validation\font_optimization_round4_lut_finetune\Verify-Round4LutPackages.ps1"
```

Expected final line:

```text
Round4 LUT fine-tune packages are internally consistent.
```

## Preview Cache Install

Use `-WhatIf` first:

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File "D:\Download\HPPrimeFontPatch_Work\hardware_validation\font_optimization_round4_lut_finetune\Set-Round4PrimeG1CacheVariant.ps1" -Variant lut32_ease150 -WhatIf
```

If the preview looks correct, remove `-WhatIf`:

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File "D:\Download\HPPrimeFontPatch_Work\hardware_validation\font_optimization_round4_lut_finetune\Set-Round4PrimeG1CacheVariant.ps1" -Variant lut32_ease150
```

Then restart HP Connectivity Kit and use its firmware update workflow.

## Recommended Hardware Order

1. `lut32_ease150`
2. `lut32_ease135` if `lut32_ease150` is too heavy
3. `lut24_ease140` if both `lut32` variants still feel too hard
4. `lut32_ease170` if `lut32_ease150` is too soft
5. `lut40_ease150` if edge cleanup matters more than softness

## Reproduce Packages Yourself

```powershell
$repo = 'D:\Download\hp-prime-g1-cjk-patch'
$fw = 'D:\Download\HP_Prime_Calculator_Firmware_20250915'
$work = 'D:\Download\hpprime-round4-lut-work'
$py = 'python'

& $py "$repo\scripts\hpprime_round2_variants.py" all `
  --extract `
  --firmware-dir $fw `
  --work-dir $work `
  --flash-root "$work\flash_packages" `
  --variants `
    lut24_ease140 `
    lut32_ease135 `
    lut32_ease150 `
    lut32_ease170 `
    lut40_ease150
```

The public repository includes only scripts, manifests, docs, and images.  It
does not include HP firmware files or any patched firmware payload.
