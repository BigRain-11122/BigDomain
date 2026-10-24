"""Byte-surgical export refresh for the R2072 closeout.

Updates export_ts, the three ceo_face lines, prepends the R2072
narrative + tick row to results, and recomputes every derived counter
in BOTH blocks with the canonical caliber. Pure ASCII source.
"""

import io
import json
import os
import re
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
EXPORT = os.path.join(ROOT, "docs", "status-export.json")

sys.path.insert(0, HERE)
from check_export_consistency import recompute  # noqa: E402

with io.open(os.path.join(HERE, "export_consistency_patterns.json"),
             "r", encoding="utf-8") as _f:
    TICK_LABEL = json.load(_f)["tick_row_label"]

CURRENT = ("R2072: evidence logs now have one canonical single writer -"
           " every EOL form is normalised to LF, the bytes are encoded"
           " before any disk touch, the fresh file is classified and"
           " must read as the tee dialect or the writer raises, and the"
           " whole qa/ history can be classified read-only (1660 files:"
           " 1134 tee, 526 other) and repaired on the EOL axis only.")

ARTIFACT = ("src/os/evidence_writer.py + src/os/test_evidence_writer.py"
            " + src/os/evidence_census_R2072.py +"
            " qa/evidence-writer-census-R2072.log (SUITE PASS 8/8"
            " double-run stdout sha16"
            " d39cf3aa81ac525120cd548859250b1d7a2c56937c9ded3d7321478d798659c5;"
            " RUNNER PASS 280/280 suites + controls 7/7 222.4s ="
            " qa/reconcile-all-R2072.log; suite-matrix 280/2347"
            " byte-identical, 2026-10-24)")

MILESTONE = ("FUNNEL 72h self-continuity acceptance <=10-31; nine-company"
             " automation plan committee tri-report <=10-25; next window"
             " <=48h (by 2026-10-26)")

with io.open(EXPORT, "r", encoding="utf-8", newline="") as f:
    text = f.read()

NL = "\r\n" if "\r\n" in text else "\n"
now_iso = datetime.now().astimezone().isoformat(timespec="seconds")

pairs = [
    ('"export_ts": "(?:[^"\\\\]|\\\\.)*"',
     '"export_ts": "' + now_iso + '"'),
    ('"current": "(?:[^"\\\\]|\\\\.)*"',
     '"current": "' + CURRENT + '"'),
    ('"latest_artifact": "(?:[^"\\\\]|\\\\.)*"',
     '"latest_artifact": "' + ARTIFACT + '"'),
    ('"next_milestone": "(?:[^"\\\\]|\\\\.)*"',
     '"next_milestone": "' + MILESTONE + '"'),
]
for pat, rep in pairs:
    text, n = re.subn(pat, rep, text, count=1)
    if n != 1:
        sys.exit("FATAL: anchor hit %d for %r" % (n, pat[:50]))

head_old = '"results": [' + NL + '    [' + NL + '      "R2071",'
head_new = ('"results": [' + NL +
            '    [' + NL +
            '      "R2072",' + NL +
            '      "' + CURRENT + '"' + NL +
            '    ],' + NL +
            '    [' + NL +
            '      "2072",' + NL +
            '      "' + TICK_LABEL + '"' + NL +
            '    ],' + NL +
            '    [' + NL +
            '      "R2071",')
if text.count(head_old) != 1:
    sys.exit("FATAL: results head anchor count %d" % text.count(head_old))
text = text.replace(head_old, head_new, 1)

derived, _s, _e, _p = recompute()
keys = ("window", "window_days", "log_lines_in_window",
        "idle_fast_mention_lines", "no_pullable_mention_lines",
        "substantive_non_idle_mention_lines", "queue_main_open",
        "queue_tech_open", "queue_explore_open", "proposals_total",
        "proposals_open")
for key in keys:
    value = derived[key]
    if isinstance(value, str):
        pattern = r'"%s": "(?:[^"\\\\]|\\\\.)*"' % key
        repl = '"%s": "%s"' % (key, value)
    else:
        pattern = r'"%s": \d+' % key
        repl = '"%s": %d' % (key, value)
    text, n = re.subn(pattern, repl, text)
    if n < 1:
        sys.exit("FATAL: derived key %s not found" % key)
    print("derived %s -> %r (%d write sites)" % (key, value, n))

doc = json.loads(text)
ids = [r[0] for r in doc["results"]]
if ids[:3] != ["R2072", "2072", "R2071"]:
    sys.exit("FATAL: results head order %r" % (ids[:3],))
if ids.count("2072") != 1:
    sys.exit("FATAL: tick row count not one")
if doc["ceo_face"]["current"] != CURRENT:
    sys.exit("FATAL: ceo_face current not applied")
if doc["self_drive"]["queue_explore_open"] != derived["queue_explore_open"]:
    sys.exit("FATAL: self_drive derived mismatch")
if doc["queue_explore_open"] != derived["queue_explore_open"]:
    sys.exit("FATAL: top-level derived mismatch")

with io.open(EXPORT, "w", encoding="utf-8", newline="") as f:
    f.write(text)
print("EXPORT-OK tick_row=2072 results_head=%r" % (ids[:2],))