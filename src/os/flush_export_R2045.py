# flush_export_R2045.py - byte-surgical export refresh for the
# R2045 closeout (export_ts + ceo_face three rows + results
# narrative prepend + tick row + self_drive window numbers).
# Raw-text edits only (no full json.dumps rewrite - the R1710
# layout-drift disease); json.loads validates before write-back.
# The self_drive numbers are written from the shared machine
# caliber (check_export_consistency.recompute) so flush and
# check stay one caliber. Pure ASCII source; CJK lives only in
# the written data values.
import io
import json
import os
import re
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normcase(os.path.normpath(
    os.path.join(HERE, "..", "..")))
EXPORT = os.path.join(ROOT, "docs", "status-export.json")

sys.path.insert(0, HERE)
from check_export_consistency import recompute  # noqa: E402

CURRENT = ("R2045: crashed-round orphan payload takeover "
           "closeout delivered end-to-end: apimarket "
           "dev_sales_board month-window zero-listing boundary "
           "cross-restart suite (the R2023-reseed FIFO head; "
           "criteria AC-AMWZB1..AMWZB7 pre-registered in the "
           "explore.md claim row by the prior session before "
           "code, three names git-grep zero-occupancy verified; "
           "the prior session died pre-closeout leaving one "
           "undecodable-dialect RUNNER artifact - this round "
           "took the payload over per the R1924/R1730 "
           "precedents). Takeover verification: suite re-run "
           "double-run stdout byte-identical sha16 "
           "708b9736ef075c1e cross-checked MATCH against the "
           "orphan evidence log (takeover evidence-chain "
           "closure). Suite-only round (apimarket.py, apidev.py, "
           "ledger.py + both shipped config.json sha256 pinned "
           "unchanged): zero-listing boundary world (ledger + "
           "devkeys populated, market three tables at zero rows) "
           "with five honest-empty read forms (default two-key "
           "envelope + four window reads carrying the window "
           "echo key, out-month included); the 14 bad-window "
           "gate family rejecting E_AM_BAD_WINDOW on the empty "
           "data face before any read (gate independent of the "
           "data face); full-stack close (am->dk->metered->led) "
           "then same-db same-cfg rebuild byte-identical on all "
           "five forms (zero in-memory drift); post-restart "
           "first listing dense window-face join (record-month "
           "window carries listing_count, every other month "
           "keeps the honest dense zero row, board rows == "
           "listing rows zero phantom); post-restart first "
           "purchase NOV-window zero-cache recompute "
           "{usr:ada,0,1,10,7,3} (70/30 default integer split) "
           "with the OCT listing window byte-frozen (record-time "
           "dual-family law, zero cross-window leakage) and the "
           "spend/dev-share tx pair present in the ledger_tx id "
           "set (cross-db provenance); conservation gross == dev "
           "+ platform on every read form; third instance "
           "byte-identical (liveness-written world survives the "
           "second restart); pure-read law (read battery leaves "
           "digests + ledger_tx constant); gate family code "
           "vectors identical across both restarts. reconcile_all "
           "wiring ledger-apimarket-devboardmonthboundary (255->"
           "256 suites, criteria 2152->2159); RUNNER PASS 256/256 "
           "suites green + controls 7/7 289.0s zero regression = "
           "qa/reconcile-all-R2045.log (undecodable dialect "
           "artifact replaced by a python single-writer utf-8 LF "
           "log, R1924/R2033 dialect law); matrix regen 256/2159 "
           "green=256/256 --check byte-identical 25072B; census "
           "--update-baseline + --check DRIFT-CLEAN; fingerprint "
           "CLEAN domains=5; profile compare DRIFT-FLAG on five "
           "small suites (funnel, ledger-clawback, pay, "
           "reconcile-daily-census, ugc - +2..5s over the 2.0s "
           "absolute floor on sub-3s suites = environment "
           "wall-clock variance on a shared box, not a payload "
           "regression, total-shared within slack) -> re-anchored "
           "per the R2044 precedent to the fresh R2045 battery "
           "log (256 suites) -> compare DRIFT-CLEAN 256/0 + "
           "--check + --daily --check all PASS. DEC receipts: "
           "D-20261019-05 acknowledged (HQ execution face), "
           "D-20261019-06 acknowledged (our D-20261019-04 port "
           "receipt already landed at R2031). fold R573 "
           "pre-closeout honored (gauge 76832B over-budget -> "
           "tail-5 folded to one rolling line, 314 tokens "
           "embedded zero-loss). Explore consume-1 reseed-1 "
           "(three-month straddle seed). Score 2 (runnable "
           "suite artifact + battery green).")

ARTIFACT = ("qa/apimarket-devboardmonthboundary-R2045.log +"
            " src/sandbox/ledger/"
            "test_apimarket_devboardmonthboundarypersist.py"
            " (SUITE 7/7 double-run identical sha16"
            " 708b9736ef075c1e, RUNNER 256/256 green,"
            " 2026-10-19)")

MILESTONE = ("FUNNEL 72h self-continuity acceptance <=10-31"
             " (day-1 stamp qa/funnel-daily-20261019.log on"
             " disk, day-2/day-3 stamps next); building-plan"
             " committee tri-report <=10-25 (plan doc ready);"
             " P3 explore queue next heads (apimarket"
             " zero-listing gate-family restart same-code"
             " [R2024 seed], honorcert grant-gate persist,"
             " coverage month-roll gate family, apimarket"
             " three-month straddle [R2045 reseed]); window"
             " <=48h (by 2026-10-21)")

with io.open(EXPORT, "r", encoding="utf-8", newline="") as f:
    text = f.read()

now_iso = datetime.now().astimezone().isoformat(
    timespec="seconds")

regex_pairs = [
    ('"export_ts": "[^"]*"',
     '"export_ts": "' + now_iso + '"'),
    ('"current": "R2044[^"]*"', '"current": "' + CURRENT + '"'),
    ('"latest_artifact": "[^"]*"',
     '"latest_artifact": "' + ARTIFACT + '"'),
    ('"next_milestone": "[^"]*"',
     '"next_milestone": "' + MILESTONE + '"'),
]
for pat, rep in regex_pairs:
    text, n = re.subn(pat, rep, text, count=1)
    if n != 1:
        sys.exit("FATAL: regex target hit count %d for %r"
                 % (n, pat[:60]))

# tick row: the only bare "2044" literal (narratives carry the
# R prefix); anchor includes the tick-row label head so a future
# stray "2044" can never mis-target
tick_old = '"2044",\n      "OSLoop '
tick_new = '"2045",\n      "OSLoop '
if text.count(tick_old) != 1:
    sys.exit("FATAL: tick row anchor hit count %d"
             % text.count(tick_old))
text = text.replace(tick_old, tick_new)

# results narrative prepend: insert the R2045 row ahead of the
# R2044 row at the head of the results container
head_old = '"results": [\n    [\n      "R2044",'
head_new = ('"results": [\n    [\n      "R2045",\n      "'
            + CURRENT + '"\n    ],\n    [\n      "R2044",')
if text.count(head_old) != 1:
    sys.exit("FATAL: results head anchor hit count %d"
             % text.count(head_old))
text = text.replace(head_old, head_new)

# shared-caliber self_drive numbers: write every machine-derived
# value, then verify the whole face against the recompute
derived, _state, _exp, _pat = recompute()
for key in ("log_lines_in_window", "idle_fast_mention_lines",
            "no_pullable_mention_lines", "queue_main_open",
            "queue_tech_open", "queue_explore_open",
            "proposals_total", "proposals_open"):
    text, n = re.subn(r'"%s": \d+' % key,
                      '"%s": %d' % (key, derived[key]),
                      text, count=1)
    if n != 1:
        sys.exit("FATAL: self_drive key %s anchor not hit"
                 % key)
text, n = re.subn(r'"window": "[^"]*"',
                  '"window": "%s"' % derived["window"],
                  text, count=1)
if n != 1:
    sys.exit("FATAL: self_drive window anchor not hit")

# shared-caliber sanity: the doc must equal the recompute
doc = json.loads(text)
for key in ("log_lines_in_window", "idle_fast_mention_lines",
            "no_pullable_mention_lines", "queue_main_open",
            "queue_tech_open", "queue_explore_open",
            "proposals_total", "proposals_open"):
    if doc["self_drive"][key] != derived[key]:
        sys.exit("FATAL: self_drive %s %r != recompute %r"
                 % (key, doc["self_drive"][key], derived[key]))

json.loads(text)  # raises on bad json

with io.open(EXPORT, "w", encoding="utf-8", newline="") as f:
    f.write(text)

print("EXPORT-FLUSH-OK bytes=%d results_rows=%d window=%s"
      % (len(text.encode("utf-8")), len(doc["results"]),
         derived["window"]))
