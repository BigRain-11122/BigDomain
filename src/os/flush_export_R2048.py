# flush_export_R2048.py - byte-surgical export refresh for the
# R2048 closeout (export_ts + ceo_face three rows + results
# narrative prepend + tick row + self_drive window numbers).
# Raw-text edits only (no full json.dumps rewrite - the R1710
# layout-drift disease); json.loads validates before write-back.
# flush_export_R2045.py precedent. Pure ASCII source; CJK
# lives only in the written data values.
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

CURRENT = ("R2048: crashed-round orphan-payload takeover "
           "closeout + QA-charter daily-crawl carrier. The "
           "prior session claimed the funnel CLI bad-args "
           "gate seed (AC-FCG1..FCG7 pre-registered in the "
           "tech.md claim row before code), fixed "
           "funnel_daily.py main() to absorb every reject "
           "into ONE clean E_FN_BAD_ARGS line + exit 2 with "
           "the day validated before any disk artifact, "
           "delivered test_funnel_cli_gates.py and wired it "
           "into reconcile_all (257 suites), then died "
           "pre-closeout leaving its standalone evidence in "
           "a bad dialect (pwsh-capture class) - the only red "
           "in its RUNNER attempt (reconcile-daily-census "
           "7/8, 256/257). Takeover verification: suite "
           "double-run raw-sha16 8f29b21a8aaa7afa cross-"
           "checked MATCH against the orphan evidence log "
           "(chain closure), evidence rebuilt canonical "
           "python-single-writer utf-8 LF (R1924/R2033/"
           "R2045 dialect law, G6 fix path), census --check "
           "DRIFT-CLEAN. Full-battery re-run (detached "
           "process): RUNNER PASS 257/257 suites green + "
           "controls 7/7 + sentinel ok + census ok + profile "
           "ok = qa/reconcile-daily-20261020-2.log (the "
           "orphan's FAIL first-attempt evidence preserved "
           "unoverwritten). FUNNEL daily standing row: "
           "qa/funnel-daily-20261020.log on disk (orphan-"
           "produced, gate PASS honest zero-activity day). "
           "DEC receipts: D-20261020-01 tail-sweep face "
           "verified clean, D-20261020-02/03 non-company "
           "seats knowledge-only, baseline 383->389. QA "
           "charter daily crawl carried: W29 E-Commerce Law "
           "official fulltext direct-captured (A-grade "
           "npc.gov.cn, 7 chapters 89 articles - art. 17 "
           "fabricated-transaction/fabricated-review ban, "
           "art. 18 non-personalized option, art. 19 "
           "default-bundling ban, art. 24 immediate deletion "
           "on cancellation, art. 31 3-year transaction "
           "records, art. 48 automatic-system legal effect, "
           "art. 49 order-submission contract formation + "
           "post-payment-invalidation clause void, arts. "
           "53-57 payment five laws incl. free "
           "reconciliation + 3-year records) -> benchmarks "
           "four-place entry (sec.1 block + sec.2 row 13 + "
           "sec.3 source + sec.4 record) + intelligence-wall "
           "W29 dual rows + benchmarks_refreshed=2026-10-20 + "
           "smoke pair (real-log rendered png). Heartbeat "
           "tick-2047 backfill row landed ([HB] lag=1 debt). "
           "tech.md seed flipped done. Score 2 (runnable "
           "CLI-gate fix + suite + wiring + full battery "
           "green + statute four-place entry).")

ARTIFACT = ("qa/funnel-cli-gates-R2048.log +"
            " src/sandbox/funnel/test_funnel_cli_gates.py"
            " (SUITE 7/7 double-run raw-sha16 8f29b21a8aaa7afa"
            " cross-match; census DRIFT-CLEAN; RUNNER 257/257"
            " green = qa/reconcile-daily-20261020-2.log,"
            " 2026-10-20)")

MILESTONE = ("FUNNEL 72h self-continuity acceptance <=10-31"
             " (day-2 stamp qa/funnel-daily-20261020.log on"
             " disk, day-3 stamp next); building-plan"
             " committee tri-report <=10-25 (plan doc ready);"
             " tech queue next heads (funnel ring"
             " cross-restart persist / cross-day rescan"
             " first-write-wins / late re-rollup /"
             " conservation chain [R2047 reseed]); QA"
             " charter W30 crawl; window <=48h (by"
             " 2026-10-22)")

with io.open(EXPORT, "r", encoding="utf-8", newline="") as f:
    text = f.read()

now_iso = datetime.now().astimezone().isoformat(
    timespec="seconds")

regex_pairs = [
    ('"export_ts": "[^"]*"',
     '"export_ts": "' + now_iso + '"'),
    ('"current": "R2047[^"]*"', '"current": "' + CURRENT + '"'),
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

tick_old = '"2047",\n      "OSLoop '
tick_new = '"2048",\n      "OSLoop '
if text.count(tick_old) != 1:
    sys.exit("FATAL: tick row anchor hit count %d"
             % text.count(tick_old))
text = text.replace(tick_old, tick_new)

head_old = '"results": [\n    [\n      "R2047",'
head_new = ('"results": [\n    [\n      "R2048",\n      "'
            + CURRENT + '"\n    ],\n    [\n      "R2047",')
if text.count(head_old) != 1:
    sys.exit("FATAL: results head anchor hit count %d"
             % text.count(head_old))
text = text.replace(head_old, head_new)

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

doc = json.loads(text)
for key in ("log_lines_in_window", "idle_fast_mention_lines",
            "no_pullable_mention_lines", "queue_main_open",
            "queue_tech_open", "queue_explore_open",
            "proposals_total", "proposals_open"):
    if doc["self_drive"][key] != derived[key]:
        sys.exit("FATAL: self_drive %s %r != recompute %r"
                 % (key, doc["self_drive"][key], derived[key]))

json.loads(text)

with io.open(EXPORT, "w", encoding="utf-8", newline="") as f:
    f.write(text)

print("EXPORT-FLUSH-OK bytes=%d results_rows=%d window=%s"
      % (len(text.encode("utf-8")), len(doc["results"]),
         derived["window"]))
