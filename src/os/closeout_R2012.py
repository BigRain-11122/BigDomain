# closeout_R2012.py - R2012 closeout driver: (1) state.json byte
# surgery (tick 2011 -> 2012, two-line log append via ps_escape,
# last_order / last_gord_tbl_rows re-anchor after the tail scan),
# (2) heartbeat.txt line, (3) status-export.json refresh (ceo_face +
# results R2012 row prepend + tick row 2012 + self_drive recompute).
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
    u"2026-10-17 R2012（五静全绿〔LEDGER @BigDomain 零行+DEC 348 基线持平+ORD 尾三新行"
    u"（06:27 CEO-PROXY 云批/07:3x @bm-b 活窗/09:0x @bm-c 导演席单）均非本司执行面=知悉不动"
    u"+benchmarks 当日已刷+树净零锁+对账当日证据在盘 R2002〕→P1 顶行全 gated〔雷达候清单/R777 候外件"
    u"/bootstrap 候物理件〕+P2 tech 开项全门控〔docker 缺位/logs 常设线·承 R1883..R2011 判读〕"
    u"→P3 explore FIFO 队头认领=lobby chat idem_seen TTL 过期窗例窗〔R1995 回补种子〕"
    u"·AC-IDT1..IDT8 判据预注册先于代码·AC-IDT 前缀全仓 git grep 零占用·查重先行=R1892 AC-S39..S43"
    u"+R1899 AC-S44..S48 在册=真缺口四边界律——产品件=test_client.py idem_boundary_cases()"
    u"〔suite-only·server.py+shipped config sha 双证零改动〕：固定窗不滑动（t+0.7 吸收后 t+1.8 重发越原 1.5s 窗重入新广播"
    u"·滑窗假想实现必判负）+过期重挂新 evt_id（即时重放 dup 回新 evt·原 evt 永不回带）"
    u"+错峰键窗独立（键二 t+0.9 记在键一已过期同批仍吸收）+恰 cap 无逐出（len==cap 双活键全吸收）"
    u"+超 cap FIFO 逐出序（幸存者吸收·被逐仍活键诚实重入·记账 2→3→4）+world 记账恰新鲜行零幻影"
    u"+卫生（恰界不可钉诚实注=活 monotonic 钟下 exact-instant 不可钉·序边界宽裕距代之）"
    u"——SUITE PASS 65/65 双跑 stdout 逐字节同一 sha16 01505bd0f187aa51〔首跑揪出 R1993 硬化漏网"
    u" AC-S8a 裸挂钟读数 3.1s/3.0s 漂移→同轮读数类化修（sub-5s/10s 显示类·真闸 elapsed<10 不动）二跑同一〕"
    u"·lobby 判据 57→65〔RUNNER 231 套件 1961→1969〕·RUNNER PASS 231/231 controls 7/7 271.4s 零回归"
    u"=qa/reconcile-all-R2012.log·矩阵再生 231/1969 green=231/231 --check byte-identical 22299B"
    u"·指纹 CLEAN domains=5·profile --daily --check PASS·census files=1526 flags=0 DRIFT-CLEAN〔健康方言免重锚〕"
    u"——explore 消费 1 补种 1 守恒〔idem_seen 门序预算例窗种子入列〕·fold R543 收账前置兑现"
    u"〔gauge 77834B margin 666B+收账预算必越线→tail-3 窗 fold R542 滚窗行+R2011 双行 5787B 压 1 滚窗行 3480B"
    u"·45 token 机械嵌入零丢失 gen543·post 75487B==predicted·archive §R2012 3 行 verbatim"
    u"+preop logs/state-preop-R2012.bak〕·ORD/GORD 基线重锚〔last_order→2026-10-17 09:0x"
    u"+last_gord_tbl_rows→522·旧值 455 为多轮尾扫未回写漂移·尾部新行过目均非本司面后重锚如实注〕·score 2）"
)

TOKENS_LINE = (
    "R2012 tokens: local=~1.4M api=0 api_reason=five-silence scan + P3 claim "
    "round all local (suite double-run x2 + AC-S8a readout-classing fix + "
    "full battery RUNNER 271.4s + matrix regen/check + fingerprint + "
    "profile + census + fold R543 gen/execute + state/export/heartbeat/"
    "queue edits + directed commit), zero cloud calls"
)

HB_BODY = (
    " R2012: P3 explore FIFO head delivered: lobby chat.send idem_seen"
    " TTL/FIFO boundary window (AC-IDT1..IDT8 pre-registered before"
    " code; fixed-window non-refresh, post-expiry re-arm with the NEW"
    " evt_id, per-key staggered windows, len==cap no-eviction +"
    " over-cap FIFO eviction order; exact-instant expiry honestly"
    " noted unpinnable against the live monotonic clock, order"
    " boundaries pinned). SUITE 65/65 double-run identical sha16"
    " 01505bd0f187aa51 (first double-run caught the R1993-hardening"
    " miss on AC-S8a raw wall-clock readout 3.1s/3.0s - classed"
    " same-round, real gate unchanged); RUNNER PASS 231/231 suites"
    " green controls 7/7 271.4s; matrix 231/1969 --check"
    " byte-identical 22299B; fingerprint CLEAN domains=5; profile"
    " --daily --check PASS; census files=1526 flags=0 DRIFT-CLEAN;"
    " fold R543 executed (45 tokens zero-loss, post 75487B); ORD/GORD"
    " baselines re-anchored after tail scan. Score 2."
)

CEO_CURRENT = (
    "R2012: P3 explore FIFO-head claim delivered end-to-end: lobby "
    "chat.send idem_seen TTL/FIFO boundary window - criteria "
    "pre-registered before code (AC-IDT1..IDT8, prefix "
    "zero-occupancy verified; dedup-first against the in-book R1892 "
    "restart-semantics and R1899 key-binding windows = the genuine "
    "four boundary gaps). Suite test_client.py idem_boundary_cases(): "
    "the TTL window is fixed at first processing (an absorbed replay "
    "never slides it - the t+1.8 resend re-enters past the original "
    "1.5s expiry), a post-expiry resend re-arms the cache with the "
    "NEW evt_id, windows stagger per-key independently, len==cap is "
    "the no-eviction boundary and the cap+1-th distinct key evicts "
    "the FIFO oldest (evicted-while-live re-entry), store accounting "
    "exact. SUITE 65/65 double-run identical sha16 01505bd0f187aa51; "
    "the first double-run caught a pre-existing raw wall-clock drift "
    "on AC-S8a (3.1s vs 3.0s, R1993-hardening miss) - readout "
    "classed same-round per that family, real gate unchanged; RUNNER "
    "PASS 231/231 suites green controls 7/7 271.4s zero regression; "
    "matrix 231/1969 --check byte-identical; fingerprint CLEAN "
    "domains=5; profile --daily --check PASS; census flags=0 "
    "DRIFT-CLEAN. fold R543 closeout-precedent honored (post 75487B, "
    "45 tokens zero-loss). ORD/GORD baselines re-anchored after the "
    "tail scan (three newest group rows are all non-BigDomain "
    "execution faces, acknowledged no-action). Score 2."
)
CEO_LATEST = (
    "qa/idem-boundary-R2012.log + src/sandbox/lobby/test_client.py "
    "idem_boundary_cases (SUITE 65/65, RUNNER 231/231 green, "
    "2026-10-17)"
)
CEO_NEXT = (
    "P3 explore queue: next open heads (stats_board month-window "
    "read, dev_sales_board month-window, dev_sales_board "
    "zero-listing boundary persist, yearbooks_combined multi-year "
    "persist) + R2012 reseed idem_seen gate-order budget row; P2 "
    "tech gated rows unchanged, window <=48h (by 2026-10-19)"
)

RESULTS_ROW = (
    "R2012: P3 explore FIFO-head claim delivered: lobby chat.send "
    "idem_seen TTL/FIFO boundary window (the R1995-backfilled seed "
    "row, strict topmost-open claim; criteria AC-IDT1..AC-IDT8 "
    "pre-registered in the explore.md claim row before code, AC-IDT "
    "prefix zero-occupancy git-grep-verified; dedup-first: R1892 "
    "AC-S39..S43 restart-semantics and R1899 AC-S44..S48 "
    "key-binding windows are in-book, the genuine gaps are four "
    "boundary laws). Suite-only round (server.py + shipped config "
    "sha256 pinned unchanged): (1) fixed-window non-refresh - the "
    "t+0.7 absorbed replay does not slide the 1.5s window, the t+1.8 "
    "resend re-enters as a fresh broadcast (a sliding "
    "implementation would fail this probe); (2) post-expiry re-arm - "
    "an immediate replay re-acks the NEW evt_id, the original is "
    "never re-acked; (3) per-key staggered windows - key two "
    "(remembered t+0.9) still absorbs in the same probe batch where "
    "key one already expired; (4) len==cap no-eviction boundary "
    "(both live keys absorb at exactly cap=2) + over-cap FIFO "
    "eviction order (third key evicts the oldest, survivor absorbs, "
    "evicted-while-still-TTL-live key re-enters, rows 2->3->4 "
    "exact); world store accounting = exactly the fresh entries, "
    "zero phantom. Honest boundary note: the exact-instant expiry "
    "predicate is unpinnable against the live monotonic clock in "
    "the subprocess server - order boundaries pinned with wide "
    "margins instead. SUITE PASS 65/65 double-run stdout "
    "byte-identical sha16 01505bd0f187aa51; the first double-run "
    "caught a pre-existing raw wall-clock readout drift on AC-S8a "
    "(3.1s vs 3.0s, an R1993-hardening miss) - classed same-round "
    "per that family (sub-5s/sub-10s display class, real "
    "elapsed<10 gate unchanged, fixture-level, zero product touch), "
    "second double-run identical. reconcile_all wiring lobby 57->65 "
    "(231 suites, criteria 1961->1969); RUNNER PASS 231/231 suites "
    "green controls 7/7 271.4s zero regression "
    "(qa/reconcile-all-R2012.log); matrix regen 231/1969 "
    "green=231/231 --check byte-identical 22299B; fingerprint CLEAN "
    "domains=5; profile --daily --check PASS; census files=1526 "
    "flags=0 DRIFT-CLEAN (new evidence file healthy-dialect exempt, "
    "no re-anchor). fold R543 closeout-precedent honored (gauge "
    "77834B margin 666B, tail-3 window 5787B -> 3480B rolling "
    "line, 45 tokens mechanically embedded zero-loss gen543, post "
    "75487B == predicted, archive verbatim + preop backup). "
    "ORD/GORD baselines re-anchored after tail scan (last_order -> "
    "2026-10-17 09:0x, gord table rows 455->522; the three newest "
    "rows - 06:27 CEO-PROXY game cloud batch, 07:3x bm-b "
    "live-window dispatch, 09:0x bm-c director reburn addendum - "
    "are all non-BigDomain execution faces, acknowledged no-action). "
    "Explore consume-1 reseed-1 (idem_seen gate-order budget seed). "
    "Score 2."
)


def die(msg):
    print("ABORT: %s" % msg)
    sys.exit(2)


def main():
    # ---------- 1. state.json byte surgery ----------------------
    raw = open(P_STATE, "rb").read()
    text = raw.decode("utf-8")
    if text.count('"tick": 2011,') != 1:
        die("tick anchor not unique")
    text = text.replace('"tick": 2011,', '"tick": 2012,')
    if text.count(u'"last_order": "2026-10-17 03:2x",') != 1:
        die("last_order anchor not unique")
    text = text.replace(
        u'"last_order": "2026-10-17 03:2x",',
        u'"last_order": "2026-10-17 09:0x",')
    if text.count('"last_gord_tbl_rows": 455,') != 1:
        die("gord anchor not unique")
    text = text.replace(
        '"last_gord_tbl_rows": 455,',
        '"last_gord_tbl_rows": 522,')
    tail = '"\r\n    ]\r\n}\r\n'
    if not text.endswith(tail):
        die("state tail layout unexpected")
    import logs_toolkit as LT  # noqa: E402
    lit1 = " " * 16 + LT.ps_escape(ROUND_LINE)
    lit2 = " " * 16 + LT.ps_escape(TOKENS_LINE)
    text = (text[:-len(tail)] + '",\r\n' + lit1 + ',\r\n' + lit2
            + '\r\n    ]\r\n}\r\n')
    new_bytes = text.encode("utf-8")
    if len(new_bytes) >= 78500:
        die("state over the line: %d" % len(new_bytes))
    st = json.loads(text)
    if st["tick"] != 2012 or len(st["log"]) != 19:
        die("tick/log shape wrong: %s %d" % (st["tick"], len(st["log"])))
    if not st["log"][-2].startswith(u"2026-10-17 R2012"):
        die("round line missing")
    if not st["log"][-1].startswith("R2012 tokens:"):
        die("tokens line missing")
    open(P_STATE, "wb").write(new_bytes)
    print("state.json OK: tick=2012 log-items=19 bytes=%d"
          % len(new_bytes))

    # ---------- 2. heartbeat.txt -------------------------------
    hb = io.open(P_HEART, encoding="utf-8", newline="").read()
    if not hb.endswith("\r\n"):
        hb += "\r\n"
    now = datetime.now()
    stamp = now.strftime("%Y-%m-%d %H:%M")[:-1] + "x +08:00"
    io.open(P_HEART, "w", encoding="utf-8", newline="").write(
        hb + stamp + HB_BODY + "\r\n")
    print("heartbeat.txt OK: R2012 line appended")

    # ---------- 3. status-export.json --------------------------
    import check_export_consistency as cec  # noqa: E402
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
    tick_row = ["2012", label]
    rrows = [r for r in results
             if isinstance(r, list) and len(r) >= 2
             and r[1] != label]
    new_results = ([["R2012", RESULTS_ROW]]
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
    print("R2012 CLOSEOUT DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
