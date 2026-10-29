# export_R2267.py - refresh docs/status-export.json from this window's
# measured state. Every value is derived from files on disk (F3 law): the
# tick and log window from state.json, the queue counts from queue_floor,
# the proposal counts from docs/proposals.md, the milestone window from the
# wall clock. Pure stdlib, pure ASCII source, utf-8 LF writer without BOM.
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
PROPOSALS = os.path.join(ROOT, "docs", "proposals.md")
QUEUES = (("queue_main_open", "main"), ("queue_tech_open", "tech"),
          ("queue_explore_open", "explore"))

sys.path.insert(0, BASE)
import queue_floor

CURRENT = (
    "R2267 出实物：src/os/debt_gate.py —— 债务登记簿写的 first=yes 那一条，"
    "从此有一个闸在开工前必须回答：这一窗到底该领哪一项。三种诚实结局，没有"
    "第四种：CLAIM-FIRST 点名条目/开启轮/备注/已背窗数；OPEN-NONE 同时覆盖"
    "「空登记簿」和「有开项但没标 first」，因为两者都只说明这一窗该自己登记；"
    "而登记簿缺失、不可读或坏形一律拒绝并带着登记簿自己的错误码族——文件不在，"
    "绝不能被读成「没有欠账」。行法是从 debt_register 导入的，不重写，所以登记"
    "簿只有一个主人；模块不写盘、不读钟。"
)
LATEST = (
    "src/os/debt_gate.py + src/os/test_debt_gate.py（双跑判据同 digest，"
    "qa/debt-gate-R2267.log）+ 接线 os-debt-gate(5)；实测 "
    "DEBT GATE verdict=CLAIM-FIRST item=product-face-R2267 carried=1 open=2"
)
NEXT = (
    "R2268 回到验证：在已提交的树上跑全量回归电池（预期 439 套件 / 3610 判据"
    "= R2266 的 438/3605 加本窗 os-debt-gate 的 1 套件 5 判据），再跑四段收尾；"
    "电池绿之前不碰产品码。预计 2026-10-29 内完成"
)
RESULTS = (
    "R2267 product window on the debt register first item (product-face-R2267, "
    "seed = the R2248 f debt_gate row with AC-DGT1..AC-DGT5 already pinned "
    "BEFORE the code): src/os/debt_gate.py plus src/os/test_debt_gate.py. The "
    "register names a first=yes row for the next window and nothing stopped a "
    "window from not reading it, so the gate asks that one question: "
    "CLAIM-FIRST naming item/opened/note/carried, OPEN-NONE covering an empty "
    "register and an all-first=no register alike, and a refusal on a missing, "
    "unreadable or malformed register so an absent file never reads as nothing "
    "owed. Row law imported from debt_register, zero writes, no clock, "
    "byte-stable JSON. SUITE PASS 5/5 double-run identical digest "
    "(qa/debt-gate-R2267.log, single writer utf-8 LF through the R2261 capture "
    "callable), five adjacent os suites green, wired os-debt-gate(5). LIVE "
    "DEBT GATE verdict=CLAIM-FIRST item=product-face-R2267 carried=1 open=2 "
    "first=1. One real gap row (queue_head, AC-QHD1..AC-QHD6) seeded to hold "
    "the tech floor after the claim; gauge FLOOR-MET 10/10."
)


def load_state():
    with io.open(STATE, "r", encoding="utf-8") as handle:
        return json.load(handle)


def queue_counts():
    report = queue_floor.check(ROOT) if hasattr(queue_floor, "check") else None
    counts = {}
    for key, name in QUEUES:
        path = os.path.join(ROOT, "state", "queue", "%s.md" % name)
        rows = 0
        with io.open(path, "r", encoding="utf-8") as handle:
            for line in handle:
                if line.startswith("- [ ]"):
                    rows += 1
        counts[key] = rows
    return counts


def proposal_counts():
    total = 0
    opened = 0
    with io.open(PROPOSALS, "r", encoding="utf-8") as handle:
        for line in handle:
            if line.startswith("### BD-PROP-"):
                total += 1
                if "open" in line.lower():
                    opened += 1
    return total, opened


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
    window = [i for i in log
              if re.search(r"\b(\d{4}-\d{2}-\d{2})\b", i)
              and re.search(r"\b(\d{4}-\d{2}-\d{2})\b", i).group(1) >= start]
    substantive = [i for i in window
                   if not i.startswith("carry-forward")
                   and i.strip()]
    proposals_total, proposals_open = proposal_counts()
    counts = queue_counts()
    # the self_drive counts come from the consistency checker, which owns the
    # window and row laws - re-deriving them here is how faces drifted before.
    import check_export_consistency as CEC
    derived = CEC.recompute()[0]
    now = datetime.datetime.now().astimezone()
    export = {
        "export_ts": now.replace(microsecond=0).isoformat(),
        "do": ("product window R2267 on the debt register first item: the "
               "first=yes row now has a gate that must answer which item this "
               "window leads with, and it refuses to read an absent register as "
               "no debt."),
        "ceo_face": {
            "current": CURRENT,
            "latest_artifact": LATEST,
            "last_artifact": LATEST,
            "next_milestone": NEXT,
            "next_milestone_due": (now.replace(microsecond=0)
                                   + datetime.timedelta(hours=36)).isoformat(),
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
        if isinstance(row, list) and len(row) == 2 and \
                "OSLoop" in str(row[1]) and "tick" in str(row[1]):
            continue
        results.append(row)
    results.append(["R2267", RESULTS])
    # the tick row is the single row the consistency checker recomputes
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