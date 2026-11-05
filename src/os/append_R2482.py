"""Append the R2482 round log to src/os/state.json (one utf-8 LF writer)."""

import io
import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(BASE, "state.json")

TICK = 2482

LOG = [
    "2026-11-06 R2482 BUSINESS window DELIVERED (CEO standing order "
    "OB-20261105-003656-879, real output only; it SUPERSEDES the carried "
    "internal audit row product-face-R2456 by name, which stays open and "
    "claimable at state/queue/tech.md:522 prefix AC-PFKC1). Five-silence scan "
    "at open: git status empty at HEAD cf85b5ce with origin/main level "
    "(0 ahead / 0 behind) and no .git/index.lock, zero unreplied @BigDomain "
    "dispatch rows in cph4/evolution-ledger.md, the content-addressed decisions "
    "diff reading new=0 against the stored 142-token baseline, the group orders "
    "tail unchanged at 2026-11-05 20:22 equal to the stored last_order, "
    "benchmarks refreshed 2026-11-03 inside the seven-day gate, and the debt "
    "gate naming CLAIM-FIRST item product-face-R2456 carried=27. CLAIM: R2481 "
    "shipped a panel that starts three faces and said in its own docstring that "
    "the lobby was deliberately not offered because it owns five sockets in one "
    "process; a person at /panel/ therefore could not bring up the face the "
    "product is actually about. AC-LBY1..AC-LBY6 were written in this window "
    "before the lobby leg of panel.py existed and before test_panel_lobby.py "
    "existed.",

    "2026-11-06 R2482 SHIPPED the lobby leg of src/sandbox/panel.py plus one "
    "registry row panel-lobby(6): the panel now publishes FOUR startable faces "
    "(checkout, ledger, ugc, lobby); starting the lobby assigns five distinct "
    "OS ports up front (ws/city/web/hub/gate), spawns src/sandbox/lobby/server.py "
    "through an argv vector led by sys.executable with CREATE_NO_WINDOW, waits "
    "until the HUB socket accepts, and only then publishes port=hub, "
    "url=http://host:hub/hub/ plus the whole ports map and the exact command "
    "that would reproduce it. The page needed no new markup because the table is "
    "rendered from /panel/api/state, so its footer sentence was rewritten from "
    "'only three faces start here' to the four-face truth rather than left "
    "lying; panel.html is 7738B now and still carries zero external references, "
    "the AI label, the non-advice note and the mock/no-real-charge statement.",

    "2026-11-06 R2482 PROOF: AC-LBY1..AC-LBY6 read SUITE PASS 6/6 TWICE with "
    "identical criterion lines both legs (qa/panel-lobby-R2482-a.log and "
    "-b.log, exit 0 each), and two adjacent suites stayed green in the same "
    "window (qa/panel-R2482-adjacent.log SUITE PASS 6/6, "
    "qa/start-all-R2482-adjacent.log SUITE PASS 6/6). LIVE leg "
    "qa/panel-lobby-live-R2482.log drove a REAL panel process over HTTP: panel "
    "port 51242 accepted, page 200 at 7738B, POST start lobby 200 with ports "
    "ws=51248 city=51249 web=51250 hub=51251 gate=51252 all distinct, hub "
    "accepted at the moment of the answer, GET the published URL 200 at 7104B, "
    "state then read lobby live=true port=51251 with the same command string, "
    "stop 200 left live=false, and the hub port refused a connect afterwards.",

    "2026-11-06 R2482 criterion amendments disclosed rather than hidden: (a) "
    "AC-PAN2 in test_panel.py pinned the published face list as exactly "
    "checkout/ledger/ugc; adding a fourth face would have made a shipped green "
    "criterion fail, so the pinned list gained lobby (and its module name in the "
    "command check) instead of the assertion being loosened - the comment in the "
    "suite names the reason; (b) AC-PAN4 used 'lobby' as its unknown-face "
    "example, which stopped being unknown this window, so the example moved to "
    "'nope' while the criterion (400 E_PANEL_UNKNOWN_FACE) is unchanged; (c) "
    "AC-LBY1 first expected the row module as 'src/sandbox/lobby/server.py' and "
    "the first run reported the real contract value 'sandbox/lobby/server.py' - "
    "the shipped panel already publishes rows relative to src/, so the "
    "expectation was corrected to the existing contract rather than the module "
    "being changed to satisfy a test-only prefix. No criterion was relaxed and "
    "no PASS was claimed before these fixes.",

    "2026-11-06 R2482 registry and debt: the registry moved 568 -> 569 suites "
    "and 4384 -> 4390 criteria by exactly one row panel-lobby(6). Because this "
    "window added product bytes plus a suite, the R2168 mixed-tree rule makes "
    "the NEXT window owe the battery on the committed tree BEFORE any further "
    "product byte; reconcile-battery-R2482 is appended first=no through the "
    "shipped debt_append with that pre-registered target, and the suite-matrix "
    "restamp is left to that verification window because this one ran no "
    "battery to stamp from.",

    "2026-11-06 R2482 honest disclosures: (a) a PRODUCT window worth 2 points on "
    "the Executive Protocol scale - a person can now start the lobby, the face "
    "the whole product is about, from the one panel page; (b) what it does NOT "
    "do: the panel is still not linked from the hub payload, so the hub page "
    "does not lead to it, and the hub's own liveness map does not know about a "
    "panel-started lobby; (c) the ws/city/gate/web ports the lobby opens are "
    "published but only the hub port is measured live by this panel; (d) Docker "
    "is absent on this host so a containerised bring-up stays unproved and is "
    "not claimed; (e) the real 19.9 debit and the real msgSecCheck still wait on "
    "CEO physical items (merchant id, mini-program appid/secret); (f) tasks.md "
    "was not touched, it is the P-47 canonical board.",

    "R2482 tokens: local=~12k api=0 api_reason=business window - one product "
    "leg (the panel really starts the lobby on five assigned ports and proves it "
    "by its hub socket), one self-contained page sentence corrected to the new "
    "truth, one six-criteria suite proved twice, two adjacent suites re-run "
    "green, three pinned criteria amended openly where the product legitimately "
    "moved them, one live end-to-end leg against a real panel process over HTTP, "
    "one debt row appended through its own writer, and the "
    "state/export/backlog/heartbeat closeout; zero cloud calls and zero external "
    "API touches",
]


def main():
    with io.open(STATE, encoding="utf-8") as handle:
        state = json.load(handle)
    before = os.path.getsize(STATE)
    state["tick"] = TICK
    state.setdefault("log", []).extend(LOG)
    data = json.dumps(state, ensure_ascii=False, indent=2, sort_keys=False)
    tmp = STATE + ".tmp"
    with io.open(tmp, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(data + "\n")
    os.replace(tmp, STATE)
    with io.open(STATE, encoding="utf-8") as handle:
        back = json.load(handle)
    after = os.path.getsize(STATE)
    print("STATE tick=%d log=%d before=%dB after=%dB readback=%s"
          % (back["tick"], len(back["log"]), before, after,
             "ok" if back["tick"] == TICK else "BAD"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())