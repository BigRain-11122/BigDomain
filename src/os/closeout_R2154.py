"""R2154 closeout: advance the tick, append the round narrative and the
machine-readable ledger line, re-anchor the decision-token baseline to
the measured set, and refresh the derived status-export faces.

Writes through a temp file plus os.replace. ASCII source, stdlib only,
zero network.
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

ROUND = 2154
PAYLOAD = os.path.join(BASE, "r2154_export_payload.json")
TOKEN_RE = re.compile(r"(?:D|C|O|P|T|XL)-\d{8}-\d+")

NARRATIVE = (
    "2026-10-27 R2154 (five-silence scan clean at open: ledger carries the "
    "same three @BigDomain patrol rows already paid off and zero unreplied; "
    "decisions.md 364 rows / 239 content-addressed tokens with three real "
    "new tokens D-20261027-08..10 - the BigMoney CODELY.md structural "
    "corruption remedy, the Tools/silence-enforce.ps1 push to BigMoney and "
    "the MiniGame HQ-FEEDBACK routing ruling - all other seats' execution "
    "faces, acknowledged with zero action and the baseline advanced; the "
    "remaining apparent diff is the O- family re-parsed at a different "
    "digit width by the group-side rotation, disclosed as a parse artifact "
    "rather than new law; group orders baseline unchanged at the 2026-10-26 "
    "22:36 dispatch-deck row; benchmarks refreshed 2026-10-27 inside the "
    "seven-day gate; tree clean, no index.lock; the four tech heads below "
    "the head were reseeds, so this window claimed the R2152 seed head and "
    "registered AC-LGN1..AC-LGN8 in the queue line BEFORE the code (five "
    "anchors zero-occupancy against HEAD rc=1; honest note: AC-LGN and "
    "LEDGER OK were already mentioned by the seed row and the R2152 export "
    "placeholder, so only their code occupancy was free) - the round "
    "closing-station window). Product: src/os/ledger_lines.py grows "
    "check_closeout(lines, round_no=None) - the question the closing step "
    "itself must answer before it may shut a round, and the one the "
    "whole-window audit can only answer after the fact. Target round is the "
    "newest narrative round by default and an explicit --round N otherwise; "
    "the report has five pinned keys and four verdicts OK/MISSING/BAD_SHAPE/"
    "NOT_MONOTONIC in a fail-closed order (absent closing line, then broken "
    "shape, then disorder); a broken-prefix line counts as the target "
    "round's evidence instead of being silently skipped; ordering compares "
    "only against rounds settled BEFORE the closing line, so future lines "
    "never move the verdict; the --closeout CLI prints exactly one "
    "'LEDGER OK <round>' line on success with exit 0, prints nothing of the "
    "sort on failure with exit 2, and --closeout --json emits the same "
    "verdict as a report; the gate is read-only (state.json bytes identical "
    "around a run) and the module stays stdlib-only with zero network "
    "imports. Suite src/os/test_ledger_closeout.py SUITE PASS 8/8, double "
    "run byte-identical sha16 ee6213c878588c65 (qa/ledger-closeout-R2154-a."
    "log / -b.log, single-writer utf-8 LF), wired as os-ledger-closeout(8); "
    "the previous ledger suite still passes 8/8 as the regression control. "
    "Honest note: the first run of AC-LGN6 went red because the "
    "implementation printed both the summary line and the OK line; the "
    "implementation was tightened to the criterion (one line on success) "
    "instead of the criterion being relaxed."
)

TOKENS_LINE = (
    "R2154 tokens: local=~85k api=0 api_reason=five-silence scan + "
    "closing-station product change (check_closeout plus the --closeout "
    "CLI) + suite 8/8 double-run + wiring + battery + state/export "
    "closeout, zero cloud calls"
)


BATTERY_LINE = (
    "R2154 battery outcome: RUNNER PASS 356/356 suites green plus "
    "reconcile controls 7/7 in 618.9s (qa/reconcile-all-R2154.log, "
    "single-writer utf-8 LF), TMP RECLAIM candidates=805 removed=805 "
    "busy=0 failed=0 reclaimed=288.11 MiB through the birth-site sweep; "
    "suite matrix regenerated against this battery to 356 suites / 2970 "
    "criteria with --check byte-identical. The new os-ledger-closeout "
    "suite is green inside the battery."
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