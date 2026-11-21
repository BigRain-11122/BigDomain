# round_evidence.py - does every round that claims evidence actually have a file?
# Criteria AC-RQE1..AC-RQE6 were pinned in state/queue/tech.md as the R2248-c
# seed row BEFORE this file existed (pre-registration note added by R2255).
# Disclosed prefix substitution: the seed suggested AC-REV, but that prefix is
# already occupied across a thousand hits by the AC-REVM / AC-REVW / AC-REV1
# families shipped by other suites, so a fresh non-colliding AC-RQE prefix was
# registered instead. "AC-RQE" / "round_evidence" / "E_RQE" were git grep -F
# zero-occupancy against HEAD 2026-10-29 rc=1 outside the seed row text.
#
# Why this exists: a round writes "SUITE PASS" into its own log item in
# state.json and the file that proves it lives in qa/ under a round-suffixed
# name, but until now the link between the two was only the prose. A window
# could claim a passing suite and no file would exist, and nothing would say
# so. This reader closes that gap: it extracts the round each log item
# belongs to, maps every qa/ file name to the round token it carries, and
# reports the claiming rounds that have no file at all.
#
# Three deliberate narrowings:
#   * A round label is only the item's OWN label (the "YYYY-MM-DD R<n>" or
#     "R<n> tokens:" prefix), never a round merely mentioned in the body -
#     the body routinely names older rounds ("the R2168 mixed-tree rule")
#     and counting those as rounds would invent evidence obligations.
#   * A round token in a file name must not be a fragment of a longer number,
#     so R2254 never borrows the file of R22541.
#   * Claim markers are pinned, not guessed: "SUITE PASS" and "RUNNER PASS".
#     A round that makes no such claim owes no file and is not reported.
#
# Pure read: nothing is written, no clock is read, no network import.
# Source is pure ASCII, stdlib only.

import io
import json
import os
import re
import sys

# The owning round of a log item, if it has one.
ROUND_LABEL_RE = re.compile(r"^(?:\d{4}-\d{2}-\d{2}\s+)?R(\d{3,5})\b")

# A round token inside a qa/ file name; never a fragment of a longer number.
FILE_ROUND_RE = re.compile(r"(?<![0-9A-Za-z])R(\d{3,5})(?![0-9])")

# A round claims evidence only through these markers (AC-RQE3).
CLAIM_MARKERS = ("SUITE PASS", "RUNNER PASS")

# R3164 (AC-RQE7): the fold moves a round's log items OUT of the live log and
# into logs/state-log-archive-*.md, and this reader judged only the live log,
# so every folded round left its judgement without a word. Measured live at
# R3164: 1939 labelled rounds, 374 with no qa/ file, and ALL 374 are
# archive-only - the live log carries none - of which 82 claim a pass. The
# folder and prefix below are the fold's own names, mirrored from state_seq
# (which imports this module, so the dependency cannot run the other way);
# AC-RQE7 arm f asserts the two modules still agree rather than trusting it.
ARCHIVE_DIR = ("logs",)
ARCHIVE_PREFIX = "state-log-archive-"

# R3165 (AC-RQE8): a claiming round with no file of its OWN NAME may still
# name a qa/ file inside its own log line. Measured live at R3165 over the 82
# folded claiming rounds: 44 name at least one on-disk qa/ path and 42 of
# those files carry a pinned marker - but the names almost always carry
# ANOTHER round's token (29 rounds) or none at all (15 rounds, nine of them
# sharing qa/reconcile-daily-20261006.log), so a named file is not this
# round's evidence. The claim-to-file verdict is therefore left untouched and
# this reading only publishes the third state for an operator to act on.
NAMED_PATH_RE = re.compile(r"qa/[A-Za-z0-9][A-Za-z0-9._\-]*")

# R3166 (AC-RQE9): `no_named` mixed two worlds - a round that named nothing
# at all and a round that named something the reader could not resolve. A
# measurement over the ten such rounds (tmp/probe_R3166.py) found ZERO names
# that exist under docs/ or logs/ (the wrong-prefix hypothesis), so no
# DANGLE/PREFIX split is added here; what is published instead is the token
# list of a round that named something and resolved nothing. Bare file names
# and the leg-/runner- families are read for this READING ONLY: they never
# enter `named`, never move a verdict, and a file on disk outside qa/ does
# not count (AC-RQE9 e).
OFFQA_BARE_RE = re.compile(
    r"(?<![A-Za-z0-9._/\-])([A-Za-z0-9][A-Za-z0-9._\-]*"
    r"\.(?:log|json|md|png|txt))")
OFFQA_FAMILY_RE = re.compile(
    r"(?<![A-Za-z0-9._/\-])((?:leg|runner)-[A-Za-z0-9._\-]+)")

OFFQA_ROW_KEYS = ("round", "tokens")

# R3167 (AC-RQE10): the OFFQA tokens are names the reader could not resolve,
# and an operator could not tell a near miss (a longer qa/ file name holding
# the token) from a narrative word. Measured at R3167 over the same ten rounds
# and thirteen tokens: 4 are near misses and only 1 of those has a single
# candidate, so a candidate is a CANDIDATE and never evidence - the face
# publishes the count and a resume file only when the count is exactly one.
RESOLVE_EXTENSIONS = (".log", ".json", ".md", ".png", ".txt")

RESOLVE_TOKEN_KEYS = ("token", "hits", "resume")

RESOLVE_ROW_KEYS = ("round", "tokens")

REPORT_RESOLVE_KEYS = (
    "offqa_rounds",
    "tokens_total",
    "near_tokens",
    "unique_tokens",
    "multi_tokens",
    "unresolved_tokens",
    "rows",
    "verdict",
)

RESOLVE_VERDICT = "RESOLVABLE-READING"

NAMED_VERDICT = "NAMED-READING"

NAMED_ROW_KEYS = ("round", "files", "pass")

REPORT_NAMED_KEYS = (
    "rounds_missing",
    "named_on_disk",
    "named_pass",
    "named_no_pass",
    "no_named",
    "named_offqa",
    "silent",
    "named",
    "offqa",
    "verdict",
)

VERDICTS = ("EMPTY", "EVIDENCE-OK", "EVIDENCE-MISSING")

ROUND_KEYS = ("round", "items", "markers", "claims")

MISSING_KEYS = ("round", "markers")

REPORT_KEYS = (
    "rounds",
    "log_items",
    "claiming_rounds",
    "with_files",
    "files_total",
    "missing_count",
    "missing",
    "verdict",
)


class RoundEvidenceError(Exception):
    """Raised when the reader cannot produce an honest reading."""

    def __init__(self, code, detail):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def load_state(root):
    """Read state.json; fail closed rather than fabricating rounds."""
    path = os.path.join(root, "src", "os", "state.json")
    try:
        with io.open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except (IOError, OSError, ValueError) as exc:
        raise RoundEvidenceError("E_RQE_BAD_STATE", "%s (%s)" % (path, exc))


def item_round(text):
    """The round label this log item owns, or None (AC-RQE1)."""
    match = ROUND_LABEL_RE.match(text.strip())
    if not match:
        return None
    return int(match.group(1))


def item_markers(text):
    """The pinned claim markers this item carries, in pinned order."""
    found = []
    for marker in CLAIM_MARKERS:
        if marker in text:
            found.append(marker)
    return found


def extract_rounds(state):
    """Every round the log names as its own, oldest first (AC-RQE1)."""
    log = state.get("log")
    if not isinstance(log, list):
        raise RoundEvidenceError("E_RQE_BAD_STATE", "log is not a list")
    order = []
    seen = {}
    for raw in log:
        if not isinstance(raw, str):
            raise RoundEvidenceError("E_RQE_BAD_STATE", "log item is not text")
        number = item_round(raw)
        if number is None:
            continue
        if number not in seen:
            seen[number] = {"round": number, "items": 0, "markers": [],
                            "claims": False}
            order.append(number)
        row = seen[number]
        row["items"] += 1
        for marker in item_markers(raw):
            if marker not in row["markers"]:
                row["markers"].append(marker)
        if row["markers"]:
            row["claims"] = True
    return [seen[number] for number in order]


def file_round(name):
    """The round token in a qa/ file name, or None (AC-RQE2)."""
    match = FILE_ROUND_RE.search(name)
    if not match:
        return None
    return int(match.group(1))


def map_files(qa_dir):
    """Map each round to the file names that carry it (AC-RQE2)."""
    if not os.path.isdir(qa_dir):
        return {}
    mapping = {}
    try:
        names = sorted(os.listdir(qa_dir))
    except (IOError, OSError) as exc:
        raise RoundEvidenceError("E_RQE_BAD_QA", "%s (%s)" % (qa_dir, exc))
    for name in names:
        full = os.path.join(qa_dir, name)
        if not os.path.isfile(full):
            continue
        number = file_round(name)
        if number is None:
            continue
        mapping.setdefault(number, []).append(name)
    return mapping


def archive_lines(root):
    """Every line the fold archive holds, in file and line order (AC-RQE7).

    A missing directory reads nothing rather than raising (the same tolerance
    state_seq applies); an unreadable file fails closed like archive_rounds.
    """
    directory = os.path.join(root, *ARCHIVE_DIR)
    if not os.path.isdir(directory):
        return []
    try:
        names = sorted(os.listdir(directory))
    except (IOError, OSError) as exc:
        raise RoundEvidenceError("E_RQE_BAD_ARCHIVE",
                                 "%s (%s)" % (directory, exc))
    lines = []
    for name in names:
        if not (name.startswith(ARCHIVE_PREFIX) and name.endswith(".md")):
            continue
        path = os.path.join(directory, name)
        try:
            with io.open(path, "r", encoding="utf-8") as handle:
                text = handle.read()
        except (IOError, OSError, ValueError) as exc:
            raise RoundEvidenceError("E_RQE_BAD_ARCHIVE",
                                     "%s (%s)" % (path, exc))
        lines.extend(text.split("\n"))
    return lines


def archive_rounds(root):
    """Every round the fold archive labels, and the items it holds (AC-RQE7).

    The owning label is the same `item_round` law the live log uses, and the
    claim markers are the same pinned pair, so a folded round is read exactly
    as it would have been before the fold.
    """
    order = []
    seen = {}
    for line in archive_lines(root):
        number = item_round(line)
        if number is None:
            continue
        if number not in seen:
            seen[number] = {"round": number, "items": 0, "markers": [],
                            "claims": False}
            order.append(number)
        row = seen[number]
        row["items"] += 1
        for marker in item_markers(line):
            if marker not in row["markers"]:
                row["markers"].append(marker)
        if row["markers"]:
            row["claims"] = True
    return [seen[number] for number in order]


def audit(root, qa_dir=None, include_archive=False):
    """Audit the claim-to-file link; return the closed report shape.

    With include_archive the judged universe is the LIVE log plus the fold
    archive, merged per round (items summed, markers unioned) and ordered by
    round number, so a folded claim is judged instead of silently leaving the
    face. The default reads the live log only, byte-identical to before.
    """
    if qa_dir is None:
        qa_dir = os.path.join(root, "qa")
    state = load_state(root)
    rounds = extract_rounds(state)
    log_items = len(state.get("log") or [])
    if include_archive:
        folded = archive_rounds(root)
        merged = {}
        for row in rounds + folded:
            key = row["round"]
            if key not in merged:
                merged[key] = {"round": key, "items": 0, "markers": [],
                               "claims": False}
            target = merged[key]
            target["items"] += row["items"]
            for marker in row["markers"]:
                if marker not in target["markers"]:
                    target["markers"].append(marker)
            target["claims"] = bool(target["markers"])
        rounds = [merged[key] for key in sorted(merged)]
        for row in folded:
            log_items += row["items"]
    mapping = map_files(qa_dir)
    files_total = 0
    for names in mapping.values():
        files_total += len(names)
    claiming = 0
    with_files = 0
    missing = []
    for row in rounds:
        if not row["claims"]:
            continue
        claiming += 1
        if mapping.get(row["round"]):
            with_files += 1
        else:
            missing.append({"round": row["round"],
                            "markers": row["markers"]})
    if not rounds:
        verdict = "EMPTY"
    elif missing:
        verdict = "EVIDENCE-MISSING"
    else:
        verdict = "EVIDENCE-OK"
    return {
        "rounds": rounds,
        "log_items": log_items,
        "claiming_rounds": claiming,
        "with_files": with_files,
        "files_total": files_total,
        "missing_count": len(missing),
        "missing": missing,
        "verdict": verdict,
    }


def one_line(report):
    """The single line an operator reads."""
    return ("ROUND EVIDENCE rounds=%d claiming=%d with_files=%d missing=%d "
            "files=%d verdict=%s"
            % (len(report["rounds"]), report["claiming_rounds"],
               report["with_files"], report["missing_count"],
               report["files_total"], report["verdict"]))


def named_paths(text):
    """The qa/ paths an item names, in first-occurrence order (AC-RQE8)."""
    found = []
    for match in NAMED_PATH_RE.findall(text):
        if match not in found:
            found.append(match)
    return found


def carries_marker(path):
    """Does the file's own text carry a pinned claim marker? (AC-RQE8 b)."""
    try:
        with io.open(path, "r", encoding="utf-8", errors="replace") as handle:
            text = handle.read()
    except (IOError, OSError, ValueError):
        return False
    return any(marker in text for marker in CLAIM_MARKERS)


def offqa_names(text):
    """Every evidence-shaped name an item points at (AC-RQE9 b).

    The order is first occurrence; a qa/ path is kept verbatim so the caller
    can tell an explicit folder from a bare name. This is a READING of what
    the prose points at, not a claim about whether the round owes a file.
    """
    found = []
    for token in named_paths(text):
        if token not in found:
            found.append(token)
    for token in OFFQA_BARE_RE.findall(text):
        if token not in found:
            found.append(token)
    for token in OFFQA_FAMILY_RE.findall(text):
        if token not in found:
            found.append(token)
    return found


def named_evidence(root, qa_dir=None, include_archive=False):
    """The third state: did a missing round name an on-disk qa/ file?

    The judged universe is the audit's own `missing` set - this reading adds
    no round and never moves the claim-to-file verdict (AC-RQE8 a, d). Only a
    path that starts with qa/ and resolves to a file on disk is counted; a
    missing target or a name outside qa/ is no evidence at all (AC-RQE8 c).
    A named file proves nothing about the claim on its own, so the face says
    what was named and whether the file carries a marker, and stops there.
    """
    report = audit(root, qa_dir, include_archive)
    if qa_dir is None:
        qa_dir = os.path.join(root, "qa")
    missing = set(row["round"] for row in report["missing"])
    lines_by_round = {}
    state = load_state(root)
    for raw in state.get("log") or []:
        if not isinstance(raw, str):
            continue
        number = item_round(raw)
        if number in missing:
            lines_by_round.setdefault(number, []).append(raw)
    if include_archive:
        for line in archive_lines(root):
            number = item_round(line)
            if number in missing:
                lines_by_round.setdefault(number, []).append(line)
    rows = []
    for number in sorted(missing):
        names = []
        passes = False
        for line in lines_by_round.get(number, []):
            for token in named_paths(line):
                leaf = token.split("/", 1)[1]
                if leaf in names:
                    continue
                path = os.path.join(qa_dir, leaf)
                if not os.path.isfile(path):
                    continue
                names.append(leaf)
                if carries_marker(path):
                    passes = True
        if names:
            rows.append({"round": number, "files": names, "pass": passes})
    named_pass = 0
    for row in rows:
        if row["pass"]:
            named_pass += 1
    # AC-RQE9 a/b: split the no-evidence bucket. A round that is absent from
    # `named` either pointed at names it could not resolve (offqa) or named
    # nothing at all (silent); no_named keeps its shipped meaning.
    named_rounds = set(row["round"] for row in rows)
    offqa = []
    silent = 0
    for number in sorted(missing):
        if number in named_rounds:
            continue
        tokens = []
        for line in lines_by_round.get(number, []):
            for token in offqa_names(line):
                if token not in tokens:
                    tokens.append(token)
        if tokens:
            offqa.append({"round": number, "tokens": tokens})
        else:
            silent += 1
    return {
        "rounds_missing": len(missing),
        "named_on_disk": len(rows),
        "named_pass": named_pass,
        "named_no_pass": len(rows) - named_pass,
        "no_named": len(missing) - len(rows),
        "named_offqa": len(offqa),
        "silent": silent,
        "named": rows,
        "offqa": offqa,
        "verdict": NAMED_VERDICT,
    }


def render_named(report):
    """The named-evidence face: one summary line, then every named round."""
    out = [("ROUND NAMED EVIDENCE missing=%d named_on_disk=%d named_pass=%d "
            "named_no_pass=%d no_named=%d offqa=%d silent=%d verdict=%s")
           % (report["rounds_missing"], report["named_on_disk"],
              report["named_pass"], report["named_no_pass"],
              report["no_named"], report["named_offqa"], report["silent"],
              report["verdict"])]
    for row in report["named"]:
        out.append("  NAMED R%d files=%s pass=%s"
                   % (row["round"], ",".join(row["files"]),
                      "yes" if row["pass"] else "no"))
    for row in report["offqa"]:
        out.append("  OFFQA R%d tokens=%s"
                   % (row["round"], ",".join(row["tokens"])))
    return "\n".join(out)


def to_json_named(report):
    """Serialise the named reading in a stable key order (AC-RQE8 e)."""
    pinned_rows = []
    for row in report["named"]:
        item = {}
        for key in NAMED_ROW_KEYS:
            item[key] = row[key]
        pinned_rows.append(item)
    offqa_rows = []
    for row in report["offqa"]:
        item = {}
        for key in OFFQA_ROW_KEYS:
            item[key] = row[key]
        offqa_rows.append(item)
    ordered = {}
    for key in REPORT_NAMED_KEYS:
        if key == "named":
            ordered[key] = pinned_rows
        elif key == "offqa":
            ordered[key] = offqa_rows
        else:
            ordered[key] = report[key]
    return json.dumps(ordered, ensure_ascii=True, sort_keys=False) + "\n"


def split_extension(name):
    """Split a known evidence extension off a name (AC-RQE10 c)."""
    for ext in RESOLVE_EXTENSIONS:
        if name.endswith(ext) and len(name) > len(ext):
            return name[:-len(ext)], ext
    return name, ""


def stem_carries(stem, target):
    """Does `stem` carry `target` at a boundary, never inside a number run?

    The boundary test is what keeps R1992.log from matching R19920.log while
    still matching reconcile-all-R1992.log (AC-RQE10 c).
    """
    start = stem.find(target)
    while start >= 0:
        before = stem[start - 1] if start > 0 else ""
        after = stem[start + len(target):]
        if (before == "" or not before.isalnum()) and \
                (after == "" or not after[0].isdigit()):
            return True
        start = stem.find(target, start + 1)
    return False


def near_candidates(token, qa_names):
    """The qa/ files a token could be a near miss of, bounded (AC-RQE10 c).

    A token carrying a known extension matches a file of the same extension
    whose stem carries the token's stem at a boundary; a bare or family token
    matches a file whose name starts with it and continues with - _ or . .
    A qa/ path is never near-scanned: it is here only because that file is
    absent, so it is unresolved by construction (AC-RQE10 b).
    """
    token = token.strip()
    hits = []
    if token.startswith("qa/"):
        return hits
    stem, ext = split_extension(token)
    for name in qa_names:
        if name == token:
            hits.append(name)
            continue
        if ext:
            name_stem, name_ext = split_extension(name)
            if name_ext != ext:
                continue
            if stem_carries(name_stem, stem):
                hits.append(name)
        elif name.startswith(token) and len(name) > len(token):
            if name[len(token)] in "-_.":
                hits.append(name)
    return hits


def resolvable_evidence(root, qa_dir=None, include_archive=False):
    """How many qa/ candidates each unresolvable token has (AC-RQE10).

    The universe is named_evidence's own `offqa` rows, so this reading adds
    no round and never moves the claim-to-file verdict (arm a, d). A count is
    published, a resume file only when the count is exactly one, and the
    summary carries unique/multi/unresolved so the face says how far a token
    is from being evidence rather than implying it is.
    """
    reading = named_evidence(root, qa_dir, include_archive)
    if qa_dir is None:
        qa_dir = os.path.join(root, "qa")
    qa_names = []
    if os.path.isdir(qa_dir):
        try:
            qa_names = sorted(name for name in os.listdir(qa_dir)
                              if os.path.isfile(os.path.join(qa_dir, name)))
        except (IOError, OSError) as exc:
            raise RoundEvidenceError("E_RQE_BAD_QA", "%s (%s)" % (qa_dir, exc))
    rows = []
    tokens_total = 0
    near = 0
    unique = 0
    for row in reading["offqa"]:
        parts = []
        for token in row["tokens"]:
            tokens_total += 1
            hits = near_candidates(token, qa_names)
            if hits:
                near += 1
                if len(hits) == 1:
                    unique += 1
            parts.append({"token": token, "hits": len(hits),
                          "resume": hits[0] if len(hits) == 1 else ""})
        rows.append({"round": row["round"], "tokens": parts})
    return {
        "offqa_rounds": len(rows),
        "tokens_total": tokens_total,
        "near_tokens": near,
        "unique_tokens": unique,
        "multi_tokens": near - unique,
        "unresolved_tokens": tokens_total - near,
        "rows": rows,
        "verdict": RESOLVE_VERDICT,
    }


def render_resolve(report):
    """The resolution face: one summary line, then every offqa round."""
    out = [("ROUND TOKEN RESOLUTION offqa_rounds=%d tokens=%d near=%d "
            "unique=%d multi=%d unresolved=%d verdict=%s")
           % (report["offqa_rounds"], report["tokens_total"],
              report["near_tokens"], report["unique_tokens"],
              report["multi_tokens"], report["unresolved_tokens"],
              report["verdict"])]
    for row in report["rows"]:
        parts = []
        for item in row["tokens"]:
            text = "%s(%d)" % (item["token"], item["hits"])
            if item["resume"]:
                text += "=" + item["resume"]
            parts.append(text)
        out.append("  RES R%d tokens=%s" % (row["round"], ",".join(parts)))
    return "\n".join(out)


def to_json_resolve(report):
    """Serialise the resolution reading in a stable key order (AC-RQE10 e)."""
    pinned_rows = []
    for row in report["rows"]:
        item = {}
        for key in RESOLVE_ROW_KEYS:
            if key == "tokens":
                tokens = []
                for part in row["tokens"]:
                    piece = {}
                    for name in RESOLVE_TOKEN_KEYS:
                        piece[name] = part[name]
                    tokens.append(piece)
                item[key] = tokens
            else:
                item[key] = row[key]
        pinned_rows.append(item)
    ordered = {}
    for key in REPORT_RESOLVE_KEYS:
        if key == "rows":
            ordered[key] = pinned_rows
        else:
            ordered[key] = report[key]
    return json.dumps(ordered, ensure_ascii=True, sort_keys=False) + "\n"


def render(report):
    """Full text rendering: the one line, then every missing round."""
    out = [one_line(report)]
    for item in report["missing"]:
        out.append("  MISSING R%d markers=%s"
                   % (item["round"], ",".join(item["markers"])))
    return "\n".join(out)


def to_json(report):
    """Serialise in a stable key order (no indent, ASCII, one trailing LF)."""
    ordered = {}
    for key in REPORT_KEYS:
        ordered[key] = report[key]
    pinned_rounds = []
    for row in report["rounds"]:
        item = {}
        for key in ROUND_KEYS:
            item[key] = row[key]
        pinned_rounds.append(item)
    ordered["rounds"] = pinned_rounds
    pinned_missing = []
    for bad in report["missing"]:
        item = {}
        for key in MISSING_KEYS:
            item[key] = bad[key]
        pinned_missing.append(item)
    ordered["missing"] = pinned_missing
    return json.dumps(ordered, ensure_ascii=True, sort_keys=False) + "\n"


USAGE = ("usage: round_evidence.py --check [--root PATH] [--qa-dir PATH] "
         "[--archive] [--json]\n"
         "       round_evidence.py --named [--root PATH] [--qa-dir PATH] "
         "[--archive] [--json]\n"
         "       round_evidence.py --resolvable [--root PATH] [--qa-dir PATH] "
         "[--archive] [--json]\n"
         "  --archive also judges the rounds folded into logs/ (AC-RQE7)\n"
         "  --named reads, for every missing round, the qa/ files its own\n"
         "          lines name (AC-RQE8); it never changes the verdict\n"
         "  --resolvable reads, for every unresolvable name, how many qa/\n"
         "          candidates it has (AC-RQE10); never evidence, never a\n"
         "          verdict move\n"
         "  exit 0 = every claiming round has a qa/ file (or the log is "
         "empty)\n"
         "  exit 2 = a claiming round has no file (EVIDENCE-MISSING) or "
         "bad flags\n"
         "  exit 3 = state.json is missing or unparseable\n")


def main(argv):
    check = False
    as_json = False
    include_archive = False
    named = False
    resolvable = False
    root = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    qa_dir = None
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--check":
            check = True
        elif arg == "--json":
            as_json = True
        elif arg == "--archive":
            include_archive = True
        elif arg == "--named":
            named = True
        elif arg == "--resolvable":
            resolvable = True
        elif arg == "--root":
            index += 1
            if index >= len(argv):
                sys.stdout.write("E_RQE_BAD_ARGS: --root needs a path\n")
                return 2
            root = argv[index]
        elif arg == "--qa-dir":
            index += 1
            if index >= len(argv):
                sys.stdout.write("E_RQE_BAD_ARGS: --qa-dir needs a path\n")
                return 2
            qa_dir = argv[index]
        elif arg in ("--help", "-h"):
            sys.stdout.write(USAGE)
            return 0
        else:
            sys.stdout.write("E_RQE_BAD_ARGS: unknown flag %s\n" % arg)
            sys.stdout.write(USAGE)
            return 2
        index += 1
    if named:
        try:
            reading = named_evidence(root, qa_dir, include_archive)
        except RoundEvidenceError as exc:
            sys.stdout.write("%s\n" % exc.code)
            return 3
        if as_json:
            sys.stdout.write(to_json_named(reading))
        else:
            sys.stdout.write(render_named(reading) + "\n")
        return 0
    if resolvable:
        try:
            reading = resolvable_evidence(root, qa_dir, include_archive)
        except RoundEvidenceError as exc:
            sys.stdout.write("%s\n" % exc.code)
            return 3
        if as_json:
            sys.stdout.write(to_json_resolve(reading))
        else:
            sys.stdout.write(render_resolve(reading) + "\n")
        return 0
    if not check:
        sys.stdout.write("E_RQE_BAD_ARGS: --check is required\n")
        sys.stdout.write(USAGE)
        return 2
    try:
        report = audit(root, qa_dir, include_archive)
    except RoundEvidenceError as exc:
        sys.stdout.write("%s\n" % exc.code)
        return 3
    if as_json:
        sys.stdout.write(to_json(report))
    else:
        sys.stdout.write(render(report) + "\n")
    if report["verdict"] == "EVIDENCE-MISSING":
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))