# flush_export_R2058.py - byte-surgical export refresh for the R2058
# closeout: export_ts + the three ceo_face rows + the R2058 pair
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

CURRENT = ("R2058 P2 tech-queue FIFO head, skipping the gated heads "
           "(docker host missing, member refunded schema design-gated, "
           "suite-matrix live-normalized window awaiting a real "
           "git-checkout mtime event, daily profile window time-gated to "
           "10-24): the funnel per-sku order totals read face across "
           "restarts, the gap AC-FST7 left behind (it proves only a "
           "single close/reopen). AC-FSP1..AC-FSP8 pre-registered before "
           "the suite existed. Three-instance cascade over a three-day "
           "order world: instance one anchors the lifetime face plus "
           "three day windows plus an honest no-row day; the reopened "
           "instance reproduces all five byte-for-byte; a late day-three "
           "batch grows the lifetime book (named bucket 3->4 orders, "
           "5980->6480 cent; blank sku stays its own bucket 1->2; the "
           "new sku takes its byte-order slot) while day one and two "
           "stay frozen; re-booking the original inbox after the restart "
           "is idempotent; the read path and the restart write nothing; "
           "a second restart keeps the injected state stable at nine "
           "orders. Suite SUITE 8/8, double-run sha16 "
           "1DFDF3FCECC14343; battery RUNNER 267/267 suites + controls "
           "7/7 258.5s; matrix 267/2246 --check byte-identical; fold "
           "R580 pre-closeout. One delivery-time criteria amendment "
           "(3->4, not 3->5; amounts were right). Queue hygiene: one "
           "true-live reseed from a code-face finding (sku str "
           "coercion). Score 2.")

ARTIFACT = ("src/sandbox/funnel/test_funnel_sku_persist.py + "
            "qa/reconcile-all-R2058.log (SUITE PASS 8/8 AC-FSP1..8, "
            "double-run sha16 1DFDF3FCECC14343; RUNNER PASS 267/267 "
            "suites + controls 7/7 258.5s; suite-matrix 267/2246 "
            "byte-identical, 2026-10-20)")

MILESTONE = ("FUNNEL 72h self-continuity acceptance <=10-31 (day-3 "
             "stamp next round); building-plan committee tri-report "
             "<=10-25 (plan doc ready); weekly dead-doc deletion inside "
             "the 10-19..10-26 rectification window; QA charter W30 "
             "crawl; window <=48h (by 2026-10-22)")

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

head_old = '"results": [' + NL + '    [' + NL + '      "R2057",'
head_new = ('"results": [' + NL +
            '    [' + NL +
            '      "R2058",' + NL +
            '      "' + CURRENT + '"' + NL +
            '    ],' + NL +
            '    [' + NL +
            '      "2058",' + NL +
            '      "' + TICK_LABEL + '"' + NL +
            '    ],' + NL +
            '    [' + NL +
            '      "R2057",')
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
if ids[:3] != ["R2058", "2058", "R2057"]:
    sys.exit("FATAL: results head order %r" % (ids[:3],))
if [r[0] for r in doc["results"]].count("2058") != 1:
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