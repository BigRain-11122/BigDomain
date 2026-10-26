"""R2155 closeout: append the round narrative, the machine-readable
ledger line and the battery outcome line, re-anchor the decision-token
baseline to the measured set, and refresh the derived status-export
faces.

Writes through a temp file plus os.replace. ASCII source, stdlib only,
zero network. Model: closeout_R2154.py (one file per round).
"""

import io
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
STATE = os.path.join(BASE, "state.json")
EXPORT = os.path.join(REPO, "docs", "status-export.json")
DECISIONS = os.path.join(os.path.dirname(REPO), "..", "docs", "decisions.md")

sys.path.insert(0, BASE)

import check_export_consistency as CEC  # noqa: E402

ROUND = 2155
PAYLOAD = os.path.join(BASE, "r2155_export_payload.json")
TOKEN_RE = re.compile(r"(?:D|C|O|P|T|XL)-\d{8}-\d+")

NARRATIVE = (
    "2026-10-27 R2155 (five-silence scan clean at open: decisions.md 294 "
    "non-empty rows and the strict content-addressed diff yields ZERO new "
    "D-/C- tokens - the apparent additions are the O-/T- family re-parsed "
    "at a different digit width by the group-side rotation (O-20261015-1049 "
    "reads as O-20261015-10 and so on), disclosed as a parse artifact "
    "rather than new law; the ledger carries the same three @BigDomain "
    "patrol rows already paid off with zero unreplied; group orders "
    "baseline unchanged at the 2026-10-26 22:36 dispatch-deck row; "
    "benchmarks refreshed 2026-10-27 inside the seven-day gate; tree clean, "
    "no index.lock; today's standing rows were already on disk "
    "(qa/funnel-daily-20261027.log and the reconcile-daily chain "
    "20261027/-2/-3), so neither was re-run. The P1 canonical rows stay "
    "blocked-on-CEO and the weekly proposal duty is met by BD-PROP-005, so "
    "this window claimed the P2 tech FIFO head - the R2149 reseed row - and "
    "registered AC-FSW1..AC-FSW8 in the queue line BEFORE the code existed "
    "(six anchors zero-occupancy against HEAD rc=1: AC-FSW, book_conflicts, "
    "rescan_conflicts, test_funnel_firstwrite, ledger-funnel-firstwrite and "
    "first_offered_day; honest note: the seed row suggested reusing "
    "AC-FCW2, but AC-FCW1..FCW8 are already the CLI working-directory "
    "family from R2064, so this window used AC-FSW as the seed itself "
    "warned). Product: the funnel's first-write-wins law was already "
    "idempotent per ring (AC-FIN / AC-FRS), but a LATER submission of an "
    "already-booked natural key carrying a DIFFERENT money payload vanished "
    "in silence - INSERT OR IGNORE kept the first row and no one could "
    "learn that two sources disagreed about the amount of one order, which "
    "on a commercialisation ledger is silent divergence rather than "
    "harmless idempotency. funnel_daily.py grows an append-only "
    "rescan_conflicts table, _record_conflict and a book_conflicts(day=None) "
    "read face: the two money rings (orders, flows) compare the offered "
    "payload against the booked row before the insert (canonical compact "
    "ASCII JSON array text, so a sku or account containing the separator "
    "can never collide) and register each distinct divergent claim once "
    "under UNIQUE(ring, natural_key, offered_text); repeated identical "
    "re-submissions add nothing, a submission identical to the booked "
    "payload is not a divergence at all, and offered_day keeps the day the "
    "divergence was FIRST presented so retries never re-date it. First "
    "values and day attribution are never rewritten, so a later day still "
    "counts nothing (the booked day owns the row) and the outstanding "
    "identity is untouched. Rings 1 and 2 keep first-write-wins WITHOUT "
    "registration by declared law: a lead-text disagreement belongs to the "
    "UGC content-safety pipeline, not to a bookkeeping register. Every ring "
    "return dictionary and every existing read face is byte-identical "
    "(pure addition). Suite src/sandbox/funnel/test_funnel_firstwrite.py "
    "SUITE PASS 8/8, double run byte-identical sha16 5f1b3637579d8e42 "
    "(qa/funnel-firstwrite-R2155-a.log / -b.log, single writer utf-8 LF), "
    "wired as funnel-firstwrite(8); the whole 18-suite funnel family "
    "(including the 12 pre-existing ring suites) re-ran green as the "
    "regression control."
)

TOKENS_LINE = (
    "R2155 tokens: local=~75k api=0 api_reason=five-silence scan + "
    "first-write-wins divergence register product change + suite 8/8 "
    "double-run + 18-suite funnel regression + battery + state/export "
    "closeout, zero cloud calls"
)

BATTERY_LINE = (
    "R2155 battery outcome: RUNNER PASS 357/357 suites green plus "
    "reconcile controls 7/7 in 779.7s (qa/reconcile-all-R2155.log, "
    "single-writer utf-8 LF), TMP RECLAIM candidates=805 removed=805 "
    "busy=0 failed=0 reclaimed=288.11 MiB through the birth-site sweep; "
    "the new funnel-firstwrite suite is green inside the battery and the "
    "suite matrix was regenerated against this battery to 357 suites / "
    "2978 criteria with --check byte-identical. The FAIL strings in the "
    "log belong to the tamper-control suites, which are supposed to fail "
    "and exit 2 - each reported PASS on its expected exit code."
)


def write_json(path, payload, indent=2):
    text = json.dumps(payload, ensure_ascii=False, indent=indent,
                      sort_keys=False)
    tmp = path + ".tmp"
    with io.open(tmp, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text + "\n")
    os.replace(tmp, path)


def measured_decisions():
    with io.open(DECISIONS, "r", encoding="utf-8") as handle:
        text = handle.read()
    rows = len([line for line in text.split("\n") if line.strip()])
    tokens = sorted(set(TOKEN_RE.findall(text)))
    return rows, tokens


def main():
    with io.open(STATE, "r", encoding="utf-8") as handle:
        state = json.load(handle)
    if state.get("tick") != ROUND - 1:
        sys.stderr.write("E_TICK: state tick is %r\n" % (state.get("tick"),))
        return 2
    log = state["log"]
    if log and str(ROUND) in log[-1][:40]:
        sys.stderr.write("E_ALREADY: round already stamped\n")
        return 2
    log.append(NARRATIVE)
    log.append(TOKENS_LINE)
    log.append(BATTERY_LINE)
    state["tick"] = ROUND
    rows, tokens = measured_decisions()
    state["last_decision_rows"] = rows
    state["last_dec_tokens"] = ",".join(tokens)
    write_json(STATE, state)

    derived, _state, export, _pat = CEC.recompute()
    with io.open(PAYLOAD, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    export["export_ts"] = payload["export_ts"]
    ceo = export.setdefault("ceo_face", {})
    ceo.update(payload["ceo_face"])
    self_drive = export.setdefault("self_drive", {})
    self_drive.update(derived)
    write_json(EXPORT, export)
    print("tick=%d log=%d rows=%d tokens=%d"
          % (state["tick"], len(log), rows, len(tokens)))
    return 0


if __name__ == "__main__":
    sys.exit(main())