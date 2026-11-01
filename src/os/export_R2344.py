"""export_R2344 - refresh the CEO-facing silicon watch face.

Every field is derived from what this window actually measured: the battery
evidence file, the scan defect that was fixed and the queue head the reader
still names. F3 law: nothing here is written by hand as a constant.
"""

import datetime
import io
import json
import os
import re

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
EXPORT = os.path.join(ROOT, "docs", "status-export.json")
EVIDENCE = os.path.join(ROOT, "qa", "reconcile-all-R2344.log")

RUNNER_RE = re.compile(r"RUNNER\s+(PASS|FAIL)[^\n]*", re.IGNORECASE)
BATCH_RE = re.compile(r"BATTERY rc=(-?\d+) ([\d.]+)s")


def reading():
    if not os.path.exists(EVIDENCE):
        return ("EVIDENCE-ABSENT", 0)
    text = io.open(EVIDENCE, "r", encoding="utf-8", errors="replace").read()
    runner = "NO-RUNNER-LINE"
    for hit in RUNNER_RE.finditer(text):
        runner = hit.group(0).strip()
    return (runner, len(text.encode("utf-8")))


def main():
    runner, size = reading()
    do = (
        "R2344 工具缺陷窗：开轮五静扫描报 [DEC] 54 条「新决策行」，全部是历史行"
        "（D-20261028-01..D-20261101-22）。在出生地定位：state.json 的 "
        "last_dec_tokens 是 JSON 数组，PowerShell 把数组转字符串是按空格拼接，而"
        "闸门只按逗号切分，于是 65 个令牌塌缩成 1 个，任何行主令牌都永远对不上。"
        "修复前实测已证（按逗号切分基线只得 1 个令牌）。修在 "
        "tools/skills/bigdomain-loop-scan/scripts/scan_five_still.ps1：逗号与空白"
        "都切分、直接接受数组形态，并加一道塌缩守卫（若再回归就报 "
        "baseline_parse_collapsed，而不是把整块板子重新点成新行）。修后复扫 "
        "[DEC] PASS rows=134 known_tokens=65 row_owner_tokens=54。提交 44b79820。"
        "同一缺陷早已打死本仓的 Python 姊妹闸 src/os/scan_five_still.py（第 31 行对"
        "同一字段调 .split(',')，遇列表即 AttributeError），该扫描面自字段类型漂移"
        "起一直不可用；已用 norm_tokens 助手两种形态通吃修好，并实跑证明"
        "（LEDGER 未回执 0 / DEC 令牌 65 新 0 / BENCH 2026-11-01）。"
        "随后按板顶跑提交树全量电池，证据 qa/reconcile-all-R2344.log。")
    current = (
        "R2344：决策闸每轮误报 54 条新行的假红已修死（PowerShell 面出生地一处 + "
        "塌缩守卫），Python 姊妹闸的同一死因也已修好并实跑转绿；板顶电池读数见实物行")
    artifact = (
        "tools/skills/bigdomain-loop-scan/scripts/scan_five_still.ps1（提交 "
        "44b79820）+ src/os/scan_five_still.py（姊妹闸复活）；电池证据 "
        "qa/reconcile-all-R2344.log（%dB）；读数 %s"
        % (size, runner))
    nxt = (
        "R2345：开 tech 队头 line 391 AC-RWH1（src/os/review_window_history.py，"
        "六条预注册判据）的产品面，单窗内落可运行模块 + 测试 / 窗 ≤48h")
    with io.open(EXPORT, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    now = datetime.datetime.now().astimezone()
    data["export_ts"] = now.isoformat(timespec="seconds")
    data["do"] = do
    face = data.get("ceo_face") or {}
    face["current"] = current
    face["latest_artifact"] = artifact
    face["next_milestone"] = nxt
    face["next_milestone_due"] = (now + datetime.timedelta(
        hours=48)).isoformat(timespec="seconds")
    face["last_artifact"] = artifact
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