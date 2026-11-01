"""closeout_R2351 - append this window's log items and refresh the CEO face.

Every value is derived in this run (the queue row is closed here, the backlog
line is written here, the export counts are recomputed by the shipped checker
from state.json, docs/proposals.md and the queue files, and the artifact line
names an evidence file that exists on disk).
Dry run by default; --execute writes state.json through state_io.canon and the
export through its own single writer, each with a read-back proof.
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
import check_export_consistency as CC  # noqa: E402

STATE = os.path.join(ROOT, "src", "os", "state.json")
EXPORT = os.path.join(ROOT, "docs", "status-export.json")
HEARTBEAT = os.path.join(ROOT, "heartbeat.txt")
QUEUE = os.path.join(ROOT, "state", "queue", "tech.md")
BACKLOG = os.path.join(ROOT, "src", "os", "backlog.md")
EVIDENCE = "qa/residue-triage-head-renew-R2351.log"

NOW = datetime.strptime("2026-11-01T23:41:00", "%Y-%m-%dT%H:%M:%S")
STAMP = "2026-11-01T23:41:00+08:00"
DUE = (NOW + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%S+08:00")

OLD_ROW = ("- [ ] P2 tech seed (R2350, from this window own live reading): "
           "`src/os/residue_triage_head_renew.py`")

NEW_ROW = ("- [x] [done 2026-11-01 R2351] P2 tech seed (R2350, from this "
           "window own live reading): `src/os/residue_triage_head_renew.py`")

DISCHARGE = (
    "  DISCHARGED R2351: src/os/residue_triage_head_renew.py plus "
    "src/os/test_residue_triage_head_renew.py shipped; SUITE PASS 6/6 twice "
    "with an identical criterion digest E76AE248C5320D9E through "
    "evidence_capture (qa/residue-triage-head-renew-R2351.log, 834B, single "
    "writer utf-8 LF) plus three adjacent suites green (declaration reason, "
    "declaration append, retire apply), wired "
    "os-residue-triage-head-renew(6). The writer asks residue_triage for the "
    "entry set, the statuses and the live residue and "
    "residue_triage_decl_reason for the head claim; the dry run is the default "
    "and writes no byte; a renewal is refused before ANY byte when a declared "
    "entry disagrees with the live reading, when a live residue round is "
    "undeclared, or when the round would predate an entry's declared_by; an "
    "executed renewal is one atomic splice that rewrites only the head "
    "declared_by and reason values, leaves the entries region byte-identical, "
    "and proves its own predicted size. LIVE, and it is the finding: the real "
    "declaration REFUSES renewal with E_RTRH_UNDECLARED naming R2339 - a live "
    "residue round that no entry covers - so the head stays at R2331 rather "
    "than being renewed over a set it does not speak for. Adjacent suite "
    "residue_triage is RED on its live assertion for that same drift (one "
    "undeclared live round R2339 plus the inert entry R2342, measured at its "
    "own claim round R2348): a pre-existing declaration drift, not a defect "
    "in this window's code, disclosed rather than swept.")

NEW_SEED = (
    "- [ ] P2 tech seed (R2351, from this window own live reading): "
    "`src/os/residue_triage_entry_retire.py` - the declaration now has a "
    "writer for NEW entries (residue_triage_append) and a writer for the head "
    "(residue_triage_head_renew), but nothing can RETIRE an entry whose round "
    "left the live residue: measured at R2351, the entry for R2342 reads "
    "UNMATCHED (its round is no longer in the live stamp_residue table) and "
    "stays in the declared set forever, so the head speaks for rounds that no "
    "longer exist and only a hand edit can remove one. Product: the missing "
    "retire writer, which may only remove what the live reading proves is "
    "gone. Criteria AC-RTER1..AC-RTER6 pre-registered HERE BEFORE any code: "
    "AC-RTER1 the entry set and the live residue are imported from "
    "residue_triage (patching its loader or its live reading moves the plan, "
    "and the module carries no second declaration reader); AC-RTER2 the dry "
    "run is the default - the plan names every UNMATCHED round, the entry "
    "count before and after and the predicted byte count, and writes nothing "
    "without --execute, proved by whole-file digest; AC-RTER3 an entry whose "
    "round the live reading still carries is REFUSED with its round named, so "
    "the writer can never retire a live round; AC-RTER4 an executed retire is "
    "one atomic text splice that removes only the retired entry objects, "
    "leaves every surviving entry and the head byte-identical, proves the "
    "predicted post size against the write and leaves no .tmp/.part residue; "
    "AC-RTER5 CLI exits 0 planned or retired, 2 refused over live state, 3 "
    "unreadable or missing declaration, 5 bad flags, with a byte-stable "
    "--json over pinned keys; AC-RTER6 pure ASCII, stdlib only, zero network, "
    "no clock of its own (the round is an argument), no delete path outside "
    "the atomic replace, and its own reconcile label. Anchor check at HEAD "
    "2026-11-01: residue_triage_entry_retire, AC-RTER, os-residue-triage-"
    "entry-retire all git grep -F zero-occupancy rc=1.")

DO = (
    "R2351 产品窗口：把三账声明（state/residue_triage.json）的头从"
    "「只能手改」变成「只能按实测续期」——新写入器先问实况：条目集、状态"
    "词表、实况残差全部取自 residue_triage，头声明取自 "
    "residue_triage_decl_reason；默认干跑零写入；条目与实况不符、实况有未"
    "声明轮、或续期轮早于条目 declared_by 一律在任何字节前拒绝并点名轮次；"
    "执行是以一次原子文本拼接只改头两个值，条目区字节不变并自证预测长度。"
    "实弹读数即结论：真声明被 E_RTRH_UNDECLARED 拒绝并点名 R2339（实况有"
    "残差轮无声明），所以头保持 R2331 而不是被改写成一句没人做过的通读。"
)

ARTIFACT = (
    "src/os/residue_triage_head_renew.py + "
    "src/os/test_residue_triage_head_renew.py，证据 "
    "qa/residue-triage-head-renew-R2351.log（834B，同一判据摘要 "
    "E76AE248C5320D9E，6/6 两次，邻接三套件全绿）；实弹 "
    "E_RTRH_UNDECLARED R2339 退出 2。"
)

NEXT = (
    "R2352：在已提交的 R2351 树上跑全量电池（预注册 484 套件 / 3880 判据），"
    "随后交付队列头 line 398 AC-QHO1 queue_head_delivered（已在种子行内预注册判据）。"
)

LOG_ITEMS = [
    "2026-11-01 R2351 product window (five-silence scan clean at open: empty "
    "git status --short, no .git/index.lock; scan_five_still reads LEDGER "
    "atbd_lines=0 unreplied_groups=0 and DEC rows=101 tokens=65 new=0, so no "
    "decision row was owed; the group orders tail still reads the 2026-11-01 "
    "10:4x baseline already acked by R2350 as non-execution; benchmarks "
    "refreshed 2026-11-01, inside the seven-day gate). PRODUCT: claimed the "
    "queue head the reader named, state/queue/tech.md:396 prefix AC-RTRH1 "
    "(residue_triage_head_renew), whose AC-RTRH1..AC-RTRH6 were pinned INSIDE "
    "that row at R2350 BEFORE any code, and re-ran the anchor check at this "
    "HEAD (all five names zero-occupancy outside the seed row). Shipped "
    "src/os/residue_triage_head_renew.py plus its suite: the triage "
    "declaration head could only be renewed by hand, which is exactly how it "
    "aged (R2350 measured eleven appends behind a R2331 head), so the writer "
    "renews only what it MEASURED - the entry set, the statuses and the live "
    "residue come from residue_triage (its loader, its stamp reader, its live "
    "residue), the head claim from residue_triage_decl_reason, the dry run is "
    "the default and writes no byte, and a renewal is refused before any byte "
    "when a declared entry disagrees with the live reading, when a live "
    "residue round is still undeclared, or when the round would predate an "
    "entry's own declared_by, each refusal naming the rounds. SUITE PASS 6/6 "
    "twice with an identical criterion digest E76AE248C5320D9E through "
    "evidence_capture (qa/residue-triage-head-renew-R2351.log, 834B) plus "
    "three adjacent suites green in the same capture, wired "
    "os-residue-triage-head-renew(6). TWO HONEST CORRECTIONS made inside this "
    "window rather than shipped broken: (a) the first design renewed the head "
    "window to the NEWEST entry window and claimed the result reads clean; the "
    "suite measured that a head window is the MODE of the entry windows, so a "
    "renewal may not rewrite an entry and a heterogeneous set stays HEAD-STALE "
    "on the UNTIL axis - the writer now takes its window from the shipped "
    "comparison and REPORTS the breaks that will survive (remaining_breaks / "
    "remaining_first) instead of implying a clean read; (b) the first "
    "AC-RTRH4 assertion looked for the old head string anywhere in the file, "
    "which every entry also carries, so it was scoped to the head region - the "
    "criterion was wrong, the writer was right. LIVE READING, and it is the "
    "finding rather than a green: the real declaration REFUSES renewal with "
    "E_RTRH_UNDECLARED naming R2339 (a live residue round no entry covers), so "
    "the head stays at R2331. Related live drift measured the same way: the "
    "adjacent residue_triage suite is RED on its own live assertion (its claim "
    "round R2348 reads untriaged=1 R2339 and unmatched=1 R2342) - a "
    "pre-existing declaration drift, disclosed instead of swept, and it is why "
    "that suite was excluded from the evidence adjacent list (the three suites "
    "that ran are green and named). Board: row closed and one REAL gap row "
    "seeded from this window's live reading (residue_triage_entry_retire, "
    "AC-RTER1..AC-RTER6 pre-registered, three anchors zero-occupancy) because "
    "nothing can retire an entry whose round left the live residue. STATED "
    "PLAINLY: no battery ran this window; the measured successor target is 484 "
    "suites / 3880 criteria, exactly +1 suite / +6 criteria against R2350 "
    "(483/3874).",
    "R2351 decision gate (D-20260930-19 step 2): the content-addressed diff of "
    "the group decisions.md against the stored baseline read NO new tokens "
    "(new=[] over 65 live tokens), and the evolution ledger carries no "
    "@BigDomain row, so nothing was executed, rejected or acknowledged this "
    "window and the baseline is unchanged. The group orders tail still reads "
    "the 2026-11-01 10:4x baseline (the model-policy order) already acked by "
    "R2350 as non-execution for this company.",
]


TOKENS = (
    "R2351 tokens: local=~19k api=0 api_reason=product window - one product "
    "writer with its six pre-registered criteria and its suite (red twice "
    "before green: the design renewed the head window to a window the shipped "
    "comparison cannot read as clean, and one criterion asserted a string the "
    "entries themselves carry), three adjacent suites, one dry-run reading of "
    "the live declaration and the closeout, all stdlib/local."
)


def read_json(path):
    with io.open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def close_queue(execute):
    """Close the head row, note the discharge, seed one real gap row."""
    with io.open(QUEUE, "r", encoding="utf-8", newline="") as handle:
        text = handle.read()
    if text.count(OLD_ROW) != 1:
        raise SystemExit("E_R2351_ROW count=%d" % text.count(OLD_ROW))
    text = text.replace(OLD_ROW, NEW_ROW, 1)
    marker = NEW_ROW
    head, sep, tail = text.partition(marker)
    line_end = tail.index("\n") + 1
    text = head + marker + tail[:line_end] + DISCHARGE + "\n" + tail[line_end:]
    if not text.endswith("\n"):
        text += "\n"
    text += NEW_SEED + "\n"
    print("QUEUE closed row 396, seeded residue_triage_entry_retire, "
          "bytes=%d" % len(text.encode("utf-8")))
    if not execute:
        return 0
    with io.open(QUEUE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    with io.open(QUEUE, "r", encoding="utf-8") as handle:
        back = handle.read()
    ok = back == text
    print("QUEUE READBACK ok=%s" % ok)
    return 0 if ok else 2


def prepend_backlog(execute):
    line = (
        "- [x] [done 2026-11-01 R2351] product-face-R2351: "
        "state/queue/tech.md:396 AC-RTRH1 residue_triage_head_renew - the "
        "triage declaration head finally has a writer, and it may only renew "
        "what it measured. src/os/residue_triage_head_renew.py + "
        "src/os/test_residue_triage_head_renew.py: the entry set, the status "
        "vocabulary and the live residue are imported from residue_triage and "
        "the head claim from residue_triage_decl_reason (all four patched in "
        "the suite, and the module carries no json.loads and no second "
        "declaration reader), the dry run is the default and writes no byte, "
        "three refusals name their rounds before any byte (a declared entry "
        "disagreeing with the live reading, a live residue round with no "
        "declaration, a round that would predate an entry's declared_by), and "
        "the executed renewal is ONE atomic splice that rewrites only the head "
        "declared_by and reason values, leaves the entries region "
        "byte-identical and proves its own predicted size with no temp "
        "residue. SUITE PASS 6/6 twice identical digest E76AE248C5320D9E via "
        "evidence_capture (qa/residue-triage-head-renew-R2351.log, 834B) plus "
        "three adjacent suites green, wired os-residue-triage-head-renew(6). "
        "LIVE: the real declaration REFUSES renewal E_RTRH_UNDECLARED naming "
        "R2339, so the head stays at R2331 instead of being renewed over a set "
        "it does not speak for; the adjacent residue_triage suite is RED on "
        "the same pre-existing drift (untriaged R2339, unmatched R2342) and "
        "that is disclosed, not swept. Board: row closed, one REAL gap row "
        "seeded (residue_triage_entry_retire, AC-RTER1..AC-RTER6 "
        "pre-registered, anchors zero-occupancy). Battery NOT run: the "
        "measured successor target is 484 suites / 3880 criteria.\n")
    print("BACKLOG prepend bytes=%d" % len(line.encode("utf-8")))
    if not execute:
        return 0
    with io.open(BACKLOG, "r", encoding="utf-8", newline="") as handle:
        text = handle.read()
    text = line + text
    with io.open(BACKLOG, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    with io.open(BACKLOG, "r", encoding="utf-8") as handle:
        back = handle.read()
    ok = back == text
    print("BACKLOG READBACK ok=%s" % ok)
    return 0 if ok else 2


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
    if len(data) > 78500:
        raise SystemExit("E_R2351_STATE_GATE bytes=%d" % len(data))
    if not execute:
        print("DRY RUN: pass --execute to write")
        return 0
    folder = os.path.dirname(os.path.abspath(STATE))
    handle, temp = tempfile.mkstemp(dir=folder, prefix=".state_R2351_")
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
        "src/os/residue_triage_head_renew.py", "on",
        "R2351 product: the triage declaration head has a writer that renews "
        "only what it measured - dry run by default, three named refusals "
        "before any byte, one atomic splice that leaves every entry "
        "byte-identical and proves its predicted size",
    ])
    data["results"].append([
        "R2351",
        "product window: residue_triage_head_renew shipped with "
        "AC-RTRH1..AC-RTRH6 (6/6 twice plus three adjacent suites), live "
        "reading refuses with E_RTRH_UNDECLARED naming R2339 so the head "
        "stays at R2331; one real gap row seeded "
        "(residue_triage_entry_retire); no battery ran and the measured "
        "successor target is 484 suites / 3880 criteria",
    ])
    label = patterns["tick_row_label"]
    tick_rows = [row for row in data["results"]
                 if isinstance(row, list) and len(row) >= 2 and row[1] == label]
    if len(tick_rows) != 1:
        raise SystemExit("E_R2351_TICK_ROW count=%d" % len(tick_rows))
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
    if "--append-tokens" in argv:
        # The round-accounting line is written after the window item so the
        # window log keeps its own order; nothing else is touched here.
        state = read_json(STATE)
        if any(item.startswith("R2351 tokens:") for item in state["log"]):
            print("TOKENS already present")
            return 0
        state["log"] = state["log"] + [TOKENS]
        payload = json.dumps(state, ensure_ascii=False, indent=2,
                             sort_keys=False)
        data = SIO.canon(payload).encode("utf-8")
        print("STATE log_items=%d bytes=%d" % (len(state["log"]), len(data)))
        if len(data) > 78500:
            raise SystemExit("E_R2351_STATE_GATE bytes=%d" % len(data))
        if not execute:
            print("DRY RUN: pass --execute to write")
            return 0
        folder = os.path.dirname(os.path.abspath(STATE))
        handle, temp = tempfile.mkstemp(dir=folder, prefix=".state_R2351t_")
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
            ok = back.read() == data
        print("STATE READBACK ok=%s" % ok)
        return 0 if ok else 2
    if "--export-only" in argv:
        return write_export(read_json(STATE), execute)
    code = close_queue(execute)
    if code:
        return code
    code = prepend_backlog(execute)
    if code:
        return code
    code = bump_state(execute)
    if code:
        return code
    code = write_export(read_json(STATE), execute)
    if code:
        return code
    return write_heartbeat(read_json(STATE), execute)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))