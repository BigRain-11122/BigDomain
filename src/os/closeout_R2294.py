"""closeout_R2294.py - the R2294 queue and board edits, in one callable.

One-off per-round helper (the house pattern since R2252): it closes the claimed
tech row with its window stamp, seeds the gap row that holds the tech floor,
and marks the board row done while prepending the successor. It writes only the
two files it names, in their own measured layout (tech.md is CRLF, the board is
LF), and prints the byte counts it produced.
"""

import io
import os

REPO = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))

TECH = os.path.join(REPO, "state", "queue", "tech.md")
BOARD = os.path.join(REPO, "src", "os", "backlog.md")

DONE_NOTE = (
    " [done 2026-10-31 R2294] Delivered src/os/stamp_exempt_review.py + "
    "src/os/test_stamp_exempt_review.py: the accepted-stamp declaration is now "
    "read from BOTH sides. MISSING names a declared entry whose "
    "(queue, identity) matches no live debt row (with its declaration entry "
    "index) and UNDECLARED names a live debt row carrying no entry (with file "
    "and line); the split reconciles with queue_done_stamp_exempt's own exempt "
    "and unmatched numbers before any verdict, and a disagreement refuses with "
    "E_SER_COUNT. The gate and the identity law are imported from the two "
    "modules that own them (both proved by patching). A missing declaration "
    "refuses as E_SER_UNPINNED rather than reading a 380-row drift, a malformed "
    "one as E_SER_BAD_DECL, an ambiguous pair as E_SER_AMBIGUOUS and a missing "
    "queue as E_SER_BAD_GATE. SUITE PASS 6/6 double-run with identical "
    "criterion lines, five adjacent suites green "
    "(qa/stamp-exempt-review-R2294.log, 1844B, one utf-8 LF single writer "
    "through the src/os/evidence_capture.py callable), wired "
    "os-stamp-exempt-review(6). LIVE: STAMP EXEMPT REVIEW round=R2294 "
    "declaration=PINNED entries=380 violations=380 matched=380 exempt=380 "
    "expired=0 missing=0 undeclared=0 verdict=NO-DRIFT, with both real files "
    "proved byte-unchanged by the reading. The claim dropped tech claimable to "
    "9, so one real gap row was seeded (stamp_exempt_append, AC-SAP1..AC-SAP6 "
    "pre-registered, five anchors git grep -F zero-occupancy rc=1) and the "
    "gauge closed FLOOR-MET 5/5 10/10 10/10.")

SEED = (
    "- [ ] P2 tech seed (R2294, from this window own live finding): "
    "`src/os/stamp_exempt_append.py` - accepting a NEW closed row still means "
    "hand-editing a 380-entry JSON: the shipped entries were generated one-off "
    "by src/os/stamp_exempt_seed_R2280.py and there is no writer, so a row "
    "accepted after R2280 can only be typed in, with no duplicate check, no "
    "identity check against a live row and no atomic write - exactly the shape "
    "debt_append already fixed for the debt register. Criteria AC-SAP1..AC-SAP6 "
    "pre-registered HERE BEFORE any code: a new entry is rendered in the "
    "declaration own shape and validated through read_declaration rather than "
    "re-deriving it; an identity matching no live debt row, a duplicate "
    "(queue, identity) pair and a second entry for one row are each refused "
    "before any byte changes; append is a dry run by default and prints the "
    "before/after byte counts; an executed append is one atomic replace proved "
    "by read-back with no temp residue; a refused call writes nothing; purity "
    "plus its own reconcile label. Anchor check at HEAD 2026-10-31: "
    "`stamp_exempt_append`, `AC-SAP`, `E_SEAP`, `os-stamp-exempt-append`, "
    "`test_stamp_exempt_append` were all git grep -F zero-occupancy rc=1.")

BOARD_DONE = (
    " [done 2026-10-31 R2294] Discharged as the product face first and "
    "committed BEFORE any battery (the R2168 mixed-tree rule): "
    "src/os/stamp_exempt_review.py + src/os/test_stamp_exempt_review.py "
    "(AC-SER1..AC-SER6 already pinned in the R2280 seed row at "
    "state/queue/tech.md:360 BEFORE the code, fresh zero-occupancy anchor "
    "check at HEAD). SUITE PASS 6/6 double-run identical criterion lines, five "
    "adjacent queue suites green (qa/stamp-exempt-review-R2294.log, 1844B, one "
    "utf-8 LF single writer through evidence_capture), wired "
    "os-stamp-exempt-review(6). LIVE NO-DRIFT over 380 entries / 380 "
    "violations. One real gap row seeded (stamp_exempt_append, "
    "AC-SAP1..AC-SAP6) to hold the tech floor at 10/10. The battery carries to "
    "R2295.")

SUCCESSOR = (
    "- [ ] [carried 2026-10-31 R2294] R2295 first item: THE BATTERY ON THE "
    "COMMITTED TREE, zero product edits until green (the R2168 mixed-tree "
    "rule). This window changed src/os (stamp_exempt_review.py, "
    "test_stamp_exempt_review.py), one runner entry, the tech queue (one row "
    "closed and one seed added), the debt register and state.json, so run the "
    "full reconcile battery on the committed tree with an empty git status "
    "before the run, expecting +1 suite / +6 criteria against R2293 (452 "
    "suites / 3688 criteria) from this window's os-stamp-exempt-review suite - "
    "measure it, and disclose any delta that does not resolve to a named "
    "suite. Then the four follow-up sections through "
    "src/os/battery_followup.py (its matrix section will FAIL first on the "
    "stale doc and must not rewrite it; regenerate with "
    "src/sandbox/suite_matrix.py and re-run). After that the product face "
    "resumes at the tech head, which the claim and the seeded row have moved "
    "past line 360 - re-read it. Also open and needing an ELEVATED shell: "
    "BigDomain-OSLoop reads LogonType=InteractiveToken (fifty-ninth "
    "consecutive disclosure; carried as loop-s4u-reconcile in state/debt.md).")


def edit_tech():
    raw = io.open(TECH, "rb").read().decode("utf-8")
    lines = raw.split("\r\n")
    target = None
    for index, line in enumerate(lines):
        if line.startswith("- [ ] P2 tech seed (R2280"):
            target = index
            break
    if target is None:
        raise SystemExit("E_CLOSE_NO_ROW: the R2280 seed row was not found")
    lines[target] = lines[target].replace(
        "- [ ] P2 tech seed (R2280",
        "- [x] [done 2026-10-31 R2294] P2 tech seed (R2280", 1) + DONE_NOTE
    while lines and lines[-1] == "":
        lines.pop()
    lines.append(SEED)
    lines.append("")
    body = "\r\n".join(lines).encode("utf-8")
    io.open(TECH, "wb").write(body)
    return len(body)


def edit_board():
    raw = io.open(BOARD, "rb").read().decode("utf-8")
    items = raw.split("\n")
    if not items[0].startswith("- [ ] [carried 2026-10-31 R2293] R2294"):
        raise SystemExit("E_CLOSE_NO_ROW: the board head is not the R2294 row")
    rest = items[0].split("]", 1)[1]
    items[0] = "- [x] [carried 2026-10-31 R2293]" + rest + BOARD_DONE
    out = SUCCESSOR + "\n" + "\n".join(items)
    body = out.encode("utf-8")
    io.open(BOARD, "wb").write(body)
    return len(body)


def main():
    tech_bytes = edit_tech()
    board_bytes = edit_board()
    print("CLOSE R2294 tech.md=%dB backlog.md=%dB" % (tech_bytes, board_bytes))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())