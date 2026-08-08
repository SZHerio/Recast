[CmdletBinding()]
param(
    [string]$Root,
    [switch]$Quiet
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

if ([string]::IsNullOrWhiteSpace($Root)) {
    $Root = Split-Path -Parent $PSScriptRoot
}

$Root = (Resolve-Path -LiteralPath $Root).Path
$errors = New-Object 'System.Collections.Generic.List[string]'
$warnings = New-Object 'System.Collections.Generic.List[string]'
$passes = New-Object 'System.Collections.Generic.List[string]'

function Add-ValidationError {
    param([string]$Message)
    $script:errors.Add($Message)
}

function Add-ValidationWarning {
    param([string]$Message)
    $script:warnings.Add($Message)
}

function Add-ValidationPass {
    param([string]$Message)
    $script:passes.Add($Message)
}

function Test-HasProperty {
    param(
        [object]$Object,
        [string]$Name
    )

    if ($null -eq $Object) {
        return $false
    }

    return $null -ne $Object.PSObject.Properties[$Name]
}

function Resolve-ContractPath {
    param([string]$RelativePath)

    if ([string]::IsNullOrWhiteSpace($RelativePath)) {
        throw 'Contract path is empty.'
    }
    if ([System.IO.Path]::IsPathRooted($RelativePath)) {
        throw "Contract path must be workspace-relative: $RelativePath"
    }
    if ($RelativePath -match '(^|[\\/])\.\.([\\/]|$)') {
        throw "Contract path may not traverse outside the workspace: $RelativePath"
    }

    $candidate = [System.IO.Path]::GetFullPath((Join-Path $Root $RelativePath))
    $rootPrefix = $Root.TrimEnd([System.IO.Path]::DirectorySeparatorChar, [System.IO.Path]::AltDirectorySeparatorChar) + [System.IO.Path]::DirectorySeparatorChar
    if (-not $candidate.StartsWith($rootPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Resolved path escapes the workspace: $RelativePath"
    }
    return $candidate
}

function Read-ContractJson {
    param(
        [string]$RelativePath,
        [string]$Label
    )

    try {
        $path = Resolve-ContractPath $RelativePath
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
            Add-ValidationError "$Label is missing: $RelativePath"
            return $null
        }
        $raw = Get-Content -Raw -LiteralPath $path
        $parsed = $raw | ConvertFrom-Json
        Add-ValidationPass "$Label parses as JSON."
        return [pscustomobject]@{
            Path = $path
            Raw = $raw
            Value = $parsed
        }
    }
    catch {
        Add-ValidationError "$Label could not be parsed: $RelativePath ($($_.Exception.Message))"
        return $null
    }
}

function Assert-RequiredProperties {
    param(
        [object]$Object,
        [object[]]$Required,
        [string]$Label
    )

    foreach ($nameValue in $Required) {
        $name = [string]$nameValue
        if (-not (Test-HasProperty $Object $name)) {
            Add-ValidationError "$Label is missing schema-required property '$name'."
        }
    }
}

function Assert-NoUnknownProperties {
    param(
        [object]$Object,
        [object[]]$Allowed,
        [string]$Label
    )

    $allowedNames = @($Allowed | ForEach-Object { [string]$_ })
    foreach ($property in @($Object.PSObject.Properties)) {
        if ($allowedNames -notcontains $property.Name) {
            Add-ValidationError "$Label contains undeclared property '$($property.Name)'."
        }
    }
}

function Assert-UniqueValues {
    param(
        [object[]]$Values,
        [string]$Label
    )

    $normalized = @($Values | ForEach-Object { [string]$_ })
    $duplicates = @($normalized | Group-Object | Where-Object { $_.Count -gt 1 } | ForEach-Object { $_.Name })
    if ($duplicates.Count -gt 0) {
        Add-ValidationError "$Label contains duplicates: $($duplicates -join ', ')"
    }
}

function Compare-ExactSets {
    param(
        [object[]]$Expected,
        [object[]]$Actual,
        [string]$Label
    )

    $expectedStrings = @($Expected | ForEach-Object { [string]$_ } | Sort-Object -Unique)
    $actualStrings = @($Actual | ForEach-Object { [string]$_ } | Sort-Object -Unique)
    $missing = @($expectedStrings | Where-Object { $actualStrings -notcontains $_ })
    $extra = @($actualStrings | Where-Object { $expectedStrings -notcontains $_ })
    if ($missing.Count -gt 0) {
        Add-ValidationError "$Label is missing: $($missing -join ', ')"
    }
    if ($extra.Count -gt 0) {
        Add-ValidationError "$Label has unexpected entries: $($extra -join ', ')"
    }
}

function Get-PngDimensions {
    param([string]$Path)

    $stream = [System.IO.File]::Open($Path, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::Read)
    try {
        $header = New-Object byte[] 24
        $read = $stream.Read($header, 0, 24)
        if ($read -ne 24) {
            throw 'File is shorter than a PNG header.'
        }
        $signature = @(137, 80, 78, 71, 13, 10, 26, 10)
        for ($index = 0; $index -lt $signature.Count; $index++) {
            if ([int]$header[$index] -ne $signature[$index]) {
                throw 'Invalid PNG signature.'
            }
        }
        [uint32]$width = ([uint32]$header[16] * 16777216) + ([uint32]$header[17] * 65536) + ([uint32]$header[18] * 256) + [uint32]$header[19]
        [uint32]$height = ([uint32]$header[20] * 16777216) + ([uint32]$header[21] * 65536) + ([uint32]$header[22] * 256) + [uint32]$header[23]
        return [pscustomobject]@{
            Width = [int64]$width
            Height = [int64]$height
        }
    }
    finally {
        $stream.Dispose()
    }
}

function Get-ObjectValues {
    param([object]$Object)
    return @($Object.PSObject.Properties | ForEach-Object { $_.Value })
}

$schemaDoc = Read-ContractJson 'authoring/schemas/m9_visual_system.schema.json' 'M9 JSON schema'
$registryDoc = Read-ContractJson 'docs/registries/m9_visual_system.json' 'M9 visual registry'
$provenanceDoc = Read-ContractJson 'docs/registries/m9_asset_provenance.json' 'M9 provenance registry'

if ($null -eq $schemaDoc -or $null -eq $registryDoc -or $null -eq $provenanceDoc) {
    foreach ($message in $errors) { Write-Host "[M9][ERROR] $message" -ForegroundColor Red }
    exit 1
}

$schema = $schemaDoc.Value
$registry = $registryDoc.Value
$provenance = $provenanceDoc.Value

try {
    $definitions = $schema.'$defs'
    $visualSchema = $definitions.visualRegistry
    $provenanceSchema = $definitions.provenanceRegistry
    $provenanceRecordSchema = $definitions.provenanceRecord
    $sourceArtworkRecordSchema = $definitions.sourceArtworkRecord
    Assert-RequiredProperties $registry @($visualSchema.required) 'M9 visual registry'
    Assert-NoUnknownProperties $registry @($visualSchema.properties.PSObject.Properties.Name) 'M9 visual registry'
    Assert-RequiredProperties $provenance @($provenanceSchema.required) 'M9 provenance registry'
    Assert-NoUnknownProperties $provenance @($provenanceSchema.properties.PSObject.Properties.Name) 'M9 provenance registry'
    foreach ($asset in @($provenance.assets)) {
        Assert-RequiredProperties $asset @($provenanceRecordSchema.required) "Provenance record '$($asset.asset_id)'"
        Assert-NoUnknownProperties $asset @($provenanceRecordSchema.properties.PSObject.Properties.Name) "Provenance record '$($asset.asset_id)'"
    }
    foreach ($sourceArtwork in @($provenance.source_artwork)) {
        Assert-RequiredProperties $sourceArtwork @($sourceArtworkRecordSchema.required) "Source-artwork record '$($sourceArtwork.source_id)'"
        Assert-NoUnknownProperties $sourceArtwork @($sourceArtworkRecordSchema.properties.PSObject.Properties.Name) "Source-artwork record '$($sourceArtwork.source_id)'"
    }
    Add-ValidationPass 'Schema-required and additional-property contracts were enforced.'
}
catch {
    Add-ValidationError "Schema contract could not be evaluated: $($_.Exception.Message)"
}

$testJsonCommand = Get-Command -Name 'Test-Json' -ErrorAction SilentlyContinue
if ($null -ne $testJsonCommand) {
    try {
        if (-not (Test-Json -Json $registryDoc.Raw -SchemaFile $schemaDoc.Path -ErrorAction Stop)) {
            Add-ValidationError 'M9 visual registry failed draft-2020-12 JSON Schema validation.'
        }
        if (-not (Test-Json -Json $provenanceDoc.Raw -SchemaFile $schemaDoc.Path -ErrorAction Stop)) {
            Add-ValidationError 'M9 provenance registry failed draft-2020-12 JSON Schema validation.'
        }
        Add-ValidationPass 'Full JSON Schema validation completed through Test-Json.'
    }
    catch {
        Add-ValidationError "Full JSON Schema validation failed: $($_.Exception.Message)"
    }
}

if ([int]$registry.schema_version -ne 1 -or [int]$provenance.schema_version -ne 1) {
    Add-ValidationError 'M9 registry schema_version must be 1.'
}
if ([string]$registry.registry_id -ne 'industrial_frontier:m9/visual_system') {
    Add-ValidationError "Unexpected visual registry ID: $($registry.registry_id)"
}
if ([string]$provenance.registry_id -ne 'industrial_frontier:m9/asset_provenance') {
    Add-ValidationError "Unexpected provenance registry ID: $($provenance.registry_id)"
}
if ([string]$registry.status -ne 'IMPLEMENTED_STATIC_UNTESTED') {
    Add-ValidationWarning "Visual registry status is '$($registry.status)', not IMPLEMENTED_STATIC_UNTESTED."
}
if (-not [bool]$registry.validation_contract.no_game_launch) {
    Add-ValidationError 'M9 validation contract must prohibit launching the game.'
}

foreach ($rootProperty in @($registry.asset_roots.PSObject.Properties)) {
    try {
        $resolvedRoot = Resolve-ContractPath ([string]$rootProperty.Value)
        if (-not (Test-Path -LiteralPath $resolvedRoot)) {
            Add-ValidationError "Asset root '$($rootProperty.Name)' is missing: $($rootProperty.Value)"
        }
    }
    catch {
        Add-ValidationError "Asset root '$($rootProperty.Name)' is invalid: $($_.Exception.Message)"
    }
}

$countProperties = @(
    'screens',
    'epochs',
    'process_pathways',
    'factions',
    'base_levels',
    'reputation_tiers',
    'treaties',
    'operation_stages'
)
foreach ($propertyName in $countProperties) {
    $expectedProperty = $registry.validation_contract.expected_counts.PSObject.Properties[$propertyName]
    $actualProperty = $registry.PSObject.Properties[$propertyName]
    if ($null -eq $expectedProperty -or $null -eq $actualProperty) {
        Add-ValidationError "Count contract is incomplete for '$propertyName'."
        continue
    }
    $actualCount = @($actualProperty.Value).Count
    if ($actualCount -ne [int]$expectedProperty.Value) {
        Add-ValidationError "Count mismatch for '$propertyName': expected $($expectedProperty.Value), got $actualCount."
    }
}

foreach ($collectionName in $countProperties) {
    $collection = @($registry.PSObject.Properties[$collectionName].Value)
    Assert-UniqueValues @($collection | ForEach-Object { $_.id }) "$collectionName IDs"
}

$stableIdPattern = '^[a-z0-9_.-]+:[a-z0-9_./-]+$'
foreach ($collectionName in $countProperties) {
    foreach ($entry in @($registry.PSObject.Properties[$collectionName].Value)) {
        if ([string]$entry.id -notmatch $stableIdPattern) {
            Add-ValidationError "Invalid stable ID in ${collectionName}: $($entry.id)"
        }
    }
}

$m2ProgressionDoc = Read-ContractJson 'docs/registries/m2_progression_graph.json' 'M2 progression graph'
for ($epochIndex = 0; $epochIndex -lt 10; $epochIndex++) {
    $epoch = @($registry.epochs | Where-Object { [int]$_.order -eq $epochIndex })
    if ($epoch.Count -ne 1) {
        Add-ValidationError "Exactly one epoch must have order $epochIndex."
        continue
    }
    $epochEntry = $epoch[0]
    $expectedEpochId = "industrial_frontier:epoch/p$epochIndex"
    if ([string]$epochEntry.id -ne $expectedEpochId -or [string]$epochEntry.code -ne "P$epochIndex") {
        Add-ValidationError "Epoch order $epochIndex does not use canonical ID/code $expectedEpochId / P$epochIndex."
    }
    if ($null -ne $m2ProgressionDoc -and -not $m2ProgressionDoc.Raw.Contains($expectedEpochId)) {
        Add-ValidationError "Epoch $expectedEpochId is absent from m2_progression_graph.json."
    }
}

$m2ProcessesDoc = Read-ContractJson 'docs/registries/m2_domain_process_ownership.json' 'M2 domain/process ownership'
if ($null -ne $m2ProcessesDoc) {
    $canonicalProcessIds = @([regex]::Matches($m2ProcessesDoc.Raw, 'industrial_frontier:pathway/[a-z0-9_./-]+') | ForEach-Object { $_.Value } | Sort-Object -Unique)
    $visualProcessIds = @($registry.process_pathways | ForEach-Object { [string]$_.id })
    Compare-ExactSets $canonicalProcessIds $visualProcessIds 'M9 process pathway IDs versus M2 ownership registry'
}

$canonicalFactionSlugs = @('zemlemer', 'meridian', 'free_caravans', 'helios', 'ash_root', 'scar')
Compare-ExactSets $canonicalFactionSlugs @($registry.factions | ForEach-Object { [string]$_.slug }) 'M9 faction slugs'
$factionRuntimePath = Resolve-ContractPath 'kubejs/server_scripts/40_balance/m85_factions_1_data.js'
if (Test-Path -LiteralPath $factionRuntimePath -PathType Leaf) {
    $factionRuntimeRaw = Get-Content -Raw -LiteralPath $factionRuntimePath
    foreach ($faction in @($registry.factions)) {
        if (-not $factionRuntimeRaw.Contains([string]$faction.slug)) {
            Add-ValidationError "Faction '$($faction.slug)' is absent from the M8.5 runtime data."
        }
        foreach ($colorField in @('runtime_color_hex', 'display_color_hex')) {
            if ([string]$faction.PSObject.Properties[$colorField].Value -notmatch '^#[0-9A-F]{6}$') {
                Add-ValidationError "Faction '$($faction.slug)' has invalid $colorField."
            }
        }
        $baseKeys = @($faction.base_asset_ids.PSObject.Properties.Name)
        Compare-ExactSets @('b0', 'b1', 'b2', 'b3', 'b4', 'b5', 'b6') $baseKeys "Faction '$($faction.slug)' base asset levels"
    }
}
else {
    Add-ValidationError 'M8.5 faction runtime data is missing.'
}

for ($baseIndex = 0; $baseIndex -le 6; $baseIndex++) {
    $base = @($registry.base_levels | Where-Object { [int]$_.order -eq $baseIndex })
    if ($base.Count -ne 1 -or [string]$base[0].id -ne "industrial_frontier:base/b$baseIndex" -or [string]$base[0].code -ne "B$baseIndex") {
        Add-ValidationError "Base level order $baseIndex does not use canonical B$baseIndex identity."
    }
}

$sortedReputation = @($registry.reputation_tiers | Sort-Object { [int]$_.order })
if ($sortedReputation.Count -eq 7) {
    if ([int]$sortedReputation[0].minimum -ne -100) {
        Add-ValidationError 'Reputation tiers must start at -100.'
    }
    if ([int]$sortedReputation[-1].maximum -ne 100) {
        Add-ValidationError 'Reputation tiers must end at 100.'
    }
    for ($index = 0; $index -lt $sortedReputation.Count; $index++) {
        $tier = $sortedReputation[$index]
        if ([int]$tier.minimum -gt [int]$tier.maximum) {
            Add-ValidationError "Reputation tier '$($tier.slug)' has an inverted range."
        }
        if ($index -gt 0 -and [int]$tier.minimum -ne ([int]$sortedReputation[$index - 1].maximum + 1)) {
            Add-ValidationError "Reputation tiers are not contiguous before '$($tier.slug)'."
        }
    }
}

$canonicalTreaties = @('truce', 'trade', 'tribute', 'alliance', 'joint_defence')
$canonicalOperations = @('planned', 'recon', 'warned', 'negotiation_window', 'preparation', 'active', 'recovery', 'cooldown', 'closed')
Compare-ExactSets $canonicalTreaties @($registry.treaties | ForEach-Object { [string]$_.slug }) 'Treaty visual IDs'
for ($operationIndex = 0; $operationIndex -lt $canonicalOperations.Count; $operationIndex++) {
    $operation = @($registry.operation_stages | Where-Object { [int]$_.order -eq $operationIndex })
    if ($operation.Count -ne 1 -or [string]$operation[0].slug -ne $canonicalOperations[$operationIndex]) {
        Add-ValidationError "Operation stage order $operationIndex must be '$($canonicalOperations[$operationIndex])'."
    }
}

$provenanceAssets = @($provenance.assets)
Assert-UniqueValues @($provenanceAssets | ForEach-Object { $_.asset_id }) 'Provenance asset IDs'
Assert-UniqueValues @($provenanceAssets | ForEach-Object { $_.path }) 'Provenance asset paths'
$assetById = @{}
$assetByResource = @{}
foreach ($asset in $provenanceAssets) {
    $assetId = [string]$asset.asset_id
    if ($assetId -notmatch '^industrial_frontier:asset/[a-z0-9_./-]+$') {
        Add-ValidationError "Invalid provenance asset ID: $assetId"
    }
    $assetById[$assetId] = $asset
    if (Test-HasProperty $asset 'resource_location') {
        $resourceLocation = [string]$asset.resource_location
        if ($assetByResource.ContainsKey($resourceLocation)) {
            Add-ValidationError "Duplicate resource location in provenance: $resourceLocation"
        }
        else {
            $assetByResource[$resourceLocation] = $asset
        }
    }

    try {
        $assetPath = Resolve-ContractPath ([string]$asset.path)
        if (-not (Test-Path -LiteralPath $assetPath -PathType Leaf)) {
            Add-ValidationError "Provenance asset is missing: $($asset.path)"
            continue
        }
        $item = Get-Item -LiteralPath $assetPath
        if ([int64]$item.Length -ne [int64]$asset.bytes) {
            Add-ValidationError "Byte-size mismatch for $($asset.path): expected $($asset.bytes), got $($item.Length)."
        }
        $actualHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $assetPath).Hash.ToUpperInvariant()
        if ($actualHash -ne ([string]$asset.sha256).ToUpperInvariant()) {
            Add-ValidationError "SHA-256 mismatch for $($asset.path)."
        }
        if ([string]$asset.kind -eq 'PNG') {
            if (-not (Test-HasProperty $asset 'width') -or -not (Test-HasProperty $asset 'height')) {
                Add-ValidationError "PNG provenance record lacks dimensions: $($asset.path)"
            }
            else {
                $dimensions = Get-PngDimensions $assetPath
                if ([int64]$dimensions.Width -ne [int64]$asset.width -or [int64]$dimensions.Height -ne [int64]$asset.height) {
                    Add-ValidationError "PNG dimension mismatch for $($asset.path): expected $($asset.width)x$($asset.height), got $($dimensions.Width)x$($dimensions.Height)."
                }
            }
        }
    }
    catch {
        Add-ValidationError "Asset validation failed for '$($asset.path)': $($_.Exception.Message)"
    }
}

foreach ($asset in $provenanceAssets) {
    if (Test-HasProperty $asset 'derived_from') {
        $sourceId = [string]$asset.derived_from
        if (-not $assetById.ContainsKey($sourceId)) {
            Add-ValidationError "Derived asset '$($asset.asset_id)' references missing source '$sourceId'."
        }
        elseif ([string]$asset.sha256 -ne [string]$assetById[$sourceId].sha256) {
            Add-ValidationError "Derived asset '$($asset.asset_id)' is declared byte-identical but its hash differs from '$sourceId'."
        }
    }
}

$sourceArtworkRecords = @($provenance.source_artwork)
Assert-UniqueValues @($sourceArtworkRecords | ForEach-Object { $_.source_id }) 'Source-artwork IDs'
Assert-UniqueValues @($sourceArtworkRecords | ForEach-Object { $_.path }) 'Source-artwork paths'
$sourceArtworkById = @{}
$sourceOutputAssetIds = New-Object 'System.Collections.Generic.List[string]'
foreach ($sourceArtwork in $sourceArtworkRecords) {
    $sourceArtworkId = [string]$sourceArtwork.source_id
    if ($sourceArtworkId -notmatch '^industrial_frontier:source/[a-z0-9_./-]+$') {
        Add-ValidationError "Invalid source-artwork ID: $sourceArtworkId"
    }
    $sourceArtworkById[$sourceArtworkId] = $sourceArtwork
    foreach ($outputAssetId in @($sourceArtwork.output_asset_ids)) {
        $sourceOutputAssetIds.Add([string]$outputAssetId)
    }

    try {
        $sourceArtworkPath = Resolve-ContractPath ([string]$sourceArtwork.path)
        if (-not (Test-Path -LiteralPath $sourceArtworkPath -PathType Leaf)) {
            Add-ValidationError "Source artwork is missing: $($sourceArtwork.path)"
            continue
        }
        $sourceArtworkItem = Get-Item -LiteralPath $sourceArtworkPath
        if ([int64]$sourceArtworkItem.Length -ne [int64]$sourceArtwork.bytes) {
            Add-ValidationError "Source-artwork byte-size mismatch for $($sourceArtwork.path): expected $($sourceArtwork.bytes), got $($sourceArtworkItem.Length)."
        }
        $sourceArtworkHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $sourceArtworkPath).Hash.ToUpperInvariant()
        if ($sourceArtworkHash -ne ([string]$sourceArtwork.sha256).ToUpperInvariant()) {
            Add-ValidationError "Source-artwork SHA-256 mismatch for $($sourceArtwork.path)."
        }
        $sourceArtworkDimensions = Get-PngDimensions $sourceArtworkPath
        if ([int64]$sourceArtworkDimensions.Width -ne [int64]$sourceArtwork.width -or [int64]$sourceArtworkDimensions.Height -ne [int64]$sourceArtwork.height) {
            Add-ValidationError "Source-artwork dimension mismatch for $($sourceArtwork.path): expected $($sourceArtwork.width)x$($sourceArtwork.height), got $($sourceArtworkDimensions.Width)x$($sourceArtworkDimensions.Height)."
        }
    }
    catch {
        Add-ValidationError "Source-artwork validation failed for '$($sourceArtwork.path)': $($_.Exception.Message)"
    }
}
Assert-UniqueValues @($sourceOutputAssetIds) 'Direct source-artwork output asset IDs'

foreach ($sourceArtwork in $sourceArtworkRecords) {
    $sourceArtworkId = [string]$sourceArtwork.source_id
    foreach ($outputAssetIdValue in @($sourceArtwork.output_asset_ids)) {
        $outputAssetId = [string]$outputAssetIdValue
        if (-not $assetById.ContainsKey($outputAssetId)) {
            Add-ValidationError "Source artwork '$sourceArtworkId' references missing output asset '$outputAssetId'."
        }
        elseif (-not (Test-HasProperty $assetById[$outputAssetId] 'source_artwork_id') -or [string]$assetById[$outputAssetId].source_artwork_id -ne $sourceArtworkId) {
            Add-ValidationError "Output asset '$outputAssetId' does not point back to source artwork '$sourceArtworkId'."
        }
    }
}

foreach ($asset in $provenanceAssets) {
    if (Test-HasProperty $asset 'source_artwork_id') {
        $sourceArtworkId = [string]$asset.source_artwork_id
        if (-not $sourceArtworkById.ContainsKey($sourceArtworkId)) {
            Add-ValidationError "Asset '$($asset.asset_id)' references missing source artwork '$sourceArtworkId'."
        }
        elseif (@($sourceArtworkById[$sourceArtworkId].output_asset_ids) -notcontains [string]$asset.asset_id) {
            Add-ValidationError "Asset '$($asset.asset_id)' is absent from source artwork '$sourceArtworkId' output_asset_ids."
        }
    }
}

try {
    $generatorPaths = @(
        [string]$provenance.generator.visual_generator_path,
        [string]$provenance.generator.brand_generator_path,
        [string]$provenance.generator.hero_installer_path
    )
    $fontLicensePath = Resolve-ContractPath ([string]$provenance.generator.font_license_path)
    foreach ($generatorPathValue in $generatorPaths) {
        $generatorPath = Resolve-ContractPath $generatorPathValue
        if (-not (Test-Path -LiteralPath $generatorPath -PathType Leaf)) {
            Add-ValidationError "Visual-generation tool is missing: $generatorPathValue"
        }
    }
    if (-not (Test-Path -LiteralPath $fontLicensePath -PathType Leaf)) {
        Add-ValidationError "Font license is missing: $($provenance.generator.font_license_path)"
    }
}
catch {
    Add-ValidationError "Generator provenance paths are invalid: $($_.Exception.Message)"
}

$referencedAssetIds = New-Object 'System.Collections.Generic.List[string]'
foreach ($screen in @($registry.screens)) {
    foreach ($assetId in @($screen.asset_ids)) { $referencedAssetIds.Add([string]$assetId) }
}
foreach ($entry in @($registry.epochs)) { $referencedAssetIds.Add([string]$entry.asset_id) }
foreach ($entry in @($registry.process_pathways)) { $referencedAssetIds.Add([string]$entry.asset_id) }
foreach ($faction in @($registry.factions)) {
    $referencedAssetIds.Add([string]$faction.emblem_asset_id)
    $referencedAssetIds.Add([string]$faction.silhouette_asset_id)
    foreach ($assetId in @(Get-ObjectValues $faction.base_asset_ids)) { $referencedAssetIds.Add([string]$assetId) }
}
foreach ($entry in @($registry.reputation_tiers)) { $referencedAssetIds.Add([string]$entry.asset_id) }
foreach ($entry in @($registry.treaties)) { $referencedAssetIds.Add([string]$entry.asset_id) }
foreach ($entry in @($registry.operation_stages)) { $referencedAssetIds.Add([string]$entry.asset_id) }
foreach ($assetId in @($referencedAssetIds | Sort-Object -Unique)) {
    if (-not $assetById.ContainsKey($assetId)) {
        Add-ValidationError "Visual registry references untracked asset '$assetId'."
    }
}

$ruDoc = Read-ContractJson ([string]$registry.localization_contract.ru_path) 'Russian M9 language source'
$enDoc = Read-ContractJson ([string]$registry.localization_contract.en_path) 'English M9 language source'
if ($null -ne $ruDoc -and $null -ne $enDoc) {
    $ruKeys = @($ruDoc.Value.PSObject.Properties.Name)
    $enKeys = @($enDoc.Value.PSObject.Properties.Name)
    if ([bool]$registry.localization_contract.parity_required) {
        Compare-ExactSets $ruKeys $enKeys 'RU/EN language-key parity'
    }
    foreach ($requiredKeyValue in @($registry.localization_contract.required_keys)) {
        $requiredKey = [string]$requiredKeyValue
        $ruProperty = $ruDoc.Value.PSObject.Properties[$requiredKey]
        $enProperty = $enDoc.Value.PSObject.Properties[$requiredKey]
        if ($null -eq $ruProperty) {
            Add-ValidationError "Russian language source is missing required M9 key '$requiredKey'."
        }
        elseif ([string]::IsNullOrWhiteSpace([string]$ruProperty.Value)) {
            Add-ValidationError "Russian M9 key '$requiredKey' has an empty value."
        }
        if ($null -eq $enProperty) {
            Add-ValidationError "English language source is missing required M9 key '$requiredKey'."
        }
        elseif ([string]::IsNullOrWhiteSpace([string]$enProperty.Value)) {
            Add-ValidationError "English M9 key '$requiredKey' has an empty value."
        }
    }
}

foreach ($screen in @($registry.screens)) {
    try {
        $layoutPath = Resolve-ContractPath ([string]$screen.layout_path)
        if (-not (Test-Path -LiteralPath $layoutPath -PathType Leaf)) {
            Add-ValidationError "Screen layout is missing for '$($screen.id)': $($screen.layout_path)"
            continue
        }
        $layoutRaw = Get-Content -Raw -LiteralPath $layoutPath
        if (-not $layoutRaw.Contains("identifier = $($screen.identifier)")) {
            Add-ValidationError "Screen '$($screen.id)' layout does not declare identifier '$($screen.identifier)'."
        }
        foreach ($referenceValue in @($screen.required_references)) {
            $reference = [string]$referenceValue
            if (-not $layoutRaw.Contains($reference)) {
                Add-ValidationError "Screen '$($screen.id)' layout is missing reference '$reference'."
            }
        }
        $activationPath = Resolve-ContractPath ([string]$screen.activation.path)
        if (-not (Test-Path -LiteralPath $activationPath -PathType Leaf)) {
            Add-ValidationError "Screen '$($screen.id)' activation file is missing: $($screen.activation.path)"
        }
        else {
            $activationRaw = Get-Content -Raw -LiteralPath $activationPath
            if (-not $activationRaw.Contains([string]$screen.activation.token)) {
                Add-ValidationError "Screen '$($screen.id)' activation token is missing: $($screen.activation.token)"
            }
        }
    }
    catch {
        Add-ValidationError "Screen contract failed for '$($screen.id)': $($_.Exception.Message)"
    }
}

$drippyScreens = @($registry.screens | Where-Object { [string]$_.kind -eq 'DRIPPY_LOADING' })
if ($drippyScreens.Count -gt 0) {
    $drippyOptionsPath = Resolve-ContractPath 'config/drippyloadingscreen/options.txt'
    if (-not (Test-Path -LiteralPath $drippyOptionsPath -PathType Leaf)) {
        Add-ValidationError 'Drippy Loading Screen options are missing.'
    }
    else {
        $drippyOptions = Get-Content -Raw -LiteralPath $drippyOptionsPath
        if (-not $drippyOptions.Contains('wait_for_textures_in_loading')) {
            Add-ValidationError 'Drippy Loading Screen options do not declare wait_for_textures_in_loading.'
        }
    }
}

foreach ($stackEntry in @($registry.implementation_stack)) {
    if ([string]$stackEntry.id -in @('fancymenu', 'drippyloadingscreen')) {
        $jar = @(Get-ChildItem -LiteralPath (Resolve-ContractPath 'mods') -File -Filter "*$($stackEntry.id)*$($stackEntry.version)*.jar")
        if ($jar.Count -eq 0) {
            Add-ValidationError "Implementation stack JAR not found for $($stackEntry.id) $($stackEntry.version)."
        }
    }
}

foreach ($epoch in @($registry.epochs)) {
    try {
        $chapterPath = Resolve-ContractPath ([string]$epoch.quest_chapter_path)
        if (-not (Test-Path -LiteralPath $chapterPath -PathType Leaf)) {
            Add-ValidationError "Epoch quest chapter is missing: $($epoch.quest_chapter_path)"
            continue
        }
        $chapterRaw = Get-Content -Raw -LiteralPath $chapterPath
        if (-not $chapterRaw.Contains([string]$epoch.resource_location)) {
            Add-ValidationError "Epoch quest '$($epoch.quest_chapter_path)' does not reference '$($epoch.resource_location)'."
        }
    }
    catch {
        Add-ValidationError "Epoch quest reference failed for '$($epoch.id)': $($_.Exception.Message)"
    }
}

$questIconPattern = 'industrial_frontier:[a-z0-9_./-]+\.png'
$scannedQuestFiles = 0
$scannedQuestReferences = New-Object 'System.Collections.Generic.List[string]'
foreach ($scanRootValue in @($registry.validation_contract.quest_icon_scan_roots)) {
    try {
        $scanRoot = Resolve-ContractPath ([string]$scanRootValue)
        if (-not (Test-Path -LiteralPath $scanRoot -PathType Container)) {
            Add-ValidationError "Quest icon scan root is missing: $scanRootValue"
            continue
        }
        foreach ($questFile in @(Get-ChildItem -LiteralPath $scanRoot -Recurse -File -Filter '*.snbt')) {
            $scannedQuestFiles++
            $questRaw = Get-Content -Raw -LiteralPath $questFile.FullName
            foreach ($match in @([regex]::Matches($questRaw, $questIconPattern))) {
                $scannedQuestReferences.Add([string]$match.Value)
            }
        }
    }
    catch {
        Add-ValidationError "Quest icon scan failed for '$scanRootValue': $($_.Exception.Message)"
    }
}
foreach ($resourceLocation in @($scannedQuestReferences | Sort-Object -Unique)) {
    if (-not $assetByResource.ContainsKey($resourceLocation)) {
        Add-ValidationError "Quest icon resource is not tracked by M9 provenance: $resourceLocation"
    }
}

if ($errors.Count -eq 0) {
    Add-ValidationPass "Validated $($provenanceAssets.Count) provenance assets (existence, SHA-256, bytes and PNG dimensions)."
    Add-ValidationPass "Validated $($sourceArtworkRecords.Count) retained source artworks and every direct output backlink."
    Add-ValidationPass "Validated $($registry.localization_contract.required_keys.Count) required M9 localization keys with full RU/EN parity."
    Add-ValidationPass "Validated $($registry.screens.Count) FancyMenu/Drippy screen contracts."
    Add-ValidationPass "Scanned $scannedQuestFiles FTB Quests files and $($scannedQuestReferences.Count) direct PNG icon references."
}

if (-not $Quiet) {
    foreach ($message in $passes) { Write-Host "[M9][PASS] $message" -ForegroundColor Green }
}
foreach ($message in $warnings) { Write-Host "[M9][WARN] $message" -ForegroundColor Yellow }
foreach ($message in $errors) { Write-Host "[M9][ERROR] $message" -ForegroundColor Red }

Write-Host "[M9][SUMMARY] errors=$($errors.Count) warnings=$($warnings.Count) passes=$($passes.Count) assets=$($provenanceAssets.Count) source_artwork=$($sourceArtworkRecords.Count) quest_files=$scannedQuestFiles quest_icon_refs=$($scannedQuestReferences.Count)"
if ($errors.Count -gt 0) {
    exit 1
}
exit 0
