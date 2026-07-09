# HP Prime G1 softcut64 font patch

This repository documents and reproduces an experimental HP Prime G1 firmware
font-rendering patch for the official 20250915 firmware.

The chosen patch is `softcut64`:

```c
coverage = min(coverage, 255);
if (coverage < 64) {
    coverage = 0;
}
```

It keeps the original FreeType grayscale bitmap path (`FT_PIXEL_MODE_GRAY`) and
only removes weak gray fringe coverage.  It does not replace fonts, does not add
a renderer, and does not change ELF or FAT file sizes.

## Status

- Target: HP Prime G1 only, official 20250915 firmware.
- Recommended candidate: ARM `softcut64`.
- Static verification: passed.
- Repack verification: passed.
- Emulator comparison: generated and included.
- Standalone patched Updater route: rejected because it crashed in local testing.
- Practical flashing route: HP Connectivity Kit local G1 firmware cache.
- Hardware validation: experimental; use a recovery plan before flashing.

## What is included

- Detailed research notes and reproduction docs in `docs/`.
- Public-safe patch manifests in `patches/`.
- A parameterized Python helper in `scripts/hpprime_softcut64.py`.
- Connectivity Kit cache helper scripts in `tools/connectivity-cache/`.
- Rejected and experimental route notes in `reports/`.
- Visual comparison images in `images/`.
- Post-`softcut64` boost/LUT candidate notes and previews.

## What is not included

This repository intentionally does not include:

- HP official firmware files.
- HP simulator or Connectivity Kit binaries.
- Extracted HP fonts.
- Patched `armfir.elf`.
- Patched `PRIME_APP.DAT`.
- Patched `Updater.exe`.

You must obtain the official firmware and tools yourself, then run the scripts
locally to generate your own patched artifacts.

## Fast path

PowerShell 7 is recommended on Windows:

```powershell
$fw = 'D:\Download\HP_Prime_Calculator_Firmware_20250915'
$work = 'D:\Download\hpprime-softcut64-work'
$repo = 'D:\Download\hp-prime-g1-softcut64-font-patch'
$py = 'python'

& $py "$repo\scripts\hpprime_softcut64.py" all `
  --firmware-dir $fw `
  --work-dir $work `
  --cutoff 64 `
  --flash-out "$work\flash_package_softcut64"
```

Expected final MD5 values for the 20250915 G1 source:

```text
original armfir.elf                 9e1ed504c294e70ff478e0bd5553c441
patched armfir.softcut64.elf        32ac6681f1a8287db20fbe33d0035fe7
patched PRIME_APP.softcut64_poc.DAT 59c9a785212599acd5b676bf72e6b5c2
```

Then read the flashing guide before using the output:

- `docs/06-flashing-with-connectivity-kit-cache.md`
- `docs/07-rollback-and-recovery.md`
- `docs/11-hardware-test-checklist.md`

## Key docs

- `docs/00-overview.md` - goal, route, status, and safety boundary.
- `docs/02-firmware-layout.md` - FAT16, `armfir.elf`, fonts, and FreeType facts.
- `docs/03-font-rendering-analysis.md` - where the rendering algorithm was found.
- `docs/04-softcut64-design.md` - why `softcut64` was selected.
- `docs/05-reproduce-your-own-patch.md` - end-to-end local reproduction.
- `docs/06-flashing-with-connectivity-kit-cache.md` - practical flashing path.
- `docs/08-updater-analysis.md` - why the standalone Updater route was rejected.
- `docs/12-visual-comparison.md` - simulator comparison images and visual conclusion.
- `docs/13-research-log.md` - chronological exploration record.
- `docs/14-artifact-index.md` - what every included artifact is for.
- `docs/15-round2-coverage-optimization.md` - more aggressive post-softcut64 candidates.
- `docs/16-round3-lut-and-modern-coverage-curves.md` - LUT curves and round3 preview.
- `docs/17-lut-finetune-preview.md` - fine-tuned LUT candidates around `lut32_ease150`.
- `docs/candidate-selection-dashboard.html` - offline image/metric dashboard for choosing the next hardware candidate.

## Warning

This is experimental firmware modification work.  Flashing a calculator can
brick it or require recovery.  Back up calculator data first, verify every hash,
keep an official stock package ready, and do not use this on G2 hardware.

