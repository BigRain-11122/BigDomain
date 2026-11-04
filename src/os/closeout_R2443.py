"""closeout_R2443 - state / backlog / heartbeat closeout for the R2443
verification window (reconcile-battery-R2443, red then green).

Writes the state log through state_io.canon with a byte read-back, prepends
the backlog row, appends the heartbeat row, and refuses any drift. Run with
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

TICK = 2443
DEC_ROWS = 239

LOG = [
    "2026-11-04 R2443 verification window (five-silence scan clean at open: "
    "git status empty at HEAD b55c6a2a with no .git/index.lock; the evolution "
    "ledger carries zero @BigDomain rows; the content-addressed decisions "
    "diff read 177 rows and 118 tokens with new=0 against the stored "
    "baseline; the group orders tail max_ts is 2026-11-04 with last_order "
    "2026-11-04 00:46, so nothing dispatches this company; benchmarks were "
    "refreshed 2026-11-03 inside the seven-day gate; the queue gauge read "
    "FLOOR-MET main 5/5 tech 10/10 explore 10/10 and the deliverable-aware "
    "reader offered state/queue/tech.md:510 prefix AC-PICIC1). The debt gate "
    "named CLAIM-FIRST item=reconcile-battery-R2443 carried from R2442 at the "
    "pre-registered 549 suites / 4270 criteria, so the battery ran FIRST on "
    "the committed tree with zero product edits (the R2168 mixed-tree rule).",

    "2026-11-04 R2443 the first battery leg came back RED on the SUITE the "
    "previous window shipped, not on the product it shipped: 548/549 suites "
    "green with the criteria total 4270 EXACTLY as pre-registered "
    "(qa/reconcile-all-R2443.log kept as the honest red leg, 855436B at "
    "RUNNER close, 1258.9s, TMP RECLAIM 932/932 worlds 326.59 MiB busy=0 "
    "failed=0), the only red being os-matrix-stamp-provenance-line at "
    "AC-MSPL1 'ordinary render keeps the header/label block byte for byte' "
    "with 5 of its 6 criteria green. The cause was read off the assertion "
    "rather than guessed: the suite's block() compared an ORDINARY render "
    "against the SHIPPED doc, and R2442 regenerated that doc with "
    "--stamp-from, so the doc legitimately carries a provenance line the "
    "ordinary render must not carry - the oracle had silently assumed the "
    "shipped artifact stays a plain render forever.",

    "2026-11-04 R2443 repair at the BIRTH SITE, never by widening a "
    "criterion: block() now excludes the stamp_from label line on BOTH sides "
    "while every other header/label line stays byte-compared, and the "
    "absence of that line from an ordinary render is still proved on its own "
    "by the separate AC-MSPL1 assertion, so nothing was relaxed. The suite "
    "re-ran SUITE PASS 6/6 at exit 0 with 6 pass lines and no fail line, and "
    "the repair was committed ALONE as 23901bcf before any further byte "
    "changed. The red leg is preserved, not overwritten.",

    "2026-11-04 R2443 the retry leg then ran on the committed repair tree: "
    "python src/os/battery_stream.py --evidence "
    "qa/reconcile-all-R2443-retry.log read RUNNER PASS (549/549 suites "
    "green, reconcile controls 7/7, 1328.1s) with a measured criteria total "
    "of 4270 - the pre-registered number to the unit - and TMP RECLAIM "
    "candidates=932 removed=932 busy=0 failed=0 reclaimed=326.59 MiB.",

    "2026-11-04 R2443 the four follow-up sections produced the designed "
    "first FAIL and then a green verdict: leg 1 read VERDICT FAIL "
    "failing=matrix at on-disk=52994B against regenerated=52990B and wrote "
    "no byte, src/sandbox/suite_matrix.py regenerated "
    "docs/sandbox-suite-matrix.md from THIS round green evidence through "
    "--stamp-from so the render is stamp-aligned to the doc it is compared "
    "with, --check read byte-identical at 52990B / 549 suites / 4270 "
    "criteria, and the re-run read VERDICT R2443 PASS failing=none (matrix "
    "byte-identical 52990B, fingerprint CLEAN domains=5, profile "
    "byte-identical, census DRIFT-CLEAN). Both legs stay appended in the "
    "evidence tail (1889B FAIL then 1950B PASS, eol_ok=True).",

    "2026-11-04 R2443 debt register after this window: open=1 done=158. "
    "reconcile-battery-R2443 was closed through the shipped debt_close at "
    "its predicted 112389B -> 112392B (measured exactly, line=178, open 2->1, "
    "done 157->158, readback=ok) and ONE leader row product-face-R2444 was "
    "appended first=yes through the shipped debt_append at 112392B -> "
    "112963B (readback=ok), naming the next window a product face on the "
    "tech head state/queue/tech.md:510 prefix AC-PICIC1 "
    "(comma_binding_identity_face_compare), whose AC-PICIC1..AC-PICIC6 were "
    "pinned in that row at R2430 BEFORE any code. NO successor battery was "
    "registered: this window changed only a test file and moved neither the "
    "registry suite count nor the criteria count (still 549 suites / 4270 "
    "criteria), so the R2168 mixed-tree rule does not fire.",

    "2026-11-04 R2443 honest disclosures: (a) this window shipped ZERO "
    "product code and claims zero product points - the battery consumed the "
    "window exactly as the carried row said it would; (b) the red is the "
    "EIGHTH defect this battery has caught and nothing else would have, and "
    "it is a defect in the previous window's own test oracle rather than in "
    "the product it tested - the product's AC-MSPL1 'records nothing extra' "
    "line passed while the byte-level oracle failed, which is exactly how a "
    "suite can rot while its module stays right; (c) no criterion was "
    "widened and no checker relaxed - the excluded line is the one this "
    "product deliberately writes, and its absence from an ordinary render is "
    "asserted separately; (d) the window ran far past its 25-minute budget: "
    "two full batteries at 1258.9s and 1328.1s plus the follow-up legs, "
    "named rather than hidden; (e) tasks.md was not touched, it is the P-47 "
    "canonical board and carries no row for this verification window; (f) "
    "the doc's provenance line still records the doc itself as its borrowed "
    "source, which is the R2442 stamp-aligned render's own honest artefact "
    "and not a new claim this window makes.",

    "2026-11-04 R2443 self-heal check: BigDomain-OSLoop still exists and its "
    "Principal.LogonType reads InteractiveToken, which the 2026-09-29 "
    "machine law forbids for every lane task; "
    "src/os/register_loop_task.ps1 passes an explicit S4U principal and "
    "needs an elevated shell while this session is unelevated, so the "
    "definition was left untouched again (two-hundred-and-tenth consecutive "
    "disclosure, carried as the stale row loop-s4u-reconcile).",
]

TOKENS = ("R2443 tokens: local=~12k api=0 api_reason=verification window - "
          "two full batteries on committed trees (one red at a pre-registered "
          "549 suites / 4270 criteria whose only red was the previous "
          "window's own test oracle, one green at the same criteria count "
          "after a birth-site repair committed alone), four follow-up "
          "sections with one designed matrix FAIL and one green "
          "stamp-aligned verdict, one debt row closed and one leader row "
          "opened through their shipped CLIs, and the "
          "state/export/backlog/heartbeat closeout; zero product code "
          "shipped, zero cloud calls and zero external API touches")

BACKLOG_ROW = (
    "- [x] [done 2026-11-04 R2443] R2443 verification window on the debt "
    "gate first=yes item (reconcile-battery-R2443, carried from R2442): zero "
    "product code changed, the R2168 mixed-tree rule honoured. Leg 1 on the "
    "committed b55c6a2a tree read 548/549 suites at the criteria total 4270 "
    "exactly as pre-registered (qa/reconcile-all-R2443.log kept as the red "
    "leg, 1258.9s, TMP RECLAIM 932/932) and the only red was "
    "os-matrix-stamp-provenance-line at AC-MSPL1: the R2442 suite compared "
    "an ORDINARY render against the SHIPPED doc, which R2442 had regenerated "
    "stamp-aligned, so the doc legitimately carries a provenance line the "
    "ordinary render must not. Repaired at the birth site, never by widening "
    "a criterion: block() excludes the stamp_from line on BOTH sides while "
    "every other header/label line stays byte-compared and the ordinary "
    "render's lack of that line is still asserted on its own; suite 6/6 at "
    "exit 0 and the repair committed ALONE as 23901bcf. Retry on the "
    "committed tree: RUNNER PASS 549/549 plus controls 7/7 in 1328.1s at "
    "criteria 4270 exactly, TMP RECLAIM 932/932 "
    "(qa/reconcile-all-R2443-retry.log). Four follow-ups gave the designed "
    "matrix FAIL at 52994B vs 52990B, a stamp-aligned regeneration to "
    "52990B / 549 / 4270 with --check byte-identical, and VERDICT R2443 PASS "
    "failing=none (fingerprint CLEAN 5 domains, profile byte-identical, "
    "census DRIFT-CLEAN). Debt: battery closed through the shipped debtor at "
    "112389B -> 112392B (line=178, open 2->1, done 157->158, readback ok) "
    "and product-face-R2444 opened first=yes at 112392B -> 112963B naming "
    "state/queue/tech.md:510 AC-PICIC1; no successor battery owed because "
    "only a test file changed. Zero product points claimed.")

HEARTBEAT_ROW = (
    "2026-11-04T21:12:00+08:00 tick=2443 R2443 verification window - "
    "reconcile-battery-R2443 ran red then green on committed trees: leg 1 "
    "548/549 at criteria 4270 with the only red being the R2442 suite's own "
    "block oracle comparing an ordinary render against the stamp-aligned "
    "shipped doc, repaired at the birth site (provenance line excluded on "
    "both sides, every other line still byte-compared) and committed alone "
    "as 23901bcf; retry 549/549 plus controls 7/7 in 1328.1s at criteria "
    "4270, four follow-ups VERDICT R2443 PASS after a stamp-aligned matrix "
    "regeneration to 52990B [via BigDomain-OSLoop]")


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
        raise SystemExit("E_R2443_BACK read-back does not match the write")
    return len(back)


def main(execute):
    if not execute:
        print("DRY RUN tick=%d log_lines=%d" % (TICK, len(LOG) + 1))
        for line in LOG:
            print("  LOG %s" % line[:100])
        return 0

    raw = open(STATE, "rb").read()
    payload = json.loads(raw.decode("utf-8"))
    if payload["tick"] != TICK - 1:
        raise SystemExit("E_R2443_TICK state reads %s, expected %d"
                         % (payload["tick"], TICK - 1))
    payload["tick"] = TICK
    payload["last_decision_rows"] = DEC_ROWS
    payload["log"].extend(LOG)
    payload["log"].append(TOKENS)
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    canonical = state_io.canon(text)
    if json.loads(canonical) != payload:
        raise SystemExit("E_R2443_PAYLOAD canon moved the payload")
    size = write_bytes_atomic(STATE, canonical.encode("utf-8"),
                              ".r2443-state-")
    layout = state_io.layout(canonical)
    print("STATE tick=%d bytes=%d log_len=%d layout_ok=%s crlf=%d bare_lf=%d"
          % (TICK, size, len(payload["log"]), layout["layout_ok"],
             layout["crlf"], layout["bare_lf"]))

    backlog = io.open(BACKLOG, encoding="utf-8", newline="").read()
    if "R2443] R2443 verification window" in backlog:
        raise SystemExit("E_R2443_BACKLOG row already present")
    write_bytes_atomic(BACKLOG, (BACKLOG_ROW + "\n" + backlog).encode(
        "utf-8"), ".r2443-backlog-")
    print("BACKLOG row prepended")

    beat = io.open(HEARTBEAT, encoding="utf-8", newline="").read()
    if "tick=2443 " in beat:
        raise SystemExit("E_R2443_HEARTBEAT row already present")
    if not beat.endswith("\n"):
        beat += "\n"
    write_bytes_atomic(HEARTBEAT, (beat + HEARTBEAT_ROW + "\n").encode(
        "utf-8"), ".r2443-beat-")
    print("HEARTBEAT row appended")
    return 0


if __name__ == "__main__":
    sys.exit(main("--execute" in sys.argv[1:]))