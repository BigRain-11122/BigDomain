"""Closeout for the R2286 window: the queue/board flip and the state rows.

Both the queue file and the board are edited as text so the bytes that are
not this window's are untouched; the state batch append goes through the
shipped layout writers and proves its own bytes by re-parsing. Every refusal
happens before a write. A fold runs only when the predicted post size would
cross the gate.

ASCII, stdlib only, zero network.
"""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
STATE = os.path.join(ROOT, "src", "os", "state.json")
QUEUE = os.path.join(ROOT, "state", "queue", "tech.md")
BOARD = os.path.join(ROOT, "src", "os", "backlog.md")

sys.path.insert(0, BASE)
import state_fold  # noqa: E402

KEEP_LIVE = 24
TICK = 2286

ROW_HEAD = "- [ ] P2 tech seed (R2270, from this window own live reading): "
ROW_DONE_HEAD = "- [x] [done 2026-10-31 R2286] P2 tech seed (R2270, " \
                "from this window own live reading): "

DONE_NOTE = (
    " [done 2026-10-31 R2286] DELIVERED as this window's product face: "
    "src/os/machine_gate.py, src/os/test_machine_gate.py and the pinned "
    "declaration state/machine_gates.json (one docker blocker keyed by the "
    "row identity -#02878cdc), with AC-MGT1..AC-MGT6 already pinned in THIS "
    "row before the code. The head law is imported - every candidate comes "
    "out of queue_head.head_text and advancing past a blocked row only masks "
    "that row's leading marker in a copy of the text so the line count stays "
    "honest - and the suite proves it by patching that law (a constant head "
    "then reads through as AC-PATCH). Identity is <prefix>#<sha8 row text>, "
    "so a row that moves inside the file keeps its declaration while a row "
    "whose text changed stops matching and reads INERT instead of silently "
    "gating something else. A blocker must name identity, capability, reason "
    "and declared_by and must use the declared capability vocabulary, so a "
    "typo fails closed (E_MGT_BAD_CAPABILITY); a missing or unreadable "
    "declaration refuses the reading (E_MGT_NO_DECL / E_MGT_BAD_DECL) rather "
    "than pretending nothing is blocked. Evidence: SUITE PASS 6/6 "
    "double-run identical through the R2261 evidence_capture callable with "
    "five adjacent suites green (qa/machine-gate-R2286.log, 1304B, single "
    "writer utf-8 LF), wired os-machine-gate(6). LIVE at closeout: MACHINE "
    "GATE tech line=355 prefix=AC-MGT1 declarations=1 blocked=0 inert=1 "
    "candidates=7 verdict=OFFERED - the docker row 41 is declared but "
    "carries no criteria prefix, so the head law never offers it and the "
    "declaration is INERT until that row declares criteria (disclosed "
    "plainly rather than dressed up as a blocker in force). The claim drops "
    "tech claimable to 9, so one real gap row was seeded below (gate_drift, "
    "AC-GDR1..AC-GDR6 pre-registered, five anchors git grep -F "
    "zero-occupancy rc=1)."
)

SEED_ROW = (
    "- [ ] P2 tech seed (R2286, from this window own live reading): "
    "`src/os/gate_drift.py` - machine_gate reports an inert declaration as "
    "an identity that matches no candidate, but it cannot say WHY it stopped "
    "matching: a row whose text was edited and a row that was deleted both "
    "read as the same inert entry with line=None, so an operator cannot tell "
    "\"this blocker moved house\" from \"this blocker is gone\" and rebuild "
    "the declaration without grepping the queue by hand. One read-only "
    "drift reader that takes the prefix part of every inert identity, looks "
    "for candidate rows still carrying that prefix, and names the match - "
    "DRIFT with the old digest, the new digest and both lines when the row "
    "still exists, GONE when no row carries the prefix - so an inert entry "
    "becomes a decision instead of a shrug. Criteria prefix AC-GDR1..AC-GDR6 "
    "pre-registered HERE BEFORE any code: AC-GDR1 the gate reading and the "
    "declaration are both imported from machine_gate rather than "
    "re-implemented, and a patched reading flows straight through; "
    "AC-GDR2 DRIFT names the old identity, the new identity, the row line "
    "and the shared prefix, and GONE names the prefix with no line; AC-GDR3 "
    "the split is exhaustive and disjoint - every inert entry is either "
    "DRIFT or GONE, never both, and an empty inert list reads NO-DRIFT at "
    "exit 0 honestly; AC-GDR4 a missing or unreadable declaration or queue "
    "refuses the reading with its own code instead of reporting NO-DRIFT; "
    "AC-GDR5 CLI exits 0 no-drift / 2 drift / 3 unreadable / 5 bad flags "
    "with a byte-stable --json over pinned keys, and the reader writes "
    "nothing and reads no clock; AC-GDR6 pure ASCII source, stdlib only, "
    "zero network, plus its own reconcile label. Anchor check at HEAD "
    "2026-10-31: gate_drift, AC-GDR, E_GDR, os-gate-drift and "
    "test_gate_drift were all git grep -F zero-occupancy rc=1."
)

BOARD_DONE = (
    " [done 2026-10-31 R2286] Discharged as the product face on exactly the "
    "row the reader named (state/queue/tech.md:355 per queue_head's own "
    "newline numbering, prefix AC-MGT1): src/os/machine_gate.py + "
    "src/os/test_machine_gate.py + state/machine_gates.json. The head law is "
    "imported from queue_head (proven by patching it), identity is "
    "<prefix>#<sha8 row text> so a line shift never changes a declaration, a "
    "bad capability or a malformed entry refuses the whole reading, and an "
    "inert declaration is reported with its live line or line=None instead "
    "of being swallowed. SUITE PASS 6/6 double-run identical with five "
    "adjacent suites green (qa/machine-gate-R2286.log, 1304B, single writer "
    "utf-8 LF through evidence_capture), wired os-machine-gate(6). Claim "
    "dropped tech claimable to 9, so one real gap row was seeded "
    "(gate_drift) and the gauge closes at main 5/5 tech 10/10 explore 10/10. "
    "Committed BEFORE any battery (the R2168 mixed-tree rule); the battery "
    "and the matrix regeneration are the R2287 first item."
)

NEW_BOARD_ROW = (
    "- [ ] [carried 2026-10-31 R2286] R2287 first item: THE BATTERY ON THE "
    "COMMITTED TREE, zero product edits until green (the R2168 mixed-tree "
    "rule). R2286 changed src/os (machine_gate.py, test_machine_gate.py, "
    "closeout_R2286.py), state/machine_gates.json, one runner entry and the "
    "queue/board/state/export files, so run the full reconcile battery on "
    "the committed tree with an empty git status before and after; the "
    "registry read 448 suites / 3664 criteria at R2285 and the "
    "pre-registered expectation is +1 suite / +6 criteria (449 / 3670) from "
    "the os-machine-gate suite - measure it, and if a delta does not resolve "
    "to a named suite disclose the prediction error instead of sweeping it. "
    "Then the four follow-up sections through src/os/battery_followup.py "
    "(its matrix section will FAIL first on the stale doc and must not "
    "rewrite it; regenerate with src/sandbox/suite_matrix.py and re-run). "
    "After that the product face resumes at the tech head - re-read it, "
    "because the R2286 claim consumed line 355 and the new row is the head. "
    "Also open and needing an ELEVATED shell: BigDomain-OSLoop reads "
    "LogonType=InteractiveToken (fifty-second consecutive disclosure; "
    "carried as loop-s4u-reconcile in state/debt.md, still stale)."
)

ROWS = [
    "2026-10-31 R2286 (five-silence scan clean at open: tree clean with an "
    "empty git status --short and no index.lock; decisions.md carries 289 "
    "non-empty rows EQUAL to the stored 289-row baseline, so no new decision "
    "row is presented and zero domain action is owed; the group ledger "
    "carries the same three @BigDomain patrol rows already paid off with "
    "zero unreplied numbered handoffs; the group orders tail is unchanged at "
    "the 2026-10-31 18:23 baseline consumed in R2278; benchmarks refreshed "
    "2026-10-29 inside the seven-day gate) - the P1 canonical rows stay "
    "blocked-on-CEO, the weekly proposal duty is met by BD-PROP-005, the "
    "queue floors read FLOOR-MET main 5/5 tech 10/10 explore 10/10, and the "
    "debt gate named exactly one first=yes row (product-face-R2286), so this "
    "window claimed the TOP deliverable tech row that the gate itself named: "
    "the R2270 machine_gate seed, its AC-MGT1..AC-MGT6 criteria already "
    "pinned INSIDE that row BEFORE the code (fresh zero-occupancy anchor "
    "check at HEAD 2026-10-31: E_MGT and test_machine_gate were git grep -F "
    "rc 1, while machine_gate / AC-MGT / os-machine-gate hit only prose plus "
    "the closeout and export helpers - disclosed). PRODUCT: "
    "src/os/machine_gate.py plus src/os/test_machine_gate.py plus the pinned "
    "declaration state/machine_gates.json - whether this host can DELIVER the "
    "row the reader names becomes a reading. queue_head answers which row "
    "comes first and honestly offers rows a human only skips from memory; the "
    "gate joins one declared file of capability blockers with that reading "
    "and names the first claimable row this host is not blocked from. The "
    "head law is IMPORTED - every candidate comes out of queue_head.head_text "
    "and advancing past a blocked row only masks that row's leading marker in "
    "a copy of the text, so the line count stays honest and the same law is "
    "asked again - and the suite proves the import by patching it (a "
    "constant head then reads through as AC-PATCH). Identity is "
    "<prefix>#<sha8 of the row text>, stable across a line shift; a row whose "
    "text changed stops matching and its declaration reads INERT with its "
    "live line or line=None rather than silently gating something else. A "
    "blocker must name identity, capability, reason and declared_by and must "
    "use the declared capability vocabulary, so a typo fails closed "
    "(E_MGT_BAD_CAPABILITY); missing, unreadable or malformed declarations "
    "refuse the reading (E_MGT_NO_DECL / E_MGT_BAD_DECL / E_MGT_BAD_ENTRY) "
    "instead of pretending nothing is blocked. Evidence: SUITE PASS 6/6 "
    "double-run identical through the R2261 evidence_capture callable with "
    "five adjacent suites green (qa/machine-gate-R2286.log, 1304B, single "
    "writer utf-8 LF), wired os-machine-gate(6). LIVE at closeout: MACHINE "
    "GATE tech line=355 prefix=AC-MGT1 declarations=1 blocked=0 inert=1 "
    "candidates=7 verdict=OFFERED, the one inert entry being the docker row "
    "41 - declared, but that row carries no criteria prefix so the head law "
    "never offers it and the declaration is honestly inert until it does.",
    "R2286 tokens: local=~22k api=0 api_reason=product window on the debt "
    "register first item - one new os module with its six pre-registered "
    "criteria and its suite, one pinned declaration file, one dogfooded "
    "evidence capture (two legs identical, five adjacent suites green), one "
    "live CLI reading that keeps the inert declaration honest, one runner "
    "wiring line, one real gap row seeded to hold the tech floor, and the "
    "queue/board/state/export closeout; zero cloud calls and zero external "
    "API touches",
    "R2286 self-heal check: BigDomain-OSLoop is registered and its principal "
    "still reads LogonType=InteractiveToken, which the 2026-09-29 machine law "
    "forbids for every lane task; src/os/register_loop_task.ps1 already "
    "passes an explicit S4U principal and needs an elevated shell to apply "
    "it, and this session runs unelevated, so the definition of the loop "
    "hosting this window was left untouched. Open local-lane item for an "
    "elevated window (fifty-second consecutive disclosure, carried as the "
    "stale row loop-s4u-reconcile in state/debt.md).",
    "R2286 honest disclosures: (a) the first suite run was red 3/6 and all "
    "three reds were this-window TEST defects measured against the truth, "
    "never criteria widened - the fixture rows lacked the word Criteria that "
    "queue_row's own prefix law requires, so no candidate existed at all, and "
    "the expected line numbers were one lower than the world actually laid "
    "out; both fixed in the tests. (b) The AC-MGT6 red was the honest one: "
    "the runner label was not yet wired, and the wiring landed before the "
    "green run. (c) queue_head's numbering is newline-based while Python's "
    "splitlines also splits the one form-feed character that sits in an "
    "older done row, so the same row reads as line 355 or 356 depending on "
    "the reader; this window follows queue_head (the law that produced the "
    "reading) and mentions the discrepancy rather than editing history. "
    "(d) The live declaration is inert today and is recorded as such - the "
    "value is the data layer plus the suite that proves blocked candidates "
    "are never offered on a world where they exist.",
]


def tokens_of(window):
    found = set()
    for line in window:
        found |= set(state_fold.PAT.findall(line))
    return sorted(found)


def raw_and_state():
    with io.open(STATE, "rb") as handle:
        raw = handle.read()
    return raw, json.loads(raw.decode("utf-8"))


def fold(execute):
    raw, state = raw_and_state()
    count = len(state["log"])
    end = count - KEEP_LIVE
    if end < 1:
        return None
    window = state["log"][0:end]
    tokens = tokens_of(window)
    summary = ("Fold 601 (R2286): log lines 1..%d folded verbatim into "
               "logs/state-log-archive-2026-10.md; window tokens: %s"
               % (end, " ".join(tokens)))
    return state_fold.fold(ROOT, "R2286", 601, 1, end, summary,
                           execute=execute)


def predicted_append_bytes(rows):
    raw, state = raw_and_state()
    text = raw.decode("utf-8")
    layout = state_fold.split_layout(text, len(state["log"]))
    if layout is None:
        raise SystemExit("REFUSE: log item lines do not match the log length")
    return sum(len(state_fold.ps_escape(row)) + len(state_fold.ITEM_PREFIX) + 2
               for row in rows)


def append(rows, tick, execute):
    raw, state = raw_and_state()
    if tick <= state["tick"]:
        raise SystemExit("REFUSE: tick %d is not above %d"
                         % (tick, state["tick"]))
    text = raw.decode("utf-8")
    layout = state_fold.split_layout(text, len(state["log"]))
    if layout is None:
        raise SystemExit("REFUSE: log item lines do not match the log length")
    newline = layout["newline"]
    index = layout["item_index"][-1]
    lines = list(layout["lines"])
    if not lines[index].rstrip().endswith(","):
        lines[index] = lines[index] + ","
    insert = []
    for position, row in enumerate(rows):
        tail = "," if position < len(rows) - 1 else ""
        insert.append(state_fold.ITEM_PREFIX + state_fold.ps_escape(row)
                      + tail)
    new_lines = lines[:index + 1] + insert + lines[index + 1:]
    body = newline.join(new_lines)
    body = body.replace('"tick": %d' % state["tick"], '"tick": %d' % tick, 1)
    data = body.encode("utf-8")
    if not execute:
        return {"would_bytes": len(data), "before": len(raw)}
    with io.open(STATE, "wb") as handle:
        handle.write(data)
    with io.open(STATE, "rb") as handle:
        back = handle.read()
    if back != data:
        raise SystemExit("REFUSE: read-back differs")
    check = json.loads(back.decode("utf-8"))
    expected = list(state["log"]) + list(rows)
    if check["log"] != expected or check["tick"] != tick:
        raise SystemExit("REFUSE: payload does not round-trip")
    return {"post_bytes": len(data), "before": len(raw),
            "log": len(check["log"]), "tick": check["tick"]}


def read_text(path):
    with io.open(path, "r", encoding="utf-8", newline="") as handle:
        return handle.read()


def write_text(path, text):
    data = text.encode("utf-8")
    with io.open(path, "wb") as handle:
        handle.write(data)
    with io.open(path, "rb") as handle:
        back = handle.read()
    if back != data:
        raise SystemExit("REFUSE: %s read-back differs" % path)
    return len(data)


def flip_queue(execute):
    text = read_text(QUEUE)
    if ROW_DONE_HEAD in text:
        raise SystemExit("REFUSE: the tech row is already stamped done")
    start = text.find(ROW_HEAD)
    if start < 0:
        raise SystemExit("REFUSE: the tech row head was not found")
    end = text.find("\n", start)
    if end < 0:
        raise SystemExit("REFUSE: the tech row has no line end")
    row = text[start:end]
    new_row = ROW_DONE_HEAD + row[len(ROW_HEAD):] + DONE_NOTE
    body = text[:start] + new_row + text[end:]
    if not body.endswith("\n"):
        body = body + "\n"
    body = body + SEED_ROW + "\n"
    if not execute:
        return {"row_bytes": len(row), "post_bytes": len(body)}
    return {"row_bytes": len(row), "post_bytes": write_text(QUEUE, body)}


def flip_board(execute):
    text = read_text(BOARD)
    head = "- [ ] [carried 2026-10-31 R2285] R2286 first item:"
    if head not in text:
        raise SystemExit("REFUSE: the carried R2286 board row was not found")
    if text.startswith(NEW_BOARD_ROW):
        raise SystemExit("REFUSE: the R2287 board row is already at the top")
    line_end = text.find("\n")
    first = text[:line_end]
    first = first.replace(head, "- [x] [carried 2026-10-31 R2285] "
                                "R2286 first item:", 1) + BOARD_DONE
    body = NEW_BOARD_ROW + "\n" + first + text[line_end:]
    if not execute:
        return {"post_bytes": len(body)}
    return {"post_bytes": write_text(BOARD, body)}


def main(argv):
    execute = "--execute" in argv
    before, state = raw_and_state()
    print("STATE before=%dB tick=%d log=%d gate=%d margin=%d"
          % (len(before), state["tick"], len(state["log"]),
             state_fold.GATE, state_fold.GATE - len(before)))
    predict = predicted_append_bytes(ROWS)
    will_cross = len(before) + predict >= state_fold.GATE
    print("APPEND predicted=%dB would_cross_gate=%r" % (predict, will_cross))
    if will_cross:
        plan = fold(execute)
        if plan is None:
            print("FOLD skipped: fewer than %d live rows" % (KEEP_LIVE + 1))
        else:
            print("FOLD window=%d:%d lines=%d tokens=%d predicted=%dB "
                  "mode=%s" % (plan["window_start"], plan["window_end"],
                               plan["window_lines"], plan["tokens_total"],
                               plan["predicted_bytes"], plan["mode"]))
            if plan["would_fail"]:
                return 2
    else:
        print("FOLD not due: predicted post stays under the gate")
    print("QUEUE mode=%s %r"
          % ("execute" if execute else "dry-run", flip_queue(execute)))
    print("BOARD mode=%s %r"
          % ("execute" if execute else "dry-run", flip_board(execute)))
    appended = append(ROWS, TICK, execute)
    print("APPEND mode=%s %r"
          % ("execute" if execute else "dry-run", appended))
    after, new_state = raw_and_state()
    print("STATE after=%dB gate=%d margin=%d tick=%d log=%d"
          % (len(after), state_fold.GATE, state_fold.GATE - len(after),
             new_state["tick"], len(new_state["log"])))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))