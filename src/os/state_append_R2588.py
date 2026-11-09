"""R2588 state append: tick + the round log block, layout proved before
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
    "2026-11-09 R2588 PRODUCT window on the queue head the register named: "
    "state/queue/tech.md:621 prefix AC-PNAC1, whose AC-PNAC1..AC-PNAC6 were "
    "pinned in that row at R2587 BEFORE any code. Five-silence at open: git "
    "status empty, no index.lock, zero @BigDomain rows in "
    "cph4/evolution-ledger.md, the content-addressed D-/C- scan read 167 "
    "tokens with new=0, benchmarks 2026-11-03 inside the seven-day gate, and "
    "the queue head claimable=13 with queue_floor FLOOR-MET 5/5 13/10 10/10. "
    "SHIPPED: src/os/probe_seam_name_binding_arm_mixed_residual_alias_"
    "attribute_import_alias_scope_module_alias_attribute_alias_walrus_"
    "relative_branch_elif_with_scope.py plus its six-criteria suite, one "
    "registry row (625 -> 626 suites, 4726 -> 4732 criteria, recounted by "
    "importing reconcile_all.SUITES with 626 unique names and 626 unique "
    "paths). A walrus bound inside a module-level elif section resolves and "
    "the elif is named as branch:M@elif; a walrus inside a module-level with "
    "body resolves and names branch:M@with; a for body and a branch nested "
    "inside another branch keep the shipped refusal "
    "attr-module-alias-unbound:M.HW and publish NO branch read; and an "
    "elif/else pair is refused as attr-module-alias-ambiguous:M@elif+else "
    "rather than resolved to either. PROOF: suite PASS 6/6 on the first run "
    "and 6/6 TWICE with identical output (qa/module-alias-walrus-elif-with-"
    "scope-R2588.log, 7104 bytes, legs written by the capture writer rather "
    "than a shell redirection), the R2587 parent suite still 6/6, the bounded "
    "live leg reads 2 real modules read-only at 49 loops with no mismatch "
    "against the parent, and the SAME fixture is measured on both readers "
    "(ok/b here against refused/attr-module-alias-unbound:M.HW there). BOARD: "
    "row 621 marked done with its DISCHARGED note and ONE successor seed "
    "inserted (AC-PNAD1..AC-PNAD6, while/match), bytes 1838158 -> 1841513, "
    "readback ok, queue head now line 623 prefix AC-PNAD1 claimable=13 and "
    "queue_floor still FLOOR-MET.",

    "2026-11-09 R2588 DEBT AND HONEST DISCLOSURES: product-face-R2586 was "
    "still open first=yes because the R2587 product window shipped the work it "
    "named (a product face on queue head 619 prefix AC-PNAB1) but never closed "
    "the row and never opened its own; this window closed it THROUGH the "
    "shipped writer at its predicted and measured byte count (open 36 -> 35, "
    "done 286 -> 287, readback ok) and then appended reconcile-battery-R2588 "
    "first=yes at the pre-registered 626 suites / 4732 criteria, because this "
    "window moved product src bytes and the R2168 mixed-tree rule puts the full "
    "battery on the committed tree BEFORE any further product byte. Honest "
    "disclosures: (a) ONE product face measurable and testable, not something "
    "a CEO can open in a browser, so this is not a 2 point window on the "
    "Executive Protocol scale; (b) the battery was NOT run this window - it is "
    "owed first thing next window and the suite matrix document is therefore "
    "stale at its R2586 numbers until that follow-up regenerates it, which is "
    "named rather than hidden; (c) the live leg is bounded to TWO real modules "
    "because this face re-reads the parent rather than replacing it, so the leg "
    "is about agreement, not coverage; (d) the fold, residue_triage and "
    "loop-s4u carries were NOT re-run this window and are not claimed; (e) the "
    "real 19.9 debit and the real msgSecCheck still wait on CEO physical items "
    "(merchant id, mini-program appid/secret); (f) tasks.md was not touched, "
    "it is the P-47 canonical board; (g) BigDomain-OSLoop still reads "
    "InteractiveToken and needs an ELEVATED shell (carried ceo-pending "
    "physical item loop-s4u-reconcile).",

    "R2588 tokens: local=~26k api=0 api_reason=product window - one "
    "five-silence scan with the content-addressed decisions scan, the group "
    "orders tail and the ledger face actually read, one debt gate read naming "
    "the claim, one queue head and floor read, one re-measure of the four "
    "shapes that row named before any code, one new probe face and one "
    "six-criteria suite written, one registry row appended and recounted by "
    "import, two suite legs compared byte for byte plus the parent suite as the "
    "adjacent reading, one successor limits script measured on four private "
    "worlds, one board row closed with one seed, one debt row closed and one "
    "opened through their shipped writers, and the state/export closeout; zero "
    "cloud calls and zero external API touches",
]


def main(argv):
    raw = open(STATE, "rb").read()
    text = raw.decode("utf-8")
    state = json.loads(text)
    layout = None
    for indent in (1, 2):
        for trail in ("", "\n"):
            if json.dumps(state, indent=indent,
                          ensure_ascii=False) + trail == text:
                print("LAYOUT PROVED indent=%d trail=%r bytes=%d"
                      % (indent, trail, len(raw)))
                layout = (indent, trail)
                break
        if layout:
            break
    if not layout:
        print("E_R2588_BAD_LAYOUT")
        return 3
    block = state.setdefault("log", [])
    start = len(block)
    block.extend(LINES)
    state["tick"] = int(state.get("tick", 0)) + 1
    new_text = json.dumps(state, indent=layout[0],
                          ensure_ascii=False) + layout[1]
    check = json.loads(new_text)
    if check["log"][start:] != LINES or len(check["log"]) != len(block):
        print("E_R2588_ROUNDTRIP")
        return 4
    execute = "--execute" in argv
    print("APPEND tick=%s log %d -> %d lines, bytes %d -> %d, execute=%s"
          % (state["tick"], start, len(block), len(raw),
             len(new_text.encode("utf-8")), execute))
    if not execute:
        return 0
    folder = os.path.dirname(os.path.abspath(STATE))
    handle, temp = tempfile.mkstemp(dir=folder, prefix=".r2588_")
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