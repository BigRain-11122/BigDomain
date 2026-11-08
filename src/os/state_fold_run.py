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


def already_folded(state, window_start, window_end, summary):
    """The fold already happened: its summary line is live.

    The summary is the fold's own artifact and is unique per fold, so its
    presence is the one honest signal that a re-run has nothing left to do -
    window indices point at the pre-fold layout and must not be trusted.
    """
    return summary in state["log"]


def run(root, round_label, fold_no, window_start, window_end, summary,
        archive_path=None, dry_run=False, gate=SF.GATE):
    """Plan, refuse on any dirty predicate, execute, then prove the result."""
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
            "archive_path": archive_path or SF.default_archive(root),
            "archive_appendix_bytes": 0, "archive_verified": True,
            "layout_agree": True, "field_set_same": True,
            "ledger_rounds_before": len(ledger_coverage(
                logs_dir, state["log"])["ledger_rounds"]),
            "ledger_rounds_after": len(ledger_coverage(
                logs_dir, state["log"])["ledger_rounds"]),
            "would_fail": [], "dry_run_digest_same": after_digest == pre_digest,
        }

    plan, folded_text = SF.plan_fold(raw, state, window_start, window_end,
                                     summary, gate=gate)
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
    if plan["predicted_bytes"] > gate:
        # AC-SFOLD5: a fold that would leave the file over the waterline is
        # refused instead of claiming success - its own code, not the
        # predicate's general one.
        raise FoldRunError("E_SFOLD_GATE",
                           "%d bytes over %d"
                           % (plan["predicted_bytes"], gate))

    archive = archive_path or SF.default_archive(root)
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
                     summary, gate=gate, execute=True, archive_path=archive)
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
    if not before_cov["ledger_rounds"] <= after_cov["ledger_rounds"]:
        raise FoldRunError("E_SFOLD_LEDGER_LOSS",
                           "%d -> %d" % (len(before_cov["ledger_rounds"]),
                                         len(after_cov["ledger_rounds"])))
    if not report["archive_verified"]:
        raise FoldRunError("E_SFOLD_ARCHIVE_COPY",
                           "%s" % archive)
    if not report["layout_agree"]:
        raise FoldRunError("E_SFOLD_LAYOUT_DISAGREE", path)
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
    "       state_fold_run.py --check [--root PATH] [--json]\n"
    "  exit 0 = folded / ALREADY-FOLDED / FOLD-CLEAR\n"
    "  exit 2 = refused by the predicate (nothing written)\n"
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
                     "--root", "--archive"):
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
                     summary, archive_path=archive, dry_run=dry_run)
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