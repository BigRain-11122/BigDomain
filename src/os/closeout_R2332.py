"""R2332 closeout: append the round items, refresh the CEO face, bump the heartbeat.

Bookkeeping only - this window shipped no product code (verification window).
"""

import io
import json
import os
import sys
import tempfile

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "os"))

import state_io  # noqa: E402
import ledger_lines  # noqa: E402

STATE = os.path.join(BASE, "os", "state.json")
EXPORT = os.path.join(BASE, "docs", "status-export.json")
HEARTBEAT = os.path.join(BASE, "heartbeat.txt")

NARRATIVE = (
    "2026-11-01 R2332 verification window (five-silence scan clean at open: empty "
    "git status --short and no index.lock; the content-addressed diff of the group "
    "decisions.md against the stored baseline read NEW=0 over 59 live tokens, so no "
    "decision row was owed; the evolution ledger carries no @BigDomain row at all; the "
    "group orders tail is unchanged at the 2026-11-01 10:4x baseline R2321 already "
    "acked by number as non-execution; benchmarks refreshed 2026-11-01 inside the "
    "seven-day gate). The debt register's only open row is the elevated-shell S4U "
    "item, so this window claimed the board TOP row: THE BATTERY ON THE COMMITTED "
    "TREE 5574820a with zero product edits (the R2168 mixed-tree rule) and an empty "
    "git status before the run. RUNNER PASS 473/473 suites green plus controls 7/7 in "
    "907.8s with birth-site TMP RECLAIM 932/932 worlds 326.59 MiB busy=0 failed=0 "
    "(qa/reconcile-all-R2332.log, 790225B re-read at close, single writer utf-8 LF "
    "through src/os/battery_stream.py, never a shell redirection), criteria total 3814 "
    "- EXACTLY the pre-registered 473/3814 against R2330 (472/3808) from the R2331 "
    "os-retire-candidate suite, so the prediction matched the measurement with no "
    "correction. Four follow-up sections ran through src/os/battery_followup.py in the "
    "designed order: matrix FAILED first on the stale doc (on-disk=45292B "
    "regenerated=45349B) and did NOT rewrite it; src/sandbox/suite_matrix.py "
    "regenerated docs/sandbox-suite-matrix.md to 473 suites / 3814 criteria (45349B); "
    "the re-run read all four PASS (matrix byte-identical, fingerprint CLEAN 5 domains, "
    "profile --daily --check byte-identical, census DRIFT-CLEAN), closing VERDICT R2332 "
    "PASS. Residue re-read at close: declaration=PINNED declared_by=R2331 residue=195 "
    "triaged=195 untriaged=0 expired=0 verdict=TRIAGED, so no splice was owed (no fold "
    "ran this window). Honest score: a 0-point verification window with no product face."
)

TOKENS = (
    "R2332 tokens: local=~8k api=0 api_reason=verification-only window on the "
    "committed tree - one full reconcile battery (473/473 suites, 3814 criteria) with "
    "its streamed evidence file, two four-section follow-ups (the designed matrix FAIL "
    "then PASS) plus one matrix regeneration, one residue re-read, and the "
    "state/export/heartbeat/board closeout; zero cloud calls and zero external API "
    "touches; the product face resumes at R2333"
)

SELF_HEAL = (
    "R2332 self-heal check: BigDomain-OSLoop is registered and its principal still "
    "reads LogonType=InteractiveToken, which the 2026-09-29 machine law forbids for "
    "lane tasks; src/os/register_loop_task.ps1 already passes an explicit S4U principal "
    "and needs an elevated shell, which this session is not, so the definition was left "
    "untouched (ninety-fourth consecutive disclosure, carried as the stale row "
    "loop-s4u-reconcile in state/debt.md)."
)

DECISION = (
    "R2332 decision gate (D-20260930-19 step 2): the content-addressed diff of the "
    "group decisions.md against the stored baseline read NO new tokens (new=[] over 59 "
    "live tokens), and the evolution ledger carries no @BigDomain row at all, so "
    "nothing was executed, rejected or acknowledged this window and the baseline is "
    "unchanged."
)

HONEST = (
    "R2332 honest disclosures: (a) this window shipped NO product code and scores 0 "
    "product points; the work it did was the battery the board named. (b) The battery "
    "ran as a background shell task; the evidence file is the runner's own streamed "
    "write and its byte size was re-read at close (790225B), so no bytes are claimed "
    "from a tool capture. (c) The pre-registered target was met exactly, which is the "
    "point of pre-registration: the +1 suite / +6 criteria against R2330 resolves to "
    "the R2331 os-retire-candidate suite, and any larger delta would have had to be "
    "named rather than swept. (d) No fold ran this window, so no fold-creates-residue "
    "splice was owed, and the declaration still reads TRIAGED with until=R2350. (e) "
    "tasks.md was left untouched: it is the P-47 canonical board and carries no row for "
    "a verification window, disclosed rather than silently skipped. (f) state.json was "
    "NOT off the write canon at open (70109B, margin 8391B under the 78500B gate), so "
    "no canon repair was needed before the append."
)


def main():
    raw = state_io.read_raw(STATE)
    text = state_io.decode(raw)
    state = state_io.parse(text)
    before = len(raw)
    state["tick"] = 2332
    for item in (NARRATIVE, TOKENS, SELF_HEAL, DECISION, HONEST):
        state["log"].append(item)
    new_text = json.dumps(state, indent=2, ensure_ascii=False) + "\n"
    new_text = state_io.canon(new_text.replace("\r\n", "\n"))
    new_bytes = new_text.encode("utf-8")
    folder = os.path.dirname(os.path.abspath(STATE))
    handle, temp = tempfile.mkstemp(dir=folder, prefix=".state_R2332_")
    with os.fdopen(handle, "wb") as sink:
        sink.write(new_bytes)
        sink.flush()
        os.fsync(sink.fileno())
    os.replace(temp, STATE)
    post = state_io.read_raw(STATE)
    if post != new_bytes:
        raise SystemExit("E_R2332_READBACK post=%d predicted=%d" % (len(post), len(new_bytes)))
    print("STATE before=%dB after=%dB post=%dB predicted-equal" % (before, len(new_bytes), len(post)))
    print("LAYOUT", json.dumps(state_io.layout(state_io.decode(post))["layout_ok"]))
    closeout = ledger_lines.check_closeout(state_io.parse(state_io.decode(post))["log"], round_no=2332)
    print("CLOSEOUT", json.dumps({k: closeout[k] for k in list(closeout)[:6]}))

    export = json.load(io.open(EXPORT, "r", encoding="utf-8"))
    ts = "2026-11-01T16:40:00+08:00"
    export["export_ts"] = ts
    face = export["ceo_face"]
    face["last_artifact"] = face.get("latest_artifact")
    face["latest_artifact"] = (
        "qa/reconcile-all-R2332.log（R2332 全量校准电池，473/473 套件 + 控制 7/7，"
        "判据 3814 与预登记逐位一致）· 2026-11-01"
    )
    face["current"] = (
        "R2332 验证窗：在已提交树 5574820a 上跑全量校准电池（零产品改动），"
        "473/473 套件全绿 + 控制 7/7，907.8s，判据总数 3814——与预登记的 473/3814 "
        "完全一致（相对 R2330 的 472/3808 恰为 +1 套件 / +6 判据，来源=R2331 交付的 "
        "os-retire-candidate 套件）。四段跟进按设计顺序：矩阵段先在过期文档上 FAIL "
        "且不改写，再由 suite_matrix 重生成 473/3814（45349B），复跑四段全 PASS"
        "（矩阵逐字节同一 / 指纹五域 CLEAN / runner profile --daily --check 逐字节同一 / "
        "census DRIFT-CLEAN），VERDICT R2332 PASS。残留判定复读 TRIAGED（195 条，"
        "until=R2350）。本轮 0 产品分：只买回验证确定性。"
    )
    face["next_milestone"] = (
        "R2333 回到产品面：认领 tech 队头（state/queue/tech.md:384 前缀 AC-RAC1，"
        "retire_accept——本轮实测仍有 6 份 RETIRE-READY 副本落在盘上），先零占用锚检再落码，"
        "提交后才跑电池（R2168 混合树铁律）。"
    )
    face["next_milestone_due"] = "2026-11-03T16:40:00+08:00"

    row = (
        "R2332 verification window: RUNNER PASS 473/473 suites + controls 7/7 in "
        "907.8s, TMP RECLAIM 932/932, criteria total 3814 exactly as pre-registered "
        "(+1 suite / +6 criteria against R2330 472/3808 from the R2331 "
        "os-retire-candidate suite); four follow-up sections PASS after the designed "
        "matrix FAIL and its regeneration to 473/3814 (45349B); residue TRIAGED; zero "
        "product code, 0 product points."
    )
    export["outs"] = [[("qa/reconcile-all-R2332.log"), "on", row]] + export["outs"]
    export["results"] = [["R2332", row]] + export["results"]

    log_lines = state["log"]
    export["self_drive"]["log_lines_in_window"] = len(
        [l for l in log_lines if isinstance(l, str) and l.startswith("R2332") or "R2332" in l[:40]]
    )
    payload = json.dumps(export, indent=2, ensure_ascii=False) + "\n"
    with io.open(EXPORT, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
    print("EXPORT bytes=%d" % len(payload.encode("utf-8")))

    hb = io.open(HEARTBEAT, "r", encoding="utf-8").read()
    io.open(HEARTBEAT, "w", encoding="utf-8", newline="\n").write(
        hb.rstrip("\n") + "\n2026-11-01T16:40:00+08:00 tick=2332 round=R2332 verification-window-battery-pass\n"
    )
    print("HEARTBEAT tail ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())