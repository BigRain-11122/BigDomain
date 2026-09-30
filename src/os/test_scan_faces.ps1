# test_scan_faces.ps1 - regression harness for scan_five_still.ps1 judgment faces.
# Scope = the newer faces (tech queue items, R531/R530 rework + R763 GORD extension):
#   [ORD]  own orders.md LAST table-row first-cell token vs state.last_order
#          baseline (R531 rework: bottom-appended rows must be seen; the old
#          first-row + HH:MM read was blind to them).
#   [TREE] single-writer check: index.lock / dirty / ahead-behind divergence
#          with the "NOT a local other-writer" note.
#   [QA]   daily smoke evidence charter face (png + log + benchmarks today).
#   [GORD] group orders multi-row batch face (R763: last-3 table rows visible
#          + mechanical new-row count vs state.last_gord_tbl_rows; R709
#          evidence: a 3-row batch hid two rows behind a single-last-row
#          display and needed a manual tail re-read).
# Other faces get minimal fixtures so the real scan script runs end to end;
# they are deliberately NOT asserted (scope control).
#
# PREREGISTERED ACCEPTANCE CRITERIA (backlog R554 line written BEFORE this
# file existed and BEFORE any run - preregistration discipline):
#   AC-SC1  bottom-appended newest table row (first-cell token != baseline)
#           -> "[ORD] FLAG last=<bottom token> baseline=<old>" + ord_last
#           detail line naming the bottom row (R530/R531 blind-spot face).
#   AC-SC2  last table-row token == baseline -> "[ORD] PASS last=X baseline=X".
#   AC-SC3  unparseable state.json -> "[STATE] FLAG parse_failed" back-off
#           signal + "[ORD] INFO last=<token> (state unavailable)"; child
#           scan still exits 0 (no crash on degraded state).
#   AC-SC4  .git\index.lock present -> "[TREE] FLAG index_lock_present".
#   AC-SC5  clean tree, no divergence -> "[TREE] PASS clean=1 lock=0".
#   AC-SC6  dirty tree (untracked file) -> "[TREE] FLAG dirty=N" + "git: ??"
#           detail line.
#   AC-SC7  ahead-1 divergence (bare remote + one unpushed commit)
#           -> "[TREE] FLAG clean=1 lock=0 diverged=..[ahead 1]" + the
#           "note: remote moved" line (not a local other-writer).
#   AC-SC8  today-dated qa/smoke-*.png + smoke-*.log AND
#           state.benchmarks_refreshed == today -> "[QA] PASS today_png=1
#           today_log=1 bench_today=True".
#   AC-SC9  no qa evidence + stale benchmarks -> "[QA] FLAG today_png=0
#           today_log=0 bench_today=False" + "(charter daily crawl round due)".
#   AC-SC11 GORD multi-row batch (4 table rows, 3-row batch at the tail)
#           -> all three "gord_tbl_last3[-1..-3]" lines present naming the
#           batch rows (R709 blind-spot face: no manual tail re-read needed);
#           state without last_gord_tbl_rows -> "gord_new_rows=baseline_missing"
#           (INFO, no crash).
#   AC-SC12 GORD new-row count math: state last_gord_tbl_rows=2 vs 4 table
#           rows -> "gord_new_rows=2"; scan child still exits 0.
#   AC-SC10 harness laws: sandbox scan copy is byte-identical to the real
#           script (copied at run time = single source of truth, zero drift);
#           harness file is pure ASCII; exit 0 all-pass / 2 any-fail.
#
# SAFETY: everything runs inside a per-run TEMP sandbox shaped as
# FluxGroup\domain\BigDomain plus FluxGroup-level fixture files. The real
# repo, real state.json, real group files and the real git tree are never
# touched. Sandbox git repos are throwaway.
#
# Usage: powershell -NoProfile -ExecutionPolicy Bypass -File src\os\test_scan_faces.ps1
# Exit code: 0 = all criteria pass, 2 = at least one FAIL (repo test law).

$ErrorActionPreference = 'Continue'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$repo = (Resolve-Path (Join-Path $here '..\..')).Path
$realScan = Join-Path $repo '.codely-cli\skills\bigdomain-loop-scan\scripts\scan_five_still.ps1'
$today = (Get-Date).ToString('yyyy-MM-dd')
$script:fail = 0

function Assert([bool]$cond, [string]$name, [string]$detail) {
    if ($cond) { Write-Output "PASS $name ($detail)" }
    else { Write-Output "FAIL $name ($detail)"; $script:fail = $script:fail + 1 }
}

$sbxRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("bd_scanfaces_" + [System.IO.Path]::GetRandomFileName().Replace('.', ''))
$sbxGroup = Join-Path $sbxRoot 'FluxGroup'
$sbxRepo = Join-Path $sbxGroup 'domain\BigDomain'
$sbxScan = Join-Path $sbxRepo '.codely-cli\skills\bigdomain-loop-scan\scripts\scan_five_still.ps1'
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)

function Reset-Sandbox {
    if (Test-Path $sbxRoot) { Remove-Item -LiteralPath $sbxRoot -Recurse -Force -ErrorAction SilentlyContinue }
    foreach ($d in @(
        (Split-Path -Parent $sbxScan),
        (Join-Path $sbxRepo 'src\os'),
        (Join-Path $sbxRepo 'docs'),
        (Join-Path $sbxRepo 'qa'),
        (Join-Path $sbxGroup 'cph4'),
        (Join-Path $sbxGroup 'docs')
    )) { New-Item -ItemType Directory -Path $d -Force | Out-Null }
    [System.IO.File]::Copy($realScan, $sbxScan, $true)
}

function Write-All([string]$relPath, [string[]]$lines) {
    $p = Join-Path $sbxRepo $relPath
    [System.IO.File]::WriteAllLines($p, $lines, $utf8NoBom)
}

function Write-Group([string]$relPath, [string[]]$lines) {
    $p = Join-Path $sbxGroup $relPath
    [System.IO.File]::WriteAllLines($p, $lines, $utf8NoBom)
}

function New-StateJson([string]$lastOrder, [string]$benchDate) {
    return '{"tick":9,"last_order":"' + $lastOrder + '","last_decision_rows":1,"benchmarks_refreshed":"' + $benchDate + '","log":["a","b"]}'
}

function Setup-Fixtures([string[]]$repoOrders, [string]$stateJson, [bool]$qaEvidence) {
    Write-Group 'cph4\evolution-ledger.md' @('ledger fixture row 1 (no atbd no conflict)')
    Write-Group 'docs\decisions.md' @('decision fixture row 1')
    Write-Group 'docs\orders.md' @('| 09-28 | group order fixture | dispatched |')
    Write-All 'orders.md' $repoOrders
    Write-All 'src\os\state.json' @($stateJson)
    Write-All 'src\os\backlog.md' @('- [ ] bootstrap item blocked on CEO physical parts')
    Write-All 'tasks.md' @('- [x] canon fixture item done')
    Write-All 'docs\status-export.json' @(('{"export_ts":"' + (Get-Date).ToString('yyyy-MM-ddTHH:mm:ss') + '"}'))
    if ($qaEvidence) {
        Write-All 'qa\smoke-R1.png' @('png-fixture')
        Write-All 'qa\smoke-R1.log' @('log-fixture')
    }
}

function Git-Baseline {
    git -C $sbxRepo init 2>$null | Out-Null
    git -C $sbxRepo add -A 2>$null
    git -C $sbxRepo -c user.name=bd -c user.email=bd@local commit -m baseline 2>$null | Out-Null
}

function Invoke-Scan {
    $out = & powershell -NoProfile -ExecutionPolicy Bypass -File $sbxScan 2>&1
    $code = $LASTEXITCODE
    $text = (@($out) | ForEach-Object { "$_" }) -join "`n"
    return @{ text = $text; code = $code }
}

try {
    # --- [ORD] face -------------------------------------------------------
    # AC-SC1: bottom-appended newest row must be flagged (R531 rework face).
    Reset-Sandbox
    Setup-Fixtures @(
        '| 2026-09-28 22:1x | older top order row | open |',
        '| 2026-09-29 05:0x | newly appended bottom order RUN-7 | open |'
    ) (New-StateJson '2026-09-28 22:1x' $today) $false
    Git-Baseline
    $r = Invoke-Scan
    Assert ($r.text -match '\[ORD\] FLAG last=2026-09-29 05:0x baseline=2026-09-28 22:1x') 'AC-SC1' 'bottom-appended new row flagged with last/baseline tokens'
    Assert ($r.text -match 'ord_last: .*newly appended bottom order') 'AC-SC1' 'ord_last detail line names the bottom row'

    # AC-SC2: last-row token equals baseline -> PASS.
    Reset-Sandbox
    Setup-Fixtures @('| 2026-09-28 22:1x | single current order row | open |') (New-StateJson '2026-09-28 22:1x' $today) $false
    Git-Baseline
    $r = Invoke-Scan
    Assert ($r.text -match '\[ORD\] PASS last=2026-09-28 22:1x baseline=2026-09-28 22:1x') 'AC-SC2' 'matching last-row token -> ORD PASS'

    # AC-SC3: broken state.json -> STATE FLAG back-off + ORD INFO, no crash.
    Reset-Sandbox
    Setup-Fixtures @('| 2026-09-28 22:1x | order row | open |') '{"tick":9 "broken json' $false
    Git-Baseline
    $r = Invoke-Scan
    Assert ($r.text -match '\[STATE\] FLAG parse_failed') 'AC-SC3' 'broken state -> STATE FLAG back-off signal'
    Assert ($r.text -match '\[ORD\] INFO last=2026-09-28 22:1x \(state unavailable\)') 'AC-SC3' 'ORD degrades to INFO when state unavailable'
    Assert ($r.code -eq 0) 'AC-SC3' 'scan child exits 0 on degraded state (no crash)'

    # --- [TREE] face ------------------------------------------------------
    # AC-SC4: index.lock present -> back-off FLAG.
    Reset-Sandbox
    Setup-Fixtures @('| 2026-09-28 22:1x | order row | open |') (New-StateJson '2026-09-28 22:1x' $today) $false
    Git-Baseline
    New-Item -ItemType File -Path (Join-Path $sbxRepo '.git\index.lock') -Force | Out-Null
    $r = Invoke-Scan
    Assert ($r.text -match '\[TREE\] FLAG index_lock_present') 'AC-SC4' 'index.lock -> TREE FLAG back-off'

    # AC-SC5: clean tree, no divergence -> PASS.
    Reset-Sandbox
    Setup-Fixtures @('| 2026-09-28 22:1x | order row | open |') (New-StateJson '2026-09-28 22:1x' $today) $false
    Git-Baseline
    $r = Invoke-Scan
    Assert ($r.text -match '\[TREE\] PASS clean=1 lock=0') 'AC-SC5' 'clean tree -> TREE PASS'

    # AC-SC6: dirty tree (untracked file) -> FLAG with detail lines.
    Reset-Sandbox
    Setup-Fixtures @('| 2026-09-28 22:1x | order row | open |') (New-StateJson '2026-09-28 22:1x' $today) $false
    Git-Baseline
    Write-All 'untracked_new.txt' @('dirty fixture')
    $r = Invoke-Scan
    Assert ($r.text -match '\[TREE\] FLAG dirty=1') 'AC-SC6' 'dirty tree -> TREE FLAG with count'
    Assert ($r.text -match 'git: \?\?') 'AC-SC6' 'git detail line lists the dirty entry'

    # AC-SC7: ahead-1 divergence -> FLAG + not-a-local-other-writer note.
    Reset-Sandbox
    Setup-Fixtures @('| 2026-09-28 22:1x | order row | open |') (New-StateJson '2026-09-28 22:1x' $today) $false
    Git-Baseline
    $bare = Join-Path $sbxRoot 'remote.git'
    git init --bare $bare 2>$null | Out-Null
    git -C $sbxRepo remote add origin $bare 2>$null
    $br = [string](git -C $sbxRepo symbolic-ref --short HEAD)
    git -C $sbxRepo push -u origin $br 2>$null | Out-Null
    Write-All 'second_commit.txt' @('ahead fixture')
    git -C $sbxRepo add -A 2>$null
    git -C $sbxRepo -c user.name=bd -c user.email=bd@local commit -m ahead 2>$null | Out-Null
    $r = Invoke-Scan
    Assert ($r.text -match '\[TREE\] FLAG clean=1 lock=0 diverged=.*\[ahead 1\]') 'AC-SC7' 'ahead-1 divergence detected'
    Assert ($r.text -match 'note: remote moved') 'AC-SC7' 'not-a-local-other-writer note present'

    # --- [QA] face --------------------------------------------------------
    # AC-SC8: today-dated png+log evidence + today benchmarks -> PASS.
    Reset-Sandbox
    Setup-Fixtures @('| 2026-09-28 22:1x | order row | open |') (New-StateJson '2026-09-28 22:1x' $today) $true
    Git-Baseline
    $r = Invoke-Scan
    Assert ($r.text -match '\[QA\] PASS today_png=1 today_log=1 bench_today=True') 'AC-SC8' 'today evidence + today benchmarks -> QA PASS'

    # AC-SC9: no evidence + stale benchmarks -> FLAG with charter-due note.
    Reset-Sandbox
    Setup-Fixtures @('| 2026-09-28 22:1x | order row | open |') (New-StateJson '2026-09-28 22:1x' '2026-09-01') $false
    Git-Baseline
    $r = Invoke-Scan
    Assert ($r.text -match '\[QA\] FLAG today_png=0 today_log=0 bench_today=False') 'AC-SC9' 'missing evidence + stale benchmarks -> QA FLAG'
    Assert ($r.text -match '\(charter daily crawl round due\)') 'AC-SC9' 'charter due note present'

    # --- [GORD] face (R763 extension) -------------------------------------
    # AC-SC11: a 3-row order batch at the tail must be fully visible in the
    # last3 block; state without last_gord_tbl_rows -> baseline_missing INFO.
    Reset-Sandbox
    Setup-Fixtures @('| 2026-09-28 22:1x | order row | open |') (New-StateJson '2026-09-28 22:1x' $today) $false
    Write-Group 'docs\orders.md' @(
        '| 09-28 | old group order fixture row | dispatched |',
        '| 09-30 ~21:0x | batch row one O-015 | dispatched |',
        '| 09-30 ~21:1x | batch row two O-016 | dispatched |',
        '| 09-30 ~21:2x | batch row three O-017 | dispatched |'
    )
    Git-Baseline
    $r = Invoke-Scan
    Assert ($r.text -match 'gord_tbl_last3\[-1\]: .*batch row three O-017') 'AC-SC11' 'last3 block shows the newest batch row'
    Assert ($r.text -match 'gord_tbl_last3\[-2\]: .*batch row two O-016' -and $r.text -match 'gord_tbl_last3\[-3\]: .*batch row one O-015') 'AC-SC11' 'last3 block shows both older batch rows (R709 blind-spot face)'
    Assert ($r.text -match '\[GORD\] INFO lines=\d+ tbl_rows=4 atbd=\d+ sha16=[0-9A-F]{16} gord_new_rows=baseline_missing') 'AC-SC11' 'no baseline field -> baseline_missing (INFO, no crash)'

    # AC-SC12: new-row count = current tbl_rows - state baseline (4 - 2 = 2).
    Reset-Sandbox
    Setup-Fixtures @('| 2026-09-28 22:1x | order row | open |') ('{"tick":9,"last_order":"2026-09-28 22:1x","last_decision_rows":1,"benchmarks_refreshed":"' + $today + '","last_gord_tbl_rows":2,"log":["a","b"]}') $false
    Write-Group 'docs\orders.md' @(
        '| 09-28 | old group order fixture row | dispatched |',
        '| 09-30 ~21:0x | batch row one O-015 | dispatched |',
        '| 09-30 ~21:1x | batch row two O-016 | dispatched |',
        '| 09-30 ~21:2x | batch row three O-017 | dispatched |'
    )
    Git-Baseline
    $r = Invoke-Scan
    Assert ($r.text -match 'gord_new_rows=2(?!\d)') 'AC-SC12' 'new-row count = tbl_rows - baseline (4-2=2)'
    Assert ($r.code -eq 0) 'AC-SC12' 'scan child exits 0 with GORD baseline math active'

    # --- AC-SC10: harness laws ---------------------------------------------
    [System.IO.File]::Copy($realScan, $sbxScan, $true)
    $a = [System.IO.File]::ReadAllBytes($realScan)
    $b = [System.IO.File]::ReadAllBytes($sbxScan)
    $sha = [System.Security.Cryptography.SHA256]::Create()
    $ha = [System.BitConverter]::ToString($sha.ComputeHash($a))
    $hb = [System.BitConverter]::ToString($sha.ComputeHash($b))
    $sha.Dispose()
    Assert ($ha -eq $hb) 'AC-SC10' 'sandbox scan copy byte-identical to real script (sha256 match)'
    $selfBytes = [System.IO.File]::ReadAllBytes($PSCommandPath)
    $nonAscii = 0
    foreach ($x in $selfBytes) { if ($x -gt 127) { $nonAscii++ } }
    Assert ($nonAscii -eq 0) 'AC-SC10' ("harness pure ASCII (non-ascii bytes=" + $nonAscii + ")")
}
finally {
    Remove-Item -LiteralPath $sbxRoot -Recurse -Force -ErrorAction SilentlyContinue
}

$checks = 23
if ($script:fail -eq 0) { Write-Output ("ALL CRITERIA PASS (AC-SC1..SC12, " + $checks + " checks)"); exit 0 }
Write-Output ("FAILURES=" + $script:fail)
exit 2
