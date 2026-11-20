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
# R3084 AC-LGA10: the SHAPE law and the PRESENCE law are two laws, and only
# the shape law may refuse. LEDGER_PREFIX_RE is asked at birth (the write
# door, ledger_line_shape_guard) and by every shape reader, so it stays
# anchored at the round marker: a ledger line may not carry a date prefix.
# The history, however, holds 786 lines that DO carry one (measured over the
# three archive files), written before that door existed; the fold-carry
# law asks only whether a pairing survived the fold, and it read presence
# through the shape regex, so a dated line was invisible and a pairing that
# survived was reported lost (measured: R2980, window 2987). This regex is
# the presence read and nothing else: it tolerates the same optional date
# prefix NARRATIVE_RE already tolerates. classify(), parse_ledger_line()
# and the write door never see it, so relaxing presence cannot accept a
# malformed line at birth.
LEDGER_PRESENCE_RE = re.compile(r"^(?:\d{4}-\d{2}-\d{2}\s+)?R(\d{3,5}) tokens:")
# R3087 AC-LGA12: the date prefix the presence law tolerates, as its own
# constant so the payload reader can strip exactly what the presence law
# forgives and nothing else. Used only by audit_archive().
DATE_PREFIX_RE = re.compile(r"^\d{4}-\d{2}-\d{2}\s+")
NARRATIVE_RE = re.compile(r"^(?:\d{4}-\d{2}-\d{2}\s+)?R(\d{3,5})\s")
# R2580 AC-FCLS1..AC-FCLS3: the summary a fold leaves behind starts with
# the round it folded ("R2568 fold of log lines 1..20 ..."). The kind
# table above calls fold lines other, but NARRATIVE_RE matched them as
# round narratives, so a fold that archived a round's ledger line while
# keeping its summary live reported that round as having no ledger at all.
# The guard is word-bounded, so "R<n> folder of ..." is not swallowed.
#
# R2581 AC-LKND1/AC-LKND2: that guard was still anchored at the line start
# and knew only the bare "fold" inflection, so two real fold-summary shapes
# fell back to NARRATIVE_RE and re-opened the same gap - a summary stamped
# with the date the fold ran ("2026-11-08 R2568 fold of log lines ...") and
# the past-tense form ("R2568 folded the block into the archive"). Both are
# summary lines and never round narratives. The optional date prefix is the
# same one NARRATIVE_RE already tolerates, and both alternatives stay
# word-bounded so "R<n> folder of ..." is STILL a narrative.
#
# R2815 AC-LKNF1/AC-LKNF2: the inflection list was still lower-case and
# had no third-person form, so "R<n> Fold of log lines ..." and
# "R<n> folds the block ..." both fell back to NARRATIVE_RE and reported
# a false missing-ledger gap (measured at HEAD over five fixture lines).
# Case folding is scoped to the verb only - the round marker stays "R" -
# and the word boundary is unchanged, so "folder" and "foldsomething"
# remain narratives.
FOLD_SUMMARY_RE = re.compile(
    r"^(?:\d{4}-\d{2}-\d{2}\s+)?R(\d{3,5})\s+(?i:fold(?:s|ed)?)\b")
# R2832 AC-RMS1..AC-RMS3: the window derivation in
# check_export_consistency hangs on the max ^YYYY-MM-DD prefix of the live
# log, and R2828/R2829/R2830 wrote their round main lines as "R28xx ...".
# Nothing asked that shape before the line was appended, so the only
# detector was a ValueError raised at read time - and it detected by
# crashing, which reddened three queue-face suites with a traceback
# instead of a verdict. This regex is the law, and check_round_main_shape
# asks it of the NEWEST round only: older history may predate the law,
# the live round may not.
ROUND_MAIN_RE = re.compile(r"^\d{4}-\d{2}-\d{2} R(\d{3,5}) ")
# R2874 AC-RLBL1..AC-RLBL5: the LABEL law, and the only definition of it.
# The two readers of the CEO face (src/os/export_round.py ROUND_HEAD_RE and
# tools/status_export_fresh.py HEADLINE_RE) both open a headline with an
# UPPERCASE word after the round number; the write gate asked only for the
# date. Measured at R2864: a window that wrote "2026-11-17 R2864 law_status
# ..." passed state_append, both readers skipped it, and the CEO face went on
# naming the PREVIOUS round while every check read PASS. The law is therefore
# made stricter at the BIRTH site (nothing that no reader accepts should land)
# and both readers compose their pattern from this one string instead of
# keeping a second copy that can drift.
ROUND_LABEL_SRC = r"[A-Z][A-Z0-9 /_-]{2,}"
ROUND_LABEL_RE = re.compile(
    r"^(?:\d{4}-\d{2}-\d{2}\s+)?R\d{3,5}\s+" + ROUND_LABEL_SRC)
ROUND_MAIN_SAMPLE = 40
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
    if FOLD_SUMMARY_RE.match(text):
        return "other"
    if NARRATIVE_RE.match(text):
        return "round"
    return "other"


def classify_archive(line):
    """Return 'ledger', 'round' or 'other' for one ARCHIVE line (R3086).

    The live face and the archive face ask different questions, and only
    the archive face may tolerate a date prefix. classify() is the SHAPE
    face: it reads LEDGER_PREFIX_RE, so a ledger line written before the
    write door existed (measured: 786 dated lines over the three archives)
    reads as a round narrative there, and that is correct for the place
    the shape law is enforced. The archive is frozen history that no round
    may rewrite, so its counts and its advisory gap sets must ask presence
    instead - the same law audit_fold_carry already reads (R3084). This
    classifier is used ONLY by audit_archive/audit_scope; classify(),
    parse_ledger_line() and the write door never see it, so the shape law
    keeps refusing a malformed line at birth.
    """
    text = line if isinstance(line, str) else str(line)
    if LEDGER_PRESENCE_RE.match(text):
        return "ledger"
    if FOLD_SUMMARY_RE.match(text):
        return "other"
    if NARRATIVE_RE.match(text):
        return "round"
    return "other"


def check_round_main_shape(lines):
    """Ask the round-main shape law of the NEWEST round (R2832).

    Two laws, both fail-closed and neither of them a crash:

    - the window must hold at least one round narrative at all, or there
      is nothing for the export window to anchor on (E_RMS_NO_ROUND);
    - the newest round - newest by ROUND NUMBER, never by position - must
      carry at least one dated main line, because a round's later lines
      (disclosures, group scans, notes) legitimately carry no date of their
      own and belong to the main line they follow (E_RMS_NO_DATE);
    - that dated main line must also carry an UPPERCASE label after the
      round number (E_RMS_NO_LABEL), because both CEO-face readers
      (export_round.ROUND_HEAD_RE, status_export_fresh.HEADLINE_RE) require
      one and a line they skip makes the published face name the PREVIOUS
      round while the checks still read PASS (measured at R2864).

    Older rounds are deliberately not asked: history may predate the law,
    and a live round may not. The refinement against the pinned wording
    is disclosed in the R2832 board row - requiring the newest round's
    EVERY line to be dated would redden a healthy tree, while requiring
    its dated-main count to be at least one still catches the measured
    R2831 failure (14 live lines, none anchored).
    """
    newest = None
    per_round = {}
    for raw in lines:
        line = raw if isinstance(raw, str) else str(raw)
        if classify(line) != "round":
            continue
        round_no = int(NARRATIVE_RE.match(line).group(1))
        bucket = per_round.setdefault(round_no, {"lines": 0, "dated": 0,
                                                "labelled": 0})
        bucket["lines"] += 1
        if ROUND_MAIN_RE.match(line):
            bucket["dated"] += 1
            if ROUND_LABEL_RE.match(line):
                bucket["labelled"] += 1
            if newest is None or round_no > newest:
                newest = round_no
        elif newest is None or round_no > newest:
            newest = round_no
    if newest is None:
        return {
            "round": None,
            "ok": False,
            "code": "E_RMS_NO_ROUND",
            "detail": "the window holds no round narrative to anchor on",
            "round_lines": 0,
            "dated_lines": 0,
            "labelled_lines": 0,
            "sample": "",
        }
    bucket = per_round[newest]
    if bucket["dated"] >= 1 and bucket["labelled"] >= 1:
        return {
            "round": newest,
            "ok": True,
            "code": "",
            "detail": "",
            "round_lines": bucket["lines"],
            "dated_lines": bucket["dated"],
            "labelled_lines": bucket["labelled"],
            "sample": "",
        }
    if bucket["dated"] >= 1:
        sample = ""
        for raw in lines:
            line = raw if isinstance(raw, str) else str(raw)
            if ROUND_MAIN_RE.match(line) and not ROUND_LABEL_RE.match(line) \
                    and int(NARRATIVE_RE.match(line).group(1)) == newest:
                sample = line[:ROUND_MAIN_SAMPLE]
                break
        return {
            "round": newest,
            "ok": False,
            "code": "E_RMS_NO_LABEL",
            "detail": "newest round %d has %d dated line(s) and none carries "
                      "an UPPERCASE label after the round number, so no "
                      "CEO-face reader accepts it" % (newest, bucket["dated"]),
            "round_lines": bucket["lines"],
            "dated_lines": bucket["dated"],
            "labelled_lines": 0,
            "sample": sample,
        }
    sample = ""
    for raw in lines:
        line = raw if isinstance(raw, str) else str(raw)
        if classify(line) == "round" and int(
                NARRATIVE_RE.match(line).group(1)) == newest:
            sample = line[:ROUND_MAIN_SAMPLE]
            break
    return {
        "round": newest,
        "ok": False,
        "code": "E_RMS_NO_DATE",
        "detail": "newest round %d has %d round line(s) and none starts "
                  "with a YYYY-MM-DD prefix" % (newest, bucket["lines"]),
        "round_lines": bucket["lines"],
        "dated_lines": 0,
        "labelled_lines": 0,
        "sample": sample,
    }


def format_round_main(report):
    """Render the round-main verdict as exactly one printable ASCII line."""
    if report["ok"]:
        return "ROUND-MAIN OK %d" % report["round"]
    return "ROUND-MAIN FAIL %s round=%s" % (
        report["code"],
        "none" if report["round"] is None else str(report["round"]))


def parse_round_main_line(line):
    """Parse one rendered round-main verdict or raise LedgerLineError.

    The suite reads the CLI face through this parser so that the printed
    shape and the asserted shape cannot drift apart.
    """
    text = line if isinstance(line, str) else str(line)
    ok_match = re.match(r"^ROUND-MAIN OK (\d+)$", text)
    if ok_match is not None:
        return {"ok": True, "round": int(ok_match.group(1)), "code": ""}
    fail_match = re.match(r"^ROUND-MAIN FAIL (E_RMS_[A-Z_]+) "
                          r"round=(?:(\d+)|none)$", text)
    if fail_match is None:
        raise LedgerLineError("E_RMS_BAD_VERDICT",
                              "not a round-main verdict line: %r"
                              % text[:60])
    return {
        "ok": False,
        "round": None if fail_match.group(2) is None
        else int(fail_match.group(2)),
        "code": fail_match.group(1),
    }


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


def audit_archive(lines):
    """Audit frozen archive lines through the PRESENCE law (R3086).

    Same shape of report as audit(), derived with classify_archive() so a
    dated ledger line is a ledger line and not a round narrative. No parse
    is attempted: archives hold pre-law payloads (measured: R2875 has no
    ' local=' field) and a parse error there is frozen fact, not drift, so
    the scope face never reported one.
    """
    kinds = {"ledger": 0, "round": 0, "other": 0}
    ledger_rounds = []
    round_rounds = []
    bare = 0
    dated = 0
    unshaped = 0
    unshaped_codes = {}
    for raw in lines:
        line = raw if isinstance(raw, str) else str(raw)
        kind = classify_archive(line)
        kinds[kind] += 1
        if kind == "ledger":
            ledger_rounds.append(
                int(LEDGER_PRESENCE_RE.match(line).group(1)))
            if LEDGER_PREFIX_RE.match(line) is not None:
                bare += 1
            else:
                dated += 1
            # R3087 AC-LGA12: presence counts a line, parse judges its
            # payload. The date prefix is stripped first, so a dated line
            # with an intact payload is dated and NOT unshaped - only a
            # payload no reader can attribute is counted here. PUBLISHED
            # only: the archives are frozen history, no gate reads this.
            try:
                parse_ledger_line(DATE_PREFIX_RE.sub("", line, count=1))
            except LedgerLineError as exc:
                unshaped += 1
                unshaped_codes[exc.code] = unshaped_codes.get(exc.code, 0) + 1
        elif kind == "round":
            round_rounds.append(int(NARRATIVE_RE.match(line).group(1)))
    return {
        "total_lines": len(lines),
        "ledger_lines": kinds["ledger"],
        "round_lines": kinds["round"],
        "other_lines": kinds["other"],
        "bare_ledger_lines": bare,
        "dated_ledger_lines": dated,
        "unshaped_ledger_lines": unshaped,
        "unshaped_codes": unshaped_codes,
        "rounds_without_ledger": sorted(set(round_rounds)
                                        - set(ledger_rounds)),
        "ledger_without_round": sorted(set(ledger_rounds)
                                       - set(round_rounds)),
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


# R2914 AC-LGA9: the FOLD-CARRY law, scoped because the unscoped form was
# measured red before it was written. `--archives logs` reads
# archived_missing=787 / archived_orphan=52 on the pre-law tree (R2913), so
# "every archived round carries its ledger line" would install a gate that
# no later round could ever satisfy, and a permanently red gate teaches the
# next round to skip it. The law is therefore a FOLD-WINDOW law: it is asked
# only of windows whose own marker round is at or after the round that
# pinned it. Windows opened before the pin are frozen history this module
# may only read (same reason archived_* never gates in audit_scope).
#
# FOLD_CARRY_PIN is the ONE place the pin is typed; a window's marker round
# is read from the archive header line the fold itself writes.
FOLD_CARRY_PIN = 2914
FOLD_MARKER_RE = re.compile(r"^#\s*---\s*R(\d{3,5})\b")


def load_archive_windows(path):
    """Split ONE archive section file into its fold windows (R2914).

    A window opens at a '# --- R<n>' marker line and runs until the next
    marker of the same file; the marker's own round number is what the
    FOLD-CARRY scope is asked about. Lines before the first marker belong
    to no window and are dropped from the window view (they are still read
    by load_archive for the coverage scope). Each window carries the log
    lines verbatim, with '#' comment lines and blank lines dropped exactly
    as load_archive does, so the two readers cannot disagree about what a
    window holds.
    """
    windows = []
    current = None
    ordinal = 0
    try:
        handle = io.open(path, "r", encoding="utf-8")
    except (IOError, OSError) as exc:
        raise LedgerLineError("E_LGR_BAD_ARCHIVE",
                              "%s is unreadable: %s" % (path, exc))
    try:
        for line_no, raw in enumerate(handle, 1):
            text = raw.rstrip("\n").rstrip("\r")
            if text.startswith(COMMENT_PREFIX):
                match = FOLD_MARKER_RE.match(text)
                if match is not None:
                    # R3089: a position among EXAMINED windows shifts when
                    # the pin moves and cannot be opened in a file. The
                    # in-file ordinal and the marker's own line number are
                    # properties of the archive, measured unique and dense
                    # across all 754 windows, so they are what a reader can
                    # actually open. Both are read, never invented.
                    ordinal += 1
                    current = {"round": int(match.group(1)), "lines": [],
                               "path": path, "ordinal": ordinal,
                               "line": line_no}
                    windows.append(current)
                continue
            if not text.strip() or current is None:
                continue
            current["lines"].append(text)
    except UnicodeDecodeError as exc:
        raise LedgerLineError("E_LGR_BAD_ARCHIVE",
                              "%s is not valid utf-8: %s" % (path, exc))
    finally:
        handle.close()
    return windows


def audit_fold_carry(paths, min_round=None):
    """Ask the FOLD-CARRY law of every window opened at or after the pin.

    For each such window, every round whose NARRATIVE sits inside it must
    have its LEDGER line carried into the archive with it. The carry is
    checked at ARCHIVE granularity rather than same-window granularity
    because a fold is a contiguous line range: a round split across two
    windows would otherwise redden a healthy tree. The defect this law
    pins is the one R2912 measured - a narrative archived while its ledger
    line stayed behind in the LIVE log (ledger_without_round=2893), which
    is a lost pairing no reader can repair without the archive.

    Windows opened before the pin are counted as skipped, never as clean:
    with no post-pin window the gate reports itself VACUOUS rather than
    passing on nothing, so a green reading cannot be confused with a
    measured one.
    """
    if min_round is None:
        min_round = FOLD_CARRY_PIN
    if not isinstance(min_round, int) or min_round < 1:
        raise LedgerLineError("E_LGR_BAD_ARGS",
                              "min_round must be a positive integer")
    examined = []
    skipped = 0
    archive_rounds = set()
    for path in paths:
        for window in load_archive_windows(path):
            for line in window["lines"]:
                # Presence read, never a shape read: the archive carries
                # pre-law ledger lines whose payload is broken (measured:
                # R2875 has no ' local=' field), and this law asks only
                # whether the pairing survived the fold. Shape has its own
                # gates, and they are live-only by design (audit_scope).
                # R3084: presence goes through LEDGER_PRESENCE_RE, not the
                # shape regex - a dated line written before the write door
                # existed is still a ledger line that survived the fold.
                presence = LEDGER_PRESENCE_RE.match(line)
                if presence is not None:
                    archive_rounds.add(int(presence.group(1)))
            if window["round"] < min_round:
                skipped += 1
                continue
            examined.append(window)
    gaps = []
    same_window = []
    rounds = 0
    # R3086: two PUBLISHED diagnostics, neither of which may change the
    # verdict. The carry law is archive-granular by design (a fold moves a
    # contiguous line range, so a round can legitimately land in two
    # windows), which left a reader unable to tell a whole round from a
    # split one - measured: 3 split rounds across the 29 post-pin windows,
    # and 48 across all 754 archive windows. Naming them is the smallest
    # honest answer; gating on them would false-kill healthy history,
    # measured before this line was written.
    window_rounds = []
    window_indices = []
    for index, window in enumerate(examined):
        here = set()
        for line in window["lines"]:
            presence = LEDGER_PRESENCE_RE.match(line)
            if presence is not None:
                here.add(int(presence.group(1)))
        narratives = sorted(set(
            int(NARRATIVE_RE.match(line).group(1))
            for line in window["lines"] if classify(line) == "round"))
        window_rounds.append(narratives)
        window_indices.append(index + 1)
        rounds += len(narratives)
        for round_no in narratives:
            if round_no not in archive_rounds:
                gaps.append({"window": window["round"],
                             "round": round_no,
                             "path": window["path"],
                             "file": os.path.basename(window["path"]),
                             "file_ordinal": window["ordinal"],
                             "line": window["line"]})
            if round_no not in here:
                # R3087 AC-LGA12: the marker alone cannot locate a short
                # window - two folds in one round write two windows with
                # the same marker (measured: 2946 and 3085 each carried
                # twice). window_index is the position among the examined
                # windows, so two entries with one marker are still told
                # apart by a reader. PUBLISHED, never a verdict input.
                # R3089 AC-LGA13: window_index alone still cannot be
                # opened - it starts at the pin, so a reader has to add the
                # file's pre-pin window count (measured: 202 for the live
                # 29). file/file_ordinal/line are the archive's own
                # coordinates, read at this moment.
                same_window.append({"window": window["round"],
                                    "window_index": index + 1,
                                    "round": round_no,
                                    "path": window["path"],
                                    "file": os.path.basename(window["path"]),
                                    "file_ordinal": window["ordinal"],
                                    "line": window["line"]})
    seen = {}
    for index, narratives in enumerate(window_rounds):
        for round_no in narratives:
            seen.setdefault(round_no, []).append(
                (examined[index]["round"], window_indices[index], index))
    split = [{"round": round_no,
              "windows": sorted(marker for marker, _i, _x in members),
              "window_indices": sorted(idx for _m, idx, _x in members),
              "locators": [{"file": os.path.basename(
                                examined[x]["path"]),
                            "file_ordinal": examined[x]["ordinal"],
                            "line": examined[x]["line"]}
                           for _m, _idx, x in sorted(
                               members, key=lambda row: row[1])]}
             for round_no, members in sorted(seen.items())
             if len(members) > 1]
    marker_counts = {}
    for window in examined:
        marker_counts[window["round"]] = marker_counts.get(
            window["round"], 0) + 1
    duplicate_markers = sorted(marker for marker, count
                               in marker_counts.items() if count > 1)
    return {
        "since": min_round,
        "windows": len(examined),
        "skipped_windows": skipped,
        "rounds": rounds,
        "gaps": gaps,
        "split_rounds": split,
        "same_window_gaps": same_window,
        "duplicate_markers": duplicate_markers,
        "clean": not gaps,
        "vacuous": not examined,
    }


def format_fold_carry(report):
    """Render the FOLD-CARRY verdict as exactly one printable ASCII line.

    R3089: positions in this report are the ARCHIVE's own coordinates -
    file name, in-file window ordinal, marker line number - so the trailing
    token says so on every shape. They are true as of the read that
    produced this line.

    R3090: that claim is only as strong as the archive's provenance, and it
    was measured per file: the November archive IS git-tracked (137 commits,
    +5498/-0 lines), which is what makes a published line number stable; the
    September and October archives are NOT tracked (0 commits, excluded by
    the 'logs/' ignore rule), so for them the honest reading is 'no local
    rewrite observed on this machine', not 'append-only proven'. The FAIL
    shape now publishes those coordinates on every gap, because a red line
    that names only the marker still sends the reader hunting by hand.
    """
    if report["vacuous"]:
        return ("FOLD-CARRY VACUOUS since=%d windows=0 skipped=%d "
                "(no window opened at or after the pin yet) dup=0 "
                "loc=file@line"
                % (report["since"], report["skipped_windows"]))
    if report["clean"]:
        return ("FOLD-CARRY OK since=%d windows=%d rounds=%d skipped=%d "
                "split=%d same_window=%d dup=%d loc=file@line"
                % (report["since"], report["windows"], report["rounds"],
                   report["skipped_windows"], len(report["split_rounds"]),
                   len(report["same_window_gaps"]),
                   len(report["duplicate_markers"])))
    # R3090: a gap entry already knows where its window opens; printing only
    # the marker left the reader to search. The locator is appended INSIDE
    # the per-gap token so every existing reader (which matches R<n>) keeps
    # working, and it falls back to the old shape if a caller builds a report
    # without the R3089 fields rather than printing a broken position.
    def _gap_token(item):
        head = "R%d(w%d" % (item["round"], item["window"])
        if all(key in item for key in ("file", "file_ordinal", "line")):
            return "%s@%s:%d:%d)" % (head, item["file"],
                                     item["file_ordinal"], item["line"])
        return head + ")"

    gaps = ",".join(_gap_token(item) for item in report["gaps"])
    return ("FOLD-CARRY FAIL E_LFC_CARRY since=%d windows=%d gaps=%s "
            "split=%d same_window=%d dup=%d loc=file@line"
            % (report["since"], report["windows"], gaps,
               len(report["split_rounds"]),
               len(report["same_window_gaps"]),
               len(report["duplicate_markers"])))


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

    R3086: the archive half of every number here is derived through
    audit_archive(), i.e. the presence law, not classify(). Measured
    before the change: 786 dated ledger lines over the three archives
    were counted as round narratives (archive_ledger_lines 1090 where
    presence reads 1876) and inflated archived_missing by the same root.
    The archive advisory sets move with the counts so the published face
    cannot say "counted as round" and "missing a ledger" about one line.
    The live half keeps classify() unchanged: that is where the shape law
    is enforced and where a later round can still introduce drift.
    """
    live_report = audit(live_lines, tail)
    live_full = audit(live_lines)
    archive_report = audit_archive(archive_lines)
    out = dict(live_report)
    out["scope"] = "live+archive"
    out["archive_lines"] = archive_report["total_lines"]
    out["live_lines"] = live_full["total_lines"]
    out["archive_ledger_lines"] = archive_report["ledger_lines"]
    out["archive_round_lines"] = archive_report["round_lines"]
    # R3087 AC-LGA12: two PUBLISHED payload readings, derived from the same
    # archive pass. audit_archive() counts a line by presence and never
    # parsed it, so a frozen line whose payload no reader can attribute was
    # invisible (measured: 2 bare archive ledger lines carry no ' local=').
    # Neither number may gate: the archives are frozen history.
    out["archive_dated_ledger_lines"] = archive_report["dated_ledger_lines"]
    out["archive_unshaped_ledger_lines"] = archive_report[
        "unshaped_ledger_lines"]
    out["archive_unshaped_codes"] = archive_report["unshaped_codes"]
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
        # R3087 AC-LGA12: the payload reading a reader never had. Published
        # only - the archives are frozen, so neither number may gate.
        out.append("archive_payload: dated=%d unshaped=%d codes=%s"
                   % (report["archive_dated_ledger_lines"],
                      report["archive_unshaped_ledger_lines"],
                      ",".join("%s:%d" % (code, count) for code, count
                               in sorted(
                                   report["archive_unshaped_codes"].items()))
                      or "none"))
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
    round_main = False
    round_no = None
    archives_dir = None
    fold_carry = False
    since_round = None
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
        elif arg == "--round-main":
            # R2832 AC-RMS2: the write path's shape law, asked as its own
            # gate so a window can redden BEFORE it appends.
            round_main = True
            index += 1
        elif arg == "--fold-carry":
            # R2914 AC-LGA9: the scoped fold-carry gate, asked beside
            # --archives so a window can redden before it folds.
            fold_carry = True
            index += 1
        elif arg == "--since":
            if index + 1 >= len(args) or not args[index + 1].isdigit():
                _stderr("E_LGR_BAD_ARGS: --since needs a positive integer")
                return 2
            since_round = int(args[index + 1])
            if since_round < 1:
                _stderr("E_LGR_BAD_ARGS: --since needs a positive integer")
                return 2
            index += 2
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
    if fold_carry and archives_dir is None:
        # R2914: a missing companion flag is a usage error (exit 2), not a
        # broken state file (exit 3) - the reader never got far enough to
        # touch the tree.
        _stderr("E_LGR_BAD_ARGS: --fold-carry needs --archives DIR to read "
                "windows from")
        return 2
    try:
        log = load_state_log(path)
        if closeout:
            report = check_closeout(log, round_no)
        elif round_main:
            report = check_round_main_shape(log)
        elif fold_carry:
            report = audit_fold_carry(archive_files(archives_dir),
                                      since_round)
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
    if round_main:
        if as_json:
            sys.stdout.write(json.dumps(report, sort_keys=True) + "\n")
        else:
            sys.stdout.write(format_round_main(report) + "\n")
            if not report["ok"] and report["sample"]:
                _stderr("%s: %s (first line: %r)"
                        % (report["code"], report["detail"],
                           report["sample"]))
        return 0 if report["ok"] else 2
    if fold_carry:
        if as_json:
            sys.stdout.write(json.dumps(report, sort_keys=True) + "\n")
        else:
            sys.stdout.write(format_fold_carry(report) + "\n")
        return 0 if report["clean"] else 2
    if as_json:
        sys.stdout.write(json.dumps(report, sort_keys=True) + "\n")
    else:
        for line in format_report(report):
            sys.stdout.write(line + "\n")
    return 0 if report["clean"] else 2


if __name__ == "__main__":
    sys.exit(main())