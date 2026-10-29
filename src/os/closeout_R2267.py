import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import state_io

PATH = os.path.join(os.path.dirname(os.path.dirname(BASE)), "src", "os",
                    "state.json")

raw = state_io.read_raw(PATH)
state = state_io.parse(state_io.decode(raw))

items = [
    "2026-10-29 R2267 (five-silence scan clean at open: tree clean with an "
    "empty git status --short and no index.lock; the queue gauge read main 5/5 "
    "tech 10/10 explore 10/10 FLOOR-MET with tech 11 open of which 1 gated and "
    "explore 10 open; decisions.md carries 289 non-empty rows and 189 "
    "content-addressed D/C/O/T tokens against the stored 194-token superset "
    "baseline with ZERO additions - the five apparent losses are the known "
    "group-side rotation and truncation artefacts and the baseline stays a "
    "superset so a later-restored token cannot masquerade as a new decision, so "
    "zero domain action; the group ledger carries the same three @BigDomain "
    "patrol rows already paid off with zero unreplied; the group orders tail is "
    "unchanged at the 2026-10-29 02:1x CEO-PROXY event round R2.48 already "
    "consumed in R2226; benchmarks refreshed 2026-10-29 inside the seven-day "
    "gate) - the P1 canonical rows stay blocked-on-CEO, the weekly proposal duty "
    "is met by BD-PROP-005, and the debt register named exactly one first=yes "
    "row (product-face-R2267), so this window claimed the top deliverable tech "
    "row rather than the one that row own note proposed: the R2248 f debt_gate "
    "seed, whose five criteria were already pinned in that row BEFORE any code. "
    "RESULT: src/os/debt_gate.py plus src/os/test_debt_gate.py - the register "
    "names a first=yes row for the next window and nothing stopped a window from "
    "simply not reading it, so the gate asks that one question before any work "
    "starts. Three honest outcomes and no fourth: CLAIM-FIRST naming "
    "item/opened/note/carried; OPEN-NONE covering BOTH an empty register and an "
    "all-first=no register, because both mean this window owes its own row; and "
    "a refusal when the register is missing, unreadable or malformed, because an "
    "absent file must never read as nothing owed. The row law is imported from "
    "debt_register instead of re-implemented (one owner, and a patched register "
    "verdict flows straight through), the module writes nothing and reads no "
    "clock, and the JSON carries the eleven pinned keys byte-stably. Evidence: "
    "SUITE PASS 5/5 double-run with an identical criterion digest (qa/"
    "debt-gate-R2267.log, single writer utf-8 LF through the R2261 capture "
    "callable, five adjacent os suites green inside the same capture), wired "
    "os-debt-gate(5). LIVE: DEBT GATE verdict=CLAIM-FIRST "
    "item=product-face-R2267 opened=R2266 carried=1 stale=no open=2 first=1. "
    "Queue ordering disclosed: rows 41 (docker absent on this machine), 54 "
    "(standing maintenance line with no defined next slice), 85 (product-gated) "
    "and 88 (AC-LN1..LN8 already delivered at R1727) were not deliverable faces "
    "and that judgement has now been re-derived by hand at R2257, R2259, R2263, "
    "R2266 and R2267 - which is exactly the queue_head seed this window "
    "registered rather than left as prose.",
    "R2267 tokens: local=~19k api=0 api_reason=product window on the debt "
    "register first item - one reader module with its five pre-registered "
    "criteria and its suite, one defect found by the suite and fixed in the "
    "this-window test rather than by widening a criterion (the JSON assertion "
    "counted lines in a one-line payload), one dogfooded evidence capture (two "
    "legs identical, five adjacent suites green), two live CLI readings, one "
    "runner wiring line, one real gap row seeded to hold the tech floor, and the "
    "queue/backlog/debt/state/export closeout; zero cloud calls and zero "
    "external API touches; the battery carries to R2268 as the register "
    "successor row",
    "R2267 self-heal check: BigDomain-OSLoop is registered and its principal "
    "still reads LogonType=InteractiveToken, which the 2026-09-29 machine law "
    "forbids for every lane task; src/os/register_loop_task.ps1 already passes an "
    "explicit S4U principal and needs an elevated shell to apply it, and this "
    "session runs unelevated, so the definition of the loop hosting this window "
    "was left untouched. Open local-lane item for an elevated window "
    "(thirty-third consecutive disclosure, registered as the stale row "
    "loop-s4u-reconcile in state/debt.md).",
]
state["log"].extend(items)
state["tick"] = 2267

body = json.dumps(state, ensure_ascii=False, indent=2)
canon = state_io.canon(body)
folder = os.path.dirname(os.path.abspath(PATH))
handle, temp = None, None
import tempfile
handle, temp = tempfile.mkstemp(dir=folder, prefix=".closeout_R2267_")
with os.fdopen(handle, "wb") as sink:
    sink.write(canon.encode("utf-8"))
    sink.flush()
    os.fsync(sink.fileno())
os.replace(temp, PATH)
back = state_io.read_raw(PATH)
if back != canon.encode("utf-8"):
    raise SystemExit("E_BACK_READ_MISMATCH")
report = state_io.layout(state_io.decode(back))
print("tick=%d items=%d" % (state["tick"], len(state["log"])))
print("layout: %s" % report)