"""state_fold_run suite (R2567; AC-SFOLD1..AC-SFOLD6 were pre-registered in
state/queue/tech.md at R2548 BEFORE this code existed - honesty law).

What this proves: the fold that state_fold.py could only report is now a
face an operator can run, and every claim it makes is measured - the archive
copy is byte-equal, the ledger coverage reader still sees every round it saw
before (because it reads the archive), the layout writer and the fold reader
agree about the same file, the gate only clears when the bytes really are at
or under the waterline, and a fold re-run on its own output writes zero bytes.

Stdlib only, ASCII source, zero network. Exit 0 = all green.
"""

import hashlib
import io
import json
import os
import shutil
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
sys.path.insert(0, BASE)

import state_fold_run as FR  # noqa: E402
import state_fold as SF  # noqa: E402

EXPECTED_CRITERIA = 9
MODULE = os.path.join(BASE, "state_fold_run.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-state-fold-run"

PASSES = 0
FAILS = 0
INDENT = " " * 16


def check(ok, label):
    global PASSES, FAILS
    if ok:
        PASSES += 1
        print("PASS %s" % label, flush=True)
    else:
        FAILS += 1
        print("FAIL %s" % label, flush=True)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def fixture_lines(count=44):
    """Paired rounds: each narrative is followed by ITS OWN ledger line.

    R3085 turned the old shape (narrative round N, ledger round N+1) into a
    refusal, and correctly so: a round whose ledger line never travels with
    its narrative is exactly the fold-carry gap AC-SFOLD8 now refuses.
    """
    lines = []
    for index in range(count):
        round_no = 1000 + index // 2
        if index % 2 == 0:
            lines.append("R%d narrative line for the fixture round" % round_no)
        else:
            lines.append("R%d tokens: local=1k api=0 api_reason=fixture reason"
                         % round_no)
    return lines


def gap_lines(separated=True, orphan_ledger=False):
    """A 115-line fixture whose R4000 ledger line may sit away from its block.

    Shape: 10 clean pairs, the R4000 narrative block, 30 clean pairs, the
    R4000 ledger line, 16 clean pairs. A cut at 60 moves the narrative block
    and keeps the ledger - the exact shape measured on the live tree this
    round (R3059 narrative 512..517, retro ledger at 666). `orphan_ledger`
    adds a ledger line for a round with no narrative anywhere, which is a
    PRE-EXISTING gap a fold may legitimately remove.
    """
    lines = []
    for index in range(10):
        round_no = 3000 + index
        lines.append("R%d narrative line for the first block" % round_no)
        lines.append("R%d tokens: local=1k api=0 api_reason=fixture reason"
                     % round_no)
    if orphan_ledger:
        lines.append("R5000 tokens: local=1k api=0 api_reason=orphaned reason")
    lines.append("R4000 narrative line for the separated round")
    lines.append("R4000 disclosure sentence about the separated round")
    if not separated:
        lines.append("R4000 tokens: local=1k api=0 api_reason=fixture reason")
    for index in range(30):
        round_no = 3100 + index
        lines.append("R%d narrative line for the middle block" % round_no)
        lines.append("R%d tokens: local=1k api=0 api_reason=fixture reason"
                     % round_no)
    if separated:
        lines.append("R4000 tokens: local=1k api=0 api_reason=fixture reason")
    for index in range(16):
        round_no = 3200 + index
        lines.append("R%d narrative line for the last block" % round_no)
        lines.append("R%d tokens: local=1k api=0 api_reason=fixture reason"
                     % round_no)
    return lines


def carry_lines():
    """A round the cut SPLITS: its first line moves, its ledger stays live.

    This is the shape fold 39 opened on the live tree (R3079): the live
    window still pairs the leftover narrative with the leftover ledger, so
    the live-gap law reads clean - only the fold-carry question sees it.
    """
    lines = []
    for index in range(10):
        round_no = 3000 + index
        lines.append("R%d narrative line for the first block" % round_no)
        lines.append("R%d tokens: local=1k api=0 api_reason=fixture reason"
                     % round_no)
    lines.append("R4000 landed: the first half of a round the cut splits")
    for index in range(30):
        round_no = 3100 + index
        lines.append("R%d narrative line for the middle block" % round_no)
        lines.append("R%d tokens: local=1k api=0 api_reason=fixture reason"
                     % round_no)
    lines.append("R4000 honest disclosures: the second half stays live")
    lines.append("R4000 tokens: local=1k api=0 api_reason=fixture reason")
    for index in range(16):
        round_no = 3200 + index
        lines.append("R%d narrative line for the last block" % round_no)
        lines.append("R%d tokens: local=1k api=0 api_reason=fixture reason"
                     % round_no)
    return lines


def cut_after_ledger(lines, minimum=55):
    """The first cut after `minimum` that splits no round.

    The last moved line must be a ledger line and the first kept line must
    open a DIFFERENT round's narrative, which is exactly the shape the
    shipped round_split predicate accepts. Derived from the fixture instead
    of hard-coded, because the three fixtures differ by one line and a
    hard-coded index would silently land on a tokens line.
    """
    for end in range(minimum, len(lines) - 30):
        last = lines[end - 1]
        head = lines[end]
        if " tokens:" not in last or " tokens:" in head:
            continue
        if last.split()[0] != head.split()[0]:
            return end
    raise AssertionError("fixture has no ledger-then-narrative cut")


def state_text(lines, indent=INDENT):
    items = (",\r\n").join(indent + json.dumps(line, ensure_ascii=False)
                           for line in lines)
    return ('{\r\n  "version": 1,\r\n  "tick": 7,\r\n  "note": "fixture",'
            '\r\n  "log": [\r\n' + items + '\r\n  ]\r\n}\r\n')


def make_world(base, lines=None, indent=INDENT):
    root = os.path.join(base, "world")
    os.makedirs(os.path.join(root, "src", "os"))
    os.makedirs(os.path.join(root, "logs"))
    path = os.path.join(root, "src", "os", "state.json")
    body = state_text(lines or fixture_lines(), indent=indent)
    with io.open(path, "wb") as handle:
        handle.write(body.encode("utf-8"))
    return root, path


def read(path):
    with io.open(path, "rb") as handle:
        return handle.read()


def main():
    base = tempfile.mkdtemp(prefix="state-fold-run-")
    try:
        # --- AC-SFOLD1: verbatim archive copy + stated live floor -----------
        root, path = make_world(base)
        before = read(path)
        before_state = json.loads(before.decode("utf-8"))
        summary = ("R1001 fold 1 of log lines 1..12 into"
                   " logs/state-log-archive-2026-11.md; tokens carried:"
                   " R1000 R1001 R1002 R1003 R1004 R1005 R1006 R1007 R1008"
                   " R1009 R1010 R1011")
        report = FR.run(root, "R9001", 1, 1, 12, summary)
        archive = report["archive_path"]
        archived_text = read(archive).decode("utf-8")
        moved = before_state["log"][0:12]
        verbatim = all(line in set(archived_text.split("\n"))
                       for line in moved)
        after_state = json.loads(read(path).decode("utf-8"))
        floor_ok = len(after_state["log"]) >= FR.MIN_LIVE_LINES
        check(report["verdict"] == "CLEAR" and verbatim and floor_ok
              and report["archive_verified"],
              "AC-SFOLD1 verbatim archive copy for all %d moved lines, "
              "live block %d >= %d, verdict CLEAR"
              % (len(moved), len(after_state["log"]), FR.MIN_LIVE_LINES))

        # --- AC-SFOLD2: coverage reader reads the archive -------------------
        logs_dir = os.path.join(root, "logs")
        post_cov = FR.ledger_coverage(logs_dir, after_state["log"])
        pre_cov = FR.ledger_coverage(
            os.path.join(base, "empty-logs"), before_state["log"])
        check(post_cov["ledger_lines"] == pre_cov["ledger_lines"]
              and post_cov["ledger_rounds"] == pre_cov["ledger_rounds"]
              and "R1001" in post_cov["ledger_rounds"],
              "AC-SFOLD2 ledger coverage unchanged through the archive: "
              "ledger_lines %d -> %d, rounds %d -> %d (R1001 still found)"
              % (pre_cov["ledger_lines"], post_cov["ledger_lines"],
                 len(pre_cov["ledger_rounds"]),
                 len(post_cov["ledger_rounds"])))

        # --- AC-SFOLD3: round-trip + a re-run writes zero bytes -------------
        fields_ok = set(after_state.keys()) == set(before_state.keys())
        post_bytes = read(path)
        again = FR.run(root, "R9001", 1, 1, 12, summary)
        check(fields_ok and again["verdict"] == "ALREADY-FOLDED"
              and read(path) == post_bytes
              and again["bytes_after"] == again["bytes_before"],
              "AC-SFOLD3 round-trip: field set preserved, re-run reads "
              "ALREADY-FOLDED with zero bytes written")

        # --- AC-SFOLD4: writer and fold reader agree on one file ------------
        # R2522 measured the defect this closes: state_fold insisted on a
        # 16-space item indent while the shipped append path wrote 2-space
        # items, so the reader refused the real file. The reader now derives
        # the indent from the file, so a file in ANY consistent layout folds
        # in its OWN layout (no reformat) and only items that disagree with
        # each other are refused.
        agree = report["layout_agree"] is True
        other_root, other_path = make_world(os.path.join(base, "other"),
                                            indent="  ")
        other_before = read(other_path)
        other = FR.run(other_root, "R9002", 1, 1, 4,
                       "R9002 fold 1 of log lines 1..4 into"
                       " logs/state-log-archive-2026-11.md")
        other_after = read(other_path)
        kept_prefix = other_after.startswith(other_before.split(b"\n")[0])
        header_same = (other_after.split(b'"log"')[0]
                       == other_before.split(b'"log"')[0])
        bad_root, bad_path = make_world(os.path.join(base, "bad"),
                                        indent="  ")
        bad_text = read(bad_path).replace(b'"log": [\r\n  "',
                                          b'"log": [\r\n      "', 1)
        with io.open(bad_path, "wb") as handle:
            handle.write(bad_text)
        bad_before = read(bad_path)
        refused = False
        try:
            FR.run(bad_root, "R9003", 1, 1, 4,
                   "R9003 fold 1 of log lines 1..4 into"
                   " logs/state-log-archive-2026-11.md")
        except SF.StateFoldError as exc:
            refused = exc.code in ("E_SF_BAD_LAYOUT", "E_SF_BAD_STATE")
        check(agree and other["verdict"] == "CLEAR" and other["layout_agree"]
              and header_same and kept_prefix and refused
              and read(bad_path) == bad_before,
              "AC-SFOLD4 the reader derives the file own indent: a 2-space "
              "real-style file folds in its own layout (header bytes and "
              "prefix intact), and items disagreeing with each other refused "
              "with the shipped code and no byte written [agree=%s other=%s "
              "layout=%s header=%s prefix=%s refused=%s untouched=%s]"
              % (agree, other["verdict"], other["layout_agree"], header_same,
                 kept_prefix, refused, read(bad_path) == bad_before))

        # --- AC-SFOLD5: the gate is honest ---------------------------------
        gate_root, _ = make_world(os.path.join(base, "gate"))
        over = False
        try:
            FR.run(gate_root, "R9003", 1, 1, 4,
                   "R9003 fold 1 of log lines 1..4 into"
                   " logs/state-log-archive-2026-11.md", gate=100)
        except FR.FoldRunError as exc:
            over = exc.code == "E_SFOLD_GATE"
        honest = (report["verdict"] == "CLEAR"
                  and report["bytes_after"] <= report["gate"]
                  and report["margin_after"] >= 0)
        check(over and honest,
              "AC-SFOLD5 gate honest: a fold that would leave %d bytes over "
              "100 refused E_SFOLD_GATE, the real fold cleared at %d <= %d"
              % (report["bytes_after"], report["bytes_after"],
                 report["gate"]))

        # --- AC-SFOLD6: dry run writes nothing; ASCII; registry wired ------
        dry_root, dry_path = make_world(os.path.join(base, "dry"))
        dry_before = read(dry_path)
        dry = FR.run(dry_root, "R9004", 1, 1, 4,
                     "R9004 fold 1 of log lines 1..4 into"
                     " logs/state-log-archive-2026-11.md",
                     dry_run=True)
        source = read(MODULE)
        ascii_ok = all(byte < 128 for byte in source)
        no_clock = b"import datetime" not in source and b"time.time" not in source
        with io.open(RUNNER, "rb") as handle:
            runner = handle.read()
        wired = (LABEL.encode("ascii") in runner
                 and EXPECTED_CRITERIA == 9)
        check(read(dry_path) == dry_before
              and dry["dry_run_digest_same"] is True
              and dry["verdict"] == "DRY-RUN" and ascii_ok and no_clock
              and wired,
              "AC-SFOLD6 dry run wrote zero bytes (digest %s), source ASCII "
              "and clockless, wired as %s(6)"
              % (digest(read(dry_path))[:16], LABEL))
        # --- AC-SFOLD7: a fold may not CREATE a live gap -------------------
        # R3085 measured the live shape this closes: R3059's narrative sat at
        # 512..517 while its retro-written ledger line sat at 666, so a cut
        # past 518 read as 'no round lost' by the set comparison above and
        # would have landed a live orphan. The law is a SUBSET law.
        split_root, split_path = make_world(os.path.join(base, "split"),
                                            gap_lines(separated=True))
        split_before = read(split_path)
        split_end = cut_after_ledger(gap_lines(separated=True))
        split_report = FR.run(split_root, "R9005", 1, 1, split_end,
                              "R9006 fold 1 of log lines 1..4 into"
                          " logs/state-log-archive-2026-11.md")
        arm_a = (split_report["verdict"] == "REFUSED"
                 and "live-dirty" in split_report["would_fail"]
                 and read(split_path) == split_before
                 and not os.path.exists(os.path.join(
                     split_root, "logs",
                     os.path.basename(split_report["archive_path"]))))

        pair_root, pair_path = make_world(os.path.join(base, "pair"),
                                          gap_lines(separated=False))
        pair_report = FR.run(pair_root, "R9006", 1, 1,
                             cut_after_ledger(gap_lines(separated=False)),
                             "R9007 fold 1 of log lines 1..4 into"
                          " logs/state-log-archive-2026-11.md")
        pair_state = json.loads(read(pair_path).decode("utf-8"))
        pair_gaps = FR.live_gaps(pair_root, pair_state["log"])
        pair_archive = read(pair_report["archive_path"]).decode("utf-8")
        arm_b = (pair_report["verdict"] == "CLEAR"
                 and not pair_gaps["missing"] and not pair_gaps["orphan"]
                 and "R4000 narrative line for the separated round"
                 in pair_archive and "R4000 tokens:" in pair_archive)

        subset_root, subset_path = make_world(
            os.path.join(base, "subset"),
            gap_lines(separated=False, orphan_ledger=True))
        before_gaps = FR.live_gaps(
            subset_root, json.loads(read(subset_path).decode("utf-8"))["log"])
        subset_report = FR.run(
            subset_root, "R9007", 1, 1,
            cut_after_ledger(gap_lines(separated=False, orphan_ledger=True)),
            "R9008 fold 1 of log lines 1..4 into"
                          " logs/state-log-archive-2026-11.md")
        subset_state = json.loads(read(subset_path).decode("utf-8"))
        after_gaps = FR.live_gaps(subset_root, subset_state["log"])
        arm_c = (before_gaps["orphan"] == {5000}
                 and subset_report["verdict"] == "CLEAR"
                 and not after_gaps["orphan"])
        carry_root, carry_path = make_world(os.path.join(base, "carry"),
                                           carry_lines())
        carry_before = read(carry_path)
        carry_report = FR.run(carry_root, "R9008", 1, 1,
                              cut_after_ledger(carry_lines()),
                              "R9010 fold 1 of log lines 1..4 into"
                              " logs/state-log-archive-2026-11.md")
        arm_d = (carry_report["verdict"] == "REFUSED"
                 and "carry-gap" in carry_report["would_fail"]
                 and "live-dirty" not in carry_report["would_fail"]
                 and read(carry_path) == carry_before)
        choice_root, choice_path = make_world(os.path.join(base, "choice"),
                                              gap_lines(separated=True))
        choice_raw = read(choice_path)
        choice_state = json.loads(choice_raw.decode("utf-8"))
        end, summary, plan = FR.choose_window(
            choice_root, choice_raw, choice_state, set(), label="R9009",
            archive_name="state-log-archive-2026-11.md")
        arm_e = False
        if end is not None:
            reuse, _ = SF.plan_fold(choice_raw, choice_state, 1, end, summary,
                                    gate=SF.GATE, covered=set())
            live_after = FR.live_gaps(choice_root, choice_state["log"][end:])
            live_before = FR.live_gaps(choice_root, choice_state["log"])
            arm_e = (reuse["token_ok"] and reuse["round_split"] is None
                     and reuse["folded_log_len"] >= FR.MIN_LIVE_LINES
                     and reuse["predicted_bytes"] <= SF.GATE
                     and live_after["missing"] <= live_before["missing"]
                     and live_after["orphan"] <= live_before["orphan"]
                     and not FR.prospective_carry_gaps(
                         choice_root, choice_state["log"][:end]))
        check(arm_a and arm_b and arm_c and arm_d and arm_e,
              "AC-SFOLD7 a fold may not CREATE a live gap: a cut that would "
              "orphan the separated ledger line is REFUSED live-dirty with "
              "zero bytes written [a=%s fails=%s untouched=%s]; the same cut "
              "with the ledger inside its block is CLEAR and both R4000 lines "
              "reach the archive [b=%s gaps=%s]; a PRE-EXISTING orphan inside "
              "the moved window is removed rather than refused, so the law is "
              "a SUBSET law [c=%s before=%s after=%s]; a round the cut SPLITS "
              "reads clean on the live face while the fold-carry face names "
              "it, so the carry guard refuses it on its own [d=%s fails=%s]; "
              "and the shipped chooser, asked of the log that contains that "
              "split, steps off it and returns a window every law accepts "
              "with its missing tokens named [e=%s end=%s]"
              % (arm_a, split_report["would_fail"],
                 read(split_path) == split_before, arm_b, pair_gaps, arm_c,
                 sorted(before_gaps["orphan"]), sorted(after_gaps["orphan"]),
                 arm_d, carry_report["would_fail"], arm_e, end))

        # --- AC-SUM2: a summary the reader cannot recognise never lands -----
        # R3183 measured the live red gate this closes: fold 608 wrote a prose
        # summary that named no archive file, so the sequence reader counted
        # it as a round (BACKWARDS + REPEAT, fold_summaries=0). The reader is
        # not loosened; the birth point refuses instead.
        prose_root, prose_path = make_world(os.path.join(base, "prose"))
        prose_before = read(prose_path)
        prose_codes = []
        for dry in (True, False):
            try:
                FR.run(prose_root, "R9005", 1, 1, 4,
                       "R9005 fold 1: prose without the archive name",
                       dry_run=dry)
            except FR.FoldRunError as exc:
                prose_codes.append(exc.code)
        shipped_ok = FR.SQ.is_fold_summary(
            "R9005 fold 1 of log lines 1..4 into"
            " logs/state-log-archive-2026-11.md")
        after_prose = read(prose_path)
        check(prose_codes == ["E_FLR_SUMMARY_SHAPE", "E_FLR_SUMMARY_SHAPE"]
              and after_prose == prose_before and shipped_ok,
              "AC-SUM2 a summary the reader refuses is refused at the birth "
              "point in dry-run AND execute (%s), zero bytes written "
              "[untouched=%s], while the shipped shape is still accepted "
              "[%s]" % (prose_codes, after_prose == prose_before, shipped_ok))
        # --- AC-SUM6: a summary must name the archive it lands in -----------
        # R3184 measured the hole: check_summary_shape accepted a summary that
        # named the default month file while --archive pointed elsewhere, and
        # the reader accepts it too (it only checks the prefix), so a fold
        # record could misname its own destination. The writer refuses now.
        wrong_root, wrong_path = make_world(os.path.join(base, "wrongarc"))
        wrong_before = read(wrong_path)
        wrong_archive = os.path.join(wrong_root, "logs",
                                     "state-log-archive-2026-10.md")
        mismatched = ("R9010 fold 1 of log lines 1..4 into"
                      " logs/state-log-archive-2026-11.md")
        wrong_codes = []
        for dry in (True, False):
            try:
                FR.run(wrong_root, "R9010", 1, 1, 4, mismatched,
                       archive_path=wrong_archive, dry_run=dry)
            except FR.FoldRunError as exc:
                wrong_codes.append(exc.code)
        reader_accepts = FR.SQ.is_fold_summary(mismatched)
        matches_root, matches_path = make_world(os.path.join(base, "matcharc"))
        matches_archive = os.path.join(matches_root, "logs",
                                       "state-log-archive-2026-10.md")
        named_custom = ("R9011 fold 1 of log lines 1..4 into"
                        " logs/state-log-archive-2026-10.md")
        custom_report = FR.run(matches_root, "R9011", 1, 1, 4, named_custom,
                               archive_path=matches_archive)
        custom_state = json.loads(read(matches_path).decode("utf-8"))
        default_root, default_path = make_world(os.path.join(base, "defarc"))
        default_report = FR.run(default_root, "R9012", 1, 1, 4,
                                "R9012 fold 1 of log lines 1..4 into logs/%s"
                                % os.path.basename(SF.default_archive(
                                    default_root)))
        double_names = FR.summary_archive_names(named_custom)
        two_names = FR.summary_archive_names(
            named_custom + " and logs/state-log-archive-2026-11.md")
        same_name_twice = False
        try:
            FR.check_summary_shape(named_custom + " and " + named_custom,
                                   matches_archive)
            same_name_twice = True
        except FR.FoldRunError:
            same_name_twice = False
        module_src = io.open(MODULE, "rb").read().decode("utf-8")
        hygiene = (all(ord(char) < 128 for char in module_src)
                   and "import socket" not in module_src
                   and "import urllib" not in module_src
                   and "import http" not in module_src)
        check(wrong_codes == ["E_FLR_SUMMARY_ARCHIVE",
                              "E_FLR_SUMMARY_ARCHIVE"]
              and read(wrong_path) == wrong_before
              and not os.path.exists(wrong_archive)
              and reader_accepts
              and custom_report["verdict"] == "CLEAR"
              and custom_report["archive_verified"]
              and named_custom in custom_state["log"]
              and default_report["verdict"] == "CLEAR"
              and double_names == ["state-log-archive-2026-10.md"]
              and len(two_names) == 2 and same_name_twice and hygiene,
              "AC-SUM6 a summary naming one archive while the fold writes "
              "another is refused at the birth point in dry-run AND execute "
              "[%s] with zero bytes written [untouched=%s archive_absent=%s] "
              "while the reader still accepts that same text [%s] - so the "
              "gate is the writer, not a loosened reader; a summary naming "
              "the custom archive it does write folds and VERIFIES [%s %s "
              "landed=%s]; the default path is not hurt [%s]; and every "
              "archive name the summary points at is compared, so two "
              "different names are seen [%d] while the same name twice "
              "passes [%s]; module hygiene [%s]"
              % (wrong_codes, read(wrong_path) == wrong_before,
                 not os.path.exists(wrong_archive), reader_accepts,
                 custom_report["verdict"],
                 custom_report["archive_verified"],
                 named_custom in custom_state["log"],
                 default_report["verdict"], len(two_names),
                 same_name_twice, hygiene))
    finally:
        shutil.rmtree(base, ignore_errors=True)


    print("CRITERIA %d/%d passes=%d fails=%d"
          % (EXPECTED_CRITERIA, EXPECTED_CRITERIA, PASSES, FAILS))
    _law_verdict = "SUITE PASS" if FAILS == 0 else "SUITE FAIL"
    print("%s %d/%d" % (_law_verdict, PASSES, EXPECTED_CRITERIA))
    return 0 if FAILS == 0 and PASSES == EXPECTED_CRITERIA else 1


if __name__ == "__main__":
    sys.exit(main())