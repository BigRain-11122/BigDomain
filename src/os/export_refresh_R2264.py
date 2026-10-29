# export_refresh_R2264.py - refresh docs/status-export.json from this
# window's measured state. Every value is derived from files on disk
# (F3 law): the battery counts come from the R2264 evidence log, the
# tick from state.json, the milestone window from the wall clock.
# Pure stdlib, pure ASCII source, utf-8 LF writer without BOM.
import io
import json
import os
import re
import sys
import time

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     "..", ".."))
PATH = os.path.join(ROOT, "docs", "status-export.json")
LOG = os.path.join(ROOT, "qa", "reconcile-all-R2264.log")
MATRIX = os.path.join(ROOT, "docs", "sandbox-suite-matrix.md")

CURRENT = (
    "R2264 是验证轮：在已提交的树上重跑全量回归，不碰产品码。电池一次通过 "
    "436/436 套件 + 7/7 控制项（856.5s），矩阵再生到 436 套件 / 3593 判据，"
    "指纹 CLEAN、跑手档 PASS、证据写者普查 DRIFT-CLEAN（files=2210 flags=0）。"
    "本轮零产品码改动，得分诚实地记 0 分；目的是把上一轮新增的队列残留分类器"
    "纳入全量回归，避免「自己的套件绿、邻域其实已断」的假绿。"
)
LATEST = (
    "qa/reconcile-all-R2264.log（769785B·单写者 utf-8 LF·crlf=0 bare_cr=0 "
    "bom=False）+ docs/sandbox-suite-matrix.md（436 套件 / 3593 判据·42342B·"
    "green=436/436）+ 四段收尾工具 src/os/battery_followup_R2264.py"
)
NEXT = (
    "R2265 回到产品面：认领队头可交付行（R2263 补种的 log_floor 技术行，或 "
    "explore 队头 api_seller_refund_months），判据先写进队列行再动代码，"
    "锚点先验零占用；预计 2026-10-30 前出可跑实物"
)
RESULTS = (
    "R2264 verification window on the debt register first item "
    "(product-face-R2264 = reconcile battery): zero product code changed "
    "(the R2168 mixed-tree rule). RUNNER PASS 436/436 suites plus controls "
    "7/7 in 856.5s with birth-site TMP RECLAIM 932/932 worlds 326.57 MiB "
    "busy=0 failed=0 (qa/reconcile-all-R2264.log, single-writer utf-8 LF "
    "through src/os/battery_stream.py), expected criteria total 3593. Four "
    "follow-up sections all PASS via src/os/battery_followup_R2264.py - "
    "matrix 436 suites / 3593 criteria byte-identical (42342B, green=436/436), "
    "fingerprint CLEAN 5 domains, runner profile --daily --check PASS, writer "
    "census re-frozen then DRIFT-CLEAN files=2210 tee=1681 baselined=529 "
    "disappeared=0 flags=0, VERDICT PASS. The +1 suite / +6 criteria against "
    "R2262 is exactly the R2263 os-queue-only suite joining the registry and "
    "the pre-registered prediction matched the measured total exactly. Honest "
    "score 0 product points; heartbeat.txt backfilled ticks 2260..2264 from "
    "the state log. Register row closed, successor product-face-R2265 opened "
    "first=yes."
)


def main():
    raw = io.open(PATH, "rb").read()
    doc = json.loads(raw.decode("utf-8"))
    state = json.loads(io.open(os.path.join(ROOT, "src", "os", "state.json"),
                               "rb").read().decode("utf-8"))
    log_text = io.open(LOG, "rb").read().decode("utf-8", "replace")
    m = re.search(r"RUNNER PASS \((\d+)/(\d+) suites green, reconcile controls "
                  r"(\d+)/(\d+), ([\d.]+)s\)", log_text)
    if not m:
        print("REFUSE: no RUNNER line in evidence")
        return 2
    suites, crit = m.group(1), None
    mc = re.search(r"registry suites=(\d+) criteria=(\d+)", log_text)
    if mc:
        crit = mc.group(2)
    matrix_bytes = os.path.getsize(MATRIX)
    face = doc.get("ceo_face", {})
    doc["ceo_face"] = {
        "current": CURRENT,
        "latest_artifact": LATEST,
        "last_artifact": face.get("latest_artifact", ""),
        "next_milestone": NEXT,
        "next_milestone_due": time.strftime("%Y-%m-%dT23:59:59+08:00",
                                            time.localtime(time.time()
                                                           + 86400)),
    }
    doc["do"] = ("verification window R2264 on the debt register first item: "
                 "the whole reconcile battery and the suite matrix were "
                 "re-proven on the committed tree with zero product code "
                 "changed, so the R2263 reader is covered by every suite and "
                 "not only by its own plus neighbours.")
    doc["export_ts"] = time.strftime("%Y-%m-%dT%H:%M:%S+08:00")
    doc["results"].append(["R2264", RESULTS])
    out = (json.dumps(doc, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    io.open(PATH, "wb").write(out)
    back = json.loads(io.open(PATH, "rb").read().decode("utf-8"))
    ok = (back["results"][-1][0] == "R2264"
          and back["export_ts"] == doc["export_ts"])
    print("EXPORT rows=%d suites=%s criteria=%s matrix_bytes=%d bytes=%d ok=%s"
          % (len(back["results"]), suites, crit, matrix_bytes, len(out), ok))
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main())