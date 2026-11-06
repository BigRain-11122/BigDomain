"""R2502 board row: prepend this window's summary to src/os/backlog.md."""

import io
import sys

P = "src/os/backlog.md"
ROW = (
    "- [x] [done 2026-11-07 R2502] R2502 PRODUCT window on the tech head the "
    "register named (state/queue/tech.md:538 prefix AC-PLR1 "
    "patterns_label_readability, criteria AC-PLR1..AC-PLR6 pinned in that row "
    "at R2494 BEFORE any code). Five-silence scan at open was clean at HEAD "
    "a4393852; debt_gate read OPEN-NONE and queue_head named tech line 538 "
    "claimable=10. SHIPPED src/os/patterns_label_readability.py plus its "
    "suite: reading() asks unicodedata for every non-ASCII codepoint of every "
    "string label at CALL time - a broken codepoint or a script bucket no "
    "other label in the same file carries is SUSPECT with its position, its "
    "U+XXXX and its Unicode name - gate() names the first suspect as "
    "E_PLR_SUSPECT with its label key, and publish(labels, render) refuses to "
    "call the renderer on a suspect file while a clean file reaches it "
    "untouched. HONEST: the shipped tree reads CLEAN on every label because "
    "the R2494 note's mojibake was a console decoding artifact, so detection "
    "is proved on fixtures and NOT claimed as a live catch. PROOF: SUITE PASS "
    "6/6 TWICE identical plus three adjacent suites green "
    "(qa/patterns-label-readability-R2502.log 4773B legs=2 identical=True "
    "fails=0 adjacent=3) and a live reading with the patterns digest unchanged "
    "(qa/patterns-label-readability-live-R2502.log); the clean parity leg "
    "drives the REAL suite_matrix.render through publish() and gets the "
    "artifact byte for byte. FIRST LEG WAS RED on AC-PLR3 byte-identity "
    "because the new registry row moved the registry - repaired by "
    "stamp-aligned regeneration from qa/reconcile-all-R2500.log, not by "
    "loosening the assertion. REGISTRY 579/4450 -> 580/4456; matrix restamped "
    "to 55718B with --check byte-identical and a green line honestly reading "
    "578/580. DEBT: reconcile-battery-R2502 appended first=no (136171B -> "
    "136574B, readback ok), so the next window owes the battery on the "
    "committed tree before any further product byte; the older "
    "reconcile-battery-R2501 row is still open beside it and is disclosed "
    "rather than merged away.\n"
)


def main():
    raw = io.open(P, "rb").read()
    text = raw.decode("utf-8")
    newline = "\r\n" if "\r\n" in text[:200] else "\n"
    row = ROW if newline == "\n" else ROW.replace("\n", newline)
    if text.startswith("- [x] [done 2026-11-07 R2502]"):
        print("FAIL already prepended")
        return 2
    io.open(P, "w", encoding="utf-8", newline="").write(row + text)
    back = io.open(P, encoding="utf-8").read()
    ok = back.startswith("- [x] [done 2026-11-07 R2502]")
    print("prepended=%s bytes=%d newline=%r"
          % (ok, len(back.encode("utf-8")), newline))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())