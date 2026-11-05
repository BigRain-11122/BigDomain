"""export_R2464 - refresh docs/status-export.json for the R2464 window.

The derivation, atomic write and read-back self-check live in the shipped
export_R2431 module; this driver only supplies this round's CEO lines and its
outs row, so no second derivation exists.
"""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import export_R2431 as base  # noqa: E402

base.DO = ("R2464 business window: the lobby page now has a room selector "
           "filled from the server own config and a readable event ledger. "
           "Bring-up unchanged - python src/sandbox/lobby/server.py "
           "--city-http-port 8092 --web-port 8094 then open "
           "http://127.0.0.1:8094/lobby/ - switch rooms from the selector and "
           "watch the ledger record every frame; a second window still stays "
           "quiet until it joins the same room")

base.LATEST = ("src/sandbox/lobby/lobby.html (10077B page with room selector + "
               "event ledger, zero hardcoded room names) + "
               "src/sandbox/lobby/lobby_page.py (GET /lobby/api/rooms wired "
               "from the server cfg) + server.py rooms wiring + "
               "src/sandbox/lobby/test_lobby_rooms.py SUITE PASS 6/6 twice with "
               "an identical digest (qa/lobby-room-picker-R2464.log) + "
               "qa/lobby-room-picker-live-R2464.log")

base.NEXT = ("2026-11-05/07 the battery the R2464 src edits owe runs FIRST next "
             "window on the committed tree at the pre-registered 560 suites / "
             "4336 criteria (reconcile-battery-R2465); then the real msgSecCheck "
             "and the real 19.9 debit the moment the mini-program "
             "appid/secret and the merchant id land, and a server-side room "
             "history read face so the ledger can show what happened before the "
             "page was opened, ETA inside 48h")

base.RESULT = (
    "2026-11-05 R2464 BUSINESS window on the milestone the R2463 export named: "
    "the lobby had three configured rooms but only one room a visitor could "
    "reach. Shipped GET /lobby/api/rooms wired from the server own config, a "
    "room selector that subscribes the new room and releases the old one, and a "
    "client-side event ledger recording every received frame. Six criteria were "
    "pinned BEFORE the code and read off a real server and a real WebSocket "
    "client, twice with an identical digest, adjacent suites green: the rooms "
    "route matches the config in order, the page hardcodes no room name, the "
    "standing compliance surfaces are intact, an unknown room is refused, and "
    "rooms really partition - a client left on the default room received "
    "nothing for a full second while the subscriber read the message. Registry "
    "560 suites / 4336 criteria, matrix byte-identical. Honest limits: the "
    "ledger is a client-side reading that starts empty on reload, Docker is "
    "absent so the compose bring-up stays unproved, and the real debit plus the "
    "real msgSecCheck still wait on CEO physical items."
)

base.OUTS = (
    "src/sandbox/lobby/lobby.html + src/sandbox/lobby/lobby_page.py + "
    "src/sandbox/lobby/server.py (rooms wiring) + "
    "src/sandbox/lobby/test_lobby_rooms.py + "
    "src/sandbox/reconcile_all.py (one registry row) + "
    "qa/lobby-room-picker-R2464.log + qa/lobby-room-picker-live-R2464.log + "
    "docs/sandbox-suite-matrix.md + state/debt.md + src/os/backlog.md + "
    "src/os/closeout_R2464.py + src/os/live_R2464.py + "
    "src/os/export_R2464.py + docs/status-export.json + src/os/state.json + "
    "heartbeat.txt"
)

if __name__ == "__main__":
    sys.exit(base.main())