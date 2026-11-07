"""append_R2522 - append this window's state.json log lines and advance the baseline.

Split in two passes by design: PASS A lands the window narrative plus the round
ledger line BEFORE the third battery leg (the coverage law needs a ledger line
in the same pass as any round line, which is exactly the defect this window
repaired), and PASS B lands the measured battery outcome afterwards.
"""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(BASE, "os", "state.json")
NEW_DEC = ["D-20261107-13", "D-20261107-14", "D-20261107-15",
           "D-20261107-16", "D-20261107-17"]

PASS_A = [
    "2026-11-07 R2522 VERIFICATION window on the battery the register owed "
    "(reconcile-battery-R2521, pre-registered 590 suites / 4516 criteria). "
    "Five-silence scan: git status empty and no index.lock, zero @BigDomain "
    "rows in cph4/evolution-ledger.md, group orders tail unchanged at "
    "2026-11-06 23:46, benchmarks 2026-11-03 inside the seven-day gate, but "
    "the content-addressed decisions diff read 5 new tokens and the queue head "
    "read claimable=10 at line 559. The target was RE-MEASURED before the run "
    "by importing reconcile_all.SUITES: 590 suites and 4516 criteria, byte for "
    "byte the registered note. DECISIONS: the five new tokens are "
    "D-20261107-13..D-20261107-17, every one a group-level batch, fleet or "
    "scheduling row with no BigDomain execution face, so all five are "
    "ACKNOWLEDGED and none is actioned here; D-20261107-14 is worth naming "
    "because it formally reclassifies the S4U task re-registration as a "
    "ceo-pending physical item with zero chase, which is exactly the state of "
    "the carried loop-s4u-reconcile row, so that row stops being an obligation "
    "this loop can discharge and is recorded as a physical item instead.",
    "2026-11-07 R2522 LEG 1 RED AND THE RED LEG KEPT (qa/reconcile-all-R2522.log, "
    "907773B, utf-8, bom=False, crlf=0): 585/590 suites green with SIX failed "
    "assertions across five suites - os-ledger-lines AC-LGR8, os-ledger-archive "
    "AC-LGA7 and AC-LGA8, os-ledger-baseline AC-LGB8, os-ledger-closeout "
    "AC-LGN8, and os-export-driver-queue-face AC-EDQF2 and AC-EDQF5. THE CAUSE "
    "WAS READ, NOT GUESSED: running the shipped reader on the live tree read "
    "rounds_without_ledger: 2521 while the ledger line was present as 'RR2521 "
    "tokens: ...', because the R2521 window wrote a doubled R on four narrative "
    "lines and on its own ledger line, so the coverage law saw round 2521 "
    "carrying no ledger line and four shipped ledger suites read their live "
    "criterion red on an otherwise healthy tree. REPAIR AT THE BIRTH SITE: "
    "shipped src/os/repair_R2522_round_token.py, an idempotent ASCII normaliser "
    "with a --check face that rewrites that one token on exactly five state.json "
    "log lines (5 insertions / 5 deletions, no sentence and no count dropped); "
    "coverage then read VERDICT CLEAN with ledger=2 round=10 other=0, and all "
    "five red suites re-read SUITE PASS 8/8, 8/8, 8/8, 8/8 and 6/6 alone. The "
    "repair was committed ALONE as e0894301 so the retry ran on a committed "
    "tree with an empty git status.",
    "2026-11-07 R2522 LEG 2 RED BUT NARROWER, AND THE SECOND BIRTH SITE NAMED "
    "(qa/reconcile-all-R2522-retry.log, 907643B, utf-8, bom=False, crlf=0, 591 "
    "suite rows, 461 SUITE PASS): the four ledger suites and their five "
    "assertions healed exactly as the repair predicted, and FOUR assertions "
    "named a DIFFERENT birth site - the shipped export document was stale "
    "against state, read as check_export_consistency 20/21 with FAIL "
    "self_drive.substantive_non_idle_mention_lines stored=45 recomputed=49. "
    "That is the honest consequence of the repair itself: four log lines that "
    "had no round token now carry one and became substantive, so the document "
    "had to be re-derived from the repaired state rather than patched. The "
    "second repair is a re-derivation, not a hand edit: src/os/export_R2522.py "
    "supplies this window's CEO lines to the shipped export_R2431 derivation "
    "and the shipped queue face writes the document, after which "
    "check_export_consistency re-read 21/21.",
    "R2522 tokens: local=~18k api=0 api_reason=verification window - five-silence "
    "scan, one registry target re-measured by import, one full 590-suite battery "
    "kept red as evidence, one cause read from the shipped coverage reader "
    "rather than guessed, one birth-site token normaliser shipped and committed "
    "alone, one second battery narrow enough to name the next birth site, one "
    "export re-derivation driver shipped, and the state/export/backlog/heartbeat "
    "closeout; zero cloud calls and zero external API touches",
]


PASS_B = [
    "2026-11-07 R2522 LEG 3 GREEN ON THE COMMITTED REPAIR TREE, measured not "
    "quoted: qa/reconcile-all-R2522-leg3.log is 907470B, utf-8, bom=False, "
    "crlf=0, lone_cr=0, zero SUITE FAIL rows, closing RUNNER PASS (590/590 "
    "suites green, reconcile controls 7/7, 1195.1s), and an independent recount "
    "over the PASS suite rows sums to EXACTLY 4516 criteria - the pre-registered "
    "total matched by measurement. Launched detached and unfiltered through "
    "src/os/battery_stream.py (pid in logs/battery-R2522-leg3.pid) so the "
    "filtering-pipe trap was not re-paid. FOUR FOLLOW-UP SECTIONS in the "
    "designed order: the dry run read SECTION matrix FAIL at on-disk 56795B "
    "against regenerated 56790B with NO byte written while fingerprint read "
    "CLEAN domains=5, profile byte-identical and census DRIFT-CLEAN; "
    "docs/sandbox-suite-matrix.md was then regenerated stamp-aligned from THIS "
    "round own green evidence through src/sandbox/suite_matrix.py --stamp-from "
    "to 56790B at 590 suites / 4516 criteria with its green line honestly "
    "reading 590/590, --check read byte-identical, and the re-run read all four "
    "PASS for VERDICT sandbox-suite-battery PASS failing=none (APPENDED 1982B "
    "eol_ok=True).",
    "2026-11-07 R2522 DEBT AND BOARD: reconcile-battery-R2521 closed through the "
    "shipped debtor at its predicted 153585B -> 153589B (line 247, open 7->6, "
    "done 222->223, readback ok) and product-face-R2522 was appended first=no "
    "through the shipped appender at its predicted 153589B -> 154248B "
    "(readback ok) because this window shipped no product face - the "
    "first=yes append was REFUSED with E_DEBTA_FIRST while product-face-R2521 "
    "still holds that slot, which is the correct refusal and was not worked "
    "around by flipping the flag. NO successor battery is owed: this window "
    "moved no product src byte and the registry is unmoved at 590 suites / "
    "4516 criteria, re-read by import rather than trusted. The next window owes "
    "the PRODUCT face the register names on tech head state/queue/tech.md:559 "
    "prefix AC-PLC1 probe_seam_local_constant_scope, whose criteria were pinned "
    "at R2521 BEFORE any code.",
    "2026-11-07 R2522 honest disclosures: (a) ZERO product points on the "
    "Executive Protocol scale - nothing a CEO could open was built this window "
    "and none is claimed; the deliverable is a green 590/4516 battery, two "
    "birth-site repairs and a matrix document whose evidence column is now "
    "self-describing rather than borrowed from an older leg. (b) The window ran "
    "THREE full batteries (1195.1s green plus 907773B and 907643B red legs) and "
    "overshot its 25-minute budget by more than an hour; it says so rather than "
    "hiding it. (c) BOTH red legs are kept in qa/ and committed, not deleted. "
    "(d) The first red cause was born in R2521 (a doubled R on five log lines); "
    "the second red cause was born in THIS window own repair (four lines became "
    "substantive, which made the export stale) and in a phrase - a narrative "
    "line quoting the literal ledger marker was classified as a ledger line and "
    "silently stopped counting as substantive; both were read from the shipped "
    "reader, not guessed. (e) A date prefix was tried on this round ledger line "
    "and REVERTED because it broke ledger recognition (rounds_without_ledger: "
    "2522) - reported rather than quietly dropped. (f) Docker is absent on this "
    "host so no containerised bring-up is claimed. (g) The real 19.9 debit and "
    "the real msgSecCheck still wait on CEO physical items (merchant id, "
    "mini-program appid/secret). (h) tasks.md was not touched, it is the P-47 "
    "canonical board. (i) The S4U lane re-registration needs an ELEVATED shell "
    "and D-20261107-14 has now formally classified it as a ceo-pending physical "
    "item with zero chase, so it is recorded as a physical item rather than "
    "carried as a loop obligation.",
]


def load():
    with io.open(STATE, encoding="utf-8") as handle:
        return json.load(handle)


def save(data):
    with io.open(STATE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(data, ensure_ascii=False, indent=4) + "\n")


def main(argv):
    pass_a = "--pass-b" not in argv
    data = load()
    if pass_a:
        data["tick"] = 2522
        data["last_decision_rows"] = 210
        known = list(data.get("last_dec_tokens") or [])
        for token in NEW_DEC:
            if token not in known:
                known.append(token)
        data["last_dec_tokens"] = known
        data.setdefault("log", []).extend(PASS_A)
    print("PASS_A" if pass_a else "PASS_B", "tick", data["tick"],
          "log", len(data.get("log") or []))
    if pass_a:
        save(data)
    else:
        data.setdefault("log", []).extend(PASS_B)
        save(data)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))