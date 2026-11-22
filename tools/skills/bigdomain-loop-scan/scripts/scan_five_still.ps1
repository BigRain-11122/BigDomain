# scan_five_still.ps1 - BigDomain OSLoop five-still opening scan (read-only)
# Emits one "[AREA] PASS|FLAG|INFO" line per face plus flagged-line details.
# The agent (not this script) interprets results against state.json baselines.
$ErrorActionPreference = 'Continue'
$utf8 = [System.Text.Encoding]::UTF8
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$repo = (Resolve-Path (Join-Path $here '..\..\..\..')).Path
$group = (Resolve-Path (Join-Path $repo '..\..')).Path

# --- group-ledger read-only consumption canon (D-20261001-03): git fetch + git show origin/main:<path> ---
# Working-tree pull/rebase/checkout against the group tree are FORBIDDEN by the same canon.
# A direct working-tree read survives ONLY as an explicit fallback when git show is unavailable;
# per-file mode is reported on the [GROUPSRC] line so any fallback use stays visible (honesty law).
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { }
$grpMode = @{}
try { & git -C $group fetch origin --quiet 2>$null } catch { }
$grpFetchOk = ($LASTEXITCODE -eq 0)
function Get-GroupFile([string]$rel) {
  $out = & git -C $group show "origin/main:$rel" 2>$null
  if ($LASTEXITCODE -eq 0 -and $null -ne $out) {
    $raw = (@($out) -join "`n") + "`n"
    if ($raw.Length -gt 1 -and $raw[0] -eq [char]0xFEFF) { $raw = $raw.Substring(1) }
    $m = 'origin-main'
    if (-not $grpFetchOk) { $m = 'origin-main(stale-fetch)' }
    $script:grpMode[$rel] = $m
    return @{ raw = $raw }
  }
  $p = Join-Path $group ($rel -replace '/', '\')
  if (Test-Path $p) {
    $script:grpMode[$rel] = 'worktree-fallback'
    return @{ raw = [System.IO.File]::ReadAllText($p, $utf8) }
  }
  throw "group file unreadable both ways: $rel"
}

# --- [STATE] own state.json ---
$st = $null
$raw = $null
try {
  $raw = [System.IO.File]::ReadAllText((Join-Path $repo 'src\os\state.json'), $utf8)
  $st = $raw | ConvertFrom-Json
  $logN = @($st.log).Count
  $bytes = $utf8.GetByteCount($raw)
  # CRLF conservation gate (R1705 AC-EO5): closeout LF write must surface
  # here BEFORE fold refuses with E_STATE_LAYOUT (R1697/R1704 recurrences).
  $lfN = [regex]::Matches($raw, "`n").Count
  $crlfN = [regex]::Matches($raw, "`r`n").Count
  $bareLf = $lfN - $crlfN
  if ($bareLf -gt 0) {
    Write-Output "[STATE] FLAG eol_bare_lf=$bareLf (closeout wrote bare LF; repair first: python src/os/logs_toolkit.py eol --fix --execute; fold would refuse E_STATE_LAYOUT)"
  } else {
    Write-Output "[STATE] PASS tick=$($st.tick) last_order=$($st.last_order) last_decision_rows=$($st.last_decision_rows) benchmarks_refreshed=$($st.benchmarks_refreshed) log_lines=$logN state_bytes=$bytes eol_ok=1"
  }
} catch {
  Write-Output '[STATE] FLAG parse_failed (other writer may be active - back off, read-only round)'
}

# --- [LEDGER] group evolution ledger (group-level, read-only) ---
try {
  $gt = Get-GroupFile 'cph4/evolution-ledger.md'
  $L = @(($gt.raw.TrimEnd("`r", "`n")) -split "\r?\n")
  $atbd = @($L | Select-String -SimpleMatch '@BigDomain')
  # R2907: anchor the merge-marker test to the START of a line. The unanchored form
  # matched prose that DESCRIBES an old cleanup ("(`<<<<<<< HEAD` / ... / `>>>>>>>`)"),
  # which kept this face red for rounds against a file with no conflict in it, and once
  # sent a false escalation to HQ-FEEDBACK. A real marker is the whole leading token.
  $conf = @($L | Select-String -Pattern '^(<<<<<<<|>>>>>>>|\|\|\|\|\|\|\|)( |$)')
  $pnums = @($L | Select-String -Pattern 'P-\d{4}-\d{2}-\d{2}-\d{2}' -AllMatches | ForEach-Object { $_.Matches } | ForEach-Object { $_.Value })
  $lastp = (@($pnums | Select-Object -Last 3) -join ',')
  if ($conf.Count -gt 0) {
    Write-Output "[LEDGER] FLAG lines=$($L.Count) atbd_rows=$($atbd.Count) conflict=$($conf.Count) lastp=$lastp"
  } else {
    Write-Output "[LEDGER] PASS lines=$($L.Count) atbd_rows=$($atbd.Count) conflict=$($conf.Count) lastp=$lastp"
  }
} catch { Write-Output '[LEDGER] FLAG read_failed' }

# --- [DEC] group decisions.md (content-addressed D-/C- token set diff vs state baseline; D-20260930-18/19: pure row-count is drift-prone and forbidden) ---
# Row-owner token law (R1794 false-positive fix, delivered R1795): a decision row's own ID is
# the FIRST D-/C- token on a table row ('|'-prefixed) line. Tokens cited inside a row body,
# or on non-table lines, are references - never new rows. A referenced token missing from
# the baseline is an INFO note (historical recording gap), NOT a FLAG; only a row-owner
# token missing from the baseline is a new decision row to judge.
try {
  $gt = Get-GroupFile 'docs/decisions.md'
  $draw = $gt.raw
  $D = @(($draw.TrimEnd("`r", "`n")) -split "\r?\n")
  $tok = @([regex]::Matches($draw, '(?:D|C)-\d{8}-\d{2}') | ForEach-Object { $_.Value } | Sort-Object -Unique)
  $decTokRe = '(?:D|C)-\d{8}-\d{2}'
  $ownerRaw = @()
  $refRaw = @()
  $ownerRow = @{}
  for ($i = 0; $i -lt $D.Count; $i++) {
    $ln = [string]$D[$i]
    $ms = @([regex]::Matches($ln, $decTokRe))
    if ($ms.Count -eq 0) { continue }
    if ($ln -match '^\s*\|') {
      $own = $ms[0].Value
      $ownerRaw += $own
      if (-not $ownerRow.ContainsKey($own)) { $ownerRow[$own] = $ln }
      if ($ms.Count -gt 1) { $refRaw += @($ms | Select-Object -Skip 1 | ForEach-Object { $_.Value }) }
    } else {
      $refRaw += @($ms | ForEach-Object { $_.Value })
    }
  }
  $ownerTok = @($ownerRaw | Sort-Object -Unique)
  $refTok = @($refRaw | Sort-Object -Unique)
  $baseStr = ''
  if ($st -ne $null) { $baseStr = [string]$st.last_dec_tokens }
  if ($baseStr -eq '') {
    Write-Output "[DEC] FLAG rows=$($D.Count) known_tokens=$($tok.Count) row_owner_tokens=$($ownerTok.Count) baseline_missing (init state.json last_dec_tokens from full token set, then only diff)"
  } else {
    # last_dec_tokens is a JSON array; [string] on an array joins with spaces (not commas),
    # so a comma-only split collapsed the entire baseline into one token and every row
    # re-flagged as new each round (R2344 birth-site fix). Split on commas AND whitespace,
    # and accept the array form directly.
    $baseTok = @(@($st.last_dec_tokens) | ForEach-Object { [string]$_ } | ForEach-Object { $_ -split '[,\s]+' } | Where-Object { $_ })
    # Guard: a baseline that collapses to a single token while rows exist means the parse
    # regressed, not that every row is new. Say so instead of re-flagging the whole board.
    if ($baseTok.Count -eq 1 -and $ownerTok.Count -gt 1) {
      Write-Output "[DEC] FLAG baseline_parse_collapsed count=1 owners=$($ownerTok.Count) (parse defect, not new rows - fix the baseline split)"
    }
    $newTok = @($ownerTok | Where-Object { $baseTok -notcontains $_ })
    $refMissing = @($refTok | Where-Object { $baseTok -notcontains $_ -and $ownerTok -notcontains $_ })
    if ($newTok.Count -gt 0) {
      Write-Output "[DEC] FLAG rows=$($D.Count) known_tokens=$($tok.Count) row_owner_tokens=$($ownerTok.Count) new_tokens=$($newTok.Count) (content-addressed row-owner; row baseline=$($st.last_decision_rows) secondary)"
      foreach ($n in $newTok) {
        $t = ''
        if ($ownerRow.ContainsKey($n)) { $t = [string]$ownerRow[$n] }
        else {
          $hit = @($D | Select-String -SimpleMatch $n) | Select-Object -First 1
          if ($hit) { $t = [string]$hit.Line }
        }
        if ($t.Length -gt 300) { $t = $t.Substring(0, 300) + '...' }
        Write-Output "  dec_new_tok $n : $t"
      }
    } else {
      Write-Output "[DEC] PASS rows=$($D.Count) known_tokens=$($tok.Count) row_owner_tokens=$($ownerTok.Count) (content-addressed row-owner; row baseline=$($st.last_decision_rows) secondary)"
    }
    if ($refMissing.Count -gt 0) {
      foreach ($n in $refMissing) {
        Write-Output "  dec_ref_missing_base $n (inline reference token absent from baseline; not a new row)"
      }
    }
  }
} catch { Write-Output '[DEC] FLAG read_failed' }

# --- [GORD] group docs/orders.md FULL-FILE scan (D-20260927-05(2) adopted 2026-09-27: active-order rows land in the head table region and mid-table, tail-only scan had blind spots) ---
# R763 multi-row batch blind-spot fix (R709 evidence: a 3-row order batch landed right after
# the scan window; the single-last-row display surfaced only the newest row O-017, the older
# two batch rows needed a manual tail re-read): display the LAST 3 table rows plus a
# mechanical new-row count vs the state baseline last_gord_tbl_rows (kept at ack/judgment
# closeout, same discipline as last_dec_tokens). Absent baseline -> baseline_missing (INFO),
# negative count -> rows were removed (honest display, formatting drift).
try {
  $gt = Get-GroupFile 'docs/orders.md'
  $gordRaw = $gt.raw
  $O = @(($gordRaw.TrimEnd("`r", "`n")) -split "\r?\n")
  $shaProv = [System.Security.Cryptography.SHA256]::Create()
  $sha16 = [System.BitConverter]::ToString($shaProv.ComputeHash($utf8.GetBytes($gordRaw))).Replace('-','').Substring(0,16)
  $shaProv.Dispose()
  $tbl = @($O | Select-String -Pattern '^\|\s*\d{2}-\d{2}')
  $atbd = @($O | Select-String -SimpleMatch '@BigDomain').Count
  $gordBaseRows = $null
  if ($st -ne $null -and @($st.PSObject.Properties.Name) -contains 'last_gord_tbl_rows') { $gordBaseRows = [int]$st.last_gord_tbl_rows }
  if ($null -ne $gordBaseRows) {
    $newRows = [string]($tbl.Count - $gordBaseRows)
  } else {
    $newRows = 'baseline_missing (init state.json last_gord_tbl_rows at ack closeout)'
  }
  Write-Output "[GORD] INFO lines=$($O.Count) tbl_rows=$($tbl.Count) atbd=$atbd sha16=$sha16 gord_new_rows=$newRows"
  $lastN = @($tbl | Select-Object -Last 3)
  $pos = $lastN.Count
  foreach ($row in $lastN) {
    $s = [string]$row
    if ($s.Length -gt 200) { $s = $s.Substring(0, 200) + '...' }
    Write-Output "  gord_tbl_last3[-$pos]: $s"
    $pos--
  }
  $lastLine = [string]$O[$O.Count - 1]
  $u = $lastLine; if ($u.Length -gt 200) { $u = $u.Substring(0, 200) + '...' }
  Write-Output "  gord_last_line: $u"
} catch { Write-Output '[GORD] FLAG read_failed' }

# --- [GROUPSRC] consumption-mode report (D-20261001-03 canon: git fetch + git show origin/main:<path>; worktree = fallback only) ---
$modes = @()
foreach ($k in @('cph4/evolution-ledger.md', 'docs/decisions.md', 'docs/orders.md')) {
  if ($grpMode.ContainsKey($k)) { $modes += ($k + '=' + $grpMode[$k]) }
}
if ($modes.Count -eq 0) { $modes += 'no-group-read' }
Write-Output ("[GROUPSRC] " + ($modes -join ' ') + " | canon D-20261001-03: git fetch + git show origin/main:<path>; worktree read = fallback only")

# --- [ORD] own orders.md LAST table-row token vs baseline (append-newest convention; R531 rework: first-row+HH:MM regex was blind to bottom-appended RUN_ID-format rows) ---
# R2001 dual-format + direction law (tech.md L259 seed; R1999 takeover rescan evidence):
# table rows exist in BOTH the legacy year format '| 2026-MM-DD HH:MMx |' and the
# no-year '| MM-DD HH:MMx |' shape; the year-only regex read a stale 2026-09-28 tail
# and false-FLAGged every round. last_order has tracked the GROUP orders tail since
# R1998 (that is where new CEO orders land), so an older own-tail is INFO (baseline
# ahead), never a FLAG; only a token NEWER than baseline is a new order to judge.
# Wildcard law: 'x' in either token matches any character at that position.
try {
  $OO = [System.IO.File]::ReadAllLines((Join-Path $repo 'orders.md'), $utf8)
  $orows = @($OO | Where-Object { $_ -match '^\|\s*(2026-\d{2}-\d{2}|\d{2}-\d{2})\s' })
  $lastRow = [string]($orows | Select-Object -Last 1)
  $topTs = ''
  if ($lastRow -match '^\|\s*([^|]+?)\s*\|') { $topTs = $Matches[1].Trim() }
  $yr = ''
  foreach ($rw in $orows) { if ("$rw" -match '^\|\s*(\d{4})-') { $yr = $Matches[1] } }
  if ($yr -eq '') { $yr = (Get-Date).ToString('yyyy') }
  $normTs = $topTs
  if ($normTs -match '^(\d{2})-(\d{2})\s+(.+)$') { $normTs = "$yr-$($Matches[1])-$($Matches[2]) $($Matches[3])" }
  $baseRaw = ''
  if ($st -ne $null) { $baseRaw = [string]$st.last_order }
  $normBase = $baseRaw
  if ($normBase -match '^(\d{2})-(\d{2})\s+(.+)$') { $normBase = "$yr-$($Matches[1])-$($Matches[2]) $($Matches[3])" }
  $cmp = 0
  $n = [Math]::Min($normTs.Length, $normBase.Length)
  for ($i = 0; $i -lt $n; $i++) {
    $a = [string]$normTs[$i]; $b = [string]$normBase[$i]
    if ($a -eq 'x' -or $b -eq 'x' -or $a -eq $b) { continue }
    if ($a -lt $b) { $cmp = -1 } else { $cmp = 1 }
    break
  }
  if ($st -eq $null) {
    Write-Output "[ORD] INFO last=$topTs (state unavailable)"
  } elseif ($topTs -eq $baseRaw -or $cmp -eq 0) {
    Write-Output "[ORD] PASS last=$topTs baseline=$baseRaw"
  } elseif ($cmp -gt 0) {
    Write-Output "[ORD] FLAG last=$topTs baseline=$baseRaw"
    if ($lastRow.Length -gt 0) { Write-Output "  ord_last: $lastRow" }
  } else {
    Write-Output "[ORD] INFO last=$topTs baseline=$baseRaw (baseline ahead: last_order tracks group-orders tail since R1998; own tail older, no new order)"
  }
} catch { Write-Output '[ORD] FLAG read_failed' }

# --- [BENCH] benchmarks freshness (7-day cycle) ---
try {
  $days = [int]((Get-Date) - (Get-Date $st.benchmarks_refreshed)).TotalDays
  if ($days -gt 7) {
    Write-Output "[BENCH] FLAG days=$days refreshed=$($st.benchmarks_refreshed)"
  } else {
    Write-Output "[BENCH] PASS days=$days refreshed=$($st.benchmarks_refreshed)"
  }
} catch { Write-Output '[BENCH] INFO refresh_age_unmeasured' }

# --- [QA] daily crawl record + smoke evidence (group QA Smoke Test charter v1.0, orders L254 2026-09-28: daily crawl + qa/ evidence; R2989: the benchmark limb reads the same 7-day canon gate as [BENCH] because the charter's "not stale 15h" cannot coexist with a 7-day refresh cycle - escalated in HQ-FEEDBACK; R2990: the crawl limb reads a RECORD with three fields instead of a filename, because an mtime cannot tell a crawl apart from any other artifact written the same day) ---
try {
  $today = (Get-Date).ToString('yyyy-MM-dd')
  $qaDir = Join-Path $repo 'qa'
  $qaPng = 0; $qaLog = 0
  if (Test-Path $qaDir) {
    $qaPng = @(Get-ChildItem -LiteralPath $qaDir -Filter 'smoke-*.png' | Where-Object { $_.LastWriteTime.ToString('yyyy-MM-dd') -eq $today }).Count
    $qaLog = @(Get-ChildItem -LiteralPath $qaDir -Filter 'smoke-*.log' | Where-Object { $_.LastWriteTime.ToString('yyyy-MM-dd') -eq $today }).Count
  }
  # R2990: a smoke artifact's mtime says "something was written", not "a source
  # was crawled" - measured, one round's PASS came from a gallery screenshot plus
  # a suite payload. A crawl is now a record in qa/crawl-log.jsonl carrying
  # source_url, fetched_at and verdict; its day is the first ten characters of
  # fetched_at taken literally, the same law as tools/crawl_record.py. The
  # png/log counts stay on the line as DISPLAY fields only - they gate nothing.
  $crawlToday = 0; $crawlRows = 0; $crawlBad = 0
  $crawlPath = Join-Path $qaDir 'crawl-log.jsonl'
  if (Test-Path -LiteralPath $crawlPath) {
    foreach ($ln in [System.IO.File]::ReadAllLines($crawlPath, $utf8)) {
      if ([string]::IsNullOrWhiteSpace($ln)) { continue }
      try { $o = $ln | ConvertFrom-Json } catch { $crawlBad++; continue }
      $u = [string]$o.source_url
      $ft = [string]$o.fetched_at
      $v = [string]$o.verdict
      if (-not ($u.StartsWith('http://') -or $u.StartsWith('https://')) -or ($ft -notmatch '^\d{4}-\d{2}-\d{2}') -or [string]::IsNullOrWhiteSpace($v)) { $crawlBad++; continue }
      $crawlRows++
      if ($ft.Substring(0, 10) -eq $today) { $crawlToday++ }
    }
  }
  # R2989: the charter limb "not stale 15h" was coded as "refreshed today", which
  # can only be true on a refresh day while the canon cycle is 7 days - the face
  # was red by construction. This limb now reads the SAME 7-day gate as [BENCH],
  # and the field names say so (bench_age_d / bench_fresh7), so the output cannot
  # be misread as a daily refresh; the charter-vs-canon gap is escalated, not hidden.
  $benchAgeD = $null
  try { $benchAgeD = ((Get-Date) - (Get-Date ('' + $st.benchmarks_refreshed))).TotalDays } catch { }
  $benchFresh7 = ($null -ne $benchAgeD -and $benchAgeD -le 7)
  $benchAgeTxt = 'unmeasured'
  if ($null -ne $benchAgeD) { $benchAgeTxt = [string][math]::Round([double]$benchAgeD, 2) }
  if ($crawlToday -ge 1 -and $benchFresh7) {
    Write-Output "[QA] PASS crawl_today=$crawlToday crawl_rows=$crawlRows crawl_bad=$crawlBad today_png=$qaPng today_log=$qaLog bench_age_d=$benchAgeTxt bench_fresh7=$benchFresh7"
  } else {
    Write-Output "[QA] FLAG crawl_today=$crawlToday crawl_rows=$crawlRows crawl_bad=$crawlBad today_png=$qaPng today_log=$qaLog bench_age_d=$benchAgeTxt bench_fresh7=$benchFresh7 (charter daily crawl round due)"
  }
} catch { Write-Output '[QA] FLAG check_failed' }

# --- [HB] repo-root heartbeat.txt row freshness (standing law R532; detection face added R851 after 2nd recurrence R537..R540 + R849/R850; backfill precedent R541; R1386: skip trailing blank lines - trailing 0D0A0D0A gave false missing_or_unparsed) ---
try {
  $hbPath = Join-Path $repo 'heartbeat.txt'
  $hbTick = -1
  if (Test-Path $hbPath) {
    $hbLast = @(Get-Content -LiteralPath $hbPath -Tail 5 | Where-Object { $_ -match '\S' } | Select-Object -Last 1)
    if (@($hbLast).Count -gt 0 -and $hbLast[0] -match 'tick (\d+)') { $hbTick = [int]$Matches[1] }
  }
  $stTick = [int]$st.tick
  if ($hbTick -lt 0) {
    Write-Output '[HB] FLAG heartbeat_missing_or_unparsed'
  } elseif (($stTick - $hbTick) -gt 0) {
    Write-Output "[HB] FLAG hb_tick=$hbTick state_tick=$stTick lag=$($stTick - $hbTick) (heartbeat row debt: backfill due in this round closeout)"
  } elseif (($hbTick - $stTick) -gt 0) {
    # R3323: a row stamped past the state is not a fresh row with lag 0. The
    # shipped reader prints the truth instead of the old hard-coded lag=0, so
    # an ahead row (a hand or repair wrote the next tick) names itself here.
    Write-Output "[HB] PASS hb_tick=$hbTick state_tick=$stTick ahead=$($hbTick - $stTick) (heartbeat row is ahead of state by design)"
  } else {
    Write-Output "[HB] PASS hb_tick=$hbTick state_tick=$stTick lag=0"
  }
} catch { Write-Output '[HB] FLAG check_failed' }

# --- [TASKS] canonical board + claim board ---
try {
  $T = [System.IO.File]::ReadAllLines((Join-Path $repo 'tasks.md'), $utf8)
  $un = @($T | Select-String -Pattern '- \[ \]')
  $B = [System.IO.File]::ReadAllLines((Join-Path $repo 'src\os\backlog.md'), $utf8)
  $open = @($B | Select-String -Pattern '^- \[ \]')
  $blocked = 0; $claimable = 0
  foreach ($o in $open) { if ($o.Line -match 'blocked on CEO') { $blocked++ } else { $claimable++ } }
  Write-Output "[TASKS] INFO tasks_unchecked=$($un.Count) backlog_open=$($open.Count) blocked_on_ceo=$blocked claimable=$claimable"
} catch { Write-Output '[TASKS] FLAG read_failed' }

# --- [EXPORT] silicon-watch export freshness (24h gate) ---
try {
  $E = [System.IO.File]::ReadAllText((Join-Path $repo 'docs\status-export.json'), $utf8)
  $ex = $E | ConvertFrom-Json
  $age = [Math]::Round(((Get-Date) - (Get-Date $ex.export_ts)).TotalHours, 1)
  if ($age -ge 24) {
    Write-Output "[EXPORT] FLAG age_h=$age export_ts=$($ex.export_ts)"
  } else {
    Write-Output "[EXPORT] PASS age_h=$age export_ts=$($ex.export_ts)"
  }
} catch { Write-Output '[EXPORT] FLAG read_or_parse_failed' }

# --- [DELIV] CEO entry page vs disk (R3068, criteria AC-SC22) ---
# preview/index.html is rendered by tools/deliverable_index.py, and that tool's
# own --check is the only face that can see the LANDED page fall behind disk:
# the battery suite drives the tool inside a private temp world. Nothing in the
# loop ran it - the launcher does lock/crawl/pull/spawn, and face_sweep (which
# does run every face's --check) is not scheduled. This face runs it on every
# opening scan for one read-only pass (measured 0.16 s). Fail-soft by
# construction: a missing tool, a missing interpreter or a crashing tool reads
# SKIP/FLAG and never aborts the scan.
try {
  $diTool = Join-Path $repo 'tools\deliverable_index.py'
  $diPy = (Get-Command python -ErrorAction SilentlyContinue).Source
  if (-not (Test-Path -LiteralPath $diTool)) {
    Write-Output '[DELIV] SKIP tool_absent'
  } elseif (-not $diPy) {
    Write-Output '[DELIV] SKIP python_absent'
  } else {
    $diOut = & $diPy $diTool --check 2>&1
    $diRc = $LASTEXITCODE
    $diTxt = (@($diOut) | ForEach-Object { "$_" }) -join "`n"
    $diFail = @([regex]::Matches($diTxt, 'FAIL (AC-DIX[0-9A-Za-z]+)') | ForEach-Object { $_.Groups[1].Value } | Select-Object -Unique)
    $diFailTxt = 'none'
    if ($diFail.Count -gt 0) { $diFailTxt = ($diFail -join ',') }
    if ($diRc -eq 0) {
      Write-Output '[DELIV] PASS entry_page_matches_disk=1 failed=none'
    } else {
      Write-Output "[DELIV] FLAG entry_page_matches_disk=0 failed=$diFailTxt rc=$diRc (re-render: python tools\deliverable_index.py)"
    }
  }
} catch { Write-Output '[DELIV] FLAG check_failed' }

# --- [GATES] all nine CEO face gates (R3069, criteria AC-SC23) ---
# [DELIV] above runs ONE of the nine gates (the entry page). Measured at R3069:
# the nine --check runs together cost 8.68 s, none of them writes to its own
# pair, and two of them (six-gate-live, ugc-gate) were RED with nothing in the
# loop running them. face_sweep owns BOTH the face table and the executor, so
# this face asks it for the reading (--gates: one row per face plus one summary,
# no render, no write) instead of keeping a second list here. Scheduling
# face_sweep's render mode was refused: it writes two CEO pages every round and
# its own AC-FSW10 goes stale again on the next face re-render. Fail-soft.
try {
  $fsTool = Join-Path $repo 'tools\face_sweep.py'
  $fsPy = (Get-Command python -ErrorAction SilentlyContinue).Source
  if (-not (Test-Path -LiteralPath $fsTool)) {
    Write-Output '[GATES] SKIP tool_absent'
  } elseif (-not $fsPy) {
    Write-Output '[GATES] SKIP python_absent'
  } else {
    $fsOut = & $fsPy $fsTool --gates 2>&1
    $fsRc = $LASTEXITCODE
    $fsTxt = (@($fsOut) | ForEach-Object { "$_" }) -join "`n"
    $fsSum = @([regex]::Matches($fsTxt, 'GATES (PASS|FLAG) gates=(\d+) green=(\d+) red=(\d+) red_ids=(\S+)'))
    if ($fsSum.Count -lt 1) {
      Write-Output "[GATES] FLAG no_summary_line rc=$fsRc"
    } else {
      $fsM = $fsSum[$fsSum.Count - 1]
      if ($fsRc -eq 0) {
        Write-Output ("[GATES] PASS gates={0} green={1} red=0" -f $fsM.Groups[2].Value, $fsM.Groups[3].Value)
      } else {
        Write-Output ("[GATES] FLAG gates={0} green={1} red={2} red_ids={3} rc={4}" -f $fsM.Groups[2].Value, $fsM.Groups[3].Value, $fsM.Groups[4].Value, $fsM.Groups[5].Value, $fsRc)
      }
    }
  }
} catch { Write-Output '[GATES] FLAG check_failed' }

# --- [TREE] git single-writer check ---
$lockPath = Join-Path $repo '.git\index.lock'
if (Test-Path $lockPath) {
  Write-Output '[TREE] FLAG index_lock_present (back off, read-only round)'
} else {
  $gs = @(git -C $repo status --short | Where-Object { $_ })
  if ($gs.Count -gt 0) {
    Write-Output "[TREE] FLAG dirty=$($gs.Count)"
    $gs | Select-Object -First 8 | ForEach-Object { Write-Output "  git: $_" }
  } else {
    $sb = @(git -C $repo status -sb)
    $head = [string]@($sb)[0]
    $div = 0
    if ($head -match '\[ahead (\d+), behind (\d+)\]') { $div = [int]$Matches[1] + [int]$Matches[2] }
    elseif ($head -match '\[ahead (\d+)\]') { $div = [int]$Matches[1] }
    elseif ($head -match '\[behind (\d+)\]') { $div = [int]$Matches[1] }
    if ($div -gt 0) {
      Write-Output "[TREE] FLAG clean=1 lock=0 diverged=$head"
      Write-Output '  note: remote moved (e.g. bm-c dispatch) or prior push rejected; NOT a local other-writer; next round first item = merge, then judge new orders'
    } else {
      Write-Output "[TREE] PASS clean=1 lock=0 $head"
    }
  }
}

# ---------------------------------------------------------------------------
# FALLBACK (script failed -> run these manually, same metrics):
#   group reads (D-20261001-03 canon) = git -C <group> fetch origin; git -C <group> show origin/main:<path>
#     $L = git show origin/main:cph4/evolution-ledger.md (split lines)
#   -> DEC fallback = row-owner tokens only: FIRST (?:D|C)-\d{8}-\d{2} token per '|'-prefixed
#      table row line (inline referenced tokens are INFO-only, never new rows - R1794
#      false-positive law, delivered R1795); diff vs state.json last_dec_tokens
#      (content-addressed per D-20260930-19(1); pure row-count forbidden per D-20260930-18;
#      report each new owner token's own row)
#   -> GORD fallback = full-file digest (SHA-256 over whole text, first 16 hex chars) + line/table-row/@BigDomain counts; any change anywhere flips the digest (D-20260927-05(2)).
#      NOTE: digest is over the origin/main blob text as served by git show (LF-normalized, BOM-stripped) - one-time rebase vs the pre-D-03 worktree-read baseline is expected at the mode switch.
#      report counts; compare with state.json baselines; git status --short;
#      Test-Path .git\index.lock. Paths: <repo>=domain\BigDomain, <group>=FluxGroup.
