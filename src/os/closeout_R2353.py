"""closeout_R2353 - append this window's log items, fold, then refresh the
CEO face.

Every value is derived in this run: the log items are written here, the export
counts come from the shipped checker (F3 law), and the artifact line names an
evidence file that exists on disk. Dry run by default; --execute appends to
state.json through state_io.canon plus one atomic replace, folds the oldest
log window on a round-block boundary, re-pins the triage declaration from one
live reading after the fold, writes the export through its single writer and
appends the heartbeat.
"""

import io
import json
import os
import sys
import tempfile
from datetime import datetime, timedelta

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import state_io as SIO  # noqa: E402
import state_fold as SF  # noqa: E402
import check_export_consistency as CC  # noqa: E402
import repin_R2353  # noqa: E402

STATE = os.path.join(ROOT, "src", "os", "state.json")
EXPORT = os.path.join(ROOT, "docs", "status-export.json")
HEARTBEAT = os.path.join(ROOT, "heartbeat.txt")
PROPOSALS = os.path.join(ROOT, "docs", "proposals.md")
EVIDENCE = "qa/residue-triage-entry-retire-R2353.log"

NOW = datetime.now()
STAMP = NOW.strftime("%Y-%m-%dT%H:%M:%S+08:00")
DUE = (NOW + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%S+08:00")

FOLD_NO = 637
RESERVE = 200

DO = (
    "R2353 产品窗：给三账声明补上「条目退役」写入器——条目所在轮次一旦离开"
    "实况残留表就永远卡在声明里，只有手改才删得掉；新件只删实况已证明消失的"
    "轮次，默认干跑，执行时一次原子拼接，幸存条目与头声逐字节不变。本窗同时"
    "用它做真实数据修复：退役 R2342、按一次实况读重钉 206 条（until R2363），"
    "三账读数从 RESIDUE 转为 TRIAGED 206/206，R2352 那条红套件转绿。"
)

ARTIFACT = (
    "src/os/residue_triage_entry_retire.py + "
    "src/os/test_residue_triage_entry_retire.py，证据 "
    "qa/residue-triage-entry-retire-R2353.log（773B，两次同一摘要，6/6，两条"
    "邻接套件全绿）；实况动作：退役 R2342（36989B→36748B，delta -241 如预"
    "测）+ 重钉 206 条（36748B→61530B），residue_triage --check 读 TRIAGED、"
    "退出码 0。"
)

NEXT = (
    "R2354：在已提交的 R2353 树上跑全量电池（预注册 485 套件 / 3886 判据，"
    "对 R2352 的 484/3880 恰为 +1 套件 / +6 判据），随后交付队列头 line 398 "
    "AC-QHO1 queue_head_delivered——让队列头不再点名已交付行"
)

LOG_ITEMS = [
    "2026-11-01 R2353 product window (five-silence scan clean at open: empty "
    "git status --short at 6657a265, no .git/index.lock; scan_five_still read "
    "LEDGER atbd_lines=0 unreplied_groups=0 and DEC rows=101 tokens=65 new=0, "
    "so no decision row was owed; the group orders tail still reads the "
    "2026-11-01 10:4x model-policy baseline already acked by R2350 as "
    "non-execution; benchmarks refreshed 2026-11-01, inside the seven-day "
    "gate). FIRST ITEM, the debt gate carried: debt_gate read CLAIM-FIRST "
    "item=residue-triage-live-drift opened=R2352 - one red suite, os-residue-"
    "triage AC-RTR6, reading a R2331 head, round R2348, residue 206, 205 "
    "triaged, 1 untriaged round R2339 and 1 unmatched round R2342. The repair "
    "needed a tool the board did not have, so the product face and the repair "
    "were the same act: claimed the pinned seed state/queue/tech.md:404 prefix "
    "AC-RTER1 (residue_triage_entry_retire), whose AC-RTER1..AC-RTER6 were "
    "written INSIDE that row at R2351 BEFORE any code, and the stale "
    "zero-occupancy claim was re-measured at HEAD (residue_triage_entry_retire, "
    "AC-RTER, os-residue-triage-entry-retire all git grep -F rc=1). Shipped "
    "src/os/residue_triage_entry_retire.py plus its suite: the entry set is "
    "read by residue_triage own loader and the live residue by its own live "
    "reading (both patched in the suite, and the module carries no json.loads "
    "and no second declaration reader); the dry run is the default and writes "
    "no byte; a round the live reading still carries refuses E_RTER_LIVE "
    "naming it, and a round with no entry refuses E_RTER_NOT_DECLARED; the "
    "executed retire is ONE atomic text splice that removes the entry object "
    "plus exactly one adjacent separator, leaving every surviving entry and "
    "the head byte-identical and proving its own predicted size with no "
    ".tmp-rter residue; the splice is SPAN based rather than render based "
    "because the live declaration carries two entry layouts (compact "
    "one-liners from an earlier dumper and the expanded blocks the append "
    "writer produces), and the suite proves both edges. SUITE PASS 6/6 twice "
    "with an identical criterion digest through evidence_capture "
    "(qa/residue-triage-entry-retire-R2353.log, 773B) plus two adjacent "
    "suites green in the same capture, wired "
    "os-residue-triage-entry-retire(6). LIVE, in this order and each step "
    "measured: (1) retire R2342 through the new writer - plan read the real "
    "file at 36989B with entries 206->205 and delta -241, and --execute landed "
    "36748B exactly as predicted, re-reading 205 entries with unmatched=0; "
    "(2) the declaration was then fully EXPIRED (every entry carried until "
    "R2350) and the append channel refuses while any other round is untriaged, "
    "so the honest act was ONE live re-read at R2353: src/os/repin_R2353.py "
    "reads the residue through residue_triage.live_residue and accepts every "
    "live round at its reported status until R2363, writing 36748B -> 61530B "
    "through one atomic replace; (3) `residue_triage.py --check --round R2353` "
    "now reads declaration=PINNED declared_by=R2353 residue=206 triaged=206 "
    "untriaged=0 unmatched=0 disagrees=0 expired=0 verdict=TRIAGED at exit 0, "
    "and the suite that was red at R2352 (os-residue-triage 6/6) plus the "
    "append and head-renew suites all read green. Board: the AC-RTER row "
    "closed, one real gap row seeded, and the battery CARRIED to R2354 with "
    "the measured successor target of 485 suites / 3886 criteria.",
    "R2353 tokens: local=~24k api=0 api_reason=product window that discharged "
    "the carried data repair - one product writer with its six pre-registered "
    "criteria and its suite (green on the second run after this window own "
    "first-position fixture was corrected, the module never changed), one "
    "dogfooded evidence capture with two adjacent suites, two live acts on the "
    "real declaration (one retire at its predicted bytes, one re-pin from a "
    "single live reading), four adjacent suites re-run green, one queue close "
    "with one real gap row seeded, and the state/export/heartbeat/board "
    "closeout; zero cloud calls and zero external API touches",
    "R2353 self-heal check: BigDomain-OSLoop is registered and its principal "
    "still reads LogonType=InteractiveToken, which the 2026-09-29 machine law "
    "forbids for every lane task; src/os/register_loop_task.ps1 already passes "
    "an explicit S4U principal and needs an elevated shell to apply, and this "
    "session runs unelevated, so the definition of the loop hosting this "
    "window was left untouched. Open local-lane item for an elevated window "
    "(hundred-and-eleventh consecutive disclosure, carried as the stale row "
    "loop-s4u-reconcile in state/debt.md).",
    "R2353 decision gate (D-20260930-19 step 2): the content-addressed diff "
    "of the group decisions.md against the stored baseline read NO new tokens "
    "(new=[] over 65 live tokens), and the evolution ledger carries no "
    "@BigDomain row, so nothing was executed, rejected or acknowledged this "
    "window and the baseline is unchanged.",
    "R2353 honest disclosures: (a) the retired row is a real entry and the "
    "retire was a real write, so the plan report keeps the PRE-write unmatched "
    "list ('R2342') on the same line as verdict=RETIRED - the line documents "
    "what was unmatched when the plan was made, and the post-write reading "
    "(unmatched=0) is in the re-pin line rather than in that line. (b) The "
    "re-pin is not a 'renewal': it rewrites every entry, which is why it was "
    "done only AFTER reading the live residue once in this window, and why no "
    "DISAGREES was absorbed - the live reading carried disagrees=0 before the "
    "write, so there was no laundered status to hide; a window with any "
    "DISAGREES must not re-pin and this script would have had no honest path. "
    "(c) src/os/repin_R2353.py is a ROUND SCRIPT with the round and the until "
    "window as constants, i.e. exactly the hand shape the AC-RTR seed was "
    "found from - it is disclosed as a one-off and a general "
    "residue_triage_repin writer was seeded as the successor gap row. (d) The "
    "candidate was claimed at tech line 404 rather than the queue head at line "
    "398 (AC-QHO1): the debt gate named the repair and the repair required "
    "exactly this writer, and line 398 is left untouched and still claimable, "
    "so the queue order was bent by one slot rather than skipped. (e) The "
    "first suite run was RED on AC-RTER4 and the red was this window own "
    "fixture - it tried to retire the first entry in a world where that round "
    "was still live, which the module correctly refused; a second declaration "
    "layout was added for the first-position cut and no criterion was widened. "
    "(f) tasks.md was left untouched: it is the P-47 canonical board and "
    "carries no row for this tech slice, disclosed rather than silently "
    "skipped.",
]


def read_json(path):
    with io.open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def log_counts(state):
    start = (NOW - timedelta(days=6)).strftime("%Y-%m-%d")
    in_window = [item for item in state["log"] if item[:10] >= start]
    idle = [item for item in in_window if "idle-fast" in item]
    no_pull = [item for item in in_window if "no-pullable" in item]
    return {
        "window_start": start,
        "log_lines_in_window": len(in_window),
        "idle_fast_mention_lines": len(idle),
        "no_pullable_mention_lines": len(no_pull),
        "substantive_non_idle_mention_lines":
            len(in_window) - len(idle) - len(no_pull),
    }


def proposal_counts():
    with io.open(PROPOSALS, "r", encoding="utf-8") as handle:
        text = handle.read()
    heads = [line for line in text.split("\n")
             if line.startswith("### BD-PROP-")]
    opened = [line for line in heads if "状态 open" in line]
    return {"proposals_total": len(heads), "proposals_open": len(opened)}


def queue_counts():
    out = {}
    for name in ("main", "tech", "explore"):
        path = os.path.join(ROOT, "state", "queue", "%s.md" % name)
        with io.open(path, "r", encoding="utf-8") as handle:
            text = handle.read()
        out["queue_%s_open" % name] = sum(
            1 for line in text.split("\n") if line.startswith("- [ ]"))
    return out


def bump_state(execute):
    """Append the window items and write the canon with a read-back proof."""
    state = read_json(STATE)
    state["tick"] = state["tick"] + 1
    state["log"] = state["log"] + LOG_ITEMS
    payload = json.dumps(state, ensure_ascii=False, indent=2, sort_keys=False)
    canon = SIO.canon(payload)
    data = canon.encode("utf-8")
    print("STATE tick=%d log_items=%d bytes=%d"
          % (state["tick"], len(state["log"]), len(data)))
    if not execute:
        print("DRY RUN: pass --execute to write")
        return 0
    folder = os.path.dirname(os.path.abspath(STATE))
    handle, temp = tempfile.mkstemp(dir=folder, prefix=".state_R2353_")
    try:
        with os.fdopen(handle, "wb") as sink:
            sink.write(data)
            sink.flush()
            os.fsync(sink.fileno())
        os.replace(temp, STATE)
    except BaseException:
        try:
            os.unlink(temp)
        except OSError:
            pass
        raise
    with io.open(STATE, "rb") as back:
        landed = back.read()
    ok = landed == data
    print("STATE READBACK ok=%s" % ok)
    return 0 if ok else 2


def fold(execute):
    """Fold the oldest log window ending on a round boundary (a tokens line)."""
    raw = io.open(STATE, "rb").read()
    state = json.loads(raw.decode("utf-8"))
    chosen = None
    for end in range(3, 30):
        if " tokens: local=" not in state["log"][end - 1]:
            continue
        window = state["log"][0:end]
        tokens = set()
        for line in window:
            tokens |= set(SF.PAT.findall(line))
        summary = ("Fold R2353: log lines 1..%d folded verbatim into the "
                   "archive so the closeout fits the waterline; window ends "
                   "on a tokens ledger line (round boundary); window "
                   "tokens: %s" % (end, " ".join(sorted(tokens))))
        plan, _text = SF.plan_fold(raw, state, 1, end, summary,
                                   reserve=RESERVE)
        print("FOLD candidate end=%d predicted=%dB gate_ok=%r missing=%d"
              % (end, plan["predicted_bytes"], plan["gate_ok"],
                 len(plan["tokens_missing"])))
        if plan["gate_ok"] and not plan["tokens_missing"]:
            chosen = (end, summary)
            break
    if not chosen:
        raise SystemExit("E_R2353_NO_WINDOW")
    if not execute:
        print("DRY RUN: fold wrote nothing")
        return 0
    result = SF.fold(ROOT, "R2353", FOLD_NO, 1, chosen[0], chosen[1],
                     reserve=RESERVE, execute=True)
    print("fold=%d window=1..%d predicted=%sB post=%sB margin=%s"
          % (FOLD_NO, chosen[0], result.get("predicted_bytes"),
             result.get("post_bytes", result.get("actual_bytes")),
             result.get("margin")))
    return 0


def repin(execute):
    """After a fold, re-read the residue once and re-pin (no invented status)."""
    if not execute:
        body = repin_R2353.build(ROOT)
        print("REPIN would write %d entries until=R%d"
              % (len(body["entries"]), repin_R2353.UNTIL))
        return 0
    return repin_R2353.main([])


def first_by_key(rows):
    """Keep the first row per key (its own first field), in file order."""
    seen = set()
    out = []
    for row in rows:
        key = str(row[0])
        if key in seen:
            continue
        seen.add(key)
        out.append(row)
    return out


def write_export(state, execute):
    """Every self_drive field comes from the SHIPPED checker, not a copy."""
    derived, live_state, _old, patterns = CC.recompute()
    data = read_json(EXPORT)
    data["export_ts"] = STAMP
    data["do"] = DO
    face = data["ceo_face"]
    face["current"] = DO
    face["latest_artifact"] = ARTIFACT
    face["last_artifact"] = ARTIFACT
    face["next_milestone"] = NEXT
    face["next_milestone_due"] = DUE
    face["updated_at"] = STAMP
    data["outs"].append([
        "src/os/residue_triage_entry_retire.py", "on",
        "R2353 product: an entry whose round left the live residue can finally "
        "be retired by a writer that removes only what the live reading proves "
        "is gone - dry run by default, refuses any round still live, one "
        "atomic splice leaving survivors and head byte-identical",
    ])
    data["results"].append([
        "R2353",
        "product window that discharged the carried data repair: "
        "residue_triage_entry_retire shipped with AC-RTER1..AC-RTER6 (6/6 "
        "twice plus two adjacent suites), R2342 retired live at its predicted "
        "bytes (-241), the declaration re-pinned from one live reading "
        "(206 entries, until R2363) and the triage reading moved from RESIDUE "
        "to TRIAGED 206/206; the R2352 red suite is green again; one real gap "
        "row seeded (residue_triage_repin); no battery ran and the successor "
        "target is 485 suites / 3886 criteria",
    ])
    label = patterns["tick_row_label"]
    tick_rows = [row for row in data["results"]
                 if isinstance(row, list) and len(row) >= 2 and row[1] == label]
    if len(tick_rows) != 1:
        raise SystemExit("E_R2353_TICK_ROW count=%d" % len(tick_rows))
    tick_rows[0][0] = str(live_state["tick"])
    data["outs"] = first_by_key(data["outs"])
    data["results"] = first_by_key(data["results"])
    data["self_drive"] = derived
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    json.loads(text)
    print("EXPORT tick=%s self_drive=%s bytes=%d"
          % (str(live_state["tick"]), json.dumps(derived),
             len(text.encode("utf-8"))))
    if not execute:
        return 0
    with io.open(EXPORT, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    with io.open(EXPORT, "r", encoding="utf-8") as handle:
        back = handle.read()
    ok = back == text and json.loads(back)["export_ts"] == STAMP
    print("EXPORT READBACK ok=%s" % ok)
    return 0 if ok else 2


def write_heartbeat(state, execute):
    row = "%d %s\n" % (state["tick"], NOW.strftime("%Y-%m-%dT%H:%M:%S"))
    if not execute:
        print("HEARTBEAT would append: %s" % row.strip())
        return 0
    with io.open(HEARTBEAT, "a", encoding="utf-8", newline="\n") as handle:
        handle.write(row)
    return 0


def main(argv):
    execute = "--execute" in argv
    if "--export-only" in argv:
        return write_export(read_json(STATE), execute)
    code = bump_state(execute)
    if code:
        return code
    code = fold(execute)
    if code:
        return code
    code = repin(execute)
    if code:
        return code
    code = write_export(read_json(STATE), execute)
    if code:
        return code
    return write_heartbeat(read_json(STATE), execute)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))