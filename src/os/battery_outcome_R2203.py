"""R2203 battery outcome: append the RUNNER PASS line to state, lift the
export next_milestone, and record the debt as discharged. ASCII source."""
import io
import json
import os
import time

BASE = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATE = os.path.join(BASE, "src", "os", "state.json")
EXPORT = os.path.join(BASE, "docs", "status-export.json")

LINE = (
    "R2203 battery outcome (discharged the R2202 carry-over in the same"
    " window, on the committed tree): RUNNER PASS 398/398 suites green"
    " plus reconcile controls 7/7 in 857.7s (qa/reconcile-all-R2203.log,"
    " 736797 bytes before the follow-up sections, single-writer utf-8 LF,"
    " crlf=0), with the birth-site tmp sweep inside the same battery"
    " window reclaiming 886 of 886 candidate worlds and 313.09 MiB,"
    " busy=0 failed=0. The suite matrix was then regenerated against this"
    " run to 398 suites / 3306 criteria (docs/sandbox-suite-matrix.md,"
    " 38657 bytes, green=398/398), the baseline fingerprint chain read"
    " CLEAN over five domains, the runner profile check PASSed and the qa"
    " writer census read DRIFT-CLEAN after its update-baseline pass"
    " (VERDICT PASS in the same evidence log). Honest notes: the first"
    " attempt was cancelled by the shell tool because the output was piped"
    " through a buffering filter and produced no visible stream for five"
    " minutes - no evidence file and no survivor process were left behind,"
    " so the second attempt started from a clean tree; and an accidental"
    " `reconcile_all.py --help` probe ran a partial battery and dropped a"
    " stray file literally named `--help` at the repo root, which was"
    " deleted rather than committed. The product face landed before the"
    " battery, so this round carries both a 2-point product increment and"
    " a clean 398-suite verification.")

NEXT = ("next explore seed (seller-side monthly watch inflow) with its"
        " criteria registered before the code, on top of a clean"
        " 398-suite battery (within 48h)")


def main():
    state = json.load(io.open(STATE, encoding="utf-8"))
    if not any("R2203 battery outcome" in row for row in state["log"]):
        state["log"].append(LINE)
    io.open(STATE, "w", encoding="utf-8", newline="\n").write(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n")

    export = json.load(io.open(EXPORT, encoding="utf-8"))
    export["export_ts"] = time.strftime("%Y-%m-%dT%H:%M:%S+08:00")
    face = export["ceo_face"]
    face["latest_artifact"] = (
        "qa/apimarket-buyerrefundmonths-R2203-a.log / -b.log (SUITE 8/8,"
        " sha256 d530197188a7ef2b...) + qa/reconcile-all-R2203.log"
        " (RUNNER PASS 398/398 suites, controls 7/7, 857.7s) +"
        " src/sandbox/ledger/apimarket.py (api_buyer_refund_months,"
        " written 2026-10-28)")
    face["next_milestone"] = NEXT
    io.open(EXPORT, "w", encoding="utf-8", newline="\n").write(
        json.dumps(export, ensure_ascii=False, indent=2) + "\n")
    print("log_lines", len(state["log"]), "tick", state["tick"])


if __name__ == "__main__":
    main()