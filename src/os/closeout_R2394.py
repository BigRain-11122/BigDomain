"""R2394 closeout: append the round items, prepend the backlog row, stamp
the heartbeat, and fold whole blocks only if the state file passes its gate.

The battery leg was the CLAIM-FIRST obligation this window, so the round
increment is a discharged debt plus one repaired declaration, not a new
module; that is stated plainly rather than dressed up.

Stdlib only, ASCII source, no clock, no network.
"""

import io
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import state_io as SIO  # noqa: E402

STATE = os.path.join(REPO, "src", "os", "state.json")
ARCHIVE = os.path.join(REPO, "logs", "state-log-archive-2026-11.md")
BACKLOG = os.path.join(REPO, "src", "os", "backlog.md")
HEARTBEAT = os.path.join(REPO, "heartbeat.txt")
GATE = 78500
TARGET = 73500

TOKENS_RE = re.compile(r"^(?:\d{4}-\d{2}-\d{2}\s+)?R(\d{3,5}) tokens:")

ITEMS = [
    "2026-11-03 R2394 verification-only window (five-silence scan at open: "
    "empty git status at HEAD ef8bce07-ish, no .git/index.lock; LEDGER "
    "@BigDomain unreplied=0; DEC tokens 86 -> 92 with six new rows "
    "D-20261103-01..06, ALL read and all non-execution for this company "
    "(Biggame directory, duanju dormancy, audit cadence, CC-2/CC-3 registry "
    "supplement) so the receipt is an acknowledgement with the numbers "
    "cited; benchmarks refreshed 2026-11-02 inside the seven-day gate; "
    "floor FLOOR-MET). The debt gate named CLAIM-FIRST "
    "item=reconcile-battery-R2387 carried=7 stale=yes, so the battery ran "
    "FIRST on the committed tree with zero product edits, exactly as that "
    "row demanded after R2393 exhausted three legs without a green RUNNER.",

    "2026-11-03 R2394 battery leg 1 red on ONE real data defect, not code: "
    "qa/reconcile-all-R2394b.log read 519/520 suites with the only red being "
    "os-residue-triage AC-RTR6, whose live reading was RESIDUE "
    "declared_by=R2391 residue=238 triaged=237 untriaged=1 - round 2382. "
    "Root cause measured: the R2391 fold repair re-pinned its siblings R2380 "
    "and R2381 into state/residue_triage.json but skipped R2382, so the "
    "triage face had been quietly carrying one untriaged round since that "
    "repair and only a full battery could see it. Repaired at the birth site "
    "through the SHIPPED writer, not by hand: residue_triage_append "
    "--append --round R2382 --status DELIVERED --by R2391 --until R2408 "
    "predicted entries 237->238 and bytes 68151->68335 (delta 184) and "
    "delivered exactly that, verdict TRIAGED, declaration PINNED; "
    "test_residue_triage then read SUITE PASS 6/6 where it had read 5/6.",

    "2026-11-03 R2394 battery leg 2 GREEN: "
    "qa/reconcile-all-R2394-retry.log read RUNNER PASS (520/520 suites "
    "green, reconcile controls 7/7, 1007.7s) with criteria total 4096 "
    "exactly as the registry expects, TMP RECLAIM 932/932 at 326.59 MiB. "
    "The four follow-up sections ran through battery_followup.py: the matrix "
    "section FAILED FIRST on the stale doc and did NOT rewrite it "
    "(on-disk=49422B, regenerated=49953B), suite_matrix then regenerated "
    "docs/sandbox-suite-matrix.md to 520 suites / 4096 criteria and the "
    "re-run read matrix PASS byte-identical 49953B, fingerprint CLEAN "
    "domains=5, profile byte-identical, census DRIFT-CLEAN, VERDICT R2394 "
    "PASS. Evidence and matrix were committed ALONE as d5a63adc before the "
    "data repair byte changed (the R2168 mixed-tree rule); the repair itself "
    "was committed alone as 5183e51a. The register row "
    "reconcile-battery-R2387 was closed through debt_close (open 4->3, "
    "88365B->88368B as predicted) and the successor row "
    "reconcile-battery-R2394 was registered first=yes through debt_append "
    "(88368B->88773B as predicted), so the gate now reads CLAIM-FIRST with "
    "the measured target 520 suites / 4096 criteria.",

    "2026-11-03 R2394 product face, stated honestly: NO new product module "
    "shipped this window. The CLAIM-FIRST battery owned the window (two legs "
    "at 1007.7s and roughly 14 minutes each) and its single red had to be "
    "repaired and re-verified before anything could be claimed, so the "
    "product-first increment this window is the discharged battery debt and "
    "the repaired declaration rather than a new tool. The two seeded product "
    "rows remain claimable and untouched with their criteria pre-registered "
    "at R2393: state/queue/tech.md runner_suite_timeout_headroom "
    "AC-RTH1..AC-RTH6 and ledger_line_shape_guard AC-LLSG1..AC-LLSG6. No "
    "queue row was stamped and no floor number moved.",

    "2026-11-03 R2394 process note, disclosed rather than buried: the first "
    "battery invocation passed --help and the runner read it as an evidence "
    "PATH, writing a 13859B file literally named --help in the repo root; it "
    "was removed and the CLI contract already pins a bare --help as a "
    "question, so the defect is the runner's argument surface accepting a "
    "flag-shaped positional. A second invocation was killed by the shell "
    "tool after five minutes of buffered silence (its 542844B partial log had "
    "no verdict and was discarded, not counted as evidence); the third and "
    "fourth ran detached with their own evidence paths and are the legs cited "
    "above.",

    "2026-11-03 R2394 self-heal check: BigDomain-OSLoop is still registered "
    "with LogonType=InteractiveToken (state=Ready), which the 2026-09-29 "
    "machine law forbids for every lane task; the registration script already "
    "passes an explicit S4U principal but needs an elevated shell and this "
    "session is unelevated, so the task definition was left untouched "
    "(hundred-and-forty-ninth consecutive disclosure, carried as the stale "
    "row loop-s4u-reconcile in state/debt.md).",

    "R2394 tokens: local=~72k api=0 api_reason=verification-only window "
    "where the carried battery ran twice on the committed tree (leg 1 red on "
    "one untriaged residue round, leg 2 green 520/520 plus controls 7/7 in "
    "1007.7s), one birth-site data repair through the shipped writer at the "
    "predicted +184 bytes, one follow-up matrix regeneration after its "
    "designed first-read FAIL, two commits split per the mixed-tree rule, "
    "one debt row closed and one successor row registered with predicted "
    "sizes, and the state/backlog/heartbeat/export closeout; zero product "
    "module shipped, zero cloud calls, zero external API touches",
]

BACKLOG_ROW = (
    "- [x] R2394 [done 2026-11-03] verification-only - the debt gate named "
    "CLAIM-FIRST item=reconcile-battery-R2387 (carried=7, stale), so the "
    "battery ran first on the committed tree: leg 1 qa/"
    "reconcile-all-R2394b.log read 519/520 with the ONLY red being a real "
    "data defect nobody had seen - os-residue-triage AC-RTR6 read RESIDUE "
    "with round 2382 untriaged because the R2391 fold repair re-pinned its "
    "siblings R2380/R2381 but skipped it; repaired through the shipped "
    "residue_triage_append at the predicted +184 bytes (68151->68335, "
    "TRIAGED) and committed alone as 5183e51a. Leg 2 "
    "qa/reconcile-all-R2394-retry.log read RUNNER PASS 520/520 suites plus "
    "controls 7/7 in 1007.7s with criteria 4096 exactly as registered; "
    "follow-ups ran through battery_followup (matrix FAILED first on the "
    "stale doc without rewriting it, regenerated to 49953B, then all four "
    "PASS, VERDICT R2394 PASS) and evidence plus matrix were committed alone "
    "as d5a63adc. Register: battery-R2387 closed (88365->88368B), successor "
    "reconcile-battery-R2394 registered first=yes (88368->88773B). No "
    "product module shipped this window and none is claimed - the two "
    "seeded rows AC-RTH1..6 / AC-LLSG1..6 stay claimable with criteria "
    "pre-registered at R2393. Disclosed: a --help invocation became an "
    "evidence path and wrote a file named --help (removed), and one leg was "
    "killed by buffered shell output with no verdict (discarded).\n")


def write_state(payload):
    text = json.dumps(payload, ensure_ascii=True, indent=2)
    text = SIO.canon(text)
    temp = STATE + ".tmp"
    with io.open(temp, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    os.replace(temp, STATE)
    with io.open(STATE, "r", encoding="utf-8", newline="") as handle:
        written = handle.read()
    if json.loads(written) != payload:
        raise SystemExit("REFUSED: the state write moved the payload")
    return len(written.encode("utf-8"))


def block_windows(log):
    out = []
    for index, item in enumerate(log):
        if TOKENS_RE.match(item):
            out.append(index + 1)
    return out


def prepend_backlog(row):
    with io.open(BACKLOG, "r", encoding="utf-8", newline="") as handle:
        body = handle.read()
    if "R2394 [done 2026-11-03]" in body:
        raise SystemExit("REFUSED: the backlog already carries this row")
    temp = BACKLOG + ".tmp"
    with io.open(temp, "w", encoding="utf-8", newline="") as handle:
        handle.write(row + body)
    os.replace(temp, BACKLOG)
    with io.open(BACKLOG, "r", encoding="utf-8", newline="") as handle:
        written = handle.read()
    if not written.startswith(row):
        raise SystemExit("REFUSED: the backlog row did not land first")
    return len(written.encode("utf-8"))


def main(argv):
    dry = "--execute" not in argv
    with io.open(STATE, "r", encoding="utf-8", newline="") as handle:
        payload = json.load(handle)
    before = len(io.open(STATE, encoding="utf-8", newline="")
                 .read().encode("utf-8"))
    log = list(payload["log"])
    payload["tick"] = 2394
    already = bool(log) and log[-1] == ITEMS[-1]
    if not already:
        payload["log"] = log + list(ITEMS)
    print("tick=%d log %d -> %d items, before_bytes=%d already=%s"
          % (payload["tick"], len(log), len(payload["log"]), before, already),
          flush=True)
    if dry:
        print("DRY: no byte written", flush=True)
        return 0
    size = write_state(payload)
    print("after append: %d bytes (gate %d)" % (size, GATE), flush=True)
    if size > GATE:
        windows = block_windows(payload["log"])
        chosen = None
        for cut in windows:
            removed = sum(len(item.encode("utf-8")) + 22
                          for item in payload["log"][:cut])
            if size - removed + 200 <= TARGET:
                chosen = cut
                break
        if chosen is None:
            raise SystemExit("REFUSED: no whole-block window reaches the "
                             "target; refusing rather than splitting a round")
        moved = payload["log"][:chosen]
        rest = payload["log"][chosen:]
        rounds = []
        for item in moved:
            match = TOKENS_RE.match(item)
            if match:
                rounds.append("R%s" % match.group(1))
        summary = ('Fold R2394: %d log items (rounds %s) moved verbatim into '
                   'logs/state-log-archive-2026-11.md; every round block moved '
                   'whole, ending on its own ledger line.'
                   % (len(moved), ",".join(rounds)))
        with io.open(ARCHIVE, "a", encoding="utf-8", newline="\n") as handle:
            handle.write("\n## Fold R2394\n")
            for item in moved:
                handle.write(item + "\n")
        payload["log"] = [summary] + rest
        size = write_state(payload)
        print("after fold: %d bytes, moved=%d rounds=%s"
              % (size, len(moved), ",".join(rounds)), flush=True)
        if size > GATE:
            raise SystemExit("REFUSED: still above the gate")
    backlog_bytes = prepend_backlog(BACKLOG_ROW)
    with io.open(HEARTBEAT, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("2026-11-03T01:00+08:00 R2394 battery green 520/520\n")
    print("backlog bytes=%d heartbeat stamped" % backlog_bytes, flush=True)
    check = SIO.report(STATE)
    print("layout crlf=%d bare_lf=%d off_indent=%d ok=%s"
          % (check["crlf"], check["bare_lf"], check["items_off_indent"],
             check["layout_ok"]), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))