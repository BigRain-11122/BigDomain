"""R2568 closeout append: prove the byte-exact round-trip, then mutate.

The state file layout is json.dump(indent=1) with no trailing newline (law
proved at R2561 and re-proved here before any byte moves).
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PATH = os.path.join(ROOT, "src", "os", "state.json")

LINES = [
    "2026-11-08 R2568 VERIFICATION window on the battery the register owed (reconcile-battery-R2567, "
    "pre-registered 613 suites / 4654 criteria at R2567 after it wired os-state-fold-run). Five-silence "
    "at open: git status EMPTY at HEAD 88d6b501 with no index.lock, zero @BigDomain rows in "
    "cph4/evolution-ledger.md, the content-addressed decisions diff read new=0 over the stored baseline "
    "at 273 rows / 164 tokens, the group orders tail unchanged at 2026-11-08 12:06 "
    "(OB-20261108-120628-589 knowledge-only; the 2026-11-09 string is a due date INSIDE a @BigCompute "
    "order, not a new order), benchmarks 2026-11-03 inside the seven-day gate. This CLOSES the two reads "
    "R2567 declared unread rather than inheriting its silence. Registry RE-MEASURED by importing "
    "reconcile_all.SUITES at 613 suites / 4654 criteria with 613 unique names and 613 unique paths, byte "
    "for byte the registered number. LEG 1 RED AND KEPT (qa/reconcile-all-R2568.log, 1030081B): 606/613 "
    "at exactly 4654 criteria in 1530.9s, EIGHT failed assertions across SEVEN suites with TWO INDEPENDENT "
    "BIRTH SITES - the R2557 residue head pin expired at R2567 so every entry flipped EXPIRED/untriaged "
    "(os-residue-triage AC-RTR6, 319 untriaged), and R2567 moved the registry to 613/4654 without "
    "regenerating the matrix doc so six text-coverage suites read a stale document. BOTH BIRTH SITES "
    "REPAIRED ALONE in commit 0b076f20 before any retry: residue re-pinned through the shipped repin tool "
    "from measured live state (305->319 entries, 4 unmatched dropped as no longer live, until R2578, every "
    "status derived by the tool rather than typed) and the doc regenerated stamp-aligned from the R2566 "
    "eligible green leg; both red suites then re-ran 6/6 alone.",
    "2026-11-08 R2568 RETRY GREEN measured not quoted (qa/reconcile-all-R2568-retry.log, 1029889B): RUNNER "
    "PASS, 613/613 suites green, reconcile controls 7/7, 1504.8s, ZERO FAIL suite rows, 613 PASS suite rows, "
    "and an INDEPENDENT recount over their own criteria fields summing to EXACTLY 4654, with the registry "
    "re-read by import matching at 613 / 4654. FOLLOW-UP in the designed order: the dry run read SECTION "
    "matrix FAIL BY DESIGN at 60002B against regenerated 60023B with no byte written while fingerprint "
    "(CLEAN domains=5), profile (byte-identical) and census (DRIFT-CLEAN) all read clean; docs/"
    "sandbox-suite-matrix.md was then regenerated stamp-aligned from THIS round own green leg to 60023B at "
    "613 suites / 4654 criteria with its green line honestly reading 613/613 self-describing, --check read "
    "byte-identical at rc=0, and the four sections re-ran to VERDICT R2568 PASS failing=none (APPENDED "
    "1951B eol_ok=True). DEBT through the shipped writers: reconcile-battery-R2567 closed at its predicted "
    "and measured 177615B -> 177618B (line 312, open 27->26, done 267->268, readback ok) and "
    "product-face-R2568 appended first=yes at 177618B -> 177887B (readback ok) naming the next window a "
    "PRODUCT face on tech head state/queue/tech.md:603 prefix AC-PNDCF1, whose AC-PNDCF1..AC-PNDCF6 were "
    "pinned there at R2565 BEFORE any code. NO successor battery is owed: this window moved no product src "
    "byte and the registry is unmoved at 613 suites / 4654 criteria, which is exactly what the green leg "
    "measured. queue_head read line 603 claimable=11 and queue_floor read FLOOR-MET main=5/5 tech=11/10 "
    "explore=10/10; no queue row was opened or closed, because a verification window writes no board row.",
    "R2568 tokens: local=~11k api=0 api_reason=verification window - five-silence scan with the decisions "
    "and orders faces ACTUALLY read this time instead of inherited, one registry target re-measured by "
    "import on both axes, one full 613-suite leg kept red with both birth sites named, two birth-site "
    "repairs through their shipped tools with both red suites re-run alone, one commit carrying the red leg "
    "plus the repairs and nothing else, one green retry at the pre-registered 4654 criteria with an "
    "independent recount, one designed matrix FAIL, one stamp-aligned regeneration checked byte-identical, "
    "one four-section follow-up to a PASS verdict, one debt row closed and one opened through their shipped "
    "writers, one log fold through the shipped fold face with all 138 tokens preserved, and the "
    "state/export/backlog/heartbeat closeout; zero cloud calls and zero external API touches",
]


def dump(state):
    return json.dumps(state, ensure_ascii=False, indent=1)


def main():
    raw = open(PATH, "rb").read()
    text = raw.decode("utf-8")
    state = json.loads(text)
    proved = dump(state)
    if proved.encode("utf-8") != raw:
        raise SystemExit("E_ROUNDTRIP: dump differs from disk (%d vs %d bytes)"
                         % (len(proved.encode("utf-8")), len(raw)))
    before = len(state["log"])
    state["tick"] = int(state["tick"]) + 1
    state["log"].extend(LINES)
    state["last_decision_rows"] = 273
    out = dump(state).encode("utf-8")
    with open(PATH, "wb") as handle:
        handle.write(out)
    print("ROUNDTRIP-OK bytes=%d tick=%d log=%d->%d after=%d"
          % (len(raw), state["tick"], before, len(state["log"]), len(out)))


if __name__ == "__main__":
    main()