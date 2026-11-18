# test_scan_faces.ps1 - regression harness for scan_five_still.ps1 judgment faces.
# Scope = the newer faces (tech queue items, R531/R530 rework + R763 GORD extension):
#   [ORD]  own orders.md LAST table-row first-cell token vs state.last_order
#          baseline (R531 rework: bottom-appended rows must be seen; the old
#          first-row + HH:MM read was blind to them).
#   [TREE] single-writer check: index.lock / dirty / ahead-behind divergence
#          with the "NOT a local other-writer" note.
#   [QA]   daily smoke evidence charter face (today png + log; R2989: the
#          benchmark limb reads the SAME 7-day canon gate as [BENCH] and names
#          itself bench_age_d / bench_fresh7 - the old bench_today field could
#          only be true on a refresh day, so the face was red by construction).
#   [GORD] group orders multi-row batch face (R763: last-3 table rows visible
#          + mechanical new-row count vs state.last_gord_tbl_rows; R709
#          evidence: a 3-row batch hid two rows behind a single-last-row
#          display and needed a manual tail re-read).
#   [DEC]  group decisions.md row-owner token face (R1794 false-positive law,
#          delivered R1795): a row's own ID is the FIRST D-/C- token on a
#          '|'-prefixed line; inline references are INFO-only, never new rows.
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
#   AC-SC8  a qa/crawl-log.jsonl record naming today (source_url + fetched_at +
#           verdict) AND state.benchmarks_refreshed inside the 7-day canon gate
#           -> "[QA] PASS crawl_today=1 crawl_rows=1 crawl_bad=0 today_png=0
#           today_log=0 bench_age_d=... bench_fresh7=True" - written WITHOUT any
#           smoke file, so a limb that still gated on png/log would read FLAG
#           here (R2990: the crawl limb reads a record, not a filename).
#   AC-SC9  no record + stale benchmarks -> "[QA] FLAG crawl_today=0
#           crawl_rows=0 crawl_bad=0 ... bench_fresh7=False" + "(charter daily
#           crawl round due)".
#   AC-SC20 benchmark limb is a RANGE law, not a same-day law: (a) refreshed
#           3 days ago + today record -> QA PASS with bench_age_d=3 and
#           bench_fresh7=True; (b) refreshed 8 days ago + today record ->
#           QA FLAG with bench_fresh7=False (widening to always-green goes red);
#           (c) the emitted line carries no bench_today token at all.
#   AC-SC21 smoke artifacts can no longer stand in for a crawl: (a) today's
#           png+log with no record -> FLAG (the measured R2988 false green);
#           (b) a record missing verdict -> FLAG crawl_bad=1, today=0;
#           (c) a truncated line beside a good record -> PASS, crawl_bad=1;
#           (d) a record naming yesterday -> crawl_rows=1 but crawl_today=0.
#   AC-SC11 GORD multi-row batch (4 table rows, 3-row batch at the tail)
#           -> all three "gord_tbl_last3[-1..-3]" lines present naming the
#           batch rows (R709 blind-spot face: no manual tail re-read needed);
#           state without last_gord_tbl_rows -> "gord_new_rows=baseline_missing"
#           (INFO, no crash).
#   AC-SC12 GORD new-row count math: state last_gord_tbl_rows=2 vs 4 table
#           rows -> "gord_new_rows=2"; scan child still exits 0.
#   AC-SC13 state.json parseable but written with bare-LF terminators
#           (closeout LF disease, R1697/R1704 recurrences) -> "[STATE] FLAG
#           eol_bare_lf=N" carrying the logs_toolkit eol repair hint; scan
#           child still exits 0 (detection lands BEFORE fold's
#           E_STATE_LAYOUT refusal - R1705 AC-EO5).
#   AC-SC14 healthy CRLF state -> "[STATE] PASS ... eol_ok=1" (CRLF
#           conservation gate positive face).
#   AC-SC15 DEC row-owner law: a judged row citing an old gap token in its
#           body (reference, not a new row) -> "[DEC] PASS ... row_owner_tokens=1"
#           + dec_ref_missing_base INFO note; NO dec_new_tok line (R1794
#           false-FLAG face does not reproduce).
#   AC-SC16 a genuine new owner row (first token on a '|'-prefixed line
#           absent from the baseline) -> "[DEC] FLAG ... new_tokens=1" and the
#           dec_new_tok detail names the owner's OWN row (attribution fix);
#           scan child exits 0.
#   AC-SC17 [ORD] dual-format law (R2001, tech.md L259): a no-year
#           '| MM-DD HH:MMx |' tail row NEWER than baseline -> "[ORD] FLAG
#           last=<raw token>" + ord_last detail (year-only regex was blind).
#   AC-SC18 [ORD] direction law: own tail OLDER than baseline ->
#           "[ORD] INFO ... (baseline ahead...)" - never a FLAG (last_order
#           tracks the group-orders tail since R1998; stale own-tail is not
#           a new order - R1999 false-FLAG root cure).
#   AC-SC19 [ORD] wildcard law: baseline x-digit vs concrete same-position
#           token ("17:4x" vs "17:45") -> "[ORD] PASS" (same row, no
#           false FLAG).
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
$yesterday = (Get-Date).AddDays(-1).ToString('yyyy-MM-dd')
$script:fail = 0
$script:pass = 0

function Assert([bool]$cond, [string]$name, [string]$detail) {
    if ($cond) { Write-Output "PASS $name ($detail)"; $script:pass = $script:pass + 1 }
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

    # AC-SC13: parseable but bare-LF state.json -> eol FLAG + repair hint.
    Reset-Sandbox
    Setup-Fixtures @('| 2026-09-28 22:1x | order row | open |') (New-StateJson '2026-09-28 22:1x' $today) $false
    $sickState = '{"tick":9,' + "`n" + '"last_order":"2026-09-28 22:1x","last_decision_rows":1,"benchmarks_refreshed":"' + $today + '",' + "`n" + '"log":["a","b"]}'
    [System.IO.File]::WriteAllText((Join-Path $sbxRepo 'src\os\state.json'), $sickState, $utf8NoBom)
    Git-Baseline
    $r = Invoke-Scan
    Assert ($r.text -match '\[STATE\] FLAG eol_bare_lf=2 \(closeout wrote bare LF; repair first: python src/os/logs_toolkit.py eol --fix --execute') 'AC-SC13' 'bare-LF state -> eol_bare_lf=2 FLAG with repair hint'
    Assert ($r.code -eq 0) 'AC-SC13' 'scan child exits 0 on eol FLAG (no crash)'

    # AC-SC14: healthy CRLF state -> PASS carries eol_ok=1.
    Reset-Sandbox
    Setup-Fixtures @('| 2026-09-28 22:1x | order row | open |') (New-StateJson '2026-09-28 22:1x' $today) $false
    Git-Baseline
    $r = Invoke-Scan
    Assert ($r.text -match '\[STATE\] PASS .*eol_ok=1') 'AC-SC14' 'healthy CRLF state -> eol_ok=1 on STATE PASS'

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
    # R2990: the crawl limb reads qa/crawl-log.jsonl (source_url / fetched_at /
    # verdict) instead of a smoke file's mtime, so every arm writes records and
    # the png/log counts are asserted as DISPLAY ONLY.
    function New-CrawlLine([string]$url, [string]$fetchedAt, [string]$verdict) {
        return ('{"source_url":"' + $url + '","fetched_at":"' + $fetchedAt + '","verdict":"' + $verdict + '"}')
    }
    function Write-CrawlRecord([string[]]$lines) {
        Write-All 'qa\crawl-log.jsonl' $lines
    }

    # AC-SC8: a record naming today + benchmarks inside the 7-day gate -> PASS.
    # NO png and NO log are written here on purpose: if a smoke file still gated
    # the limb, this arm would read FLAG.
    Reset-Sandbox
    Setup-Fixtures @('| 2026-09-28 22:1x | order row | open |') (New-StateJson '2026-09-28 22:1x' $today) $false
    Write-CrawlRecord @((New-CrawlLine 'https://www.gov.cn/zhengce/x.htm' ($today + 'T09:10:00+08:00') 'new-source'))
    Git-Baseline
    $r = Invoke-Scan
    Assert ($r.text -match '\[QA\] PASS crawl_today=1 crawl_rows=1 crawl_bad=0 today_png=0 today_log=0 bench_age_d=[0-9.]+ bench_fresh7=True') 'AC-SC8' 'today record + fresh benchmarks -> QA PASS with no smoke file at all'

    # AC-SC9: no record + stale benchmarks -> FLAG with charter-due note.
    Reset-Sandbox
    Setup-Fixtures @('| 2026-09-28 22:1x | order row | open |') (New-StateJson '2026-09-28 22:1x' '2026-09-01') $false
    Git-Baseline
    $r = Invoke-Scan
    Assert ($r.text -match '\[QA\] FLAG crawl_today=0 crawl_rows=0 crawl_bad=0 today_png=0 today_log=0 bench_age_d=[0-9.]+ bench_fresh7=False') 'AC-SC9' 'no record + stale benchmarks -> QA FLAG'
    Assert ($r.text -match '\(charter daily crawl round due\)') 'AC-SC9' 'charter due note present'

    # AC-SC20: the benchmark limb is a range law (R2989). (a) three days old
    # is INSIDE the 7-day gate -> PASS and the age is named, not "today";
    # (c) the old bench_today token is gone from the emitted line.
    $d3 = (Get-Date).AddDays(-3).ToString('yyyy-MM-dd')
    Reset-Sandbox
    Setup-Fixtures @('| 2026-09-28 22:1x | order row | open |') (New-StateJson '2026-09-28 22:1x' $d3) $false
    Write-CrawlRecord @((New-CrawlLine 'https://pay.weixin.qq.com/doc/v2/merchant/4011986682' ($today + 'T07:20:00+08:00') 'no-drift'))
    Git-Baseline
    $r = Invoke-Scan
    Assert ($r.text -match '\[QA\] PASS crawl_today=1 crawl_rows=1 crawl_bad=0 today_png=0 today_log=0 bench_age_d=3\.[0-9]+ bench_fresh7=True') 'AC-SC20' '3-day-old benchmarks inside the gate -> QA PASS with a named age'
    Assert ($r.text -notmatch 'bench_today') 'AC-SC20' 'the retired bench_today token no longer reaches the emitted line'

    # AC-SC20 (b): eight days old is OUTSIDE the gate even with a today record
    # -> FLAG (a limb widened to always-green would go red here).
    $d8 = (Get-Date).AddDays(-8).ToString('yyyy-MM-dd')
    Reset-Sandbox
    Setup-Fixtures @('| 2026-09-28 22:1x | order row | open |') (New-StateJson '2026-09-28 22:1x' $d8) $false
    Write-CrawlRecord @((New-CrawlLine 'https://pay.weixin.qq.com/doc/v2/merchant/4011986682' ($today + 'T07:20:00+08:00') 'no-drift'))
    Git-Baseline
    $r = Invoke-Scan
    Assert ($r.text -match '\[QA\] FLAG crawl_today=1 crawl_rows=1 crawl_bad=0 today_png=0 today_log=0 bench_age_d=8\.[0-9]+ bench_fresh7=False') 'AC-SC20' '8-day-old benchmarks outside the gate -> QA FLAG'
    Assert ($r.code -eq 0) 'AC-SC20' 'scan child exits 0 on the QA FLAG face (detection only)'

    # AC-SC21 (R2990): today's smoke artifacts can no longer stand in for a
    # crawl. (a) png+log today with NO record -> FLAG (the measured false green
    # of R2988); (b) a record missing a field -> FLAG with bad=1 and not today;
    # (c) a truncated line beside a good one -> PASS, bad=1, the good row kept;
    # (d) a record naming YESTERDAY -> today=0, so the day filter is real.
    Reset-Sandbox
    Setup-Fixtures @('| 2026-09-28 22:1x | order row | open |') (New-StateJson '2026-09-28 22:1x' $today) $true
    Git-Baseline
    $r = Invoke-Scan
    Assert ($r.text -match '\[QA\] FLAG crawl_today=0 crawl_rows=0 crawl_bad=0 today_png=1 today_log=1') 'AC-SC21' 'smoke png+log without a crawl record -> FLAG (false green closed)'

    Reset-Sandbox
    Setup-Fixtures @('| 2026-09-28 22:1x | order row | open |') (New-StateJson '2026-09-28 22:1x' $today) $false
    Write-CrawlRecord @('{"source_url":"https://a.example/x","fetched_at":"' + $today + 'T09:00:00+08:00"}')
    Git-Baseline
    $r = Invoke-Scan
    Assert ($r.text -match '\[QA\] FLAG crawl_today=0 crawl_rows=0 crawl_bad=1') 'AC-SC21' 'a record with no verdict reads bad=1 and never today'

    Reset-Sandbox
    Setup-Fixtures @('| 2026-09-28 22:1x | order row | open |') (New-StateJson '2026-09-28 22:1x' $today) $false
    Write-CrawlRecord @(
        (New-CrawlLine 'https://www.gov.cn/zhengce/x.htm' ($today + 'T09:10:00+08:00') 'new-source'),
        '{"source_url": "https://a.example/broken",'
    )
    Git-Baseline
    $r = Invoke-Scan
    Assert ($r.text -match '\[QA\] PASS crawl_today=1 crawl_rows=1 crawl_bad=1') 'AC-SC21' 'a truncated line reads bad=1 while the good record still answers today'

    Reset-Sandbox
    Setup-Fixtures @('| 2026-09-28 22:1x | order row | open |') (New-StateJson '2026-09-28 22:1x' $today) $false
    Write-CrawlRecord @((New-CrawlLine 'https://www.gov.cn/zhengce/x.htm' ($yesterday + 'T23:50:00+08:00') 'no-drift'))
    Git-Baseline
    $r = Invoke-Scan
    Assert ($r.text -match '\[QA\] FLAG crawl_today=0 crawl_rows=1 crawl_bad=0') 'AC-SC21' 'a yesterday record is counted as a row but not as today'

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

    # --- [DEC] row-owner face (R1794 false-positive law, delivered R1795) ---
    # AC-SC15: a judged row citing an old gap token in its body is a
    # reference, not a new row -> PASS + INFO note, no false FLAG.
    Reset-Sandbox
    Setup-Fixtures @('| 2026-09-28 22:1x | order row | open |') ('{"tick":9,"last_order":"2026-09-28 22:1x","last_decision_rows":1,"benchmarks_refreshed":"' + $today + '","last_dec_tokens":"D-20261011-06","log":["a","b"]}') $false
    Write-Group 'docs\decisions.md' @(
        '| 2026-10-11 | D-20261011-06 judged decision row (body cites D-20260930-04 gap token) | detail |'
    )
    Git-Baseline
    $r = Invoke-Scan
    Assert ($r.text -match '\[DEC\] PASS rows=\d+ known_tokens=2 row_owner_tokens=1 \(content-addressed row-owner; row baseline=1 secondary\)') 'AC-SC15' 'referenced gap token -> DEC PASS with row_owner_tokens (no false FLAG)'
    Assert ($r.text -match 'dec_ref_missing_base D-20260930-04 \(inline reference token absent from baseline; not a new row\)') 'AC-SC15' 'ref-missing INFO note names the gap token'
    Assert ($r.text -notmatch 'dec_new_tok') 'AC-SC15' 'no dec_new_tok line for a referenced-only token'

    # AC-SC16: a genuine new owner row still FLAGs, and the detail line names
    # the owner's own row (not a row that merely references it).
    Reset-Sandbox
    Setup-Fixtures @('| 2026-09-28 22:1x | order row | open |') ('{"tick":9,"last_order":"2026-09-28 22:1x","last_decision_rows":1,"benchmarks_refreshed":"' + $today + '","last_dec_tokens":"D-20261011-06","log":["a","b"]}') $false
    Write-Group 'docs\decisions.md' @(
        '| 2026-10-11 | D-20261011-06 judged row (body cites D-20260930-04 gap token) | detail |',
        '| 2026-10-11 | D-20261011-07 brand new owner decision row | detail |'
    )
    Git-Baseline
    $r = Invoke-Scan
    Assert ($r.text -match '\[DEC\] FLAG rows=\d+ known_tokens=3 row_owner_tokens=2 new_tokens=1') 'AC-SC16' 'new owner token -> FLAG with new_tokens=1 (detection semantics preserved)'
    Assert ($r.text -match 'dec_new_tok D-20261011-07 : .*brand new owner decision row') 'AC-SC16' 'detail line names the owner row itself (attribution fix)'
    Assert ($r.code -eq 0) 'AC-SC16' 'scan child exits 0 with DEC row-owner face active'

    # --- [ORD] dual-format + direction face (R2001, tech.md L259 fix) ---------
    # AC-SC17: a no-year '| MM-DD HH:MMx |' tail row NEWER than the baseline
    # must FLAG (dual-format match law: the year-only regex was blind to it).
    Reset-Sandbox
    Setup-Fixtures @(
        '| 2026-09-28 22:1x | older year-format order row | open |',
        '| 10-15 18:0x | mirrored no-year group order row | open |'
    ) (New-StateJson '2026-10-15 17:4x' $today) $false
    Git-Baseline
    $r = Invoke-Scan
    Assert ($r.text -match '\[ORD\] FLAG last=10-15 18:0x baseline=2026-10-15 17:4x') 'AC-SC17' 'no-year tail newer than baseline -> FLAG with raw token'
    Assert ($r.text -match 'ord_last: .*mirrored no-year group order') 'AC-SC17' 'ord_last detail names the no-year row'

    # AC-SC18: own year-format tail OLDER than baseline -> INFO (baseline
    # ahead), never a FLAG (R1999 false-FLAG root cure).
    Reset-Sandbox
    Setup-Fixtures @('| 2026-09-28 22:1x | old own order row | open |') (New-StateJson '2026-10-15 18:0x' $today) $false
    Git-Baseline
    $r = Invoke-Scan
    Assert ($r.text -match '\[ORD\] INFO last=2026-09-28 22:1x baseline=2026-10-15 18:0x \(baseline ahead') 'AC-SC18' 'older own tail vs ahead baseline -> INFO baseline-ahead'
    Assert ($r.text -notmatch '\[ORD\] FLAG') 'AC-SC18' 'no false FLAG for the stale own-tail face'

    # AC-SC19: wildcard-equal (baseline x-digit vs concrete same row) -> PASS.
    Reset-Sandbox
    Setup-Fixtures @(
        '| 2026-09-28 22:1x | older year-format order row | open |',
        '| 10-15 17:45 | current no-year order row | open |'
    ) (New-StateJson '2026-10-15 17:4x' $today) $false
    Git-Baseline
    $r = Invoke-Scan
    Assert ($r.text -match '\[ORD\] PASS last=10-15 17:45 baseline=2026-10-15 17:4x') 'AC-SC19' 'x-wildcard baseline vs concrete token -> PASS (same row)'

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

if ($script:fail -eq 0) { Write-Output ("ALL CRITERIA PASS (AC-SC1..SC21, " + $script:pass + " checks)"); exit 0 }
Write-Output ("FAILURES=" + $script:fail)
exit 2
