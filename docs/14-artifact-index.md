# Artifact Index

## Reproduction

```text
scripts/hpprime_softcut64.py
```

单文件复现工具，负责提取、生成 manifest、应用 patch、重打包、校验和生成 flash package。

## Flashing helpers

```text
tools/connectivity-cache/Install-PrimeG1CachePackage.ps1
tools/connectivity-cache/Verify-PrimeG1CachePackage.ps1
tools/connectivity-cache/Restore-PrimeG1CacheBackup.ps1
```

用于备份、替换和验证 HP Connectivity Kit 的 G1 本地固件缓存。

## Main patch manifests

```text
patches/patch_manifest.arm_softcut64.json
patches/patch_manifest.arm_softcut64.apply_results.json
```

`softcut64` 是当前推荐候选。

## Round2 manifests

```text
patches/round2/patch_manifest.arm_softcut48.json
patches/round2/patch_manifest.arm_softcut80.json
patches/round2/patch_manifest.arm_softband48_240.json
patches/round2/patch_manifest.arm_softband64_240.json
patches/round2/patch_manifest.arm_boost48_125.json
patches/round2/patch_manifest.arm_boost64_125.json
patches/round2/patch_manifest.arm_boost48_150.json
patches/round2/patch_manifest.arm_boost64_150.json
```

These are post-`softcut64` candidates.  They remain parameter/algorithm-level
coverage patches and do not include any HP binary payload.

## Round3 LUT manifests

```text
patches/round3-lut/patch_manifest.arm_lut32_ease150.json
patches/round3-lut/patch_manifest.arm_lut48_ease150.json
patches/round3-lut/patch_manifest.arm_lut32_contrast125.json
patches/round3-lut/patch_manifest.arm_lut48_contrast150.json
```

These use the same gray coverage patch point but route coverage through a
256-byte lookup table.  They preserve `FT_PIXEL_MODE_GRAY` and do not include
any HP binary payload.

## LUT fine-tune manifests

```text
patches/round4-lut-finetune/patch_manifest.arm_lut24_ease140.json
patches/round4-lut-finetune/patch_manifest.arm_lut32_ease135.json
patches/round4-lut-finetune/patch_manifest.arm_lut32_ease170.json
patches/round4-lut-finetune/patch_manifest.arm_lut40_ease150.json
```

These are nearby `ease` LUT parameters around `lut32_ease150`.  They are
provided so a chosen visual style can be reproduced without shipping patched
firmware.

## Rejected manifests

```text
patches/patch_manifest.coverage255.rejected.json
patches/patch_manifest.threshold128.rejected.json
```

这些保留为研究过程证据，不建议刷入。

## Experimental manifests

```text
patches/patch_manifest.arm_softband64_224.experimental.json
```

更锐利但风险更高的候选。只有 `softcut64` 实机反馈仍偏软时才考虑。

## Reports

```text
reports/render_algorithm_patch_points.md
reports/smooth_renderer_analysis.md
reports/arm_softcut64_patch_report.md
reports/emulator_softcut_patch_report.md
reports/coverage255_patch_report.rejected.md
reports/threshold128_patch_report.rejected.md
reports/softband_patch_report.experimental.md
reports/external_projects_assessment.md
reports/updater_patch_guide.rejected.md
reports/round3_preview_metrics.md
reports/lut_finetune_preview_metrics.md
```

这些报告来自探索过程，保留更多原始细节。

## Images

```text
images/emulator_softcut_only_comparison_crops.png
images/emulator_softcut_only_comparison_full.png
images/emulator_round3_comparison_crops.png
images/emulator_round3_comparison_full.png
images/emulator_lut_finetune_comparison_crops.png
images/emulator_lut_finetune_comparison_full.png
```

模拟器对比图。用于说明为什么选择 `softcut64`，不是硬件最终验收。

## Example output

```text
examples/repack_report.softcut64.example.json
```

示例 repack report，路径已替换为 `<work>` 占位符。
