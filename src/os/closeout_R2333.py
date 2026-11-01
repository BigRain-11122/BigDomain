"""closeout_R2333 - the round ledger for the product window.

Bumps the tick, appends the four log lines this window owes, marks the carried
board row done and inserts the successor. Dry run by default; --execute writes
utf-8 through one atomic replace with a read-back proof, then the caller runs
state_io --fix to land the house write canon.
"""

import io
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
STATE = os.path.join(ROOT, "src", "os", "state.json")
DECISIONS = os.path.join(os.path.dirname(os.path.dirname(ROOT)),
                         "docs", "decisions.md")
BACKLOG = os.path.join(ROOT, "src", "os", "backlog.md")

TICK = 2333
TOKEN_RE = re.compile(r"[DC]-\d{8}-\d{2}")

LIVE = (
    "2026-11-01 R2333 product window (five-silence scan clean at open: empty "
    "git status --short and no .git/index.lock; the content-addressed diff of "
    "the group decisions.md against the stored baseline read NEW=0 over 61 "
    "live tokens, so no decision row was owed; the evolution ledger carries "
    "no @BigDomain row at all; the group orders tail is unchanged at the "
    "2026-11-01 10:4x baseline R2321 already acked by number as "
    "non-execution; benchmarks refreshed 2026-11-01 inside the seven-day "
    "gate). The debt gate named product-face-R2333 first=yes and its note "
    "matched the board top, so this window claimed state/queue/tech.md:384 "
    "prefix AC-RAC1, the R2331 retire_accept seed whose AC-RAC1..AC-RAC6 were "
    "pinned INSIDE that row BEFORE the code (re-read, not re-run; a fresh "
    "zero-occupancy anchor check at HEAD found retire_accept, AC-RAC, E_RAC, "
    "os-retire-accept and test_retire_accept all git grep -F rc=1). PRODUCT: "
    "src/os/retire_accept.py plus src/os/test_retire_accept.py - "
    "retire_candidate named the six copies that are safe to retire and "
    "nothing could ACT on that reading: the resolver is read-only by "
    "contract and a hand rm leaves no record of when a copy became safe, why, "
    "or until when the judgement held. The new module pins one acceptance "
    "declaration (state/queue/retire_accept.json) and reads it back against "
    "the live resolver, with exactly one class per entry and the four classes "
    "disjoint by construction: ACCEPTED (still RETIRE-READY inside its "
    "window), EXPIRED (names its until round), UNMATCHED (no live row at all) "
    "and STALE-DECISION (reads OWNED again with the current blocker named). "
    "Precedence is pinned and documented - the two integrity classes outrank "
    "expiry, and between them 'no row at all' outranks 'owned'. A missing "
    "declaration reads UNPINNED at exit 2 with the full live candidate list "
    "instead of a fabricated green, and the writer refuses a duplicate "
    "script, an until earlier than its own declaring round, and a script the "
    "live resolver does not read RETIRE-READY. SUITE PASS 6/6 twice with an "
    "identical criterion digest D1F1F5649B84F963 through evidence_capture "
    "with four adjacent suites green (qa/retire-accept-R2333.log 1282B), "
    "wired os-retire-accept(6). LIVE AND DOGFOODED: the declaration was "
    "pinned empty and then filled through the module own append path - six "
    "accepts for the six measured RETIRE-READY copies (R2248/2250/2253/2255/"
    "2257/2259) with until=R2350, every append one atomic replace read back "
    "at its predicted byte count (48 -> 270 -> 493 -> 716 -> 939 -> 1162 -> "
    "1385B); the CLI now reads pinned=yes entries=6 accepted=6 expired=0 "
    "unmatched=0 stale_decision=0 pending=0 verdict=PINNED at exit 0, with a "
    "byte-stable --json over the pinned keys (two runs identical). The module "
    "never deletes anything: acting on an accepted retirement is the "
    "successor seed."
)

SELF_HEAL = (
    "R2333 self-heal check: BigDomain-OSLoop is registered and its principal "
    "still reads LogonType=InteractiveToken, which the 2026-09-29 machine law "
    "forbids for every lane task; src/os/register_loop_task.ps1 already passes "
    "an explicit S4U principal and needs an elevated shell to apply, and this "
    "session runs unelevated, so the definition of the loop hosting this "
    "window was left untouched. Open local-lane item for an elevated window "
    "(ninety-fifth consecutive disclosure, carried as the stale row "
    "loop-s4u-reconcile in state/debt.md)."
)

HONEST = (
    "R2333 honest disclosures: (a) the first suite run was red 5/6 and the "
    "sixth criterion CRASHED, and both causes were this-window TEST defects, "
    "never a criterion widened and never the module: the AC-RAC3 and AC-RAC5 "
    "CLI legs spawned the module as a subprocess against a fixture world with "
    "an EMPTY src/os, so the live resolver honestly refused E_RAC_NO_INPUT "
    "(exit 3) and the JSON leg parsed empty stdout - the fix was to give "
    "those worlds one copy that performs the whole ritual, so the CLI legs "
    "exercise the unpatched resolver; the module source did not change across "
    "the fix. (b) The live acceptance is a RECORD, not a deletion: all six "
    "copies stay on disk byte-identical, and the acting step (a MOVE into a "
    "quarantine path, never a delete) is the seeded successor retire_apply. "
    "(c) The declaration was seeded as an empty pinned file before the first "
    "accept, so the first append's before_bytes=48 is that seed rather than a "
    "measurement of anything else, and it is disclosed because a 48-byte "
    "'before' would otherwise look like a lost file. (d) One judgement text "
    "was applied to all six entries (declaration resolved, ritual complete, "
    "no collision at R2333, superseded by evidence_capture); it is a single "
    "measured judgement over six rows, not six independent reasons, and it is "
    "named here rather than dressed up. (e) The writer's E_RAC_NOT_READY "
    "refusal is ADDED at the birth site beyond the pinned criteria text, "
    "because accepting a copy the resolver does not read RETIRE-READY is a "
    "record that can never be acted on; it is a tightening, not a widened "
    "criterion, and AC-RAC5 still pins the exit codes. (f) The waterline was "
    "crossed by this window's own append estimate, so fold 622 moved log "
    "lines 1..9 (two older fold markers plus the R2319 tail and the whole "
    "R2320 block) verbatim into logs/state-log-archive-2026-11.md, predicted "
    "64804B equal to measured 64804B; the fold-creates-residue law did not "
    "fire this window because fuse rounds R2319/R2320 both sit on CLOSED "
    "rows. (g) tasks.md was left untouched: it is the P-47 canonical board "
    "and carries no row for this tech slice, disclosed rather than silently "
    "skipped."
)

LEDGER = (
    "R2333 tokens: local=~22k api=0 api_reason=product window on the debt "
    "register first item - one acceptance reader/writer with its six "
    "pre-registered criteria and its suite (green on the second run after "
    "this window test fixtures were corrected against the measured CLI "
    "codes), one dogfooded evidence capture (two legs identical, four "
    "adjacent suites green), six live accepts through the module own append "
    "path each proved by read-back at its predicted byte count, three live "
    "CLI readings of the real declaration, one runner wiring line, one queue "
    "close and one real gap row seeded through the anchor check, one "
    "waterline fold with its archive append, and the debt/state/export/"
    "heartbeat/board closeout; zero cloud calls and zero external API "
    "touches; the battery carries to R2334"
)

BOARD_DONE = (
    "- [x] [done 2026-11-01 R2333 - product window on the debt gate first "
    "item: src/os/retire_accept.py plus src/os/test_retire_accept.py shipped "
    "with AC-RAC1..AC-RAC6 pre-registered in the R2331 queue row BEFORE the "
    "code; verdicts imported from retire_candidate, four disjoint classes "
    "(ACCEPTED / EXPIRED / UNMATCHED / STALE-DECISION), UNPINNED at exit 2 "
    "with the live candidate list, atomic append proved by read-back; SUITE "
    "PASS 6/6 twice identical digest D1F1F5649B84F963 "
    "(qa/retire-accept-R2333.log 1282B) with four adjacent suites green; "
    "state/queue/retire_accept.json pinned and then filled through the module "
    "own append path - six RETIRE-READY copies (R2248/2250/2253/2255/2257/"
    "2259) accepted until R2350, live reading verdict=PINNED at exit 0]"
)

BOARD_NEXT = (
    "- [ ] [carried 2026-11-01 R2333] R2334 first item: THE BATTERY on the "
    "committed R2333 tree with zero product edits (the R2168 mixed-tree "
    "rule), pre-registered at 474 suites / 3820 criteria (+1 suite / +6 "
    "criteria against R2332 473/3814 from this window os-retire-accept "
    "suite), and any larger delta must be named rather than swept. After that "
    "the product face resumes at the tech head `python src/os/queue_head.py "
    "--head tech` names (state/queue/tech.md:385 prefix AC-RTA1, "
    "residue_triage_append), and the seeded successor retire_apply "
    "(AC-RAP1..AC-RAP6, anchors zero-occupancy at HEAD) is the acting step "
    "for the six ACCEPTED copies - a MOVE into a quarantine path, never a "
    "delete. Also open and needing an ELEVATED shell: BigDomain-OSLoop reads "
    "LogonType=InteractiveToken (ninety-fifth consecutive disclosure; carried "
    "as the stale row loop-s4u-reconcile in state/debt.md)."
)


def read_text(path):
    with io.open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def write_text(path, text):
    temp = path + ".tmp"
    with io.open(temp, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    os.replace(temp, path)
    with io.open(path, "r", encoding="utf-8") as handle:
        back = handle.read()
    if back != text:
        raise SystemExit("E_READBACK %s" % path)
    if os.path.exists(temp):
        raise SystemExit("E_RESIDUE %s" % path)


def main(argv):
    state = json.loads(read_text(STATE))
    decisions = read_text(DECISIONS) if os.path.isfile(DECISIONS) else ""
    tokens = sorted(set(TOKEN_RE.findall(decisions)))
    backlog = read_text(BACKLOG).split("\n")
    print("tick %d -> %d" % (state.get("tick"), TICK))
    print("decision tokens: stored=%d live=%d new=%s"
          % (len(state.get("last_dec_tokens") or []), len(tokens),
             sorted(set(tokens) - set(state.get("last_dec_tokens") or []))))
    print("backlog head: %s" % backlog[2][:70])
    if "--execute" not in argv:
        print("DRY RUN - wrote nothing")
        return 0
    state["tick"] = TICK
    state["last_dec_tokens"] = tokens
    state["last_decision_rows"] = len(decisions.split("\n"))
    log = state.get("log") or []
    for line in (LIVE, SELF_HEAL, HONEST, LEDGER):
        log.append(line)
    state["log"] = log
    write_text(STATE, json.dumps(state, ensure_ascii=False, indent=2) + "\n")
    backlog[2] = BOARD_DONE
    backlog.insert(3, BOARD_NEXT)
    write_text(BACKLOG, "\n".join(backlog))
    print("WROTE state.json and backlog.md with read-back")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))