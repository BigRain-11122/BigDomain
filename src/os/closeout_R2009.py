# closeout_R2009.py - R2009 closeout: (1) state.json byte-
# surgical append of the R2009 round+tokens log lines (CRLF +
# 16-space indent preserved, tick 2008 -> 2009, no whole-file
# re-serialization; zero external-baseline changes this round),
# (2) backlog.md radar standing-row R2009 note (window-8 OH
# sweep: two new lists, zero @BigDomain fit, zero claim),
# (3) explore.md claim-row done flip + R2010 persist-family
# month-roll reseed row, (4) heartbeat line, (5) status-export
# refresh (ceo_face + results R2009 row + self_drive recompute).
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
P_EXPLORE = os.path.join(ROOT, "state", "queue", "explore.md")
P_HEART = os.path.join(ROOT, "heartbeat.txt")
P_EXPORT = os.path.join(ROOT, "docs", "status-export.json")

ROUND_LINE = (
    u"2026-10-17 R2009（五静绿+雷达行窗 8 切片：OH-20261016-biglife"
    u"+OH-20261015-bigstream 两件新到清单过目毕=零 @BigDomain 命中"
    u"〔大小写不敏感全文 search 实测〕+收益透镜照判均非商业化/增长域"
    u"契合=零认领合法〔R1154/R1155/R1990 先例口径〕·下窗续候〕+"
    u"BigLife R777 复核档 life/**/*R777* 零命中=外件未达续候·对账日常化"
    u"当日已跑〔R2002 当日戳证据在盘〕——P3 explore FIFO 队头认领="
    u"数据集覆盖榜双窗并读板跨重启持久化例窗交付〔AC-CVDBP1.."
    u"CVDBP7 判据预注册先于代码在认领行·AC-CVDBP 前缀+套件名"
    u" test_datasub_coveragedualpersist 全仓 git grep 零占用实锚〕："
    u"套件三实例世界〔冻结钟锚世界+manual 前缀 SQL 交叉+关前双电池快照"
    u"→close 同库重开四脸字节同一→7 代表坏窗参门律零漂移〔计数恒定〕"
    u"→重启后十一月记录真路径双区续接〔新注册 city-transit+ada 订阅"
    u"期窗十月记录十一月+carol 十月期投递记录十一月=双溯源探针·oct"
    u" 窗区三既有行字节冻结零渗透+nov 窗区 mobility/parks 冻结与"
    u" air 续接 0→1+transit {1hh,1sub,0dlv}+full 区携全量〕→纯读律"
    u"→双重启稳定〕SUITE PASS 7/7 双跑 stdout 逐字节同一 sha16 "
    u"9f7cd3f25179e272·reconcile_all SUITES 接线 ledger-datasub-"
    u"coveragedualpersist criteria 7〔228→229 套件〕·RUNNER PASS "
    u"229/229 suites green reconcile controls 7/7 272.0s 零回归="
    u"qa/reconcile-all-R2009.log〔battery_R2009.py 驱动·R2008 先例"
    u"包装器〕·矩阵再生 229 套件 1947 判据 green=229/229 --check "
    u"byte-identical·census CENSUS-COMPLETE 1518 件全分类·证据="
    u"qa/coveragedual-persist-R2009.log 三节〔套件双跑+RUNNER+矩阵〕"
    u"·fold R541 收账前置兑现〔轮首 gauge 78073B margin 427B+收账两行"
    u"预算 ~3.4KB 必越线→tail-3 窗 fold R540 滚窗行+R2008 双行 6023B"
    u" 压 1 滚窗行·37 token 全字面嵌零丢失·首跑 token-missing 37+"
    u"gate-exceed 双检 fail-closed 拦截如实注〔reserve-bytes 语义="
    u"收账预留非 gate 值·修参 3400+全嵌后过〕·archive §R2009 "
    u"verbatim+preop logs/state-preop-R2009.bak·post 73344B=="
    u"predicted〕·score 2〔能跑实物=新 persist 套件+RUNNER 电池"
    u" 229 扩容全绿〕）"
)

TOKENS_LINE = (
    u"R2009 tokens: local=~1.5M api=0 api_reason=five-silence scan + "
    u"P3 claim round all local (suite double-run + full battery "
    u"RUNNER 272.0s via battery_R2009 driver + matrix regen/check + "
    u"census + fold R541 + closeout byte surgery + export recompute "
    u"+ directed commit), zero cloud calls"
)

HB_BODY = (
    " R2009: P3 explore FIFO-head claim delivered: coverage_board_"
    "dual cross-restart persistence example (suite test_datasub_"
    "coveragedualpersist.py, AC-CVDBP1..7 pre-registered before "
    "code; three-instance world: byte-identical dual-battery "
    "replay + gate zero-drift + dual-zone continuation + pure-read "
    "+ double-restart stability; SUITE 7/7 double-run identical "
    "sha16 9f7cd3f25179e272); RUNNER PASS 229/229 suites green "
    "controls 7/7 272.0s; matrix 229 suites 1947 criteria --check "
    "byte-identical; census CENSUS-COMPLETE; radar window-8 sweep: "
    "OH-20261016-biglife + OH-20261015-bigstream zero @BigDomain "
    "fit, zero claim; fold R541 pre-closeout 78073B->73344B. "
    "Score 2."
)

BACKLOG_NOTE = (
    u"〔R2009 注记：窗 8 新到候选清单两件过目毕=OH-20261016-biglife.md"
    u"（10-16 落库·BigLife 域切片）+OH-20261015-bigstream.md（10-15 落库"
    u"·BigStream 域切片）——两件 @BigDomain 命中零（大小写不敏感全文"
    u" search 实测）+收益透镜照判均非商业化/增长域契合=零认领合法"
    u"（R1154/R1155/R1990 先例口径）·下窗清单到达续候〕"
)

DONE_NOTE = (
    u"——〔done 2026-10-17 R2009：AC-CVDBP1..CVDBP7 全过：套件 "
    u"test_datasub_coveragedualpersist.py 三实例世界（锚世界+关前"
    u"双电池快照→同库重开四脸字节同一→门律零漂移→十一月记录真路径"
    u"双区续接〔双溯源探针：ada 期窗十月记录十一月订阅+carol 十月期"
    u"投递十一月记录·oct 窗区既有行字节冻结零渗透+nov 窗区 air 续接"
    u" 0→1+transit 新行〕→纯读律→双重启稳定）SUITE PASS 7/7 双跑"
    u" stdout 逐字节同一 sha16 9f7cd3f25179e272+reconcile_all 接线"
    u" ledger-datasub-coveragedualpersist criteria 7+RUNNER PASS "
    u"229/229 suites green controls 7/7 272.0s 零回归+矩阵 229/1947 "
    u"--check byte-identical+census CENSUS-COMPLETE·证据="
    u"qa/coveragedual-persist-R2009.log 三节〕"
)

RESEED_ROW = (
    u"- [ ] 数据集覆盖榜双窗并读板月滚例窗探索（coverage month-window"
    u" 月滚族：bannerroll R1883 判读——跨月记录世界下双窗板月差分呈现"
    u"+十月窗冻结/十一月窗滚动语义例〔同族先例 R1883 bannerroll/"
    u"R1884 persist/R2009 coveragedualpersist·AC 前缀认领时 git grep"
    u" 零占用再验〕——种子源=datasub.py coverage_board_dual persist "
    u"R2009 在册·R2009 收账补种）\n"
)

CEO_CURRENT = (
    "R2009: P3 explore FIFO-head claim delivered end-to-end: "
    "coverage_board_dual cross-restart persistence example - "
    "criteria pre-registered before code (AC-CVDBP1..7), suite "
    "test_datasub_coveragedualpersist.py three-instance world "
    "(byte-identical dual-battery replay, gate zero-drift, "
    "dual-zone continuation with two provenance probes, pure-read "
    "law, double-restart stability), SUITE 7/7 double-run "
    "identical; full battery RUNNER PASS 229/229 suites green "
    "controls 7/7 272.0s zero regression; matrix 229/1947 --check "
    "byte-identical; census CENSUS-COMPLETE. Radar window-8 sweep: "
    "two new OH lists zero @BigDomain fit (zero claim, legal). "
    "fold R541 pre-closeout 78073B->73344B. Score 2."
)
CEO_LATEST = (
    "qa/coveragedual-persist-R2009.log + src/sandbox/ledger/"
    "test_datasub_coveragedualpersist.py (SUITE 7/7, RUNNER "
    "229/229 green, 2026-10-17)"
)
CEO_NEXT = (
    "P3 explore reseed head: coverage dual-board month-roll example "
    "(R2010 window; plus P2 tech gated rows unchanged), window "
    "<=48h (by 2026-10-19)"
)

RESULTS_ROW = (
    "R2009: P3 explore FIFO-head claim delivered: coverage_board_"
    "dual cross-restart persistence example. Criteria AC-CVDBP1.."
    "CVDBP7 pre-registered in the explore.md claim row before code "
    "(prefix + suite filename git-grep zero-occupied). Suite "
    "test_datasub_coveragedualpersist.py: frozen-clock anchor "
    "world + manual prefix-SQL cross derivation, close -> same-db "
    "reopen four-face battery byte-identical, seven bad windows "
    "gate zero-drift (counts constant), post-restart November-"
    "record real-path continuation on both zones (new registration "
    "city-transit + ada subscription with October period recorded "
    "in November + carol October-period air delivery recorded in "
    "November = double provenance probe; October window zone rows "
    "byte-frozen with zero permeation, November zone air continues "
    "0->1 and transit enters 1hh/1sub/0dlv), pure-read law, "
    "double-restart stability. SUITE PASS 7/7, double-run stdout "
    "byte-identical sha16 9f7cd3f25179e272. reconcile_all SUITES "
    "wiring ledger-datasub-coveragedualpersist criteria 7 (229 "
    "suites); RUNNER PASS 229/229 suites green, reconcile controls "
    "7/7, 272.0s zero regression (qa/reconcile-all-R2009.log via "
    "battery_R2009 driver); matrix regen 229 suites 1947 criteria "
    "--check byte-identical; census CENSUS-COMPLETE 1518 files. "
    "Radar window-8 sweep: OH-20261016-biglife + OH-20261015-"
    "bigstream both zero @BigDomain hit (case-insensitive search) "
    "and non-commercialization fit by the revenue lens = zero "
    "claim legal. BigLife R777 review dossier still absent "
    "(life/**/*R777* zero hit, external wait). fold R541 pre-"
    "closeout: gauge 78073B margin 427B, tail-3 window fold, 37 "
    "tokens embedded, first run fail-closed on token-missing(37) + "
    "gate-exceed (reserve-bytes semantics = closeout reserve, "
    "fixed to 3400) - honest note. Score 2 (runnable artifact + "
    "battery growth)."
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
    if raw_s.count(b'"tick": 2008,') != 1:
        die("tick anchor not unique")
    if not raw_s.endswith(b"\r\n"):
        die("state must end with CRLF")
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
    out_s = out_s.replace(b'"tick": 2008,',
                         b'"tick": 2009,', 1)
    sz = len(out_s)
    if sz >= 78500:
        die("state over the line: %d" % sz)
    io.open(P_STATE, "wb").write(out_s)
    st = json.loads(io.open(P_STATE, encoding="utf-8").read())
    if st["tick"] != 2009:
        die("surgery verify failed (tick)")
    if st["log"][-2] != ROUND_LINE or st["log"][-1] != TOKENS_LINE:
        die("content verify failed")
    d = io.open(P_STATE, "rb").read()
    if d.count(b"\n") != d.count(b"\r\n"):
        die("bare LF leaked")
    print("state.json OK: tick=2009 bytes=%d (cap 78500)" % sz)

    # ---------- 2. backlog.md radar standing-row note ------------
    raw_b = io.open(P_BACKLOG, encoding="utf-8", newline="").read()
    crlf_b = "\r\n" in raw_b
    norm_b = (raw_b.replace("\r\n", "\n") if crlf_b else raw_b)
    bl = norm_b.split("\n")
    hits = [i for i, ln in enumerate(bl)
            if u"雷达路由闭环本司承接行" in ln]
    if len(hits) != 1:
        die("radar row found=%d" % len(hits))
    bi = hits[0]
    if BACKLOG_NOTE in bl[bi]:
        die("backlog note already present")
    bl[bi] = bl[bi] + BACKLOG_NOTE
    out_b = "\n".join(bl)
    if crlf_b:
        out_b = out_b.replace("\n", "\r\n")
    if out_b.count(BACKLOG_NOTE) != 1:
        die("backlog note count wrong")
    io.open(P_BACKLOG, "w", encoding="utf-8", newline="").write(out_b)
    print("backlog.md OK: R2009 radar note appended")

    # ---------- 3. explore.md done flip + reseed -----------------
    raw_e = io.open(P_EXPLORE, encoding="utf-8", newline="").read()
    crlf_e = "\r\n" in raw_e
    norm_e = (raw_e.replace("\r\n", "\n") if crlf_e else raw_e)
    el = norm_e.split("\n")
    ehits = [i for i, ln in enumerate(el)
             if ln.startswith(u"- [ ] 数据集覆盖榜双窗并读板跨重启持久化例窗探索")]
    if len(ehits) != 1:
        die("explore claim row found=%d" % len(ehits))
    ei = ehits[0]
    el[ei] = el[ei].replace(u"- [ ] ", u"- [x] ", 1) + DONE_NOTE
    if not norm_e.endswith("\n"):
        norm_e += "\n"
    out_e = "\n".join(el) + RESEED_ROW
    if not out_e.endswith("\n"):
        out_e += "\n"
    if crlf_e:
        out_e = out_e.replace("\n", "\r\n")
    if out_e.count(DONE_NOTE) != 1:
        die("done note count wrong")
    io.open(P_EXPLORE, "w", encoding="utf-8", newline="").write(out_e)
    print("explore.md OK: R2009 done flip + R2010 reseed row")

    # ---------- 4. heartbeat.txt --------------------------------
    hb = io.open(P_HEART, encoding="utf-8", newline="").read()
    if not hb.endswith("\r\n"):
        hb += "\r\n"
    now = datetime.now()
    stamp = now.strftime("%Y-%m-%d %H:%M")[:-1] + "x +08:00"
    io.open(P_HEART, "w", encoding="utf-8", newline="").write(
        hb + stamp + HB_BODY + "\r\n")
    print("heartbeat.txt OK: R2009 line appended")

    # ---------- 5. status-export.json ---------------------------
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
    tick_row = ["2009", label]
    rrows = [r for r in results
             if isinstance(r, list) and len(r) >= 2
             and r[1] != label]
    new_results = ([["R2009", RESULTS_ROW]]
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
    print("R2009 CLOSEOUT DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
