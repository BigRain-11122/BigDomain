"""closeout_R2327.py - tick, log items, export refresh (R2327 product window).

This window shipped a product face, so there is no fold: nothing moved out of
the log and no new residue is created. Log items are appended through one
writer and the file is re-read before it is trusted. The CEO-visible export is
refreshed from the shipped consistency checker (F3: derived fields are never
written by hand), and one heartbeat row is appended.

Dry run by default; --execute writes. Pure ASCII, stdlib only, no network.
"""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import state_io  # noqa: E402

STATE = os.path.join(ROOT, "src", "os", "state.json")
GATE = 78500

NARRATIVE = (
    "2026-11-01 R2327 product window (five-silence scan clean at open: empty "
    "git status --short, no .git/index.lock, no @BigDomain ledger row at all, "
    "no new decision token - the content-addressed diff of decisions.md "
    "against the baseline read new=[] - orders tail unchanged, benchmarks "
    "refreshed 2026-11-01). CLAIMED the tech head AC-RWW1, the R2305 "
    "review_window_wire seed whose AC-RWW1..AC-RWW6 were pinned inside that "
    "row BEFORE the code, after a fresh zero-occupancy anchor check at HEAD "
    "2026-11-01 (the five anchors hit only prose, no code path). "
    "DELIVERED src/os/review_window_wire.py plus src/os/test_review_window_wire.py, "
    "one runner entry os-review-window-wire(6), and --window-from-declaration on "
    "exempt_review: the window is read off review_window_decl.resolve own report "
    "and never re-derived (a patched resolver flows straight through); the "
    "resolver codes are carried through the E_RWD_ -> E_RWW_ prefix rather than "
    "collapsed, so UNPINNED, DRIFT, REFUSED, DECL_FUTURE and UNREADABLE each "
    "refuse at exit 2 with zero counts and a WINDOW-REFUSED line instead of the "
    "CLI default of 100; an explicit --window together with the flag is refused "
    "E_RWW_BOTH at exit 5 rather than resolved by precedence; the same pinned "
    "window leaves the entries and stale rows byte-identical between the literal "
    "and declared readings with window_source the only difference; --json stays "
    "byte-stable over the nine report keys and the reading writes nothing; the "
    "age law itself is untouched, and window_source was appended to REPORT_KEYS "
    "and one_line, which the AC-EXR suite asserts against the constant, so it "
    "re-read 6/6 unchanged. SUITE "
    "PASS 6/6 twice with an identical criterion digest 139BF1A0AB53642E through "
    "evidence_capture, adjacent os-exempt-review 6/6 and os-review-window 6/6 "
    "green in the same capture, qa/review-window-wire-R2327.log 2345B as one "
    "utf-8 LF single writer. LIVE: EXEMPT REVIEW round=R2327 window=100 "
    "declaration=PINNED entries=9 stale=0 verdict=REVIEW-CLEAN "
    "source=declaration.") 

LEDGER = (
    "tokens: local=1 api=0 api_reason=none - code, suite and queue work done in "
    "this session and no cloud call was needed.")

SELF_HEAL = (
    "R2327 self-heal check: BigDomain-OSLoop is registered and its principal "
    "still reads LogonType=InteractiveToken, which the 2026-09-29 machine law "
    "forbids for lane tasks; register_loop_task.ps1 passes an explicit S4U "
    "principal but needs an elevated shell, which this session is not, so the "
    "definition was left untouched (eighty-ninth consecutive disclosure, "
    "carried as loop-s4u-reconcile in state/debt.md).")

DECISIONS = (
    "R2327 decision gate (D-20260930-19 step 2): the content-addressed diff of "
    "the group decisions.md against the baseline read NO new tokens (new=[]), "
    "and the evolution ledger carries no @BigDomain row at all, so nothing was "
    "executed, rejected or acknowledged this window and the baseline is "
    "unchanged.")

DISCLOSURES = (
    "R2327 honest disclosures: (a) first suite run red 3/6 and all "
    "three reds were THIS window own fixture/message defects - two fixtures "
    "miscounted their own stale entries and one refusal line printed only the "
    "code - so one fixture and one message were corrected; no criterion was "
    "widened and the module was never changed to turn a red green. (b) The "
    "claim kept tech claimable at 10 only because one REAL gap row was seeded "
    "in the same window: a declarations list that rewinds in time (R2400 row "
    "then R2300 row) was measured this window resolving AGREES, so "
    "review_window_history is the new tech head with AC-RWH1..AC-RWH6 "
    "pre-registered and five anchors zero-occupancy. (c) tasks.md is "
    "untouched: the P-47 board carries no row for this tech slice. "
    "(d) No battery ran: the R2168 mixed-tree rule puts it on the "
    "committed tree in the successor row, pre-registered at 471 suites / 3802 "
    "criteria (+1/+6 against the R2326 measurement of 470/3796).")


def build(raw):
    state = json.loads(raw.decode("utf-8"))
    before = len(state["log"])
    state["tick"] = 2327
    state["log"].extend([NARRATIVE, LEDGER, SELF_HEAL, DECISIONS, DISCLOSURES])
    ascii_only = all(byte < 0x80 for byte in raw)
    body = json.dumps(state, ensure_ascii=ascii_only, indent=2)
    return before, state_io.canon(body).encode("utf-8")


def write(path, data, label):
    temp = os.path.join(os.path.dirname(path), ".%s.tmp" % label)
    with open(temp, "wb") as sink:
        sink.write(data)
        sink.flush()
        os.fsync(sink.fileno())
    os.replace(temp, path)
    if open(path, "rb").read() != data:
        raise SystemExit("E_READBACK %s" % label)
    if os.path.exists(temp):
        raise SystemExit("E_RESIDUE %s" % label)


def refresh_export():
    import check_export_consistency as CEC
    import datetime
    export = os.path.join(ROOT, "docs", "status-export.json")
    heartbeat = os.path.join(ROOT, "heartbeat.txt")
    data = json.load(io.open(export, encoding="utf-8"))
    derived, state, _exp, pat = CEC.recompute()
    now = datetime.datetime.now().astimezone().replace(microsecond=0)
    before = len(json.dumps(data, ensure_ascii=False).encode("utf-8"))
    data["export_ts"] = now.isoformat()
    data["do"] = ("R2327 产品窗：把 review_window_decl 已钉住的复核窗口真正接到 "
                  "exempt_review 上，让窗口来源只有声明一处，别再各算各的。")
    face = data.get("ceo_face") or {}
    face["current"] = ("R2327 产品窗交付：exempt_review 新增 --window-from-declaration，"
                       "窗口经 review_window_wire 从 review_window_decl.resolve 读取；"
                       "UNPINNED/DRIFT/被拒声明在老化任何条目之前即以自有错误码退出 2 且"
                       "计数为零，显式 --window 与该旗标并用按两处真相拒绝；同一钉住窗口下"
                       "FRESH/STALE 行逐字节一致。判据 AC-RWW1..RWW6 SUITE PASS 6/6（双跑"
                       "同一判据摘要），相邻两套件 6/6 全绿。")
    face["latest_artifact"] = ("qa/review-window-wire-R2327.log（2026-11-01·2345B·"
                               "SUITE PASS 6/6 双跑·相邻 6/6+6/6）+ "
                               "src/os/review_window_wire.py")
    face["last_artifact"] = "qa/review-window-wire-R2327.log"
    face["next_milestone"] = ("R2328 验证窗：在已提交的 R2327 树上跑全量对账电池，"
                              "预注册 471 套件 / 3802 判据（即本窗 +1 套件/+6 判据，"
                              "任一差值须命名）；窗 ≤48h")
    face["next_milestone_due"] = (now + datetime.timedelta(hours=48)).isoformat()
    data["ceo_face"] = face
    drive = data.get("self_drive") or {}
    for key in ("window", "window_days", "log_lines_in_window",
                "idle_fast_mention_lines", "no_pullable_mention_lines",
                "substantive_non_idle_mention_lines", "proposals_total",
                "proposals_open", "queue_main_open", "queue_tech_open",
                "queue_explore_open"):
        if key in derived:
            drive[key] = derived[key]
    data["self_drive"] = drive
    entry = ("R2327 product window: exempt_review now takes its review window "
             "from the pinned declaration through review_window_wire instead "
             "of a per-call default, refusing UNPINNED/DRIFT/refused "
             "declarations at exit 2 with zero counts, refusing an explicit "
             "--window together with the new flag as two sources of truth, and "
             "leaving the FRESH/STALE rows byte-identical for the same pinned "
             "window; AC-RWW1..AC-RWW6 SUITE PASS 6/6 twice.")
    out_key = "qa/review-window-wire-R2327.log"
    outs = data.get("outs") or []
    if not any(row and row[0] == out_key for row in outs):
        outs.insert(0, [out_key, "on", entry])
    data["outs"] = outs
    results = data.get("results") or []
    label = pat["tick_row_label"]
    for row in results:
        if isinstance(row, list) and len(row) >= 2 and row[1] == label:
            row[0] = str(state.get("tick"))
    if not any(row and row[0] == "R2327" for row in results):
        results.insert(0, ["R2327", entry])
    data["results"] = results
    body = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    write(export, body.encode("utf-8"), "export_R2327")
    after = len(body.encode("utf-8"))
    print("EXPORT before=%dB after=%dB export_ts=%s"
          % (before, after, data["export_ts"]))
    row = ("tick 2327 2026-11-01 R2327 product window: exempt_review gained "
           "--window-from-declaration reading the window through "
           "review_window_wire from review_window_decl.resolve (never "
           "re-derived), refusing UNPINNED/DRIFT/refused declarations at exit "
           "2 with zero counts and a named E_RWW_* code instead of the CLI "
           "default 100, refusing --window with the flag as two sources of "
           "truth, and keeping the FRESH/STALE rows byte-identical for the "
           "same pinned window; AC-RWW1..AC-RWW6 SUITE PASS 6/6 twice with "
           "adjacent suites green; tech queue closed row 381 and seeded the "
           "real rewind gap review_window_history (AC-RWH1..AC-RWH6); gauge "
           "FLOOR-MET main 5/5 tech 10/10 explore 10/10.")
    beat = io.open(heartbeat, encoding="utf-8").read()
    if "tick 2327 " not in beat:
        if not beat.endswith("\n"):
            beat += "\n"
        write(heartbeat, (beat + row + "\n").encode("utf-8"), "heartbeat_R2327")
        print("HEARTBEAT appended tick 2327")


def main(argv):
    execute = "--execute" in argv
    raw = open(STATE, "rb").read()
    before_items, new = build(raw)
    print("LOG_ITEMS %d -> %d TICK 2327 BEFORE %dB AFTER %dB DELTA %+d "
          "GATE %d MARGIN %d"
          % (before_items, before_items + 5, len(raw), len(new),
             len(new) - len(raw), GATE, GATE - len(new)))
    if len(new) > GATE:
        raise SystemExit("E_C2327_OVER_GATE %d" % len(new))
    if not execute:
        print("DRY RUN - nothing written")
        return 0
    write(STATE, new, "state_close_R2327")
    parsed = json.loads(open(STATE, "rb").read().decode("utf-8"))
    if parsed["tick"] != 2327 or len(parsed["log"]) != before_items + 5:
        raise SystemExit("E_C2327_PARSE")
    print("WROTE %dB readback ok temp clean tick=%d log=%d"
          % (len(new), parsed["tick"], len(parsed["log"])))
    refresh_export()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))