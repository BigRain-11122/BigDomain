# closeout_R2057.py - R2057 orphan-payload takeover closeout: state.json
# tick/log pair, tech queue claim-row done flip + duplicate seed merge +
# one true-live reseed, backlog claim-row done flip, heartbeat row.
# Pure ASCII source; CJK only in written data values (UTF-8 data faces).
import io
import json
import os
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
STATE = os.path.join(HERE, "state.json")
TECH = os.path.join(ROOT, "state", "queue", "tech.md")
BACKLOG = os.path.join(HERE, "backlog.md")
HB = os.path.join(ROOT, "heartbeat.txt")

ROUND = (
    "2026-10-20 R2057 (P2 tech-queue FIFO head, R2052 reseed: funnel "
    "inbox non-JSON noise classification) - five-silence scan: DEC "
    "content-addressed zero new tokens (212 tokens, zero new, "
    "D-20261020-07 baseline held), ledger zero new @BigDomain rows, no "
    "new orders (last_order 2026-10-20 00:5x held), benchmarks "
    "refreshed today, tree clean no index.lock. ORPHAN PAYLOAD "
    "TAKEOVER: the predecessor session landed product and evidence but "
    "died before closeout (funnel_daily.py _load_inbox classification "
    "law, new suite src/sandbox/funnel/test_funnel_inbox.py, "
    "reconcile_all SUITES wiring, qa/reconcile-all-R2057.log); no live "
    "writer verified (no index.lock, tree carried only the expected "
    "payload, mtimes stale), so the successor session re-verified every "
    "face live before adopting it: suite SUITE PASS 8/8 first-run green "
    "+ double-run stdout byte-identical sha16 1F3CF16200C7D0E1; full "
    "battery RUNNER PASS 266/266 suites green + controls 7/7 277.6s "
    "exit=0 = qa/reconcile-all-R2057.log (265-suite baseline zero "
    "regression); matrix --check byte-identical 266 suites / 2238 "
    "criteria; daily reconcile verdict=PASS runner_exit=0 sentinel=ok "
    "profile=ok census=ok = qa/reconcile-daily-20261020-3.log (census "
    "DRIFT-CLEAN files=1628 flags=0). Classification law delivered: an "
    "inbox entry is a regular file with the exact lower-case .json "
    "suffix; every other entry (other suffixes, bare names, directories "
    "- including one literally named fake.json) is junk, skipped "
    "unopened and never recursed into; a file that IS in contract but "
    "cannot be honoured (bad JSON text, invalid UTF-8, empty file, "
    "decoded value not an object) rejects the whole ring with "
    "FunnArgError before any row of that ring is written, and no "
    "JSONDecodeError / UnicodeDecodeError / IsADirectoryError escapes "
    "the library boundary. AC-FIN1..AC-FIN8 were pre-registered in the "
    "tech.md claim row before any code existed (honest inheritance note: "
    "the criteria text and the code both came from the crashed "
    "predecessor round; this round re-verified rather than re-authored). "
    "fold R579 honored pre-closeout (gauge 77951B, margin 549B against "
    "the two closeout lines: tail-4 window folded with the full "
    "41-token catalog embedded zero-loss, predicted==actual 74761B, "
    "archive append + preop backup e04084b056dbcce5). Queue hygiene: "
    "claim row flipped done, the duplicate R2052 seed row merged closed "
    "(same title, superseded by the claim row), and one true-live seed "
    "appended (funnel route distribution read face cross-restart "
    "persistence, AC-FRTP prefix git-grep zero occupancy 2026-10-20) so "
    "the standby line holds 10 open. Score 2 (runnable artifact: new "
    "classification law + suite + battery wiring all green)."
)

TOKENS = (
    "R2057 tokens: local=~380k api=0 api_reason=five-silence scan + "
    "orphan payload takeover re-verification (suite double-run, full "
    "battery 266/266, matrix check, daily census) + tech duplicate "
    "merge and one reseed + fold R579 + export flush, zero cloud calls"
)

with io.open(STATE, "r", encoding="utf-8") as f:
    state = json.load(f)
state["tick"] = 2057
state["log"].append(ROUND)
state["log"].append(TOKENS)
with io.open(STATE, "w", encoding="utf-8", newline="\r\n") as f:
    json.dump(state, f, ensure_ascii=False, indent=8)
print("STATE tick=%d log=%d bytes=%d"
      % (state["tick"], len(state["log"]), os.path.getsize(STATE)))

# ---- tech queue: claim row done, duplicate seed merged, one reseed ----
raw = io.open(TECH, "rb").read().decode("utf-8")
lines = raw.splitlines()
claim_done = 0
seed_merged = 0
for idx, line in enumerate(lines):
    if line.startswith("- [ ] funnel ") and "AC-FIN1..AC-FIN8" in line:
        lines[idx] = (
            line.replace("- [ ]", "- [x]", 1)
            + "\uff08done 2026-10-20 R2057\uff1aAC-FIN1..AC-FIN8 "
            "\u5168\u8fc7=\u5957\u4ef6 test_funnel_inbox.py SUITE 8/8 "
            "\u9996\u8dd1\u5168\u7eff\u3001\u53cc\u8dd1 sha16 "
            "1F3CF16200C7D0E1 \u540c\u4e00\uff1b\u63a5\u7ebf "
            "\"funnel-inbox\" 8 \u5224\u636e\uff1b\u5168\u7535\u6c60 "
            "RUNNER PASS 266/266 + controls 7/7 277.6s="
            "qa/reconcile-all-R2057.log\uff1b\u77e9\u9635 266/2238 "
            "--check byte-identical\uff1bcensus DRIFT-CLEAN "
            "1628/0\u2014\u2014tech \u961f\u5217\u6d88\u8017 1\uff09"
        )
        claim_done += 1
    elif (line.startswith("- [ ] funnel ")
          and "funnel-inbox-noise" in line
          and "AC-FIN" not in line):
        lines[idx] = (
            line.replace("- [ ]", "- [x]", 1)
            + "\uff08\u5408\u5e76\u5173\u95ed 2026-10-20 R2057\uff1a"
            "\u4e0e\u8ba4\u9886\uff08R2057\u884c\u540c\u9898\u91cd"
            "\u590d\u79cd\u5b50\uff0c\u8ba4\u9886\u884c\u542b "
            "AC-FIN1..AC-FIN8 \u5df2\u63a5\u7ba1\u5e76\u6536"
            "\u53e3\uff09"
        )
        seed_merged += 1
if claim_done != 1 or seed_merged != 1:
    raise SystemExit("TECH flip counts claim=%d seed=%d"
                     % (claim_done, seed_merged))

SEED = (
    "- [ ] funnel \u8def\u7531\u5206\u5e03\u8bfb\u6570\u9762\u8de8"
    "\u91cd\u542f\u6301\u4e45\u5316\uff08R2057 \u8865\u79cd\u00b7"
    "\u67e5\u91cd\u524d\u7f6e\u5df2\u8fc7\uff1aAC-FRTP \u524d\u7f00"
    "\u5168\u4ed3 git grep \u96f6\u5360\u7528 2026-10-20\uff1b"
    "\u6ce8\u518c\u8868 label \u5168\u5f62\u626b\u63cf "
    "funnel-route-persist \u96f6\u547d\u4e2d\uff09\u2014\u2014"
    "\u9762\u7f3a\u53e3=R2055 \u4ea4\u4ed8\u7684 route_tally "
    "\u8bfb\u6570\u9762\u4ec5\u540c\u5b9e\u4f8b\u5b9e\u8bc1\uff0c"
    "\u5173\u95ed\u91cd\u5f00\u540e\u540c db \u7684\u8de8\u91cd\u542f"
    "\u8bfb\u6570\u9762\u4e00\u81f4\u4e0e\u65b0\u65e5\u589e\u91cf"
    "\u91cd\u7b97\u65e0\u7f13\u5b58\u672a\u9a8c\uff1b\u7269\u7406"
    "\u9762=close/reopen \u4e09\u5b9e\u4f8b\u5c42\u53e0\uff08"
    "snapshot \u56db\u4efd + \u7a97\u53e3\u9694\u79bb + \u7b2c\u4e09"
    "\u5b9e\u4f8b\u4e00\u81f4\u6027\uff09\uff1b\u7528\u4f8b=R2055 "
    "\u540c\u5ce5\u8fde\u7eed\u4f8b\u7a97\u8303\u5f0f\uff1b"
    "\u5224\u636e\u9884\u6ce8\u518c\u7559\u7ed9\u8ba4\u9886\u8f6e"
    "\uff08\u672c\u884c\u96f6 AC \u9884\u8f7d=\u8bda\u5b9e"
    "\u5f8b\uff09"
)
if not lines or lines[-1].strip() == "":
    insert_at = len(lines)
else:
    insert_at = len(lines)
lines.insert(insert_at, SEED)
out = "\n".join(lines)
if raw.endswith("\n"):
    out += "\n"
io.open(TECH, "wb").write(out.encode("utf-8"))
print("TECH claim done + duplicate merged + reseed appended")

# ---- backlog: R2057 claim row done ----
rawb = io.open(BACKLOG, "rb").read().decode("utf-8")
linesb = rawb.splitlines()
hits = 0
for idx, line in enumerate(linesb):
    if line.startswith("- [ ] R2057 "):
        linesb[idx] = (
            line.replace("- [ ]", "- [x]", 1)
            + "\uff08done 2026-10-20 R2057\uff1a\u5b64\u513f\u8f7d"
            "\u8377\u63a5\u7ba1\u6536\u53e3\u2014\u2014\u5957\u4ef6 "
            "test_funnel_inbox.py SUITE 8/8 \u9996\u8dd1\u5168\u7eff"
            "\u3001\u53cc\u8dd1 sha16 1F3CF16200C7D0E1 \u540c\u4e00"
            "\uff1b\u7535\u6c60 RUNNER PASS 266/266 + controls 7/7 "
            "277.6s=qa/reconcile-all-R2057.log\uff1b\u77e9\u9635 "
            "266/2238 --check byte-identical\uff1bcensus DRIFT-CLEAN "
            "1628/0\uff09"
        )
        hits += 1
if hits != 1:
    raise SystemExit("BACKLOG flip hits=%d" % hits)
outb = "\n".join(linesb)
if rawb.endswith("\n"):
    outb += "\n"
io.open(BACKLOG, "wb").write(outb.encode("utf-8"))
print("BACKLOG R2057 done flip ok")

now = datetime.now().astimezone()
stamp = now.strftime("%Y-%m-%d %H:%M")
with io.open(HB, "a", encoding="utf-8", newline="\n") as f:
    f.write(
        "%s +08:00 | BigDomain OSLoop alive | tick 2057 | R2057: "
        "orphan-payload takeover closeout for the P2 tech FIFO head "
        "(funnel inbox non-JSON noise classification, AC-FIN1..AC-FIN8) "
        "- suite 8/8 first-run green + double-run sha16 1F3CF16200C7D0E1, "
        "battery 266/266 + controls 7/7 277.6s, matrix --check "
        "byte-identical 266/2238, census DRIFT-CLEAN 1628/0, fold R579 "
        "(74761B), tech duplicate seed merged + one reseed. "
        "[via BigDomain-OSLoop]\n" % stamp
    )
print("HEARTBEAT row appended")