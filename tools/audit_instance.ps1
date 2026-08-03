[CmdletBinding()]
param(
    [string]$Root = '',
    [string]$BuildId = 'IF-M2-0001',
    [string]$OutputDirectory = ''
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem

if ([string]::IsNullOrWhiteSpace($Root)) {
    $scriptDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
    $Root = (Resolve-Path (Join-Path $scriptDirectory '..')).Path
}

if ([string]::IsNullOrWhiteSpace($OutputDirectory)) {
    $OutputDirectory = Join-Path $Root "docs\registries\generated\$BuildId"
}

$rootPath = (Resolve-Path -LiteralPath $Root).Path
$modsPath = (Resolve-Path -LiteralPath (Join-Path $rootPath 'mods')).Path
if (-not $modsPath.StartsWith($rootPath, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw 'Resolved mods path escaped the instance root.'
}
New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null

function Get-ZipEntryText {
    param(
        [System.IO.Compression.ZipArchive]$Archive,
        [string]$Name
    )
    $entry = $Archive.GetEntry($Name)
    if ($null -eq $entry) { return $null }
    $reader = [System.IO.StreamReader]::new($entry.Open(), [System.Text.Encoding]::UTF8, $true)
    try { return $reader.ReadToEnd() } finally { $reader.Dispose() }
}

function Get-TomlString {
    param([string]$Block, [string]$Name)
    $escaped = [regex]::Escape($Name)
    $doublePattern = '(?m)^\s*{0}\s*=\s*"([^"]*)"' -f $escaped
    $double = [regex]::Match($Block, $doublePattern)
    if ($double.Success) { return $double.Groups[1].Value }
    $single = [regex]::Match($Block, "(?m)^\s*$escaped\s*=\s*'([^']*)'")
    if ($single.Success) { return $single.Groups[1].Value }
    return $null
}

function Get-TomlBoolean {
    param([string]$Block, [string]$Name, [bool]$Default = $false)
    $escaped = [regex]::Escape($Name)
    $match = [regex]::Match($Block, "(?mi)^\s*$escaped\s*=\s*(true|false)\s*$")
    if (-not $match.Success) { return $Default }
    return $match.Groups[1].Value -ieq 'true'
}

function Get-ManifestVersion {
    param([System.IO.Compression.ZipArchive]$Archive)
    $manifest = Get-ZipEntryText -Archive $Archive -Name 'META-INF/MANIFEST.MF'
    if ($null -eq $manifest) { return $null }
    foreach ($name in @('Implementation-Version', 'Specification-Version')) {
        $pattern = '(?mi)^{0}:\s*(.+?)\s*$' -f [regex]::Escape($name)
        $match = [regex]::Match($manifest, $pattern)
        if ($match.Success) { return $match.Groups[1].Value.Trim() }
    }
    return $null
}

function Get-ModMetadataFromArchive {
    param(
        [System.IO.Compression.ZipArchive]$Archive,
        [string]$Origin,
        [int]$Depth = 0
    )

    $provided = [System.Collections.Generic.List[object]]::new()
    $dependencies = [System.Collections.Generic.List[object]]::new()
    $errors = [System.Collections.Generic.List[string]]::new()
    $manifestVersion = Get-ManifestVersion -Archive $Archive
    $toml = Get-ZipEntryText -Archive $Archive -Name 'META-INF/mods.toml'

    if ($null -ne $toml) {
        $modBlocks = [regex]::Matches($toml, '(?ms)^\s*\[\[mods\]\]\s*(.*?)(?=^\s*\[\[|\z)')
        foreach ($match in $modBlocks) {
            $block = $match.Groups[1].Value
            $modId = Get-TomlString -Block $block -Name 'modId'
            $version = Get-TomlString -Block $block -Name 'version'
            if ($null -ne $version -and $version -match '^\$\{.+\}$' -and $null -ne $manifestVersion) {
                $version = $manifestVersion
            }
            if (-not [string]::IsNullOrWhiteSpace($modId)) {
                $provided.Add([pscustomobject]@{
                    mod_id = $modId
                    version = if ($null -eq $version) { 'UNKNOWN' } else { $version }
                    origin = $Origin
                    embedded = ($Depth -gt 0)
                })
            }
        }

        $dependencyBlocks = [regex]::Matches($toml, '(?ms)^\s*\[\[dependencies\.(?:\"?)([A-Za-z0-9_.-]+)(?:\"?)\]\]\s*(.*?)(?=^\s*\[\[|\z)')
        foreach ($match in $dependencyBlocks) {
            $owner = $match.Groups[1].Value
            $block = $match.Groups[2].Value
            $dependencyId = Get-TomlString -Block $block -Name 'modId'
            if ([string]::IsNullOrWhiteSpace($dependencyId)) { continue }
            $dependencies.Add([pscustomobject]@{
                owner_mod_id = $owner
                dependency_mod_id = $dependencyId
                mandatory = Get-TomlBoolean -Block $block -Name 'mandatory' -Default $false
                version_range = Get-TomlString -Block $block -Name 'versionRange'
                ordering = Get-TomlString -Block $block -Name 'ordering'
                side = Get-TomlString -Block $block -Name 'side'
                origin = $Origin
                embedded_owner = ($Depth -gt 0)
            })
        }
    }
    elseif ($Depth -eq 0) {
        $errors.Add("$Origin has no META-INF/mods.toml")
    }

    if ($Depth -lt 2) {
        foreach ($entry in $Archive.Entries | Where-Object { $_.FullName -like 'META-INF/jarjar/*.jar' }) {
            $memory = [System.IO.MemoryStream]::new()
            $stream = $entry.Open()
            try { $stream.CopyTo($memory) } finally { $stream.Dispose() }
            $memory.Position = 0
            try {
                $nested = [System.IO.Compression.ZipArchive]::new($memory, [System.IO.Compression.ZipArchiveMode]::Read, $false)
                try {
                    $nestedResult = Get-ModMetadataFromArchive -Archive $nested -Origin "$Origin!/$($entry.FullName)" -Depth ($Depth + 1)
                    foreach ($item in $nestedResult.provided) { $provided.Add($item) }
                    foreach ($item in $nestedResult.dependencies) { $dependencies.Add($item) }
                    foreach ($item in $nestedResult.errors) { $errors.Add($item) }
                }
                finally { $nested.Dispose() }
            }
            catch {
                $errors.Add("Failed to inspect embedded JAR $Origin!/$($entry.FullName): $($_.Exception.Message)")
            }
            finally { $memory.Dispose() }
        }
    }

    return [pscustomobject]@{
        provided = @($provided)
        dependencies = @($dependencies)
        errors = @($errors)
    }
}

function Get-VersionTokens {
    param([string]$Version)
    if ([string]::IsNullOrWhiteSpace($Version)) { return @() }
    return @([regex]::Matches($Version.Trim(), '[0-9]+|[A-Za-z]+') | ForEach-Object { $_.Value })
}

function Compare-LooseVersion {
    param([string]$Left, [string]$Right)
    $a = @(Get-VersionTokens $Left)
    $b = @(Get-VersionTokens $Right)
    $count = [Math]::Max($a.Count, $b.Count)
    for ($index = 0; $index -lt $count; $index++) {
        $av = if ($index -lt $a.Count) { $a[$index] } else { '0' }
        $bv = if ($index -lt $b.Count) { $b[$index] } else { '0' }
        $an = 0L
        $bn = 0L
        $aIsNumber = [long]::TryParse($av, [ref]$an)
        $bIsNumber = [long]::TryParse($bv, [ref]$bn)
        if ($aIsNumber -and $bIsNumber) {
            if ($an -lt $bn) { return -1 }
            if ($an -gt $bn) { return 1 }
        }
        else {
            $comparison = [string]::Compare($av, $bv, [System.StringComparison]::OrdinalIgnoreCase)
            if ($comparison -lt 0) { return -1 }
            if ($comparison -gt 0) { return 1 }
        }
    }
    return 0
}

function Test-VersionRange {
    param([string]$Version, [string]$Range)
    if ([string]::IsNullOrWhiteSpace($Range) -or $Range -eq '*') {
        return [pscustomobject]@{ status = 'SATISFIED'; reason = 'unbounded' }
    }
    if ([string]::IsNullOrWhiteSpace($Version) -or $Version -eq 'UNKNOWN' -or $Range -match '\$\{') {
        return [pscustomobject]@{ status = 'UNVERIFIED'; reason = 'unresolved version property' }
    }
    $exact = [regex]::Match($Range, '^\s*\[\s*([^,\]]+)\s*\]\s*$')
    if ($exact.Success) {
        $ok = (Compare-LooseVersion $Version $exact.Groups[1].Value) -eq 0
        return [pscustomobject]@{ status = if ($ok) { 'SATISFIED' } else { 'MISMATCH' }; reason = "exact $($exact.Groups[1].Value)" }
    }
    # Forge builds every versionRange with Maven VersionRange.createFromVersionSpec.
    # A spec that carries no interval brackets leaves the restriction list empty,
    # Maven fills it with Restriction.EVERYTHING, and containsVersion then accepts
    # any installed version. Such a spec is a recommendation, never a hard gate, so
    # treating it as an exact match invented four failures that Forge cannot raise.
    if ($Range -notmatch '[\[\]\(\)]') {
        $comparators = @([regex]::Matches($Range, '(>=|<=|>|<|=)\s*([0-9][^\s,]*)'))
        if ($comparators.Count -gt 0) {
            # Comparator syntax (">=6.0.4", ">=1.1.20 <1.2.0") is not Maven and Forge
            # never enforces it, but it still states what the author built against,
            # so it is evaluated as a conjunction and reported as advice.
            $ok = $true
            foreach ($comparator in $comparators) {
                $comparison = Compare-LooseVersion $Version $comparator.Groups[2].Value
                switch ($comparator.Groups[1].Value) {
                    '>=' { if ($comparison -lt 0) { $ok = $false } }
                    '>' { if ($comparison -le 0) { $ok = $false } }
                    '<=' { if ($comparison -gt 0) { $ok = $false } }
                    '<' { if ($comparison -ge 0) { $ok = $false } }
                    '=' { if ($comparison -ne 0) { $ok = $false } }
                }
            }
            if ($ok) {
                return [pscustomobject]@{ status = 'SATISFIED'; reason = "comparator range $($Range.Trim())" }
            }
            return [pscustomobject]@{ status = 'ADVISORY'; reason = "comparator range $($Range.Trim()) not met by $Version; Forge does not enforce a non-Maven spec" }
        }
        $ok = (Compare-LooseVersion $Version $Range.Trim()) -eq 0
        if ($ok) {
            return [pscustomobject]@{ status = 'SATISFIED'; reason = "recommended $($Range.Trim())" }
        }
        return [pscustomobject]@{ status = 'ADVISORY'; reason = "recommended $($Range.Trim()), installed $Version; Maven soft requirement, Forge accepts it" }
    }
    $interval = [regex]::Match($Range, '^\s*([\[\(])\s*([^,]*)\s*,\s*([^\]\)]*)\s*([\]\)])\s*$')
    if (-not $interval.Success) {
        return [pscustomobject]@{ status = 'UNVERIFIED'; reason = 'unsupported compound range' }
    }
    $lowerInclusive = $interval.Groups[1].Value -eq '['
    $upperInclusive = $interval.Groups[4].Value -eq ']'
    $lower = $interval.Groups[2].Value.Trim()
    $upper = $interval.Groups[3].Value.Trim()
    $ok = $true
    if ($lower.Length -gt 0) {
        $comparison = Compare-LooseVersion $Version $lower
        if ($comparison -lt 0 -or ($comparison -eq 0 -and -not $lowerInclusive)) { $ok = $false }
    }
    if ($upper.Length -gt 0) {
        $comparison = Compare-LooseVersion $Version $upper
        if ($comparison -gt 0 -or ($comparison -eq 0 -and -not $upperInclusive)) { $ok = $false }
    }
    return [pscustomobject]@{ status = if ($ok) { 'SATISFIED' } else { 'MISMATCH' }; reason = 'interval' }
}

function Get-JsonKeysFromText {
    param([string]$Text)
    try {
        $object = $Text | ConvertFrom-Json
        return @($object.PSObject.Properties.Name)
    }
    catch {
        return $null
    }
}

function Get-JsonObjectFromText {
    param([string]$Text)
    try { return $Text | ConvertFrom-Json }
    catch { return $null }
}

function Get-FormatTokenSignature {
    param([string]$Text)
    if ($null -eq $Text) { return '' }
    $pattern = '%(?:\d+\$)?[-#+0,(<]*(?:\d+)?(?:\.\d+)?(?:[tT][a-zA-Z]|[bBhHsScCdoxXeEfgGaAn%])'
    $tokens = @([regex]::Matches($Text, $pattern) | ForEach-Object { $_.Value } | Sort-Object)
    return ($tokens -join '|')
}

function Get-RegexGroupSignature {
    param(
        [string]$Text,
        [string]$Pattern,
        [int]$Group = 1
    )
    if ($null -eq $Text) { return '' }
    $values = @([regex]::Matches($Text, $Pattern, [System.Text.RegularExpressions.RegexOptions]::Multiline) | ForEach-Object {
        $_.Groups[$Group].Value
    } | Sort-Object)
    return ($values -join "`n")
}

function Get-GuideTagSignature {
    param([string]$Text)
    if ($null -eq $Text) { return '' }
    $values = @([regex]::Matches($Text, '<\s*(/?)\s*([A-Za-z][A-Za-z0-9]*)\b') | Where-Object {
        $_.Groups[2].Value -ine 'a'
    } | ForEach-Object {
        $prefix = if ($_.Groups[1].Value -eq '/') { '/' } else { '' }
        $prefix + $_.Groups[2].Value.ToLowerInvariant()
    } | Sort-Object)
    return ($values -join "`n")
}

function Get-GuideAttributeSignature {
    param([string]$Text)
    if ($null -eq $Text) { return '' }
    $values = [System.Collections.Generic.List[string]]::new()
    foreach ($tag in [regex]::Matches($Text, '<\s*([A-Za-z][A-Za-z0-9]*)\b([^>]*)>')) {
        $tagName = $tag.Groups[1].Value.ToLowerInvariant()
        if ($tagName -eq 'a') { continue }
        foreach ($attribute in [regex]::Matches($tag.Groups[2].Value, '\b([A-Za-z_:][A-Za-z0-9_:.-]*)\s*=\s*("[^"]*"|''[^'']*''|\{[^}]*\})')) {
            $attributeName = $attribute.Groups[1].Value.ToLowerInvariant()
            $attributeValue = $attribute.Groups[2].Value
            $values.Add("$tagName|$attributeName=$attributeValue")
        }
    }
    return (@($values | Sort-Object) -join "`n")
}

function Get-NumericProseSignature {
    param([string]$Text)
    if ($null -eq $Text) { return '' }
    # Ordered-list markers and small cardinal numbers are routinely written
    # differently in natural Russian ("4" -> "четыре"). Keep the gate on
    # values where a silent translation error is both likely and material:
    # 10+, versions/decimals, percentages, K-sized capacities and dimensions.
    $withoutListMarkers = [regex]::Replace($Text, '(?m)^\s*\d+[.)]\s+', ' ')
    $withoutTags = [regex]::Replace($withoutListMarkers, '<[^>]+>', ' ')
    $withoutThousandsSpaces = [regex]::Replace($withoutTags, '(?<=\d)[\u00A0 ](?=\d{3}\b)', '')
    # Keep the executable syntax ASCII-only: Windows PowerShell 5.1 reads a
    # BOM-less UTF-8 script as the active ANSI codepage. Unicode characters
    # in regex literals would otherwise silently turn into mojibake.
    $values = @([regex]::Matches($withoutThousandsSpaces, '(?<![A-Za-z0-9_])\d+(?:[.,]\d+)*(?:\s*[\u00D7x*]\s*\d+(?:[.,]\d+)*)*[Kk\u041A\u043A]?\s*%?') | ForEach-Object {
        $value = $_.Value -replace '\s+', ''
        if ($value -match '^\d{1,3}(?:,\d{3})+(?:%?)$') { $value = $value -replace ',', '' }
        $value = $value -replace ',', '.' -replace '[\u041A\u043Ak]', 'K' -replace '[x*]', ([char]0x00D7)
        if ($value -match '^(\d+)K$') { $value = ([int64]$matches[1] * 1000).ToString() }
        $leadingInteger = [int64]([regex]::Match($value, '^\d+').Value)
        if ($leadingInteger -ge 10 -or $value -match '[.%K\u00D7]') { $value }
    } | Sort-Object -Unique)
    return ($values -join "`n")
}

function Test-ContainsUntranslatedSourceLine {
    param(
        [string]$SourceText,
        [string]$RussianText
    )
    if ([string]::IsNullOrWhiteSpace($SourceText) -or [string]::IsNullOrWhiteSpace($RussianText)) { return $false }

    $russianLines = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::Ordinal)
    foreach ($line in ($RussianText -split "`r?`n")) { [void]$russianLines.Add($line.Trim()) }

    foreach ($line in ($SourceText -split "`r?`n")) {
        $candidate = $line.Trim()
        if ($candidate.Length -lt 40) { continue }
        if ($candidate -match '^\s*(?:<|---|```|[A-Za-z][A-Za-z0-9_-]*\s*:)') { continue }
        if ($candidate -match '\p{IsCyrillic}') { continue }
        if ([regex]::Matches($candidate, '\b[A-Za-z]{3,}\b').Count -lt 5) { continue }
        if ($russianLines.Contains($candidate)) { return $true }
    }
    return $false
}

$instancePath = Join-Path $rootPath 'minecraftinstance.json'
$instance = Get-Content -Raw -Encoding UTF8 -LiteralPath $instancePath | ConvertFrom-Json
$appSources = @{}
foreach ($addon in @($instance.installedAddons)) {
    $fileName = [string]$addon.installedFile.fileName
    if (-not [string]::IsNullOrWhiteSpace($fileName)) { $appSources[$fileName] = $addon }
}

$manualPath = Join-Path $rootPath 'docs\registries\curseforge_sources.json'
$manualRegistry = Get-Content -Raw -Encoding UTF8 -LiteralPath $manualPath | ConvertFrom-Json
$manualSources = @{}
foreach ($file in @($manualRegistry.files)) { $manualSources[[string]$file.file_name] = $file }
# owner_exceptions are files the owner deliberately took from outside CurseForge.
# Their origin is registered and hashed, so calling them UNKNOWN hid a real check:
# nothing compared the installed file against the hash written down for it.
$ownerExceptionSources = @{}
foreach ($file in @($manualRegistry.owner_exceptions)) { $ownerExceptionSources[[string]$file.file_name] = $file }

$jars = @(Get-ChildItem -LiteralPath $modsPath -File -Filter '*.jar' | Sort-Object Name)
$manifestEntries = [System.Collections.Generic.List[object]]::new()
$allProvided = [System.Collections.Generic.List[object]]::new()
$allDependencies = [System.Collections.Generic.List[object]]::new()
$metadataErrors = [System.Collections.Generic.List[string]]::new()
$languageSources = [System.Collections.Generic.List[object]]::new()
$guideDefaultPages = @{}
$guideRussianPages = [System.Collections.Generic.HashSet[string]]::new()
$guideRussianTexts = @{}
$bookDefaultPages = @{}
$bookRussianPages = [System.Collections.Generic.HashSet[string]]::new()
$bookRussianTexts = @{}
$hashMismatches = [System.Collections.Generic.List[string]]::new()
$invalidCurseForgeUrls = [System.Collections.Generic.List[string]]::new()

foreach ($jar in $jars) {
    $hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $jar.FullName).Hash
    $source = $null
    $expectedHash = $null
    $expectedHashAlgorithm = $null
    $actualExpectedAlgorithmHash = $null
    $hashMatches = $null
    if ($manualSources.ContainsKey($jar.Name)) {
        $manual = $manualSources[$jar.Name]
        if ($null -ne $manual.PSObject.Properties['sha256']) { $expectedHash = [string]$manual.sha256 }
        $expectedHashAlgorithm = 'SHA256'
        $actualExpectedAlgorithmHash = $hash
        $hashMatches = if ([string]::IsNullOrWhiteSpace($expectedHash)) { $null } else { $hash -ieq $expectedHash }
        $source = [pscustomobject]@{
            provenance = 'curseforge_exact_file_registry'
            project_id = [int64]$manual.project_id
            file_id = [int64]$manual.file_id
            download_url = [string]$manual.download_url
            expected_sha256 = $expectedHash
            expected_hash_algorithm = $expectedHashAlgorithm
            expected_hash = $expectedHash
            actual_hash = $actualExpectedAlgorithmHash
            hash_matches = $hashMatches
        }
    }
    elseif ($appSources.ContainsKey($jar.Name)) {
        $addon = $appSources[$jar.Name]
        $publishedHash = @($addon.installedFile.hashes | Where-Object { [int]$_.type -in @(1, 2) } | Sort-Object { if ([int]$_.type -eq 1) { 0 } else { 1 } } | Select-Object -First 1)
        if ($publishedHash.Count -gt 0) {
            $expectedHashAlgorithm = if ([int]$publishedHash[0].type -eq 1) { 'SHA1' } else { 'MD5' }
            $expectedHash = [string]$publishedHash[0].value
            $actualExpectedAlgorithmHash = (Get-FileHash -Algorithm $expectedHashAlgorithm -LiteralPath $jar.FullName).Hash
            $hashMatches = $actualExpectedAlgorithmHash -ieq $expectedHash
        }
        $source = [pscustomobject]@{
            provenance = 'curseforge_app_metadata'
            project_id = [int64]$addon.addonID
            file_id = [int64]$addon.installedFile.id
            download_url = [string]$addon.installedFile.downloadUrl
            expected_sha256 = $null
            expected_hash_algorithm = $expectedHashAlgorithm
            expected_hash = $expectedHash
            actual_hash = $actualExpectedAlgorithmHash
            hash_matches = $hashMatches
        }
    }
    elseif ($ownerExceptionSources.ContainsKey($jar.Name)) {
        $exception = $ownerExceptionSources[$jar.Name]
        if ($null -ne $exception.PSObject.Properties['sha256']) { $expectedHash = [string]$exception.sha256 }
        $expectedHashAlgorithm = 'SHA256'
        $actualExpectedAlgorithmHash = $hash
        $hashMatches = if ([string]::IsNullOrWhiteSpace($expectedHash)) { $null } else { $hash -ieq $expectedHash }
        $source = [pscustomobject]@{
            provenance = 'owner_registered_exception'
            project_id = $null
            file_id = $null
            download_url = $null
            expected_sha256 = $expectedHash
            expected_hash_algorithm = $expectedHashAlgorithm
            expected_hash = $expectedHash
            actual_hash = $actualExpectedAlgorithmHash
            hash_matches = $hashMatches
        }
    }
    else {
        $source = [pscustomobject]@{
            provenance = 'UNKNOWN'
            project_id = $null
            file_id = $null
            download_url = $null
            expected_sha256 = $null
            expected_hash_algorithm = $null
            expected_hash = $null
            actual_hash = $null
            hash_matches = $null
        }
    }
    if ($hashMatches -eq $false) {
        $hashMismatches.Add($jar.Name)
    }
    if ($source.provenance -notin @('UNKNOWN', 'owner_registered_exception') -and [string]$source.download_url -notmatch '^https://(?:edge|mediafiles?|mediafilez)\.forgecdn\.net/') {
        $invalidCurseForgeUrls.Add($jar.Name)
    }

    $archive = [System.IO.Compression.ZipFile]::OpenRead($jar.FullName)
    try {
        $metadata = Get-ModMetadataFromArchive -Archive $archive -Origin $jar.Name
        foreach ($item in $metadata.provided) { $allProvided.Add($item) }
        foreach ($item in $metadata.dependencies) { $allDependencies.Add($item) }
        foreach ($item in $metadata.errors) { $metadataErrors.Add($item) }

        foreach ($entry in $archive.Entries | Where-Object { $_.FullName -match '^assets/([^/]+)/lang/(en_us|ru_ru)\.json$' }) {
            $match = [regex]::Match($entry.FullName, '^assets/([^/]+)/lang/(en_us|ru_ru)\.json$')
            $languageSources.Add([pscustomobject]@{
                namespace = $match.Groups[1].Value
                locale = $match.Groups[2].Value
                jar = $jar.Name
                text = Get-ZipEntryText -Archive $archive -Name $entry.FullName
            })
        }

        foreach ($entry in $archive.Entries | Where-Object { $_.FullName -match '^assets/([^/]+)/([^/]*guide[^/]*)/(.+\.md)$' }) {
            $match = [regex]::Match($entry.FullName, '^assets/([^/]+)/([^/]*guide[^/]*)/(.+\.md)$')
            $namespace = $match.Groups[1].Value
            $guideRoot = $match.Groups[2].Value
            $relativePage = $match.Groups[3].Value
            $localized = [regex]::Match($relativePage, '^_([a-z]{2}_[a-z]{2})/(.+)$')
            if ($localized.Success) {
                if ($localized.Groups[1].Value -eq 'ru_ru') {
                    $localizedKey = "$namespace/$guideRoot/$($localized.Groups[2].Value)"
                    [void]$guideRussianPages.Add($localizedKey)
                    $guideRussianTexts[$localizedKey] = Get-ZipEntryText -Archive $archive -Name $entry.FullName
                }
                continue
            }
            $pageKey = "$namespace/$guideRoot/$relativePage"
            $guideDefaultPages[$pageKey] = [pscustomobject]@{
                namespace = $namespace
                guide_root = $guideRoot
                relative_page = $relativePage
                source_jar = $jar.Name
                source_text = Get-ZipEntryText -Archive $archive -Name $entry.FullName
            }
        }

        foreach ($entry in $archive.Entries | Where-Object { $_.FullName -match '^assets/([^/]+)/book/([^/]+)/(en_us|ru_ru)/(.+\.txt)$' }) {
            $match = [regex]::Match($entry.FullName, '^assets/([^/]+)/book/([^/]+)/(en_us|ru_ru)/(.+\.txt)$')
            $namespace = $match.Groups[1].Value
            $bookRoot = $match.Groups[2].Value
            $locale = $match.Groups[3].Value
            $relativePage = $match.Groups[4].Value
            $pageKey = "$namespace/$bookRoot/$relativePage"
            if ($locale -eq 'ru_ru') {
                [void]$bookRussianPages.Add($pageKey)
                $bookRussianTexts[$pageKey] = Get-ZipEntryText -Archive $archive -Name $entry.FullName
            }
            else {
                $bookDefaultPages[$pageKey] = [pscustomobject]@{
                    namespace = $namespace
                    book_root = $bookRoot
                    relative_page = $relativePage
                    source_jar = $jar.Name
                    source_text = Get-ZipEntryText -Archive $archive -Name $entry.FullName
                }
            }
        }
    }
    finally { $archive.Dispose() }

    $manifestEntries.Add([pscustomobject]@{
        file_name = $jar.Name
        size = $jar.Length
        sha256 = $hash
        curseforge = $source
    })
}

$providers = @{
    minecraft = [pscustomobject]@{ version = '1.20.1'; origin = 'platform' }
    forge = [pscustomobject]@{ version = '47.4.22'; origin = 'platform' }
}
foreach ($provided in $allProvided) {
    if (-not $providers.ContainsKey($provided.mod_id)) {
        $providers[$provided.mod_id] = [pscustomobject]@{ version = $provided.version; origin = $provided.origin }
    }
    elseif ((Compare-LooseVersion $provided.version $providers[$provided.mod_id].version) -gt 0) {
        $providers[$provided.mod_id] = [pscustomobject]@{ version = $provided.version; origin = $provided.origin }
    }
}

$dependencyChecks = [System.Collections.Generic.List[object]]::new()
foreach ($dependency in $allDependencies | Where-Object { $_.mandatory }) {
    if (-not $providers.ContainsKey($dependency.dependency_mod_id)) {
        $dependencyChecks.Add([pscustomobject]@{
            owner_mod_id = $dependency.owner_mod_id
            dependency_mod_id = $dependency.dependency_mod_id
            required_range = $dependency.version_range
            actual_version = $null
            status = 'MISSING'
            origin = $dependency.origin
            provider_origin = $null
            reason = 'no provider'
        })
        continue
    }
    $provider = $providers[$dependency.dependency_mod_id]
    $rangeResult = Test-VersionRange -Version $provider.version -Range $dependency.version_range
    $dependencyChecks.Add([pscustomobject]@{
        owner_mod_id = $dependency.owner_mod_id
        dependency_mod_id = $dependency.dependency_mod_id
        required_range = $dependency.version_range
        actual_version = $provider.version
        status = $rangeResult.status
        origin = $dependency.origin
        provider_origin = $provider.origin
        reason = $rangeResult.reason
    })
}

$overrideRussian = @{}
$overrideRoot = Join-Path $rootPath 'config\paxi\resourcepacks\IndustrialFrontier-Core\assets'
if (Test-Path -LiteralPath $overrideRoot) {
    foreach ($file in Get-ChildItem -LiteralPath $overrideRoot -Recurse -File -Filter 'en_us.json') {
        $relative = $file.FullName.Substring($overrideRoot.Length).TrimStart('\', '/')
        $namespace = ($relative -split '[\\/]')[0]
        $languageSources.Add([pscustomobject]@{
            namespace = $namespace
            locale = 'en_us'
            jar = "Paxi:$relative"
            text = Get-Content -Raw -Encoding UTF8 -LiteralPath $file.FullName
        })
    }
    foreach ($file in Get-ChildItem -LiteralPath $overrideRoot -Recurse -File -Filter 'ru_ru.json') {
        $relative = $file.FullName.Substring($overrideRoot.Length).TrimStart('\', '/')
        $namespace = ($relative -split '[\\/]')[0]
        $object = Get-JsonObjectFromText (Get-Content -Raw -Encoding UTF8 -LiteralPath $file.FullName)
        if ($null -ne $object) {
            if (-not $overrideRussian.ContainsKey($namespace)) { $overrideRussian[$namespace] = @{} }
            foreach ($property in $object.PSObject.Properties) {
                $overrideRussian[$namespace][$property.Name] = [string]$property.Value
            }
        }
    }
}

$formatExceptions = @{}
$seenFormatExceptions = [System.Collections.Generic.HashSet[string]]::new()
$formatExceptionPath = Join-Path $rootPath 'docs\registries\localization_format_exceptions.json'
if (Test-Path -LiteralPath $formatExceptionPath) {
    $formatExceptionRegistry = Get-Content -Raw -Encoding UTF8 -LiteralPath $formatExceptionPath | ConvertFrom-Json
    foreach ($exception in @($formatExceptionRegistry.exceptions)) {
        $exceptionId = "$([string]$exception.namespace)|$([string]$exception.key)"
        $formatExceptions[$exceptionId] = $exception
    }
}

$guideContentCorrections = @{}
$guideContentCorrectionsByPage = @{}
$seenGuideContentCorrections = [System.Collections.Generic.HashSet[string]]::new()
$guideContentCorrectionPath = Join-Path $rootPath 'docs\registries\guideme_content_corrections.json'
if (Test-Path -LiteralPath $guideContentCorrectionPath) {
    $guideContentCorrectionRegistry = Get-Content -Raw -Encoding UTF8 -LiteralPath $guideContentCorrectionPath | ConvertFrom-Json
    foreach ($correction in @($guideContentCorrectionRegistry.entries)) {
        $correctionId = [string]$correction.id
        $correctionPage = [string]$correction.page
        $guideContentCorrections[$correctionId] = $correction
        if (-not $guideContentCorrectionsByPage.ContainsKey($correctionPage)) {
            $guideContentCorrectionsByPage[$correctionPage] = [System.Collections.Generic.List[object]]::new()
        }
        $guideContentCorrectionsByPage[$correctionPage].Add($correction)
    }
}

$localizationRows = [System.Collections.Generic.List[object]]::new()
foreach ($group in $languageSources | Group-Object namespace) {
    $english = [System.Collections.Generic.HashSet[string]]::new()
    $russian = [System.Collections.Generic.HashSet[string]]::new()
    $englishValues = @{}
    $russianValues = @{}
    $parseErrors = [System.Collections.Generic.List[string]]::new()
    foreach ($source in $group.Group) {
        $object = Get-JsonObjectFromText $source.text
        if ($null -eq $object) {
            $parseErrors.Add("$($source.jar):$($source.locale)")
            continue
        }
        foreach ($property in $object.PSObject.Properties) {
            $key = $property.Name
            $value = [string]$property.Value
            if ($source.locale -eq 'en_us') {
                [void]$english.Add($key)
                $englishValues[$key] = $value
            }
            if ($source.locale -eq 'ru_ru') {
                [void]$russian.Add($key)
                $russianValues[$key] = $value
            }
        }
    }
    $overlayUnknown = @()
    if ($overrideRussian.ContainsKey($group.Name)) {
        foreach ($key in $overrideRussian[$group.Name].Keys) {
            [void]$russian.Add($key)
            $russianValues[$key] = $overrideRussian[$group.Name][$key]
            if (-not $english.Contains($key)) { $overlayUnknown += $key }
        }
    }
    $missing = @($english | Where-Object { -not $russian.Contains($_) } | Sort-Object)
    $empty = @($english | Where-Object {
        $russianValues.ContainsKey($_) -and
        -not [string]::IsNullOrWhiteSpace([string]$englishValues[$_]) -and
        [string]::IsNullOrWhiteSpace([string]$russianValues[$_])
    } | Sort-Object)
    $replacementCharacters = @($english | Where-Object { $russianValues.ContainsKey($_) -and ([string]$russianValues[$_]).Contains([char]0xFFFD) } | Sort-Object)
    $placeholderMismatches = [System.Collections.Generic.List[object]]::new()
    $allowedPlaceholderExceptions = [System.Collections.Generic.List[object]]::new()
    foreach ($key in $english) {
        if (-not $russianValues.ContainsKey($key)) { continue }
        $englishSignature = Get-FormatTokenSignature ([string]$englishValues[$key])
        $russianSignature = Get-FormatTokenSignature ([string]$russianValues[$key])
        if ($englishSignature -cne $russianSignature) {
            $mismatch = [pscustomobject]@{
                key = $key
                en_value = [string]$englishValues[$key]
                ru_value = [string]$russianValues[$key]
                en_tokens = $englishSignature
                ru_tokens = $russianSignature
            }
            $exceptionId = "$($group.Name)|$key"
            if (
                $formatExceptions.ContainsKey($exceptionId) -and
                [string]$formatExceptions[$exceptionId].en_tokens -ceq $englishSignature -and
                [string]$formatExceptions[$exceptionId].ru_tokens -ceq $russianSignature
            ) {
                [void]$seenFormatExceptions.Add($exceptionId)
                $allowedPlaceholderExceptions.Add([pscustomobject]@{
                    key = $key
                    en_tokens = $englishSignature
                    ru_tokens = $russianSignature
                    reason = [string]$formatExceptions[$exceptionId].reason
                })
            }
            else { $placeholderMismatches.Add($mismatch) }
        }
    }
    $coverage = if ($english.Count -eq 0) { 100.0 } else { [Math]::Round((($english.Count - $missing.Count) * 100.0) / $english.Count, 2) }
    $localizationRows.Add([pscustomobject]@{
        namespace = $group.Name
        en_us_keys = $english.Count
        ru_ru_keys_after_overlay = $russian.Count
        missing_ru_keys = $missing
        missing_count = $missing.Count
        coverage_percent = $coverage
        empty_ru_keys = $empty
        empty_count = $empty.Count
        replacement_character_keys = $replacementCharacters
        replacement_character_count = $replacementCharacters.Count
        placeholder_mismatches = @($placeholderMismatches)
        placeholder_mismatch_count = $placeholderMismatches.Count
        allowed_placeholder_exceptions = @($allowedPlaceholderExceptions)
        allowed_placeholder_exception_count = $allowedPlaceholderExceptions.Count
        overlay_unknown_keys = @($overlayUnknown | Sort-Object)
        overlay_unknown_count = $overlayUnknown.Count
        parse_errors = @($parseErrors)
    })
}

$unknownSources = @($manifestEntries | Where-Object { $_.curseforge.provenance -eq 'UNKNOWN' })
$ownerExceptionEntries = @($manifestEntries | Where-Object { $_.curseforge.provenance -eq 'owner_registered_exception' })
# A registered exception that no longer has an installed file is a stale rule, and a
# registered exception whose file changed is an unreviewed swap. Both are failures.
$staleOwnerExceptions = @($ownerExceptionSources.Keys | Where-Object { $_ -notin @($jars | ForEach-Object { $_.Name }) } | Sort-Object)
$hardDependencyFailures = @($dependencyChecks | Where-Object { $_.status -in @('MISSING', 'MISMATCH') })
$unverifiedDependencies = @($dependencyChecks | Where-Object { $_.status -eq 'UNVERIFIED' })
# An advisory is a declared expectation Forge will not act on. It stays visible so
# a genuinely wrong pairing cannot hide behind Maven soft-requirement semantics.
$advisoryDependencies = @($dependencyChecks | Where-Object { $_.status -eq 'ADVISORY' })
$missingTranslations = ($localizationRows | Measure-Object -Property missing_count -Sum).Sum
if ($null -eq $missingTranslations) { $missingTranslations = 0 }
$emptyTranslations = ($localizationRows | Measure-Object -Property empty_count -Sum).Sum
if ($null -eq $emptyTranslations) { $emptyTranslations = 0 }
$replacementCharacters = ($localizationRows | Measure-Object -Property replacement_character_count -Sum).Sum
if ($null -eq $replacementCharacters) { $replacementCharacters = 0 }
$placeholderMismatches = ($localizationRows | Measure-Object -Property placeholder_mismatch_count -Sum).Sum
if ($null -eq $placeholderMismatches) { $placeholderMismatches = 0 }
$unknownOverlayKeys = ($localizationRows | Measure-Object -Property overlay_unknown_count -Sum).Sum
if ($null -eq $unknownOverlayKeys) { $unknownOverlayKeys = 0 }
$allowedPlaceholderExceptions = ($localizationRows | Measure-Object -Property allowed_placeholder_exception_count -Sum).Sum
if ($null -eq $allowedPlaceholderExceptions) { $allowedPlaceholderExceptions = 0 }
$unusedFormatExceptions = @($formatExceptions.Keys | Where-Object { -not $seenFormatExceptions.Contains($_) } | Sort-Object)

$guideRows = [System.Collections.Generic.List[object]]::new()
foreach ($pageKey in @($guideDefaultPages.Keys | Sort-Object)) {
    $page = $guideDefaultPages[$pageKey]
    $overlayPath = Join-Path $overrideRoot "$($page.namespace)\$($page.guide_root)\_ru_ru\$($page.relative_page -replace '/', '\')"
    $translated = $guideRussianPages.Contains($pageKey) -or (Test-Path -LiteralPath $overlayPath -PathType Leaf)
    # Paxi resource-pack content overrides the copy bundled in a mod JAR.
    # Audit the effective text in the same order instead of letting a
    # pre-existing vendor translation hide an authored correction.
    $russianText = if (Test-Path -LiteralPath $overlayPath -PathType Leaf) {
        Get-Content -Raw -Encoding UTF8 -LiteralPath $overlayPath
    }
    elseif ($guideRussianTexts.ContainsKey($pageKey)) {
        [string]$guideRussianTexts[$pageKey]
    }
    else { $null }
    $qaIssues = [System.Collections.Generic.List[string]]::new()
    $sourceNumericSignature = $null
    $russianNumericSignature = $null
    if ($translated) {
        if ([string]::IsNullOrWhiteSpace($russianText)) { $qaIssues.Add('empty_translation') }
        if ($null -ne $russianText -and $russianText.Contains([char]0xFFFD)) { $qaIssues.Add('replacement_character') }
        if ((Get-GuideTagSignature $page.source_text) -cne (Get-GuideTagSignature $russianText)) { $qaIssues.Add('guide_tag_signature') }
        if ((Get-GuideAttributeSignature $page.source_text) -cne (Get-GuideAttributeSignature $russianText)) { $qaIssues.Add('guide_attribute_signature') }
        if ((Get-RegexGroupSignature $page.source_text '\b(?:src|id|href)\s*=\s*"([^"]+)"') -cne (Get-RegexGroupSignature $russianText '\b(?:src|id|href)\s*=\s*"([^"]+)"')) { $qaIssues.Add('resource_attribute_signature') }
        if ((Get-RegexGroupSignature $page.source_text '!?(?:\[[^\]]*\])\(([^)\s]+)(?:\s+"[^"]*")?\)') -cne (Get-RegexGroupSignature $russianText '!?(?:\[[^\]]*\])\(([^)\s]+)(?:\s+"[^"]*")?\)')) { $qaIssues.Add('markdown_link_signature') }
        if (([regex]::Matches($page.source_text, '(?m)^\s*```').Count) -ne ([regex]::Matches($russianText, '(?m)^\s*```').Count)) { $qaIssues.Add('code_fence_count') }
        if ((Get-RegexGroupSignature $page.source_text '^\s*position:\s*(.+)$') -cne (Get-RegexGroupSignature $russianText '^\s*position:\s*(.+)$')) { $qaIssues.Add('frontmatter_position') }
        $sourceNumericValues = @((Get-NumericProseSignature $page.source_text) -split "`n" | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
        $russianNumericSignature = Get-NumericProseSignature $russianText
        if ($guideContentCorrectionsByPage.ContainsKey([string]$page.relative_page)) {
            foreach ($correction in @($guideContentCorrectionsByPage[[string]$page.relative_page])) {
                $correctionId = [string]$correction.id
                $sourcePresent = $page.source_text.Contains([string]$correction.source_contains)
                $russianPresent = $russianText.Contains([string]$correction.ru_contains)
                if (-not $sourcePresent) { $qaIssues.Add("content_correction_source_drift:$correctionId") }
                if (-not $russianPresent) { $qaIssues.Add("content_correction_missing:$correctionId") }
                if ($sourcePresent -and $russianPresent) { [void]$seenGuideContentCorrections.Add($correctionId) }
                if ($null -ne $correction.numeric_source -and $null -ne $correction.numeric_ru) {
                    for ($index = 0; $index -lt $sourceNumericValues.Count; $index++) {
                        if ($sourceNumericValues[$index] -ceq [string]$correction.numeric_source) {
                            $sourceNumericValues[$index] = [string]$correction.numeric_ru
                        }
                    }
                }
            }
        }
        $sourceNumericSignature = (@($sourceNumericValues | Sort-Object -Unique) -join "`n")
        if ($sourceNumericSignature -cne $russianNumericSignature) { $qaIssues.Add('numeric_prose_signature') }
        if ($russianText -match '/>\p{IsCyrillic}') { $qaIssues.Add('inflected_component_suffix') }
        if (Test-ContainsUntranslatedSourceLine $page.source_text $russianText) { $qaIssues.Add('untranslated_source_line') }
    }
    $guideRows.Add([pscustomobject]@{
        namespace = $page.namespace
        guide_root = $page.guide_root
        relative_page = $page.relative_page
        source_jar = $page.source_jar
        expected_ru_overlay = "assets/$($page.namespace)/$($page.guide_root)/_ru_ru/$($page.relative_page)"
        translated = $translated
        qa_issues = @($qaIssues)
        qa_issue_count = $qaIssues.Count
        numeric_source_signature = if ($qaIssues.Contains('numeric_prose_signature')) { $sourceNumericSignature } else { $null }
        numeric_ru_signature = if ($qaIssues.Contains('numeric_prose_signature')) { $russianNumericSignature } else { $null }
    })
}
$missingGuidePages = @($guideRows | Where-Object { -not $_.translated })
$guideQaFailures = @($guideRows | Where-Object { $_.qa_issue_count -gt 0 })
$unusedGuideContentCorrections = @($guideContentCorrections.Keys | Where-Object { -not $seenGuideContentCorrections.Contains($_) } | Sort-Object)

$bookRows = [System.Collections.Generic.List[object]]::new()
foreach ($pageKey in @($bookDefaultPages.Keys | Sort-Object)) {
    $page = $bookDefaultPages[$pageKey]
    $overlayPath = Join-Path $overrideRoot "$($page.namespace)\book\$($page.book_root)\ru_ru\$($page.relative_page -replace '/', '\')"
    $translated = $bookRussianPages.Contains($pageKey) -or (Test-Path -LiteralPath $overlayPath -PathType Leaf)
    # The sparse Paxi overlay is the effective resource and therefore must
    # take precedence over a lower-quality ru_ru page bundled in the JAR.
    $russianText = if (Test-Path -LiteralPath $overlayPath -PathType Leaf) {
        Get-Content -Raw -Encoding UTF8 -LiteralPath $overlayPath
    }
    elseif ($bookRussianTexts.ContainsKey($pageKey)) {
        [string]$bookRussianTexts[$pageKey]
    }
    else { $null }
    $qaIssues = [System.Collections.Generic.List[string]]::new()
    if ($translated) {
        if ([string]::IsNullOrWhiteSpace($russianText)) { $qaIssues.Add('empty_translation') }
        if ($null -ne $russianText -and $russianText.Contains([char]0xFFFD)) { $qaIssues.Add('replacement_character') }
        if ((Get-RegexGroupSignature $page.source_text '(<[A-Z_]+>)') -cne (Get-RegexGroupSignature $russianText '(<[A-Z_]+>)')) { $qaIssues.Add('book_markup_signature') }
        if (Test-ContainsUntranslatedSourceLine $page.source_text $russianText) { $qaIssues.Add('untranslated_source_line') }
    }
    $bookRows.Add([pscustomobject]@{
        namespace = $page.namespace
        book_root = $page.book_root
        relative_page = $page.relative_page
        source_jar = $page.source_jar
        expected_ru_overlay = "assets/$($page.namespace)/book/$($page.book_root)/ru_ru/$($page.relative_page)"
        translated = $translated
        qa_issues = @($qaIssues)
        qa_issue_count = $qaIssues.Count
    })
}
$missingBookPages = @($bookRows | Where-Object { -not $_.translated })
$bookQaFailures = @($bookRows | Where-Object { $_.qa_issue_count -gt 0 })

$manifestReport = [pscustomobject]@{
    schema_version = 2
    build_id = $BuildId
    generated_at = (Get-Date).ToUniversalTime().ToString('o')
    platform = [pscustomobject]@{ minecraft = '1.20.1'; forge = '47.4.22' }
    jar_count = $jars.Count
    curseforge_provenance_complete = ($unknownSources.Count -eq 0)
    owner_registered_exception_count = $ownerExceptionEntries.Count
    owner_registered_exception_files = @($ownerExceptionEntries | ForEach-Object { $_.file_name })
    stale_owner_exception_count = $staleOwnerExceptions.Count
    stale_owner_exception_files = @($staleOwnerExceptions)
    curseforge_cdn_url_complete = ($invalidCurseForgeUrls.Count -eq 0)
    invalid_curseforge_url_count = $invalidCurseForgeUrls.Count
    invalid_curseforge_url_files = @($invalidCurseForgeUrls)
    expected_hash_mismatch_count = $hashMismatches.Count
    entries = @($manifestEntries)
}
$dependencyReport = [pscustomobject]@{
    schema_version = 1
    build_id = $BuildId
    generated_at = (Get-Date).ToUniversalTime().ToString('o')
    providers = @($providers.GetEnumerator() | Sort-Object Name | ForEach-Object { [pscustomobject]@{ mod_id = $_.Name; version = $_.Value.version; origin = $_.Value.origin } })
    mandatory_checks = @($dependencyChecks | Sort-Object owner_mod_id, dependency_mod_id)
    hard_failure_count = $hardDependencyFailures.Count
    unverified_count = $unverifiedDependencies.Count
    advisory_count = $advisoryDependencies.Count
    advisories = @($advisoryDependencies)
    metadata_errors = @($metadataErrors)
}
$localizationReport = [pscustomobject]@{
    schema_version = 2
    build_id = $BuildId
    generated_at = (Get-Date).ToUniversalTime().ToString('o')
    total_missing_ru_keys = [int]$missingTranslations
    total_empty_ru_values = [int]$emptyTranslations
    total_replacement_characters = [int]$replacementCharacters
    total_placeholder_mismatches = [int]$placeholderMismatches
    total_allowed_placeholder_exceptions = [int]$allowedPlaceholderExceptions
    total_unknown_overlay_keys = [int]$unknownOverlayKeys
    unused_format_exceptions = $unusedFormatExceptions
    release_gate_met = ([int]$missingTranslations -eq 0 -and [int]$emptyTranslations -eq 0 -and [int]$replacementCharacters -eq 0 -and [int]$placeholderMismatches -eq 0 -and [int]$unknownOverlayKeys -eq 0 -and $unusedFormatExceptions.Count -eq 0)
    namespaces = @($localizationRows | Sort-Object namespace)
}
$guideContentReport = [pscustomobject]@{
    schema_version = 2
    build_id = $BuildId
    generated_at = (Get-Date).ToUniversalTime().ToString('o')
    default_markdown_page_count = $guideRows.Count
    translated_ru_page_count = $guideRows.Count - $missingGuidePages.Count
    missing_ru_page_count = $missingGuidePages.Count
    qa_failure_count = $guideQaFailures.Count
    unused_content_corrections = $unusedGuideContentCorrections
    release_gate_met = ($missingGuidePages.Count -eq 0 -and $guideQaFailures.Count -eq 0 -and $unusedGuideContentCorrections.Count -eq 0)
    pages = @($guideRows)
}
$bookContentReport = [pscustomobject]@{
    schema_version = 1
    build_id = $BuildId
    generated_at = (Get-Date).ToUniversalTime().ToString('o')
    default_text_page_count = $bookRows.Count
    translated_ru_page_count = $bookRows.Count - $missingBookPages.Count
    missing_ru_page_count = $missingBookPages.Count
    qa_failure_count = $bookQaFailures.Count
    release_gate_met = ($missingBookPages.Count -eq 0 -and $bookQaFailures.Count -eq 0)
    pages = @($bookRows)
}

$manifestReport | ConvertTo-Json -Depth 20 | Set-Content -Encoding UTF8 -LiteralPath (Join-Path $OutputDirectory 'mod_manifest_lock.json')
$dependencyReport | ConvertTo-Json -Depth 20 | Set-Content -Encoding UTF8 -LiteralPath (Join-Path $OutputDirectory 'dependency_audit.json')
$localizationReport | ConvertTo-Json -Depth 20 | Set-Content -Encoding UTF8 -LiteralPath (Join-Path $OutputDirectory 'localization_baseline.json')
$guideContentReport | ConvertTo-Json -Depth 20 | Set-Content -Encoding UTF8 -LiteralPath (Join-Path $OutputDirectory 'guide_content_baseline.json')
$bookContentReport | ConvertTo-Json -Depth 20 | Set-Content -Encoding UTF8 -LiteralPath (Join-Path $OutputDirectory 'book_content_baseline.json')

$summary = @"
# Generated static audit - $BuildId

- JAR files: $($jars.Count)
- Unknown CurseForge provenance: $($unknownSources.Count)
- Owner-registered non-CurseForge exceptions: $($ownerExceptionEntries.Count)
- Stale owner exceptions without an installed file: $($staleOwnerExceptions.Count)
- Invalid CurseForge CDN URLs: $($invalidCurseForgeUrls.Count)
- Published-source hash mismatches: $($hashMismatches.Count)
- Mandatory dependency failures: $($hardDependencyFailures.Count)
- Mandatory dependency ranges requiring manual review: $($unverifiedDependencies.Count)
- Mandatory dependency advisories Forge does not enforce: $($advisoryDependencies.Count)
- Missing Russian keys after current overlay: $missingTranslations
- Empty Russian values: $emptyTranslations
- Replacement-character values: $replacementCharacters
- Placeholder mismatches: $placeholderMismatches
- Allowed placeholder exceptions: $allowedPlaceholderExceptions
- Unused format exceptions: $($unusedFormatExceptions.Count)
- Unknown overlay keys: $unknownOverlayKeys
- Missing Russian GuideME Markdown pages: $($missingGuidePages.Count)
- GuideME translated-page structural QA failures: $($guideQaFailures.Count)
- Unused registered GuideME content corrections: $($unusedGuideContentCorrections.Count)
- Missing Russian localized-book text pages: $($missingBookPages.Count)
- Localized-book structural QA failures: $($bookQaFailures.Count)
- Minecraft was not launched by this audit.

The JSON files beside this summary contain the exact manifest, dependency checks, and localisation backlog.
"@
$summary | Set-Content -Encoding UTF8 -LiteralPath (Join-Path $OutputDirectory 'README.md')

Write-Output "Build: $BuildId"
Write-Output "JARs: $($jars.Count)"
Write-Output "Unknown CurseForge provenance: $($unknownSources.Count)"
Write-Output "Owner-registered non-CurseForge exceptions: $($ownerExceptionEntries.Count)"
Write-Output "Stale owner exceptions: $($staleOwnerExceptions.Count)"
Write-Output "Invalid CurseForge CDN URLs: $($invalidCurseForgeUrls.Count)"
Write-Output "Published-source hash mismatches: $($hashMismatches.Count)"
Write-Output "Mandatory dependency failures: $($hardDependencyFailures.Count)"
Write-Output "Unverified mandatory ranges: $($unverifiedDependencies.Count)"
Write-Output "Unenforced dependency advisories: $($advisoryDependencies.Count)"
Write-Output "Missing Russian keys after overlay: $missingTranslations"
Write-Output "Empty Russian values: $emptyTranslations"
Write-Output "Replacement-character values: $replacementCharacters"
Write-Output "Placeholder mismatches: $placeholderMismatches"
Write-Output "Allowed placeholder exceptions: $allowedPlaceholderExceptions"
Write-Output "Unused format exceptions: $($unusedFormatExceptions.Count)"
Write-Output "Unknown overlay keys: $unknownOverlayKeys"
Write-Output "Missing Russian GuideME Markdown pages: $($missingGuidePages.Count)"
Write-Output "GuideME translated-page structural QA failures: $($guideQaFailures.Count)"
Write-Output "Unused registered GuideME content corrections: $($unusedGuideContentCorrections.Count)"
Write-Output "Missing Russian localized-book text pages: $($missingBookPages.Count)"
Write-Output "Localized-book structural QA failures: $($bookQaFailures.Count)"
Write-Output "Reports: $OutputDirectory"

if ($unknownSources.Count -gt 0 -or $staleOwnerExceptions.Count -gt 0 -or $invalidCurseForgeUrls.Count -gt 0 -or $hashMismatches.Count -gt 0 -or $hardDependencyFailures.Count -gt 0) { exit 2 }
exit 0
