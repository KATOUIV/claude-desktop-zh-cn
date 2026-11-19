$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '../scripts/windows_locale_preference.ps1')

$source = 'var state={isLoaded:!1,localeOverride:null,localeChoice:null,localePickCount:0,setLocaleOverride:t=>{let n=t===null?null:nu(t);return n}};'
$fixed = Convert-CodeLocalePreference $source
if (-not $fixed.Contains('localeOverride:"zh-CN",localeChoice:"zh-CN"')) { throw 'Chinese initial locale missing' }
if ((Convert-CodeLocalePreference $fixed) -cne $fixed) { throw 'Second application changed the patch' }
foreach ($bad in @('new-unknown-layout', ($source + $source), $source.Replace('setLocaleOverride:', 'renamed:'))) {
    $rejected = $false
    try { Convert-CodeLocalePreference $bad | Out-Null } catch { $rejected = $true }
    if (-not $rejected) { throw 'An unsupported or ambiguous module was accepted' }
}

# Execute the transformed setter with a benign identity normalizer to verify fallback semantics.
$testFile = Join-Path ([IO.Path]::GetTempPath()) ('claude-locale-test-' + [guid]::NewGuid().ToString('N') + '.cjs')
try {
    $js = 'const assert=require("node:assert/strict");const nu=x=>x;' + $fixed + 'assert.equal(state.setLocaleOverride("en-US"),"zh-CN");assert.equal(state.setLocaleOverride(null),"zh-CN");assert.equal(state.setLocaleOverride("ja-JP"),"ja-JP");'
    [IO.File]::WriteAllText($testFile, $js, [Text.UTF8Encoding]::new($false))
    & node $testFile
    if ($LASTEXITCODE -ne 0) { throw 'Locale fallback behavior failed' }
} finally { Remove-Item -LiteralPath $testFile -ErrorAction SilentlyContinue }
Write-Host 'PASS: initial locale, fallback behavior, idempotence and unsupported-layout rejection'

# Newer bundles rename the locale normalizer while retaining the same state/setter shape.
$newSource = $source.Replace('nu(t)', 'ss(t)')
$newFixed = Convert-CodeLocalePreference $newSource
if ((Convert-CodeLocalePreference $newFixed) -cne $newFixed) { throw 'Renamed normalizer patch is not idempotent' }
$testFile = Join-Path ([IO.Path]::GetTempPath()) ('claude-locale-test-' + [guid]::NewGuid().ToString('N') + '.cjs')
try {
    $js = 'const assert=require("node:assert/strict");const ss=x=>x;' + $newFixed + 'assert.equal(state.localeChoice,"zh-CN");assert.equal(state.setLocaleOverride("en-US"),"zh-CN");assert.equal(state.setLocaleOverride(null),"zh-CN");assert.equal(state.setLocaleOverride("ja-JP"),"ja-JP");'
    [IO.File]::WriteAllText($testFile, $js, [Text.UTF8Encoding]::new($false))
    & node $testFile
    if ($LASTEXITCODE -ne 0) { throw 'Renamed locale normalizer behavior failed' }
} finally { Remove-Item -LiteralPath $testFile -ErrorAction SilentlyContinue }
$rejected = $false
try { Convert-CodeLocalePreference ($source.Replace('nu(t)', 'unknown(t)')) | Out-Null } catch { $rejected = $true }
if (-not $rejected) { throw 'Unreviewed locale normalizer was accepted' }
Write-Host 'PASS: reviewed normalizer rename preserves locale semantics and rejects unknown layouts'
