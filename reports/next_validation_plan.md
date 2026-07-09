# Next Validation Plan

## Current Candidate

Use `softcut64` for the first controlled HP Prime G1 hardware validation.

Artifacts:

- `<work>\patched\armfir.softcut64.elf`
- `<work>\patched_firmware\PRIME_APP.softcut64_poc.DAT`
- `<work>\patched_firmware\Prime_FW.softcut64_poc.md5`
- `<work>\hardware_validation\softcut64\flash_package`
- `<work>\hardware_validation\softcut64\flash_package_force_20250916`
- `<work>\hardware_validation\softcut64\flash_package_legacy_names`
- `<work>\hardware_validation\softcut64\stock_rollback_package`
- `<work>\updater_patch\ConnectivityKit_updater_prime_names_version_bypass_runtime\Updater.exe`

Reason: simulator comparison rejected hard threshold styles as too blocky for
dense 12 px text. `softcut64` preserves the official 8-bit gray bitmap path and
only removes very low coverage below 64:

```c
coverage = min(coverage, 255);
if (coverage < 64) {
    coverage = 0;
}
```

## What Is Proven

- FreeType `smooth` gray coverage path is located.
- `softcut64` modifies the ARM firmware through a manifest-based patch.
- Patched ELF size and ELF magic are unchanged.
- Patched ELF equals original plus manifest-described byte edits only.
- `PRIME_APP.DAT` FAT16 is still parseable.
- Embedded `programs/misc/armfir.elf` matches `armfir.softcut64.elf`.
- `APPSLIST.MD5` matches the patched `armfir.elf`.
- Outer `Prime_FW.md5` matches the repacked `PRIME_APP.DAT`.
- Full hardware-validation staging directory has been created with official
  filenames.
- A force-version staging directory has been created for the common case where
  Updater rejects same-version `20250915` packages as `No updates are available`.
- A legacy-name staging directory has been created because standalone
  `Updater.exe` early-filtered local files by `APPSDISK.DAT`, `BESTAARM.ROM`,
  and `MASTER.DAT`.
- A patched Updater copy has been created that accepts `PRIME_*` names and
  bypasses the final no-update gate.
- Stock rollback package has been created from unmodified official files.
- `Verify-Softcut64ValidationPackage.ps1` verifies both packages.

## What Is Not Yet Proven

- No real HP Prime G1 has been flashed by Codex.
- Runtime boot behavior on hardware is unknown.
- LCD visual quality is unknown beyond simulator-side comparison.
- The user's specific USB/driver/Updater environment still needs live checking.

## Hardware Validation Package

Root:

```text
<work>\hardware_validation\softcut64
```

Before flashing:

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File "<work>\hardware_validation\softcut64\Verify-Softcut64ValidationPackage.ps1"
```

Read:

- `FLASHING_GUIDE.md`
- `ROLLBACK_AND_RECOVERY.md`
- `HARDWARE_TEST_CHECKLIST.md`

## Update Tool Evidence

Local official evidence supports this route:

- Connectivity Kit PDF: `Help > Update Calculator` manually updates firmware
  over USB.
- Connectivity Kit PDF: right-click calculator in Calculators pane and select
  `Update firmware`; calculator display changes to `Recovery Mode`.
- Connectivity Kit PDF troubleshooting: paperclip reset, change USB port,
  repeat update.
- `Updater.exe` strings include `Browse for update files`, `PRIME_APP.DAT`,
  `PRIME_MASTER.DAT`, `PRIME_OS.ROM`, and `Prime update`.
- Updater disassembly shows an early local-folder filename filter originally
  accepting legacy names and a later `cmp eax, 3; je start_update` gate before
  the `No updates are available` branch.

## Decision Gates

Proceed with `softcut64` only if:

- package verification passes immediately before flashing;
- stock rollback package is present;
- user data backup is complete;
- HP Connectivity Kit sees the calculator over USB;
- the Updater path exposes local update file browsing or otherwise clearly uses
  the prepared `flash_package` directory.
- if `flash_package` reports `No updates are available`, use
  `flash_package_force_20250916`, whose firmware payload is identical but whose
  outer `version_` marker is one day newer.

Rollback immediately if:

- text has black blocks or is unreadable;
- glyphs are missing or menus are unusable;
- the device boot-loops or crashes;
- Connectivity Kit cannot reliably see the device after flashing.

Do not continue resource-level font replacement in this validation track.

