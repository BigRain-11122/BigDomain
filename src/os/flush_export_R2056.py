# flush_export_R2056.py - byte-surgical export refresh for the R2056
# closeout: export_ts + the three ceo_face rows + the R2056 pair
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

CURRENT = ("R2056 tech-queue FIFO head claim (R2052 reseed seed 8): the "
           "funnel daily CLI multi-day evidence determinism. AC-FCC1.."
           "AC-FCC8 pre-registered in the tech.md claim row BEFORE the "
           "suite existed. The suite drives the real subprocess over a "
           "D1/D2/D3 chain in a temp world: one evidence file per day "
           "byte-equal to the stdout block (LF normalised, no BOM, no CR, "
           "strict utf-8), day isolation, chain-rerun determinism, the "
           "printed envelope equal to the stored rollup, the gate/exit "
           "contract pair (clean 0/PASS, banned-word world 2/FAIL with "
           "the evidence still written), evidence purity (all bytes "
           "under 128, no repo root, no un-injected date), source-table "
           "idempotency and hygiene. Delivery-time honest amendments: the "
           "AC-FCC2 flow arithmetic was fixed and the AC-FCC3 wording was "
           "corrected to the product truth - ring lines flip their "
           "per-pass activity fields on a rerun and the lifetime "
           "token_outstanding_total recomputes from the whole ledger "
           "(the R2052 AC-FCV7 finding), so the frozen face is the "
           "day-window keys plus the summary/focus lines and the stored "
           "rollup. Suite SUITE 8/8 first-run green, double-run "
           "byte-identical; wiring reconcile_all SUITES (funnel-cli-chain, "
           "8); full battery RUNNER PASS 265/265 suites + controls 7/7 "
           "223.3s = qa/reconcile-all-R2056.log; matrix 265/2230 "
           "--check byte-identical; census DRIFT-CLEAN; fold R578 "
           "pre-closeout (74949B, predicted==actual); tech reseeded to 10 "
           "open. Score 2.")

ARTIFACT = ("src/sandbox/funnel/test_funnel_cli_chain.py + "
            "qa/reconcile-all-R2056.log (SUITE PASS 8/8 AC-FCC1..8 "
            "first-run green, double-run sha16 bd9f2d67cfc1525d; RUNNER "
            "PASS 265/265 suites + controls 7/7 223.3s; suite-matrix "
            "265/2230 byte-identical; census DRIFT-CLEAN, 2026-10-20)")

MILESTONE = ("FUNNEL 72h self-continuity acceptance <=10-31 (day-3 stamp "
             "next round); building-plan committee tri-report <=10-25 "
             "(plan doc ready); tech queue next head (funnel inbox "
             "non-JSON noise classification) plus the two new reseed "
             "seeds; weekly dead-doc deletion inside the 10-19..10-26 "
             "rectification window; QA charter W30 crawl; window <=48h "
             "(by 2026-10-22)")

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

head_old = '"results": [' + NL + '    [' + NL + '      "R2055",'
head_new = ('"results": [' + NL +
            '    [' + NL +
            '      "R2056",' + NL +
            '      "' + CURRENT + '"' + NL +
            '    ],' + NL +
            '    [' + NL +
            '      "2056",' + NL +
            '      "' + TICK_LABEL + '"' + NL +
            '    ],' + NL +
            '    [' + NL +
            '      "R2055",')
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
if ids[:3] != ["R2056", "2056", "R2055"]:
    sys.exit("FATAL: results head order %r" % (ids[:3],))
if [r[0] for r in doc["results"]].count("2056") != 1:
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