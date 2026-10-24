"""Byte-surgical export refresh for the R2088 closeout.

Updates export_ts, the three ceo_face lines, prepends the R2088
narrative row to results, and recomputes every derived counter in
BOTH blocks with the canonical caliber. Pure ASCII source.
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

CURRENT = ("R2088: the developer API marketplace now has a post-sale"
           " remedy door - a buyer can refund a purchase, the four ledger"
           " legs put buyer, seller and both pools back to their"
           " pre-purchase balances exactly, a refunded unit returns to the"
           " shelf so another buyer can take it, and a seller who already"
           " spent the proceeds fails the refund closed with zero tokens"
           " moved.")

ARTIFACT = ("src/sandbox/ledger/test_apimarket_refund.py +"
            " qa/apimarket-refund-R2088.log (SUITE PASS 8/8 double-run"
            " identical sha16 0526d2a53ffebbf6; RUNNER PASS 294/294"
            " suites, 2458 criteria, controls 7/7, 280.3s ="
            " qa/reconcile-all-R2088.log; suite-matrix 294 suites /"
            " 2458 criteria byte-identical, 2026-10-24)")

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

head_old = '"results": [' + NL + '    [' + NL + '      "R2087",'
head_new = ('"results": [' + NL +
            '    [' + NL +
            '      "R2088",' + NL +
            '      "' + CURRENT + '"' + NL +
            '    ],' + NL +
            '    [' + NL +
            '      "R2087",')
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
if ids[:2] != ["R2088", "R2087"]:
    sys.exit("FATAL: results head order %r" % (ids[:2],))
if doc["ceo_face"]["current"] != CURRENT:
    sys.exit("FATAL: ceo_face current not applied")
if doc["self_drive"]["queue_explore_open"] != derived["queue_explore_open"]:
    sys.exit("FATAL: self_drive derived mismatch")

with io.open(EXPORT, "w", encoding="utf-8", newline="") as f:
    f.write(text)
print("EXPORT-OK results_head=%r" % (ids[:2],))