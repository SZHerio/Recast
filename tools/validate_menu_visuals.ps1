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
    $registryPath = Resolve-MenuPath 'docs/registries/menu_visuals.json'
    $schemaPath = Resolve-MenuPath 'authoring/schemas/menu_visuals.schema.json'
    $registryRaw = Get-Content -Raw -LiteralPath $registryPath -Encoding UTF8
    $registry = $registryRaw | ConvertFrom-Json
    $schema = Get-Content -Raw -LiteralPath $schemaPath -Encoding UTF8 | ConvertFrom-Json
    if ([string]$registry.registry_id -ne 'industrial_frontier:menu_visuals_v2') { Add-MenuError 'Unexpected menu registry ID.' }
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
    if ([Math]::Abs($positionMultiplier - 1.0) -gt 0.000001) {
        Add-MenuError 'FancyMenu image-background parallax uses the direct 1.0 position multiplier.'
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
            if ([string]$layer.layout.kind -eq 'MENU_BACKGROUND_RESIZE_SAFE') {
                if ([string]$layer.id -ne 'base') {
                    Add-MenuError 'Only the composite base may use resize-safe image-background parallax.'
                }
            }
            else {
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
    }
    Add-MenuPass 'Resize-safe composite-background parallax and archived mid/near PNG contracts validated.'
}

Assert-Png 'config/fancymenu/assets/logo.png' 1536 512 'RGBA'
Assert-Png 'config/fancymenu/assets/ui/panel.png' 96 96 'RGBA'
foreach ($state in @('normal', 'hover', 'inactive')) {
    Assert-Png "config/fancymenu/assets/ui/button_$state.png" 48 24 'RGBA'
    Assert-Png "config/fancymenu/assets/ui/icon_button_$state.png" 24 24 'RGBA'
}
Assert-Png 'pack_icon.png' 256 256 'RGBA'
Assert-Png 'config/fancymenu/assets/icon_16.png' 16 16 'RGBA'
Assert-Png 'config/fancymenu/assets/icon_32.png' 32 32 'RGBA'
Assert-Png 'docs/visual_previews/recast_title_v2_center.png' 1920 1080 'RGB'
Assert-Png 'docs/visual_previews/recast_title_v2_cursor_extremes.png' 1920 1080 'RGB'
Assert-Png 'docs/visual_previews/recast_title_v2_button_states.png' 1280 480 'RGB'
Assert-Png 'docs/visual_previews/recast_loading_frontier_compact.png' 1920 1080 'RGB'
if ($errors.Count -eq 0) { Add-MenuPass 'Logo, icon, panel, button states and static preview dimensions validated.' }

try {
    $fancyMenuOptions = Get-Content -Raw -Encoding UTF8 -LiteralPath (Resolve-MenuPath 'config/fancymenu/options.txt')
    foreach ($token in @(
        "B:show_custom_window_icon = 'true';",
        "S:custom_window_icon_16 = 'config/fancymenu/assets/icon_16.png';",
        "S:custom_window_icon_32 = 'config/fancymenu/assets/icon_32.png';"
    )) {
        if (-not $fancyMenuOptions.Contains($token)) {
            Add-MenuError "FancyMenu window-icon configuration is missing token: $token"
        }
    }
    if ([string]$registry.icon.window_icon_design -ne 'SMOOTH_ALPHA_MASTER_LANCZOS_DOWNSCALE') {
        Add-MenuError 'Window-icon registry must require the smooth transparent high-resolution master.'
    }
    Add-MenuPass 'FancyMenu points the window and taskbar to smooth transparent 16px/32px icon derivatives.'
}
catch {
    Add-MenuError "Window-icon configuration validation failed: $($_.Exception.Message)"
}

try {
    $layoutPath = Resolve-MenuPath 'config/fancymenu/customization/recast_title.txt'
    $layout = Get-Content -Raw -LiteralPath $layoutPath -Encoding UTF8
    foreach ($token in @(
        '[source:local]/config/fancymenu/assets/menu/base.png',
        'parallax = false',
        'invert_parallax = false',
        '[source:local]/config/fancymenu/assets/ui/icon_button_normal.png'
    )) {
        if (-not $layout.Contains($token)) { Add-MenuError "Title layout is missing required token: $token" }
    }
    if ($layout.Contains('[source:local]/config/fancymenu/assets/menu/mid.png') -or
        $layout.Contains('[source:local]/config/fancymenu/assets/menu/near.png')) {
        Add-MenuError 'Fullscreen-resize-unsafe mid/near image elements must not exist in the runtime title layout.'
    }
    if ($layout -match '(?m)^\s*enable_parallax\s*=\s*true\s*$') {
        Add-MenuError 'The title layout must not contain separate cursor-parallax elements after the F11 resize defect.'
    }
    # Решение владельца от 11 августа 2026 года: фон за курсором не ездит.
    if ([regex]::Matches($layout, '(?m)^\s*parallax\s*=\s*true\s*$').Count -ne 0) {
        Add-MenuError 'The menu background must stay still; cursor parallax is disabled by owner decision.'
    }
    if ($layout -match '(?m)^\s*parallax_intensity_[xy]\s*=') {
        Add-MenuError 'Parallax intensity keys must be absent while the background is static.'
    }
    if ([regex]::Matches($layout, '(?m)^\s*nine_slice_custom_background\s*=\s*true\s*$').Count -ne 15) {
        Add-MenuError 'All eight visible custom buttons and the seven hidden compatibility widgets must retain nine-slice styling.'
    }
    if ([regex]::Matches($layout, 'action_type:mimicbutton').Count -ne 5) {
        Add-MenuError 'The five visible main-menu buttons must use mimicbutton actions instead of rendering the grey vanilla widgets.'
    }
    if ($layout -match '(?m)^\s*slide\s*=\s*true\s*$') { Add-MenuError 'The stable title background must not slide.' }
    # Решение владельца от 11 августа 2026 года: размер меню не должен зависеть
    # от выбранного игроком масштаба интерфейса. Это делает автомасштаб: макет
    # живёт в поле 640x360 и приводится к экрану независимо от настройки.
    if ($layout -notmatch '(?m)^\s*action\s*=\s*autoscale\s*$') {
        Add-MenuError 'Title layout must use autoscale so the menu size does not follow the GUI scale setting.'
    }
    foreach ($token in @('basewidth = 640', 'baseheight = 360')) {
        if (-not $layout.Contains($token)) { Add-MenuError "Autoscale base is missing token: $token" }
    }
    if ($layout -match '(?m)^\s*action\s*=\s*setscale\s*$') {
        Add-MenuError 'Fixed setscale must not be combined with autoscale.'
    }

    $panelBlock = Get-ElementBlock $layout 'recast_title_panel'
    if ([string]::IsNullOrWhiteSpace($panelBlock)) {
        Add-MenuError 'Missing title-panel element.'
    }
    else {
        # Геометрия живёт в базовом поле автомасштаба 640x360 и привязана к
        # середине левого края, поэтому не зависит ни от размера окна, ни от
        # выбранного масштаба интерфейса.
        $expectedPanel = @{ anchor_point = 'mid-left'; x = '12'; y = '-111'; width = '208'; height = '222' }
        foreach ($setting in $expectedPanel.Keys) {
            if ((Get-BlockSetting $panelBlock $setting) -ne $expectedPanel[$setting]) {
                Add-MenuError "Title-panel setting '$setting' must be '$($expectedPanel[$setting])' inside the 640x360 autoscale base."
            }
        }
        $panelHeight = [int](Get-BlockSetting $panelBlock 'height')
        if ($panelHeight -gt 332) {
            Add-MenuError "Title panel is $panelHeight tall; it must leave margins inside the 360-pixel autoscale base."
        }
    }
    if ([regex]::Matches($layout, '(?m)^\s*stay_on_screen\s*=\s*true\s*$').Count -ne 0) {
        Add-MenuError 'No element may clamp itself to the screen: independent clamping is what broke the composition.'
    }
    foreach ($removedId in @('recast_service_hint', 'recast_build_label')) {
        if (-not [string]::IsNullOrWhiteSpace((Get-ElementBlock $layout $removedId))) {
            Add-MenuError "Clutter element '$removedId' must be physically absent because text_v2 ignores is_hidden."
        }
    }
    foreach ($widgetId in @('minecraft_logo_widget', 'minecraft_splash_widget', 'minecraft_branding_widget')) {
        if ($layout -notmatch "(?s)element_type\s*=\s*vanilla_button\s+instance_identifier\s*=\s*$([regex]::Escape($widgetId))\s+is_hidden\s*=\s*true") {
            Add-MenuError "Vanilla title widget '$widgetId' must be hidden by its real FancyMenu 3.9.9 identifier."
        }
    }
    foreach ($widgetId in @('mc_titlescreen_singleplayer_button', 'mc_titlescreen_multiplayer_button', 'forge_titlescreen_mods_button', 'mc_titlescreen_options_button', 'mc_titlescreen_quit_button')) {
        if ($layout -notmatch "(?s)instance_identifier\s*=\s*$([regex]::Escape($widgetId)).*?is_hidden\s*=\s*true") {
            Add-MenuError "Vanilla action widget '$widgetId' must remain hidden behind its white mimic button."
        }
    }
    # Копирайт Mojang обязан оставаться читаемым, и его место — внизу экрана.
    # Прежний приём с уносом за границу экрана не работал: подпись всё равно
    # рисовалась в левом верхнем углу поверх логотипа.
    if ($layout -notmatch '(?s)instance_identifier\s*=\s*title_screen_copyright_button\s+label_base_color\s*=\s*#FF8A939C\s+label_hover_color\s*=\s*#FF8A939C\s+base_opacity\s*=\s*1\.0\s+anchor_point\s*=\s*bottom-left\s+x\s*=\s*4\s+y\s*=\s*-12') {
        Add-MenuError 'Copyright widget must stay legible and anchored to the bottom-left corner.'
    }
    Add-MenuPass 'FancyMenu static background, 640x360 autoscale panel and exact hidden-widget contracts validated.'
}
catch {
    Add-MenuError "Title-layout validation failed: $($_.Exception.Message)"
}

try {
    $startupLayouts = @(
        'recast_title.txt',
        'recast_guide.txt',
        'recast_credits.txt',
        'recast_licenses.txt',
        'recast_changelog.txt',
        'recast_loading_frontier.txt',
        'recast_loading_works.txt',
        'recast_loading_launch.txt'
    )
    foreach ($name in $startupLayouts) {
        $startupLayout = Get-Content -Raw -Encoding UTF8 -LiteralPath (Resolve-MenuPath "config/fancymenu/customization/$name")
        # Титульный экран — единственный layout с autoscale: панель 208×222
        # привязана к базовой сетке 640×360 и не зависит от GUI scale.
        $allowedScaling = ($name -eq 'recast_title.txt')
        if (-not $allowedScaling -and $startupLayout -match '(?m)^\s*action\s*=\s*(?:setscale|autoscale)\s*$') {
            Add-MenuError "Startup layout '$name' must use native GUI coordinates; forced scaling clips at maximum GUI scale."
        }
        if ($allowedScaling -and $startupLayout -match '(?m)^\s*action\s*=\s*setscale\s*$') {
            Add-MenuError "Startup layout '$name' must scale automatically, not at a fixed factor."
        }
    }

    foreach ($name in @('recast_loading_frontier.txt', 'recast_loading_works.txt', 'recast_loading_launch.txt')) {
        $loadingLayout = Get-Content -Raw -Encoding UTF8 -LiteralPath (Resolve-MenuPath "config/fancymenu/customization/$name")
        if ($loadingLayout -match 'industrial_frontier\.loading\.' -or $loadingLayout -match '"placeholder"\s*:\s*"local"') {
            Add-MenuError "Loading layout '$name' contains a localization lookup that is unavailable before Paxi resource loading."
        }
        foreach ($expected in @('width = 200', 'height = 67', 'width = 420', 'height = 104', 'y = -112', 'height = 30', 'height = 18', 'height = 16', 'width = 388', 'width = 376')) {
            if (-not $loadingLayout.Contains($expected)) {
                Add-MenuError "Loading layout '$name' is missing compact geometry token '$expected'."
            }
        }
    }
    Add-MenuPass 'All startup layouts use native maximum-GUI-scale-safe geometry; loading copy is bootstrap-safe and compact.'
}
catch {
    Add-MenuError "Startup-layout validation failed: $($_.Exception.Message)"
}

try {
    $provenancePath = Resolve-MenuPath 'docs/registries/asset_provenance.json'
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
        'config/fancymenu/assets/icon_16.png',
        'config/fancymenu/assets/icon_32.png',
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
