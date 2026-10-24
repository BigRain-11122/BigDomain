# -*- coding: utf-8 -*-
"""R2110 closeout: boards, state.json and the silicon-watch export face."""
import io
import json
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
os.chdir(ROOT)

DONE = ("[done 2026-10-25 R2110]（判据 AC-AMBD1..AMBD8 预注册先于代码·"
        "六锚 git grep -F 零占用 rc=1·套件 8/8 双跑判据行同一 sha16 "
        "50999cbdeecb5975=qa/apimarket-buyerhistory-R2110.log+-2·"
        "电池 RUNNER PASS 315/315 suites+controls 7/7 404.5s="
        "qa/reconcile-all-R2110.log·矩阵 315/2628 --check byte-identical·"
        "census CENSUS-COMPLETE files=1769 flags=0·呈看件 "
        "preview/apimarket-report-buyers.html sha256 981a59af8f83823e）")

for path in ("state/queue/explore.md", "src/os/backlog.md"):
    text = io.open(path, encoding="utf-8").read()
    lines = text.splitlines(True)
    assert lines[0].startswith("- [ ] P3 explore 自补种并同窗认领（R2110）")
    lines[0] = lines[0].replace("- [ ]", "- [x]", 1)
    if lines[0].endswith("\n"):
        lines[0] = lines[0][:-1] + DONE + "\n"
    else:
        lines[0] = lines[0] + DONE
    io.open(path, "w", encoding="utf-8", newline="\n").write("".join(lines))

# --- state.json ---
sp = "src/os/state.json"
state = json.loads(io.open(sp, encoding="utf-8").read())
state["tick"] = int(state.get("tick", 0)) + 1

dec = io.open(r"C:\Users\sjs20\Desktop\FluxGroup\docs\decisions.md",
              encoding="utf-8", errors="replace").read()
tokens = sorted(set(re.findall(r"\b[DdCc]-\d{8}-\d{2,4}\b", dec)))
old = set(x.strip() for x in state["last_dec_tokens"].split(",") if x.strip())
new_tokens = [t for t in tokens if t not in old]
state["last_dec_tokens"] = ",".join(sorted(old | set(tokens)))
state["last_decision_rows"] = len(
    [l for l in dec.splitlines() if l.strip()])

log = list(state.get("log") or [])
row = (
    "2026-10-25 R2110 (five-silence scan clean: decisions.md yields zero "
    "new content-addressed tokens against the stored baseline (newest still "
    "D-20261025-04, acknowledged in R2104) with the assistive UTF-8 row "
    "count at 204; ledger zero new @BigDomain transfer rows; group orders "
    "baseline unchanged at 2026-10-24 12:17; benchmarks refreshed "
    "2026-10-24 inside 7 days; tree clean, no index.lock; both daily "
    "standing rows for 2026-10-25 were already stamped by R2105 so neither "
    "was re-run; all four tech heads stayed gated and the single open "
    "explore row stays gated on the merchant id, so this window seeded and "
    "claimed a fresh P3 row in the SAME window with AC-AMBD1..AC-AMBD8 "
    "pre-registered BEFORE the code existed (AC-AMBD, "
    "collect_buyer_history, BUYER_HISTORY_KEYS, buyer_history_block, the "
    "suite name and the ledger-apimarket-buyerhistory runner label were all "
    "git grep -F zero-occupancy anchored 2026-10-25, rc=1)) - the buyer "
    "history section on the settlement report, and the window's real "
    "finding: api_rating_history takes a rating_id that NO listing-wide face "
    "exposed (it surfaced only through the seller inbox, and only for "
    "unanswered rows), so that history face was unreachable by construction. "
    "Product: api_ratings rows now carry rating_id as an ADDITIVE key (every "
    "earlier key keeps its value), collect_buyer_history() reads "
    "api_library, api_watchlist, api_refund and api_rating_history once per "
    "buyer into one history block with exactly BUYER_HISTORY_KEYS, refund "
    "rows are the eleven-key provenance envelopes with the resident "
    "disclaimer stripped, and rating_history_rows folds base-only ratings "
    "into one base row and revised ratings into one row per append-only "
    "revision. render_html gains a Buyer history group of four sub-tables "
    "per buyer (library / watchlist / refunds / rating history) with honest "
    "empty states; REPORT_SCHEMA moves 4 -> 5 additively (envelope still "
    "exactly schema_version/report/attention, every v4 report value equal to "
    "its direct face call, a legacy report dict without the key renders "
    "empties). Suite test_apimarket_report_buyerhistory.py SUITE PASS 10/10 "
    "double-run criterion lines identical sha16 50999cbdeecb5975 "
    "(qa/apimarket-buyerhistory-R2110.log plus -2); wired "
    "ledger-apimarket-buyerhistory (8); battery RUNNER PASS 315/315 suites "
    "plus controls 7/7 in 404.5s (qa/reconcile-all-R2110.log); matrix 315 "
    "suites / 2628 criteria --check byte-identical; census CENSUS-COMPLETE "
    "(files=1769, flags=0, read-only pass); preview artifacts "
    "preview/apimarket-report-buyers.html (24167B, sha256 "
    "981a59af8f83823e) and .json (38330B, schema 5). Three defects "
    "disclosed: (a) the dossier and workbench suites pinned the exact buyer "
    "key set and the dossier suite pinned REPORT_SCHEMA == 4 as literals, so "
    "this additive bump broke them - both birth stations now pin the v4 "
    "buyer keys as a literal SUBSET and the schema as >= 4 / module constant, "
    "with the v4 key sets still literal; (b) the first determinism attempt "
    "failed because rich_world() wrote watches and rating revisions with the "
    "real clock, so two seeded worlds differed in watched_utc/revised_utc - "
    "both clocks are pinned now, exactly as seed_demo does; (c) the first "
    "battery invocation piped the runner through Out-Null (zero output for "
    "five minutes) and the tool killed it, leaving qa/_r2110_runner_stdout.txt "
    "and a zero-byte evidence path - the runner was relaunched detached "
    "windowless and the byproduct file removed before the commit.")
tok = ("R2110 tokens: local=~130k api=0 api_reason=five-silence scan + "
       "buyer history product change (rating_id additive key + four-face "
       "collector + four HTML sub-tables) + suite 10/10 double-run + two "
       "birth-station pin repairs + battery 315/315 + matrix regen/check + "
       "census + preview artifacts + state/export closeout, zero cloud calls")

state["log"] = list(state.get("log") or []) + [row, tok]
io.open(sp, "w", encoding="utf-8", newline="\n").write(
    json.dumps(state, ensure_ascii=False, indent=1) + "\n")

# --- export face ---
def open_rows(path):
    if not os.path.isfile(path):
        return 0
    return len([l for l in io.open(path, encoding="utf-8").read().splitlines()
                if l.startswith("- [ ]")])


prop_total = 0
prop_open = 0
pp = "docs/proposals.md"
if os.path.isfile(pp):
    pt = io.open(pp, encoding="utf-8").read().splitlines()
    prop_total = len([l for l in pt if l.startswith("- [")])
    prop_open = len([l for l in pt if l.startswith("- [ ]")])

ep = "docs/status-export.json"
exp = json.loads(io.open(ep, encoding="utf-8").read())
exp["export_ts"] = "2026-10-25T04:20:00+08:00"
exp["ceo_face"]["current"] = (
    "R2110：结算报告多了「买家全史」——买家库（买了什么还拥有什么）、关注清单、"
    "退款溯源、评分史四张面此前在生产代码里零调用点（与 R2101/R2106/R2108/R2109 "
    "同一种空转形态）；更实的一条：评分史面只收 rating_id，而任何列表级读面都不给 "
    "rating_id（只在卖家待答收件箱里露过），所以那张面事实上不可能被调用。本窗给"
    "评分行加法暴露 rating_id，再把四张面接进报告唯一消费者：每个买家名下新增四张"
    "子表（持有库/关注/退款/评分史），空态诚实呈现；机读契约 v4→v5 加法升级"
    "（信封仍恰三键、旧键一字不动）。")
exp["ceo_face"]["latest_artifact"] = (
    "preview/apimarket-report-buyers.html（24167B·sha256 981a59af8f83823e·"
    "可直接双击打开：市场总账+月度时间线+待办+公共活动+在架清单+挂牌全史档案+"
    "每个买家的持有库/关注/退款/评分史+卖家全表）+ "
    "preview/apimarket-report-buyers.json（38330B·schema 5）")
exp["ceo_face"]["next_milestone"] = (
    "R2111（≤48h）：继续把零消费者的读面接进产品面；商户号未到之前不碰支付对接，"
    "本地沙箱与证据链照跑")
exp["outs"].insert(0, {
    "ts": "2026-10-25T04:20:00+08:00",
    "kind": "product",
    "what": "apimarket report buyer history: library/watchlist/refund/"
            "rating-history faces consumed",
    "artifact": "preview/apimarket-report-buyers.html"})
exp["results"].insert(0, {
    "ts": "2026-10-25T04:20:00+08:00",
    "suite": "test_apimarket_report_buyerhistory.py",
    "verdict": "SUITE PASS 10/10 double-run sha16 50999cbdeecb5975",
    "evidence": "qa/apimarket-buyerhistory-R2110.log"})
sd = exp["self_drive"]
sd["log_lines_in_window"] = 20
sd["proposals_total"] = prop_total
sd["proposals_open"] = prop_open
sd["queue_tech_open"] = open_rows("state/queue/tech.md")
sd["queue_explore_open"] = open_rows("state/queue/explore.md")
io.open(ep, "w", encoding="utf-8", newline="\n").write(
    json.dumps(exp, ensure_ascii=False, indent=2) + "\n")

print("tick", state["tick"], "new_dec_tokens", len(new_tokens),
      "tech_open", sd["queue_tech_open"], "explore_open",
      sd["queue_explore_open"], "proposals", prop_open, "/", prop_total)