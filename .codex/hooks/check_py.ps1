# PostToolUse hook for Write|Edit. Runs ruff on the edited .py file and
# pytest on the suite. Silent on success; prints findings on failure.
$ErrorActionPreference = 'Continue'

try {
    $stdin = [Console]::In.ReadToEnd()
    if (-not $stdin) { exit 0 }
    $j = $stdin | ConvertFrom-Json
} catch {
    exit 0
}

$f = $null
if ($j.tool_input -and $j.tool_input.file_path) { $f = $j.tool_input.file_path }
elseif ($j.tool_response -and $j.tool_response.filePath) { $f = $j.tool_response.filePath }

if (-not $f) { exit 0 }
if ($f -notlike '*.py') { exit 0 }
if ($f -like '*\data\*' -or $f -like '*/data/*') { exit 0 }

Set-Location 'C:\Users\brand\Documents\PhilosophersQuest'

$problems = New-Object System.Collections.ArrayList

# ruff on the edited file
$ruffOut = & ruff check $f 2>&1
if ($LASTEXITCODE -ne 0) {
    [void]$problems.Add("ruff:`n" + (($ruffOut | Out-String).Trim()))
}

# pytest full suite (fast: ~0.1s)
$pytestOut = & pytest tests/ -q --no-header --tb=line 2>&1
if ($LASTEXITCODE -ne 0) {
    $tail = $pytestOut | Select-Object -Last 12
    [void]$problems.Add("pytest:`n" + (($tail | Out-String).Trim()))
}

if ($problems.Count -gt 0) {
    Write-Output ($problems -join "`n---`n")
}
exit 0
