# Round2 Coverage Optimization

`softcut64` has now been tested successfully on real HP Prime G1 hardware.  That
changes the next step: the patch point itself is proven viable, so round2 can
be more aggressive while still preserving the same 8-bit grayscale bitmap
contract.

## Design Boundary

Round2 still does not:

- replace fonts;
- use `FT_RENDER_MODE_MONO`;
- change `FT_PIXEL_MODE_GRAY`;
- change ELF size;
- change `PRIME_MASTER.DAT` or `PRIME_OS.ROM`.

All variants still patch the FreeType gray coverage output path near
`gray_hline`, then repack only `programs/misc/armfir.elf` inside
`PRIME_APP.DAT`.

## Variant Families

### softcut

```c
coverage = min(coverage, 255);
if (coverage < low) {
    coverage = 0;
}
```

Variants:

```text
softcut48  more natural, less sharp than softcut64
softcut80  sharper than softcut64, higher risk of thin/broken strokes
```

### softband

```c
coverage = min(coverage, 255);
if (coverage < low) {
    coverage = 0;
}
if (coverage >= high) {
    coverage = 255;
}
```

Variants:

```text
softband48_240  mild solid-stem strengthening
softband64_240  softcut64 plus only very-high coverage forced black
```

### boost

```c
coverage = min(coverage, 255);
if (coverage < low) {
    coverage = 0;
} else {
    coverage += coverage >> shift;
    if (coverage >= 256) {
        coverage = 255;
    }
}
```

Variants:

```text
boost48_125  low=48, about 1.25x surviving coverage
boost64_125  low=64, about 1.25x surviving coverage
boost48_150  low=48, about 1.5x surviving coverage
boost64_150  low=64, about 1.5x surviving coverage
```

`boost48_125` is the recommended first round2 test.  It is more aggressive than
`softcut64`, but it is less likely than `boost64_150` to create dense Chinese
stroke sticking.

## Generate Round2 Variants

```powershell
$repo = 'D:\Download\hp-prime-g1-softcut64-font-patch'
$fw = 'D:\Download\HP_Prime_Calculator_Firmware_20250915'
$work = 'D:\Download\hpprime-round2-work'
$py = 'python'

& $py "$repo\scripts\hpprime_round2_variants.py" all `
  --extract `
  --firmware-dir $fw `
  --work-dir $work `
  --flash-root "$work\flash_packages" `
  --variants `
    softcut48 `
    softcut80 `
    softband48_240 `
    softband64_240 `
    boost48_125 `
    boost64_125 `
    boost48_150 `
    boost64_150
```

Output flash packages will be under:

```text
$work\flash_packages\flash_package_boost48_125
$work\flash_packages\flash_package_boost48_150
$work\flash_packages\flash_package_boost64_125
$work\flash_packages\flash_package_boost64_150
$work\flash_packages\flash_package_softband48_240
$work\flash_packages\flash_package_softband64_240
$work\flash_packages\flash_package_softcut48
$work\flash_packages\flash_package_softcut80
```

Each package contains:

```text
PRIME_APP.DAT
PRIME_MASTER.DAT
PRIME_OS.ROM
Prime_FW.md5
```

## Expected MD5s

For official G1 20250915 input:

| Variant | armfir.elf MD5 | PRIME_APP.DAT MD5 |
| --- | --- | --- |
| `softcut48` | `63f146fcb26d7db63f7340156fbb1ed2` | `7e6ba77b54fbbdf8d0b92705ff1405e3` |
| `softcut80` | `0213a3aa11784fd3c47cb2f172237e50` | `86832ecfc1b6ae358896dedc45ef2300` |
| `softband48_240` | `b63e895284a68c34efda3113a975c9e8` | `a9dab93503f1e21519819c261580cf96` |
| `softband64_240` | `a5a96bfeb4e11dd338339854f34a9edd` | `e64d713d219a5f8d892f5ea9fdd03ea7` |
| `boost48_125` | `0119700662235c2c09c82312a9271e66` | `043abf7df048fbfa01ef836479db9672` |
| `boost64_125` | `1175dc34706918587059ca12873a27dd` | `6404fd314e668de8625eea65d157024b` |
| `boost48_150` | `cab2d965540ac81e2b018c0bcba05c6f` | `2d63727fb67bfe7d994e20599142e597` |
| `boost64_150` | `167210aedc212b148472927bc03a228e` | `5af03671e838a52b450264535868e97b` |

## Suggested Hardware Order

Start with:

1. `boost48_125`
2. `boost48_150`
3. `softband64_240`
4. `softcut80`

Use the remaining variants only if those four do not bracket the desired look.

Judgement criteria:

- dense Chinese at 12 px;
- Home/CAS readability;
- math symbols;
- menus and soft keys;
- input box text;
- black blocks;
- stroke sticking;
- broken thin strokes.

If a variant produces black blocks or unreadable Chinese, stop testing that
branch and go back to `softcut64` or stock.

