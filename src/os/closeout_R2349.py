"""closeout_R2349 - append this window round to state.json (R2349).

Verification window. Every figure written here was measured this window: the
battery verdict on the committed R2348 tree, the pre-registered target it was
compared against, the four follow-up sections after the designed matrix FAIL
and its regeneration, and the debt rows this window closed and opened.

State text is rewritten through state_io.canon with a read-back proof. Dry run
by default; --execute writes. Pure ASCII source, stdlib only.
"""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
STATE = os.path.join(ROOT, "src", "os", "state.json")
EXPORT = os.path.join(ROOT, "docs", "status-export.json")
HEARTBEAT = os.path.join(ROOT, "heartbeat.txt")
BACKLOG = os.path.join(ROOT, "src", "os", "backlog.md")

TICK = 2349
STAMP = "2026-11-01T23:20:00+08:00"

HEARTBEAT_LINE = (
    "R2349: battery on the committed R2348 tree read RUNNER PASS 482/482 "
    "suites plus controls 7/7 in 981.1s with criteria total 3868 exactly as "
    "pre-registered; the designed matrix FAIL was the stale doc and pointed at "
    "46114B regenerated, so suite_matrix regenerated and all four sections "
    "then PASS (matrix byte-identical 46114B, fingerprint CLEAN 5 domains, "
    "profile byte-identical, census DRIFT-CLEAN), VERDICT R2349 PASS; debt row "
    "reconcile-battery-R2348 closed and reconcile-battery-R2350 opened "
    "first=yes; zero product code, 0 product points\n"
)

sys.path.insert(0, BASE)
import state_io as SIO  # noqa: E402

ROUND_LINE = (
    "2026-11-01 R2349 verification window (five-silence scan at open: clean "
    "git status --short and no .git/index.lock; the content-addressed DEC "
    "diff read 65 live tokens against a 65-token baseline with new=[], the "
    "evolution ledger carries no @BigDomain row, the local orders board tail "
    "is unchanged and benchmarks were refreshed 2026-11-01, inside the "
    "seven-day gate). SELF-INFLICTED TRAP DISCLOSED FIRST: the window probed "
    "src/sandbox/reconcile_all.py with --help, which has no argument parser, "
    "so a real battery started and the truncating pipe killed it - exactly the "
    "shape R2348 disclosed and seeded runner_arg_guard (AC-RAG1..AC-RAG6) for. "
    "No battery process survived (checked by command line, not by name: the "
    "only python processes left were the MCP bridges and BigMoney's own "
    "smoke_test parent), and the 13859B stray '--help' file was deleted before "
    "any commit; nothing from that dead run is counted as work. The runner "
    "contract was then read FROM SOURCE (main(argv) takes argv[1] as the tee "
    "path) instead of probed. FIRST ITEM, the debt gate carried: THE BATTERY "
    "ON THE COMMITTED R2348 TREE with an empty git status before the run (the "
    "R2168 mixed-tree rule), pre-registered at 482 suites / 3868 criteria - "
    "exactly +1 suite / +6 criteria against R2347 (481/3862) from the "
    "os-retire-apply suite. MEASURED: RUNNER PASS 482/482 suites green plus "
    "controls 7/7 in 981.1s with birth-site TMP RECLAIM 932/932 worlds 326.59 "
    "MiB busy=0 failed=0 (qa/reconcile-all-R2349.log, single writer utf-8 LF "
    "through src/os/battery_stream.py, never a shell redirection), criteria "
    "total 3868 - the prediction matched the measurement exactly, no "
    "correction and no swept delta. THE FOLLOW-UP RAN AS DESIGNED: the matrix "
    "section FAILED first on the stale doc (on-disk=46044B "
    "regenerated=46114B) and did NOT rewrite it, suite_matrix then regenerated "
    "docs/sandbox-suite-matrix.md at 46114B with green=482/482, and the second "
    "pass read all four sections PASS (matrix byte-identical 46114B, "
    "fingerprint CLEAN domains=5, profile --check byte-identical, census "
    "DRIFT-CLEAN) for VERDICT R2349 PASS. DEBT: reconcile-battery-R2348 closed "
    "through debt_close (open 3->2, done 85->86, readback ok) and "
    "reconcile-battery-R2350 opened first=yes through debt_append (readback "
    "ok); the register still reads stale=2 because loop-s4u-reconcile (R2231, "
    "needs an elevated shell) and fold-block-boundary (R2336) are both older "
    "than the stale threshold, disclosed rather than hidden. NO PRODUCT FACE "
    "WAS SHIPPED and the window scores 0 product points honestly: the queue "
    "head is untouched at state/queue/tech.md:394 prefix AC-RTD1 "
    "(residue_triage_decl_reason), floors read main 5/5 tech 10/10 explore "
    "10/10 FLOOR-MET, and tasks.md was not touched because it carries no row "
    "for this slice."
)

LEDGER_LINE = (
    "R2349 tokens: local=1 api=0 api_reason=no cloud call was needed - the "
    "round was one battery on the committed tree, four local follow-up "
    "sections, two debt-register writes and the closeout, all stdlib/local."
)


def items():
    return [ROUND_LINE, LEDGER_LINE]


def bump(text):
    state = json.loads(text)
    state["tick"] = TICK
    state["log"] = list(state["log"]) + items()
    return json.dumps(state, ensure_ascii=False, indent=2) + "\n"


def write_export(execute):
    with io.open(EXPORT, "r", encoding="utf-8") as handle:
        doc = json.load(handle)
    face = doc.setdefault("ceo_face", {})
    face["current"] = (
        "R2349 验证窗：全量电池在已提交的 R2348 树上跑完——482 套件全绿 / 3868 "
        "判据（与预注册完全一致）、对账控制 7/7、981.1 秒、临时世界 932/932 "
        "回收零残留。四段后续按设计先红后绿：矩阵段先报文档过期且拒绝改写，"
        "suite_matrix 重生成到 46114B 后四段全 PASS，判定 R2349 PASS。本窗"
        "未出产品件（如实记 0 分），队列头部仍是 line 394 AC-RTD1。"
    )
    face["latest_artifact"] = (
        "qa/reconcile-all-R2349.log（482/482 套件绿、3868 判据、控制 7/7、"
        "981.1s）+ docs/sandbox-suite-matrix.md（46114B，482 套件 / 3868 判据）"
        "（2026-11-01 23:0x）"
    )
    face["next_milestone"] = (
        "R2350：产品面 state/queue/tech.md:394 AC-RTD1"
        "（residue_triage_decl_reason——把三分类声明的首部声明与逐条条目对账，"
        "首部陈旧读 HEAD-STALE）六判据交付+套件；随后电池预注册 483 套件 / "
        "3874 判据。2026-11-02 前完成。"
    )
    face["next_milestone_due"] = "2026-11-03T23:20:00+08:00"
    face["updated_at"] = STAMP
    doc["export_ts"] = STAMP
    body = json.dumps(doc, ensure_ascii=False, indent=2) + "\n"
    print("EXPORT keys=%d bytes=%d" % (len(doc), len(body.encode("utf-8"))))
    if execute:
        temp = EXPORT + ".closeout-tmp"
        with io.open(temp, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(body)
        os.replace(temp, EXPORT)


BOARD_LINE = (
    "- [x] [done 2026-11-01 R2349] verification window: THE BATTERY ON THE "
    "COMMITTED R2348 TREE with an empty git status before the run (the R2168 "
    "mixed-tree rule) - RUNNER PASS 482/482 suites green plus controls 7/7 in "
    "981.1s with birth-site TMP RECLAIM 932/932 worlds 326.59 MiB busy=0 "
    "failed=0 (qa/reconcile-all-R2349.log, single writer utf-8 LF through "
    "src/os/battery_stream.py), criteria total 3868 EXACTLY as pre-registered "
    "against R2347 (481/3862) from the R2348 os-retire-apply suite; the four "
    "follow-up sections ran as designed (matrix FAILED first on the stale doc "
    "and did not rewrite it; suite_matrix regenerated 46114B at green=482/482; "
    "re-run read matrix byte-identical, fingerprint CLEAN 5 domains, profile "
    "byte-identical, census DRIFT-CLEAN) for VERDICT R2349 PASS; debt row "
    "reconcile-battery-R2348 closed and reconcile-battery-R2350 opened "
    "first=yes; zero product code, 0 product points. DISCLOSED: the open "
    "probed reconcile_all.py with --help, started a real battery and the "
    "truncating pipe killed it - the R2348 runner_arg_guard trap repeated - "
    "with no surviving process and the 13859B stray '--help' file deleted "
    "before any commit; the runner contract was then read from source. Head "
    "carried to R2350 at state/queue/tech.md:394 AC-RTD1."
)


def main(argv):
    execute = "--execute" in argv
    with open(STATE, "r", encoding="utf-8", newline="") as handle:
        text = handle.read()
    new_text = bump(text)
    before = json.loads(text)
    after = json.loads(new_text)
    same = all(after[key] == before[key] for key in before
               if key not in ("log", "tick"))
    grew = len(after["log"]) == len(before["log"]) + len(items())
    canon = SIO.canon(new_text)
    print("CLOSEOUT R2349 tick=%d items=%d log=%d->%d fields_same=%s "
          "canon_bytes=%d"
          % (after["tick"], len(items()), len(before["log"]), len(after["log"]),
             same, len(canon.encode("utf-8"))))
    if not (same and grew and after["tick"] == TICK):
        print("E_CLOSE_SHAPE: refusing to write")
        return 2
    if not execute:
        print("DRY RUN: pass --execute to write")
        write_export(False)
        return 0
    if SIO.canon(canon) != canon:
        print("E_CLOSE_CANON: the text is not in the state canon")
        return 2
    temp = STATE + ".closeout-tmp"
    with open(temp, "wb") as handle:
        handle.write(canon.encode("utf-8"))
    os.replace(temp, STATE)
    written = len(canon.encode("utf-8"))
    with open(STATE, "rb") as handle:
        back = handle.read()
    ok = (back.decode("utf-8") == canon
          and json.loads(back.decode("utf-8"))["tick"] == TICK)
    print("WROTE %s bytes=%d READBACK ok=%s" % (STATE, written, ok))
    if not ok:
        return 2
    write_export(True)
    with io.open(HEARTBEAT, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(HEARTBEAT_LINE)
    with io.open(BACKLOG, "r", encoding="utf-8", newline="") as handle:
        board = handle.read()
    if "[done 2026-11-01 R2349]" in board:
        print("BOARD already carries this row")
    else:
        with io.open(BACKLOG, "w", encoding="utf-8", newline="") as handle:
            handle.write(BOARD_LINE + "\n" + board)
        print("BOARD row prepended bytes=%d" % len(BOARD_LINE))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))