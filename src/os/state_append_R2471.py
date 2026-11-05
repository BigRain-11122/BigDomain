"""R2471 closeout state append (one-off): business window receipt."""
import io
import json
import os
import sys

ROOT = r"C:\Users\sjs20\Desktop\FluxGroup\domain\BigDomain"
SRC = os.path.join(ROOT, "src", "os")
PATH = os.path.join(SRC, "state.json")

if SRC not in sys.path:
    sys.path.insert(0, SRC)

LINES = [
    "2026-11-05 R2471 BUSINESS window, taken on the CEO standing order OB-20261105-003656-879 (real output only) and SUPERSEDING the carried internal audit row product-face-R2456 by name - that row stays open and claimable at state/queue/tech.md:522 prefix AC-PFKC1 and is CARRIED, never dropped. Five-silence scan at open: git status empty at HEAD 34c752af equal to origin/main with no .git/index.lock, zero unreplied @BigDomain rows in the evolution ledger, the content-addressed decisions diff new=0 against the stored baseline (rows 289), the group orders tail unchanged at 2026-11-05 00:36 equal to the stored last_order, benchmarks refreshed 2026-11-03 inside the seven-day gate, queue head AC-PFKC1 with the floor MET. FINDING before any code, the one R2470 named as the candidate: the hub entry page published only lobby/city/checkout, so the P-47-2 token console R2469 shipped was unreachable from the single entry URL, and every published link was a promise - a reader could not tell a running face from a dead one without clicking.",

    "2026-11-05 R2471 SHIPPED the hub ledger face and a measured live map: src/sandbox/lobby/hub_page.py now publishes ledger + ledger_note + ledger_cmd (default port 8097) and face_ports, and answers GET /hub/api/faces?probe=1 with a live map built by TCP connect at request time (face_live, 0.35s, refused connect reads dead, never unknown); src/sandbox/lobby/hub.html gains a fourth card (link-ledger, id data-face=ledger) plus one live marker per face, all painted from that payload at call time, still zero external references; src/sandbox/lobby/server.py advertises --ledger-port (default 8097, named in the help text) and passes it into build_faces, so the published URL is the port the operator chose rather than a guess.",

    "2026-11-05 R2471 EVIDENCE, measured rather than asserted: AC-HLL1..AC-HLL6 were written into src/os/backlog.md BEFORE the module edit, the card and the suite existed, and src/sandbox/lobby/test_hub_ledger_live.py reads SUITE PASS 6/6 TWICE with byte-identical verdict lines (qa/hub-ledger-R2471-a.log and -b.log); the old face keys were compared value by value against a 14-key golden so the addition cannot have silently moved one, the live map was proved by opening a real listener on the checkout port (reads true) and closing it again (reads false) while an unrelated face stayed false, the page and interface stayed byte-identical on both slash forms with 404/405 intact, and two consecutive probe calls on a still world returned identical bodies. Adjacent suites test_hub_page.py and ledger/test_ledger_page.py were re-run green from inside AC-HLL6 rather than asserted.",

    "2026-11-05 R2471 LIVE, not a plan: qa/hub-ledger-live-R2471.log starts the real stack the way a person would - server.py with --web-port 8094 --city-http-port 8092 --hub-port 8095 --gate-port 8096, checkout_demo.py on 8093, ledger_page.py on 8097 against a temp db - and all five faces answered 200 (lobby 10077B, city 6653B, checkout 8051B, ledger 7977B, hub 6551B), GET /hub/api/faces?probe=1 answered live={checkout:true, city:true, gate:true, ledger:true, lobby:true} with the ledger URL and its exact start command in the same payload, every child was terminated with zero survivors, and the hub stopped answering afterwards (VERDICT PASS).",

    "2026-11-05 R2471 matrix and debt register: docs/sandbox-suite-matrix.md was regenerated stamp-aligned from the last eligible green evidence (qa/reconcile-all-R2470.log) through src/sandbox/suite_matrix.py --evidence plus --stamp-from and now reads 54266B at registry suites=563 criteria=4354, with --check byte-identical and its green line honestly 562/563 because no battery log carries the new suite yet. reconcile-battery-R2471 was opened first=no through the shipped debt_append at 121823B -> 122265B (readback=ok) because product src bytes changed and the registry moved 562->563 suites / 4348->4354 criteria, so the R2168 mixed-tree rule puts the battery first in the next window at the pre-registered 563 suites / 4354 criteria.",

    "2026-11-05 R2471 honest disclosures: (a) two business points for a page a person can open and click through, and the hub now shows which faces are alive instead of implying all are; (b) the ledger console is still a SEPARATE process - this window publishes its URL and the exact command and never claims it is running until a probe says so, so one URL still does not start four servers; (c) the real msgSecCheck, the real 19.9 debit and public opening stay blocked on CEO physical items (mini-program appid/secret, merchant id, server/record filing); (d) Docker is absent on this host, so a containerised bring-up stays unproved and is not claimed; (e) the live driver printed a substring check labelled NO-PROBE whose 'live' hit came from the words 'make this link live' in a note, so that one line proves nothing and is disclosed here rather than cited as evidence; (f) the window ran past its 25-minute budget on one suite, one live stack and the matrix/debt legs, named rather than hidden.",

    "R2471 tokens: local=~30k api=0 api_reason=business window - one additive face contract, one request-time TCP liveness map, one page card plus markers, one operator flag wired through, one six-criteria suite proved twice with identical verdict lines plus two adjacent suites re-run green, one real five-face live capture with zero survivors, one registry row, one stamp-aligned matrix regeneration with a byte-identical check, one battery debt row via its shipped CLI, and the state/export/backlog/heartbeat closeout; zero cloud calls and zero external API touches",
]


def main():
    import state_io
    with io.open(PATH, "r", encoding="utf-8", newline="") as handle:
        state = json.load(handle)
    if state["log"] and state["log"][-1] == LINES[-1]:
        print("already appended")
        return
    state["tick"] = 2471
    state["log"].extend(LINES)
    state["last_decision_rows"] = 289
    text = json.dumps(state, indent=2, ensure_ascii=False) + "\n"
    payload = state_io.canon(text).encode("utf-8")
    tmp = PATH + ".tmp"
    with io.open(tmp, "wb") as handle:
        handle.write(payload)
    os.replace(tmp, PATH)
    with io.open(PATH, "r", encoding="utf-8", newline="") as handle:
        back = json.load(handle)
    ok = (len(back["log"]) == len(state["log"]) and back["tick"] == 2471)
    print("APPEND tick=%d log_items=%d bytes=%d readback=%s"
          % (back["tick"], len(back["log"]), os.path.getsize(PATH),
             "ok" if ok else "MISMATCH"))
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main())