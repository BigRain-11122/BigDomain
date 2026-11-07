"""R2524 seed: append ONE tech queue row with criteria pinned BEFORE the
code, for the gap this verification window measured on the live debt
register.

MEASURED at R2524: debt_gate read open_count 8 while four of those open
rows - product-face-R2511, product-face-R2513, product-face-R2515 and
product-face-R2517 - name product windows whose work demonstrably shipped
(R2513 shipped probe_seam_registry, R2515 shipped probe_seam_forwarding_scope,
R2517 shipped probe_seam_lazy_scope, R2519 shipped probe_seam_dynamic_import_scope,
each with its suite in the registry). No reader in src/os names them: the
debt gate only ever ranks the first=yes row, so a first=no row whose work
landed stays OPEN forever and the register slowly tells the CEO that work
is outstanding when it is not. This window declines to hand-close them and
seeds the reading instead.

Writes only state/queue/tech.md, appends one line, utf-8 LF, and reads the
file back to prove the row landed exactly once.
"""

import io
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(BASE)
QUEUE = os.path.join(REPO, "state", "queue", "tech.md")

ROW = (
    "- [ ] P2 tech seed (R2524, from this window own measured limit): "
    "`src/os/debt_stale_open_scan.py` - MEASURED this window that the debt "
    "register can carry an OPEN row whose named work already shipped and no "
    "shipped reader ever names it: at R2524 the gate read open_count 8 while "
    "product-face-R2511, product-face-R2513, product-face-R2515 and "
    "product-face-R2517 each name a product window whose suite is in the "
    "registry (probe_seam_registry, probe_seam_forwarding_scope, "
    "probe_seam_lazy_scope, probe_seam_dynamic_import_scope), because the "
    "gate ranks only the first=yes row. The fix must land with these "
    "criteria pinned BEFORE the code. "
    "AC-DSRC1 the register is read through the SHIPPED debt row law imported "
    "at call time (a patched parser moves the report) and this module carries "
    "no second row parser. "
    "AC-DSRC2 every OPEN row is asked what it names: the round tokens in its "
    "note are taken in order and each is looked up in the SHIPPED round "
    "evidence face, and a row whose every named round reads DISCHARGED is "
    "reported STALE-OPEN with the rounds it named and their evidence. "
    "AC-DSRC3 a row whose named work is genuinely outstanding reads OPEN and "
    "is never promoted to STALE, an UNPINNED or unreadable register refuses "
    "at its own exit code with zero rows, and the STALE word can never be "
    "reached by a missing measurement. "
    "AC-DSRC4 the reading is read-only: it closes nothing, stages no byte, "
    "and the whole-tree digest is byte-identical before and after, with the "
    "report saying CLOSE-BY-HAND so the operator is not misled into thinking "
    "the tool fixed the register. "
    "AC-DSRC5 the CLI exits 0 (clean or stale reported) / 2 (stale found, "
    "when asked to gate) / 3 (missing root) / 5 (bad flags) with a "
    "byte-stable --json over the pinned keys and one trailing LF. "
    "AC-DSRC6 hygiene and registration: pure ASCII stdlib module, no clock, "
    "no network, wired as os-debt-stale-open(6), live reading on the real "
    "register taken this window, and the live STALE count is reported as a "
    "number rather than hidden."
)


def main():
    raw = open(QUEUE, "rb").read()
    text = raw.decode("utf-8")
    before = len(text.splitlines())
    if "debt_stale_open_scan" in text:
        print("REFUSED already seeded")
        return 2
    body = text
    if not body.endswith("\n"):
        body += "\n"
    body += ROW + "\n"
    with io.open(QUEUE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(body)
    back = open(QUEUE, "rb").read().decode("utf-8")
    after = len(back.splitlines())
    ok = (back.count("debt_stale_open_scan") == 1 and after == before + 1
          and back.endswith("\n") and "\r" not in back)
    print("SEED lines %d->%d once=%s lf_only=%s"
          % (before, after, back.count("debt_stale_open_scan") == 1,
             "\r" not in back))
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main())