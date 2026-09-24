# BigDomain OS loop - OS-scheduled headless round launcher.
# Built 2026-09-24 by the CPH4 Labs inspection batch (CEO full-start order) -
# honest provenance: ported from the proven BigStream pattern
# (media/BigStream/src/os/iteration_loop.ps1, live since 2026-09-23).
# The durable session cron only fires while a Codely CLI window is open - the
# OS task is the only 10-min channel that survives closed windows (:x4 lane,
# see cph4/cadence.md 10-min lane table). Every beat: guards -> spawn ONE
# headless codely round (src/os/iteration_prompt.txt driven) -> heartbeat.
# Round budget 25 min; overlap prevented by logs/round.lock + task-level
# IgnoreNew. Lock = group single-instance standard D-20260925-03 (2026-09-25
# decision round; originated from this loop's R13/R14 stale-takeover incident
# report): PID-recorded lock + pre-takeover holder liveness probe + atomic
# CreateNew grab + takeover floor 1.2 x budget (30 min). Verified by
# src/os/test_lock.ps1.
#
# ENCODING RULE: this file must stay PURE ASCII. powershell.exe 5.1 decodes
# BOM-less .ps1 as ANSI/GBK and swallows quote bytes after multibyte sequences.
# All Chinese content lives in src/os/iteration_prompt.txt (UTF-8, read at
# runtime with explicit -Encoding UTF8).
#
# Self-heal recipe (run from an agent round when Get-ScheduledTask
# BigDomain-OSLoop is missing - path-agnostic, works on any machine):
#   powershell -NoProfile -ExecutionPolicy Bypass -File src/os/register_loop_task.ps1
param(
    [string]$Project = (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)),
    # takeover floor: 1.2 x round budget per group standard D-20260925-03
    [int]$LockMaxAgeMinutes = 30,
    [int]$RoundTimeoutMinutes = 25
)
$ErrorActionPreference = 'Continue'
Set-Location $Project
$logDir = Join-Path $Project 'logs'
New-Item -ItemType Directory -Force $logDir | Out-Null
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$runLog = Join-Path $logDir "run_$stamp.log"
$roundOut = Join-Path $logDir "round_$stamp.out"
$roundErr = Join-Path $logDir "round_$stamp.err"
$heart = Join-Path $logDir 'probe-heartbeat.txt'

function Log([string]$m) {
    $line = "$(Get-Date -Format 'HH:mm:ss') $m"
    Write-Output $line
    Add-Content -Path $runLog -Value $line -Encoding UTF8
}
function Beat([string]$m) {
    Add-Content -Path $heart -Value "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') osloop: $m" -Encoding UTF8
}

# ---- single-instance lock begin (D-20260925-03) ----
# Group single-instance standard (decision D-20260925-03, 2026-09-25 round;
# originated from this loop's R13/R14 stale-takeover incident report; paradigm
# = the FluxVerse tick.lock implementation this decision ratified as proven):
#   - the lock file records the holder PID (written+flushed+closed at once,
#     no held handle);
#   - before any takeover the holder PID is probed for liveness and the
#     takeover floor is 1.2 x round budget (30 min): a dead holder alone is
#     NOT takeover proof - its orphaned child round may still be writing
#     (R13 lesson); heartbeat touching was explicitly rejected by the call;
#   - the lock is removed only after death/overage is confirmed, then the
#     grab is atomic (FileMode.CreateNew) so racing beats cannot both win.
# Verified by src/os/test_lock.ps1 (AC-D03-1..10).
$lock = Join-Path $logDir 'round.lock'
$lockAcquired = $false
for ($i = 0; $i -lt 24 -and -not $lockAcquired; $i++) {
    if (Test-Path $lock) {
        $lockAge = ((Get-Date) - (Get-Item $lock).LastWriteTime).TotalMinutes
        $holderPid = ''
        try { $holderPid = ([string]([System.IO.File]::ReadAllText($lock))).Trim() } catch {}
        if ($holderPid -notmatch '^\d{1,8}$') { $holderPid = 'unreadable' }
        $holderAlive = $false
        if ($holderPid -ne 'unreadable') { $holderAlive = [bool](Get-Process -Id ([int]$holderPid) -ErrorAction SilentlyContinue) }
        if ($holderAlive -and $lockAge -lt $LockMaxAgeMinutes) { Log "skip: holder PID $holderPid alive, round in flight (age=$([int]$lockAge)min)"; Beat "skip (round in flight pid $holderPid)"; exit 0 }
        if (-not $holderAlive -and $holderPid -ne 'unreadable' -and $lockAge -lt $LockMaxAgeMinutes) { Log "skip: holder PID $holderPid dead but age=$([int]$lockAge)min < ${LockMaxAgeMinutes}min floor (orphan-writer window)"; Beat 'skip (young lock, holder dead)'; exit 0 }
        if ($holderPid -eq 'unreadable' -and $lockAge -lt $LockMaxAgeMinutes) { Log "skip: unreadable lock, age=$([int]$lockAge)min < ${LockMaxAgeMinutes}min floor"; Beat 'skip (unreadable young lock)'; exit 0 }
        $holderState = 'dead'
        if ($holderAlive) { $holderState = 'alive-hung' }
        Log "stale lock confirmed (holder pid=$holderPid state=$holderState, age=$([int]$lockAge)min) - taking over"
        Remove-Item -Path $lock -Force -ErrorAction SilentlyContinue
        Start-Sleep -Milliseconds 250
        continue
    }
    try {
        $lockFs = [System.IO.File]::Open($lock, [System.IO.FileMode]::CreateNew, [System.IO.FileAccess]::Write, ([System.IO.FileShare]::Read -bor [System.IO.FileShare]::Delete))
        $lockBytes = [System.Text.Encoding]::ASCII.GetBytes([string]$PID)
        $lockFs.Write($lockBytes, 0, $lockBytes.Length)
        $lockFs.Flush()
        $lockFs.Close()
        $lockAcquired = $true
        Log "lock acquired (pid=$PID)"
    } catch { Start-Sleep -Milliseconds 250 }
}
if (-not $lockAcquired) { Log 'skip: lock grab not won after retries'; Beat 'skip (grab retries exhausted)'; exit 0 }
# ---- single-instance lock end ----

try {
    Log "iteration round start $stamp"

    # Head-of-round pull, group cadence law P-2026-09-24-77 item 3 (git
    # round-trip: head pull --ff-only + agent tail-of-round push <= 10 min,
    # cadence.md 7). Fail-soft: an unreachable origin is only logged and
    # never blocks the round. Runs under the lock so it cannot race a
    # parallel round's working tree.
    $pullRaw = & git pull --ff-only 2>&1
    $pullOut = ($pullRaw | Where-Object { $_ } | ForEach-Object { "$_" }) -join ' | '
    Log "head pull exit=$($LASTEXITCODE): $pullOut"

    $codelyPath = (Get-Command codely -ErrorAction SilentlyContinue).Source
    if (-not $codelyPath) { Log 'FATAL: codely not on PATH for this context'; Beat 'error codely missing'; exit 2 }
    Log "codely=$codelyPath"

    # Round prompt (Chinese) lives outside this file - see ENCODING RULE above.
    $promptFile = Join-Path $Project 'src\os\iteration_prompt.txt'
    if (-not (Test-Path $promptFile)) { Log 'FATAL: iteration_prompt.txt missing'; Beat 'error prompt file missing'; exit 2 }
    $prompt = (Get-Content -Raw -Encoding UTF8 $promptFile).Trim()
    if ($prompt.Length -lt 50) { Log 'FATAL: iteration_prompt.txt too short'; Beat 'error prompt file empty'; exit 2 }

    # Sanitize embedded double quotes before Start-Process argument passing.
    if ($prompt.Contains('"')) { $prompt = $prompt.Replace('"', "'") }
    $argLine = '-y -p "' + $prompt + '"'
    Log "spawning headless round (budget ${RoundTimeoutMinutes}min, prompt_chars=$($prompt.Length), out=$roundOut)"
    $p = Start-Process -FilePath $codelyPath -ArgumentList $argLine -WorkingDirectory $Project -PassThru -NoNewWindow -RedirectStandardOutput $roundOut -RedirectStandardError $roundErr
    $null = $p.Handle   # materialize handle so ExitCode is readable
    if (-not $p.WaitForExit($RoundTimeoutMinutes * 60 * 1000)) {
        Log "ROUND TIMEOUT after ${RoundTimeoutMinutes}min - killing headless process tree"
        try {
            Get-CimInstance Win32_Process -Filter "ParentProcessId=$($p.Id)" -ErrorAction SilentlyContinue |
                ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
            Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
        } catch { Log "kill failed: $_" }
        Beat "round timeout killed (age over ${RoundTimeoutMinutes}min)"
        exit 3
    }
    $p.Refresh()
    Log "headless round finished exit=$($p.ExitCode)"
    Beat "round done exit=$($p.ExitCode)"
    exit $p.ExitCode
}
finally {
    Remove-Item $lock -Force -ErrorAction SilentlyContinue
}
