[CmdletBinding()]
param(
    [string]$Root = ''
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem

if ([string]::IsNullOrWhiteSpace($Root)) {
    $scriptDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
    $Root = (Resolve-Path (Join-Path $scriptDirectory '..')).Path
}

$rootPath = (Resolve-Path -LiteralPath $Root).Path
$errors = [System.Collections.Generic.List[string]]::new()
$warnings = [System.Collections.Generic.List[string]]::new()
$idLocations = @{}
$idKinds = @{}
$references = [System.Collections.Generic.List[object]]::new()
$registryDocuments = @{}
$registryRawText = @{}
$documentsByRegistryId = @{}
$zipEntriesByPath = @{}
$schemaDocumentsByPath = @{}
$schemaPathsById = @{}
$schemaKeywordAudited = @{}
$schemaValidationCount = 0
$schemaKeywordAuditCount = 0
$ruFieldCount = 0
$manifestCountsByRegistryId = @{}

function Add-ValidationError {
    param([string]$Message)
    $script:errors.Add($Message)
}

function Add-ValidationWarning {
    param([string]$Message)
    $script:warnings.Add($Message)
}

function Get-ManifestExpectedCount {
    param([string]$RegistryId, [string]$CountName)
    if (-not $script:manifestCountsByRegistryId.ContainsKey($RegistryId)) {
        Add-ValidationError "Manifest has no count map for registry '$RegistryId'."
        return $null
    }
    $countMap = $script:manifestCountsByRegistryId[$RegistryId]
    if (-not $countMap.ContainsKey($CountName)) {
        Add-ValidationError "Manifest registry '$RegistryId' lacks required derived count '$CountName'."
        return $null
    }
    return [int]$countMap[$CountName]
}

function Assert-ManifestCount {
    param(
        [string]$RegistryId,
        [string]$CountName,
        [int]$ActualCount,
        [string]$Context
    )
    $expectedCount = Get-ManifestExpectedCount -RegistryId $RegistryId -CountName $CountName
    if ($null -ne $expectedCount -and $ActualCount -ne [int]$expectedCount) {
        Add-ValidationError "$Context count disagrees with manifest: expected=$expectedCount actual=$ActualCount."
    }
}

function Has-Property {
    param($Object, [string]$Name)
    if ($null -eq $Object) { return $false }
    return $null -ne $Object.PSObject.Properties[$Name]
}

function Get-PropertyValue {
    param($Object, [string]$Name)
    if ($null -eq $Object) { return $null }
    $property = $Object.PSObject.Properties[$Name]
    if ($null -eq $property) { return $null }
    return $property.Value
}

function Get-JsonPropertyValue {
    param($Object, [string]$Name)
    if ($null -eq $Object) { return $null }
    $property = $null
    foreach ($candidate in $Object.PSObject.Properties) {
        if ([string]$candidate.Name -ceq $Name) { $property = $candidate; break }
    }
    if ($null -eq $property) { return $null }
    # The schema engine must retain the JSON distinction between [], [x], x
    # and null. PowerShell 5.1 normally unwraps arrays returned by functions.
    Write-Output -NoEnumerate $property.Value
    return
}

function Has-JsonProperty {
    param($Object, [string]$Name)
    if ($null -eq $Object) { return $false }
    foreach ($property in $Object.PSObject.Properties) {
        if ([string]$property.Name -ceq $Name) { return $true }
    }
    return $false
}

function Get-RecordId {
    param($Object)
    foreach ($name in @(
        'manifest_id', 'registry_id', 'substance_id', 'form_id', 'domain_id',
        'process_id', 'contract_id', 'network_id', 'converter_id', 'link_id',
        'decision_id', 'bypass_id', 'node_id', 'edge_id', 'dependency_id', 'gate_id', 'evidence_id',
        'component_id', 'passport_id', 'family_id'
    )) {
        $value = Get-PropertyValue -Object $Object -Name $name
        if ($value -is [string] -and -not [string]::IsNullOrWhiteSpace($value)) {
            return [string]$value
        }
    }
    return '<unidentified-entry>'
}

function Read-JsonDocument {
    param([string]$Path, [string]$Label)
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        Add-ValidationError "Missing JSON file: $Label ($Path)"
        return $null
    }
    try {
        return Get-Content -Raw -Encoding UTF8 -LiteralPath $Path | ConvertFrom-Json
    }
    catch {
        Add-ValidationError "Invalid JSON: $Label ($Path) - $($_.Exception.Message)"
        return $null
    }
}

function Normalize-RelativePath {
    param([string]$Path)
    if ([string]::IsNullOrWhiteSpace($Path)) { return '' }
    return (($Path -replace '\\', '/') -replace '^\./', '')
}

function Test-PathInsideInstanceRoot {
    param([string]$Path)
    try { $fullPath = [System.IO.Path]::GetFullPath($Path) } catch { return $false }
    if ($fullPath.Equals($rootPath, [System.StringComparison]::OrdinalIgnoreCase)) { return $true }
    $rootBoundary = $rootPath.TrimEnd([System.IO.Path]::DirectorySeparatorChar, [System.IO.Path]::AltDirectorySeparatorChar) + [System.IO.Path]::DirectorySeparatorChar
    return $fullPath.StartsWith($rootBoundary, [System.StringComparison]::OrdinalIgnoreCase)
}

function Resolve-RootRelativePath {
    param([string]$RelativePath, [string]$Context)
    if ([string]::IsNullOrWhiteSpace($RelativePath)) {
        Add-ValidationError "Empty path in $Context."
        return $null
    }
    try {
        $candidate = [System.IO.Path]::GetFullPath((Join-Path $rootPath ($RelativePath -replace '/', '\')))
    }
    catch {
        Add-ValidationError "Invalid path in ${Context}: $RelativePath"
        return $null
    }
    if (-not (Test-PathInsideInstanceRoot -Path $candidate)) {
        Add-ValidationError "Path escapes the instance root in ${Context}: $RelativePath"
        return $null
    }
    return $candidate
}

function Test-IsJsonObject {
    param($Value)
    return $Value -is [pscustomobject] -or $Value -is [System.Collections.IDictionary]
}

function Test-IsJsonArray {
    param($Value)
    return $Value -is [System.Array] -or (
        $Value -is [System.Collections.IList] -and
        $Value -isnot [string] -and
        $Value -isnot [System.Collections.IDictionary]
    )
}

function Expand-JsonSequence {
    param($Value)
    if ($null -eq $Value) { return }
    if (Test-IsJsonArray -Value $Value) {
        foreach ($item in $Value) {
            # Emit each JSON array member as one pipeline value. In particular,
            # do not let PowerShell unwrap a nested JSON array member here.
            Write-Output -NoEnumerate $item
        }
        return
    }
    Write-Output -NoEnumerate $Value
}

function Test-IsJsonNumber {
    param($Value)
    if ($null -eq $Value -or $Value -is [bool]) { return $false }
    return $Value -is [byte] -or $Value -is [sbyte] -or
        $Value -is [int16] -or $Value -is [uint16] -or
        $Value -is [int32] -or $Value -is [uint32] -or
        $Value -is [int64] -or $Value -is [uint64] -or
        $Value -is [single] -or $Value -is [double] -or $Value -is [decimal]
}

function Test-IsJsonInteger {
    param($Value)
    if (-not (Test-IsJsonNumber -Value $Value)) { return $false }
    try { return ([decimal]$Value % 1) -eq 0 } catch { return $false }
}

function Get-JsonTypeName {
    param($Value)
    if ($null -eq $Value) { return 'null' }
    if ($Value -is [bool]) { return 'boolean' }
    if ($Value -is [string]) { return 'string' }
    if (Test-IsJsonArray -Value $Value) { return 'array' }
    if (Test-IsJsonObject -Value $Value) { return 'object' }
    if (Test-IsJsonInteger -Value $Value) { return 'integer' }
    if (Test-IsJsonNumber -Value $Value) { return 'number' }
    return $Value.GetType().FullName
}

function Test-JsonInstanceType {
    param($Value, [string]$ExpectedType)
    switch -CaseSensitive ($ExpectedType) {
        'null' { return $null -eq $Value }
        'boolean' { return $Value -is [bool] }
        'string' { return $Value -is [string] }
        'array' { return Test-IsJsonArray -Value $Value }
        'object' { return Test-IsJsonObject -Value $Value }
        'integer' { return Test-IsJsonInteger -Value $Value }
        'number' { return Test-IsJsonNumber -Value $Value }
        default { return $false }
    }
}

function Test-JsonValueEqual {
    param($Left, $Right)
    if ($null -eq $Left -or $null -eq $Right) { return $null -eq $Left -and $null -eq $Right }
    if ((Test-IsJsonNumber -Value $Left) -and (Test-IsJsonNumber -Value $Right)) {
        try { return [decimal]$Left -eq [decimal]$Right } catch { return [double]$Left -eq [double]$Right }
    }
    if ($Left -is [string] -and $Right -is [string]) { return $Left -ceq $Right }
    if ($Left -is [bool] -and $Right -is [bool]) { return $Left -eq $Right }
    $leftIsArray = Test-IsJsonArray -Value $Left
    $rightIsArray = Test-IsJsonArray -Value $Right
    if ($leftIsArray -or $rightIsArray) {
        if (-not ($leftIsArray -and $rightIsArray)) { return $false }
        $leftItems = @($Left)
        $rightItems = @($Right)
        if ($leftItems.Count -ne $rightItems.Count) { return $false }
        for ($index = 0; $index -lt $leftItems.Count; $index++) {
            if (-not (Test-JsonValueEqual -Left $leftItems[$index] -Right $rightItems[$index])) { return $false }
        }
        return $true
    }
    $leftIsObject = Test-IsJsonObject -Value $Left
    $rightIsObject = Test-IsJsonObject -Value $Right
    if ($leftIsObject -or $rightIsObject) {
        if (-not ($leftIsObject -and $rightIsObject)) { return $false }
        $leftProperties = @($Left.PSObject.Properties)
        $rightProperties = @($Right.PSObject.Properties)
        if ($leftProperties.Count -ne $rightProperties.Count) { return $false }
        foreach ($leftProperty in $leftProperties) {
            $propertyName = [string]$leftProperty.Name
            if (-not (Has-JsonProperty -Object $Right -Name $propertyName)) { return $false }
            if (-not (Test-JsonValueEqual -Left $leftProperty.Value -Right (Get-JsonPropertyValue -Object $Right -Name $propertyName))) { return $false }
        }
        return $true
    }
    return $false
}

function Get-LocalSchemaDocument {
    param([string]$SchemaPath, [System.Collections.Generic.List[string]]$Problems)
    try { $fullPath = [System.IO.Path]::GetFullPath($SchemaPath) } catch {
        [void]$Problems.Add("Invalid schema path '$SchemaPath'.")
        return $null
    }
    if (-not (Test-PathInsideInstanceRoot -Path $fullPath)) {
        [void]$Problems.Add("Schema path escapes the instance root: $SchemaPath")
        return $null
    }
    if ($schemaDocumentsByPath.ContainsKey($fullPath)) { return $schemaDocumentsByPath[$fullPath] }
    if (-not (Test-Path -LiteralPath $fullPath -PathType Leaf)) {
        [void]$Problems.Add("Schema file does not exist: $fullPath")
        return $null
    }
    try {
        $document = Get-Content -Raw -Encoding UTF8 -LiteralPath $fullPath | ConvertFrom-Json
    }
    catch {
        [void]$Problems.Add("Invalid schema JSON '$fullPath': $($_.Exception.Message)")
        return $null
    }
    $schemaDocumentsByPath[$fullPath] = $document
    $schemaId = Get-JsonPropertyValue -Object $document -Name '$id'
    if ($schemaId -is [string] -and -not [string]::IsNullOrWhiteSpace([string]$schemaId)) {
        if ($schemaPathsById.ContainsKey([string]$schemaId) -and [string]$schemaPathsById[[string]$schemaId] -ne $fullPath) {
            [void]$Problems.Add("Duplicate schema `$id '$schemaId': $($schemaPathsById[[string]$schemaId]) and $fullPath")
        }
        else {
            $schemaPathsById[[string]$schemaId] = $fullPath
        }
    }
    return $document
}

function Resolve-JsonSchemaReference {
    param(
        [string]$Reference,
        $CurrentRoot,
        [string]$CurrentSchemaPath,
        [System.Collections.Generic.List[string]]$Problems
    )
    if ([string]::IsNullOrWhiteSpace($Reference)) {
        [void]$Problems.Add('Schema contains an empty $ref.')
        return $null
    }
    $parts = $Reference -split '#', 2
    $documentPart = [string]$parts[0]
    $fragment = if ($parts.Count -eq 2) { [string]$parts[1] } else { '' }
    $targetRoot = $CurrentRoot
    $targetSchemaPath = $CurrentSchemaPath

    if (-not [string]::IsNullOrWhiteSpace($documentPart)) {
        if ($documentPart -match '^https?://') {
            if (-not $schemaPathsById.ContainsKey($documentPart)) {
                [void]$Problems.Add("Remote schema `$ref is not mapped to a local `$id: $Reference")
                return $null
            }
            $targetSchemaPath = [string]$schemaPathsById[$documentPart]
        }
        else {
            $targetSchemaPath = [System.IO.Path]::GetFullPath((Join-Path (Split-Path -Parent $CurrentSchemaPath) ($documentPart -replace '/', '\')))
        }
        $targetRoot = Get-LocalSchemaDocument -SchemaPath $targetSchemaPath -Problems $Problems
        if ($null -eq $targetRoot) { return $null }
    }

    $target = $targetRoot
    if (-not [string]::IsNullOrWhiteSpace($fragment)) {
        if (-not $fragment.StartsWith('/', [System.StringComparison]::Ordinal)) {
            [void]$Problems.Add("Only JSON Pointer schema fragments are supported locally: $Reference")
            return $null
        }
        foreach ($encodedToken in ($fragment.Substring(1) -split '/')) {
            $token = [System.Uri]::UnescapeDataString($encodedToken).Replace('~1', '/').Replace('~0', '~')
            if (Test-IsJsonArray -Value $target) {
                $index = 0
                if (-not [int]::TryParse($token, [ref]$index) -or $index -lt 0 -or $index -ge @($target).Count) {
                    [void]$Problems.Add("Unresolved array token '$token' in schema `$ref '$Reference'.")
                    return $null
                }
                $target = @($target)[$index]
            }
            elseif (Test-IsJsonObject -Value $target) {
                if (-not (Has-JsonProperty -Object $target -Name $token)) {
                    [void]$Problems.Add("Unresolved object token '$token' in schema `$ref '$Reference'.")
                    return $null
                }
                $target = Get-JsonPropertyValue -Object $target -Name $token
            }
            else {
                [void]$Problems.Add("Schema `$ref '$Reference' traverses a scalar at '$token'.")
                return $null
            }
        }
    }
    return [pscustomobject]@{
        schema = $target
        root = $targetRoot
        path = $targetSchemaPath
    }
}

function Assert-SupportedSchemaKeywords {
    param(
        $Schema,
        [string]$Location,
        [System.Collections.Generic.List[string]]$Problems
    )
    if ($Schema -is [bool]) { return }
    if (-not (Test-IsJsonObject -Value $Schema)) {
        [void]$Problems.Add("Schema node is not an object or boolean at $Location.")
        return
    }
    $supported = @(
        '$schema', '$id', '$ref', '$defs', 'title', 'description',
        'type', 'const', 'enum', 'required', 'properties', 'additionalProperties',
        'propertyNames', 'minProperties', 'patternProperties',
        'items', 'prefixItems', 'minItems', 'maxItems', 'uniqueItems',
        'minLength', 'pattern', 'format', 'minimum', 'maximum', 'exclusiveMinimum',
        'allOf', 'anyOf', 'oneOf', 'if', 'then', 'else', 'not'
    )
    foreach ($property in $Schema.PSObject.Properties) {
        $keyword = [string]$property.Name
        if ($supported -cnotcontains $keyword) {
            [void]$Problems.Add("Unsupported schema keyword '$keyword' at $Location.")
            continue
        }
        $value = $property.Value
        switch -CaseSensitive ($keyword) {
            { $_ -cin @('properties', 'patternProperties', '$defs') } {
                if (-not (Test-IsJsonObject -Value $value)) {
                    [void]$Problems.Add("Schema keyword '$keyword' must be an object at $Location.")
                    break
                }
                foreach ($child in $value.PSObject.Properties) {
                    if ($keyword -eq 'patternProperties') {
                        try { [void][regex]::new([string]$child.Name) } catch {
                            [void]$Problems.Add("Invalid patternProperties regex '$($child.Name)' at $Location.")
                        }
                    }
                    Assert-SupportedSchemaKeywords -Schema $child.Value -Location "$Location.$keyword.$($child.Name)" -Problems $Problems
                }
            }
            { $_ -cin @('allOf', 'anyOf', 'oneOf', 'prefixItems') } {
                if (-not (Test-IsJsonArray -Value $value) -or $value.Count -eq 0) {
                    [void]$Problems.Add("Schema keyword '$keyword' must be a non-empty array at $Location.")
                    break
                }
                $index = 0
                foreach ($child in $value) {
                    Assert-SupportedSchemaKeywords -Schema $child -Location "$Location.$keyword[$index]" -Problems $Problems
                    $index++
                }
            }
            { $_ -cin @('items', 'additionalProperties', 'propertyNames', 'if', 'then', 'else', 'not') } {
                if ($value -is [bool] -or (Test-IsJsonObject -Value $value)) {
                    Assert-SupportedSchemaKeywords -Schema $value -Location "$Location.$keyword" -Problems $Problems
                }
                else {
                    [void]$Problems.Add("Schema keyword '$keyword' must contain a schema at $Location.")
                }
            }
            'type' {
                $types = @($value)
                if (($value -isnot [string] -and -not (Test-IsJsonArray -Value $value)) -or $types.Count -eq 0) {
                    [void]$Problems.Add("Schema type must be a string or non-empty array at $Location.")
                    break
                }
                $seenTypes = @{}
                foreach ($declaredType in $types) {
                    if ($declaredType -isnot [string] -or [string]$declaredType -cnotin @('null', 'boolean', 'string', 'array', 'object', 'integer', 'number')) {
                        [void]$Problems.Add("Invalid schema type '$declaredType' at $Location.")
                    }
                    elseif ($seenTypes.ContainsKey([string]$declaredType)) {
                        [void]$Problems.Add("Duplicate schema type '$declaredType' at $Location.")
                    }
                    else { $seenTypes[[string]$declaredType] = $true }
                }
            }
            'enum' {
                if (-not (Test-IsJsonArray -Value $value) -or $value.Count -eq 0) {
                    [void]$Problems.Add("Schema enum must be a non-empty array at $Location.")
                    break
                }
                for ($index = 0; $index -lt $value.Count; $index++) {
                    for ($previousIndex = 0; $previousIndex -lt $index; $previousIndex++) {
                        if (Test-JsonValueEqual -Left $value[$index] -Right $value[$previousIndex]) {
                            [void]$Problems.Add("Schema enum has duplicate values at indexes $previousIndex and $index at $Location.")
                            break
                        }
                    }
                }
            }
            'required' {
                if (-not (Test-IsJsonArray -Value $value)) {
                    [void]$Problems.Add("Schema required must be an array at $Location.")
                    break
                }
                $seenRequired = @{}
                foreach ($requiredName in $value) {
                    if ($requiredName -isnot [string]) {
                        [void]$Problems.Add("Schema required contains a non-string value at $Location.")
                    }
                    elseif ($seenRequired.ContainsKey([string]$requiredName)) {
                        [void]$Problems.Add("Schema required repeats '$requiredName' at $Location.")
                    }
                    else { $seenRequired[[string]$requiredName] = $true }
                }
            }
            { $_ -cin @('minProperties', 'minItems', 'maxItems', 'minLength') } {
                if (-not (Test-IsJsonInteger -Value $value) -or [decimal]$value -lt 0) {
                    [void]$Problems.Add("Schema keyword '$keyword' must be a non-negative integer at $Location.")
                }
            }
            { $_ -cin @('minimum', 'maximum', 'exclusiveMinimum') } {
                if (-not (Test-IsJsonNumber -Value $value)) {
                    [void]$Problems.Add("Schema keyword '$keyword' must be numeric at $Location.")
                }
            }
            'uniqueItems' {
                if ($value -isnot [bool]) { [void]$Problems.Add("Schema uniqueItems must be boolean at $Location.") }
            }
            'pattern' {
                if ($value -isnot [string]) {
                    [void]$Problems.Add("Schema pattern must be a string at $Location.")
                }
                else {
                    try { [void][regex]::new([string]$value) } catch {
                        [void]$Problems.Add("Invalid schema pattern '$value' at $Location.")
                    }
                }
            }
            { $_ -cin @('$schema', '$id', '$ref', 'title', 'description') } {
                if ($value -isnot [string]) { [void]$Problems.Add("Schema keyword '$keyword' must be a string at $Location.") }
            }
            'format' {
                if ($value -isnot [string] -or [string]$value -cne 'date') {
                    [void]$Problems.Add("Unsupported schema format '$value' at $Location.format.")
                }
            }
        }
    }
}

function Test-JsonSchemaNode {
    param(
        $Instance,
        $Schema,
        $SchemaRoot,
        [string]$SchemaPath,
        [string]$InstancePath,
        [System.Collections.Generic.List[string]]$Problems,
        [int]$Depth = 0
    )
    if ($Depth -gt 256) {
        [void]$Problems.Add("Schema recursion limit exceeded at $InstancePath.")
        return
    }
    if ($Schema -is [bool]) {
        if (-not $Schema) { [void]$Problems.Add("Boolean false schema rejected $InstancePath.") }
        return
    }
    if (-not (Test-IsJsonObject -Value $Schema)) {
        [void]$Problems.Add("Invalid schema node while validating $InstancePath.")
        return
    }

    if (Has-JsonProperty -Object $Schema -Name '$ref') {
        $reference = [string](Get-JsonPropertyValue -Object $Schema -Name '$ref')
        $resolved = Resolve-JsonSchemaReference -Reference $reference -CurrentRoot $SchemaRoot -CurrentSchemaPath $SchemaPath -Problems $Problems
        if ($null -ne $resolved) {
            Test-JsonSchemaNode -Instance $Instance -Schema $resolved.schema -SchemaRoot $resolved.root -SchemaPath $resolved.path -InstancePath $InstancePath -Problems $Problems -Depth ($Depth + 1)
        }
    }

    if (Has-JsonProperty -Object $Schema -Name 'type') {
        $typeMatches = $false
        $declaredTypes = @(Expand-JsonSequence -Value (Get-JsonPropertyValue -Object $Schema -Name 'type'))
        foreach ($declaredType in $declaredTypes) {
            if ($declaredType -isnot [string] -or [string]$declaredType -cnotin @('null', 'boolean', 'string', 'array', 'object', 'integer', 'number')) {
                [void]$Problems.Add("Schema has invalid type declaration at $InstancePath.")
                continue
            }
            if (Test-JsonInstanceType -Value $Instance -ExpectedType ([string]$declaredType)) { $typeMatches = $true }
        }
        if (-not $typeMatches) {
            [void]$Problems.Add("$InstancePath has JSON type '$(Get-JsonTypeName $Instance)', expected [$($declaredTypes -join ', ')].")
            return
        }
    }

    if (Has-JsonProperty -Object $Schema -Name 'const') {
        if (-not (Test-JsonValueEqual -Left $Instance -Right (Get-JsonPropertyValue -Object $Schema -Name 'const'))) {
            [void]$Problems.Add("$InstancePath does not equal the schema const value.")
        }
    }
    if (Has-JsonProperty -Object $Schema -Name 'enum') {
        $enumMatch = $false
        $enumValues = Get-JsonPropertyValue -Object $Schema -Name 'enum'
        if (-not (Test-IsJsonArray -Value $enumValues)) {
            [void]$Problems.Add("Schema enum is not an array at $InstancePath.")
        }
        else {
            for ($enumIndex = 0; $enumIndex -lt $enumValues.Count; $enumIndex++) {
                if (Test-JsonValueEqual -Left $Instance -Right $enumValues[$enumIndex]) { $enumMatch = $true; break }
            }
        }
        if (-not $enumMatch) { [void]$Problems.Add("$InstancePath is not one of the schema enum values.") }
    }

    if (Test-IsJsonNumber -Value $Instance) {
        $numericValue = [decimal]$Instance
        if ((Has-JsonProperty -Object $Schema -Name 'minimum') -and ($numericValue -lt [decimal](Get-JsonPropertyValue -Object $Schema -Name 'minimum'))) {
            [void]$Problems.Add("$InstancePath is below minimum $(Get-JsonPropertyValue $Schema 'minimum').")
        }
        if ((Has-JsonProperty -Object $Schema -Name 'maximum') -and ($numericValue -gt [decimal](Get-JsonPropertyValue -Object $Schema -Name 'maximum'))) {
            [void]$Problems.Add("$InstancePath exceeds maximum $(Get-JsonPropertyValue $Schema 'maximum').")
        }
        if ((Has-JsonProperty -Object $Schema -Name 'exclusiveMinimum') -and ($numericValue -le [decimal](Get-JsonPropertyValue -Object $Schema -Name 'exclusiveMinimum'))) {
            [void]$Problems.Add("$InstancePath must be greater than $(Get-JsonPropertyValue $Schema 'exclusiveMinimum').")
        }
    }

    if ($Instance -is [string]) {
        if ((Has-JsonProperty -Object $Schema -Name 'minLength') -and ($Instance.Length -lt [int](Get-JsonPropertyValue -Object $Schema -Name 'minLength'))) {
            [void]$Problems.Add("$InstancePath is shorter than minLength $(Get-JsonPropertyValue $Schema 'minLength').")
        }
        if (Has-JsonProperty -Object $Schema -Name 'pattern') {
            $pattern = [string](Get-JsonPropertyValue -Object $Schema -Name 'pattern')
            try { $patternMatches = [regex]::IsMatch($Instance, $pattern) } catch {
                [void]$Problems.Add("Schema pattern is invalid at ${InstancePath}: $pattern")
                $patternMatches = $true
            }
            if (-not $patternMatches) { [void]$Problems.Add("$InstancePath does not match pattern '$pattern'.") }
        }
        if (Has-JsonProperty -Object $Schema -Name 'format') {
            $format = [string](Get-JsonPropertyValue -Object $Schema -Name 'format')
            if ($format -ceq 'date') {
                $parsedDate = [datetime]::MinValue
                if (-not [datetime]::TryParseExact($Instance, 'yyyy-MM-dd', [System.Globalization.CultureInfo]::InvariantCulture, [System.Globalization.DateTimeStyles]::None, [ref]$parsedDate)) {
                    [void]$Problems.Add("$InstancePath is not a strict YYYY-MM-DD date.")
                }
            }
            else {
                [void]$Problems.Add("$InstancePath uses unsupported schema format '$format'.")
            }
        }
    }

    if (Test-IsJsonArray -Value $Instance) {
        $items = @($Instance)
        if ((Has-JsonProperty -Object $Schema -Name 'minItems') -and ($items.Count -lt [int](Get-JsonPropertyValue -Object $Schema -Name 'minItems'))) {
            [void]$Problems.Add("$InstancePath has fewer than $(Get-JsonPropertyValue $Schema 'minItems') items.")
        }
        if ((Has-JsonProperty -Object $Schema -Name 'maxItems') -and ($items.Count -gt [int](Get-JsonPropertyValue -Object $Schema -Name 'maxItems'))) {
            [void]$Problems.Add("$InstancePath has more than $(Get-JsonPropertyValue $Schema 'maxItems') items.")
        }
        if ((Get-JsonPropertyValue -Object $Schema -Name 'uniqueItems') -eq $true) {
            for ($index = 0; $index -lt $items.Count; $index++) {
                for ($previousIndex = 0; $previousIndex -lt $index; $previousIndex++) {
                    if (Test-JsonValueEqual -Left $items[$index] -Right $items[$previousIndex]) {
                        [void]$Problems.Add("$InstancePath has duplicate array item at index $index (matches index $previousIndex).")
                        break
                    }
                }
            }
        }
        $prefixSchemas = @()
        if (Has-JsonProperty -Object $Schema -Name 'prefixItems') {
            $prefixSchemas = @(Expand-JsonSequence -Value (Get-JsonPropertyValue -Object $Schema -Name 'prefixItems'))
            $prefixCount = [Math]::Min($items.Count, $prefixSchemas.Count)
            for ($index = 0; $index -lt $prefixCount; $index++) {
                Test-JsonSchemaNode -Instance $items[$index] -Schema $prefixSchemas[$index] -SchemaRoot $SchemaRoot -SchemaPath $SchemaPath -InstancePath "$InstancePath[$index]" -Problems $Problems -Depth ($Depth + 1)
            }
        }
        if (Has-JsonProperty -Object $Schema -Name 'items') {
            $itemSchema = Get-JsonPropertyValue -Object $Schema -Name 'items'
            for ($index = $prefixSchemas.Count; $index -lt $items.Count; $index++) {
                Test-JsonSchemaNode -Instance $items[$index] -Schema $itemSchema -SchemaRoot $SchemaRoot -SchemaPath $SchemaPath -InstancePath "$InstancePath[$index]" -Problems $Problems -Depth ($Depth + 1)
            }
        }
    }

    if (Test-IsJsonObject -Value $Instance) {
        $instanceProperties = @($Instance.PSObject.Properties)
        if ((Has-JsonProperty -Object $Schema -Name 'minProperties') -and ($instanceProperties.Count -lt [int](Get-JsonPropertyValue -Object $Schema -Name 'minProperties'))) {
            [void]$Problems.Add("$InstancePath has fewer than $(Get-JsonPropertyValue $Schema 'minProperties') properties.")
        }
        if (Has-JsonProperty -Object $Schema -Name 'required') {
            foreach ($requiredName in @(Expand-JsonSequence -Value (Get-JsonPropertyValue -Object $Schema -Name 'required'))) {
                if (-not (Has-JsonProperty -Object $Instance -Name ([string]$requiredName))) {
                    [void]$Problems.Add("$InstancePath is missing required property '$requiredName'.")
                }
            }
        }
        $propertySchemas = Get-JsonPropertyValue -Object $Schema -Name 'properties'
        if ($null -ne $propertySchemas) {
            foreach ($propertySchema in $propertySchemas.PSObject.Properties) {
                $propertyName = [string]$propertySchema.Name
                if (Has-JsonProperty -Object $Instance -Name $propertyName) {
                    Test-JsonSchemaNode -Instance (Get-JsonPropertyValue -Object $Instance -Name $propertyName) -Schema $propertySchema.Value -SchemaRoot $SchemaRoot -SchemaPath $SchemaPath -InstancePath "$InstancePath.$propertyName" -Problems $Problems -Depth ($Depth + 1)
                }
            }
        }
        if (Has-JsonProperty -Object $Schema -Name 'propertyNames') {
            $propertyNameSchema = Get-JsonPropertyValue -Object $Schema -Name 'propertyNames'
            foreach ($instanceProperty in $instanceProperties) {
                Test-JsonSchemaNode -Instance ([string]$instanceProperty.Name) -Schema $propertyNameSchema -SchemaRoot $SchemaRoot -SchemaPath $SchemaPath -InstancePath "$InstancePath.<property:$($instanceProperty.Name)>" -Problems $Problems -Depth ($Depth + 1)
            }
        }
        $patternSchemas = Get-JsonPropertyValue -Object $Schema -Name 'patternProperties'
        if ($null -ne $patternSchemas) {
            foreach ($instanceProperty in $instanceProperties) {
                foreach ($patternSchema in $patternSchemas.PSObject.Properties) {
                    if ([regex]::IsMatch([string]$instanceProperty.Name, [string]$patternSchema.Name)) {
                        Test-JsonSchemaNode -Instance $instanceProperty.Value -Schema $patternSchema.Value -SchemaRoot $SchemaRoot -SchemaPath $SchemaPath -InstancePath "$InstancePath.$($instanceProperty.Name)" -Problems $Problems -Depth ($Depth + 1)
                    }
                }
            }
        }
        if (Has-JsonProperty -Object $Schema -Name 'additionalProperties') {
            $additionalSchema = Get-JsonPropertyValue -Object $Schema -Name 'additionalProperties'
            foreach ($instanceProperty in $instanceProperties) {
                $propertyName = [string]$instanceProperty.Name
                $declared = $null -ne $propertySchemas -and (Has-JsonProperty -Object $propertySchemas -Name $propertyName)
                $patternMatched = $false
                if ($null -ne $patternSchemas) {
                    foreach ($patternSchema in $patternSchemas.PSObject.Properties) {
                        if ([regex]::IsMatch($propertyName, [string]$patternSchema.Name)) { $patternMatched = $true; break }
                    }
                }
                if ($declared -or $patternMatched) { continue }
                if ($additionalSchema -is [bool]) {
                    if (-not $additionalSchema) { [void]$Problems.Add("$InstancePath has forbidden additional property '$propertyName'.") }
                }
                elseif ($null -ne $additionalSchema) {
                    Test-JsonSchemaNode -Instance $instanceProperty.Value -Schema $additionalSchema -SchemaRoot $SchemaRoot -SchemaPath $SchemaPath -InstancePath "$InstancePath.$propertyName" -Problems $Problems -Depth ($Depth + 1)
                }
            }
        }
    }

    if (Has-JsonProperty -Object $Schema -Name 'allOf') {
        foreach ($branch in @(Expand-JsonSequence -Value (Get-JsonPropertyValue -Object $Schema -Name 'allOf'))) {
            Test-JsonSchemaNode -Instance $Instance -Schema $branch -SchemaRoot $SchemaRoot -SchemaPath $SchemaPath -InstancePath $InstancePath -Problems $Problems -Depth ($Depth + 1)
        }
    }
    if (Has-JsonProperty -Object $Schema -Name 'anyOf') {
        $matchingBranches = 0
        foreach ($branch in @(Expand-JsonSequence -Value (Get-JsonPropertyValue -Object $Schema -Name 'anyOf'))) {
            $branchProblems = [System.Collections.Generic.List[string]]::new()
            Test-JsonSchemaNode -Instance $Instance -Schema $branch -SchemaRoot $SchemaRoot -SchemaPath $SchemaPath -InstancePath $InstancePath -Problems $branchProblems -Depth ($Depth + 1)
            if ($branchProblems.Count -eq 0) { $matchingBranches++ }
        }
        if ($matchingBranches -eq 0) { [void]$Problems.Add("$InstancePath does not match any anyOf branch.") }
    }
    if (Has-JsonProperty -Object $Schema -Name 'oneOf') {
        $matchingBranches = 0
        foreach ($branch in @(Expand-JsonSequence -Value (Get-JsonPropertyValue -Object $Schema -Name 'oneOf'))) {
            $branchProblems = [System.Collections.Generic.List[string]]::new()
            Test-JsonSchemaNode -Instance $Instance -Schema $branch -SchemaRoot $SchemaRoot -SchemaPath $SchemaPath -InstancePath $InstancePath -Problems $branchProblems -Depth ($Depth + 1)
            if ($branchProblems.Count -eq 0) { $matchingBranches++ }
        }
        if ($matchingBranches -ne 1) { [void]$Problems.Add("$InstancePath must match exactly one oneOf branch; matched $matchingBranches.") }
    }
    if (Has-JsonProperty -Object $Schema -Name 'if') {
        $ifProblems = [System.Collections.Generic.List[string]]::new()
        Test-JsonSchemaNode -Instance $Instance -Schema (Get-JsonPropertyValue -Object $Schema -Name 'if') -SchemaRoot $SchemaRoot -SchemaPath $SchemaPath -InstancePath $InstancePath -Problems $ifProblems -Depth ($Depth + 1)
        if ($ifProblems.Count -eq 0 -and (Has-JsonProperty -Object $Schema -Name 'then')) {
            Test-JsonSchemaNode -Instance $Instance -Schema (Get-JsonPropertyValue -Object $Schema -Name 'then') -SchemaRoot $SchemaRoot -SchemaPath $SchemaPath -InstancePath $InstancePath -Problems $Problems -Depth ($Depth + 1)
        }
        elseif ($ifProblems.Count -gt 0 -and (Has-JsonProperty -Object $Schema -Name 'else')) {
            Test-JsonSchemaNode -Instance $Instance -Schema (Get-JsonPropertyValue -Object $Schema -Name 'else') -SchemaRoot $SchemaRoot -SchemaPath $SchemaPath -InstancePath $InstancePath -Problems $Problems -Depth ($Depth + 1)
        }
    }
    if (Has-JsonProperty -Object $Schema -Name 'not') {
        $notProblems = [System.Collections.Generic.List[string]]::new()
        Test-JsonSchemaNode -Instance $Instance -Schema (Get-JsonPropertyValue -Object $Schema -Name 'not') -SchemaRoot $SchemaRoot -SchemaPath $SchemaPath -InstancePath $InstancePath -Problems $notProblems -Depth ($Depth + 1)
        if ($notProblems.Count -eq 0) { [void]$Problems.Add("$InstancePath matches a forbidden not schema.") }
    }
}

function Invoke-LocalJsonSchemaValidation {
    param($Instance, [string]$SchemaPath, [string]$Label)
    $problems = [System.Collections.Generic.List[string]]::new()
    $schema = Get-LocalSchemaDocument -SchemaPath $SchemaPath -Problems $problems
    if ($null -ne $schema) {
        Test-JsonSchemaNode -Instance $Instance -Schema $schema -SchemaRoot $schema -SchemaPath ([System.IO.Path]::GetFullPath($SchemaPath)) -InstancePath '$' -Problems $problems
    }
    foreach ($problem in $problems) {
        Add-ValidationError "Schema violation [$Label]: $problem"
    }
    $script:schemaValidationCount++
}

function Add-IdDeclaration {
    param([string]$Id, [string]$Kind, [string]$Location)
    if ([string]::IsNullOrWhiteSpace($Id) -or -not $Id.StartsWith('industrial_frontier:', [System.StringComparison]::Ordinal)) {
        return
    }
    if ($idLocations.ContainsKey($Id)) {
        Add-ValidationError "Duplicate industrial_frontier ID '$Id': $($idLocations[$Id]) and $Location"
        return
    }
    $idLocations[$Id] = $Location
    $idKinds[$Id] = $Kind
}

function Add-ReferenceValue {
    param($Value, [string]$PropertyName, [string]$Location)
    foreach ($candidate in @($Value)) {
        if ($candidate -isnot [string]) { continue }
        $reference = [string]$candidate
        if ($reference.StartsWith('#', [System.StringComparison]::Ordinal)) { continue }
        if (-not $reference.StartsWith('industrial_frontier:', [System.StringComparison]::Ordinal)) { continue }
        $references.Add([pscustomobject]@{
            value = $reference
            property = $PropertyName
            location = $Location
        })
    }
}

function Visit-RegistryNode {
    param($Node, [string]$Location)
    if ($null -eq $Node -or $Node -is [string] -or $Node -is [System.ValueType]) { return }

    if ($Node -is [System.Collections.IEnumerable] -and $Node -isnot [System.Collections.IDictionary] -and $Node -isnot [pscustomobject]) {
        $index = 0
        foreach ($item in $Node) {
            Visit-RegistryNode -Node $item -Location "$Location[$index]"
            $index++
        }
        return
    }

    foreach ($property in $Node.PSObject.Properties) {
        $name = [string]$property.Name
        $value = $property.Value
        $propertyLocation = "$Location.$name"

        if ($name -match '(^|_)id$' -and $value -is [string] -and ([string]$value).StartsWith('industrial_frontier:', [System.StringComparison]::Ordinal)) {
            Add-IdDeclaration -Id ([string]$value) -Kind $name -Location $propertyLocation
        }

        if ($name -match '(_ru$|^russian_term$|^ru_name$|^name_ru$|^title_ru$)') {
            $script:ruFieldCount++
            if ($value -is [string]) {
                if ([string]::IsNullOrWhiteSpace([string]$value)) {
                    Add-ValidationError "Empty Russian term at $propertyLocation."
                }
            }
            elseif ($value -is [System.Collections.IEnumerable]) {
                $values = @($value)
                if ($values.Count -eq 0) {
                    Add-ValidationError "Empty Russian term list at $propertyLocation."
                }
                foreach ($term in $values) {
                    if ($term -isnot [string] -or [string]::IsNullOrWhiteSpace([string]$term)) {
                        Add-ValidationError "Invalid Russian term in $propertyLocation."
                    }
                }
            }
            else {
                Add-ValidationError "Russian term is not text at $propertyLocation."
            }
        }

        if ($name -match '(_ref|_refs)$') {
            Add-ReferenceValue -Value $value -PropertyName $name -Location $propertyLocation
        }

        Visit-RegistryNode -Node $value -Location $propertyLocation
    }
}

function Get-ZipEntryNames {
    param([string]$ArchivePath)
    if ($zipEntriesByPath.ContainsKey($ArchivePath)) {
        return @($zipEntriesByPath[$ArchivePath])
    }
    try {
        $archive = [System.IO.Compression.ZipFile]::OpenRead($ArchivePath)
        try {
            $names = @($archive.Entries | ForEach-Object { $_.FullName })
            $zipEntriesByPath[$ArchivePath] = $names
            return $names
        }
        finally {
            $archive.Dispose()
        }
    }
    catch {
        Add-ValidationError "Cannot inspect evidence archive '$ArchivePath': $($_.Exception.Message)"
        return @()
    }
}

function Test-EvidencePath {
    param($Evidence, [string]$Location)
    $evidenceId = [string](Get-PropertyValue -Object $Evidence -Name 'evidence_id')
    foreach ($required in @('evidence_id', 'type', 'path', 'locator', 'observed', 'verified_on', 'static_only')) {
        if (-not (Has-Property -Object $Evidence -Name $required)) {
            Add-ValidationError "Evidence '$evidenceId' lacks '$required' at $Location."
        }
    }
    if ($evidenceId -notmatch '^industrial_frontier:evidence/[a-z0-9_./-]+$') {
        Add-ValidationError "Invalid evidence ID '$evidenceId' at $Location."
    }
    foreach ($textField in @('type', 'path', 'locator', 'observed', 'verified_on')) {
        $textValue = Get-PropertyValue -Object $Evidence -Name $textField
        if ($textValue -isnot [string] -or [string]::IsNullOrWhiteSpace([string]$textValue)) {
            Add-ValidationError "Evidence '$evidenceId' has empty '$textField'."
        }
    }
    $staticOnly = Get-PropertyValue -Object $Evidence -Name 'static_only'
    if ($staticOnly -isnot [bool]) {
        Add-ValidationError "Evidence '$evidenceId' must declare boolean static_only."
    }

    $evidencePath = [string](Get-PropertyValue -Object $Evidence -Name 'path')
    if ([string]::IsNullOrWhiteSpace($evidencePath)) { return }
    if ($evidencePath -match '^https?://') {
        Add-ValidationError "Evidence '$evidenceId' must point to a local immutable file or JAR entry, not a remote URL."
        return
    }
    $segments = $evidencePath -split '!', 2
    $outerPath = Resolve-RootRelativePath -RelativePath $segments[0] -Context "evidence '$evidenceId'"
    if ($null -eq $outerPath) { return }
    if (-not (Test-Path -LiteralPath $outerPath)) {
        Add-ValidationError "Evidence source does not exist for '$evidenceId': $($segments[0])"
        return
    }
    if ($segments.Count -ne 2) { return }
    if (-not (Test-Path -LiteralPath $outerPath -PathType Leaf)) {
        Add-ValidationError "Evidence archive is not a file for '$evidenceId': $($segments[0])"
        return
    }
    $innerPath = ($segments[1].TrimStart('/') -replace '\\', '/')
    if ([string]::IsNullOrWhiteSpace($innerPath)) {
        Add-ValidationError "Evidence '$evidenceId' has an empty archive-internal path."
        return
    }
    $entryNames = @(Get-ZipEntryNames -ArchivePath $outerPath)
    $entryFound = $false
    foreach ($entryName in $entryNames) {
        if ($entryName -eq $innerPath -or $entryName.StartsWith(($innerPath.TrimEnd('/') + '/'), [System.StringComparison]::Ordinal)) {
            $entryFound = $true
            break
        }
    }
    if (-not $entryFound) {
        Add-ValidationError "Evidence archive path does not exist for '$evidenceId': $evidencePath"
    }
}

function Require-EntryEvidenceAndGate {
    param($Entry, [string]$Collection, [string]$RegistryPath)
    $entryId = Get-RecordId -Object $Entry
    $evidenceRefs = @(Get-PropertyValue -Object $Entry -Name 'evidence_refs')
    $gateRefs = @(Get-PropertyValue -Object $Entry -Name 'gate_refs')
    if ($evidenceRefs.Count -eq 0 -or @($evidenceRefs | Where-Object { $_ -is [string] -and -not [string]::IsNullOrWhiteSpace($_) }).Count -eq 0) {
        Add-ValidationError "Entry '$entryId' in $Collection ($RegistryPath) has no source evidence."
    }
    if ($gateRefs.Count -eq 0 -or @($gateRefs | Where-Object { $_ -is [string] -and -not [string]::IsNullOrWhiteSpace($_) }).Count -eq 0) {
        Add-ValidationError "Entry '$entryId' in $Collection ($RegistryPath) has no explicit gate."
    }
}

function Get-ExpectedReferenceKind {
    param([string]$PropertyName)
    switch -Regex ($PropertyName) {
        '^evidence_refs$' { return 'evidence_id' }
        '(^|_)gate_ref$|^gate_refs$' { return 'gate_id' }
        '(^|_)substance_ref$|(^|_)substance_refs$|^byproduct_refs$' { return 'substance_id' }
        '(^|_)form_refs$|^target_form_ref$' { return 'form_id' }
        'domain_ref$|domain_refs$' { return 'domain_id' }
        'network_ref$|network_refs$' { return 'network_id' }
        '^contract_refs$' { return 'contract_id' }
        '^grind_chain_refs$' { return 'chain_id' }
        '^budget_ref$' { return 'chain_id' }
        '^critical_component_refs$' { return 'component_id' }
        '^process_refs$' { return 'process_id' }
        '^resource_(?:input|output)_refs$' { return 'substance_id' }
        '^world_origin_decision_ref$' { return 'decision_id' }
        default { return $null }
    }
}

function Assert-BooleanConfigValue {
    param([string]$RelativePath, [string]$Key, [bool]$Expected)
    $path = Resolve-RootRelativePath -RelativePath $RelativePath -Context "config decision $Key"
    if ($null -eq $path -or -not (Test-Path -LiteralPath $path -PathType Leaf)) {
        Add-ValidationError "Missing config for decision '$Key': $RelativePath"
        return
    }
    $text = Get-Content -Raw -Encoding UTF8 -LiteralPath $path
    $pattern = '(?mi)^\s*{0}\s*[:=]\s*(true|false)\s*(?:#.*)?$' -f [regex]::Escape($Key)
    $matches = [regex]::Matches($text, $pattern)
    if ($matches.Count -eq 0) {
        Add-ValidationError "Config key '$Key' is absent from $RelativePath."
        return
    }
    if ($matches.Count -gt 1) {
        Add-ValidationError "Config key '$Key' is declared more than once in $RelativePath."
        return
    }
    $actual = $matches[0].Groups[1].Value -ieq 'true'
    if ($actual -ne $Expected) {
        Add-ValidationError "Config decision mismatch: $RelativePath#$Key expected=$Expected actual=$actual"
    }
}

function Find-ObjectById {
    param($Items, [string]$IdField, [string]$Id)
    foreach ($item in @($Items)) {
        if ([string](Get-PropertyValue -Object $item -Name $IdField) -eq $Id) { return $item }
    }
    return $null
}

function Assert-WorldgenCheck {
    param($WorldgenRegistry, [string]$DecisionId, [string]$Key, [string]$Expected)
    $decision = Find-ObjectById -Items (Get-PropertyValue -Object $WorldgenRegistry -Name 'ownership_decisions') -IdField 'decision_id' -Id $DecisionId
    if ($null -eq $decision) {
        Add-ValidationError "Missing worldgen decision '$DecisionId'."
        return
    }
    $matching = @((Get-PropertyValue -Object $decision -Name 'implementation_checks') | Where-Object {
        [string](Get-PropertyValue -Object $_ -Name 'key_or_resource') -eq $Key -and
        [string](Get-PropertyValue -Object $_ -Name 'expected') -ieq $Expected
    })
    if ($matching.Count -ne 1) {
        Add-ValidationError "Worldgen decision '$DecisionId' must contain exactly one '$Key=$Expected' implementation check."
    }
}

function Get-EpochNumber {
    param($Value)
    if (Test-IsJsonInteger -Value $Value) {
        $number = [int]$Value
        if ($number -ge 0 -and $number -le 9) { return $number }
        return $null
    }
    if ($Value -is [string] -and [string]$Value -cmatch '^P([0-9])$') {
        return [int]$Matches[1]
    }
    return $null
}

function Test-CoreDependencyRefsObject {
    param(
        $Owner,
        [string]$Context,
        $ConsumerEpoch,
        [hashtable]$AvailabilityById,
        [hashtable]$ConceptById
    )
    if (-not (Has-JsonProperty -Object $Owner -Name 'core_dependency_refs')) {
        Add-ValidationError "$Context lacks core_dependency_refs."
        return
    }
    $coreRefs = Get-JsonPropertyValue -Object $Owner -Name 'core_dependency_refs'
    if (-not (Test-IsJsonObject -Value $coreRefs)) {
        Add-ValidationError "$Context core_dependency_refs must be an object."
        return
    }
    $fieldContracts = @{
        substance_refs = [pscustomobject]@{ kind = 'substance_id'; registry = 'docs/registries/m2_substance_passports.json' }
        form_refs = [pscustomobject]@{ kind = 'form_id'; registry = 'docs/registries/m2_material_forms.json' }
        process_refs = [pscustomobject]@{ kind = 'process_id'; registry = 'docs/registries/m2_domain_process_ownership.json' }
    }
    foreach ($property in $coreRefs.PSObject.Properties) {
        if ([string]$property.Name -cnotin @('substance_refs', 'form_refs', 'process_refs', 'fallback_concept_refs')) {
            Add-ValidationError "$Context core_dependency_refs has unexpected field '$($property.Name)'."
        }
    }
    $dependencyCount = 0
    foreach ($fieldName in @('substance_refs', 'form_refs', 'process_refs')) {
        if (-not (Has-JsonProperty -Object $coreRefs -Name $fieldName)) {
            Add-ValidationError "$Context core_dependency_refs lacks '$fieldName'."
            continue
        }
        $fieldValue = Get-JsonPropertyValue -Object $coreRefs -Name $fieldName
        if (-not (Test-IsJsonArray -Value $fieldValue)) {
            Add-ValidationError "$Context core_dependency_refs.$fieldName must be an array."
            continue
        }
        $seenRefs = @{}
        foreach ($coreRef in $fieldValue) {
            $dependencyCount++
            if ($coreRef -isnot [string] -or -not ([string]$coreRef).StartsWith('industrial_frontier:', [System.StringComparison]::Ordinal)) {
                Add-ValidationError "$Context core_dependency_refs.$fieldName contains a runtime/external ID '$coreRef'; only declared core IDs are allowed."
                continue
            }
            $coreRef = [string]$coreRef
            if ($seenRefs.ContainsKey($coreRef)) {
                Add-ValidationError "$Context core_dependency_refs.$fieldName repeats '$coreRef'."
                continue
            }
            $seenRefs[$coreRef] = $true
            $contract = $fieldContracts[$fieldName]
            if (-not $idKinds.ContainsKey($coreRef) -or [string]$idKinds[$coreRef] -ne [string]$contract.kind) {
                Add-ValidationError "$Context core_dependency_refs.$fieldName does not resolve to a declared $($contract.kind): '$coreRef'."
                continue
            }
            if (-not ([string]$idLocations[$coreRef]).StartsWith(([string]$contract.registry + '.'), [System.StringComparison]::Ordinal)) {
                Add-ValidationError "$Context core dependency '$coreRef' is not declared by $($contract.registry)."
            }
            if ($null -ne $ConsumerEpoch -and $AvailabilityById.ContainsKey($coreRef) -and [int]$ConsumerEpoch -lt [int]$AvailabilityById[$coreRef]) {
                Add-ValidationError "$Context at P$ConsumerEpoch depends on '$coreRef', first available at P$($AvailabilityById[$coreRef])."
            }
        }
    }
    if (-not (Has-JsonProperty -Object $coreRefs -Name 'fallback_concept_refs')) {
        Add-ValidationError "$Context core_dependency_refs lacks 'fallback_concept_refs'."
    }
    else {
        $fallbackRefs = Get-JsonPropertyValue -Object $coreRefs -Name 'fallback_concept_refs'
        if (-not (Test-IsJsonArray -Value $fallbackRefs)) {
            Add-ValidationError "$Context core_dependency_refs.fallback_concept_refs must be an array."
        }
        else {
            $seenFallbackRefs = @{}
            foreach ($fallbackRefValue in $fallbackRefs) {
                $dependencyCount++
                $fallbackRef = [string]$fallbackRefValue
                if ($seenFallbackRefs.ContainsKey($fallbackRef)) {
                    Add-ValidationError "$Context core_dependency_refs.fallback_concept_refs repeats '$fallbackRef'."
                    continue
                }
                $seenFallbackRefs[$fallbackRef] = $true
                if ($null -eq $ConceptById -or -not $ConceptById.ContainsKey($fallbackRef)) {
                    Add-ValidationError "$Context fallback_concept_ref '$fallbackRef' does not resolve in concept_registry."
                    continue
                }
                $fallbackConceptEpoch = Get-EpochNumber (Get-PropertyValue -Object $ConceptById[$fallbackRef] -Name 'first_epoch')
                if ($null -ne $ConsumerEpoch -and $null -ne $fallbackConceptEpoch -and [int]$fallbackConceptEpoch -gt [int]$ConsumerEpoch) {
                    Add-ValidationError "$Context at P$ConsumerEpoch uses fallback concept '$fallbackRef', first available at P$fallbackConceptEpoch."
                }
            }
        }
    }
    if ($dependencyCount -eq 0) {
        Add-ValidationError "$Context has an empty core_dependency_refs contract; add a physical core reference or an explicit typed fallback concept."
    }
}

function Test-PositionalConceptMapping {
    param(
        $Claims,
        $ConceptRefs,
        [string[]]$AllowedKinds,
        [string]$Context,
        $ConsumerEpoch,
        [hashtable]$ConceptById
    )
    # PowerShell 5.1 binds an empty JSON array passed through a function call as
    # $null. Preserve the JSON meaning here: no claims/refs means two empty
    # arrays, not one array containing a null element.
    $claimValues = @()
    if ($null -ne $Claims) { $claimValues = @($Claims) }
    $referenceValues = @()
    if ($null -ne $ConceptRefs) { $referenceValues = @($ConceptRefs) }
    if ($claimValues.Count -ne $referenceValues.Count) {
        Add-ValidationError "$Context positional claim/ref counts differ: claims=$($claimValues.Count), refs=$($referenceValues.Count)."
    }
    for ($index = 0; $index -lt $referenceValues.Count; $index++) {
        $conceptRef = [string]$referenceValues[$index]
        if ($null -eq $ConceptById -or -not $ConceptById.ContainsKey($conceptRef)) {
            Add-ValidationError "$Context concept ref at position $index does not resolve: '$conceptRef'."
            continue
        }
        $concept = $ConceptById[$conceptRef]
        $conceptKind = [string](Get-PropertyValue -Object $concept -Name 'concept_kind')
        if ($AllowedKinds -cnotcontains $conceptKind) {
            Add-ValidationError "$Context concept '$conceptRef' at position $index is $conceptKind, expected one of $($AllowedKinds -join ', ')."
        }
        # ConsumerEpoch is supplied only when the adjacent claim is active at a
        # concrete epoch (or at the maximum of an explicit native range).
        # Aggregate catalogs with future variants deliberately pass $null.
        $conceptEpoch = Get-EpochNumber (Get-PropertyValue -Object $concept -Name 'first_epoch')
        if ($null -ne $ConsumerEpoch -and $null -ne $conceptEpoch -and [int]$conceptEpoch -gt [int]$ConsumerEpoch) {
            Add-ValidationError "$Context at P$ConsumerEpoch maps position $index to '$conceptRef', first available at P$conceptEpoch."
        }
    }
}

function Test-ReachableEnergyNetwork {
    param([string]$Current, [string]$Target, [hashtable]$Visited, [hashtable]$Adjacency)
    if ($Current -eq $Target) { return $true }
    if ($Visited.ContainsKey($Current)) { return $false }
    $Visited[$Current] = $true
    if (-not $Adjacency.ContainsKey($Current)) { return $false }
    foreach ($edge in @($Adjacency[$Current])) {
        $next = [string](Get-PropertyValue -Object $edge -Name 'target_network_ref')
        if (Test-ReachableEnergyNetwork -Current $next -Target $Target -Visited $Visited -Adjacency $Adjacency) {
            return $true
        }
    }
    return $false
}

# Parse the manifest and every M2 registry before doing semantic work.
$manifestRelativePath = 'authoring/m2/registry_manifest.json'
$manifestPath = Resolve-RootRelativePath -RelativePath $manifestRelativePath -Context 'M2 manifest'
$manifest = if ($null -eq $manifestPath) { $null } else { Read-JsonDocument -Path $manifestPath -Label $manifestRelativePath }

$registryDirectory = Join-Path $rootPath 'docs\registries'
$m2RegistryFiles = @()
if (-not (Test-Path -LiteralPath $registryDirectory -PathType Container)) {
    Add-ValidationError 'Missing docs/registries directory.'
}
else {
    $m2RegistryFiles = @(Get-ChildItem -LiteralPath $registryDirectory -File -Filter 'm2_*.json' | Sort-Object Name)
    if ($m2RegistryFiles.Count -eq 0) {
        Add-ValidationError 'No docs/registries/m2_*.json files were found.'
    }
    foreach ($file in $m2RegistryFiles) {
        $relative = Normalize-RelativePath -Path $file.FullName.Substring($rootPath.Length).TrimStart('\', '/')
        $document = Read-JsonDocument -Path $file.FullName -Label $relative
        $registryRawText[$relative] = Get-Content -Raw -Encoding UTF8 -LiteralPath $file.FullName
        if ($null -eq $document) { continue }
        $registryDocuments[$relative] = $document
        $registryId = [string](Get-PropertyValue -Object $document -Name 'registry_id')
        if ([string]::IsNullOrWhiteSpace($registryId)) {
            Add-ValidationError "Registry lacks registry_id: $relative"
        }
        elseif ($registryId -notmatch '^industrial_frontier:[a-z0-9_./-]+$') {
            Add-ValidationError "Registry has invalid registry_id '$registryId': $relative"
        }
        elseif ($documentsByRegistryId.ContainsKey($registryId)) {
            Add-ValidationError "Duplicate registry_id '$registryId': $($documentsByRegistryId[$registryId].path) and $relative"
        }
        else {
            $documentsByRegistryId[$registryId] = [pscustomobject]@{ path = $relative; document = $document }
        }
    }
}

# Manifest paths, schemas, IDs and declared counts.
$manifestRegistryPaths = @{}
if ($null -ne $manifest) {
    $manifestId = [string](Get-PropertyValue -Object $manifest -Name 'manifest_id')
    if ($manifestId -notmatch '^industrial_frontier:[a-z0-9_./-]+$') {
        Add-ValidationError "M2 manifest has invalid manifest_id '$manifestId'."
    }
    Add-IdDeclaration -Id $manifestId -Kind 'manifest_id' -Location "$manifestRelativePath.manifest_id"
    if ([string](Get-PropertyValue -Object $manifest -Name 'namespace') -ne 'industrial_frontier') {
        Add-ValidationError 'M2 manifest namespace must be industrial_frontier.'
    }
    $manifestEntries = @(Get-PropertyValue -Object $manifest -Name 'registries')
    if ($manifestEntries.Count -eq 0) {
        Add-ValidationError 'M2 manifest has no registry entries.'
    }
    $manifestIds = @{}
    foreach ($entry in $manifestEntries) {
        $registryId = [string](Get-PropertyValue -Object $entry -Name 'registry_id')
        $registryRelative = Normalize-RelativePath -Path ([string](Get-PropertyValue -Object $entry -Name 'registry_path'))
        $schemaRelative = Normalize-RelativePath -Path ([string](Get-PropertyValue -Object $entry -Name 'schema_path'))
        if ([string]::IsNullOrWhiteSpace($registryId) -or -not $registryId.StartsWith('industrial_frontier:', [System.StringComparison]::Ordinal)) {
            Add-ValidationError "Manifest entry has invalid registry_id '$registryId'."
        }
        elseif ($manifestIds.ContainsKey($registryId)) {
            Add-ValidationError "Manifest repeats registry_id '$registryId'."
        }
        else {
            $manifestIds[$registryId] = $registryRelative
        }
        if ([string]::IsNullOrWhiteSpace($registryRelative)) {
            Add-ValidationError "Manifest registry '$registryId' has an empty registry_path."
            continue
        }
        if ($manifestRegistryPaths.ContainsKey($registryRelative)) {
            Add-ValidationError "Manifest repeats registry_path '$registryRelative'."
        }
        else {
            $manifestRegistryPaths[$registryRelative] = $registryId
        }

        $registryFullPath = Resolve-RootRelativePath -RelativePath $registryRelative -Context "manifest registry '$registryId'"
        $schemaFullPath = Resolve-RootRelativePath -RelativePath $schemaRelative -Context "manifest schema '$registryId'"
        if ($null -eq $registryFullPath -or -not (Test-Path -LiteralPath $registryFullPath -PathType Leaf)) {
            Add-ValidationError "Manifest registry path does not exist: $registryRelative"
            continue
        }
        if ($null -eq $schemaFullPath -or -not (Test-Path -LiteralPath $schemaFullPath -PathType Leaf)) {
            Add-ValidationError "Manifest schema path does not exist: $schemaRelative"
        }
        else {
            [void](Read-JsonDocument -Path $schemaFullPath -Label $schemaRelative)
        }
        if (-not $registryDocuments.ContainsKey($registryRelative)) { continue }
        $document = $registryDocuments[$registryRelative]
        $actualRegistryId = [string](Get-PropertyValue -Object $document -Name 'registry_id')
        if ($actualRegistryId -ne $registryId) {
            Add-ValidationError "Manifest registry_id mismatch for ${registryRelative}: manifest='$registryId', document='$actualRegistryId'"
        }
        $counts = Get-PropertyValue -Object $entry -Name 'counts'
        $manifestCountMap = @{}
        if ($null -eq $counts) {
            Add-ValidationError "Manifest registry '$registryId' lacks counts."
        }
        else {
            foreach ($countProperty in $counts.PSObject.Properties) {
                $collectionName = [string]$countProperty.Name
                if (-not (Test-IsJsonInteger -Value $countProperty.Value) -or [int]$countProperty.Value -lt 0) {
                    Add-ValidationError "Manifest count '$registryId#$collectionName' must be a non-negative integer."
                    continue
                }
                $manifestCountMap[$collectionName] = [int]$countProperty.Value
                $countResolved = $false
                $actualCount = 0
                if ($registryId -eq 'industrial_frontier:m2_extended_domains') {
                    $extendedFactionsForCount = Get-PropertyValue -Object $document -Name 'factions'
                    $extendedFactionValuesForCount = @()
                    if (Test-IsJsonObject -Value $extendedFactionsForCount) {
                        $extendedFactionValuesForCount = @($extendedFactionsForCount.PSObject.Properties | ForEach-Object { $_.Value })
                    }
                    $extendedFactionRowsForCount = @($extendedFactionValuesForCount | ForEach-Object {
                        @(Get-PropertyValue -Object $_ -Name 'epoch_matrix')
                    })
                    $constructionForCount = Get-PropertyValue -Object $document -Name 'construction'
                    $foodForCount = Get-PropertyValue -Object $document -Name 'food'
                    $combatForCount = Get-PropertyValue -Object $document -Name 'combat'
                    $extendedConsumerOwnersForCount = @()
                    $extendedConsumerOwnersForCount += @(Get-PropertyValue -Object $constructionForCount -Name 'material_families')
                    foreach ($foodCollectionForCount in @(
                        'crop_passports', 'ingredient_passports', 'food_fluid_passports', 'ration_passports',
                        'container_passports', 'refrigerant_passports', 'bio_waste_passports'
                    )) {
                        $extendedConsumerOwnersForCount += @(Get-PropertyValue -Object $foodForCount -Name $foodCollectionForCount)
                    }
                    foreach ($combatProfileForCount in @(Get-PropertyValue -Object $combatForCount -Name 'epoch_profiles')) {
                        foreach ($combatCategoryForCount in @('weapon', 'armor', 'artillery', 'ammunition')) {
                            $extendedConsumerOwnersForCount += @(Get-PropertyValue -Object $combatProfileForCount -Name $combatCategoryForCount)
                        }
                    }
                    switch ($collectionName) {
                        'typed_concepts' {
                            $actualCount = @(Get-PropertyValue -Object (Get-PropertyValue -Object $document -Name 'concept_registry') -Name 'concepts').Count
                            $countResolved = $true
                        }
                        'construction_material_families' {
                            $actualCount = @(Get-PropertyValue -Object $constructionForCount -Name 'material_families').Count
                            $countResolved = $true
                        }
                        'furniture_categories' {
                            $actualCount = @(Get-PropertyValue -Object $constructionForCount -Name 'furniture_categories').Count
                            $countResolved = $true
                        }
                        'epoch_palettes' {
                            $actualCount = @(Get-PropertyValue -Object $constructionForCount -Name 'epoch_palettes').Count
                            $countResolved = $true
                        }
                        'crop_passports' {
                            $actualCount = @(Get-PropertyValue -Object $foodForCount -Name 'crop_passports').Count
                            $countResolved = $true
                        }
                        'ingredient_passports' {
                            $actualCount = @(Get-PropertyValue -Object $foodForCount -Name 'ingredient_passports').Count
                            $countResolved = $true
                        }
                        'food_fluid_passports' {
                            $actualCount = @(Get-PropertyValue -Object $foodForCount -Name 'food_fluid_passports').Count
                            $countResolved = $true
                        }
                        'ration_passports' {
                            $actualCount = @(Get-PropertyValue -Object $foodForCount -Name 'ration_passports').Count
                            $countResolved = $true
                        }
                        'container_passports' {
                            $actualCount = @(Get-PropertyValue -Object $foodForCount -Name 'container_passports').Count
                            $countResolved = $true
                        }
                        'refrigerant_passports' {
                            $actualCount = @(Get-PropertyValue -Object $foodForCount -Name 'refrigerant_passports').Count
                            $countResolved = $true
                        }
                        'bio_waste_passports' {
                            $actualCount = @(Get-PropertyValue -Object $foodForCount -Name 'bio_waste_passports').Count
                            $countResolved = $true
                        }
                        'combat_profiles' {
                            $actualCount = @(Get-PropertyValue -Object $combatForCount -Name 'epoch_profiles').Count
                            $countResolved = $true
                        }
                        'combat_passports' {
                            $combatProfilesForCount = @(Get-PropertyValue -Object $combatForCount -Name 'epoch_profiles')
                            $actualCount = $combatProfilesForCount.Count * 4
                            $countResolved = $true
                        }
                        'consumer_dependency_objects' {
                            $actualCount = $extendedConsumerOwnersForCount.Count
                            $countResolved = $true
                        }
                        'consumer_substance_refs' {
                            $actualCount = @($extendedConsumerOwnersForCount | ForEach-Object {
                                @(Get-PropertyValue -Object (Get-PropertyValue -Object $_ -Name 'core_dependency_refs') -Name 'substance_refs')
                            }).Count
                            $countResolved = $true
                        }
                        'consumer_form_refs' {
                            $actualCount = @($extendedConsumerOwnersForCount | ForEach-Object {
                                @(Get-PropertyValue -Object (Get-PropertyValue -Object $_ -Name 'core_dependency_refs') -Name 'form_refs')
                            }).Count
                            $countResolved = $true
                        }
                        'consumer_process_refs' {
                            $actualCount = @($extendedConsumerOwnersForCount | ForEach-Object {
                                @(Get-PropertyValue -Object (Get-PropertyValue -Object $_ -Name 'core_dependency_refs') -Name 'process_refs')
                            }).Count
                            $countResolved = $true
                        }
                        'consumer_fallback_refs' {
                            $actualCount = @($extendedConsumerOwnersForCount | ForEach-Object {
                                @(Get-PropertyValue -Object (Get-PropertyValue -Object $_ -Name 'core_dependency_refs') -Name 'fallback_concept_refs')
                            }).Count
                            $countResolved = $true
                        }
                        'factions' {
                            $actualCount = $extendedFactionValuesForCount.Count
                            $countResolved = $true
                        }
                        'faction_epoch_rows' {
                            $actualCount = $extendedFactionRowsForCount.Count
                            $countResolved = $true
                        }
                        'role_slots' {
                            $actualCount = @($extendedFactionRowsForCount | ForEach-Object {
                                @(Get-PropertyValue -Object $_ -Name 'roles')
                            }).Count
                            $countResolved = $true
                        }
                        'role_bindings' {
                            $actualCount = 0
                            foreach ($factionRowForCount in $extendedFactionRowsForCount) {
                                $bindingsForCount = Get-PropertyValue -Object $factionRowForCount -Name 'role_loadout_bindings'
                                if (Test-IsJsonObject -Value $bindingsForCount) {
                                    $actualCount += @($bindingsForCount.PSObject.Properties).Count
                                }
                            }
                            $countResolved = $true
                        }
                    }
                }
                if (-not $countResolved -and (Has-Property -Object $document -Name $collectionName)) {
                    $actualCount = @(Get-PropertyValue -Object $document -Name $collectionName).Count
                    $countResolved = $true
                }
                elseif (-not $countResolved -and $registryId -eq 'industrial_frontier:m2/domain_process_ownership') {
                    $manifestProcesses = @((Get-PropertyValue -Object $document -Name 'domains') | ForEach-Object {
                        @(Get-PropertyValue -Object $_ -Name 'processes')
                    })
                    switch ($collectionName) {
                        'processes' {
                            $actualCount = $manifestProcesses.Count
                            $countResolved = $true
                        }
                        'flow_records' {
                            $actualCount = @($manifestProcesses | ForEach-Object {
                                $flowContract = Get-PropertyValue -Object $_ -Name 'flow_contract'
                                @(Get-PropertyValue -Object $flowContract -Name 'records')
                            }).Count
                            $countResolved = $true
                        }
                        'non_material_exemptions' {
                            $actualCount = @($manifestProcesses | Where-Object {
                                [string](Get-PropertyValue -Object (Get-PropertyValue -Object $_ -Name 'flow_contract') -Name 'model') -eq 'NON_MATERIAL_COORDINATION'
                            }).Count
                            $countResolved = $true
                        }
                    }
                }
                elseif (-not $countResolved -and $registryId -eq 'industrial_frontier:m2/progression_graph' -and $collectionName -eq 'component_requirement_edges') {
                    $actualCount = @((Get-PropertyValue -Object $document -Name 'dependency_edges') | Where-Object {
                        [string](Get-PropertyValue -Object $_ -Name 'relation') -eq 'COMPONENT_REQUIRES'
                    }).Count
                    $countResolved = $true
                }
                if (-not $countResolved) {
                    Add-ValidationError "Manifest count '$collectionName' has no matching collection in $registryRelative."
                    continue
                }
                if ($actualCount -ne [int]$countProperty.Value) {
                    Add-ValidationError "Manifest count mismatch for $registryRelative#${collectionName}: expected=$($countProperty.Value), actual=$actualCount"
                }
            }
        }
        if (-not $manifestCountsByRegistryId.ContainsKey($registryId)) {
            $manifestCountsByRegistryId[$registryId] = $manifestCountMap
        }
    }
}

# Manifest prose is part of the authority contract. Reject the two known broad
# claims that become false as soon as the extended construction/food/combat
# registry is part of the manifest-declared M2 baseline.
if ($null -ne $manifest) {
    $manifestRegistryIds = @((Get-PropertyValue -Object $manifest -Name 'registries') | ForEach-Object {
        [string](Get-PropertyValue -Object $_ -Name 'registry_id')
    })
    if ($manifestRegistryIds -contains 'industrial_frontier:m2_extended_domains') {
        foreach ($assumption in @(Get-PropertyValue -Object $manifest -Name 'validation_assumptions')) {
            if ([string]$assumption -match '(?i)baseline\s+intentionally\s+excludes.*construction.*food.*weapon.*faction') {
                Add-ValidationError 'Manifest validation_assumptions contradict the included extended construction/food/combat/faction registry.'
            }
        }
        foreach ($invariant in @(Get-PropertyValue -Object $manifest -Name 'cross_registry_invariants')) {
            if ([string]$invariant -match '(?i)^every\s+entry\s+references\s+at\s+least\s+one\s+source[- ]evidence') {
                Add-ValidationError 'Manifest evidence/gate invariant is broader than its schemas; scope it to core technical entries or add evidence/gates to every extended entry.'
            }
        }
    }
}

# Apply the authored Draft 2020-12 schema subset locally. This is a real
# instance-vs-schema pass, not merely a JSON parse: the manifest and all listed
# registries are validated, while every locally available M2 schema is audited
# for unsupported keywords. Relative/external and local-fragment $ref targets
# are resolved read-only from authoring/schemas.
$schemaDirectory = Join-Path $rootPath 'authoring\schemas'
if (-not (Test-Path -LiteralPath $schemaDirectory -PathType Container)) {
    Add-ValidationError 'Missing authoring/schemas directory.'
}
else {
    foreach ($schemaFile in Get-ChildItem -LiteralPath $schemaDirectory -File -Filter 'm2_*.schema.json' | Sort-Object Name) {
        $keywordProblems = [System.Collections.Generic.List[string]]::new()
        $schemaDocument = Get-LocalSchemaDocument -SchemaPath $schemaFile.FullName -Problems $keywordProblems
        if ($null -ne $schemaDocument) {
            Assert-SupportedSchemaKeywords -Schema $schemaDocument -Location $schemaFile.Name -Problems $keywordProblems
        }
        foreach ($problem in $keywordProblems) {
            Add-ValidationError "Schema definition error [$($schemaFile.Name)]: $problem"
        }
        $schemaKeywordAudited[$schemaFile.FullName] = $true
        $schemaKeywordAuditCount++
    }
}

if ($null -ne $manifest) {
    $manifestSchemaPath = Join-Path $rootPath 'authoring\schemas\m2_registry_manifest.schema.json'
    Invoke-LocalJsonSchemaValidation -Instance $manifest -SchemaPath $manifestSchemaPath -Label $manifestRelativePath
    foreach ($entry in @(Get-PropertyValue -Object $manifest -Name 'registries')) {
        $registryRelative = Normalize-RelativePath -Path ([string](Get-PropertyValue -Object $entry -Name 'registry_path'))
        $schemaRelative = Normalize-RelativePath -Path ([string](Get-PropertyValue -Object $entry -Name 'schema_path'))
        if (-not $registryDocuments.ContainsKey($registryRelative)) { continue }
        $schemaFullPath = Resolve-RootRelativePath -RelativePath $schemaRelative -Context "schema application for '$registryRelative'"
        if ($null -ne $schemaFullPath) {
            Invoke-LocalJsonSchemaValidation -Instance $registryDocuments[$registryRelative] -SchemaPath $schemaFullPath -Label $registryRelative
        }
    }
}
if ($null -ne $manifest) {
    $expectedSchemaValidationCount = @(Get-PropertyValue -Object $manifest -Name 'registries').Count + 1
    if ($schemaValidationCount -ne $expectedSchemaValidationCount) {
        Add-ValidationError "Schema application count must equal manifest plus listed registries: expected=$expectedSchemaValidationCount completed=$schemaValidationCount."
    }
}

# A schema self-declared by an extension is still parsed. Every M2 registry is
# authoritative and must be listed; silent manifest drift is an error.
foreach ($relative in @($registryDocuments.Keys | Sort-Object)) {
    $document = $registryDocuments[$relative]
    if (-not $manifestRegistryPaths.ContainsKey($relative)) {
        Add-ValidationError "M2 registry is not listed in registry_manifest.json: $relative"
    }
    $declaredSchema = Get-PropertyValue -Object $document -Name '$schema'
    if ($declaredSchema -is [string] -and -not [string]::IsNullOrWhiteSpace([string]$declaredSchema)) {
        $registryFullPath = Join-Path $rootPath ($relative -replace '/', '\')
        $schemaCandidate = [System.IO.Path]::GetFullPath((Join-Path (Split-Path -Parent $registryFullPath) ([string]$declaredSchema)))
        if (-not (Test-PathInsideInstanceRoot -Path $schemaCandidate) -or -not (Test-Path -LiteralPath $schemaCandidate -PathType Leaf)) {
            Add-ValidationError "Registry-declared schema does not exist for ${relative}: $declaredSchema"
        }
        else {
            [void](Read-JsonDocument -Path $schemaCandidate -Label "$relative#`$schema")
        }
    }
}

# Declare every pack-owned ID, capture references and require Russian terms.
foreach ($relative in @($registryDocuments.Keys | Sort-Object)) {
    Visit-RegistryNode -Node $registryDocuments[$relative] -Location $relative
}
if ($ruFieldCount -eq 0) {
    Add-ValidationError 'No Russian terminology fields were found in M2 registries.'
}

# Load stable pack resource IDs as legitimate external-to-M2 targets.
$allowedPackRuntimeIds = @{}
$stableIdsPath = Join-Path $rootPath 'docs\registries\stable_ids.json'
if (Test-Path -LiteralPath $stableIdsPath -PathType Leaf) {
    $stableIds = Read-JsonDocument -Path $stableIdsPath -Label 'docs/registries/stable_ids.json'
    if ($null -ne $stableIds) {
        $resourceIds = Get-PropertyValue -Object $stableIds -Name 'resource_ids'
        if ($null -ne $resourceIds) {
            foreach ($property in $resourceIds.PSObject.Properties) {
                $allowedPackRuntimeIds[[string]$property.Value] = $true
            }
        }
    }
}

# Resolve cross-registry references, with stronger type checks for gates,
# evidence, forms, substances, domains, networks and contracts.
foreach ($reference in $references) {
    $value = [string]$reference.value
    if (-not $idLocations.ContainsKey($value)) {
        if (-not $allowedPackRuntimeIds.ContainsKey($value)) {
            Add-ValidationError "Unresolved industrial_frontier reference '$value' at $($reference.location)."
        }
        continue
    }
    $expectedKind = Get-ExpectedReferenceKind -PropertyName ([string]$reference.property)
    if ($null -ne $expectedKind -and [string]$idKinds[$value] -ne $expectedKind) {
        Add-ValidationError "Reference kind mismatch at $($reference.location): '$value' is $($idKinds[$value]), expected $expectedKind."
    }
}

# Every source-evidence record is unique (by the global ID pass), complete and
# backed by an existing local file/JAR path. Core entries must cite evidence and
# an explicit gate; gates themselves must cite evidence.
$evidenceReferenceUse = @{}
foreach ($reference in $references | Where-Object { $_.property -eq 'evidence_refs' }) {
    $id = [string]$reference.value
    if (-not $evidenceReferenceUse.ContainsKey($id)) { $evidenceReferenceUse[$id] = 0 }
    $evidenceReferenceUse[$id] = [int]$evidenceReferenceUse[$id] + 1
}

$coreEntryCollections = @('passports', 'planned_substances', 'forms', 'domains', 'contracts', 'networks', 'converters', 'ownership_decisions', 'decisions', 'nodes', 'dependency_edges', 'edges')
$coreCollectionIdFields = @{
    passports = 'substance_id'
    planned_substances = 'substance_id'
    forms = 'form_id'
    domains = 'domain_id'
    contracts = 'contract_id'
    networks = 'network_id'
    converters = 'converter_id'
    ownership_decisions = 'decision_id'
    decisions = 'bypass_id'
    nodes = 'node_id'
    dependency_edges = 'dependency_id'
    edges = 'edge_id'
}
foreach ($relative in @($registryDocuments.Keys | Sort-Object)) {
    $document = $registryDocuments[$relative]
    foreach ($collectionName in $coreEntryCollections) {
        if (-not (Has-Property -Object $document -Name $collectionName)) { continue }
        foreach ($entry in @(Get-PropertyValue -Object $document -Name $collectionName)) {
            $idField = [string]$coreCollectionIdFields[$collectionName]
            $entryId = [string](Get-PropertyValue -Object $entry -Name $idField)
            if ($entryId -notmatch '^industrial_frontier:[a-z0-9_./-]+$') {
                Add-ValidationError "Entry in $relative#$collectionName has invalid or missing $idField '$entryId'."
            }
            Require-EntryEvidenceAndGate -Entry $entry -Collection $collectionName -RegistryPath $relative
        }
    }
    if (Has-Property -Object $document -Name 'gates') {
        foreach ($gate in @(Get-PropertyValue -Object $document -Name 'gates')) {
            $gateId = Get-RecordId -Object $gate
            if (@(Get-PropertyValue -Object $gate -Name 'evidence_refs').Count -eq 0) {
                Add-ValidationError "Gate '$gateId' in $relative has no source evidence."
            }
            $requirementRu = Get-PropertyValue -Object $gate -Name 'requirement_ru'
            if ($requirementRu -isnot [string] -or [string]::IsNullOrWhiteSpace([string]$requirementRu)) {
                Add-ValidationError "Gate '$gateId' in $relative has no Russian requirement."
            }
        }
    }
    if (Has-Property -Object $document -Name 'source_evidence') {
        $evidenceIndex = 0
        foreach ($evidence in @(Get-PropertyValue -Object $document -Name 'source_evidence')) {
            Test-EvidencePath -Evidence $evidence -Location "$relative.source_evidence[$evidenceIndex]"
            $evidenceId = [string](Get-PropertyValue -Object $evidence -Name 'evidence_id')
            if (-not [string]::IsNullOrWhiteSpace($evidenceId) -and -not $evidenceReferenceUse.ContainsKey($evidenceId)) {
                Add-ValidationWarning "Unused source evidence '$evidenceId' in $relative."
            }
            $evidenceIndex++
        }
    }
}

# Active process claims inherit the evidence/gates of their sovereign domain;
# the parent must therefore be fully sourced.
$domainRegistryInfo = $documentsByRegistryId['industrial_frontier:m2/domain_process_ownership']
$domainRegistry = if ($null -eq $domainRegistryInfo) { $null } else { $domainRegistryInfo.document }
if ($null -eq $domainRegistry) {
    Add-ValidationError 'Missing industrial_frontier:m2/domain_process_ownership registry.'
}
else {
    foreach ($domain in @(Get-PropertyValue -Object $domainRegistry -Name 'domains')) {
        $activeProcesses = @((Get-PropertyValue -Object $domain -Name 'processes') | Where-Object { [string](Get-PropertyValue -Object $_ -Name 'status') -match '^ACTIVE' })
        if ($activeProcesses.Count -gt 0) {
            if (@(Get-PropertyValue -Object $domain -Name 'evidence_refs').Count -eq 0 -or @(Get-PropertyValue -Object $domain -Name 'gate_refs').Count -eq 0) {
                Add-ValidationError "Domain '$(Get-RecordId $domain)' has active process claims without inherited evidence/gates."
            }
        }
    }

    # A process flow is a typed material contract, not explanatory prose. The
    # contract lives in pathways and stages: every stage names its input groups,
    # products, waste and bounded returns, and the progression graph projects
    # those stages into production and recycle edges. NON_MATERIAL_COORDINATION
    # is the only model allowed to own no pathway; it must explain why and must
    # stay clear of substances entirely.
    $allProductionProcesses = @((Get-PropertyValue -Object $domainRegistry -Name 'domains') | ForEach-Object {
        @(Get-PropertyValue -Object $_ -Name 'processes')
    })

    $pathwayById = @{}
    foreach ($pathway in @(Get-PropertyValue -Object $domainRegistry -Name 'pathways')) {
        $pathwayById[[string](Get-PropertyValue -Object $pathway -Name 'pathway_id')] = $pathway
    }
    $stageById = @{}
    $stagesByPathwayRef = @{}
    foreach ($stage in @(Get-PropertyValue -Object $domainRegistry -Name 'stages')) {
        $stageId = [string](Get-PropertyValue -Object $stage -Name 'stage_id')
        $stageById[$stageId] = $stage
        $pathwayRef = [string](Get-PropertyValue -Object $stage -Name 'pathway_ref')
        if (-not $stagesByPathwayRef.ContainsKey($pathwayRef)) { $stagesByPathwayRef[$pathwayRef] = @() }
        $stagesByPathwayRef[$pathwayRef] = @($stagesByPathwayRef[$pathwayRef]) + @($stage)
    }

    $expectedProductionIdentities = @{}
    $expectedRecycleIdentities = @{}
    $nonMaterialExemptionCount = 0
    $visitedStageIds = @{}

    foreach ($process in $allProductionProcesses) {
        $processId = [string](Get-PropertyValue -Object $process -Name 'process_id')
        $processStatus = [string](Get-PropertyValue -Object $process -Name 'status')
        $processEarliestEpoch = Get-PropertyValue -Object $process -Name 'earliest_epoch'
        $processAutomationEpoch = Get-PropertyValue -Object $process -Name 'automation_epoch'
        if ($null -ne $processAutomationEpoch -and $null -ne $processEarliestEpoch -and [int]$processAutomationEpoch -lt [int]$processEarliestEpoch) {
            Add-ValidationError "Process '$processId' automates at P$processAutomationEpoch before earliest_epoch P$processEarliestEpoch."
        }

        $flowContract = Get-PropertyValue -Object $process -Name 'flow_contract'
        if (-not (Test-IsJsonObject -Value $flowContract)) {
            Add-ValidationError "Process '$processId' lacks a typed flow_contract object."
            continue
        }
        $flowModel = [string](Get-PropertyValue -Object $flowContract -Name 'model')
        $pathwayRefs = @(Get-PropertyValue -Object $flowContract -Name 'pathway_refs')
        $exemptionReason = Get-PropertyValue -Object $flowContract -Name 'non_material_exemption_reason_ru'

        if ($flowModel -ceq 'NON_MATERIAL_COORDINATION') {
            $nonMaterialExemptionCount++
            if ($pathwayRefs.Count -ne 0) {
                Add-ValidationError "Non-material process '$processId' must not own material pathways."
            }
            if ($exemptionReason -isnot [string] -or [string]::IsNullOrWhiteSpace([string]$exemptionReason)) {
                Add-ValidationError "Non-material process '$processId' lacks an explicit Russian exemption reason."
            }
            foreach ($legacyRef in @(
                @(Get-PropertyValue -Object $process -Name 'input_refs') +
                @(Get-PropertyValue -Object $process -Name 'output_refs')
            )) {
                $legacyRef = [string]$legacyRef
                if ($idKinds.ContainsKey($legacyRef) -and [string]$idKinds[$legacyRef] -eq 'substance_id') {
                    Add-ValidationError "Non-material process '$processId' exposes substance '$legacyRef' through legacy input/output refs instead of a typed material flow."
                }
            }
            continue
        }
        if ($flowModel -cne 'PATHWAY_OWNER') {
            Add-ValidationError "Process '$processId' has unsupported material flow model '$flowModel'."
            continue
        }
        if ($pathwayRefs.Count -eq 0) {
            Add-ValidationError "Material process '$processId' owns no pathway and declares no non-material exemption."
            continue
        }

        $processConsumed = @{}
        $processProduced = @{}
        $processRecycled = @{}

        foreach ($pathwayRefValue in $pathwayRefs) {
            $pathwayRefText = [string]$pathwayRefValue
            if (-not $pathwayById.ContainsKey($pathwayRefText)) {
                Add-ValidationError "Process '$processId' references unknown pathway '$pathwayRefText'."
                continue
            }
            $pathway = $pathwayById[$pathwayRefText]
            $pathwayOwner = [string](Get-PropertyValue -Object $pathway -Name 'parent_process_ref')
            if ($pathwayOwner -cne $processId) {
                Add-ValidationError "Pathway '$pathwayRefText' is parented to '$pathwayOwner' but listed by process '$processId'."
            }
            $declaredStageRefs = @(@(Get-PropertyValue -Object $pathway -Name 'stage_refs') | ForEach-Object { [string]$_ })
            foreach ($declaredStageRef in $declaredStageRefs) {
                if (-not $stageById.ContainsKey($declaredStageRef)) {
                    Add-ValidationError "Pathway '$pathwayRefText' references unknown stage '$declaredStageRef'."
                }
            }
            $pathwayStages = @($stagesByPathwayRef[$pathwayRefText])
            if ($pathwayStages.Count -eq 0) {
                Add-ValidationError "Pathway '$pathwayRefText' owns no stage and therefore carries no material contract."
                continue
            }

            foreach ($stage in $pathwayStages) {
                $stageId = [string](Get-PropertyValue -Object $stage -Name 'stage_id')
                if ($visitedStageIds.ContainsKey($stageId)) {
                    Add-ValidationError "Stage '$stageId' is claimed by more than one pathway."
                    continue
                }
                $visitedStageIds[$stageId] = $true

                if ($declaredStageRefs -cnotcontains $stageId) {
                    Add-ValidationError "Stage '$stageId' claims pathway '$pathwayRefText', which does not list it in stage_refs."
                }
                $stageParent = [string](Get-PropertyValue -Object $stage -Name 'parent_process_ref')
                if ($stageParent -cne $processId) {
                    Add-ValidationError "Stage '$stageId' names parent process '$stageParent' but is reached through '$processId'."
                }

                $stageStatus = [string](Get-PropertyValue -Object $stage -Name 'status')
                if ($processStatus -ceq 'GATED_NOT_INSTALLED' -and $stageStatus -cne 'GATED_BINDING') {
                    Add-ValidationError "Future process '$processId' exposes non-gated stage '$stageId'."
                }

                $stageEarliestEpoch = Get-PropertyValue -Object $stage -Name 'earliest_epoch'
                $stageAutomationEpoch = Get-PropertyValue -Object $stage -Name 'automation_epoch'
                if ($null -eq $stageEarliestEpoch) {
                    Add-ValidationError "Stage '$stageId' lacks earliest_epoch."
                }
                elseif ($null -ne $processEarliestEpoch -and [int]$stageEarliestEpoch -lt [int]$processEarliestEpoch) {
                    Add-ValidationError "Stage '$stageId' starts at P$stageEarliestEpoch before process earliest_epoch P$processEarliestEpoch."
                }
                if ($null -ne $stageAutomationEpoch) {
                    if ($null -ne $stageEarliestEpoch -and [int]$stageAutomationEpoch -lt [int]$stageEarliestEpoch) {
                        Add-ValidationError "Stage '$stageId' automates at P$stageAutomationEpoch before availability P$stageEarliestEpoch."
                    }
                }
                elseif ($stageStatus -ceq 'STATIC_BINDING') {
                    Add-ValidationError "Static stage '$stageId' must have a concrete automation_epoch."
                }

                $consumedSet = @{}
                foreach ($group in @(Get-PropertyValue -Object $stage -Name 'input_groups')) {
                    $groupId = [string](Get-PropertyValue -Object $group -Name 'group_id')
                    $groupLogic = [string](Get-PropertyValue -Object $group -Name 'logic')
                    $groupRefs = @(@(Get-PropertyValue -Object $group -Name 'substance_refs') | ForEach-Object { [string]$_ })
                    if ($groupRefs.Count -eq 0) {
                        Add-ValidationError "Stage '$stageId' input group '$groupId' declares no substance."
                    }
                    if ($groupLogic -ceq 'ONE_OF' -and $groupRefs.Count -lt 2) {
                        Add-ValidationError "Stage '$stageId' input group '$groupId' is ONE_OF but offers no alternative."
                    }
                    foreach ($groupRef in $groupRefs) {
                        if (-not $idKinds.ContainsKey($groupRef) -or [string]$idKinds[$groupRef] -ne 'substance_id') {
                            $actualKind = if ($idKinds.ContainsKey($groupRef)) { [string]$idKinds[$groupRef] } else { 'unresolved' }
                            Add-ValidationError "Stage '$stageId' input '$groupRef' is $actualKind, expected substance_id."
                        }
                        $identity = "$stageId|PROCESS_CONSUMES|$groupId|$groupRef"
                        if ($expectedProductionIdentities.ContainsKey($identity)) {
                            Add-ValidationError "Stage '$stageId' repeats input '$groupRef' inside group '$groupId'."
                        }
                        $expectedProductionIdentities[$identity] = $true
                        $consumedSet[$groupRef] = $true
                        $processConsumed[$groupRef] = $true
                    }
                }

                $producedSet = @{}
                $wasteSet = @{}
                foreach ($relationPair in @(
                    [pscustomobject]@{ relation = 'PROCESS_PRODUCES'; property = 'output_refs' },
                    [pscustomobject]@{ relation = 'PROCESS_EMITS_WASTE'; property = 'waste_output_refs' }
                )) {
                    foreach ($outputRefValue in @(Get-PropertyValue -Object $stage -Name $relationPair.property)) {
                        $outputRef = [string]$outputRefValue
                        if (-not $idKinds.ContainsKey($outputRef) -or [string]$idKinds[$outputRef] -ne 'substance_id') {
                            $actualKind = if ($idKinds.ContainsKey($outputRef)) { [string]$idKinds[$outputRef] } else { 'unresolved' }
                            Add-ValidationError "Stage '$stageId' output '$outputRef' is $actualKind, expected substance_id."
                        }
                        $identity = "$stageId|$($relationPair.relation)||$outputRef"
                        if ($expectedProductionIdentities.ContainsKey($identity)) {
                            Add-ValidationError "Stage '$stageId' repeats $($relationPair.relation) for '$outputRef'."
                        }
                        $expectedProductionIdentities[$identity] = $true
                        if ($relationPair.relation -ceq 'PROCESS_PRODUCES') { $producedSet[$outputRef] = $true }
                        else { $wasteSet[$outputRef] = $true }
                        $processProduced[$outputRef] = $true
                    }
                }

                $wasteRefs = @(Get-PropertyValue -Object $stage -Name 'waste_output_refs')
                $recycleRefs = @(@(Get-PropertyValue -Object $stage -Name 'recycle_input_refs') | ForEach-Object { [string]$_ })
                foreach ($recycleRef in $recycleRefs) {
                    # A bounded return may re-enter from any stream the stage
                    # actually handles, including its own waste: reclaiming
                    # process water is a real loop, inventing mass is not.
                    if (-not $consumedSet.ContainsKey($recycleRef) -and -not $producedSet.ContainsKey($recycleRef) -and -not $wasteSet.ContainsKey($recycleRef)) {
                        Add-ValidationError "Stage '$stageId' returns '$recycleRef', which it neither consumes, produces nor emits as waste."
                    }
                    $identity = "$stageId|$recycleRef"
                    if ($expectedRecycleIdentities.ContainsKey($identity)) {
                        Add-ValidationError "Stage '$stageId' repeats bounded return of '$recycleRef'."
                    }
                    $expectedRecycleIdentities[$identity] = $true
                    $processRecycled[$recycleRef] = $true
                }

                $stageKind = [string](Get-PropertyValue -Object $stage -Name 'stage_kind')
                switch ($stageKind) {
                    'MATERIAL_SOURCE' {
                        if ($consumedSet.Count -ne 0 -or $producedSet.Count -eq 0 -or $wasteRefs.Count -ne 0) {
                            Add-ValidationError "Material source '$stageId' must only produce substances from a declared world or vendor origin."
                        }
                    }
                    'MATERIAL_TRANSFORMATION' {
                        if ($consumedSet.Count -eq 0 -or ($producedSet.Count + $wasteRefs.Count) -eq 0) {
                            Add-ValidationError "Material transformation '$stageId' must consume input and produce output or waste."
                        }
                    }
                    'MATERIAL_SINK' {
                        if ($consumedSet.Count -eq 0 -or $producedSet.Count -ne 0 -or $wasteRefs.Count -ne 0) {
                            Add-ValidationError "Material sink '$stageId' must only consume substances."
                        }
                    }
                    'IDENTITY_PRESERVING_SERVICE' {
                        if ($wasteRefs.Count -ne 0) {
                            Add-ValidationError "Identity-preserving service '$stageId' must not emit waste."
                        }
                        foreach ($substanceId in @((@($consumedSet.Keys) + @($producedSet.Keys)) | Sort-Object -Unique)) {
                            if (-not $consumedSet.ContainsKey($substanceId) -or -not $producedSet.ContainsKey($substanceId)) {
                                Add-ValidationError "Identity-preserving service '$stageId' does not preserve substance '$substanceId' in both directions."
                            }
                        }
                    }
                    default {
                        Add-ValidationError "Stage '$stageId' has unsupported stage_kind '$stageKind'."
                    }
                }
            }
        }

        # Legacy input/output refs may include non-material infrastructure IDs.
        # When they do name a substance, the stage contract must account for it.
        foreach ($inputRefValue in @(Get-PropertyValue -Object $process -Name 'input_refs')) {
            $inputRef = [string]$inputRefValue
            if (-not $idKinds.ContainsKey($inputRef) -or [string]$idKinds[$inputRef] -ne 'substance_id') { continue }
            if (-not $processConsumed.ContainsKey($inputRef) -and -not $processRecycled.ContainsKey($inputRef)) {
                Add-ValidationError "Process '$processId' legacy input '$inputRef' is not consumed or returned by any owned stage."
            }
        }
        foreach ($outputRefValue in @(Get-PropertyValue -Object $process -Name 'output_refs')) {
            $outputRef = [string]$outputRefValue
            if (-not $idKinds.ContainsKey($outputRef) -or [string]$idKinds[$outputRef] -ne 'substance_id') { continue }
            if (-not $processProduced.ContainsKey($outputRef) -and -not $processRecycled.ContainsKey($outputRef)) {
                Add-ValidationError "Process '$processId' legacy output '$outputRef' is not produced, wasted or returned by any owned stage."
            }
        }
    }

    foreach ($stageId in @($stageById.Keys)) {
        if (-not $visitedStageIds.ContainsKey($stageId)) {
            Add-ValidationError "Stage '$stageId' is not reachable from any process pathway."
        }
    }

    Assert-ManifestCount -RegistryId 'industrial_frontier:m2/domain_process_ownership' -CountName 'processes' -ActualCount $allProductionProcesses.Count -Context 'M2 production processes'
    Assert-ManifestCount -RegistryId 'industrial_frontier:m2/domain_process_ownership' -CountName 'pathways' -ActualCount $pathwayById.Count -Context 'M2 production pathways'
    Assert-ManifestCount -RegistryId 'industrial_frontier:m2/domain_process_ownership' -CountName 'stages' -ActualCount $stageById.Count -Context 'M2 production stages'
    Assert-ManifestCount -RegistryId 'industrial_frontier:m2/domain_process_ownership' -CountName 'non_material_exemptions' -ActualCount $nonMaterialExemptionCount -Context 'M2 non-material coordination exemptions'

    # The progression graph must project exactly the authored stage contract:
    # no invented edge, no silently dropped flow, no unbounded return loop.
    $progressionForEdges = $documentsByRegistryId['industrial_frontier:m2/progression_graph']
    if ($null -eq $progressionForEdges) {
        Add-ValidationError 'Cannot audit stage projection: progression graph registry is missing.'
    }
    else {
        $seenProductionIdentities = @{}
        foreach ($productionEdge in @(Get-PropertyValue -Object $progressionForEdges.document -Name 'production_edges')) {
            $edgeId = [string](Get-PropertyValue -Object $productionEdge -Name 'production_edge_id')
            $stageRef = [string](Get-PropertyValue -Object $productionEdge -Name 'stage_ref')
            $relation = [string](Get-PropertyValue -Object $productionEdge -Name 'relation')
            $fromRef = [string](Get-PropertyValue -Object $productionEdge -Name 'from_ref')
            $toRef = [string](Get-PropertyValue -Object $productionEdge -Name 'to_ref')
            $direction = [string](Get-PropertyValue -Object $productionEdge -Name 'direction')
            $groupRefValue = Get-PropertyValue -Object $productionEdge -Name 'input_group_ref'
            $groupRef = if ($null -eq $groupRefValue) { '' } else { [string]$groupRefValue }

            if (-not $stageById.ContainsKey($stageRef)) {
                Add-ValidationError "Production edge '$edgeId' references unknown stage '$stageRef'."
                continue
            }
            $stage = $stageById[$stageRef]
            if ([string](Get-PropertyValue -Object $stage -Name 'pathway_ref') -cne [string](Get-PropertyValue -Object $productionEdge -Name 'pathway_ref')) {
                Add-ValidationError "Production edge '$edgeId' names a pathway that does not own stage '$stageRef'."
            }
            if ([string](Get-PropertyValue -Object $stage -Name 'owner_domain_ref') -cne [string](Get-PropertyValue -Object $productionEdge -Name 'owner_domain_ref')) {
                Add-ValidationError "Production edge '$edgeId' reassigns the owner domain of stage '$stageRef'."
            }
            if ([string](Get-PropertyValue -Object $stage -Name 'status') -cne [string](Get-PropertyValue -Object $productionEdge -Name 'status')) {
                Add-ValidationError "Production edge '$edgeId' does not inherit the binding status of stage '$stageRef'."
            }

            $substanceRef = if ($relation -ceq 'PROCESS_CONSUMES') { $fromRef } else { $toRef }
            $expectedDirection = if ($relation -ceq 'PROCESS_CONSUMES') { 'SUBSTANCE_TO_STAGE' } else { 'STAGE_TO_SUBSTANCE' }
            $expectedAnchor = if ($relation -ceq 'PROCESS_CONSUMES') { $toRef } else { $fromRef }
            if ($direction -cne $expectedDirection) {
                Add-ValidationError "Production edge '$edgeId' direction must be '$expectedDirection', found '$direction'."
            }
            if ($expectedAnchor -cne $stageRef) {
                Add-ValidationError "Production edge '$edgeId' does not anchor relation '$relation' on stage '$stageRef'."
            }
            if ($relation -cne 'PROCESS_CONSUMES' -and $groupRef -ne '') {
                Add-ValidationError "Production edge '$edgeId' declares an input group on an output relation."
            }

            $identity = "$stageRef|$relation|$groupRef|$substanceRef"
            if ($seenProductionIdentities.ContainsKey($identity)) {
                Add-ValidationError "Production edge '$edgeId' duplicates flow '$identity'."
            }
            $seenProductionIdentities[$identity] = $true
            if (-not $expectedProductionIdentities.ContainsKey($identity)) {
                Add-ValidationError "Production edge '$edgeId' projects flow '$identity', which no stage declares."
            }
        }
        foreach ($identity in @($expectedProductionIdentities.Keys)) {
            if (-not $seenProductionIdentities.ContainsKey($identity)) {
                Add-ValidationError "Stage flow '$identity' has no production edge in the progression graph."
            }
        }

        $seenRecycleIdentities = @{}
        foreach ($recycleEdge in @(Get-PropertyValue -Object $progressionForEdges.document -Name 'bounded_recycle_edges')) {
            $edgeId = [string](Get-PropertyValue -Object $recycleEdge -Name 'recycle_edge_id')
            $stageRef = [string](Get-PropertyValue -Object $recycleEdge -Name 'stage_ref')
            $substanceRef = [string](Get-PropertyValue -Object $recycleEdge -Name 'substance_ref')
            $loopKind = [string](Get-PropertyValue -Object $recycleEdge -Name 'loop_kind')
            $returnRatio = [double](Get-PropertyValue -Object $recycleEdge -Name 'max_return_ratio')
            $makeupRatio = [double](Get-PropertyValue -Object $recycleEdge -Name 'minimum_makeup_ratio')

            if (-not $stageById.ContainsKey($stageRef)) {
                Add-ValidationError "Recycle edge '$edgeId' references unknown stage '$stageRef'."
                continue
            }
            $stage = $stageById[$stageRef]
            $stageKind = [string](Get-PropertyValue -Object $stage -Name 'stage_kind')
            $expectedLoopKind = if ($stageKind -ceq 'IDENTITY_PRESERVING_SERVICE') { 'IDENTITY_PRESERVING_FORM' } else { 'MATERIAL_RECOVERY' }
            if ($loopKind -cne $expectedLoopKind) {
                Add-ValidationError "Recycle edge '$edgeId' declares '$loopKind' for a '$stageKind' stage; expected '$expectedLoopKind'."
            }
            if ($loopKind -ceq 'MATERIAL_RECOVERY' -and ($returnRatio -ge 1 -or $makeupRatio -le 0)) {
                Add-ValidationError "Recycle edge '$edgeId' recovers material without measurable loss or make-up."
            }
            if (($returnRatio + $makeupRatio) -gt 1.0000001) {
                Add-ValidationError "Recycle edge '$edgeId' returns more mass than one pass can carry."
            }

            $identity = "$stageRef|$substanceRef"
            if ($seenRecycleIdentities.ContainsKey($identity)) {
                Add-ValidationError "Recycle edge '$edgeId' duplicates bounded loop '$identity'."
            }
            $seenRecycleIdentities[$identity] = $true
            if (-not $expectedRecycleIdentities.ContainsKey($identity)) {
                Add-ValidationError "Recycle edge '$edgeId' projects loop '$identity', which no stage declares."
            }
        }
        foreach ($identity in @($expectedRecycleIdentities.Keys)) {
            if (-not $seenRecycleIdentities.ContainsKey($identity)) {
                Add-ValidationError "Stage return '$identity' has no bounded recycle edge in the progression graph."
            }
        }

        $productionEdgeCount = @(Get-PropertyValue -Object $progressionForEdges.document -Name 'production_edges').Count
        $recycleEdgeCount = @(Get-PropertyValue -Object $progressionForEdges.document -Name 'bounded_recycle_edges').Count
        Assert-ManifestCount -RegistryId 'industrial_frontier:m2/progression_graph' -CountName 'production_edges' -ActualCount $productionEdgeCount -Context 'M2 stage production edges'
        Assert-ManifestCount -RegistryId 'industrial_frontier:m2/progression_graph' -CountName 'bounded_recycle_edges' -ActualCount $recycleEdgeCount -Context 'M2 bounded recycle edges'
    }
}

# The authoritative progression is a single linear P0 -> ... -> P9 graph.
$progressionInfo = $documentsByRegistryId['industrial_frontier:m2/progression_graph']
$progression = if ($null -eq $progressionInfo) { $null } else { $progressionInfo.document }
if ($null -eq $progression) {
    Add-ValidationError 'Missing industrial_frontier:m2/progression_graph registry.'
}
else {
    $nodes = @(Get-PropertyValue -Object $progression -Name 'nodes')
    $edges = @(Get-PropertyValue -Object $progression -Name 'edges')
    if ($nodes.Count -ne 10) { Add-ValidationError "Progression must have 10 nodes; found $($nodes.Count)." }
    if ($edges.Count -ne 9) { Add-ValidationError "Progression must have 9 edges; found $($edges.Count)." }

    for ($epoch = 0; $epoch -le 9; $epoch++) {
        $matches = @($nodes | Where-Object { [int](Get-PropertyValue -Object $_ -Name 'epoch') -eq $epoch })
        if ($matches.Count -ne 1) {
            Add-ValidationError "Progression epoch P$epoch must occur exactly once; found $($matches.Count)."
            continue
        }
        $expectedNodeId = "industrial_frontier:epoch/p$epoch"
        if ([string](Get-PropertyValue -Object $matches[0] -Name 'node_id') -ne $expectedNodeId) {
            Add-ValidationError "Progression epoch P$epoch must use node_id '$expectedNodeId'."
        }
    }

    for ($epoch = 0; $epoch -lt 9; $epoch++) {
        $expectedFrom = "industrial_frontier:epoch/p$epoch"
        $expectedTo = "industrial_frontier:epoch/p$($epoch + 1)"
        $matchingEdges = @($edges | Where-Object {
            [string](Get-PropertyValue -Object $_ -Name 'from') -eq $expectedFrom -and
            [string](Get-PropertyValue -Object $_ -Name 'to') -eq $expectedTo
        })
        if ($matchingEdges.Count -ne 1) {
            Add-ValidationError "Progression edge P$epoch -> P$($epoch + 1) must occur exactly once; found $($matchingEdges.Count)."
        }
    }
    foreach ($edge in $edges) {
        $from = [string](Get-PropertyValue -Object $edge -Name 'from')
        $to = [string](Get-PropertyValue -Object $edge -Name 'to')
        if ($from -notmatch '^industrial_frontier:epoch/p([0-9])$' -or $to -notmatch '^industrial_frontier:epoch/p([0-9])$') {
            Add-ValidationError "Progression edge '$(Get-RecordId $edge)' has invalid endpoint IDs."
            continue
        }
        $fromEpoch = [int]([regex]::Match($from, 'p([0-9])$').Groups[1].Value)
        $toEpoch = [int]([regex]::Match($to, 'p([0-9])$').Groups[1].Value)
        if ($toEpoch -ne $fromEpoch + 1) {
            Add-ValidationError "Progression edge '$(Get-RecordId $edge)' is not a single forward Pn -> Pn+1 transition."
        }
    }

    # Validate the typed dependency DAG independently from the nine linear
    # epoch-transition edges. The production spine is extended with typed
    # substance/process/network -> critical-component requirements.
    $dependencyEdges = @(Get-PropertyValue -Object $progression -Name 'dependency_edges')
    if ($dependencyEdges.Count -eq 0) {
        Add-ValidationError 'Progression dependency_edges is empty.'
    }
    else {
        $relationKinds = @{
            FORM_REPRESENTS_SUBSTANCE = [pscustomobject]@{ from = @('form_id'); to = @('substance_id') }
            SUBSTANCE_GOVERNED_BY_PROCESS = [pscustomobject]@{ from = @('substance_id'); to = @('process_id') }
            PROCESS_ENABLES_EPOCH = [pscustomobject]@{ from = @('process_id'); to = @('node_id') }
            EPOCH_SERVES_CONSUMER_DOMAIN = [pscustomobject]@{ from = @('node_id'); to = @('domain_id') }
            COMPONENT_REQUIRES = [pscustomobject]@{ from = @('substance_id', 'process_id', 'network_id'); to = @('component_id') }
        }
        $seenDependencyIds = @{}
        $seenDependencyTriples = @{}
        $dependencyAdjacency = @{}
        $dependencyIndegree = @{}
        $actualDependencyRelationCounts = @{
            FORM_REPRESENTS_SUBSTANCE = 0
            SUBSTANCE_GOVERNED_BY_PROCESS = 0
            PROCESS_ENABLES_EPOCH = 0
            EPOCH_SERVES_CONSUMER_DOMAIN = 0
            COMPONENT_REQUIRES = 0
        }
        $processById = @{}
        $domainMinimumProcessEpoch = @{}
        $dependencyAvailabilityById = @{}
        if ($null -ne $domainRegistry) {
            foreach ($domain in @(Get-PropertyValue -Object $domainRegistry -Name 'domains')) {
                $domainId = [string](Get-PropertyValue -Object $domain -Name 'domain_id')
                $minimumEpoch = $null
                foreach ($process in @(Get-PropertyValue -Object $domain -Name 'processes')) {
                    $processId = [string](Get-PropertyValue -Object $process -Name 'process_id')
                    $processById[$processId] = $process
                    $earliestEpochValue = Get-PropertyValue -Object $process -Name 'earliest_epoch'
                    if ($null -ne $earliestEpochValue) {
                        $earliestEpoch = [int]$earliestEpochValue
                        $dependencyAvailabilityById[$processId] = $earliestEpoch
                        if ($null -eq $minimumEpoch -or $earliestEpoch -lt [int]$minimumEpoch) { $minimumEpoch = $earliestEpoch }
                    }
                }
                if ($null -ne $minimumEpoch) { $domainMinimumProcessEpoch[$domainId] = [int]$minimumEpoch }
            }
        }
        $substanceRegistryInfoForComponentDag = $documentsByRegistryId['industrial_frontier:m2/substance_passports']
        if ($null -ne $substanceRegistryInfoForComponentDag) {
            foreach ($collectionName in @('passports', 'planned_substances')) {
                foreach ($substance in @(Get-PropertyValue -Object $substanceRegistryInfoForComponentDag.document -Name $collectionName)) {
                    $dependencyAvailabilityById[[string](Get-PropertyValue -Object $substance -Name 'substance_id')] = [int](Get-PropertyValue -Object $substance -Name 'first_epoch')
                }
            }
        }
        $energyRegistryInfoForComponentDag = $documentsByRegistryId['industrial_frontier:m2/energy_networks']
        if ($null -ne $energyRegistryInfoForComponentDag) {
            foreach ($network in @(Get-PropertyValue -Object $energyRegistryInfoForComponentDag.document -Name 'networks')) {
                $networkEpoch = Get-PropertyValue -Object $network -Name 'earliest_epoch'
                if ($null -ne $networkEpoch) {
                    $dependencyAvailabilityById[[string](Get-PropertyValue -Object $network -Name 'network_id')] = [int]$networkEpoch
                }
            }
        }
        $criticalComponentByIdForDag = @{}
        $grindRegistryInfoForComponentDag = $documentsByRegistryId['industrial_frontier:m2/grind_budget']
        if ($null -ne $grindRegistryInfoForComponentDag) {
            foreach ($component in @(Get-PropertyValue -Object $grindRegistryInfoForComponentDag.document -Name 'critical_components')) {
                $criticalComponentByIdForDag[[string](Get-PropertyValue -Object $component -Name 'component_id')] = $component
            }
        }
        $epochByNodeId = @{}
        foreach ($node in $nodes) {
            $epochByNodeId[[string](Get-PropertyValue -Object $node -Name 'node_id')] = [int](Get-PropertyValue -Object $node -Name 'epoch')
        }

        foreach ($dependencyEdge in $dependencyEdges) {
            $dependencyId = [string](Get-PropertyValue -Object $dependencyEdge -Name 'dependency_id')
            $fromRef = [string](Get-PropertyValue -Object $dependencyEdge -Name 'from_ref')
            $toRef = [string](Get-PropertyValue -Object $dependencyEdge -Name 'to_ref')
            $relation = [string](Get-PropertyValue -Object $dependencyEdge -Name 'relation')
            if ($dependencyId -notmatch '^industrial_frontier:dependency/[a-z0-9_./-]+$') {
                Add-ValidationError "Invalid dependency_id '$dependencyId'."
            }
            elseif ($seenDependencyIds.ContainsKey($dependencyId)) {
                Add-ValidationError "Duplicate dependency_id '$dependencyId'."
            }
            else { $seenDependencyIds[$dependencyId] = $true }

            if (-not $relationKinds.ContainsKey($relation)) {
                Add-ValidationError "Dependency '$dependencyId' has unsupported relation '$relation'."
                continue
            }
            $actualDependencyRelationCounts[$relation] = [int]$actualDependencyRelationCounts[$relation] + 1
            $expectedFromKinds = @((Get-PropertyValue -Object $relationKinds[$relation] -Name 'from'))
            $expectedToKinds = @((Get-PropertyValue -Object $relationKinds[$relation] -Name 'to'))
            if (-not $idKinds.ContainsKey($fromRef) -or -not $idKinds.ContainsKey($toRef)) {
                Add-ValidationError "Dependency '$dependencyId' has an unresolved endpoint: '$fromRef' -> '$toRef'."
            }
            else {
                if ($expectedFromKinds -cnotcontains [string]$idKinds[$fromRef]) {
                    Add-ValidationError "Dependency '$dependencyId' source '$fromRef' is $($idKinds[$fromRef]), expected one of $($expectedFromKinds -join ', ')."
                }
                if ($expectedToKinds -cnotcontains [string]$idKinds[$toRef]) {
                    Add-ValidationError "Dependency '$dependencyId' target '$toRef' is $($idKinds[$toRef]), expected one of $($expectedToKinds -join ', ')."
                }
            }

            $triple = "$relation|$fromRef|$toRef"
            $recipePolicyPointer = Get-PropertyValue -Object $dependencyEdge -Name 'recipe_policy_pointer'
            $dependencyIdentity = if ($recipePolicyPointer -is [string] -and -not [string]::IsNullOrWhiteSpace([string]$recipePolicyPointer)) {
                "$triple|$recipePolicyPointer"
            }
            else { $triple }
            if ($seenDependencyTriples.ContainsKey($dependencyIdentity)) {
                Add-ValidationError "Duplicate dependency relation identity '$dependencyIdentity'."
            }
            else { $seenDependencyTriples[$dependencyIdentity] = $dependencyId }

            foreach ($endpoint in @($fromRef, $toRef)) {
                if (-not $dependencyIndegree.ContainsKey($endpoint)) { $dependencyIndegree[$endpoint] = 0 }
                if (-not $dependencyAdjacency.ContainsKey($endpoint)) { $dependencyAdjacency[$endpoint] = @() }
            }
            $dependencyAdjacency[$fromRef] = @($dependencyAdjacency[$fromRef]) + @($toRef)
            $dependencyIndegree[$toRef] = [int]$dependencyIndegree[$toRef] + 1

            if ($relation -eq 'COMPONENT_REQUIRES') {
                if ($null -ne $recipePolicyPointer) {
                    Add-ValidationError "Component dependency '$dependencyId' must not use a substance recipe_policy_pointer."
                }
                if ([string](Get-PropertyValue -Object $dependencyEdge -Name 'direction') -cne 'REQUIREMENT_TO_COMPONENT') {
                    Add-ValidationError "Component dependency '$dependencyId' must use direction REQUIREMENT_TO_COMPONENT."
                }
                if ([string](Get-PropertyValue -Object $dependencyEdge -Name 'optionality') -cne 'REQUIRED') {
                    Add-ValidationError "Component dependency '$dependencyId' maps required_refs and must use optionality REQUIRED."
                }
                $requirementEarliestEpoch = Get-PropertyValue -Object $dependencyEdge -Name 'earliest_epoch'
                $requirementAutomationEpoch = Get-PropertyValue -Object $dependencyEdge -Name 'automation_epoch'
                if ($null -eq $requirementEarliestEpoch -or $null -eq $requirementAutomationEpoch) {
                    Add-ValidationError "Component dependency '$dependencyId' must declare concrete earliest_epoch and automation_epoch values."
                }
                elseif ([int]$requirementAutomationEpoch -lt [int]$requirementEarliestEpoch) {
                    Add-ValidationError "Component dependency '$dependencyId' automates at P$requirementAutomationEpoch before earliest_epoch P$requirementEarliestEpoch."
                }
                if ($null -ne $requirementEarliestEpoch -and $dependencyAvailabilityById.ContainsKey($fromRef) -and [int]$requirementEarliestEpoch -lt [int]$dependencyAvailabilityById[$fromRef]) {
                    Add-ValidationError "Component dependency '$dependencyId' uses '$fromRef' at P$requirementEarliestEpoch before its core availability P$($dependencyAvailabilityById[$fromRef])."
                }

                if (-not $criticalComponentByIdForDag.ContainsKey($toRef)) {
                    Add-ValidationError "Component dependency '$dependencyId' targets undeclared critical component '$toRef'."
                }
                else {
                    $targetComponent = $criticalComponentByIdForDag[$toRef]
                    $targetComponentEpoch = [int](Get-PropertyValue -Object $targetComponent -Name 'epoch')
                    $targetAutomationEpoch = Get-PropertyValue -Object $targetComponent -Name 'automation_epoch'
                    $targetComponentStatus = [string](Get-PropertyValue -Object $targetComponent -Name 'status')
                    $dependencyStatus = [string](Get-PropertyValue -Object $dependencyEdge -Name 'status')
                    if ($null -ne $requirementEarliestEpoch -and [int]$requirementEarliestEpoch -gt $targetComponentEpoch) {
                        Add-ValidationError "Component dependency '$dependencyId' becomes available at P$requirementEarliestEpoch after target '$toRef' is introduced at P$targetComponentEpoch."
                    }
                    if ($null -ne $requirementAutomationEpoch -and $null -ne $targetAutomationEpoch -and [int]$requirementAutomationEpoch -gt [int]$targetAutomationEpoch) {
                        Add-ValidationError "Component dependency '$dependencyId' automates after target '$toRef' automation budget P$targetAutomationEpoch."
                    }
                    if ($targetComponentStatus -eq 'ACTIVE_M2' -and $dependencyStatus -ne 'STATIC_BINDING') {
                        Add-ValidationError "Active critical component '$toRef' has non-static requirement '$dependencyId'."
                    }
                    if ($targetComponentStatus -ne 'ACTIVE_M2' -and $dependencyStatus -ne 'GATED_BINDING') {
                        Add-ValidationError "Non-active critical component '$toRef' exposes non-gated requirement '$dependencyId'."
                    }
                }
            }

            if ($relation -eq 'PROCESS_ENABLES_EPOCH' -and $processById.ContainsKey($fromRef) -and $epochByNodeId.ContainsKey($toRef)) {
                $earliestEpoch = [int](Get-PropertyValue -Object $processById[$fromRef] -Name 'earliest_epoch')
                $targetEpoch = [int]$epochByNodeId[$toRef]
                if ($targetEpoch -lt $earliestEpoch) {
                    Add-ValidationError "Dependency '$dependencyId' enables P$targetEpoch before process '$fromRef' earliest_epoch P$earliestEpoch."
                }
            }
            if ($relation -eq 'EPOCH_SERVES_CONSUMER_DOMAIN' -and $epochByNodeId.ContainsKey($fromRef) -and $domainMinimumProcessEpoch.ContainsKey($toRef)) {
                $sourceEpoch = [int]$epochByNodeId[$fromRef]
                $domainEpoch = [int]$domainMinimumProcessEpoch[$toRef]
                if ($sourceEpoch -lt $domainEpoch) {
                    Add-ValidationError "Dependency '$dependencyId' serves domain '$toRef' at P$sourceEpoch before its earliest process P$domainEpoch."
                }
            }
        }

        Assert-ManifestCount -RegistryId 'industrial_frontier:m2/progression_graph' -CountName 'dependency_edges' -ActualCount $dependencyEdges.Count -Context 'M2 dependency edges'
        $classifiedDependencyEdgeCount = 0
        foreach ($relation in @($actualDependencyRelationCounts.Keys)) {
            $classifiedDependencyEdgeCount += [int]$actualDependencyRelationCounts[$relation]
        }
        if ($classifiedDependencyEdgeCount -ne $dependencyEdges.Count) {
            Add-ValidationError "Dependency relation parity failed: classified=$classifiedDependencyEdgeCount edges=$($dependencyEdges.Count)."
        }

        $dependencyRootIds = @($dependencyIndegree.Keys | Where-Object { [int]$dependencyIndegree[$_] -eq 0 } | Sort-Object)
        if ($dependencyRootIds.Count -eq 0) {
            Add-ValidationError 'Progression dependency DAG has no zero-indegree authored root.'
        }
        # Prove explicit reachability from the authored roots independently of
        # cycle detection, including every critical-component sink.
        $reachableDependencyEndpoints = @{}
        $reachabilityQueue = [System.Collections.Generic.Queue[string]]::new()
        foreach ($rootEndpoint in $dependencyRootIds) {
            if (-not $reachableDependencyEndpoints.ContainsKey($rootEndpoint)) {
                $reachableDependencyEndpoints[$rootEndpoint] = $true
                $reachabilityQueue.Enqueue([string]$rootEndpoint)
            }
        }
        while ($reachabilityQueue.Count -gt 0) {
            $currentEndpoint = $reachabilityQueue.Dequeue()
            foreach ($targetEndpoint in @($dependencyAdjacency[$currentEndpoint])) {
                if (-not $reachableDependencyEndpoints.ContainsKey($targetEndpoint)) {
                    $reachableDependencyEndpoints[$targetEndpoint] = $true
                    $reachabilityQueue.Enqueue([string]$targetEndpoint)
                }
            }
        }
        if ($reachableDependencyEndpoints.Count -ne $dependencyIndegree.Count) {
            Add-ValidationError "Progression dependency DAG has endpoints unreachable from authored roots: reached $($reachableDependencyEndpoints.Count) of $($dependencyIndegree.Count)."
        }
        foreach ($criticalComponentId in @($criticalComponentByIdForDag.Keys)) {
            if (-not $reachableDependencyEndpoints.ContainsKey($criticalComponentId)) {
                Add-ValidationError "Critical component '$criticalComponentId' is unreachable in the typed production DAG."
            }
        }

        # Kahn's algorithm proves the complete typed edge set is acyclic. Every
        # endpoint processed here is consequently reachable from at least one
        # zero-indegree authored root.
        $dependencyQueue = [System.Collections.Generic.Queue[string]]::new()
        foreach ($endpoint in @($dependencyIndegree.Keys)) {
            if ([int]$dependencyIndegree[$endpoint] -eq 0) { $dependencyQueue.Enqueue([string]$endpoint) }
        }
        $processedDependencyNodes = 0
        while ($dependencyQueue.Count -gt 0) {
            $currentEndpoint = $dependencyQueue.Dequeue()
            $processedDependencyNodes++
            foreach ($targetEndpoint in @($dependencyAdjacency[$currentEndpoint])) {
                $dependencyIndegree[$targetEndpoint] = [int]$dependencyIndegree[$targetEndpoint] - 1
                if ([int]$dependencyIndegree[$targetEndpoint] -eq 0) { $dependencyQueue.Enqueue([string]$targetEndpoint) }
            }
        }
        if ($processedDependencyNodes -ne $dependencyIndegree.Count) {
            Add-ValidationError "Progression dependency DAG contains a directed cycle; processed $processedDependencyNodes of $($dependencyIndegree.Count) endpoints."
        }

        $formsRegistryInfoForDag = $documentsByRegistryId['industrial_frontier:m2/material_forms']
        if ($null -eq $formsRegistryInfoForDag) {
            Add-ValidationError 'Cannot audit FORM_REPRESENTS_SUBSTANCE completeness: material forms registry is missing.'
        }
        else {
            $formEdgesByPair = @{}
            foreach ($dependencyEdge in $dependencyEdges | Where-Object { [string](Get-PropertyValue -Object $_ -Name 'relation') -eq 'FORM_REPRESENTS_SUBSTANCE' }) {
                $pair = "$(Get-PropertyValue $dependencyEdge 'from_ref')->$(Get-PropertyValue $dependencyEdge 'to_ref')"
                if (-not $formEdgesByPair.ContainsKey($pair)) { $formEdgesByPair[$pair] = 0 }
                $formEdgesByPair[$pair] = [int]$formEdgesByPair[$pair] + 1
            }
            $declaredForms = @(Get-PropertyValue -Object $formsRegistryInfoForDag.document -Name 'forms')
            if (@($dependencyEdges | Where-Object { [string](Get-PropertyValue -Object $_ -Name 'relation') -eq 'FORM_REPRESENTS_SUBSTANCE' }).Count -ne $declaredForms.Count) {
                Add-ValidationError "FORM_REPRESENTS_SUBSTANCE count must equal material form count $($declaredForms.Count)."
            }
            foreach ($form in $declaredForms) {
                $expectedPair = "$(Get-PropertyValue $form 'form_id')->$(Get-PropertyValue $form 'substance_ref')"
                if (-not $formEdgesByPair.ContainsKey($expectedPair) -or [int]$formEdgesByPair[$expectedPair] -ne 1) {
                    Add-ValidationError "Material form dependency '$expectedPair' must occur exactly once."
                }
            }
        }

        $substanceRegistryInfoForDag = $documentsByRegistryId['industrial_frontier:m2/substance_passports']
        if ($null -eq $substanceRegistryInfoForDag) {
            Add-ValidationError 'Cannot audit SUBSTANCE_GOVERNED_BY_PROCESS completeness: substance registry is missing.'
        }
        else {
            $expectedSubstanceProcessPairs = @{}
            $substanceCollectionById = @{}
            $substanceEntryById = @{}
            foreach ($collectionName in @('passports', 'planned_substances')) {
                foreach ($substance in @(Get-PropertyValue -Object $substanceRegistryInfoForDag.document -Name $collectionName)) {
                    $substanceId = [string](Get-PropertyValue -Object $substance -Name 'substance_id')
                    $substanceCollectionById[$substanceId] = $collectionName
                    $substanceEntryById[$substanceId] = $substance
                    foreach ($processRef in @(Get-PropertyValue -Object $substance -Name 'process_refs')) {
                        $expectedSubstanceProcessPairs["$substanceId->$processRef"] = $true
                    }
                }
            }
            $actualSubstanceProcessPairs = @{}
            $substanceProcessEdges = @($dependencyEdges | Where-Object { [string](Get-PropertyValue -Object $_ -Name 'relation') -eq 'SUBSTANCE_GOVERNED_BY_PROCESS' })
            foreach ($dependencyEdge in $substanceProcessEdges) {
                $dependencyId = [string](Get-PropertyValue -Object $dependencyEdge -Name 'dependency_id')
                $substanceId = [string](Get-PropertyValue -Object $dependencyEdge -Name 'from_ref')
                $processId = [string](Get-PropertyValue -Object $dependencyEdge -Name 'to_ref')
                $pair = "$substanceId->$processId"
                if (-not $actualSubstanceProcessPairs.ContainsKey($pair)) { $actualSubstanceProcessPairs[$pair] = 0 }
                $actualSubstanceProcessPairs[$pair] = [int]$actualSubstanceProcessPairs[$pair] + 1

                if ($substanceCollectionById.ContainsKey($substanceId)) {
                    $slug = $substanceId.Substring('industrial_frontier:substance/'.Length)
                    $expectedPointer = "docs/registries/m2_substance_passports.json#/$($substanceCollectionById[$substanceId])?substance_id=$slug/recipe_policy_ru"
                    $actualPointer = [string](Get-PropertyValue -Object $dependencyEdge -Name 'recipe_policy_pointer')
                    if ($actualPointer -cne $expectedPointer) {
                        Add-ValidationError "Dependency '$dependencyId' recipe_policy_pointer does not select '$substanceId': expected '$expectedPointer'."
                    }
                    $recipePolicy = Get-PropertyValue -Object $substanceEntryById[$substanceId] -Name 'recipe_policy_ru'
                    if ($recipePolicy -isnot [string] -or [string]::IsNullOrWhiteSpace([string]$recipePolicy)) {
                        Add-ValidationError "Dependency '$dependencyId' selects an empty recipe_policy_ru for '$substanceId'."
                    }
                }
            }
            foreach ($dependencyEdge in $dependencyEdges | Where-Object { [string](Get-PropertyValue -Object $_ -Name 'relation') -eq 'PROCESS_ENABLES_EPOCH' }) {
                $dependencyId = [string](Get-PropertyValue -Object $dependencyEdge -Name 'dependency_id')
                $processId = [string](Get-PropertyValue -Object $dependencyEdge -Name 'from_ref')
                $epochNodeId = [string](Get-PropertyValue -Object $dependencyEdge -Name 'to_ref')
                $policyPointer = [string](Get-PropertyValue -Object $dependencyEdge -Name 'recipe_policy_pointer')
                if ($policyPointer -cnotmatch '^docs/registries/m2_substance_passports\.json#/(passports|planned_substances)\?substance_id=([a-z0-9_./-]+)/recipe_policy_ru$') {
                    Add-ValidationError "Dependency '$dependencyId' has an invalid PROCESS_ENABLES_EPOCH recipe_policy_pointer '$policyPointer'."
                    continue
                }
                $selectedCollection = [string]$Matches[1]
                $selectedSubstanceId = "industrial_frontier:substance/$($Matches[2])"
                if (-not $substanceEntryById.ContainsKey($selectedSubstanceId) -or [string]$substanceCollectionById[$selectedSubstanceId] -cne $selectedCollection) {
                    Add-ValidationError "Dependency '$dependencyId' recipe policy selector does not resolve to '$selectedSubstanceId' in '$selectedCollection'."
                    continue
                }
                $selectedEntry = $substanceEntryById[$selectedSubstanceId]
                if (@(Get-PropertyValue -Object $selectedEntry -Name 'process_refs') -cnotcontains $processId) {
                    Add-ValidationError "Dependency '$dependencyId' selects '$selectedSubstanceId', whose process_refs do not contain '$processId'."
                }
                $recipePolicy = Get-PropertyValue -Object $selectedEntry -Name 'recipe_policy_ru'
                if ($recipePolicy -isnot [string] -or [string]::IsNullOrWhiteSpace([string]$recipePolicy)) {
                    Add-ValidationError "Dependency '$dependencyId' selects an empty recipe_policy_ru for '$selectedSubstanceId'."
                }
                if ($epochByNodeId.ContainsKey($epochNodeId)) {
                    $selectedFirstEpoch = [int](Get-PropertyValue -Object $selectedEntry -Name 'first_epoch')
                    if ([int]$epochByNodeId[$epochNodeId] -lt $selectedFirstEpoch) {
                        Add-ValidationError "Dependency '$dependencyId' enables '$processId' before selected substance '$selectedSubstanceId' first_epoch P$selectedFirstEpoch."
                    }
                }
            }
            if ($substanceProcessEdges.Count -ne $expectedSubstanceProcessPairs.Count) {
                Add-ValidationError "SUBSTANCE_GOVERNED_BY_PROCESS count must equal the $($expectedSubstanceProcessPairs.Count) unique passport process_refs pairs."
            }
            foreach ($expectedPair in @($expectedSubstanceProcessPairs.Keys)) {
                if (-not $actualSubstanceProcessPairs.ContainsKey($expectedPair) -or [int]$actualSubstanceProcessPairs[$expectedPair] -ne 1) {
                    Add-ValidationError "Substance/process dependency '$expectedPair' must occur exactly once."
                }
            }
            foreach ($actualPair in @($actualSubstanceProcessPairs.Keys)) {
                if (-not $expectedSubstanceProcessPairs.ContainsKey($actualPair)) {
                    Add-ValidationError "Dependency DAG contains undeclared substance/process pair '$actualPair'."
                }
            }
        }
    }

    # The graph is the complete M2 dependency spine, so every authored
    # substance passport and every domain contract must be reachable from at
    # least one epoch node. Exact row counts alone cannot prove that coverage.
    $substanceRegistryInfo = $documentsByRegistryId['industrial_frontier:m2/substance_passports']
    if ($null -eq $substanceRegistryInfo) {
        Add-ValidationError 'Cannot audit progression coverage: substance passport registry is missing.'
    }
    else {
        $declaredSubstanceIds = @()
        foreach ($collectionName in @('passports', 'planned_substances')) {
            foreach ($substance in @(Get-PropertyValue -Object $substanceRegistryInfo.document -Name $collectionName)) {
                $declaredSubstanceIds += [string](Get-PropertyValue -Object $substance -Name 'substance_id')
            }
        }
        $referencedSubstances = @($nodes | ForEach-Object { @(Get-PropertyValue -Object $_ -Name 'required_substance_refs') })
        $referencedSubstanceSet = @{}
        foreach ($substanceRef in $referencedSubstances) { $referencedSubstanceSet[[string]$substanceRef] = $true }
        foreach ($substanceId in $declaredSubstanceIds) {
            if (-not $referencedSubstanceSet.ContainsKey($substanceId)) {
                Add-ValidationError "Progression P0-P9 does not cover substance passport '$substanceId'."
            }
        }
    }

    if ($null -eq $domainRegistry) {
        Add-ValidationError 'Cannot audit progression coverage: domain contract registry is missing.'
    }
    else {
        $referencedContractSet = @{}
        foreach ($contractRef in @($nodes | ForEach-Object { @(Get-PropertyValue -Object $_ -Name 'contract_refs') })) {
            $referencedContractSet[[string]$contractRef] = $true
        }
        foreach ($contract in @(Get-PropertyValue -Object $domainRegistry -Name 'contracts')) {
            $contractId = [string](Get-PropertyValue -Object $contract -Name 'contract_id')
            if (-not $referencedContractSet.ContainsKey($contractId)) {
                Add-ValidationError "Progression P0-P9 does not cover domain contract '$contractId'."
            }
        }
    }

    $extendedRegistryInfoForGraph = $documentsByRegistryId['industrial_frontier:m2_extended_domains']
    if ($null -eq $extendedRegistryInfoForGraph) {
        Add-ValidationError 'Cannot audit progression extended_refs: extended-domain registry is missing.'
    }
    else {
        foreach ($node in $nodes) {
            $nodeEpoch = [int](Get-PropertyValue -Object $node -Name 'epoch')
            $expectedExtendedRefs = @(
                "docs/registries/m2_extended_domains.json#/construction/epoch_palettes?epoch=p$nodeEpoch",
                "docs/registries/m2_extended_domains.json#/food/ration_passports?epoch=p$nodeEpoch",
                "docs/registries/m2_extended_domains.json#/combat/epoch_profiles?epoch=p$nodeEpoch"
            )
            $actualExtendedRefs = @(Get-PropertyValue -Object $node -Name 'extended_refs')
            if ($actualExtendedRefs.Count -ne $expectedExtendedRefs.Count) {
                Add-ValidationError "Progression P$nodeEpoch extended dependency count must match the declared construction/food/combat contract: expected=$($expectedExtendedRefs.Count) actual=$($actualExtendedRefs.Count)."
            }
            foreach ($expectedExtendedRef in $expectedExtendedRefs) {
                if ($actualExtendedRefs -cnotcontains $expectedExtendedRef) {
                    Add-ValidationError "Progression P$nodeEpoch lacks extended dependency '$expectedExtendedRef'."
                }
            }
            foreach ($extendedRef in $actualExtendedRefs) {
                if ([string]$extendedRef -cnotmatch '^docs/registries/m2_extended_domains\.json#/(construction/epoch_palettes|food/ration_passports|combat/epoch_profiles)\?epoch=p([0-9])$') {
                    Add-ValidationError "Progression P$nodeEpoch has invalid extended_ref '$extendedRef'."
                    continue
                }
                if ([int]$Matches[2] -ne $nodeEpoch) {
                    Add-ValidationError "Progression P$nodeEpoch points to a P$($Matches[2]) extended dependency: '$extendedRef'."
                }
            }
        }
    }
}

# Domains whose wave has not arrived are architectural placeholders only. The
# list shrinks as milestones land: civil nuclear left it in M6, and the
# strategic-nuclear and planetary-spaceflight domains left it in M7, when each
# gained passports, an epoch gate, recipes and a chapter. A domain must never be
# dropped from here without that work — the point is that "installed" and
# "integrated" stay different words.
if ($null -ne $domainRegistry) {
    $requiredFutureDomainIds = @(
        'industrial_frontier:domain/living_city'
    )
    foreach ($futureDomainId in $requiredFutureDomainIds) {
        $domain = Find-ObjectById -Items (Get-PropertyValue -Object $domainRegistry -Name 'domains') -IdField 'domain_id' -Id $futureDomainId
        if ($null -eq $domain) {
            Add-ValidationError "Missing gated future domain '$futureDomainId'."
            continue
        }
    }

    # Any domain marked absent follows the same rule, including newly added
    # petroleum/heavy-industry placeholders.
    foreach ($domain in @(Get-PropertyValue -Object $domainRegistry -Name 'domains')) {
        $domainId = [string](Get-PropertyValue -Object $domain -Name 'domain_id')
        $domainStatus = [string](Get-PropertyValue -Object $domain -Name 'status')
        if ($domainId -in $requiredFutureDomainIds -and $domainStatus -ne 'GATED_NOT_INSTALLED') {
            Add-ValidationError "Future domain '$domainId' must be GATED_NOT_INSTALLED."
        }
        if ($domainStatus -ne 'GATED_NOT_INSTALLED') { continue }
        if (@(Get-PropertyValue -Object $domain -Name 'installed_mod_ids').Count -ne 0) {
            Add-ValidationError "Future domain '$domainId' must not declare installed_mod_ids."
        }
        foreach ($process in @(Get-PropertyValue -Object $domain -Name 'processes')) {
            if ([string](Get-PropertyValue -Object $process -Name 'status') -ne 'GATED_NOT_INSTALLED') {
                Add-ValidationError "Future process '$(Get-RecordId $process)' must be GATED_NOT_INSTALLED."
            }
        }
    }
    foreach ($contract in @(Get-PropertyValue -Object $domainRegistry -Name 'contracts')) {
        $target = [string](Get-PropertyValue -Object $contract -Name 'target_domain_ref')
        $targetDomain = Find-ObjectById -Items (Get-PropertyValue -Object $domainRegistry -Name 'domains') -IdField 'domain_id' -Id $target
        if ($null -ne $targetDomain -and [string](Get-PropertyValue -Object $targetDomain -Name 'status') -eq 'GATED_NOT_INSTALLED' -and [string](Get-PropertyValue -Object $contract -Name 'status') -ne 'GATED_NOT_INSTALLED') {
            Add-ValidationError "Contract '$(Get-RecordId $contract)' into future domain '$target' must be GATED_NOT_INSTALLED."
        }
    }
}

$energyInfo = $documentsByRegistryId['industrial_frontier:m2/energy_networks']
$energyRegistry = if ($null -eq $energyInfo) { $null } else { $energyInfo.document }
if ($null -eq $energyRegistry) {
    Add-ValidationError 'Missing industrial_frontier:m2/energy_networks registry.'
}
else {
    # The HBM network opened with its own wave in M7 and now names its unit and
    # its mod. The converter did not: HE stays closed on itself, so the pack
    # keeps exactly one direction of energy conversion — the EU to FE export.
    # An HBM bridge would let a strategic reactor feed the city grid and quietly
    # undo the whole energy constitution.
    $hbmNetwork = Find-ObjectById -Items (Get-PropertyValue -Object $energyRegistry -Name 'networks') -IdField 'network_id' -Id 'industrial_frontier:energy/hbm_reserved'
    $hbmConverter = Find-ObjectById -Items (Get-PropertyValue -Object $energyRegistry -Name 'converters') -IdField 'converter_id' -Id 'industrial_frontier:converter/future_hbm_to_fe'
    if ($null -eq $hbmNetwork -or [string](Get-PropertyValue -Object $hbmNetwork -Name 'status') -ne 'ACTIVE_INSTALLED' -or @(Get-PropertyValue -Object $hbmNetwork -Name 'installed_mod_ids') -notcontains 'hbm_ntm_rebirth') {
        Add-ValidationError 'HBM energy network must be ACTIVE_INSTALLED and name hbm_ntm_rebirth after the M7 wave.'
    }
    if ($null -eq $hbmConverter -or [string](Get-PropertyValue -Object $hbmConverter -Name 'status') -ne 'GATED_NOT_INSTALLED' -or @(Get-PropertyValue -Object $hbmConverter -Name 'implementation_refs').Count -ne 0) {
        Add-ValidationError 'Future HBM -> FE converter must be GATED_NOT_INSTALLED with no implementation IDs.'
    }

    # Every bridge has explicit one-way direction, ratios/limit fields and a
    # closed reverse flag. Only enabled bridges participate in cycle analysis.
    $activeConverters = [System.Collections.Generic.List[object]]::new()
    foreach ($converter in @(Get-PropertyValue -Object $energyRegistry -Name 'converters')) {
        $converterId = Get-RecordId -Object $converter
        foreach ($requiredField in @('source_network_ref', 'target_network_ref', 'direction', 'input_units', 'output_units', 'max_rate', 'reverse_path_allowed', 'cycle_audit')) {
            if (-not (Has-Property -Object $converter -Name $requiredField)) {
                Add-ValidationError "Energy converter '$converterId' lacks '$requiredField'."
            }
        }
        if ([string](Get-PropertyValue -Object $converter -Name 'direction') -ne 'ONE_WAY') {
            Add-ValidationError "Energy converter '$converterId' must be ONE_WAY."
        }
        if ((Get-PropertyValue -Object $converter -Name 'reverse_path_allowed') -ne $false) {
            Add-ValidationError "Energy converter '$converterId' must explicitly forbid its reverse path."
        }
        $status = [string](Get-PropertyValue -Object $converter -Name 'status')
        if ($status -match '^(ACTIVE|ACCEPTED)') {
            $inputUnits = Get-PropertyValue -Object $converter -Name 'input_units'
            $outputUnits = Get-PropertyValue -Object $converter -Name 'output_units'
            try {
                if ([decimal]$inputUnits -le 0 -or [decimal]$outputUnits -le 0) {
                    Add-ValidationError "Active converter '$converterId' must have positive input_units and output_units."
                }
            }
            catch {
                Add-ValidationError "Active converter '$converterId' has non-numeric input/output limits."
            }
            if ($null -eq (Get-PropertyValue -Object $converter -Name 'max_rate')) {
                $cycleAudit = [string](Get-PropertyValue -Object $converter -Name 'cycle_audit')
                $gateRefs = @(Get-PropertyValue -Object $converter -Name 'gate_refs')
                if ($cycleAudit -notmatch 'USER_TEST_REQUIRED' -or $gateRefs -notcontains 'industrial_frontier:gate/energy/runtime_cycle_test') {
                    Add-ValidationError "Active converter '$converterId' has no max_rate and no explicit owner-test limit gate."
                }
            }
            else {
                try {
                    if ([decimal](Get-PropertyValue -Object $converter -Name 'max_rate') -le 0) {
                        Add-ValidationError "Active converter '$converterId' has a non-positive max_rate."
                    }
                }
                catch {
                    Add-ValidationError "Active converter '$converterId' has a non-numeric max_rate."
                }
            }
            $activeConverters.Add($converter)
        }
    }

    $adjacency = @{}
    $activeEdgePairs = @{}
    foreach ($converter in $activeConverters) {
        $source = [string](Get-PropertyValue -Object $converter -Name 'source_network_ref')
        $target = [string](Get-PropertyValue -Object $converter -Name 'target_network_ref')
        $pair = "$source->$target"
        if ($activeEdgePairs.ContainsKey($pair)) {
            Add-ValidationError "Duplicate active energy bridge '$pair'."
        }
        else {
            $activeEdgePairs[$pair] = Get-RecordId -Object $converter
        }
        if (-not $adjacency.ContainsKey($source)) { $adjacency[$source] = @() }
        $adjacency[$source] = @($adjacency[$source]) + @($converter)
    }
    foreach ($converter in $activeConverters) {
        $source = [string](Get-PropertyValue -Object $converter -Name 'source_network_ref')
        $target = [string](Get-PropertyValue -Object $converter -Name 'target_network_ref')
        if ($activeEdgePairs.ContainsKey("$target->$source")) {
            Add-ValidationError "Active reverse energy bridges form a loop: $source <-> $target."
        }
        $visited = @{}
        if (Test-ReachableEnergyNetwork -Current $target -Target $source -Visited $visited -Adjacency $adjacency) {
            Add-ValidationError "Active energy bridge '$(Get-RecordId $converter)' participates in a directed conversion cycle."
        }
    }
    foreach ($forbiddenLink in @(Get-PropertyValue -Object $energyRegistry -Name 'forbidden_links')) {
        if ([string](Get-PropertyValue -Object $forbiddenLink -Name 'status') -eq 'FORBIDDEN') {
            $pair = "$(Get-PropertyValue $forbiddenLink 'source_network_ref')->$(Get-PropertyValue $forbiddenLink 'target_network_ref')"
            if ($activeEdgePairs.ContainsKey($pair)) {
                Add-ValidationError "Forbidden energy link is active: $pair via $($activeEdgePairs[$pair])."
            }
        }
    }
}

# Material-form conversions are explicitly non-profitable. Unknown conversions
# stay gated rather than receiving invented ratios.
$formsInfo = $documentsByRegistryId['industrial_frontier:m2/material_forms']
$formsRegistry = if ($null -eq $formsInfo) { $null } else { $formsInfo.document }
if ($null -eq $formsRegistry) {
    Add-ValidationError 'Missing industrial_frontier:m2/material_forms registry.'
}
else {
    foreach ($form in @(Get-PropertyValue -Object $formsRegistry -Name 'forms')) {
        $canonicalTermRu = Get-PropertyValue -Object $form -Name 'canonical_term_ru'
        if ($canonicalTermRu -isnot [string] -or [string]::IsNullOrWhiteSpace([string]$canonicalTermRu)) {
            Add-ValidationError "Form '$(Get-RecordId $form)' lacks canonical_term_ru."
        }
        $conversion = Get-PropertyValue -Object $form -Name 'conversion'
        if ($null -eq $conversion) {
            Add-ValidationError "Form '$(Get-RecordId $form)' lacks a conversion policy."
            continue
        }
        if ((Get-PropertyValue -Object $conversion -Name 'material_gain_forbidden') -ne $true) {
            Add-ValidationError "Form '$(Get-RecordId $form)' does not forbid material gain."
        }
        $inputUnits = Get-PropertyValue -Object $conversion -Name 'input_units'
        $outputUnits = Get-PropertyValue -Object $conversion -Name 'output_units'
        if ($null -ne $inputUnits -or $null -ne $outputUnits) {
            if ($null -eq $inputUnits -or $null -eq $outputUnits) {
                Add-ValidationError "Form '$(Get-RecordId $form)' has a partial conversion ratio."
            }
            else {
                try {
                    if ([decimal]$inputUnits -le 0 -or [decimal]$outputUnits -le 0 -or [decimal]$outputUnits -gt [decimal]$inputUnits) {
                        Add-ValidationError "Form '$(Get-RecordId $form)' has a positive or invalid material conversion ratio."
                    }
                }
                catch {
                    Add-ValidationError "Form '$(Get-RecordId $form)' has non-numeric conversion units."
                }
            }
        }
    }
}

# Atomic and planetary worldgen were decided in M7 and must stay decided. The
# rule is unchanged since M0 — GregTech owns ore generation — so the check moved
# from "still blocked" to "named an owner and named who was disabled".
$worldgenInfo = $documentsByRegistryId['industrial_frontier:m2/worldgen_ownership']
$worldgenRegistry = if ($null -eq $worldgenInfo) { $null } else { $worldgenInfo.document }
if ($null -eq $worldgenRegistry) {
    Add-ValidationError 'Missing industrial_frontier:m2/worldgen_ownership registry.'
}
else {
    foreach ($decidedWorldgen in @(
        @{ id = 'industrial_frontier:worldgen/future_atomic_feedstocks'; status = 'DISABLED_DUPLICATE'; disabled = @('nuclearcraft', 'hbm_ntm_rebirth') },
        @{ id = 'industrial_frontier:worldgen/future_planetary_resources'; status = 'PRESERVED_UNIQUE'; disabled = @('creatingspace') }
    )) {
        $decision = Find-ObjectById -Items (Get-PropertyValue -Object $worldgenRegistry -Name 'ownership_decisions') -IdField 'decision_id' -Id $decidedWorldgen.id
        if ($null -eq $decision) {
            Add-ValidationError "Missing worldgen decision '$($decidedWorldgen.id)'."
            continue
        }
        if ([string](Get-PropertyValue -Object $decision -Name 'status') -ne $decidedWorldgen.status) {
            Add-ValidationError "Worldgen decision '$($decidedWorldgen.id)' must be $($decidedWorldgen.status) after the M7 wave."
        }
        $disabledProviders = @(Get-PropertyValue -Object $decision -Name 'disabled_provider_mod_ids')
        foreach ($expectedProvider in $decidedWorldgen.disabled) {
            if ($disabledProviders -notcontains $expectedProvider) {
                Add-ValidationError "Worldgen decision '$($decidedWorldgen.id)' no longer records $expectedProvider as a disabled provider."
            }
        }
    }
}

$bypassInfo = $documentsByRegistryId['industrial_frontier:m2/bypass_decisions']
$bypassRegistry = if ($null -eq $bypassInfo) { $null } else { $bypassInfo.document }
if ($null -eq $bypassRegistry) {
    Add-ValidationError 'Missing industrial_frontier:m2/bypass_decisions registry.'
}
else {
    $futureBypass = Find-ObjectById -Items (Get-PropertyValue -Object $bypassRegistry -Name 'decisions') -IdField 'bypass_id' -Id 'industrial_frontier:bypass/future_nuclear_hbm_cycles'
    if ($null -eq $futureBypass -or [string](Get-PropertyValue -Object $futureBypass -Name 'status') -ne 'CLOSED_STATIC') {
        Add-ValidationError 'The NuclearCraft/HBM bypass entry must be CLOSED_STATIC after the M7 wave.'
    }
    foreach ($decision in @(Get-PropertyValue -Object $bypassRegistry -Name 'decisions')) {
        $status = [string](Get-PropertyValue -Object $decision -Name 'status')
        $profit = Get-PropertyValue -Object $decision -Name 'profit_check'
        if ($null -eq $profit) {
            Add-ValidationError "Bypass decision '$(Get-RecordId $decision)' lacks profit_check."
            continue
        }
        $materialGain = [string](Get-PropertyValue -Object $profit -Name 'material_gain')
        $energyCycle = [string](Get-PropertyValue -Object $profit -Name 'energy_cycle')
        if ($materialGain -match '^(POSITIVE|PROFIT|FREE)') {
            Add-ValidationError "Bypass decision '$(Get-RecordId $decision)' permits positive material gain."
        }
        if ($energyCycle -match '^(POSITIVE|PROFIT|FREE)') {
            Add-ValidationError "Bypass decision '$(Get-RecordId $decision)' permits a free energy cycle."
        }
        if ($status -match '^(CLOSED|ACCEPTED)' -and [string]::IsNullOrWhiteSpace([string](Get-PropertyValue -Object $profit -Name 'static_result'))) {
            Add-ValidationError "Closed/accepted bypass decision '$(Get-RecordId $decision)' lacks a static_result."
        }
    }
}

# The pack explicitly excludes these competing global technology systems.
foreach ($relative in @($registryRawText.Keys | Sort-Object)) {
    $text = [string]$registryRawText[$relative]
    if ($text -match '(?i)__[A-Z0-9_]*(?:PLACEHOLDER|TODO|TBD)[A-Z0-9_]*__|"\s*(?:TODO|TBD)\s*"') {
        Add-ValidationError "Unresolved placeholder token appears in $relative."
    }
    if ($text -match '(?i)mekanism') {
        Add-ValidationError "Forbidden technology system Mekanism appears in $relative."
    }
    if ($text -match '(?i)industrial[ _-]?foregoing') {
        Add-ValidationError "Forbidden technology system Industrial Foregoing appears in $relative."
    }
}
# An owner may knowingly accept a deviation from an architectural rule, but only
# on the record: the entry names the files, the reason, the limits and the
# milestone that closes it. A record whose file is not installed is stale and
# fails, so the list cannot quietly rot into a blanket exemption.
$acceptedDeviationFiles = @{}
$deviationPath = Join-Path $rootPath 'docs\registries\accepted_deviations.json'
if (Test-Path -LiteralPath $deviationPath -PathType Leaf) {
    $deviationRegistry = Read-JsonDocument -Path $deviationPath -Label 'docs/registries/accepted_deviations.json'
    if ($null -ne $deviationRegistry) {
        foreach ($deviation in @(Get-PropertyValue -Object $deviationRegistry -Name 'deviations')) {
            $deviationId = [string](Get-PropertyValue -Object $deviation -Name 'deviation_id')
            foreach ($fieldName in @('rule_ru', 'reason_ru', 'limits_ru', 'resolved_in', 'decided_on', 'owner')) {
                $fieldValue = Get-PropertyValue -Object $deviation -Name $fieldName
                if ($fieldValue -isnot [string] -or [string]::IsNullOrWhiteSpace([string]$fieldValue)) {
                    Add-ValidationError "Accepted deviation '$deviationId' lacks '$fieldName'."
                }
            }
            foreach ($deviationFile in @(Get-PropertyValue -Object $deviation -Name 'files')) {
                $deviationFileName = [string]$deviationFile
                $acceptedDeviationFiles[$deviationFileName] = $deviationId
                if (-not (Test-Path -LiteralPath (Join-Path $rootPath "mods\$deviationFileName") -PathType Leaf)) {
                    Add-ValidationError "Accepted deviation '$deviationId' names a mod that is not installed: $deviationFileName"
                }
            }
        }
    }
}

$ownershipRegistry = $documentsByRegistryId['industrial_frontier:m2/domain_process_ownership']
$civilNuclearDomainStatus = 'UNKNOWN'
$strategicNuclearDomainStatus = 'UNKNOWN'
if ($null -ne $ownershipRegistry) {
    $civilNuclearDomain = Find-ObjectById -Items (Get-PropertyValue -Object $ownershipRegistry.document -Name 'domains') -IdField 'domain_id' -Id 'industrial_frontier:domain/civil_nuclear_industry'
    if ($null -ne $civilNuclearDomain) {
        $civilNuclearDomainStatus = [string](Get-PropertyValue -Object $civilNuclearDomain -Name 'status')
    }
    $strategicNuclearDomain = Find-ObjectById -Items (Get-PropertyValue -Object $ownershipRegistry.document -Name 'domains') -IdField 'domain_id' -Id 'industrial_frontier:domain/strategic_nuclear_program'
    if ($null -ne $strategicNuclearDomain) {
        $strategicNuclearDomainStatus = [string](Get-PropertyValue -Object $strategicNuclearDomain -Name 'status')
    }
}

$modsDirectory = Join-Path $rootPath 'mods'
if (Test-Path -LiteralPath $modsDirectory -PathType Container) {
    foreach ($modFile in Get-ChildItem -LiteralPath $modsDirectory -File) {
        if ($modFile.Extension -ine '.jar') { continue }
        if ($modFile.Name -match '(?i)mekanism|industrial[ _-]?foregoing') {
            Add-ValidationError "Forbidden technology mod is installed: $($modFile.Name)"
        }
        # A nuclear mod stops being "future" the moment its domain is declared
        # installed. Reading that from the architecture beats hardcoding a
        # filename list here: when the M6 wave arrived, exactly one registry
        # line changed and this check followed it.
        if ($modFile.Name -match '(?i)nuclear[ _-]?craft') {
            if ($civilNuclearDomainStatus -ne 'ACTIVE_INSTALLED' -and -not $acceptedDeviationFiles.ContainsKey($modFile.Name)) {
                Add-ValidationError "Civil nuclear mod is installed while its domain is still $civilNuclearDomainStatus`: $($modFile.Name)"
            }
            elseif ($civilNuclearDomainStatus -ne 'ACTIVE_INSTALLED') {
                Add-ValidationWarning "Accepted deviation $($acceptedDeviationFiles[$modFile.Name]): $($modFile.Name) is installed ahead of its gated integration stage."
            }
        }
        # The strategic port follows the same rule as the civil one: it stops
        # being "future" when its domain is declared installed. Before M7 this
        # branch could only be silenced by an accepted deviation; now the
        # architecture answers for it, and the deviation list is empty again.
        elseif ($modFile.Name -match '(?i)(^|[._-])hbm([._-]|$)|(^|[._-])ntm([._-]|$)') {
            if ($strategicNuclearDomainStatus -ne 'ACTIVE_INSTALLED' -and -not $acceptedDeviationFiles.ContainsKey($modFile.Name)) {
                Add-ValidationError "Strategic nuclear mod is installed while its domain is still $strategicNuclearDomainStatus`: $($modFile.Name)"
            }
            elseif ($strategicNuclearDomainStatus -ne 'ACTIVE_INSTALLED') {
                Add-ValidationWarning "Accepted deviation $($acceptedDeviationFiles[$modFile.Name]): $($modFile.Name) is installed ahead of its gated integration stage."
            }
        }
    }
}

# Exact static configuration decisions. These checks read text only and never
# initialize Forge, Java or Minecraft.
Assert-BooleanConfigValue -RelativePath 'config/create-common.toml' -Key 'disableWorldGen' -Expected $true
Assert-BooleanConfigValue -RelativePath 'config/gtceu.yaml' -Key 'removeVanillaOreGen' -Expected $true
Assert-BooleanConfigValue -RelativePath 'config/gtceu.yaml' -Key 'removeVanillaLargeOreVeins' -Expected $true
Assert-BooleanConfigValue -RelativePath 'config/gtceu.yaml' -Key 'enableFEConverters' -Expected $false

if ($null -ne $worldgenRegistry) {
    Assert-WorldgenCheck -WorldgenRegistry $worldgenRegistry -DecisionId 'industrial_frontier:worldgen/gtceu_geological_ores' -Key 'worldgen.disableWorldGen' -Expected 'true'
    Assert-WorldgenCheck -WorldgenRegistry $worldgenRegistry -DecisionId 'industrial_frontier:worldgen/vanilla_ores_suppressed' -Key 'worldgen.oreVeins.removeVanillaOreGen' -Expected 'true'
    Assert-WorldgenCheck -WorldgenRegistry $worldgenRegistry -DecisionId 'industrial_frontier:worldgen/vanilla_ores_suppressed' -Key 'worldgen.oreVeins.removeVanillaLargeOreVeins' -Expected 'true'
}
if ($null -ne $energyRegistry) {
    $disabledFeConverter = Find-ObjectById -Items (Get-PropertyValue -Object $energyRegistry -Name 'converters') -IdField 'converter_id' -Id 'industrial_frontier:converter/gtceu_fe_to_eu_disabled'
    if ($null -eq $disabledFeConverter -or [string](Get-PropertyValue -Object $disabledFeConverter -Name 'status') -ne 'DISABLED_BY_CONFIG' -or @(Get-PropertyValue -Object $disabledFeConverter -Name 'implementation_refs') -notcontains 'config/gtceu.yaml#compatibility.energy.enableFEConverters') {
        Add-ValidationError 'Energy registry must keep GTCEu FE -> EU converters disabled by config.'
    }
}
if ($null -ne $bypassRegistry) {
    $createWorldgenBypass = Find-ObjectById -Items (Get-PropertyValue -Object $bypassRegistry -Name 'decisions') -IdField 'bypass_id' -Id 'industrial_frontier:bypass/create_zinc_worldgen'
    $feToEuBypass = Find-ObjectById -Items (Get-PropertyValue -Object $bypassRegistry -Name 'decisions') -IdField 'bypass_id' -Id 'industrial_frontier:bypass/gtceu_fe_to_eu'
    if ($null -eq $createWorldgenBypass -or [string](Get-PropertyValue -Object $createWorldgenBypass -Name 'status') -ne 'CLOSED_STATIC' -or [string](Get-PropertyValue -Object (Get-PropertyValue -Object $createWorldgenBypass -Name 'enforcement') -Name 'expected_state_ru') -notmatch 'disableWorldGen=true') {
        Add-ValidationError 'Bypass registry must statically close Create worldgen with disableWorldGen=true.'
    }
    if ($null -eq $feToEuBypass -or [string](Get-PropertyValue -Object $feToEuBypass -Name 'status') -ne 'CLOSED_STATIC' -or [string](Get-PropertyValue -Object (Get-PropertyValue -Object $feToEuBypass -Name 'enforcement') -Name 'expected_state_ru') -notmatch 'enableFEConverters=false') {
        Add-ValidationError 'Bypass registry must statically close GTCEu FE -> EU converters with enableFEConverters=false.'
    }
}

# If the extended domain registry is finalized, its installed/future component
# claims must remain honest. Temporary design placeholders are intentionally not
# interpreted as runtime content here.
$extendedInfo = $documentsByRegistryId['industrial_frontier:m2_extended_domains']
if ($null -ne $extendedInfo) {
    $extended = $extendedInfo.document
    $extendedRawText = if ($registryRawText.ContainsKey([string]$extendedInfo.path)) { [string]$registryRawText[[string]$extendedInfo.path] } else { '' }
    if ($extendedRawText.IndexOf([string][char]0xFFFD, [System.StringComparison]::Ordinal) -ge 0) {
        Add-ValidationError 'Extended-domain registry contains the Unicode replacement character U+FFFD.'
    }
    $extendedTemporaryFiles = @(Get-ChildItem -LiteralPath (Join-Path $rootPath 'docs\registries') -File | Where-Object {
        $_.Name -match '^m2_extended_domains.*(?:\.tmp|\.temp|\.bak)$'
    })
    if ($extendedTemporaryFiles.Count -ne 0) {
        Add-ValidationError "Extended-domain migration left $($extendedTemporaryFiles.Count) temporary file(s): $($extendedTemporaryFiles.Name -join ', ')."
    }

    $extendedComponents = @(Get-PropertyValue -Object $extended -Name 'components')
    Assert-ManifestCount -RegistryId 'industrial_frontier:m2_extended_domains' -CountName 'components' -ActualCount $extendedComponents.Count -Context 'Extended components'
    $extendedComponentById = @{}
    foreach ($component in $extendedComponents) {
        $componentId = [string](Get-PropertyValue -Object $component -Name 'component_id')
        if ($extendedComponentById.ContainsKey($componentId)) {
            Add-ValidationError "Extended baseline repeats component_id '$componentId'."
        }
        else { $extendedComponentById[$componentId] = $component }
    }

    $conceptRegistry = Get-PropertyValue -Object $extended -Name 'concept_registry'
    $typedConcepts = @(Get-PropertyValue -Object $conceptRegistry -Name 'concepts')
    Assert-ManifestCount -RegistryId 'industrial_frontier:m2_extended_domains' -CountName 'typed_concepts' -ActualCount $typedConcepts.Count -Context 'Extended typed concepts'
    $conceptById = @{}
    foreach ($concept in $typedConcepts) {
        $conceptId = [string](Get-PropertyValue -Object $concept -Name 'concept_id')
        if ($conceptById.ContainsKey($conceptId)) {
            Add-ValidationError "Extended concept_registry repeats concept_id '$conceptId'."
        }
        else { $conceptById[$conceptId] = $concept }
    }
    $conceptCoreFieldKinds = @{
        substance_refs = 'substance_id'
        form_refs = 'form_id'
        process_refs = 'process_id'
    }
    foreach ($concept in $typedConcepts) {
        $conceptId = [string](Get-PropertyValue -Object $concept -Name 'concept_id')
        $conceptStatus = [string](Get-PropertyValue -Object $concept -Name 'status')
        $conceptEpoch = Get-EpochNumber (Get-PropertyValue -Object $concept -Name 'first_epoch')
        $conceptReason = Get-PropertyValue -Object $concept -Name 'reason_ru'
        if ($null -eq $conceptEpoch) {
            Add-ValidationError "Typed concept '$conceptId' has invalid first_epoch."
        }
        if ($conceptReason -isnot [string] -or [string]::IsNullOrWhiteSpace([string]$conceptReason)) {
            Add-ValidationError "Typed concept '$conceptId' lacks an explicit Russian mapping/gate/out-of-scope reason."
        }
        $conceptCoreRefs = Get-PropertyValue -Object $concept -Name 'core_dependency_refs'
        if (-not (Test-IsJsonObject -Value $conceptCoreRefs)) {
            Add-ValidationError "Typed concept '$conceptId' lacks core_dependency_refs."
            continue
        }
        $physicalConceptRefCount = 0
        foreach ($fieldName in @('substance_refs', 'form_refs', 'process_refs')) {
            $fieldRefs = @(Get-PropertyValue -Object $conceptCoreRefs -Name $fieldName)
            $physicalConceptRefCount += $fieldRefs.Count
            foreach ($coreRefValue in $fieldRefs) {
                $coreRef = [string]$coreRefValue
                $expectedKind = [string]$conceptCoreFieldKinds[$fieldName]
                if (-not $idKinds.ContainsKey($coreRef) -or [string]$idKinds[$coreRef] -ne $expectedKind) {
                    $actualKind = if ($idKinds.ContainsKey($coreRef)) { [string]$idKinds[$coreRef] } else { 'unresolved' }
                    Add-ValidationError "Typed concept '$conceptId' $fieldName ref '$coreRef' is $actualKind, expected $expectedKind."
                }
            }
        }
        foreach ($fallbackRefValue in @(Get-PropertyValue -Object $conceptCoreRefs -Name 'fallback_concept_refs')) {
            $fallbackRef = [string]$fallbackRefValue
            if (-not $conceptById.ContainsKey($fallbackRef)) {
                Add-ValidationError "Typed concept '$conceptId' has unresolved fallback_concept_ref '$fallbackRef'."
            }
            elseif ($fallbackRef -ceq $conceptId) {
                Add-ValidationError "Typed concept '$conceptId' refers to itself as a fallback concept."
            }
        }
        foreach ($conceptDependencyRefValue in @(Get-PropertyValue -Object $concept -Name 'concept_dependency_refs')) {
            $conceptDependencyRef = [string]$conceptDependencyRefValue
            if (-not $conceptById.ContainsKey($conceptDependencyRef)) {
                Add-ValidationError "Typed concept '$conceptId' has unresolved concept_dependency_ref '$conceptDependencyRef'."
            }
            elseif ($conceptDependencyRef -ceq $conceptId) {
                Add-ValidationError "Typed concept '$conceptId' has a self dependency."
            }
        }
        if ($conceptStatus -eq 'CORE_MAPPED' -and $physicalConceptRefCount -eq 0) {
            Add-ValidationError "CORE_MAPPED concept '$conceptId' has no substance/form/process mapping."
        }
        if ($conceptStatus -in @('PACK_NATIVE_ABSTRACT', 'OUT_OF_SCOPE_WITH_REASON') -and $physicalConceptRefCount -ne 0) {
            Add-ValidationError "$conceptStatus concept '$conceptId' must not claim physical core IDs."
        }
    }

    foreach ($component in @(Get-PropertyValue -Object $extended -Name 'components')) {
        $componentId = [string](Get-PropertyValue -Object $component -Name 'component_id')
        $state = [string](Get-PropertyValue -Object $component -Name 'integration_state')
        $runtimeClaims = Get-PropertyValue -Object $component -Name 'runtime_claims_allowed'
        if ($state -eq 'GATED_NOT_INSTALLED' -and $runtimeClaims -ne $false) {
            Add-ValidationError "Future extended component '$componentId' must forbid runtime claims."
        }
        if ($state -eq 'INSTALLED_CURRENT') {
            $sourceDocument = [string](Get-PropertyValue -Object $component -Name 'source_document')
            $sourcePath = Resolve-RootRelativePath -RelativePath $sourceDocument -Context "extended component '$componentId'"
            if ($runtimeClaims -ne $true -or $null -eq $sourcePath -or -not (Test-Path -LiteralPath $sourcePath -PathType Leaf)) {
                Add-ValidationError "Installed extended component '$componentId' lacks an allowed, existing source claim."
            }
        }
    }

    # Build one core availability map for epoch-safe construction, food and
    # combat dependencies. Forms inherit the epoch of their substance;
    # processes use earliest_epoch.
    $coreAvailabilityById = @{}
    $coreSubstanceInfo = $documentsByRegistryId['industrial_frontier:m2/substance_passports']
    if ($null -ne $coreSubstanceInfo) {
        foreach ($collectionName in @('passports', 'planned_substances')) {
            foreach ($substance in @(Get-PropertyValue -Object $coreSubstanceInfo.document -Name $collectionName)) {
                $substanceId = [string](Get-PropertyValue -Object $substance -Name 'substance_id')
                $coreAvailabilityById[$substanceId] = [int](Get-PropertyValue -Object $substance -Name 'first_epoch')
            }
        }
    }
    $coreFormsInfo = $documentsByRegistryId['industrial_frontier:m2/material_forms']
    if ($null -ne $coreFormsInfo) {
        foreach ($form in @(Get-PropertyValue -Object $coreFormsInfo.document -Name 'forms')) {
            $formId = [string](Get-PropertyValue -Object $form -Name 'form_id')
            $substanceRef = [string](Get-PropertyValue -Object $form -Name 'substance_ref')
            if ($coreAvailabilityById.ContainsKey($substanceRef)) {
                $coreAvailabilityById[$formId] = [int]$coreAvailabilityById[$substanceRef]
            }
        }
    }
    if ($null -ne $domainRegistry) {
        foreach ($domain in @(Get-PropertyValue -Object $domainRegistry -Name 'domains')) {
            foreach ($process in @(Get-PropertyValue -Object $domain -Name 'processes')) {
                $processEpochValue = Get-PropertyValue -Object $process -Name 'earliest_epoch'
                if ($null -ne $processEpochValue) {
                    $coreAvailabilityById[[string](Get-PropertyValue -Object $process -Name 'process_id')] = [int]$processEpochValue
                }
            }
        }
    }

    foreach ($waterConceptContract in @(
        [pscustomobject]@{ id = 'food.raw_water'; substance = 'industrial_frontier:substance/raw_water' },
        [pscustomobject]@{ id = 'food.drinking_water'; substance = 'industrial_frontier:substance/drinking_water' }
    )) {
        if (-not $coreAvailabilityById.ContainsKey([string]$waterConceptContract.substance)) {
            Add-ValidationError "Missing core availability for water substance '$($waterConceptContract.substance)'."
            continue
        }
        $waterSubstanceEpoch = [int]$coreAvailabilityById[[string]$waterConceptContract.substance]
        if (-not $conceptById.ContainsKey([string]$waterConceptContract.id)) {
            Add-ValidationError "Missing water concept '$($waterConceptContract.id)'."
            continue
        }
        $waterConcept = $conceptById[[string]$waterConceptContract.id]
        if ((Get-EpochNumber (Get-PropertyValue -Object $waterConcept -Name 'first_epoch')) -ne $waterSubstanceEpoch -or
            @(Get-PropertyValue -Object (Get-PropertyValue -Object $waterConcept -Name 'core_dependency_refs') -Name 'substance_refs') -cnotcontains [string]$waterConceptContract.substance) {
            Add-ValidationError "Water concept '$($waterConceptContract.id)' must map to '$($waterConceptContract.substance)' at its passport epoch P$waterSubstanceEpoch."
        }
    }
    if ($coreAvailabilityById.ContainsKey('industrial_frontier:substance/raw_water') -and [int]$coreAvailabilityById['industrial_frontier:substance/raw_water'] -ne 0) {
        Add-ValidationError 'raw_water must be available in the fixed P0 bootstrap epoch.'
    }
    if ($coreAvailabilityById.ContainsKey('industrial_frontier:substance/raw_water') -and $coreAvailabilityById.ContainsKey('industrial_frontier:substance/drinking_water') -and
        [int]$coreAvailabilityById['industrial_frontier:substance/drinking_water'] -le [int]$coreAvailabilityById['industrial_frontier:substance/raw_water']) {
        Add-ValidationError 'drinking_water must unlock strictly after raw_water treatment input.'
    }

    # Loadout archetypes are typed role contracts. Their class references must
    # resolve to the matching concept kind, budgets must agree with ammunition
    # class, and artillery/role duties must remain semantically coherent.
    $loadoutArchetypes = @(Get-PropertyValue -Object $extended -Name 'loadout_archetypes')
    Assert-ManifestCount -RegistryId 'industrial_frontier:m2_extended_domains' -CountName 'loadout_archetypes' -ActualCount $loadoutArchetypes.Count -Context 'Extended loadout archetypes'
    $loadoutArchetypeById = @{}
    $ammoClassByBudget = @{
        NONE = 'equipment.ammunition.none'
        LOW = 'equipment.ammunition.low_personal'
        STANDARD = 'equipment.ammunition.standard_personal'
        HIGH = 'equipment.ammunition.high_personal'
        PRECISION = 'equipment.ammunition.precision'
        ENGINEERING = 'equipment.ammunition.engineering'
        CREW = 'equipment.ammunition.crew'
    }
    $loadoutClassContracts = @{
        weapon_class_refs = 'WEAPON_CLASS'
        armor_class_refs = 'ARMOR_CLASS'
        ammunition_class_refs = 'AMMUNITION_CLASS'
        artillery_class_refs = 'ARTILLERY_CLASS'
    }
    foreach ($archetype in $loadoutArchetypes) {
        $archetypeId = [string](Get-PropertyValue -Object $archetype -Name 'archetype_id')
        if ($loadoutArchetypeById.ContainsKey($archetypeId)) {
            Add-ValidationError "Duplicate loadout archetype '$archetypeId'."
        }
        else { $loadoutArchetypeById[$archetypeId] = $archetype }
        $epochBounds = Get-PropertyValue -Object $archetype -Name 'tech_epoch_bounds'
        $minimumEpoch = Get-EpochNumber (Get-PropertyValue -Object $epochBounds -Name 'minimum')
        $maximumEpoch = Get-EpochNumber (Get-PropertyValue -Object $epochBounds -Name 'maximum')
        if ($null -eq $minimumEpoch -or $null -eq $maximumEpoch -or [int]$minimumEpoch -gt [int]$maximumEpoch) {
            Add-ValidationError "Loadout archetype '$archetypeId' has invalid tech_epoch_bounds."
        }
        $allowedClasses = Get-PropertyValue -Object $archetype -Name 'allowed_class_refs'
        foreach ($classField in @($loadoutClassContracts.Keys)) {
            $classRefs = @(Get-PropertyValue -Object $allowedClasses -Name $classField)
            foreach ($classRefValue in $classRefs) {
                $classRef = [string]$classRefValue
                if (-not $conceptById.ContainsKey($classRef)) {
                    Add-ValidationError "Loadout archetype '$archetypeId' has unresolved $classField '$classRef'."
                }
                elseif ([string](Get-PropertyValue -Object $conceptById[$classRef] -Name 'concept_kind') -cne [string]$loadoutClassContracts[$classField]) {
                    Add-ValidationError "Loadout archetype '$archetypeId' $classField '$classRef' has the wrong concept kind."
                }
            }
        }
        $loadoutBudget = Get-PropertyValue -Object $archetype -Name 'budget'
        $ammoBudget = [string](Get-PropertyValue -Object $loadoutBudget -Name 'ammo_budget')
        $expectedAmmoClass = if ($ammoClassByBudget.ContainsKey($ammoBudget)) { [string]$ammoClassByBudget[$ammoBudget] } else { '' }
        if ([string]::IsNullOrWhiteSpace($expectedAmmoClass) -or @(Get-PropertyValue -Object $allowedClasses -Name 'ammunition_class_refs') -cnotcontains $expectedAmmoClass) {
            Add-ValidationError "Loadout archetype '$archetypeId' ammo budget '$ammoBudget' is incompatible with its ammunition class refs."
        }
        $roleCategory = [string](Get-PropertyValue -Object $archetype -Name 'role_category')
        if ($roleCategory -in @('role.security', 'role.combat', 'role.combat_support', 'role.command') -and $ammoBudget -eq 'NONE') {
            Add-ValidationError "Armed role archetype '$archetypeId' cannot use ammo budget NONE."
        }
        $duties = Get-PropertyValue -Object $archetype -Name 'duties'
        if ($roleCategory -eq 'role.medical' -and [string](Get-PropertyValue -Object $duties -Name 'medical') -in @('duty.none', 'duty.first_aid')) {
            Add-ValidationError "Medical archetype '$archetypeId' lacks a specialist medical duty."
        }
        if ($roleCategory -eq 'role.engineering' -and [string](Get-PropertyValue -Object $duties -Name 'repair') -in @('duty.none', 'duty.self_maintenance')) {
            Add-ValidationError "Engineering archetype '$archetypeId' lacks a specialist repair duty."
        }
        $artilleryAccess = Get-PropertyValue -Object $archetype -Name 'artillery_access'
        $artilleryState = [string](Get-PropertyValue -Object $artilleryAccess -Name 'state')
        $artilleryRefs = @(Get-PropertyValue -Object $allowedClasses -Name 'artillery_class_refs')
        if ($artilleryState -eq 'DISABLED') {
            if ($null -ne (Get-PropertyValue -Object $artilleryAccess -Name 'enabled_from_epoch') -or $artilleryRefs -cnotcontains 'equipment.artillery.disabled') {
                Add-ValidationError "Disabled-artillery archetype '$archetypeId' has inconsistent artillery access."
            }
        }
        elseif ($artilleryState -eq 'ENABLED_FROM_EPOCH') {
            $artilleryEpoch = Get-EpochNumber (Get-PropertyValue -Object $artilleryAccess -Name 'enabled_from_epoch')
            if ($null -eq $artilleryEpoch -or ($null -ne $minimumEpoch -and [int]$artilleryEpoch -lt [int]$minimumEpoch) -or
                $artilleryRefs -cnotcontains 'equipment.artillery.crew_operated' -or $ammoBudget -ne 'CREW' -or
                [string](Get-PropertyValue -Object $loadoutBudget -Name 'supply_budget') -ne 'CREW_LOGISTICS') {
                Add-ValidationError "Artillery archetype '$archetypeId' has incompatible epoch, class or crew budgets."
            }
        }
    }

    # Base levels describe when a blueprint may be generated natively. Older
    # bases may persist only as frozen legacy snapshots; that persistence must
    # never make a higher level native early.
    $baseLevels = @(Get-PropertyValue -Object $extended -Name 'base_levels')
    Assert-ManifestCount -RegistryId 'industrial_frontier:m2_extended_domains' -CountName 'base_levels' -ActualCount $baseLevels.Count -Context 'Extended base levels'
    $baseByLevel = @{}
    $highestIntroducedBaseByEpoch = @{}
    $previousBaseMinimum = -1
    foreach ($base in $baseLevels) {
        $baseLevel = [string](Get-PropertyValue -Object $base -Name 'level')
        if ($baseByLevel.ContainsKey($baseLevel)) {
            Add-ValidationError "Duplicate base level '$baseLevel'."
        }
        else { $baseByLevel[$baseLevel] = $base }
        $baseRange = Get-PropertyValue -Object $base -Name 'native_epoch_range'
        $baseMinimum = Get-EpochNumber (Get-PropertyValue -Object $baseRange -Name 'minimum')
        $baseMaximum = Get-EpochNumber (Get-PropertyValue -Object $baseRange -Name 'maximum')
        if ($null -eq $baseMinimum -or $null -eq $baseMaximum -or [int]$baseMinimum -gt [int]$baseMaximum) {
            Add-ValidationError "Base '$baseLevel' has an invalid native_epoch_range."
            continue
        }
        if ([int]$baseMinimum -le $previousBaseMinimum) {
            Add-ValidationError "Base '$baseLevel' does not advance beyond the preceding native-range minimum."
        }
        $previousBaseMinimum = [int]$baseMinimum
        $expectedIntroductionEpochs = @()
        for ($epoch = [int]$baseMinimum; $epoch -le [int]$baseMaximum; $epoch++) {
            $expectedIntroductionEpochs += "P$epoch"
        }
        $actualIntroductionEpochs = @(Get-PropertyValue -Object $base -Name 'introduction_epochs')
        if ($actualIntroductionEpochs.Count -ne $expectedIntroductionEpochs.Count) {
            Add-ValidationError "Base '$baseLevel' introduction_epochs must exactly cover its native range."
        }
        foreach ($expectedIntroductionEpoch in $expectedIntroductionEpochs) {
            if ($actualIntroductionEpochs -cnotcontains $expectedIntroductionEpoch) {
                Add-ValidationError "Base '$baseLevel' native range lacks introduction epoch '$expectedIntroductionEpoch'."
            }
        }
        if ([string](Get-PropertyValue -Object $base -Name 'legacy_snapshot_policy') -cne 'MAY_PERSIST_AFTER_NATIVE_RANGE_WITH_FROZEN_EPOCH_SNAPSHOT') {
            Add-ValidationError "Base '$baseLevel' lacks the frozen legacy snapshot policy."
        }
        Test-PositionalConceptMapping -Claims (Get-PropertyValue -Object $base -Name 'material_language') -ConceptRefs (Get-PropertyValue -Object $base -Name 'material_concept_refs') -AllowedKinds @('MATERIAL') -Context "Base '$baseLevel' materials" -ConsumerEpoch $baseMaximum -ConceptById $conceptById
    }
    for ($epoch = 0; $epoch -le 9; $epoch++) {
        $eligibleBaseLevels = @($baseLevels | Where-Object {
            $candidateMinimum = Get-EpochNumber (Get-PropertyValue -Object (Get-PropertyValue -Object $_ -Name 'native_epoch_range') -Name 'minimum')
            $null -ne $candidateMinimum -and [int]$candidateMinimum -le $epoch
        })
        if ($eligibleBaseLevels.Count -eq 0) {
            Add-ValidationError "No base level is introduced by P$epoch."
        }
        else {
            $highestIntroducedBaseByEpoch[$epoch] = @($eligibleBaseLevels | Sort-Object {
                Get-EpochNumber (Get-PropertyValue -Object (Get-PropertyValue -Object $_ -Name 'native_epoch_range') -Name 'minimum')
            })[-1]
        }
        $nativeAtEpoch = @($baseLevels | Where-Object {
            $range = Get-PropertyValue -Object $_ -Name 'native_epoch_range'
            $minimum = Get-EpochNumber (Get-PropertyValue -Object $range -Name 'minimum')
            $maximum = Get-EpochNumber (Get-PropertyValue -Object $range -Name 'maximum')
            $null -ne $minimum -and $null -ne $maximum -and $epoch -ge [int]$minimum -and $epoch -le [int]$maximum
        })
        if ($nativeAtEpoch.Count -eq 0) {
            Add-ValidationError "Base native ranges leave P$epoch uncovered."
        }
    }

    # Every faction epoch has one explicit loadout binding per listed role.
    # Cells may not collapse distinct roles onto one archetype, and a named role
    # inside one faction keeps its typed archetype across all epochs in which it
    # appears. The binding is capped by the same combat profile and epoch as its
    # row, while the row itself may expose only the highest base introduced so far.
    $factions = Get-PropertyValue -Object $extended -Name 'factions'
    if ($null -ne $factions) {
        $factionProperties = @($factions.PSObject.Properties)
        Assert-ManifestCount -RegistryId 'industrial_frontier:m2_extended_domains' -CountName 'factions' -ActualCount $factionProperties.Count -Context 'Extended factions'
        $totalFactionRows = 0
        $totalFactionRoleSlots = 0
        $totalFactionRoleBindings = 0
        $usedLoadoutArchetypes = @{}
        foreach ($factionProperty in $factionProperties) {
            $factionKey = [string]$factionProperty.Name
            $faction = $factionProperty.Value
            $factionId = [string](Get-PropertyValue -Object $faction -Name 'faction_id')
            if ($factionId -cne $factionKey) {
                Add-ValidationError "Faction key '$factionKey' does not match faction_id '$factionId'."
            }
            $epochRows = @(Get-PropertyValue -Object $faction -Name 'epoch_matrix')
            if ($epochRows.Count -ne 10) {
                Add-ValidationError "Faction '$factionKey' must contain exactly ten P0-P9 epoch rows; found $($epochRows.Count)."
            }
            $totalFactionRows += $epochRows.Count
            $seenFactionEpochs = @{}
            $factionRoleArchetype = @{}
            $roleCatalog = Get-PropertyValue -Object $faction -Name 'role_catalog'
            foreach ($row in $epochRows) {
                $rowEpochText = [string](Get-PropertyValue -Object $row -Name 'epoch')
                $rowEpoch = Get-EpochNumber -Value $rowEpochText
                $context = "Faction '$factionKey' epoch '$rowEpochText'"
                if ($null -eq $rowEpoch) {
                    Add-ValidationError "$context has an invalid epoch."
                    continue
                }
                if ($seenFactionEpochs.ContainsKey([int]$rowEpoch)) {
                    Add-ValidationError "Faction '$factionKey' repeats epoch P$rowEpoch."
                }
                else { $seenFactionEpochs[[int]$rowEpoch] = $true }
                $expectedProfile = "combat.P$rowEpoch"
                $rowProfile = [string](Get-PropertyValue -Object $row -Name 'equipment_profile_ref')
                if ($rowProfile -cne $expectedProfile) {
                    Add-ValidationError "$context equipment_profile_ref must be '$expectedProfile'."
                }
                $doctrineModifier = Get-PropertyValue -Object $row -Name 'faction_doctrine_modifier_ru'
                if ($doctrineModifier -isnot [string] -or [string]::IsNullOrWhiteSpace([string]$doctrineModifier)) {
                    Add-ValidationError "$context lacks a faction-specific doctrine modifier."
                }
                if (-not $highestIntroducedBaseByEpoch.ContainsKey([int]$rowEpoch)) {
                    Add-ValidationError "$context cannot resolve the highest base introduced by this epoch."
                }
                else {
                    $expectedBaseLevel = [string](Get-PropertyValue -Object $highestIntroducedBaseByEpoch[[int]$rowEpoch] -Name 'level')
                    $actualBaseLevel = [string](Get-PropertyValue -Object $row -Name 'max_base_level')
                    if ($actualBaseLevel -cne $expectedBaseLevel) {
                        Add-ValidationError "$context max_base_level must be '$expectedBaseLevel', not '$actualBaseLevel'."
                    }
                }
                $roleSet = @{}
                foreach ($role in @(Get-PropertyValue -Object $row -Name 'roles')) {
                    $role = [string]$role
                    if ($roleSet.ContainsKey($role)) {
                        Add-ValidationError "$context repeats role '$role'."
                    }
                    else { $roleSet[$role] = $true }
                    if (-not (Has-JsonProperty -Object $roleCatalog -Name $role)) {
                        Add-ValidationError "$context uses role '$role' absent from role_catalog."
                    }
                }
                $totalFactionRoleSlots += $roleSet.Count
                $bindings = Get-PropertyValue -Object $row -Name 'role_loadout_bindings'
                if (-not (Test-IsJsonObject -Value $bindings)) {
                    Add-ValidationError "$context role_loadout_bindings must be an object."
                    continue
                }
                $bindingProperties = @($bindings.PSObject.Properties)
                $totalFactionRoleBindings += $bindingProperties.Count
                if ($bindingProperties.Count -ne $roleSet.Count) {
                    Add-ValidationError "$context has $($roleSet.Count) roles but $($bindingProperties.Count) role_loadout_bindings."
                }
                foreach ($role in @($roleSet.Keys)) {
                    if (-not (Has-JsonProperty -Object $bindings -Name $role)) {
                        Add-ValidationError "$context lacks a loadout binding for role '$role'."
                    }
                }
                $cellArchetypes = @{}
                foreach ($bindingProperty in $bindingProperties) {
                    $roleKey = [string]$bindingProperty.Name
                    $binding = $bindingProperty.Value
                    if (-not $roleSet.ContainsKey($roleKey)) {
                        Add-ValidationError "$context has an extra loadout binding '$roleKey'."
                    }
                    if ([string](Get-PropertyValue -Object $binding -Name 'role_id') -cne $roleKey) {
                        Add-ValidationError "$context binding key '$roleKey' does not match its role_id."
                    }
                    $bindingProfile = [string](Get-PropertyValue -Object $binding -Name 'profile_ref')
                    if ($bindingProfile -cne $expectedProfile -or $bindingProfile -cne $rowProfile) {
                        Add-ValidationError "$context role '$roleKey' profile_ref must equal row profile '$expectedProfile'."
                    }
                    $archetypeRef = [string](Get-PropertyValue -Object $binding -Name 'archetype_ref')
                    if (-not $loadoutArchetypeById.ContainsKey($archetypeRef)) {
                        Add-ValidationError "$context role '$roleKey' has unresolved archetype_ref '$archetypeRef'."
                    }
                    else {
                        $archetypeBounds = Get-PropertyValue -Object $loadoutArchetypeById[$archetypeRef] -Name 'tech_epoch_bounds'
                        $archetypeMinimum = Get-EpochNumber (Get-PropertyValue -Object $archetypeBounds -Name 'minimum')
                        $archetypeMaximum = Get-EpochNumber (Get-PropertyValue -Object $archetypeBounds -Name 'maximum')
                        if ($null -eq $archetypeMinimum -or $null -eq $archetypeMaximum -or [int]$rowEpoch -lt [int]$archetypeMinimum -or [int]$rowEpoch -gt [int]$archetypeMaximum) {
                            Add-ValidationError "$context role '$roleKey' uses archetype '$archetypeRef' outside its epoch bounds."
                        }
                        $usedLoadoutArchetypes[$archetypeRef] = $true
                    }
                    if ($cellArchetypes.ContainsKey($archetypeRef)) {
                        Add-ValidationError "$context assigns archetype '$archetypeRef' to both '$($cellArchetypes[$archetypeRef])' and '$roleKey'; faction roles must remain mechanically distinct."
                    }
                    else { $cellArchetypes[$archetypeRef] = $roleKey }
                    if ($factionRoleArchetype.ContainsKey($roleKey) -and [string]$factionRoleArchetype[$roleKey] -cne $archetypeRef) {
                        Add-ValidationError "Faction '$factionKey' remaps role '$roleKey' from archetype '$($factionRoleArchetype[$roleKey])' to '$archetypeRef' at P$rowEpoch."
                    }
                    else { $factionRoleArchetype[$roleKey] = $archetypeRef }
                    foreach ($ceilingName in @('loot_ceiling', 'trade_ceiling')) {
                        $ceiling = Get-PropertyValue -Object $binding -Name $ceilingName
                        if (-not (Test-IsJsonObject -Value $ceiling)) {
                            Add-ValidationError "$context role '$roleKey' lacks $ceilingName."
                            continue
                        }
                        if ([string](Get-PropertyValue -Object $ceiling -Name 'max_epoch') -cne $rowEpochText) {
                            Add-ValidationError "$context role '$roleKey' $ceilingName.max_epoch must equal '$rowEpochText'."
                        }
                        $policy = Get-PropertyValue -Object $ceiling -Name 'policy'
                        if ($policy -isnot [string] -or [string]::IsNullOrWhiteSpace([string]$policy)) {
                            Add-ValidationError "$context role '$roleKey' $ceilingName.policy is empty."
                        }
                    }
                }
            }
            for ($epoch = 0; $epoch -le 9; $epoch++) {
                if (-not $seenFactionEpochs.ContainsKey($epoch)) {
                    Add-ValidationError "Faction '$factionKey' lacks epoch P$epoch."
                }
            }
        }
        $expectedFactionRowsFromEpochCoverage = $factionProperties.Count * 10
        if ($totalFactionRows -ne $expectedFactionRowsFromEpochCoverage) {
            Add-ValidationError "Faction matrix row coverage must equal factions times P0-P9: expected=$expectedFactionRowsFromEpochCoverage actual=$totalFactionRows."
        }
        Assert-ManifestCount -RegistryId 'industrial_frontier:m2_extended_domains' -CountName 'faction_epoch_rows' -ActualCount $totalFactionRows -Context 'Extended faction epoch rows'
        Assert-ManifestCount -RegistryId 'industrial_frontier:m2_extended_domains' -CountName 'role_slots' -ActualCount $totalFactionRoleSlots -Context 'Extended faction role slots'
        Assert-ManifestCount -RegistryId 'industrial_frontier:m2_extended_domains' -CountName 'role_bindings' -ActualCount $totalFactionRoleBindings -Context 'Extended faction role bindings'
        if ($totalFactionRoleBindings -ne $totalFactionRoleSlots) {
            Add-ValidationError "Extended faction matrix must contain one binding per role slot: roles=$totalFactionRoleSlots bindings=$totalFactionRoleBindings."
        }
        foreach ($archetypeId in @($loadoutArchetypeById.Keys)) {
            if (-not $usedLoadoutArchetypes.ContainsKey($archetypeId)) {
                Add-ValidationError "Loadout archetype '$archetypeId' is never used by a faction role binding."
            }
        }
    }

    # Construction, food and combat provide the manifest-counted consumer
    # contracts of the typed concept layer. Every consumer must have a non-empty physical or fallback
    # dependency, and every human-readable material/chemistry/category list has
    # a positionally aligned typed concept list.
    $consumerContracts = @()
    $construction = Get-PropertyValue -Object $extended -Name 'construction'
    $materialFamilies = @(Get-PropertyValue -Object $construction -Name 'material_families')
    Assert-ManifestCount -RegistryId 'industrial_frontier:m2_extended_domains' -CountName 'construction_material_families' -ActualCount $materialFamilies.Count -Context 'Construction material families'
    $materialFamilyById = @{}
    foreach ($family in $materialFamilies) {
        $familyId = [string](Get-PropertyValue -Object $family -Name 'family_id')
        $familyEpoch = Get-EpochNumber (Get-PropertyValue -Object $family -Name 'first_epoch')
        if ($materialFamilyById.ContainsKey($familyId)) {
            Add-ValidationError "Construction material family '$familyId' is duplicated."
        }
        else { $materialFamilyById[$familyId] = $family }
        $bulkAutomationEpoch = Get-EpochNumber (Get-PropertyValue -Object $family -Name 'bulk_automation_epoch')
        if ($null -eq $familyEpoch -or $null -eq $bulkAutomationEpoch -or [int]$bulkAutomationEpoch -lt [int]$familyEpoch) {
            Add-ValidationError "Construction material family '$familyId' has an invalid first/bulk-automation epoch contract."
        }
        $familyConceptRefs = Get-PropertyValue -Object $family -Name 'material_concept_refs'
        Test-PositionalConceptMapping -Claims $familyConceptRefs -ConceptRefs $familyConceptRefs -AllowedKinds @('MATERIAL') -Context "Construction material family '$familyId' typed materials" -ConsumerEpoch $null -ConceptById $conceptById
        $consumerContracts += [pscustomobject]@{ owner = $family; context = "Construction material family '$familyId'"; epoch = $familyEpoch; fallback_kinds = @('MATERIAL') }
    }

    $furnitureCategories = @(Get-PropertyValue -Object $construction -Name 'furniture_categories')
    Assert-ManifestCount -RegistryId 'industrial_frontier:m2_extended_domains' -CountName 'furniture_categories' -ActualCount $furnitureCategories.Count -Context 'Construction furniture categories'
    $epochPalettes = @(Get-PropertyValue -Object $construction -Name 'epoch_palettes')
    Assert-ManifestCount -RegistryId 'industrial_frontier:m2_extended_domains' -CountName 'epoch_palettes' -ActualCount $epochPalettes.Count -Context 'Construction epoch palettes'
    $seenPaletteEpochs = @{}
    foreach ($palette in $epochPalettes) {
        $paletteEpochText = [string](Get-PropertyValue -Object $palette -Name 'epoch')
        $paletteEpoch = Get-EpochNumber -Value $paletteEpochText
        $paletteContext = "Construction palette '$paletteEpochText'"
        if ($null -eq $paletteEpoch) {
            Add-ValidationError "$paletteContext has an invalid epoch."
        }
        elseif ($seenPaletteEpochs.ContainsKey([int]$paletteEpoch)) {
            Add-ValidationError "Construction palettes repeat P$paletteEpoch."
        }
        else { $seenPaletteEpochs[[int]$paletteEpoch] = $true }
        Test-PositionalConceptMapping -Claims (Get-PropertyValue -Object $palette -Name 'settlement_materials') -ConceptRefs (Get-PropertyValue -Object $palette -Name 'settlement_material_concept_refs') -AllowedKinds @('MATERIAL') -Context "$paletteContext settlement materials" -ConsumerEpoch $paletteEpoch -ConceptById $conceptById
        foreach ($familyRefValue in @(Get-PropertyValue -Object $palette -Name 'permitted_material_families')) {
            $familyRef = [string]$familyRefValue
            if (-not $materialFamilyById.ContainsKey($familyRef)) {
                Add-ValidationError "$paletteContext has unresolved permitted material family '$familyRef'."
                continue
            }
            $permittedFamilyEpoch = Get-EpochNumber (Get-PropertyValue -Object $materialFamilyById[$familyRef] -Name 'first_epoch')
            if ($null -ne $paletteEpoch -and $null -ne $permittedFamilyEpoch -and [int]$permittedFamilyEpoch -gt [int]$paletteEpoch) {
                Add-ValidationError "$paletteContext permits material family '$familyRef' before P$permittedFamilyEpoch."
            }
        }
    }
    for ($epoch = 0; $epoch -le 9; $epoch++) {
        if (-not $seenPaletteEpochs.ContainsKey($epoch)) {
            Add-ValidationError "Construction baseline lacks the P$epoch epoch palette."
        }
    }

    $food = Get-PropertyValue -Object $extended -Name 'food'
    $foodCollectionNames = @(
        'crop_passports',
        'ingredient_passports',
        'food_fluid_passports',
        'ration_passports',
        'container_passports',
        'refrigerant_passports',
        'bio_waste_passports'
    )
    $foodPassportCount = 0
    foreach ($collectionName in $foodCollectionNames) {
        $passports = @(Get-PropertyValue -Object $food -Name $collectionName)
        $foodPassportCount += $passports.Count
        Assert-ManifestCount -RegistryId 'industrial_frontier:m2_extended_domains' -CountName $collectionName -ActualCount $passports.Count -Context "Food collection '$collectionName'"
        foreach ($passport in $passports) {
            $passportId = [string](Get-PropertyValue -Object $passport -Name 'passport_id')
            $passportEpoch = Get-EpochNumber (Get-PropertyValue -Object $passport -Name 'first_epoch')
            $fallbackKinds = switch ($collectionName) {
                'crop_passports' { @('FOOD_CATEGORY', 'WASTE_CATEGORY') }
                'ingredient_passports' { @('FOOD_CATEGORY') }
                'food_fluid_passports' { @('FOOD_CATEGORY') }
                'ration_passports' { @('FOOD_CATEGORY') }
                'container_passports' { @('MATERIAL', 'FOOD_CATEGORY') }
                'refrigerant_passports' { @('CHEMISTRY') }
                'bio_waste_passports' { @('WASTE_CATEGORY') }
            }
            $consumerContracts += [pscustomobject]@{ owner = $passport; context = "Food passport '$passportId'"; epoch = $passportEpoch; fallback_kinds = $fallbackKinds }
            switch ($collectionName) {
                'crop_passports' {
                    Test-PositionalConceptMapping -Claims (Get-PropertyValue -Object $passport -Name 'outputs') -ConceptRefs (Get-PropertyValue -Object $passport -Name 'output_concept_refs') -AllowedKinds @('FOOD_CATEGORY', 'WASTE_CATEGORY') -Context "Food passport '$passportId' outputs" -ConsumerEpoch $null -ConceptById $conceptById
                }
                'ingredient_passports' {
                    Test-PositionalConceptMapping -Claims (Get-PropertyValue -Object $passport -Name 'source_classes') -ConceptRefs (Get-PropertyValue -Object $passport -Name 'source_concept_refs') -AllowedKinds @('FOOD_CATEGORY') -Context "Food passport '$passportId' sources" -ConsumerEpoch $null -ConceptById $conceptById
                }
                'food_fluid_passports' {
                    Test-PositionalConceptMapping -Claims (Get-PropertyValue -Object $passport -Name 'purity_classes') -ConceptRefs (Get-PropertyValue -Object $passport -Name 'purity_concept_refs') -AllowedKinds @('FOOD_CATEGORY') -Context "Food passport '$passportId' purity classes" -ConsumerEpoch $null -ConceptById $conceptById
                    Test-PositionalConceptMapping -Claims (Get-PropertyValue -Object $passport -Name 'container_classes') -ConceptRefs (Get-PropertyValue -Object $passport -Name 'container_class_concept_refs') -AllowedKinds @('FOOD_CATEGORY') -Context "Food passport '$passportId' container classes" -ConsumerEpoch $null -ConceptById $conceptById
                }
                'ration_passports' {
                    Test-PositionalConceptMapping -Claims (Get-PropertyValue -Object $passport -Name 'accepted_food_categories') -ConceptRefs (Get-PropertyValue -Object $passport -Name 'accepted_food_concept_refs') -AllowedKinds @('FOOD_CATEGORY') -Context "Food passport '$passportId' accepted foods" -ConsumerEpoch $null -ConceptById $conceptById
                    Test-PositionalConceptMapping -Claims (Get-PropertyValue -Object $passport -Name 'packaging_classes') -ConceptRefs (Get-PropertyValue -Object $passport -Name 'packaging_concept_refs') -AllowedKinds @('FOOD_CATEGORY') -Context "Food passport '$passportId' packaging" -ConsumerEpoch $null -ConceptById $conceptById
                }
                'container_passports' {
                    Test-PositionalConceptMapping -Claims (Get-PropertyValue -Object $passport -Name 'material_families') -ConceptRefs (Get-PropertyValue -Object $passport -Name 'material_concept_refs') -AllowedKinds @('MATERIAL') -Context "Food passport '$passportId' container materials" -ConsumerEpoch $null -ConceptById $conceptById
                    Test-PositionalConceptMapping -Claims (Get-PropertyValue -Object $passport -Name 'contents') -ConceptRefs (Get-PropertyValue -Object $passport -Name 'contents_concept_refs') -AllowedKinds @('FOOD_CATEGORY') -Context "Food passport '$passportId' contents" -ConsumerEpoch $null -ConceptById $conceptById
                }
                'refrigerant_passports' {
                    $refrigerantConceptRefs = Get-PropertyValue -Object $passport -Name 'category_concept_refs'
                    Test-PositionalConceptMapping -Claims $refrigerantConceptRefs -ConceptRefs $refrigerantConceptRefs -AllowedKinds @('CHEMISTRY') -Context "Food passport '$passportId' refrigerant category" -ConsumerEpoch $null -ConceptById $conceptById
                }
                'bio_waste_passports' {
                    Test-PositionalConceptMapping -Claims (Get-PropertyValue -Object $passport -Name 'sources') -ConceptRefs (Get-PropertyValue -Object $passport -Name 'source_concept_refs') -AllowedKinds @('WASTE_CATEGORY') -Context "Food passport '$passportId' waste sources" -ConsumerEpoch $null -ConceptById $conceptById
                    Test-PositionalConceptMapping -Claims (Get-PropertyValue -Object $passport -Name 'allowed_routes') -ConceptRefs (Get-PropertyValue -Object $passport -Name 'route_concept_refs') -AllowedKinds @('WASTE_CATEGORY') -Context "Food passport '$passportId' waste routes" -ConsumerEpoch $null -ConceptById $conceptById
                    Test-PositionalConceptMapping -Claims (Get-PropertyValue -Object $passport -Name 'products') -ConceptRefs (Get-PropertyValue -Object $passport -Name 'product_concept_refs') -AllowedKinds @('WASTE_CATEGORY') -Context "Food passport '$passportId' waste products" -ConsumerEpoch $null -ConceptById $conceptById
                }
            }
        }
    }

    $combat = Get-PropertyValue -Object $extended -Name 'combat'
    $combatProfiles = @(Get-PropertyValue -Object $combat -Name 'epoch_profiles')
    Assert-ManifestCount -RegistryId 'industrial_frontier:m2_extended_domains' -CountName 'combat_profiles' -ActualCount $combatProfiles.Count -Context 'Combat epoch profiles'
    $combatConceptKindByCategory = @{
        weapon = 'WEAPON_CLASS'
        armor = 'ARMOR_CLASS'
        artillery = 'ARTILLERY_CLASS'
        ammunition = 'AMMUNITION_CLASS'
    }
    $seenCombatEpochs = @{}
    $combatPassportCount = 0
    foreach ($epochProfile in $combatProfiles) {
        $combatEpochText = [string](Get-PropertyValue -Object $epochProfile -Name 'epoch')
        $combatEpoch = Get-EpochNumber -Value $combatEpochText
        if ($null -eq $combatEpoch) {
            Add-ValidationError "Combat profile '$combatEpochText' has an invalid epoch."
        }
        elseif ($seenCombatEpochs.ContainsKey([int]$combatEpoch)) {
            Add-ValidationError "Combat baseline repeats profile P$combatEpoch."
        }
        else { $seenCombatEpochs[[int]$combatEpoch] = $true }
        foreach ($categoryName in @('weapon', 'armor', 'artillery', 'ammunition')) {
            $category = Get-PropertyValue -Object $epochProfile -Name $categoryName
            $combatPassportCount++
            $categoryKind = [string]$combatConceptKindByCategory[$categoryName]
            $consumerContracts += [pscustomobject]@{ owner = $category; context = "Combat $combatEpochText $categoryName"; epoch = $combatEpoch; fallback_kinds = @($categoryKind) }
            Test-PositionalConceptMapping -Claims (Get-PropertyValue -Object $category -Name 'classes') -ConceptRefs (Get-PropertyValue -Object $category -Name 'class_concept_refs') -AllowedKinds @($categoryKind) -Context "Combat $combatEpochText $categoryName classes" -ConsumerEpoch $combatEpoch -ConceptById $conceptById
            Test-PositionalConceptMapping -Claims (Get-PropertyValue -Object $category -Name 'materials') -ConceptRefs (Get-PropertyValue -Object $category -Name 'material_concept_refs') -AllowedKinds @('MATERIAL') -Context "Combat $combatEpochText $categoryName materials" -ConsumerEpoch $combatEpoch -ConceptById $conceptById
            Test-PositionalConceptMapping -Claims (Get-PropertyValue -Object $category -Name 'chemistry') -ConceptRefs (Get-PropertyValue -Object $category -Name 'chemistry_concept_refs') -AllowedKinds @('CHEMISTRY') -Context "Combat $combatEpochText $categoryName chemistry" -ConsumerEpoch $combatEpoch -ConceptById $conceptById
        }
    }
    Assert-ManifestCount -RegistryId 'industrial_frontier:m2_extended_domains' -CountName 'combat_passports' -ActualCount $combatPassportCount -Context 'Combat category passports'
    for ($epoch = 0; $epoch -le 9; $epoch++) {
        if (-not $seenCombatEpochs.ContainsKey($epoch)) {
            Add-ValidationError "Combat baseline lacks the P$epoch profile."
        }
    }

    $consumerDependencyObjects = 0
    $consumerSubstanceRefs = 0
    $consumerFormRefs = 0
    $consumerProcessRefs = 0
    $consumerFallbackRefs = 0
    $emptyConsumerDependencies = 0
    foreach ($contract in $consumerContracts) {
        Test-CoreDependencyRefsObject -Owner $contract.owner -Context ([string]$contract.context) -ConsumerEpoch $contract.epoch -AvailabilityById $coreAvailabilityById -ConceptById $conceptById
        $consumerDependencyObjects++
        $coreRefs = Get-PropertyValue -Object $contract.owner -Name 'core_dependency_refs'
        $substanceRefCount = @(Get-PropertyValue -Object $coreRefs -Name 'substance_refs').Count
        $formRefCount = @(Get-PropertyValue -Object $coreRefs -Name 'form_refs').Count
        $processRefCount = @(Get-PropertyValue -Object $coreRefs -Name 'process_refs').Count
        $fallbackRefs = @(Get-PropertyValue -Object $coreRefs -Name 'fallback_concept_refs')
        $consumerSubstanceRefs += $substanceRefCount
        $consumerFormRefs += $formRefCount
        $consumerProcessRefs += $processRefCount
        $consumerFallbackRefs += $fallbackRefs.Count
        if (($substanceRefCount + $formRefCount + $processRefCount + $fallbackRefs.Count) -eq 0) {
            $emptyConsumerDependencies++
        }
        Test-PositionalConceptMapping -Claims $fallbackRefs -ConceptRefs $fallbackRefs -AllowedKinds @($contract.fallback_kinds) -Context "$($contract.context) fallback dependency" -ConsumerEpoch $contract.epoch -ConceptById $conceptById
    }
    $expectedConsumerDependencyObjects = $materialFamilies.Count + $foodPassportCount + $combatPassportCount
    if ($consumerDependencyObjects -ne $expectedConsumerDependencyObjects) {
        Add-ValidationError "Consumer dependency coverage mismatch: expected one contract for each material family, food passport and combat passport ($expectedConsumerDependencyObjects), found $consumerDependencyObjects."
    }
    Assert-ManifestCount -RegistryId 'industrial_frontier:m2_extended_domains' -CountName 'consumer_dependency_objects' -ActualCount $consumerDependencyObjects -Context 'Extended consumer dependency objects'
    Assert-ManifestCount -RegistryId 'industrial_frontier:m2_extended_domains' -CountName 'consumer_substance_refs' -ActualCount $consumerSubstanceRefs -Context 'Extended consumer substance refs'
    Assert-ManifestCount -RegistryId 'industrial_frontier:m2_extended_domains' -CountName 'consumer_form_refs' -ActualCount $consumerFormRefs -Context 'Extended consumer form refs'
    Assert-ManifestCount -RegistryId 'industrial_frontier:m2_extended_domains' -CountName 'consumer_process_refs' -ActualCount $consumerProcessRefs -Context 'Extended consumer process refs'
    Assert-ManifestCount -RegistryId 'industrial_frontier:m2_extended_domains' -CountName 'consumer_fallback_refs' -ActualCount $consumerFallbackRefs -Context 'Extended consumer fallback refs'
    if ($emptyConsumerDependencies -ne 0) {
        Add-ValidationError "Extended baseline contains $emptyConsumerDependencies empty consumer dependency contracts."
    }

    $prohibitedLeaks = @(Get-PropertyValue -Object $extended -Name 'prohibited_leaks')
    Assert-ManifestCount -RegistryId 'industrial_frontier:m2_extended_domains' -CountName 'prohibited_leaks' -ActualCount $prohibitedLeaks.Count -Context 'Extended prohibited leaks'
    $releaseGates = @(Get-PropertyValue -Object $extended -Name 'release_gates')
    Assert-ManifestCount -RegistryId 'industrial_frontier:m2_extended_domains' -CountName 'release_gates' -ActualCount $releaseGates.Count -Context 'Extended release gates'
}

# The grind registry uses local design-file evidence rather than the core
# evidence-ID namespace. Enforce its hard ceilings and the rule that automation
# exists no later than mass demand.
$grindInfo = $documentsByRegistryId['industrial_frontier:m2/grind_budget']
if ($null -ne $grindInfo) {
    $grind = $grindInfo.document
    $limits = Get-PropertyValue -Object $grind -Name 'limits'
    $chains = @(Get-PropertyValue -Object $grind -Name 'chains')
    if ($null -eq $limits -or $chains.Count -eq 0) {
        Add-ValidationError 'Grind budget registry must declare limits and at least one chain.'
    }
    else {
        Assert-ManifestCount -RegistryId 'industrial_frontier:m2/grind_budget' -CountName 'chains' -ActualCount $chains.Count -Context 'Grind-budget chains'
        $seenGrindIds = @{}
        $epochsCovered = @{}
        $limitNames = @(
            'training_batches_max', 'manual_repeats_green_max', 'manual_repeats_hard_max',
            'transfers_green_max', 'transfers_hard_max', 'passive_minutes_green_max',
            'passive_minutes_hard_max'
        )
        foreach ($limitName in $limitNames) {
            $limitValue = Get-PropertyValue -Object $limits -Name $limitName
            if ($null -eq $limitValue -or [int]$limitValue -lt 0) {
                Add-ValidationError "Grind budget has invalid limit '$limitName'."
            }
        }
        if ([int](Get-PropertyValue -Object $limits -Name 'manual_repeats_green_max') -gt [int](Get-PropertyValue -Object $limits -Name 'manual_repeats_hard_max')) {
            Add-ValidationError 'Grind manual green limit exceeds the hard limit.'
        }
        if ([int](Get-PropertyValue -Object $limits -Name 'transfers_green_max') -gt [int](Get-PropertyValue -Object $limits -Name 'transfers_hard_max')) {
            Add-ValidationError 'Grind transfer green limit exceeds the hard limit.'
        }
        if ([int](Get-PropertyValue -Object $limits -Name 'passive_minutes_green_max') -gt [int](Get-PropertyValue -Object $limits -Name 'passive_minutes_hard_max')) {
            Add-ValidationError 'Grind passive-time green limit exceeds the hard limit.'
        }

        foreach ($chain in $chains) {
            $chainId = [string](Get-PropertyValue -Object $chain -Name 'chain_id')
            $epoch = [int](Get-PropertyValue -Object $chain -Name 'epoch')
            if ($chainId -notmatch '^industrial_frontier:grind/[a-z0-9_./-]+$') {
                Add-ValidationError "Invalid grind chain ID '$chainId'."
            }
            elseif ($seenGrindIds.ContainsKey($chainId)) {
                Add-ValidationError "Duplicate grind chain ID '$chainId'."
            }
            else {
                $seenGrindIds[$chainId] = $true
            }
            if ($epoch -lt 0 -or $epoch -gt 9) {
                Add-ValidationError "Grind chain '$chainId' has epoch outside P0-P9."
            }
            else {
                $epochsCovered[$epoch] = $true
                if ($chainId -notmatch "^industrial_frontier:grind/p$epoch/") {
                    Add-ValidationError "Grind chain '$chainId' does not match its P$epoch epoch path."
                }
            }
            foreach ($justificationField in @('title_ru', 'goal_ru', 'deterministic_alternative_ru', 'decision_ru')) {
                $justification = Get-PropertyValue -Object $chain -Name $justificationField
                if ($justification -isnot [string] -or [string]::IsNullOrWhiteSpace([string]$justification)) {
                    Add-ValidationError "Grind chain '$chainId' lacks '$justificationField'."
                }
            }
            foreach ($metric in @('training_batches', 'repeated_manual_operations', 'manual_transfers', 'active_minutes', 'passive_minutes')) {
                $metricValue = Get-PropertyValue -Object $chain -Name $metric
                if ($null -eq $metricValue -or [int]$metricValue -lt 0) {
                    Add-ValidationError "Grind chain '$chainId' has invalid metric '$metric'."
                }
            }
            if ([int](Get-PropertyValue -Object $chain -Name 'training_batches') -gt [int](Get-PropertyValue -Object $limits -Name 'training_batches_max')) {
                Add-ValidationError "Grind chain '$chainId' exceeds the training-batch hard limit."
            }
            if ([int](Get-PropertyValue -Object $chain -Name 'repeated_manual_operations') -gt [int](Get-PropertyValue -Object $limits -Name 'manual_repeats_hard_max')) {
                Add-ValidationError "Grind chain '$chainId' exceeds the repeated-operation hard limit."
            }
            if ([int](Get-PropertyValue -Object $chain -Name 'manual_transfers') -gt [int](Get-PropertyValue -Object $limits -Name 'transfers_hard_max')) {
                Add-ValidationError "Grind chain '$chainId' exceeds the manual-transfer hard limit."
            }
            if ([int](Get-PropertyValue -Object $chain -Name 'passive_minutes') -gt [int](Get-PropertyValue -Object $limits -Name 'passive_minutes_hard_max')) {
                Add-ValidationError "Grind chain '$chainId' exceeds the passive-time hard limit."
            }
            if ([string](Get-PropertyValue -Object $chain -Name 'result') -eq 'GREEN') {
                if ([int](Get-PropertyValue -Object $chain -Name 'repeated_manual_operations') -gt [int](Get-PropertyValue -Object $limits -Name 'manual_repeats_green_max') -or
                    [int](Get-PropertyValue -Object $chain -Name 'manual_transfers') -gt [int](Get-PropertyValue -Object $limits -Name 'transfers_green_max') -or
                    [int](Get-PropertyValue -Object $chain -Name 'passive_minutes') -gt [int](Get-PropertyValue -Object $limits -Name 'passive_minutes_green_max')) {
                    Add-ValidationError "Grind chain '$chainId' is marked GREEN but exceeds a green limit."
                }
            }
            if ([int](Get-PropertyValue -Object $chain -Name 'rng_percent') -ne 100) {
                Add-ValidationError "Mandatory grind chain '$chainId' lacks a deterministic 100% route."
            }
            if ([int](Get-PropertyValue -Object $chain -Name 'automation_epoch') -gt [int](Get-PropertyValue -Object $chain -Name 'mass_demand_epoch')) {
                Add-ValidationError "Grind chain '$chainId' demands mass output before automation."
            }
            if ((Get-PropertyValue -Object $chain -Name 'returned_tools_or_catalysts') -ne $true) {
                Add-ValidationError "Grind chain '$chainId' does not return tools/catalysts."
            }
            $gate = Get-PropertyValue -Object $chain -Name 'gate'
            if ($gate -isnot [string] -or [string]::IsNullOrWhiteSpace([string]$gate)) {
                Add-ValidationError "Grind chain '$chainId' has no explicit gate."
            }
            $chainEvidence = @(Get-PropertyValue -Object $chain -Name 'evidence_refs')
            if ($chainEvidence.Count -eq 0) {
                Add-ValidationError "Grind chain '$chainId' has no evidence."
            }
            foreach ($evidenceReference in $chainEvidence) {
                if ($evidenceReference -isnot [string] -or [string]::IsNullOrWhiteSpace([string]$evidenceReference)) {
                    Add-ValidationError "Grind chain '$chainId' has an invalid evidence reference."
                    continue
                }
                $evidenceRelativePath = (([string]$evidenceReference) -split '#', 2)[0]
                $evidenceFullPath = Resolve-RootRelativePath -RelativePath $evidenceRelativePath -Context "grind chain '$chainId'"
                if ($null -eq $evidenceFullPath -or -not (Test-Path -LiteralPath $evidenceFullPath)) {
                    Add-ValidationError "Grind chain '$chainId' references missing evidence '$evidenceReference'."
                }
            }
        }
        for ($epoch = 0; $epoch -le 9; $epoch++) {
            if (-not $epochsCovered.ContainsKey($epoch)) {
                Add-ValidationError "Grind budget has no audited chain for P$epoch."
            }
        }

        if ($null -eq $progression) {
            Add-ValidationError 'Cannot audit grind-chain completeness: progression graph is missing.'
        }
        else {
            $grindById = @{}
            foreach ($chain in $chains) {
                $grindById[[string](Get-PropertyValue -Object $chain -Name 'chain_id')] = $chain
            }
            $graphGrindRefs = @{}
            foreach ($node in @(Get-PropertyValue -Object $progression -Name 'nodes')) {
                $nodeEpoch = [int](Get-PropertyValue -Object $node -Name 'epoch')
                foreach ($chainRef in @(Get-PropertyValue -Object $node -Name 'grind_chain_refs')) {
                    $chainRef = [string]$chainRef
                    $graphGrindRefs[$chainRef] = $true
                    if ($grindById.ContainsKey($chainRef)) {
                        $chainEpoch = [int](Get-PropertyValue -Object $grindById[$chainRef] -Name 'epoch')
                        if ($chainEpoch -ne $nodeEpoch) {
                            Add-ValidationError "Progression P$nodeEpoch references grind chain '$chainRef' assigned to P$chainEpoch."
                        }
                    }
                }
            }
            foreach ($chain in $chains) {
                $chainId = [string](Get-PropertyValue -Object $chain -Name 'chain_id')
                if (-not $graphGrindRefs.ContainsKey($chainId)) {
                    Add-ValidationError "Grind chain '$chainId' is not covered by any progression node."
                }
            }
        }

        # Critical components are the bridge between the typed production DAG,
        # the P0-P9 nodes and anti-grind policy. Require a one-to-one grind card,
        # exact COMPONENT_REQUIRES coverage, a bootstrap route and automation no
        # later than mass demand.
        $criticalComponents = @(Get-PropertyValue -Object $grind -Name 'critical_components')
        Assert-ManifestCount -RegistryId 'industrial_frontier:m2/grind_budget' -CountName 'critical_components' -ActualCount $criticalComponents.Count -Context 'Grind-budget critical components'
        if ($criticalComponents.Count -ne $chains.Count) {
            Add-ValidationError "Critical-component/grind-card parity requires equal collection sizes: components=$($criticalComponents.Count) chains=$($chains.Count)."
        }
        $criticalComponentById = @{}
        foreach ($component in $criticalComponents) {
            $componentId = [string](Get-PropertyValue -Object $component -Name 'component_id')
            if ($criticalComponentById.ContainsKey($componentId)) {
                Add-ValidationError "Duplicate critical component '$componentId'."
            }
            else { $criticalComponentById[$componentId] = $component }
        }
        $chainByIdForComponents = @{}
        $componentChainOccurrences = @{}
        foreach ($chain in $chains) {
            $chainId = [string](Get-PropertyValue -Object $chain -Name 'chain_id')
            $chainByIdForComponents[$chainId] = $chain
            $chainComponentRefs = @(Get-PropertyValue -Object $chain -Name 'critical_component_refs')
            if ($chainComponentRefs.Count -ne 1) {
                Add-ValidationError "Grind chain '$chainId' must budget exactly one critical component; found $($chainComponentRefs.Count)."
            }
            foreach ($componentRefValue in $chainComponentRefs) {
                $componentRef = [string]$componentRefValue
                if (-not $componentChainOccurrences.ContainsKey($componentRef)) { $componentChainOccurrences[$componentRef] = 0 }
                $componentChainOccurrences[$componentRef] = [int]$componentChainOccurrences[$componentRef] + 1
                if (-not $criticalComponentById.ContainsKey($componentRef)) {
                    Add-ValidationError "Grind chain '$chainId' references undeclared critical component '$componentRef'."
                }
            }
        }

        $componentRequirementEdges = if ($null -eq $progression) { @() } else {
            @((Get-PropertyValue -Object $progression -Name 'dependency_edges') | Where-Object {
                [string](Get-PropertyValue -Object $_ -Name 'relation') -eq 'COMPONENT_REQUIRES'
            })
        }
        Assert-ManifestCount -RegistryId 'industrial_frontier:m2/progression_graph' -CountName 'component_requirement_edges' -ActualCount $componentRequirementEdges.Count -Context 'Progression COMPONENT_REQUIRES edges'
        $declaredComponentRequirementCount = 0
        foreach ($criticalComponentForCount in $criticalComponents) {
            $declaredComponentRequirementCount += @(Get-PropertyValue -Object $criticalComponentForCount -Name 'required_refs').Count
        }
        if ($componentRequirementEdges.Count -ne $declaredComponentRequirementCount) {
            Add-ValidationError "COMPONENT_REQUIRES edge parity must equal all critical-component required_refs: edges=$($componentRequirementEdges.Count) required_refs=$declaredComponentRequirementCount."
        }
        $componentRequirementPairs = @{}
        foreach ($requirementEdge in $componentRequirementEdges) {
            $requirementSource = [string](Get-PropertyValue -Object $requirementEdge -Name 'from_ref')
            $requirementTarget = [string](Get-PropertyValue -Object $requirementEdge -Name 'to_ref')
            $requirementPair = "$requirementSource->$requirementTarget"
            if (-not $componentRequirementPairs.ContainsKey($requirementPair)) { $componentRequirementPairs[$requirementPair] = 0 }
            $componentRequirementPairs[$requirementPair] = [int]$componentRequirementPairs[$requirementPair] + 1
        }

        $graphComponentOccurrences = @{}
        if ($null -ne $progression) {
            foreach ($node in @(Get-PropertyValue -Object $progression -Name 'nodes')) {
                $nodeEpoch = [int](Get-PropertyValue -Object $node -Name 'epoch')
                foreach ($componentRefValue in @(Get-PropertyValue -Object $node -Name 'critical_component_refs')) {
                    $componentRef = [string]$componentRefValue
                    if (-not $graphComponentOccurrences.ContainsKey($componentRef)) {
                        $graphComponentOccurrences[$componentRef] = [pscustomobject]@{ count = 0; epochs = @() }
                    }
                    $occurrence = $graphComponentOccurrences[$componentRef]
                    $occurrence.count = [int]$occurrence.count + 1
                    $occurrence.epochs = @($occurrence.epochs) + @($nodeEpoch)
                }
            }
        }

        foreach ($component in $criticalComponents) {
            $componentId = [string](Get-PropertyValue -Object $component -Name 'component_id')
            $componentEpoch = [int](Get-PropertyValue -Object $component -Name 'epoch')
            $componentAutomationEpoch = Get-PropertyValue -Object $component -Name 'automation_epoch'
            $componentMassDemandEpoch = Get-PropertyValue -Object $component -Name 'mass_demand_epoch'
            $budgetRef = [string](Get-PropertyValue -Object $component -Name 'budget_ref')
            if ($componentId -notmatch "^industrial_frontier:component/p$componentEpoch/[a-z0-9_./-]+$") {
                Add-ValidationError "Critical component '$componentId' does not match its P$componentEpoch epoch path."
            }
            if ((Get-PropertyValue -Object $component -Name 'mandatory') -ne $true) {
                Add-ValidationError "Critical component '$componentId' must be mandatory."
            }
            foreach ($routeField in @('bootstrap_route_ru', 'automation_route_ru')) {
                $routeText = Get-PropertyValue -Object $component -Name $routeField
                if ($routeText -isnot [string] -or [string]::IsNullOrWhiteSpace([string]$routeText)) {
                    Add-ValidationError "Critical component '$componentId' lacks '$routeField'."
                }
            }
            if ($null -eq $componentAutomationEpoch -or $null -eq $componentMassDemandEpoch) {
                Add-ValidationError "Critical component '$componentId' must declare concrete automation_epoch and mass_demand_epoch budgets."
            }
            elseif ([int]$componentAutomationEpoch -gt [int]$componentMassDemandEpoch) {
                Add-ValidationError "Critical component '$componentId' reaches mass demand before automation."
            }

            $requiredRefs = @(Get-PropertyValue -Object $component -Name 'required_refs')
            if ($requiredRefs.Count -eq 0) {
                Add-ValidationError "Critical component '$componentId' has no typed production requirements."
            }
            foreach ($requiredRefValue in $requiredRefs) {
                $requiredRef = [string]$requiredRefValue
                if (-not $idKinds.ContainsKey($requiredRef) -or @('substance_id', 'process_id', 'network_id') -cnotcontains [string]$idKinds[$requiredRef]) {
                    $requiredKind = if ($idKinds.ContainsKey($requiredRef)) { [string]$idKinds[$requiredRef] } else { 'unresolved' }
                    Add-ValidationError "Critical component '$componentId' required_ref '$requiredRef' is $requiredKind, expected substance/process/network."
                }
                $pair = "$requiredRef->$componentId"
                if (-not $componentRequirementPairs.ContainsKey($pair) -or [int]$componentRequirementPairs[$pair] -ne 1) {
                    $pairCount = if ($componentRequirementPairs.ContainsKey($pair)) { [int]$componentRequirementPairs[$pair] } else { 0 }
                    Add-ValidationError "Critical component requirement '$pair' must occur exactly once; found $pairCount."
                }
            }

            if (-not $chainByIdForComponents.ContainsKey($budgetRef)) {
                Add-ValidationError "Critical component '$componentId' budget_ref '$budgetRef' does not resolve to a grind chain."
            }
            else {
                $budgetChain = $chainByIdForComponents[$budgetRef]
                $budgetComponentRefs = @(Get-PropertyValue -Object $budgetChain -Name 'critical_component_refs')
                if ($budgetComponentRefs.Count -ne 1 -or $budgetComponentRefs -cnotcontains $componentId) {
                    Add-ValidationError "Critical component '$componentId' budget '$budgetRef' is not a one-to-one grind card."
                }
                if ([int](Get-PropertyValue -Object $budgetChain -Name 'epoch') -ne $componentEpoch) {
                    Add-ValidationError "Critical component '$componentId' P$componentEpoch uses grind card '$budgetRef' from another epoch."
                }
                if ($null -ne $componentAutomationEpoch -and [int](Get-PropertyValue -Object $budgetChain -Name 'automation_epoch') -ne [int]$componentAutomationEpoch) {
                    Add-ValidationError "Critical component '$componentId' automation_epoch disagrees with grind card '$budgetRef'."
                }
                if ($null -ne $componentMassDemandEpoch -and [int](Get-PropertyValue -Object $budgetChain -Name 'mass_demand_epoch') -ne [int]$componentMassDemandEpoch) {
                    Add-ValidationError "Critical component '$componentId' mass_demand_epoch disagrees with grind card '$budgetRef'."
                }
            }
            if (-not $componentChainOccurrences.ContainsKey($componentId) -or [int]$componentChainOccurrences[$componentId] -ne 1) {
                $chainCount = if ($componentChainOccurrences.ContainsKey($componentId)) { [int]$componentChainOccurrences[$componentId] } else { 0 }
                Add-ValidationError "Critical component '$componentId' must occur on exactly one grind card; found $chainCount."
            }
            if (-not $graphComponentOccurrences.ContainsKey($componentId) -or [int]$graphComponentOccurrences[$componentId].count -ne 1) {
                $nodeCount = if ($graphComponentOccurrences.ContainsKey($componentId)) { [int]$graphComponentOccurrences[$componentId].count } else { 0 }
                Add-ValidationError "Critical component '$componentId' must occur in exactly one progression node; found $nodeCount."
            }
            elseif (@($graphComponentOccurrences[$componentId].epochs) -cnotcontains $componentEpoch) {
                Add-ValidationError "Critical component '$componentId' is assigned to a progression node other than P$componentEpoch."
            }
        }
        foreach ($requirementEdge in $componentRequirementEdges) {
            $requirementSource = [string](Get-PropertyValue -Object $requirementEdge -Name 'from_ref')
            $requirementTarget = [string](Get-PropertyValue -Object $requirementEdge -Name 'to_ref')
            if (-not $criticalComponentById.ContainsKey($requirementTarget)) { continue }
            if (@(Get-PropertyValue -Object $criticalComponentById[$requirementTarget] -Name 'required_refs') -cnotcontains $requirementSource) {
                Add-ValidationError "COMPONENT_REQUIRES edge '$requirementSource->$requirementTarget' is absent from the component required_refs contract."
            }
        }
    }
}

Write-Output 'M2 architecture validation'
foreach ($message in $errors) { Write-Output "ERROR: $message" }
foreach ($message in $warnings) { Write-Output "WARNING: $message" }
Write-Output "Schema definitions audited: $schemaKeywordAuditCount"
Write-Output "Schema applications: $schemaValidationCount"
Write-Output "Errors: $($errors.Count)"
Write-Output "Warnings: $($warnings.Count)"
Write-Output 'Minecraft was not launched'

if ($errors.Count -gt 0) { exit 2 }
exit 0
