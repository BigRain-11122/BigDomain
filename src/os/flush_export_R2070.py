"""Byte-surgical export refresh for the R2070 closeout.

Updates export_ts, the three ceo_face lines, prepends the R2070
narrative + tick row to results, and recomputes every derived counter
in BOTH blocks (top level and self_drive) with the canonical caliber
from check_export_consistency. Raw-text edits only; json.loads
validates before write-back. Pure ASCII source.
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

CURRENT = ("R2070: the lobby chat mute window now has its boundary proven -"
           " a replayed message still answers as a duplicate inside a"
           " mute (no budget, no violation, no ledger row) while an"
           " expired replay is refused, and the mute counter only ever"
           " belongs to the rate gate.")

ARTIFACT = ("src/sandbox/lobby/test_chatmute_idem.py +"
            " qa/lobby-chat-mute-idem-R2070.log (SUITE PASS 8/8"
            " AC-CMI1..CMI8, double-run stdout sha16"
            " f7f1249d64c40c47; RUNNER PASS 278/278 suites + controls"
            " 7/7 217.5s = qa/reconcile-all-R2070.log; suite-matrix"
            " 278/2332 byte-identical; census DRIFT-CLEAN, 2026-10-24)")

MILESTONE = ("Reseed the tech queue back to >=10 real seeds (currently 4"
             " open after the merge) next round; FUNNEL 72h"
             " self-continuity acceptance <=10-31; nine-company"
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

head_old = '"results": [' + NL + '    [' + NL + '      "R2069",'
head_new = ('"results": [' + NL +
            '    [' + NL +
            '      "R2070",' + NL +
            '      "' + CURRENT + '"' + NL +
            '    ],' + NL +
            '    [' + NL +
            '      "2070",' + NL +
            '      "' + TICK_LABEL + '"' + NL +
            '    ],' + NL +
            '    [' + NL +
            '      "R2069",')
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
if ids[:3] != ["R2070", "2070", "R2069"]:
    sys.exit("FATAL: results head order %r" % (ids[:3],))
if ids.count("2070") != 1:
    sys.exit("FATAL: tick row count not one")
if doc["ceo_face"]["current"] != CURRENT:
    sys.exit("FATAL: ceo_face current not applied")
if doc["self_drive"]["queue_explore_open"] != derived["queue_explore_open"]:
    sys.exit("FATAL: self_drive derived mismatch")
if doc["queue_explore_open"] != derived["queue_explore_open"]:
    sys.exit("FATAL: top-level derived mismatch")

with io.open(EXPORT, "w", encoding="utf-8", newline="") as f:
    f.write(text)
print("EXPORT-OK tick_row=2070 results_head=%r" % (ids[:2],))