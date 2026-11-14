"""state_append_R2747 - record the R2747 adoption, the fold-caliber birth-site
repair, the round-aligned fold and the honest disclosures through the
canonical writer.
"""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import state_io  # noqa: E402

STATE = os.path.join(BASE, "state.json")
TICK = 2747

LINES = [
    "2026-11-15 R2747 ADOPTION window on reconcile-battery-R2742 that became a BIRTH-SITE "
    "REPAIR instead: the leg had ended before open and was adopted by its evidence path, never "
    "relaunched. Five readings at open: git status carried one untracked evidence file and no "
    "index.lock; PID 64528 read GONE; logs/battery-R2742.stream closed 'RUNNER FAIL (6 failed "
    "assertions) BATTERY rc=1 4308.6s'; qa/reconcile-all-R2742.log measured 1252699B utf-8 "
    "bom=False crlf=0 lone_cr=0 nul=0 with 671 PASS suite rows carrying 671 UNIQUE names, 6 "
    "FAIL rows (five suites plus the summary) and an INDEPENDENT criteria recount summing to "
    "EXACTLY 5032 - byte for byte the 676 suites / 5032 criteria the debt row pre-registered. "
    "debt_gate read CLAIM-FIRST item=reconcile-battery-R2742 open=11 and queue_head read tech "
    "line=713 prefix AC-LKNF1 claimable=10.",

    "R2747 THE FIVE RED SUITES WERE THE LEDGER FAMILY AND THEY WERE RE-RUN, NOT READ: "
    "os-ledger-lines, os-ledger-archive, os-ledger-baseline, os-ledger-fold-kind and "
    "os-ledger-fold-kind-dateprefix - exactly the five R2745 repaired mid-leg by restoring the "
    "R2742 tokens line through the canonical writer. Under the R2738 precedent a red row repaired "
    "mid-leg is not evidence about the repaired tree, so this window executed them individually "
    "on the FINAL committed tree at HEAD 377893c4 and all five read rc=0 GREEN "
    "(8/8, 8/8, 8/8, 6/6, 6/6 = 36 criteria, qa/ledger-five-R2747.log). The leg itself is kept "
    "as RED evidence and is NOT re-litigated; a successor full battery on the committed tree is "
    "launched detached after the closeout commit for the next window to adopt.",

    "R2747 THE FOLD CALIBER DEFECT WAS REPAIRED AT THREE SITES BECAUSE THE LEG WAS FINALLY DONE: "
    "R2746 shipped tools/fold_caliber_check.py as a read side and refused to patch the live leg "
    "for measurement reasons; that block is lifted. src/os/logs_toolkit.py gained one helper "
    "item_indent_caliber that derives the item indent FROM THE DOCUMENT and accepts a uniform "
    "two-space block beside the legacy sixteen while still refusing an eight-space or mixed "
    "block, and it is now used by all three faces: split_ps_layout (which also now accepts the "
    "comma-carrying close '  ],' that the real document actually emits), eol_profile (same close "
    "defect, which is why it counted 104 items on a 98-item log and called a healthy file an "
    "indent disease) and the cmd_fold summary literal, which finally carries the measured caliber "
    "instead of a hardcoded sixteen spaces. split_ps_layout returns the caliber as a fifth tuple "
    "element; its only caller is cmd_fold.",

    "R2747 A SECOND PRE-EXISTING DEFECT WAS FOUND AND REPAIRED IN THE SAME SUITE, and it is a "
    "calendar rot: test_logs_toolkit.py pinned the archive filename at "
    "state-log-archive-2026-10.md while the tool names the archive from datetime.now(CST), so the "
    "whole suite went red the moment the calendar left 2026-10. Proven pre-existing rather than "
    "caused by this window by running the HEAD copy of both files in an isolated directory, which "
    "failed at the identical assertion. Repaired with an archive_name() helper derived from the "
    "tool own CST; one census fixture keeps a fixed 2026-10 key on purpose because there the month "
    "is a fixture key rather than a clock reading. Suite reads SUITE PASS 163 checks rc=0.",

    "R2747 THE WATERLINE RED WAS CLEARED BY A ROUND-ALIGNED FOLD, and the FIRST ATTEMPT WAS BORN "
    "BROKEN AND CAUGHT BY THE LEDGER GATES: folding a naive window-slice 1:60 cut round R2739 in "
    "half, moving its narrative into the archive while its tokens line stayed live, and "
    "ledger_lines.py immediately read ledger_without_round 2739 with VERDICT DIRTY, reddening five "
    "suites. Repaired at the birth site rather than papered over: state.json was restored "
    "byte-exactly from logs/state-preop-R2747.bak (96461B) and the archive appendix was truncated "
    "back to its pre-fold 3087067B, then the window was aligned to item 61, the last line of "
    "R2739. The second fold read window-slice 1:61, token_ok True, gate_ok True, would_fail "
    "empty, and executed through the repaired caliber: state.json 96461B -> 47708B against a "
    "78500B waterline, margin +30792B, and the fresh summary line classifies as OTHER rather than "
    "as a round narrative. ledger_lines.py then read lines=44 ledger=7 round=36 other=1 "
    "rounds_without_ledger=none ledger_without_round=none VERDICT CLEAN, and all six related "
    "suites re-ran green (the five ledger suites plus os-logs-toolkit 163 checks).",

    "R2747 honest disclosures: (a) ZERO product points by the Executive Protocol scale - a "
    "repaired tool, a cleared waterline, a green five-suite receipt and a measured RED leg are "
    "unblocking and evidence, not something a CEO can newly open, and every P-47 business face "
    "still waits on CEO physical pieces (merchant id, mini-program appid/secret); (b) the R2742 "
    "leg is NOT closed by this window - it measured 671/676 RED and a successor battery on the "
    "committed tree is launched detached after the closeout, so the debt row stays open naming "
    "that leg rather than being closed on individual re-runs; (c) os-logs-toolkit is NOT "
    "registered in src/sandbox/reconcile_all.py SUITES, so the 163 checks that guard state.json "
    "surgery are invisible to every battery and its calendar rot went unseen from 2026-11-01 to "
    "today - that gap is recorded here and seed the queue rather than being silently fixed; (d) "
    "the registry is unmoved at 676 suites / 5032 criteria measured by import, so this window "
    "owes no successor battery by the R2168 mixed-tree rule and the launch is a retry of the "
    "R2742 obligation, not a new one; (e) src/os still carries hundreds of one-off closeout "
    "scripts, pre-existing bloat this window neither created nor cleaned, and this window added "
    "one; (f) tasks.md was not touched, it is the P-47 canonical board; (g) Docker is absent on "
    "this host; (h) BigDomain-OSLoop still reads InteractiveToken and needs an ELEVATED shell for "
    "its S4U re-registration (carried ceo-pending physical item loop-s4u-reconcile).",

    "R2747 tokens: local=~18k api=0 api_reason=adoption plus birth-site repair window - one "
    "open five-reading scan with a kernel-free pid check, one byte-level evidence measurement "
    "with an independent criteria recount of 5032 and a unique-name census, one debt gate and "
    "one queue head read, two individual five-suite ledger re-runs on the final committed tree, "
    "three root-cause reads of the shipped gates, one three-site caliber patch with a shared "
    "helper, one isolated HEAD-copy proof that the suite rot was pre-existing, eleven fixture "
    "archive-name replacements with one deliberate revert, one full suite green at 163 checks, "
    "one naive fold that the ledger gates caught and one byte-exact restore of both state and "
    "archive, one round-aligned refold with a token-complete summary, six post-fold suites green "
    "and one registry count by import; zero cloud calls and zero external API touches",
]


def main():
    raw = state_io.read_raw(STATE)
    data = state_io.parse(state_io.decode(raw))
    log = data["log"]
    if any(l.startswith("R2747 ") for l in log):
        sys.stdout.write("NOOP existing R2747 lines\n")
        return 0
    before = len(log)
    log.extend(LINES)
    data["tick"] = TICK
    state_io.write_document(STATE, data)
    after = len(state_io.parse(state_io.decode(state_io.read_raw(STATE)))["log"])
    sys.stdout.write("log %d->%d tick %d\n" % (before, after, TICK))
    return 0


if __name__ == "__main__":
    sys.exit(main())
