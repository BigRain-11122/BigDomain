"""R2431 closeout: append the window items to state.json through the shipped canon writer.

Usage: python src/os/closeout_R2431.py
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
    "2026-11-04 R2431 verification window (five-silence scan clean at open: git status empty at HEAD 5f54ec92 with no .git/index.lock; zero unreplied @BigDomain ledger rows; the content-addressed decisions diff read 165 rows and 110 tokens with new=0 against the stored baseline; the group orders tail max_ts is 2026-11-04 00:46, equal to the stored last_order, so nothing dispatches this company; benchmarks refreshed 2026-11-03 inside the seven-day gate; the queue gauge read tech claimable=10 with the head at state/queue/tech.md:494 prefix AC-BEDP1). The debt gate named CLAIM-FIRST item=reconcile-battery-R2431 carried from R2430 at the pre-registered 543 suites / 4234 criteria, so the battery ran FIRST on the committed tree with zero product edits (the R2168 mixed-tree rule).",
    "2026-11-04 R2431 the first battery leg came back RED ON MY OWN TRANSPORT, NOT ON CODE: 542/543 suites green with the criteria total 4234 EXACTLY as pre-registered (qa/reconcile-all-R2431.log kept as the honest red leg, 843784B, TMP RECLAIM 932/932 worlds 326.59 MiB busy=0 failed=0), the only red suite being reconcile-daily-census at cd7-live-real-tree exit=2 label=drift. qa_writer_census --check named the file and the dialect instead of leaving a guess: qa/battery-R2431-stdout.log read class=cmd-raw, because this window launched the battery with a Start-Process stdout redirect pointed INTO the evidence directory, so the launcher capture itself was filed as evidence.",
    "2026-11-04 R2431 repair at the BIRTH SITE, never by widening the census baseline: the two launcher captures were MOVED out of qa/ into the gitignored logs/ directory (logs/battery-R2431-stdout.log, logs/battery-R2431-stderr.log) so the bytes survive while the evidence face carries only single-writer evidence, after which qa_writer_census --check read files=2487 tee=1958 baselined=529 disappeared=0 flags=0 verdict=DRIFT-CLEAN with the baseline file UNTOUCHED. Nothing was deleted and nothing was reclassified; the defect was where the capture was pointed.",
    "2026-11-04 R2431 the retry leg then ran on the repaired tree with its own captures outside qa/: python src/os/battery_stream.py --evidence qa/reconcile-all-R2431-retry.log read RUNNER PASS (543/543 suites green, reconcile controls 7/7, 956.2s) with the measured criteria total 4234 - the pre-registered number to the unit - and TMP RECLAIM candidates=932 removed=932 busy=0 failed=0 reclaimed=326.59 MiB; the census re-read DRIFT-CLEAN after it.",
    "2026-11-04 R2431 the four follow-up sections produced the designed first FAIL and then a green verdict: leg 1 read VERDICT FAIL failing=matrix at on-disk=52215B against regenerated=52317B and wrote no byte, src/sandbox/suite_matrix.py regenerated docs/sandbox-suite-matrix.md from THIS round green evidence through --stamp-from so the render is stamp-aligned to the doc it is compared with, --check read byte-identical at 52317B / 543 suites / 4234 criteria, and the re-run read VERDICT R2431 PASS failing=none (matrix byte-identical 52317B, fingerprint CLEAN domains=5, profile byte-identical, census DRIFT-CLEAN). Both legs stay appended in the retry evidence tail (1889B FAIL then 1950B PASS, eol_ok=True).",
    "2026-11-04 R2431 debt register after this window: open=1 done=145. reconcile-battery-R2431 was closed through the shipped debt_close at its predicted 106872B -> 106875B (measured exactly, line=165, readback=ok) and ONE leader row product-face-R2432 was appended first=yes through the shipped debt_append at 106875B -> 107167B (readback=ok), naming the next window a product face on the tech head state/queue/tech.md:494 prefix AC-BEDP1 (bare_evidence_deep_pile) whose AC-BEDP1..AC-BEDP6 were pinned at R2404 BEFORE any code. NO successor battery was registered: this window changed no src byte, so the registry still reads 543 suites / 4234 criteria and the R2168 rule does not fire. Remaining open: loop-s4u-reconcile and product-face-R2432.",
    "2026-11-04 R2431 honest disclosures: (a) this window shipped ZERO product code and claims zero product points - the battery consumed the window exactly as the carried row said it would; (b) the red is the FOURTH transport defect this census station has caught and nothing else would have, and for the first time the defect was the harness of the window itself rather than a product writer; (c) no criterion was widened, no baseline entry was added, and the census baseline still reads 529; (d) the window ran far past its 25-minute budget - the red leg (969.9s) plus the retry leg (956.2s) plus the follow-up legs cost well over 35 minutes of battery time - named rather than hidden; (e) tasks.md was not touched, it is the P-47 canonical board and carries no row for this verification window.",
    "R2431 tokens: local=~12k api=0 api_reason=verification window - one battery on the committed R2430 tree at the pre-registered 543 suites / 4234 criteria that came back red on a launcher capture pointed into the evidence directory, one birth-site repair by moving the captures to the gitignored logs face with the census re-read clean and the baseline untouched, one retry battery to RUNNER PASS at the same criteria count, four follow-up sections with one designed matrix FAIL and one green stamp-aligned verdict, one debt row closed and one leader row opened through their shipped CLIs, and the state/export/backlog/heartbeat closeout; zero product code shipped, zero cloud calls and zero external API touches",
    "2026-11-04 R2431 self-heal check: BigDomain-OSLoop still exists and its Principal.LogonType reads InteractiveToken, which the 2026-09-29 machine law forbids for every lane task; src/os/register_loop_task.ps1 passes an explicit S4U principal and needs an elevated shell while this session is unelevated, so the definition was left untouched again (hundred-and-ninety-eighth consecutive disclosure, carried as the stale row loop-s4u-reconcile).",
]


def main():
    raw = state_io.read_raw(STATE)
    state = json.loads(state_io.decode(raw))
    state["tick"] = int(state.get("tick", 0)) + 1
    state.setdefault("log", []).extend(ITEMS)
    payload = json.dumps(state, ensure_ascii=False, indent=2)
    post = state_io.canon(payload)
    before = len(raw)
    print("tick=%d items=%d before=%dB after=%dB" % (state["tick"], len(ITEMS), before, len(post)))
    if "--execute" not in sys.argv:
        print("dry run, wrote nothing")
        return 0
    body = post.encode("utf-8")
    tmp = STATE + ".tmp"
    with open(tmp, "wb") as fh:
        fh.write(body)
    os.replace(tmp, STATE)
    back = state_io.decode(state_io.read_raw(STATE))
    assert back == post, "E_R2431_READBACK"
    print("readback bytes=%d eol_ok=%s" % (len(back.encode("utf-8")), state_io.layout(back)["eol_ok"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())