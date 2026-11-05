"""export_R2481 - refresh docs/status-export.json for the R2481 window.

The derivation, atomic write and read-back self-check live in the shipped
export_R2431 module; this driver only supplies this round's CEO lines and its
outs row, so no second derivation exists.
"""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import export_R2431 as base  # noqa: E402

base.DO = ("R2481 business window: the sandbox gained a control panel - one page "
           "with a Start and a Stop verb per face, and the Start button really "
           "spawns the shipped module on an OS-assigned port and returns the URL "
           "only after that socket accepts, which is the half R2477 disclosed as "
           "unmet")

base.LATEST = ("src/sandbox/panel.html (7590B, self-contained) + "
               "qa/panel-R2481.log (SUITE PASS 6/6 twice, digest "
               "CEB6D522A66597E5, two adjacent suites green) + "
               "qa/panel-live-R2481.log (362B, live leg: page 200 at 7590B, "
               "ledger started on port 53571, published URL 200 with the "
               "shipped 7977B page byte-identical, stop left the port refused)")

base.NEXT = ("2026-11-07 the next window owes the battery on the committed tree "
             "before any further product byte (reconcile-battery-R2481, "
             "pre-registered 568 suites / 4384 criteria, R2168 mixed-tree rule); "
             "after that the strongest product candidate is wiring the panel "
             "into the hub payload so the one entry page can reach it, and every "
             "P-47 item beyond the shipped sandbox faces still waits on CEO "
             "physical items (merchant id, mini-program appid/secret)")

base.RESULT = (
    "2026-11-06 R2481 business window delivered: a person can now start a "
    "shipped sandbox face from a browser instead of a terminal. SHIPPED "
    "src/sandbox/panel.py (pure ASCII stdlib, GET /panel and /panel/ from disk, "
    "GET /panel/api/state with a live flag measured by TCP at call time, POST "
    "/panel/api/start spawning the shipped module through sys.executable with "
    "CREATE_NO_WINDOW and reporting the URL only after the socket accepts, POST "
    "/panel/api/stop terminating the child it owns) and src/sandbox/panel.html "
    "(7590B, zero external references, the AI label, the non-advice note and a "
    "mock/no-real-charge statement on screen) plus one registry row panel(6). "
    "PROOF: AC-PAN1..AC-PAN6 were pinned in src/os/backlog.md before the code "
    "and read SUITE PASS 6/6 twice with identical bodies (digest "
    "CEB6D522A66597E5) with two adjacent suites green in the same capture; the "
    "live leg drove the real module over HTTP - page 200 at 7590B, state naming "
    "checkout,ledger,ugc, ledger started on OS-assigned port 53571, the "
    "published URL answering 200 with bytes byte-identical to ledger.html "
    "(7977B), stop answered 200 and the port then refused a connect. ONE REAL "
    "DEFECT found by running and repaired at its birth site: the suite printed "
    "'AC-PAN1 ... PASS' rather than a PASS/FAIL-prefixed line, so the first "
    "capture digested to the empty-string hash and the battery's ^PASS counter "
    "would have read zero criteria; the prefix was corrected, the stale "
    "evidence file deleted, and the capture re-taken. ONE AMENDMENT disclosed: "
    "AC-PAN6 first carried the copied 'imports no clock module' ban, impossible "
    "for a module that must wait on a socket, dropped before the suite existed "
    "and before any PASS was claimed. Registry 568 suites / 4384 criteria; "
    "matrix restamped stamp-aligned to 54605B with --check byte-identical "
    "(green honestly 567/568); reconcile-battery-R2481 appended first=no at "
    "124975B -> 125178B, so the next window owes the battery before any further "
    "product byte. Honest: the panel starts three faces and not the lobby "
    "server, the hub page does not yet link to it, Docker is absent so no "
    "containerised bring-up is claimed, the real 19.9 debit and the real "
    "msgSecCheck still wait on CEO physical items, tasks.md was not touched, and "
    "no fold was due at 56704B against the 78500B waterline."
)

base.OUTS = (
    "src/sandbox/panel.py + src/sandbox/panel.html + src/sandbox/test_panel.py "
    "+ src/sandbox/reconcile_all.py + qa/panel-R2481.log + "
    "qa/panel-live-R2481.log + docs/sandbox-suite-matrix.md + state/debt.md + "
    "src/os/state.json + src/os/panel_live_R2481.py + src/os/append_R2481.py + "
    "src/os/export_R2481.py + docs/status-export.json + heartbeat.txt + "
    "src/os/backlog.md"
)

if __name__ == "__main__":
    print(base.main())