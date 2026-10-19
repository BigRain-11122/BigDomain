# flush_export_R2053.py - byte-surgical export refresh for the R2053
# closeout: export_ts + the three ceo_face rows + the R2053 pair
# (narrative + tick) prepended to the results array + recomputed
# self_drive window numbers. Raw-text edits only (no full json.dumps
# rewrite - R1710 layout-drift disease); json.loads validates before
# write-back. The R2052 closeout appended its pair at the TAIL (out of
# order); this script only drops its stray tick row so the checker's
# exactly-one-tick law holds - its narrative row stays where it is.
# Pure ASCII source; CJK lives only in written data values.
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

with io.open(os.path.join(HERE, "export_consistency_patterns.json"),
             "r", encoding="utf-8") as _f:
    TICK_LABEL = json.load(_f)["tick_row_label"]

CURRENT = ("R2053 tech-queue FIFO head claim (R2052 reseed seed 5): the "
           "funnel per-account token ledger read face. AC-FAR1..AC-FAR8 "
           "pre-registered in the tech.md claim row BEFORE the code "
           "existed. funnel_daily.py grows account_ledger(day=None): a "
           "pure read over the append-only flows table grouped by account "
           "into granted / spent / outstanding in sorted-account order, "
           "the blank account as its own bucket (never merged into a "
           "named one), an honest negative overdraft that is never "
           "clamped to zero, the day-window vs lifetime vs honest-empty-"
           "day law, cross-restart byte-identical reads with zero writes, "
           "and bad day forms rejecting E_FN_BAD_ARGS before any row is "
           "touched. The sum of per-account outstanding closes the "
           "lifetime rollup total key-for-key. Suite "
           "test_funnel_account.py SUITE 8/8; wiring reconcile_all SUITES "
           "+ (funnel-account, 8 criteria); full battery RUNNER PASS 262/262 "
           "suites green + controls 7/7 343.5s = "
           "qa/reconcile-all-R2053.log; matrix regen 262 suites / 2206 "
           "criteria --check byte-identical; census pass=true; tech open "
           "9. Score 2.")

ARTIFACT = ("src/sandbox/funnel/funnel_daily.py account_ledger + "
            "src/sandbox/funnel/test_funnel_account.py + "
            "qa/funnel-account-R2053.log (SUITE PASS 8/8 AC-FAR1..8; "
            "RUNNER PASS 262/262 suites + controls 7/7 343.5s; "
            "suite-matrix 262/2206 byte-identical; census pass=true, "
            "2026-10-20)")

MILESTONE = ("FUNNEL 72h self-continuity acceptance <=10-31 (day-2 stamp "
             "on disk, day-3 stamp next); building-plan committee "
             "tri-report <=10-25 (plan doc ready); tech queue next head "
             "(funnel order SKU summary read face seed 6); weekly "
             "dead-doc deletion inside the 10-19..10-26 rectification "
             "window; QA charter W30 crawl; window <=48h (by 2026-10-22)")

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

head_old = '"results": [' + NL + '    [' + NL + '      "R2051",'
head_new = ('"results": [' + NL +
            '    [' + NL +
            '      "R2053",' + NL +
            '      "' + CURRENT + '"' + NL +
            '    ],' + NL +
            '    [' + NL +
            '      "2053",' + NL +
            '      "' + TICK_LABEL + '"' + NL +
            '    ],' + NL +
            '    [' + NL +
            '      "R2051",')
if text.count(head_old) != 1:
    sys.exit("FATAL: results head anchor hit count %d"
             % text.count(head_old))
text = text.replace(head_old, head_new, 1)

stray_tick = ('    ],' + NL +
              '    [' + NL +
              '      "2052",' + NL +
              '      "' + TICK_LABEL + '"' + NL +
              '    ],' + NL +
              '    [' + NL +
              '      "R2049",')
if text.count(stray_tick) == 1:
    text = text.replace(stray_tick,
                        '    ],' + NL + '    [' + NL +
                        '      "R2049",', 1)
else:
    sys.exit("FATAL: stray tick anchor hit count %d"
             % text.count(stray_tick))

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
if ids[:3] != ["R2053", "2053", "R2051"]:
    sys.exit("FATAL: results head order %r" % (ids[:3],))
if [r[0] for r in doc["results"]].count("2053") != 1:
    sys.exit("FATAL: tick row count not one")
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