"""R2331 closeout: fold first (the waterline is crossed), then tick + log items.

state.json measured 78731B against the 78500B gate before this window's append
(margin -231), so a fold must run before the closeout text lands. The window is
chosen from the real measurement (plan_fold with the same reserve the house
uses), the summary carries every token of the window, and the append is one
canonical atomic write with a predicted byte count and a read-back proof.

Pure ASCII, stdlib only, no network.
"""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import state_fold as SF  # noqa: E402
import state_io as SIO  # noqa: E402

STATE = os.path.join(ROOT, "src", "os", "state.json")
TICK = 2331
FOLD_NO = 621
RESERVE = 7000

ITEMS = [
    "2026-11-01 R2331 product window (five-silence scan clean at open: empty "
    "git status --short and no index.lock; the content-addressed diff of the "
    "group decisions.md against the stored baseline read NEW=0 over 61 live "
    "tokens, so no decision row was owed; the evolution ledger carries no "
    "@BigDomain row; the group orders tail is unchanged at the 2026-11-01 "
    "10:4x baseline R2321 already acked by number as non-execution; benchmarks "
    "refreshed 2026-11-01 inside the seven-day gate). The debt gate named "
    "product-face-R2331 first=yes and its note matched the board top, so this "
    "window claimed state/queue/tech.md:383 prefix AC-RET1, the R2308 "
    "retire_candidate seed whose AC-RET1..AC-RET6 were pinned INSIDE that row "
    "BEFORE the code (re-read, not re-run). PRODUCT: src/os/retire_candidate.py "
    "plus src/os/test_retire_candidate.py - the retirement question stops being "
    "three readings held in one head. The audit rows, the map collisions and "
    "the parity scan are all IMPORTED from their own readers (the suite patches "
    "EOA.audit, EOM.build and EVP.scan in turn and watches the verdict move, and "
    "asserts the module carries no re.compile, no hexdigest and no "
    "split_target, so there is no second declaration scan); RETIRE-READY needs "
    "all three conditions at once; and the blocker reason is pinned in one "
    "documented order - DECLARATION-STALE first (AC-RET3: an unresolved "
    "declaration is the one case where deleting the copy also deletes the only "
    "record of what it wrote), PARITY-DEBT second, COLLISION last - so a "
    "multi-blocker script still names one thing to work. SUITE PASS 6/6 twice "
    "with an identical criterion digest through evidence_capture with three "
    "adjacent suites green (qa/retire-candidate-R2331.log, 1262B), wired "
    "os-retire-candidate(6). LIVE on the real pile: 92 scripts, retire_ready=6 "
    "(evidence_R2248/2250/2253/2255/2257/2259), owned=86, stale=1 "
    "(evidence_R2213 reads NO-DECLARATION), parity_debt=85, collision=0, "
    "verdict=CANDIDATES - the six legacy per-round writers that evidence_capture "
    "replaced at R2261 are now named by a reading instead of guessed. The claim "
    "dropped tech claimable to 9, so one REAL gap row was seeded from this "
    "window own live reading (retire_accept, AC-RAC1..AC-RAC6 pre-registered, "
    "five anchors git grep -F zero-occupancy at HEAD) and the gauge closed "
    "FLOOR-MET main 5/5 tech 10/10 explore 10/10; the head moved to "
    "state/queue/tech.md:384 prefix AC-RAC1. The battery did not run here (the "
    "R2168 mixed-tree rule keeps it on a committed tree), so it is the "
    "successor row with the pre-registered target of 473 suites / 3814 criteria "
    "- exactly +1 suite / +6 criteria against R2330 (472/3808).",
    "R2331 tokens: local=~15k api=0 api_reason=product window on the debt "
    "register first item - one resolver module with its six pre-registered "
    "criteria and its suite (green on the second run after the runner wiring "
    "the last criterion asserts was landed), one dogfooded evidence capture "
    "with three adjacent suites, two live readings of the whole 92-script pile, "
    "one runner wiring line, one queue close and one real gap row seeded "
    "through the anchor check, one waterline fold with its archive append, and "
    "the debt/state/export/heartbeat/board closeout; zero cloud calls and zero "
    "external API touches; the battery carries to R2332",
    "R2331 self-heal check: BigDomain-OSLoop is registered and its principal "
    "still reads LogonType=InteractiveToken, which the 2026-09-29 machine law "
    "forbids for every lane task; src/os/register_loop_task.ps1 already passes "
    "an explicit S4U principal and needs an elevated shell to apply, and this "
    "session runs unelevated, so the definition of the loop hosting this window "
    "was left untouched. Open local-lane item for an elevated window "
    "(ninety-third consecutive disclosure, carried as the stale row "
    "loop-s4u-reconcile in state/debt.md).",
    "R2331 honest disclosures: (a) the first suite run was red on AC-RET6 "
    "alone, and the red was exactly what that criterion is for: it asserts the "
    "runner carries this window label, and the wiring had not been added yet - "
    "the wiring landed and the second run read 6/6, with no criterion widened "
    "and no module changed to turn a red green. (b) The live reading is a "
    "finding, not a green claim: six copies read RETIRE-READY and every one of "
    "them stays on disk, because this module never deletes, moves or runs "
    "anything - acting on the finding is the successor seed and needs a pinned "
    "acceptance record, not a silent rm. (c) The 85 PARITY-DEBT rows are "
    "inherited, not created: most legacy copies predate the SECTION ritual the "
    "parity reader asks about, which is exactly why the resolver refuses to "
    "call them retirable. (d) The queue row and the seeded row were edited as "
    "two direct text edits rather than through a predicted-delta helper; the "
    "gates were re-read afterwards (FLOOR-MET 5/5 10/10 10/10, head AC-RAC1, "
    "claimable 10) so the edit is verified by the readers rather than by a "
    "prediction. (e) The first live JSON capture was written through a shell "
    "redirection and landed as UTF-16 (the known dialect trap); the artifact "
    "was deleted and NO bytes from it are claimed - every live number above "
    "comes from a python-level reading. (f) tasks.md was left untouched: it is "
    "the P-47 canonical board and carries no row for this tech slice, disclosed "
    "rather than silently skipped.",
]


def fold_first():
    raw = io.open(STATE, "rb").read()
    state = json.loads(raw.decode("utf-8"))
    if any(line.startswith("Fold R2331:") for line in state["log"]):
        print("FOLD already applied this window; not folded twice")
        return
    chosen = None
    for end in range(3, 15):
        window = state["log"][1:end]
        tokens = set()
        for line in window:
            tokens |= set(SF.PAT.findall(line))
        summary = ("Fold R2331: log lines 2..%d folded verbatim into the "
                   "archive so the closeout fits the waterline; window tokens: "
                   "%s" % (end, " ".join(sorted(tokens))))
        plan, _text = SF.plan_fold(raw, state, 2, end, summary,
                                   reserve=RESERVE)
        print("candidate end=%d predicted=%dB gate_ok=%r tokens_missing=%d"
              % (end, plan["predicted_bytes"], plan["gate_ok"],
                 len(plan["tokens_missing"])))
        if plan["gate_ok"] and not plan["tokens_missing"]:
            chosen = (end, summary)
            break
    if not chosen:
        raise SystemExit("E_R2331_NO_WINDOW")
    result = SF.fold(ROOT, "R2331", FOLD_NO, 2, chosen[0], chosen[1],
                     reserve=RESERVE, execute=True)
    print("fold=%d window=2..%d predicted=%sB post=%sB margin=%s"
          % (FOLD_NO, chosen[0], result.get("predicted_bytes"),
             result.get("post_bytes", result.get("actual_bytes")),
             result.get("margin")))


def append_items():
    raw = io.open(STATE, encoding="utf-8", newline="").read()
    before = len(raw.encode("utf-8"))
    data = json.loads(raw)
    if data.get("tick") == TICK:
        raise SystemExit("E_R2331_ALREADY_CLOSED")
    data["tick"] = TICK
    data["log"].extend(ITEMS)
    canon = SIO.canon(json.dumps(data, ensure_ascii=False, indent=2))
    predicted = len(canon.encode("utf-8"))
    tmp = STATE + ".tmp-r2331c"
    with io.open(tmp, "w", encoding="utf-8", newline="") as handle:
        handle.write(canon)
    written = os.path.getsize(tmp)
    if written != predicted:
        os.remove(tmp)
        raise SystemExit("E_R2331_PREDICT %d != %d" % (written, predicted))
    os.replace(tmp, STATE)
    if os.path.exists(tmp):
        raise SystemExit("E_R2331_TEMP")
    back = json.loads(io.open(STATE, encoding="utf-8", newline="").read())
    layout = SIO.layout(io.open(STATE, encoding="utf-8", newline="").read())
    print("state before=%dB after=%dB tick=%d log_len=%d layout_ok=%r"
          % (before, os.path.getsize(STATE), back["tick"], len(back["log"]),
             layout.get("layout_ok")))


def main():
    fold_first()
    append_items()


if __name__ == "__main__":
    main()