"""R2598 closeout: tick, log items, and a canonical write of src/os/state.json.

The file round-trips through json.dumps(indent=2, ensure_ascii=False) exactly
at open (measured: 69544 bytes, crlf=0), so the write is canonical rather than
a re-layout. Every number written here was measured this window.
"""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
STATE = os.path.join(REPO, "src", "os", "state.json")

ITEMS = [
    "2026-11-10 R2598 VERIFICATION window on the battery the register owed "
    "(reconcile-battery-R2596, pre-registered 631 suites / 4762 criteria). "
    "Five-silence at open measured rather than assumed: git status carried ONE "
    "untracked file (src/os/launch_battery_R2597.py, a one-off detached "
    "launcher whose own docstring says 'deleted before commit', left behind by "
    "the previous window and adopted as residue and removed), no index.lock, "
    "zero @BigDomain rows in cph4/evolution-ledger.md, the content-addressed "
    "decisions scan read 169 tokens against the stored 210 with NEW=[] (the "
    "stored set carries tokens the file has since archived, so the diff is "
    "GONE-only and no decision needed a judgement), the BigDomain orders head "
    "unchanged at 2026-11-09 15:2x and benchmarks 2026-11-03 exactly seven days "
    "old (the refresh gate is '>7 days', so not yet due). The debt gate read "
    "CLAIM-FIRST item=reconcile-battery-R2596 first=1 open=37, the queue head "
    "read state/queue/tech.md:632 prefix AC-EDWT1 claimable=14 and the floor "
    "read FLOOR-MET at 5/5, 14/10, 10/10, so the window was a verification "
    "window and ran the battery BEFORE any product byte.",
    "2026-11-10 R2598 THE TARGET WAS RE-MEASURED BEFORE THE LAUNCH and the "
    "pre-registered figure was STALE by exactly one suite and six criteria: "
    "importing reconcile_all.SUITES read 632 suites / 4768 criteria (632 "
    "unique names, 632 unique paths) against the row's 631/4762, because the "
    "R2597 birth-site repair shipped its own six-criteria suite after that row "
    "was pinned. The battery was launched detached through "
    "src/os/battery_stream.py at 03:07:12 (pid 67084, stream and stderr under "
    "logs/, never a shell redirection into qa/) and finished at 05:16 with "
    "qa/reconcile-all-R2598.log at 1078987 bytes: RUNNER FAIL (8 failed "
    "assertions) in 4095.8s over all 632 suites, zero skipped.",
    "2026-11-10 R2598 THE RED LEG WAS KEPT AND ITS REDS WERE DIAGNOSED rather "
    "than counted: seven suites went red. (a) ledger-apimarket-refundregister "
    "exit=124 on the 600s cap after 191.6s at R2595 and 409.6s at R2596, and "
    "the SAME suite on the SAME tree finished in 296s when run alone at "
    "04:22-04:27 (logs/measure-refundregister.stream), so it is the load "
    "artefact the headroom reader's own docstring names, not a code defect. "
    "(b) SIX readability suites (os-patterns-label-readability and its render "
    "consumer, os-patterns-non-label-text-readability, "
    "os-artifact-disk-text-readability, os-evidence-name-text-coverage, "
    "os-stamp-text-coverage) failed AC-PLR3's doc-equals-render check because "
    "docs/sandbox-suite-matrix.md still renders the 631-row registry while the "
    "registry reads 632 rows - measured by reproducing the render: the fresh "
    "body is 64514 bytes against the doc's 64414 and differs in exactly the "
    "summary row plus the new suite's row.",
    "2026-11-10 R2598 BIRTH-SITE REPAIR, committed alone: the AC-RSC2 "
    "mechanism that exists for exactly this case was used instead of a global "
    "widening - SUITE_TIMEOUT_OVERRIDES now declares "
    "ledger-apimarket-refundregister at 900s (1.5x the slowest measured "
    "in-battery leg) with the measurements cited in the source, verified by "
    "import (suite_timeout 900 for that label, 600 for every other) and by "
    "re-running both timeout guard suites green (os-runner-suite-timeout-cap "
    "6/6, os-runner-suite-timeout-headroom 6/6). The matrix document was NOT "
    "repaired this window: it was regenerated from the red leg and then "
    "judged by its own check face, which resolved the newest RUNNER PASS leg "
    "and refused the document as an evidence-face mismatch, so the "
    "regeneration was REVERTED and the document stands at HEAD with no red-leg "
    "claim baked into it; the six readability reds therefore stay red until a "
    "green leg exists, which is disclosed instead of papered over.",
    "2026-11-10 R2598 BOARD AND DEBT: the four follow-up sections in "
    "src/os/battery_followup.py were NOT run this window - the window spent "
    "its whole budget on the battery and the repair, and the budget overrun is "
    "disclosed rather than hidden. ONE row was seeded through a one-off writer "
    "measured against the file on disk (src/os/queue_seed_R2598.py, "
    "1857644B -> 1859012B, readback ok at line 632): "
    "runner_suite_timeout_headroom.py never reads SUITE_TIMEOUT_OVERRIDES, so "
    "the declared 900s ceiling is invisible to its report (it printed "
    "'slowest=600.0s headroom=0.0s' at cap 600 in the same window), with "
    "criteria AC-EDWU1..AC-EDWU6 pinned BEFORE any code. queue_head then read "
    "the new head at line 632 prefix AC-EDWU1 claimable=15 and queue_floor "
    "read FLOOR-MET at 5/5, 15/10, 10/10. The open debt row "
    "reconcile-battery-R2596 was NOT closed: its note gained ONE segment "
    "through src/os/debt_note_R2598.py (191536B -> 192410B, one line changed, "
    "readback ok) recording the red run, the repair and the reason the row "
    "stays open, and the gate re-read CLAIM-FIRST with first=1 afterwards.",
    "R2598 honest disclosures: (a) ZERO product points and NOTHING a CEO could "
    "newly open - this is a verification window, its only artifacts are a "
    "repaired ceiling, a kept red evidence leg and a seeded queue row; (b) the "
    "battery is RED, not green, so the debt row it was run for remains open and "
    "the next window owes the full battery again on the committed tree; (c) the "
    "six readability reds are structural until a green leg regenerates the "
    "matrix and are named as such rather than repaired by doctoring the "
    "document; (d) while probing flags I ran `python src/sandbox/reconcile_all.py "
    "--list` by mistake, which started a second battery writing its evidence to "
    "a file literally named '--list' in the repo root - it was stopped by the "
    "shell silence limit, the stray file was deleted and the interleaving is "
    "disclosed because it may have added load during its short life (04:20); "
    "(e) src/os/launch_battery_R2597.py was removed as residue, not authored "
    "here; (f) qa/reconcile-all-R2596-retry.log is still untracked from an "
    "earlier window and is committed with this window rather than deleted; "
    "(g) Docker is absent on this host so no containerised sandbox bring-up is "
    "claimed; (h) tasks.md was not touched, it is the P-47 canonical board, and "
    "every P-47 item still waits on CEO physical pieces (merchant id, "
    "mini-program appid/secret); (i) BigDomain-OSLoop still needs an ELEVATED "
    "shell for its S4U re-registration (carried ceo-pending physical item "
    "loop-s4u-reconcile).",
    "R2598 tokens: local=~22k api=0 api_reason=verification window - one "
    "five-silence scan, one debt gate plus one queue head and floor read, one "
    "registry re-measure by import, one detached battery leg of 4095.8s over "
    "632 suites kept red, three reds diagnosed by reproduction, one birth-site "
    "ceiling declared and proved through two guard suites, one matrix "
    "regeneration judged and reverted by its own check face, one queue row "
    "seeded and one debt note appended through measured one-off writers, and "
    "the state/export closeout; zero cloud calls and zero external API touches",
]


def main():
    path = STATE
    raw = io.open(path, "rb").read()
    doc = json.loads(raw.decode("utf-8"))
    before = len(raw)
    assert doc.get("tick") == 2596, doc.get("tick")
    doc["tick"] = 2598
    log = doc.get("log") or []
    for item in ITEMS:
        log.append(item)
    doc["log"] = log
    out = json.dumps(doc, ensure_ascii=False, indent=2)
    io.open(path, "w", encoding="utf-8", newline="\n").write(out)
    back = json.loads(io.open(path, "r", encoding="utf-8").read())
    print("tick=%s bytes %d -> %d items_added=%d log_len=%d"
          % (back.get("tick"), before,
             len(io.open(path, "rb").read()), len(ITEMS), len(back["log"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())