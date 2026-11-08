"""R2561 state append: the round narrative, disclosures and token ledger.

The layout law was MEASURED before any mutation: json.dumps(indent=1,
ensure_ascii=False) with NO trailing newline reads byte-identical at 282439B,
so this append prints that same form and proves the read-back.
"""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
STATE = os.path.join(REPO, "src", "os", "state.json")

LINES = [
    "2026-11-08 R2561 PRODUCT window on the tech head the register named "
    "(product-face-R2560, state/queue/tech.md:597 prefix AC-PNDB1, criteria "
    "AC-PNDB1..AC-PNDB6 pinned in that row at R2559 BEFORE any code). THIS "
    "WINDOW OPENED ON AN INTERRUPTED ATTEMPT: the face module, its suite, the "
    "registry row, two evidence logs and five scratch drivers were already on "
    "disk with no index.lock and no live python reader, so every one was "
    "MEASURED rather than rebuilt and none is claimed as newly written here. "
    "VERIFIED BY RE-RUNNING, not by reading the leftovers: the suite re-ran "
    "SUITE PASS 6/6 alone at closeout with 30 PASS lines and exit 0, and the "
    "capture log reads legs=2 with an IDENTICAL digest 489031857ADE8A94 plus "
    "adjacent=5 green (qa/probe-seam-name-binding-arm-mixed-residual-alias-"
    "attribute-predicate-R2561.log, 4850B, utf-8 bom=False crlf=0 bare_cr=0 "
    "nul=0), while the live leg reads modules=5 loops=161 pred_resolved=0 "
    "pred_named=2 unreadable=0 BOUNDED-READ-CLEAN with mine=yes base=yes "
    "read-only (qa/...-predicate-live-R2561.log, 852B, same dialect, measured "
    "by byte read-back rather than by eye). The claimed row 597 owns exactly "
    "these six criteria and names exactly this module, so the spare is real.",
    "R2561 REGISTRY, MATRIX AND BOARD: the registry reads 610 suites / 4636 "
    "criteria recounted by importing reconcile_all.SUITES rather than trusted "
    "(610 unique names, 610 unique paths), which is the number the interrupted "
    "attempt registered. docs/sandbox-suite-matrix.md read FAIL on content at "
    "the same byte count first by design, was then regenerated from the "
    "ELIGIBLE battery leg qa/reconcile-all-R2560.log through suite_matrix.py "
    "--stamp-from to 59508 bytes at 610 suites / 4636 criteria with its green "
    "line honestly reading 609/610 because this round own suite is not in that "
    "battery leg, and --check then read byte-identical at rc=0. Row 597 was "
    "closed through src/os/queue_close_R2561.py at its predicted and measured "
    "1776924 bytes with its DISCHARGED note, and ONE row was seeded from THIS "
    "window own MEASURED limits - a plain `import m` base reads state=None with "
    "NO reason at all, an `import m as x` base and a with-as module base both "
    "read attr-base-local, and a helper constant that is an alias or a "
    "re-export reads attr-non-constant / attr-missing - as AC-PNDC1..AC-PNDC6; "
    "queue_head then read the new head at line 599 prefix AC-PNDC1 claimable=12 "
    "and queue_floor read FLOOR-MET main=5/5 tech=12/10 explore=10/10.",
    "R2561 DEBT AND RESIDUE: product-face-R2560 was closed through the shipped "
    "debtor at its predicted 174884B -> 174887B (line 302, open 24->23, "
    "done 260->261, readback ok), reconcile-battery-R2561 was appended "
    "first=yes at the pre-registered 610 suites / 4636 criteria "
    "(174887B -> 175089B, readback ok) and product-face-R2561 appended "
    "first=no naming tech line 599 AC-PNDC1 (175089B -> 175377B, readback ok), "
    "so the gate now names that battery first. The round was declared through "
    "the shipped residue batch writer after a dry run at 302 -> 303 entries / "
    "83288B -> 83514B until R2571, after which residue_triage --check read "
    "residue=301 triaged=301 untriaged=0 expired=0 verdict=TRIAGED with "
    "unmatched=2, and its exit code is 1 on those two historical unmatched "
    "entries rather than on an undeclared round.",
    "R2561 DECISIONS (content-addressed): the group canon now carries 113 "
    "table rows / 112 row-owner tokens, and the diff against the stored "
    "192-token baseline reads NEW=0. MY FIRST READER WAS BROKEN and is named "
    "rather than hidden: a line-anchored regex matched none of the table rows "
    "and printed 0 rows / 0 tokens, which would have been a false clean; the "
    "reader was rewritten to take the row-owner cell and then measured 113 "
    "rows / 112 tokens / new=0. The stored last_decision_rows field read 273 "
    "against that measured 113 and was corrected to the measurement rather "
    "than left drifting. The group orders tail still reads 2026-11-08 12:06 "
    "(OB-20261108-120628-589, the BigMoney quant/BigCompute CEO order already "
    "judged knowledge-only at R2560) and is not an execution face for this "
    "company; zero unreplied @BigDomain rows in cph4/evolution-ledger.md; "
    "benchmarks 2026-11-03 inside the seven-day gate.",
    "R2561 honest disclosures: (a) TWO product points on the Executive "
    "Protocol scale - a runnable CLI with its own suite and a bounded live "
    "reading a maintainer can run - but nothing a CEO could newly open was "
    "built and no P-47 business surface moved; (b) THE WINDOW OPENED ON AN "
    "INTERRUPTED ATTEMPT and the face, its suite, the registry row and both "
    "evidence logs were already on disk - they were re-measured by re-running "
    "the suite and by reading the logs byte by byte, and no part of that work "
    "is claimed as this window own authorship; (c) FOUR of my own scratch "
    "drivers (debug, debug2, smoke, tidy) were deleted before the commit "
    "rather than staged, and capture/live are kept because they are the "
    "reproducible provenance of the evidence; (d) MY LIMIT MEASUREMENT FIRST "
    "READ A FIXTURE I HAD BROKEN - the helper-alias world lacked its own "
    "`import ha`, so the face honestly answered attr-not-imported and the "
    "reading was re-taken with the import present, where the true answer is "
    "attr-non-constant; both readings are named; (e) the state.json round-trip "
    "law had to be RE-DERIVED this window: dump with indent=2 differs at byte "
    "3 and indent=1 with a trailing newline differs by one byte, and only "
    "indent=1 with NO trailing newline reads byte-identical at 282439B, so "
    "that is the form this append proves before mutating anything; (f) "
    "MEASURED DEFECT STILL OPEN from R2522: state.json stands far above the "
    "78500B waterline so state_fold --check reads FOLD-DUE and the shipped "
    "tool offers only a --check face, so the fold stays an OWED obligation "
    "seeded as state_fold_run (AC-SFOLD1..AC-SFOLD6); (g) the matrix green "
    "line honestly reads 609/610 rather than claiming a green it cannot count; "
    "(h) Docker is absent on this host so no containerised bring-up of the "
    "sandbox faces is claimed; (i) the real 19.9 debit and the real msgSecCheck "
    "still wait on CEO physical items (merchant id, mini-program "
    "appid/secret); (j) tasks.md was not touched, it is the P-47 canonical "
    "board; (k) the S4U lane re-registration still needs an ELEVATED shell and "
    "D-20261107-14 has classified it as a ceo-pending physical item with zero "
    "chase; (l) the open rows product-face-R2511, R2513, R2515, R2517 and "
    "R2522 still name product windows whose suites demonstrably shipped and "
    "the shipped readers still do not age them - this window declined to "
    "mass-close them by hand and did not invent a reading to hide them.",
    "R2561 tokens: local=~13k api=0 api_reason=product window adopted from an "
    "interrupted attempt - five-silence scan, one content-addressed decisions "
    "scan whose first reader was broken and replaced, one registry recount by "
    "import, one suite re-run to 6/6 at closeout, two evidence logs measured "
    "for bytes and dialect, six limit shapes measured on both readers with one "
    "broken fixture re-taken, one stamp-aligned matrix regeneration checked "
    "byte-identical, one board row closed and one seeded through their "
    "writers, three debt rows moved and one residue declaration appended "
    "through their shipped writers, and the state/export/backlog/heartbeat "
    "closeout; zero cloud calls and zero external API touches",
]


def dump(state):
    return json.dumps(state, indent=1, ensure_ascii=False).encode("utf-8")


def main():
    with open(STATE, "rb") as handle:
        before = handle.read()
    state = json.loads(before.decode("utf-8"))
    if dump(state) != before:
        print("REFUSED E_SA_LAYOUT: the file is not in the indent=1 no-newline "
              "form (%d bytes)" % (len(before),))
        return 3
    state["tick"] = 2561
    state["last_order"] = "2026-11-08 12:06"
    state["last_decision_rows"] = 113
    for line in LINES:
        if line not in state["log"]:
            state["log"].append(line)
    payload = dump(state)
    with open(STATE, "wb") as handle:
        handle.write(payload)
    back = json.loads(open(STATE, "rb").read().decode("utf-8"))
    ok = (back["tick"] == 2561
          and back["last_decision_rows"] == 113
          and len(back["log"]) == len(state["log"]))
    print("state %s tick=%d log=%d before=%dB after=%dB"
          % ("OK" if ok else "FAIL", back["tick"], len(back["log"]),
             len(before), len(payload)))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())