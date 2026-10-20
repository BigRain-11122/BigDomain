# flush_export_R2057.py - byte-surgical export refresh for the R2057
# closeout: export_ts + the three ceo_face rows + the R2057 pair
# (narrative + tick) prepended to the results array + recomputed
# self_drive window numbers. Raw-text edits only (no full json.dumps
# rewrite - R1710 layout-drift disease); json.loads validates before
# write-back. Pure ASCII source; CJK lives only in written data values.
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

CURRENT = ("R2057 P2 tech-queue FIFO head (R2052 reseed): funnel inbox "
           "non-JSON noise classification law, delivered by a crashed "
           "predecessor round and re-verified live before adoption "
           "(AC-FIN1..AC-FIN8 pre-registered before the code existed). "
           "An inbox entry is a regular file with the exact lower-case "
           ".json suffix; everything else - other suffixes, bare names, "
           "directories including one literally named fake.json - is "
           "junk, skipped unopened and never recursed into. A file that "
           "is in contract but cannot be honoured (bad JSON text, "
           "invalid UTF-8, empty file, decoded value not an object) "
           "rejects the whole ring with FunnArgError before any row is "
           "written and no decoder error escapes the library boundary. "
           "Suite SUITE 8/8 first-run green, double-run stdout "
           "byte-identical; wiring reconcile_all SUITES (funnel-inbox, "
           "8); full battery RUNNER PASS 266/266 suites + controls 7/7 "
           "277.6s; matrix 266/2238 --check byte-identical; census "
           "DRIFT-CLEAN 1628/0; fold R579 pre-closeout (74761B). Queue "
           "hygiene: duplicate seed merged, one true-live reseed, 10 "
           "open. Score 2.")

ARTIFACT = ("src/sandbox/funnel/test_funnel_inbox.py + "
            "qa/reconcile-all-R2057.log (SUITE PASS 8/8 AC-FIN1..8 "
            "first-run green, double-run sha16 1F3CF16200C7D0E1; RUNNER "
            "PASS 266/266 suites + controls 7/7 277.6s; suite-matrix "
            "266/2238 byte-identical; census DRIFT-CLEAN 1628/0, "
            "2026-10-20)")

MILESTONE = ("FUNNEL 72h self-continuity acceptance <=10-31 (day-3 "
             "stamp next round); building-plan committee tri-report "
             "<=10-25 (plan doc ready); next tech head = funnel route "
             "distribution read face cross-restart persistence; weekly "
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

head_old = '"results": [' + NL + '    [' + NL + '      "R2056",'
head_new = ('"results": [' + NL +
            '    [' + NL +
            '      "R2057",' + NL +
            '      "' + CURRENT + '"' + NL +
            '    ],' + NL +
            '    [' + NL +
            '      "2057",' + NL +
            '      "' + TICK_LABEL + '"' + NL +
            '    ],' + NL +
            '    [' + NL +
            '      "R2056",')
if text.count(head_old) != 1:
    sys.exit("FATAL: results head anchor hit count %d"
             % text.count(head_old))
text = text.replace(head_old, head_new, 1)

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
if ids[:3] != ["R2057", "2057", "R2056"]:
    sys.exit("FATAL: results head order %r" % (ids[:3],))
if [r[0] for r in doc["results"]].count("2057") != 1:
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

print("EXPORT-FLUSH-OK bytes=%d results_rows=%d window=%s tick=%s"
      % (len(text.encode("utf-8")), len(doc["results"]),
         derived["window"], doc["self_drive"].get("tick")))