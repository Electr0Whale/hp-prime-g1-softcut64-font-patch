[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)

$Root = Split-Path -Parent $PSCommandPath
$Original = Join-Path $Root 'ConnectivityKit_patched_runtime\Updater.exe'
$PrimeNames = Join-Path $Root 'ConnectivityKit_updater_prime_names_runtime\Updater.exe'
$VersionBypass = Join-Path $Root 'ConnectivityKit_updater_version_bypass_runtime\Updater.exe'
$Combined = Join-Path $Root 'ConnectivityKit_updater_prime_names_version_bypass_runtime\Updater.exe'
$Failures = [System.Collections.Generic.List[string]]::new()

function Ok([string]$Message) {
    Write-Host "OK   $Message" -ForegroundColor Green
}

function Fail([string]$Message) {
    $Failures.Add($Message) | Out-Null
    Write-Host "FAIL $Message" -ForegroundColor Red
}

function Read-Bytes([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        Fail "missing file: $Path"
        return $null
    }
    return [System.IO.File]::ReadAllBytes($Path)
}

function Check-PatchSet {
    param(
        [string]$Label,
        [string]$Path,
        [hashtable]$Expected
    )

    $orig = Read-Bytes $Original
    $patched = Read-Bytes $Path
    if ($null -eq $orig -or $null -eq $patched) {
        return
    }
    if ($orig.Length -ne $patched.Length) {
        Fail "$Label size changed: $($orig.Length) -> $($patched.Length)"
        return
    }
    if ($patched[0] -ne 0x4d -or $patched[1] -ne 0x5a) {
        Fail "$Label no longer has MZ magic"
        return
    }

    $diffs = @()
    for ($i = 0; $i -lt $orig.Length; $i++) {
        if ($orig[$i] -ne $patched[$i]) {
            $diffs += $i
        }
    }

    $expectedOffsets = @($Expected.Keys | ForEach-Object { [int]$_ } | Sort-Object)
    $actualOffsets = @($diffs | Sort-Object)
    if (($actualOffsets -join ',') -ne ($expectedOffsets -join ',')) {
        Fail "$Label diff offsets mismatch: expected $($expectedOffsets | ForEach-Object { '0x{0:x}' -f $_ } | Join-String -Separator ', '), got $($actualOffsets | ForEach-Object { '0x{0:x}' -f $_ } | Join-String -Separator ', ')"
        return
    }

    foreach ($off in $expectedOffsets) {
        $want = [byte]$Expected[$off]
        if ($patched[$off] -eq $want) {
            Ok "$Label patch byte 0x$($off.ToString('x')) = 0x$($want.ToString('x2'))"
        } else {
            Fail "$Label byte 0x$($off.ToString('x')) expected 0x$($want.ToString('x2')), got 0x$($patched[$off].ToString('x2'))"
        }
    }
    Ok "$Label only expected bytes changed"
}

Check-PatchSet 'prime-name Updater' $PrimeNames @{
    0x5a13 = 0x39
    0x5a27 = 0x35
    0x5a3b = 0x31
}

Check-PatchSet 'version-bypass Updater' $VersionBypass @{
    0x5ce2 = 0xeb
}

Check-PatchSet 'combined Updater' $Combined @{
    0x5a13 = 0x39
    0x5a27 = 0x35
    0x5a3b = 0x31
    0x5ce2 = 0xeb
}

if ($Failures.Count -gt 0) {
    Write-Host ''
    Write-Host "Updater patch verification failed with $($Failures.Count) issue(s)." -ForegroundColor Red
    exit 1
}

Write-Host ''
Write-Host 'Updater patch verification passed.' -ForegroundColor Green

