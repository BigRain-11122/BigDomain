"""R2153 closeout: advance the tick, append the round narrative and the
machine-readable ledger line, and refresh the derived status-export
faces (ceo_face text plus self_drive recomputed with the canonical
caliber imported from check_export_consistency.recompute).

Writes through a temp file plus os.replace. ASCII source, stdlib only,
zero network.
"""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
STATE = os.path.join(BASE, "state.json")
EXPORT = os.path.join(REPO, "docs", "status-export.json")

sys.path.insert(0, BASE)

import check_export_consistency as CEC  # noqa: E402

ROUND = 2153
PAYLOAD = os.path.join(BASE, "r2153_export_payload.json")

NARRATIVE = (
    "2026-10-27 R2153 (five-silence scan at open: 79 bare-LF state lines "
    "repaired first by logs_toolkit eol --fix --execute (written, json_eq "
    "true, post_bare_lf 0); the ledger carries three @BigDomain patrol rows "
    "already paid off with conflict=0; decisions.md 358 rows / 212 "
    "content-addressed tokens with zero new against the stored baseline "
    "(row-owner 183); the group orders tail advanced to the 2026-10-27 "
    "00:40 bm-b model-slot row which is another seat's execution face, so "
    "zero action and the own-orders baseline stays 2026-10-26 22:36; "
    "benchmarks refreshed 2026-10-27 inside the seven-day gate; QA smoke "
    "png/log and the benchmark row are all stamped today; tree clean, no "
    "index.lock. The P1 canonical rows were either the proposal duty "
    "already met by BD-PROP-005 (window 10-25..10-31) or blocked-on-CEO, so "
    "this window claimed the P2 tech head and registered AC-RID1..AC-RID8 "
    "in the queue line BEFORE the code (seven anchors zero-occupancy "
    "against HEAD, with two honest notes: the seed row itself occupies the "
    "placeholder prefix AC-DRR so the real prefix is AC-RID, and "
    "test_determinism only ever existed as a function name inside a "
    "copyright dump) - the double-run identity dialect window). Product: "
    "src/os/run_identity.py - the question 'did run two agree with run "
    "one' now has one dialect instead of two. normalize() does only the "
    "three disclosed things (drop BOM, unify CRLF/CR to LF, end with one "
    "newline) and never scrubs timestamps or paths; digest16 is the byte "
    "key; the two modes are explicit and one-directional (bytes identity "
    "implies conclusions identity, never the reverse, and the comparator "
    "never upgrades one into the other); criteria parsing accepts a "
    "multi-leg id whose legs agree and rejects a self-contradicting id; "
    "the suite verdict must be exactly one line; claims are read from the "
    "BODY only, because a criterion detail such as 'three-instance "
    "byte-identical=True' asserts something about the product, not about "
    "the pair of files; a byte claim that does not hold is "
    "E_FALSE_BYTE_CLAIM; a declared digest is accepted against either "
    "disclosed form (the whole file, or the payload view with the driver's "
    "RUN line dropped) so a reproducible number is never called a lie; "
    "pairs are discovered by base name for -a/-b, -verifya/-verifyb and "
    "-run2 only, and the ambiguous battery '-2' re-run shape is "
    "deliberately NOT paired. The CLI is read-only with exit 0/2/3 and a "
    "stable JSON key set. The live audit of qa/ finds 63 pairs, 62 clean, "
    "zero conclusion drift, zero false digests and exactly one pre-existing "
    "defect: apimarket-buyermonths-R2100, whose driver appended its RUN "
    "verdict line to the primary log only, so the file pair differs by that "
    "single line while both declared digests do reproduce from the payload "
    "view; it is baselined class-wise in state/run_identity_baseline.json "
    "so only a NEW (base,class) pair turns red and a baselined artifact can "
    "never mask a conclusion drift. Two mid-window corrections, both "
    "disclosed: the first draft read body digests such as 'SUITE-SHA16' as "
    "file digests and manufactured two false accusations (report-R2101 and "
    "sellerquality-R2117 are criterion-block digests), so the fallback was "
    "removed; and the first draft paired '-2' re-runs, which accused nine "
    "historical battery logs of a defect that is merely a re-run shape. New "
    "suite src/os/test_run_identity.py covers the normalization and digest "
    "key, the parse family, conclusions versus bytes, claim verification "
    "with both false-claim codes, the pairing shapes, the CLI contract with "
    "a zero-write proof, and a live gated audit; SUITE PASS 8/8 double-run "
    "byte-identical sha16 1155d8b16494c313 (qa/run-identity-R2153-a.log and "
    "-b.log, single-writer UTF-8 LF, and both files carry the same "
    "self-declaring RUN line so the pair's own byte claim is itself "
    "verified); wired as os-run-identity(8); adjacent suites os-ledger-lines "
    "8/8 and ledger-census-negative 12/12 green. Honest gaps: the full "
    "battery and the suite-matrix regen were NOT run this window (the round "
    "budget) and are the first item of the next round."
)

TOKENS_LINE = (
    "R2153 tokens: local=~85k api=0 api_reason=five-silence scan + state "
    "EOL repair + double-run identity dialect product change (two modes, "
    "claim verification, pair audit, known-defect baseline) + suite 8/8 "
    "double-run sha16 1155d8b16494c313 + two adjacent regressions + "
    "wiring + state/export closeout, zero cloud calls"
)

def write_json(path, payload, indent=2):
    text = json.dumps(payload, ensure_ascii=False, indent=indent,
                      sort_keys=False)
    tmp = path + ".tmp"
    with io.open(tmp, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text + "\n")
    os.replace(tmp, path)


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
    state["tick"] = ROUND
    state["last_decision_rows"] = 358
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
    print("tick=%d log=%d derived=%s"
          % (state["tick"], len(log), sorted(derived)))
    return 0


if __name__ == "__main__":
    sys.exit(main())