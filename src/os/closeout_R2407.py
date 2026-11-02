# closeout_R2407.py - the R2407 verification window: the carried battery ran
# FIRST on the committed tree, its one real defect (a fold that split a round)
# was repaired at its birth site, the guard and its suite shipped, and the
# closeout re-derives the live faces from the real tree.
import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
sys.path.insert(0, BASE)

import state_io  # noqa: E402
import ledger_line_shape_guard as LLSG  # noqa: E402
import queue_floor_export_face as QFEF  # noqa: E402
import check_export_consistency as CEC  # noqa: E402

STATE = os.path.join(BASE, "state.json")
EXPORT = os.path.join(REPO, "docs", "status-export.json")
HEART = os.path.join(REPO, "heartbeat.txt")
BACKLOG = os.path.join(BASE, "backlog.md")
DEBT = os.path.join(REPO, "state", "debt.md")

STAMP = "2026-11-03T08:5x:00+08:00"
DO = ("R2407 verification: the carried battery ran on the committed tree and "
      "found one real defect - the R2405 fold cut a round in half - so the "
      "fold now refuses a round-split window")
ART = ("src/os/state_fold.py + src/os/test_fold_round_block_boundary.py + "
       "qa/reconcile-all-R2407.log + qa/reconcile-all-R2407-retry.log + "
       "qa/fold-round-block-boundary-R2407.log")
NEXT = ("run the battery a third leg on the closed-out tree (target 532 "
        "suites / 4168 criteria), then claim state/queue/tech.md AC-LDWS1")

DECISIONS = ["D-20261103-07", "D-20261103-08", "D-20261103-09",
             "D-20261103-10", "D-20261103-11"]

LEDGER = (
    "R2407 tokens: local=~38k api=0 api_reason=verification window - the "
    "carried battery ran twice on committed trees (1015.9s then 1187.4s), the "
    "first leg measured three red ledger suites and the single cause was a "
    "fold that cut the R2395 block after its tokens line while the round's "
    "closeout disclosure stayed live, one shared guard now refuses that cut "
    "before any write, one orphan line was moved verbatim to the archive and "
    "dropped from the live log, one six-criteria suite shipped with its "
    "criteria registered after the repair and disclosed as such, the residue "
    "declaration was re-pinned through the shipped CLI at its predicted "
    "70344->70447 bytes, and the state/export/backlog/heartbeat closeout; "
    "zero cloud calls and zero external API touches")

LOG = [
    ("2026-11-03 R2407 verification window (five-silence scan at open: empty "
     "git status at HEAD 6618b360, no .git/index.lock; LEDGER @BigDomain "
     "addressed rows=0 unreplied=0; DEC tokens 95 new=0 against a 97-token "
     "baseline whose two extra tokens are superseded lines, so nothing new to "
     "judge; the local orders table tail is the 2026-09-28 batch already "
     "acknowledged and the group orders tail is the 2026-11-02 voicebank/CPU "
     "work, neither of which dispatches this company; benchmarks refreshed "
     "2026-11-02 inside the seven-day gate; floor FLOOR-MET main 5/5 tech "
     "10/10 explore 10/10). The debt gate had first claim on "
     "reconcile-battery-R2406, whose note recorded that R2406 changed src/os "
     "and one registry line, so the R2168 mixed-tree rule put the battery "
     "FIRST with zero product edits."),
    ("2026-11-03 R2407 battery red leg, measured not guessed: RUNNER FAIL "
     "528/531 suites in 1015.9s with three red suites and NOTHING changed by "
     "this window (qa/reconcile-all-R2407.log, 836034B, crlf=0). All three "
     "were the same birth-site defect: os-ledger-lines read "
     "rounds_without_ledger=[2395], os-ledger-archive read the same live gate "
     "unclean, and os-ledger-baseline exited 2 while printing 8/8. The live "
     "log carried the R2395 closeout disclosure as its second item while "
     "R2395's own 'tokens:' ledger line sat in logs/"
     "state-log-archive-2026-11.md - so ledger coverage read a round line "
     "with no ledger. Cause: the R2405 fold chose its window at a tokens "
     "line, but R2395 appended its disclosures AFTER the ledger, so the "
     "tokens line was not the block's last line."),
    ("2026-11-03 R2407 repair at the birth site: SHIPPED the guard in "
     "src/os/state_fold.py (round_split(window, kept), asked inside "
     "plan_fold and in fold()'s fail list as round-split, PLAN_KEYS extended "
     "in the same change so the pinned key set is not silently widened). It "
     "refuses only the exact shape measured: the last moved line is round "
     "X's own tokens line AND the first kept line still OPENS with round X. "
     "Proved on the real material: the R2395 shape returns R2395, a cut at "
     "the next round's opener returns None, and a mesage that merely mentions "
     "R2395 mid-line returns None, so ordinary cuts still fold. The live log "
     "was repaired through src/os/repair_R2407.py (dry run first): the orphan "
     "1461B line was appended verbatim to the archive and removed from the "
     "live log, 75 -> 74 items, state 75142 -> 73660 bytes, and all three red "
     "suites then read 8/8 green directly."),
    ("2026-11-03 R2407 evidence and board: the guard's own suite "
     "os-fold-round-block-boundary reads 6/6 twice with an identical digest "
     "and three adjacent suites green (qa/fold-round-block-boundary-R2407.log, "
     "1257B, legs=2 identical=True adjacent=3 fails=0), state_fold's own "
     "suite stays 6/6, and the registry reads 532 suites / 4168 criteria. The "
     "repair and the guard were committed ALONE (e997d2bf) before any retry, "
     "which is the R2405 order."),
    ("2026-11-03 R2407 retry leg: RUNNER FAIL 530/532 suites in 1187.4s "
     "(qa/reconcile-all-R2407-retry.log, 836847B, crlf=0) - the three ledger "
     "suites were green and the two remaining reds were this window's own "
     "closeout counters, not product regressions: os-residue-triage read "
     "RESIDUE because the repair left the triage declaration one item stale "
     "(250 declared against 249 live items), and os-queue-floor-export-face "
     "read AC-QFE3 19/21 because the export still carried "
     "log_lines_in_window=62 against a recomputed 61 after the item moved out "
     "of the live log. Both were repaired the honest way: the declaration was "
     "re-pinned through the shipped CLI at its own predicted 70344->70447 "
     "bytes (entries 249->250, dropped=0) and residue_triage now reads 6/6 "
     "green, and the export is re-derived from the real tree by this closeout "
     "rather than hand-edited."),
    ("2026-11-03 R2407 honest disclosures: (a) the guard shipped BEFORE its "
     "criteria existed - AC-FRB1..AC-FRB6 were written at R2407 AFTER the "
     "fix, because the fix was the repair of a red measured in this same "
     "window; the suite docstring and the registry comment both say so rather "
     "than implying a pre-registration the tree does not have, and the debt "
     "row fold-block-boundary has carried the item intent since R2336. (b) "
     "The first suite run was 4/6: AC-FRB5 used a window whose kept[0] was by "
     "construction the same round's continuation, so the CLEAN case was "
     "fixtured as a split - the fixture moved to a genuine boundary, no "
     "criterion was widened. (c) The first battery leg was launched through a "
     "Select-Object pipeline that buffers, so it printed nothing until the end "
     "and was cancelled at the five-minute output gate; the process survived "
     "and its evidence landed, and the retry used a detached process with a "
     "progress file instead - the same trap R2405 recorded. (d) The commit "
     "message gate refused four drafts over 500B; the shipped message is the "
     "trimmed one. (e) A third battery leg was NOT run this window, so GREEN "
     "is not claimed for the full suite set: 532 suites / 4168 criteria is a "
     "WIRING count and reconcile-battery-R2407 is OPEN with that target."),
    ("2026-11-03 R2407 self-heal check: BigDomain-OSLoop is still registered "
     "with LogonType=InteractiveToken, which the 2026-09-29 machine law "
     "forbids for every lane task; src/os/register_loop_task.ps1 already "
     "passes an explicit S4U principal but needs an elevated shell, and this "
     "session is unelevated, so the task definition was left untouched "
     "(hundred-and-sixty-second consecutive disclosure, carried as the stale "
     "row loop-s4u-reconcile in state/debt.md)."),
]

BACKLOG_ROW = (
    "- [x] R2407 verification window: the carried battery ran FIRST on the "
    "committed tree (R2168 rule) and read RUNNER FAIL 528/531 with three "
    "ledger suites red for ONE cause: the R2405 fold cut the R2395 block "
    "after its tokens line while the round's closeout disclosure stayed live, "
    "so ledger coverage saw a round line with no ledger. SHIPPED the guard in "
    "src/os/state_fold.py - round_split(window, kept) asked in plan_fold and "
    "refused by fold() as round-split before any write, with PLAN_KEYS "
    "extended in the same change - proved on the real shape (R2395 named), on "
    "a true boundary (allowed) and on a mid-line mention (allowed). The "
    "orphan line moved verbatim to the archive and out of the live log "
    "through src/os/repair_R2407.py (dry run first, 75142 -> 73660 bytes), "
    "greening all three suites. New suite os-fold-round-block-boundary 6/6 "
    "twice, adjacent 3/3 (qa/fold-round-block-boundary-R2407.log). Retry leg "
    "read 530/532 with the two reds being this window's own closeout "
    "counters; the triage declaration was re-pinned through the shipped CLI "
    "at its predicted 70344->70447 bytes and the export is re-derived here. "
    "AC-FRB1..6 post-date the repair and say so. No third leg ran: "
    "reconcile-battery-R2407 stays OPEN at 532/4168.\n")


def write_atomic(path, text):
    temp = path + ".tmp-co2407"
    with io.open(temp, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    os.replace(temp, path)


def fix_debt():
    text = io.open(DEBT, encoding="utf-8", newline="").read()
    head, sep, tail = text.partition("## Closed")
    if not sep:
        sys.stdout.write("E_DEBT no Closed section\n")
        return 2
    rows = head.split("\n")
    out = []
    for row in rows:
        if row.startswith("- [ ] opened=R2406 | item=reconcile-battery-R2406"):
            out.append(row.replace("- [ ]", "- [x]", 1)
                       .replace("| first=yes", "| closed=R2407 | note=closed "
                                "at R2407: the battery ran twice on committed "
                                "trees (FAIL 528/531 in 1015.9s, then FAIL "
                                "530/532 in 1187.4s with the three ledger "
                                "suites green); the remaining reds were this "
                                "window's own closeout counters, repaired "
                                "before the window closed", 1))
            continue
        if row.startswith("- [ ] opened=R2336 | item=fold-block-boundary"):
            out.append(row.replace("- [ ]", "- [x]", 1)
                       .replace("| first=no", "| closed=R2407 | note=closed at "
                                "R2407 by the guard measured against the real "
                                "recurrence: the R2405 fold split R2395 "
                                "exactly as fold 624 split R2322, so "
                                "state_fold.round_split now refuses that shape "
                                "before any write (AC-FRB1..AC-FRB6)", 1))
            continue
        out.append(row)
    head = "\n".join(out)
    successor = ("- [ ] opened=R2407 | item=reconcile-battery-R2407 | "
                 "note=this window shipped os-fold-round-block-boundary (+1 "
                 "suite, +6 criteria) and changed src/os plus one registry "
                 "line, so the successor target is 532 suites / 4168 "
                 "criteria; the third leg was NOT run this window and the "
                 "retry leg's 530/532 carried two closeout-counter reds that "
                 "were repaired after it | first=yes")
    head = head.rstrip("\n") + "\n\n" + successor + "\n\n"
    write_atomic(DEBT, head + sep + tail)
    sys.stdout.write("DEBT closed two rows, opened reconcile-battery-R2407 "
                     "bytes=%d\n" % os.path.getsize(DEBT))
    return 0


def main():
    backlog = io.open(BACKLOG, encoding="utf-8", newline="").read()
    if backlog.startswith("- [x] R2407"):
        sys.stdout.write("NOTE backlog already carries the R2407 row\n")
    else:
        write_atomic(BACKLOG, BACKLOG_ROW + backlog)
        sys.stdout.write("BACKLOG row prepended\n")

    before = io.open(STATE, encoding="utf-8", newline="").read()
    state = json.loads(before)
    if LOG[0] in state.get("log", []):
        sys.stdout.write("NOTE state already carries this window's items\n")
    else:
        state["tick"] = int(state.get("tick", 0)) + 1
        for item in LOG:
            if item in state["log"]:
                sys.stdout.write("E_STATE duplicate item\n")
                return 2
            state["log"].append(item)
    tokens = list(state.get("last_dec_tokens") or [])
    for token in DECISIONS:
        if token not in tokens:
            tokens.append(token)
    state["last_dec_tokens"] = tokens
    state["last_decision_rows"] = 148
    text = state_io.canon(json.dumps(state, ensure_ascii=False, indent=2)
                          + "\n")
    raw = text.encode("utf-8")
    write_atomic(STATE, text)
    if open(STATE, "rb").read() != raw:
        sys.stdout.write("E_STATE read-back differs\n")
        return 2
    readback = json.load(io.open(STATE, encoding="utf-8"))
    sys.stdout.write("STATE tick=%d log_items=%d tokens=%d bytes=%d -> %d\n"
                     % (readback["tick"], len(readback["log"]), len(tokens),
                        len(before.encode("utf-8")), len(raw)))

    if fix_debt() != 0:
        return 2

    verdict = LLSG.append_ledger_line(STATE, LEDGER, execute=True)
    sys.stdout.write("LEDGER door verdict=%s predicted=%s wrote=%s\n"
                     % (verdict["verdict"], verdict.get("predicted_bytes"),
                        verdict.get("wrote")))
    if verdict["verdict"] != "ACCEPTED" or verdict.get("wrote") != "yes":
        return 2
    final = json.load(io.open(STATE, encoding="utf-8"))
    sys.stdout.write("STATE after ledger tick=%d log_items=%d bytes=%d\n"
                     % (final["tick"], len(final["log"]),
                        os.path.getsize(STATE)))

    data = json.load(io.open(EXPORT, encoding="utf-8"))
    QFEF.apply(data, REPO)
    derived = CEC.recompute()[0]
    for key, value in derived.items():
        if key in data.get("self_drive", {}):
            data["self_drive"][key] = value
        else:
            sys.stdout.write("NOTE derived key not in export: %s\n" % key)
    data["export_ts"] = STAMP
    data["do"] = DO
    outs = data.get("outs") or []
    if not outs or outs[0] != ART:
        data["outs"] = [ART] + outs
    rows = data.get("results") or []
    if not rows or rows[0][0] != "2407":
        data["results"] = [["2407", DO]] + rows
    face = data["ceo_face"]
    face["current"] = DO
    face["latest_artifact"] = ART
    face["last_artifact"] = ART
    face["next_milestone"] = NEXT
    face["next_milestone_due"] = "2026-11-04T23:00:00+08:00"
    face["updated_at"] = STAMP
    write_atomic(EXPORT, json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    sys.stdout.write("EXPORT refreshed bytes=%d\n" % os.path.getsize(EXPORT))

    heart = io.open(HEART, encoding="utf-8", newline="").read()
    if not heart.endswith("\n"):
        heart += "\n"
    heart += ("%s tick=%d R2407 verification - the carried battery found a fold "
              "that split a round; the guard refuses that cut before any write "
              "and the orphan line sits in the archive beside its round\n"
              % (STAMP, final["tick"]))
    write_atomic(HEART, heart)
    sys.stdout.write("HEARTBEAT appended\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())