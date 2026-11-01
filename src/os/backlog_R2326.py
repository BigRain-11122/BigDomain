"""R2326 board closeout: close the battery row and carry the product row.

One predicted byte delta, one atomic replace, a read-back proof, no temp
residue. Pure ASCII, stdlib only, no network.
"""

import io
import os

BASE = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
BOARD = os.path.join(BASE, "src", "os", "backlog.md")
TMP = BOARD + ".tmp-r2326"

HEAD = "- [ ] R2326 first item:"

DONE = (" [done 2026-11-01 R2326] Discharged as the battery row on the "
        "committed R2325 tree with zero product edits (the R2168 mixed-tree "
        "rule). RUNNER PASS 470/470 suites plus controls 7/7 in 839.6s with "
        "birth-site TMP RECLAIM 932/932 worlds 326.59 MiB busy=0 failed=0 "
        "(qa/reconcile-all-R2326.log, 787466B, single writer utf-8 LF through "
        "src/os/battery_stream.py), expected criteria total 3796. PREDICTION "
        "RECONCILED BY A NAMED CORRECTION rather than swept: the row predicted "
        "471/3802 'against R2324 (470/3796)', but R2324's own log records "
        "469/469 at criteria 3790 - the parenthetical baseline was the "
        "POST-R2325 state mislabelled as R2324 - so the measured 470/3796 is "
        "exactly +1 suite / +6 criteria against the true baseline, delivered by "
        "the os-followup-retry-history suite this round ran green at 6/6. Four "
        "follow-up sections ran through src/os/battery_followup.py in the "
        "designed order: matrix FAILED first on the stale doc (45005B vs "
        "45098B) and did not rewrite it, src/sandbox/suite_matrix.py "
        "regenerated docs/sandbox-suite-matrix.md to 470 suites / 3796 criteria "
        "(45098B), and the re-run read all four PASS (matrix byte-identical, "
        "fingerprint CLEAN 5 domains, profile --daily --check byte-identical, "
        "census DRIFT-CLEAN), VERDICT R2326 PASS. Fold 620 ran before the "
        "append (76984B -> 70832B, 6 whole round blocks, 7000B reserve, "
        "predicted equal to measured) and state.json closed at 74650B with a "
        "3850B margin. Four new decision tokens D-20261101-15/16/17/18 were "
        "judged and all four read non-execution for this company (D-18 records "
        "BigDomain as no-op). Honest score: a 0-point verification window with "
        "no product face.")

NEW_ROW = (
    "- [ ] R2327 first item: BACK TO THE PRODUCT FACE on the row the reader "
    "names. `python src/os/queue_head.py --head tech` reads line 381 prefix "
    "AC-RWW1 (claimable=10) - the R2305 `review_window_wire` seed, whose "
    "AC-RWW1..AC-RWW6 criteria are already pinned INSIDE that row BEFORE the "
    "code (re-read it rather than trusting this line). Run a fresh "
    "zero-occupancy anchor check at HEAD (`git grep -F`, expecting rc 1) "
    "before writing anything, ship one product face with its suite "
    "(`exempt_review` gains `--window-from-declaration`, mutually exclusive "
    "with `--window`, taking the number from `review_window_decl.resolve` and "
    "refusing UNPINNED/DRIFT/refused before any entry is aged, so a PINNED "
    "declaration can no longer be ignored while readings use another window), "
    "refill the tech floor with one real gap row if the claim drops claimable "
    "to 9, and commit BEFORE any battery (the R2168 mixed-tree rule) - the "
    "battery is then the successor row with a pre-registered target stated "
    "against THIS round's measured 470 suites / 3796 criteria. Note the "
    "established trap: `test_exempt_review.py` asserts "
    "`tuple(parsed.keys()) == ER.REPORT_KEYS`, so any new JSON key must be "
    "added to the module constant, not just emitted. Also open and needing an "
    "ELEVATED shell: BigDomain-OSLoop reads LogonType=InteractiveToken "
    "(eighty-eighth consecutive disclosure; carried as loop-s4u-reconcile in "
    "state/debt.md).\n")


def main():
    with io.open(BOARD, encoding="utf-8") as handle:
        before = handle.read()
    lines = before.split("\n")
    target = lines[0]
    if not target.startswith(HEAD):
        raise SystemExit("E_B2326_HEAD %s" % target[:60])
    lines[0] = "- [x]" + target[len("- [ ]"):] + DONE
    after = NEW_ROW + "\n".join(lines)
    predicted = len(after.encode("utf-8"))
    with io.open(TMP, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(after)
    written = os.path.getsize(TMP)
    if written != predicted:
        os.remove(TMP)
        raise SystemExit("E_B2326_PREDICT %d != %d" % (written, predicted))
    os.replace(TMP, BOARD)
    if os.path.exists(TMP):
        raise SystemExit("E_B2326_TEMP %s" % TMP)
    back = os.path.getsize(BOARD)
    if back != predicted:
        raise SystemExit("E_B2326_READBACK %d != %d" % (back, predicted))
    print("board before=%dB after=%dB R2326 closed, R2327 prepended"
          % (len(before.encode("utf-8")), back))


if __name__ == "__main__":
    main()