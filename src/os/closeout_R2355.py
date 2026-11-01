"""closeout_R2355 - append this window's log items, fold, then refresh the
CEO face.

Every value is derived in this run: the log items are written here, the export
counts come from the shipped checker (F3 law), and the artifact line names an
evidence file that exists on disk. Dry run by default; --execute appends to
state.json through state_io.canon plus one atomic replace, folds the oldest
log window on a ROUND-BLOCK boundary, and writes the export through its
single writer.
"""

import io
import json
import os
import sys
import tempfile
from datetime import datetime, timedelta

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import state_io as SIO  # noqa: E402
import state_fold as SF  # noqa: E402
import check_export_consistency as CC  # noqa: E402

STATE = os.path.join(ROOT, "src", "os", "state.json")
EXPORT = os.path.join(ROOT, "docs", "status-export.json")
HEARTBEAT = os.path.join(ROOT, "heartbeat.txt")
PROPOSALS = os.path.join(ROOT, "docs", "proposals.md")
EVIDENCE = "qa/reconcile-all-R2355.log"

NOW = datetime.now()
STAMP = NOW.strftime("%Y-%m-%dT%H:%M:%S+08:00")
DUE = (NOW + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%S+08:00")

FOLD_NO = 640
RESERVE = 200

# The nine decision tokens this window judged, all acknowledged as
# non-execution for this company (see the gate item in the log).
NEW_DEC_TOKENS = [
    "D-20261026-14", "D-20261026-17", "D-20261026-18",
    "D-20261102-01", "D-20261102-02", "D-20261102-03",
    "D-20261102-04", "D-20261102-05", "D-20261102-06",
]

DO = (
    "R2355 verification window: the carried battery ran on the committed "
    "R2354 tree and reads RUNNER PASS 486/486 suites plus controls 7/7 in "
    "1056.0s with criteria total 3892; all four follow-up sections then "
    "PASS (matrix byte-identical at 46510B, fingerprint CLEAN, profile "
    "byte-identical, census DRIFT-CLEAN) for VERDICT R2355 PASS. The six "
    "new group decision rows were reviewed and none dispatches this "
    "company. No product code shipped."
)

ARTIFACT = (
    "qa/reconcile-all-R2355.log (796964B, single writer utf-8 LF through "
    "src/os/battery_stream.py) - 486 suites / 3892 criteria, 7/7 reconcile "
    "controls, TMP RECLAIM 932/932 worlds 326.59 MiB; docs/sandbox-suite-"
    "matrix.md regenerated to 486 / 3892 (46510B)."
)

NEXT = (
    "R2356: claim the queue head state/queue/tech.md:400 prefix AC-OPW1 "
    "(orphan_promotion_wire) - wire the promotion writer to ask the "
    "promotion ledger before it copies, then commit before any battery."
)

LOG_ITEMS = [
    "2026-11-02 R2355 verification window (five-silence scan at open: empty "
    "git status --short at 5070b522, no .git/index.lock; scan_five_still read "
    "LEDGER atbd_lines=0 unreplied_groups=0 and DEC rows=112 tokens=74 new=9; "
    "the group orders tail still reads the 2026-11-01 10:4x model-policy "
    "baseline already acked by R2350 as non-execution; benchmarks refreshed "
    "2026-11-01, inside the seven-day gate). THE GATE NAMED THE CARRIED "
    "BATTERY, and it ran FIRST on the committed tree: debt_gate read "
    "CLAIM-FIRST item=reconcile-battery-R2355 opened=R2354, the working tree "
    "was empty at 5070b522 (the R2168 mixed-tree rule), and the "
    "pre-registered target was 485 suites / 3886 criteria. MEASURED: RUNNER "
    "PASS 486/486 suites green plus controls 7/7 in 1056.0s with birth-site "
    "TMP RECLAIM 932/932 worlds 326.59 MiB busy=0 failed=0 "
    "(qa/reconcile-all-R2355.log, 796964B at runner close, single writer "
    "utf-8 LF through src/os/battery_stream.py, never a shell redirection), "
    "criteria total 3892. THE PREDICTION WAS ONE SUITE SHORT AND THE DELTA IS "
    "NAMED, not swept: +1 suite / +6 criteria over the register note resolves "
    "exactly to os-queue-head-delivered (6 criteria), the suite R2354 itself "
    "shipped after the note counted only the R2353 edit; no other suite is "
    "unaccounted for. Four follow-up sections then ran through "
    "src/os/battery_followup.py: the matrix section FAILED first on the stale "
    "doc (on-disk=46114B regenerated=46510B) and did NOT rewrite it, which is "
    "the designed order; src/sandbox/suite_matrix.py regenerated "
    "docs/sandbox-suite-matrix.md to 486 suites / 3892 criteria (46510B) and "
    "the re-run read all four PASS (matrix byte-identical, fingerprint CLEAN "
    "5 domains, profile --daily --check byte-identical, census DRIFT-CLEAN), "
    "closing VERDICT R2355 PASS. Register: the battery row was closed through "
    "its own writer (debt_close: open 3->2, done 88->89, before=72488B "
    "after=72491B, readback ok) and the successor product row was opened "
    "first=yes through debt_append (product-face-R2356, 72491B -> 72854B, "
    "readback ok). DECISION GATE: six new rows D-20261102-01..06 were read in "
    "full and NONE dispatches this company - D-01 is the 7-day return visit "
    "with HQ tool domain and @Biggame as owners, D-02/D-03 are BigCompute "
    "items, D-04 is @Biggame, D-05 is the HQ lane registry plus FluxVerse and "
    "City3D, and D-06 is the collection-face batch that records BigDomain "
    "HQ-FEEDBACK as unchanged since 2026-10-29 (a no-op, not a claim against "
    "us); the three older tokens D-20261026-14/17/18 are body mentions inside "
    "D-01 and were never separate rows. ZERO product code shipped and the "
    "window scores 0 product points, honestly recorded.",
    "R2355 tokens: local=~9k api=0 api_reason=verification window - one full "
    "reconcile battery on the committed tree (1056.0s), one matrix "
    "regeneration, one four-section follow-up re-run, two register writes "
    "through their own writers, six group decision rows read, and the "
    "state/export/heartbeat/board closeout; zero cloud calls and zero "
    "external API touches",
    "R2355 self-heal check: BigDomain-OSLoop is registered and its principal "
    "still reads LogonType=InteractiveToken, which the 2026-09-29 machine law "
    "forbids for every lane task; src/os/register_loop_task.ps1 already passes "
    "an explicit S4U principal and needs an elevated shell to apply, and this "
    "session runs unelevated, so the definition of the loop hosting this "
    "window was left untouched. Open local-lane item for an elevated window "
    "(hundred-and-thirteenth consecutive disclosure, carried as the stale row "
    "loop-s4u-reconcile in state/debt.md).",
    "R2355 decision gate (D-20260930-19 step 2): the content-addressed diff "
    "of the group decisions.md against the stored baseline read NINE new "
    "tokens (new=[D-20261026-14, D-20261026-17, D-20261026-18, "
    "D-20261102-01..06]). Six are live rows from 2026-11-02 and every one was "
    "read in full: D-01 (7-day return visit / decision-lifetime law) names "
    "@HQ tool domain and @Biggame, D-02 and D-03 are BigCompute pieces, D-04 "
    "is the @Biggame feedback face, D-05 is the HQ lane registry with "
    "FluxVerse and City3D owners, D-06 is the collection batch and records "
    "this company as an honest no-op. Three tokens are older rounds mentioned "
    "inside D-01's body rather than rows of their own. Executed 0, rejected "
    "0, acknowledged as non-execution 6; the baseline is widened to all nine "
    "so they cannot re-flag.",
    "R2355 honest disclosures: (a) NO product face shipped and the window "
    "scores 0 product points; the register's first=yes item was a battery and "
    "the tree carried the product edit that owed it. (b) The register's "
    "pre-registered target was ONE SUITE SHORT (485/3886 against a measured "
    "486/3892): the note counted the R2353 product edit and omitted the "
    "os-queue-head-delivered suite that R2354 shipped in the same window that "
    "wrote the note, and the delta resolves to that suite's 6 criteria - "
    "named here so the next register row is written against the measured "
    "registry. (c) Two untracked scratch files (logs/tmp/extract.py and "
    "logs/tmp/dec-R2355.txt) were written after the open's empty-tree check "
    "and before the battery started, used only to read a decision row whose "
    "console rendering is mojibake, outside qa/ and src/; they are deleted in "
    "this closeout and the window is disclosed rather than presented as a "
    "pristine tree. (d) The evidence file carries a FAIL block from the "
    "designed first follow-up pass (matrix, 1889B) followed by the PASS "
    "block (1950B); both are left in place because deleting the designed "
    "FAIL is exactly the shape this house forbids. (e) tasks.md was left "
    "untouched: it is the P-47 canonical board and carries no row for a "
    "verification window, disclosed rather than silently skipped.",
]


def read_json(path):
    with io.open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def proposal_counts():
    with io.open(PROPOSALS, "r", encoding="utf-8") as handle:
        text = handle.read()
    heads = [line for line in text.split("\n")
             if line.startswith("### BD-PROP-")]
    opened = [line for line in heads if "状态 open" in line]
    return {"proposals_total": len(heads), "proposals_open": len(opened)}


def bump_state(execute):
    """Append the window items and write the canon with a read-back proof."""
    state = read_json(STATE)
    state["tick"] = state["tick"] + 1
    state["log"] = state["log"] + LOG_ITEMS
    known = list(state.get("last_dec_tokens") or [])
    for token in NEW_DEC_TOKENS:
        if token not in known:
            known.append(token)
    state["last_dec_tokens"] = known
    payload = json.dumps(state, ensure_ascii=False, indent=2, sort_keys=False)
    canon = SIO.canon(payload)
    data = canon.encode("utf-8")
    print("STATE tick=%d log_items=%d dec_tokens=%d bytes=%d"
          % (state["tick"], len(state["log"]), len(known), len(data)))
    if not execute:
        return data
    folder = os.path.dirname(os.path.abspath(STATE))
    handle, temp = tempfile.mkstemp(dir=folder, prefix=".state_R2355_")
    try:
        with os.fdopen(handle, "wb") as sink:
            sink.write(data)
            sink.flush()
            os.fsync(sink.fileno())
        os.replace(temp, STATE)
    except BaseException:
        try:
            os.unlink(temp)
        except OSError:
            pass
        raise
    with io.open(STATE, "rb") as back:
        landed = back.read()
    ok = landed == data
    print("STATE READBACK ok=%s" % ok)
    return data if ok else None


def fold(execute, data):
    """Fold the oldest window that ENDS a whole round block.

    A window is eligible only when it closes on a tokens ledger line AND the
    next item opens a new round block (a 'YYYY-MM-DD R<n>' line). The R2354
    repair proved that a tokens line alone can sit in the middle of a block.
    """
    if data is None:
        raise SystemExit("E_R2355_STATE_WRITE")
    raw = data
    state = json.loads(raw.decode("utf-8"))
    print("FOLD gate at predicted %dB margin=%dB"
          % (len(raw), 78500 - len(raw)))
    if len(raw) <= 78500 - RESERVE:
        print("FOLD not due")
        return 0
    chosen = None
    for end in range(3, min(40, len(state["log"]))):
        if " tokens: local=" not in state["log"][end - 1]:
            continue
        nxt = state["log"][end]
        if not (len(nxt) > 12 and nxt[:4].isdigit() and nxt[4] == "-"):
            continue
        window = state["log"][0:end]
        tokens = set()
        for line in window:
            tokens |= set(SF.PAT.findall(line))
        summary = ("Fold R2355: log lines 1..%d folded verbatim into the "
                   "archive so the closeout fits the waterline; window ends "
                   "on a tokens ledger line AND on a round-block boundary; "
                   "window tokens: %s" % (end, " ".join(sorted(tokens))))
        plan, _text = SF.plan_fold(raw, state, 1, end, summary,
                                   reserve=RESERVE)
        print("FOLD candidate end=%d predicted=%dB gate_ok=%r missing=%d"
              % (end, plan["predicted_bytes"], plan["gate_ok"],
                 len(plan["tokens_missing"])))
        if plan["gate_ok"] and not plan["tokens_missing"]:
            chosen = (end, summary)
            break
    if not chosen:
        raise SystemExit("E_R2355_NO_WINDOW")
    if not execute:
        print("DRY RUN: fold wrote nothing")
        return 0
    result = SF.fold(ROOT, "R2355", FOLD_NO, 1, chosen[0], chosen[1],
                     reserve=RESERVE, execute=True)
    print("fold=%d window=1..%d predicted=%sB post=%sB margin=%s"
          % (FOLD_NO, chosen[0], result.get("predicted_bytes"),
             result.get("post_bytes", result.get("actual_bytes")),
             result.get("margin")))
    return 0


def first_by_key(rows):
    """Keep the first row per key (its own first field), in file order."""
    seen = set()
    out = []
    for row in rows:
        key = str(row[0])
        if key in seen:
            continue
        seen.add(key)
        out.append(row)
    return out


def write_export(state, execute):
    """Every self_drive field comes from the SHIPPED checker, not a copy."""
    derived, live_state, _old, patterns = CC.recompute()
    data = read_json(EXPORT)
    data["export_ts"] = STAMP
    data["do"] = DO
    face = data["ceo_face"]
    face["current"] = DO
    face["latest_artifact"] = ARTIFACT
    face["last_artifact"] = ARTIFACT
    face["next_milestone"] = NEXT
    face["next_milestone_due"] = DUE
    face["updated_at"] = STAMP
    data["outs"].append([
        "qa/reconcile-all-R2355.log", "on",
        "R2355 verification: the carried battery on the committed R2354 tree "
        "read 486/486 suites plus controls 7/7 with criteria total 3892, and "
        "all four follow-up sections PASS after the designed matrix FAIL and "
        "its regeneration - the newest two suites are proven wired into the "
        "whole registry, not only into their own runs",
    ])
    data["results"].append([
        "R2355",
        "verification window on the register's first=yes item: battery PASS "
        "486/486 suites, criteria 3892, 1056.0s, TMP RECLAIM 932/932; matrix "
        "regenerated to 486/3892 (46510B) and re-read byte-identical; "
        "fingerprint CLEAN, profile byte-identical, census DRIFT-CLEAN; the "
        "pre-registered 485/3886 missed by exactly os-queue-head-delivered "
        "(6 criteria) and the delta is named; six new group decision rows "
        "acknowledged as non-execution and the token baseline widened to 74; "
        "battery row closed and product-face-R2356 opened first=yes",
    ])
    label = patterns["tick_row_label"]
    tick_rows = [row for row in data["results"]
                 if isinstance(row, list) and len(row) >= 2 and row[1] == label]
    if len(tick_rows) != 1:
        raise SystemExit("E_R2355_TICK_ROW count=%d" % len(tick_rows))
    tick_rows[0][0] = str(live_state["tick"])
    data["outs"] = first_by_key(data["outs"])
    data["results"] = first_by_key(data["results"])
    data["self_drive"] = derived
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    json.loads(text)
    print("EXPORT tick=%s self_drive=%s bytes=%d"
          % (str(live_state["tick"]), json.dumps(derived),
             len(text.encode("utf-8"))))
    if not execute:
        return 0
    with io.open(EXPORT, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    with io.open(EXPORT, "r", encoding="utf-8") as handle:
        back = handle.read()
    ok = back == text and json.loads(back)["export_ts"] == STAMP
    print("EXPORT READBACK ok=%s" % ok)
    return 0 if ok else 2


def write_heartbeat(state, execute):
    row = "%d %s\n" % (state["tick"], NOW.strftime("%Y-%m-%dT%H:%M:%S"))
    if not execute:
        print("HEARTBEAT would append: %s" % row.strip())
        return 0
    with io.open(HEARTBEAT, "a", encoding="utf-8", newline="\n") as handle:
        handle.write(row)
    return 0


def main(argv):
    execute = "--execute" in argv
    if "--export-only" in argv:
        return write_export(read_json(STATE), execute)
    code = bump_state(execute)
    if code is None:
        return 2
    code = fold(execute, code)
    if code:
        return code
    code = write_export(read_json(STATE), execute)
    if code:
        return code
    return write_heartbeat(read_json(STATE), execute)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))