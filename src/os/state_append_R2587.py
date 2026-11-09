"""R2587 state append: tick + the round log block, layout proved before
mutation.
"""

import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(ROOT)
STATE = os.path.join(ROOT, "src", "os", "state.json")

LINES = [
    "2026-11-09 R2587 PRODUCT window on the queue head the register named: "
    "state/queue/tech.md:619 prefix AC-PNAB1, whose AC-PNAB1..AC-PNAB6 were "
    "pinned in that row at R2585 BEFORE any code. Five-silence at open: git "
    "status empty, no index.lock, zero @BigDomain rows in "
    "cph4/evolution-ledger.md, the content-addressed D-/C- token scan read 167 "
    "tokens against the stored 200-token baseline with new=0, benchmarks "
    "2026-11-03 inside the seven-day gate, and the queue head claimable=13 with "
    "queue_floor FLOOR-MET 5/5 13/10 10/10. SHIPPED: "
    "src/os/probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_"
    "alias_scope_module_alias_attribute_alias_walrus_relative_branch_scope.py "
    "plus its six-criteria suite, one registry row (624 -> 625 suites, 4720 -> "
    "4726 criteria). A walrus bound inside a module-level if/else body now "
    "resolves and the branch is named on the chain (branch:M@if); the same name "
    "bound on two branches is refused as attr-module-alias-ambiguous:M@else+if "
    "instead of being resolved to either; a function-body walrus keeps the "
    "shipped refusal byte for byte; and the live leg reads four real modules "
    "read-only at 80 loops with no mismatch against the parent. PROOF: suite "
    "PASS 6/6 on the first run and 6/6 TWICE with identical output "
    "(qa/module-alias-walrus-branch-scope-R2587.log, 3450 bytes, crlf=0, "
    "nul=0, bom=False, written by the capture writer rather than a shell "
    "redirection after the ps-utf16 trap was hit on a scratch file), the "
    "parent suite still 6/6, and the limits measured with "
    "src/os/limits_module_alias_walrus_branch_next_R2587.py. BOARD: row 619 "
    "marked done with its DISCHARGED note and ONE successor seed inserted "
    "(AC-PNAC1..AC-PNAC6, elif/with/nested/for), bytes 1835522 -> 1838158, "
    "readback ok.",

    "2026-11-09 R2587 honest disclosures: (a) Executive Protocol points are ONE "
    "product face measurable and testable rather than something a CEO can open "
    "in a browser, and no commercial artefact is claimed, so this is not a 2 "
    "point window on that scale; (b) the suite is SLOW by construction - the "
    "parent live leg costs about 22s per real module and this face repeats it "
    "on both readers - so a full window run takes minutes and the capture had "
    "to print progress to avoid a silent kill, which is named rather than "
    "hidden; (c) an earlier attempt of this same round deadlocked on the "
    "parent face plain (non re-entrant) lock and had to leave a stray spinning "
    "python process that was found at 13000s CPU and killed, and the fix is the "
    "re-entrant lock swap now shipped and proven; (d) the fold, residue_triage "
    "and loop-s4u carries were NOT re-run this window and are not claimed; (e) "
    "the real 19.9 debit and the real msgSecCheck still wait on CEO physical "
    "items.",

    "R2587 tokens: local=~9k api=0 api_reason=single product face on one queue "
    "row - one five-silence scan with the content-addressed decisions scan, one "
    "queue head and floor read, one parent face and suite read, one new probe "
    "module and one six-criteria suite written, one registry row appended, one "
    "limits script measured on four private worlds, two suites proven (own and "
    "parent) with one repeat compared line by line, one board close with one "
    "successor seed, and the state/export/heartbeat closeout; zero cloud calls "
    "and zero external API touches",
]


def main(argv):
    raw = open(STATE, "rb").read()
    text = raw.decode("utf-8")
    state = json.loads(text)
    layout = None
    for indent in (1, 2):
        for trail in ("", "\n"):
            if json.dumps(state, indent=indent, ensure_ascii=False) + trail == text:
                print("LAYOUT PROVED indent=%d trail=%r bytes=%d"
                      % (indent, trail, len(raw)))
                layout = (indent, trail)
                break
        if layout:
            break
    if not layout:
        print("E_R2587_BAD_LAYOUT")
        return 3
    block = state.setdefault("log", [])
    start = len(block)
    block.extend(LINES)
    state["tick"] = int(state.get("tick", 0)) + 1
    new_text = json.dumps(state, indent=layout[0], ensure_ascii=False) + layout[1]
    check = json.loads(new_text)
    if check["log"][start:] != LINES or len(check["log"]) != len(block):
        print("E_R2587_ROUNDTRIP")
        return 4
    execute = "--execute" in argv
    print("APPEND tick=%s log %d -> %d lines, bytes %d -> %d, execute=%s"
          % (state["tick"], start, len(block), len(raw),
             len(new_text.encode("utf-8")), execute))
    if not execute:
        return 0
    folder = os.path.dirname(os.path.abspath(STATE))
    handle, temp = tempfile.mkstemp(dir=folder, prefix=".r2587_")
    try:
        with os.fdopen(handle, "wb") as sink:
            sink.write(new_text.encode("utf-8"))
            sink.flush()
            os.fsync(sink.fileno())
        os.replace(temp, STATE)
    except BaseException:
        try:
            os.unlink(temp)
        except OSError:
            pass
        raise
    back = json.load(open(STATE, encoding="utf-8"))
    print("READBACK tick=%s log_lines=%d ok=%s"
          % (back["tick"], len(back["log"]), back["log"][start:] == LINES))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))