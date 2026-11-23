# state_fold.py - the state.json log fold as one callable, plus a --check read
# Criteria AC-SF1..AC-SF6 were pre-registered in state/queue/tech.md (R2240 b)
# BEFORE this file existed.
#
# Why this exists: the fold has been executed by hand in many windows - the
# waterline was measured by eyeballing a file size, the window was chosen by
# counting lines, and the archive append was a bespoke script each time. Each
# hand execution was a chance to cut a round line in half or to rewrite the
# archive instead of appending to it. This module owns the three decisions
# once: does the file need a fold (waterline law), what exactly moves to the
# archive (verbatim preservation plus token coverage), and how the archive
# grows (append, never rewrite).
#
# The surface is small on purpose:
#   measure(size)                      the waterline verdict
#   plan_fold(raw, state, w1, w2, s)   the fold predicate, no writes
#   append_archive(path, header, ln)    the verbatim append, byte verified
#   fold(root, ...)                     one callable: plan, back up, append, write
#   check(root)                         the read-only --check report
#
# Layout law: the live state.json is the PS 5.1 layout - one log item per
# line, indented by exactly 16 spaces, CRLF separators. A file whose layout
# does not match the parsed log length is refused rather than guessed at.
# R3208: the CRLF half of that law is now asked explicitly (E_SF_EOL) - the
# reader used to fall back to a bare-LF split, so a drifted carrier was folded
# and re-landed as LF with every gate green.
#
# Pure read in --check: nothing is written, no clock is read on that path.
# Source is pure ASCII, stdlib only, zero network imports, and the fold
# predicate is single-owned here (logs_toolkit is not imported).

import hashlib
import io
import json
import os
import re
import sys
import tempfile
from datetime import datetime

GATE = 78500

# Token family from the group ledger grammar (AC/BD/C/D/O/T/XL/OH/R).
# AC-FTOK1/2: the multi-letter families keep a loose body because none of them
# collides with English prose; the single-letter families require a DIGIT right
# after the hyphen, otherwise ordinary hyphenations (C-tier, D-copy, T-based,
# O-face, R-CHECK) are counted as ledger tokens and every fold is refused.
PAT = re.compile(r'(?:(?:AC|BD|XL|OH)-[0-9A-Za-z][0-9A-Za-z]*'
                 r'|[CDOTR]-\d[0-9A-Za-z]*)'
                 r'(?:-[0-9A-Za-z]+)*')

# Round-block boundary law (R2407). A tokens line ends a round's ledger, but a
# round may append items AFTER its ledger line (disclosures, self-heal,
# repairs), so the ledger line is not automatically the block's last line.
TOKENS_RE = re.compile(r'^R(\d{3,5}) tokens:')
ROUND_HEAD_RE = re.compile(r'^(?:\d{4}-\d{2}-\d{2}\s+)?R(\d{3,5})\b')

VERDICTS = ("FOLD-CLEAR", "FOLD-DUE")

# R3088 AC-SF7: the fold vehicle writes '# --- R<n> ...' as a window marker
# and, until now, never read the target archive before writing, so two folds
# in one round wrote two windows under one marker with nothing naming the
# collision (measured: 5 post-pin windows / 4 markers, and the R3085 repair
# folds 40 and 39-again are 2 of them). The vehicle now refuses to reuse a
# marker SILENTLY: a real re-fold says so and its reason lands verbatim in
# the header. A blanket "one round, one window" law was measured first and
# would have blocked that repair, which is why the law is "no silent
# collision" rather than "no second window".
#
# ARCHIVE_MARKER_RE is the writer's twin of ledger_lines.FOLD_MARKER_RE; the
# suite pins that both read the same marker from the same header, because a
# writer that marks windows a reader cannot see is the defect this gate
# exists to prevent.
ARCHIVE_MARKER_RE = re.compile(r"^#\s*---\s*R(\d{3,5})\b")
ROUND_LABEL_RE = re.compile(r"^R(\d{3,5})$")
# R3365 (AC-SF8, pinned in src/os/backlog.md before this edit): the header
# writes round_label verbatim, while the archive reader can only recover a
# round from two numeric shapes (R####, and the legacy bare #### read by
# logs_toolkit CEN_HDR_BARE) plus its own probe labels. The measured defect
# was a fold called with the FOLD NUMBER in the round slot - "642" - which
# round_marker() cannot order (so no collision check ran) and CEN_HDR_BARE
# cannot read (so the section landed unlabelled in the census). A writer that
# emits a header its reader cannot read is refused here, before any byte
# moves; letter-initial labels stay free because the probe path (RTEST) is a
# documented consumer of this door rather than a numeric round.
ROUND_LABEL_WRITE_RE = re.compile(r"^(?:R?\d{4,}|[A-Za-z][A-Za-z0-9_-]*)$")
REFOLD_DECL = "re-fold"

ITEM_INDENT = 16
ITEM_PREFIX = " " * ITEM_INDENT

CHECK_KEYS = ("state_path", "archive_path", "bytes", "log_lines", "gate",
              "margin", "fold_needed", "verdict", "archive_present")

PLAN_KEYS = ("window_start", "window_end", "window_lines",
             "window_content_bytes", "summary_head", "tokens_total",
             "tokens_missing", "token_ok", "gate", "reserve_bytes",
             "predicted_bytes", "margin", "gate_ok", "preop_sha16",
             "round_split", "newline", "folded_log_len")

ARCHIVE_KEYS = ("path", "created", "prefix_intact", "before_bytes",
                "before_sha16", "after_bytes", "appendix_bytes", "sha16")


class StateFoldError(Exception):
    """Raised when the fold cannot produce an honest result.

    R3189 measured that this family exited through prose only: four different
    facts (state missing, state not JSON, log not a list, window out of
    bounds) all printed one line under --json, and the --check face dropped
    the detail entirely. `stage` and `face()` give a machine caller the same
    facts the FoldRunError family publishes (AC-SFOLD11); the text face is
    unchanged.

    R3192 adds a third stage: `rolled-back` means bytes did move and were
    taken back (the appended archive block plus the backup), so `after_write`
    is False and the same window may be retried; `after-write` still means
    the half-landing is on disk and needs a human.
    """

    def __init__(self, code, detail, stage="pre-write"):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail
        self.stage = stage

    def face(self):
        return {"error": self.code, "stage": self.stage,
                "detail": self.detail,
                "after_write": self.stage == "after-write"}


def state_path(root):
    return os.path.join(root, "src", "os", "state.json")


def default_archive(root, now=None):
    stamp = (now or datetime.now()).strftime("%Y-%m")
    return os.path.join(root, "logs", "state-log-archive-%s.md" % stamp)


def measure(disk_bytes, gate=GATE):
    """Waterline law: fold_needed iff the disk size is strictly over gate."""
    margin = gate - int(disk_bytes)
    fold_needed = margin < 0
    return {
        "bytes": int(disk_bytes),
        "gate": int(gate),
        "margin": margin,
        "fold_needed": fold_needed,
        "verdict": "FOLD-DUE" if fold_needed else "FOLD-CLEAR",
    }


def read_state(path=None):
    """Read and parse the state file; fail closed on anything unexpected."""
    if path is None:
        raise StateFoldError("E_SF_BAD_ARGS", "state path is required")
    try:
        with io.open(path, "rb") as handle:
            raw = handle.read()
    except (IOError, OSError) as exc:
        raise StateFoldError("E_SF_BAD_STATE", "%s (%s)" % (path, exc))
    try:
        state = json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as exc:
        raise StateFoldError("E_SF_BAD_STATE", "%s (%s)" % (path, exc))
    log = state.get("log")
    if not isinstance(log, list) or not all(isinstance(x, str) for x in log):
        raise StateFoldError("E_SF_BAD_STATE", "%s (log is not a string list)"
                             % path)
    return raw, state


def split_layout(text, log_len):
    """Locate the log item lines in the layout the FILE ITSELF uses.

    R2522 measured a reader that insisted on a 16-space item indent while the
    shipped append path wrote 2-space items, so the fold refused the real
    file. The indent is therefore DERIVED from the first item line and every
    item must share it; a file whose items disagree with each other is refused
    rather than reformatted. Returns the split lines, the newline, the ordered
    item line indices, the first item index and the derived item prefix.
    """
    newline = "\r\n" if "\r\n" in text else "\n"
    lines = text.split(newline)
    first = None
    items = []
    prefix = None
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('"log"') and stripped.endswith("["):
            first = index
            continue
        if first is None:
            continue
        indent = line[:len(line) - len(line.lstrip(" "))]
        if indent and line[len(indent):len(indent) + 1] == '"':
            if prefix is None:
                prefix = indent
            if indent != prefix:
                return None
            items.append(index)
        elif stripped.startswith("]"):
            break
    if first is None or prefix is None or len(items) != log_len:
        return None
    return {
        "lines": lines,
        "newline": newline,
        "item_index": items,
        "first_item": items[0],
        "item_prefix": prefix,
    }


def ps_escape(value):
    """Serialize one log string in the on-disk PS 5.1 style."""
    literal = json.dumps(value, ensure_ascii=False)
    for char, escape in (("<", "\\u003c"), (">", "\\u003e"),
                         ("&", "\\u0026"), ("'", "\\u0027")):
        literal = literal.replace(char, escape)
    return literal


def round_split(window, kept):
    """The round this cut splits in half, or None.

    R2405 cut after `R2395 tokens:` and left R2395's closeout disclosures in
    the live log, so the round line survived while its ledger line moved to
    the archive - and the ledger coverage law then read R2395 as a round
    without a ledger. A cut is refused only when the LAST moved line is a
    round's own tokens line and the FIRST kept line still opens with that same
    round; prose that merely mentions the number mid-line is not a
    continuation, so this does not refuse ordinary cuts.
    """
    if not window or not kept:
        return None
    last = TOKENS_RE.match(window[-1])
    if last:
        head = ROUND_HEAD_RE.match(kept[0])
        if head and head.group(1) == last.group(1):
            return "R" + last.group(1)
    # R2829 mirror case: a cut can also leave a round's tokens line LIVE while
    # moving that round's narrative into the archive. The R2822 fold did
    # exactly this to R2815 - it cut at item 49 of the then log, one item past
    # the R2815 narrative block and one short of its ledger line - so the round
    # read as a ledger with no round and AC-LGR8/AC-LGA8/AC-LGB8/AC-FCLS6/
    # AC-LKND6/AC-LKNF6 all went red on a healthy tree. Both directions split
    # one round, so both are refused and the round is named.
    kept_head = TOKENS_RE.match(kept[0])
    if kept_head:
        round_no = kept_head.group(1)
        for line in window:
            head = ROUND_HEAD_RE.match(line)
            if (head and head.group(1) == round_no
                    and not TOKENS_RE.match(line)):
                return "R" + round_no
    return None


def archive_tokens(path):
    """Tokens already standing in the archive, read from disk (AC-FTOK6)."""
    if not path or not os.path.exists(path):
        return set()
    try:
        with io.open(path, "rb") as handle:
            text = handle.read().decode("utf-8", "replace")
    except (IOError, OSError):
        return set()
    return set(PAT.findall(text))


def plan_fold(raw, state, window_start, window_end, summary, reserve=0,
              gate=GATE, covered=()):
    """The fold predicate. Returns (plan, folded_text); writes nothing."""
    if not isinstance(summary, str) or not summary.strip():
        raise StateFoldError("E_SF_BAD_SUMMARY", "summary must be a line")
    if "\n" in summary or "\r" in summary:
        raise StateFoldError("E_SF_BAD_SUMMARY", "summary must be one line")
    log = state["log"]
    count = len(log)
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise StateFoldError("E_SF_BAD_LAYOUT", "state is not utf-8 (%s)"
                             % exc)
    # R3208: split_layout falls back to a bare-LF reading, so a carrier that
    # had already lost its CRLF was planned and re-landed as LF - measured:
    # plan_fold on an LF carrier answered newline=LF and composed 77 bare LF
    # separators with every gate green. The fold was therefore a silent
    # PROPAGATOR of the drift the closeout gate only flags at the end of the
    # round. The sibling door has refused an LF carrier since it shipped
    # (logs_toolkit prints E_STATE_LAYOUT plus the repair hint), so this door
    # now refuses it by name instead of carrying the dialect forward.
    if "\r\n" not in text:
        raise StateFoldError(
            "E_SF_EOL",
            "the carrier carries no CRLF separator, so a fold would land the "
            "same dialect back (nothing written); repair: python "
            "src/os/logs_toolkit.py eol --fix --execute")
    layout = split_layout(text, count)
    if layout is None:
        raise StateFoldError("E_SF_BAD_LAYOUT",
                             "log item lines do not match log length %d"
                             % count)
    start = int(window_start)
    end = int(window_end)
    if start < 1 or end < start or end > count:
        raise StateFoldError("E_SF_WINDOW",
                             "window %d:%d is out of log bounds 1:%d"
                             % (start, end, count))
    window = log[start - 1:end]
    tokens = set()
    for line in window:
        tokens |= set(PAT.findall(line))
    # AC-FTOK6: the fold summary is one line and cannot name hundreds of ids,
    # so a token survives either by being named in the summary OR by already
    # standing in the archive, which is the byte-verified verbatim vehicle.
    held = set(covered)
    missing = sorted(token for token in tokens
                     if token not in summary and token not in held)
    literal = layout["item_prefix"] + ps_escape(summary)
    if end < count:
        literal += ","
    drop = end - start + 1
    insert_at = layout["item_index"][start - 1]
    new_lines = (layout["lines"][:insert_at] + [literal]
                 + layout["lines"][insert_at + drop:])
    folded_text = layout["newline"].join(new_lines)
    predicted = len(folded_text.encode("utf-8"))
    new_log_len = count - drop + 1
    plan = {
        "window_start": start,
        "window_end": end,
        "window_lines": drop,
        "window_content_bytes": sum(len(line.encode("utf-8"))
                                    for line in window),
        "summary_head": summary[:60],
        "tokens_total": len(tokens),
        "tokens_missing": missing,
        "token_ok": not missing,
        "gate": int(gate),
        "reserve_bytes": int(reserve),
        "predicted_bytes": predicted,
        "margin": int(gate) - predicted,
        "gate_ok": predicted + int(reserve) <= int(gate),
        "preop_sha16": hashlib.sha256(raw).hexdigest()[:16],
        "round_split": round_split(window, log[end:]),
        "newline": "CRLF" if layout["newline"] == "\r\n" else "LF",
        "folded_log_len": new_log_len,
    }
    return plan, folded_text


def round_marker(round_label):
    """The marker round a fold label would write, or None (labels like RTEST).

    Fractional or non-numeric labels never become markers, so they are also
    invisible to the archive reader; the gate stays out of their way rather
    than inventing an ordering it cannot prove.
    """
    match = ROUND_LABEL_RE.match(round_label or "")
    return int(match.group(1)) if match is not None else None


def marker_rounds(path):
    """The marker rounds already written into ONE archive file (read-only).

    Reads header lines only, never a payload, and reads no clock. A path
    that is not a file holds no markers, which is what a first fold sees.
    """
    rounds = set()
    if not os.path.isfile(path):
        return rounds
    try:
        with io.open(path, "r", encoding="utf-8") as handle:
            for raw in handle:
                text = raw.rstrip("\n").rstrip("\r")
                if not text.startswith("# --- "):
                    continue
                match = ARCHIVE_MARKER_RE.match(text)
                if match is not None:
                    rounds.add(int(match.group(1)))
    except (IOError, OSError, UnicodeDecodeError) as exc:
        raise StateFoldError("E_SF_ARCHIVE", "%s (%s)" % (path, exc))
    return rounds


def archive_appendix(header, window_lines):
    """The exact bytes a fold contributes to the archive."""
    if not isinstance(header, str) or not header.startswith("# --- "):
        raise StateFoldError("E_SF_BAD_HEADER",
                             "header must start with '# --- '")
    if "\n" in header or "\r" in header:
        raise StateFoldError("E_SF_BAD_HEADER", "header must be one line")
    blob = header + "\n" + "\n".join(window_lines) + "\n"
    return blob.encode("utf-8")


def append_archive(path, header, window_lines, allow_create=False, now=None):
    """Append the fold block verbatim; never rewrite what is already there."""
    appendix = archive_appendix(header, window_lines)
    if os.path.isfile(path):
        with io.open(path, "rb") as handle:
            before = handle.read()
        separator = b""
        if before and not before.endswith(b"\n"):
            separator = b"\n"
        expected = before + separator + appendix
        with io.open(path, "ab") as handle:
            handle.write(separator + appendix)
        with io.open(path, "rb") as handle:
            after = handle.read()
        if after != expected:
            raise StateFoldError("E_SF_ARCHIVE",
                                 "append read-back differs from expectation",
                                 stage="after-write")
        return {
            "path": path,
            "created": False,
            "prefix_intact": after.startswith(before),
            "before_bytes": len(before),
            "after_bytes": len(after),
            "appendix_bytes": len(separator) + len(appendix),
            "before_sha16": hashlib.sha256(before).hexdigest()[:16],
            "sha16": hashlib.sha256(after).hexdigest()[:16],
        }
    if not allow_create:
        raise StateFoldError("E_SF_ARCHIVE_MISSING",
                             "%s (pass allow_create to create it)" % path)
    stamp = (now or datetime.now()).strftime("%Y-%m-%d")
    preamble = ("# logs/%s (created by state_fold.py %s)\n"
                % (os.path.basename(path), stamp)).encode("utf-8")
    blob = preamble + appendix
    with io.open(path, "wb") as handle:
        handle.write(blob)
    with io.open(path, "rb") as handle:
        if handle.read() != blob:
            raise StateFoldError("E_SF_ARCHIVE",
                                 "create read-back differs from expectation",
                                 stage="after-write")
    return {
        "path": path,
        "created": True,
        "prefix_intact": False,
        "before_bytes": 0,
        "after_bytes": len(blob),
        "appendix_bytes": len(blob),
        "before_sha16": hashlib.sha256(b"").hexdigest()[:16],
        "sha16": hashlib.sha256(blob).hexdigest()[:16],
    }


def rollback_archive(path, appended):
    """Take back the fold block that landed before the state write failed.

    R3192 measured both halves of the hole: a replace failure left the
    archive carrying the window while the state did not (the ledger face read
    7 -> 9 lines for a fold that never landed), and the retry was refused by
    E_SF_MARKER_COLLISION with no way back. Truncating to before_bytes - or
    deleting an archive this fold created - restores the exact pre-fold
    bytes, and that restoration is PROVED by before_sha16 rather than
    assumed.
    """
    if appended.get("created"):
        os.remove(path)
        return {"rolled_back": True, "how": "removed the created archive"}
    before_bytes = int(appended["before_bytes"])
    with io.open(path, "r+b") as handle:
        handle.truncate(before_bytes)
    with io.open(path, "rb") as handle:
        restored = handle.read()
    if (len(restored) != before_bytes
            or hashlib.sha256(restored).hexdigest()[:16]
            != appended.get("before_sha16")):
        raise StateFoldError("E_SF_ARCHIVE",
                             "rollback read-back differs from before_sha16",
                             stage="after-write")
    return {"rolled_back": True, "how": "truncated to before_bytes"}


def fold(root, round_label, fold_no, window_start, window_end, summary,
         reserve=0, gate=GATE, execute=True, archive_path=None, now=None,
         refold_reason=None):
    """One callable: plan the fold, back up, append the archive, write state.

    A dry run (execute=False) returns the plan and writes nothing. An
    execute run refuses before any write when the plan is not clean, and
    refuses a window marker the target archive already carries unless the
    caller declares refold_reason (AC-SF7) - a repair may open a second
    window for one round, a silent one may not.
    """
    path = state_path(root)
    if not ROUND_LABEL_WRITE_RE.match(str(round_label if round_label is not None else "")):
        raise StateFoldError(
            "E_SF_BAD_ROUND",
            "round label %r is not a shape the archive reader can read: pass "
            "R#### (or a legacy bare ####), never a fold number; the header "
            "is written verbatim and an unreadable label lands as an "
            "unlabelled section" % (round_label,))
    raw, state = read_state(path)
    cov_archive = archive_path or default_archive(root)
    covered = archive_tokens(cov_archive)
    plan, folded_text = plan_fold(raw, state, window_start, window_end,
                                  summary, reserve=reserve, gate=gate,
                                  covered=covered)
    fail = []
    if plan["tokens_missing"]:
        fail.append("token-missing")
    if plan["round_split"]:
        fail.append("round-split")
    if not plan["gate_ok"]:
        fail.append("gate-exceed")
    result = dict(plan)
    result["mode"] = "execute" if execute else "dry-run"
    result["round"] = round_label
    result["fold_no"] = fold_no
    result["would_fail"] = fail
    if not execute or fail:
        return result
    stamp = now or datetime.now()
    archive = archive_path or default_archive(root, stamp)
    reason = ""
    if refold_reason is not None:
        text = str(refold_reason).strip()
        if not text:
            raise StateFoldError("E_SF_BAD_ARGS",
                                 "refold_reason must be non-empty when given")
        reason = ", %s: %s" % (REFOLD_DECL, text)
    header = ("# --- %s fold append (%s, %d lines verbatim: %s, "
              "fold %s window, pre-op sha16 %s%s)"
              % (round_label, stamp.strftime("%Y-%m-%d"),
                 plan["window_lines"], "log window", fold_no,
                 plan["preop_sha16"], reason))
    marker = round_marker(round_label)
    if marker is not None:
        existing = marker_rounds(archive)
        if marker in existing and REFOLD_DECL not in header:
            raise StateFoldError(
                "E_SF_MARKER_COLLISION",
                "%s already carries a window marked R%d and this fold does "
                "not declare %s: <reason>"
                % (os.path.basename(archive), marker, REFOLD_DECL))
    window = state["log"][plan["window_start"] - 1:plan["window_end"]]
    backup_path = os.path.join(root, "logs",
                               "state-preop-%s.bak" % round_label)
    # R3191 measured the order this closes: the temp file used to be reserved
    # LAST, so at that moment the backup and the archive were already on disk
    # and a reservation failure left a half-landed fold behind. The
    # reservation now comes FIRST - a failure here moves no byte at all - and
    # every refusal after it removes the reserved file (AC-SFOLD13).
    try:
        fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path),
                                   prefix=".state-fold-")
        os.close(fd)
    except (IOError, OSError) as exc:
        raise StateFoldError(
            "E_SF_STATE_WRITE",
            "%s could not open a temp file (%s); nothing was written"
            % (path, exc))
    try:
        # R3189 measured an uncaught traceback here: a backup path that is a
        # directory made io.open raise IsADirectoryError, which left the CLI
        # at rc=1 with 1145 bytes of stderr and NO output under --json. Only
        # the reserved temp file exists at this point, so the honest shape is
        # a named refusal, not a crash (AC-SFOLD11 arm d).
        try:
            with io.open(backup_path, "wb") as backup:
                backup.write(raw)
        except (IOError, OSError) as exc:
            raise StateFoldError("E_SF_BACKUP",
                                 "%s (%s)" % (backup_path, exc))
        with io.open(backup_path, "rb") as backup:
            if backup.read() != raw:
                # the backup file exists now, so bytes moved even though the
                # archive and the state have not been touched.
                raise StateFoldError("E_SF_BACKUP",
                                     "backup read-back differs",
                                     stage="after-write")
        appended = append_archive(archive, header, window,
                                 allow_create=True, now=stamp)
        import general_writer_dialect_audit as GWDA
        payload = GWDA.payload_for(path, folded_text)
        # R3190 measured the crash this face replaces: a mkstemp or os.replace
        # failure escaped as a raw OSError (rc=1 with a traceback and no
        # --json face). Reservation is now pre-write; a replace failure is
        # still honestly after-write because the backup and archive have
        # landed (AC-SFOLD12 arm d proves that, AC-SFOLD13 keeps it).
        try:
            with io.open(tmp, "wb") as state_handle:
                state_handle.write(payload)
            os.replace(tmp, path)
        except (IOError, OSError) as exc:
            # R3192 measured the leftover: the archive carried the window
            # while the state did not, so the ledger face read 7 -> 9 lines
            # for a fold that never landed and the retry was refused by
            # E_SF_MARKER_COLLISION with no way back. The block this fold
            # appended is taken back here and the backup goes with it - the
            # state bytes never changed, so the backup holds no new
            # information. A rollback that itself fails is reported as the
            # half-landing it is, never as a clean refusal.
            try:
                rolled = rollback_archive(archive, appended)
            except (IOError, OSError, StateFoldError) as rb:
                raise StateFoldError(
                    "E_SF_STATE_WRITE",
                    "%s not replaced (%s); archive still carries the window "
                    "(%s); state bytes unchanged" % (path, exc, rb),
                    stage="after-write")
            backup_note = "the backup was removed"
            try:
                if os.path.exists(backup_path):
                    os.remove(backup_path)
            except OSError:
                backup_note = "the backup could not be removed"
            raise StateFoldError(
                "E_SF_STATE_WRITE",
                "%s not replaced (%s); %s and %s; state bytes unchanged, "
                "the fold did not land"
                % (path, exc, rolled["how"], backup_note),
                stage="rolled-back")
        tmp = None
    finally:
        if tmp is not None and os.path.exists(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass
    with io.open(path, "rb") as handle:
        post_raw = handle.read()
    post_state = json.loads(post_raw.decode("utf-8"))
    expected_log = (state["log"][:plan["window_start"] - 1] + [summary]
                    + state["log"][plan["window_end"]:])
    result.update({
        "backup_path": backup_path,
        "archive": appended,
        "post_bytes": len(post_raw),
        "predicted_eq_actual": (len(post_raw) == plan["predicted_bytes"]
                                and post_raw == payload
                                and post_state["log"] == expected_log),
    })
    return result


def check(root, gate=GATE):
    """The read-only waterline report behind --check."""
    path = state_path(root)
    raw, state = read_state(path)
    size = os.path.getsize(path)
    water = measure(size, gate)
    archive = default_archive(root)
    return {
        "state_path": path,
        "archive_path": archive,
        "bytes": water["bytes"],
        "log_lines": len(state["log"]),
        "gate": water["gate"],
        "margin": water["margin"],
        "fold_needed": water["fold_needed"],
        "verdict": water["verdict"],
        "archive_present": os.path.isfile(archive),
    }


def to_json(report, keys):
    ordered = {}
    for key in keys:
        ordered[key] = report[key]
    return json.dumps(ordered, ensure_ascii=True, sort_keys=False) + "\n"


def render(report):
    return ("STATE FOLD bytes=%d gate=%d margin=%d log_lines=%d verdict=%s "
            "archive=%s" % (report["bytes"], report["gate"],
                            report["margin"], report["log_lines"],
                            report["verdict"],
                            "present" if report["archive_present"]
                            else "absent"))


USAGE = ("usage: state_fold.py --check [--root PATH] [--json]\n"
         "  exit 0 = FOLD-CLEAR (disk size at or under the waterline)\n"
         "  exit 2 = FOLD-DUE (disk size over the waterline) or bad flags\n"
         "  exit 3 = the state file is missing or not readable, or another\n"
         "           StateFoldError code. With --json the refusal is a JSON\n"
         "           object carrying error, stage, detail and after_write;\n"
         "           stage is pre-write, after-write or rolled-back (R3192:\n"
         "           the appended archive block was taken back, so\n"
         "           after_write is False and a retry is allowed);\n"
         "           without --json the line is the code alone, unchanged.\n")


def main(argv):
    check_mode = False
    as_json = False
    root = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--check":
            check_mode = True
        elif arg == "--json":
            as_json = True
        elif arg == "--root":
            index += 1
            if index >= len(argv):
                sys.stdout.write("E_SF_BAD_ARGS: --root needs a path\n")
                return 2
            root = argv[index]
        elif arg in ("--help", "-h"):
            sys.stdout.write(USAGE)
            return 0
        else:
            sys.stdout.write("E_SF_BAD_ARGS: unknown flag %s\n" % arg)
            sys.stdout.write(USAGE)
            return 2
        index += 1
    if not check_mode:
        sys.stdout.write("E_SF_BAD_ARGS: --check is required\n")
        sys.stdout.write(USAGE)
        return 2
    try:
        report = check(root)
    except StateFoldError as exc:
        # R3189 (AC-SFOLD11): --json asked for a machine face, so the error
        # face is machine-readable too. The text face keeps the code-only
        # line it always printed (that contract is unchanged).
        if as_json:
            sys.stdout.write(to_json(exc.face(),
                                     ("error", "stage", "detail",
                                      "after_write")))
        else:
            sys.stdout.write("%s\n" % exc.code)
        return 3
    if as_json:
        sys.stdout.write(to_json(report, CHECK_KEYS))
    else:
        sys.stdout.write(render(report) + "\n")
    return 2 if report["fold_needed"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))