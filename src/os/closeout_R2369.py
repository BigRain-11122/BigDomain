"""closeout_R2369.py - append this window's items and fold if the gate demands.

One-off for the round, same shape as closeout_R2368: the state file is written
through state_io.canon and any fold runs through state_fold.fold.

Usage: python src/os/closeout_R2369.py
"""

import io
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import state_fold  # noqa: E402
import state_io  # noqa: E402

STATE = os.path.join(REPO, "src", "os", "state.json")
GATE = 78500
RESERVE = 6000
FOLD_BASE = 645

ITEMS = [
    "2026-11-02 R2369 verification-then-product window (five-silence scan clean "
    "at open: empty git status at 74d94279, no .git/index.lock; LEDGER "
    "atbd_lines=0 unreplied_groups=0, DEC rows=124 tokens=81 new=0, group "
    "orders tail still the 2026-11-01 10:4x model-policy baseline already "
    "acknowledged as non-execution, benchmarks refreshed 2026-11-02 inside the "
    "seven-day gate). The debt gate named CLAIM-FIRST "
    "item=reconcile-battery-R2368, so the battery ran FIRST on the committed "
    "tree: RUNNER PASS 495/495 suites green plus reconcile controls 7/7 in "
    "945.9s with birth-site TMP RECLAIM 932/932 worlds 326.59 MiB busy=0 "
    "failed=0 (qa/reconcile-all-R2369.log, 803489B, single writer utf-8 LF "
    "through src/os/battery_stream.py, never a shell redirection) and criteria "
    "total 3946 EXACTLY as pre-registered (494/3940 at HEAD plus this window "
    "os-queue-floor-reading-wire suite), so the prediction matched the "
    "measurement with no correction and nothing to name.",
    "R2369 follow-up sections and matrix: the four sections ran through "
    "src/os/battery_followup.py and the matrix section FAILED first on the "
    "stale doc (on-disk=47273B regenerated=47371B) and did NOT rewrite it, "
    "which is the designed order; src/sandbox/suite_matrix.py regenerated "
    "docs/sandbox-suite-matrix.md to 495 suites / 3946 criteria (47371B) and "
    "the re-run read all four PASS (matrix byte-identical, fingerprint CLEAN 5 "
    "domains, profile --check byte-identical, census DRIFT-CLEAN) for VERDICT "
    "R2369 PASS. One CLI shape was learned rather than assumed: "
    "battery_followup --round takes an INTEGER, not R<n>, and the R<n> form "
    "refuses at exit 1 E_BFU_BAD_ARGS - recorded because it cost one call.",
    "R2369 product face, the row the reader named: CLAIMED "
    "state/queue/tech.md:414 prefix AC-RTAB1 (residue_triage_append_batch), "
    "whose AC-RTAB1..AC-RTAB6 were pinned INSIDE that row at R2355 BEFORE any "
    "code, after a fresh anchor check at HEAD - the face, its suite, its "
    "runner label and E_RTAB were git grep -F zero-occupancy or prose-only "
    "(src/os/append_R2355_fold_residue.py and src/os/splice_residue_R2366.py "
    "mention the name only as the pain they are, recorded rather than "
    "reported as a clean null).",
    "R2369 the wire: shipped src/os/residue_triage_append_batch.py plus "
    "src/os/test_residue_triage_append_batch.py. Several (round, status) pairs "
    "land in ONE call, which is the capability the single-entry writer cannot "
    "have: it demands a TRIAGED file after each entry, so the three rounds "
    "fold 640 created at once (R2345, R2346, R2348) could not go through the "
    "shipped channel and were spliced by a one-off script for the seventh "
    "time. The declaration reader, the status vocabulary, the shape check and "
    "the judge all stay owned by residue_triage (RT.load_declaration, "
    "RT.live_residue, RT.shape, RT.judge are imported) and the entry layout "
    "stays owned by residue_triage_append, whose entry_text the batch renders "
    "through, so this file holds no second parser and no second formatter. "
    "Every pair is validated before a byte moves (duplicate in the call, "
    "duplicate declared, not in the residue, DISAGREES naming both statuses), "
    "the file is judged BEFORE the write so a partial batch refuses and names "
    "the rounds it would leave behind, and the write is ONE atomic replace at "
    "a predicted size with a per-entry re-read and no .tmp residue.",
    "R2369 evidence and board: SUITE PASS 6/6 twice with an identical "
    "criterion digest plus four adjacent suites green "
    "(qa/residue-triage-append-batch-R2369.log, 1246B, legs=2 identical=True "
    "adjacent=4 fails=0, single writer utf-8 LF through "
    "src/os/evidence_capture.py), wired os-residue-triage-append-batch(6) in "
    "src/sandbox/reconcile_all.py. LIVE, not a plan: on the real tree "
    "`residue_triage_append_batch.py --check --round 2369` reads entries "
    "222->222 declaration=PINNED verdict=TRIAGED residue=- at exit 0, i.e. "
    "the declaration carries nothing to append today, so no real byte was "
    "touched and the value shipped is the channel (proved on fixtures), not a "
    "live catch. Tech row 414 stamped [done 2026-11-02 R2369] and one REAL "
    "measured gap row seeded (residue_batch_status_face, AC-RSBF1..AC-RSBF6 "
    "pre-registered in that row, five anchors zero-occupancy), from this "
    "window own pain: --check names the rounds awaiting an entry and no live "
    "status at all, so composing a --pair list means running another tool and "
    "guessing, and this window own first fixture guessed wrong. Gauge after "
    "the stamp and the seed reads FLOOR-MET main 5/5 tech 10/10 explore 10/10.",
    "R2369 honest disclosures: (a) three suite criteria were RED on the first "
    "runs and all three were this window own fixtures, not the module: the "
    "fixture rows were built as `- [x]` closed rows and the live reader "
    "therefore reports DELIVERED where the fixture declared STAMP-ONLY-OPEN; "
    "the fixture window's `until` was R2360 while the checking round is R2369, "
    "so the judge read the seed entry as EXPIRED and the batch correctly "
    "refused; and AC-RTAB5 expected exit 0 from the single-entry --check while "
    "the honest answer with two undeclared rounds is 2. Each was fixed in the "
    "test against the module's own measured law, and no criterion was "
    "widened. (b) src/os/queue_R2369.py stamps the row by rewriting the whole "
    "file through one write; the read-back is proved but there is no "
    "byte-delta prediction, which is weaker than the discipline the shipped "
    "writers use - disclosed rather than dressed up. (c) tasks.md was left "
    "untouched: it is the P-47 canonical board and carries no row for this "
    "tech slice, disclosed rather than silently skipped. (d) This window ran "
    "past its 25-minute budget: the battery alone measured 945.9s, and the "
    "product face was still shipped on the same budget rather than deferred, "
    "because the tree was committed and clean before the battery.",
    "R2369 self-heal check: BigDomain-OSLoop is still registered with "
    "LogonType=InteractiveToken, which the 2026-09-29 machine law forbids for "
    "every lane task; src/os/register_loop_task.ps1 already passes an "
    "explicit S4U principal and needs an elevated shell to apply, and this "
    "session runs unelevated, so the definition of the loop hosting this "
    "window was left untouched. Open local-lane item for an elevated window "
    "(hundred-and-twenty-fourth consecutive disclosure, carried as the stale "
    "row loop-s4u-reconcile in state/debt.md).",
    "R2369 tokens: local=~29k api=0 api_reason=verification-then-product "
    "window - one full battery (495 suites, 945.9s) plus its four follow-up "
    "sections and one matrix regeneration, one batch writer and its "
    "six-criteria suite written to criteria pinned fourteen rounds earlier, "
    "one registry wiring line, one two-leg evidence capture with four adjacent "
    "suites, one live check on the real declaration, one board stamp and one "
    "measured gap row seeded, and the state/export/heartbeat closeout; zero "
    "cloud calls and zero external API touches",
]


def read_state():
    with io.open(STATE, "r", encoding="utf-8", newline="") as handle:
        return handle.read()


def write_state(text):
    with io.open(STATE, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    with io.open(STATE, "r", encoding="utf-8", newline="") as handle:
        back = handle.read()
    return back


def block_boundaries(log):
    out = []
    for index, line in enumerate(log):
        if re.match(r"^(?:\d{4}-\d{2}-\d{2} )?R\d+ tokens:", line.strip()):
            out.append(index + 1)
    return out


def main():
    raw = read_state()
    before = len(raw.encode("utf-8"))
    data = json.loads(raw)
    tick = data.get("tick", 0) + 1
    data["tick"] = tick
    data["benchmarks_refreshed"] = "2026-11-02"
    data["log"] = list(data["log"]) + ITEMS
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    text = state_io.canon(text)
    write_state(text)
    size = len(text.encode("utf-8"))
    print("STATE tick=%d items=+%d before=%dB after=%dB"
          % (tick, len(ITEMS), before, size))

    guard = 0
    while True:
        measure = state_fold.measure(size, GATE)
        if not measure["fold_needed"]:
            print("FOLD none needed bytes=%d margin=%d"
                  % (size, measure["margin"]))
            break
        current = read_state()
        state = json.loads(current)
        log = state["log"]
        ends = block_boundaries(log)
        target = GATE - RESERVE
        chosen = None
        for end in ends:
            if end >= len(log):
                continue
            window = log[:end]
            found = set()
            for line in window:
                found |= set(state_fold.PAT.findall(line))
            rounds = sorted(set(re.findall(r"R(\d{4})", " ".join(window))))
            summary = ("Fold %d: log lines 1..%d folded verbatim into the "
                       "archive at a TRUE round-block boundary; rounds %s; "
                       "tokens %s"
                       % (FOLD_BASE + guard, end,
                          ",".join("R" + r for r in rounds),
                          " ".join(sorted(found))))
            try:
                plan, _folded = state_fold.plan_fold(
                    current.encode("utf-8"), state, 1, end, summary,
                    reserve=0, gate=GATE)
            except Exception as exc:  # noqa: BLE001 - reported, not hidden
                print("FOLD plan refused end=%d %s" % (end, exc))
                continue
            if not plan["token_ok"]:
                print("FOLD token gap end=%d missing=%d"
                      % (end, len(plan["tokens_missing"])))
                continue
            if plan["predicted_bytes"] <= target:
                chosen = (end, summary, plan)
        if chosen is None:
            print("FOLD none fits target=%d bytes=%d" % (target, size))
            break
        end, summary, plan = chosen
        state_fold.fold(REPO, "R2369", FOLD_BASE + guard, 1, end, summary,
                        reserve=0, gate=GATE, execute=True)
        size = os.path.getsize(STATE)
        print("FOLD %d window=1..%d predicted=%dB measured=%dB"
              % (FOLD_BASE + guard, end, plan["predicted_bytes"], size))
        guard += 1
        if guard > 6:
            print("FOLD guard tripped")
            break
    final = state_fold.measure(os.path.getsize(STATE), GATE)
    print("FINAL bytes=%d margin=%d fold_needed=%s verdict=%s"
          % (final["bytes"], final["margin"], final["fold_needed"],
             final["verdict"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())