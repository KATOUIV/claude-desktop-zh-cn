# Local compatibility layer for third-party Code mode. No app or user data is executed.
function Convert-CodeLocalePreference {
    param([Parameter(Mandatory = $true)][string]$Text)
    $state = 'isLoaded:!1,localeOverride:null,localeChoice:null,localePickCount:0'
    $setter = 'setLocaleOverride:t=>{let n=t===null?null:nu(t);'
    $fixedState = 'isLoaded:!1,localeOverride:"zh-CN",localeChoice:"zh-CN",localePickCount:0'
    $fixedSetter = 'setLocaleOverride:t=>{let n=t===null?"zh-CN":nu(t==="en-US"?"zh-CN":t);'
    $stateCount = [regex]::Matches($Text, [regex]::Escape($state)).Count
    $setterCount = [regex]::Matches($Text, [regex]::Escape($setter)).Count
    $fixedStateCount = [regex]::Matches($Text, [regex]::Escape($fixedState)).Count
    $fixedSetterCount = [regex]::Matches($Text, [regex]::Escape($fixedSetter)).Count
    if ($stateCount -eq 0 -and $setterCount -eq 0 -and $fixedStateCount -eq 1 -and $fixedSetterCount -eq 1) { return $Text }
    if ($stateCount -ne 1 -or $setterCount -ne 1 -or $fixedStateCount -ne 0 -or $fixedSetterCount -ne 0) {
        throw 'Unsupported Code locale layout: review the new bundle before patching.'
    }
    return $Text.Replace($state, $fixedState).Replace($setter, $fixedSetter)
}

function Set-CodeLocalePreference {
    param([string]$FrontendPath, [string]$LanguageCode)
    if ($LanguageCode -ne 'zh-CN') { return }
    $candidates = @(Get-ChildItem -LiteralPath (Join-Path $FrontendPath 'assets/v1') -Filter 'shared-*.js' -File | Where-Object {
        $body = [IO.File]::ReadAllText($_.FullName)
        $body.Contains('spa:locale') -and $body.Contains('setLocaleOverride:t=>')
    })
    if ($candidates.Count -ne 1) { throw 'Expected exactly one Code locale module; review this Claude version.' }
    $file = $candidates[0].FullName
    $before = [IO.File]::ReadAllText($file)
    $after = Convert-CodeLocalePreference $before
    if ($before -cne $after) { [IO.File]::WriteAllText($file, $after, [Text.UTF8Encoding]::new($false)) }
    Write-Host '  Code locale preference: zh-CN (host English fallback mapped to Chinese)'
}
