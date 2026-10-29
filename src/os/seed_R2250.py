# seed_R2250.py - append one real tech-queue seed after the R2250 claim.
# The floor gauge read tech 9/10 once the head row was claimed, so the
# standing seeding duty applies. The gap is not manufactured: the battery
# follow-up sections exist as four near-identical per-round scripts
# (battery_followup_R2235 / _R2239 / _R2247 / _R2249) that each re-implement
# the same four sections, so the next window has one callable to write.
import io
import os
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     "..", ".."))
QUEUE = os.path.join(ROOT, "state", "queue", "tech.md")

ROW = (
    "- [ ] P2 tech seed (R2250): battery follow-up as one callable - the four "
    "post-battery sections (suite-matrix regeneration and read-back, "
    "fingerprint --chain --check, runner profile --daily --check, writer "
    "census re-freeze then --check) today live in four per-round scripts "
    "(src/os/battery_followup_R2235.py, _R2239.py, _R2247.py, _R2249.py) that "
    "each re-implement the same four sections and differ only by evidence "
    "path and label, so a defect fixed in one round's copy can stay broken in "
    "the next. Criteria prefix AC-BFU1..AC-BFU6 (pre-registered here BEFORE the "
    "code): AC-BFU1 sections(root, label, round_no) returns the four pinned "
    "section names in order and reports each outcome as PASS/FAIL with its "
    "own one-line detail; AC-BFU2 the matrix section regenerates and reads "
    "back byte-identical, and a mismatch is FAIL with both byte counts rather "
    "than a silent rewrite; AC-BFU3 the follow-up writes nothing outside the "
    "evidence file it is given (tmp world listing unchanged, shipped config "
    "unchanged); AC-BFU4 a missing tool or unreadable matrix is FAIL with its "
    "error code, never fail-open PASS; AC-BFU5 CLI exits 0 only when all four "
    "sections PASS, 2 when any FAILs, 5 on bad flags, and --json carries the "
    "pinned report keys byte-stably; AC-BFU6 source is pure ASCII, stdlib "
    "only, zero network, and the four legacy per-round copies are proven "
    "byte-wider than the new callable before they are retired (a retirement "
    "is a separate window with its own evidence).\n"
)


def main():
    with io.open(QUEUE, "r", encoding="utf-8", newline="") as handle:
        text = handle.read()
    if "AC-BFU1" in text:
        raise SystemExit("seed already present")
    if not text.endswith("\n"):
        text += "\n"
    with io.open(QUEUE, "w", encoding="utf-8", newline="") as handle:
        handle.write(text + ROW)
    print("SEED appended bytes=%d" % len(text.encode("utf-8")))
    return 0


if __name__ == "__main__":
    sys.exit(main())