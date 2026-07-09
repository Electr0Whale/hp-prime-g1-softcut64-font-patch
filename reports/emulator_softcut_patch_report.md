# Emulator Softcut Coverage Patch Report

## Summary

The pure binary threshold experiments are not visually acceptable for dense
12 px Chinese text. They prove that the FreeType gray coverage output point is
under control, but they also turn many glyph interiors into solid black blocks
or remove too many strokes.

The better simulator PoC is now the soft cutoff family:

```c
coverage = min(coverage, 255);
if (coverage < cutoff) {
    coverage = 0;
}
```

This keeps the existing FreeType `FT_PIXEL_MODE_GRAY` bitmap layout and preserves
mid/high gray coverage instead of converting glyphs to 1-bit output.

## Implemented Variants

- `softcut64`
- `softcut96`

Artifacts:

- `patched\patch_manifest.emulator_softcut64.json`
- `patched\patch_manifest.emulator_softcut96.json`
- `patched_emulator\HPPrime.softcut64.exe`
- `patched_emulator\HPPrime.softcut96.exe`
- `patched_emulator_runtime_softcut64\HPPrime.exe`
- `patched_emulator_runtime_softcut96\HPPrime.exe`
- `screenshots\patched\emulator_softcut64_apps.png`
- `screenshots\patched\emulator_softcut96_apps.png`
- `screenshots\patched\emulator_threshold_comparison_crops.png`
- `patched\emulator_apps_screenshot_stats.md`
- `patched\emulator_softcut64_verification.json`
- `patched\emulator_softcut96_verification.json`

## Patch Shape

The original x64 simulator clamp sites are redirected to stubs placed in an
existing zero-filled `.rdata` cave:

- Cave file offset: `0xd97030`
- Cave VA: `0x140d99630`
- Section characteristics patch: `.rdata` changes from read-only data to
  read/execute data by adding `IMAGE_SCN_MEM_EXECUTE`.

Patched callouts:

- `0x140cec316 -> 0x140d99630`, output register `edx`
- `0x140cece8a -> 0x140d99670`, output register `eax`
- `0x140cecf84 -> 0x140d996b0`, output register `r8d`

The stubs reproduce the original `coverage >= 256 ? 255 : coverage` clamp,
then zero only low coverage values below the cutoff, and jump back to the
original continuation addresses.

This is intentionally a simulator PoC technique. It is useful for visual
validation, but the `.rdata` executable cave method should not be copied
directly into ARM firmware without a separate ARM-specific code cave plan.

## Visual Result

The hard threshold variants all remove midtones:

| ROI | baseline largest solid | threshold128 | threshold160 | threshold192 | softcut64 | softcut96 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `label_function` | 12 | 144 | 128 | 28 | 12 | 12 |
| `label_spreadsheet` | 36 | 192 | 192 | 136 | 36 | 36 |
| `label_statistics` | 44 | 300 | 268 | 92 | 44 | 44 |
| `label_datasampler` | 20 | 192 | 156 | 104 | 20 | 20 |

The important signal is that `softcut64` and `softcut96` reduce faint coverage
pixels while preserving baseline-sized solid components. That matches the user
feedback: avoid black block formation while reducing blur.

Current visual preference:

- `softcut64`: safer; closer to baseline, fewer faint edge pixels.
- `softcut96`: sharper but starts dropping more light strokes.
- `threshold128/160/192`: not recommended as final visual settings.

## Verification

Run:

```powershell
& 'python' `
  '<work>\scripts\verify_emulator_softcut_artifacts.py' `
  --manifest '<work>\patched\patch_manifest.emulator_softcut64.json'

& 'python' `
  '<work>\scripts\verify_emulator_softcut_artifacts.py' `
  --manifest '<work>\patched\patch_manifest.emulator_softcut96.json'
```

Both variants currently pass:

- PE size unchanged.
- Source MD5 matches the original simulator copy.
- Patched exe equals original plus manifest-described bytes only.
- `.rdata` has `IMAGE_SCN_MEM_EXECUTE` set.
- Each original clamp point redirects to the expected softcut stub.
- Each stub compares against the expected cutoff and jumps back to the original
  continuation.

## Next ARM Direction

For firmware, do not migrate the simulator `.rdata` code-cave technique blindly.
The ARM side should first search near `gray_hline` / `gray_sweep` for one of:

- an existing executable padding area inside the loaded ARM segment;
- an in-place sequence long enough for clamp + low-cutoff logic;
- a nearby literal-controlled branch table or helper that can be repurposed
  without changing segment sizes.

The semantic target for ARM should be `softcut64` first, not binary threshold.
If ARM space is too tight for a stub, the next fallback is a smaller in-place
coverage attenuation experiment, but pure 1-bit threshold should remain a
rejected visual branch unless the font itself changes.

