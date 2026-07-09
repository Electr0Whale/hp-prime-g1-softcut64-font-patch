param(
  [Parameter(Mandatory = $true)]
  [string] $PackagePath,

  [string] $CachePath = (Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'HP Connectivity Kit\固件\PrimeG1'),

  [string] $BackupRoot = (Join-Path (Get-Location) 'cache_backups'),

  [switch] $NoBackup
)

$ErrorActionPreference = 'Stop'
$OutputEncoding = [Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)

function Get-Md5([string] $Path) {
  $hash = [Security.Cryptography.MD5]::Create()
  try {
    $stream = [IO.File]::OpenRead($Path)
    try {
      return (($hash.ComputeHash($stream) | ForEach-Object { $_.ToString('x2') }) -join '')
    } finally {
      $stream.Dispose()
    }
  } finally {
    $hash.Dispose()
  }
}

function Require-File([string] $Path) {
  if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
    throw "Missing required file: $Path"
  }
}

$pkg = (Resolve-Path -LiteralPath $PackagePath).Path
$cacheParent = Split-Path -Parent $CachePath
if (-not (Test-Path -LiteralPath $cacheParent -PathType Container)) {
  New-Item -ItemType Directory -Force -Path $cacheParent | Out-Null
}

foreach ($name in @('PRIME_APP.DAT', 'PRIME_MASTER.DAT', 'PRIME_OS.ROM', 'Prime_FW.md5')) {
  Require-File (Join-Path $pkg $name)
}

$backupPath = $null
if ((Test-Path -LiteralPath $CachePath -PathType Container) -and -not $NoBackup) {
  New-Item -ItemType Directory -Force -Path $BackupRoot | Out-Null
  $stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
  $backupPath = Join-Path $BackupRoot "PrimeG1_before_patch_$stamp"
  Copy-Item -LiteralPath $CachePath -Destination $backupPath -Recurse -Force
}

New-Item -ItemType Directory -Force -Path $CachePath | Out-Null
Copy-Item -LiteralPath (Join-Path $pkg '*') -Destination $CachePath -Recurse -Force

$manifest = [ordered]@{
  package_path = $pkg
  cache_path = (Resolve-Path -LiteralPath $CachePath).Path
  backup_path = $backupPath
  installed_at = (Get-Date).ToString('o')
  files = @()
}

foreach ($file in Get-ChildItem -LiteralPath $CachePath -File | Sort-Object Name) {
  $manifest.files += [ordered]@{
    name = $file.Name
    length = $file.Length
    md5 = Get-Md5 $file.FullName
  }
}

$manifestPath = Join-Path $CachePath 'softcut_cache_install_manifest.json'
$manifest | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $manifestPath -Encoding utf8

Write-Host "Installed package into Connectivity Kit cache:"
Write-Host "  $CachePath"
if ($backupPath) {
  Write-Host "Backup:"
  Write-Host "  $backupPath"
}
Write-Host "Manifest:"
Write-Host "  $manifestPath"

