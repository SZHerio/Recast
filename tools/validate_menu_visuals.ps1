param(
    [string]$Root = (Split-Path -Parent $PSScriptRoot)
)

$ErrorActionPreference = 'Stop'
$errors = New-Object 'System.Collections.Generic.List[string]'
$warnings = New-Object 'System.Collections.Generic.List[string]'
$passes = New-Object 'System.Collections.Generic.List[string]'

function Add-MenuError([string]$Message) { $errors.Add($Message) }
function Add-MenuWarning([string]$Message) { $warnings.Add($Message) }
function Add-MenuPass([string]$Message) { $passes.Add($Message) }

function Assert-RequiredProperties($Object, [object[]]$Required, [string]$Context) {
    $names = @($Object.PSObject.Properties.Name)
    foreach ($name in $Required) {
        if ($names -notcontains [string]$name) {
            Add-MenuError "$Context is missing schema-required property '$name'."
        }
    }
}

function Assert-NoUnknownProperties($Object, [object[]]$Allowed, [string]$Context) {
    $allowedNames = @($Allowed | ForEach-Object { [string]$_ })
    foreach ($name in @($Object.PSObject.Properties.Name)) {
        if ($allowedNames -notcontains [string]$name) {
            Add-MenuError "$Context contains schema-forbidden property '$name'."
        }
    }
}

function Get-ElementBlock([string]$Layout, [string]$Identifier) {
    foreach ($match in [regex]::Matches($Layout, '(?ms)^element\s*\{.*?^\}')) {
        if ($match.Value -match "(?m)^\s*instance_identifier\s*=\s*$([regex]::Escape($Identifier))\s*$") {
            return [string]$match.Value
        }
    }
    return $null
}

function Get-BlockSetting([string]$Block, [string]$Name) {
    $match = [regex]::Match($Block, "(?m)^\s*$([regex]::Escape($Name))\s*=\s*(.*?)\s*$")
    if (-not $match.Success) { return $null }
    return [string]$match.Groups[1].Value.Trim()
}

function Resolve-MenuPath([string]$RelativePath) {
    if ([string]::IsNullOrWhiteSpace($RelativePath) -or $RelativePath -match '^[A-Za-z]:' -or $RelativePath.StartsWith('/')) {
        throw "Menu contract path must be workspace-relative: $RelativePath"
    }
    $candidate = [System.IO.Path]::GetFullPath((Join-Path $Root ($RelativePath -replace '/', [System.IO.Path]::DirectorySeparatorChar)))
    $rootFull = [System.IO.Path]::GetFullPath($Root).TrimEnd([System.IO.Path]::DirectorySeparatorChar) + [System.IO.Path]::DirectorySeparatorChar
    if (-not $candidate.StartsWith($rootFull, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Menu contract path escapes the workspace: $RelativePath"
    }
    return $candidate
}

function Get-PngMetadata([string]$Path) {
    $stream = [System.IO.File]::OpenRead($Path)
    try {
        $header = New-Object byte[] 26
        if ($stream.Read($header, 0, $header.Length) -ne $header.Length) {
            throw 'PNG header is truncated.'
        }
        $signature = @(137, 80, 78, 71, 13, 10, 26, 10)
        for ($index = 0; $index -lt $signature.Count; $index++) {
            if ($header[$index] -ne $signature[$index]) { throw 'Invalid PNG signature.' }
        }
        [uint32]$width = ([uint32]$header[16] * 16777216) + ([uint32]$header[17] * 65536) + ([uint32]$header[18] * 256) + [uint32]$header[19]
        [uint32]$height = ([uint32]$header[20] * 16777216) + ([uint32]$header[21] * 65536) + ([uint32]$header[22] * 256) + [uint32]$header[23]
        $mode = switch ([int]$header[25]) {
            2 { 'RGB' }
            6 { 'RGBA' }
            default { "PNG_COLOR_TYPE_$([int]$header[25])" }
        }
        return [pscustomobject]@{ Width = [int]$width; Height = [int]$height; Mode = $mode }
    }
    finally {
        $stream.Dispose()
    }
}

function Assert-Png([string]$RelativePath, [int]$Width, [int]$Height, [string]$Mode) {
    try {
        $path = Resolve-MenuPath $RelativePath
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
            Add-MenuError "Missing PNG: $RelativePath"
            return
        }
        $metadata = Get-PngMetadata $path
        if ($metadata.Width -ne $Width -or $metadata.Height -ne $Height) {
            Add-MenuError "PNG dimensions for $RelativePath are $($metadata.Width)x$($metadata.Height), expected ${Width}x${Height}."
        }
        if ($metadata.Mode -ne $Mode) {
            Add-MenuError "PNG mode for $RelativePath is $($metadata.Mode), expected $Mode."
        }
    }
    catch {
        Add-MenuError "PNG validation failed for ${RelativePath}: $($_.Exception.Message)"
    }
}

try {
    $registryPath = Resolve-MenuPath 'docs/registries/m9_menu_visuals.json'
    $schemaPath = Resolve-MenuPath 'authoring/schemas/m9_menu_visuals.schema.json'
    $registryRaw = Get-Content -Raw -LiteralPath $registryPath -Encoding UTF8
    $registry = $registryRaw | ConvertFrom-Json
    $schema = Get-Content -Raw -LiteralPath $schemaPath -Encoding UTF8 | ConvertFrom-Json
    if ([string]$registry.registry_id -ne 'industrial_frontier:m9/menu_visuals_v2') { Add-MenuError 'Unexpected menu registry ID.' }
    if ([string]$registry.status -ne 'IMPLEMENTED_STATIC_UNTESTED') { Add-MenuError 'Menu status must remain IMPLEMENTED_STATIC_UNTESTED until the owner runs Minecraft.' }
    if (-not [bool]$registry.no_game_launch) { Add-MenuError 'Menu contract must state no_game_launch=true.' }
    if ([string]$registry.translation_scope -ne 'EXCLUDED_NO_FILES_TOUCHED') { Add-MenuError 'Translation scope is not explicitly excluded.' }
    if (@($registry.layers).Count -ne 3) { Add-MenuError 'The v2 menu must declare exactly three scene layers.' }
    Add-MenuPass 'Menu registry and no-launch/no-translation scope parsed.'

    Assert-RequiredProperties $registry @($schema.required) 'Menu registry'
    Assert-NoUnknownProperties $registry @($schema.properties.PSObject.Properties.Name) 'Menu registry'
    Assert-RequiredProperties $registry.implementation @($schema.properties.implementation.required) 'Menu implementation contract'
    Assert-NoUnknownProperties $registry.implementation @($schema.properties.implementation.properties.PSObject.Properties.Name) 'Menu implementation contract'
    Assert-RequiredProperties $registry.implementation.reference_canvas @($schema.properties.implementation.properties.reference_canvas.required) 'Menu reference canvas'
    Assert-NoUnknownProperties $registry.implementation.reference_canvas @($schema.properties.implementation.properties.reference_canvas.properties.PSObject.Properties.Name) 'Menu reference canvas'
    foreach ($layer in @($registry.layers)) {
        Assert-RequiredProperties $layer @($schema.properties.layers.items.required) "Menu layer '$($layer.id)'"
        Assert-NoUnknownProperties $layer @($schema.properties.layers.items.properties.PSObject.Properties.Name) "Menu layer '$($layer.id)'"
        if ([bool]$layer.parallax) {
            Assert-RequiredProperties $layer @('maximum_cursor_offset_x', 'maximum_cursor_offset_y') "Parallax layer '$($layer.id)'"
        }
    }
    Assert-RequiredProperties $registry.acceptance @($schema.properties.acceptance.required) 'Menu acceptance contract'

    $testJson = Get-Command Test-Json -ErrorAction SilentlyContinue
    if ($null -ne $testJson) {
        if (-not (Test-Json -Json $registryRaw -SchemaFile $schemaPath -ErrorAction Stop)) {
            Add-MenuError 'Menu registry failed JSON Schema validation.'
        }
        else {
            Add-MenuPass 'Menu registry passed JSON Schema validation.'
        }
    }
    else {
        Add-MenuPass 'PowerShell 5.1 fallback enforced schema-required and additional-property contracts.'
    }
}
catch {
    Add-MenuError "Menu registry could not be read: $($_.Exception.Message)"
    $registry = $null
}

if ($null -ne $registry) {
    $referenceWidth = [double]$registry.implementation.reference_canvas.width
    $referenceHeight = [double]$registry.implementation.reference_canvas.height
    $positionMultiplier = [double]$registry.implementation.parallax_position_multiplier
    if ([Math]::Abs($positionMultiplier - 0.1) -gt 0.000001) {
        Add-MenuError 'FancyMenu 3.9.9 parallax position multiplier must be 0.1.'
    }
    foreach ($layer in @($registry.layers)) {
        Assert-Png ([string]$layer.runtime_path) ([int]$layer.width) ([int]$layer.height) ([string]$layer.mode)
        $sourcePath = Resolve-MenuPath ([string]$layer.source_path)
        if (-not (Test-Path -LiteralPath $sourcePath -PathType Leaf)) {
            Add-MenuError "Missing accepted source artwork: $($layer.source_path)"
        }
        if ([bool]$layer.parallax) {
            $expectedOffsetX = [Math]::Round(($referenceWidth / 2.0) * [double]$layer.intensity_x * $positionMultiplier, 2)
            $expectedOffsetY = [Math]::Round(($referenceHeight / 2.0) * [double]$layer.intensity_y * $positionMultiplier, 2)
            if ([Math]::Abs([double]$layer.maximum_cursor_offset_x - $expectedOffsetX) -gt 0.011) {
                Add-MenuError "Layer '$($layer.id)' maximum_cursor_offset_x is not derived from the FancyMenu 3.9.9 formula; expected $expectedOffsetX."
            }
            if ([Math]::Abs([double]$layer.maximum_cursor_offset_y - $expectedOffsetY) -gt 0.011) {
                Add-MenuError "Layer '$($layer.id)' maximum_cursor_offset_y is not derived from the FancyMenu 3.9.9 formula; expected $expectedOffsetY."
            }
            $left = [double](-[int]$layer.layout.x)
            $right = [double]([int]$layer.layout.width - 854 + [int]$layer.layout.x)
            $top = [double](-[int]$layer.layout.y)
            $bottom = [double]([int]$layer.layout.height - 480 + [int]$layer.layout.y)
            if ($expectedOffsetX -gt [Math]::Min($left, $right)) {
                Add-MenuError "Layer '$($layer.id)' can expose a horizontal edge at maximum cursor displacement."
            }
            if ($expectedOffsetY -gt [Math]::Min($top, $bottom)) {
                Add-MenuError "Layer '$($layer.id)' can expose a vertical edge at maximum cursor displacement."
            }
        }
    }
    Add-MenuPass 'Base/mid/near PNG modes, dimensions, sources and overscan budgets validated.'
}

Assert-Png 'config/fancymenu/assets/logo.png' 1536 512 'RGBA'
Assert-Png 'config/fancymenu/assets/ui/panel.png' 96 96 'RGBA'
foreach ($state in @('normal', 'hover', 'inactive')) {
    Assert-Png "config/fancymenu/assets/ui/button_$state.png" 48 24 'RGBA'
    Assert-Png "config/fancymenu/assets/ui/icon_button_$state.png" 24 24 'RGBA'
}
Assert-Png 'pack_icon.png' 256 256 'RGB'
Assert-Png 'config/fancymenu/assets/icon_16.png' 16 16 'RGB'
Assert-Png 'config/fancymenu/assets/icon_32.png' 32 32 'RGB'
Assert-Png 'docs/visual_previews/recast_title_v2_center.png' 1920 1080 'RGB'
Assert-Png 'docs/visual_previews/recast_title_v2_cursor_extremes.png' 1920 1080 'RGB'
Assert-Png 'docs/visual_previews/recast_title_v2_button_states.png' 1280 480 'RGB'
if ($errors.Count -eq 0) { Add-MenuPass 'Logo, icon, panel, button states and static preview dimensions validated.' }

try {
    $layoutPath = Resolve-MenuPath 'config/fancymenu/customization/recast_title.txt'
    $layout = Get-Content -Raw -LiteralPath $layoutPath -Encoding UTF8
    foreach ($token in @(
        '[source:local]/config/fancymenu/assets/menu/base.png',
        '[source:local]/config/fancymenu/assets/menu/mid.png',
        '[source:local]/config/fancymenu/assets/menu/near.png',
        'parallax_intensity_x = 0.18',
        'parallax_intensity_y = 0.10',
        'parallax_intensity_x = 0.30',
        'parallax_intensity_y = 0.16',
        '[source:local]/config/fancymenu/assets/ui/icon_button_normal.png'
    )) {
        if (-not $layout.Contains($token)) { Add-MenuError "Title layout is missing required token: $token" }
    }
    if ([regex]::Matches($layout, '(?m)^\s*enable_parallax\s*=\s*true\s*$').Count -ne 2) {
        Add-MenuError 'Exactly two non-interactive image layers must enable parallax.'
    }
    if ([regex]::Matches($layout, '(?m)^\s*nine_slice_custom_background\s*=\s*true\s*$').Count -ne 10) {
        Add-MenuError 'All eight action buttons and two compact buttons must use nine-slicing.'
    }
    if ($layout -match '(?m)^\s*slide\s*=\s*true\s*$') { Add-MenuError 'Wide-image sliding conflicts with cursor parallax.' }

    foreach ($layer in @($registry.layers | Where-Object { [bool]$_.parallax })) {
        $identifier = [string]$layer.layout.instance_identifier
        $block = Get-ElementBlock $layout $identifier
        if ([string]::IsNullOrWhiteSpace($block)) {
            Add-MenuError "Missing FancyMenu element block for parallax layer '$identifier'."
            continue
        }
        $expectedStrings = @{
            'source' = "[source:local]/$($layer.runtime_path)"
            'enable_parallax' = 'true'
            'invert_parallax' = ([string][bool]$layer.layout.invert_parallax).ToLowerInvariant()
            'stay_on_screen' = ([string][bool]$layer.layout.stay_on_screen).ToLowerInvariant()
            'anchor_point' = 'top-left'
        }
        foreach ($setting in $expectedStrings.Keys) {
            $actual = Get-BlockSetting $block $setting
            if ($actual -ne $expectedStrings[$setting]) {
                Add-MenuError "Layer '$identifier' setting '$setting' is '$actual', expected '$($expectedStrings[$setting])'."
            }
        }
        foreach ($setting in @('x', 'y', 'width', 'height')) {
            $actual = Get-BlockSetting $block $setting
            if ([int]$actual -ne [int]$layer.layout.$setting) {
                Add-MenuError "Layer '$identifier' setting '$setting' is '$actual', expected '$($layer.layout.$setting)'."
            }
        }
        foreach ($pair in @(@('parallax_intensity_x', 'intensity_x'), @('parallax_intensity_y', 'intensity_y'))) {
            $actual = Get-BlockSetting $block $pair[0]
            if ([Math]::Abs([double]::Parse($actual, [Globalization.CultureInfo]::InvariantCulture) - [double]$layer.($pair[1])) -gt 0.000001) {
                Add-MenuError "Layer '$identifier' setting '$($pair[0])' is '$actual', expected '$($layer.($pair[1]))'."
            }
        }
    }

    $midIndex = $layout.IndexOf('instance_identifier = recast_title_midground')
    $nearIndex = $layout.IndexOf('instance_identifier = recast_title_foreground')
    $panelIndex = $layout.IndexOf('instance_identifier = recast_title_panel')
    if (-not ($midIndex -ge 0 -and $nearIndex -gt $midIndex -and $panelIndex -gt $nearIndex)) {
        Add-MenuError 'FancyMenu layer order must be midground, foreground, then stationary UI panel.'
    }

    $buildBlock = Get-ElementBlock $layout 'recast_build_label'
    if ([string]::IsNullOrWhiteSpace($buildBlock)) {
        Add-MenuError 'Missing build-label element.'
    }
    else {
        $buildContract = $registry.ui.build_label
        foreach ($setting in @('anchor_point', 'x', 'y')) {
            $actual = Get-BlockSetting $buildBlock $setting
            $expected = [string]$buildContract.$setting
            if ($actual -ne $expected) {
                Add-MenuError "Build-label setting '$setting' is '$actual', expected '$expected' from the registry."
            }
        }
        if (-not [bool]$buildContract.inside_panel -or [int]$buildContract.y -lt 370 -or [int]$buildContract.y -gt 454) {
            Add-MenuError 'Build label must remain inside the lower panel and outside vanilla branding zones.'
        }
    }
    if ($layout -notmatch '(?s)element_type\s*=\s*title_screen_branding.*?is_hidden\s*=\s*false') {
        Add-MenuError 'Protected Minecraft copyright branding must remain visible.'
    }
    Add-MenuPass 'FancyMenu layer geometry/order, parallax, nine-slice and protected-branding tokens validated.'
}
catch {
    Add-MenuError "Title-layout validation failed: $($_.Exception.Message)"
}

try {
    $provenancePath = Resolve-MenuPath 'docs/registries/m9_asset_provenance.json'
    $provenance = Get-Content -Raw -LiteralPath $provenancePath -Encoding UTF8 | ConvertFrom-Json
    $byPath = @{}
    foreach ($asset in @($provenance.assets)) { $byPath[[string]$asset.path] = $asset }
    $runtimePaths = @(
        'config/fancymenu/assets/menu/base.png',
        'config/fancymenu/assets/menu/mid.png',
        'config/fancymenu/assets/menu/near.png',
        'config/fancymenu/assets/logo.png',
        'config/fancymenu/assets/ui/button_normal.png',
        'config/fancymenu/assets/ui/button_hover.png',
        'config/fancymenu/assets/ui/button_inactive.png',
        'config/fancymenu/assets/ui/icon_button_normal.png',
        'config/fancymenu/assets/ui/icon_button_hover.png',
        'config/fancymenu/assets/ui/icon_button_inactive.png',
        'config/fancymenu/assets/ui/panel.png',
        'pack_icon.png'
    )
    foreach ($relativePath in $runtimePaths) {
        if (-not $byPath.ContainsKey($relativePath)) {
            Add-MenuError "Menu runtime asset is missing from M9 provenance: $relativePath"
            continue
        }
        $actualHash = (Get-FileHash -Algorithm SHA256 -LiteralPath (Resolve-MenuPath $relativePath)).Hash.ToUpperInvariant()
        if ($actualHash -ne ([string]$byPath[$relativePath].sha256).ToUpperInvariant()) {
            Add-MenuError "Menu provenance hash mismatch: $relativePath"
        }
    }
    if (@($provenance.source_artwork | Where-Object { $_.source_id -in @(
        'industrial_frontier:source/brand/mark',
        'industrial_frontier:source/brand/menu_background',
        'industrial_frontier:source/brand/menu_mid',
        'industrial_frontier:source/brand/menu_near',
        'industrial_frontier:source/brand/title_lockup'
    ) }).Count -ne 5) {
        Add-MenuError 'Five accepted v2 source-artwork records are required.'
    }
    Add-MenuPass 'Runtime assets are hash-current in the M9 provenance ledger.'
}
catch {
    Add-MenuError "Menu provenance validation failed: $($_.Exception.Message)"
}

foreach ($message in $passes) { Write-Host "[MENU][PASS] $message" -ForegroundColor Green }
foreach ($message in $warnings) { Write-Host "[MENU][WARN] $message" -ForegroundColor Yellow }
foreach ($message in $errors) { Write-Host "[MENU][ERROR] $message" -ForegroundColor Red }
Write-Host "[MENU][SUMMARY] errors=$($errors.Count) warnings=$($warnings.Count) passes=$($passes.Count) layers=3 game_launched=false translations_touched=false"

if ($errors.Count -gt 0) { exit 1 }
exit 0
