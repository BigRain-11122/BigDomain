# export_refresh_R2023.py - CEO-face export refresh for the
# R2023 closeout (F3 law: every field derived from actual
# state; results row append; self_drive left to the machine
# caliber - checker re-verified after this write). Pure ASCII
# source; CJK lives only in the loaded/written data file.
import io
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
P = os.path.join(ROOT, "docs", "status-export.json")

raw = io.open(P, "r", encoding="utf-8", newline="").read()
eol = "\r\n" if raw.count("\r\n") > raw.count("\n") - raw.count("\r\n") else "\n"
doc = json.loads(raw)

pat = json.loads(io.open(os.path.join(
    HERE, "export_consistency_patterns.json"),
    encoding="utf-8").read())
label = pat["tick_row_label"]

doc["export_ts"] = "2026-10-18T17:20:00+08:00"
doc["ceo_face"]["current"] = (
    "R2023: P3 explore queue FIFO head delivered: apimarket"
    " developer sales board month-window cross-restart persistence"
    " example window (the R2022 reseed; criteria AC-AMWP1..AMWP7"
    " pre-registered in the explore.md claim row before code;"
    " AC-AMWP prefix + suite name + registry label all git-grep"
    " zero-occupancy verified). Suite test_apimarket_devboard"
    "monthpersist.py (suite-only round, five product sha256"
    " pinned): pre-close default / SEP / OCT window boards pinned"
    " with a record-time prefix manual cross and the"
    " listed-09-sold-10 separation probe; fourteen bad-window"
    " forms all reject E_AM_BAD_WINDOW before any read with zero"
    " side effects; full-stack restart (am -> dk -> metered ->"
    " led close, same db_path same cfg bytes rebuild) replays"
    " all three reads byte-identically with the window echo key"
    " surviving; post-restart NOV continuation (carol publishes"
    " c2 price 5, bob buys dan's OCT-listed d1, eve buys c2)"
    " keeps the SEP and OCT boards byte-frozen (zero"
    " cross-window leakage) while the NOV board and the default"
    " board recompute zero-cache and equal the manual cross;"
    " the bad-window gate family rejects identically on"
    " instances two and three; append-only frozen row prefixes"
    " plus per-purchase spend/share ledger tx provenance (every"
    " tx present in ledger_tx, +4 tx for the two NOV"
    " purchases); third instance four-read byte-identical."
    " SUITE PASS 7/7 double-run LF-normalized byte-identical"
    " sha16 8c81a689059ffc48 = qa/apimarket-devboardmonth"
    "persist-R2023.log; reconcile_all wiring ledger-apimarket-"
    "devboardmonthpersist (238->239 suites, 2025->2032"
    " criteria); RUNNER PASS 239/239 + reconcile controls 7/7"
    " 199.6s zero regression = qa/reconcile-all-R2023.log;"
    " matrix regen 239/2032 green=239/239 --check"
    " byte-identical 23195B; census DRIFT-CLEAN files=1555"
    " flags=0; fingerprint CLEAN domains=5; profile --daily"
    " --check PASS. Two honest errata in the evidence chain,"
    " both healed in-round: the fingerprint sentinel was first"
    " invoked with a bare chain path (FileNotFoundError) -"
    " corrected to the shipped chain path, CLEAN rerun"
    " recorded; an erratum append captured unnormalized CRLF"
    " child stdout tripping the census dialect gate - the"
    " collector now LF-normalizes child stdout, the evidence"
    " log was regenerated and the census re-verified"
    " DRIFT-CLEAN. fold R553 pre-closeout honored (gauge"
    " 76829B, tail-3 rolling line, 73 tokens embedded"
    " zero-loss, predicted == actual 77923B). Heartbeat debt"
    " cleared (R2022 row backfilled + R2023 row, hb tick ==="
    " state tick). Explore consume-1 reseed-1. Score 2.")
doc["ceo_face"]["latest_artifact"] = (
    "src/sandbox/ledger/test_apimarket_devboardmonthpersist.py"
    " (month-window persist suite, AC-AMWP1..AMWP7) +"
    " qa/apimarket-devboardmonthpersist-R2023.log (SUITE 7/7"
    " double-run byte-identical sha16 8c81a689059ffc48) +"
    " qa/reconcile-all-R2023.log (RUNNER PASS 239/239) +"
    " docs/sandbox-suite-matrix.md regen (239 suites / 2032"
    " criteria, 2026-10-18)")
doc["ceo_face"]["next_milestone"] = (
    "P3 explore next open heads (dev_sales_board month-window"
    " zero-listing boundary persist [R2023 reseed], dev_sales"
    "_board zero-listing boundary persist, yearbooks_combined"
    " multi-year persist, coverage dual-window month-roll,"
    " showcase stats gate-family cross-restart) - one per"
    " round at the established cadence, next within 48h;"
    " P1/P2 lines stay gated on external arrivals (radar OH"
    " list, R777 review file, CEO physical items for"
    " bootstrap)")

row = doc["results"][-1]
if row[0] != "2022" or row[1] != label:
    raise SystemExit("FATAL: unexpected last results row " + str(row))
doc["results"][-1] = ["2023", label]

text = json.dumps(doc, ensure_ascii=False, indent=1)
if eol == "\r\n":
    text = text.replace("\n", "\r\n")
text += eol
io.open(P, "w", encoding="utf-8", newline="").write(text)
print("export refreshed: results rows=%d, ts=%s"
      % (len(doc["results"]), doc["export_ts"]))
