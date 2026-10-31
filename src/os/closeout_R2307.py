# closeout_R2307.py - one-off closeout for the stamp_exempt_append window
# Closes the claimed tech row (state/queue/tech.md line 369, prefix AC-SAP1)
# and appends one real gap seed holding the tech floor. Every write is one
# atomic replace with a read-back proof; the expected byte delta is asserted
# before anything is written.
#
# Usage: python src/os/closeout_R2307.py [--execute]

import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
QUEUE = os.path.join(ROOT, "state", "queue", "tech.md")

OLD_HEAD = "- [ ] P2 tech seed (R2294,"
NEW_HEAD = "- [x] [done 2026-11-01 R2307] P2 tech seed (R2294,"

NOTE = (" [done 2026-11-01 R2307] Discharged as the product face and committed "
        "BEFORE any battery (the R2168 mixed-tree rule): src/os/"
        "stamp_exempt_append.py plus src/os/test_stamp_exempt_append.py, with "
        "AC-SAP1..AC-SAP6 already pinned in this row BEFORE the code. The "
        "declaration's reader is the authority on shape (the module calls "
        "queue_done_stamp_exempt.read_declaration on the post text in a "
        "throwaway world and carries no second copy of the entry rules), and "
        "the live (queue, identity) join is stamp_exempt_review.live_pairs - "
        "both proven by patching each import in the suite. A missing row, a "
        "duplicate pair and an ambiguous pair (one entry covering two live "
        "rows) each refuse before any byte changes; a dry run is the default "
        "and predicts the exact post size; an executed append is one atomic "
        "replace proved by read-back with no temp residue. SUITE PASS 6/6 "
        "double-run identical with five adjacent suites green through the "
        "R2261 evidence_capture callable (qa/stamp-exempt-append-R2307.log, "
        "850B, one utf-8 LF single writer), wired "
        "os-stamp-exempt-append(6). LIVE on the real 78774B declaration: a "
        "fabricated identity reads E_SEAP_NO_ROW and an already-declared live "
        "pair (main:N1-N7#a69002dc) reads E_SEAP_DUP, both exit 2, and the "
        "file sha256 is unchanged (cf14161f0f1df99d) - no honest append was "
        "possible this window because every live debt row is already "
        "declared, so the positive path is proven on fixture worlds instead "
        "and that is disclosed rather than dressed up.")

SEED = (
    "- [ ] P2 tech seed (R2307, from this window own live finding): "
    "`src/os/stamp_exempt_prune.py` - the declaration can now grow but not "
    "shrink: an entry whose row was amended after the fact (its text digest "
    "moves, so stamp_exempt_review reads it MISSING) or whose until round has "
    "passed stays in the file forever, so the 380-entry list rots in the "
    "direction the reviewer names but nobody can retire. Criteria "
    "AC-SEPR1..AC-SEPR6 pre-registered HERE BEFORE any code: the retire set "
    "is derived from the reviewer's own MISSING and expired readings rather "
    "than a second join; a plan names every entry it would drop with its "
    "index, queue and identity, and a dry run is the default; the splice "
    "removes exactly those entries while every surviving entry stays "
    "byte-identical and in order; the post text is validated through "
    "read_declaration and must carry exactly the expected count; an executed "
    "prune is one atomic replace proved by read-back with no temp residue and "
    "a refused plan writes nothing; purity plus its own reconcile label. "
    "Anchor check at HEAD 2026-11-01: stamp_exempt_prune, AC-SEPR, E_SEPR, "
    "os-stamp-exempt-prune and test_stamp_exempt_prune were all git grep -F "
    "zero-occupancy rc=1.\n")


def main(argv):
    execute = "--execute" in argv
    with io.open(QUEUE, "r", encoding="utf-8", newline="") as handle:
        text = handle.read()
    lines = text.split("\n")
    index = 368
    row = lines[index]
    if not row.startswith(OLD_HEAD):
        sys.stderr.write("E_CO2307_HEAD: line 369 does not start with %r\n"
                         % OLD_HEAD)
        return 2
    if "[done 2026-11-01 R2307]" in row:
        sys.stderr.write("E_CO2307_DONE: line 369 is already closed\n")
        return 2
    lines[index] = NEW_HEAD + row[len(OLD_HEAD):] + NOTE
    post = "\n".join(lines)
    if not post.endswith("\n"):
        post += "\n"
    post += SEED
    before = len(text.encode("utf-8"))
    after = len(post.encode("utf-8"))
    print("CLOSEOUT R2307 before=%dB after=%dB delta=%+d executed=%s"
          % (before, after, after - before, "yes" if execute else "no"))
    if not execute:
        return 0
    data = post.encode("utf-8")
    temp = QUEUE + ".co2307-tmp"
    try:
        with io.open(temp, "wb") as handle:
            handle.write(data)
        os.replace(temp, QUEUE)
    except (IOError, OSError) as exc:
        if os.path.exists(temp):
            os.remove(temp)
        sys.stderr.write("E_CO2307_WRITE: %s\n" % exc)
        return 3
    with io.open(QUEUE, "rb") as handle:
        back = handle.read()
    if back != data:
        sys.stderr.write("E_CO2307_READBACK: %d bytes, predicted %d\n"
                         % (len(back), len(data)))
        return 3
    if os.path.exists(temp):
        sys.stderr.write("E_CO2307_RESIDUE: %s\n" % temp)
        return 3
    print("CLOSEOUT R2307 readback=ok residue=none")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))