"""R2285 export refresh: rewrite the CEO-visible face from measured state.

F3 law: every field below is derived from this window's actual readings (the
battery evidence file and its criterion total, the follow-up sections, the
register writers and the live gauges) and the self_drive block is recomputed
by check_export_consistency.recompute() rather than typed, so a stale counter
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
    data["do"] = ("verification window on the debt register first item: the "
                  "whole reconcile battery green on the committed R2284 tree "
                  "(448 suites / 3664 criteria), matrix regenerated to match")
    face = data["ceo_face"]
    face["current"] = (
        "R2285 验证窗：在已提交的 R2284 树 453f45c7 上跑全量 reconcile 电池，"
        "全过程零产品改动，直到判据全绿（R2168 混合树律）。"
    )
    face["latest_artifact"] = (
        "qa/reconcile-all-R2285.log（775794B，单一写入器 utf-8 LF）；"
        "RUNNER PASS 448/448 套件 + 7/7 控制，865.5s，判据共 3664"
    )
    face["last_artifact"] = face["latest_artifact"]
    face["next_milestone"] = (
        "R2286 产品窗：tech 队头 state/queue/tech.md:355（AC-MGT1 段，"
        "machine_gate 种子）——机器原因不可交付的队行变成带日期的声明数据，"
        "而不是操作者记忆；先做 HEAD 零占用锚检，再交付模块与套件，提交后才跑电池。"
    )
    face["next_milestone_due"] = due_ts
    data["self_drive"] = derived
    kept = []
    for row in data["results"]:
        if isinstance(row, list) and len(row) == 2 and row[0] == "2284":
            row[0] = "2285"
        if isinstance(row, list) and len(row) == 2 and row[0] == "R2283":
            continue
        kept.append(row)
    data["results"] = kept + [[
        "R2285",
        ("R2285 verification window on the debt register first item "
         "(product-face-R2285 = reconcile-battery-R2285), discharged on the "
         "committed R2284 tree 453f45c7 with an empty git status before the "
         "run and zero product edits until green (the R2168 mixed-tree "
         "rule): RUNNER PASS 448/448 suites green plus controls 7/7 in "
         "865.5s with birth-site TMP RECLAIM 932/932 worlds 326.57 MiB "
         "busy=0 failed=0 (qa/reconcile-all-R2285.log, 775794B, single "
         "writer utf-8 LF through src/os/battery_stream.py, never a shell "
         "redirection), criteria total 3664 - exactly the pre-registered +1 "
         "suite / +6 criteria against R2283 (447/3658) from the R2284 "
         "os-stamp-locator suite, so the prediction matched the measurement "
         "with no correction. Four follow-up sections then ran through "
         "src/os/battery_followup.py: the matrix section FAILED first on the "
         "stale doc (on-disk=43205B regenerated=43279B) and did NOT rewrite "
         "it, which is the designed order; src/sandbox/suite_matrix.py "
         "regenerated docs/sandbox-suite-matrix.md to 448 suites / 3664 "
         "criteria (43279B) and the re-run read all four sections PASS "
         "(matrix byte-identical, fingerprint CLEAN 5 domains, profile "
         "--daily --check byte-identical, census DRIFT-CLEAN), closing on "
         "VERDICT R2285 PASS. Register closed through its own writer "
         "(debt_close line=57, open 2->1, done 34->35, readback ok) and "
         "product-face-R2286 opened first=yes through debt_append "
         "(before=35007B after=35381B, readback ok) naming the tech head at "
         "state/queue/tech.md:355 prefix AC-MGT1. Honest score: a 0-point "
         "verification window with no product face."),
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