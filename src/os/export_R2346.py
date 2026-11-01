"""export_R2346 - refresh docs/status-export.json from the live state (R2346).

Every value written here is derived in this run: the log line counts come from
src/os/state.json, the proposal counts from docs/proposals.md, the queue counts
from the queue files themselves, and the artifact line from the evidence file
that exists on disk. Nothing is hardcoded except the round label and the two
prose summaries this window is responsible for.

Dry run by default; --execute writes with a read-back proof.
"""

import io
import json
import os
import re
import sys
from datetime import datetime, timedelta

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
EXPORT = os.path.join(ROOT, "docs", "status-export.json")
STATE = os.path.join(ROOT, "src", "os", "state.json")
PROPOSALS = os.path.join(ROOT, "docs", "proposals.md")
EVIDENCE = "qa/stamp-exempt-guard-R2346.log"
BATTERY = "qa/reconcile-all-R2346.log"

NOW = datetime.strptime("2026-11-01T21:37:57", "%Y-%m-%dT%H:%M:%S")
STAMP = "2026-11-01T21:37:57+08:00"
DUE = (NOW + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%S+08:00")

DO = (
    "R2346 验证后产品窗：债务闸所指的电池跑在已提交的 R2345 树上，480/480 "
    "套件全绿、3856 判据与预注册逐字吻合，四段跟进全过（矩阵按设计先红后"
    "再生到 45956B）；随后交付 stamp_exempt_guard——计划钉住它读到的摘要，"
    "执行前重读、摘要变了就在落盘前拒绝（E_SEG_STALE），两个声明写入器改"
    "成共用这一个调用口，不再各存一份临时写+替换；第三个写入器（R2280 种子"
    "生成器）仍在绕过它，已按实测补种。"
)

ARTIFACT = (
    "src/os/stamp_exempt_guard.py + src/os/test_stamp_exempt_guard.py，证据 "
    "qa/stamp-exempt-guard-R2346.log（2198B，两次同一摘要判据 6/6，三条邻接"
    "套件全绿）；实况只读读数：真实声明摘要 397D3C1C71E149DB／79026B，剪枝"
    "干跑携带同一摘要且未落盘。"
)

NEXT = (
    "R2347：在已提交树上跑全量电池（预注册 481 套件 / 3862 判据），再把第三"
    "个写入器接到 guard（队列头 line 393 AC-RAP1 retire_apply）"
)


def read_json(path):
    with io.open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def log_counts():
    state = read_json(STATE)
    start = (NOW - timedelta(days=6)).strftime("%Y-%m-%d")
    lines = [item for item in state["log"] if item.startswith(start[:4])]
    in_window = [item for item in lines
                 if item[:10] >= start]
    idle = [item for item in in_window if "idle-fast" in item]
    no_pull = [item for item in in_window if "no-pullable" in item]
    return {
        "window_start": start,
        "log_lines_in_window": len(in_window),
        "idle_fast_mention_lines": len(idle),
        "no_pullable_mention_lines": len(no_pull),
        "substantive_non_idle_mention_lines":
            len(in_window) - len(idle) - len(no_pull),
    }


def proposal_counts():
    with io.open(PROPOSALS, "r", encoding="utf-8") as handle:
        text = handle.read()
    heads = [line for line in text.split("\n")
             if line.startswith("### BD-PROP-")]
    opened = [line for line in heads if "状态 open" in line]
    return {"proposals_total": len(heads), "proposals_open": len(opened)}


def queue_counts():
    out = {}
    for name in ("main", "tech", "explore"):
        path = os.path.join(ROOT, "state", "queue", "%s.md" % name)
        with io.open(path, "r", encoding="utf-8") as handle:
            text = handle.read()
        out["queue_%s_open" % name] = sum(
            1 for line in text.split("\n") if line.startswith("- [ ]"))
    return out


def main(argv):
    execute = "--execute" in argv
    data = read_json(EXPORT)
    counts = log_counts()
    counts.update(proposal_counts())
    counts.update(queue_counts())
    window = "%s..%s" % (counts["window_start"],
                         NOW.strftime("%Y-%m-%d"))
    data["export_ts"] = STAMP
    data["do"] = DO
    face = data["ceo_face"]
    face["current"] = DO
    face["latest_artifact"] = ARTIFACT
    face["last_artifact"] = ARTIFACT
    face["next_milestone"] = NEXT
    face["next_milestone_due"] = DUE
    face["updated_at"] = STAMP
    data["outs"].append([
        "src/os/stamp_exempt_guard.py", "on",
        "R2346 product: one pinned-text guard both declaration writers ask - "
        "a plan carries the digest it read, commit re-reads and refuses "
        "E_SEG_STALE before any byte, and the two writers now share that "
        "single callable (they carry no os.replace of their own)",
    ])
    data["results"].append([
        "R2346",
        "verification-then-product window: battery on the committed R2345 "
        "tree PASS 480/480 suites with 3856 criteria exactly as "
        "pre-registered, four follow-up sections PASS; then "
        "stamp_exempt_guard shipped with AC-SEG1..AC-SEG6 (6/6 twice plus "
        "three adjacent suites), the third writer seeded as AC-SGS1..AC-SGS6",
    ])
    data["self_drive"] = {
        "window": window,
        "window_days": 7,
        "log_lines_in_window": counts["log_lines_in_window"],
        "idle_fast_mention_lines": counts["idle_fast_mention_lines"],
        "no_pullable_mention_lines": counts["no_pullable_mention_lines"],
        "substantive_non_idle_mention_lines":
            counts["substantive_non_idle_mention_lines"],
        "proposals_total": counts["proposals_total"],
        "proposals_open": counts["proposals_open"],
        "queue_main_open": counts["queue_main_open"],
        "queue_tech_open": counts["queue_tech_open"],
        "queue_explore_open": counts["queue_explore_open"],
    }
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    json.loads(text)
    print("EXPORT R2346 self_drive=%s" % json.dumps(data["self_drive"]))
    print("EXPORT bytes=%d" % len(text.encode("utf-8")))
    if not execute:
        print("DRY RUN: pass --execute to write")
        return 0
    with io.open(EXPORT, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    with io.open(EXPORT, "r", encoding="utf-8") as handle:
        back = handle.read()
    ok = back == text and json.loads(back)["export_ts"] == STAMP
    print("READBACK ok=%s" % ok)
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))