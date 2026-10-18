# flush_export_R2025.py - byte-surgical export refresh for R2025
# closeout (export_ts + ceo_face three rows + tick row). Raw-text
# edits only (no full json.dumps rewrite - the R1710 layout-drift
# disease); json.loads validates before write-back. Pure ASCII
# source; the CJK tick-row label stays as the data it already is.
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
EXPORT = os.path.join(ROOT, "docs", "status-export.json")

with io.open(EXPORT, "r", encoding="utf-8", newline="") as f:
    text = f.read()

CURRENT = ("R2025: P3 explore queue FIFO head delivered: honorcert"
           " yearbooks_combined multi-year cross-restart"
           " persistence example window (the R2007 reseed;"
           " criteria AC-HYCP1..HYCP7 pre-registered in the"
           " explore.md claim row before code; AC-HYCP prefix +"
           " suite name + registry label all git-grep"
           " zero-occupancy verified). Suite"
           " test_honorcert_yearbooks_persist.py (suite-only"
           " round, four product files sha16 pinned unchanged):"
           " the anchor multi-year world (2026 board carol 12 /"
           " aaron 7 with the tie broken by account id / dave 3,"
           " plus a 2027 side board carol 5 / aaron 2, plus"
           " zero-earn 2025/2028 honest empty blocks; top-2"
           " grants both years) pins the scrambled-request"
           " combined envelope - the request (2028, 2026, 2025,"
           " 2027) canonicalizes to the ascending year axis,"
           " per-block values + totals pinned (overlap accounts"
           " carol/aaron counted once in distinct_accounts=2),"
           " every block == honor_yearbook minus disclaimer"
           " (single-source), double-call byte-identical;"
           " three-piece close (cl -> cv -> led, honorcert owns"
           " no storage) -> same two dbs + same cfg rebuild"
           " replays the combined envelope byte-identical"
           " (sha16 a47cbdb6230c12c7, table counts frozen);"
           " post-restart 2026 block live continuation (erin"
           " 20 pts enters rank 1, re-grant heals incrementally"
           " granted=1/already=1, aaron outside the top-2 slice"
           " keeps his yearbook row - permanent-certificate law"
           " across restart) with 2027/2025/2028 blocks frozen;"
           " post-restart 2027 continuation (frank 20 pts, the"
           " 2026 block byte-frozen across the 2027 grant ="
           " cross-read isolation); front-door gate survives the"
           " restart (6 non-iterable forms + 9 bad element forms"
           " + duplicate year all rejected E_HC_BAD_ARGS with"
           " zero honor_board calls); second restart stable"
           " (third stack reads byte-identical sha16"
           " 6f234d459d6e2b26, two-year subset law, ledger_tx=0"
           " zero-token law); hygiene pins. SUITE PASS 7/7"
           " double-run LF-normalized byte-identical sha16"
           " cee8e630e7bc27be = qa/honorcert-yearbooks-persist"
           "-R2025.log; reconcile_all wiring"
           " ledger-honorcert-yearbookspersist (240->241 suites,"
           " 2039->2046 criteria); RUNNER PASS 241/241 controls"
           " 7/7 198.7s zero regression = qa/reconcile-all"
           "-R2025.log; matrix regen 241/2046 green --check"
           " byte-identical 23414B; census DRIFT-CLEAN;"
           " fingerprint CLEAN domains=5; profile --daily"
           " --check PASS. Group faces: GORD tail new row"
           " 2026-10-18 17:20 CEO verdict (bm-d compute-brain"
           " hardware window: CPU E5-2696v2 x2 bought +"
           " topic-narrowing order, via bm-a, zero @BigDomain"
           " face) adjudicated knowledge-only, last_order"
           " advanced to 17:20; fold R555 pre-closeout honored"
           " (round-start gauge 77918B, tail-3 -> one rolling"
           " line, tokens embedded zero-loss gen555, archive +"
           " preop backup, post-fold same-round wording"
           " compression 78595->78252B honest note). Score 2"
           " (runnable suite artifact + battery green).")

ARTIFACT = ("src/sandbox/ledger/test_honorcert_yearbooks_persist.py"
            " (yearbooks_combined cross-restart persist suite,"
            " AC-HYCP1..HYCP7) + qa/honorcert-yearbooks-persist"
            "-R2025.log (SUITE 7/7 double-run byte-identical"
            " sha16 cee8e630e7bc27be) + qa/reconcile-all-R2025.log"
            " (RUNNER PASS 241/241) + docs/sandbox-suite-matrix.md"
            " regen (241 suites / 2046 criteria, 2026-10-18)")

MILESTONE = ("P3 explore next open heads (yearbooks subset-axis"
             " semantics [R2025 reseed], coverage dual-window"
             " month-roll, showcase stats gate-family"
             " cross-restart, proposal gate-family cross-restart,"
             " idem expiry-recharge billing, straddle"
             " netflow-exception, devboard month-window"
             " zero-listing boundary persist, devboard"
             " zero-listing gate-family cross-restart) - one per"
             " round at the established cadence, next within"
             " 48h; P1/P2 lines stay gated on external arrivals"
             " (radar OH list, R777 review file, CEO physical"
             " items for bootstrap)")

pairs = [
    ('"export_ts": "2026-10-18T18:15:00+08:00"',
     '"export_ts": "2026-10-18T18:46:00+08:00"'),
]
regex_pairs = [
    ('"current": "R2024: [^"]*"', '"current": "' + CURRENT + '"'),
    ('"latest_artifact": "[^"]*"',
     '"latest_artifact": "' + ARTIFACT + '"'),
    ('"next_milestone": "[^"]*"',
     '"next_milestone": "' + MILESTONE + '"'),
]

import re

for old, new in pairs:
    if text.count(old) != 1:
        sys.exit("FATAL: literal target hit count %d for %r"
                 % (text.count(old), old[:60]))
    text = text.replace(old, new)

for pat, rep in regex_pairs:
    new, n = re.subn(pat, rep, text, count=1)
    if n != 1:
        sys.exit("FATAL: regex target hit count %d for %r"
                 % (n, pat[:60]))
    text = new

tick_old = '"2024",\r\n   "OSLoop '
tick_new = '"2025",\r\n   "OSLoop '
if text.count(tick_old) != 1:
    sys.exit("FATAL: tick row anchor hit count %d"
             % text.count(tick_old))
text = text.replace(tick_old, tick_new)

json.loads(text)  # raises on bad json

with io.open(EXPORT, "w", encoding="utf-8", newline="") as f:
    f.write(text)

print("EXPORT-FLUSH-OK bytes=%d" % len(text.encode("utf-8")))
