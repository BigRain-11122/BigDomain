"""R2559 backlog + heartbeat closeout (one carried row closed, one opened)."""

import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
BACKLOG = os.path.join(REPO, "src", "os", "backlog.md")
HEARTBEAT = os.path.join(REPO, "heartbeat.txt")

DONE_MARK = "[carried 2026-11-08 R2558] R2559 first item"

NEW = (
    "- [ ] [carried 2026-11-08 R2559] R2560 first item: a VERIFICATION window "
    "on the battery the register now names first - reconcile-battery-R2559 at "
    "the pre-registered 609 suites / 4630 criteria, because this window moved "
    "the registry by one row and shipped a document (the R2168 mixed-tree "
    "rule). Re-measure the target by importing reconcile_all.SUITES before "
    "the launch, run the full battery on a CLEAN committed tree with git "
    "status empty, launch it detached through src/os/battery_stream.py with "
    "an explicit --evidence path and NEVER a shell redirection of its stdout "
    "into qa/ (the ps-utf16 trap), keep the red leg if it goes red and commit "
    "a birth-site repair ALONE before any retry, then run the four follow-up "
    "sections through src/os/battery_followup.py (its matrix section FAILS "
    "first by design and must not rewrite the doc; regenerate with "
    "src/sandbox/suite_matrix.py --evidence <leg> --stamp-from "
    "docs/sandbox-suite-matrix.md after) and land the verdict. On green go "
    "back to the product face the queue head names - re-read it with "
    "`python src/os/queue_head.py --head tech`, which this window left at "
    "state/queue/tech.md:597 prefix AC-PNDB1 "
    "probe_seam_name_binding_arm_mixed_residual_alias_attribute_predicate_"
    "scope (criteria AC-PNDB1..AC-PNDB6 pinned in that row THIS window before "
    "any code): a walrus attribute alias records NOTHING (state=None, no "
    "reason), a subscript or call base is published as `?`, a package own "
    "__init__ constant is never joined, and a with-as helper binding reads "
    "attr-missing. NOTE measured many times: a commit that moves the queue "
    "must also re-derive docs/status-export.json and land its queue block "
    "through queue_export_gate_wire --execute. Also open and misc: state.json "
    "stands at 272128B against the 78500B waterline so state_fold --check "
    "reads FOLD-DUE and this build ships only a --check face, so the fold "
    "stays an OWED obligation seeded as state_fold_run (AC-SFOLD1..6); "
    "residue_triage --check --round R2559 reads TRIAGED with untriaged=0 at "
    "rc=0 and the declaration runs until R2569, so no re-pin is due; the open "
    "rows product-face-R2511, R2513, R2515, R2517 and R2522 still overstate "
    "outstanding work and are disclosed rather than hand-closed; and "
    "BigDomain-OSLoop still reads InteractiveToken, which the 2026-09-29 "
    "machine law forbids for every lane task (carried as the ceo-pending "
    "physical item loop-s4u-reconcile, needs an ELEVATED shell)."
)

HEART = (
    "2026-11-08T11:0x+08:00 product window R2559: shipped probe_seam_name_"
    "binding_arm_mixed_residual_alias_attribute_base + suite, 6/6 twice with "
    "5 adjacent suites, registry 609/4630, bounded live leg on both readers "
    "(attr-base-local:node vs attr-not-imported:node.value; ok/b vs "
    "attr-deep:pkg.mod.ATTR); battery owed next at 609/4630\n"
)


def main():
    text = io.open(BACKLOG, encoding="utf-8").read()
    lines = text.split("\n")
    hits = [i for i, row in enumerate(lines) if DONE_MARK in row]
    if len(hits) != 1:
        print("REFUSED E_BL_CLAIM: hits=%d" % (len(hits),))
        return 2
    at = hits[0]
    lines[at] = "- [x] [done 2026-11-08 R2559]" + lines[at][len("- [ ]"):]
    lines.insert(at + 1, NEW)
    payload = "\n".join(lines)
    with io.open(BACKLOG, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
    back = io.open(BACKLOG, encoding="utf-8").read().split("\n")
    ok = (back[at].startswith("- [x] [done 2026-11-08 R2559]")
          and back[at + 1].startswith("- [ ] [carried 2026-11-08 R2559]"))
    with io.open(HEARTBEAT, "a", encoding="utf-8", newline="\n") as handle:
        handle.write(HEART)
    print("backlog %s at=%d rows=%d" % ("OK" if ok else "FAIL", at,
                                        len(back)))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())