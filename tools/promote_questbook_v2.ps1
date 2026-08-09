param(
    [string]$Root = (Split-Path -Parent $PSScriptRoot),
    [string]$Build = 'build/questbook_v2',
    [switch]$CheckOnly
)

$ErrorActionPreference = 'Stop'

function Resolve-UnderRoot([string]$Base, [string]$Path, [switch]$MustExist) {
    $baseFull = [System.IO.Path]::GetFullPath($Base).TrimEnd([System.IO.Path]::DirectorySeparatorChar)
    $candidate = if ([System.IO.Path]::IsPathRooted($Path)) {
        [System.IO.Path]::GetFullPath($Path)
    }
    else {
        [System.IO.Path]::GetFullPath((Join-Path $baseFull $Path))
    }
    $prefix = $baseFull + [System.IO.Path]::DirectorySeparatorChar
    if (-not $candidate.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Path escapes workspace root: $Path"
    }
    if ($MustExist -and -not (Test-Path -LiteralPath $candidate)) {
        throw "Required path does not exist: $candidate"
    }
    return $candidate
}

function Assert-ManifestFile([string]$BuildRoot, [string]$RelativePath, [string]$ExpectedHash) {
    $path = Join-Path $BuildRoot ($RelativePath -replace '/', [System.IO.Path]::DirectorySeparatorChar)
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Manifest file is missing: $RelativePath"
    }
    $actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash.ToLowerInvariant()
    if ($actual -ne $ExpectedHash.ToLowerInvariant()) {
        throw "Manifest hash mismatch for ${RelativePath}: expected $ExpectedHash, got $actual"
    }
}

$rootFull = [System.IO.Path]::GetFullPath($Root)
$buildFull = Resolve-UnderRoot $rootFull $Build -MustExist
$runtimeFull = Resolve-UnderRoot $rootFull 'config/ftbquests/quests' -MustExist
$runtimeChapters = Resolve-UnderRoot $rootFull 'config/ftbquests/quests/chapters' -MustExist
$runtimeGroups = Resolve-UnderRoot $rootFull 'config/ftbquests/quests/chapter_groups.snbt' -MustExist
$runtimeData = Resolve-UnderRoot $rootFull 'config/ftbquests/quests/data.snbt' -MustExist

$manifestPath = Join-Path $buildFull 'manifest.json'
$manifest = Get-Content -Raw -Encoding UTF8 -LiteralPath $manifestPath | ConvertFrom-Json
if ([int]$manifest.schema_version -ne 2 -or [string]$manifest.status -ne 'STAGED') {
    throw 'Questbook build manifest is not a staged schema-v2 build.'
}
if ([string]$manifest.text_mode -ne 'ru-inline') {
    throw 'Questbook promotion requires the natural-Russian inline build.'
}

$runtimeFiles = @($manifest.files.PSObject.Properties | Where-Object {
    $_.Name -eq 'chapter_groups.snbt' -or $_.Name.StartsWith('chapters/')
})
foreach ($entry in $runtimeFiles) {
    Assert-ManifestFile $buildFull ([string]$entry.Name) ([string]$entry.Value)
}
$expectedChapters = @($runtimeFiles | Where-Object { $_.Name.StartsWith('chapters/') }).Count
if ($expectedChapters -lt 1) { throw 'Staged build contains no quest chapters.' }
if ($CheckOnly) {
    Write-Host "[QUEST-PROMOTE][PASS] staged manifest and $expectedChapters chapter hashes are valid."
    Write-Host '[QUEST-PROMOTE][PASS] check-only mode; runtime was not modified and Minecraft was not launched.'
    return
}

$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$stageRoot = Resolve-UnderRoot $rootFull ("tmp/questbook_v2_promote_${stamp}_$PID")
$stageChapters = Join-Path $stageRoot 'chapters'
$stageGroups = Join-Path $stageRoot 'chapter_groups.snbt'
$backupRoot = Resolve-UnderRoot $rootFull "backups/questbook_runtime_before_v2_$stamp"
$backupChapters = Join-Path $backupRoot 'chapters'
$backupGroups = Join-Path $backupRoot 'chapter_groups.snbt'
$backupData = Join-Path $backupRoot 'data.snbt'

New-Item -ItemType Directory -Path $stageChapters -Force | Out-Null
$buildChapters = Join-Path $buildFull 'chapters'
foreach ($chapter in @(Get-ChildItem -LiteralPath $buildChapters -Filter '*.snbt' -File)) {
    Copy-Item -LiteralPath $chapter.FullName -Destination $stageChapters -ErrorAction Stop
}
Copy-Item -LiteralPath (Join-Path $buildFull 'chapter_groups.snbt') -Destination $stageGroups -ErrorAction Stop

$stagedCount = @(Get-ChildItem -LiteralPath $stageChapters -Filter '*.snbt' -File).Count
if ($stagedCount -ne $expectedChapters) {
    throw "Staging chapter count mismatch: expected $expectedChapters, got $stagedCount"
}

New-Item -ItemType Directory -Path $backupRoot | Out-Null
Copy-Item -LiteralPath $runtimeGroups -Destination $backupGroups
Copy-Item -LiteralPath $runtimeData -Destination $backupData
$oldChapterCount = @(Get-ChildItem -LiteralPath $runtimeChapters -Filter '*.snbt' -File).Count

$promoted = $false
try {
    Move-Item -LiteralPath $runtimeChapters -Destination $backupChapters
    Move-Item -LiteralPath $stageChapters -Destination $runtimeChapters
    Copy-Item -LiteralPath $stageGroups -Destination $runtimeGroups -Force

    $runtimeCount = @(Get-ChildItem -LiteralPath $runtimeChapters -Filter '*.snbt' -File).Count
    if ($runtimeCount -ne $expectedChapters) {
        throw "Runtime chapter count mismatch after promotion: expected $expectedChapters, got $runtimeCount"
    }
    foreach ($entry in $runtimeFiles) {
        $runtimePath = if ($entry.Name -eq 'chapter_groups.snbt') {
            $runtimeGroups
        }
        else {
            Join-Path $runtimeFull ($entry.Name -replace '/', [System.IO.Path]::DirectorySeparatorChar)
        }
        $actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $runtimePath).Hash.ToLowerInvariant()
        if ($actual -ne ([string]$entry.Value).ToLowerInvariant()) {
            throw "Runtime hash mismatch after promotion: $($entry.Name)"
        }
    }
    $promoted = $true
}
finally {
    if (-not $promoted) {
        $failedRuntime = Join-Path $stageRoot 'failed_runtime_chapters'
        if (Test-Path -LiteralPath $runtimeChapters) {
            Move-Item -LiteralPath $runtimeChapters -Destination $failedRuntime -Force
        }
        if (Test-Path -LiteralPath $backupChapters) {
            Move-Item -LiteralPath $backupChapters -Destination $runtimeChapters
        }
        if (Test-Path -LiteralPath $backupGroups) {
            Copy-Item -LiteralPath $backupGroups -Destination $runtimeGroups -Force
        }
    }
}

if ($promoted -and (Test-Path -LiteralPath $stageRoot)) {
    Remove-Item -LiteralPath $stageRoot -Recurse -Force
}

Write-Host "[QUEST-PROMOTE][PASS] old_chapters=$oldChapterCount new_chapters=$expectedChapters"
Write-Host "[QUEST-PROMOTE][PASS] backup=$backupRoot"
Write-Host '[QUEST-PROMOTE][PASS] data.snbt preserved; Minecraft was not launched.'
