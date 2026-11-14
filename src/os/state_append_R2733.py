"""state_append_R2733 - record the R2733 product window in src/os/state.json.

Every number below was read in this window, not carried from the queue note:
the registry by import at 675 suites / 5026 criteria / 675 unique names / 675
unique paths, the live binding reading at scanned=2265 bound=21 unbound=1
out_of_scope=2238 unparsed=12, the evidence file at 2951 bytes with two
identical legs, the AST-versus-regex gap at 22 real calls in 15 files against
52 regex occurrences in 32 files, the designed matrix ROWS-MISMATCH at
doc-rows 674 against registry-rows 675 with no byte written, and the debt
register moving open 35 -> 36 across one close and two appends.
"""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(BASE, "state.json")
sys.path.insert(0, BASE)

import state_io  # noqa: E402

ITEMS = [
    "2026-11-14 R2733 PRODUCT window on AC-CEPB1..AC-CEPB6 (state/queue/tech.md:702, pinned at R2501 BEFORE any code): shipped src/os/closeout_export_parity_wire_binding_consumer.py plus its six-criteria suite. Five readings at open: git status EMPTY at HEAD 2b9512bd equal to origin/main with no index.lock; ZERO @BigDomain rows in the group ledger; the content-addressed decisions face read tokens=69 against a baseline of 266 with new=0; the group orders tail is the 2026-11-14 01:3x BigStream seat row already carried as knowledge-only; benchmarks_refreshed 2026-11-14 inside the seven-day gate. debt_gate read CLAIM-FIRST item=product-face-R2732, queue_head read tech line=702 prefix AC-CEPB1 claimable=12, queue_floor read FLOOR-MET 5/5 13/10 10/10.",
    "R2733 THE DEFECT WAS RE-MEASURED ON THE REAL TREE BEFORE ANY BYTE, and the measurement changed the design: a regex over CEPW.publish( reads 52 occurrences in 32 src/os files while the AST reader finds 22 REAL publish calls in 15 files, because the rest are publish lines printed inside string literals and calls on other modules. So the face derives its caller set with ast.parse (a string literal is never an ast.Call) and never with a pattern over bytes; twelve files in the tree do not parse at all and are NAMED in an unparsed list rather than silently folded into OUT-OF-SCOPE.",
    "R2733 THE LIVE LEG FOUND ONE REAL UNBOUND CALLER, which is the product value of the window: on the shipped tree the reading is scanned=2265 bound=21 unbound=1 out_of_scope=2238 unparsed=12, and the single UNBOUND row is closeout_R2385.py:159 - its text carries no json composition at all, so first differing field export_ts and other=(uncomposed). Every other real caller reads BOUND with its own document composition and its bytes unchanged.",
    "R2733 PROOF: AC-CEPB1..AC-CEPB6 SUITE PASS 6/6 twice through the shipped capture callable with an IDENTICAL digest E038F813C7AD2EF87BB68D288D5CA89519EF2A63A92F37D6629ADA70FB9C5F53 (qa/closeout-export-parity-wire-binding-consumer-R2733.log, 2951 bytes, utf-8, bom=False, crlf=0, lone_cr=0, nul=0, legs=2 identical=True rc=0,0, adjacent=5 green=5; one adjacent file test_closeout_export_parity_text_binding.py emits no SUITE line while exiting rc=0, named here so the next window does not read it as a missing leg). The suite proves the string-literal case directly: a fixture that only PRINTS a publish call reads OUT-OF-SCOPE, and a fixture that imports the wire without publishing reads OUT-OF-SCOPE too.",
    "R2733 REGISTRY, BOARD, MATRIX AND DEBT THROUGH THE SHIPPED WRITERS: one runner row os-closeout-export-parity-wire-binding-consumer(6) wired after the shape-typing row; the registry re-measured BY IMPORT at 675 suites / 5026 criteria / 675 unique names / 675 unique paths (674/5020 before this window). docs/sandbox-suite-matrix.md read the DESIGNED ROWS-MISMATCH (doc-rows 674 against registry-rows 675, evidence qa/reconcile-all-R2731.log leg 674/674) with NO byte written - the restamp belongs to the adopting window of the battery this window registers. tech row 702 was closed with its done stamp. Debt: product-face-R2732 closed at line 439 (open 35->34, done 386->387, readback ok), product-face-R2733 appended first=no naming queue head state/queue/tech.md:703 prefix AC-DFOB1, and reconcile-battery-R2733 appended first=yes because this window moved product src and one registry row; debt_gate now reads CLAIM-FIRST item=reconcile-battery-R2733 open=36, queue head is tech line=703 AC-DFOB1 claimable=11 and queue_floor reads FLOOR-MET 5/5 11/10 10/10.",
    "R2733 honest disclosures: (a) ONE product point by the Executive Protocol scale - a runnable census that names one real unbound caller, but nothing a CEO can newly open, and every P-47 business face still waits on CEO physical pieces (merchant id, mini-program appid/secret); (b) this window DID NOT run a battery and claims none: it moved product src and one registry row, so reconcile-battery-R2733 is registered first=yes and the matrix green line is one row behind BY DESIGN until that leg lands; (c) the twelve unparsed files are pre-existing in this tree and this window neither created nor repaired them - they are named, not swept; (d) the one UNBOUND caller closeout_R2385.py:159 was MEASURED and named, not repaired, because repairing a closeout script is not in this row's criteria; (e) the R2731 dead per-round export hook in src/os/export_R2431.py is STILL OWED and now overdue by two windows, and it is carried to the next board line again rather than fixed inside a product window whose criteria do not cover it; (f) src/os still carries more than 190 one-off state_append_R*.py scripts, pre-existing bloat this window neither created nor cleaned; (g) tasks.md was not touched, it is the P-47 canonical board; (h) Docker is absent on this host; (i) BigDomain-OSLoop still reads InteractiveToken and needs an ELEVATED shell for its S4U re-registration (carried ceo-pending physical item loop-s4u-reconcile).",
    "R2733 tokens: local=~14k api=0 api_reason=product window - one five-silence scan with the debt gate, the queue head, the queue floor and the content-addressed decisions face, one AST-versus-regex measurement of the caller set before any byte, one face plus one six-criteria suite shipped, one suite run green plus one twice-through capture with an identical digest and five adjacent suites, one live reading on the real tree naming a single unbound caller, one registry count by import on four axes, one designed matrix ROWS-MISMATCH with no byte written, one board close, one debt close and two debt appends with readback, and the state/export/heartbeat closeout; zero cloud calls and zero external API touches",
]


def main():
    text = state_io.decode(state_io.read_raw(STATE))
    data = json.loads(text)
    data["tick"] = int(data.get("tick", 0)) + 1
    log = data.get("log") or []
    log.extend(ITEMS)
    data["log"] = log
    new_text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    new_text = state_io.canon(new_text)
    # state_io.write_canon is payload-preserving by design (layout repair only),
    # so an append goes through its own atomic replace and is proved by a
    # read-back parse of the written bytes.
    temp = STATE + ".tmp"
    with io.open(temp, "w", encoding="utf-8", newline="\n") as sink:
        sink.write(new_text)
    os.replace(temp, STATE)
    back = json.loads(state_io.decode(state_io.read_raw(STATE)))
    ok = back["tick"] == data["tick"] and back["log"] == data["log"]
    print("TICK %s LINES %d OK %s LAST %s"
          % (back["tick"], len(back["log"]), ok, back["log"][-1][:60]))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
