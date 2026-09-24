# test_lock.ps1 - acceptance harness for the iteration_loop.ps1 lock block.
# Standard under test: group single-instance lock standard D-20260925-03
# (2026-09-25 decision round; this loop + BigStream OSLoop = the two 48h
# pilot adopters; paradigm = FluxVerse tick.lock, ratified as proven).
#
# PREREGISTERED ACCEPTANCE CRITERIA (this header written BEFORE the launcher
# edit and BEFORE any test run - preregistration discipline):
#   AC-D03-1  lock records the holder PID: after acquire, round.lock content
#             is exactly the acquiring child process PID (bare digits).
#   AC-D03-2  live holder PID + lock age below floor -> skip (exit 0),
#             lock file left untouched.
#   AC-D03-3  dead holder + young lock -> skip (orphan-writer mitigation: a
#             dead launcher may still have a writing child - R13 lesson).
#   AC-D03-4  dead holder + lock age >= floor -> takeover: old lock removed,
#             re-grabbed with the taker PID.
#   AC-D03-5  live holder + age >= floor (hung round) -> fail-open takeover.
#   AC-D03-6  unreadable / legacy-format lock -> age floor alone decides
#             (young -> skip, old -> takeover). Protects the one in-flight
#             old-format round across the standard transition.
#   AC-D03-7  atomic grab: FileMode.CreateNew on an existing path throws.
#   AC-D03-8  takeover floor default = 30 min = 1.2 x 25-min round budget.
#   AC-D03-9  encoding law: iteration_loop.ps1 is pure ASCII.
#   AC-D03-10 static parse of iteration_loop.ps1: 0 parser errors.
#
# SAFETY: the lock block is EXTRACTED VERBATIM from the real launcher by
# marker comments (single source of truth, zero drift) and runs in CHILD
# powershell processes against a TEMP directory - no codely round is ever
# spawned and the real logs/round.lock is never touched.
#
# Usage: powershell -NoProfile -ExecutionPolicy Bypass -File src\os\test_lock.ps1
# Exit code: 0 = all criteria pass, 2 = at least one FAIL (repo test law).

$ErrorActionPreference = 'Continue'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$launcher = Join-Path $here 'iteration_loop.ps1'
$script:fail = 0

function Assert([bool]$cond, [string]$name, [string]$detail) {
    if ($cond) { Write-Output "PASS $name ($detail)" }
    else { Write-Output "FAIL $name ($detail)"; $script:fail = $script:fail + 1 }
}

# --- extract the lock block verbatim from the real launcher ---
$lines = [System.IO.File]::ReadAllLines($launcher)
$beginHit = $lines | Select-String -SimpleMatch '# ---- single-instance lock begin'
$endHit = $lines | Select-String -SimpleMatch '# ---- single-instance lock end'
if (-not $beginHit -or -not $endHit) { Write-Output 'FAIL extract: lock block markers missing'; exit 2 }
$b0 = @($beginHit)[0].LineNumber
$e0 = @($endHit)[-1].LineNumber
if ($e0 -le $b0) { Write-Output 'FAIL extract: marker order wrong'; exit 2 }
$blockText = ($lines[($b0 - 1)..($e0 - 1)] -join "`r`n")

# --- build the child harness in a temp dir ---
$tmpDir = Join-Path ([System.IO.Path]::GetTempPath()) ("bd_locktest_" + [System.IO.Path]::GetRandomFileName().Replace('.', ''))
New-Item -ItemType Directory -Path $tmpDir -Force | Out-Null
$harnessFile = Join-Path $tmpDir 'harness.ps1'
$tmpLock = Join-Path $tmpDir 'round.lock'
$tmpl = @'
$logDir = '{LOCKDIR}'
$LockMaxAgeMinutes = 30
function Log([string]$m) { Write-Output ("LOG: " + $m) }
function Beat([string]$m) { Write-Output ("BEAT: " + $m) }
{BLOCK}
Write-Output 'HARNESS:ACQUIRED'
Write-Output ("HARNESS:PID=" + $PID)
'@
$harnessText = $tmpl.Replace('{LOCKDIR}', $tmpDir).Replace('{BLOCK}', $blockText)
[System.IO.File]::WriteAllText($harnessFile, $harnessText, [System.Text.Encoding]::ASCII)

function Invoke-Case {
    $out = & powershell -NoProfile -ExecutionPolicy Bypass -File $harnessFile 2>&1
    $text = (@($out) | ForEach-Object { "$_" }) -join "`n"
    return @{ text = $text; code = $LASTEXITCODE }
}
function New-Lock([string]$content, [double]$ageMinutes) {
    if (Test-Path $tmpLock) { Remove-Item $tmpLock -Force }
    [System.IO.File]::WriteAllText($tmpLock, $content)
    (Get-Item $tmpLock).LastWriteTime = (Get-Date).AddMinutes(-$ageMinutes)
}
function LockContent { try { ([string]([System.IO.File]::ReadAllText($tmpLock))).Trim() } catch { '<gone>' } }

$liveProc = $null
try {
    # AC-D03-1: no lock -> atomic grab, lock records the child PID.
    if (Test-Path $tmpLock) { Remove-Item $tmpLock -Force }
    $r = Invoke-Case
    $childPid = ''
    if ($r.text -match 'HARNESS:PID=(\d+)') { $childPid = $Matches[1] }
    Assert ($r.code -eq 0 -and $r.text.Contains('HARNESS:ACQUIRED') -and $r.text.Contains('lock acquired')) 'AC-D03-1' 'grab with no lock, acquired'
    Assert ((LockContent) -eq $childPid -and $childPid -match '^\d+$') 'AC-D03-1' 'lock content == child pid'

    # live holder process for AC-D03-2 / AC-D03-5
    $liveProc = Start-Process powershell -ArgumentList '-NoProfile', '-Command', 'Start-Sleep -Seconds 90' -PassThru -WindowStyle Hidden
    Start-Sleep -Milliseconds 800

    # AC-D03-2: live holder + young lock -> skip, lock untouched.
    New-Lock ("{0}" -f $liveProc.Id) 5
    $r = Invoke-Case
    Assert ($r.code -eq 0 -and (-not $r.text.Contains('HARNESS:ACQUIRED')) -and $r.text.Contains('alive, round in flight')) 'AC-D03-2' 'live holder young lock -> skip'
    Assert ((LockContent) -eq ("{0}" -f $liveProc.Id)) 'AC-D03-2' 'lock untouched by skip'

    # AC-D03-3: dead holder + young lock -> skip (orphan-writer window).
    $deadProc = Start-Process powershell -ArgumentList '-NoProfile', '-Command', 'Start-Sleep -Milliseconds 200' -PassThru -WindowStyle Hidden
    Wait-Process -Id $deadProc.Id -ErrorAction SilentlyContinue
    Start-Sleep -Milliseconds 600
    Assert ($null -eq (Get-Process -Id $deadProc.Id -ErrorAction SilentlyContinue)) 'AC-D03-3' 'dead pid prepared'
    New-Lock ("{0}" -f $deadProc.Id) 5
    $r = Invoke-Case
    Assert ($r.code -eq 0 -and (-not $r.text.Contains('HARNESS:ACQUIRED')) -and $r.text.Contains('dead but age')) 'AC-D03-3' 'dead holder young lock -> skip'
    Assert ((LockContent) -eq ("{0}" -f $deadProc.Id)) 'AC-D03-3' 'lock untouched by skip'

    # AC-D03-4: dead holder + stale lock -> takeover + re-grab.
    New-Lock ("{0}" -f $deadProc.Id) 31
    $r = Invoke-Case
    $childPid4 = ''
    if ($r.text -match 'HARNESS:PID=(\d+)') { $childPid4 = $Matches[1] }
    Assert ($r.code -eq 0 -and $r.text.Contains('HARNESS:ACQUIRED') -and $r.text.Contains('state=dead')) 'AC-D03-4' 'dead holder stale lock -> takeover'
    Assert ((LockContent) -eq $childPid4) 'AC-D03-4' 're-grabbed lock records taker pid'

    # AC-D03-5: live holder + stale lock (hung round) -> fail-open takeover.
    New-Lock ("{0}" -f $liveProc.Id) 31
    $r = Invoke-Case
    Assert ($r.code -eq 0 -and $r.text.Contains('HARNESS:ACQUIRED') -and $r.text.Contains('state=alive-hung')) 'AC-D03-5' 'hung live holder stale lock -> takeover'

    # AC-D03-6: unreadable/legacy lock content -> age floor decides both ways.
    New-Lock '20260925_001402' 5
    $r = Invoke-Case
    Assert ($r.code -eq 0 -and (-not $r.text.Contains('HARNESS:ACQUIRED')) -and $r.text.Contains('unreadable lock')) 'AC-D03-6' 'legacy young -> skip'
    New-Lock '20260925_001402' 31
    $r = Invoke-Case
    Assert ($r.code -eq 0 -and $r.text.Contains('HARNESS:ACQUIRED')) 'AC-D03-6' 'legacy stale -> takeover'

    # AC-D03-7: FileMode.CreateNew refuses an existing path (atomic gate).
    $threw = $false
    try { $fsx = [System.IO.File]::Open($tmpLock, [System.IO.FileMode]::CreateNew, [System.IO.FileAccess]::Write); $fsx.Close() } catch { $threw = $true }
    Assert $threw 'AC-D03-7' 'CreateNew threw on existing path'

    # AC-D03-8: takeover floor default = 30 (1.2 x 25-min budget).
    $rawLauncher = [System.IO.File]::ReadAllText($launcher)
    Assert ($rawLauncher.Contains('[int]$LockMaxAgeMinutes = 30')) 'AC-D03-8' 'floor default 30'

    # AC-D03-9: encoding law - launcher stays pure ASCII.
    $bytes = [System.IO.File]::ReadAllBytes($launcher)
    $nonAscii = 0
    foreach ($b in $bytes) { if ($b -gt 127) { $nonAscii++ } }
    Assert ($nonAscii -eq 0) 'AC-D03-9' ("non-ascii bytes=" + $nonAscii)

    # AC-D03-10: static parse, 0 errors.
    $tok = $null
    $perr = $null
    [System.Management.Automation.Language.Parser]::ParseFile($launcher, [ref]$tok, [ref]$perr) | Out-Null
    Assert (@($perr).Count -eq 0) 'AC-D03-10' ("parse errors=" + @($perr).Count)
}
finally {
    if ($liveProc -and (Get-Process -Id $liveProc.Id -ErrorAction SilentlyContinue)) { Stop-Process -Id $liveProc.Id -Force -ErrorAction SilentlyContinue }
    Remove-Item -Path $tmpDir -Recurse -Force -ErrorAction SilentlyContinue
}

if ($script:fail -eq 0) { Write-Output 'ALL CRITERIA PASS (AC-D03-1..10)'; exit 0 }
Write-Output ("FAILURES=" + $script:fail)
exit 2
