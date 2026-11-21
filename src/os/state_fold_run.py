# state_fold_run.py - the fold FACE that state_fold.py never shipped
# Criteria AC-SFOLD1..AC-SFOLD6 were pre-registered in state/queue/tech.md
# (R2548 seed) BEFORE this file existed - honesty law.
#
# Why this exists: state_fold.py owns the predicate (plan_fold), the verbatim
# archive append and the waterline read, but its CLI only ever answered
# --check, so the gate could report FOLD-DUE forever and no shipped face could
# discharge it. Windows kept folding by hand, each hand fold a fresh chance to
# cut a round in half or to leave the file over the waterline and call it done.
# This module is the one callable an operator runs: it asks the shipped
# predicate, refuses anything that is not clean, proves the archive copy is
# byte-equal, proves the ledger coverage reader still sees every round it saw
# before, proves the layout writer and the layout reader agree, and only then
# writes.
#
# Read paths write nothing and read no clock. Stdlib only, ASCII source,
# zero network.

import hashlib
import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

import state_fold as SF  # noqa: E402
import general_writer_dialect_audit as GWDA  # noqa: E402
import ledger_lines as LL  # noqa: E402
import state_seq as SQ  # noqa: E402

MIN_LIVE_LINES = 30
LABEL = "os-state-fold-run"

REPORT_KEYS = ("round", "fold_no", "mode", "verdict", "window_start",
               "window_end", "window_lines", "live_lines_before",
               "live_lines_after", "bytes_before", "bytes_after",
               "gate", "margin_after", "token_ok", "tokens_total",
               "tokens_missing", "archive_path", "archive_appendix_bytes",
               "archive_verified", "layout_agree", "field_set_same",
               "ledger_rounds_before", "ledger_rounds_after",
               "would_fail", "dry_run_digest_same")


class FoldRunError(Exception):
    def __init__(self, code, detail=""):
        Exception.__init__(self, code)
        self.code = code
        self.detail = detail


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def ledger_coverage(logs_dir, live_lines):
    """Ledger rounds and ledger line count over live + archive (AC-SFOLD2).

    The archive is READ here rather than ignored: that is the only way the
    count can survive a fold.
    """
    try:
        archived = LL.load_archive_lines(logs_dir)
    except Exception:
        archived = []
    lines = list(archived) + list(live_lines)
    rounds = set()
    ledgers = 0
    for line in lines:
        head = SF.ROUND_HEAD_RE.match(line)
        if head:
            rounds.add("R" + head.group(1))
        if SF.TOKENS_RE.match(line):
            ledgers += 1
    return {"ledger_rounds": rounds, "ledger_lines": ledgers}


def archive_copy_ok(path, window_lines):
    """Every moved line appears VERBATIM as a line of the archive."""
    try:
        with io.open(path, "rb") as handle:
            text = handle.read().decode("utf-8")
    except (IOError, OSError, UnicodeDecodeError):
        return False
    present = set(text.split("\n"))
    return all(line in present for line in window_lines)


def read_archive_text(path):
    try:
        with io.open(path, "rb") as handle:
            return handle.read().decode("utf-8", "replace")
    except (IOError, OSError):
        return ""


def live_gaps(root, lines):
    """The actionable LIVE gap sets, baseline applied (AC-SFOLD7, R3085).

    The baseline is read from THIS root, so the live tree is judged with the
    shipped exemption list and a private world is judged with its own (or an
    empty one) - the law is identical, the exemptions are not borrowed.
    """
    path = os.path.join(root, "state", LL.BASELINE_NAME)
    report = LL.apply_baseline(LL.audit(list(lines)), LL.load_baseline(path))
    return {"missing": set(report["new_missing"]),
            "orphan": set(report["new_orphan"])}


def prospective_carry_gaps(root, window_lines):
    """Rounds whose narrative moves without their ledger (AC-SFOLD8, R3085).

    The FOLD-CARRY law (R2914) is only asked AFTER the archive grew, so it
    could report a gap the fold itself opened - measured this round: fold 39
    cut R3079 in two (its early lines archived, its disclosures and ledger
    line left live) and the law reddened the very window the fold had just
    written. This asks the same question BEFORE any byte is written: every
    round whose narrative moves must have its ledger line either in the
    moved window or already standing in an archive window.
    """
    held = set()
    logs_dir = os.path.join(root, "logs")
    if os.path.isdir(logs_dir):
        try:
            for path in LL.archive_files(logs_dir):
                for window in LL.load_archive_windows(path):
                    for line in window["lines"]:
                        match = LL.LEDGER_PRESENCE_RE.match(line)
                        if match is not None:
                            held.add(int(match.group(1)))
        except Exception:
            held = set()
    for line in window_lines:
        match = LL.LEDGER_PRESENCE_RE.match(line)
        if match is not None:
            held.add(int(match.group(1)))
    gaps = set()
    for line in window_lines:
        if LL.classify(line) != "round":
            continue
        round_no = int(LL.NARRATIVE_RE.match(line).group(1))
        if round_no not in held:
            gaps.add(round_no)
    return sorted(gaps)


def base_summary(label, end, start=1, tag="", archive_name=None):
    """The summary a fold leaves behind, in the shape FOLD_SUMMARY_RE reads."""
    name = archive_name or os.path.basename(SF.default_archive(
        os.path.dirname(os.path.dirname(BASE))))
    return ("%s fold%s of log lines %d..%d into logs/%s"
            % (label, tag, start, end, name))


def choose_window(root, raw, state, covered, start=1, tag="", label=None,
                  archive_name=None, gate=SF.GATE):
    """The widest window every law of this face accepts, plus its summary.

    R3085 measured why an operator needs this as a callable rather than a
    fresh one-off script per round: the choice is a conjunction of five
    refusals (gate, live floor, round split, live gap, carry gap) and one
    requirement (every moved token named or already archived), and each hand
    re-derivation is a fresh chance to miss one - the R3085 hand fold missed
    the carry question and split a round in half. Returns
    (end, summary, plan) or (None, None, None).
    """
    label = label or "fold"
    log = state["log"]
    count = len(log)
    before = live_gaps(root, log)
    for end in range(count + start - MIN_LIVE_LINES, start - 1, -1):
        summary = base_summary(label, end, start, tag, archive_name)
        plan, _ = SF.plan_fold(raw, state, start, end, summary, gate=gate,
                               covered=covered)
        if plan["predicted_bytes"] > gate:
            continue
        if plan["folded_log_len"] < MIN_LIVE_LINES:
            continue
        if plan["round_split"]:
            continue
        after = live_gaps(root, log[end:])
        if not (after["missing"] <= before["missing"]
                and after["orphan"] <= before["orphan"]):
            continue
        if prospective_carry_gaps(root, log[start - 1:end]):
            continue
        if plan["tokens_missing"]:
            summary = (base_summary(label, end, start, tag, archive_name)
                       + "; tokens carried: "
                       + " ".join(plan["tokens_missing"]))
            plan, _ = SF.plan_fold(raw, state, start, end, summary,
                                   gate=gate, covered=covered)
        if not plan["token_ok"]:
            continue
        return end, summary, plan
    return None, None, None


def already_folded(state, window_start, window_end, summary):
    """The fold already happened: its summary line is live.

    The summary is the fold's own artifact and is unique per fold, so its
    presence is the one honest signal that a re-run has nothing left to do -
    window indices point at the pre-fold layout and must not be trusted.
    """
    return summary in state["log"]


def summary_archive_names(summary):
    """Every archive file name a fold summary points at, in text order."""
    names = []
    marker = SQ.ARCHIVE_PREFIX
    index = summary.find(marker)
    while index != -1:
        end = index + len(marker)
        while end < len(summary) and (summary[end].isalnum()
                                      or summary[end] in "-._"):
            end += 1
        names.append(summary[index:end])
        index = summary.find(marker, end)
    return names


def check_archive_path(archive_path, root):
    """Refuse an archive that is not a direct child of <root>/logs (AC-SUM7).

    R3185 measured the hole the AC-SUM6 name law leaves open: base_summary
    always writes "logs/<name>", while --archive can point anywhere, so a fold
    record could name a path that does not exist and is not the file that
    really grew (measured in a private tree: outside/ created, logs/ left
    untouched, state bytes already rewritten). The reader only looks for the
    archive prefix, so the honest birth point is here - every accepted fold
    lands where its own sentence says it does.
    """
    logs_dir = os.path.join(root, "logs")
    target = os.path.normcase(os.path.realpath(archive_path))
    home = os.path.normcase(os.path.realpath(logs_dir))
    if os.path.dirname(target) != home:
        raise FoldRunError(
            "E_FLR_ARCHIVE_PATH",
            "archive %s is not inside %s" % (archive_path, logs_dir))


def check_archive_name(archive_path):
    """Refuse an archive the ledger coverage reader never enumerates (AC-SUM8).

    R3186 measured the hole AC-SUM7 leaves open: a fold into logs/<name>.txt
    (or .MD) passed every pre-gate, wrote backup + archive + state, and only
    then failed E_SFOLD_LEDGER_LOSS 40 -> 21 - because `LL.load_archive_lines`
    enumerates ARCHIVE_PREFIX*ARCHIVE_SUFFIX only, so the very file the fold
    just wrote was invisible to the proof. The name is statically checkable
    before any byte, so it is refused here instead of proved after the write.
    """
    name = os.path.basename(archive_path)
    if not (name.startswith(LL.ARCHIVE_PREFIX)
            and name.endswith(LL.ARCHIVE_SUFFIX)):
        raise FoldRunError(
            "E_FLR_ARCHIVE_NAME",
            "%s (the coverage reader enumerates %s*%s only)"
            % (name, LL.ARCHIVE_PREFIX, LL.ARCHIVE_SUFFIX))


def check_archive_set(root):
    """Refuse to fold while any archive the proof must read is unreadable.

    R3186 measured the second legal-entry route: one sibling archive that
    `load_archive` cannot decode makes `ledger_coverage` swallow the exception
    and read zero archived lines, so the post-write set comparison collapses
    (40 -> 21) after the fold landed. A proof whose reader is blind is not a
    proof, so the read is done here, before the plan.
    """
    logs_dir = os.path.join(root, "logs")
    try:
        paths = LL.archive_files(logs_dir)
    except LL.LedgerLineError as exc:
        raise FoldRunError("E_FLR_ARCHIVE_UNREADABLE", exc.detail)
    for path in paths:
        try:
            LL.load_archive(path)
        except LL.LedgerLineError as exc:
            raise FoldRunError("E_FLR_ARCHIVE_UNREADABLE", exc.detail)


def check_summary_shape(summary, archive_path=None):
    """Refuse a summary the reader cannot recognise, or one that misnames
    the archive it is about to be written into (AC-SUM2 + AC-SUM6).

    R3183 measured the live red gate: a hand-written summary that named no
    archive file was not a fold summary to `state_seq`, so it re-entered the
    live sequence as a round of its own - BACKWARDS and REPEAT appeared and
    `fold_summaries` read 0. Loosening the reader would let any narrative
    starting with "R<n> fold" leave the sequence silently, so the birth point
    is here instead: a summary this reader refuses is never written.

    R3184 measured the same birth point accepting a summary that names one
    archive while the fold lands in another (the reader only checks the
    prefix, and run() never compared the two). A fold record that misnames
    its own destination is unreadable history, so the write is refused here.
    """
    if not SQ.is_fold_summary(summary or ""):
        raise FoldRunError(
            "E_FLR_SUMMARY_SHAPE",
            "summary is not a fold summary the reader recognises"
            " (needs '^R<n> fold' plus %r)" % SQ.ARCHIVE_PREFIX)
    if archive_path is None:
        return
    written = os.path.basename(archive_path)
    named = summary_archive_names(summary)
    wrong = [name for name in named if name != written]
    if wrong:
        raise FoldRunError(
            "E_FLR_SUMMARY_ARCHIVE",
            "summary names %s but the fold writes %s"
            % (",".join(wrong), written))


def run(root, round_label, fold_no, window_start, window_end, summary,
        archive_path=None, dry_run=False, gate=SF.GATE, refold_reason=None):
    """Plan, refuse on any dirty predicate, execute, then prove the result."""
    archive = archive_path or SF.default_archive(root)
    check_archive_path(archive, root)
    check_archive_name(archive)
    check_archive_set(root)
    check_summary_shape(summary, archive)
    path = SF.state_path(root)
    raw, state = SF.read_state(path)
    pre_digest = digest(raw)
    live_before = len(state["log"])
    bytes_before = len(raw)
    logs_dir = os.path.join(root, "logs")

    if already_folded(state, int(window_start), int(window_end), summary):
        # AC-SFOLD3: re-running the fold on its own output writes ZERO bytes.
        after_digest = digest(open(path, "rb").read())
        return {
            "round": round_label, "fold_no": fold_no, "mode": "already",
            "verdict": "ALREADY-FOLDED",
            "window_start": int(window_start), "window_end": int(window_end),
            "window_lines": int(window_end) - int(window_start) + 1,
            "live_lines_before": live_before, "live_lines_after": live_before,
            "bytes_before": bytes_before, "bytes_after": bytes_before,
            "gate": int(gate), "margin_after": int(gate) - bytes_before,
            "token_ok": True, "tokens_total": 0, "tokens_missing": [],
            "archive_path": archive,
            "archive_appendix_bytes": 0, "archive_verified": True,
            "layout_agree": True, "field_set_same": True,
            "ledger_rounds_before": len(ledger_coverage(
                logs_dir, state["log"])["ledger_rounds"]),
            "ledger_rounds_after": len(ledger_coverage(
                logs_dir, state["log"])["ledger_rounds"]),
            "would_fail": [], "dry_run_digest_same": after_digest == pre_digest,
        }

    plan, folded_text = SF.plan_fold(raw, state, window_start, window_end,
                                     summary, gate=gate,
                                     covered=SF.archive_tokens(archive))
    # AC-SFOLD4: the layout the append path lands and the layout this fold
    # reader expects must agree about the SAME file.
    payload = GWDA.payload_for(path, folded_text)
    layout = SF.split_layout(folded_text, plan["folded_log_len"])
    layout_agree = (layout is not None
                    and payload.decode("utf-8") == folded_text)
    # AC-SFOLD1: a stated minimum live block survives the cut.
    floor_ok = plan["folded_log_len"] >= MIN_LIVE_LINES
    fails = []
    if plan["tokens_missing"]:
        fails.append("token-missing")
    if plan["round_split"]:
        fails.append("round-split")
    if not floor_ok:
        fails.append("live-floor")
    if not layout_agree:
        fails.append("layout-disagree")
    # AC-SFOLD7 (R3085): a fold may not CREATE a live gap. The post-check
    # below compares round SETS (E_SFOLD_LEDGER_LOSS), so a narrative moved
    # into the archive while its ledger line stays behind reads as 'no round
    # lost' and lands as a live orphan - measured on the shipped tree this
    # round: R3059's narrative sat at 512..517 and its retro-written ledger
    # line at 666, so every cut past 518 orphaned it. The law is a SUBSET
    # law, not 'any gap refuses': a pre-existing gap that the fold REMOVES
    # (an orphan ledger inside the moved window) must stay foldable.
    live_before_gaps = live_gaps(root, state["log"])
    live_after_gaps = live_gaps(root, state["log"][int(window_end):])
    if not (live_after_gaps["missing"] <= live_before_gaps["missing"]
            and live_after_gaps["orphan"] <= live_before_gaps["orphan"]):
        fails.append("live-dirty")
    # AC-SFOLD8 (R3085): a fold may not open a FOLD-CARRY gap - a narrative
    # whose ledger line stays behind reads as a lost pairing to every later
    # reader, and the law that detects it runs only after the archive grew.
    carry_gaps = prospective_carry_gaps(
        root, state["log"][plan["window_start"] - 1:plan["window_end"]])
    if carry_gaps:
        fails.append("carry-gap")
    if plan["predicted_bytes"] > gate:
        # AC-SFOLD5: a fold that would leave the file over the waterline is
        # refused instead of claiming success - its own code, not the
        # predicate's general one.
        raise FoldRunError("E_SFOLD_GATE",
                           "%d bytes over %d"
                           % (plan["predicted_bytes"], gate))

    before_cov = ledger_coverage(logs_dir, state["log"])
    report = {
        "round": round_label, "fold_no": fold_no,
        "mode": "dry-run" if dry_run else "execute",
        "verdict": "REFUSED" if fails else ("DRY-RUN" if dry_run
                                            else "FOLDED"),
        "window_start": plan["window_start"], "window_end": plan["window_end"],
        "window_lines": plan["window_lines"],
        "live_lines_before": live_before,
        "live_lines_after": plan["folded_log_len"],
        "bytes_before": bytes_before,
        "bytes_after": plan["predicted_bytes"],
        "gate": int(gate), "margin_after": int(gate) - plan["predicted_bytes"],
        "token_ok": plan["token_ok"], "tokens_total": plan["tokens_total"],
        "tokens_missing": plan["tokens_missing"],
        "archive_path": archive, "archive_appendix_bytes": 0,
        "archive_verified": False, "layout_agree": layout_agree,
        "field_set_same": True,
        "ledger_rounds_before": len(before_cov["ledger_rounds"]),
        "ledger_rounds_after": len(before_cov["ledger_rounds"]),
        "would_fail": fails, "dry_run_digest_same": True,
    }
    if fails:
        return report

    if dry_run:
        # AC-SFOLD6: a dry run writes NOTHING, proved by a whole-file digest.
        with io.open(path, "rb") as handle:
            report["dry_run_digest_same"] = digest(handle.read()) == pre_digest
        return report

    result = SF.fold(root, round_label, fold_no, window_start, window_end,
                     summary, gate=gate, execute=True, archive_path=archive,
                     refold_reason=refold_reason)
    if result.get("would_fail"):
        raise FoldRunError("E_SFOLD_PREDICATE",
                           ",".join(result["would_fail"]))

    with io.open(path, "rb") as handle:
        post_raw = handle.read()
    post_state = json.loads(post_raw.decode("utf-8"))
    moved = state["log"][plan["window_start"] - 1:plan["window_end"]]

    report.update({
        "bytes_after": len(post_raw),
        "margin_after": int(gate) - len(post_raw),
        "archive_appendix_bytes": result["archive"]["appendix_bytes"],
        "archive_verified": archive_copy_ok(archive, moved),
        "field_set_same": (set(post_state.keys()) == set(state.keys())),
        "live_lines_after": len(post_state["log"]),
        "dry_run_digest_same": True,
        "layout_agree": bool(result.get("predicted_eq_actual")
                             and layout_agree),
    })
    after_cov = ledger_coverage(logs_dir, post_state["log"])
    report["ledger_rounds_after"] = len(after_cov["ledger_rounds"])
    # AC-SFOLD2: no round that had a ledger line may lose it to the fold.
    # R3186: these three proofs run AFTER the write, so their codes say so -
    # the caller must not read "refused, nothing written" from a fold that
    # already moved bytes.
    if not before_cov["ledger_rounds"] <= after_cov["ledger_rounds"]:
        raise FoldRunError("E_SFOLD_LEDGER_LOSS",
                           "after write: %d -> %d (state, archive and backup"
                           " already changed)"
                           % (len(before_cov["ledger_rounds"]),
                              len(after_cov["ledger_rounds"])))
    if not report["archive_verified"]:
        raise FoldRunError("E_SFOLD_ARCHIVE_COPY",
                           "after write: %s" % archive)
    if not report["layout_agree"]:
        raise FoldRunError("E_SFOLD_LAYOUT_DISAGREE",
                           "after write: %s" % path)
    # AC-SFOLD5: the gate is honest - success only at or under the waterline.
    post = SF.check(root, gate=gate)
    report["verdict"] = post["verdict"].replace("FOLD-", "")
    if post["fold_needed"]:
        raise FoldRunError("E_SFOLD_GATE",
                           "%d bytes over %d" % (post["bytes"], gate))
    return report


USAGE = (
    "usage: state_fold_run.py --fold --round R<n> --fold-no <n> "
    "--start <a> --end <b> --summary <line>\n"
    "                                   [--dry-run] [--root PATH] "
    "[--archive PATH] [--json]\n"
    "                                   [--refold-reason TEXT]  (required to "
    "open a second window for one round marker)\n"
    "       state_fold_run.py --check [--root PATH] [--json]\n"
    "  exit 0 = folded / ALREADY-FOLDED / FOLD-CLEAR\n"
    "  exit 2 = refused by the predicate (nothing written), or a proof that\n"
    "           ran after the write (message starts 'after write:')\n"
    "  exit 3 = state file missing or unreadable\n"
    "  exit 5 = bad flags\n")


def render(report):
    return ("STATE FOLD RUN round=%s fold=%s mode=%s verdict=%s "
            "window=%d..%d lines=%d live %d->%d bytes %d->%d margin=%d "
            "tokens=%d ok=%s archive=%s layout=%s"
            % (report["round"], report["fold_no"], report["mode"],
               report["verdict"], report["window_start"], report["window_end"],
               report["window_lines"], report["live_lines_before"],
               report["live_lines_after"], report["bytes_before"],
               report["bytes_after"], report["margin_after"],
               report["tokens_total"], report["token_ok"],
               "VERIFIED" if report["archive_verified"] else "UNVERIFIED",
               "AGREE" if report["layout_agree"] else "DISAGREE"))


def main(argv):
    root = os.path.dirname(os.path.dirname(BASE))
    round_label = None
    fold_no = None
    start = None
    end = None
    summary = None
    archive = None
    refold_reason = None
    as_json = False
    dry_run = False
    fold_mode = False
    check_mode = False
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--fold":
            fold_mode = True
        elif arg == "--check":
            check_mode = True
        elif arg == "--dry-run":
            dry_run = True
        elif arg == "--json":
            as_json = True
        elif arg in ("--round", "--fold-no", "--start", "--end", "--summary",
                     "--root", "--archive", "--refold-reason"):
            index += 1
            if index >= len(argv):
                sys.stdout.write("E_SFOLD_BAD_ARGS: %s needs a value\n" % arg)
                return 5
            value = argv[index]
            if arg == "--round":
                round_label = value
            elif arg == "--fold-no":
                fold_no = value
            elif arg == "--start":
                start = value
            elif arg == "--end":
                end = value
            elif arg == "--summary":
                summary = value
            elif arg == "--root":
                root = value
            elif arg == "--refold-reason":
                refold_reason = value
            else:
                archive = value
        elif arg in ("--help", "-h"):
            sys.stdout.write(USAGE)
            return 0
        else:
            sys.stdout.write("E_SFOLD_BAD_ARGS: unknown flag %s\n" % arg)
            sys.stdout.write(USAGE)
            return 5
        index += 1

    if check_mode:
        try:
            report = SF.check(root)
        except SF.StateFoldError as exc:
            sys.stdout.write("%s\n" % exc.code)
            return 3
        if as_json:
            sys.stdout.write(SF.to_json(report, SF.CHECK_KEYS))
        else:
            sys.stdout.write(SF.render(report) + "\n")
        return 2 if report["fold_needed"] else 0

    if not fold_mode:
        sys.stdout.write("E_SFOLD_BAD_ARGS: --fold or --check is required\n")
        sys.stdout.write(USAGE)
        return 5
    missing = [name for name, value in (("--round", round_label),
                                        ("--fold-no", fold_no),
                                        ("--start", start), ("--end", end),
                                        ("--summary", summary))
               if value is None]
    if missing:
        sys.stdout.write("E_SFOLD_BAD_ARGS: missing %s\n"
                         % ",".join(missing))
        return 5
    try:
        report = run(root, round_label, int(fold_no), int(start), int(end),
                     summary, archive_path=archive, dry_run=dry_run,
                     refold_reason=refold_reason)
    except FoldRunError as exc:
        sys.stdout.write("%s %s\n" % (exc.code, exc.detail))
        return 2
    except SF.StateFoldError as exc:
        sys.stdout.write("%s %s\n" % (exc.code, exc.detail))
        return 3
    if as_json:
        ordered = {}
        for key in REPORT_KEYS:
            ordered[key] = report.get(key)
        sys.stdout.write(json.dumps(ordered, ensure_ascii=True,
                                    sort_keys=False) + "\n")
    else:
        sys.stdout.write(render(report) + "\n")
        if report["would_fail"]:
            sys.stdout.write("REFUSED %s\n"
                             % ",".join(report["would_fail"]))
            return 2
    return 2 if report["would_fail"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))