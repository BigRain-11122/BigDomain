# closeout_R2016.py - R2016 closeout driver: (1) state.json byte
# surgery (tick 2015 -> 2016, two-line log append via ps_escape,
# last_gord_tbl_rows re-anchor 533 -> 455 after the five-still
# tail scan: the group compacted their table, the tail line is
# unchanged at 13:5x = zero new orders, negative delta is table
# shrinkage honestly noted), (2) heartbeat.txt line, (3)
# status-export.json refresh (ceo_face + results R2016 row
# prepend + tick row 2016 + self_drive recompute).
# ASCII script logic; CJK content lives in the constants.
import io
import json
import os
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)

P_STATE = os.path.join(ROOT, "src", "os", "state.json")
P_HEART = os.path.join(ROOT, "heartbeat.txt")
P_EXPORT = os.path.join(ROOT, "docs", "status-export.json")

ROUND_LINE = (
    u"2026-10-17 R2016（五静检出=[STATE] FLAG eol_bare_lf=29 唯一异常〔R2015 收口裸"
    u" LF→eol --fix 修 29 行 CRLF·json_eq=true 零内容损+缩进病 19 行 8→16 空格 eol"
    u" --fix-indent 同轮修=轮首首件〕+LEDGER @BigDomain 零新行+DEC 356 基线持平+ORD 尾"
    u" 13:5x 基线持平+GORD 表缩 533→455=集团侧折叠非新令（尾行 13:5x 持平·负增量=表收缩"
    u"如实注）+benchmarks 当日已刷+树净——P1 顶行全 gated〔雷达候清单/BigLife R777 候外件"
    u"/bootstrap 候物理件·对账当日已跑 R2002〕+P2 tech 开项全门控〔docker 缺位/logs 常设线"
    u"按需/R1727 散布态留窗/R2003 复评窗 10-24〕→P3 explore FIFO 队头认领=展示橱窗统计榜月"
    u"份窗读面跨重启持久化例窗〔R2015 补种〕·AC-SSMP1..SSMP7 判据预注册先于代码·AC-SSMP"
    u" 前缀+套件名+注册行名三面全仓 git grep 零占用实锚——产品件=test_showcase_statsmonth"
    u"persist.py〔suite-only·产品三件 sha256 双证零改动〕：七形窗读族（full/cap2/wcur/"
    u"wcap2/wprev/whist/wzero2099）关前控制锚〔信封键集钉死+wcur/wprev==独立 SQL substr"
    u"(acted_utc,1,7) 记录时间重数+displayed_now 跨面互证+帽读==窗读决序尾切片+双调字节"
    u"同一+门序探针 E_SH_BAD_LIMIT 先拒〕+全栈跨重启七形逐字节同一〔sh→led close→同 db/"
    u"cfg/sh 路径重建·零内存态漂移〕+重启后现月真路径活态〔zeta-gal place→wcur zeta 行"
    u" {places 1,retracts 0,displayed_now 1} 零缓存再算+未触行冻结+prev/hist/2099 窗字节"
    u"冻结〕+重启后新月 fixture 活态〔R1730 直插律·mu-gal hist 窗行 0→1 记录时间律+cur/"
    u"prev/2099 冻结〕+门族跨重启同码〔9 坏窗全拒 E_SH_BAD_WINDOW+limit 门先拒+探针批计数恒"
    u"定〕+第三实例稳定+纯读律+卫生——SUITE PASS 7/7 双跑 stdout 逐字节同一 sha16 "
    u"40b64bbeee45dcfd 2338B〔模块首验即净〕·RUNNER PASS 233/233 判据 1983→1990〔SUITES "
    u"232→233〕controls 7/7 282.4s=qa/reconcile-all-R2016.log·四电池面 VERDICT PASS〔矩阵"
    u"再生 233/1990 --check byte-identical+指纹 CLEAN domains=5+profile daily+main 双面+"
    u"census --update-baseline 后 DRIFT-CLEAN〕·证据=qa/showcase-statsmonthpersist-R2016."
    u"log——explore 消费 1 补种 1 守恒〔月份窗零注册边界世界跨重启例窗种子入列〕·fold R546"
    u" 收账前置兑现〔gauge 77052B margin 1448B+收账预算必越线→tail-3 窗 fold R545 滚窗行"
    u"+R2015 round+tokens 5120B 压 1 滚窗行 kept=0·61 token 机械嵌入零丢失 gen546·post "
    u"73986B==predicted·archive §R2016 3 行 verbatim+preop logs/state-preop-R2016.bak"
    u"·fold 拒面缩进病当窗修=R1710 病族 R1717 工具正法实弹〕·GORD 基线重锚 533→455〔表收"
    u"缩如实注〕·score 2）"
)

TOKENS_LINE = (
    "R2016 tokens: local=~1.3M api=0 api_reason=five-silence scan + "
    "EOL/indent repair + P3 claim round all local (suite double-run "
    "x2 + full battery RUNNER 282.4s + matrix regen/check + "
    "fingerprint + profile daily+main + census update-baseline/check "
    "+ fold R546 gen/execute + state/export/heartbeat/queue edits + "
    "directed commit), zero cloud calls"
)

HB_BODY = (
    " R2016: P3 explore FIFO head delivered: showcase stats_board"
    " month-window cross-restart persistence example window"
    " (AC-SSMP1..SSMP7 pre-registered before code; seven-form window"
    " read family byte-identical across a full-stack close/reopen;"
    " post-restart current-month true-path recompute + new-month"
    " direct-INSERT recompute with old windows byte-frozen; gate"
    " family same-code on the restarted instance; third instance"
    " stability; pure-read law + hygiene). SUITE 7/7 double-run"
    " identical sha16 40b64bbeee45dcfd; RUNNER PASS 233/233 criteria"
    " 1990 controls 7/7 282.4s; four-face battery VERDICT PASS"
    " (matrix --check byte-identical, fingerprint CLEAN domains=5,"
    " profile daily+main, census DRIFT-CLEAN); fold R546"
    " closeout-precedent honored (61 tokens zero-loss, post 73986B;"
    " the fold's layout refusal caught the R2015 closeout indent"
    " disease - repaired same-round via eol --fix-indent); GORD"
    " baseline re-anchored 533->455 (group-side table compaction,"
    " tail line unchanged). Score 2."
)

CEO_CURRENT = (
    "R2016: P3 explore FIFO-head claim delivered end-to-end: the "
    "showcase stats_board month-window cross-restart persistence "
    "example window (the R2015 reseed; criteria AC-SSMP1..SSMP7 "
    "pre-registered in the explore.md claim row before code, "
    "prefix/suite/registry names git-grep zero-occupancy "
    "verified). Suite test_showcase_statsmonthpersist.py "
    "(suite-only, three product files sha256 pinned unchanged): "
    "the seven-form window read family {full, cap2, wcur, wcap2, "
    "wprev, whist, wzero} is pinned pre-close (envelope key sets, "
    "record-time SQL cross recount, displayed_now cross-face "
    "probe, capped==windowed decisive tail slice, gate-order "
    "probe E_SH_BAD_LIMIT first), then proven byte-identical "
    "across a full-stack close/reopen on the same db/cfg paths "
    "(zero in-memory drift), then the restarted instance recomputes "
    "zero-cache: a current-month true-path place updates only the "
    "current window board (old windows byte-frozen) and a new-month "
    "direct-INSERT fixture (R1730 law) updates only that month's "
    "board; the 9-form malformed-window gate family refuses with "
    "the same codes on the restarted instance; third instance "
    "stable. SUITE 7/7 double-run byte-identical sha16 "
    "40b64bbeee45dcfd; RUNNER PASS 233/233 suites green criteria "
    "1990 controls 7/7 282.4s zero regression; four-face battery "
    "VERDICT PASS (matrix 233/1990 --check byte-identical, "
    "fingerprint CLEAN domains=5, profile daily+main, census "
    "DRIFT-CLEAN after legal re-anchor). fold R546 "
    "closeout-precedent honored (gauge 77052B margin 1448B -> "
    "tail-3 window 5120B -> one rolling line, 61 tokens "
    "zero-loss, post 73986B == predicted; the fold's layout "
    "refusal caught the previous closeout's 19-line indent "
    "disease, repaired same-round via eol --fix-indent). GORD "
    "baseline re-anchored 533->455: the group compacted their "
    "table, the tail line is unchanged at 13:5x = zero new "
    "orders. Score 2."
)
CEO_LATEST = (
    "qa/showcase-statsmonthpersist-R2016.log + "
    "src/sandbox/ledger/test_showcase_statsmonthpersist.py "
    "(SUITE 7/7 double-run identical, RUNNER 233/233 green, "
    "2026-10-17)"
)
CEO_NEXT = (
    "P3 explore queue: next open heads (dev_sales_board "
    "month-window, dev_sales_board zero-listing boundary persist, "
    "yearbooks_combined multi-year persist, coverage-dual "
    "month-roll) + R2016 reseed statsmonth zero-reg boundary "
    "persist row; P2 tech gated rows unchanged, window <=48h "
    "(by 2026-10-19)"
)

RESULTS_ROW = (
    "R2016: P3 explore FIFO-head claim delivered: showcase "
    "stats_board month-window cross-restart persistence example "
    "window (the R2015-reseed row, strict topmost-open claim; "
    "criteria AC-SSMP1..AC-SSMP7 pre-registered in the "
    "explore.md claim row before code, AC-SSMP prefix + suite + "
    "registry names git-grep zero-occupancy verified). "
    "Suite-only round (showcase.py + both shipped config.json "
    "sha256 pinned unchanged): (1) pre-close control anchor - "
    "the seven-form window read family {full, cap2, wcur, wcap2, "
    "wprev, whist, wzero-2099} pinned with exact envelope key "
    "sets (2/6/3/7 keys), wcur/wprev rows cross-checked against "
    "the independent SQL substr(acted_utc,1,7) recount and the "
    "_displayed_rows_window view face, capped==windowed "
    "decisive tail slice with the honest overflow block, family "
    "double-call byte-identical, bad limit + bad window refuses "
    "E_SH_BAD_LIMIT first; (2) full-stack close (sh -> led) then "
    "rebuild on the same db/cfg/sh paths: all seven forms "
    "byte-identical (derived month-window face carries zero "
    "in-memory state across restart); (3) post-restart "
    "current-month true-path place into the zero-activity "
    "showcase recomputes the current window row zero-cache "
    "{places=1, retracts=0, displayed_now=1} with the alpha/mu "
    "rows and the prev/hist/2099 window boards byte-frozen; (4) "
    "post-restart new-month direct-INSERT fixture (R1730 law): "
    "the hist-month window mu row recomputes 0->1 by the "
    "record-time law while cur/prev/2099 boards stay "
    "byte-frozen; (5) the 9-form malformed-window gate family "
    "refuses E_SH_BAD_WINDOW with the same codes on the "
    "restarted instance, limit gate order preserved, probe batch "
    "row counts flat; (6) third instance == second-instance "
    "final state byte-identical; (7) pure-read law + hygiene "
    "(read battery counts flat, method source zero write "
    "statements zero RNG, suite pure ASCII zero network "
    "imports, world db outside the repo). SUITE PASS 7/7 "
    "double-run stdout byte-identical sha16 40b64bbeee45dcfd "
    "(2338B, module first-verification clean); reconcile_all "
    "wiring ledger-showcase-statsmonth-persist criteria 7 (233 "
    "suites, criteria 1983->1990); RUNNER PASS 233/233 suites "
    "green controls 7/7 282.4s zero regression "
    "(qa/reconcile-all-R2016.log); four-face battery VERDICT "
    "PASS (matrix regen 233/1990 --check byte-identical, "
    "fingerprint CLEAN domains=5, runner_profile --daily and "
    "main --check PASS, qa-writer census --update-baseline then "
    "--check DRIFT-CLEAN for the two new evidence files, "
    "R1996/R1998/R2009/R2010 re-anchor precedent). fold R546 "
    "closeout-precedent honored: gauge 77052B margin 1448B, "
    "tail-3 window (fold R545 rolling line + R2015 round + "
    "R2015 tokens, 5120B content) folded to one rolling line "
    "kept=0, 61 tokens mechanically embedded zero-loss "
    "(gen546, PAT single-source import), post 73986B == "
    "predicted, archive verbatim + preop backup "
    "logs/state-preop-R2016.bak; the fold's E_STATE_LAYOUT "
    "refusal caught the previous closeout's 19-line 8-space "
    "indent disease - repaired same-round via eol "
    "--fix-indent (content_eq/json_eq true, post == predicted), "
    "R1710/R1717 family precedent. GORD baseline re-anchored "
    "533->455 after the five-still tail scan (the group "
    "compacted their table; the tail line is unchanged at "
    "13:5x = zero new orders; negative delta is shrinkage, "
    "honestly noted). The R2015 closeout's bare-LF disease was "
    "repaired at round start via eol --fix (29 lines, json_eq "
    "true). Explore consume-1 reseed-1 (statsmonth zero-reg "
    "boundary persist seed). Score 2."
)


def die(msg):
    print("ABORT: %s" % msg)
    sys.exit(2)


def main():
    # ---------- 1. state.json byte surgery ----------------------
    raw = open(P_STATE, "rb").read()
    text = raw.decode("utf-8")
    if text.count('"tick": 2015,') != 1:
        die("tick anchor not unique")
    text = text.replace('"tick": 2015,', '"tick": 2016,')
    if text.count('"last_gord_tbl_rows": 533,') != 1:
        die("gord anchor not unique")
    text = text.replace('"last_gord_tbl_rows": 533,',
                       '"last_gord_tbl_rows": 455,')
    tail = '"\r\n  ]\r\n}\r\n'
    if not text.endswith(tail):
        die("state tail layout unexpected")
    import logs_toolkit as LT                     # noqa: E402
    lit1 = " " * 16 + LT.ps_escape(ROUND_LINE)
    lit2 = " " * 16 + LT.ps_escape(TOKENS_LINE)
    text = (text[:-len(tail)] + '",\r\n' + lit1 + ',\r\n' + lit2
            + '\r\n  ]\r\n}\r\n')
    new_bytes = text.encode("utf-8")
    if len(new_bytes) >= 78500:
        die("state over the line: %d" % len(new_bytes))
    st = json.loads(text)
    if st["tick"] != 2016 or len(st["log"]) != 19:
        die("tick/log shape wrong: %s %d" % (st["tick"],
                                              len(st["log"])))
    if not st["log"][-2].startswith(u"2026-10-17 R2016"):
        die("round line missing")
    if not st["log"][-1].startswith("R2016 tokens:"):
        die("tokens line missing")
    if st["log"][-3].find(u"fold R546") < 0:
        die("fold rolling line missing")
    open(P_STATE, "wb").write(new_bytes)
    print("state.json OK: tick=2016 log-items=19 bytes=%d"
          % len(new_bytes))

    # ---------- 2. heartbeat.txt -------------------------------
    hb = io.open(P_HEART, encoding="utf-8", newline="").read()
    if not hb.endswith("\r\n"):
        hb += "\r\n"
    now = datetime.now()
    stamp = now.strftime("%Y-%m-%d %H:%M")[:-1] + "x +08:00"
    io.open(P_HEART, "w", encoding="utf-8", newline="").write(
        hb + stamp + HB_BODY + "\r\n")
    print("heartbeat.txt OK: R2016 line appended")

    # ---------- 3. status-export.json --------------------------
    import check_export_consistency as cec          # noqa: E402
    derived, _state, _exp, pat = cec.recompute()
    exp = json.loads(io.open(P_EXPORT, encoding="utf-8").read())
    exp["export_ts"] = now.astimezone().isoformat(timespec="seconds")
    exp["ceo_face"] = {
        "current": CEO_CURRENT,
        "latest_artifact": CEO_LATEST,
        "next_milestone": CEO_NEXT,
    }
    results = exp["results"]
    label = pat["tick_row_label"]
    tick_row = ["2016", label]
    rrows = [r for r in results
             if isinstance(r, list) and len(r) >= 2
             and r[1] != label]
    new_results = ([["R2016", RESULTS_ROW]]
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
    print("R2016 CLOSEOUT DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
