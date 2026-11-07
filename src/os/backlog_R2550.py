"""R2550 backlog closeout: mark the carried R2549 row done and prepend the next
window own carried row (the product face the queue head names).
"""
import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
BACKLOG = os.path.join(BASE, "backlog.md")

OLD_HEAD = "- [ ] [carried 2026-11-08 R2549]"
NEW_HEAD = "- [x] [done 2026-11-08 R2550] [was carried 2026-11-08 R2549]"

ROW = (
    "- [ ] [carried 2026-11-08 R2550] R2551 first item: a PRODUCT face on the "
    "tech head the register now names - state/queue/tech.md:587 prefix AC-PNDP1 "
    "probe_seam_name_binding_nested_arm_mixed_scope, criteria AC-PNDP1..AC-PNDP6 "
    "pinned in that row at R2549 BEFORE any code. The measured limit, taken from "
    "the nested exhaustive face own reader: (1) an arm that binds the name "
    "DIRECTLY and also contains a nested guard reads mixed:<arm> and resolves "
    "nothing even when the direct value and every nested leaf agree; (2) a try "
    "nested under an arm carrying an else or a finally reads incomplete:<group> "
    "even when every handler arm agrees and the else rebinds the same literal; "
    "(3) a with-as key inside an arm reads non-literal:<arm> and is never named "
    "with-as, so the reason it was refused is hidden. Product: ONE reading that "
    "merges a direct arm binding with its nested tree when they agree on ONE "
    "literal, treats an else rebinding the same literal as coverage while an "
    "else binding nothing stays partial, and NAMES a with-as binding as "
    "with-as:<arm> rather than a shape word. Prove the six criteria twice with "
    "identical output through the shipped capture callable, run the adjacent "
    "probe suites, and add a live leg on the real tree with the same fixtures "
    "measured on BOTH readers. NOTE measured many times: a commit that moves the "
    "queue must also re-derive docs/status-export.json and land its queue block "
    "through queue_export_gate_wire --execute. Also open and misc: state.json "
    "stands at 210084B against the 78500B waterline so state_fold --check reads "
    "FOLD-DUE and this build of the tool ships only a --check face, so the fold "
    "stays an OWED obligation seeded as state_fold_run (AC-SFOLD1..6); and "
    "BigDomain-OSLoop still reads InteractiveToken, which the 2026-09-29 machine "
    "law forbids for every lane task (carried as the ceo-pending physical item "
    "loop-s4u-reconcile, needs an ELEVATED shell)."
)


def main():
    text = io.open(BACKLOG, encoding="utf-8").read()
    if not text.startswith(OLD_HEAD):
        print("FAIL head: %r" % text[:60])
        return 2
    body = NEW_HEAD + text[len(OLD_HEAD):]
    body = ROW + "\n" + body
    with io.open(BACKLOG, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(body)
    back = io.open(BACKLOG, encoding="utf-8").read()
    ok = (back.startswith("- [ ] [carried 2026-11-08 R2550]")
          and NEW_HEAD in back and back.count("R2551 first item") == 1
          and "\r" not in back)
    print("BACKLOG %s lines=%d bytes=%d"
          % ("OK" if ok else "FAIL", len(back.splitlines()),
             len(back.encode("utf-8"))))
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main())