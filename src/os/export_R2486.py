"""export_R2486 - refresh docs/status-export.json for the R2486 window.

The derivation, atomic write and read-back self-check live in the shipped
export_R2431 module; this driver only supplies this round's CEO lines and its
outs row, so no second derivation exists.
"""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import export_R2431 as base  # noqa: E402

base.DO = ("R2486 tech-face window: a key that only two of the three "
           "export-reading faces publish can no longer disagree in silence, "
           "and the reading that used to drop it now publishes every key with "
           "the number of faces that actually carry it")

base.LATEST = ("qa/row-key-carrier-scope-R2486.log (3118B, legs=2 "
               "identical=True, adjacent=3 fails=0) + "
               "qa/row-key-carrier-scope-live-R2486.log (579B, utf-8 LF, "
               "crlf=0, verdict=AGREE keys=6 all=4 subset=2 singles=1) + "
               "docs/sandbox-suite-matrix.md (54827B, 571 suites / 4402 "
               "criteria, --check byte-identical) at 2026-11-06 R2486")

base.NEXT = ("2026-11-07 the debt register owed reconcile-battery-R2486 "
             "(pre-registered 571 suites / 4402 criteria) must run on the "
             "committed tree before any further product byte; after that the "
             "queue head is the R2438 per-entry expiry-window seed, and every "
             "P-47 item beyond the shipped sandbox faces still waits on CEO "
             "physical items (merchant id, mini-program appid/secret)")

base.RESULT = (
    "2026-11-06 R2486 tech-face window: no new clickable surface, and what this "
    "window bought is that the export-reading family can no longer carry a key "
    "two of its three faces publish and disagree about silently. Claim order "
    "was read from the gate, not guessed: no battery was owed (R2485 closed "
    "reconcile-battery-R2484) and debt_gate --check --round R2486 printed "
    "CLAIM-FIRST item=product-face-R2456 opened=R2455 carried=31 stale=yes "
    "open=2 first=1, naming the tech queue row at state/queue/tech.md:522 whose "
    "AC-PFKC1..AC-PFKC6 were pinned at R2446 before any code. Product: "
    "src/os/row_key_carrier_scope.py asks the shipped row-drift reading at CALL "
    "time (which itself asks the identity compare), keeps that report unchanged "
    "inside its own, derives each key carrier set from the rows that publish it "
    "rather than from a fixed list, reads every key across its own carriers per "
    "(path, line), names a two-of-three disagreement ROWS-SPLIT with the key and "
    "every carrying face, and reports a one-of-three key SINGLE-FACE with its "
    "carrier count. MEASURED on the real tree: verdict=AGREE cells=11 keys=6 "
    "all=4 subset=2 singles=1, with kind carriers=2 (from-import,relative) and "
    "relative carriers=1 - exactly the two keys the R2446 intersection dropped. "
    "The blind spot is proved on FIXTURES and NOT claimed as a live catch: one "
    "rewritten from-import kind keeps the shipped reading at FACES-AGREE rc=0 "
    "splits=0 while this face reads ROWS-SPLIT naming kind and both carriers, "
    "and the all-face keys stay byte-identical to the R2446 reading on the clean "
    "tree and on the drifted probe. Proof: AC-PFKC1..AC-PFKC6 SUITE PASS 6/6 "
    "twice with an identical digest plus three adjacent comma suites green "
    "through the shipped capture callable, and one live reading. Registry 570 -> "
    "571 suites / 4396 -> 4402 criteria; matrix restamped stamp-aligned to "
    "54827B with --check byte-identical and its green line honestly reading "
    "570/571 because this window ran no battery; census flags=0 DRIFT-CLEAN with "
    "the 529-entry baseline untouched. Honest: the first live evidence file "
    "inherited the child process CRLF endings and the census refused it as "
    "class=pwsh-capture, so the bytes were rewritten as utf-8 LF and nothing was "
    "baselined or widened to make it pass; Docker is absent so no containerised "
    "bring-up is claimed; the real 19.9 debit and the real msgSecCheck still wait "
    "on CEO physical items; no fold was due (state 29040B at open against the "
    "78500B waterline); tasks.md was not touched. Debt: "
    "reconcile-battery-R2486 appended first=no at 125935B -> 126340B with "
    "readback ok, so the next window owes the battery on the committed tree "
    "before any further product byte."
)

base.OUTS = (
    "src/os/row_key_carrier_scope.py + src/os/test_row_key_carrier_scope.py + "
    "qa/row-key-carrier-scope-R2486.log + "
    "qa/row-key-carrier-scope-live-R2486.log + "
    "src/sandbox/reconcile_all.py + docs/sandbox-suite-matrix.md + "
    "state/queue/tech.md + state/debt.md + src/os/state_append_R2486.py + "
    "src/os/export_R2486.py + src/os/state.json + docs/status-export.json + "
    "heartbeat.txt + src/os/backlog.md"
)

if __name__ == "__main__":
    print(base.main())