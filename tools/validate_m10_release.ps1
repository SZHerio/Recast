[CmdletBinding()]
param(
    [string]$Root = '',
    [switch]$Quiet
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if ([string]::IsNullOrWhiteSpace($Root)) {
    $Root = Split-Path -Parent $PSScriptRoot
}
$rootPath = (Resolve-Path -LiteralPath $Root).Path
$errors = [System.Collections.Generic.List[string]]::new()
$warnings = [System.Collections.Generic.List[string]]::new()
$passes = [System.Collections.Generic.List[string]]::new()

function Add-M10Error { param([string]$Message) $script:errors.Add($Message) }
function Add-M10Warning { param([string]$Message) $script:warnings.Add($Message) }
function Add-M10Pass { param([string]$Message) $script:passes.Add($Message) }

function Test-HasProperty {
    param([object]$Object, [string]$Name)
    return $null -ne $Object -and $null -ne $Object.PSObject.Properties[$Name]
}

function Get-M10IntProperty {
    param([object]$Object, [string]$Name)
    if (-not (Test-HasProperty $Object $Name)) { return 0 }
    return [int]$Object.PSObject.Properties[$Name].Value
}

function Resolve-M10Path {
    param([string]$RelativePath)
    if ([string]::IsNullOrWhiteSpace($RelativePath)) { throw 'Path is empty.' }
    if ([System.IO.Path]::IsPathRooted($RelativePath)) { throw "Path must be relative: $RelativePath" }
    if ($RelativePath -match '(^|[\/])\.\.([\/]|$)') { throw "Path traversal is forbidden: $RelativePath" }
    $candidate = [System.IO.Path]::GetFullPath((Join-Path $rootPath ($RelativePath -replace '/', '\')))
    $prefix = $rootPath.TrimEnd('\', '/') + [System.IO.Path]::DirectorySeparatorChar
    if (-not $candidate.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Path escapes instance root: $RelativePath"
    }
    return $candidate
}

function Read-M10Json {
    param([string]$RelativePath, [string]$Label)
    try {
        $path = Resolve-M10Path $RelativePath
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
            Add-M10Error "$Label is missing: $RelativePath"
            return $null
        }
        $raw = Get-Content -Raw -Encoding UTF8 -LiteralPath $path
        $value = $raw | ConvertFrom-Json
        return [pscustomobject]@{ Path = $path; Raw = $raw; Value = $value }
    }
    catch {
        Add-M10Error "$Label is not valid JSON: $RelativePath ($($_.Exception.Message))"
        return $null
    }
}

function Assert-PathExists {
    param([string]$RelativePath, [string]$Label, [switch]$Directory)
    try {
        $path = Resolve-M10Path $RelativePath
        $pathType = if ($Directory) { 'Container' } else { 'Leaf' }
        if (-not (Test-Path -LiteralPath $path -PathType $pathType)) {
            Add-M10Error "$Label is missing: $RelativePath"
            return $false
        }
        return $true
    }
    catch {
        Add-M10Error "$Label has an invalid path '$RelativePath': $($_.Exception.Message)"
        return $false
    }
}

function Assert-Unique {
    param([object[]]$Values, [string]$Label)
    $duplicates = @($Values | ForEach-Object { [string]$_ } | Group-Object | Where-Object Count -gt 1)
    if ($duplicates.Count -gt 0) {
        Add-M10Error "$Label contains duplicates: $($duplicates.Name -join ', ')"
    }
}

$schemaDoc = Read-M10Json 'authoring/schemas/m10_release_readiness.schema.json' 'M10 schema'
$readinessDoc = Read-M10Json 'docs/registries/m10_release_readiness.json' 'M10 readiness ledger'
$releaseFilesDoc = Read-M10Json 'docs/registries/m10_release_files.json' 'M10 release-file contract'
$manifestDoc = Read-M10Json 'manifest.json' 'CurseForge manifest'
$instanceDoc = Read-M10Json 'minecraftinstance.json' 'CurseForge instance metadata'
$sourcesDoc = Read-M10Json 'docs/registries/curseforge_sources.json' 'Exact-file source registry'
$milestonesDoc = Read-M10Json 'docs/registries/milestone_status.json' 'Milestone ledger'
$lockDoc = Read-M10Json 'docs/registries/generated/IF-M10-0001/mod_manifest_lock.json' 'M10 mod lock'
$dependencyDoc = Read-M10Json 'docs/registries/generated/IF-M10-0001/dependency_audit.json' 'M10 dependency audit'
$licenseDoc = Read-M10Json 'docs/registries/generated/IF-M10-0001/license_inventory.json' 'M10 license inventory'
$progressionDoc = Read-M10Json 'docs/registries/generated/IF-M10-0001/progression_grind_audit.json' 'M10 progression/grind audit'

$loadedDocuments = @($schemaDoc, $readinessDoc, $releaseFilesDoc, $manifestDoc, $instanceDoc, $sourcesDoc, $milestonesDoc, $lockDoc, $dependencyDoc, $licenseDoc, $progressionDoc)
if (@($loadedDocuments | Where-Object { $null -eq $_ }).Count -gt 0) {
    foreach ($message in $errors) { Write-Output "[M10][ERROR] $message" }
    Write-Output '[M10] Minecraft/Forge was not launched.'
    exit 1
}

$readiness = $readinessDoc.Value
$releaseFiles = $releaseFilesDoc.Value
$manifest = $manifestDoc.Value
$instance = $instanceDoc.Value
$sources = $sourcesDoc.Value
$milestones = $milestonesDoc.Value
$lock = $lockDoc.Value
$dependency = $dependencyDoc.Value
$license = $licenseDoc.Value
$progression = $progressionDoc.Value

# Full JSON Schema validation is used when available; the explicit checks below
# remain authoritative on Windows PowerShell versions without Test-Json.
$testJson = Get-Command -Name 'Test-Json' -ErrorAction SilentlyContinue
if ($null -ne $testJson) {
    try {
        if (-not (Test-Json -Json $readinessDoc.Raw -SchemaFile $schemaDoc.Path -ErrorAction Stop)) {
            Add-M10Error 'Readiness ledger failed JSON Schema validation.'
        }
        else { Add-M10Pass 'Readiness ledger passed JSON Schema validation.' }
    }
    catch { Add-M10Error "Readiness JSON Schema validation failed: $($_.Exception.Message)" }
}

$expectedGateIds = 1..14 | ForEach-Object { 'M10-{0:D2}' -f $_ }
$gates = @($readiness.gates)
Assert-Unique @($gates | ForEach-Object { $_.id }) 'M10 gate IDs'
if ($gates.Count -ne 14) { Add-M10Error "M10 readiness ledger must contain 14 gates, found $($gates.Count)." }
$actualGateIds = @($gates | ForEach-Object { [string]$_.id } | Sort-Object)
$missingGateIds = @($expectedGateIds | Where-Object { $actualGateIds -notcontains $_ })
$extraGateIds = @($actualGateIds | Where-Object { $expectedGateIds -notcontains $_ })
if ($missingGateIds.Count -gt 0) { Add-M10Error "Missing M10 gate IDs: $($missingGateIds -join ', ')" }
if ($extraGateIds.Count -gt 0) { Add-M10Error "Unexpected M10 gate IDs: $($extraGateIds -join ', ')" }

$allowedStatuses = @('DONE', 'PARTIAL', 'NOT_DONE', 'DEFERRED', 'OWNER')
foreach ($gate in $gates) {
    if ($allowedStatuses -notcontains [string]$gate.status) {
        Add-M10Error "Gate $($gate.id) has invalid status '$($gate.status)'."
    }
    foreach ($evidencePath in @($gate.evidence)) {
        [void](Assert-PathExists ([string]$evidencePath) "Evidence for $($gate.id)")
    }
}
$statusCounts = @{}
foreach ($status in $allowedStatuses) { $statusCounts[$status] = @($gates | Where-Object status -eq $status).Count }
$expectedStatusCounts = @{ DONE = 6; OWNER = 5; PARTIAL = 2; NOT_DONE = 0; DEFERRED = 1 }
foreach ($status in $expectedStatusCounts.Keys) {
    if ($statusCounts[$status] -ne $expectedStatusCounts[$status]) {
        Add-M10Error "M10 gate count for $status is $($statusCounts[$status]), expected $($expectedStatusCounts[$status])."
    }
}

if ([string]$readiness.build_id -ne 'IF-M10-0001' -or [string]$readiness.status -ne 'STATIC_IMPLEMENTED_GATES_OPEN') {
    Add-M10Error 'Readiness ledger build/status does not describe the current static M10 slice.'
}
if (-not [bool]$readiness.no_game_launch) { Add-M10Error 'M10 ledger must preserve no_game_launch=true.' }
if ([bool]$readiness.release_ready) { Add-M10Error 'M10 may not claim release_ready while open gates exist.' }
$openBlockers = @($readiness.blockers | Where-Object status -eq 'OPEN')
if ($openBlockers.Count -ne 3) { Add-M10Error "Expected three explicit open blockers, found $($openBlockers.Count)." }
Assert-Unique @($readiness.blockers | ForEach-Object { $_.id }) 'M10 blocker IDs'
foreach ($blocker in @($readiness.blockers)) {
    foreach ($evidencePath in @($blocker.evidence)) {
        [void](Assert-PathExists ([string]$evidencePath) "Evidence for $($blocker.id)")
    }
}

$translation = $readiness.translation_stream
if ([string]$translation.mode -ne 'LOCALIZATION_MERGED_AND_STATICALLY_AUDITED' -or
    [string]$translation.status -ne 'DONE' -or
    [bool]$translation.release_blocking) {
    Add-M10Error 'Translation stream must be merged, DONE and non-blocking after localization acceptance.'
}
if (($gates | Where-Object id -eq 'M10-10').status -ne 'DONE') {
    Add-M10Error 'M10-10 localization gate must be DONE after the accepted static audit.'
}
Add-M10Pass 'Russian localization is merged and protected by source-backed static validators.'

# Milestone reporting must mirror the authoritative gate statuses in order.
$m10Milestones = @($milestones.milestones | Where-Object id -eq 'M10')
if ($m10Milestones.Count -ne 1) {
    Add-M10Error "Milestone ledger must contain exactly one M10 record, found $($m10Milestones.Count)."
}
else {
    $milestoneItems = @($m10Milestones[0].items)
    if ($milestoneItems.Count -ne 14) { Add-M10Error "M10 milestone must contain 14 items, found $($milestoneItems.Count)." }
    $compareCount = [Math]::Min($milestoneItems.Count, $gates.Count)
    for ($index = 0; $index -lt $compareCount; $index++) {
        if ([string]$milestoneItems[$index].status -ne [string]$gates[$index].status) {
            Add-M10Error "M10 milestone/readiness status differs at item $($index + 1): $($milestoneItems[$index].status) vs $($gates[$index].status)."
        }
    }
}

# Exact CurseForge manifest coverage: 132 launcher-managed JARs, no duplicate
# project, and no hidden project/file omitted from the public manifest.
if ([string]$manifest.version -ne 'IF-M10-0001') { Add-M10Error "manifest.json build is '$($manifest.version)', expected IF-M10-0001." }
$manifestFiles = @($manifest.files)
if ($manifestFiles.Count -ne 132) { Add-M10Error "manifest.json must contain 132 CurseForge files, found $($manifestFiles.Count)." }
Assert-Unique @($manifestFiles | ForEach-Object { $_.projectID }) 'Manifest project IDs'
Assert-Unique @($manifestFiles | ForEach-Object { "$($_.projectID)/$($_.fileID)" }) 'Manifest project/file pairs'
$manifestPairs = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::Ordinal)
foreach ($entry in $manifestFiles) { [void]$manifestPairs.Add("$($entry.projectID)/$($entry.fileID)") }
$installedPairs = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::Ordinal)
foreach ($addon in @($instance.installedAddons)) {
    if ((Test-HasProperty $addon 'isEnabled') -and -not [bool]$addon.isEnabled) { continue }
    if ($null -eq $addon.installedFile) { continue }
    [void]$installedPairs.Add("$($addon.addonID)/$($addon.installedFile.id)")
}
$manifestMissing = @($installedPairs | Where-Object { -not $manifestPairs.Contains($_) })
$manifestExtra = @($manifestPairs | Where-Object { -not $installedPairs.Contains($_) })
if ($manifestMissing.Count -gt 0) { Add-M10Error "Installed CurseForge pairs missing from manifest: $($manifestMissing -join ', ')" }
if ($manifestExtra.Count -gt 0) { Add-M10Error "Manifest pairs absent from enabled launcher metadata: $($manifestExtra -join ', ')" }
if ($installedPairs.Count -ne 132) { Add-M10Error "Expected 132 enabled CurseForge addon records, found $($installedPairs.Count)." }
else { Add-M10Pass 'All 132 launcher-managed JARs have an exact manifest project/file pair.' }

if ([string]$sources.build_id -ne 'IF-M10-0001') { Add-M10Error 'Source registry build_id is not IF-M10-0001.' }
$sourceByName = @{}
foreach ($entry in @($sources.files)) { $sourceByName[[string]$entry.file_name] = $entry }
$expectedCorrections = @{
    'blockui-1.20.1-1.0.193.jar' = @(522992, 7541343)
    'domum_ornamentum-1.20.1-1.0.303-snapshot-universal.jar' = @(527361, 8338110)
    'create_central_kitchen-1.20.1-for-create-6.0.8-1.5.0.jar' = @(820977, 8204836)
    'toms_storage-1.20-1.7.1.jar' = @(378609, 6418133)
}
foreach ($fileName in $expectedCorrections.Keys) {
    if (-not $sourceByName.ContainsKey($fileName)) {
        Add-M10Error "Corrected exact-file record is missing: $fileName"
        continue
    }
    $record = $sourceByName[$fileName]
    $expected = $expectedCorrections[$fileName]
    if ([int64]$record.project_id -ne [int64]$expected[0] -or [int64]$record.file_id -ne [int64]$expected[1]) {
        Add-M10Error "$fileName has $($record.project_id)/$($record.file_id), expected $($expected[0])/$($expected[1])."
    }
}

$modsPath = Resolve-M10Path 'mods'
$localJars = @(Get-ChildItem -LiteralPath $modsPath -Filter '*.jar' -File)
if ($localJars.Count -ne 133) { Add-M10Error "Expected 133 installed JARs, found $($localJars.Count)." }
if ([string]$lock.build_id -ne 'IF-M10-0001' -or [int]$lock.jar_count -ne $localJars.Count) {
    Add-M10Error 'M10 mod lock build/JAR count is stale.'
}
if (-not [bool]$lock.curseforge_provenance_complete -or [int]$lock.invalid_curseforge_url_count -ne 0 -or
    [int]$lock.expected_hash_mismatch_count -ne 0 -or [int]$lock.stale_owner_exception_count -ne 0) {
    Add-M10Error 'M10 source/hash lock contains an unknown source, invalid URL, hash mismatch or stale exception.'
}
if ([int]$lock.owner_registered_exception_count -ne 1) {
    Add-M10Error "Expected one explicit non-CurseForge owner exception, found $($lock.owner_registered_exception_count)."
}
if ([string]$dependency.build_id -ne 'IF-M10-0001' -or [int]$dependency.hard_failure_count -ne 0 -or [int]$dependency.unverified_count -ne 0) {
    Add-M10Error 'M10 mandatory dependency audit is stale or has failures/unverified ranges.'
}
Add-M10Pass "Source/dependency audit: 133 JAR, 0 unknown, 0 hash mismatch, 0 hard dependency failure, $($dependency.advisory_count) advisory."

# License inventory hashes every JAR independently. Ambiguous declarations are
# an explicit manual gate, while missing/unregistered artifacts are hard errors.
if ([string]$license.build_id -ne 'IF-M10-0001' -or [int]$license.summary.jar_count -ne $localJars.Count) {
    Add-M10Error 'License inventory build/JAR count is stale.'
}
if ((Get-M10IntProperty $license.summary.source_counts 'UNREGISTERED') -gt 0 -or
    (Get-M10IntProperty $license.summary.status_counts 'ERROR') -gt 0 -or
    (Get-M10IntProperty $license.summary.status_counts 'UNDECLARED') -gt 0) {
    Add-M10Error 'License inventory contains unregistered, unreadable or undeclared JARs.'
}
$licenseByName = @{}
foreach ($record in @($license.mods)) { $licenseByName[[string]$record.file_name] = $record }
foreach ($jar in $localJars) {
    if (-not $licenseByName.ContainsKey($jar.Name)) {
        Add-M10Error "License inventory is missing $($jar.Name)."
        continue
    }
    $actualHash = (Get-FileHash -LiteralPath $jar.FullName -Algorithm SHA256).Hash
    if ($actualHash -ne [string]$licenseByName[$jar.Name].sha256) {
        Add-M10Error "License inventory hash is stale for $($jar.Name)."
    }
}
if ([int]$license.summary.manual_review_count -ne 3) {
    Add-M10Error "Expected three ambiguous license declarations, found $($license.summary.manual_review_count)."
}
else { Add-M10Pass 'License inventory covers all 133 JARs; three ambiguous declarations remain manifest-only until manual review.' }

# Release-profile contract is validated against the live source workspace. The
# forbidden globs apply to a future staging archive, not to this development
# instance (which necessarily contains mods/).
if ([string]$releaseFiles.build_id -ne 'IF-M10-0001' -or [string]$releaseFiles.status -ne 'STATIC_UNTESTED') {
    Add-M10Error 'Release-file registry has an unexpected build/status.'
}
foreach ($path in @($releaseFiles.include_roots)) { [void](Assert-PathExists ([string]$path) 'Release include root' -Directory) }
foreach ($path in @($releaseFiles.include_files)) { [void](Assert-PathExists ([string]$path) 'Release include file') }
foreach ($path in @($releaseFiles.required_files)) { [void](Assert-PathExists ([string]$path) 'M10 required file') }
if (@($releaseFiles.exclude_roots) -notcontains 'mods') { Add-M10Error 'Release excludes must contain mods.' }
if (@($releaseFiles.forbidden_globs) -notcontains 'mods/*.jar') { Add-M10Error 'Release forbidden globs must reject mods/*.jar.' }
foreach ($includeRoot in @($releaseFiles.include_roots)) {
    $includePath = Resolve-M10Path ([string]$includeRoot)
    $embeddedJars = @(Get-ChildItem -LiteralPath $includePath -Recurse -File -Filter '*.jar')
    if ($embeddedJars.Count -gt 0) { Add-M10Error "Release include root '$includeRoot' contains embedded JARs." }
}
if ([int]$releaseFiles.current_snapshot.manifest_file_count -ne 132 -or
    [int]$releaseFiles.current_snapshot.local_jar_count -ne 133 -or
    [int]$releaseFiles.current_snapshot.owner_registered_non_curseforge_exceptions -ne 1) {
    Add-M10Error 'Release-file current_snapshot is stale.'
}
$openReleaseFindings = @($releaseFiles.known_release_blockers | Where-Object status -eq 'OPEN')
if ($openReleaseFindings.Count -ne $openBlockers.Count) {
    Add-M10Error "Release-file/readiness open-blocker counts differ: $($openReleaseFindings.Count) vs $($openBlockers.Count)."
}

# Progression JSON is canonical only while its recorded input hashes match the
# live registries. This lets lint validate freshness without requiring Python.
if ([int]$progression.summary.unexplained_blockers -ne 0 -or [string]$progression.summary.status -ne 'PASS_STATIC' -or [bool]$progression.summary.minecraft_launched) {
    Add-M10Error 'Progression/grind report is not a no-game PASS_STATIC with zero unexplained blockers.'
}
foreach ($property in @($progression.inputs.PSObject.Properties)) {
    $input = $property.Value
    if (-not (Test-HasProperty $input 'path') -or -not (Test-HasProperty $input 'sha256')) {
        Add-M10Error "Progression input '$($property.Name)' lacks path/SHA-256 freshness metadata."
        continue
    }
    try {
        $inputPath = Resolve-M10Path ([string]$input.path)
        $actualHash = (Get-FileHash -LiteralPath $inputPath -Algorithm SHA256).Hash
        if ($actualHash -ne [string]$input.sha256) {
            Add-M10Error "Progression report is stale for $($input.path); rerun audit_progression.py."
        }
    }
    catch { Add-M10Error "Progression input '$($property.Name)' cannot be verified: $($_.Exception.Message)" }
}
if ([int]$progression.checks.epochs.present -ne 10 -or [int]$progression.checks.epochs.sequential_edges_present -ne 9) {
    Add-M10Error 'Progression audit does not cover all P0-P9 nodes and transitions.'
}
if ([int]$progression.checks.grind.chains -ne 21 -or [int]$progression.checks.grind.hard_exceedances -ne 0) {
    Add-M10Error 'Progression audit grind counts differ from the M10 contract.'
}
if ([int]$progression.checks.evidence.physical_paths_valid -ne [int]$progression.checks.evidence.physical_paths_checked) {
    Add-M10Error 'Progression evidence paths are not all valid.'
}
Add-M10Pass 'Progression/grind report is hash-current with P0-P9 10/10, transitions 9/9 and zero unexplained blockers.'

# Structural quest audit deliberately does not open lang files.
$questRoot = Resolve-M10Path 'authoring/quests'
$questFiles = @(Get-ChildItem -LiteralPath $questRoot -Filter '*.json' -File)
$questCount = 0
$descriptionCount = 0
$taskCount = 0
$descriptionRefCount = 0
$aliases = [System.Collections.Generic.List[string]]::new()
$engineIds = [System.Collections.Generic.List[string]]::new()
$mainlineNames = @(
    '10_p0_expedition', '11_p1_mechanised', '12_p2_steam_metallurgy', '13_p3_electrification',
    '14_p4_chemical_city', '15_p5_regional_logistics', '16_p6_nuclear', '17_p7_strategic_space',
    '18_p8_orbital_network', '19_p9_finale'
)
$mainlineQuestCount = 0
foreach ($questFile in $questFiles) {
    try { $source = Get-Content -Raw -Encoding UTF8 -LiteralPath $questFile.FullName | ConvertFrom-Json }
    catch { Add-M10Error "Quest source is invalid: $($questFile.Name)"; continue }
    $quests = @($source.quests)
    $questCount += $quests.Count
    foreach ($quest in $quests) {
        $aliases.Add([string]$quest.alias)
        $engineIds.Add([string]$quest.engine_id)
        if ([string]::IsNullOrWhiteSpace([string]$quest.purpose)) { Add-M10Error "$($questFile.Name)/$($quest.alias) has no purpose." }
        if ([string]::IsNullOrWhiteSpace([string]$quest.grind_class)) { Add-M10Error "$($questFile.Name)/$($quest.alias) has no grind_class." }
    }
    if (-not (Assert-PathExists ([string]$source.compiled_path) "Compiled quest chapter for $($questFile.Name)")) { continue }
    $compiledPath = Resolve-M10Path ([string]$source.compiled_path)
    $compiled = Get-Content -Raw -Encoding UTF8 -LiteralPath $compiledPath
    $chapterDescriptions = [regex]::Matches($compiled, '(?m)^\s*description:\s*\[$').Count
    $chapterTasks = [regex]::Matches($compiled, '(?m)^\s*tasks:\s*\[').Count
    if ($chapterDescriptions -ne $quests.Count) { Add-M10Error "$($questFile.Name) has $chapterDescriptions description blocks for $($quests.Count) quests." }
    if ($chapterTasks -ne $quests.Count) { Add-M10Error "$($questFile.Name) has $chapterTasks task blocks for $($quests.Count) quests." }
    $descriptionCount += $chapterDescriptions
    $taskCount += $chapterTasks
    $descriptionRefCount += [regex]::Matches($compiled, '\{industrial_frontier\.quest\.[^}]+\.desc\.\d+\}').Count
    if ($mainlineNames -contains $questFile.BaseName) {
        if ((Test-HasProperty $source 'optional') -and [bool]$source.optional) { Add-M10Error "$($questFile.Name) is a mainline chapter but optional=true." }
        $mainlineQuestCount += $quests.Count
        $mainlineTags = [regex]::Matches($compiled, 'tags:\s*\["mainline"\]').Count
        if ($mainlineTags -ne $quests.Count) { Add-M10Error "$($questFile.Name) has $mainlineTags mainline tags for $($quests.Count) quests." }
    }
}
Assert-Unique @($aliases) 'Quest aliases'
Assert-Unique @($engineIds) 'Quest engine IDs'
if ($questFiles.Count -ne 24 -or $questCount -ne 214 -or $descriptionCount -ne 214 -or $taskCount -ne 214 -or $mainlineQuestCount -ne 118) {
    Add-M10Error "Quest structure differs from M10 baseline: chapters=$($questFiles.Count), quests=$questCount, descriptions=$descriptionCount, tasks=$taskCount, mainline=$mainlineQuestCount."
}
if ($descriptionRefCount -lt ($questCount * 2)) { Add-M10Error "Quest guidebook has only $descriptionRefCount description-key references for $questCount quests." }
else { Add-M10Pass "Quest structure: 24 chapters, 214 quests, 118 P0-P9 mainline quests and $descriptionRefCount description-key references." }

$requiredDocs = @(
    'docs/M10_BUILD_TEST_PROTOCOL.md',
    'docs/M10_TEST_JOURNAL_TEMPLATE.md',
    'docs/M10_GRIND_BUDGET_REPORT.md',
    'docs/M10_QUEST_EDITORIAL_AUDIT.md',
    'docs/M10_RELEASE_PROFILES.md',
    'docs/RU_LOCALIZATION_REPORT.md',
    'docs/MIGRATION_NOTES_IF-M10-0001.md',
    'docs/THIRD_PARTY_NOTICES.md',
    'docs/licenses/CCCyrillic-MIT.txt',
    'docs/registries/cc_terminal_font.json',
    'tools/generate_archive_lang_audit.ps1',
    'docs/KNOWN_ISSUES.md',
    'docs/M10_IMPLEMENTATION_REPORT.md'
)
foreach ($path in $requiredDocs) { [void](Assert-PathExists $path 'M10 required document') }

if (-not $Quiet) {
    foreach ($message in $errors) { Write-Output "[M10][ERROR] $message" }
    foreach ($message in $warnings) { Write-Output "[M10][WARN] $message" }
    foreach ($message in $passes) { Write-Output "[M10][PASS] $message" }
}
Write-Output "[M10] errors=$($errors.Count) warnings=$($warnings.Count) passes=$($passes.Count) gates=$($gates.Count) done=$($statusCounts.DONE) owner=$($statusCounts.OWNER) partial=$($statusCounts.PARTIAL) not_done=$($statusCounts.NOT_DONE) deferred=$($statusCounts.DEFERRED) open_blockers=$($openBlockers.Count) release_ready=$([bool]$readiness.release_ready)"
Write-Output '[M10] Russian localization is merged; runtime rendering remains an owner smoke test.'
Write-Output '[M10] Minecraft/Forge was not launched.'

if ($errors.Count -gt 0) { exit 1 }
exit 0
