"""closeout_R2313.py - this window's bookkeeping, one guarded step each.

Steps (each refuses before writing when its own guard fails):
  append    - tick 2313 and the R2313 log items, in the canonical layout
  queue     - seed one real gap row from this window's own live reading
  boards    - prepend the R2314 first item to src/os/backlog.md
  export    - refresh docs/status-export.json from the R2313 face
  heartbeat - append the tick 2313 row

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
FACE = os.path.join(ROOT, "state", "export_face_R2313.json")
HEARTBEAT = os.path.join(ROOT, "heartbeat.txt")
TECH = os.path.join(ROOT, "state", "queue", "tech.md")
BACKLOG = os.path.join(ROOT, "src", "os", "backlog.md")

ROUND = "R2313"
TICK = 2313

SEED_MARK = "- [ ] P2 tech seed (R2313, from this window own live finding)"

NARRATIVE = (
    "2026-11-01 R2313 verification window (five-silence scan clean at open: "
    "empty git status --short, no index.lock; decisions.md carries 289 "
    "non-empty rows EQUAL to the stored 289-row baseline and the token set "
    "diff is empty, so no new decision row is presented and zero domain "
    "action is owed; the group ledger carries the same three @BigDomain "
    "patrol rows already paid off, the last one P-20261026-0930 acked at "
    "R2311, with zero unreplied numbered handoffs; group orders tail "
    "unchanged at 2026-10-31 18:23; benchmarks refreshed 2026-10-29 inside "
    "the seven-day gate). The debt gate named exactly one first=yes row "
    "(product-face-R2313) and its note was live, so this window ran the "
    "VERIFICATION it demanded with ZERO product edits until green (the R2168 "
    "mixed-tree rule). RESULT: full reconcile battery on the committed R2312 "
    "tree 21ea75c9 with an empty git status before the run = RUNNER PASS "
    "463/463 suites green plus controls 7/7 in 800.3s with birth-site TMP "
    "RECLAIM 932/932 worlds 326.57 MiB busy zero failed zero "
    "(qa/reconcile-all-R2313.log, 783785B, single writer utf-8 LF through "
    "src/os/battery_stream.py, never a shell redirection), criteria total "
    "3754 - exactly the pre-registered +1 suite / +6 criteria against R2311 "
    "(462/3748) from the R2312 os-gate-decl-append suite, so the prediction "
    "matched the measurement with no correction. Four follow-up sections then "
    "ran through src/os/battery_followup.py: the matrix section FAILED first "
    "on the stale doc (on-disk=44406B regenerated=44486B) and did NOT rewrite "
    "it, which is the designed order; src/sandbox/suite_matrix.py "
    "regenerated docs/sandbox-suite-matrix.md to 463 suites / 3754 criteria "
    "(44486B) and the re-run read all four sections PASS (matrix "
    "byte-identical 44486B, fingerprint CLEAN 5 domains, profile --daily "
    "--check byte-identical, census DRIFT-CLEAN), VERDICT R2313 PASS. Then "
    "the live product reading the debt note demanded: "
    "gate_decl_append.py --identity '-#02878cdc' --capability docker refused "
    "E_GDA_DUP at exit 2 and the declaration hash stayed "
    "10EF269E863896CE9BE023FF57AD70B1CDB3EF5F83FFEBA09CEAFE41C8A64DF7, and "
    "queue_head re-read the tech head live. Zero product points; the product "
    "face carries to R2314."
)

DISCLOSURES = (
    "R2313 honest disclosures: (a) an UNINTENDED WRITE happened and is "
    "disclosed rather than swept: the first duplicate probe used --identity "
    "'-' instead of the live '-#02878cdc', the writer judged it a NEW "
    "identity and APPENDED an entry (427B -> 548B, hash 1E96CA4C). It was "
    "reverted inside the same window: git checkout produced the committed "
    "CONTENT but with CRLF worktree bytes (439B), so the blob was then "
    "rewritten from 'git show HEAD:state/machine_gates.json' and the file "
    "reads 427B / LF / hash 10EF269E again, byte-identical to HEAD with an "
    "empty git diff. The intended refusal probe was then run correctly and "
    "refused E_GDA_DUP at exit 2. (b) That accident is also this window's "
    "real finding, and the seed row is written from the measurement, not from "
    "theory: identity validation is machine_gate's permissive non-empty "
    "uniqueness rule, so a bare placeholder '-' that no row carries is "
    "accepted and planned for 120 bytes while a true duplicate is refused - "
    "the writer cannot tell a live row identity from a typo. (c) The waterline "
    "fold ran BEFORE the append because the margin was 2486B against a 5200B "
    "write: fold 613 over log lines 1..5 (whole round blocks), 614 window "
    "tokens covered, predicted 69563B equal to measured 69563B. (d) The "
    "battery was launched as a detached hidden process because battery_stream "
    "buffers its evidence in memory and writes once at completion, so probes "
    "before the end legitimately found no file - that is buffering, not a "
    "dead runner, confirmed by live child processes and then by the 783785B "
    "file. One polling command was cancelled by the five-minute no-output "
    "rule mid-wait; it spent no work and the battery was untouched. (e) This "
    "round shipped no product code, so the register successor names the "
    "seeded face (gate_decl_identity) rather than a second verification. (f) "
    "The tech queue claimable count rises 10 -> 11 because the seed is this "
    "window's own measured gap and not filler; no row was closed because no "
    "queue row was claimed. (g) tasks.md was left untouched: it is the P-47 "
    "canonical board and carries no row for this tech slice, disclosed rather "
    "than silently skipped."
)

TOKENS = (
    "R2313 tokens: local=~10k api=0 api_reason=verification-only window - one "
    "full reconcile battery on the committed tree with its streamed evidence "
    "file, one four-section follow-up plus one matrix regeneration and a "
    "re-run that read all four PASS, one live duplicate-refusal probe with an "
    "unintended write reverted byte-exactly, one queue_head re-read, one "
    "waterline fold, and the queue/board/state/export closeout; zero cloud "
    "calls and zero external API touches."
)

SELF_HEAL = (
    "R2313 self-heal check: BigDomain-OSLoop is registered and its principal "
    "still reads LogonType=InteractiveToken, which the 2026-09-29 machine law "
    "forbids for every lane task; src/os/register_loop_task.ps1 already passes "
    "an explicit S4U principal and needs an elevated shell to apply, and this "
    "session runs unelevated, so the definition of the loop hosting this "
    "window was left untouched. Open local-lane item for an elevated window "
    "(seventy-fifth consecutive disclosure, carried as the stale row "
    "loop-s4u-reconcile in state/debt.md)."
)

SEED_ROW = (
    "- [ ] P2 tech seed (R2313, from this window own live finding): "
    "`src/os/gate_decl_identity.py` - the gate writer validates an identity "
    "only as a NON-EMPTY UNIQUE STRING, so it cannot tell a live row identity "
    "from a typo or a bare placeholder. Measured this window: `--identity "
    "'-' --capability docker` was planned as a brand-new declaration "
    "(427B -> 547B, verdict PLANNED) because '-' is not the declared "
    "'-#02878cdc', while the true duplicate was refused E_GDA_DUP - so a "
    "misaddressed blocker lands silently and then reads INERT against every "
    "row forever. One reader that takes the declaration plus the live queue "
    "text and resolves each identity against `queue_head`'s own row law, "
    "reporting MATCHED (the identity names a row that exists), UNMATCHED (no "
    "row carries it) and AMBIGUOUS (a bare prefix several rows share), and "
    "refuses nothing (it is a reader, not a gate); the writer then asks THAT "
    "reader instead of owning a second copy of the address law. Criteria "
    "prefix AC-GDI1..AC-GDI6 pre-registered HERE BEFORE any code: AC-GDI1 the "
    "row parsing and the identity shape come from `queue_head` and "
    "`machine_gate`, never re-implemented, proven by patching each import and "
    "watching the verdict move; AC-GDI2 MATCHED / UNMATCHED / AMBIGUOUS are "
    "exhaustive and disjoint over the live declaration and every reading "
    "names the identity and the row line or the reason; AC-GDI3 a bare "
    "placeholder shared by several rows reads AMBIGUOUS naming every carrier "
    "rather than silently borrowing the first; AC-GDI4 every reading is "
    "level-tagged so a MATCHED row that is not claimable is still MATCHED and "
    "the reader never criticises claimability; AC-GDI5 CLI exits 0 all "
    "matched, 2 any unmatched or ambiguous, 3 missing or unreadable, 5 bad "
    "flags, with byte-stable --json over pinned keys; AC-GDI6 pure ASCII "
    "source, stdlib only, no network, no clock, plus its own reconcile label. "
    "Anchor check at HEAD 2026-11-01: gate_decl_identity / AC-GDI / E_GDI / "
    "os-gate-decl-identity / test_gate_decl_identity were all git grep -F "
    "zero-occupancy rc=1."
)

BACKLOG_ROW = (
    "- [ ] R2314 first item: the product face the register names - the "
    "`src/os/gate_decl_identity.py` seed at the tech head, whose "
    "AC-GDI1..AC-GDI6 criteria are pinned inside that row BEFORE any code "
    "(re-read it with `python src/os/queue_head.py --head tech` rather than "
    "trusting this line). Read the live declaration first: "
    "`state/machine_gates.json` carries one entry, '-#02878cdc', and a bare "
    "'-' is planned as new, which is the gap the row was seeded from. Ship "
    "the reader, its six-criteria suite, one dogfooded evidence capture "
    "through the shared callable, one runner wiring line, and read the whole "
    "live declaration through it. Then commit BEFORE any battery (the R2168 "
    "mixed-tree rule) and carry the battery to R2315 with the pre-registered "
    "target of +1 suite / +6 criteria against R2313 (463 suites / 3754 "
    "criteria). Also open and needing an ELEVATED shell: BigDomain-OSLoop "
    "reads LogonType=InteractiveToken (seventy-fifth consecutive disclosure; "
    "carried as loop-s4u-reconcile in state/debt.md, still stale)."
)

HEARTBEAT_2313 = ("tick 2313 2026-11-01 R2313 verification battery 463/463 "
                  "criteria 3754 followup 4/4 PASS")


def load(path):
    with io.open(path, "rb") as handle:
        return handle.read()


def write_atomic(path, blob):
    temp = path + ".tmp-r2313"
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
    if [item for item in log if item.startswith("2026-11-01 R2313 ")]:
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
    if SEED_MARK in text:
        print("ALREADY seeded")
        return 0
    import queue_head as QH
    rel = QH.queue_path("tech")
    report = QH.head_text("tech", rel, text)
    head = report["head"]
    if head is None:
        print("E_QUEUE no claimable head to anchor the seed")
        return 3
    seed_at = head["line"] - 1
    lines = text.split("\n")
    lines.insert(seed_at, SEED_ROW)
    post = "\n".join(lines)
    if "--execute" not in argv:
        print("DRY RUN queue seed_at=%d bytes=%d->%d"
              % (seed_at + 1, len(text.encode("utf-8")),
                 len(post.encode("utf-8"))))
        return 0
    size = write_atomic(TECH, post.encode("utf-8"))
    print("QUEUE seeded at %d %dB" % (seed_at + 1, size))
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
    text += HEARTBEAT_2313 + "\n"
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
        sys.stdout.write("usage: closeout_R2313.py {%s} [--execute]\n"
                         % "|".join(sorted(STEPS)))
        return 5
    return STEPS[argv[1]](argv)


if __name__ == "__main__":
    sys.exit(main(sys.argv))