"""R2248 closeout: state.json tick + log, and the CEO-visible export.

Single writer. state.json is re-serialised at the measured layout
(indent 2, CRLF, one trailing newline) and the export's derived faces
are recomputed through check_export_consistency.recompute() so the flush
and the checker share one caliber (F3 law: no canned numbers).
"""

import datetime as dt
import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import check_export_consistency as CEC  # noqa: E402

P_STATE = os.path.join(BASE, "state.json")
P_EXPORT = os.path.join(ROOT, "docs", "status-export.json")

ROUND = "R2248"

LOG_ITEMS = [
    "2026-10-29 R2248 (five-silence scan clean at open: decisions.md carries "
    "181 content-addressed D/C tokens against the stored 190-token superset "
    "baseline with ZERO additions, so zero domain action; the group ledger "
    "carries the same three @BigDomain patrol rows, none numbered, already "
    "paid off, so zero unreplied handoffs; the group orders tail is unchanged "
    "at the 2026-10-29 02:1x CEO-PROXY event round R2.48 already consumed in "
    "R2226; benchmarks refreshed 2026-10-29 inside the seven-day gate; tree "
    "clean, no index.lock) - the P1 canonical rows stay blocked-on-CEO and "
    "the weekly proposal duty is met by BD-PROP-005, so this window took the "
    "P2 tech head that R2247 named. Product: state/debt.md plus "
    "src/os/debt_register.py, the register the R2240-c seed asked for. The "
    "pain was concrete: every product window defers the reconcile battery, "
    "and the deferral lived only in log prose, so 'owed since R2244, third "
    "window running' had to be re-derived by reading the tail of state.json. "
    "Now a row is a row: column-0 checkbox plus pipe-separated key=value "
    "segments, known keys only, unknown or duplicate or missing keys refused "
    "rather than guessed, at most one open row may carry first=yes (two is "
    "E_DR_BAD_FIRST), and a debt carried three windows or more is an alarm "
    "with its own exit code. Staleness is a window count and needs --round; "
    "without it the checker says stale=unknown instead of pretending. CLI "
    "exits 0 clean / 2 open / 3 missing-or-malformed / 4 stale / 5 bad "
    "flags, and --json carries the eleven pinned report keys byte-stably. "
    "Criteria AC-DEBT1..AC-DEBT6 were pre-registered in state/queue/tech.md "
    "as the R2240-c seed before this code existed; AC-DEBT7 (live-tree "
    "agreement with an independent recount) and AC-DEBT8 (battery wiring) "
    "landed in the same window and are disclosed as such, with no "
    "pre-registered criterion relaxed. The first suite run read 7/8 and the "
    "red was a real shape defect - done rows were missing the carried/stale "
    "keys - fixed in the implementation, not by widening the criterion. "
    "Evidence: SUITE PASS 8/8 double-run byte-identical criterion sha16 "
    "8230EE0683CCB6EB (qa/debt-register-R2248-a.log and -b.log, 800B each, "
    "single writer utf-8 LF by src/os/evidence_R2248.py, never a shell "
    "redirection); wired os-debt-register(8); five adjacent os suites green "
    "(qa/regression-R2248.log, fails=0). The register's first real reading "
    "names the live truth: DEBT REGISTER open=2 done=2 "
    "first=reconcile-battery-and-matrix stale=1 carried=17 verdict=DEBT-STALE "
    "- the seventeen-window S4U item is the stale one. Second product: the "
    "seeding duty R2247 handed over was discharged - ten seed rows landed "
    "(five tech, five explore), every anchor checked zero-occupancy against "
    "HEAD with git grep -F rc=1, and the floor gauge now reads QUEUE FLOOR "
    "main=5/5 tech=10/10 explore=10/10 verdict=FLOOR-MET shortfall=0, up "
    "from FLOOR-DEBT shortfall=10. The queue-seeding row is closed in the "
    "register with closed=R2248. Honest debt: this window changed src/os, "
    "the battery runner and two queue files but did NOT run the full "
    "reconcile battery or regenerate the suite matrix (25-minute budget, the "
    "R2168 mixed-tree rule), and that is registered as the open "
    "first=yes row for R2249.",
    "R2248 tokens: local=~26k api=0 api_reason=product window on the P2 tech "
    "head - one register module with its eight-criterion suite, one "
    "single-writer double-run evidence pair, five adjacent os regressions, "
    "ten zero-occupancy-checked seed rows, and the state/export/backlog "
    "closeout; zero cloud calls and zero external API touches",
    "R2248 self-heal check: BigDomain-OSLoop exists and is Running, but its "
    "principal still reads LogonType=InteractiveToken, which the 2026-09-29 "
    "machine law forbids for every lane task; src/os/register_loop_task.ps1 "
    "already passes an explicit S4U principal but applying it needs an "
    "elevated shell and this session is unelevated, so the definition of the "
    "loop hosting this window was left untouched. Open local-lane item for an "
    "elevated window (eighteenth consecutive disclosure, now registered as "
    "the stale row loop-s4u-reconcile in state/debt.md).",
]

DO = ("product window R2248: carried debt becomes a register with a "
      "checker (state/debt.md + src/os/debt_register.py, AC-DEBT1..8 green "
      "8/8) and the standing floors are back to FLOOR-MET "
      "(main 5/5 tech 10/10 explore 10/10)")

CURRENT = ("R2248 产品轮：债务登记册 + 检查器落盘（state/debt.md、"
           "src/os/debt_register.py，判据 AC-DEBT1..8 全绿 8/8·双跑逐字节一致），"
           "并把队列补回地板（main 5/5·tech 10/10·explore 10/10，"
           "十条种子均过零占用锚检）。登记册实况=open 2 done 2 "
           "stale 1 carried 17（卡在提权壳的 S4U 项）。")

LAST_ARTIFACT = ("state/debt.md + src/os/debt_register.py（R2248，"
                 "2026-10-29 12:0x）；证据 qa/debt-register-R2248-a.log / "
                 "-b.log，回归 qa/regression-R2248.log")

NEXT = ("R2249 先跑全量电池 + 矩阵重生成（本轮改了 src/os、电池runner与两个队列文件，"
        "必须在已提交树上验证；R2168 混树律），窗 ≤48h")


def write_text(path, text, newline="\r\n"):
    data = text.replace("\r\n", "\n").replace("\n", newline).encode("utf-8")
    with io.open(path, "wb") as handle:
        handle.write(data)
    return len(data)


def main():
    with io.open(P_STATE, "r", encoding="utf-8") as handle:
        text = handle.read()
    state = json.loads(text)
    state["tick"] = state.get("tick", 0) + 1
    for item in LOG_ITEMS:
        state["log"].append(item)
    body = json.dumps(state, indent=2, ensure_ascii=False)
    if not body.endswith("\n"):
        body += "\n"
    size = write_text(P_STATE, body)
    print("STATE tick=%d items=%d bytes=%d"
          % (state["tick"], len(state["log"]), size))

    with io.open(P_EXPORT, "r", encoding="utf-8") as handle:
        export = json.loads(handle.read())
    now = dt.datetime.now(dt.timezone(dt.timedelta(hours=8)))
    export["export_ts"] = now.replace(microsecond=0).isoformat()
    export["do"] = DO
    face = export.get("ceo_face", {})
    face["current"] = CURRENT
    face["last_artifact"] = LAST_ARTIFACT
    face["next_milestone"] = NEXT
    export["ceo_face"] = face
    export["outs"].insert(0, [
        "debt register + checker, and the standing floors restored (R2248)",
        "on",
        "R2248: state/debt.md is the machine-readable carried-debt "
        "register and src/os/debt_register.py is its checker "
        "(AC-DEBT1..8 green 8/8, double-run byte-identical sha16 "
        "8230EE0683CCB6EB, wired os-debt-register(8)); live reading "
        "DEBT REGISTER open=2 done=2 first=reconcile-battery-and-matrix "
        "stale=1 carried=17 verdict=DEBT-STALE. Ten seed rows with "
        "pre-registered criteria landed after zero-occupancy anchor "
        "checks, so QUEUE FLOOR reads main=5/5 tech=10/10 explore=10/10 "
        "FLOOR-MET (was FLOOR-DEBT shortfall=10).",
    ])
    export["results"].insert(0, [
        ROUND,
        "product window: carried debt is a register instead of log prose "
        "(state/debt.md + src/os/debt_register.py, AC-DEBT1..8 green 8/8, "
        "double-run byte-identical criterion sha16 8230EE0683CCB6EB, five "
        "adjacent os suites green), the ten-row seeding duty is discharged "
        "and the floors read FLOOR-MET; the full battery and the matrix "
        "regeneration were NOT run (25-minute budget, R2168 mixed-tree "
        "rule) and are the registered first item for R2249",
    ])
    self_drive, _state, _export, _patterns = CEC.recompute()
    export["self_drive"] = self_drive
    body = json.dumps(export, indent=2, ensure_ascii=False)
    if not body.endswith("\n"):
        body += "\n"
    size = write_text(P_EXPORT, body)
    print("EXPORT bytes=%d self_drive=%s" % (size, json.dumps(self_drive)))
    return 0


if __name__ == "__main__":
    sys.exit(main())