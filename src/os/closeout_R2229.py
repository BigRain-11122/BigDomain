import io
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
STATE = os.path.join(ROOT, "src", "os", "state.json")

narrative = (
    "2026-10-29 R2229 (five-silence scan clean at open: decisions.md"
    " carried 274 rows / 180 content-addressed D/C/O/T tokens with"
    " four apparent additions that are all the known group-side"
    " rotation artefacts (D-20261006-05, D-20261007-04,"
    " D-20261007-05, D-20261008-05), so zero genuinely new rows and"
    " zero domain action; the group ledger carries the same three"
    " @BigDomain patrol rows already paid off with zero unreplied;"
    " the group orders baseline is unchanged at the 2026-10-29 02:1x"
    " CEO-PROXY fleet event round R2.48 already consumed in R2226;"
    " benchmarks refreshed 2026-10-29 inside the seven-day gate; tree"
    " clean, no index.lock) - the P1 canonical rows stay"
    " blocked-on-CEO, the weekly proposal duty is met by BD-PROP-005,"
    " all four tech heads stayed gated (docker host absent, logs"
    " toolkit standing maintenance, member refunded schema"
    " product-gated, the live-mtime row waiting on a real"
    " normalized-mtime event), so this window claimed the explore head"
    " seed and shipped a product increment: apimarket face"
    " api_category_claim_months(include_uncategorized=True). Gap:"
    " api_market_claim_months answers the whole market on a month"
    " axis, api_claims the three present status views,"
    " api_claim_latency the per-leg durations and"
    " api_category_refund_months the refunded money by category, so"
    " WHICH CATEGORIES absorb after-sales claim pressure month over"
    " month had no face at all - a category drowning in claims read"
    " exactly like a quiet one. Product: an eighteen-key envelope with"
    " twelve-key month rows and eleven-key category cells; the booking"
    " law books a claim in the UTC month of its own opened_utc AND in"
    " the category in force at that instant, so a February re-file"
    " never moves a January bucket (asserted: JAN keeps data and"
    " carries no audio, MAR carries audio and no data); the status"
    " seam (refunded beats withdrawn beats answered beats open)"
    " partitions claim_count in every row and in the envelope, and"
    " money stays on the claim side - claim_amount sums the price_paid"
    " frozen at open while refunded_amount sums the refund joined"
    " through the claim's purchase, so the fixture's refund with no"
    " claim never appears; the contiguous JAN..MAR grid carries an"
    " honest zero FEB row whose refund_rate is None, and the APR"
    " refund of a January claim neither moves it nor invents an April"
    " row; the uncategorized bucket sorts last and"
    " include_uncategorized=False drops it AND recomputes every"
    " aggregate (6 claims -> 5, envelope rate 0.1667 -> 0.2,"
    " categories 4 -> 3); six bad flag forms fail closed with"
    " E_AM_BAD_ARGS before any read with frozen table digests and a"
    " constant ledger_tx set; cross-face identity holds on all seven"
    " shared totals against api_market_claim_months plus the non-zero"
    " month set; the peak takes JAN with 4 and never a zero month;"
    " three instances over two full-stack restarts read byte-identical."
    " Evidence: SUITE PASS 8/8 double-run byte-identical criterion"
    " sha16 018F0A7C4BBA3C27"
    " (qa/apimarket-categoryclaimmonths-R2229-a.log and -b.log,"
    " single-writer utf-8 LF via src/os/run_evidence_R2229.py, never a"
    " shell redirection), wired as"
    " ledger-apimarket-categoryclaimmonths(8), seven adjacent"
    " claim/category suites green (qa/regression-R2229.log),"
    " PRODUCT_SHA_STABLE True. Honest notes: the first AC-CKM8"
    " evidence line carried a format-string arity bug (four arguments"
    " for five placeholders) which aborted the run after seven"
    " criteria had already passed - the fix touched the evidence text"
    " only and no assertion was relaxed; the stale R2228 explore row"
    " was flipped to done in the same window because"
    " api_seller_repeat_months shipped in R2228 and only the marker"
    " was missing (zero product change). Debt carried: the full"
    " reconcile battery and the suite-matrix regeneration were NOT run"
    " in this 25-minute window (the R2168 mixed-tree rule) and are the"
    " R2230 first item.")

tokens = (
    "R2229 tokens: local=~35k api=0 api_reason=product window on one"
    " apimarket category face - an anchor check, one new face plus an"
    " eight-criterion suite double-run to byte-identical evidence,"
    " seven adjacent regressions, one stale explore row closed, and the"
    " state/export/backlog closeout; zero cloud calls")

heal = (
    "R2229 self-heal check: the BigDomain-OSLoop scheduled task exists"
    " and is Running, but its principal still reads"
    " LogonType=Interactive with RunLevel=Limited, which the 2026-09-29"
    " machine law forbids for every lane task. src/os/register_loop_task.ps1"
    " already passes an explicit S4U principal and needs an elevated"
    " shell to apply it; this session runs unelevated, so the task was"
    " left untouched rather than risk replacing the definition of the"
    " loop hosting this window. Open local-lane item for an elevated"
    " window.")

with io.open(STATE, encoding="utf-8", newline="") as handle:
    state = json.load(handle)

state["tick"] = 2229
state["log"].extend([narrative, tokens, heal])

body = json.dumps(state, indent=2, ensure_ascii=False)
body = body.replace("\r\n", "\n").replace("\n", "\r\n")
with io.open(STATE, "w", encoding="utf-8", newline="") as handle:
    handle.write(body + "\r\n")

# verify readback
with io.open(STATE, encoding="utf-8", newline="") as handle:
    again = json.load(handle)
print("tick", again["tick"], "log", len(again["log"]))
raw = io.open(STATE, "rb").read()
print("bare_lf", raw.count(b"\n") - raw.count(b"\r\n"))
print("last_line_has_crlf", raw.endswith(b"}\r\n"))

# ---- export refresh ----
EXPORT = os.path.join(ROOT, "docs", "status-export.json")
with io.open(EXPORT, encoding="utf-8", newline="") as handle:
    export = json.load(handle)
export["export_ts"] = "2026-10-29T05:05:00+08:00"
export["do"] = ("product round R2229 (per-category monthly claim"
                " pressure face)")
export["ceo_face"] = {
    "current": ("R2229 是产品轮：给 API 市场补了「按品类的月度售后索赔"
                "压力面」（api_category_claim_months）。此前市场月度面只答"
                "全市场、退款面只答金额，一个品类这月被投诉几次、投诉是"
                "开放还是已答/已撤/已退款、钱冻结多少退回多少，只能人工"
                "拆表；现在一眼看清哪个品类在吸索赔压力、以及它随时间在"
                "变好还是变坏，这就是品类风险定价的读数。"),
    "latest_artifact": ("src/sandbox/ledger/apimarket.py（新增"
                        " api_category_claim_months）、"
                        "qa/apimarket-categoryclaimmonths-R2229-a.log / -b.log"
                        "（8/8 双跑逐字节同一 sha16 018F0A7C4BBA3C27）、"
                        "qa/regression-R2229.log（7 邻域全绿）、"
                        "state/queue/explore.md 判据行 AC-CKM1..AC-CKM8；"
                        "2026-10-29"),
    "next_milestone": ("48h 内：把这枚新面纳入全量电池（当前 413 套件 + 本面"
                       " = 414）并重生成套件矩阵，先清上一轮遗留的验证欠账；"
                       "随后继续 explore 队头「全市场月度目录规模时间线」"
                       "（api_market_catalog_months）。"),
}
ebody = json.dumps(export, indent=2, ensure_ascii=False)
ebody = ebody.replace("\r\n", "\n").replace("\n", "\r\n")
with io.open(EXPORT, "w", encoding="utf-8", newline="") as handle:
    handle.write(ebody + "\r\n")
print("export_ts", export["export_ts"])

# ---- heartbeat ----
with io.open(os.path.join(ROOT, "heartbeat.txt"), "w",
             encoding="ascii", newline="") as handle:
    handle.write("tick 2229\r\n")

# ---- backlog done row ----
BACKLOG = os.path.join(ROOT, "src", "os", "backlog.md")
with io.open(BACKLOG, encoding="utf-8", newline="") as handle:
    bl = handle.read()
row = (
    "- [x] [done 2026-10-29 R2229] P3 explore head claim (R2229, seed"
    " R2213, criteria AC-CKM1..AC-CKM8 registered in that queue row"
    " BEFORE the code; anchor check at HEAD 2026-10-29: AC-CKM,"
    " claim_category_cells and category_claim_count were git grep -F"
    " zero-occupancy rc=1 while the face, suite and wiring names were"
    " occupied only by the seed row text): apimarket **per-category"
    " monthly after-sales claim pressure**"
    " (api_category_claim_months(include_uncategorized=True)). Gap:"
    " api_market_claim_months answers the whole market on a month"
    " axis, api_claims the status views, api_claim_latency the leg"
    " durations and api_category_refund_months the refunded money by"
    " category, so which categories absorb claim pressure month over"
    " month had no face. Product: eighteen-key envelope, twelve-key"
    " month rows, eleven-key category cells; the booking law books a"
    " claim in its own opened_utc month AND in the category in force"
    " at that instant (a February re-file never moves a January"
    " bucket); the status seam partitions claim_count and money stays"
    " on the claim side so a refund with no claim never appears; the"
    " contiguous grid carries an honest zero month whose refund_rate"
    " is None and an April refund never invents an April row; the"
    " uncategorized bucket sorts last and include_uncategorized=False"
    " drops it AND recomputes every aggregate; six bad flag forms fail"
    " closed before any read with frozen digests; cross-face identity"
    " holds on seven shared totals against api_market_claim_months;"
    " the peak never lands on a zero month; three instances over two"
    " restarts read byte-identical. Evidence: SUITE PASS 8/8"
    " double-run byte-identical sha16 018F0A7C4BBA3C27"
    " (qa/apimarket-categoryclaimmonths-R2229-a.log and -b.log),"
    " wired ledger-apimarket-categoryclaimmonths(8), seven adjacent"
    " suites green (qa/regression-R2229.log). Debt: the full reconcile"
    " battery and the suite-matrix regeneration are the R2230 first"
    " item (the R2168 mixed-tree rule).\n")
with io.open(BACKLOG, "w", encoding="utf-8", newline="") as handle:
    handle.write(row + bl)
print("backlog prepended", len(row))