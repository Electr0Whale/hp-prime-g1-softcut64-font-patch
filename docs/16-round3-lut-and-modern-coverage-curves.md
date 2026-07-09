# Round3 LUT And Modern Coverage Curves

`softcut64` has passed a real HP Prime G1 flash test, so the next useful
question is no longer whether the gray coverage patch point works.  It does.
Round3 explores better coverage transfer curves while preserving the same
contract:

- no font resource replacement;
- no packed 1-bit bitmap output;
- no compositor rewrite;
- no ELF or FAT file size changes;
- still patch only the FreeType gray coverage output path.

This avoids the earlier hard-threshold failure mode where small Chinese text
can turn into dense black blocks.

## Why LUT Curves

`softcut` and `boost` are simple formulas.  They are easy to audit, but they
have limited control:

```c
softcut: coverage < low ? 0 : coverage
boost:   coverage < low ? 0 : min(255, coverage + (coverage >> shift))
```

A 256-byte LUT keeps the same 8-bit grayscale bitmap format, but allows any
monotonic coverage curve:

```c
coverage = min(coverage, 255);
coverage = table[coverage];
```

This is a better modern fit for low-resolution LCD font tuning because it can
separate three different goals:

- remove very weak fringe coverage;
- preserve mid-tone anti-aliasing where it helps recognition;
- darken strong strokes without forcing every edge to black.

## Candidate Families

### boost48_125

```c
coverage = min(coverage, 255);
if (coverage < 48) {
    coverage = 0;
} else {
    coverage += coverage >> 2;
    coverage = min(coverage, 255);
}
```

This is the mild linear-darkening candidate.  It should look sharper than
`softcut64` but still avoid the worst black-block behavior.

### boost48_150

```c
coverage = min(coverage, 255);
if (coverage < 48) {
    coverage = 0;
} else {
    coverage += coverage >> 1;
    coverage = min(coverage, 255);
}
```

This is the aggressive linear-darkening candidate.  It is useful when
`softcut64` still looks too light or soft, but it has higher risk of Chinese
stroke sticking.

### lut32_ease150

```c
if (coverage < 32) {
    out = 0;
} else {
    t = (coverage - 32) / (255 - 32);
    out = 255 * (1 - (1 - t)^1.50);
}
```

This is the most balanced modern candidate in this round.  It keeps more edge
information than `boost48_150`, but lifts mid and high coverage more smoothly
than a linear multiplier.

### lut48_contrast150

```c
if (coverage < 48) {
    out = 0;
} else {
    out = clamp(128 + 1.50 * (coverage - 128));
}
```

This is the sharp/high-contrast LUT candidate.  It can look very crisp on thin
Latin strokes, but dense Chinese is the main risk area.

## Simulator Preview

The preview compares:

```text
baseline
softcut64
boost48_125
boost48_150
lut32_ease150
lut48_contrast150
```

### Crops

![round3 comparison crops](../images/emulator_round3_comparison_crops.png)

### Full Page

![round3 full comparison](../images/emulator_round3_comparison_full.png)

## Static Verification Results

For official G1 20250915 input:

| Variant | armfir.elf MD5 | PRIME_APP.DAT MD5 |
| --- | --- | --- |
| `lut32_ease150` | `eea4b32eb430cce1509d2d9a65eb5c93` | `ff1433c4b422a1a6cf30c9c1389dd9a0` |
| `lut48_ease150` | `32e1a8eccf50b70e6e601407a93b9055` | `b585c32cd58641d93220e5cf40087dc0` |
| `lut32_contrast125` | `860d1f02c83ba35c4773f97376e4d707` | `a3ae11391452af41327ee962069e0849` |
| `lut48_contrast150` | `d7cd4c7af5d759082808906be0682cc1` | `f19a33e245afdf6c05510ff3721f516a` |

Verification covered:

- patched ELF keeps the original `8230724` byte size;
- patched ELF still has ELF magic;
- patched ELF equals source plus manifest bytes only;
- `programs/misc/armfir.elf` is written back at the same FAT16 file size;
- `APPSLIST.MD5` matches the patched `armfir.elf`;
- outer `Prime_FW.md5` matches patched `PRIME_APP.DAT`.

## Generate LUT Variants

The existing round2 helper now also recognizes LUT variant names:

```powershell
$repo = 'D:\Download\hp-prime-g1-softcut64-font-patch'
$fw = 'D:\Download\HP_Prime_Calculator_Firmware_20250915'
$work = 'D:\Download\hpprime-round3-lut-work'
$py = 'python'

& $py "$repo\scripts\hpprime_round2_variants.py" all `
  --extract `
  --firmware-dir $fw `
  --work-dir $work `
  --flash-root "$work\flash_packages" `
  --variants `
    lut32_ease150 `
    lut48_ease150 `
    lut32_contrast125 `
    lut48_contrast150
```

## Current Recommendation

Use the simulator preview before flashing.  The likely order is:

1. `lut32_ease150`
2. `boost48_125`
3. `boost48_150`
4. `lut48_contrast150`

`lut32_ease150` is the first candidate I would take to hardware if the goal is
cleaner text without the hard pixel look.  `lut48_contrast150` is the more
aggressive option if the LCD still looks too soft, but it should be treated as
a higher-risk dense-Chinese test.
