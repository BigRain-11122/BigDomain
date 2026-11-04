"""closeout_R2449 - state / backlog / heartbeat closeout for the R2449
verification window.

Writes the state log through state_io.canon with a byte read-back, prepends the
backlog row, appends the heartbeat row and refuses any drift. Run with
--execute to write; the default is a dry run.
"""

import io
import json
import os
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import state_io  # noqa: E402

STATE = os.path.join(BASE, "state.json")
BACKLOG = os.path.join(BASE, "backlog.md")
HEARTBEAT = os.path.join(ROOT, "heartbeat.txt")

TICK = 2449
DEC_ROWS = 186
ORDER_TS = "2026-11-05 00:36"
NEW_DEC_TOKENS = []

LOG = [
    "2026-11-05 R2449 verification window (five-silence scan at open: git "
    "status empty at HEAD 31a30fd5 with no .git/index.lock; the evolution "
    "ledger carries zero @BigDomain rows; the content-addressed decisions "
    "diff read 123 tokens over 253 lines with new=0 and gone=0 against the "
    "stored baseline; the group orders tail max_ts is 2026-11-05 00:36 equal "
    "to the stored last_order, so nothing dispatches this company; benchmarks "
    "were refreshed 2026-11-03 inside the seven-day gate; the queue head "
    "reads state/queue/tech.md:516 prefix AC-SEWD1). The debt gate named "
    "CLAIM-FIRST item=reconcile-battery-R2449 carried from R2448 at the "
    "pre-registered 552 suites / 4288 criteria, so the battery ran FIRST on "
    "the committed tree with zero product edits (the R2168 mixed-tree rule).",
    "2026-11-05 R2449 the battery read RUNNER PASS on the FIRST leg and no "
    "red leg exists for this round because none was produced, stated rather "
    "than implied: 552/552 suites green plus reconcile controls 7/7 in "
    "1235.9s with a measured criteria total of 4288 - the pre-registered "
    "number to the unit - and TMP RECLAIM candidates=932 removed=932 busy=0 "
    "failed=0 reclaimed=326.59 MiB (qa/reconcile-all-R2449.log, 852581B, "
    "crlf=0, one utf-8 LF single writer through src/os/battery_stream.py).",
    "2026-11-05 R2449 the four follow-up sections, through the shipped "
    "battery_followup callable, produced the designed first FAIL and then a "
    "green verdict: leg 1 read SECTION matrix FAIL at on-disk=53313B against "
    "regenerated=53304B and wrote no byte, src/sandbox/suite_matrix.py then "
    "regenerated docs/sandbox-suite-matrix.md from THIS round own eligible "
    "evidence (qa/reconcile-all-R2449.log) through --stamp-from, --check read "
    "byte-identical at 53304B / 552 suites / 4288 criteria, and the re-run "
    "read VERDICT R2449 PASS failing=none with fingerprint CLEAN domains=5, "
    "profile byte-identical and census DRIFT-CLEAN. Both legs stay appended "
    "in the evidence tail (1889B FAIL then 1950B eol_ok=True).",
    "2026-11-05 R2449 the matrix became self-describing again: it was "
    "regenerated from THIS round own green battery evidence rather than a "
    "borrowed older leg, so its own green line reads 552/552 instead of the "
    "551/552 the R2448 render honestly had to carry. The R2445 ordering law "
    "is restated for the next writer: a matrix regeneration must name an "
    "evidence file that is BOTH eligible (all green) and the one --check will "
    "resolve.",
    "2026-11-05 R2449 debt register after this window: open=1 done=165. "
    "reconcile-battery-R2449 was closed through the shipped debt_close at its "
    "predicted 115711B -> 115714B (line=185, open 3->2, done 163->164, "
    "readback=ok), the carried fold-due-R2445 row was closed through the same "
    "CLI at 115714B -> 115718B (line=181, open 2->1, done 164->165, "
    "readback=ok, discharged by measurement: state_fold --check reads "
    "FOLD-CLEAR at 69469B against the 78500B gate with margin 9031B and "
    "archive=present), and ONE leader row product-face-R2450 was appended "
    "first=yes through debt_append at 115718B -> 116179B (readback=ok) naming "
    "the next window a product face on the tech head state/queue/tech.md:516 "
    "prefix AC-SEWD1 (status_export_writer_dialect_wire), whose "
    "AC-SEWD1..AC-SEWD6 were pinned in that row at R2448 BEFORE any code. NO "
    "successor battery was registered: this window changed no product src "
    "byte and moved neither the registry suite nor the criteria count (still "
    "552 / 4288), so the R2168 rule does not fire. Remaining open: "
    "loop-s4u-reconcile.",
    "2026-11-05 R2449 honest disclosures: (a) this window shipped ZERO "
    "product code and claims zero product points - the battery consumed the "
    "window exactly as the carried row said it would; (b) no defect was "
    "caught this round, which is the honest reading and not a result the "
    "battery is asked to manufacture; (c) a real mistake of mine is recorded "
    "rather than smoothed - I probed `python src/sandbox/reconcile_all.py "
    "--help`, a flag that runner does not implement, so it STARTED a second "
    "run and created a stray file literally named --help in the repo root; "
    "the file was deleted, git status then showed only the untracked evidence "
    "log, and no tracked byte was modified - the battery had already "
    "finished, so no evidence leg is contaminated; (d) the window ran past "
    "its 25-minute budget on one 1235.9s battery plus the follow-up legs, "
    "named rather than hidden; (e) tasks.md was not touched, it is the P-47 "
    "canonical board and carries no row for a verification window; (f) the "
    "export's DO/latest_artifact fields describe this round's battery and "
    "matrix rather than a new product face because no product face shipped, "
    "and that is stated rather than dressed up as a deliverable; (g) the "
    "CEO group order OB-20261105-003656-879 (stop building mechanisms and "
    "rules, deliver real output) dispatches bm-a/bm-b/bm-c/bm-m and carries "
    "no BigDomain action, so it is ACKNOWLEDGED-NO-ACTION - but its spirit is "
    "honestly noted here against this station: the tech queue it has been "
    "walking for nine windows is entirely internal audit tooling, so a "
    "strategy line was written to HQ-FEEDBACK.md asking whether the tech "
    "queue should be suspended in favour of the P-47 business faces; (h) "
    "src/os/state.json stood at 69469B against the 78500B waterline before "
    "this closeout, FOLD-CLEAR.",
    "2026-11-05 R2449 self-heal check: BigDomain-OSLoop still exists and its "
    "Principal.LogonType reads InteractiveToken, which the 2026-09-29 "
    "machine law forbids for every lane task; src/os/register_loop_task.ps1 "
    "passes an explicit S4U principal and needs an elevated shell while this "
    "session is unelevated, so the definition was left untouched again "
    "(two-hundred-and-fifteenth consecutive disclosure, carried as the stale "
    "row loop-s4u-reconcile).",
]

TOKENS = (
    "R2449 tokens: local=~11k api=0 api_reason=verification window - one full "
    "battery on the committed tree at a pre-registered 552 suites / 4288 "
    "criteria (green on the first leg), four follow-up sections through the "
    "shipped callable with one designed matrix FAIL and one green "
    "stamp-aligned verdict rendered from this round own eligible evidence, two "
    "debt rows closed and one leader row opened through their shipped CLIs, "
    "and the state/export/backlog/heartbeat closeout; zero product code "
    "shipped, zero cloud calls and zero external API touches"
)

BACKLOG_ROW = (
    "- [x] [done 2026-11-05 R2449] R2449 verification window on the debt gate "
    "first=yes item (reconcile-battery-R2449, carried from R2448 at the "
    "pre-registered 552 suites / 4288 criteria): zero product code changed, "
    "the R2168 mixed-tree rule honoured. The battery ran FIRST on the "
    "committed 31a30fd5 tree and read RUNNER PASS on the FIRST leg - 552/552 "
    "suites green, controls 7/7, 1235.9s, criteria total 4288 EXACTLY as "
    "pre-registered (qa/reconcile-all-R2449.log, 852581B, crlf=0), TMP RECLAIM "
    "932/932 busy=0 failed=0. Four follow-up sections: matrix FAILED first at "
    "on-disk=53313B against regenerated=53304B with no byte written, "
    "suite_matrix regenerated docs/sandbox-suite-matrix.md from this round own "
    "eligible evidence through --stamp-from, --check read byte-identical at "
    "53304B / 552 suites / 4288 criteria with green=552/552, and the re-run "
    "read VERDICT R2449 PASS failing=none (fingerprint CLEAN domains=5, "
    "profile byte-identical, census DRIFT-CLEAN); both legs stay in the "
    "evidence tail (1889B FAIL then 1950B PASS, eol_ok=True). Debt: "
    "reconcile-battery-R2449 closed at 115711B -> 115714B (line=185, open "
    "3->2, done 163->164, readback ok), fold-due-R2445 closed at 115714B -> "
    "115718B (line=181, open 2->1, done 164->165, readback ok, discharged by "
    "state_fold --check FOLD-CLEAR at 69469B against the 78500B gate), and "
    "product-face-R2450 opened first=yes at 115718B -> 116179B naming the tech "
    "head state/queue/tech.md:516 prefix AC-SEWD1; no successor battery was "
    "registered because this window moved no product byte and no registry "
    "count. Zero product points claimed; disclosed that an unsupported --help "
    "probe started a stray second run whose only residue was a repo-root file "
    "literally named --help (deleted, no tracked byte touched), that the "
    "window ran past its 25-minute budget, and that a strategy line was "
    "written to HQ-FEEDBACK.md about pivoting the tech queue toward the P-47 "
    "business faces under CEO order OB-20261105-003656-879."
)

HEARTBEAT_ROW = (
    "2026-11-05T03:40:00+08:00 tick=2449 R2449 verification window - the full "
    "battery went green on the first leg at the pre-registered 552 suites / "
    "4288 criteria in 1235.9s, and the suite matrix was regenerated from this "
    "round own green evidence so its green line reads 552/552 for the first "
    "time in four windows; the carried fold debt closed at FOLD-CLEAR "
    "69469B/78500B, leaving only the S4U reconcile open [via BigDomain-OSLoop]"
)


def write_bytes_atomic(path, data, prefix):
    folder = os.path.dirname(os.path.abspath(path))
    handle, temp = tempfile.mkstemp(dir=folder, prefix=prefix)
    try:
        with os.fdopen(handle, "wb") as sink:
            sink.write(data)
            sink.flush()
            os.fsync(sink.fileno())
        os.replace(temp, path)
    except BaseException:
        try:
            os.unlink(temp)
        except OSError:
            pass
        raise
    back = open(path, "rb").read()
    if back != data:
        raise SystemExit("E_R2449_BACK read-back does not match the write")
    return len(back)


def main(execute):
    if not execute:
        print("DRY RUN tick=%d log_lines=%d new_dec=%d"
              % (TICK, len(LOG) + 1, len(NEW_DEC_TOKENS)))
        for line in LOG:
            print("  LOG %s" % line[:100])
        print("  TOKENS %s" % TOKENS[:100])
        return 0

    raw = open(STATE, "rb").read()
    payload = json.loads(raw.decode("utf-8"))
    if payload["tick"] != TICK - 1:
        raise SystemExit("E_R2449_TICK state reads %s, expected %d"
                         % (payload["tick"], TICK - 1))
    payload["tick"] = TICK
    payload["last_decision_rows"] = DEC_ROWS
    payload["last_order"] = ORDER_TS
    tokens = sorted(set(list(payload["last_dec_tokens"]) + NEW_DEC_TOKENS))
    payload["last_dec_tokens"] = tokens
    payload["log"].extend(LOG)
    payload["log"].append(TOKENS)
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    canonical = state_io.canon(text)
    if json.loads(canonical) != payload:
        raise SystemExit("E_R2449_PAYLOAD canon moved the payload")
    size = write_bytes_atomic(STATE, canonical.encode("utf-8"),
                              ".r2449-state-")
    layout = state_io.layout(canonical)
    print("STATE tick=%d bytes=%d log_len=%d tokens=%d layout_ok=%s crlf=%d "
          "bare_lf=%d" % (TICK, size, len(payload["log"]), len(tokens),
                          layout["layout_ok"], layout["crlf"],
                          layout["bare_lf"]))

    backlog = io.open(BACKLOG, encoding="utf-8", newline="").read()
    if "R2449] R2449 verification window" in backlog:
        raise SystemExit("E_R2449_BACKLOG row already present")
    write_bytes_atomic(BACKLOG, (BACKLOG_ROW + "\n" + backlog).encode(
        "utf-8"), ".r2449-backlog-")
    print("BACKLOG row prepended")

    beat = io.open(HEARTBEAT, encoding="utf-8", newline="").read()
    if "tick=2449 " in beat:
        raise SystemExit("E_R2449_HEARTBEAT row already present")
    if not beat.endswith("\n"):
        beat += "\n"
    write_bytes_atomic(HEARTBEAT, (beat + HEARTBEAT_ROW + "\n").encode(
        "utf-8"), ".r2449-beat-")
    print("HEARTBEAT row appended")
    return 0


if __name__ == "__main__":
    sys.exit(main("--execute" in sys.argv[1:]))