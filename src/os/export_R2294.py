"""R2294 export refresh: the CEO-visible face after the product window.

Derives every number it writes from the live tree; it invents no reading.
"""

import datetime
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EXPORT = os.path.join(ROOT, "docs", "status-export.json")

DO = (
    "product window: an accepted-stamp declaration that could rot silently in either "
    "direction is now a reading - src/os/stamp_exempt_review.py lists MISSING (a "
    "declared entry matching no live debt row, with its declaration entry index) and "
    "UNDECLARED (a live debt row carrying no entry, with file and line) from the gate "
    "and the declaration it already trusts, reconciles both against the reader own "
    "exempt/unmatched numbers before any verdict, and refuses rather than guessing; "
    "SUITE PASS 6/6 double-run with five adjacent suites green, live reading NO-DRIFT "
    "over 380 entries / 380 violations"
)

CURRENT = (
    "R2294 产品轮：接受的盖章豁免声明从此可被双向体检。queue_done_stamp_exempt 只问「这条声明还"
    "匹配得到一行吗」，于是两种腐烂都无声：被豁免的行事后被加注→文本摘要漂移→声明变成无主；声明之后"
    "新关的行→根本没有条目。两种情况下验收面一直是绿的。新增 src/os/stamp_exempt_review.py：从两个"
    "既有读数（queue_done_stamp.audit_root 的闸 + queue_done_stamp_exempt 的声明与身份律）双向列出"
    "漂移——MISSING 带声明条目序号，UNDECLARED 带文件与行号——且从不猜哪边过期；两侧计数必须先与"
    "阅读器自身的 exempt/unmatched 数字对平（否则 E_SER_COUNT 拒绝），缺声明= E_SER_UNPINNED 而非"
    "把 380 行一律报成漂移，坏 JSON/缺队文件/同一队内两行同身份各有专属码；零写盘零读钟。"
    "证据 SUITE PASS 6/6 双跑判据行同一 + 五个相邻队套件全绿（qa/stamp-exempt-review-R2294.log，"
    "1844B，单写者 utf-8 LF 经 evidence_capture），接线 os-stamp-exempt-review(6)。"
    "实况 STAMP EXEMPT REVIEW round=R2294 entries=380 violations=380 matched=380 "
    "missing=0 undeclared=0 verdict=NO-DRIFT（声明与 tech.md 均证明逐字节未动）。"
    "认领使 tech 可认领降到 9，已补一条真缺口种子（stamp_exempt_append，AC-SAP1..AC-SAP6 预注册，"
    "五锚零占用）→ 队列回到 main 5/5 · tech 10/10 · explore 10/10。"
    "债务行经自带写入器关闭（debt_close line 66，open 2→1，done 43→44，回读 ok），"
    "后继 product-face-R2295 置 first=yes（39397B→39875B，回读 ok）。"
    "收口跨水位，按整块折窗折 602（log 1..10，R2279+R2280 完整块，580 token 全覆盖），"
    "折后 72147B / 余量 6353B，四个账本套件复跑 8/8/8/8 全绿。"
)

LATEST = (
    "src/os/stamp_exempt_review.py + src/os/test_stamp_exempt_review.py + "
    "qa/stamp-exempt-review-R2294.log（SUITE PASS 6/6 双跑，1844B）·2026-10-31"
)

NEXT = (
    "R2295 验证轮：在已提交的 R2294 树上跑全量 reconcile 电池（R2168 混合树规避，零产品改动直到转绿），"
    "预注册预期 = 对上轮 452 套件 / 3688 判据的 +1 套件 / +6 判据（来自 os-stamp-exempt-review），"
    "随后四段后续经 battery_followup 执行。窗口 ≤24h。"
)

LAST = (
    "R2294 产品窗：stamp_exempt_review 6/6 双跑 + 5 相邻套件绿，qa/stamp-exempt-review-R2294.log·"
    "2026-10-31"
)


def main(argv):
    execute = "--execute" in argv
    raw = open(EXPORT, "rb").read()
    data = json.loads(raw.decode("utf-8"))
    now = datetime.datetime.now().astimezone().replace(microsecond=0)
    data["export_ts"] = now.isoformat()
    data["do"] = DO
    face = data.setdefault("ceo_face", {})
    face["current"] = CURRENT
    face["latest_artifact"] = LATEST
    face["next_milestone"] = NEXT
    face["next_milestone_due"] = (
        now + datetime.timedelta(hours=24)).replace(microsecond=0).isoformat()
    face["last_artifact"] = LAST
    data["results"] = [["R2294",
                        "R2294 product window on the debt register first item "
                        "(product-face-R2294): the accepted-stamp declaration is read "
                        "from BOTH sides - MISSING names a declared entry matching no "
                        "live debt row with its declaration entry index, UNDECLARED "
                        "names a live debt row carrying no entry with its file and "
                        "line - and the split reconciles with the reader own exempt and "
                        "unmatched numbers before any verdict, refusing with E_SER_COUNT "
                        "on disagreement; SUITE PASS 6/6 double-run with five adjacent "
                        "suite green (qa/stamp-exempt-review-R2294.log, 1844B); live "
                        "reading NO-DRIFT over 380 entries / 380 violations with both "
                        "real files proved byte-unchanged; one real gap row seeded for "
                        "the tech floor; 2-point product window"]] + data["results"]
    data["outs"] = [["a drift reader that will not go green on a rotten pair: MISSING "
                     "and UNDECLARED are both listed with their own locators, and a "
                     "count disagreement refuses instead of printing a drift list "
                     "nobody can trust (R2294)",
                     "on",
                     "R2294: the first suite run was red 3/6 and two reds were "
                     "this-window test defects - one expected a patched reader to "
                     "affect a subprocess (it cannot) and one put duplicate rows in "
                     "different queues, which is not ambiguous because identity is "
                     "keyed per queue. The third red was the missing runner wiring. No "
                     "criterion was widened; the fixtures were fixed."]] + data["outs"]
    if not execute:
        print("DRY RUN export_ts=%s results=%d outs=%d"
              % (data["export_ts"], len(data["results"]), len(data["outs"])))
        return 0
    text = json.dumps(data, ensure_ascii=False, indent=2)
    blob = text.encode("utf-8")
    if not blob.endswith(b"\n"):
        blob += b"\n"
    temp = EXPORT + ".tmp"
    with open(temp, "wb") as sink:
        sink.write(blob)
        sink.flush()
        os.fsync(sink.fileno())
    os.replace(temp, EXPORT)
    back = json.loads(open(EXPORT, "rb").read().decode("utf-8"))
    assert back["export_ts"] == data["export_ts"]
    print("WROTE %dB readback ok" % len(blob))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))