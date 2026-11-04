"""export_R2460 - refresh docs/status-export.json for the R2460 window.

The derivation, atomic write and read-back self-check live in the shipped
export_R2431 module; this driver only supplies this round's CEO lines and its
outs row, so no second derivation exists.
"""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import export_R2431 as base  # noqa: E402

base.DO = ("R2460 business window: the silicon lobby now opens in a browser. "
           "Run `python src/sandbox/lobby/server.py --web-port 8094` and open "
           "http://127.0.0.1:8094/lobby/ - connect, take the mock sandbox "
           "entrance, open a second window, and the two windows chat in the "
           "same room while an un-entitled window is refused")

base.LATEST = ("src/sandbox/lobby/lobby.html (7379B self-contained page, zero "
               "external references, AI generated label + non-advice note + "
               "mock/no-real-charge statement on screen) + "
               "src/sandbox/lobby/lobby_page.py (GET /lobby/, GET /lobby, GET "
               "/lobby/api/config publishing the REAL ws port; read-only HTTP) "
               "+ one --web-port flag on src/sandbox/lobby/server.py + "
               "src/sandbox/lobby/test_lobby_page.py SUITE PASS 6/6 twice with "
               "an identical digest (qa/lobby-page-R2460.log 1225B) + a live "
               "process capture (qa/lobby-page-live-R2460.log)")

base.NEXT = ("2026-11-05/06 the battery the R2459/R2460 src edits owe runs FIRST "
             "next window on the committed tree at the pre-registered 558 suites "
             "/ 4324 criteria (reconcile-battery-R2461), which also un-stales "
             "docs/sandbox-suite-matrix.md; then the lobby page gets its next "
             "business step - the same two-window chat driven by the real "
             "msgSecCheck the moment the mini-program appid/secret lands, and a "
             "room picker over the shipped lobby/quant/cocreate rooms, ETA "
             "inside 48h")

base.RESULT = (
    "2026-11-05 R2460 BUSINESS window, SUPERSEDING the carried internal audit "
    "face product-face-R2456 (still open and claimable at state/queue/tech.md:522 "
    "prefix AC-PFKC1) under the CEO standing order OB-20261105-003656-879: real "
    "output only, no new mechanism, rule or document. Until today the lobby "
    "WebSocket could only be driven by a terminal demo (interop_demo.py) while "
    "the city page and the checkout page were already clickable, so this window "
    "shipped the missing surface: lobby.html plus lobby_page.py, a read-only "
    "HTTP face serving the page byte-identical from disk and answering a "
    "same-origin GET /lobby/api/config with the REAL ws port, wired into "
    "server.py behind one --web-port flag. A person opens "
    "http://127.0.0.1:8094/lobby/, connects, takes the MOCK sandbox entrance and "
    "chats with a second window: both receive one shared evt_id, the server "
    "stays authoritative on actor and ai_generated, a spectator is refused "
    "E_ENTRANCE_REQUIRED, and unknown paths 404 while every non-GET reads 405. "
    "Six criteria were read off a REAL server on an OS-assigned port and a REAL "
    "WebSocket client, twice with an identical digest, with the city-view suite "
    "re-run green adjacent; the registry moved exactly one row to 558 suites / "
    "4324 criteria; a live capture proves the same bring-up a CEO would run. "
    "Three self-inflicted defects were caught by RUNNING and fixed at their "
    "birth site without widening a criterion: the peer connection hello/risk "
    "frames were never drained, three printed lines carried volatile values "
    "that broke cross-leg comparison, and the state canon had drifted (CRLF "
    "preserved, off-indent 89 -> 0). Honest limits: the criteria landed on the "
    "board only at closeout so the pin-before-code order was not honoured this "
    "window; the suite matrix is stale because no battery ran and its newest "
    "evidence face carries no stamp line; Docker is absent so the compose "
    "bring-up is unproved; the real debit and the real msgSecCheck still wait "
    "on CEO physical items (merchant id, mini-program appid/secret)."
)

base.OUTS = (
    "src/sandbox/lobby/lobby.html + src/sandbox/lobby/lobby_page.py + "
    "src/sandbox/lobby/server.py (one --web-port flag) + "
    "src/sandbox/lobby/test_lobby_page.py + qa/lobby-page-R2460.log + "
    "qa/lobby-page-live-R2460.log + src/sandbox/reconcile_all.py (one registry "
    "row) + state/debt.md + src/os/backlog.md + src/os/closeout_R2460.py + "
    "src/os/export_R2460.py + docs/status-export.json + src/os/state.json + "
    "heartbeat.txt"
)

if __name__ == "__main__":
    sys.exit(base.main())