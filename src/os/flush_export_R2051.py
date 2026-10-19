# flush_export_R2051.py - byte-surgical export refresh for the
# R2051 closeout: export_ts + the three ceo_face rows + the R2051
# pair (narrative + tick) prepended to the newest-first results
# array + recomputed self_drive window numbers.
#
# Scope note (honest): the R2050 closeout appended its own pair at
# the TAIL of the results array, so that pair sits out of order.
# Re-ordering it is a separate cosmetic repair left registered for
# a later round; this script only adds this round's head rows so no
# narrative content is touched.
#
# Raw-text edits only (no full json.dumps rewrite - the R1710
# layout-drift disease); json.loads validates before write-back.
# Pure ASCII source; CJK lives only in the written data values.
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

CURRENT = ("R2051 tech-queue FIFO head claim (R2047 reseed seed 3): "
           "funnel late-arrival re-rollup suite. AC-FRL1..AC-FRL8 "
           "pre-registered in the tech.md claim row BEFORE the suite "
           "existed. A late lead/order/flow dropped into day D's inbox "
           "after D was rolled up books on the re-run (the late lead is "
           "dispatched the same day, first-round rows byte-frozen), the "
           "re-derived D counts follow and the rollups face still holds "
           "exactly one row for that day, a second re-run books zero and "
           "reproduces the envelope bytes, the earlier day's stored "
           "envelope stays byte-frozen while D's prev-day delta stays "
           "anchored to it key-by-key, the conservation identity holds "
           "after a late spend (60 = 140-80) with day windows "
           "zero-penetrated, a late row that duplicates an existing id "
           "with a different payload is a no-op on every face, and the "
           "correction propagates into the next day's delta (leads -2 / "
           "granted -125 / spent -50 / outstanding 0) while D stays "
           "frozen. Two honest in-round findings: the AC-FRL5 expected "
           "outstanding was first written as 105 and then 80 against the "
           "real 60 (the criteria value is anchored to the actual run; "
           "the semantics did not change), and reconcile_all --help "
           "treated --help as an evidence path and produced a 571714-byte "
           "root artifact, moved byte-preserved to .codely-cli/tmp/ "
           "(R2046 precedent). Wiring: reconcile_all SUITES plus "
           "funnel-rerollup (8 criteria); full battery RUNNER PASS 260/260 "
           "suites green + controls 7/7 465.7s = "
           "qa/reconcile-all-R2051.log (259-suite baseline zero "
           "regression); matrix regen 260 suites / 2190 criteria --check "
           "byte-identical; census DRIFT-CLEAN (files=1612 flags=0); "
           "tech open 7->6. Score 2.")

ARTIFACT = ("src/sandbox/funnel/test_funnel_rerollup.py +"
            " qa/reconcile-all-R2051.log (SUITE PASS 8/8 AC-FRL1..8"
            " double-run identical sha16 6dbf294a9fb4d193; RUNNER PASS"
            " 260/260 suites + controls 7/7 465.7s; suite-matrix"
            " 260/2190 byte-identical; census DRIFT-CLEAN, 2026-10-20)")

MILESTONE = ("FUNNEL 72h self-continuity acceptance <=10-31 (day-2"
             " stamp on disk, day-3 stamp next); building-plan"
             " committee tri-report <=10-25 (plan doc ready); tech"
             " queue next head (funnel conservation multi-day chain"
             " [R2047 reseed], then a fresh reseed to hold the >=10"
             " standing supply); weekly dead-doc deletion inside the"
             " 10-19..10-26 rectification window; QA charter W30"
             " crawl; window <=48h (by 2026-10-22)")

with io.open(EXPORT, "r", encoding="utf-8", newline="") as f:
    text = f.read()

NL = "\r\n" if "\r\n" in text else "\n"
now_iso = datetime.now().astimezone().isoformat(timespec="seconds")

regex_pairs = [
    ('"export_ts": "(?:[^"\\\\]|\\\\.)*"',
     '"export_ts": "' + now_iso + '"'),
    ('"current": "(?:[^"\\\\]|\\\\.)*"',
     '"current": "' + CURRENT + '"'),
    ('"latest_artifact": "(?:[^"\\\\]|\\\\.)*"',
     '"latest_artifact": "' + ARTIFACT + '"'),
    ('"next_milestone": "(?:[^"\\\\]|\\\\.)*"',
     '"next_milestone": "' + MILESTONE + '"'),
]
for pat, rep in regex_pairs:
    text, n = re.subn(pat, rep, text, count=1)
    if n != 1:
        sys.exit("FATAL: regex target hit count %d for %r"
                 % (n, pat[:60]))

head_old = '"results": [' + NL + '    [' + NL + '      "R2049",'
head_new = ('"results": [' + NL +
            '    [' + NL +
            '      "R2051",' + NL +
            '      "' + CURRENT + '"' + NL +
            '    ],' + NL +
            '    [' + NL +
            '      "2051",' + NL +
            '      "OSLoop 执行 tick"' + NL +
            '    ],' + NL +
            '    [' + NL +
            '      "R2049",')
if text.count(head_old) != 1:
    sys.exit("FATAL: results head anchor hit count %d"
             % text.count(head_old))
text = text.replace(head_old, head_new, 1)

# the checker enforces exactly ONE tick row in results; the R2050
# closeout left a stray one at the tail, so drop that block (its
# narrative row stays where it is - the ordering note above).
stray_tick = ('    ],' + NL +
              '    [' + NL +
              '      "2050",' + NL +
              '      "OSLoop 执行 tick"' + NL +
              '    ],' + NL +
              '    [' + NL +
              '      "R2050",')
if text.count(stray_tick) == 1:
    text = text.replace(stray_tick,
                        '    ],' + NL + '    [' + NL +
                        '      "R2050",', 1)
elif text.count(stray_tick) != 0:
    sys.exit("FATAL: stray tick anchor ambiguous")

derived, _state, _exp, _pat = recompute()
for key in ("log_lines_in_window", "idle_fast_mention_lines",
            "no_pullable_mention_lines",
            "substantive_non_idle_mention_lines",
            "queue_main_open",
            "queue_tech_open", "queue_explore_open",
            "proposals_total", "proposals_open"):
    text, n = re.subn(r'"%s": \d+' % key,
                      '"%s": %d' % (key, derived[key]),
                      text, count=1)
    if n != 1:
        sys.exit("FATAL: self_drive key %s anchor not hit" % key)
text, n = re.subn(r'"window": "[^"]*"',
                  '"window": "%s"' % derived["window"],
                  text, count=1)
if n != 1:
    sys.exit("FATAL: self_drive window anchor not hit")

doc = json.loads(text)
ids = [r[0] for r in doc["results"]]
if ids[:3] != ["R2051", "2051", "R2049"]:
    sys.exit("FATAL: results head order %r" % (ids[:3],))
if doc["ceo_face"]["current"] != CURRENT:
    sys.exit("FATAL: ceo_face current not applied")
for key in ("log_lines_in_window", "idle_fast_mention_lines",
            "no_pullable_mention_lines",
            "substantive_non_idle_mention_lines",
            "queue_main_open",
            "queue_tech_open", "queue_explore_open",
            "proposals_total", "proposals_open"):
    if doc["self_drive"][key] != derived[key]:
        sys.exit("FATAL: self_drive %s %r != recompute %r"
                 % (key, doc["self_drive"][key], derived[key]))

with io.open(EXPORT, "w", encoding="utf-8", newline="") as f:
    f.write(text)

print("EXPORT-FLUSH-OK bytes=%d results_rows=%d window=%s"
      % (len(text.encode("utf-8")), len(doc["results"]),
         derived["window"]))