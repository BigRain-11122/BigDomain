"""R2326 closeout: the battery round on the committed R2325 tree.

state.json stood at 76984B against the 78500B waterline (a 1516B margin), so
the fold runs BEFORE any append through the shipped state_fold law. Log items
4..9 are whole round blocks (R2312 and R2313) and nothing is split.

Then the window items are appended through state_io and the decision tokens
this window judged are folded into last_dec_tokens.

Dry run by default; --execute writes. Pure ASCII, stdlib only, no network.
"""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import state_fold as SF  # noqa: E402
import state_io  # noqa: E402

STATE = os.path.join(ROOT, "src", "os", "state.json")
GATE = 78500
FOLD_NO = 620
WINDOW_START = 4
WINDOW_END = 9

NEW_DEC = ["D-20261101-15", "D-20261101-16", "D-20261101-17", "D-20261101-18"]

NARRATIVE = (
    "2026-11-01 R2326 verification window (five-silence scan clean at open: "
    "empty git status --short, no .git/index.lock, no unreplied @BigDomain "
    "ledger row, orders tail unchanged, benchmarks refreshed 2026-11-01). "
    "Claimed the board TOP row R2326: the full reconcile battery on the "
    "committed R2325 tree with zero product edits, per the R2168 mixed-tree "
    "rule. RUNNER PASS 470/470 suites plus controls 7/7 in 839.6s with "
    "birth-site TMP RECLAIM 932/932 worlds 326.59 MiB busy=0 failed=0 "
    "(qa/reconcile-all-R2326.log, 787466B, single writer utf-8 LF through "
    "src/os/battery_stream.py, never a shell redirection); expected criteria "
    "total 3796. PRE-REGISTERED TARGET RECONCILED WITH ONE NAMED CORRECTION: "
    "the R2326 row predicted 471 suites / 3802 criteria 'against R2324 "
    "(470/3796)', but R2324's own log records 469/469 with criteria total "
    "3790 - the parenthetical baseline was the POST-R2325 state mislabelled "
    "as R2324. Measured 470/3796 is therefore exactly +1 suite / +6 criteria "
    "against the true R2324 baseline 469/3790, delivered by the "
    "os-followup-retry-history suite this round ran and passed at 6/6 in 7.4s; "
    "no delta remains unresolved and no suite is missing from the registry. "
    "FOUR FOLLOW-UP SECTIONS via src/os/battery_followup.py in the designed "
    "order: matrix FAILED first on the stale doc (on-disk=45005B "
    "regenerated=45098B) and did NOT rewrite it; src/sandbox/suite_matrix.py "
    "regenerated docs/sandbox-suite-matrix.md to 470 suites / 3796 criteria "
    "(45098B); the re-run read all four PASS (matrix byte-identical, "
    "fingerprint CLEAN 5 domains, profile --daily --check byte-identical, "
    "census DRIFT-CLEAN), closing on VERDICT R2326 PASS. Honest score: a "
    "0-point verification window with no product face.")

LEDGER = (
    "R2326 tokens: local=~14k api=0 api_reason=verification-only window on "
    "the committed tree - one full reconcile battery (470/470 suites, 3796 "
    "criteria), four follow-up sections with the designed matrix fail-then-"
    "regenerate, one closeout; no cloud or external API calls was made and no "
    "product code was written")

SELF_HEAL = (
    "R2326 self-heal check: BigDomain-OSLoop is registered and its principal "
    "still reads LogonType=InteractiveToken, which the 2026-09-29 machine law "
    "forbids for lane tasks; register_loop_task.ps1 already passes an explicit "
    "S4U principal and needs an elevated shell, which this session is not, so "
    "the definition was left untouched (eighty-eighth consecutive disclosure, "
    "carried as loop-s4u-reconcile in state/debt.md).")

DECISIONS = (
    "R2326 decision gate (D-20260930-19 step 2): four new content-addressed "
    "tokens D-20261101-15/16/17/18 were presented and all four read NON-"
    "EXECUTION for this company - D-15 rewrites the D-03 acceptance criteria "
    "for executor liveness and dispatches @BigCompute/@bm-b/@bm-c, D-16 orders "
    "a lane task revive guard plus a disabled.json trail for @BigCompute and "
    "@HQ tooling, D-17 pins the three-face task health criteria for @HQ "
    "tooling, and D-18 is the group receipt batch which explicitly records "
    "BigDomain 10-29 05:15 as no-op. None names a BigDomain deliverable, so "
    "this window acknowledged rather than acted, and the four tokens are now "
    "in the baseline.")

DISCLOSURES = (
    "R2326 honest disclosures: (a) the first battery launch was killed by the "
    "shell tool's five-minute silence guard because its output was piped "
    "through a buffering select; it was relaunched unbuffered and the killed "
    "run's partial log was overwritten by the launch itself, so no evidence "
    "from the dead run survives and none is claimed. (b) The retro-dated "
    "prediction error in the board row is disclosed above rather than edited "
    "away. (c) tasks.md is untouched: the P-47 board carries no row for a "
    "battery round. (d) No product face shipped, so the next window resumes at "
    "the tech head AC-RWW1.")


def fold(execute):
    state = json.load(io.open(STATE, encoding="utf-8"))
    items = state["log"][WINDOW_START - 1:WINDOW_END]
    body = "\n".join(items)
    tokens = sorted(set(SF.PAT.findall(body)))
    summary = ("Fold R2326: log lines %d..%d (the R2312 and R2313 whole round "
               "blocks) moved verbatim to the archive; window tokens: %s"
               % (WINDOW_START, WINDOW_END, " ".join(tokens)))
    report = SF.fold(ROOT, "R2326", FOLD_NO, WINDOW_START, WINDOW_END,
                     summary, reserve=7000, execute=execute)
    for key in sorted(report):
        if key in ("post_text", "window_lines"):
            continue
        print("FOLD %s=%r" % (key, report[key]))
    return report


def build(text):
    state = json.loads(text.decode("utf-8"))
    before = len(state["log"])
    state["tick"] = 2326
    done = set(x for x in state["last_dec_tokens"].split(",") if x.strip())
    done.update(NEW_DEC)
    state["last_dec_tokens"] = ",".join(sorted(done))
    state["log"].extend([NARRATIVE, LEDGER, SELF_HEAL, DECISIONS, DISCLOSURES])
    ascii_only = all(byte < 0x80 for byte in text)
    body = json.dumps(state, ensure_ascii=ascii_only, indent=2)
    return before, state_io.canon(body).encode("utf-8")


def write(path, data, label):
    temp = os.path.join(os.path.dirname(path), ".%s.tmp" % label)
    with open(temp, "wb") as sink:
        sink.write(data)
        sink.flush()
        os.fsync(sink.fileno())
    os.replace(temp, path)
    if open(path, "rb").read() != data:
        raise SystemExit("E_READBACK %s" % label)
    if os.path.exists(temp):
        raise SystemExit("E_RESIDUE %s" % label)


def main(argv):
    execute = "--execute" in argv
    fold(execute)
    raw = open(STATE, "rb").read()
    before_items, new = build(raw)
    print("LOG_ITEMS %d -> %d TICK 2326 BEFORE %dB AFTER %dB DELTA %+d "
          "GATE %d MARGIN %d"
          % (before_items, before_items + 5, len(raw), len(new),
             len(new) - len(raw), GATE, GATE - len(new)))
    if len(new) > GATE:
        raise SystemExit("E_C2326_OVER_GATE %d" % len(new))
    if not execute:
        print("DRY RUN - nothing written")
        return 0
    write(STATE, new, "state_close_R2326")
    parsed = json.loads(open(STATE, "rb").read().decode("utf-8"))
    if parsed["tick"] != 2326 or len(parsed["log"]) != before_items + 5:
        raise SystemExit("E_C2326_PARSE")
    if "D-20261101-18" not in parsed["last_dec_tokens"]:
        raise SystemExit("E_C2326_DEC")
    print("WROTE %dB readback ok temp clean tick=%d log=%d"
          % (len(new), parsed["tick"], len(parsed["log"])))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))