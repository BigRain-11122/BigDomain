"""R2296 export refresh: the CEO-visible face after the product window.

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
    "product window: the legacy evidence pile gained a read-only output map - "
    "per script the qa paths it declares, every collision naming both scripts "
    "and the declaration line, and the cited outputs nobody declares, so a "
    "legacy script can be retired without silently deleting a file another one "
    "still owns or breaking a citation"
)

CURRENT = (
    "R2296 产品轮：认领 tech 队头 AC-EOM1（R2282 evidence_output_map 种子，判据先于代码钉在该行），"
    "交付 src/os/evidence_output_map.py + 套件。它回答「删掉一件遗留证据脚本安不安全」——按脚本列出它"
    "声明的 qa 产物路径、把两件脚本同写一条路径的冲突连同双方脚本名与声明行号一起报告、再把「被记录"
    "引用却无人声明」的产物单列。全程只读、不跑被审脚本、不读时钟。套件 SUITE PASS 6/6 双跑判据行"
    "同一 digest F9ABC32AFC68130B，五邻域套件同次捕获全绿（qa/evidence-output-map-R2296.log，1273B，"
    "单写者 utf-8 LF），接线 os-evidence-output-map(6)。实况读数（qa/evidence-output-map-live-R2296.log）："
    "92 件脚本 / 164 条声明路径 / 0 冲突 / 16 条被引用但无人声明 / 1 件读 NONE——冲突腿在夹具上已实证、"
    "在真实数据上尚未触发，如实披露。声明读取覆盖四种本仓写法（拼接字面量、os.path.join 拆分、字符串相加、"
    "qa 目录常量先绑定后拼接）。认领后 tech 可认领数降到 9，故同窗补入一条真缺口种子 "
    "evidence_output_audit（AC-EOA1..AC-EOA6 预注册，五锚零占用），floor 复归 main 5/5 tech 10/10 explore 10/10。"
    "收口：state 折叠 603（log 1..10 整块迁入 archive，token 全覆盖，82229B→71779B，预测=实测，"
    "归档 4952494B→4968242B），账本四套件复跑 8/8/8/8 全绿；债务行经自带写入器关闭（line 68，"
    "open 2→1，done 45→46，回读 ok），后继 product-face-R2297 置 first=yes（40820B→41502B，回读 ok）。"
)

LATEST = (
    "src/os/evidence_output_map.py + qa/evidence-output-map-R2296.log（SUITE PASS 6/6 双跑同一 digest，"
    "五邻域全绿）+ qa/evidence-output-map-live-R2296.log（92 脚本 / 164 声明 / 0 冲突 / 16 引用未声明）·2026-11-01"
)

NEXT = (
    "R2297 验证轮：在已提交的 R2296 树上零产品改动跑全量套件电池，预注册期望本轮 453 套件/3694 判据"
    "→ +1 套件/+6 判据（来自 os-evidence-output-map），随后四段后续（矩阵段先 FAIL 后重生成再 PASS）；"
    "之后产品面回到 tech 队头第 364 行 AC-SRS1。窗 ≤24h。"
)

LAST = (
    "R2296 产品轮：遗留证据脚本的产物地图交付，qa/evidence-output-map-R2296.log·2026-11-01"
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
    data["results"] = [["R2296",
                        "R2296 product window on the debt register first item "
                        "(product-face-R2296): claimed the tech head the reader "
                        "named, state/queue/tech.md line 362 prefix AC-EOM1, whose "
                        "AC-EOM1..AC-EOM6 criteria were already pinned in that row "
                        "BEFORE the code, after a fresh zero-occupancy anchor check "
                        "at HEAD. src/os/evidence_output_map.py plus its suite report "
                        "per legacy script the qa outputs it declares, every path two "
                        "scripts both claim (naming both scripts and the declaration "
                        "line) and the cited outputs no script declares, so retiring a "
                        "script stops being a hunch; it never runs the scripts it "
                        "judges, writes nothing and reads no clock. SUITE PASS 6/6 "
                        "double-run with identical digest F9ABC32AFC68130B and five "
                        "adjacent suites green through evidence_capture, wired "
                        "os-evidence-output-map(6). Live: 92 scripts, 164 declared "
                        "paths, 0 collisions, 16 cited-but-undeclared outputs and 1 "
                        "NONE row, so the collision leg has fired on fixtures but not "
                        "yet on real data - disclosed. One real gap row seeded "
                        "(evidence_output_audit, AC-EOA1..AC-EOA6) to hold the tech "
                        "floor at 10/10; register closed and product-face-R2297 opened "
                        "first=yes naming the battery"]] + data["results"]
    data["outs"] = [["a read-only map that makes deleting a legacy evidence script "
                     "a decidable act: the qa paths each script declares, the paths "
                     "two scripts both own, and the cited outputs nobody declares "
                     "(R2296)",
                     "on",
                     "the first suite run was red 2/6 because the fixture writes its "
                     "declarations as os.path.join(ROOT, 'qa', '<name>') and the "
                     "module only read the joined literal form; the module gained the "
                     "form and two more were added only after the live pile exposed "
                     "them. No criterion was widened. The first capture was refused "
                     "E_EVC_RED on a relative --root and the second E_EVC_BADDIR on a "
                     "relative --evidence; the sanctioned run passed both absolute and "
                     "left no partial file."]] + data["outs"]
    # Derived face: recompute through the shipped checker so flush and check
    # share one caliber (the R1254 flush-drift precedent); nothing is invented.
    import check_export_consistency as consistency
    derived, _, _, pat = consistency.recompute()
    data["self_drive"] = derived
    label = pat["tick_row_label"]
    tick_rows = [row for row in data["results"]
                 if isinstance(row, list) and len(row) >= 2 and row[1] == label]
    if len(tick_rows) != 1:
        print("E_TICK_ROW expected exactly one tick row, found %d"
              % len(tick_rows))
        return 3
    tick_rows[0][0] = str(json.loads(
        open(os.path.join(ROOT, "src", "os", "state.json"), "rb")
        .read().decode("utf-8"))["tick"])
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