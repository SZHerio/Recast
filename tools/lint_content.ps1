[CmdletBinding()]
param(
    [string]$Root = '',
    [string]$NodePath = ''
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if ([string]::IsNullOrWhiteSpace($Root)) {
    $scriptDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
    $Root = (Resolve-Path (Join-Path $scriptDirectory '..')).Path
}
$rootPath = (Resolve-Path -LiteralPath $Root).Path
$errors = [System.Collections.Generic.List[string]]::new()
$warnings = [System.Collections.Generic.List[string]]::new()

function Add-LintError { param([string]$Message) $script:errors.Add($Message) }
function Add-LintWarning { param([string]$Message) $script:warnings.Add($Message) }

function Read-JsonObject {
    param([string]$Path)
    try {
        return Get-Content -Raw -Encoding UTF8 -LiteralPath $Path | ConvertFrom-Json
    }
    catch {
        Add-LintError "Invalid JSON: $Path - $($_.Exception.Message)"
        return $null
    }
}

# Parse every authored JSON file. Generated reports are valid audit output too.
$jsonRoots = @('authoring', 'threat_director', 'config\paxi', 'docs\registries')
foreach ($relativeRoot in $jsonRoots) {
    $path = Join-Path $rootPath $relativeRoot
    if (-not (Test-Path -LiteralPath $path)) { continue }
    foreach ($file in Get-ChildItem -LiteralPath $path -Recurse -File -Filter '*.json') {
        [void](Read-JsonObject $file.FullName)
    }
}

# Traceability must point to real authored or generated artifacts. Counts are
# checked for the M1 corpora so documentation cannot silently drift from disk.
$tracePath = Join-Path $rootPath 'authoring\trace\m1_trace.json'
$trace = Read-JsonObject $tracePath
if ($null -ne $trace) {
    if ([int]$trace.schema_version -ne 2) { Add-LintError 'm1_trace.json must use schema_version 2.' }
    $featureIds = [System.Collections.Generic.HashSet[string]]::new()
    $featuresById = @{}
    foreach ($feature in @($trace.features)) {
        $featureId = [string]$feature.id
        if ([string]::IsNullOrWhiteSpace($featureId)) { Add-LintError 'Trace feature has an empty ID.'; continue }
        if (-not $featureIds.Add($featureId)) { Add-LintError "Duplicate trace feature ID: $featureId" }
        $featuresById[$featureId] = $feature
        foreach ($relativeFile in @($feature.files)) {
            $artifactPath = Join-Path $rootPath (([string]$relativeFile) -replace '/', '\')
            if (-not (Test-Path -LiteralPath $artifactPath)) { Add-LintError "Trace artifact does not exist: $relativeFile ($featureId)" }
        }
    }

    if ($featuresById.ContainsKey('m1.questbook')) {
        $questSourceCount = 0
        foreach ($questSourcePath in @(
            (Join-Path $rootPath 'authoring\quests\00_start_here.json'),
            (Join-Path $rootPath 'authoring\quests\90_help.json')
        )) {
            $questSource = Read-JsonObject $questSourcePath
            if ($null -ne $questSource) { $questSourceCount += @($questSource.quests).Count }
        }
        if ($questSourceCount -ne [int]$featuresById['m1.questbook'].artifact_count) {
            Add-LintError "Trace quest count mismatch: trace=$($featuresById['m1.questbook'].artifact_count), source=$questSourceCount"
        }
    }
    if ($featuresById.ContainsKey('m1.ru.guideme_ae2')) {
        $guideRoot = Join-Path $rootPath 'config\paxi\resourcepacks\IndustrialFrontier-Core\assets\ae2\ae2guide\_ru_ru'
        $guideCount = @(Get-ChildItem -LiteralPath $guideRoot -Recurse -File -Filter '*.md').Count
        if ($guideCount -ne [int]$featuresById['m1.ru.guideme_ae2'].artifact_count) {
            Add-LintError "Trace GuideME page count mismatch: trace=$($featuresById['m1.ru.guideme_ae2'].artifact_count), disk=$guideCount"
        }
    }
    if ($featuresById.ContainsKey('m1.ru.alexsmobs_dictionary')) {
        $alexRoot = Join-Path $rootPath 'config\paxi\resourcepacks\IndustrialFrontier-Core\assets\alexsmobs\book\animal_dictionary\ru_ru'
        $alexOverrideCount = @(Get-ChildItem -LiteralPath $alexRoot -File -Filter '*.txt').Count
        if ($alexOverrideCount -ne [int]$featuresById['m1.ru.alexsmobs_dictionary'].override_count) {
            Add-LintError "Trace Alex's Mobs override count mismatch: trace=$($featuresById['m1.ru.alexsmobs_dictionary'].override_count), disk=$alexOverrideCount"
        }
    }
    if ($featuresById.ContainsKey('m1.ru.citadel_book')) {
        $citadelRoot = Join-Path $rootPath 'config\paxi\resourcepacks\IndustrialFrontier-Core\assets\citadel\book\citadel_book'
        $citadelPageCount = @(Get-ChildItem -LiteralPath (Join-Path $citadelRoot 'ru_ru') -File -Filter '*.txt').Count
        if ($citadelPageCount -ne [int]$featuresById['m1.ru.citadel_book'].artifact_count) {
            Add-LintError "Trace Citadel page count mismatch: trace=$($featuresById['m1.ru.citadel_book'].artifact_count), disk=$citadelPageCount"
        }
    }
}

# M2 trace is separate so the historical M1 artifact counts stay immutable.
$m2TracePath = Join-Path $rootPath 'authoring\trace\m2_trace.json'
$m2Trace = Read-JsonObject $m2TracePath
if ($null -ne $m2Trace) {
    if ([int]$m2Trace.schema_version -ne 2) { Add-LintError 'm2_trace.json must use schema_version 2.' }
    if ([string]$m2Trace.build_id -ne 'IF-M2-0001') { Add-LintError 'm2_trace.json must identify IF-M2-0001.' }
    $m2FeatureIds = [System.Collections.Generic.HashSet[string]]::new()
    $m2FeaturesById = @{}
    foreach ($feature in @($m2Trace.features)) {
        $featureId = [string]$feature.id
        if ([string]::IsNullOrWhiteSpace($featureId)) { Add-LintError 'M2 trace feature has an empty ID.'; continue }
        if (-not $m2FeatureIds.Add($featureId)) { Add-LintError "Duplicate M2 trace feature ID: $featureId" }
        $m2FeaturesById[$featureId] = $feature
        foreach ($relativeFile in @($feature.files)) {
            $artifactPath = Join-Path $rootPath (([string]$relativeFile) -replace '/', '\')
            if (-not (Test-Path -LiteralPath $artifactPath)) { Add-LintError "M2 trace artifact does not exist: $relativeFile ($featureId)" }
        }
    }
    if ($m2FeaturesById.ContainsKey('m2.questbook_academy')) {
        $m2QuestSource = Read-JsonObject (Join-Path $rootPath 'authoring\quests\70_material_passports.json')
        if ($null -ne $m2QuestSource -and @($m2QuestSource.quests).Count -ne [int]$m2FeaturesById['m2.questbook_academy'].artifact_count) {
            Add-LintError "M2 trace quest count mismatch: trace=$($m2FeaturesById['m2.questbook_academy'].artifact_count), source=$(@($m2QuestSource.quests).Count)"
        }
    }
    if ($m2FeaturesById.ContainsKey('m2.accepted_input_tags')) {
        $m2ItemTagRoot = Join-Path $rootPath 'config\paxi\datapacks\IndustrialFrontier-Data\data\industrial_frontier\tags\items\materials'
        $m2FluidTagRoot = Join-Path $rootPath 'config\paxi\datapacks\IndustrialFrontier-Data\data\industrial_frontier\tags\fluids\materials'
        $m2TagCount = @(Get-ChildItem -LiteralPath $m2ItemTagRoot -File -Filter '*.json' | Where-Object { $_.BaseName -ne 'wood_logs' }).Count
        $m2TagCount += @(Get-ChildItem -LiteralPath $m2FluidTagRoot -File -Filter '*.json').Count
        if ($m2TagCount -ne [int]$m2FeaturesById['m2.accepted_input_tags'].artifact_count) {
            Add-LintError "M2 trace accepted-input tag count mismatch: trace=$($m2FeaturesById['m2.accepted_input_tags'].artifact_count), disk=$m2TagCount"
        }
    }
}

# M3 trace covers the P0-P3 main line. Its quest count is derived from the four
# authoring sources so a hand-edited chapter cannot drift away from the trace.
$m3TracePath = Join-Path $rootPath 'authoring\trace\m3_trace.json'
$m3Trace = Read-JsonObject $m3TracePath
$m3ChapterFiles = @('10_p0_expedition', '11_p1_mechanised', '12_p2_steam_metallurgy', '13_p3_electrification')
if ($null -ne $m3Trace) {
    if ([int]$m3Trace.schema_version -ne 2) { Add-LintError 'm3_trace.json must use schema_version 2.' }
    if ([string]$m3Trace.build_id -ne 'IF-M3-0001') { Add-LintError 'm3_trace.json must identify IF-M3-0001.' }
    $m3FeatureIds = [System.Collections.Generic.HashSet[string]]::new()
    $m3FeaturesById = @{}
    foreach ($feature in @($m3Trace.features)) {
        $featureId = [string]$feature.id
        if ([string]::IsNullOrWhiteSpace($featureId)) { Add-LintError 'M3 trace feature has an empty ID.'; continue }
        if (-not $m3FeatureIds.Add($featureId)) { Add-LintError "Duplicate M3 trace feature ID: $featureId" }
        $m3FeaturesById[$featureId] = $feature
        foreach ($relativeFile in @($feature.files)) {
            $artifactPath = Join-Path $rootPath (([string]$relativeFile) -replace '/', '\')
            if (-not (Test-Path -LiteralPath $artifactPath)) { Add-LintError "M3 trace artifact does not exist: $relativeFile ($featureId)" }
        }
    }

    $m3QuestCount = 0
    foreach ($chapterFile in $m3ChapterFiles) {
        $chapterSource = Read-JsonObject (Join-Path $rootPath "authoring\quests\$chapterFile.json")
        if ($null -eq $chapterSource) { continue }
        $m3QuestCount += @($chapterSource.quests).Count
        $compiled = Join-Path $rootPath "config\ftbquests\quests\chapters\$chapterFile.snbt"
        if (-not (Test-Path -LiteralPath $compiled -PathType Leaf)) {
            Add-LintError "Missing compiled M3 chapter: $chapterFile.snbt"
        }
        if ([bool]$chapterSource.optional) {
            Add-LintError "M3 main-line chapter must not be optional: $chapterFile"
        }
    }
    if ($m3FeaturesById.ContainsKey('m3.mainline_questbook') -and
        $m3QuestCount -ne [int]$m3FeaturesById['m3.mainline_questbook'].artifact_count) {
        Add-LintError "M3 trace quest count mismatch: trace=$($m3FeaturesById['m3.mainline_questbook'].artifact_count), source=$m3QuestCount"
    }
}

# M4 extends the same main line with the P4 chapter and the municipal water tail.
$m4TracePath = Join-Path $rootPath 'authoring\trace\m4_trace.json'
$m4Trace = Read-JsonObject $m4TracePath
$m4ChapterFiles = @('14_p4_chemical_city')
if ($null -ne $m4Trace) {
    if ([int]$m4Trace.schema_version -ne 2) { Add-LintError 'm4_trace.json must use schema_version 2.' }
    if ([string]$m4Trace.build_id -ne 'IF-M4-0001') { Add-LintError 'm4_trace.json must identify IF-M4-0001.' }
    $m4FeatureIds = [System.Collections.Generic.HashSet[string]]::new()
    $m4FeaturesById = @{}
    foreach ($feature in @($m4Trace.features)) {
        $featureId = [string]$feature.id
        if ([string]::IsNullOrWhiteSpace($featureId)) { Add-LintError 'M4 trace feature has an empty ID.'; continue }
        if (-not $m4FeatureIds.Add($featureId)) { Add-LintError "Duplicate M4 trace feature ID: $featureId" }
        $m4FeaturesById[$featureId] = $feature
        foreach ($relativeFile in @($feature.files)) {
            $artifactPath = Join-Path $rootPath (([string]$relativeFile) -replace '/', '\')
            if (-not (Test-Path -LiteralPath $artifactPath)) { Add-LintError "M4 trace artifact does not exist: $relativeFile ($featureId)" }
        }
    }
    $m4QuestCount = 0
    foreach ($chapterFile in $m4ChapterFiles) {
        $chapterSource = Read-JsonObject (Join-Path $rootPath "authoring\quests\$chapterFile.json")
        if ($null -eq $chapterSource) { continue }
        $m4QuestCount += @($chapterSource.quests).Count
        if (-not (Test-Path -LiteralPath (Join-Path $rootPath "config\ftbquests\quests\chapters\$chapterFile.snbt") -PathType Leaf)) {
            Add-LintError "Missing compiled M4 chapter: $chapterFile.snbt"
        }
        if ([bool]$chapterSource.optional) { Add-LintError "M4 main-line chapter must not be optional: $chapterFile" }
    }
    if ($m4FeaturesById.ContainsKey('m4.p4_chapter') -and
        $m4QuestCount -ne [int]$m4FeaturesById['m4.p4_chapter'].artifact_count) {
        Add-LintError "M4 trace quest count mismatch: trace=$($m4FeaturesById['m4.p4_chapter'].artifact_count), source=$m4QuestCount"
    }
}

# M5 opens P5 regional logistics. Its first debt was the AE2 entry contract, so
# the trace counts what the script actually registers rather than what the prose
# claims: seven authored recipe IDs and three removed foreign routes.
$m5TracePath = Join-Path $rootPath 'authoring\trace\m5_trace.json'
$m5Trace = Read-JsonObject $m5TracePath
$m5ChapterFiles = @('15_p5_regional_logistics')
if ($null -ne $m5Trace) {
    if ([int]$m5Trace.schema_version -ne 2) { Add-LintError 'm5_trace.json must use schema_version 2.' }
    if ([string]$m5Trace.build_id -ne 'IF-M5-0001') { Add-LintError 'm5_trace.json must identify IF-M5-0001.' }
    $m5FeatureIds = [System.Collections.Generic.HashSet[string]]::new()
    $m5FeaturesById = @{}
    foreach ($feature in @($m5Trace.features)) {
        $featureId = [string]$feature.id
        if ([string]::IsNullOrWhiteSpace($featureId)) { Add-LintError 'M5 trace feature has an empty ID.'; continue }
        if (-not $m5FeatureIds.Add($featureId)) { Add-LintError "Duplicate M5 trace feature ID: $featureId" }
        $m5FeaturesById[$featureId] = $feature
        foreach ($relativeFile in @($feature.files)) {
            $artifactPath = Join-Path $rootPath (([string]$relativeFile) -replace '/', '\')
            if (-not (Test-Path -LiteralPath $artifactPath)) { Add-LintError "M5 trace artifact does not exist: $relativeFile ($featureId)" }
        }
    }

    $ae2ContractPath = Join-Path $rootPath 'kubejs\server_scripts\10_progression\m5_ae2_entry_contract.js'
    if (Test-Path -LiteralPath $ae2ContractPath -PathType Leaf) {
        $ae2ContractText = Get-Content -Raw -Encoding UTF8 -LiteralPath $ae2ContractPath
        $authoredAe2Ids = @([regex]::Matches($ae2ContractText, 'industrial_frontier:m5/ae2/[a-z0-9_]+') | ForEach-Object { $_.Value } | Sort-Object -Unique)
        $removedForeignIds = @([regex]::Matches($ae2ContractText, 'nuclearcraft:assembler/ae2_[a-z_]+') | ForEach-Object { $_.Value } | Sort-Object -Unique)
        if ($m5FeaturesById.ContainsKey('m5.ae2_entry_contract')) {
            $ae2Feature = $m5FeaturesById['m5.ae2_entry_contract']
            if ($authoredAe2Ids.Count -ne [int]$ae2Feature.artifact_count) {
                Add-LintError "M5 AE2 contract recipe count mismatch: trace=$([int]$ae2Feature.artifact_count), script=$($authoredAe2Ids.Count)"
            }
            if ($removedForeignIds.Count -ne [int]$ae2Feature.removed_count) {
                Add-LintError "M5 AE2 contract removal count mismatch: trace=$([int]$ae2Feature.removed_count), script=$($removedForeignIds.Count)"
            }
        }
        # The three blocks are the epoch lock. If any of them stops citing an MV
        # GregTech component the gate silently drops back to vanilla-tier cost.
        foreach ($requiredComponent in @('gtceu:steel_plate', 'gtceu:mv_voltage_coil', 'gtceu:mv_electric_piston', 'gtceu:mv_electric_motor', 'gtceu:mv_machine_hull')) {
            if ($ae2ContractText -notmatch [regex]::Escape($requiredComponent)) {
                Add-LintError "M5 AE2 entry contract no longer prices its blocks in $requiredComponent."
            }
        }
    }

    # The P5 chapter is counted from its own source so a hand-edited SNBT cannot
    # drift away from the trace, exactly as the M3 and M4 chapters are.
    $m5QuestCount = 0
    foreach ($chapterFile in $m5ChapterFiles + @('46_operations_and_defence')) {
        $chapterSource = Read-JsonObject (Join-Path $rootPath "authoring\quests\$chapterFile.json")
        if ($null -eq $chapterSource) { continue }
        $m5QuestCount += @($chapterSource.quests).Count
        if (-not (Test-Path -LiteralPath (Join-Path $rootPath "config\ftbquests\quests\chapters\$chapterFile.snbt") -PathType Leaf)) {
            Add-LintError "Missing compiled M5 chapter: $chapterFile.snbt"
        }
        if ([bool]$chapterSource.optional) { Add-LintError "M5 chapter must not be optional: $chapterFile" }
    }
    if ($m5FeaturesById.ContainsKey('m5.questbook') -and
        $m5QuestCount -ne [int]$m5FeaturesById['m5.questbook'].artifact_count) {
        Add-LintError "M5 trace quest count mismatch: trace=$($m5FeaturesById['m5.questbook'].artifact_count), source=$m5QuestCount"
    }

    # Each transport layer must keep exactly one owner. If a removed second
    # railway or the MTR epoch gate quietly returns, the split is gone.
    $transportPath = Join-Path $rootPath 'kubejs\server_scripts\30_integrations\m5_transport_domains.js'
    if (Test-Path -LiteralPath $transportPath -PathType Leaf) {
        $transportText = Get-Content -Raw -Encoding UTF8 -LiteralPath $transportPath
        foreach ($requiredRoute in @('littlelogistics:steam_locomotive', 'littlelogistics:energy_locomotive', 'mtr:rail_node', 'mtr:railway_dashboard')) {
            if ($transportText -notmatch [regex]::Escape($requiredRoute)) {
                Add-LintError "M5 transport split no longer handles $requiredRoute."
            }
        }
    }
}

# M6 opens the civil nuclear domain. The mod was installed since the M4 wave but
# had no gate at all: its first machine cost lead and a piston, so the whole
# atomic industry was reachable in P1. The checks below make that regression
# loud if the gate is ever weakened.
$m6TracePath = Join-Path $rootPath 'authoring\trace\m6_trace.json'
$m6Trace = Read-JsonObject $m6TracePath
$m6ChapterFiles = @('16_p6_nuclear')
if ($null -ne $m6Trace) {
    if ([int]$m6Trace.schema_version -ne 2) { Add-LintError 'm6_trace.json must use schema_version 2.' }
    if ([string]$m6Trace.build_id -ne 'IF-M6-0001') { Add-LintError 'm6_trace.json must identify IF-M6-0001.' }
    $m6FeatureIds = [System.Collections.Generic.HashSet[string]]::new()
    $m6FeaturesById = @{}
    foreach ($feature in @($m6Trace.features)) {
        $featureId = [string]$feature.id
        if ([string]::IsNullOrWhiteSpace($featureId)) { Add-LintError 'M6 trace feature has an empty ID.'; continue }
        if (-not $m6FeatureIds.Add($featureId)) { Add-LintError "Duplicate M6 trace feature ID: $featureId" }
        $m6FeaturesById[$featureId] = $feature
        foreach ($relativeFile in @($feature.files)) {
            $artifactPath = Join-Path $rootPath (([string]$relativeFile) -replace '/', '\')
            if (-not (Test-Path -LiteralPath $artifactPath)) { Add-LintError "M6 trace artifact does not exist: $relativeFile ($featureId)" }
        }
    }

    $m6QuestCount = 0
    foreach ($chapterFile in $m6ChapterFiles) {
        $chapterSource = Read-JsonObject (Join-Path $rootPath "authoring\quests\$chapterFile.json")
        if ($null -eq $chapterSource) { continue }
        $m6QuestCount += @($chapterSource.quests).Count
        if (-not (Test-Path -LiteralPath (Join-Path $rootPath "config\ftbquests\quests\chapters\$chapterFile.snbt") -PathType Leaf)) {
            Add-LintError "Missing compiled M6 chapter: $chapterFile.snbt"
        }
        if ([bool]$chapterSource.optional) { Add-LintError "M6 chapter must not be optional: $chapterFile" }
    }
    if ($m6FeaturesById.ContainsKey('m6.questbook') -and
        $m6QuestCount -ne [int]$m6FeaturesById['m6.questbook'].artifact_count) {
        Add-LintError "M6 trace quest count mismatch: trace=$($m6FeaturesById['m6.questbook'].artifact_count), source=$m6QuestCount"
    }

    $nuclearGatePath = Join-Path $rootPath 'kubejs\server_scripts\10_progression\m6_nuclear_epoch_gate.js'
    if (Test-Path -LiteralPath $nuclearGatePath -PathType Leaf) {
        $nuclearGateText = Get-Content -Raw -Encoding UTF8 -LiteralPath $nuclearGatePath
        # The two entry machines are the whole lock. If either stops being
        # rebuilt on HV GregTech parts, the domain silently reopens in P1.
        foreach ($requiredRoute in @('nuclearcraft:manufactory', 'nuclearcraft:alloy_smelter', 'nuclearcraft:fission_reactor_controller')) {
            if ($nuclearGateText -notmatch [regex]::Escape($requiredRoute)) {
                Add-LintError "M6 nuclear gate no longer handles $requiredRoute."
            }
        }
        foreach ($requiredComponent in @('gtceu:steel_plate', 'gtceu:hv_machine_hull', 'gtceu:hv_electric_motor')) {
            if ($nuclearGateText -notmatch [regex]::Escape($requiredComponent)) {
                Add-LintError "M6 nuclear gate no longer prices the domain entry in $requiredComponent."
            }
        }
        $deferredCount = @([regex]::Matches($nuclearGateText, "'nuclearcraft:[a-z_]+'") | ForEach-Object { $_.Value } | Sort-Object -Unique).Count
        if ($m6FeaturesById.ContainsKey('m6.epoch_gate')) {
            $expected = [int]$m6FeaturesById['m6.epoch_gate'].artifact_count + [int]$m6FeaturesById['m6.epoch_gate'].removed_count
            # Three rebuilt entries plus eight deferred controllers, and the two
            # casing parts the controller recipe still names.
            if ($deferredCount -lt $expected) {
                Add-LintError "M6 nuclear gate names $deferredCount NuclearCraft IDs, fewer than the $expected the trace claims."
            }
        }
    }
}

# M7 opens the strategic and aerospace epoch. Two regressions are worth making
# loud here, because both were real conditions of the installed JARs rather than
# hypotheticals: the HBM machine domain had no entrance at all, and the whole
# Creating Space stack was reachable in the first epoch for six wooden slabs.
$m7TracePath = Join-Path $rootPath 'authoring\trace\m7_trace.json'
$m7Trace = Read-JsonObject $m7TracePath
$m7ChapterFiles = @('17_p7_strategic_space')
if ($null -ne $m7Trace) {
    if ([int]$m7Trace.schema_version -ne 2) { Add-LintError 'm7_trace.json must use schema_version 2.' }
    if ([string]$m7Trace.build_id -ne 'IF-M7-0001') { Add-LintError 'm7_trace.json must identify IF-M7-0001.' }
    $m7FeatureIds = [System.Collections.Generic.HashSet[string]]::new()
    $m7FeaturesById = @{}
    foreach ($feature in @($m7Trace.features)) {
        $featureId = [string]$feature.id
        if ([string]::IsNullOrWhiteSpace($featureId)) { Add-LintError 'M7 trace feature has an empty ID.'; continue }
        if (-not $m7FeatureIds.Add($featureId)) { Add-LintError "Duplicate M7 trace feature ID: $featureId" }
        $m7FeaturesById[$featureId] = $feature
        foreach ($relativeFile in @($feature.files)) {
            $artifactPath = Join-Path $rootPath (([string]$relativeFile) -replace '/', '\')
            if (-not (Test-Path -LiteralPath $artifactPath)) { Add-LintError "M7 trace artifact does not exist: $relativeFile ($featureId)" }
        }
    }

    $m7QuestCount = 0
    foreach ($chapterFile in $m7ChapterFiles) {
        $chapterSource = Read-JsonObject (Join-Path $rootPath "authoring\quests\$chapterFile.json")
        if ($null -eq $chapterSource) { continue }
        $m7QuestCount += @($chapterSource.quests).Count
        if (-not (Test-Path -LiteralPath (Join-Path $rootPath "config\ftbquests\quests\chapters\$chapterFile.snbt") -PathType Leaf)) {
            Add-LintError "Missing compiled M7 chapter: $chapterFile.snbt"
        }
        if ([bool]$chapterSource.optional) { Add-LintError "M7 chapter must not be optional: $chapterFile" }
    }
    if ($m7FeaturesById.ContainsKey('m7.questbook') -and
        $m7QuestCount -ne [int]$m7FeaturesById['m7.questbook'].artifact_count) {
        Add-LintError "M7 trace quest count mismatch: trace=$($m7FeaturesById['m7.questbook'].artifact_count), source=$m7QuestCount"
    }

    # The strategic gate is the only entrance the HBM machine domain has: its
    # assembly machine is produced solely by an assembly machine, so if this
    # recipe disappears the domain becomes unreachable again rather than early.
    $strategicGatePath = Join-Path $rootPath 'kubejs\server_scripts\10_progression\m7_strategic_epoch_gate.js'
    if (Test-Path -LiteralPath $strategicGatePath -PathType Leaf) {
        $strategicGateText = Get-Content -Raw -Encoding UTF8 -LiteralPath $strategicGatePath
        foreach ($requiredRoute in @('hbm_ntm_rebirth:machine_assembly_machine', 'hbm_ntm_rebirth:anvil_iron', 'hbm_ntm_rebirth:anvil_lead')) {
            if ($strategicGateText -notmatch [regex]::Escape($requiredRoute)) {
                Add-LintError "M7 strategic gate no longer handles $requiredRoute."
            }
        }
        foreach ($requiredComponent in @('gtceu:titanium_plate', 'gtceu:tungsten_steel_plate', 'gtceu:ev_machine_hull')) {
            if ($strategicGateText -notmatch [regex]::Escape($requiredComponent)) {
                Add-LintError "M7 strategic gate no longer prices the domain entry in $requiredComponent."
            }
        }
        # The weapon layer removal is an owner decision, not a stylistic one:
        # 367 recipes and three stations duplicated TaCZ and Epic Knights from a
        # plain crafting table.
        #
        # Removal by path pattern is a registered exception to the pack rule
        # "remove by exact ID verified against the JAR"
        # (industrial_frontier:bypass/pattern_recipe_removal). Its price is the
        # count assertion: a mod update changes the set silently, and without
        # the expected number the report would come from a player rather than
        # from a check. So the pairs themselves are what gets linted.
        foreach ($removedFolder in @(
            @{ folder = 'weapon'; expected = 121 },
            @{ folder = 'armor'; expected = 112 },
            @{ folder = 'ammo_press'; expected = 89 },
            @{ folder = 'armor_modules'; expected = 45 }
        )) {
            $assertion = "ifRemoveFolder(event, '$($removedFolder.folder)', $($removedFolder.expected))"
            if (-not $strategicGateText.Contains($assertion)) {
                Add-LintError "M7 strategic gate no longer asserts the recipe count for hbm_ntm_rebirth:$($removedFolder.folder)/ (expected $($removedFolder.expected))."
            }
        }
        # The two stations whose own recipes survive their folder's removal.
        foreach ($removedStation in @('hbm_ntm_rebirth:machines/ammo_press', 'hbm_ntm_rebirth:machines/armor_table')) {
            if ($strategicGateText -notmatch [regex]::Escape($removedStation)) {
                Add-LintError "M7 strategic gate no longer removes $removedStation."
            }
        }
    }

    # The space gate closes the other half: without it the engine designer costs
    # six wooden slabs and smooth stone, i.e. the first epoch.
    $spaceGatePath = Join-Path $rootPath 'kubejs\server_scripts\10_progression\m7_space_epoch_gate.js'
    if (Test-Path -LiteralPath $spaceGatePath -PathType Leaf) {
        $spaceGateText = Get-Content -Raw -Encoding UTF8 -LiteralPath $spaceGatePath
        foreach ($requiredRoute in @(
            'creatingspace:rocket_engineer_table', 'creatingspace:rocket_controls',
            'creatingspace:rocket_casing', 'creatingspace:oxygen_sealer',
            'creatingspace:air_liquefier', 'creatingspace:mechanical_electrolyzer',
            'creatingspace:cryogenic_tank', 'creatingspace:rocket_generator'
        )) {
            if ($spaceGateText -notmatch [regex]::Escape($requiredRoute)) {
                Add-LintError "M7 space gate no longer handles $requiredRoute."
            }
        }
    }

    # Destinations belong to GCYR. If the Creating Space route graph regains an
    # edge to a planet, the pack silently owns two Marses again.
    $orbitRoutePath = Join-Path $rootPath 'config\paxi\datapacks\IndustrialFrontier-Data\data\creatingspace\creatingspace\rocket_accessible_dimension\earth_orbit.json'
    $orbitRoute = Read-JsonObject $orbitRoutePath
    if ($null -eq $orbitRoute) {
        Add-LintError 'Missing Creating Space orbit route override.'
    }
    else {
        $adjacentNames = @($orbitRoute.adjacentDimensions.PSObject.Properties.Name)
        if ($adjacentNames.Count -ne 1 -or $adjacentNames[0] -ne 'minecraft:overworld') {
            Add-LintError "Creating Space low orbit must lead back to the overworld only; found: $($adjacentNames -join ', ')"
        }
    }

    # One radiation model. Both switches are the whole decision.
    $hbmConfigPath = Join-Path $rootPath 'config\hbm_ntm_rebirth-common.toml'
    if (-not (Test-Path -LiteralPath $hbmConfigPath -PathType Leaf)) {
        Add-LintError 'Missing HBM common config: the second radiation model would come back on first launch.'
    }
    else {
        $hbmConfigText = Get-Content -Raw -Encoding UTF8 -LiteralPath $hbmConfigPath
        foreach ($requiredSwitch in @('enableContamination', 'enableChunkRads')) {
            if ($hbmConfigText -notmatch ('(?m)^\s*{0}\s*=\s*false\s*$' -f [regex]::Escape($requiredSwitch))) {
                Add-LintError "HBM config must keep $requiredSwitch = false: the pack has exactly one radiation model."
            }
        }
    }
}

# M8 closes the campaign with P8 and P9. Two things here are worth protecting.
# The seven accelerator installations were deferred in M6 and returned here: if
# that return disappears, the whole branch becomes unreachable forever rather
# than late. And fusion has exactly two owners by owner decision — the third
# copy must stay removed.
$m8TracePath = Join-Path $rootPath 'authoring\trace\m8_trace.json'
$m8Trace = Read-JsonObject $m8TracePath
$m8ChapterFiles = @('18_p8_orbital_network', '19_p9_finale')
if ($null -ne $m8Trace) {
    if ([int]$m8Trace.schema_version -ne 2) { Add-LintError 'm8_trace.json must use schema_version 2.' }
    if ([string]$m8Trace.build_id -ne 'IF-M8-0001') { Add-LintError 'm8_trace.json must identify IF-M8-0001.' }
    $m8FeatureIds = [System.Collections.Generic.HashSet[string]]::new()
    $m8FeaturesById = @{}
    foreach ($feature in @($m8Trace.features)) {
        $featureId = [string]$feature.id
        if ([string]::IsNullOrWhiteSpace($featureId)) { Add-LintError 'M8 trace feature has an empty ID.'; continue }
        if (-not $m8FeatureIds.Add($featureId)) { Add-LintError "Duplicate M8 trace feature ID: $featureId" }
        $m8FeaturesById[$featureId] = $feature
        foreach ($relativeFile in @($feature.files)) {
            $artifactPath = Join-Path $rootPath (([string]$relativeFile) -replace '/', '\')
            if (-not (Test-Path -LiteralPath $artifactPath)) { Add-LintError "M8 trace artifact does not exist: $relativeFile ($featureId)" }
        }
    }

    $m8QuestCount = 0
    foreach ($chapterFile in $m8ChapterFiles) {
        $chapterSource = Read-JsonObject (Join-Path $rootPath "authoring\quests\$chapterFile.json")
        if ($null -eq $chapterSource) { continue }
        $m8QuestCount += @($chapterSource.quests).Count
        if (-not (Test-Path -LiteralPath (Join-Path $rootPath "config\ftbquests\quests\chapters\$chapterFile.snbt") -PathType Leaf)) {
            Add-LintError "Missing compiled M8 chapter: $chapterFile.snbt"
        }
        if ([bool]$chapterSource.optional) { Add-LintError "M8 main-line chapter must not be optional: $chapterFile" }
    }
    if ($m8FeaturesById.ContainsKey('m8.questbook') -and
        $m8QuestCount -ne [int]$m8FeaturesById['m8.questbook'].artifact_count) {
        Add-LintError "M8 trace quest count mismatch: trace=$($m8FeaturesById['m8.questbook'].artifact_count), source=$m8QuestCount"
    }

    # The mastery chapter is an optional handbook, not a progression gate.
    $masterySource = Read-JsonObject (Join-Path $rootPath 'authoring\quests\72_mastery_distributed_factory.json')
    if ($null -ne $masterySource -and -not [bool]$masterySource.optional) {
        Add-LintError 'The mastery chapter must remain optional.'
    }

    $lateGatePath = Join-Path $rootPath 'kubejs\server_scripts\10_progression\m8_late_epoch_gate.js'
    if (Test-Path -LiteralPath $lateGatePath -PathType Leaf) {
        $lateGateText = Get-Content -Raw -Encoding UTF8 -LiteralPath $lateGatePath
        foreach ($returnedInstallation in @(
            'nuclearcraft:linear_accelerator_controller', 'nuclearcraft:ring_accelerator_controller',
            'nuclearcraft:beam_diverter_controller', 'nuclearcraft:target_chamber_controller',
            'nuclearcraft:collision_chamber_controller', 'nuclearcraft:chamber_terminal',
            'nuclearcraft:quantum_transformer'
        )) {
            if ($lateGateText -notmatch [regex]::Escape($returnedInstallation)) {
                Add-LintError "M8 late gate no longer returns $returnedInstallation; the accelerator branch would stay unreachable."
            }
        }
        # Fusion has two owners, not three. The M6 gate removes the third copy
        # and M8 must not quietly re-create it.
        if ($lateGateText -match 'shaped\(\s*[''"]nuclearcraft:fusion_core') {
            Add-LintError 'M8 late gate re-creates the NuclearCraft fusion core: fusion has exactly two owners by owner decision.'
        }
    }
}

# The municipal water tail must stay closed: every declared sewage product needs
# a passport, otherwise the loop drains into an undeclared substance again.
$waterSubstancePath = Join-Path $rootPath 'docs\registries\m2_substance_passports.json'
$waterSubstances = Read-JsonObject $waterSubstancePath
if ($null -ne $waterSubstances) {
    $declaredSubstanceIds = [System.Collections.Generic.HashSet[string]]::new()
    foreach ($collection in @('passports', 'planned_substances')) {
        foreach ($entry in @($waterSubstances.$collection)) {
            [void]$declaredSubstanceIds.Add([string]$entry.substance_id)
        }
    }
    foreach ($required in @(
        'industrial_frontier:substance/raw_water',
        'industrial_frontier:substance/technical_water',
        'industrial_frontier:substance/drinking_water',
        'industrial_frontier:substance/wastewater',
        'industrial_frontier:substance/sludge',
        'industrial_frontier:substance/biogas',
        'industrial_frontier:substance/compost'
    )) {
        if (-not $declaredSubstanceIds.Contains($required)) {
            Add-LintError "Municipal water line is missing a passport: $required"
        }
    }
}

# The main line is only reachable if its chapter group exists and every chapter
# points at it. A chapter compiled into no group is invisible in game.
$chapterGroupsPath = Join-Path $rootPath 'config\ftbquests\quests\chapter_groups.snbt'
if (Test-Path -LiteralPath $chapterGroupsPath -PathType Leaf) {
    $chapterGroupsText = Get-Content -Raw -Encoding UTF8 -LiteralPath $chapterGroupsPath
    if ($chapterGroupsText -notmatch '1000000000000004') {
        Add-LintError 'Main-line chapter group 1000000000000004 is not declared in chapter_groups.snbt.'
    }
    foreach ($chapterFile in @($m3ChapterFiles + $m4ChapterFiles + $m5ChapterFiles + $m6ChapterFiles + $m7ChapterFiles + $m8ChapterFiles)) {
        $compiled = Join-Path $rootPath "config\ftbquests\quests\chapters\$chapterFile.snbt"
        if (-not (Test-Path -LiteralPath $compiled -PathType Leaf)) { continue }
        $compiledText = Get-Content -Raw -Encoding UTF8 -LiteralPath $compiled
        if ($compiledText -notmatch '(?m)^\s*group:\s*"1000000000000004"\s*$') {
            Add-LintError "Main-line chapter $chapterFile is not assigned to the main-line group."
        }
    }
}

# Milestone completion is counted, not asserted. A milestone is closed only when
# none of its plan items is PARTIAL or NOT_DONE; PARTIAL must say what is left.
$milestonePath = Join-Path $rootPath 'docs\registries\milestone_status.json'
$milestoneStatus = Read-JsonObject $milestonePath
if ($null -ne $milestoneStatus) {
    $allowedStatuses = @('DONE', 'PARTIAL', 'NOT_DONE', 'DEFERRED', 'OWNER')
    foreach ($milestone in @($milestoneStatus.milestones)) {
        $milestoneId = [string]$milestone.id
        $openCount = 0
        foreach ($item in @($milestone.items)) {
            $itemStatus = [string]$item.status
            if ($allowedStatuses -cnotcontains $itemStatus) {
                Add-LintError "Milestone $milestoneId has an unknown item status '$itemStatus'."
                continue
            }
            $hasNote = ($item.PSObject.Properties.Name -contains 'note_ru') -and
                       -not [string]::IsNullOrWhiteSpace([string]$item.note_ru)
            if ($itemStatus -ceq 'PARTIAL' -and -not $hasNote) {
                Add-LintError "Milestone $milestoneId has a PARTIAL item without saying what is left: $($item.item_ru)"
            }
            if ($itemStatus -ceq 'DEFERRED' -and -not $hasNote) {
                Add-LintError "Milestone $milestoneId has a DEFERRED item without naming the owner decision: $($item.item_ru)"
            }
            if ($itemStatus -ceq 'PARTIAL' -or $itemStatus -ceq 'NOT_DONE') { $openCount++ }
        }
        if ($openCount -gt 0) {
            Add-LintWarning "Milestone $milestoneId is NOT closed: $openCount of $(@($milestone.items).Count) plan items are still open."
        }
    }
}

# Keep the design corpus navigable. External URLs and in-page anchors are
# intentionally outside this filesystem-only check.
foreach ($markdownRootRelative in @('docs', 'authoring', 'threat_director', 'tools')) {
    $markdownRoot = Join-Path $rootPath $markdownRootRelative
    if (-not (Test-Path -LiteralPath $markdownRoot)) { continue }
    foreach ($markdownFile in Get-ChildItem -LiteralPath $markdownRoot -Recurse -File -Filter '*.md') {
        $markdownText = Get-Content -Raw -Encoding UTF8 -LiteralPath $markdownFile.FullName
        foreach ($link in [regex]::Matches($markdownText, '\[[^\]]*\]\(([^)]+)\)')) {
            $target = $link.Groups[1].Value.Trim()
            if ($target -match '^(?:https?://|mailto:|#)' -or $target -match '^<https?://') { continue }
            $target = (($target -split '#')[0]).Trim('"', '''', '<', '>')
            if ([string]::IsNullOrWhiteSpace($target)) { continue }
            $targetPath = [System.IO.Path]::GetFullPath((Join-Path $markdownFile.DirectoryName $target))
            if (-not $targetPath.StartsWith($rootPath, [System.StringComparison]::OrdinalIgnoreCase)) {
                Add-LintError "Markdown link escapes the instance root: $target ($($markdownFile.FullName))"
            }
            elseif (-not (Test-Path -LiteralPath $targetPath)) {
                Add-LintError "Broken local Markdown link: $target ($($markdownFile.FullName))"
            }
        }
    }
}

# Stable ID uniqueness and shape.
$stablePath = Join-Path $rootPath 'docs\registries\stable_ids.json'
$stable = Read-JsonObject $stablePath
$knownIds = [System.Collections.Generic.HashSet[string]]::new()
if ($null -ne $stable) {
    foreach ($property in $stable.ids.PSObject.Properties) {
        $value = [string]$property.Value
        if ($value -notmatch '^[0-9A-F]{16}$') { Add-LintError "Invalid 16-hex ID for $($property.Name): $value" }
        if (-not $knownIds.Add($value)) { Add-LintError "Duplicate engine ID: $value" }
    }
    foreach ($property in $stable.resource_ids.PSObject.Properties) {
        $value = [string]$property.Value
        if ($value -notmatch '^industrial_frontier:[a-z0-9_./-]+$') { Add-LintError "Invalid resource ID for $($property.Name): $value" }
    }
}

# Every 16-hex value used by authored quest SNBT must be registered.
$questRoot = Join-Path $rootPath 'config\ftbquests\quests'
if (-not (Test-Path -LiteralPath $questRoot)) {
    Add-LintError 'Missing config/ftbquests/quests.'
}
else {
    $questDataPath = Join-Path $questRoot 'data.snbt'
    if (-not (Test-Path -LiteralPath $questDataPath)) {
        Add-LintError 'Missing FTB Quests data.snbt.'
    }
    else {
        $questData = Get-Content -Raw -Encoding UTF8 -LiteralPath $questDataPath
        if ($questData -notmatch '(?m)^\s*version:\s*13\s*$') {
            Add-LintError 'FTB Quests 2001.4.22 expects quest data version 13.'
        }
    }
    $seenQuestIds = [System.Collections.Generic.HashSet[string]]::new()
    $declaredQuestIds = @{}
    foreach ($file in Get-ChildItem -LiteralPath $questRoot -Recurse -File -Filter '*.snbt') {
        $text = Get-Content -Raw -Encoding UTF8 -LiteralPath $file.FullName

        # Lightweight SNBT delimiter/string validation. This intentionally does
        # not evaluate NBT or load Minecraft classes.
        $stack = [System.Collections.Generic.Stack[char]]::new()
        $inString = $false
        $escapedCharacter = $false
        for ($index = 0; $index -lt $text.Length; $index++) {
            $character = $text[$index]
            if ($inString) {
                if ($escapedCharacter) { $escapedCharacter = $false; continue }
                if ($character -eq '\') { $escapedCharacter = $true; continue }
                if ($character -eq '"') { $inString = $false }
                continue
            }
            if ($character -eq '"') { $inString = $true; continue }
            if ($character -eq '{' -or $character -eq '[') { $stack.Push($character); continue }
            if ($character -eq '}' -or $character -eq ']') {
                if ($stack.Count -eq 0) {
                    Add-LintError "Unexpected closing delimiter in $($file.FullName) at character $index"
                    break
                }
                $opening = $stack.Pop()
                if (($opening -eq '{' -and $character -ne '}') -or ($opening -eq '[' -and $character -ne ']')) {
                    Add-LintError "Mismatched SNBT delimiter in $($file.FullName) at character $index"
                    break
                }
            }
        }
        if ($inString) { Add-LintError "Unterminated SNBT string in $($file.FullName)" }
        if ($stack.Count -gt 0) { Add-LintError "Unclosed SNBT delimiter in $($file.FullName)" }

        foreach ($match in [regex]::Matches($text, '"([0-9A-F]{16})"')) {
            $id = $match.Groups[1].Value
            [void]$seenQuestIds.Add($id)
            if (-not $knownIds.Contains($id)) { Add-LintError "Unregistered FTB ID $id in $($file.FullName)" }
        }
        foreach ($match in [regex]::Matches($text, '(?m)^\s*id:\s*"([0-9A-F]{16})"')) {
            $id = $match.Groups[1].Value
            if ($declaredQuestIds.ContainsKey($id)) {
                Add-LintError "Duplicate declared FTB ID $id in $($file.FullName) and $($declaredQuestIds[$id])"
            }
            else { $declaredQuestIds[$id] = $file.FullName }
        }
    }
    foreach ($id in $knownIds) {
        if (-not $seenQuestIds.Contains($id)) { Add-LintWarning "Stable ID is not compiled into current quest SNBT: $id" }
    }
}

# Author namespace language parity and all quest translation references.
$langRoot = Join-Path $rootPath 'config\paxi\resourcepacks\IndustrialFrontier-Core\assets\industrial_frontier\lang'
$ruPath = Join-Path $langRoot 'ru_ru.json'
$enPath = Join-Path $langRoot 'en_us.json'
$ru = Read-JsonObject $ruPath
$en = Read-JsonObject $enPath
$ruKeys = [System.Collections.Generic.HashSet[string]]::new()
$enKeys = [System.Collections.Generic.HashSet[string]]::new()
if ($null -ne $ru) { foreach ($property in $ru.PSObject.Properties) { [void]$ruKeys.Add($property.Name) } }
if ($null -ne $en) { foreach ($property in $en.PSObject.Properties) { [void]$enKeys.Add($property.Name) } }
foreach ($key in $ruKeys) { if (-not $enKeys.Contains($key)) { Add-LintError "ru_ru key has no separately authored en_us peer: $key" } }
foreach ($key in $enKeys) { if (-not $ruKeys.Contains($key)) { Add-LintError "en_us key has no ru_ru peer: $key" } }

if (Test-Path -LiteralPath $questRoot) {
    foreach ($file in Get-ChildItem -LiteralPath $questRoot -Recurse -File -Filter '*.snbt') {
        $text = Get-Content -Raw -Encoding UTF8 -LiteralPath $file.FullName
        foreach ($match in [regex]::Matches($text, '\{([a-z0-9_.-]+)\}')) {
            $key = $match.Groups[1].Value
            if (-not $ruKeys.Contains($key)) { Add-LintError "Quest translation key missing from ru_ru: $key ($($file.Name))" }
            if (-not $enKeys.Contains($key)) { Add-LintError "Quest translation key missing from en_us: $key ($($file.Name))" }
        }
    }
}

# Paxi pack metadata and the M1 tag contract.
foreach ($relative in @(
    'config\paxi\datapacks\IndustrialFrontier-Data\pack.mcmeta',
    'config\paxi\resourcepacks\IndustrialFrontier-Core\pack.mcmeta'
)) {
    $path = Join-Path $rootPath $relative
    $pack = Read-JsonObject $path
    if ($null -ne $pack -and [int]$pack.pack.pack_format -ne 15) {
        Add-LintError "$relative must use pack_format 15 for Minecraft 1.20.1."
    }
}
$tagPath = Join-Path $rootPath 'config\paxi\datapacks\IndustrialFrontier-Data\data\industrial_frontier\tags\items\materials\wood_logs.json'
if (-not (Test-Path -LiteralPath $tagPath)) { Add-LintError 'Missing Recast wood log tag.' }

# M2 pack tags are accepted-input aliases only. Pin their backing tag or exact
# fluid so a typo cannot silently empty an Academy task or material passport.
$m2TagContracts = @(
    @{ path = 'config\paxi\datapacks\IndustrialFrontier-Data\data\industrial_frontier\tags\items\materials\iron_ingots.json'; value = '#forge:ingots/iron' },
    @{ path = 'config\paxi\datapacks\IndustrialFrontier-Data\data\industrial_frontier\tags\items\materials\iron_nuggets.json'; value = '#forge:nuggets/iron' },
    @{ path = 'config\paxi\datapacks\IndustrialFrontier-Data\data\industrial_frontier\tags\items\materials\iron_plates.json'; value = '#forge:plates/iron' },
    @{ path = 'config\paxi\datapacks\IndustrialFrontier-Data\data\industrial_frontier\tags\items\materials\copper_ingots.json'; value = '#forge:ingots/copper' },
    @{ path = 'config\paxi\datapacks\IndustrialFrontier-Data\data\industrial_frontier\tags\items\materials\copper_plates.json'; value = '#forge:plates/copper' },
    @{ path = 'config\paxi\datapacks\IndustrialFrontier-Data\data\industrial_frontier\tags\items\materials\zinc_ingots.json'; value = '#forge:ingots/zinc' },
    @{ path = 'config\paxi\datapacks\IndustrialFrontier-Data\data\industrial_frontier\tags\items\materials\steel_ingots.json'; value = '#forge:ingots/steel' },
    @{ path = 'config\paxi\datapacks\IndustrialFrontier-Data\data\industrial_frontier\tags\items\materials\steel_plates.json'; value = '#forge:plates/steel' },
    @{ path = 'config\paxi\datapacks\IndustrialFrontier-Data\data\industrial_frontier\tags\items\materials\redstone_dusts.json'; value = '#forge:dusts/redstone' },
    @{ path = 'config\paxi\datapacks\IndustrialFrontier-Data\data\industrial_frontier\tags\items\materials\clay_balls.json'; value = 'minecraft:clay_ball' },
    @{ path = 'config\paxi\datapacks\IndustrialFrontier-Data\data\industrial_frontier\tags\fluids\materials\water.json'; value = 'minecraft:water' },
    @{ path = 'config\paxi\datapacks\IndustrialFrontier-Data\data\industrial_frontier\tags\fluids\materials\steam.json'; value = 'gtceu:steam' }
)
foreach ($contract in $m2TagContracts) {
    $contractPath = Join-Path $rootPath $contract.path
    if (-not (Test-Path -LiteralPath $contractPath -PathType Leaf)) {
        Add-LintError "Missing M2 material tag: $($contract.path)"
        continue
    }
    $tagObject = Read-JsonObject $contractPath
    if ($null -eq $tagObject) { continue }
    if ([bool]$tagObject.replace) { Add-LintError "M2 accepted-input tag must not replace upstream values: $($contract.path)" }
    if (@($tagObject.values) -notcontains [string]$contract.value) {
        Add-LintError "M2 material tag $($contract.path) does not include $($contract.value)"
    }
}

# The M2 Academy is an optional ten-card guide, not a progression or reward
# gate. Keep its source and compiled contract narrow until owner visual QA.
$m2QuestSourcePath = Join-Path $rootPath 'authoring\quests\70_material_passports.json'
$m2QuestSource = Read-JsonObject $m2QuestSourcePath
if ($null -ne $m2QuestSource) {
    if (-not [bool]$m2QuestSource.optional) { Add-LintError 'M2 material-passport chapter must remain optional.' }
    if (@($m2QuestSource.quests).Count -ne 10) { Add-LintError 'M2 material-passport source must contain exactly 10 quests.' }
}
$m2QuestChapterPath = Join-Path $questRoot 'chapters\70_material_passports.snbt'
if (-not (Test-Path -LiteralPath $m2QuestChapterPath -PathType Leaf)) {
    Add-LintError 'Missing compiled M2 material-passport chapter.'
}
else {
    $m2QuestChapterText = Get-Content -Raw -Encoding UTF8 -LiteralPath $m2QuestChapterPath
    $m2OptionalCount = [regex]::Matches($m2QuestChapterText, '(?m)^\s*optional:\s*true\s*$').Count
    if ($m2OptionalCount -ne 10) { Add-LintError "All 10 M2 Academy quests must be optional; found $m2OptionalCount." }
    if ($m2QuestChapterText -match '(?m)^\s*rewards\s*:') { Add-LintError 'M2 Academy must not contain rewards.' }
    if ($m2QuestChapterText -match '(?i)tech_epoch|scoreboard') { Add-LintError 'M2 Academy must not mutate or instruct mutation of authoritative progression state.' }
}

# Translated GuideME headings need stable English fragment anchors because
# cross-page links keep their original file/fragment targets.
$guideAnchorRegistryPath = Join-Path $rootPath 'docs\registries\guideme_required_anchors.json'
$guideAnchorRegistry = Read-JsonObject $guideAnchorRegistryPath
if ($null -ne $guideAnchorRegistry) {
    $translatedGuideRoot = Join-Path $rootPath 'config\paxi\resourcepacks\IndustrialFrontier-Core\assets\ae2\ae2guide\_ru_ru'
    foreach ($page in @($guideAnchorRegistry.pages)) {
        $pagePath = Join-Path $translatedGuideRoot (([string]$page.path) -replace '/', '\')
        if (-not (Test-Path -LiteralPath $pagePath -PathType Leaf)) { continue }
        $pageText = Get-Content -Raw -Encoding UTF8 -LiteralPath $pagePath
        foreach ($anchor in @($page.anchors)) {
            $escapedAnchor = [regex]::Escape([string]$anchor)
            if ($pageText -notmatch ('<a\s+name\s*=\s*["'']{0}["'']\s*/?>' -f $escapedAnchor)) {
                Add-LintError "Translated GuideME page $($page.path) is missing stable anchor: $anchor"
            }
        }
    }
}

$guideCorrectionRegistryPath = Join-Path $rootPath 'docs\registries\guideme_content_corrections.json'
$guideCorrectionRegistry = Read-JsonObject $guideCorrectionRegistryPath
if ($null -ne $guideCorrectionRegistry) {
    $correctionIds = [System.Collections.Generic.HashSet[string]]::new()
    foreach ($correction in @($guideCorrectionRegistry.entries)) {
        $correctionId = [string]$correction.id
        if ($correctionId -notmatch '^[a-z0-9_.-]+$') { Add-LintError "Invalid GuideME content-correction ID: $correctionId" }
        elseif (-not $correctionIds.Add($correctionId)) { Add-LintError "Duplicate GuideME content-correction ID: $correctionId" }
        if ([string]$correction.page -notmatch '^[a-z0-9_./-]+\.md$') { Add-LintError "Invalid GuideME correction page for $correctionId" }
        if ([string]::IsNullOrWhiteSpace([string]$correction.source_contains) -or [string]::IsNullOrWhiteSpace([string]$correction.ru_contains)) {
            Add-LintError "GuideME correction $correctionId must pin source_contains and ru_contains."
        }
        $hasNumericSource = $null -ne $correction.numeric_source
        $hasNumericRussian = $null -ne $correction.numeric_ru
        if ($hasNumericSource -ne $hasNumericRussian) { Add-LintError "GuideME correction $correctionId must define both numeric_source and numeric_ru or neither." }
    }
}

# Required and forbidden JARs for the current M1/M2 baseline.
$requiredJars = @(
    'citadel-2.6.3-1.20.1.jar',
    'jei-1.20.1-forge-15.20.0.134.jar',
    'ftb-library-forge-2001.2.13.jar',
    'ftb-teams-forge-2001.3.2.jar',
    'ftb-quests-forge-2001.4.22.jar',
    'ftb-xmod-compat-forge-2.1.3.jar',
    'ftb-filter-system-forge-20.0.1.jar',
    'questsadditions-1.4.7.jar',
    'kubejs-create-forge-2001.3.0-build.8.jar',
    'lootjs-forge-1.20.1-2.13.1.jar',
    'bettercombat-forge-1.9.0+1.20.1.jar',
    'epic-knights-1.20.1-forge-10.11.jar',
    'tacz-1.20.1-1.1.8-hotfix.jar',
    'cloth-config-11.1.136-forge.jar',
    'player-animation-lib-forge-1.0.2-rc1+1.20.jar',
    'FarmersDelight-1.20.1-1.3.2.jar',
    'Paxi-1.20-Forge-4.0.jar'
)
$modsPath = Join-Path $rootPath 'mods'
foreach ($name in $requiredJars) {
    if (-not (Test-Path -LiteralPath (Join-Path $modsPath $name) -PathType Leaf)) { Add-LintError "Missing required M1/M2 baseline JAR: $name" }
}
if (Test-Path -LiteralPath (Join-Path $modsPath 'jei-1.20.1-forge-15.20.0.112.jar')) {
    Add-LintError 'Old JEI 15.20.0.112 is still active beside the M0 replacement.'
}
foreach ($jar in Get-ChildItem -LiteralPath $modsPath -File -Filter '*.jar') {
    if ($jar.Name -match '(?i)mekanism|industrialforegoing|industrial-foregoing|ftb.?quests.?optimizer|almost.?unified') {
        Add-LintError "Forbidden or gated JAR is active in the M1/M2 baseline: $($jar.Name)"
    }
}

# Freeze Create worldgen ownership.
$createConfigPath = Join-Path $rootPath 'config\create-common.toml'
$createConfig = Get-Content -Raw -Encoding UTF8 -LiteralPath $createConfigPath
if ($createConfig -notmatch '(?m)^\s*disableWorldGen\s*=\s*true\s*$') {
    Add-LintError 'Create worldgen must be disabled while GTCEu owns ore generation.'
}

# Freeze the installed M2 geology and energy constitution. These checks are
# textual by design and therefore do not claim runtime transfer behaviour.
$gtConfigPath = Join-Path $rootPath 'config\gtceu.yaml'
$gtConfig = Get-Content -Raw -Encoding UTF8 -LiteralPath $gtConfigPath
foreach ($requiredSetting in @(
    @{ pattern = '(?m)^\s*removeVanillaOreGen:\s*true\s*$'; message = 'GTCEu must remove vanilla ore generation in M2.' },
    @{ pattern = '(?m)^\s*removeVanillaLargeOreVeins:\s*true\s*$'; message = 'GTCEu must remove vanilla large ore veins in M2.' },
    @{ pattern = '(?m)^\s*nativeEUToFE:\s*true\s*$'; message = 'M2 pins the one-way native EU-to-FE compatibility output pending owner test.' },
    @{ pattern = '(?m)^\s*enableFEConverters:\s*false\s*$'; message = 'Bidirectional GTCEu FE converters must remain disabled in M2.' }
)) {
    if ($gtConfig -notmatch $requiredSetting.pattern) { Add-LintError $requiredSetting.message }
}

$m2ProcessOwnershipPath = Join-Path $rootPath 'kubejs\server_scripts\30_integrations\m2_process_ownership.js'
if (-not (Test-Path -LiteralPath $m2ProcessOwnershipPath -PathType Leaf)) {
    Add-LintError 'Missing M2 Create process-ownership script.'
}
else {
    $m2ProcessText = Get-Content -Raw -Encoding UTF8 -LiteralPath $m2ProcessOwnershipPath
    foreach ($requiredToken in @(
        'create:crushing/tuff',
        'create:crushing/tuff_recycling',
        'create:splashing/crushed_raw_iron',
        'create:mixing/brass_ingot',
        '3x #forge:ingots/copper',
        '#forge:ingots/zinc',
        '4x gtceu:brass_ingot',
        'industrial_frontier:m2/create/brass_from_copper_zinc'
    )) {
        if (-not $m2ProcessText.Contains($requiredToken)) { Add-LintError "M2 process-ownership script is missing safety anchor: $requiredToken" }
    }
}

$m2Ae2GatePath = Join-Path $rootPath 'kubejs\server_scripts\10_progression\m2_ae2_epoch_gate.js'
if (-not (Test-Path -LiteralPath $m2Ae2GatePath -PathType Leaf)) {
    Add-LintError 'Missing M2 AE2 epoch-gate script.'
}
else {
    $m2Ae2GateText = Get-Content -Raw -Encoding UTF8 -LiteralPath $m2Ae2GatePath
    foreach ($requiredRecipe in @(
        'ae2:network/blocks/crystal_processing_charger',
        'ae2:network/blocks/inscribers',
        'ae2:network/blocks/energy_energy_acceptor',
        'ae2:transform/fluix_crystals',
        'ae2:inscriber/calculation_processor',
        'ae2:inscriber/engineering_processor',
        'ae2:inscriber/logic_processor'
    )) {
        if (-not $m2Ae2GateText.Contains($requiredRecipe)) { Add-LintError "M2 AE2 gate is missing vendor root: $requiredRecipe" }
    }
}

# Validate JavaScript syntax without running Minecraft or evaluating scripts.
if ([string]::IsNullOrWhiteSpace($NodePath)) {
    $node = Get-Command node -ErrorAction SilentlyContinue
    if ($null -ne $node) { $NodePath = $node.Source }
}
if ([string]::IsNullOrWhiteSpace($NodePath) -or -not (Test-Path -LiteralPath $NodePath -PathType Leaf)) {
    Add-LintWarning 'Node.js was not found; JavaScript syntax check was skipped.'
}
else {
    $scriptRoot = Join-Path $rootPath 'kubejs'
    foreach ($file in Get-ChildItem -LiteralPath $scriptRoot -Recurse -File -Filter '*.js') {
        $output = & $NodePath --check $file.FullName 2>&1
        if ($LASTEXITCODE -ne 0) { Add-LintError "JavaScript syntax error in $($file.FullName): $($output -join ' ')" }
    }
}

# Recipe and Ponder resource IDs declared in active scripts must be registered.
if ($null -ne $stable) {
    $knownResourceIds = [System.Collections.Generic.HashSet[string]]::new()
    foreach ($property in $stable.resource_ids.PSObject.Properties) { [void]$knownResourceIds.Add([string]$property.Value) }
    foreach ($file in Get-ChildItem -LiteralPath (Join-Path $rootPath 'kubejs') -Recurse -File -Filter '*.js') {
        $text = Get-Content -Raw -Encoding UTF8 -LiteralPath $file.FullName
        $resourcePattern = '(?:\.id|\.scene)\(\s*[''"](industrial_frontier:[a-z0-9_./-]+)[''"]'
        foreach ($match in [regex]::Matches($text, $resourcePattern)) {
            $id = $match.Groups[1].Value
            if (-not $knownResourceIds.Contains($id)) { Add-LintError "Unregistered active script resource ID $id in $($file.FullName)" }
        }
    }
}

# Dynamically placed Ponder blocks above the base plate must be revealed.
foreach ($ponderRelative in @(
    'kubejs\client_scripts\10_ponder\m1_batch_processing.js',
    'kubejs\client_scripts\10_ponder\m3_mechanical_stress.js'
)) {
    $ponderPath = Join-Path $rootPath $ponderRelative
    if (-not (Test-Path -LiteralPath $ponderPath)) { continue }
    $ponderText = Get-Content -Raw -Encoding UTF8 -LiteralPath $ponderPath
    if ($ponderText -notmatch 'scene\.(?:showStructure|world\.showSection)\s*\(') {
        Add-LintError "Ponder scene places blocks but never reveals its structure/sections: $ponderRelative"
    }
}

# The quest book must open gradually.
#
# Eighteen chapters and a hundred and seventy-eight quests visible from the
# first minute is not guidance, it is a wall: a player who has not mined stone
# yet could read the reactor chapter and both endings. Chapters are chained so
# the next one appears only once the previous is finished, and this check makes
# sure the chain is not silently broken by an edit.
$chapterRoot = Join-Path $rootPath 'config\ftbquests\quests\chapters'
$questDataFile = Join-Path $rootPath 'config\ftbquests\quests\data.snbt'
if ((Test-Path -LiteralPath $chapterRoot) -and (Test-Path -LiteralPath $questDataFile)) {
    $questDataText = Get-Content -Raw -Encoding UTF8 -LiteralPath $questDataFile
    if ($questDataText -notmatch 'hide_excluded_quests:\s*true') {
        Add-LintError 'Quest book shows quests that are locked out by dependencies (hide_excluded_quests is not true).'
    }

    # These two are entry and reference material: they are always available.
    $alwaysOpenChapters = @('00_start_here', '90_help')

    foreach ($chapterFile in @(Get-ChildItem -LiteralPath $chapterRoot -Filter '*.snbt' -File)) {
        $chapterName = [System.IO.Path]::GetFileNameWithoutExtension($chapterFile.Name)
        $chapterText = Get-Content -Raw -Encoding UTF8 -LiteralPath $chapterFile.FullName

        if ($alwaysOpenChapters -contains $chapterName) {
            if ($chapterText -match 'hide_until_deps_complete') {
                Add-LintError "Chapter $chapterName must stay open but is gated."
            }
            continue
        }

        if ($chapterText -notmatch 'hide_quest_until_deps_visible:\s*true') {
            Add-LintError "Chapter $chapterName does not hide its quests until the previous chapter is reached."
        }
        if ($chapterText -notmatch 'hide_until_deps_complete:\s*true') {
            Add-LintError "Chapter $chapterName has no opening gate - it would be visible from the first minute."
        }

        # The gate must point at a quest that lives in another chapter,
        # otherwise the chapter gates itself and never opens.
        $ownQuestIds = [regex]::Matches($chapterText, '(?m)^\t\t\tid: "(3\d{15})"') | ForEach-Object { $_.Groups[1].Value }
        $externalFound = $false
        foreach ($dependencyBlock in [regex]::Matches($chapterText, '(?s)dependencies: \[(.*?)\]')) {
            foreach ($reference in [regex]::Matches($dependencyBlock.Groups[1].Value, '"(3\d{15})"')) {
                if ($ownQuestIds -notcontains $reference.Groups[1].Value) { $externalFound = $true }
            }
        }
        if (-not $externalFound) {
            Add-LintError "Chapter $chapterName is gated but depends on nothing outside itself - it can never open."
        }
    }
}

# Top-level names must be unique across each script pack.
#
# KubeJS gives every script pack one shared scope, so two files declaring the
# same top-level const or function is not shadowing but a redeclaration error
# that kills the whole pack. It is silent in the editor and fatal in game, so
# it is checked here.
foreach ($packName in @('server_scripts', 'startup_scripts', 'client_scripts')) {
    $packPath = Join-Path $rootPath "kubejs\$packName"
    if (-not (Test-Path -LiteralPath $packPath)) { continue }

    $declarationOwners = @{}
    foreach ($scriptFile in @(Get-ChildItem -LiteralPath $packPath -Filter '*.js' -Recurse -File)) {
        $scriptText = Get-Content -Raw -Encoding UTF8 -LiteralPath $scriptFile.FullName
        foreach ($match in [regex]::Matches($scriptText, '(?m)^(?:const|let|var|function)\s+([A-Za-z_$][A-Za-z0-9_$]*)')) {
            $declaredName = $match.Groups[1].Value
            if ($declarationOwners.ContainsKey($declaredName)) {
                $previousOwner = $declarationOwners[$declaredName]
                if ($previousOwner -ne $scriptFile.Name) {
                    Add-LintError "Duplicate top-level name '$declaredName' in $packName ($previousOwner and $($scriptFile.Name)) - KubeJS shares one scope per pack."
                }
            }
            else {
                $declarationOwners[$declaredName] = $scriptFile.Name
            }
        }
    }
}

# The faction module must agree with the registries it claims to follow.
$factionDataRelative = 'kubejs\server_scripts\40_balance\m85_factions_1_data.js'
$factionDataPath = Join-Path $rootPath $factionDataRelative
$threatCorePath = Join-Path $rootPath 'kubejs\server_scripts\40_balance\m3_threat_director.js'
if ((Test-Path -LiteralPath $factionDataPath) -and (Test-Path -LiteralPath $threatCorePath)) {
    $factionDataText = Get-Content -Raw -Encoding UTF8 -LiteralPath $factionDataPath
    $threatCoreText = Get-Content -Raw -Encoding UTF8 -LiteralPath $threatCorePath

    # The faction order feeds scoreboard mirrors if_rep_01..06, so the module
    # and the Threat Director core must list them identically.
    $moduleOrder = ''
    if ($factionDataText -match "IF_FACTION_LIST\s*=\s*\[([^\]]+)\]") {
        $moduleOrder = ($Matches[1] -replace "[\s'`"]", '')
    }
    $coreOrder = ''
    if ($threatCoreText -match "IF_FACTIONS\s*=\s*\[([^\]]+)\]") {
        $coreOrder = ($Matches[1] -replace "[\s'`"]", '')
    }
    if (-not $moduleOrder -or -not $coreOrder) {
        Add-LintError 'Could not read the faction order from the faction module or the Threat Director core.'
    }
    elseif ($moduleOrder -ne $coreOrder) {
        Add-LintError "Faction order differs between the module and the Threat Director core: '$moduleOrder' vs '$coreOrder'."
    }

    # Dialogue buttons are gated by scoreboard thresholds baked into the NPC
    # presets, while the command that signs the treaty checks the module table.
    # If the two disagree the player gets a button that always refuses, so the
    # generator and the module are compared here.
    $npcGeneratorPath = Join-Path $rootPath 'tools\generate_faction_npc.py'
    if (Test-Path -LiteralPath $npcGeneratorPath) {
        $npcGeneratorText = Get-Content -Raw -Encoding UTF8 -LiteralPath $npcGeneratorPath
        foreach ($treatyMatch in [regex]::Matches($npcGeneratorText, '"id":\s*"([a-z_]+)",\s*"ru":\s*"[^"]*",\s*"min_reputation":\s*(-?\d+),\s*"min_epoch":\s*(\d+)')) {
            $treatyId = $treatyMatch.Groups[1].Value
            $generatorReputation = [int]$treatyMatch.Groups[2].Value
            $generatorEpoch = [int]$treatyMatch.Groups[3].Value

            $modulePattern = "(?s)\b$treatyId\s*:\s*\{.*?min_reputation:\s*(-?\d+),\s*min_epoch:\s*(\d+)"
            if ($factionDataText -match $modulePattern) {
                if ([int]$Matches[1] -ne $generatorReputation -or [int]$Matches[2] -ne $generatorEpoch) {
                    Add-LintError "Treaty '$treatyId' thresholds differ: presets say $generatorReputation/$generatorEpoch, module says $($Matches[1])/$($Matches[2])."
                }
            }
            else {
                Add-LintError "Treaty '$treatyId' is offered by the NPC presets but missing from the faction module."
            }
        }

        # Every faction must have a generated envoy preset, otherwise its base
        # would place a spokesman that does not exist.
        foreach ($factionId in @($moduleOrder -split ',')) {
            if (-not $factionId) { continue }
            $presetPath = Join-Path $rootPath "kubejs\data\industrial_frontier\preset\$factionId`_envoy.npc.snbt"
            if (-not (Test-Path -LiteralPath $presetPath -PathType Leaf)) {
                Add-LintError "Faction '$factionId' has no generated envoy preset - run tools/generate_faction_npc.py."
            }
        }
    }

    # Base tier epoch ceilings are owned by the Threat Director definitions.
    $baseDefinitionPath = Join-Path $rootPath 'threat_director\definitions\bases.json'
    if (Test-Path -LiteralPath $baseDefinitionPath) {
        $baseDefinitions = Get-Content -Raw -Encoding UTF8 -LiteralPath $baseDefinitionPath | ConvertFrom-Json
        foreach ($level in @($baseDefinitions.levels)) {
            $tierId = ($level.base_id -split '/')[-1]
            $pattern = "id:\s*'$tierId'\s*,\s*ru:\s*'[^']*'\s*,\s*max_epoch:\s*(\d+)"
            if ($factionDataText -match $pattern) {
                if ([int]$Matches[1] -ne [int]$level.max_epoch) {
                    Add-LintError "Base $tierId epoch ceiling is $($Matches[1]) in the faction module but $($level.max_epoch) in the definitions."
                }
            }
            else {
                Add-LintError "Base $tierId from the definitions is missing in the faction module."
            }
        }
    }
}

# Commands promised to the player must exist under the promised name.
#
# Every pack command is declared with ServerEvents.customCommand, which in game
# is only reachable through "/kubejs custom_command <id>". The short "/if_..."
# form the quest book and the test protocols promise is created by the bridge
# in kubejs/server_scripts/00_core/if_commands.js. If a command is added and the
# bridge is not updated, the promise silently breaks, so the two sets are
# compared here.
$commandBridgeRelative = 'kubejs\server_scripts\00_core\if_commands.js'
$commandBridgePath = Join-Path $rootPath $commandBridgeRelative
if (-not (Test-Path -LiteralPath $commandBridgePath -PathType Leaf)) {
    Add-LintError "Missing command bridge: $commandBridgeRelative"
}
else {
    $serverScriptRoot = Join-Path $rootPath 'kubejs\server_scripts'
    $declaredCommands = [System.Collections.Generic.HashSet[string]]::new()
    foreach ($scriptFile in @(Get-ChildItem -LiteralPath $serverScriptRoot -Filter '*.js' -Recurse -File)) {
        $scriptText = Get-Content -Raw -Encoding UTF8 -LiteralPath $scriptFile.FullName
        foreach ($match in [regex]::Matches($scriptText, "customCommand\(\s*'([a-z0-9_]+)'")) {
            [void]$declaredCommands.Add($match.Groups[1].Value)
        }
    }

    $bridgeText = Get-Content -Raw -Encoding UTF8 -LiteralPath $commandBridgePath
    $bridgedCommands = [System.Collections.Generic.HashSet[string]]::new()
    foreach ($match in [regex]::Matches($bridgeText, "'(if_[a-z0-9_]+)'")) {
        [void]$bridgedCommands.Add($match.Groups[1].Value)
    }

    foreach ($declared in @($declaredCommands)) {
        if (-not $bridgedCommands.Contains($declared)) {
            Add-LintError "Command /$declared has a handler but is not registered under its own name in the bridge."
        }
    }
    foreach ($bridged in @($bridgedCommands)) {
        if (-not $declaredCommands.Contains($bridged)) {
            Add-LintError "Bridge registers /$bridged but no handler declares it."
        }
    }

    # The bridge must use the real command registry; delegating through another
    # customCommand would recreate the very problem it exists to solve.
    if ($bridgeText -notmatch 'ServerEvents\.commandRegistry') {
        Add-LintError 'Command bridge does not use ServerEvents.commandRegistry.'
    }
}

# Run the M2 cross-registry validator in a separate PowerShell process so its
# exit code cannot terminate this lint process. This remains a static file
# check and never loads Forge or Minecraft.
$m2ValidatorPath = Join-Path $rootPath 'tools\validate_m2_architecture.ps1'
if (-not (Test-Path -LiteralPath $m2ValidatorPath -PathType Leaf)) {
    Add-LintError 'Missing M2 architecture validator.'
}
else {
    $powerShellExecutable = Join-Path $PSHOME 'powershell.exe'
    $m2ValidatorOutput = & $powerShellExecutable -NoProfile -ExecutionPolicy Bypass -File $m2ValidatorPath -Root $rootPath 2>&1
    $m2ValidatorExitCode = $LASTEXITCODE
    foreach ($line in @($m2ValidatorOutput)) {
        $lineText = [string]$line
        if ($lineText -match '^WARN:\s*(.+)$') { Add-LintWarning "M2 validator: $($Matches[1])" }
        if ($lineText -match '^ERROR:\s*(.+)$') { Add-LintError "M2 validator: $($Matches[1])" }
    }
    if ($m2ValidatorExitCode -ne 0 -and -not (@($m2ValidatorOutput) -match '^ERROR:')) {
        Add-LintError "M2 architecture validator exited with code $m2ValidatorExitCode."
    }
}

# M9 has its own asset and screen contract. Run it out-of-process for the same
# reason as M2: a validator failure must become a lint error instead of ending
# this process before the consolidated report is printed. This remains a
# static check and never loads Forge or Minecraft.
$m9ValidatorPath = Join-Path $rootPath 'tools\validate_m9_visuals.ps1'
if (-not (Test-Path -LiteralPath $m9ValidatorPath -PathType Leaf)) {
    Add-LintError 'Missing M9 visual-system validator.'
}
else {
    $powerShellExecutable = Join-Path $PSHOME 'powershell.exe'
    $m9ValidatorOutput = & $powerShellExecutable -NoProfile -ExecutionPolicy Bypass -File $m9ValidatorPath -Root $rootPath 2>&1
    $m9ValidatorExitCode = $LASTEXITCODE
    foreach ($line in @($m9ValidatorOutput)) {
        $lineText = [string]$line
        if ($lineText -match '^\[M9\]\[WARN\]\s*(.+)$') { Add-LintWarning "M9 validator: $($Matches[1])" }
        if ($lineText -match '^\[M9\]\[ERROR\]\s*(.+)$') { Add-LintError "M9 validator: $($Matches[1])" }
    }
    if ($m9ValidatorExitCode -ne 0 -and -not (@($m9ValidatorOutput) -match '^\[M9\]\[ERROR\]')) {
        Add-LintError "M9 visual-system validator exited with code $m9ValidatorExitCode."
    }
}

# The v2 title-menu contract is narrower than the complete M9 visual atlas. It
# verifies cursor parallax, overscan, button states and the replacement logo
# and icon without reading localization files or launching the game.
$menuValidatorPath = Join-Path $rootPath 'tools\validate_menu_visuals.ps1'
if (-not (Test-Path -LiteralPath $menuValidatorPath -PathType Leaf)) {
    Add-LintError 'Missing Recast v2 menu validator.'
}
else {
    $powerShellExecutable = Join-Path $PSHOME 'powershell.exe'
    $menuValidatorOutput = & $powerShellExecutable -NoProfile -ExecutionPolicy Bypass -File $menuValidatorPath -Root $rootPath 2>&1
    $menuValidatorExitCode = $LASTEXITCODE
    foreach ($line in @($menuValidatorOutput)) {
        $lineText = [string]$line
        if ($lineText -match '^\[MENU\]\[WARN\]\s*(.+)$') { Add-LintWarning "Menu validator: $($Matches[1])" }
        if ($lineText -match '^\[MENU\]\[ERROR\]\s*(.+)$') { Add-LintError "Menu validator: $($Matches[1])" }
    }
    if ($menuValidatorExitCode -ne 0 -and -not (@($menuValidatorOutput) -match '^\[MENU\]\[ERROR\]')) {
        Add-LintError "Menu validator exited with code $menuValidatorExitCode."
    }
}

# M10 owns release-readiness truth rather than pretending that static success
# proves runtime readiness. It validates the exact manifest/source/hash lock,
# hash-current progression report, release allowlist, licence inventory,
# milestone counts and quest structure. Translation sources are deliberately
# excluded because that work is an external parallel stream in this build.
$m10ValidatorPath = Join-Path $rootPath 'tools\validate_m10_release.ps1'
if (-not (Test-Path -LiteralPath $m10ValidatorPath -PathType Leaf)) {
    Add-LintError 'Missing M10 release-readiness validator.'
}
else {
    $powerShellExecutable = Join-Path $PSHOME 'powershell.exe'
    $m10ValidatorOutput = & $powerShellExecutable -NoProfile -ExecutionPolicy Bypass -File $m10ValidatorPath -Root $rootPath 2>&1
    $m10ValidatorExitCode = $LASTEXITCODE
    foreach ($line in @($m10ValidatorOutput)) {
        $lineText = [string]$line
        if ($lineText -match '^\[M10\]\[WARN\]\s*(.+)$') { Add-LintWarning "M10 validator: $($Matches[1])" }
        if ($lineText -match '^\[M10\]\[ERROR\]\s*(.+)$') { Add-LintError "M10 validator: $($Matches[1])" }
    }
    if ($m10ValidatorExitCode -ne 0 -and -not (@($m10ValidatorOutput) -match '^\[M10\]\[ERROR\]')) {
        Add-LintError "M10 release-readiness validator exited with code $m10ValidatorExitCode."
    }
}

Write-Output "Errors: $($errors.Count)"
foreach ($message in $errors) { Write-Output "ERROR: $message" }
Write-Output "Warnings: $($warnings.Count)"
foreach ($message in $warnings) { Write-Output "WARN: $message" }
Write-Output 'Minecraft was not launched.'

if ($errors.Count -gt 0) { exit 2 }
exit 0
