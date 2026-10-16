# closeout_R2002.py - R2002 closeout: (1) state.json byte-
# surgical append of the R2002 round+tokens log lines (CRLF +
# 16-space indent preserved, no whole-file re-serialization)
# with external-face baseline updates (ORD tail 18:0x ->
# 2026-10-17 00:5x, GORD 442 -> 571, DEC rows 275 -> 282,
# DEC tokens += 9 judged tokens), (2) backlog.md daily-reconcile
# standing-row R2002 note, (3) heartbeat line, (4) status-export
# refresh (ceo_face + results R2002 row + self_drive recompute).
# CJK content lives in the ROUND/TOKENS/CEO_* string constants;
# script logic is ASCII.
import io
import json
import os
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)

P_STATE = os.path.join(ROOT, "src", "os", "state.json")
P_BACKLOG = os.path.join(ROOT, "src", "os", "backlog.md")
P_HEART = os.path.join(ROOT, "heartbeat.txt")
P_EXPORT = os.path.join(ROOT, "docs", "status-export.json")

ORD_NEW = "2026-10-17 00:5x"
GORD_NEW = 571
DEC_ROWS_NEW = 282
NEW_DEC_TOKENS = ["C-20261015-01", "C-20261016-02",
                  "D-20261016-01", "D-20261016-02",
                  "D-20261016-03", "D-20261016-04",
                  "D-20261016-05", "D-20261016-06",
                  "D-20261016-07"]

ROUND_LINE = (
    u"2026-10-17 R2002（五静扫描非全静：LEDGER @BigDomain 零新行"
    u"+ORD 尾 10-15 18:0x→10-17 00:5x 双格式新 ~99 行全量判读"
    u"〔GORD 表 442→571〕=MV V5 修片/drama 试点/游戏云道 O-20261016-2145/"
    u"bm-d 备机/委员会普查 C-20261016-02·C-20261016-04·C-20261016-05/"
    u"智能体库建库/寻源先行+日频风向/合规阶段门控/本地故障→云端恢复/"
    u"三维资源分配令全=他司或集团治理面·零 @BigDomain 执行面=知悉不动作"
    u"·atbd 7 行=09-28/29 历史行先例已消化〕+DEC 新 9 token 判毕"
    u"〔C-20261015-01+C-20261016-02+D-20261016-01..07 全=bigmoney 爪/"
    u"atomic-push -C ROOT/回执核销 34·35/三任务复开缺口/普查管线并入类"
    u"派工面=知悉不动作·基线并入 rows 275→282〕+约束内化如实注："
    u"①bm-a 工作日停产口令制 O-20261015-1845〔本 loop 随机暂停让路="
    u"设计内·10-16 周五整日缺口合法·今日周六复产本轮在跑〕②云端 token"
    u" 严管+并发帽〔本司 loop 纯本地 api=0 合规·spawn 闸 R2001 交付件"
    u"共知交互窗豁免缺陷〔集团 L1154 已定谳修法在飞·候 spec 到位再动"
    u"·本轮无假拦实证〕③合规阶段门控令〔本司设计件四件套维持=轻顾问"
    u"态·严格介入锚=商业化令〕④agent-library-sync 装机面初判误报勘正"
    u"〔首查全局用户目录缺位→正位=FluxGroup 根 .codely-cli\\skills 五新席"
    u"全在=已装机零缺口零上报〕——P1 认领=对账日常化常设行今日件"
    u"〔qa/reconcile-daily-20261017.log 盘上缺位=当日首轮合法执行〕"
    u"兑现：RUNNER PASS 224/224 suites green+reconcile controls 7/7 "
    u"267.4s+RECONCILE-DAILY verdict=PASS runner_exit=0 sentinel=ok "
    u"profile=ok census=ok·证据=qa/reconcile-daily-20261017.log"
    u"〔481798B〕·当日闭环零升级·常设行续行——P2 tech 开项全门控"
    u"〔docker-compose 缺位/常设线〕·P3 explore 队头=civic 竞赛榜月份窗"
    u"跨重启持久化例窗〔R1999 补种子在位·10 开项〕本轮未认领诚实注"
    u"〔两日积压外景清扫+日对账占满轮预算〕·benchmarks 10-15 刷新未越"
    u" 7 天窗·fold R535 收账前置兑现〔轮首 gauge 76657B 余量 1843B+"
    u"收账两行必越线→tail-4 窗 R2000/R2001 双对行 4740B 压 1 滚窗行"
    u" kept=0·11 token 全字面嵌零丢失 gen535·archive §R2002 verbatim"
    u"+preop logs/state-preop-R2002.bak·post 73365B〕·score 1"
    u"〔日对账电池=产品管线完整性件 224 套件全绿·诚实注零新可跑"
    u"产品例窗〕）"
)

TOKENS_LINE = (
    u"R2002 tokens: local=~0.6M api=0 api_reason=five-silence scan + "
    u"ORD 99-row dual-format sweep + DEC 9-token judge + P1 daily "
    u"reconcile battery (224 suites 267.4s foreground, sentinel+"
    u"census+profile) + fold R535 gen/execute + closeout byte "
    u"surgery + directed commit, zero cloud calls"
)

HB_BODY = (
    " R2002: daily-reconcile standing row executed (RUNNER PASS "
    "224/224 suites green, reconcile controls 7/7, 267.4s, "
    "sentinel=ok profile=ok census=ok, qa/reconcile-daily-20261017"
    ".log); external sweep ORD 10-15 18:0x->10-17 00:5x (~99 rows "
    "all non-BigDomain, ack no-action, GORD 442->571) + DEC 9 new "
    "tokens acked (rows 275->282); bm-a workday-pause law + "
    "compliance stage-gate internalized; agent-library sync "
    "verified installed at FluxGroup root (false alarm corrected, "
    "zero report); fold R535 pre-closeout 76657B->73365B; score 1."
)

BACKLOG_NOTE = (
    u"〔R2002 注记：10-17 首轮当日执行兑现=RUNNER PASS 224/224 suites"
    u" green+reconcile controls 7/7 267.4s+verdict=PASS runner_exit=0 "
    u"sentinel=ok profile=ok census=ok=qa/reconcile-daily-20261017.log"
    u"〔481798B〕·当日闭环零升级·常设行续行〕"
)

CEO_CURRENT = (
    "R2002: two-day external sweep (ORD ~99 rows + DEC 9 tokens all "
    "non-BigDomain faces, acked; baselines ORD 2026-10-17 00:5x, "
    "GORD 571, DEC rows 282) + daily-reconcile standing row executed: "
    "RUNNER PASS 224/224 suites green (reconcile controls 7/7, "
    "267.4s) with sentinel/profile/census all green; fold R535 landed "
    "pre-closeout. Score 1 (battery = product-line integrity piece; "
    "honest note: zero new runnable product suite this round)."
)
CEO_LATEST = (
    "qa/reconcile-daily-20261017.log (RUNNER PASS 224/224 suites "
    "green, reconcile controls 7/7, 267.4s, sentinel=ok, 2026-10-17)"
)
CEO_NEXT = (
    "P3 explore queue head: civic honor-competition month-window "
    "cross-restart persistence example (R1999 reseed; AC prefix "
    "pre-registered before code) claimable from next round, window "
    "<=48h (by 2026-10-19)"
)

RESULTS_ROW = (
    "R2002: two-day external backlog sweep + daily-reconcile standing "
    "row same-day execution. ORD dual-format sweep 2026-10-15 18:0x "
    "-> 10-17 00:5x (~99 new rows: MV V5 rework, drama pilot, "
    "game-company cloud lane, bm-d staging, council census cases, "
    "agent-library build, github-first daily-radar, compliance "
    "stage-gate, local-failover-to-cloud, three-dim resource "
    "allocation - all other-subsidiary or governance faces, zero "
    "@BigDomain execution faces, ack no-action; GORD 442->571). DEC "
    "9 new tokens judged and acked (C-20261015-01, C-20261016-02, "
    "D-20261016-01..07 - bigmoney claw, git-atomic-push -C ROOT, "
    "receipt batches, task-resume gap, census merges; rows 275->282). "
    "Internalized: bm-a workday pause order (Friday gap = CEO-use "
    "window by design; loop resumed Saturday), cloud austerity + "
    "concurrency cap (loop local-only api=0; spawn-gate "
    "interactive-window exemption defect = group-known L1154, "
    "committee fix in flight, no false-block this round), compliance "
    "stage-gate (design four-piece set stays, light-advisory), "
    "agent-library sync verified already installed at FluxGroup root "
    "(wrong-dir false alarm corrected, zero report). P1 claim = "
    "daily-reconcile standing row same-day item: RUNNER PASS 224/224 "
    "suites green, reconcile controls 7/7, 267.4s, RECONCILE-DAILY "
    "verdict=PASS runner_exit=0 sentinel=ok profile=ok census=ok, "
    "evidence qa/reconcile-daily-20261017.log. P2 tech open items "
    "all gated; P3 explore head (civic month-window cross-restart "
    "persistence, R1999 reseed) not claimed - honest note: sweep + "
    "battery consumed the round budget. fold R535 pre-closeout "
    "(76657B -> 73365B, tail-4 pair window, tokens embedded). "
    "Score 1."
)


def die(msg):
    print("ABORT: %s" % msg)
    sys.exit(2)


def json_escape(text):
    return (text
            .replace("\\", "\\\\")
            .replace('"', '\\"')
            .replace("<", "\\u003c")
            .replace(">", "\\u003e")
            .replace("&", "\\u0026")
            .replace("'", "\\u0027"))


def main():
    # ---------- 1. state.json byte-surgical append ---------------
    raw_s = io.open(P_STATE, "rb").read()
    if raw_s.count(b'"tick": 2001,') != 1:
        die("tick anchor not unique")
    if not raw_s.endswith(b"\r\n"):
        die("state must end with CRLF")
    if raw_s.count(b'"last_order": "2026-10-15 18:0x"') != 1:
        die("last_order anchor not unique")
    if raw_s.count(b'"last_gord_tbl_rows": 442') != 1:
        die("gord anchor not unique")
    if raw_s.count(b'"last_decision_rows": 275') != 1:
        die("dec rows anchor not unique")
    if raw_s.count(b'"last_dec_tokens": "') != 1:
        die("dec tokens anchor not unique")
    blines = raw_s.split(b"\r\n")
    if blines[-1] != b"" or blines[-2] != b"}":
        die("unexpected tail layout")
    if blines[-3] != b"    ]":
        die("unexpected log closer")
    last_item = blines[-4]
    if not last_item.startswith(b'                "'):
        die("unexpected last log item indent")
    if last_item.endswith(b","):
        die("last log item already comma-terminated")
    item1 = ("                \""
             + json_escape(ROUND_LINE) + "\",").encode("utf-8")
    item2 = ("                \""
             + json_escape(TOKENS_LINE) + "\"").encode("utf-8")
    body = (blines[:-4] + [last_item + b",", item1, item2]
            + [b"    ]", b"}", b""])
    out_s = b"\r\n".join(body)
    out_s = out_s.replace(b'"tick": 2001,',
                          b'"tick": 2002,', 1)
    out_s = out_s.replace(
        b'"last_order": "2026-10-15 18:0x"',
        b'"last_order": "' + ORD_NEW.encode("ascii") + b'"', 1)
    out_s = out_s.replace(
        b'"last_gord_tbl_rows": 442',
        b'"last_gord_tbl_rows": %d' % GORD_NEW, 1)
    out_s = out_s.replace(
        b'"last_decision_rows": 275',
        b'"last_decision_rows": %d' % DEC_ROWS_NEW, 1)
    idx = out_s.index(b'"last_dec_tokens": "') + len(
        b'"last_dec_tokens": "')
    end = out_s.index(b'"', idx)
    add = ("," + ",".join(NEW_DEC_TOKENS)).encode("ascii")
    out_s = out_s[:end] + add + out_s[end:]
    sz = len(out_s)
    if sz >= 78500:
        die("state over the line: %d" % sz)
    io.open(P_STATE, "wb").write(out_s)
    st = json.loads(io.open(P_STATE, encoding="utf-8").read())
    if st["tick"] != 2002:
        die("surgery verify failed (tick)")
    if st["log"][-2] != ROUND_LINE or st["log"][-1] != TOKENS_LINE:
        die("content verify failed")
    if st["last_order"] != ORD_NEW:
        die("last_order verify failed")
    if st["last_gord_tbl_rows"] != GORD_NEW:
        die("gord verify failed")
    if st["last_decision_rows"] != DEC_ROWS_NEW:
        die("dec rows verify failed")
    for tok in NEW_DEC_TOKENS:
        if tok not in st["last_dec_tokens"]:
            die("dec token missing: %s" % tok)
    d = io.open(P_STATE, "rb").read()
    if d.count(b"\n") != d.count(b"\r\n"):
        die("bare LF leaked")
    print("state.json OK: tick=2002 bytes=%d (cap 78500)" % sz)

    # ---------- 2. backlog.md standing-row note -----------------
    raw_b = io.open(P_BACKLOG, encoding="utf-8", newline="").read()
    crlf = "\r\n" in raw_b
    norm = raw_b.replace("\r\n", "\n") if crlf else raw_b
    lines = norm.split("\n")
    hits = [i for i, ln in enumerate(lines)
            if u"对账日常化常设行" in ln and u"reconcile_daily.py" in ln]
    if len(hits) != 1:
        die("standing row found=%d" % len(hits))
    i = hits[0]
    if BACKLOG_NOTE in lines[i]:
        die("backlog note already present")
    lines[i] = lines[i] + BACKLOG_NOTE
    out_b = "\n".join(lines)
    if crlf:
        out_b = out_b.replace("\n", "\r\n")
    if out_b.count(BACKLOG_NOTE) != 1:
        die("backlog note count wrong")
    io.open(P_BACKLOG, "w", encoding="utf-8", newline="").write(out_b)
    print("backlog.md OK: R2002 note appended to standing row")

    # ---------- 3. heartbeat.txt --------------------------------
    hb = io.open(P_HEART, encoding="utf-8", newline="").read()
    if not hb.endswith("\r\n"):
        hb += "\r\n"
    now = datetime.now()
    stamp = now.strftime("%Y-%m-%d %H:%M")[:-1] + "x +08:00"
    io.open(P_HEART, "w", encoding="utf-8", newline="").write(
        hb + stamp + HB_BODY + "\r\n")
    print("heartbeat.txt OK: R2002 line appended")

    # ---------- 4. status-export.json ---------------------------
    import check_export_consistency as cec  # noqa: E402
    derived, _state, _exp, pat = cec.recompute()
    exp = json.loads(io.open(P_EXPORT, encoding="utf-8").read())
    exp["export_ts"] = now.astimezone().isoformat(
        timespec="seconds")
    exp["ceo_face"] = {
        "current": CEO_CURRENT,
        "latest_artifact": CEO_LATEST,
        "next_milestone": CEO_NEXT,
    }
    results = exp["results"]
    label = pat["tick_row_label"]
    tick_row = ["2002", label]
    rrows = [r for r in results
             if isinstance(r, list) and len(r) >= 2
             and r[1] != label]
    new_results = ([["R2002", RESULTS_ROW]]
                   + rrows[:38] + [tick_row])
    exp["results"] = new_results
    sd = dict(derived)
    sd["method"] = ("machine-derived from state.json log per "
                    "BD-PROP-001 caliber (check_export_consistency"
                    ".recompute)")
    exp["self_drive"] = sd
    io.open(P_EXPORT, "w", encoding="utf-8", newline="").write(
        json.dumps(exp, ensure_ascii=False, indent=2) + "\n")
    print("status-export.json OK: results=%d self_drive window=%s"
          % (len(new_results), sd.get("window")))
    print("R2002 CLOSEOUT DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
