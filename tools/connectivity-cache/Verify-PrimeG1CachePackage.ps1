param(
  [string] $CachePath = (Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'HP Connectivity Kit\固件\PrimeG1'),

  [string] $ExpectedPrimeAppMd5 = ''
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

if (-not (Test-Path -LiteralPath $CachePath -PathType Container)) {
  throw "Cache directory does not exist: $CachePath"
}

$required = @('PRIME_APP.DAT', 'PRIME_MASTER.DAT', 'PRIME_OS.ROM', 'Prime_FW.md5')
foreach ($name in $required) {
  Require-File (Join-Path $CachePath $name)
}

$primeApp = Join-Path $CachePath 'PRIME_APP.DAT'
$primeFw = Join-Path $CachePath 'Prime_FW.md5'
$actualPrimeAppMd5 = Get-Md5 $primeApp

if ($ExpectedPrimeAppMd5 -and ($actualPrimeAppMd5.ToLowerInvariant() -ne $ExpectedPrimeAppMd5.ToLowerInvariant())) {
  throw "PRIME_APP.DAT MD5 mismatch. Expected $ExpectedPrimeAppMd5, got $actualPrimeAppMd5"
}

$md5Text = Get-Content -LiteralPath $primeFw -Raw -Encoding ascii
if ($md5Text -notmatch '(?im)^([0-9a-f]{32})\s+\*?PRIME_APP\.DAT\s*$') {
  throw "Prime_FW.md5 does not contain a PRIME_APP.DAT line"
}

$listedPrimeAppMd5 = $Matches[1].ToLowerInvariant()
if ($listedPrimeAppMd5 -ne $actualPrimeAppMd5.ToLowerInvariant()) {
  throw "Prime_FW.md5 PRIME_APP.DAT entry mismatch. Listed $listedPrimeAppMd5, actual $actualPrimeAppMd5"
}

Write-Host "Connectivity Kit cache package is internally consistent."
Write-Host "Cache: $CachePath"
Write-Host "PRIME_APP.DAT MD5: $actualPrimeAppMd5"

