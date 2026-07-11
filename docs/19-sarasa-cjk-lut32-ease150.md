# Sarasa CJK MaxCoverage + lut32_ease150

## 中文

### 目标

这一变体把两项修改组合在一起：`lut32_ease150` 负责小字号灰度覆盖曲线，混合字体负责扩大 CJK 统一表意文字覆盖。路由范围严格限定为 `U+3400–4DBF`、`U+4E00–9FFF`、`U+F900–FAFF`；假名、谚文和 CJK 标点并不自动切换到 Sarasa。其他字符使用 Prime Sans，避免替换数字、拉丁字母、数学符号和 HP Prime 界面原有风格。

### 字体结果

| 项目 | 值 |
|---|---:|
| UPM | 256 |
| 字体大小 | 4,613,200 bytes |
| 固件槽大小 | 4,613,520 bytes |
| 零填充 | 320 bytes |
| Sarasa CJK 码位 | 16,914 |
| 尚未覆盖的 Prime/Sarasa 共有表意文字 | 10,872 |
| 保留的 Prime 非 CJK 字符 | 2,632 |
| 内部 family / PostScript 名称 | `Prime Sans` / `PrimeSansFull` |
| 字体 SHA-256 | `4be714aa90bb6f0f48bb7b395bb79a61ce42fcad682749b5215dea0ab1a444b4` |

字体轮廓从 Sarasa 的高 UPM 坐标缩放到 256 UPM。旧 TrueType hinting 指令不能直接随坐标安全缩放，因此生成过程会避免保留不再匹配的 Sarasa hinting，并依赖 HP Prime 的 FreeType 灰度栅格化及 LUT 曲线。Prime 原有非 CJK 字形保持原始轮廓和字符映射。

### 渲染曲线

`lut32_ease150` 将 0–255 灰度覆盖值量化为 32 级，并使用约 1.5 次幂的 easing 曲线。它比官方原始灰度更收敛，但不像硬阈值那样直接丢弃全部弱覆盖像素。

### 固件边界

最终 `PRIME_APP.DAT` 只允许在两个区域发生变化：

1. `programs/misc/armfir.dat` 内的 `PrimeSansFull` 固定字体槽；
2. FAT16 中 `APPSLIST.MD5` 所在簇，用于登记新的 `armfir.dat` MD5。

`armfir.elf` 必须与已验证的 `lut32_ease150` 基准完全一致；`PRIME_MASTER.DAT` 和 `PRIME_OS.ROM` 必须保持官方版本不变。外层 `Prime_FW.md5` 随新的 APP 哈希重新生成。

验证过的最终 APP：

```text
MD5     c97cd74b3b3de4d6c60da4bd08481a99
SHA-256 56f5bc341e6c4f3f23715dcc8319fc62d79d21278f2f3530143372752b3bc503
```

这些哈希只用于识别由本实验输入生成的本地产物；仓库不分发该二进制文件。

### 实机刷入

使用 [06-flashing-with-connectivity-kit-cache.md](06-flashing-with-connectivity-kit-cache.md) 的缓存方式。关闭 Connectivity Kit 和 Updater，完整备份 `Documents\HP Connectivity Kit\固件\PrimeG1`，仅替换 `PRIME_APP.DAT`，然后按固定顺序重建 13 行 `Prime_FW.md5`。重新打开 Connectivity Kit 后，由用户手动触发更新。

## English

### Goal

This variant combines two changes: `lut32_ease150` controls small-size grayscale coverage, while the hybrid expands CJK unified-ideograph coverage. Routing is strictly limited to `U+3400–4DBF`, `U+4E00–9FFF`, and `U+F900–FAFF`; kana, Hangul, and CJK punctuation are not automatically routed to Sarasa. Everything else remains Prime Sans.

### Font result

| Property | Value |
|---|---:|
| UPM | 256 |
| Font size | 4,613,200 bytes |
| Firmware slot | 4,613,520 bytes |
| Zero padding | 320 bytes |
| Sarasa CJK code points | 16,914 |
| Prime/Sarasa shared ideographs still omitted | 10,872 |
| Retained Prime non-CJK characters | 2,632 |
| Internal family / PostScript name | `Prime Sans` / `PrimeSansFull` |
| Font SHA-256 | `4be714aa90bb6f0f48bb7b395bb79a61ce42fcad682749b5215dea0ab1a444b4` |

Sarasa outlines are scaled from their high-UPM coordinates to 256 UPM. Existing TrueType instructions cannot safely be scaled with those coordinates, so the generated CJK glyphs do not retain mismatched Sarasa hinting; rasterization instead relies on the Prime FreeType grayscale path and the LUT curve. Original Prime non-CJK glyphs retain their outlines and mappings.

### Renderer curve

`lut32_ease150` quantizes 0–255 coverage into 32 levels and applies an approximately 1.5-power easing curve. It tightens the stock grayscale output without discarding all weak coverage as a hard threshold would.

### Firmware boundary

The final `PRIME_APP.DAT` is allowed to differ only in the fixed `PrimeSansFull` slot inside `programs/misc/armfir.dat` and in the FAT16 cluster containing `APPSLIST.MD5`. `armfir.elf` must remain identical to the validated `lut32_ease150` base. `PRIME_MASTER.DAT` and `PRIME_OS.ROM` remain official and unchanged. The outer `Prime_FW.md5` is regenerated for the new APP hash.

Validated final APP identity:

```text
MD5     c97cd74b3b3de4d6c60da4bd08481a99
SHA-256 56f5bc341e6c4f3f23715dcc8319fc62d79d21278f2f3530143372752b3bc503
```

These hashes identify the locally generated artifact; the binary is not distributed by this repository.

### Hardware flashing

Follow [06-flashing-with-connectivity-kit-cache.md](06-flashing-with-connectivity-kit-cache.md). Close Connectivity Kit and Updater, fully back up `Documents\HP Connectivity Kit\固件\PrimeG1`, replace only `PRIME_APP.DAT`, and regenerate the complete 13-line `Prime_FW.md5`. Reopen Connectivity Kit and initiate the update manually.
