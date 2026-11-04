"""R2433 closeout: append the window items to state.json through the shipped canon writer.

Usage: python src/os/closeout_R2433.py [--execute]
Pure local, no clock read beyond the literal strings supplied here.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import state_io  # noqa: E402

STATE = os.path.join(ROOT, "src", "os", "state.json")

ITEMS = [
    "2026-11-04 R2433 verification window (five-silence scan clean at open: git status empty at HEAD fa9ddb91 with no .git/index.lock; zero unreplied @BigDomain ledger rows; the content-addressed decisions diff read 165 rows and 110 tokens with new=0 against the stored baseline; the group orders tail max_ts is 2026-11-04 00:46, equal to the stored last_order, so nothing dispatches this company; benchmarks refreshed 2026-11-03 inside the seven-day gate; the queue gauge read tech claimable=10 and queue_head_delivered walked over the delivered AC-BEDP1 row to offer state/queue/tech.md:498 prefix AC-GWDA1). The debt gate named CLAIM-FIRST item=reconcile-battery-R2433 carried from R2432 at the pre-registered 544 suites / 4240 criteria, so the battery ran FIRST on the committed tree with zero product edits (the R2168 mixed-tree rule).",
    "2026-11-04 R2433 the first battery leg came back RED ON THE CEO-VISIBLE FACE, NOT ON CODE: 543/544 suites green with the criteria total 4240 EXACTLY as pre-registered (qa/reconcile-all-R2433.log kept as the honest red leg, 1029.8s, TMP RECLAIM 932/932 worlds 326.59 MiB busy=0 failed=0), the only red suite being os-queue-floor-export-face at AC-QFE3, whose own detail measured pass=18 fail=3 instead of 21/21.",
    "2026-11-04 R2433 the three failures were named by the shipped checker rather than guessed: self_drive.log_lines_in_window stored=19 recomputed=23, self_drive.substantive_non_idle_mention_lines the same 19 against 23, and results.tick_row expected exactly 1 row with the tick label but found 2 (tick 2432 at index 1 and tick 2431 at index 3). Root cause measured on the document itself: the R2432 closeout edited docs/status-export.json through an ad-hoc step that INSERTED a fresh tick row instead of updating the surviving one, and sampled self_drive BEFORE its own state append, so four log items landed after the count was taken.",
    "2026-11-04 R2433 repair at the BIRTH SITE, never by widening the checker: src/os/repair_R2433.py keeps the row with the largest tick, removes every other label row, sets the value to the live state tick, and re-derives self_drive through the SHIPPED export_R2431.self_drive() callable so no second derivation is written in this window; the dry run predicted exactly the three measured deltas (19 -> 23 twice, one row removed at index 3) and 64472B -> 64418B, the executed write proved its bytes with a read-back, and check_export_consistency then read SUMMARY pass=21 fail=0 VERDICT PASS. The repair was committed ALONE as da5dfc5e before any further byte changed.",
    "2026-11-04 R2433 the retry leg then ran on the committed repair tree: python src/os/battery_stream.py --evidence qa/reconcile-all-R2433-retry.log read RUNNER PASS (544/544 suites green, reconcile controls 7/7, 1017.4s) with the measured criteria total 4240 - the pre-registered number to the unit - and TMP RECLAIM candidates=932 removed=932 busy=0 failed=0 reclaimed=326.59 MiB; the census re-read DRIFT-CLEAN after it.",
    "2026-11-04 R2433 the four follow-up sections produced the designed first FAIL and then a green verdict: leg 1 read VERDICT FAIL failing=matrix at on-disk=52317B against regenerated=52412B and wrote no byte, src/sandbox/suite_matrix.py regenerated docs/sandbox-suite-matrix.md from THIS round green evidence through --stamp-from so the render is stamp-aligned to the doc it is compared with, --check read byte-identical at 52412B / 544 suites / 4240 criteria, and the re-run read VERDICT R2433 PASS failing=none (matrix byte-identical 52412B, fingerprint CLEAN domains=5, profile byte-identical, census DRIFT-CLEAN). Both legs stay appended in the retry evidence tail (1889B FAIL then 1950B PASS, eol_ok=True).",
    "2026-11-04 R2433 debt register after this window: open=2 done=147. reconcile-battery-R2433 was closed through the shipped debt_close at its predicted 107547B -> 107550B (measured exactly, line=167, readback=ok) and ONE leader row product-face-R2434 was appended first=yes through the shipped debt_append at 107550B -> 107858B (readback=ok), naming the next window a product face on the tech head state/queue/tech.md:498 prefix AC-GWDA1 (general_writer_dialect_audit) whose AC-GWDA1..AC-GWDA6 were pinned at R2409 BEFORE any code. NO successor battery was registered: this window changed no product src byte (the one-off repair script carries no suite), so the registry still reads 544 suites / 4240 criteria and the R2168 rule does not fire. Remaining open: loop-s4u-reconcile and product-face-R2434.",
    "2026-11-04 R2433 honest disclosures: (a) this window shipped ZERO product code and claims zero product points - the battery consumed the window exactly as the carried row said it would; (b) the red is the FIFTH defect this battery has caught and nothing else would have, and the first one found in the CEO-VISIBLE export face rather than in evidence transport, which is why the merge of the R2432 export edit was worth re-measuring rather than trusting; (c) no criterion was widened, no checker rule relaxed, and check_export_consistency itself was not touched - only the document it judges; (d) the window ran far past its 25-minute budget - the red leg (1029.8s) plus the retry leg (1017.4s) plus the follow-up legs cost well over 35 minutes of battery time - named rather than hidden; (e) tasks.md was not touched, it is the P-47 canonical board and carries no row for this verification window; (f) the ordering law this red exposes is now stated for the next writer: the export refresh must run AFTER the state append, because a self_drive taken before its own append is stale the moment the append lands.",
    "R2433 tokens: local=~15k api=0 api_reason=verification window - one battery on the committed R2432 tree at the pre-registered 544 suites / 4240 criteria that came back red on the CEO-visible export face, one birth-site repair through the shipped self_drive derivation with one surviving tick row and a read-back proof committed alone, one retry battery to RUNNER PASS at the same criteria count, four follow-up sections with one designed matrix FAIL and one green stamp-aligned verdict, one debt row closed and one leader row opened through their shipped CLIs, and the state/export/backlog/heartbeat closeout; zero product code shipped, zero cloud calls and zero external API touches",
    "2026-11-04 R2433 self-heal check: BigDomain-OSLoop still exists and its Principal.LogonType reads InteractiveToken, which the 2026-09-29 machine law forbids for every lane task; src/os/register_loop_task.ps1 passes an explicit S4U principal and needs an elevated shell while this session is unelevated, so the definition was left untouched again (two-hundredth consecutive disclosure, carried as the stale row loop-s4u-reconcile).",
]


def main():
    raw = state_io.read_raw(STATE)
    state = json.loads(state_io.decode(raw))
    state["tick"] = int(state.get("tick", 0)) + 1
    state.setdefault("log", []).extend(ITEMS)
    payload = json.dumps(state, ensure_ascii=False, indent=2)
    post = state_io.canon(payload)
    before = len(raw)
    print("tick=%d items=%d before=%dB after=%dB"
          % (state["tick"], len(ITEMS), before, len(post)))
    if "--execute" not in sys.argv:
        print("dry run, wrote nothing")
        return 0
    body = post.encode("utf-8")
    tmp = STATE + ".tmp"
    with open(tmp, "wb") as fh:
        fh.write(body)
    os.replace(tmp, STATE)
    back = state_io.decode(state_io.read_raw(STATE))
    assert back == post, "E_R2433_READBACK"
    print("readback bytes=%d eol_ok=%s" % (len(back.encode("utf-8")),
                                           state_io.layout(back)["eol_ok"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())