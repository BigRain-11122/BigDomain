"""R2564 backlog surgery and heartbeat: close the carried row, seed R2565.

Reads src/os/backlog.md as bytes, rewrites line 0 in place (the carried row
discharged by this window) and prepends the next carried row, then writes the
heartbeat line. A read-back refuses when either edit did not land.
"""

import io
import os
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     "..", ".."))
BACKLOG = os.path.join(ROOT, "src", "os", "backlog.md")
HEART_PATH = os.path.join(ROOT, "heartbeat.txt")

DONE = (
    "- [x] [done 2026-11-08 R2564] R2564 VERIFICATION window on the battery the "
    "register named first (reconcile-battery-R2563, pre-registered 611 suites / "
    "4642 criteria, re-measured by importing reconcile_all.SUITES before the "
    "launch and matching byte for byte). Five-silence clean at open; debt gate "
    "CLAIM-FIRST. A DUPLICATE LAUNCH happened and is disclosed: the first "
    "detached leg was misread as dead, a second battery was started on the same "
    "evidence path, both were confirmed live by command line, the older tree "
    "was killed and one writer kept; the killed leg's parent wrote a PARTIAL "
    "574130B file carrying one FAIL suite row which is not this round evidence. "
    "GREEN LEG MEASURED: qa/reconcile-all-R2564.log 1026305B at the green leg "
    "and 1028256B after the 1951B follow-up block, utf-8 bom=False crlf=0 "
    "lone_cr=0 nul=0, RUNNER PASS (611/611 suites green, controls 7/7, "
    "1727.0s), zero FAIL rows, independent recount over 611 pass rows summing "
    "to EXACTLY 4642. Follow-up: matrix FAIL first BY DESIGN at 59642B against "
    "59700B with no byte written, stamp-aligned regeneration through "
    "suite_matrix.py --stamp-from to 59700B with --check byte-identical, then "
    "four sections PASS for VERDICT R2564 PASS failing=none (APPENDED 1951B "
    "eol_ok=True); my first render omitted --stamp-from and was repaired in "
    "this window rather than committed. DEBT: reconcile-battery-R2563 closed "
    "at 175984B -> 175987B (open 26->25, done 263->264, readback ok), "
    "product-face-R2564 appended first=yes at 175987B -> 176429B naming the "
    "next window a PRODUCT face on tech head line 601 prefix AC-PNDCE1; no "
    "successor battery is owed because no product src byte moved and the "
    "registry is unmoved at 611/4642."
)

NEW = (
    "- [ ] [carried 2026-11-08 R2564] R2565 first item: the PRODUCT face the "
    "register names at tech head state/queue/tech.md:601 prefix AC-PNDCE1 "
    "probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_"
    "scope_from_scope, whose AC-PNDCE1..AC-PNDCE6 were pinned in that row at "
    "R2563 BEFORE any code: a module bound by `from pkg import helper` reads "
    "attr-base-local:helper, a helper constant declared ONLY inside a function "
    "body reads attr-plain-import, and a with call-returning-module() as m "
    "binding reads attr-with-as. Re-read the head with `python "
    "src/os/queue_head.py --head tech` and re-check the five pinned anchors at "
    "zero occupancy BEFORE any code, then ship the face plus its own suite, "
    "move the registry by one row recounted by import, regenerate "
    "docs/sandbox-suite-matrix.md from the eligible R2564 battery leg with "
    "--stamp-from, close the row with its DISCHARGED note and seed one row "
    "from this window own measured limit. NOTE measured many times: a commit "
    "that moves the queue must also re-derive docs/status-export.json and land "
    "its queue block through queue_export_gate_wire --execute. Also open and "
    "misc: state.json reads far past the 78500B waterline so state_fold "
    "--check reads FOLD-DUE and its layout reader still refuses this file, so "
    "the fold stays an OWED obligation seeded as state_fold_run (AC-SFOLD1..6); "
    "the open rows product-face-R2511, R2513, R2515, R2517 and R2522 still "
    "overstate outstanding work and were disclosed rather than hand-closed; "
    "queue_row --check still reads pre-existing VIOLATIONS on rows that predate "
    "this window; and BigDomain-OSLoop still reads InteractiveToken, which the "
    "2026-09-29 machine law forbids for every lane task (carried as the "
    "ceo-pending physical item loop-s4u-reconcile, needs an ELEVATED shell)."
)

HEART_LINE = (
    "tick 2564 2026-11-08 R2564 verification window: the owed 611-suite "
    "battery closed GREEN with 4642 criteria recounted exactly, matrix "
    "regenerated stamp-aligned at 59700B and byte-identical, follow-up four "
    "sections PASS, no successor battery owed, next window takes the AC-PNDCE1 "
    "product face at tech head line 601\n"
)


def main():
    raw = io.open(BACKLOG, "rb").read()
    text = raw.decode("utf-8")
    lines = text.split("\n")
    already = lines[0].startswith("- [ ] [carried 2026-11-08 R2564]")
    if not already:
        if not lines[0].startswith("- [ ] [carried 2026-11-08 R2563]"):
            print("REFUSE: line 0 is neither the carried row nor this round row")
            return 2
        lines[0] = DONE
        lines.insert(0, NEW)
        io.open(BACKLOG, "wb").write("\n".join(lines).encode("utf-8"))
    back = io.open(BACKLOG, encoding="utf-8").read().split("\n")
    ok = (back[0].startswith("- [ ] [carried 2026-11-08 R2564]")
          and back[1].startswith("- [x] [done 2026-11-08 R2564]"))
    io.open(HEART_PATH, "wb").write(HEART_LINE.encode("utf-8"))
    print("BACKLOG lines=%d already=%s ok=%s bytes=%d"
          % (len(back), already, ok, len(io.open(BACKLOG, "rb").read())))
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main())