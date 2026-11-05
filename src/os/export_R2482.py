"""export_R2482 - refresh docs/status-export.json for the R2482 window.

The derivation, atomic write and read-back self-check live in the shipped
export_R2431 module; this driver only supplies this round's CEO lines and its
outs row, so no second derivation exists.
"""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import export_R2431 as base  # noqa: E402

base.DO = ("R2482 business window: the sandbox control panel now starts the lobby "
           "too - the one process that owns ws, city, web, hub and gate is given "
           "five distinct OS ports up front and its hub URL is published only "
           "after that socket accepts, so the face the product is about can be "
           "brought up from the browser instead of a terminal")

base.LATEST = ("src/sandbox/panel.html (7738B, self-contained, footer now tells "
               "the four-face truth) + qa/panel-lobby-R2482-a.log and -b.log "
               "(1264B each, SUITE PASS 6/6 twice) + "
               "qa/panel-lobby-live-R2482.log (869B: lobby started with "
               "ws=51248 city=51249 web=51250 hub=51251 gate=51252, hub page 200 "
               "at 7104B, stop left the hub port refused) at 2026-11-06 02:44")

base.NEXT = ("2026-11-07 the next window owes reconcile-battery-R2482 on the "
             "committed tree before any further product byte (569 suites / 4390 "
             "criteria pre-registered, R2168 mixed-tree rule); after that the "
             "strongest product candidate is wiring the panel into the hub "
             "payload so the one entry page leads to the control panel, and "
             "every P-47 item beyond the shipped sandbox faces still waits on "
             "CEO physical items (merchant id, mini-program appid/secret)")

base.RESULT = (
    "2026-11-06 R2482 business window delivered: the panel can start the lobby. "
    "SHIPPED src/sandbox/panel.py lobby leg (LOBBY_PORT_KEYS / LOBBY_FLAGS, five "
    "distinct OS ports assigned before the spawn, published port = hub, the "
    "whole ports map and the exact reproducing command returned, stop and server "
    "shutdown both kill the child) plus src/sandbox/panel.html footer rewritten "
    "to the four-face truth (7738B) plus one registry row panel-lobby(6). "
    "PROOF: AC-LBY1..AC-LBY6 written in this window before the code and the "
    "suite, reading SUITE PASS 6/6 TWICE with identical criterion lines "
    "(qa/panel-lobby-R2482-a.log and -b.log, 1264B each) and two adjacent "
    "suites green (qa/panel-R2482-adjacent.log, "
    "qa/start-all-R2482-adjacent.log, both 6/6); the live leg drove a REAL panel "
    "process over HTTP - page 200 at 7738B, lobby started with ws=51248 "
    "city=51249 web=51250 hub=51251 gate=51252, the hub socket accepting at the "
    "moment of the answer, hub page 200 at 7104B, state live=true port=51251, "
    "stop 200, hub port refused afterwards. THREE pinned criteria amended openly "
    "where the product legitimately moved them: AC-PAN2's exact face list gained "
    "the fourth id rather than loosening, AC-PAN4's unknown-face example moved "
    "from lobby to nope with the assertion unchanged, and AC-LBY1's module "
    "expectation was corrected to the existing src-relative contract after the "
    "first run disclosed rather than dressed up. Registry 569 suites / 4390 "
    "criteria; reconcile-battery-R2482 appended first=no at 125178B -> 125387B "
    "with readback ok, so the next window owes the battery before any further "
    "product byte. Honest: the panel is not linked from the hub payload, a "
    "panel-started lobby is invisible to the hub's own liveness map, only the hub "
    "port is measured live, Docker is absent so no containerised bring-up is "
    "claimed, the real 19.9 debit and the real msgSecCheck still wait on CEO "
    "physical items, and tasks.md was not touched."
)

base.OUTS = (
    "src/sandbox/panel.py + src/sandbox/panel.html + "
    "src/sandbox/test_panel_lobby.py + src/sandbox/test_panel.py + "
    "src/sandbox/reconcile_all.py + qa/panel-lobby-R2482-a.log + "
    "qa/panel-lobby-R2482-b.log + qa/panel-lobby-live-R2482.log + "
    "qa/panel-R2482-adjacent.log + qa/start-all-R2482-adjacent.log + "
    "state/debt.md + src/os/state.json + src/os/append_R2482.py + "
    "src/os/export_R2482.py + docs/status-export.json + heartbeat.txt + "
    "src/os/backlog.md"
)

if __name__ == "__main__":
    print(base.main())