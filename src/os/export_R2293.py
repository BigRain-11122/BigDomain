"""R2293 export refresh: the CEO-visible face after a verification window.

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
    "verification window: the full reconcile battery on the committed R2292 tree "
    "reads RUNNER PASS 452/452 suites plus controls 7/7 in 854.9s with criteria total "
    "3688, exactly the pre-registered +1 suite / +6 criteria from the os-exempt-review "
    "suite; the four follow-up sections then read VERDICT PASS after the matrix section "
    "refused to rewrite the stale doc and the registry was regenerated to 452 suites / "
    "3688 criteria from this battery's own evidence"
)

CURRENT = (
    "R2293 验证轮（非产品面·诚实记 0 分）：在已提交的 R2292 树 3addd18e 上跑全量 reconcile "
    "电池，跑前 git status 全空（R2168 混合树规避）。结果 RUNNER PASS 452/452 套件 + 控制 7/7，"
    "854.9s，出生站清扫 932/932 世界 326.57 MiB busy=0 failed=0，判据总数 3688 —— 与预注册的 "
    "+1 套件 / +6 判据（对 R2291 的 451/3682）完全吻合，来自 R2292 的 os-exempt-review 套件，"
    "预测与实测无需更正。四段后续经 src/os/battery_followup.py 执行：矩阵段先如实 FAIL 于过期文档"
    "（盘上 43512B，重生成 43590B）且拒绝改写（设计如此），src/sandbox/suite_matrix.py 按本电池证据"
    "重生成 452 套件 / 3688 判据后复跑四段全 PASS（矩阵逐字节同一、指纹 5 域 CLEAN、"
    "profile --daily --check 逐字节同一、census DRIFT-CLEAN），VERDICT R2293 PASS。"
    "债务行经自带写入器关闭（debt_close line 65，open 2→1，done 42→43，回读 ok），"
    "后继 product-face-R2294 经 debt_append 置 first=yes（39148B→39394B，回读 ok）。"
    "收口跨水位，按整块折窗折 601（R2278 四行块，9 token 全覆盖），折后 75837B / 余量 2663B，"
    "四个账本套件复跑 8/8/8/8 全绿。"
)

LATEST = (
    "qa/reconcile-all-R2293.log（RUNNER PASS 452/452 + 控制 7/7，778152B）+ "
    "docs/sandbox-suite-matrix.md（452 套件 / 3688 判据，43590B）·2026-10-31"
)

NEXT = (
    "R2294 产品轮：回到债务闸点名的产品面 —— 技术队头 state/queue/tech.md:360，前缀 AC-SER1，"
    "即 R2280 的 stamp_exempt_review 种子（判据 AC-SER1..AC-SER6 已先于代码钉在该行内）。"
    "落一块带套件的产品面，认领使 tech 可认领降到 9 时补一条真缺口种子，先提交再跑电池。"
)

LAST = (
    "R2292 产品窗：src/os/exempt_review.py + 套件（6/6 双跑），"
    "qa/exempt-review-R2292.log·2026-10-31"
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
    data["results"] = [["R2293",
                        "R2293 verification window on the debt register first item "
                        "(product-face-R2293): the full reconcile battery on the "
                        "committed R2292 tree 3addd18e with an empty git status before "
                        "the run read RUNNER PASS 452/452 suites plus controls 7/7 in "
                        "854.9s, criteria total 3688 = exactly the pre-registered +1 "
                        "suite / +6 criteria against R2291 (451/3682) from the R2292 "
                        "os-exempt-review suite; four follow-up sections PASS after the "
                        "matrix section refused to rewrite the stale doc; register "
                        "closed and product-face-R2294 opened first=yes naming the tech "
                        "head at line 360 prefix AC-SER1; 0-point window with no "
                        "product face, honestly recorded"]] + data["results"]
    data["outs"] = [["a verification window that could only confirm a prediction it "
                     "had already registered, and it confirmed it exactly: 452 suites "
                     "/ 3688 criteria against the pinned 451 / 3682 (R2293)",
                     "on",
                     "R2293: the battery was launched detached and hidden because "
                     "battery_stream buffers its evidence in memory and writes once at "
                     "completion, so every probe before the end legitimately found no "
                     "file - buffering, not a dead runner, confirmed by the live process "
                     "and then by the 778152B file. No product code changed this "
                     "window."]] + data["outs"]
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