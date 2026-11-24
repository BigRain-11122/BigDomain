# Registers the BigDomain-OSLoop: self-iteration round launcher.
# Built 2026-09-24 by the CPH4 Labs inspection batch (skeleton for the dormant
# BigDomain venture) - honest provenance: ported from the proven BigStream
# pattern (media/BigStream/src/os/register_loop_task.ps1), adapted to the :x4
# lane (cph4/cadence.md lane table: :x4 free as of 2026-09-24).
# PATH-AGNOSTIC: every path derives from this script's own location - zero
# edits needed on a new machine clone.
# VBS: uses the GROUP silent wrapper at <FluxGroup>\Tools\InvisibleRunner.vbs
# (BigDomain repo keeps no local copy - anti-duplication; README.md documents
# this dependency). The absolute VBS path is baked into the task action at
# registration time; re-running this script re-derives it (self-heal).
# Pure ASCII (see iteration_loop.ps1 ENCODING RULE). Idempotent via -Force.
# Re-registering refreshes the task definition - safe to re-run for self-heal.
#
# CADENCE (R3386, 2026-11-24): the 2026-10-19 speed-up law put every OS lane on
# FIVE minutes and the live task reads PT5M, while this registrar still typed
# ten - so the one path that can repair the principal would have halved the
# round rate as a side effect. The interval is therefore never typed again for
# an existing definition: it is read off the live task and preserved
# (interval_why=preserved), defaults to five on a first registration and to an
# explicit -IntervalMinutes only when a caller asks. The start phase follows
# the chosen interval instead of a hardcoded ten-minute lane.
#
# -DryRun renders the definition it WOULD register and touches nothing, so the
# choices above are gradeable from a shell that is not elevated.
param(
    [switch]$DryRun,
    [int]$IntervalMinutes = 0,
    [string]$TaskName = 'BigDomain-OSLoop'
)

$DefaultIntervalMinutes = 5    # 2026-10-19 speed-up law: OS loops fire every 5 min
$LanePhaseMinute = 4           # fire on minutes where (m % interval) == 4

$Project = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)   # ...\BigDomain
$Group   = Split-Path -Parent (Split-Path -Parent $Project)       # ...\FluxGroup
$launcher = Join-Path $Project 'src\os\iteration_loop.ps1'
$vbs = Join-Path $Group 'Tools\InvisibleRunner.vbs'
if (-not (Test-Path $launcher)) { Write-Output "FATAL: $launcher missing"; exit 1 }
if (-not (Test-Path $vbs)) { Write-Output "FATAL: $vbs missing"; exit 1 }

# --- interval: explicit > preserved-from-live-task > declared default ----
$live = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
$liveInterval = $null
if ($live -and $live.Triggers) {
    foreach ($tr in $live.Triggers) {
        if ($tr.Repetition -and $tr.Repetition.Interval) { $liveInterval = $tr.Repetition.Interval; break }
    }
}
if ($IntervalMinutes -gt 0) {
    $span = New-TimeSpan -Minutes $IntervalMinutes
    $why = 'explicit'
} elseif ($liveInterval) {
    $span = [System.Xml.XmlConvert]::ToTimeSpan($liveInterval)
    $why = 'preserved'
} else {
    $span = New-TimeSpan -Minutes $DefaultIntervalMinutes
    $why = 'default'
}
$stepMin = [int]$span.TotalMinutes
if ($stepMin -lt 1) { Write-Output "FATAL: interval below one minute is not a lane"; exit 1 }
$intervalIso = [System.Xml.XmlConvert]::ToString($span)

# --- start: next occurrence of the lane phase, derived from the interval --
$start = Get-Date -Second 0 -Millisecond 0
$add = ($LanePhaseMinute - ($start.Minute % $stepMin) + $stepMin) % $stepMin
if ($add -eq 0) { $add = $stepMin }   # already sitting on the phase -> take the next one
$start = $start.AddMinutes($add)

$a = New-ScheduledTaskAction -Execute 'wscript.exe' `
    -Argument ('//B //nologo "' + $vbs + '" powershell.exe -NoProfile -ExecutionPolicy Bypass -File "' + $launcher + '"') `
    -WorkingDirectory $Project
$t = New-ScheduledTaskTrigger -Once -At $start -RepetitionInterval $span -RepetitionDuration (New-TimeSpan -Days 3650)
$s = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 35)
# Principal: S4U is the group-wide law for every lane task on this machine
# (2026-09-29 ruling: an InteractiveToken lane ran headless child processes
# whose consoles flashed on the active desktop; 2026-10-15 regression on the
# Bigmoney loop showed the default comes back whenever a registrar omits the
# principal). Registered without -Principal Windows defaults to a logon type
# of its own choosing, so the principal is always passed explicitly here.
$who = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$p = New-ScheduledTaskPrincipal -UserId $who -LogonType S4U -RunLevel Limited

if ($DryRun) {
    Write-Output ("DRYRUN task={0} interval={1} interval_why={2} lane_phase={3} first_fire={4} logon={5} runlevel={6} userid={7} action={8} working_dir={9}" -f `
        $TaskName, $intervalIso, $why, $LanePhaseMinute, $start.ToString('s'), 'S4U', 'Limited', $who, 'wscript.exe', $Project)
    exit 0
}

try {
    Register-ScheduledTask -TaskName $TaskName -Action $a -Trigger $t -Settings $s -Principal $p -Force -ErrorAction Stop | Out-Null
} catch {
    # Registration of an S4U principal needs an elevated shell; report the
    # failure instead of claiming success (a registrar that prints
    # "registered" after an access-denied leaves the old definition in place
    # and hides the drift).
    Write-Output ("FAILED: " + $_.Exception.Message)
    Write-Output "the existing task definition was left untouched; re-run from an elevated shell to apply S4U"
    exit 1
}

# Read back instead of announcing: a registrar that prints "registered" with
# no reading hides exactly the drift this file exists to prevent.
$after = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
$seenLogon = '<missing>'
$seenInterval = '<missing>'
$ok = $false
if ($after) {
    $seenLogon = [string]$after.Principal.LogonType
    foreach ($tr in $after.Triggers) {
        if ($tr.Repetition -and $tr.Repetition.Interval) { $seenInterval = $tr.Repetition.Interval; break }
    }
    $ok = ($seenLogon -eq 'S4U') -and ($seenInterval -eq $intervalIso)
}
if (-not $ok) {
    Write-Output ("FAILED: registered but the read-back disagrees (logon={0} interval={1} expected logon=S4U interval={2})" -f $seenLogon, $seenInterval, $intervalIso)
    exit 1
}
Write-Output ("registered {0} (project={1}) interval={2} interval_why={3} first_fire={4} VERIFY logon={5} interval={6}" -f `
    $TaskName, $Project, $intervalIso, $why, $start.ToString('s'), $seenLogon, $seenInterval)
