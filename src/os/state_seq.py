# state_seq.py - does the round sequence in the log agree with itself?
# Criteria AC-SEQ1..AC-SEQ6 were pinned in state/queue/tech.md as the R2248-d
# seed row BEFORE this file existed (claim note added by R2257).
# Anchor check at HEAD 2026-10-29: "E_SEQ" / "os-state-seq" / "test_state_seq"
# were git grep -F zero-occupancy rc=1; "state_seq" and "AC-SEQ" hit only the
# R2248 seed generator, the R2248 backlog row and the row text itself.
#
# Why this exists: the tick climbs every window and every window writes a log
# item labelled with its own round, but nothing compared the two. A window
# that reuses a round label, or one whose label goes backwards, or a stretch
# of rounds that simply never happened, was invisible - the log looked the
# same either way. This reader makes the sequence a visible object.
#
# Three deliberate narrowings:
#   * The owning label of a log item is the round_evidence law imported, not
#     re-implemented. A body mention of an older round ("the R2168 mixed-tree
#     rule") invents no label, exactly as it obliges no evidence file.
#   * A gap is only measured between the smallest and the largest distinct
#     label. Nothing is reported before the first or after the last round,
#     because those are unknown rather than absent.
#   * Repeat and backwards are separate readings. A round written twice in a
#     row is a repeat; a label smaller than its predecessor is backwards.
#
# Pure read: nothing is written, no clock is read, no network import.
# Source is pure ASCII, stdlib only.

import io
import json
import os
import re
import sys

import round_evidence

# A done stamp in a queue row: "[done 2026-10-29 R2255]".
DONE_STAMP_RE = re.compile(r"\[done\s+\d{4}-\d{2}-\d{2}\s+R(\d{3,5})\]")

QUEUE_DIR = ("state", "queue")

VERDICTS = ("EMPTY", "SEQUENCE-OK", "SEQUENCE-BROKEN")

REPEAT_KEYS = ("round", "count")

BACKWARDS_KEYS = ("index", "round", "previous")

REPORT_KEYS = (
    "labels",
    "distinct",
    "smallest",
    "largest",
    "tick",
    "tick_lead",
    "gaps",
    "repeats",
    "backwards",
    "queue_done",
    "queue_only",
    "verdict",
)


class StateSeqError(Exception):
    """Raised when the reader cannot produce an honest reading."""

    def __init__(self, code, detail):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def load_state(root):
    """Read state.json; fail closed rather than fabricating a tick."""
    path = os.path.join(root, "src", "os", "state.json")
    try:
        with io.open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except (IOError, OSError, ValueError) as exc:
        raise StateSeqError("E_SEQ_BAD_STATE", "%s (%s)" % (path, exc))


def read_tick(state):
    """The tick as an int, or fail closed (AC-SEQ1)."""
    if not isinstance(state, dict):
        raise StateSeqError("E_SEQ_BAD_STATE", "state is not an object")
    tick = state.get("tick")
    if isinstance(tick, bool) or not isinstance(tick, int):
        raise StateSeqError("E_SEQ_BAD_STATE",
                            "tick is %r, not an int" % (tick,))
    return tick


def extract_labels(state):
    """Every log item's own round label, in log order (AC-SEQ2)."""
    log = state.get("log")
    if not isinstance(log, list):
        raise StateSeqError("E_SEQ_BAD_STATE", "log is not a list")
    labels = []
    for raw in log:
        if not isinstance(raw, str):
            raise StateSeqError("E_SEQ_BAD_STATE", "log item is not text")
        number = round_evidence.item_round(raw)
        if number is None:
            continue
        labels.append(number)
    return labels


def find_gaps(labels):
    """Numbers absent between the smallest and largest distinct label."""
    if not labels:
        return []
    seen = set(labels)
    low = min(seen)
    high = max(seen)
    return [number for number in range(low, high + 1) if number not in seen]


def find_repeats(labels):
    """Labels reused in more than one contiguous block, first-seen order.

    A round legitimately writes several log items in a row (its narrative,
    its ledger line, its self-heal note), so "written more than once" would
    flag every round. A repeat is a label that comes back after a DIFFERENT
    round has intervened - the sequence then carries two blocks bearing the
    same number, which is what makes a stitched or mislabelled round
    invisible. Corrected at R2257 after the live reading flagged 15 of 15
    rounds; the criteria row records the correction.
    """
    blocks = {}
    order = []
    previous = None
    for number in labels:
        if number != previous:
            if number not in blocks:
                blocks[number] = 0
                order.append(number)
            blocks[number] += 1
        previous = number
    out = []
    for number in order:
        if blocks[number] > 1:
            out.append({"round": number, "count": blocks[number]})
    return out


def find_backwards(labels):
    """Labels smaller than their predecessor, with both sides named."""
    out = []
    previous = None
    for index, number in enumerate(labels):
        if previous is not None and number < previous:
            out.append({"index": index, "round": number,
                        "previous": previous})
        previous = number
    return out


def queue_done_rounds(root):
    """Round labels carried by queue done stamps, sorted ascending."""
    directory = os.path.join(root, *QUEUE_DIR)
    if not os.path.isdir(directory):
        return []
    found = set()
    try:
        names = sorted(os.listdir(directory))
    except (IOError, OSError) as exc:
        raise StateSeqError("E_SEQ_BAD_QUEUE", "%s (%s)" % (directory, exc))
    for name in names:
        if not name.endswith(".md"):
            continue
        path = os.path.join(directory, name)
        try:
            with io.open(path, "r", encoding="utf-8") as handle:
                text = handle.read()
        except (IOError, OSError, ValueError) as exc:
            raise StateSeqError("E_SEQ_BAD_QUEUE", "%s (%s)" % (path, exc))
        for match in DONE_STAMP_RE.finditer(text):
            found.add(int(match.group(1)))
    return sorted(found)


def audit(root):
    """Audit the sequence; return the closed report shape."""
    state = load_state(root)
    tick = read_tick(state)
    labels = extract_labels(state)
    distinct = sorted(set(labels))
    gaps = find_gaps(labels)
    repeats = find_repeats(labels)
    backwards = find_backwards(labels)
    done = queue_done_rounds(root)
    logged = set(labels)
    queue_only = [number for number in done if number not in logged]
    if not labels:
        verdict = "EMPTY"
    elif gaps or repeats or backwards:
        verdict = "SEQUENCE-BROKEN"
    else:
        verdict = "SEQUENCE-OK"
    if distinct:
        largest = distinct[-1]
        tick_lead = tick - largest
    else:
        largest = None
        tick_lead = None
    return {
        "labels": labels,
        "distinct": len(distinct),
        "smallest": distinct[0] if distinct else None,
        "largest": largest,
        "tick": tick,
        "tick_lead": tick_lead,
        "gaps": gaps,
        "repeats": repeats,
        "backwards": backwards,
        "queue_done": len(done),
        "queue_only": queue_only,
        "verdict": verdict,
    }


def one_line(report):
    """The single line an operator reads."""
    return ("STATE SEQUENCE labels=%d distinct=%d span=%s..%s gaps=%d "
            "repeats=%d backwards=%d tick=%d tick_lead=%s queue_done=%d "
            "queue_only=%d verdict=%s"
            % (len(report["labels"]), report["distinct"],
               report["smallest"], report["largest"], len(report["gaps"]),
               len(report["repeats"]), len(report["backwards"]),
               report["tick"], report["tick_lead"], report["queue_done"],
               len(report["queue_only"]), report["verdict"]))


def render(report):
    """Full text rendering: the one line, then every defect named."""
    out = [one_line(report)]
    for number in report["gaps"]:
        out.append("  GAP R%d" % number)
    for item in report["repeats"]:
        out.append("  REPEAT R%d count=%d" % (item["round"], item["count"]))
    for item in report["backwards"]:
        out.append("  BACKWARDS index=%d R%d after R%d"
                   % (item["index"], item["round"], item["previous"]))
    for number in report["queue_only"]:
        out.append("  QUEUE-ONLY R%d" % number)
    return "\n".join(out)


def to_json(report):
    """Serialise in a stable key order (no indent, ASCII, one trailing LF)."""
    ordered = {}
    for key in REPORT_KEYS:
        ordered[key] = report[key]
    pinned_repeats = []
    for item in report["repeats"]:
        row = {}
        for key in REPEAT_KEYS:
            row[key] = item[key]
        pinned_repeats.append(row)
    ordered["repeats"] = pinned_repeats
    pinned_backwards = []
    for item in report["backwards"]:
        row = {}
        for key in BACKWARDS_KEYS:
            row[key] = item[key]
        pinned_backwards.append(row)
    ordered["backwards"] = pinned_backwards
    return json.dumps(ordered, ensure_ascii=True, sort_keys=False) + "\n"


USAGE = ("usage: state_seq.py --check [--root PATH] [--json]\n"
         "  exit 0 = the round sequence is SEQUENCE-OK (or honestly EMPTY)\n"
         "  exit 2 = SEQUENCE-BROKEN (gap, repeat or backwards) or bad "
         "flags\n"
         "  exit 3 = state.json or a queue file is missing or unparseable\n")


def main(argv):
    check = False
    as_json = False
    root = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
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
                sys.stdout.write("E_SEQ_BAD_ARGS: --root needs a path\n")
                return 2
            root = argv[index]
        elif arg in ("--help", "-h"):
            sys.stdout.write(USAGE)
            return 0
        else:
            sys.stdout.write("E_SEQ_BAD_ARGS: unknown flag %s\n" % arg)
            sys.stdout.write(USAGE)
            return 2
        index += 1
    if not check:
        sys.stdout.write("E_SEQ_BAD_ARGS: --check is required\n")
        sys.stdout.write(USAGE)
        return 2
    try:
        report = audit(root)
    except StateSeqError as exc:
        sys.stdout.write("%s\n" % exc.code)
        return 3
    if as_json:
        sys.stdout.write(to_json(report))
    else:
        sys.stdout.write(render(report) + "\n")
    if report["verdict"] == "SEQUENCE-BROKEN":
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))