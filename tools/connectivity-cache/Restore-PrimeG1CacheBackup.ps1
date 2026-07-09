param(
  [Parameter(Mandatory = $true)]
  [string] $BackupPath,

  [string] $CachePath = (Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'HP Connectivity Kit\固件\PrimeG1')
)

$ErrorActionPreference = 'Stop'
$OutputEncoding = [Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)

$backup = (Resolve-Path -LiteralPath $BackupPath).Path
if (-not (Test-Path -LiteralPath $backup -PathType Container)) {
  throw "Backup directory does not exist: $backup"
}

$cacheParent = Split-Path -Parent $CachePath
if (-not (Test-Path -LiteralPath $cacheParent -PathType Container)) {
  New-Item -ItemType Directory -Force -Path $cacheParent | Out-Null
}

if (Test-Path -LiteralPath $CachePath -PathType Container) {
  $resolvedCache = (Resolve-Path -LiteralPath $CachePath).Path
  $resolvedParent = (Resolve-Path -LiteralPath $cacheParent).Path
  if (-not $resolvedCache.StartsWith($resolvedParent, [StringComparison]::OrdinalIgnoreCase)) {
    throw "Refusing to replace cache outside parent directory: $resolvedCache"
  }
  Remove-Item -LiteralPath $CachePath -Recurse -Force
}

Copy-Item -LiteralPath $backup -Destination $CachePath -Recurse -Force
Write-Host "Restored Connectivity Kit cache from:"
Write-Host "  $backup"
Write-Host "to:"
Write-Host "  $CachePath"

