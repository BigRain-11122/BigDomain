# Registers the BigDomain-OSLoop: 10-minute self-iteration round launcher.
# Built 2026-09-24 by the CPH4 Labs inspection batch (skeleton for the dormant
# BigDomain venture) - honest provenance: ported from the proven BigStream
# pattern (media/BigStream/src/os/register_loop_task.ps1), adapted to the :x4
# lane (cph4/cadence.md 10-min lane table: :x4 free as of 2026-09-24).
# PATH-AGNOSTIC: every path derives from this script's own location - zero
# edits needed on a new machine clone.
# VBS: uses the GROUP silent wrapper at <FluxGroup>\Tools\InvisibleRunner.vbs
# (BigDomain repo keeps no local copy - anti-duplication; README.md documents
# this dependency). The absolute VBS path is baked into the task action at
# registration time; re-running this script re-derives it (self-heal).
# Pure ASCII (see iteration_loop.ps1 ENCODING RULE). Idempotent via -Force.
# Re-registering refreshes the task definition - safe to re-run for self-heal.
# NOTE: the actual registration run belongs to the main session (the skeleton
# batch is file-prep only).

$Project = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)   # ...\BigDomain
$Group   = Split-Path -Parent (Split-Path -Parent $Project)       # ...\FluxGroup
$launcher = Join-Path $Project 'src\os\iteration_loop.ps1'
$vbs = Join-Path $Group 'Tools\InvisibleRunner.vbs'
if (-not (Test-Path $launcher)) { Write-Output "FATAL: $launcher missing"; exit 1 }
if (-not (Test-Path $vbs)) { Write-Output "FATAL: $vbs missing"; exit 1 }
$a = New-ScheduledTaskAction -Execute 'wscript.exe' `
    -Argument ('//B //nologo "' + $vbs + '" powershell.exe -NoProfile -ExecutionPolicy Bypass -File "' + $launcher + '"') `
    -WorkingDirectory $Project
# :x4 lane (fires at :04/:14/:24/:34/:44/:54). Deterministic next-fire calc:
# next minute m strictly in the future where (m % 10) == 4.
$start = Get-Date -Second 0 -Millisecond 0
$add = (4 - ($start.Minute % 10) + 10) % 10
if ($add -eq 0) { $add = 10 }   # already sitting on :x4 -> take the next one
$start = $start.AddMinutes($add)
$t = New-ScheduledTaskTrigger -Once -At $start -RepetitionInterval (New-TimeSpan -Minutes 10) -RepetitionDuration (New-TimeSpan -Days 3650)
$s = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 35)
# Principal: S4U is the group-wide law for every lane task on this machine
# (2026-09-29 ruling: an InteractiveToken lane ran headless child processes
# whose consoles flashed on the active desktop; 2026-10-15 regression on the
# Bigmoney loop showed the default comes back whenever a registrar omits the
# principal). Registered without -Principal Windows defaults to
# InteractiveToken, so the principal is always passed explicitly here.
$who = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$p = New-ScheduledTaskPrincipal -UserId $who -LogonType S4U -RunLevel Limited
try {
    Register-ScheduledTask -TaskName 'BigDomain-OSLoop' -Action $a -Trigger $t -Settings $s -Principal $p -Force -ErrorAction Stop | Out-Null
} catch {
    # Registration of an S4U principal needs an elevated shell; report the
    # failure instead of claiming success (a registrar that prints
    # "registered" after an access-denied leaves the old definition in place
    # and hides the drift).
    Write-Output ("FAILED: " + $_.Exception.Message)
    Write-Output "the existing task definition was left untouched; re-run from an elevated shell to apply S4U"
    exit 1
}
Write-Output "registered BigDomain-OSLoop (project=$Project, lane :x4), first fire $start"
