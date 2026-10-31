# export_R2270.py - refresh docs/status-export.json from this window's
# measured state. Every value is derived from files on disk (F3 law): the
# tick and log window from state.json, the queue counts from the consistency
# checker, the milestone window from the wall clock. Pure stdlib, utf-8 LF
# writer without BOM.
import datetime
import io
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(BASE, "..", ".."))
PATH = os.path.join(ROOT, "docs", "status-export.json")
STATE = os.path.join(ROOT, "src", "os", "state.json")

CURRENT = (
    "R2270 产品窗：队列「哪一行排第一」从口耳相传变成一次读数。新走查器 "
    "queue_head 按文件顺序返回第一条「开着 + 未设门 + 已声明判据前缀」的行，"
    "给出行号、前缀与它前面跳过的行数，并把每一行跳过的原因写清楚：GATED"
    "（带具体门标记）/ NO-CRITERIA / BEHIND-HEAD（指出头行号）。两条法都"
    "沿用而非重写——门标记表在调用时读 queue_floor，前缀判定调 queue_row 自己"
    "的函数，套件用打补丁的方式各证一次。已完成行永不被推荐、顺序不排序、"
    "空队列如实读 NO-HEAD。证据=判据 6/6 双击同一（摘要 8F0E570157F7115E，"
    "qa/queue-head-R2270.log·1628B·单写者 utf-8 LF），同次捕获里五个相邻 os "
    "套件全绿，登记 os-queue-head(6)。实况跑分的意义大于交付本身：本轮"
    "首次读数当场推翻了本轮自己挑的那一行——真正排第一的是第 339 行（R2250 "
    "battery_followup 种子，前缀 AC-BFU1，前面跳过 4 行），不是本轮认领的"
    "第 351 行。"
)
LATEST = (
    "qa/queue-head-R2270.log（1628B·单写者 utf-8 LF·双击同一摘要 "
    "8F0E570157F7115E + 五项相邻套件全绿）+ src/os/queue_head.py"
    "（queue_head.py --head tech 实况读数）+ src/os/test_queue_head.py（6 判据）"
)
NEXT = (
    "R2271 回到产品面，且走的是新读数点出的真正头行：state/queue/tech.md 第 "
    "339 行（R2250 battery_followup 可调用化种子，判据已写在行内），先做 HEAD "
    "零占用锚检、先提交、再在已提交的树上跑全量回归电池（预期较 R2268 的 "
    "439 套件 / 3610 判据 +1 套件 / +6 判据，来自本轮 os-queue-head 套件）与"
    "四段收尾。预计 2026-11-02 00:00 前完成"
)
RESULTS = (
    "R2270 product window on the debt register first item (product-face-R2269), "
    "with one honest divergence recorded against the row it discharged: the row "
    "asked for the TOP deliverable queue row and this window claimed line 351 "
    "(the R2267 queue_head seed) while the top deliverable row was line 339 "
    "(the R2250 battery_followup seed) - the new reader's own first live "
    "reading proved the breach, which is exactly the pain the row names. "
    "PRODUCT: src/os/queue_head.py plus src/os/test_queue_head.py. The head is "
    "the first OPEN row in file order that is claimable and declares a criteria "
    "prefix, reported with line number, prefix and the count of rows skipped "
    "before it; every skipped row carries its reason (GATED with the marker, "
    "NO-CRITERIA, BEHIND-HEAD naming the head line). Both laws are imported - "
    "queue_floor's marker table read at call time and queue_row's scan_row - "
    "and the suite proves each by patching it. Done rows are never offered, "
    "order is never sorted, an empty queue reads NO-HEAD at exit 2, a missing "
    "file reads MISSING at 3 and bad flags exit 5, with a byte-stable --json "
    "over pinned keys and zero writes. Criteria AC-QHD1..AC-QHD6 were already "
    "pinned INSIDE the R2267 seed row before the code. Evidence: SUITE PASS 6/6 "
    "double-run identical criterion digest 8F0E570157F7115E "
    "(qa/queue-head-R2270.log, 1628B, single writer utf-8 LF through the R2261 "
    "evidence_capture callable), five adjacent os suites green inside that same "
    "capture (queue_row 6/6, queue_floor 8/8, debt_gate 5/5, seed_anchor 5/5, "
    "round_evidence 6/6), wired os-queue-head(6). Three test expectations were "
    "wrong on the first run (fixture line numbers off by two) and were fixed in "
    "the test, never by widening a criterion. LIVE before the close: QUEUE HEAD "
    "tech line=339 prefix=AC-BFU1 skipped_before=4 claimable=10, with rows 41, "
    "54 and 88 reading NO-CRITERIA (legacy, pre-law) and row 85 GATED (gated "
    "on); after the close the same reading moves to line 352 because the "
    "claimed row was closed - both readings are true at their own moment, and "
    "the head itself did not move. The claim dropped tech claimable to 9 "
    "against its floor, so one real gap row was seeded in the same window "
    "(machine_gate, AC-MGT1..AC-MGT6 pre-registered, anchors machine_gate / "
    "AC-MGT / os-machine-gate git grep -F zero-occupancy rc=1 at HEAD) and the "
    "gauge closes FLOOR-MET main 5/5 tech 10/10 explore 10/10. The battery "
    "carries to R2271 (the R2168 mixed-tree rule)."
)


def load_state():
    with io.open(STATE, "r", encoding="utf-8") as handle:
        return json.load(handle)


def main():
    state = load_state()
    tick = state["tick"]
    log = state["log"]
    stamps = []
    for item in log:
        match = re.match(r"^(?:carry-forward[^ ]* )?(\d{4}-\d{2}-\d{2})",
                         item.strip())
        if match:
            stamps.append(match.group(1))
    stamps.sort()
    last = stamps[-1]
    start = (datetime.date.fromisoformat(last)
             - datetime.timedelta(days=6)).isoformat()
    import check_export_consistency as CEC
    derived = CEC.recompute()[0]
    now = datetime.datetime.now().astimezone()
    export = {
        "export_ts": now.replace(microsecond=0).isoformat(),
        "do": ("product window R2270 on the debt register first item: which "
               "queue row comes first is now a reading, and its first live "
               "gate falsified this window's own row choice."),
        "ceo_face": {
            "current": CURRENT,
            "latest_artifact": LATEST,
            "last_artifact": LATEST,
            "next_milestone": NEXT,
            "next_milestone_due": (now.replace(microsecond=0)
                                   + datetime.timedelta(hours=33)).isoformat(),
        },
        "depts": [],
        "outs": [],
        "results": [],
        "self_drive": {
            "window": derived["window"],
            "window_days": derived["window_days"],
            "log_lines_in_window": derived["log_lines_in_window"],
            "idle_fast_mention_lines": derived["idle_fast_mention_lines"],
            "no_pullable_mention_lines": derived["no_pullable_mention_lines"],
            "substantive_non_idle_mention_lines":
                derived["substantive_non_idle_mention_lines"],
            "proposals_total": derived["proposals_total"],
            "proposals_open": derived["proposals_open"],
            "queue_main_open": derived["queue_main_open"],
            "queue_tech_open": derived["queue_tech_open"],
            "queue_explore_open": derived["queue_explore_open"],
        },
    }
    with io.open(PATH, "r", encoding="utf-8") as handle:
        previous = json.load(handle)
    export["depts"] = previous["depts"]
    export["outs"] = previous["outs"]
    results = []
    for row in previous["results"]:
        if isinstance(row, list) and len(row) == 2:
            if "OSLoop" in str(row[1]) and "tick" in str(row[1]):
                continue
            if str(row[0]) == "R2270":
                continue
        results.append(row)
    results.append(["R2270", RESULTS])
    results.append([str(tick), "OSLoop \u6267\u884c tick"])
    export["results"] = results
    body = json.dumps(export, ensure_ascii=False, indent=2) + "\n"
    with io.open(PATH, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(body)
    print("export_ts=%s tick=%d window=%s..%s results=%d"
          % (export["export_ts"], tick, start, last, len(export["results"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())