# flush_export_R2044.py - byte-surgical export refresh for the
# R2044 closeout (export_ts + ceo_face three rows + results
# narrative prepend + tick row + self_drive window line). Raw-
# text edits only (no full json.dumps rewrite - the R1710
# layout-drift disease); json.loads validates before write-back.
# The self_drive window line is written from the shared machine
# caliber (check_export_consistency.recompute) so flush and check
# stay one caliber. Pure ASCII source; CJK lives only in the
# loaded/written data file.
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
EXPORT = os.path.join(ROOT, "docs", "status-export.json")

sys.path.insert(0, HERE)
from check_export_consistency import recompute  # noqa: E402

with io.open(EXPORT, "r", encoding="utf-8", newline="") as f:
    text = f.read()

CURRENT = ("R2044: P3 explore FIFO head claim delivered:"
           " statsmonth double-straddle pair netflow identity"
           " exception-deepening cross-restart suite (the R2043"
           " reseed; criteria AC-SMDS1..AC-SMDS7 pre-registered"
           " in the explore.md claim row before code, AC-SMDS"
           " prefix + suite + registry names git-grep"
           " zero-occupancy verified). Suite"
           " test_showcase_statsmonth_straddle2persist.py"
           " (suite-only round, three product files sha256"
           " pinned unchanged): the double straddle core - TWO"
           " previous-month fixture places (tower, bridge)"
           " retracted through the real path in the current"
           " month read {0,2,0} in the current-month window"
           " where the identity displayed_now == places -"
           " retracts honestly BREAKS (0 != 0-2, the deepened"
           " multi-pair exception) while the full board keeps"
           " the per-row identity ({3,2,1}: 1 == 3-2); after"
           " the restart the two freed slots re-place one at a"
           " time: the first re-place reads {1,2,1} (1 != 1-2,"
           " the leading-retract multi-pair variant, full board"
           " {4,2,2}: 2 == 4-2) and the second re-place reads"
           " {2,2,2} (2 != 2-2) - the closed-yet-still-broken"
           " terminal shape: even after BOTH cross-month pairs"
           " are fully re-placed inside the window the window"
           " identity stays broken forever, because the window"
           " can never see the previous-month original places"
           " that the full board pairs ({5,2,3}: 3 == 5-2) - the"
           " identity is a full-board law, never a month-window"
           " law, now pinned in the multi-pair closure shape"
           " (the R2018/R2019/R2043 ruling chain's multi-pair"
           " face). Old-month window byte-frozen through all"
           " mutations (record-time law); view_cur [] ->"
           " [tower] -> [tower,bridge] in event order; chronicle"
           " [p,p,p,r,r] -> [p,p,p,r,r,p] -> [p,p,p,r,r,p,p];"
           " tour [harbor] -> [harbor,tower] -> [harbor,tower,"
           " bridge] (tail re-join, R2019 law); two full-stack"
           " restarts replay the 13-form family byte-identically"
           " (the {0,2,0} double-retract state and the {2,2,2}"
           " terminal state both persist); read storm x2 counts"
           " flat (showcases 3, events 9, ledger_tx 0); gate"
           " family 9 bad windows + 4 bad limits + the"
           " limit-gate-first order probe identical pre/post"
           " restart; cross-showcase not-displayed probe zero"
           " rows; zero-token law throughout. SUITE PASS 7/7"
           " first-run clean + double-run stdout byte-identical"
           " sha16 a2424a025940221b = qa/showcase-statsmonth-"
           " straddle2-R2044.log; reconcile_all wiring ledger-"
           " showcase-statsmonth-straddle2-persist (254->255"
           " suites, criteria 2145->2152); RUNNER PASS 255/255"
           " suites green + reconcile controls 7/7 223.6s zero"
           " regression = qa/reconcile-all-R2044.log; matrix"
           " regen 255/2152 green=255/255 --check byte-identical"
           " 24949B; census --update-baseline + --check"
           " DRIFT-CLEAN; fingerprint CLEAN domains=5; profile"
           " compare DRIFT-FLAG (minors-wiring 19.3s vs the"
           " stale R2019 anchor 12.4s; same suite, same criteria"
           " 70, same all-green profile, the R2043 battery ran"
           " the same suite at 10.4s = environment wall-clock"
           " variance on a shared box, not a payload"
           " regression) -> isolated attribution per the R2018"
           " precedent -> --update-baseline re-anchor to the"
           " fresh R2044 battery log (255 suites) -> compare"
           " DRIFT-CLEAN 255/0 + --check + --daily --check all"
           " PASS. Explore consume-1 reseed-1 (post-closure"
           " re-retraction third-shape seed). Score 2 (runnable"
           " suite artifact + battery green).")

ARTIFACT = ("qa/showcase-statsmonth-straddle2-R2044.log +"
            " src/sandbox/ledger/"
            "test_showcase_statsmonth_straddle2persist.py"
            " (SUITE 7/7 double-run identical sha16"
            " a2424a025940221b, RUNNER 255/255 green,"
            " 2026-10-19)")

MILESTONE = ("FUNNEL 72h self-continuity acceptance <=10-31"
             " (day-1 stamp qa/funnel-daily-20261019.log on"
             " disk, day-2/day-3 stamps next); building-plan"
             " committee tri-report <=10-25 (plan doc ready);"
             " P3 explore queue next heads (post-closure"
             " re-retraction third-shape [R2044 reseed],"
             " apimarket zero-listing boundary persist,"
             " honorcert grant-gate persist, coverage"
             " month-roll gate family); window <=48h (by"
             " 2026-10-21)")

pairs = [
    ('"export_ts": "2026-10-19T09:08:14+08:00"',
     '"export_ts": "2026-10-19T09:24:00+08:00"'),
    ('"log_lines_in_window": 8,',
     '"log_lines_in_window": %d,' % 9),
]
regex_pairs = [
    ('"current": "R2043: [^"]*"', '"current": "' + CURRENT + '"'),
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

# tick row: the only bare "2043" literal (narratives carry the
# R prefix); anchor includes the tick-row label head so a future
# stray "2043" can never mis-target
tick_old = '"2043",\n      "OSLoop '
tick_new = '"2044",\n      "OSLoop '
if text.count(tick_old) != 1:
    sys.exit("FATAL: tick row anchor hit count %d"
             % text.count(tick_old))
text = text.replace(tick_old, tick_new)

# results narrative prepend: insert the R2044 row ahead of the
# R2043 row at the head of the results container
head_old = '"results": [\n    [\n      "R2043",'
head_new = ('"results": [\n    [\n      "R2044",\n      "'
            + CURRENT + '"\n    ],\n    [\n      "R2043",')
if text.count(head_old) != 1:
    sys.exit("FATAL: results head anchor hit count %d"
             % text.count(head_old))
text = text.replace(head_old, head_new)

# shared-caliber sanity: the recomputed window line must equal
# what this flush just wrote
derived, _state, _export, _pat = recompute()
doc = json.loads(text)
if doc["self_drive"]["log_lines_in_window"] != derived["log_lines_in_window"]:
    sys.exit("FATAL: self_drive window line %r != recompute %r"
             % (doc["self_drive"]["log_lines_in_window"],
                derived["log_lines_in_window"]))
for key in ("queue_main_open", "queue_tech_open",
            "queue_explore_open", "proposals_total",
            "proposals_open", "idle_fast_mention_lines",
            "no_pullable_mention_lines"):
    if doc["self_drive"][key] != derived[key]:
        sys.exit("FATAL: self_drive %s %r != recompute %r"
                 % (key, doc["self_drive"][key], derived[key]))

json.loads(text)  # raises on bad json

with io.open(EXPORT, "w", encoding="utf-8", newline="") as f:
    f.write(text)

print("EXPORT-FLUSH-OK bytes=%d results_rows=%d"
      % (len(text.encode("utf-8")), len(doc["results"])))
