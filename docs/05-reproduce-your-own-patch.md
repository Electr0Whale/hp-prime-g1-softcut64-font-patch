# Reproduce Your Own Patch

本章给出从官方固件生成 `softcut64` patched 包的完整流程。

## 1. 设置路径

PowerShell 7：

```powershell
$repo = 'D:\Download\hp-prime-g1-cjk-patch'
$fw = 'D:\Download\HP_Prime_Calculator_Firmware_20250915'
$work = 'D:\Download\hpprime-softcut64-work'
$py = 'python'
```

`$fw` 必须是你自己的官方固件目录。

`$work` 会生成提取文件和 patched 文件，不要把它提交到 GitHub。

## 2. 一键生成

```powershell
& $py "$repo\scripts\hpprime_softcut64.py" all `
  --firmware-dir $fw `
  --work-dir $work `
  --cutoff 64 `
  --flash-out "$work\flash_package_softcut64"
```

该命令会依次执行：

```text
extract
generate-softcut
apply
repack
verify
make-flash-package
```

输出目录大致为：

```text
$work\extracted\armfir.elf
$work\extracted\armfir.dat
$work\extracted\fonts\PrimeSans*.ttf
$work\patched\patch_manifest.arm_softcut64.json
$work\patched\armfir.softcut64.elf
$work\patched_firmware\PRIME_APP.softcut64_poc.DAT
$work\patched_firmware\Prime_FW.softcut64_poc.md5
$work\patched_firmware\repack_report.softcut64.json
$work\flash_package_softcut64\PRIME_APP.DAT
$work\flash_package_softcut64\Prime_FW.md5
```

## 3. 分步执行

如果要逐步审计：

```powershell
& $py "$repo\scripts\hpprime_softcut64.py" extract `
  --firmware-dir $fw `
  --work-dir $work
```

```powershell
& $py "$repo\scripts\hpprime_softcut64.py" generate-softcut `
  --work-dir $work `
  --cutoff 64
```

```powershell
& $py "$repo\scripts\hpprime_softcut64.py" apply `
  --manifest "$work\patched\patch_manifest.arm_softcut64.json"
```

```powershell
& $py "$repo\scripts\hpprime_softcut64.py" repack `
  --firmware-dir $fw `
  --work-dir $work `
  --cutoff 64
```

```powershell
& $py "$repo\scripts\hpprime_softcut64.py" verify `
  --firmware-dir $fw `
  --work-dir $work `
  --cutoff 64
```

```powershell
& $py "$repo\scripts\hpprime_softcut64.py" make-flash-package `
  --firmware-dir $fw `
  --work-dir $work `
  --cutoff 64 `
  --out-dir "$work\flash_package_softcut64"
```

## 4. 期望输出

对官方 20250915 G1 输入，`verify` 结果应包含：

```json
{
  "ok": true,
  "cutoff": 64,
  "patched_elf_md5": "32ac6681f1a8287db20fbe33d0035fe7",
  "patched_prime_app_md5": "59c9a785212599acd5b676bf72e6b5c2"
}
```

如果 `ok` 不是 `true`，不要刷入。

## 5. 对照仓库 manifest

你生成的 manifest 应和仓库内这个文件语义一致：

```text
patches/patch_manifest.arm_softcut64.json
```

路径字段会因为本机目录不同而不同，这是正常的。关键是：

- `source_md5` 一致；
- `file_offset` 一致；
- `old` 字节一致；
- `new` 字节一致；
- patched ELF MD5 一致。

## 6. 不要提交的文件

以下文件来自官方固件或由官方固件派生，不应上传到公开仓库：

```text
armfir.elf
armfir.dat
PrimeSans*.ttf
armfir.softcut64.elf
PRIME_APP.softcut64_poc.DAT
Prime_FW.softcut64_poc.md5
flash_package_softcut64\
```

本仓库的 `.gitignore` 已经覆盖这些常见路径。

