# BigDomain OS loop - OS-scheduled headless round launcher.
# Built 2026-09-24 by the CPH4 Labs inspection batch (CEO full-start order) -
# honest provenance: ported from the proven BigStream pattern
# (media/BigStream/src/os/iteration_loop.ps1, live since 2026-09-23).
# The durable session cron only fires while a Codely CLI window is open - the
# OS task is the only 10-min channel that survives closed windows (:x4 lane,
# see cph4/cadence.md 10-min lane table). Every beat: guards -> spawn ONE
# headless codely round (src/os/iteration_prompt.txt driven) -> heartbeat.
# v2 LIVENESS-GATED BUDGET (2026-10-19 port per ruling D-20261019-04 - cross-
# company iteration_loop v2 activity-gated budget port case; canonical source
# = quant/bigmoney/Tools/iteration_loop.ps1 commit 945c3f60; lineage = CEO
# root-cause order O-20261018-0948 dead-window epidemic surgery): the original
# 2026-09-24 port carried a 25-min WALL-CLOCK kill inherited from the
# MiniGame short-round pattern - every legitimate long round crossing 25 min
# was tree-killed mid-flight (fleet-wide "died pre-closeout" epidemic, 50+
# absorb generations of evidence, bm-a run_20261018_064801.log 07:13:02
# wall-clock timeout kill). v2 kills ONLY on EVIDENCE:
#   - silence kill: $RoundSilenceMinutes (25) of ZERO output activity (the
#     round's stdout/stderr redirect files gained no bytes = true hang), or
#   - hard cap: $RoundTimeoutMinutes (240) of total age.
# A productive long round streams tool output continuously and is NEVER
# killed by wall clock alone. Kills are RECURSIVE TREE kills (breadth-first
# descendant chain, seen-set guards PID-reuse cycles, 256-node bound,
# deepest-first) plus a post-kill self-check logging ZOMBIE_SURVIVOR rows
# (never silent). The task re-reads this file from disk on every fire, so
# the port takes effect on the next grid slot with zero re-registration.
# The agent-side soft budget stays 25 min per src/os/iteration_prompt.txt -
# the prompt disciplines scope; the launcher only guards against true hangs.
#
# Overlap prevented by logs/round.lock + task-level IgnoreNew. Lock = group
# single-instance standard D-20260925-03 (2026-09-25 decision round;
# originated from this loop's R13/R14 stale-takeover incident report):
# PID-recorded lock + pre-takeover holder liveness probe + atomic CreateNew
# grab + takeover floor 1.2 x round budget. v2 coherence: the floor scales
# with the budget (1.2 x 240 = 288 min) - a stale floor would take over
# legitimate long rounds exactly the way the old wall clock did. Verified by
# src/os/test_lock.ps1 (AC-D03-1..12).
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
    # (v2: 1.2 x 240min hard-cap budget = 288min)
    [int]$LockMaxAgeMinutes = 288,
    [int]$RoundTimeoutMinutes = 240,
    [int]$RoundSilenceMinutes = 25
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

# v2 kill helpers (D-20261019-04 port from canonical 945c3f60): recursive
# tree kill + post-kill self-check. The 2026-10-17 lane-starvation root
# cause: one-level kills left deep-tree survivors which kept counting into
# the cloud cap. Collect the descendant chain breadth-first (seen-set guards
# PID-reuse cycles, 256-node bound), kill deepest-first, then re-scan: any
# survivor logs a ZOMBIE_SURVIVOR row for the audit lane (child-clear
# verification, never silent).
function Kill-RoundTree([int]$rootPid) {
    $seen = @{}
    $frontier = @($rootPid)
    $ordered = @()
    while ($frontier.Count -gt 0 -and $ordered.Count -lt 256) {
        $next = @()
        foreach ($pp in $frontier) {
            $kids = @(Get-CimInstance Win32_Process -Filter "ParentProcessId=$pp" -ErrorAction SilentlyContinue)
            foreach ($k in $kids) {
                if (-not $seen.ContainsKey($k.ProcessId)) {
                    $seen[$k.ProcessId] = $true
                    $ordered += $k.ProcessId
                    $next += $k.ProcessId
                }
            }
        }
        $frontier = $next
    }
    if ($ordered.Count -gt 1) { [array]::Reverse($ordered) }
    foreach ($procId in $ordered) { Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue }
    Stop-Process -Id $rootPid -Force -ErrorAction SilentlyContinue
    return ,$ordered
}
function Stop-RoundTreeChecked([int]$rootPid, [string]$why) {
    $killed = Kill-RoundTree $rootPid
    Log "kill tree ($why): root=$rootPid descendants_killed=$($killed.Count)"
    Start-Sleep -Seconds 2
    $survivors = 0
    foreach ($procId in $killed) {
        if (Get-Process -Id $procId -ErrorAction SilentlyContinue) {
            $survivors++
            Log "ZOMBIE_SURVIVOR pid=$procId survived tree-kill ($why) -- audit lane face"
        }
    }
    if ($survivors -eq 0) { Log "kill tree self-check ($why): 0 survivors (child-clear verified)" }
    return $survivors
}

# ---- single-instance lock begin (D-20260925-03) ----
# Group single-instance standard (decision D-20260925-03, 2026-09-25 round;
# originated from this loop's R13/R14 stale-takeover incident report; paradigm
# = the FluxVerse tick.lock implementation this decision ratified as proven):
#   - the lock file records the holder PID (written+flushed+closed at once,
#     no held handle);
#   - before any takeover the holder PID is probed for liveness and the
#     takeover floor is 1.2 x round budget (288 min at v2 defaults): a dead holder alone is
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
    # Cloud concurrency cap preflight (O-20261015-1800 / council case
    # C-20261015-03 section 3 spec, applied 2026-10-15 R2001; headless-face
    # fix D-20261017-02 item 1, aligned with bigmoney commit 63943e50b /
    # C-20261016-05): this wrapper spawns a codely cloud LLM session every
    # 10-min grid slot. Before ignition count live AUTONOMOUS headless faces
    # only - cmdline carries ' -p "' (headless -p prompt signature).
    # Interactive Cowork windows are exempt per O-20261015-1800 sec.2:
    # counting them starved slots on interactive-heavy machines (R2001 real
    # reading live=7, all interactive = false-defer face; honest note: this
    # loop's own rounds are api=0 local, the cap is fleet cloud etiquette).
    # At >= 2 defer this slot (append defer ledger line + skip; the next grid
    # slot retries). fail-open by spec: a broken probe NEVER blocks production.
    $liveCount = -1
    try { $liveCount = @((Get-CimInstance Win32_Process -Filter "Name='codely.exe'" -ErrorAction SilentlyContinue) | Where-Object { $_.CommandLine -match ' -p "' }).Count } catch { $liveCount = -1 }
    if ($liveCount -ge 2) {
        Add-Content -Path (Join-Path $logDir 'cloud-cap.log') -Value "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') | CLOUD_CAP_DEFER live=$liveCount" -Encoding UTF8
        Log "cloud-cap defer live=$liveCount (cap >=2, next grid slot retries)"
        Beat "cloud-cap defer live=$liveCount"
        exit 0
    }
    if ($liveCount -lt 0) { Log 'cloud-cap probe failed - fail-open ignite per spec' }

    Log "spawning headless round (hard-cap ${RoundTimeoutMinutes}min, silence-kill ${RoundSilenceMinutes}min, prompt_chars=$($prompt.Length), out=$roundOut)"
    $p = Start-Process -FilePath $codelyPath -ArgumentList $argLine -WorkingDirectory $Project -PassThru -NoNewWindow -RedirectStandardOutput $roundOut -RedirectStandardError $roundErr
    $null = $p.Handle   # materialize handle so ExitCode is readable
    # v2 liveness budget (D-20261019-04 port, canonical 945c3f60): poll in 30s
    # slices. "Activity" = the round's stdout/stderr redirect files gaining
    # bytes. Kill ONLY on evidence of a hang (silent for $RoundSilenceMinutes)
    # or the $RoundTimeoutMinutes hard cap. A productive long round streams
    # tool output continuously and is never killed by wall clock alone (the
    # 25-min guillotine that caused the dead-window epidemic is gone).
    $startAt = Get-Date
    $lastMove = Get-Date
    $lastSize = -1L
    while (-not $p.WaitForExit(30000)) {
        $size = 0L
        foreach ($f in @($roundOut, $roundErr)) {
            try { $fi = Get-Item $f -ErrorAction SilentlyContinue; if ($fi) { $size += $fi.Length } } catch { }
        }
        if ($size -ne $lastSize) { $lastSize = $size; $lastMove = Get-Date }
        $silentMin = ((Get-Date) - $lastMove).TotalMinutes
        $totalMin = ((Get-Date) - $startAt).TotalMinutes
        if ($silentMin -ge $RoundSilenceMinutes) {
            Log "ROUND SILENCE-KILL: no output for $([int]$silentMin)min (total $([int]$totalMin)min) - killing headless process tree"
            try { $null = Stop-RoundTreeChecked $p.Id 'silence-kill' } catch { Log "kill failed: $_" }
            Beat "round silence-killed (no output $([int]$silentMin)min, total $([int]$totalMin)min)"
            exit 3
        }
        if ($totalMin -ge $RoundTimeoutMinutes) {
            Log "ROUND HARD-CAP after ${RoundTimeoutMinutes}min - killing headless process tree"
            try { $null = Stop-RoundTreeChecked $p.Id 'hard-cap' } catch { Log "kill failed: $_" }
            Beat "round hard-cap killed (age over ${RoundTimeoutMinutes}min)"
            exit 3
        }
    }
    $p.Refresh()
    Log "headless round finished exit=$($p.ExitCode) (ran $([int]((Get-Date) - $startAt).TotalMinutes)min)"
    Beat "round done exit=$($p.ExitCode)"
    exit $p.ExitCode
}
finally {
    Remove-Item $lock -Force -ErrorAction SilentlyContinue
}
