"""R2165 closeout: flip the explore claim row to done, append the backlog
row, advance state.json and refresh the status export. Pure ASCII source;
Chinese text lives in the data files it edits."""
import io
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def read(path):
    with io.open(os.path.join(ROOT, path), encoding="utf-8") as fh:
        return fh.read()


def write(path, text):
    with io.open(os.path.join(ROOT, path), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


DONE = (
    " [done 2026-10-27 R2165] \u4ea7\u54c1=apimarket.py \u65b0\u589e "
    "`api_market_hour_heatmap()`\uff1a\u5341\u516d\u952e\u4fe1\u5c01 + "
    "\u4e8c\u5341\u56db\u884c\u5c0f\u65f6 + \u4e03\u884c\u661f\u671f + "
    "\u4e00\u767e\u516d\u5341\u516b\u884c\u5355\u5143\u683c\uff08\u7f51\u683c\u6052\u5b8c\u6574\uff0c"
    "\u96f6\u884c\u4e5f\u5728\u518c\uff09\uff1b\u73b0\u91d1\u5236\u53cc\u8f74\u5f52\u5c5e"
    "\uff08\u6210\u4ea4\u6309 purchased_utc \u54cd\u5ea6\u3001\u9000\u6b3e\u6309 "
    "refunded_utc \u54cd\u5ea6\uff0c\u9000\u6b3e\u6c38\u4e0d\u6539\u5199\u6210\u4ea4\u6876\uff09"
    "\uff1b\u4e94\u9879\u5b88\u6052\u4e0e\u8de8\u9762\u4e00\u81f4\uff08\u5bf9 "
    "api_market_months\uff09\uff1b\u53c2\u4e0e\u8005\u53e3\u5f84\u884c\u5185 distinct\u3001"
    "\u4fe1\u5c01\u7ec8\u8eab distinct\uff1b\u5cf0\u503c\u5f8b\u4e24\u7ea7\u5e73\u7968"
    "\uff08\u8ba1\u6570\u2192\u91d1\u989d\u2192\u66f4\u5c0f\u7d22\u5f15\uff09\u4e14"
    "\u7eaf\u9000\u6b3e\u6876\u6c38\u4e0d\u4e3a\u5cf0\uff1b\u7eaf\u8bfb\u96f6 tok+"
    "\u96f6\u884c\u53d8\u66f4\u3002\u8bc1\u636e=\u5957\u4ef6 SUITE PASS 8/8 "
    "\u53cc\u8dd1\u8bc1\u636e\u4ef6\u9010\u5b57\u8282\u540c\u4e00 sha256 "
    "55634543bbfff7c4\uff08\u5224\u636e\u884c sha16 6c7c62a2b4a722c3\uff0c"
    "qa/apimarket-hourheatmap-R2165-a.log / -b.log\uff0962736B\u00b7\u5355\u5199"
    "\u8005 utf-8 LF\uff09\uff1b\u63a5\u7ebf ledger-apimarket-hourheatmap(8)\uff1b"
    "\u5168\u91cf\u7535\u6c60 RUNNER PASS 367/367 + \u63a7\u5236 7/7 1353.7s"
    "\uff08qa/reconcile-all-R2165.log\uff09\uff1b\u77e9\u9635\u518d\u751f "
    "367 \u5957\u4ef6 / 3058 \u5224\u636e --check \u9010\u5b57\u8282\u540c\u4e00"
    "\uff0835448B\uff09\u3002"
)

# 1. flip the explore claim row
lines = read("state/queue/explore.md").split("\n")
head = None
last = None
for i, line in enumerate(lines):
    if "R2165" in line and line.startswith("- [ ] P3 explore"):
        head = i
    if head is not None and i > head and not line.startswith("  "):
        last = i - 1
        break
if head is None or last is None:
    raise SystemExit("E_CLOSEOUT_ROW_NOT_FOUND")
lines[head] = "- [x]" + lines[head][len("- [ ]"):]
lines[last] = lines[last].rstrip() + DONE
write("state/queue/explore.md", "\n".join(lines))

# 2. append the backlog row
bl = read("src/os/backlog.md")
note = (
    "- [x] P3 explore \u961f\u5934\u8ba4\u9886\uff08R2165\u00b7\u6e90=R2149 \u8865\u79cd"
    "\u884c\u00b7\u5224\u636e AC-MHH1..AC-MHH8 \u9884\u6ce8\u518c\u4e8e "
    "state/queue/explore.md \u540c\u540d\u884c\u4e14\u5148\u4e8e\u4ee3\u7801\uff09\uff1a"
    "apimarket **\u5e02\u573a\u6d3b\u52a8\u65f6\u95f4\u70ed\u529b\u9762**"
    "\uff08api_market_hour_heatmap\uff09\u2014\u2014\u7f3a\u53e3\u5b9e\u8bc1\uff1a"
    "\u5168\u4ed3\u65f6\u95f4\u8f74\u53ea\u5230\u6708\uff08market_months / "
    "revenue_months / buyer_months / category_refund_months\uff09\uff0c"
    "\u6d3b\u52a8\u6d41\u53ea\u662f\u4e8b\u4ef6\u884c\uff1b\u201c\u4e00\u5929\u91cc\u54ea"
    "\u4e2a\u5c0f\u65f6\u3001\u4e00\u5468\u91cc\u54ea\u4e2a\u661f\u671f\u51e0\u201d"
    "\u6c38\u65e0\u9762\u53ef\u7b54\u3002\u4ea7\u54c1=apimarket.py "
    "`api_market_hour_heatmap()`\uff1a\u5341\u516d\u952e\u4fe1\u5c01 + "
    "\u4e8c\u5341\u56db\u884c\u5c0f\u65f6\u884c\uff08\u516b\u952e\uff09+ "
    "\u4e03\u884c\u661f\u671f\u884c\uff08\u4e5d\u952e\u542b weekday_name\uff09+ "
    "\u4e00\u767e\u516d\u5341\u516b\u5355\u5143\u884c\uff08\u4e94\u952e\uff09\uff0c"
    "\u7f51\u683c\u6052\u5b8c\u6574\uff1b\u73b0\u91d1\u5236\u53cc\u8f74\u5f52\u5c5e"
    "\uff08purchased_utc / refunded_utc\uff0c\u9000\u6b3e\u4e0d\u6539\u5199\u6210\u4ea4\u6876"
    "\uff09\uff1b\u4e94\u9879\u5b88\u6052 + \u8de8\u9762 market_months "
    "\u4e00\u81f4\uff1b\u53c2\u4e0e\u8005\u884c\u5185 distinct \u800c\u4fe1\u5c01"
    "\u7ec8\u8eab distinct\uff08\u8bda\u5b9e\u4e0d\u5bf9\u79f0\uff09\uff1b"
    "\u5cf0\u503c\u4e24\u7ea7\u5e73\u7968\u4e14\u7eaf\u9000\u6b3e\u6876\u4e0d\u4e3a\u5cf0"
    "\uff1b\u7eaf\u8bfb\u96f6 token\u3002\u8bc1\u636e=SUITE PASS 8/8 "
    "\u53cc\u8dd1\u8bc1\u636e\u4ef6\u9010\u5b57\u8282\u540c\u4e00\uff08\u6587\u4ef6 "
    "sha256 55634543bbfff7c4\u00b7\u5224\u636e\u884c sha16 6c7c62a2b4a722c3\uff09\uff1b"
    "\u63a5\u7ebf `ledger-apimarket-hourheatmap(8)`\uff1b\u7535\u6c60 RUNNER PASS "
    "367/367 + \u63a7\u5236 7/7 1353.7s\uff1b\u77e9\u9635 367 \u5957\u4ef6 / "
    "3058 \u5224\u636e --check \u9010\u5b57\u8282\u540c\u4e00\u3002\u672c\u7a97"
    "\uff08R2166 \u53d6\u5f55\uff09\u4e3a**\u4e2d\u65ad\u7a97\u53d6\u5f55\u9a8c\u6536**"
    "\uff1a\u4ea7\u54c1\u3001\u5957\u4ef6\u3001\u63a5\u7ebf\u3001\u961f\u5217\u884c\u3001"
    "\u7535\u6c60\u4e0e\u8bc1\u636e\u5747\u5728\u76d8\uff0c\u672c\u7a97\u91cd\u8dd1\u5957"
    "\u4ef6\u4ecd 8/8 \u540c\u4e00 sha16\uff0c\u5e76\u8865\u505a\u77e9\u9635\u518d\u751f\u4e0e"
    "\u6536\u8d26\u3002\n"
)
anchor = "> \u8ba4\u9886\u5236\uff1a\u81ea\u6b63\u5178\u4efb\u52a1\u677f"
idx = bl.find(anchor)
if idx < 0:
    raise SystemExit("E_CLOSEOUT_BACKLOG_ANCHOR")
bl = bl[:idx] + note + bl[idx:]
write("src/os/backlog.md", bl)

# 3. state.json
state = json.loads(read("src/os/state.json"))
state["tick"] = int(state.get("tick", 0)) + 1
state["last_decision_rows"] = 266
state["log"].append(
    "2026-10-27 R2166 (this window opened on an INTERRUPTED predecessor: the "
    "R2165 product diff (api_market_hour_heatmap, +152 lines in apimarket.py), "
    "the eight-criterion suite, the reconcile_all wiring, the explore claim row, "
    "both suite evidence logs, the full battery log and its stdout/stderr twins "
    "were all on disk uncommitted while state.json still ended at R2164 - no "
    "index.lock and no live battery process, so a crashed window rather than a "
    "concurrent executor; per the R2087/R2146 precedent this round verified and "
    "closed that work instead of reseeding, and every number below is re-measured "
    "here) - five-silence scan: the strict content-addressed decisions diff over "
    "docs/decisions.md yields ZERO new D-/C- tokens against the stored baseline "
    "(186 stored, 177 present, zero present-but-absent); the six tokens the "
    "assistive scanner flags are artefacts - D-20260930-1 is a digit-width "
    "truncation of D-20260930-13 and the five D-/O- rows are body-text mentions "
    "restored by the group-side rotation, none of them new law and none our "
    "execution face, so zero action and the stored baseline stays authoritative; "
    "the ledger carries the same three @BigDomain patrol rows already paid off "
    "with zero unreplied groups; the group orders tail is unchanged at the "
    "2026-10-27 21:12 fleet dispatch row (OB-20261027-211206-860, a bm-a/bm-b/"
    "bm-c fleet face, acknowledged with zero action); benchmarks refreshed "
    "2026-10-27 inside the seven-day gate. Verification delivered: the heatmap "
    "suite re-ran standalone on the current tree SUITE PASS 8/8 at the same "
    "criterion sha16 6c7c62a2b4a722c3 as the predecessor logs, whose two evidence "
    "files are byte-identical (sha256 55634543bbfff7c4, 736B each, single-writer "
    "utf-8 LF); the full battery log reads RUNNER PASS 367/367 suites green plus "
    "reconcile controls 7/7 in 1353.7s with TMP RECLAIM candidates=824 removed=824 "
    "busy=0 failed=0 reclaimed=293.68 MiB (qa/reconcile-all-R2165.log plus its "
    "stdout twin, zero-byte .err); the suite matrix was regenerated against that "
    "battery to 367 suites / 3058 criteria and --check reads byte-identical "
    "(35448B) - the predecessor had not regenerated it, so this window closed "
    "that gap too. Product substance (unchanged from the predecessor, verified "
    "not rewritten): api_market_hour_heatmap() is the market's first sub-month "
    "time axis, a sixteen-key envelope over an always-complete 24-hour / "
    "7-weekday / 168-cell grid on the same cash-basis law the monthly faces use "
    "(a sale books in the UTC hour and weekday of purchased_utc, a refund in "
    "refunded_utc, and a refund never rewrites the bucket the sale landed in), "
    "five-term conservation within rows and against api_market_months, "
    "per-bucket distinct participants against lifetime-distinct envelope counts "
    "(an honest asymmetry the suite pins), a two-level peak law (count, then "
    "gross, then the lower index) where a refund-only bucket never becomes a "
    "peak, and a pure read with zero table mutation and zero token movement."
)
state["log"].append(
    "R2166 tokens: local=~60k api=0 api_reason=interrupted-window "
    "verification (suite re-run on the current tree, battery log inspection, "
    "evidence byte-identity) + suite matrix regeneration and --check + five "
    "queue/backlog/state/export closeout, zero cloud calls"
)
write("src/os/state.json", json.dumps(state, ensure_ascii=False, indent=4) + "\n")

# 4. status export
export = json.loads(read("docs/status-export.json"))
export["export_ts"] = "2026-10-27T23:30:00+08:00"
face = export.get("ceo_face", {})
face["current"] = (
    "R2166 closeout: verified and closed the interrupted R2165 window "
    "(apimarket hourly/weekday activity heatmap)"
)
face["last_artifact"] = (
    "src/sandbox/ledger/apimarket.py api_market_hour_heatmap + "
    "qa/apimarket-hourheatmap-R2165-a.log/-b.log (2026-10-27 23:2x)"
)
face["next_milestone"] = (
    "R2167: reseed the drained explore/tech queues and take the next "
    "explore head (ETA 2026-10-27 within 48h)"
)
export["ceo_face"] = face
write("docs/status-export.json", json.dumps(export, ensure_ascii=False, indent=4) + "\n")

print("CLOSEOUT OK tick=%s" % state["tick"])