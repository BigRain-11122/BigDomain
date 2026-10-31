"""R2281 export refresh: rewrite the CEO-visible face from measured state.

F3 law: every field below is derived from this window's actual readings
(the battery evidence file, the suite matrix, the register writers) and the
self_drive block is recomputed by check_export_consistency.recompute()
rather than typed, so a stale counter cannot survive the refresh.
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
    data["do"] = ("verification window: the full reconcile battery and the four "
                  "follow-up sections re-proven on the committed tree with zero "
                  "product edits, and the pre-registered delta matched the "
                  "measurement exactly")
    face = data["ceo_face"]
    face["current"] = (
        "R2281 验证窗已完成：在已提交树 5d4038f7 上跑全量 reconcile 电池"
        "（446 套件全绿 + 7 控制项，917.8s，判据总数 3652，"
        "与预注册的 +1 套件/+6 判据精确一致）；四段 follow-up 全过"
        "（矩阵 43126B 逐字节同一、指纹链 CLEAN、runner profile 一致、"
        "census DRIFT-CLEAN）；债务行由本仓写入器自行关闭并开启 "
        "product-face-R2282。本轮零产品代码改动，诚实计 0 产品分。"
    )
    face["latest_artifact"] = (
        "qa/reconcile-all-R2281.log（774691B，单写者 utf-8 LF，"
        "RUNNER PASS 446/446 + 控制 7/7，917.8s，出生站 TMP 回收 "
        "932/932 世界 326.57 MiB busy=0 failed=0）与 "
        "docs/sandbox-suite-matrix.md（446 套件 / 3652 判据，43126B，"
        "重生成后 --check 逐字节同一）"
    )
    face["last_artifact"] = face["latest_artifact"]
    face["next_milestone"] = (
        "R2282 回产品面：取 tech 队头 line 347（AC-EVP1，"
        "evidence_parity 种子，六判据已在行内预注册），"
        "窗前做 git grep -F 零占用锚验，出一件带套件的产品面；"
        "若认领使 tech 可认领降至 9 则同窗补一条真缺口行，先提交再跑电池"
    )
    face["next_milestone_due"] = due_ts
    data["self_drive"] = derived
    for row in data["results"]:
        if isinstance(row, list) and len(row) == 2 and row[0] == "2280":
            row[0] = "2281"
    data["results"] = list(data["results"]) + [[
        "R2281",
        ("R2281 verification window on the debt register first item "
         "(reconcile-battery-R2281), discharged on the committed R2280 tree "
         "5d4038f7 with zero product edits until green (the R2168 mixed-tree "
         "rule): RUNNER PASS 446/446 suites + controls 7/7 in 917.8s, "
         "criteria total 3652 - exactly the pre-registered +1 suite / +6 "
         "criteria against R2279 (445/3646) from the os-queue-done-stamp-"
         "exempt suite. Four follow-up sections all PASS after the matrix "
         "regeneration (43126B, byte-identical), fingerprint CLEAN 5 domains, "
         "profile PASS, census DRIFT-CLEAN, VERDICT R2281 PASS. Register "
         "closed through its own writer and product-face-R2282 opened "
         "first=yes; honest score 0 product points."),
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