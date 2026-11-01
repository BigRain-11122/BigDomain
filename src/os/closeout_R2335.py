"""closeout_R2335 - the round ledger for the product window.

Bumps the tick, appends the five log lines this window owes, closes the board
row it delivered and inserts the successor row. Dry run by default;
--execute writes utf-8 through one atomic replace with a read-back proof, then
the caller runs state_io --fix to land the house write canon.
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

TICK = 2335
TOKEN_RE = re.compile(r"[DC]-\d{8}-\d{2}")

LIVE = (
    "2026-11-01 R2335 product window (five-silence scan clean at open: empty "
    "git status --short and no .git/index.lock; the content-addressed diff of "
    "the group decisions.md against the stored baseline read NEW=0 over 61 "
    "live tokens, so no decision row was owed; the evolution ledger carries "
    "no @BigDomain row at all; the group orders tail is unchanged at the "
    "2026-11-01 10:4x baseline R2321 already acked by number as "
    "non-execution; benchmarks refreshed 2026-11-01 inside the seven-day "
    "gate). The debt gate named product-face-R2335 first=yes and its note "
    "matched the board top, so this window claimed state/queue/tech.md:385 "
    "prefix AC-RTA1, the R2310 residue_triage_append seed whose AC-RTA1.."
    "AC-RTA6 were read out of that row BEFORE the code. The row's own anchor "
    "claim was RE-MEASURED at HEAD instead of trusted: the five names hit "
    "twelve files, every one of them prose (closeout_R2320_state.py, "
    "closeout_R2321.py, closeout_R2322.py, closeout_R2325.py, "
    "closeout_R2333.py, state_close_R2330.py, docs/status-export.json, "
    "src/os/backlog.md, src/os/state.json, state/debt.md, "
    "state/queue/tech.md and export_lines_R2333.json), with ZERO executable "
    "path - named here rather than reported as the bare rc=1 the row "
    "claimed. PRODUCT: src/os/residue_triage_append.py plus "
    "src/os/test_residue_triage_append.py - the triage declaration could be "
    "pinned but accepting ONE more round meant re-running the R2310 "
    "regeneration helper, which rewrites every entry from the live reading "
    "and therefore silently absorbs a DISAGREES into a TRIAGED entry. One "
    "dated append is now its own operation: the declaration comes from "
    "RT.load_declaration, the live residue from RT.live_residue, the "
    "candidate is validated by RT.shape and judged by RT.judge (a patched "
    "reader of either kind flows straight through, and the module carries no "
    "second declaration loader and no re.compile); a round already declared "
    "refuses E_RTA_DUPLICATE naming the existing status, declared_by and "
    "until; a round whose live status disagrees refuses E_RTA_DISAGREES "
    "naming BOTH statuses; an until earlier than its own declared_by refuses "
    "E_RTA_UNTIL_BEFORE_DECL; the write is a raw-text splice whose prefix and "
    "suffix are byte-identical to the file it read, so every neighbour entry "
    "survives untouched; and exit 0 is granted only when the rewritten file "
    "re-reads TRIAGED through the shipped reader. SUITE PASS 6/6 twice "
    "identical through evidence_capture with four adjacent suites green in "
    "the same capture (qa/residue-triage-append-R2335.log, 1255B, legs=2 "
    "identical=True adjacent=4 fails=0), wired os-residue-triage-append(6). "
    "LIVE: `--check --round R2335` on the real declaration reads "
    "declaration=PINNED declared_by=R2331 entries=197 residue=- "
    "verdict=TRIAGED, so the honest live outcome is NOTHING-TO-APPEND - no "
    "byte of the real declaration was touched, and the module is the "
    "treatment rather than a forced write. Queue: the delivered row was "
    "closed and one REAL gap row seeded in the same window "
    "(residue_triage_decl_reason, AC-RTD1..AC-RTD6 pre-registered, five "
    "anchors zero-occupancy, written from the drift measured this window: "
    "the declaration head still claims declared_by R2331 while entries "
    "appended at R2333 and R2334 carry their own), so the gauge reads "
    "FLOOR-MET main 5/5 tech 10/10 explore 10/10 with the head at "
    "state/queue/tech.md:386 prefix AC-GDIW1. The full reconcile battery "
    "carries to R2336 per the R2168 mixed-tree rule, pre-registered at 475 "
    "suites / 3826 criteria (+1 suite / +6 criteria against R2334 474/3820 "
    "from this window's own os-residue-triage-append suite)."
)

TOKENS = (
    "R2335 tokens: local=~18k api=0 api_reason=product window on the debt "
    "gate first item - one append module with its six pre-registered "
    "criteria and its suite (green on the second run after this window's own "
    "fixture passed a later round where it meant an earlier one), one "
    "dogfooded evidence capture with four adjacent suites, one live read-only "
    "check of the real declaration, one runner wiring line, one queue close "
    "and one real gap row seeded through the anchor check, and the "
    "state/export/heartbeat/board closeout; zero cloud calls and zero "
    "external API touches; the battery carries to R2336"
)

SELF_HEAL = (
    "R2335 self-heal check: BigDomain-OSLoop is registered and its principal "
    "still reads LogonType=InteractiveToken, which the 2026-09-29 machine law "
    "forbids for every lane task; src/os/register_loop_task.ps1 already "
    "passes an explicit S4U principal and needs an elevated shell to apply, "
    "and this session runs unelevated, so the definition of the loop hosting "
    "this window was left untouched. Open local-lane item for an elevated "
    "window (ninety-seventh consecutive disclosure, carried as the stale row "
    "loop-s4u-reconcile in state/debt.md)."
)

DECISION_GATE = (
    "R2335 decision gate (D-20260930-19 step 2): the content-addressed diff "
    "of the group decisions.md against the stored baseline read NO new tokens "
    "(new=[] over 61 live tokens), and the evolution ledger carries no "
    "@BigDomain row at all, so nothing was executed, rejected or acknowledged "
    "this window and the baseline is unchanged."
)

HONEST = (
    "R2335 honest disclosures: (a) the first suite run was red 5/6 on AC-RTA4 "
    "alone, and the cause was THIS window's fixture, never the criterion and "
    "never the module: the guard leg passed 'until R9000' believing it "
    "earlier than declared_by R2335, while 9000 is LATER - the guard "
    "correctly did not fire, and the fixture was corrected to R2000. (b) The "
    "live run appends NOTHING: the real declaration has no untriaged round, "
    "so `--check` reads residue=- and the shipped module is the treatment for "
    "a residue round that has not appeared yet - a window that appended to a "
    "healthy declaration would be the defect this face exists to prevent. "
    "(c) The anchor check was re-measured and all five names hit prose only, "
    "which is a weaker and more honest statement than the row's own 'rc=1' "
    "claim; the twelve files are named in the round line. (d) The seed row "
    "offered '(or retiring one)' as a second operation and this window "
    "deliberately shipped only the append: an entry's `until` already "
    "expresses retirement and residue_triage reads an expired entry as "
    "EXPIRED, so a second write path would owe its own pre-registration - "
    "disclosed rather than silently dropped. (e) tasks.md was left untouched: "
    "it is the P-47 canonical board and carries no row for this tech slice, "
    "disclosed rather than silently skipped. (f) state.json measured 72216B "
    "at open, 6284B under the 78500B gate, so no fold was owed and none ran."
)

BOARD_DONE = (
    "- [x] [done 2026-11-01 R2335] R2335 first item: PRODUCT on the row the "
    "reader named - `python src/os/queue_head.py --head tech` read "
    "state/queue/tech.md:385 prefix AC-RTA1 at open (skipped_before=4, "
    "claimable=10). src/os/residue_triage_append.py plus "
    "src/os/test_residue_triage_append.py shipped with AC-RTA1..AC-RTA6 "
    "pre-registered in that row BEFORE the code: the declaration and every "
    "status come from residue_triage (a patched loader or live reader flows "
    "straight through), a duplicate refuses by naming the existing entry, a "
    "live DISAGREES refuses naming BOTH statuses, an until before its own "
    "declared_by refuses, the write is a raw-text splice that leaves every "
    "neighbour entry byte-identical with one atomic replace and a read-back, "
    "and exit 0 is granted only when the file re-reads TRIAGED. SUITE PASS "
    "6/6 twice identical through evidence_capture with four adjacent suites "
    "green (qa/residue-triage-append-R2335.log, 1255B), wired "
    "os-residue-triage-append(6). LIVE --check --round R2335 reads "
    "entries=197 residue=- verdict=TRIAGED, so NOTHING-TO-APPEND and no real "
    "byte was touched."
)

BOARD_NEXT = (
    "- [ ] [carried 2026-11-01 R2335] R2336 first item: THE FULL RECONCILE "
    "BATTERY on the committed R2335 tree with zero product edits (the R2168 "
    "mixed-tree rule), pre-registered at 475 suites / 3826 criteria (+1 suite "
    "/ +6 criteria against R2334 474/3820 from this window's "
    "os-residue-triage-append suite). After that the product face resumes at "
    "`python src/os/queue_head.py --head tech`, which read "
    "state/queue/tech.md:386 prefix AC-GDIW1 (gate_decl_identity_wire) at "
    "close; the seeded successor residue_triage_decl_reason "
    "(AC-RTD1..AC-RTD6, anchors zero-occupancy at HEAD) carries the drift "
    "measured this window - the declaration head still claims declared_by "
    "R2331 while entries appended at R2333 and R2334 carry their own. Also "
    "open and needing an ELEVATED shell: BigDomain-OSLoop reads "
    "LogonType=InteractiveToken (ninety-seventh consecutive disclosure; "
    "carried as the stale row loop-s4u-reconcile in state/debt.md)."
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
    print("backlog carried row: %s" % backlog[3][:90])
    if "--execute" not in argv:
        print("DRY RUN - wrote nothing")
        return 0
    state["tick"] = TICK
    state["last_dec_tokens"] = tokens
    state["last_decision_rows"] = len(decisions.split("\n"))
    log = state.get("log") or []
    for line in (LIVE, TOKENS, SELF_HEAL, DECISION_GATE, HONEST):
        log.append(line)
    state["log"] = log
    write_text(STATE, json.dumps(state, ensure_ascii=False, indent=2) + "\n")
    backlog[3] = BOARD_DONE
    backlog.insert(4, BOARD_NEXT)
    write_text(BACKLOG, "\n".join(backlog))
    print("WROTE state.json and backlog.md with read-back")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))