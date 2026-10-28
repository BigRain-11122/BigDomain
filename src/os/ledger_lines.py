"""Round ledger line checker (R2152; AC-LGR1..AC-LGR8 pre-registered in
state/queue/tech.md BEFORE this code existed - honesty law).

Every OS round closes with one machine-readable ledger line:

    R2152 tokens: local=~95k api=0 api_reason=<one line why>

The F3 law and the status-export self_drive face both derive from that
shape, so a silent format drift would quietly mute the derivation
instead of turning it red. This module parses the shape, audits a log
window for bad forms and for narrative/ledger coverage, and exposes a
CLI gate.

Kinds of log line:
  ledger - starts with "R<n> tokens:" and must parse
  round  - starts with "R<n> " or "<date> R<n> " (the round narrative,
           or a "R<n> battery outcome:" line) and must have a ledger
           line for the same round
  other  - everything else (fold lines, receipts, notes)

A typo such as "R<n> token:" classifies as round, so the coverage law
reports the missing ledger for that round instead of silently skipping
it.

Known historical gaps live in state/ledger_gaps.json: the audit reports
every gap, and the CLI subtracts the baseline so only NEW drift turns
the gate red. Each entry exempts one round and one round only; an entry
whose gap no longer exists is reported as stale (R2157; AC-LGB3/AC-LGB4)
so the exemption list cannot rot into a silent junk drawer.

Exit codes: 0 clean, 2 dirty or bad arguments, 3 state file missing or
unparseable. Stdlib only, ASCII source, zero network.

Audit scope (R2224; AC-LGA1..AC-LGA8): a fold moves the oldest log lines
out of state.json into logs/state-log-archive-*.md, so a live-only
coverage floor cannot be met once the live array is folded (R2223
measured the 78500B waterline and a 30-line live floor to be mutually
unsatisfiable at current line sizes). audit_scope() therefore takes its
counts from the union of the live window and the archive sections, while
errors and the actionable gap set stay LIVE-only: an archive section is
frozen history no later round may rewrite, so a gap there is reported as
archived_missing / archived_orphan and never gates. The default CLI face
does not read the archive; --archives DIR switches to the scoped face.
"""

import io
import json
import os
import re
import sys

LEDGER_PREFIX_RE = re.compile(r"^R(\d{3,5}) tokens:")
NARRATIVE_RE = re.compile(r"^(?:\d{4}-\d{2}-\d{2}\s+)?R(\d{3,5})\s")
LOCAL_NUM_RE = re.compile(r"^(\d+(?:\.\d+)?)([kKmM]?)$")
API_NUM_RE = re.compile(r"^\d+$")
UNITS = {"": 1, "k": 1000, "m": 1000000}
MIN_REASON_CHARS = 10
BASELINE_NAME = "ledger_gaps.json"

NET_IMPORTS = ("urllib", "http.client", "requests", "socket", "httpx")


class LedgerLineError(ValueError):
    """A ledger line (or baseline file) that breaks the pinned shape."""

    def __init__(self, code, detail):
        ValueError.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def classify(line):
    """Return 'ledger', 'round' or 'other' for one log line."""
    text = line if isinstance(line, str) else str(line)
    if LEDGER_PREFIX_RE.match(text):
        return "ledger"
    if NARRATIVE_RE.match(text):
        return "round"
    return "other"


def parse_ledger_line(line):
    """Parse one ledger line or raise LedgerLineError.

    Gate order is pinned round -> local -> api -> reason: when several
    pieces are wrong the earliest one is reported.
    """
    text = line if isinstance(line, str) else str(line)
    match = LEDGER_PREFIX_RE.match(text)
    if match is None:
        raise LedgerLineError("E_LGR_NO_ROUND",
                              "no leading 'R<n> tokens:' prefix: %r"
                              % text[:40])
    round_no = int(match.group(1))
    rest = text[match.end():]
    if not rest.startswith(" local="):
        raise LedgerLineError("E_LGR_NO_LOCAL",
                              "round %d has no ' local=' field" % round_no)
    body = rest[len(" local="):]
    if " api=" not in body:
        raise LedgerLineError("E_LGR_NO_API",
                              "round %d has no ' api=' field" % round_no)
    head, tail = body.split(" api=", 1)
    local_raw = head.strip()
    if " api_reason=" not in tail:
        raise LedgerLineError("E_LGR_NO_REASON",
                              "round %d has no ' api_reason=' field"
                              % round_no)
    api_raw, reason = tail.split(" api_reason=", 1)

    approx = local_raw.startswith("~")
    number = local_raw[1:].strip() if approx else local_raw.strip()
    num_match = LOCAL_NUM_RE.match(number)
    if num_match is None:
        raise LedgerLineError("E_LGR_BAD_LOCAL",
                              "round %d local=%r is not a number with an "
                              "optional k/m unit" % (round_no, local_raw))
    local_value = int(round(float(num_match.group(1))
                            * UNITS[num_match.group(2).lower()]))

    api_token = api_raw.strip()
    if API_NUM_RE.match(api_token) is None:
        raise LedgerLineError("E_LGR_BAD_API",
                              "round %d api=%r is not a pure integer"
                              % (round_no, api_raw))
    api_value = int(api_token)

    if "\n" in reason or "\r" in reason:
        raise LedgerLineError("E_LGR_MULTILINE",
                              "round %d api_reason spans lines" % round_no)
    reason_text = reason.strip()
    if not reason_text:
        raise LedgerLineError("E_LGR_NO_REASON",
                              "round %d api_reason is empty" % round_no)
    if len(reason_text) < MIN_REASON_CHARS:
        raise LedgerLineError("E_LGR_SHORT_REASON",
                              "round %d api_reason=%r is shorter than %d "
                              "characters"
                              % (round_no, reason_text, MIN_REASON_CHARS))
    return {
        "round": round_no,
        "local_raw": local_raw,
        "local_value": local_value,
        "local_approx": approx,
        "api": api_value,
        "api_approx": False,
        "api_reason": reason_text,
    }


def audit(lines, tail=None):
    """Audit a list of log lines and return a derived report.

    tail=None inspects the whole list; an int inspects only the last N
    lines. Every number in the report is derived from the lines given.
    """
    total = len(lines)
    if tail is None:
        start = 0
    else:
        if not isinstance(tail, int) or tail < 1:
            raise LedgerLineError("E_LGR_BAD_ARGS",
                                  "tail must be a positive integer")
        start = max(0, total - tail)
    window = lines[start:]
    errors = []
    ledger_rounds = []
    round_rounds = []
    kinds = {"ledger": 0, "round": 0, "other": 0}
    for offset, raw in enumerate(window):
        line = raw if isinstance(raw, str) else str(raw)
        kind = classify(line)
        kinds[kind] += 1
        if kind == "ledger":
            try:
                ledger_rounds.append(parse_ledger_line(line)["round"])
            except LedgerLineError as exc:
                errors.append({
                    "line": start + offset + 1,
                    "code": exc.code,
                    "detail": exc.detail,
                })
        elif kind == "round":
            round_rounds.append(int(NARRATIVE_RE.match(line).group(1)))
    missing = sorted(set(round_rounds) - set(ledger_rounds))
    orphan = sorted(set(ledger_rounds) - set(round_rounds))
    return {
        "total_lines": total,
        "window_lines": len(window),
        "tail": tail,
        "ledger_lines": kinds["ledger"],
        "round_lines": kinds["round"],
        "other_lines": kinds["other"],
        "errors": errors,
        "rounds_without_ledger": missing,
        "ledger_without_round": orphan,
        "clean": not errors and not missing and not orphan,
    }


def default_baseline_path():
    """The shipped baseline of known historical gaps."""
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.normpath(os.path.join(here, "..", "..", "state",
                                         BASELINE_NAME))


def load_baseline(path):
    """Read the known-gap baseline; missing file means an empty one."""
    empty = {"missing": [], "orphan": []}
    if not os.path.exists(path):
        return empty
    try:
        with io.open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (IOError, OSError, ValueError) as exc:
        raise LedgerLineError("E_LGR_BAD_BASELINE",
                              "%s is unreadable: %s" % (path, exc))
    if not isinstance(data, dict):
        raise LedgerLineError("E_LGR_BAD_BASELINE",
                              "%s must hold a JSON object" % path)
    out = {}
    for key in ("missing", "orphan"):
        values = data.get(key, [])
        if not isinstance(values, list) or not all(
                isinstance(item, int) for item in values):
            raise LedgerLineError("E_LGR_BAD_BASELINE",
                                  "%s.%s must be a list of round numbers"
                                  % (path, key))
        out[key] = sorted(values)
    return out


def apply_baseline(report, baseline):
    """Subtract known historical gaps and recompute the gate verdict.

    Each baseline entry exempts exactly its own round number and
    nothing else. A baseline entry whose gap is gone from the report is
    reported back as STALE (R2157; AC-LGB3/AC-LGB4): a stale entry is a
    maintenance signal, not drift, so it never flips the verdict - but
    it is never silently kept either, because a baseline that quietly
    grows into a junk drawer makes every future exemption unreadable.
    This function never rewrites the baseline file.
    """
    known_missing = baseline.get("missing", [])
    known_orphan = baseline.get("orphan", [])
    current_missing = report["rounds_without_ledger"]
    current_orphan = report["ledger_without_round"]
    new_missing = [n for n in current_missing if n not in known_missing]
    new_orphan = [n for n in current_orphan if n not in known_orphan]
    stale_missing = [n for n in known_missing if n not in current_missing]
    stale_orphan = [n for n in known_orphan if n not in current_orphan]
    out = dict(report)
    out["baseline_missing"] = len(known_missing)
    out["baseline_orphan"] = len(known_orphan)
    out["new_missing"] = new_missing
    out["new_orphan"] = new_orphan
    out["stale_missing"] = stale_missing
    out["stale_orphan"] = stale_orphan
    out["clean"] = not report["errors"] and not new_missing and not new_orphan
    return out


def load_state_log(path):
    """Read the log list out of a state.json file."""
    with io.open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    log = data.get("log")
    if not isinstance(log, list):
        raise LedgerLineError("E_LGR_NO_STATE",
                              "%s has no 'log' list" % path)
    return log


ARCHIVE_PREFIX = "state-log-archive-"
ARCHIVE_SUFFIX = ".md"
COMMENT_PREFIX = "#"
MIN_COVERAGE_LINES = 30


def default_logs_dir(state_path=None):
    """The logs/ directory beside the repository root of a state file."""
    if state_path is None:
        here = os.path.dirname(os.path.abspath(__file__))
        state_path = os.path.join(here, "state.json")
    root = os.path.dirname(os.path.abspath(state_path))
    return os.path.normpath(os.path.join(root, "..", "..", "logs"))


def archive_files(logs_dir):
    """Archive section files in a logs directory, oldest month first."""
    if not os.path.isdir(logs_dir):
        raise LedgerLineError("E_LGR_BAD_ARCHIVE",
                              "%s is not a directory" % logs_dir)
    names = sorted(name for name in os.listdir(logs_dir)
                   if name.startswith(ARCHIVE_PREFIX)
                   and name.endswith(ARCHIVE_SUFFIX))
    return [os.path.join(logs_dir, name) for name in names]


def load_archive(path):
    """Log lines out of one folded archive section file (R2224).

    '#' lines are the rebuild header and the '# --- R<n>' fold-window
    markers, never log lines; blank lines are dropped too. Everything
    else is a line the fold moved out of state.json verbatim, so it is
    returned unmodified - no normalisation, and the file is never
    rewritten.
    """
    lines = []
    try:
        handle = io.open(path, "r", encoding="utf-8")
    except (IOError, OSError) as exc:
        raise LedgerLineError("E_LGR_BAD_ARCHIVE",
                              "%s is unreadable: %s" % (path, exc))
    try:
        for raw in handle:
            text = raw.rstrip("\n").rstrip("\r")
            if not text.strip() or text.startswith(COMMENT_PREFIX):
                continue
            lines.append(text)
    except UnicodeDecodeError as exc:
        raise LedgerLineError("E_LGR_BAD_ARCHIVE",
                              "%s is not valid utf-8: %s" % (path, exc))
    finally:
        handle.close()
    return lines


def load_archive_lines(logs_dir=None, state_path=None):
    """Every archive section line, oldest section first."""
    if logs_dir is None:
        logs_dir = default_logs_dir(state_path)
    out = []
    for path in archive_files(logs_dir):
        out.extend(load_archive(path))
    return out


def coverage_floor(report, minimum=MIN_COVERAGE_LINES):
    """The coverage floor both live-gate suites pin (R2224)."""
    return (report["ledger_lines"] >= minimum
            and report["round_lines"] >= minimum)


def audit_scope(archive_lines, live_lines, tail=None):
    """Audit the coverage scope: live window plus folded archive (R2224).

    Counts (total_lines, ledger_lines, round_lines, other_lines) come
    from the UNION, because a round the fold moved into an archive
    section is still a round that was closed - it left the live array,
    not the history. The actionable set (errors, rounds_without_ledger,
    ledger_without_round) comes from the LIVE window only, because that
    is the only place a later round can still introduce drift: an
    archive section is byte-verbatim frozen history that no round may
    rewrite, so a gap found there is a fact and is reported as
    archived_missing / archived_orphan, never used to gate.

    `tail` cuts the live window and never the union counts - which is
    exactly the conflict R2223 measured: the fold empties the live
    array, so a live-only floor can never be met again while the union
    floor keeps reading the whole history.
    """
    live_report = audit(live_lines, tail)
    live_full = audit(live_lines)
    archive_report = audit(archive_lines)
    out = dict(live_report)
    out["scope"] = "live+archive"
    out["archive_lines"] = archive_report["total_lines"]
    out["live_lines"] = live_full["total_lines"]
    out["archive_ledger_lines"] = archive_report["ledger_lines"]
    out["archive_round_lines"] = archive_report["round_lines"]
    out["live_ledger_lines"] = live_full["ledger_lines"]
    out["live_round_lines"] = live_full["round_lines"]
    out["total_lines"] = archive_report["total_lines"] + live_full["total_lines"]
    out["ledger_lines"] = (archive_report["ledger_lines"]
                           + live_full["ledger_lines"])
    out["round_lines"] = (archive_report["round_lines"]
                          + live_full["round_lines"])
    out["other_lines"] = (archive_report["other_lines"]
                          + live_full["other_lines"])
    out["archived_missing"] = archive_report["rounds_without_ledger"]
    out["archived_orphan"] = archive_report["ledger_without_round"]
    out["clean"] = live_report["clean"]
    return out


def import_roots(source_text):
    """Collect the root module names of every import statement."""
    roots = []
    for raw in source_text.splitlines():
        line = raw.strip()
        if line.startswith("import "):
            for part in line[len("import "):].split(","):
                name = part.strip().split(" ")[0]
                if name:
                    roots.append(name.split(".")[0])
        elif line.startswith("from ") and " import " in line:
            name = line[len("from "):].split(" ")[0]
            if name:
                roots.append(name.split(".")[0])
    return roots


def network_imports(source_text):
    """Import roots that touch the network, sorted for stable output."""
    return sorted(set(root for root in import_roots(source_text)
                      if root in NET_IMPORTS))


def format_report(report):
    """Render the audit report as printable ASCII lines."""
    tail = report["tail"]
    out = [
        "lines: total=%d window=%d tail=%s"
        % (report["total_lines"], report["window_lines"],
           "all" if tail is None else str(tail)),
        "kinds: ledger=%d round=%d other=%d"
        % (report["ledger_lines"], report["round_lines"],
           report["other_lines"]),
    ]
    if "scope" in report:
        out.append("scope: %s archive_lines=%d live_lines=%d "
                   "archived_missing=%d archived_orphan=%d"
                   % (report["scope"], report["archive_lines"],
                      report["live_lines"],
                      len(report["archived_missing"]),
                      len(report["archived_orphan"])))
    for item in report["errors"]:
        out.append("error %s line %d: %s"
                   % (item["code"], item["line"], item["detail"]))
    out.append("rounds_without_ledger: %s"
               % (",".join(str(n) for n in
                           report["rounds_without_ledger"]) or "none"))
    out.append("ledger_without_round: %s"
               % (",".join(str(n) for n in
                           report["ledger_without_round"]) or "none"))
    if "new_missing" in report:
        out.append("baseline: missing=%d orphan=%d"
                   % (report["baseline_missing"], report["baseline_orphan"]))
        out.append("new_missing: %s"
                   % (",".join(str(n) for n in report["new_missing"])
                      or "none"))
        out.append("new_orphan: %s"
                   % (",".join(str(n) for n in report["new_orphan"])
                      or "none"))
        stale = report["stale_missing"] + report["stale_orphan"]
        if stale:
            out.append("stale: missing=%s orphan=%s"
                       % (",".join(str(n) for n in
                                   report["stale_missing"]) or "none",
                          ",".join(str(n) for n in
                                   report["stale_orphan"]) or "none"))
    out.append("VERDICT %s" % ("CLEAN" if report["clean"] else "DIRTY"))
    return out


CLOSEOUT_KEYS = ("round", "verdict", "ledger_line", "errors",
                 "previous_round")
CLOSEOUT_VERDICTS = ("OK", "MISSING", "BAD_SHAPE", "NOT_MONOTONIC")


def _scan_entries(lines):
    """Split a log window into ledger entries and narrative rounds.

    Ledger entries keep the position of the line, its round number, the
    parsed payload (None when the shape is broken) and the error.
    Positions are 0-based here and reported 1-based by the caller.
    """
    entries = []
    narrative = []
    for index, raw in enumerate(lines):
        line = raw if isinstance(raw, str) else str(raw)
        kind = classify(line)
        if kind == "ledger":
            try:
                parsed = parse_ledger_line(line)
                entries.append((index, parsed["round"], parsed, None))
            except LedgerLineError as exc:
                round_no = int(LEDGER_PREFIX_RE.match(line).group(1))
                entries.append((index, round_no, None, exc))
        elif kind == "round":
            narrative.append((index,
                              int(NARRATIVE_RE.match(line).group(1))))
    return entries, narrative


def check_closeout(lines, round_no=None):
    """Check the closing station of ONE round (R2154; AC-LGN1..AC-LGN8).

    The whole-window audit answers "is the log consistent" only after
    the fact. This face answers the question the closing step itself
    must ask before it may declare the round shut: is the line this
    round just wrote parseable, does it carry a settleable reason, and
    is it newer than everything already settled before it.

    round_no=None targets the newest narrative round; an int targets
    that round explicitly (which is how a closeout names its own round).
    Gate order is pinned: absence, then broken shape, then ordering -
    fail-closed on the earliest missing evidence.

    Deterministic, read-only, zero network.
    """
    text_lines = [line if isinstance(line, str) else str(line)
                  for line in lines]
    entries, narrative = _scan_entries(text_lines)
    if round_no is None:
        if narrative:
            target = max(item[1] for item in narrative)
        elif entries:
            target = max(item[1] for item in entries)
        else:
            raise LedgerLineError(
                "E_LGN_NO_ROUND",
                "the window holds no round line and no ledger line")
    else:
        if not isinstance(round_no, int) or round_no < 1:
            raise LedgerLineError("E_LGN_BAD_ARGS",
                                  "round must be a positive integer")
        target = round_no
    errors = []
    target_entries = [item for item in entries if item[1] == target]
    anchor = None
    if target_entries:
        anchor = target_entries[-1][0]
    else:
        target_narrative = [item[0] for item in narrative if item[1] == target]
        if target_narrative:
            anchor = target_narrative[-1]
        else:
            anchor = len(text_lines)
    previous = [item[1] for item in entries if item[0] < anchor]
    previous_round = max(previous) if previous else None
    ledger_line = None
    if not target_entries:
        verdict = "MISSING"
        errors.append({"code": "E_LGN_MISSING",
                       "detail": "round %d has no ledger line before the "
                                 "closing station" % target})
    else:
        index, _, parsed, exc = target_entries[-1]
        ledger_line = index + 1
        if exc is not None:
            verdict = "BAD_SHAPE"
            errors.append({"code": exc.code, "detail": exc.detail,
                           "line": ledger_line})
        elif previous_round is not None and target <= previous_round:
            verdict = "NOT_MONOTONIC"
            errors.append({
                "code": "E_LGN_NOT_MONOTONIC",
                "detail": "round %d is not newer than the settled round %d"
                          % (target, previous_round),
                "line": ledger_line,
            })
        else:
            verdict = "OK"
    return {
        "round": target,
        "verdict": verdict,
        "ledger_line": ledger_line,
        "errors": errors,
        "previous_round": previous_round,
    }


def format_closeout(report):
    """Render a closeout verdict as printable ASCII lines."""
    out = [
        "closeout round=%d verdict=%s line=%s previous=%s"
        % (report["round"], report["verdict"],
           "none" if report["ledger_line"] is None
           else str(report["ledger_line"]),
           "none" if report["previous_round"] is None
           else str(report["previous_round"])),
    ]
    for item in report["errors"]:
        out.append("error %s: %s" % (item["code"], item["detail"]))
    return out


def _stderr(message):
    sys.stderr.write(message + "\n")
    sys.stderr.flush()


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    path = None
    tail = None
    as_json = False
    baseline_path = default_baseline_path()
    use_baseline = True
    closeout = False
    round_no = None
    archives_dir = None
    index = 0
    while index < len(args):
        arg = args[index]
        if arg == "--check":
            index += 1
        elif arg == "--json":
            as_json = True
            index += 1
        elif arg == "--no-baseline":
            use_baseline = False
            index += 1
        elif arg == "--closeout":
            closeout = True
            index += 1
        elif arg == "--round":
            if index + 1 >= len(args) or not args[index + 1].isdigit():
                _stderr("E_LGN_BAD_ARGS: --round needs a positive integer")
                return 2
            round_no = int(args[index + 1])
            if round_no < 1:
                _stderr("E_LGN_BAD_ARGS: --round needs a positive integer")
                return 2
            index += 2
        elif arg == "--archives":
            if index + 1 >= len(args):
                _stderr("E_LGR_BAD_ARGS: --archives needs a directory")
                return 2
            archives_dir = args[index + 1]
            index += 2
        elif arg == "--baseline":
            if index + 1 >= len(args):
                _stderr("E_LGR_BAD_ARGS: --baseline needs a path")
                return 2
            baseline_path = args[index + 1]
            use_baseline = True
            index += 2
        elif arg == "--tail":
            if index + 1 >= len(args) or not args[index + 1].isdigit():
                _stderr("E_LGR_BAD_ARGS: --tail needs a positive integer")
                return 2
            tail = int(args[index + 1])
            if tail < 1:
                _stderr("E_LGR_BAD_ARGS: --tail needs a positive integer")
                return 2
            index += 2
        elif arg.startswith("-"):
            _stderr("E_LGR_BAD_ARGS: unknown flag %s" % arg)
            return 2
        else:
            if path is not None:
                _stderr("E_LGR_BAD_ARGS: only one state file allowed")
                return 2
            path = arg
            index += 1
    if path is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "state.json")
    try:
        log = load_state_log(path)
        if closeout:
            report = check_closeout(log, round_no)
        else:
            if archives_dir is not None:
                report = audit_scope(
                    load_archive_lines(archives_dir), log, tail)
            else:
                report = audit(log, tail)
            if use_baseline:
                report = apply_baseline(report, load_baseline(baseline_path))
    except LedgerLineError as exc:
        # AC-LGB5: a broken baseline names its own code instead of being
        # relabelled as a missing state file.
        _stderr("%s: %s" % (exc.code, exc.detail))
        return 3
    except (IOError, OSError, ValueError) as exc:
        _stderr("E_LGR_NO_STATE: %s" % exc)
        return 3
    if closeout:
        if as_json:
            sys.stdout.write(json.dumps(report, sort_keys=True) + "\n")
        elif report["verdict"] == "OK":
            # AC-LGN6: the passing gate prints exactly one line.
            sys.stdout.write("LEDGER OK %d\n" % report["round"])
        else:
            for line in format_closeout(report):
                sys.stdout.write(line + "\n")
        return 0 if report["verdict"] == "OK" else 2
    if as_json:
        sys.stdout.write(json.dumps(report, sort_keys=True) + "\n")
    else:
        for line in format_report(report):
            sys.stdout.write(line + "\n")
    return 0 if report["clean"] else 2


if __name__ == "__main__":
    sys.exit(main())