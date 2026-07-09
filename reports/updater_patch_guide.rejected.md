# HP Prime Updater patch guide

> Status: rejected.  This document is preserved as a lab note.  The patched
> standalone Updater crashed in local testing, so the recommended flashing path
> is the official HP Connectivity Kit local firmware cache route, not this
> Updater patch.

## Finding

`Updater.exe` has two relevant gates in the local-folder update path:

1. An early filename filter accepts legacy G1 names:

```text
APPSDISK.DAT
BESTAARM.ROM
MASTER.DAT
```

The later classifier also knows the official package names:

```text
PRIME_APP.DAT
PRIME_OS.ROM
PRIME_MASTER.DAT
```

But the early filter can prevent those `PRIME_*` files from entering the update list.

2. After folder parsing, the updater compares the accepted update item count/state and routes to `No updates are available` unless it reaches the update path.

## Generated runtimes

All runtimes are copies under:

```text
<work>\updater_patch
```

The original installed files in `C:\Program Files\HP\HP Connectivity Kit` were not modified.

Recommended runtime:

```text
<work>\updater_patch\ConnectivityKit_updater_prime_names_version_bypass_runtime\Updater.exe
```

This runtime contains both patches:

- accept `PRIME_APP.DAT`, `PRIME_OS.ROM`, `PRIME_MASTER.DAT` in the early filename filter;
- change `cmp eax, 3; je start_update` into `cmp eax, 3; jmp start_update` to bypass the final no-update/version gate.

Lower-risk diagnostic runtime:

```text
<work>\updater_patch\ConnectivityKit_updater_prime_names_runtime\Updater.exe
```

This only fixes the early `PRIME_*` filename filter.

Aggressive diagnostic runtime:

```text
<work>\updater_patch\ConnectivityKit_updater_version_bypass_runtime\Updater.exe
```

This only bypasses the final no-update/version gate. Use the combined runtime instead unless specifically diagnosing.

## Verification

Run:

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File "<work>\updater_patch\Verify-UpdaterPatches.ps1"
```

Expected result:

```text
Updater patch verification passed.
```

The combined runtime differs from the original copied `Updater.exe` at exactly four bytes:

```text
0x5a13: 09 -> 39
0x5a27: 05 -> 35
0x5a3b: 01 -> 31
0x5ce2: 74 -> eb
```

Combined runtime SHA256:

```text
eccfaf26722aed2717a6bb01f5b83a3285438576d5df41f04206163aaa1a3423
```

## Recommended use

1. Run the combined runtime `Updater.exe`.
2. Click `Browse for update files`.
3. Select:

```text
<work>\hardware_validation\softcut64\flash_package
```

4. If this reaches `Start` / update progress, proceed with the existing flashing guide.
5. If it still fails before any device write starts, try the no-executable-patch legacy-name package with the original Updater:

```text
<work>\hardware_validation\softcut64\flash_package_legacy_names
```

Do not continue if the updater begins writing and then errors repeatedly; switch to stock rollback.


