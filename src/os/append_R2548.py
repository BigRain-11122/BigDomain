"""R2548 closeout append: a verification window that moved no product byte.

The shipped state_fold layout reader still refuses this file and the shipped
state_fold.py offers ONLY a --check face, so the append is a PROVED
load+dump round-trip: the bytes are read, decoded, re-encoded and compared
byte for byte BEFORE any mutation, and only then are the tick and the log
rows written.
"""
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
STATE = os.path.join(BASE, "state.json")

LINES = [
    "2026-11-08 R2548 VERIFICATION window on the battery the register owed "
    "(reconcile-battery-R2547, pre-registered 603 suites / 4594 criteria). Five-silence "
    "scan at open: ONE untracked battery leg qa/reconcile-all-R2548.log was already on "
    "disk from an earlier attempt of this same round, with no index.lock and no live "
    "reconcile process, so it was READ rather than restarted; git status otherwise empty "
    "at HEAD b3901362 equal to origin/main; zero @BigDomain rows in "
    "cph4/evolution-ledger.md; the content-addressed decisions scan read new=0 at a "
    "measured 70 rows / 48 file tokens (the group file keeps shrinking under a group-level "
    "fold, disclosed rather than smoothed); the group orders tail reads 2026-11-08 00:04 "
    "(OB-20261108-000400-425, the lane dispatch already judged knowledge-only at R2543); "
    "benchmarks 2026-11-03 inside the seven-day gate. The debt gate read CLAIM-FIRST "
    "item=reconcile-battery-R2547 first=1 with open=21, and the target was RE-MEASURED "
    "before anything ran by importing reconcile_all.SUITES: 603 suites / 4594 criteria, "
    "byte for byte the registered number.",

    "2026-11-08 R2548 GREEN, PROVENANCE CHECKED RATHER THAN ASSUMED: the leg was not "
    "produced by this append and its origin was not taken on trust - its on-disk mtime "
    "05:06:31 is LATER than the HEAD commit time 04:23:28, and the tree carried no other "
    "modification, so the run happened on the committed R2547 tree. qa/reconcile-all-R2548."
    "log is 979772B on disk (977822B at the green leg plus the 1950B follow-up block), "
    "utf-8 bom=False crlf=0 lone_cr=0, closing RUNNER PASS (603/603 suites green, reconcile "
    "controls 7/7, 1558.5s), ZERO FAIL suite rows, 603 suite rows with 603 unique names and "
    "zero duplicates, and an independent recount over their own criteria fields sums to "
    "EXACTLY 4594 - the pre-registered total matched by measurement on both axes. FOUR "
    "FOLLOW-UP SECTIONS in the designed order: the dry run read SECTION matrix FAIL at "
    "on-disk 58383B against regenerated 58381B with NO byte written while fingerprint read "
    "CLEAN domains=5, profile byte-identical and census DRIFT-CLEAN; "
    "docs/sandbox-suite-matrix.md was then regenerated stamp-aligned from THIS round own "
    "green evidence through src/sandbox/suite_matrix.py --stamp-from to 58381 bytes at 603 "
    "suites / 4594 criteria with its green line honestly reading 603/603 self-describing, "
    "--check read byte-identical at rc=0, and the re-run read all four PASS for VERDICT "
    "R2548 PASS failing=none (APPENDED 1950B eol_ok=True).",

    "2026-11-08 R2548 DEBT, BOARD AND ONE SEED: reconcile-battery-R2547 was closed through "
    "the shipped debtor at its predicted 170126B -> 170129B (line 284, open 21->20, done "
    "246->247, readback ok). NO successor battery is owed because this window moved no "
    "product src byte and the registry is unmoved at 603 suites / 4594 criteria, which is "
    "exactly what the green leg measured; the count was re-read by import rather than "
    "trusted. The gate then owed a leader, so product-face-R2548 was appended first=yes "
    "through the shipped appender at its predicted 170129B -> 170488B (readback ok) naming "
    "the next window a PRODUCT face on the queue head state/queue/tech.md:585 prefix "
    "AC-PNCD1 probe_seam_name_binding_nested_exhaustive_path, whose AC-PNCD1..AC-PNCD6 "
    "were pinned in that row at R2547 BEFORE any code. Residue: the R2547 declaration runs "
    "until R2557 so this round is covered - residue_triage --check --round R2548 read "
    "verdict=TRIAGED residue=300 untriaged=0 expired=0 with ONE UNMATCHED entry R2547 "
    "reading declared=DELIVERED live=- , which is the declaration own row and is named "
    "here rather than hidden.",

    "2026-11-08 R2548 SEED, AND THE FOLD DISCLOSURE TURNED INTO CLAIMABLE WORK: every "
    "window since R2522 has carried the same sentence - state.json is over the waterline "
    "and the fold cannot run - and a sentence repeated twenty-six times is not a plan. "
    "MEASURED this window: state.json reads 189280B against the 78500B waterline with 154 "
    "log lines, and the shipped src/os/state_fold.py exposes ONLY --check and --json in "
    "its own usage block, so no fold face exists at all to be fixed. Rather than implement "
    "one inside a window that had already spent 1558.5s on the battery, ONE tech queue row "
    "was seeded through src/os/seed_queue_R2548.py (state/queue/tech.md 590 -> 591 lines, "
    "once=True, utf-8 LF) pinning AC-SFOLD1..AC-SFOLD6 BEFORE any code: a deterministic "
    "lossless fold into the shipped archive face, the round ledger law preserved across "
    "the fold, a proved round-trip with ALREADY-FOLDED on re-run, the R2522 layout "
    "disagreement closed at its birth site so append and fold agree on one reader, an "
    "honest FOLD-CLEAR gate, and registration as os-state-fold-run(6) with a live run. "
    "queue_floor then read FLOOR-MET main=5/5 tech=12/10 explore=10/10 with the head "
    "unmoved at line 585 and queue_row prefixed_rows 4 -> 5.",

    "2026-11-08 R2548 DIALECT PINS, BOTH BORN FROM THIS WINDOW OWN MEASUREMENT: (1) the "
    "first seed attempt appended a row that queue_head refused as NO-CRITERIA because the "
    "house law wants the prefix declared as Criteria prefix AC-X (FORM-1) or Criteria "
    "AC-X1 (FORM-2) and the row named its criteria only in prose - the row was REVERTED "
    "with git checkout and re-pinned in FORM-2 shape rather than the reader being loosened; "
    "(2) that checkout handed back CRLF because core.autocrlf=true, so the same writer read "
    "lf_only=False minutes after it had read lf_only=True, and .gitattributes now pins "
    "state/queue/*.md to text eol=lf; (3) the matrix document had the same class of defect "
    "in the index itself - the committed blob carries CRLF while suite_matrix.py writes "
    "LF - and one regeneration produced a 491/491 whole-file diff that hid the real "
    "content delta, so docs/sandbox-suite-matrix.md is now pinned to text eol=lf and "
    "suite_matrix --check still reads byte-identical at 58381 bytes.",

    "2026-11-08 R2548 honest disclosures: (a) ZERO product points on the Executive "
    "Protocol scale - nothing a CEO could open was built this window and none is claimed; "
    "the deliverables are a green 603/4594 battery, a matrix document whose evidence "
    "column names THIS round own green leg, and one queue row that converts a 26-round "
    "carried disclosure into work with pre-registered criteria. (b) THIS WINDOW OPENED ON "
    "AN INTERRUPTED ATTEMPT: the battery leg was already on disk, its origin unknown at "
    "open, and it was read first rather than restarted - it happened to be green, which is "
    "stated as a fact of this run and not as a prediction; its provenance was then checked "
    "against the commit timestamp rather than left to trust. (c) ONE seed attempt was "
    "REFUSED by the shipped queue reader and reverted, and the retry carried CRLF until "
    "the writer output was normalised - both are my own defects, measured and named. (d) "
    "The queue_row --check still reads VIOLATIONS on state/queue/tech.md:88, :415, :524, "
    ":537, :590 and state/queue/explore.md:295, all of them rows that pre-date this "
    "window; this window declined to mass-edit them and says so. (e) The residual battery "
    "open rows product-face-R2511, R2513, R2515, R2517 and R2522 still name product "
    "windows whose suites demonstrably shipped, and the shipped readers still do not age "
    "them; this window declined to mass-close them by hand and did not invent a reading to "
    "hide them. (f) The fold remains an OWED OBLIGATION - it is not discharged here, only "
    "made claimable and given criteria; state.json therefore keeps growing and the stored "
    "last_decision_rows field was corrected from 104 to the measured 70 rows rather than "
    "left drifting. (g) Docker is absent on this host so no containerised bring-up of the "
    "sandbox faces is claimed. (h) The real 19.9 debit and the real msgSecCheck still wait "
    "on CEO physical items (merchant id, mini-program appid/secret). (i) tasks.md was not "
    "touched, it is the P-47 canonical board. (j) The S4U lane re-registration needs an "
    "ELEVATED shell and D-20261107-14 has classified it as a ceo-pending physical item "
    "with zero chase. (k) The window overshot its 25-minute budget on a 1558.5s battery "
    "plus a follow-up pass and says so.",

    "R2548 tokens: local=~9k api=0 api_reason=verification window - five-silence scan, "
    "one pre-existing battery leg read rather than restarted and its provenance checked "
    "against the commit timestamp, one content-addressed decisions scan reading new=0, one "
    "registry target re-measured by import, one full 603-suite battery green at the "
    "pre-registered 4594 criteria with an independent criteria recount and a duplicate "
    "check, one designed matrix FAIL with no byte written, one stamp-aligned matrix "
    "regeneration from this round own green evidence checked byte-identical, one "
    "four-section follow-up re-run to a PASS verdict, one debt row closed and one opened "
    "through their shipped writers, one queue row refused then re-pinned with its criteria "
    "pre-registered, two line-ending pins born from this window own measurements, and the "
    "state/export/backlog/heartbeat closeout; zero cloud calls and zero external API "
    "touches",
]


def main():
    raw = open(STATE, "rb").read()
    text = raw.decode("utf-8")
    state = json.loads(text)
    replay = json.dumps(state, ensure_ascii=False, indent=2) + "\n"
    if replay.encode("utf-8") != raw:
        print("REFUSED E_APP_ROUNDTRIP: dump does not reproduce the file")
        return 3
    state["tick"] = 2548
    state["last_decision_rows"] = 70
    state["log"].extend(LINES)
    out = (json.dumps(state, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    tmp = STATE + ".tmp"
    with open(tmp, "wb") as fh:
        fh.write(out)
    os.replace(tmp, STATE)
    back = open(STATE, "rb").read()
    print("APPENDED before=%dB after=%dB tick=%d log=%d readback=%s"
          % (len(raw), len(back), state["tick"], len(state["log"]),
             "ok" if back == out else "MISMATCH"))
    return 0


if __name__ == "__main__":
    sys.exit(main())