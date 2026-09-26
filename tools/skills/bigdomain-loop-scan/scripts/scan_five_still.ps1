# scan_five_still.ps1 - BigDomain OSLoop five-still opening scan (read-only)
# Emits one "[AREA] PASS|FLAG|INFO" line per face plus flagged-line details.
# The agent (not this script) interprets results against state.json baselines.
$ErrorActionPreference = 'Continue'
$utf8 = [System.Text.Encoding]::UTF8
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$repo = (Resolve-Path (Join-Path $here '..\..\..\..')).Path
$group = (Resolve-Path (Join-Path $repo '..\..')).Path

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
  $L = [System.IO.File]::ReadAllLines((Join-Path $group 'cph4\evolution-ledger.md'), $utf8)
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

# --- [DEC] group decisions.md (UTF-8 row count vs baseline) ---
try {
  $D = [System.IO.File]::ReadAllLines((Join-Path $group 'docs\decisions.md'), $utf8)
  $base = 0
  if ($st -ne $null) { $base = [int]$st.last_decision_rows }
  if ($D.Count -ne $base) {
    Write-Output "[DEC] FLAG rows=$($D.Count) baseline=$base"
    $from = [Math]::Max(0, $base)
    for ($i = $from; $i -lt $D.Count; $i++) {
      $t = $D[$i]; if ($t.Length -gt 300) { $t = $t.Substring(0, 300) + '...' }
      Write-Output "  dec_new_L$($i + 1): $t"
    }
  } else {
    Write-Output "[DEC] PASS rows=$($D.Count) baseline=$base"
  }
} catch { Write-Output '[DEC] FLAG read_failed' }

# --- [GORD] group docs/orders.md FULL-FILE scan (D-20260927-05(2) adopted 2026-09-27: active-order rows land in the head table region and mid-table, tail-only scan had blind spots) ---
try {
  $gordPath = Join-Path $group 'docs\orders.md'
  $gordRaw = [System.IO.File]::ReadAllText($gordPath, $utf8)
  $O = [System.IO.File]::ReadAllLines($gordPath, $utf8)
  $shaProv = [System.Security.Cryptography.SHA256]::Create()
  $sha16 = [System.BitConverter]::ToString($shaProv.ComputeHash($utf8.GetBytes($gordRaw))).Replace('-','').Substring(0,16)
  $shaProv.Dispose()
  $tbl = @($O | Select-String -Pattern '^\|\s*\d{2}-\d{2}')
  $atbd = @($O | Select-String -SimpleMatch '@BigDomain').Count
  $lastTbl = [string]($tbl | Select-Object -Last 1)
  $t = $lastTbl; if ($t.Length -gt 200) { $t = $t.Substring(0, 200) + '...' }
  $lastLine = [string]$O[$O.Count - 1]
  $u = $lastLine; if ($u.Length -gt 200) { $u = $u.Substring(0, 200) + '...' }
  Write-Output "[GORD] INFO lines=$($O.Count) tbl_rows=$($tbl.Count) atbd=$atbd sha16=$sha16"
  Write-Output "  gord_last_table_row: $t"
  Write-Output "  gord_last_line: $u"
} catch { Write-Output '[GORD] FLAG read_failed' }

# --- [ORD] own orders.md top timestamp vs baseline ---
try {
  $OO = [System.IO.File]::ReadAllLines((Join-Path $repo 'orders.md'), $utf8)
  $top = @($OO | Where-Object { $_ -match '^\|\s*2026-' } | Select-Object -First 1)
  $topTs = ''
  if ($top.Count -gt 0 -and $top[0] -match '^\|\s*(2026-\d{2}-\d{2}\s+\d{2}:\d{2})') { $topTs = $Matches[1] }
  if ($st -eq $null) {
    Write-Output "[ORD] INFO top=$topTs (state unavailable)"
  } elseif ($topTs -eq $st.last_order) {
    Write-Output "[ORD] PASS top=$topTs baseline=$($st.last_order)"
  } else {
    Write-Output "[ORD] FLAG top=$topTs baseline=$($st.last_order)"
    if ($top.Count -gt 0) { Write-Output "  ord_top: $($top[0])" }
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
    Write-Output "[TREE] PASS clean=1 lock=0 $(@($sb)[0])"
  }
}

# ---------------------------------------------------------------------------
# FALLBACK (script failed -> run these manually, same metrics):
#   $L=[IO.File]::ReadAllLines('<group>\cph4\evolution-ledger.md',[Text.Encoding]::UTF8)
#   $D=[IO.File]::ReadAllLines('<group>\docs\decisions.md',[Text.Encoding]::UTF8)
#   $O=[IO.File]::ReadAllLines('<group>\docs\orders.md',[Text.Encoding]::UTF8)
#   -> GORD fallback = full-file digest (SHA-256 over whole text, first 16 hex chars) + line/table-row/@BigDomain counts; any change anywhere flips the digest (D-20260927-05(2)).
#      report counts; compare with state.json baselines; git status --short;
#      Test-Path .git\index.lock. Paths: <repo>=domain\BigDomain, <group>=FluxGroup.
