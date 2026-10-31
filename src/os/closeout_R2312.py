"""closeout_R2312.py - this window's bookkeeping, one guarded step each.

Steps (each refuses before writing when its own guard fails):
  append    - tick 2312 and the R2312 log items, in the canonical layout
  queue     - close the R2300 tech seed row and seed one real successor
  boards    - prepend the R2313 first item to src/os/backlog.md
  export    - refresh docs/status-export.json from the R2312 face
  heartbeat - append the tick 2312 row

ASCII source only; the Chinese CEO face lives in the JSON data file.
"""

import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import state_io as SIO

ROOT = os.path.dirname(os.path.dirname(HERE))
STATE = os.path.join(ROOT, "src", "os", "state.json")
EXPORT = os.path.join(ROOT, "docs", "status-export.json")
FACE = os.path.join(ROOT, "state", "export_face_R2312.json")
HEARTBEAT = os.path.join(ROOT, "heartbeat.txt")
TECH = os.path.join(ROOT, "state", "queue", "tech.md")
BACKLOG = os.path.join(ROOT, "src", "os", "backlog.md")

ROUND = "R2312"
TICK = 2312

ROW_MARK = "- [ ] P2 tech seed (R2300"
ROW_CRITERIA = "AC-GDA1"

NARRATIVE = (
    "2026-11-01 R2312 product window (five-silence scan clean at open: empty "
    "git status, no index.lock; decisions.md 289 non-empty rows EQUAL to the "
    "stored 289-row baseline; the group ledger carries the same three "
    "@BigDomain patrol rows already paid off, the last one P-20261026-0930 "
    "acked at R2311, with zero unreplied numbered handoffs; group orders tail "
    "unchanged at 2026-10-31 18:23; benchmarks refreshed 2026-10-29 inside "
    "the seven-day gate). The debt gate named product-face-R2310 and its note "
    "was STALE (that face shipped at R2310), so the live head was re-read with "
    "queue_head: line 374 prefix AC-GDA1, the R2300 seed whose AC-GDA1..AC-GDA6 "
    "were pinned BEFORE any code. DELIVERED: src/os/gate_decl_append.py + "
    "src/os/test_gate_decl_append.py. state/machine_gates.json had a reader "
    "and a drift reader and NO writer, so every blocker was a hand edit; the "
    "writer takes identity/capability/reason/declared_by, validates them "
    "against machine_gate's own vocabulary, refuses a duplicate identity, an "
    "unknown capability and a second declaration header BEFORE any byte "
    "changes, splices one entry into the gates array AS TEXT so a pre-existing "
    "entry stays byte-intact, re-parses the post through machine_gate and "
    "requires exactly one new entry, and is a dry run by default with a "
    "predicted byte delta, one atomic os.replace, a read-back byte proof and "
    "no temp residue. One law, two entry points: machine_gate.read_declaration "
    "now delegates to a new read_declaration_text, so the writer asks the "
    "reader that already refused every defect instead of owning a second copy "
    "of the shape. SUITE PASS 6/6 twice with an identical criterion digest and "
    "the three adjacent gate suites green (gate_drift 6/6, machine_gate 6/6, "
    "residue_triage 6/6), qa/gate-decl-append-R2312.log 1268B as one utf-8 LF "
    "single writer through the evidence_capture callable. LIVE: the plan on "
    "the real declaration reports declarations=1->2 bytes=427->567 and writes "
    "nothing, and a re-declaration of the live identity -#02878cdc refuses "
    "E_GDA_DUP naming the field. Two points: a product face with a suite."
)

DISCLOSURES = (
    "R2312 honest disclosures: (a) the first smoke run refused the valid call "
    "with E_GDA_SHAPE because the byte-intact proof compared the raw array "
    "body INCLUDING its trailing whitespace against a post body that now "
    "carries a comma after the last entry; the proof was corrected to compare "
    "the stripped body, which is what 'the pre-existing entry is byte-intact' "
    "actually means, and no criterion was widened. (b) AC-GDA2 first read red "
    "for a test defect, not a module defect: the CLI prints only the refusal "
    "code, so the field naming the criterion demands is asserted on the "
    "exception detail instead of on stdout. (c) AC-GDA5 first raised "
    "TypeError because the suite unpacked run_cli's (rc, stdout) in the wrong "
    "order and then compared two DIFFERENT operations as if they were the same "
    "call - the byte-stability leg now reads two identical fresh worlds. (d) "
    "machine_gate.py was edited in this window (read_declaration split into "
    "read_declaration + read_declaration_text); its own suite and gate_drift "
    "were re-run green afterwards, which is the only reason the edit is "
    "claimed safe. (e) the full reconcile battery did NOT run here (the R2168 "
    "mixed-tree rule keeps it on a committed tree), so the successor row "
    "carries it with the pre-registered target of 463 suites / 3754 criteria - "
    "exactly +1 suite / +6 criteria against R2311 (462/3748) from this "
    "window's own os-gate-decl-append suite - so any larger delta would be "
    "unaccounted for and must be named rather than swept."
)

TOKENS = (
    "R2312 tokens: local=~13k api=0 api_reason=no cloud call - one reader "
    "refactor inside machine_gate, one writer, one six-criteria suite run "
    "three times, three adjacent suites, one evidence capture through the "
    "shared callable, one queue close and one seed, one register close and "
    "append, and the state/board/export closeout; zero external API touches."
)

SELF_HEAL = (
    "R2312 self-heal check: BigDomain-OSLoop is registered and its principal "
    "still reads LogonType=InteractiveToken, which the 2026-09-29 machine law "
    "forbids for every lane task; src/os/register_loop_task.ps1 already passes "
    "an explicit S4U principal and needs an elevated shell to apply, and this "
    "session runs unelevated, so the definition of the loop hosting this "
    "window was left untouched. Open local-lane item for an elevated window "
    "(seventy-fourth consecutive disclosure, carried as the stale row "
    "loop-s4u-reconcile in state/debt.md)."
)

SEED_ROW = (
    "- [ ] P2 tech seed (R2312, from this window own live finding): "
    "`src/os/gate_decl_retire.py` - the gate declaration can now gain an entry "
    "through `gate_decl_append`, but it can never lose one: once the blocked "
    "row is completed or its text moves, the entry stays in "
    "`state/machine_gates.json` forever and only reads INERT, so the "
    "declaration rots in the direction the reviewer names and nobody can "
    "retire it - exactly the shape `stamp_exempt_prune` was seeded for on the "
    "stamp side. One writer that takes an identity, refuses an identity that "
    "is not declared, refuses to drop an entry the live `machine_gate` reading "
    "still BLOCKS (an entry that is still doing its job is not a retirement "
    "candidate), splices the entry out as text with every surviving entry "
    "byte-intact, re-parses the post through `machine_gate.read_declaration` "
    "and requires exactly one fewer entry, and is a dry run by default with a "
    "predicted byte delta, one atomic replace, a read-back byte proof and no "
    "temp residue. Criteria prefix AC-GDRT1..AC-GDRT6 pre-registered HERE "
    "BEFORE any code: AC-GDRT1 the entry keys, the declaration keys and the "
    "post reader are imported from `machine_gate`, never re-implemented, and a "
    "patched reader flows straight through; AC-GDRT2 an undeclared identity "
    "and an entry the live reading still blocks are refused before any byte "
    "changes, each refusal naming the offending field; AC-GDRT3 the planned "
    "report gives the before and after byte counts and the removed entry "
    "index, writes nothing, while execute performs one atomic replace, proves "
    "the read-back bytes equal the prediction and leaves no temp file; "
    "AC-GDRT4 the post text re-parses and carries exactly one fewer entry, "
    "every surviving entry byte-intact and the removed identity absent; "
    "AC-GDRT5 CLI exits 0 planned or retired, 2 refused, 3 missing or "
    "unreadable or malformed, 5 bad flags, with a byte-stable --json over "
    "pinned keys; AC-GDRT6 pure ASCII source, stdlib only, no network, no "
    "clock, plus its own reconcile label. Anchor check at HEAD 2026-11-01: "
    "gate_decl_retire / AC-GDRT / E_GDRT / os-gate-decl-retire / "
    "test_gate_decl_retire were all git grep -F zero-occupancy rc=1."
)

BACKLOG_ROW = (
    "- [ ] R2313 first item: THE BATTERY ON THE COMMITTED TREE, zero product "
    "edits until green (the R2168 mixed-tree rule). R2312 changed src/os "
    "(gate_decl_append.py, test_gate_decl_append.py, machine_gate.py split, "
    "closeout_R2312.py), one runner entry, the tech queue (one row closed and "
    "one seed added), the debt register, the export and state.json, so run the "
    "full reconcile battery on the committed tree with an empty git status "
    "before the run, expecting exactly +1 suite / +6 criteria against R2311 "
    "(462 suites / 3748 criteria) from this window os-gate-decl-append suite - "
    "463 suites / 3754 criteria - measure it and disclose any delta that does "
    "not resolve to a named suite. Then the four follow-up sections through "
    "src/os/battery_followup.py: the matrix section will FAIL first on the "
    "stale doc and must NOT rewrite it, so regenerate with "
    "src/sandbox/suite_matrix.py and re-run. After that re-read the product "
    "face live (`python src/os/gate_decl_append.py --identity '-#02878cdc' "
    "--capability docker --reason x --declared-by R2313` must refuse E_GDA_DUP "
    "and write nothing) and read the seeded row with `python "
    "src/os/queue_head.py --head tech` rather than trusting this line. Also "
    "open and needing an ELEVATED shell: BigDomain-OSLoop reads "
    "LogonType=InteractiveToken (seventy-fourth consecutive disclosure; "
    "carried as loop-s4u-reconcile in state/debt.md, still stale)."
)

HEARTBEAT_2312 = ("tick 2312 2026-11-01 R2312 product gate_decl_append 6/6 "
                  "green adjacent 3/3")


def load(path):
    with io.open(path, "rb") as handle:
        return handle.read()


def write_atomic(path, blob):
    temp = path + ".tmp-r2312"
    with io.open(temp, "wb") as sink:
        sink.write(blob)
        sink.flush()
        os.fsync(sink.fileno())
    os.replace(temp, path)
    return len(blob)


def step_append(argv):
    raw = load(STATE)
    state = json.loads(raw.decode("utf-8"))
    if state["tick"] != TICK - 1:
        print("E_TICK expected %d found %s" % (TICK - 1, state["tick"]))
        return 3
    log = state["log"]
    if [item for item in log if item.startswith("2026-11-01 R2312 ")]:
        print("ALREADY appended")
        return 0
    state["tick"] = TICK
    log.extend([NARRATIVE, DISCLOSURES, TOKENS, SELF_HEAL])
    text = json.dumps(state, ensure_ascii=False, indent=4) + "\n"
    text = SIO.canon(text)
    measured = SIO.layout(text)
    if not measured["layout_ok"]:
        print("E_LAYOUT %r" % (measured,))
        return 3
    if json.loads(text) != state:
        print("E_PAYLOAD")
        return 3
    blob = text.encode("utf-8")
    if len(blob) > 78500:
        print("E_WATERLINE predicted=%d gate=78500" % len(blob))
        return 3
    if "--execute" not in argv:
        print("DRY RUN append predicted=%d log=%d" % (len(blob), len(log)))
        return 0
    size = write_atomic(STATE, blob)
    back = json.loads(load(STATE).decode("utf-8"))
    if back["tick"] != TICK or len(back["log"]) != len(log):
        print("E_READBACK")
        return 3
    print("APPEND %dB tick=%d log=%d" % (size, back["tick"], len(back["log"])))
    return 0


def step_queue(argv):
    text = load(TECH).decode("utf-8")
    lines = text.split("\n")
    hits = [index for index, line in enumerate(lines)
            if line.startswith(ROW_MARK) and ROW_CRITERIA in line]
    if len(hits) != 1:
        print("E_QUEUE_ROW found %d" % len(hits))
        return 3
    at = hits[0]
    line = lines[at]
    if line.startswith("- [x]"):
        print("ALREADY closed")
        return 0
    closed = ("- [x] [done 2026-11-01 R2312] " + line[len("- [ ] "):]
              + " [done 2026-11-01 R2312] Discharged as the product face and "
                "committed BEFORE any battery (the R2168 mixed-tree rule). "
                "DELIVERED: src/os/gate_decl_append.py + "
                "src/os/test_gate_decl_append.py, and one additive split in "
                "src/os/machine_gate.py (read_declaration now delegates to "
                "read_declaration_text so the writer asks the reader rather "
                "than owning a second copy of the shape law; machine_gate "
                "6/6 and gate_drift 6/6 re-read green after the edit). The "
                "writer validates identity/capability/reason/declared_by "
                "against machine_gate's own vocabulary, refuses a duplicate "
                "identity, an unknown capability and a second declaration "
                "header before any byte changes, splices one entry into the "
                "gates array AS TEXT so every pre-existing entry stays "
                "byte-intact, re-parses the post and requires exactly one new "
                "entry, and is a dry run by default with a predicted byte "
                "delta, one atomic replace, a read-back proof and no temp "
                "residue. SUITE PASS 6/6 twice with an identical criterion "
                "digest plus three adjacent gate suites green through "
                "evidence_capture (qa/gate-decl-append-R2312.log, 1268B, one "
                "utf-8 LF single writer). LIVE: the plan on the real "
                "declaration reads declarations=1->2 bytes=427->567 and "
                "writes nothing; re-declaring -#02878cdc refuses E_GDA_DUP "
                "naming the field. The claim left tech claimable at 9, so one "
                "real gap row was seeded (gate_decl_retire, AC-GDRT1..AC-GDRT6 "
                "pre-registered, five anchors zero-occupancy).")
    lines[at] = closed
    seed_at = at + 1
    for index in range(at, len(lines)):
        if lines[index].startswith("- [ ]"):
            seed_at = index
            break
    lines.insert(seed_at, SEED_ROW)
    post = "\n".join(lines)
    if "--execute" not in argv:
        print("DRY RUN queue close=%d seed_at=%d bytes=%d->%d"
              % (at + 1, seed_at + 1, len(text.encode("utf-8")),
                 len(post.encode("utf-8"))))
        return 0
    size = write_atomic(TECH, post.encode("utf-8"))
    print("QUEUE closed line=%d seed_at=%d %dB" % (at + 1, seed_at + 1, size))
    return 0


def step_boards(argv):
    text = load(BACKLOG).decode("utf-8")
    if BACKLOG_ROW[:60] in text:
        print("ALREADY on the board")
        return 0
    lines = text.split("\n")
    at = 1 if lines and lines[0].strip().startswith("#") else 0
    lines.insert(at, BACKLOG_ROW)
    post = "\n".join(lines)
    if "--execute" not in argv:
        print("DRY RUN boards insert_at=%d" % (at + 1))
        return 0
    size = write_atomic(BACKLOG, post.encode("utf-8"))
    print("BOARDS inserted at %d %dB" % (at + 1, size))
    return 0


def step_export(argv):
    face = json.loads(load(FACE).decode("utf-8"))
    data = json.loads(load(EXPORT).decode("utf-8"))
    import datetime
    now = datetime.datetime.now().astimezone().replace(microsecond=0)
    data["export_ts"] = now.isoformat()
    data["do"] = face["do"]
    block = data.setdefault("ceo_face", {})
    block["current"] = face["current"]
    block["latest_artifact"] = face["latest"]
    block["next_milestone"] = face["next"]
    block["next_milestone_due"] = (
        now + datetime.timedelta(hours=48)).replace(microsecond=0).isoformat()
    block["last_artifact"] = face["last"]
    data["results"] = [[ROUND, face["result"]]] + data["results"]
    data["outs"] = [[face["out"], "on", face["result"]]] + data["outs"]
    import check_export_consistency as consistency
    derived, _, _, pattern = consistency.recompute()
    data["self_drive"] = derived
    label = pattern["tick_row_label"]
    rows = [row for row in data["results"]
            if isinstance(row, list) and len(row) >= 2 and row[1] == label]
    if len(rows) != 1:
        print("E_TICK_ROW found %d" % len(rows))
        return 3
    rows[0][0] = str(TICK)
    blob = (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode(
        "utf-8")
    if "--execute" not in argv:
        print("DRY RUN export results=%d outs=%d"
              % (len(data["results"]), len(data["outs"])))
        return 0
    size = write_atomic(EXPORT, blob)
    back = json.loads(load(EXPORT).decode("utf-8"))
    if back["export_ts"] != data["export_ts"]:
        print("E_EXPORT_READBACK")
        return 3
    print("EXPORT %dB results=%d outs=%d" % (size, len(back["results"]),
                                             len(back["outs"])))
    return 0


def step_heartbeat(argv):
    text = load(HEARTBEAT).decode("utf-8")
    have = set(line.split()[1] for line in text.splitlines()
               if line.startswith("tick ") and len(line.split()) > 1)
    if str(TICK) in have:
        print("HEARTBEAT already carries tick %d" % TICK)
        return 0
    if not text.endswith("\n"):
        text += "\n"
    text += HEARTBEAT_2312 + "\n"
    if "--execute" not in argv:
        print("DRY RUN heartbeat +1 row")
        return 0
    size = write_atomic(HEARTBEAT, text.encode("utf-8"))
    print("HEARTBEAT +1 row %dB" % size)
    return 0


STEPS = {"append": step_append, "queue": step_queue, "boards": step_boards,
         "export": step_export, "heartbeat": step_heartbeat}


def main(argv):
    if len(argv) < 2 or argv[1] not in STEPS:
        sys.stdout.write("usage: closeout_R2312.py {%s} [--execute]\n"
                         % "|".join(sorted(STEPS)))
        return 5
    return STEPS[argv[1]](argv)


if __name__ == "__main__":
    sys.exit(main(sys.argv))