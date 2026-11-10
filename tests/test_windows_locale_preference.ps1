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
