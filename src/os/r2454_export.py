# r2454_export.py - R2454 status-export refresh: put the shipped closeout
# dialect wire on the CEO-visible faces, then publish through that same wire
# so the export lands in its own transport and is proved by the parity.
import io
import json
import os
import sys

BASE = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EXPORT = os.path.join(BASE, "docs", "status-export.json")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import closeout_export_parity_dialect_wire as CEPD  # noqa: E402

CURRENT = (
    "R2454 产品窗：closeout 发布线现在按目标自身换行方言组合并落盘 - CRLF 文档"
    "从 R2452 的 REFUSED 变成 WRITTEN/AGREES（lone_lf=0，413 行 CRLF），"
    "LF 文档字节与今天完全一致；病因在出生站修好（parity 组合改为调用时询问"
    "shipped 方言律），不是放宽判据"
)
ARTIFACT = (
    "src/os/closeout_export_parity_dialect_wire.py + "
    "src/os/test_closeout_export_parity_dialect_wire.py"
    "（套件 20/20 两跑同判 6 准则 × 2 + 3 邻套件绿；"
    "qa/closeout-export-parity-dialect-wire-R2454.log、"
    "qa/closeout-export-parity-dialect-wire-live-R2454.log）"
)
NEXT = (
    "下一窗=债务门 first=yes reconcile-battery-R2455（本轮改了产品字节，"
    "预注册 555 套件 / 4306 准则），24h 内跑绿并刷新矩阵"
)

OUT = (
    "closeout export parity dialect wire "
    "(src/os/closeout_export_parity_dialect_wire.py)",
    "on",
    "the closeout publish path could not land a CRLF export at all: "
    "export_closeout_gate_parity.closeout_style appended a hardcoded LF while "
    "queue_export_gate_wire kept the target's own dialect, so the parity read "
    "DISAGREES/bytes and the wire refused at exit 2. The composition now "
    "renders through general_writer_dialect_audit.payload_for asked at CALL "
    "time, and the new wire publishes, reads back and reports the transport "
    "and the lone-LF count. Suite 20/20 twice, registry 555 suites / 4306 "
    "criteria, matrix 53662B --check byte-identical.",
)

RESULT = (
    "R2454",
    "五静扫描干净（HEAD 7d6ee762、树净、24 行集团台账无新编号、决策 token "
    "差集 new=0、集团 orders 尾行 2026-11-05 00:36 与基线相同、基准 11-03 未超 "
    "7 天）；债务门 CLAIM-FIRST product-face-R2454；出生站修 parity 方言组合 + "
    "新产品线与 6 准则；实测第二处缺口（跨文档文本绑定盲区）落为 tech 行 528 "
    "AC-CEPM1；债务 118555B->118558B 关项、118558B->118758B 开电池项",
)


def main():
    with io.open(EXPORT, "r", encoding="utf-8-sig") as handle:
        data = json.load(handle)
    data["do"] = CURRENT
    face = data.get("ceo_face") or {}
    face["current"] = CURRENT
    face["latest_artifact"] = ARTIFACT
    face["next_milestone"] = NEXT
    data["ceo_face"] = face
    outs = list(data.get("outs") or [])
    outs.append("%s %s: %s" % (OUT[0], OUT[1], OUT[2]))
    data["outs"] = outs
    results = list(data.get("results") or [])
    results.append(["2454", "OSLoop 执行 tick"])
    data["results"] = results
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    report, code = CEPD.publish(os.path.dirname(EXPORT), EXPORT, text)
    print("PUBLISH verdict=%s transport=%s bytes=%d lone_lf=%d reading=%s"
          % (report["verdict"], report["transport"], report["bytes"],
             report["lone_lf"], report["reading"]))
    return 0 if code == 0 else 2


if __name__ == "__main__":
    sys.exit(main())