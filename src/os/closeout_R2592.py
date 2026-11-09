"""R2592 closeout: heartbeat stamp and one backlog row, both derived on disk."""

import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
HEART = os.path.join(REPO, "heartbeat.txt")
BACKLOG = os.path.join(REPO, "src", "os", "backlog.md")

STAMP = "2026-11-09 17:40:00"

ROW = (
    "- [x] [done 2026-11-09 R2592] R2592 PRODUCT window on the queue head "
    "state/queue/tech.md:625 prefix AC-PNAE1 (criteria AC-PNAE1..AC-PNAE6 "
    "pinned there at R2590 BEFORE any code). SHIPPED "
    "src/os/probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_"
    "alias_scope_module_alias_attribute_alias_walrus_relative_branch_elif_"
    "with_while_match_while_else_nested_scope.py plus its six-criteria suite: a "
    "walrus in a module-level `while` `else` section resolves and is named "
    "`branch:M@while_else`, a `match` nested one level in a `while` body "
    "resolves and is named `branch:M@while>case`, two `while` bodies binding "
    "one name refuse as `attr-module-alias-ambiguous:` naming BOTH, and a `for` "
    "body, a `with` body nested in a `while` and a two-deep branch keep the "
    "shipped refusal with no branch read. The four limits were MEASURED before "
    "any code (src/os/limits_module_alias_walrus_while_else_nested_R2592.py) "
    "and the successor row was MEASURED after it "
    "(src/os/limits_module_alias_walrus_while_else_nested_next_R2592.py). "
    "PROOF: SUITE PASS 6/6 on the first run and 6/6 TWICE identical plus the "
    "R2590 parent suite green (qa/module-alias-walrus-while-else-nested-scope-"
    "R2592.log, 6852B, bom=False, crlf=0, digest ED312CE499372C99, fails=0) "
    "through a detached capture after an inline launch was killed by the "
    "five-minute shell silence limit. REGISTRY 627/4738 -> 628/4744 recounted "
    "by import; matrix designed FAIL then stamp-aligned regeneration to 63757B "
    "checked byte-identical with green honestly 627/628. BOARD: row 625 closed "
    "at its measured 1845206B -> 1848921B with AC-PNAF1..AC-PNAF6 seeded at "
    "line 627; queue_head 627 claimable=13, queue_floor FLOOR-MET 5/5 13/10 "
    "10/10. DEBT: product-face-R2591 closed, reconcile-battery-R2592 opened "
    "first=yes at 628/4744, product-face-R2592 opened first=no. STATE: folded "
    "at a true round-block boundary (fold 661, items 14..23) 78274B -> 68207B "
    "with 8 tokens preserved, then appended to 75882B FOLD-CLEAR margin 2618. "
    "HONEST: two product points, nothing a CEO could newly open; every P-47 "
    "item still waits on CEO physical pieces.")


def main():
    raw = io.open(HEART, "rb").read()
    text = raw.decode("utf-8")
    newline = "\r\n" if "\r\n" in text else "\n"
    lines = text.split(newline)
    while lines and lines[-1] == "":
        lines.pop()
    lines[-1] = STAMP
    io.open(HEART, "wb").write((newline.join(lines) + newline).encode("utf-8"))
    print("HEARTBEAT %s" % STAMP)

    board_raw = io.open(BACKLOG, "rb").read()
    board = board_raw.decode("utf-8")
    if ROW in board:
        print("BACKLOG already carries this row")
        return 0
    io.open(BACKLOG, "wb").write((ROW + "\n" + board).encode("utf-8"))
    back = io.open(BACKLOG, encoding="utf-8").read()
    ok = back.startswith(ROW)
    print("BACKLOG prepended ok=%s bytes %d -> %d"
          % (ok, len(board_raw), len(back.encode("utf-8"))))
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main())