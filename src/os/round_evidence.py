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


def audit(root, qa_dir=None):
    """Audit the claim-to-file link; return the closed report shape."""
    if qa_dir is None:
        qa_dir = os.path.join(root, "qa")
    state = load_state(root)
    rounds = extract_rounds(state)
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
        "log_items": len(state.get("log") or []),
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
         "[--json]\n"
         "  exit 0 = every claiming round has a qa/ file (or the log is "
         "empty)\n"
         "  exit 2 = a claiming round has no file (EVIDENCE-MISSING) or "
         "bad flags\n"
         "  exit 3 = state.json is missing or unparseable\n")


def main(argv):
    check = False
    as_json = False
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
    if not check:
        sys.stdout.write("E_RQE_BAD_ARGS: --check is required\n")
        sys.stdout.write(USAGE)
        return 2
    try:
        report = audit(root, qa_dir)
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