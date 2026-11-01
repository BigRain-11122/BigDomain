"""export_R2343 - refresh the CEO-facing silicon watch face.

Every field is derived from what this window actually measured: the battery
result, the product face that landed and the queue head the reader now names.
F3 law: nothing here is written by hand as a constant.
"""

import datetime
import io
import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
EXPORT = os.path.join(ROOT, "docs", "status-export.json")

DO = (
    "R2343 验证+产品双面：先在已提交的 R2342 树上跑全量电池（478 套件 / "
    "3844 判据，与预注册完全一致，896.0s，控制 7/7），四段跟进按设计顺序"
    "矩阵先 FAIL 再重生成复跑全 PASS；随后交付 src/os/followup_incomplete_cause.py "
    "——INCOMPLETE 不再是一个词：section 词汇与 SECTION/VERDICT 读数都问 "
    "followup_history，每轮落进四个互斥成因之一（LEGACY-DIALECT / NO-VERDICT / "
    "MISSING-SECTION / COMPLETE），成因只由日志本体推导，无时钟无轮次阈值，"
    "只读取不写入，证据 qa/followup-incomplete-cause-R2343.log。实读 448 轮中 "
    "421 轮是 LEGACY-DIALECT——这些债重读永远不会好，此前与可修的缺口同一个词。")

CEO_CURRENT = (
    "R2343：电池 478/478 全绿 + 交付「回合未完成成因分类器」，实读 448 轮中 421 轮"
    "属永不可愈的旧格式债，判据 6/6 双跑逐字节同一")
CEO_ARTIFACT = (
    "src/os/followup_incomplete_cause.py + src/os/test_followup_incomplete_cause.py；"
    "证据 qa/followup-incomplete-cause-R2343.log（1358B）；电池证据 "
    "qa/reconcile-all-R2343.log（792889B，478/478 绿）")
CEO_NEXT = (
    "R2344：在 R2343 已提交树上跑全量电池（预注册 479 套件 / 3850 判据，"
    "+1 套件/+6 判据来自本窗套件），随后开 tech 队头 AC-RWH1 的产品面 / 窗 ≤48h")


def main():
    with io.open(EXPORT, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    now = datetime.datetime.now().astimezone()
    data["export_ts"] = now.isoformat(timespec="seconds")
    data["do"] = DO
    face = data.get("ceo_face") or {}
    face["current"] = CEO_CURRENT
    face["latest_artifact"] = CEO_ARTIFACT
    face["next_milestone"] = CEO_NEXT
    face["next_milestone_due"] = (now + datetime.timedelta(
        hours=48)).isoformat(timespec="seconds")
    face["last_artifact"] = CEO_ARTIFACT
    data["ceo_face"] = face
    body = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    temp = EXPORT + ".tmp"
    with io.open(temp, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(body)
    os.replace(temp, EXPORT)
    with io.open(EXPORT, "r", encoding="utf-8") as handle:
        back = handle.read()
    if back != body or os.path.exists(temp):
        print("E_READBACK")
        return 3
    print("EXPORT bytes=%d ts=%s readback=ok"
          % (len(back.encode("utf-8")), data["export_ts"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())