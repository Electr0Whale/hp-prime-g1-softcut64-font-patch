# External Project Assessment

## Scope

Reviewed local mirrors under:

- `<work>\external\prinux`
- `<work>\external\Linux-For-HPPrime-V2`
- `<work>\external\hpprimev2_linux_loader`
- `<work>\external\Kernel-6.1.35-HP-Prime-V2_G1`

The question was whether these projects help the HP Prime G1 font-rendering
firmware patch effort.

## zephray/prinux

`prinux` is useful background, but it targets HP Prime G2 hardware:

- The README explicitly requires a HP Prime G2 calculator.
- The boot path uses i.MX6ULL SDP mode and NXP `uuu` scripts.
- Its NAND backup/restore scripts are valuable as a model for recovery hygiene,
  but they do not match the G1 firmware package or SoC.

Conclusion: useful for general caution around full NAND backup and recovery,
not directly useful for G1 `armfir.elf` font patching.

## Repeerc/Linux-For-HPPrime-V2

This project is relevant to G1 hardware despite the confusing `V2` name. Its
README title says `Linux for HP Prime V2 (G1)`, and it provides:

- NAND flash geometry: Hynix H27U2G8F2CTR-BC, 256 MiB SLC, 128 KiB erase block,
  2048-byte page, 64-byte OOB, 2048 total blocks.
- Flash layout:
  - blocks `0..1`: `BXCBOOT0.BIN` HP boot code and recovery mode.
  - blocks `2..9`: `BOOT1.ROM`.
  - blocks `10..x`: kernel.
  - blocks `64..y`: rootfs.
  - block `2047`: serial number and original system data.
- Recovery-mode update flow using `usbtool.exe` with:
  - `BOOT1.ROM` at offset `0x00000000`.
  - `LINUX.DAT` at offset `0x000C0000`.
- `mkimg.sh` layout for `LINUX.DAT`: 63 MiB filled with `0xff`, kernel at
  offset 0, rootfs at offset 8 MiB.

Conclusion: useful for G1 hardware recovery/flash-layout planning. It does not
directly explain the official `PRIME_APP.DAT` update package, but it gives a
separate route to reason about protected boot blocks and rollback discipline.

## hpprimev2_linux_loader

This is the most technically useful external source for G1 hardware facts:

- Link/load origin: `0x30000000`, 512 KiB loader image.
- ARM core tuning: `arm926ej-s`, little-endian ARM mode.
- RAM base: `0x30000000`; loader assumes 32 MiB RAM and reserves 512 KiB for
  framebuffer.
- LCD:
  - resolution `320x240`.
  - framebuffer at `0x30000000 + 32 MiB - 512 KiB`.
  - tested 24-bit framebuffer path.
  - LCD controller register base `0x4C800000`.
- NAND:
  - controller register base `0x4E000000`.
  - standard large-page command sequence.
  - loader sets flash lock boundary to protect blocks `0..9` and `2041..2047`.
- Keypad:
  - columns via `GPKDAT`, rows via `GPGDAT`.

Conclusion: useful for standalone ARM instrumentation, LCD test payloads, NAND
recovery planning, and understanding where the firmware may place framebuffer
memory. It does not directly identify FreeType or font rendering in the official
OS, but it helps design safe runtime experiments on real G1 hardware.

## Kernel-6.1.35-HP-Prime-V2_G1

The local checkout currently contains only `.git` metadata, so there are no
source files to inspect in the working tree. The remote is:

`https://github.com/Repeerc/Kernel-6.1.35-HP-Prime-V2_G1`

Conclusion: no local evidence yet. A full checkout could help later with device
tree, keypad, LCD, NAND, and USB recovery details, but it is not needed for the
current FreeType raster patch.

## Impact On Font Patch Strategy

These projects do not change the font-rendering conclusion:

- The official firmware still uses statically linked FreeType `smooth` renderer.
- The practical font clarity patch remains inside FreeType's gray coverage
  output path, preserving `FT_PIXEL_MODE_GRAY`.
- `FT_RENDER_MODE_MONO` remains risky because packed 1-bit bitmap output would
  likely violate the official compositor's expected 8-bit gray buffer contract.

They do improve the next testing plan:

1. Treat `PRIME_APP.softcut64_poc.DAT` as a firmware-package experiment, not
   as a raw NAND image.
2. Before any hardware test, use HP recovery/update behavior documentation and
   make a separate rollback plan.
3. If a standalone ARM probe is needed, reuse the loader project's facts:
   `0x30000000` RAM base, 320x240 LCD, framebuffer near top of 32 MiB RAM, and
   `arm926ej-s` ARM mode.
4. Do not rely on `prinux` G2 SDP/uuu flow for G1 flashing.

