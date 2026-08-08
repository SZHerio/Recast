param(
    [string]$Root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path,
    [string]$CsvPath = (Join-Path $PSScriptRoot 'archive_lang_findings.csv'),
    [string]$SummaryPath = (Join-Path $PSScriptRoot 'archive_lang_summary.json')
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem

function ConvertFrom-LangText {
    param(
        [Parameter(Mandatory = $true)][string]$Text,
        [Parameter(Mandatory = $true)][string]$Extension
    )

    $dictionary = @{}
    $valid = $true
    $errorMessage = $null

    if ($Extension -eq 'json') {
        try {
            $object = $Text | ConvertFrom-Json -ErrorAction Stop
            foreach ($property in $object.PSObject.Properties) {
                $dictionary[$property.Name] = [string]$property.Value
            }
        }
        catch {
            $valid = $false
            $errorMessage = ($_.Exception.Message -replace '\s+', ' ').Trim()
            if ($errorMessage.Length -gt 500) {
                $errorMessage = $errorMessage.Substring(0, 500)
            }

            # Salvage simple string pairs only for diagnostics (and for a broken EN
            # file, should one ever occur). Invalid RU dictionaries are never merged.
            $pattern = '(?m)^\s*"((?:\\.|[^"\\])*)"\s*:\s*"((?:\\.|[^"\\])*)"\s*,?\s*$'
            foreach ($match in [regex]::Matches($Text, $pattern)) {
                $dictionary[$match.Groups[1].Value] = $match.Groups[2].Value
            }
        }
    }
    else {
        foreach ($line in ($Text -split "`r?`n")) {
            $trimmed = $line.Trim()
            if (-not $trimmed -or $trimmed.StartsWith('#') -or -not $trimmed.Contains('=')) {
                continue
            }
            $separator = $trimmed.IndexOf('=')
            $dictionary[$trimmed.Substring(0, $separator).Trim()] = $trimmed.Substring($separator + 1).Trim()
        }
    }

    [pscustomobject]@{
        Dictionary = $dictionary
        Valid = $valid
        ErrorMessage = $errorMessage
    }
}

function Read-ZipEntryText {
    param([Parameter(Mandatory = $true)]$Entry)

    $reader = [System.IO.StreamReader]::new($Entry.Open(), [System.Text.Encoding]::UTF8, $true)
    try {
        $reader.ReadToEnd()
    }
    finally {
        $reader.Dispose()
    }
}

function Get-RelativePath {
    param([Parameter(Mandatory = $true)][string]$FullPath)

    $resolved = [System.IO.Path]::GetFullPath($FullPath)
    if ($resolved.StartsWith($Root, [System.StringComparison]::OrdinalIgnoreCase)) {
        return $resolved.Substring($Root.Length).TrimStart('\', '/').Replace('\', '/')
    }
    $resolved.Replace('\', '/')
}

function Test-IsUnderPath {
    param(
        [Parameter(Mandatory = $true)][string]$Candidate,
        [Parameter(Mandatory = $true)][string]$Parent
    )

    $candidatePath = [System.IO.Path]::GetFullPath($Candidate)
    $parentPath = [System.IO.Path]::GetFullPath($Parent).TrimEnd('\', '/') + [System.IO.Path]::DirectorySeparatorChar
    $candidatePath.StartsWith($parentPath, [System.StringComparison]::OrdinalIgnoreCase)
}

function Add-ParseError {
    param(
        [Parameter(Mandatory = $true)][string]$Source,
        [Parameter(Mandatory = $true)][string]$Locale,
        [Parameter(Mandatory = $true)][string]$Message,
        [Parameter(Mandatory = $true)][int]$SalvagedKeyCount
    )

    $lineHint = $null
    $details = $null
    if ($Source -like '*ImmersivePetroleum-1.20.1-4.3.1-36b.jar!*assets/immersivepetroleum/lang/ru_ru.json') {
        $lineHint = 293
        $details = 'Missing comma after desc.immersivepetroleum.compat.jei.distillation.byproduct; the invalid RU file is ignored.'
    }

    $script:parseErrors.Add([pscustomobject][ordered]@{
        source = $Source
        locale = $Locale
        kind = 'invalid_json'
        message = $Message
        line_hint = $lineHint
        details = $details
        salvaged_key_count = $SalvagedKeyCount
        ignored = $true
    })
}

$weaponPattern = '(?i)(gun|weapon|rifle|pistol|shotgun|sniper|revolver|musket|carbine|firearm|cannon|artillery|mortar|launcher|grenade|landmine|bomb|missile|rocket|ammunition|\bammo\b|bullet|cartridge|bayonet|sword|dagger|knife|spear|halberd|mace|crossbow|longbow|shortbow|battleaxe|warhammer|flamethrower|minigun|machine.?gun|howitzer|torpedo|warhead|shell_(?:he|ap)|projectile)'

function Test-IsModName {
    param(
        [string]$Key,
        [string]$Value
    )

    $Key -match '(?i)(^|\.)(itemgroup|item_group|creative_?tab|creativetab|modname|mod_name)(\.|$)' -or
        $Key -match '(?i)^config\.[^.]+\.(title|name)$' -or
        $script:modDisplayNames.Contains($Value.Trim())
}

function Add-ModDisplayNamesFromArchive {
    param([Parameter(Mandatory = $true)]$Archive)

    foreach ($entry in $Archive.Entries) {
        $entryName = $entry.FullName.Replace('\', '/')
        if ($entryName -ieq 'META-INF/mods.toml') {
            $text = Read-ZipEntryText $entry
            foreach ($match in [regex]::Matches($text, '(?im)^\s*displayName\s*=\s*["'']([^"'']+)["'']')) {
                $name = $match.Groups[1].Value.Trim()
                if ($name) {
                    [void]$script:modDisplayNames.Add($name)
                }
            }
        }
        elseif ($entryName -ieq 'fabric.mod.json') {
            try {
                $metadata = (Read-ZipEntryText $entry) | ConvertFrom-Json -ErrorAction Stop
                if ($metadata.name) {
                    [void]$script:modDisplayNames.Add(([string]$metadata.name).Trim())
                }
            }
            catch {
                # Malformed metadata is unrelated to lang parsing and is ignored here.
            }
        }
    }
}

function Test-IsWeaponName {
    param(
        [string]$Namespace,
        [string]$Key,
        [string]$Value
    )

    # Exclude only actual registry display names. A weapon word inside a
    # tooltip, death message or configuration label does not make the whole
    # sentence a weapon name.
    if ($Key -notmatch '(?i)^(item|block|entity|effect)\.') {
        return $false
    }
    if ($Key -match '(?i)(^|\.)(desc|description|tooltip|summary|condition|behaviou?r|durability|info|message|comment|subtitle|hint|help|usage|warning|error|fire_?rate|rate_?of_?fire|controls?|action|status|mode)(\.|$)') {
        return $false
    }
    if ($Value -match "[`r`n]" -or $Value -match '%(?:\d+\$)?[a-zA-Z]' -or $Value -match '[.!?](?:\s|$)') {
        return $false
    }
    if ("$Key $Value" -match $weaponPattern) {
        return $true
    }
    if ($Namespace -in @('tacz', 'tacznpcs') -and $Key -match '(?i)^(item|entity)\.') {
        return $true
    }
    $false
}

function Get-FindingCategory {
    param([string]$Key)

    if ($Key -match '(?i)(gui|screen|menu|button|config|tooltip|info|desc|description|message|chat|command|error|warning|option|setting|advancement|subtitle|jei|ponder|keybind|controls|dialog|notification|toast|overlay|hud|search|filter)') {
        return 'ui_text'
    }
    if ($Key -match '(?i)^(item|block|entity|fluid|biome|effect|enchantment|tag)\.') {
        return 'content_name'
    }
    'other'
}

$modsPath = Join-Path $Root 'mods'
$backupsPath = Join-Path $Root 'backups'
$tmpPath = Join-Path $Root 'tmp'

$englishSources = [System.Collections.Generic.List[object]]::new()
$parseErrors = [System.Collections.Generic.List[object]]::new()
$modDisplayNames = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
$globalEnglish = @{}
$globalRussian = @{}
$globalRussianSource = @{}

$topLevelArchiveCount = 0
$topLevelArchivesWithLang = 0
$topLevelEnglishFileCount = 0
$topLevelRussianFileCount = 0
$topLevelNamespacePairs = [System.Collections.Generic.HashSet[string]]::new()
$topLevelNamespaces = [System.Collections.Generic.HashSet[string]]::new()
$nestedArchiveCount = 0
$nestedArchivesWithLang = 0
$nestedEnglishFileCount = 0
$nestedRussianFileCount = 0
$nestedNamespacePairs = [System.Collections.Generic.HashSet[string]]::new()

$archives = @(
    Get-ChildItem -LiteralPath $modsPath -File -ErrorAction SilentlyContinue |
        Where-Object { $_.Extension -in '.jar', '.zip' } |
        Sort-Object FullName
)
$topLevelArchiveCount = $archives.Count

foreach ($archiveFile in $archives) {
    $archive = [System.IO.Compression.ZipFile]::OpenRead($archiveFile.FullName)
    try {
        $archiveHasLang = $false
        $archiveRelative = Get-RelativePath $archiveFile.FullName
        Add-ModDisplayNamesFromArchive $archive

        foreach ($entry in $archive.Entries) {
            $match = [regex]::Match($entry.FullName.Replace('\', '/'), '(?i)^assets/([^/]+)/lang/(en_us|ru_ru)\.(json|lang)$')
            if (-not $match.Success) {
                continue
            }

            $archiveHasLang = $true
            $namespace = $match.Groups[1].Value.ToLowerInvariant()
            $locale = $match.Groups[2].Value.ToLowerInvariant()
            $extension = $match.Groups[3].Value.ToLowerInvariant()
            $source = "$archiveRelative!$($entry.FullName.Replace('\', '/'))"
            $parsed = ConvertFrom-LangText (Read-ZipEntryText $entry) $extension

            [void]$topLevelNamespacePairs.Add("$archiveRelative|$namespace")
            [void]$topLevelNamespaces.Add($namespace)

            if (-not $parsed.Valid) {
                Add-ParseError $source $locale $parsed.ErrorMessage $parsed.Dictionary.Count
            }

            if ($locale -eq 'en_us') {
                $topLevelEnglishFileCount++
                $englishSources.Add([pscustomobject]@{
                    source = $source
                    namespace = $namespace
                    dictionary = $parsed.Dictionary
                    kind = 'top_level_archive'
                })
                foreach ($key in $parsed.Dictionary.Keys) {
                    $globalEnglish[$key] = $parsed.Dictionary[$key]
                }
            }
            elseif ($parsed.Valid) {
                $topLevelRussianFileCount++
                foreach ($key in $parsed.Dictionary.Keys) {
                    $globalRussian[$key] = $parsed.Dictionary[$key]
                    $globalRussianSource[$key] = $source
                }
            }
        }

        if ($archiveHasLang) {
            $topLevelArchivesWithLang++
        }

        foreach ($nestedEntry in $archive.Entries) {
            if ($nestedEntry.FullName -notmatch '(?i)\.(jar|zip)$') {
                continue
            }

            $nestedArchiveCount++
            $memory = [System.IO.MemoryStream]::new()
            $nestedStream = $nestedEntry.Open()
            try {
                $nestedStream.CopyTo($memory)
            }
            finally {
                $nestedStream.Dispose()
            }
            $memory.Position = 0

            try {
                $nestedArchive = [System.IO.Compression.ZipArchive]::new($memory, [System.IO.Compression.ZipArchiveMode]::Read, $true)
                try {
                    $nestedHasLang = $false
                    Add-ModDisplayNamesFromArchive $nestedArchive
                    foreach ($entry in $nestedArchive.Entries) {
                        $match = [regex]::Match($entry.FullName.Replace('\', '/'), '(?i)^assets/([^/]+)/lang/(en_us|ru_ru)\.(json|lang)$')
                        if (-not $match.Success) {
                            continue
                        }

                        $nestedHasLang = $true
                        $namespace = $match.Groups[1].Value.ToLowerInvariant()
                        $locale = $match.Groups[2].Value.ToLowerInvariant()
                        $extension = $match.Groups[3].Value.ToLowerInvariant()
                        $source = "$archiveRelative!$($nestedEntry.FullName.Replace('\', '/'))!$($entry.FullName.Replace('\', '/'))"
                        $parsed = ConvertFrom-LangText (Read-ZipEntryText $entry) $extension

                        [void]$nestedNamespacePairs.Add("$archiveRelative!$($nestedEntry.FullName)|$namespace")

                        if (-not $parsed.Valid) {
                            Add-ParseError $source $locale $parsed.ErrorMessage $parsed.Dictionary.Count
                        }

                        if ($locale -eq 'en_us') {
                            $nestedEnglishFileCount++
                            $englishSources.Add([pscustomobject]@{
                                source = $source
                                namespace = $namespace
                                dictionary = $parsed.Dictionary
                                kind = 'nested_archive'
                            })
                            foreach ($key in $parsed.Dictionary.Keys) {
                                $globalEnglish[$key] = $parsed.Dictionary[$key]
                            }
                        }
                        elseif ($parsed.Valid) {
                            $nestedRussianFileCount++
                            foreach ($key in $parsed.Dictionary.Keys) {
                                $globalRussian[$key] = $parsed.Dictionary[$key]
                                $globalRussianSource[$key] = $source
                            }
                        }
                    }

                    if ($nestedHasLang) {
                        $nestedArchivesWithLang++
                    }
                }
                finally {
                    $nestedArchive.Dispose()
                }
            }
            finally {
                $memory.Dispose()
            }
        }
    }
    finally {
        $archive.Dispose()
    }
}

$looseRussianFiles = @(
    Get-ChildItem -LiteralPath $Root -Recurse -File -ErrorAction SilentlyContinue |
        Where-Object {
            $_.Name -in 'ru_ru.json', 'ru_ru.lang' -and
            -not (Test-IsUnderPath $_.FullName $modsPath) -and
            -not (Test-IsUnderPath $_.FullName $backupsPath) -and
            -not (Test-IsUnderPath $_.FullName $tmpPath)
        } |
        Sort-Object FullName
)

foreach ($file in $looseRussianFiles) {
    $source = Get-RelativePath $file.FullName
    $extension = $file.Extension.TrimStart('.').ToLowerInvariant()
    $text = [System.IO.File]::ReadAllText($file.FullName, [System.Text.Encoding]::UTF8)
    $parsed = ConvertFrom-LangText $text $extension

    if (-not $parsed.Valid) {
        Add-ParseError $source 'ru_ru' $parsed.ErrorMessage $parsed.Dictionary.Count
        continue
    }

    foreach ($key in $parsed.Dictionary.Keys) {
        $globalRussian[$key] = $parsed.Dictionary[$key]
        $globalRussianSource[$key] = $source
    }
}

$rawUniqueMissing = [System.Collections.Generic.HashSet[string]]::new()
$rawUniqueSame = [System.Collections.Generic.HashSet[string]]::new()
foreach ($key in $globalEnglish.Keys) {
    $english = [string]$globalEnglish[$key]
    if (-not $globalRussian.ContainsKey($key)) {
        [void]$rawUniqueMissing.Add($key)
    }
    elseif ($english -match '[A-Za-z]' -and $english.Trim() -eq ([string]$globalRussian[$key]).Trim()) {
        [void]$rawUniqueSame.Add($key)
    }
}

$findings = [System.Collections.Generic.List[object]]::new()
$excludedWeaponNames = 0
$excludedModNames = 0
$statusWithoutLatin = 0
$categoryCounts = [ordered]@{ ui_text = 0; content_name = 0; other = 0 }

foreach ($englishSource in $englishSources) {
    foreach ($key in $englishSource.dictionary.Keys) {
        $english = [string]$englishSource.dictionary[$key]
        $status = $null
        $ruSource = ''

        if (-not $globalRussian.ContainsKey($key)) {
            $status = 'missing_ru'
        }
        elseif ($english -match '[A-Za-z]' -and $english.Trim() -eq ([string]$globalRussian[$key]).Trim()) {
            $status = 'ru_equals_english'
            $ruSource = [string]$globalRussianSource[$key]
        }

        if (-not $status) {
            continue
        }
        if ($english -notmatch '[A-Za-z]') {
            $statusWithoutLatin++
            continue
        }
        if (Test-IsModName $key $english) {
            $excludedModNames++
            continue
        }
        if (Test-IsWeaponName $englishSource.namespace $key $english) {
            $excludedWeaponNames++
            continue
        }

        $category = Get-FindingCategory $key
        $categoryCounts[$category]++
        $findings.Add([pscustomobject][ordered]@{
            status = $status
            namespace = $englishSource.namespace
            key = $key
            english = $english
            source = $englishSource.source
            ru_source = $ruSource
        })
    }
}

$sortedFindings = @(
    $findings | Sort-Object status, namespace, key, source
)

$statusCounts = [ordered]@{
    missing_ru = @($sortedFindings | Where-Object status -eq 'missing_ru').Count
    ru_equals_english = @($sortedFindings | Where-Object status -eq 'ru_equals_english').Count
}
$uniqueMissingFindings = @($sortedFindings | Where-Object status -eq 'missing_ru' | Select-Object -ExpandProperty key -Unique).Count
$uniqueSameFindings = @($sortedFindings | Where-Object status -eq 'ru_equals_english' | Select-Object -ExpandProperty key -Unique).Count
$uniqueFindingKeys = @($sortedFindings | Select-Object -ExpandProperty key -Unique).Count
$placeholderPattern = '%(?:\d+\$)?[-#+ 0,(<]*\d*(?:\.\d+)?[a-zA-Z]|\{\d+\}|\\n|§[0-9A-FK-ORa-fk-or]'
$rowsWithPlaceholders = @($sortedFindings | Where-Object { $_.english -match $placeholderPattern }).Count

$namespaceSummary = @(
    $sortedFindings |
        Group-Object namespace |
        ForEach-Object {
            $groupRows = @($_.Group)
            [pscustomobject][ordered]@{
                namespace = $_.Name
                rows = $groupRows.Count
                missing_ru = @($groupRows | Where-Object status -eq 'missing_ru').Count
                ru_equals_english = @($groupRows | Where-Object status -eq 'ru_equals_english').Count
                unique_keys = @($groupRows | Select-Object -ExpandProperty key -Unique).Count
                source_count = @($groupRows | Select-Object -ExpandProperty source -Unique).Count
            }
        } |
        Sort-Object @{ Expression = 'rows'; Descending = $true }, namespace
)

$sourceSummary = @(
    $sortedFindings |
        Group-Object source |
        ForEach-Object {
            $groupRows = @($_.Group)
            [pscustomobject][ordered]@{
                source = $_.Name
                namespace = @($groupRows | Select-Object -ExpandProperty namespace -Unique) -join ','
                rows = $groupRows.Count
                missing_ru = @($groupRows | Where-Object status -eq 'missing_ru').Count
                ru_equals_english = @($groupRows | Where-Object status -eq 'ru_equals_english').Count
                unique_keys = @($groupRows | Select-Object -ExpandProperty key -Unique).Count
            }
        } |
        Sort-Object @{ Expression = 'rows'; Descending = $true }, source
)

$summary = [pscustomobject][ordered]@{
    schema_version = 1
    generated_at = (Get-Date).ToString('o')
    root = $Root.Replace('\', '/')
    outputs = [ordered]@{
        csv = (Get-RelativePath $CsvPath)
        summary = (Get-RelativePath $SummaryPath)
    }
    scope = [ordered]@{
        active_mod_archives_only = $true
        top_level_archive_directory = 'mods'
        nested_archives_scanned = $true
        loose_ru_overrides_included = $true
        excluded_inactive_directories = @('backups', 'tmp')
        resourcepacks_archive_count = @(Get-ChildItem -LiteralPath (Join-Path $Root 'resourcepacks') -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $_.Extension -eq '.zip' }).Count
        datapacks_archive_count = @(Get-ChildItem -LiteralPath (Join-Path $Root 'datapacks') -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $_.Extension -eq '.zip' }).Count
    }
    translation_policy = [ordered]@{
        generated_translations_in_csv = $false
        csv_english_is_source_text = $true
        future_translation_style = 'human, clear, natural Russian'
        preserve_placeholders_and_formatting = $true
    }
    inventory = [ordered]@{
        top_level_archives = $topLevelArchiveCount
        top_level_archives_with_lang = $topLevelArchivesWithLang
        top_level_archives_without_lang = $topLevelArchiveCount - $topLevelArchivesWithLang
        top_level_namespace_pairs = $topLevelNamespacePairs.Count
        top_level_unique_namespaces = $topLevelNamespaces.Count
        top_level_en_files = $topLevelEnglishFileCount
        top_level_valid_ru_files = $topLevelRussianFileCount
        nested_archives = $nestedArchiveCount
        nested_archives_with_lang = $nestedArchivesWithLang
        nested_namespace_pairs = $nestedNamespacePairs.Count
        nested_en_files = $nestedEnglishFileCount
        nested_valid_ru_files = $nestedRussianFileCount
        loose_valid_ru_files = $looseRussianFiles.Count - @($parseErrors | Where-Object { $_.source -notlike '*!*' }).Count
        loose_ru_files_scanned = $looseRussianFiles.Count
        english_source_files = $englishSources.Count
        unique_en_keys = $globalEnglish.Count
        unique_valid_ru_keys = $globalRussian.Count
        raw_unique_missing_ru_keys = $rawUniqueMissing.Count
        raw_unique_ru_equals_english_keys = $rawUniqueSame.Count
        known_mod_display_names = $modDisplayNames.Count
    }
    findings = [ordered]@{
        rows = $sortedFindings.Count
        unique_keys = $uniqueFindingKeys
        status_counts = $statusCounts
        unique_key_counts_by_status = [ordered]@{
            missing_ru = $uniqueMissingFindings
            ru_equals_english = $uniqueSameFindings
        }
        category_counts = $categoryCounts
        rows_with_placeholders_or_format_codes = $rowsWithPlaceholders
        excluded_by_heuristic = [ordered]@{
            weapon_names = $excludedWeaponNames
            mod_names = $excludedModNames
            status_rows_without_latin_letters = $statusWithoutLatin
        }
        duplicate_source_occurrences = $sortedFindings.Count - $uniqueFindingKeys
    }
    namespace_aggregates = $namespaceSummary
    source_aggregates = $sourceSummary
    parse_errors = @($parseErrors)
    notes = @(
        'Each CSV row is an English source occurrence; duplicate keys in repeated nested libraries remain separate because source is part of the record.',
        'missing_ru means no valid active RU value exists after merging valid mod, nested-JAR, Paxi, KubeJS, and TACZ language resources.',
        'ru_equals_english means the effective RU value is byte-content equivalent after trimming and still contains Latin letters.',
        'Invalid RU JSON files are reported and ignored, matching runtime behavior.',
        'CSV english values are copied from source language resources; no machine translations were generated.',
        'Future Russian translations must be human, clear, natural, and preserve placeholders and formatting codes exactly.',
        'Weapon and mod-name exclusion is heuristic; the exact regular expressions are preserved in generate_archive_lang_audit.ps1.'
    )
}

$outputDirectory = Split-Path -Parent $CsvPath
if (-not (Test-Path -LiteralPath $outputDirectory)) {
    New-Item -ItemType Directory -Path $outputDirectory -Force | Out-Null
}

$csvLines = @($sortedFindings | ConvertTo-Csv -NoTypeInformation -Delimiter ',')
$csvText = [string]::Join("`r`n", $csvLines) + "`r`n"
$utf8Bom = [System.Text.UTF8Encoding]::new($true)
[System.IO.File]::WriteAllText($CsvPath, $csvText, $utf8Bom)

$jsonText = $summary | ConvertTo-Json -Depth 12
$utf8NoBom = [System.Text.UTF8Encoding]::new($false)
[System.IO.File]::WriteAllText($SummaryPath, $jsonText + "`r`n", $utf8NoBom)

[pscustomobject]@{
    csv = $CsvPath
    summary = $SummaryPath
    rows = $sortedFindings.Count
    missing_ru = $statusCounts.missing_ru
    ru_equals_english = $statusCounts.ru_equals_english
    unique_keys = $uniqueFindingKeys
    parse_errors = $parseErrors.Count
}
