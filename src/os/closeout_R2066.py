import io
import json
import os
import re
import sys
from datetime import datetime

ROOT = r"C:\Users\sjs20\Desktop\FluxGroup\domain\BigDomain"
DEC = r"C:\Users\sjs20\Desktop\FluxGroup\docs\decisions.md"
STATE = os.path.join(ROOT, "src", "os", "state.json")

text = io.open(STATE, encoding="utf-8", newline="").read()
doc = json.loads(text)

# ---- decision token diff (content addressed) -------------------
raw = io.open(DEC, encoding="utf-8").read()
found = set(re.findall(r"\b[DC]-\d{8}-\d{1,3}\b", raw))
baseline = set(doc["last_dec_tokens"].split(","))
new = sorted(found - baseline)
rows = len([l for l in raw.splitlines() if l.strip().startswith("| 2026-")])
print("new_tokens=%r rows_now=%d" % (new, rows))

ack = {
    "D-20261024-01": "BigStream model route (M4/S4) - ack, not our face",
    "D-20261024-02": "BigLife local model whitelist - ack, not our face"
                     " (this sandbox runs zero local LLM)",
    "D-20261024-03": "bigmoney decisions watermark rule - ack, not our face",
    "D-20261024-04": "night-audit cadence and backfill - ack, HQ/night face",
    "D-20261024-05": "research order marked executed - our face delivered"
                     " earlier (docs/research/R-20261024-bigdomain-skill-scan.md)",
    "D-20261024-06": "MV 141 line - ack, BigStream face",
    "D-20261024-07": "FluxVerse suspension record - ack, not our face",
}
receipts = ["%s %s" % (k, ack.get(k, "ack"))
            for k in new]
receipt_txt = "; ".join(receipts) if receipts else "no new tokens"

NARRATIVE = (
    "2026-10-24 R2066 (P3 explore-queue FIFO head after the gated heads:"
    " the merchant-account payment row is a physical-item wait, the OSS"
    " 72h harvest row has no new group-company slice since 10-20, and the"
    " honorcert already-granted gate-order row would duplicate R2029"
    " AC-HYGG1..7 which already pins replay idempotency and front-door"
    " rejects across restarts) - the datasub coverage bad-window gate"
    " family cross-restart same-code window. Decisions scan found seven"
    " NEW tokens against the content-addressed baseline (the file had"
    " grown from the pruned 179-row state to %d rows) and every one was"
    " judged this round: %s. Ledger has zero new @BigDomain rows, group"
    " orders baseline unchanged at 2026-10-23 23:56, benchmarks refreshed"
    " 2026-10-20 (inside 7 days), tree clean, no index.lock. Claimed the"
    " explore row with AC-CVGG1..AC-CVGG8 pre-registered in the queue row"
    " BEFORE the suite existed. Ruling: the coverage window gate is a"
    " pure per-call front door - the ten-form probe vector (seven"
    " coverage_board_dual shapes: None, month 13, int 202610, bool True,"
    " slash form, trailing LF, trailing space; three coverage_board"
    " shapes: month 13, int, bool) answers the single family code"
    " E_DSB_BAD_WINDOW on every instance, and the dual-face reject"
    " performs ZERO coverage_board delegations (proved with a counting"
    " subclass: delta 0 for the seven dual probes, exactly 3 for the"
    " three board probes), so no zone read can happen before the gate."
    " Delivered src/sandbox/ledger/test_datasub_coveragegatepersist.py:"
    " three instances (fresh, ordered close ds->led then same db/cfg"
    " rebuild, second restart) produce a pairwise identical ten-code"
    " vector, identical delegation deltas, identical world digests and"
    " byte-identical post-battery board envelopes; the probe batches"
    " leave all three datasub tables and both ledger tables constant; an"
    " interleaved sequence (four valid reads + two bad probes) yields"
    " exactly four delegations, so the gate does not latch; and after"
    " the battery a legitimate subscribe + deliver still works (board"
    " moves honestly (1,1,1) -> (2,2,2), real spend tx bound) with the"
    " non-advisory notice still first and last in the bundle. SUITE PASS"
    " 8/8 double-run identical (stdout sha16 0d666ff57396faa1); wired"
    " ledger-datasub-coveragegatepersist (8) into reconcile_all SUITES;"
    " battery RUNNER PASS 274/274 suites + controls 7/7 218.3s ="
    " qa/reconcile-all-R2066.log; matrix regenerated 274 suites / 2302"
    " criteria with --check byte-identical twice. Honest notes: (a) the"
    " first battery run FAILED the census suite because the evidence log"
    " was written through a PowerShell redirect (ps-utf16 dialect); the"
    " file was rebuilt as a python single-writer utf-8 LF artefact and"
    " the re-run is green (R2048/R2033 dialect law again); (b) three"
    " delivery-time suite repairs were made in-window - bob needed"
    " funding of his own for the liveness leg, the interleaved"
    " delegation count is 4 not 3 (four valid reads), and the"
    " subscription query must hit the datasub db not the ledger db;"
    " (c) explore queue open stays 9 then 8 after this claim. Score 2."
)

TOKENS = ("R2066 tokens: local=~120k api=0 api_reason=five-silence scan +"
          " decisions seven-token judgement + gate-family cross-restart"
          " suite 8/8 + battery 274/274 + matrix regen/check + census"
          " dialect rebuild + state/export closeout, zero cloud calls")

# ---- state.json raw append + tick ------------------------------
tail = '"\n    ]\n}\n'
if not text.endswith(tail):
    sys.exit("FATAL: state tail anchor miss")
text = text[:-len(tail)] + '",\n        ' + json.dumps(
    NARRATIVE) + ',\n        ' + json.dumps(TOKENS) + '\n    ]\n}\n'
text, n = re.subn(r'"tick": \d+', '"tick": %d' % (doc["tick"] + 1),
                  text, count=1)
if n != 1:
    sys.exit("FATAL: tick anchor miss")
new_set = ",".join(sorted(baseline | set(found)))
text, n = re.subn(r'"last_dec_tokens": "(?:[^"\\\\]|\\\\.)*"',
                  lambda m: '"last_dec_tokens": "%s"' % new_set,
                  text, count=1)
if n != 1:
    sys.exit("FATAL: token baseline anchor miss")
text, n = re.subn(r'"last_decision_rows": \d+',
                  '"last_decision_rows": %d' % rows, text, count=1)
if n != 1:
    sys.exit("FATAL: rows anchor miss")

doc2 = json.loads(text)
if doc2["tick"] != doc["tick"] + 1:
    sys.exit("FATAL: tick not applied")
if doc2["log"][-1] != TOKENS:
    sys.exit("FATAL: log tail not the tokens line")
io.open(STATE, "w", encoding="utf-8", newline="").write(text)

# ---- explore queue row: open -> done ---------------------------
QP = os.path.join(ROOT, "state", "queue", "explore.md")
ql = io.open(QP, encoding="utf-8", newline="").read().split("\n")
hit = 0
for i, line in enumerate(ql):
    if line.startswith("- [ ] \u6570\u636e\u96c6\u8986\u76d6\u699c\u6708\u6eda\u7a97\u65cf"):
        ql[i] = line.replace("- [ ] ", "- [x] ", 1) + (
            "\u3014done 2026-10-24 R2066\uff1a"
            "AC-CVGG1..8 \u5168\u8fc7\u00b7\u5957\u4ef6 "
            "test_datasub_coveragegatepersist.py SUITE PASS 8/8"
            "\u53cc\u8dd1\u540c\u4e00\uff08stdout sha16 "
            "0d666ff57396faa1\uff09\u00b7\u63a5\u7ebf "
            "ledger-datasub-coveragegatepersist(8)\u00b7\u7535\u6c60 "
            "RUNNER PASS 274/274 suites+controls 7/7 218.3s="
            "qa/reconcile-all-R2066.log\u00b7\u77e9\u9635 274/2302 "
            "--check byte-identical\u3015")
        hit += 1
if hit != 1:
    sys.exit("FATAL: explore row hit=%d" % hit)
io.open(QP, "w", encoding="utf-8", newline="\n").write("\n".join(ql))

# ---- backlog: done line at the top of the item list ------------
BP = os.path.join(ROOT, "src", "os", "backlog.md")
bl = io.open(BP, encoding="utf-8", newline="").read().split("\n")
done = (
    "- [x] P3 explore \u961f\u5934\u8ba4\u9886\uff08R2066\uff09\uff1a"
    "datasub \u8986\u76d6\u699c\u6708\u6eda\u7a97\u65cf\u574f\u53c2\u95e8\u65cf"
    "\u8de8\u91cd\u542f\u540c\u7801\u4f8b\u7a97\uff08R2030 AC-CVMR6 \u540e\u7ee7\u9762"
    "\uff09\u2014\u2014[done 2026-10-24 R2066]\uff08\u5224\u636e "
    "AC-CVGG1..CVGG8 \u9884\u6ce8\u518c\u5148\u4e8e\u4ee3\u7801\u00b7\u5341\u5f62"
    "\u63a2\u9488\u5411\u91cf\u5355\u7801 E_DSB_BAD_WINDOW\u00b7"
    "dual \u62d2\u4ee3\u96f6 coverage_board \u59d4\u6258\uff08\u8ba1\u6570\u5b50\u7c7b"
    "\u5b9e\u8bc1\uff09\u00b7\u4e09\u5b9e\u4f8b\u9010\u4f4d\u540c\u4ee3\u7801\u5411\u91cf+"
    "\u56fe\u4e16\u754c\u6458\u8981\u6052\u5b9a\u00b7\u4ea4\u9519\u5e8f\u65e0\u9501\u5b58\u00b7"
    "\u63a2\u9488\u540e\u5199\u8def\u5f84\u6d3b\u6001\u00b7\u5957\u4ef6 8/8 \u53cc\u8dd1"
    "\u540c\u4e00+UI\u7535\u6c60 274/274+--check byte-identical\uff1b"
    "\u8be6\u89c1 state/queue/explore.md \u540c\u540d\u884c done \u6ce8\uff09")
idx = None
for i, line in enumerate(bl):
    if line.startswith("- ["):
        idx = i
        break
if idx is None:
    sys.exit("FATAL: backlog item list not found")
bl.insert(idx, done)
io.open(BP, "w", encoding="utf-8", newline="\n").write("\n".join(bl))

print("STATE-QUEUE-BACKLOG-OK tick=%d rows=%d new_tokens=%d"
      % (doc2["tick"], rows, len(new)))