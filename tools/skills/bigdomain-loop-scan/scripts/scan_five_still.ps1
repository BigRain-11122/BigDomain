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
  Write-Output "[STATE] PASS tick=$($st.tick) last_order=$($st.last_order) last_decision_rows=$($st.last_decision_rows) benchmarks_refreshed=$($st.benchmarks_refreshed) log_lines=$logN state_bytes=$bytes"
} catch {
  Write-Output '[STATE] FLAG parse_failed (other writer may be active - back off, read-only round)'
}

# --- [LEDGER] group evolution ledger (group-level, read-only) ---
try {
  $gt = Get-GroupFile 'cph4/evolution-ledger.md'
  $L = @(($gt.raw.TrimEnd("`r", "`n")) -split "\r?\n")
  $atbd = @($L | Select-String -SimpleMatch '@BigDomain')
  $conf = @($L | Select-String -Pattern '<<<<<<<|>>>>>>>')
  $pnums = @($L | Select-String -Pattern 'P-\d{4}-\d{2}-\d{2}-\d{2}' -AllMatches | ForEach-Object { $_.Matches } | ForEach-Object { $_.Value })
  $lastp = (@($pnums | Select-Object -Last 3) -join ',')
  if ($conf.Count -gt 0) {
    Write-Output "[LEDGER] FLAG lines=$($L.Count) atbd_rows=$($atbd.Count) conflict=$($conf.Count) lastp=$lastp"
  } else {
    Write-Output "[LEDGER] PASS lines=$($L.Count) atbd_rows=$($atbd.Count) conflict=$($conf.Count) lastp=$lastp"
  }
} catch { Write-Output '[LEDGER] FLAG read_failed' }

# --- [DEC] group decisions.md (content-addressed D-/C- token set diff vs state baseline; D-20260930-18/19: pure row-count is drift-prone and forbidden) ---
try {
  $gt = Get-GroupFile 'docs/decisions.md'
  $draw = $gt.raw
  $D = @(($draw.TrimEnd("`r", "`n")) -split "\r?\n")
  $tok = @([regex]::Matches($draw, '(?:D|C)-\d{8}-\d{2}') | ForEach-Object { $_.Value } | Sort-Object -Unique)
  $baseStr = ''
  if ($st -ne $null) { $baseStr = [string]$st.last_dec_tokens }
  if ($baseStr -eq '') {
    Write-Output "[DEC] FLAG rows=$($D.Count) known_tokens=$($tok.Count) baseline_missing (init state.json last_dec_tokens from full token set, then only diff)"
  } else {
    $baseTok = @($baseStr -split ',' | Where-Object { $_ })
    $newTok = @($tok | Where-Object { $baseTok -notcontains $_ })
    if ($newTok.Count -gt 0) {
      Write-Output "[DEC] FLAG rows=$($D.Count) known_tokens=$($tok.Count) new_tokens=$($newTok.Count) (content-addressed; row baseline=$($st.last_decision_rows) secondary)"
      foreach ($n in $newTok) {
        $hit = @($D | Select-String -SimpleMatch $n) | Select-Object -First 1
        $t = ''
        if ($hit) { $t = [string]$hit.Line; if ($t.Length -gt 300) { $t = $t.Substring(0, 300) + '...' } }
        Write-Output "  dec_new_tok $n : $t"
      }
    } else {
      Write-Output "[DEC] PASS rows=$($D.Count) known_tokens=$($tok.Count) (content-addressed; row baseline=$($st.last_decision_rows) secondary)"
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
try {
  $OO = [System.IO.File]::ReadAllLines((Join-Path $repo 'orders.md'), $utf8)
  $orows = @($OO | Where-Object { $_ -match '^\|\s*2026-' })
  $lastRow = [string]($orows | Select-Object -Last 1)
  $topTs = ''
  if ($lastRow -match '^\|\s*([^|]+?)\s*\|') { $topTs = $Matches[1].Trim() }
  if ($st -eq $null) {
    Write-Output "[ORD] INFO last=$topTs (state unavailable)"
  } elseif ($topTs -eq $st.last_order) {
    Write-Output "[ORD] PASS last=$topTs baseline=$($st.last_order)"
  } else {
    Write-Output "[ORD] FLAG last=$topTs baseline=$($st.last_order)"
    if ($lastRow.Length -gt 0) { Write-Output "  ord_last: $lastRow" }
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

# --- [QA] daily smoke evidence (group QA Smoke Test charter v1.0, orders L254 2026-09-28: daily crawl + qa/ evidence + 15h benchmark staleness cap) ---
try {
  $today = (Get-Date).ToString('yyyy-MM-dd')
  $qaDir = Join-Path $repo 'qa'
  $qaPng = 0; $qaLog = 0
  if (Test-Path $qaDir) {
    $qaPng = @(Get-ChildItem -LiteralPath $qaDir -Filter 'smoke-*.png' | Where-Object { $_.LastWriteTime.ToString('yyyy-MM-dd') -eq $today }).Count
    $qaLog = @(Get-ChildItem -LiteralPath $qaDir -Filter 'smoke-*.log' | Where-Object { $_.LastWriteTime.ToString('yyyy-MM-dd') -eq $today }).Count
  }
  $benchToday = ('' + $st.benchmarks_refreshed) -eq $today
  if ($qaPng -ge 1 -and $qaLog -ge 1 -and $benchToday) {
    Write-Output "[QA] PASS today_png=$qaPng today_log=$qaLog bench_today=$benchToday"
  } else {
    Write-Output "[QA] FLAG today_png=$qaPng today_log=$qaLog bench_today=$benchToday (charter daily crawl round due)"
  }
} catch { Write-Output '[QA] FLAG check_failed' }

# --- [HB] repo-root heartbeat.txt row freshness (standing law R532; detection face added R851 after 2nd recurrence R537..R540 + R849/R850; backfill precedent R541) ---
try {
  $hbPath = Join-Path $repo 'heartbeat.txt'
  $hbTick = -1
  if (Test-Path $hbPath) {
    $hbLast = @(Get-Content -LiteralPath $hbPath -Tail 1)
    if (@($hbLast).Count -gt 0 -and $hbLast[0] -match 'tick (\d+)') { $hbTick = [int]$Matches[1] }
  }
  $stTick = [int]$st.tick
  if ($hbTick -lt 0) {
    Write-Output '[HB] FLAG heartbeat_missing_or_unparsed'
  } elseif (($stTick - $hbTick) -gt 0) {
    Write-Output "[HB] FLAG hb_tick=$hbTick state_tick=$stTick lag=$($stTick - $hbTick) (heartbeat row debt: backfill due in this round closeout)"
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
#   -> DEC fallback = extract (?:D|C)-\d{8}-\d{2} token set from full text, diff vs state.json last_dec_tokens
#      (content-addressed per D-20260930-19(1); pure row-count forbidden per D-20260930-18; report each new token's row)
#   -> GORD fallback = full-file digest (SHA-256 over whole text, first 16 hex chars) + line/table-row/@BigDomain counts; any change anywhere flips the digest (D-20260927-05(2)).
#      NOTE: digest is over the origin/main blob text as served by git show (LF-normalized, BOM-stripped) - one-time rebase vs the pre-D-03 worktree-read baseline is expected at the mode switch.
#      report counts; compare with state.json baselines; git status --short;
#      Test-Path .git\index.lock. Paths: <repo>=domain\BigDomain, <group>=FluxGroup.
