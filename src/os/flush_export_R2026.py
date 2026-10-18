# flush_export_R2026.py - byte-surgical export refresh for R2026
# closeout (export_ts + ceo_face three rows + tick row). Raw-text
# edits only (no full json.dumps rewrite - the R1710 layout-drift
# disease); json.loads validates before write-back. Pure ASCII
# source; the CJK tick-row label stays as the data it already is.
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
EXPORT = os.path.join(ROOT, "docs", "status-export.json")

with io.open(EXPORT, "r", encoding="utf-8", newline="") as f:
    text = f.read()

CURRENT = ("R2026: P3 explore queue FIFO head delivered: honorcert"
           " yearbooks_combined subset-axis semantics example"
           " window (the R2025 reseed; criteria AC-HYS1..HYS7"
           " pre-registered in the explore.md claim row before"
           " code; AC-HYS prefix + suite name + registry label"
           " all git-grep zero-occupancy verified). Suite"
           " test_honorcert_yearbook_subsetaxis.py (suite-only"
           " round, four product files sha16 pinned unchanged):"
           " the strictly descending request (2028, 2027, 2026,"
           " 2025) canonicalizes to the ascending year axis with"
           " the full envelope byte-identical to the ascending"
           " same-set request (sha16 a47cbdb6230c12c7); the"
           " single-year family (2026 block == honor_yearbook"
           " minus disclaimer, totals pinned; the 2025 single"
           " empty year honest); the two-year family (descending"
           " pair byte-identical to the ascending request,"
           " mixed empty+content [2026, 2028], overlap accounts"
           " counted once); the all-empty-years family ((2025,"
           " 2028) honest empty blocks with zero totals and"
           " stable key sets); seven input forms (ascending list,"
           " descending tuple, two scrambled tuples, set,"
           " frozenset, one-pass generator) all fold to one"
           " byte-identical envelope - the ascending sort absorbs"
           " the per-process set iteration order drift, pinning"
           " the zero insertion-order-key law; single-source cross"
           " over the whole family; pure-read law with ledger_tx=0"
           " and frozen table counts; hygiene pins. SUITE PASS"
           " 7/7 double-run LF-normalized byte-identical sha16"
           " c2e44922d52f8397 = qa/honorcert-subsetaxis-R2026.log;"
           " reconcile_all wiring ledger-honorcert"
           "-yearbooksubsetaxis (241->242 suites, 2046->2053"
           " criteria); RUNNER PASS 242/242 controls 7/7 234.5s"
           " zero regression = qa/reconcile-all-R2026.log; matrix"
           " regen 242/2053 green --check byte-identical 23526B;"
           " census --update-baseline + --check DRIFT-CLEAN"
           " flags=0 files=1561 tee=1037 baselined=524;"
           " fingerprint CLEAN domains=5; profile DRIFT-CLEAN"
           " (registry ALIGNED 242) + --check byte-identical"
           " PASS + --daily --check PASS. Group faces: GORD tail"
           " new row 2026-10-18 19:01 CEO purchase report (bm-d"
           " hardware window: RAM sticks x16 at 123 CNY = 1968"
           " CNY backfill, total purchased 3303 CNY closed, via"
           " bm-a) adjudicated knowledge-only zero @BigDomain"
           " face, last_order advanced to 19:01; fold R556"
           " pre-closeout honored (round-start gauge 78252B,"
           " tail-3 -> one rolling line, 80 tokens embedded"
           " zero-loss gen556, archive + preop backup, post =="
           " predicted 78214B). Explore consume-1 reseed-1"
           " (yearbooks zero-earn boundary persist seed). Score 2"
           " (runnable suite artifact + battery green).")

ARTIFACT = ("src/sandbox/ledger/"
            "test_honorcert_yearbook_subsetaxis.py (yearbooks"
            "_combined subset-axis semantics suite, AC-HYS1.."
            "HYS7) + qa/honorcert-subsetaxis-R2026.log (SUITE 7/7"
            " double-run byte-identical sha16 c2e44922d52f8397)"
            " + qa/reconcile-all-R2026.log (RUNNER PASS 242/242)"
            " + docs/sandbox-suite-matrix.md regen (242 suites /"
            " 2053 criteria, 2026-10-18)")

MILESTONE = ("P3 explore next open heads (yearbooks zero-earn"
             " boundary world cross-restart persist [R2026"
             " reseed], coverage dual-window month-roll, showcase"
             " stats gate-family cross-restart, proposal"
             " gate-family cross-restart, idem expiry-recharge"
             " billing, straddle netflow-exception, devboard"
             " month-window zero-listing boundary persist,"
             " devboard zero-listing gate-family cross-restart)"
             " - one per round at the established cadence, next"
             " within 48h; P1/P2 lines stay gated on external"
             " arrivals (radar OH list, R777 review file, CEO"
             " physical items for bootstrap)")

pairs = [
    ('"export_ts": "2026-10-18T18:46:00+08:00"',
     '"export_ts": "2026-10-18T19:18:00+08:00"'),
]
regex_pairs = [
    ('"current": "R2025: [^"]*"', '"current": "' + CURRENT + '"'),
    ('"latest_artifact": "[^"]*"',
     '"latest_artifact": "' + ARTIFACT + '"'),
    ('"next_milestone": "[^"]*"',
     '"next_milestone": "' + MILESTONE + '"'),
]

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

tick_old = '"2025",\r\n   "OSLoop '
tick_new = '"2026",\r\n   "OSLoop '
if text.count(tick_old) != 1:
    sys.exit("FATAL: tick row anchor hit count %d"
             % text.count(tick_old))
text = text.replace(tick_old, tick_new)

json.loads(text)  # raises on bad json

with io.open(EXPORT, "w", encoding="utf-8", newline="") as f:
    f.write(text)

print("EXPORT-FLUSH-OK bytes=%d" % len(text.encode("utf-8")))
