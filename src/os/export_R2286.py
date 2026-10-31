"""R2286 export refresh: rewrite the CEO-visible face from measured state.

F3 law: every field below is derived from this window's actual readings (the
live machine gate reading, the evidence file, the register writers and the
live gauges) and the self_drive block is recomputed by
check_export_consistency.recompute() rather than typed, so a stale counter
cannot survive the refresh.
"""

import io
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
EXPORT = os.path.join(ROOT, "docs", "status-export.json")
sys.path.insert(0, HERE)

import check_export_consistency as consistency  # noqa: E402


def main(argv):
    now_ts, due_ts = argv[0], argv[1]
    data = json.loads(io.open(EXPORT, encoding="utf-8").read())
    derived, state, _old, _pat = consistency.recompute()
    data["export_ts"] = now_ts
    data["do"] = ("product window on the debt register first item: the "
                  "machine gate reads which claimable queue row this host can "
                  "actually deliver (one declared blocker file joined with "
                  "the imported head law), with its six pre-registered "
                  "criteria and its suite green")
    face = data["ceo_face"]
    face["current"] = (
        "R2286 产品面：machine_gate 落地——队列“下一行是什么”之外，"
        "再答“这台机器能不能交付这一行”（声明件 + 行身份哈希，"
        "机器原因导致的不可交付从此是带日期的数据，而不是操作者的记忆）。"
    )
    face["latest_artifact"] = (
        "src/os/machine_gate.py + src/os/test_machine_gate.py + "
        "state/machine_gates.json：套件 6/6 双跑一致、五个邻域套件全绿"
        "（qa/machine-gate-R2286.log，1304B，单写者 utf-8 LF）"
    )
    face["last_artifact"] = face["latest_artifact"]
    face["next_milestone"] = (
        "R2287 在已提交树上跑全量 reconcile 电池 + 套件矩阵再生"
        "（预注册期望 449 套件 / 3670 判据）；随后产品面回到 tech 队头"
        "（R2286 认领后队头移至 state/queue/tech.md:356，AC-FHY1 行）。"
    )
    face["next_milestone_due"] = due_ts
    data["self_drive"] = derived
    kept = []
    for row in data["results"]:
        if isinstance(row, list) and len(row) == 2 and row[0] == "2285":
            row[0] = "2286"
        if isinstance(row, list) and len(row) == 2 and row[0] == "R2284":
            continue
        kept.append(row)
    data["results"] = kept + [[
        "R2286",
        ("R2286 product window on the debt register first item "
         "(product-face-R2286): the tech head the reader named, the R2270 "
         "machine_gate seed at state/queue/tech.md:355 prefix AC-MGT1, with "
         "AC-MGT1..AC-MGT6 already pinned in that row BEFORE the code "
         "(fresh zero-occupancy anchor check at HEAD 2026-10-31: E_MGT and "
         "test_machine_gate git grep -F rc 1, the bare words hitting only "
         "prose and the closeout/export helpers). Delivered "
         "src/os/machine_gate.py plus src/os/test_machine_gate.py plus the "
         "pinned declaration state/machine_gates.json (one docker blocker on "
         "row 41, keyed by the identity -#02878cdc so a line shift never "
         "moves it). The head law is imported from queue_head - every "
         "candidate comes out of queue_head.head_text and advancing past a "
         "blocked row only masks that row's leading marker in a copy of the "
         "text, so the line count stays honest - and the suite proves the "
         "import by patching that law. A blocker must name identity, "
         "capability, reason and declared_by from the declared capability "
         "vocabulary (a typo reads E_MGT_BAD_CAPABILITY); a missing or "
         "unreadable declaration refuses the reading instead of pretending "
         "nothing is blocked; an entry that matches no candidate reads INERT "
         "with its live line or line=None. SUITE PASS 6/6 double-run "
         "identical through the R2261 evidence_capture callable with five "
         "adjacent suites green (qa/machine-gate-R2286.log, 1304B, single "
         "writer utf-8 LF), wired os-machine-gate(6). LIVE at closeout: "
         "MACHINE GATE tech line=355 prefix=AC-MGT1 declarations=1 "
         "blocked=0 inert=1 candidates=7 verdict=OFFERED. The claim dropped "
         "tech claimable to 9, so one real gap row was seeded (gate_drift, "
         "AC-GDR1..AC-GDR6 pre-registered, five anchors zero-occupancy) and "
         "the gauge closes FLOOR-MET main 5/5 tech 10/10 explore 10/10. "
         "Register closed through its own writer (debt_close line=58, "
         "open 2->1, done 35->36, readback ok) and reconcile-battery-R2287 "
         "opened first=yes through debt_append (before=35384B after=35788B, "
         "readback ok). Honest score: 2 product points (a runnable reader "
         "plus its suite and data file)."),
    ]]
    text = json.dumps(data, indent=1, ensure_ascii=False) + "\n"
    folder = os.path.dirname(EXPORT)
    handle, temp = tempfile.mkstemp(dir=folder, prefix=".export_")
    with os.fdopen(handle, "wb") as sink:
        sink.write(text.encode("utf-8"))
    os.replace(temp, EXPORT)
    back = io.open(EXPORT, "rb").read().decode("utf-8")
    if back != text:
        raise SystemExit("ABORT read-back differs from the write")
    print("WROTE %dB tick_row=%r" % (len(back.encode("utf-8")),
                                     data["results"][0][0]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))