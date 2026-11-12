"""Close the R2684 carried row and carry the next product face (R2684 window).

The window adopted the battery leg R2683 launched, closed reconcile-battery-R2682
green, honoured the R2614 discipline and owed NO successor battery, so the next
window goes back to a PRODUCT face on the queue head the debt gate now names.
"""

import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
BOARD = os.path.join(ROOT, "src", "os", "backlog.md")

OLD_PREFIX = "- [ ] [carried 2026-11-13 R2683] R2684 first item: "

NEW_PREFIX = (
    "- [x] [done 2026-11-13 R2684] R2684 first item (DISCHARGED this window): "
    "DISCHARGED: the R2683 leg was ADOPTED by its evidence path "
    "qa/reconcile-all-R2683.log rather than relaunched, the pid chain (99984) "
    "was gone by command line before any byte was read, and the stream closed on "
    "RUNNER PASS (658/658 suites green, reconcile controls 7/7, 2990.1s) with "
    "BATTERY rc=0 2992.2s after TMP RECLAIM 697/697 at 241.16 MiB. MEASURED on "
    "bytes: 1122545B, utf-8, bom=False, crlf=0, lone_cr=0, nul=0, 8844 lines, "
    "658 PASS suite rows carrying 658 UNIQUE names with ZERO FAIL rows and an "
    "INDEPENDENT criteria recount summing to EXACTLY 4924; the registry was "
    "re-measured by import at 658 suites / 4924 criteria / 658 unique names / "
    "658 unique paths, byte for byte the registered number. R2614 DISCIPLINE "
    "OWED AND HONOURED: two closeout commits (eb2bbb9d, 6d66183e) landed UNDER "
    "the leg, so the write-sensitive set was re-run on the FINAL committed tree "
    "and its FIRST pass read THREE reds (artifact-disk-text-readability, "
    "evidence-name-text-coverage, stamp-text-coverage, each rc=1) whose cause "
    "was read off the shipped check own line and not guessed - the doc recorded "
    "qa/reconcile-all-R2680.log while the check resolved qa/reconcile-all-R2683.log, "
    "an evidence-face mismatch rather than content drift - after which the doc "
    "was regenerated STAMP-ALIGNED from THIS round own green leg to 69045B at "
    "658 suites / 4924 criteria with its green line honestly reading 658/658, "
    "--check read byte-identical at rc=0, and the SAME set re-ran at "
    "rc-failures=0 over FOURTEEN suites (qa/write-sensitive-R2684.log, 1548B) "
    "with seven of them printing no PASS line beyond their rc, named rather than "
    "implied. FOLLOW-UP in the designed order: designed matrix FAIL FIRST at "
    "on-disk 69049B against regenerated 69045B with NO byte written while "
    "fingerprint read CLEAN domains=5, profile byte-identical and census "
    "DRIFT-CLEAN, then the verdict append landed VERDICT R2684 PASS failing=none "
    "(APPENDED 1951B eol_ok=True). DEBT through the shipped writers: "
    "reconcile-battery-R2682 closed at its predicted and measured 215656B -> "
    "215659B (line 401, open 45->44, done 338->339, readback ok) and "
    "product-face-R2684 opened first=yes at 215659B -> 216097B naming the next "
    "window a PRODUCT face on queue head state/queue/tech.md line 680 prefix "
    "AC-PNAL1 while queue_head reads claimable=14 and queue_floor FLOOR-MET "
    "5/5, 14/10, 10/10; NO successor battery is owed because this window moved "
    "no product src byte and the registry is unmoved at 658/4924 re-measured by "
    "import. HONEST: ZERO product points - a green battery is evidence, not "
    "something a CEO can open, and every P-47 face still waits on CEO physical "
    "pieces (merchant id, mini-program appid/secret); the leg was authored by "
    "the PREVIOUS window and is adopted by evidence path; the one-off measure "
    "and write-sensitive scripts in tmp/ are DELETED before the commit rather "
    "than staged; Docker is absent on this host; tasks.md was not touched, it is "
    "the P-47 canonical board; BigDomain-OSLoop still reads InteractiveToken and "
    "needs an ELEVATED shell for its S4U re-registration (carried ceo-pending "
    "physical item loop-s4u-reconcile). ORIGINAL ROW TEXT: "
)

ROW = (
    "- [ ] [carried 2026-11-13 R2684] R2685 first item: a PRODUCT face on the "
    "queue head the debt register now names - product-face-R2684 first=yes, "
    "state/queue/tech.md line 680 prefix AC-PNAL1, criteria AC-PNAL1..AC-PNAL6 "
    "pinned in that row at R2682 BEFORE any code. Re-read the row with "
    "`python src/os/queue_head.py --head tech` rather than trusting this line "
    "(claimable=14, floor FLOOR-MET 5/5 14/10 10/10), run a fresh zero-occupancy "
    "anchor check at HEAD before any code, measure the row own limit on private "
    "worlds BEFORE writing the face, ship ONE face with its pre-registered suite "
    "behind the shipped reading, prove it twice through the shipped capture "
    "callable with an identical digest, run the adjacent probe suites, and add a "
    "bounded live leg that measures the SAME fixture on BOTH readers. NO "
    "successor battery is owed at open: R2684 moved no product src byte and the "
    "registry is unmoved at 658 suites / 4924 criteria (re-measured by import), "
    "but this product window WILL move the registry by one row, so a battery on "
    "the committed tree becomes owed BEFORE the next product byte (the R2168 "
    "mixed-tree rule). ALSO carried: state_io.ITEM_INDENT reads 16 against this "
    "file own 2; Docker is absent on this host; tasks.md is the P-47 canonical "
    "board and is not ours to edit; and BigDomain-OSLoop still reads "
    "InteractiveToken, which the 2026-09-29 machine law forbids for every lane "
    "task (carried ceo-pending physical item loop-s4u-reconcile, needs an "
    "ELEVATED shell).\n\n"
)


def main():
    with io.open(BOARD, "rb") as handle:
        raw = handle.read()
    text = raw.decode("utf-8")
    if "done 2026-11-13 R2684" in text:
        print("E_BOARD_EXISTS already closed")
        return 2
    if OLD_PREFIX not in text:
        print("E_BOARD_NO_ROW the carried R2683 prefix was not found")
        return 2
    if not text.startswith(OLD_PREFIX):
        print("E_BOARD_NOT_TOP the carried row is not the first line")
        return 2
    updated = ROW + text.replace(OLD_PREFIX, NEW_PREFIX, 1)
    payload = updated.encode("utf-8")
    print("BOARD predicted bytes=%d -> %d" % (len(raw), len(payload)))
    with io.open(BOARD, "wb") as handle:
        handle.write(payload)
        handle.flush()
    with io.open(BOARD, "rb") as handle:
        if handle.read() != payload:
            print("E_BOARD_READBACK")
            return 3
    print("BOARD written bytes=%d -> %d readback=ok" % (len(raw), len(payload)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
