"""R2115 closeout: take over and verify the interrupted refund-exposure
window, then write the board rows, state bookkeeping and export refresh.

ASCII source (coding law); user-facing text lives in the UTF-8 data
blocks below. Idempotent: every write is guarded by a marker check.
"""

import datetime
import io
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
STATE = os.path.join(ROOT, "src", "os", "state.json")
EXPORT = os.path.join(ROOT, "docs", "status-export.json")
EXPLORE = os.path.join(ROOT, "state", "queue", "explore.md")
BACKLOG = os.path.join(ROOT, "src", "os", "backlog.md")

DONE_NOTE = (
    " [done 2026-10-25 R2115]（前窗中断遗留产物由本窗验证收口：判据 "
    "AC-RPX1..AC-RPX8 于本行预注册，诚实注=产品代码先于判据行文本同窗落盘已披露；"
    "套件 src/sandbox/ledger/test_apimarket_refundexposure.py SUITE PASS 8/8 "
    "双跑判据行逐字节同一 sha16 112e6f0d43928930（qa/apimarket-refundexposure-R2115.log "
    "+ -2·本窗以 python 单写者重出为 utf-8 LF，前窗 PS 重定向方言件已覆盖）；"
    "电池 RUNNER PASS 320/320 suites + reconcile controls 7/7 533.8s"
    "=qa/reconcile-all-R2115.log（651184B）；矩阵按本窗证据重生成 "
    "320 suites/2668 criteria 后 --check byte-identical；census DRIFT-CLEAN "
    "files=1783 flags=0；REPORT_SCHEMA 7→8 加法升级且 refund_risk 家族进 attention 摘要"
    "=本面无消费者闲置形态的直接反证）"
)

BACKLOG_ROW = (
    "- [x] P3 explore 自补种并同窗认领（R2115）apimarket 卖家侧**退款敞口读面**"
    "（api_refund_exposure）——退款门在卖家已花掉分成时 fail-closed "
    "E_AM_REFUND_UNFUNDABLE，但没有任何面事先告诉任何人「这笔钱已经不在账上了」；"
    "本面从未退款购买的存量 dev_share 派生敞口、以活账本余额判可垫付、差额即缺口，"
    "行集权威=挂牌表 distinct 卖家（密集·零成交卖家在榜），退役不销债，纯读零 token，"
    "并接入唯一消费者：collect_attention 增 refund_risk 家族（shortfall>0 · high）"
    "+REPORT_SCHEMA 7→8 加法升级。[done 2026-10-25 R2115]"
    "（判据 AC-RPX1..AC-RPX8 预注册于 state/queue/explore.md 同名行·"
    "套件 SUITE PASS 8/8 双跑判据行同一 sha16 112e6f0d43928930="
    "qa/apimarket-refundexposure-R2115.log+-2·电池 RUNNER PASS 320/320 suites+controls 7/7 "
    "533.8s=qa/reconcile-all-R2115.log·矩阵 320 suites/2668 criteria --check byte-identical·"
    "census DRIFT-CLEAN files=1783 flags=0）"
)

LOG_LINES = [
    "2026-10-25 R2115 (this window opened on an INTERRUPTED predecessor:"
    " the R2115 refund-exposure product diff, its suite, three qa logs,"
    " the queue row and the reconcile wiring were already on disk"
    " uncommitted while state.json still ended at R2114 - no live ledger"
    " battery and no index.lock, so this was a crashed window, not a"
    " concurrent executor; the round therefore verified and closed that"
    " work instead of reseeding. Five-silence scan: decisions.md carries"
    " zero new content-addressed tokens against the stored baseline (the"
    " assistive UTF-8 row count reads 209 and the baseline holds 260"
    " tokens of which 91 are absent after a rotation - zero new, so zero"
    " action); ledger zero new @BigDomain transfer rows; group orders"
    " baseline unchanged at 2026-10-24 12:17; benchmarks refreshed"
    " 2026-10-24 inside 7 days; both daily standing rows for 2026-10-25"
    " were already stamped by R2105 so neither was re-run; the only tree"
    " dirt was the R2115 payload itself) - the seller-side refund"
    " exposure read face. refund_api fails closed with"
    " E_AM_REFUND_UNFUNDABLE when the seller already spent the proceeds"
    " (the AC-L2 balance floor is constitutional), yet no face warned"
    " anyone the money to fund the reversal was gone: a seller could not"
    " answer how much of the balance is already spoken for, and the"
    " operator could not answer who would break a refund today. Product:"
    " APIMarketFace.api_refund_exposure(dev_account=None) derives the"
    " exposure from rows that already exist - the unrefunded purchases'"
    " stored dev_share is the maximum a seller can be asked to return and"
    " the live ledger balance says how much is actually fundable, with"
    " the shortfall as the honest gap. Seven-key envelope with nine-key"
    " rows, the row set authority the listing table (every distinct"
    " seller appears, zero-sale sellers included, rows a total order on"
    " dev_account); liability is never recomputed from a price, so a"
    " repricing moves it by nothing; a refund removes exactly its own"
    " dev_share from the liability and lowers the balance by the same"
    " amount; a seller with no ledger account reports balance 0 with"
    " balance_known False instead of raising; retirement keeps the"
    " obligation; the account gate runs before any read; the face is a"
    " pure read with zero token movement and is byte-identical across"
    " restarts. Consumer: collect_attention grows a refund_risk family"
    " (shortfall>0 sellers, severity high) and REPORT_SCHEMA moves 7 -> 8"
    " additively, so the face is not shipped in the no-consumer idle"
    " form. Suite src/sandbox/ledger/test_apimarket_refundexposure.py"
    " SUITE PASS 8/8 with criterion lines byte-identical across the"
    " double run (qa/apimarket-refundexposure-R2115.log + -2, sha16"
    " 112e6f0d43928930) - this window regenerated both evidence files"
    " with a python single writer as utf-8 LF because the predecessor had"
    " captured them through PowerShell redirection in the ps-utf16"
    " dialect (the census was re-run afterwards: DRIFT-CLEAN). Battery"
    " RUNNER PASS 320/320 suites green plus reconcile controls 7/7 in"
    " 533.8s (qa/reconcile-all-R2115.log, 651184 bytes; the predecessor's"
    " own log had died on a 300s subprocess timeout inside"
    " test_apimarket_report_refundregister.py - the same suite re-timed"
    " at 81s in this window and 41.6s inside the battery, so the timeout"
    " was machine load during the crash, not a product hang); suite"
    " matrix regenerated to 320 suites / 2668 criteria and --check"
    " byte-identical; evidence census files=1783 flags=0 DRIFT-CLEAN.",
    "R2115 tokens: local=~75k api=0 api_reason=five-silence scan +"
    " crashed-window takeover (suite double-run re-captured in utf-8 LF,"
    " battery timeout diagnosis) + full battery 320/320 + matrix"
    " regen/check + census + queue/backlog done marks + state/export"
    " closeout, zero cloud calls",
]

RESULTS_TEXT = (
    "R2115: take over and verify the interrupted refund-exposure window."
    " The seller-side refund exposure face (api_refund_exposure) answers"
    " the question the refund door could only refuse: how much of a"
    " seller's balance is already spoken for by refunds the market may"
    " demand. Seven-key envelope, nine-key dense rows over every listing"
    " owner, liability = stored dev_share of unrefunded purchases (never"
    " recomputed from a price), balance from the live ledger with an"
    " honest balance_known False, shortfall and covered derived,"
    " retirement keeps the obligation, account gate before any read, pure"
    " read, cross-restart byte identity. The report attention digest"
    " gains a refund_risk family and REPORT_SCHEMA moves 7 -> 8"
    " additively. Suite 8/8 double-run byte-identical sha16"
    " 112e6f0d43928930; battery RUNNER PASS 320/320 suites plus controls"
    " 7/7 in 533.8s; matrix 320 suites / 2668 criteria --check"
    " byte-identical; census DRIFT-CLEAN files=1783 flags=0.")

OUTS_TIMELINE = (
    "R2115：退款门能在卖家已花掉分成时拒付（余额地板是宪法面），"
    "但此前没有任何面在事发前告诉任何人「这笔钱已经不在账上了」——"
    "卖家答不出自己账上多少钱已被可能发生的退款占住，运营答不出今天谁会退不动。"
    "本窗交付卖家侧退款敞口读面 api_refund_exposure："
    "从未退款购买的存量卖家分账派生敞口上限（改价/改文案不移动），"
    "活账本余额判可垫付，差额即缺口并在信封汇总；"
    "行集权威=挂牌表全部 distinct 卖家（密集·零成交卖家在榜·行序 dev_account 升序），"
    "无账本账户诚实报 balance 0 / balance_known False，退役不销债，账户门前置，纯读零 token。"
    "并接进唯一消费者：报表 attention 增 refund_risk 家族（缺口>0 · high）+ REPORT_SCHEMA 7→8 加法升级。"
    "证据=套件 8/8 双跑判据行同一 sha16 112e6f0d43928930；"
    "电池 RUNNER PASS 320/320 + controls 7/7 533.8s；矩阵 320/2668 --check 逐字节同；census DRIFT-CLEAN。"
    "诚实注：本窗接管的是一个崩溃前窗的遗留产物（state 仍停在 R2114），"
    "前窗证据件是 PS 重定向方言，已用 python 单写者重出 utf-8 LF；"
    "前窗电池日志死于某报表套件 300s 超时，本窗单独计时 81s、电池内 41.6s，判定为崩溃时机器负载而非产品挂死。")


def read(path):
    with io.open(path, encoding="utf-8") as handle:
        return handle.read()


def write(path, text):
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def mark_explore():
    lines = read(EXPLORE).split("\n")
    if "R2115" not in lines[0]:
        print("skip: explore head is not the R2115 row")
        return
    if "[done 2026-10-25 R2115]" in lines[0]:
        print("skip: explore row already closed")
        return
    head = lines[0]
    if head.startswith("- [ ] "):
        head = "- [x] " + head[len("- [ ] "):]
    lines[0] = head + DONE_NOTE
    write(EXPLORE, "\n".join(lines))
    print("closed explore row")


def mark_backlog():
    text = read(BACKLOG)
    if "R2115" in text:
        print("skip: backlog row already present")
        return
    write(BACKLOG, BACKLOG_ROW + "\n\n" + text)
    print("prepended backlog row")


def main():
    mark_explore()
    mark_backlog()

    state = json.load(io.open(STATE, encoding="utf-8"))
    state["tick"] = 2115
    state["last_order"] = "2026-10-24 12:17"
    state["last_decision_rows"] = 209
    for line in LOG_LINES:
        if line in state["log"]:
            continue
        state["log"].append(line)
    write(STATE, json.dumps(state, indent=1, ensure_ascii=False) + "\n")

    export = json.load(io.open(EXPORT, encoding="utf-8"))
    now = datetime.datetime.now().astimezone().replace(microsecond=0)
    export["export_ts"] = now.isoformat()
    export["ceo_face"]["current"] = (
        "R2115 卖家退款敞口面：退款门会在卖家把分成花掉后拒付，但此前没有任何面提前说明"
        "「这笔钱已经不在账上」。现在卖家与运营都能一眼看到每家的退款敞口、账上余额与缺口。")
    export["ceo_face"]["latest_artifact"] = (
        "src/sandbox/ledger/apimarket.py 的 api_refund_exposure（七键信封+九键密集行·"
        "敞口=未退款购买的存量卖家分账·余额取活账本·缺口/covered 派生·退役不销债·纯读）"
        " + apimarket_report.py 的 refund_risk 家族与 REPORT_SCHEMA 8"
        " + src/sandbox/ledger/test_apimarket_refundexposure.py（SUITE PASS 8/8·双跑同一 sha16 112e6f0d43928930）"
        " + qa/reconcile-all-R2115.log（RUNNER PASS 320/320·controls 7/7·533.8s·2026-10-25 07:56）")
    export["ceo_face"]["next_milestone"] = (
        "48 小时内：把退款敞口接进运营侧唯一页面之外的第二个消费面（市场级敞口排行榜/告警行），"
        "并把「卖家余额低于敞口」纳入每日对账的 fail 判据；随后按排队顺序继续 explore 队头新面。")
    export["outs"].insert(0, [
        "卖家侧退款敞口读面（api_refund_exposure + refund_risk 告警家族）",
        "on",
        OUTS_TIMELINE])
    export["results"].insert(0, ["R2115", RESULTS_TEXT])
    export["self_drive"]["log_lines_in_window"] = int(
        export["self_drive"].get("log_lines_in_window", 0)) + 2
    write(EXPORT, json.dumps(export, indent=1, ensure_ascii=False) + "\n")
    print("closed tick=%s export=%s" % (state["tick"], export["export_ts"]))


if __name__ == "__main__":
    sys.exit(main())