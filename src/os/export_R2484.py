"""export_R2484 - refresh docs/status-export.json for the R2484 window.

The derivation, atomic write and read-back self-check live in the shipped
export_R2431 module; this driver only supplies this round's CEO lines and its
outs row, so no second derivation exists.
"""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import export_R2431 as base  # noqa: E402

base.DO = ("R2484 business window: the one door now leads to the control panel "
           "- the hub payload publishes the panel face at 8099 and marks "
           "whether it is really listening, so a person who opens the hub can "
           "reach a click-to-start surface instead of being told to run a "
           "command")

base.LATEST = ("qa/hub-panel-live-R2484.log (real lobby server + real panel: "
               "hub 200 at 7853B, published panel url 200 at 7738B "
               "byte-identical to panel.html, live[panel]=True, teardown "
               "refused) + qa/hub-panel-R2484.log (1163B, two identical legs "
               "6/6) + docs/sandbox-suite-matrix.md (54765B, 570 suites / 4396 "
               "criteria, --check byte-identical) at 2026-11-06 R2484")

base.NEXT = ("2026-11-07 the R2168 mixed-tree rule makes the next window owe "
             "the full reconcile battery on the committed R2484 tree at the "
             "pre-registered 570 suites / 4396 criteria BEFORE any further "
             "product byte; the strongest product candidate after that is a "
             "panel that can also STOP what it started from the hub page and a "
             "hub payload that links the panel from every card, and every P-47 "
             "item beyond the shipped sandbox faces still waits on CEO physical "
             "items (merchant id, mini-program appid/secret)")

base.RESULT = (
    "2026-11-06 R2484 business window: the hub entry page publishes the sixth "
    "face - the control panel - and marks whether it is live. Product bytes: "
    "hub_page.py gains PANEL_CMD/PANEL_NOTE and panel_port (default 8099) in "
    "build_faces and face_ports; hub.html gains the panel card id=link-panel "
    "with a data-face=panel marker, six markers total, zero external "
    "references, the subtitle corrected to six faces and the footer naming both "
    "--panel-port and the panel command; server.py advertises --panel-port and "
    "passes it through. Proof: AC-HPN1..AC-HPN6 were pinned in the backlog row "
    "BEFORE the code; the suite read SUITE PASS 6/6 twice with identical "
    "verdicts through the shipped capture callable (qa/hub-panel-R2484.log, "
    "1163B, utf-8, crlf=0, no BOM) and the live leg started the real lobby "
    "server and the real panel: hub page 200 at 7853B, payload panel url at the "
    "assigned port with live[panel]=True, that URL answering 200 at 7738B "
    "byte-identical to panel.html, /panel/api/state 200 with startable="
    "checkout,ledger,ugc,lobby, and the port refused after teardown. One "
    "neighbouring pinned criterion was amended openly: test_hub_ugc AC-HUG1 "
    "compared face_ports to an exact six-key map, so it now carries panel=8099 "
    "as a seventh member and keeps its equality law rather than being loosened "
    "to a subset. Registry 569 -> 570 suites and 4390 -> 4396 criteria; matrix "
    "restamped to 54765B with --check byte-identical and its green line "
    "honestly reading 569/570; census DRIFT-CLEAN flags=0; reconcile-battery-"
    "R2484 appended first=no at 125395B -> 125931B with readback ok. A fold was "
    "due at open (78345B, 155B under the 78500B waterline) and ran at a true "
    "round-block boundary over log items 1..78 with all 317 tokens carried into "
    "the summary (the first attempt carried 86 too few and was REFUSED by the "
    "shipped predicate, then re-run correctly), leaving 21447B. Honest: the "
    "hub still cannot start anything itself (that is the panel job one click "
    "further), the liveness probe is a 0.35s TCP connect rather than a health "
    "contract, Docker is absent so no containerised bring-up is claimed, the "
    "real 19.9 debit and the real msgSecCheck still wait on CEO physical items, "
    "and tasks.md was not touched."
)

base.OUTS = (
    "src/sandbox/lobby/hub_page.py + src/sandbox/lobby/hub.html + "
    "src/sandbox/lobby/server.py + src/sandbox/lobby/test_hub_panel.py + "
    "src/sandbox/lobby/test_hub_ugc.py + src/sandbox/reconcile_all.py + "
    "src/os/live_R2484.py + src/os/closeout_R2484.py + src/os/export_R2484.py + "
    "qa/hub-panel-R2484.log + qa/hub-panel-live-R2484.log + "
    "docs/sandbox-suite-matrix.md + state/debt.md + src/os/state.json + "
    "docs/status-export.json + heartbeat.txt + src/os/backlog.md"
)

if __name__ == "__main__":
    print(base.main())