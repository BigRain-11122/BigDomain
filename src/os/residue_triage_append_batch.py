# residue_triage_append_batch.py - SEVERAL dated triage entries in one write
# Criteria AC-RTAB1..AC-RTAB6 were pre-registered inside the R2355 seed row of
# state/queue/tech.md BEFORE this file existed.
#
# Why this exists: residue_triage_append accepts exactly ONE entry and then
# requires the file to re-read TRIAGED, so a fold that creates two or more
# residue rounds at once (measured at R2355: fold 640 created R2345, R2346 and
# R2348 in one pass) could not go through the shipped channel and was spliced
# by a one-off script. This module is that missing capability and nothing else:
#
#   * the declaration reader, the status vocabulary, the shape check and the
#     judge all stay owned by residue_triage (RT.load_declaration,
#     RT.live_residue, RT.shape, RT.judge are imported, never re-derived), and
#     the entry layout is residue_triage_append's own renderer (RNA.entry_text),
#     so this file carries no second parser and no second formatter;
#   * every pair is validated BEFORE a byte moves: a round already declared
#     refuses naming the existing entry, a round repeated inside the same call
#     refuses, a round the live reader does not carry refuses, and a status
#     that disagrees with the live reading refuses naming BOTH statuses;
#   * the file is judged BEFORE the write - if the reader would still carry
#     residue after these entries the call refuses and names the rounds, which
#     is the whole point of batching;
#   * the write is ONE atomic replace whose predicted size is proved and whose
#     entries are re-read one by one, leaving no .tmp residue behind;
#   * exit 0 only when the file re-reads TRIAGED, 2 on a refusal over live
#     state, 3 on unreadable input, 5 on bad flags (AC-RTAB4);
#   * pure ASCII source, stdlib only, zero network, no clock (AC-RTAB6).
#
# The single-entry CLI is untouched: residue_triage_append keeps its own file,
# its own codes and its own suite (AC-RTAB5).

import json
import os
import sys

import residue_triage as RT
import residue_triage_append as RNA

DECLARATION_PATH = RT.DECLARATION_PATH

SUITE_LABEL = "os-residue-triage-append-batch"

REPORT_KEYS = (
    "action",
    "rounds",
    "statuses",
    "declared_by",
    "until",
    "before_bytes",
    "after_bytes",
    "delta",
    "entries_before",
    "entries_after",
    "residue",
    "declaration",
    "verdict",
    "wrote",
)

UNREADABLE_CODES = (
    "E_RTAB_UNREADABLE",
    "E_RTAB_UNPINNED",
    "E_RTAB_BAD_SHAPE",
    "E_RTAB_BAD_STATUS",
    "E_RTAB_BAD_STATE",
    "E_RTAB_READBACK",
)


class ResidueTriageAppendBatchError(Exception):
    """A refusal carrying its own code."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def _round(value, origin):
    """One round reference, parsed by the reader's own law (AC-RTAB6)."""
    try:
        return RT.parse_round(value, origin)
    except RT.ResidueTriageError as exc:
        raise ResidueTriageAppendBatchError(
            "E_RTAB_BAD_ARGS", "%s: %s" % (origin, exc.detail or exc.code))


def _declaration(root):
    """The pinned declaration, read by residue_triage (AC-RTAB1)."""
    try:
        declaration = RT.load_declaration(root)
    except RT.ResidueTriageError as exc:
        raise ResidueTriageAppendBatchError(
            "E_RTAB_UNREADABLE", "%s: %s" % (exc.code, exc.detail))
    if declaration is None:
        raise ResidueTriageAppendBatchError(
            "E_RTAB_UNPINNED",
            "no %s to append to; pin one with the triage writer first"
            % DECLARATION_PATH.replace(os.sep, "/"))
    return declaration


def _live(root):
    """The live residue, read by stamp_residue through residue_triage."""
    try:
        rows = RT.live_residue(root)
    except RT.ResidueTriageError as exc:
        raise ResidueTriageAppendBatchError(
            "E_RTAB_BAD_STATE", "%s: %s" % (exc.code, exc.detail))
    status = {}
    for row in rows:
        status[int(row["round"])] = row["status"]
    return status


def compose(before_text, entries):
    """Splice several entries into the array, leaving every other byte."""
    if not before_text.endswith(RNA.CLOSER):
        raise ResidueTriageAppendBatchError(
            "E_RTAB_BAD_SHAPE",
            "the declaration does not end with the pinned layout")
    cut = len(before_text) - len(RNA.CLOSER)
    body = before_text[:cut].rstrip()
    if body.endswith("}"):
        prefix = body + ",\n"
    else:
        prefix = body + "\n"
    rendered = ",\n".join(RNA.entry_text(entry) for entry in entries)
    return prefix + rendered + before_text[cut:]


def plan(root, pairs, declared_by, reason, until):
    """Everything except the write: refusals, candidates, predicted bytes."""
    by = _round(declared_by, "declared_by")
    until_round = _round(until, "until")
    if until_round < by:
        raise ResidueTriageAppendBatchError(
            "E_RTAB_UNTIL_BEFORE_DECL",
            "until R%d is earlier than declared_by R%d" % (until_round, by))
    if not isinstance(reason, str) or not reason.strip():
        raise ResidueTriageAppendBatchError(
            "E_RTAB_BAD_SHAPE", "reason must be a non-empty string")
    if not pairs:
        raise ResidueTriageAppendBatchError(
            "E_RTAB_BAD_ARGS", "at least one round/status pair is required")

    numbers = []
    statuses = []
    for position, pair in enumerate(pairs, start=1):
        if not isinstance(pair, (tuple, list)) or len(pair) != 2:
            raise ResidueTriageAppendBatchError(
                "E_RTAB_BAD_ARGS",
                "pair %d must be a (round, status) couple" % position)
        number = _round(pair[0], "pair %d round" % position)
        status = pair[1]
        if not isinstance(status, str) or not status.strip():
            raise ResidueTriageAppendBatchError(
                "E_RTAB_BAD_SHAPE",
                "pair %d status must be a non-empty string" % position)
        if number in numbers:
            raise ResidueTriageAppendBatchError(
                "E_RTAB_DUPLICATE",
                "R%d appears twice in the same call" % number)
        numbers.append(number)
        statuses.append(status)

    declaration = _declaration(root)
    existing = {}
    for item in declaration["entries"]:
        existing[item["round"]] = item
    for number in numbers:
        if number in existing:
            old = existing[number]
            raise ResidueTriageAppendBatchError(
                "E_RTAB_DUPLICATE",
                "R%d is already declared status=%s declared_by=R%d until=R%d"
                % (number, old["status"], old["declared_by"], old["until"]))

    live = _live(root)
    for number, status in zip(numbers, statuses):
        if number not in live:
            raise ResidueTriageAppendBatchError(
                "E_RTAB_NOT_RESIDUE",
                "R%d is not in the live residue (%d rounds are)"
                % (number, len(live)))
        if live[number] != status:
            raise ResidueTriageAppendBatchError(
                "E_RTAB_DISAGREES",
                "R%d declares %s while the live reader reports %s"
                % (number, status, live[number]))

    entries = []
    for number, status in zip(numbers, statuses):
        entries.append({
            "round": number,
            "status": status,
            "declared_by": by,
            "reason": reason,
            "until": until_round,
        })

    raw_entries = []
    for item in declaration["entries"]:
        raw_entries.append({
            "round": "R%d" % item["round"],
            "status": item["status"],
            "declared_by": "R%d" % item["declared_by"],
            "reason": item["reason"],
            "until": "R%d" % item["until"],
        })
    for entry in entries:
        raw_entries.append({
            "round": "R%d" % entry["round"],
            "status": entry["status"],
            "declared_by": "R%d" % entry["declared_by"],
            "reason": entry["reason"],
            "until": "R%d" % entry["until"],
        })
    try:
        candidate = RT.shape({
            "declared_by": "R%d" % declaration["declared_by"],
            "reason": declaration["reason"],
            "entries": raw_entries,
        }, "candidate declaration")
    except RT.ResidueTriageError as exc:
        raise ResidueTriageAppendBatchError(
            "E_RTAB_BAD_STATUS" if exc.code == "E_RTR_BAD_STATUS"
            else "E_RTAB_BAD_SHAPE",
            "%s: %s" % (exc.code, exc.detail))

    live_rows = [{"round": key, "status": live[key]}
                 for key in sorted(live)]
    judged = RT.judge(candidate["entries"], live_rows, by)
    if judged["residue"]:
        raise ResidueTriageAppendBatchError(
            "E_RTAB_NOT_TRIAGED",
            "after R%d the reader would still carry %d untriaged round(s): %s"
            % (by, len(judged["residue"]),
               ", ".join("R%d" % value for value in judged["residue"][:5])))

    path = os.path.join(root, DECLARATION_PATH)
    try:
        with open(path, "rb") as handle:
            raw_bytes = handle.read()
    except (IOError, OSError) as exc:
        raise ResidueTriageAppendBatchError("E_RTAB_UNREADABLE", str(exc))
    try:
        before_text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ResidueTriageAppendBatchError("E_RTAB_UNREADABLE", str(exc))
    after_text = compose(before_text, entries)
    after_bytes = after_text.encode("utf-8")
    return {
        "entries": entries,
        "path": path,
        "after_bytes": after_bytes,
        "before_bytes": len(raw_bytes),
        "delta": len(after_bytes) - len(raw_bytes),
        "entries_before": len(declaration["entries"]),
        "entries_after": len(declaration["entries"]) + len(entries),
    }


def apply(root, prepared):
    """One atomic replace, then a read-back through the reader (AC-RTAB3)."""
    path = prepared["path"]
    payload = prepared["after_bytes"]
    temp = path + ".tmp-rtab"
    try:
        with open(temp, "wb") as handle:
            handle.write(payload)
        os.replace(temp, path)
    except (IOError, OSError) as exc:
        try:
            os.remove(temp)
        except (IOError, OSError):
            pass
        raise ResidueTriageAppendBatchError("E_RTAB_READBACK", str(exc))
    try:
        size = os.path.getsize(path)
    except (IOError, OSError) as exc:
        raise ResidueTriageAppendBatchError("E_RTAB_READBACK", str(exc))
    if size != prepared["before_bytes"] + prepared["delta"]:
        raise ResidueTriageAppendBatchError(
            "E_RTAB_READBACK",
            "predicted %d bytes, the file measures %d"
            % (prepared["before_bytes"] + prepared["delta"], size))
    if os.path.exists(temp):
        raise ResidueTriageAppendBatchError(
            "E_RTAB_READBACK", "the temp file survived the replace")
    reread = _declaration(root)
    found = {}
    for item in reread["entries"]:
        found[item["round"]] = item
    for entry in prepared["entries"]:
        if found.get(entry["round"]) != entry:
            raise ResidueTriageAppendBatchError(
                "E_RTAB_READBACK",
                "R%d does not re-read as written: %r"
                % (entry["round"], found.get(entry["round"])))
    if len(reread["entries"]) != prepared["entries_after"]:
        raise ResidueTriageAppendBatchError(
            "E_RTAB_READBACK",
            "entry count re-read as %d, predicted %d"
            % (len(reread["entries"]), prepared["entries_after"]))
    try:
        report = RT.read(root, "R%d" % prepared["entries"][0]["declared_by"])
    except RT.ResidueTriageError as exc:
        raise ResidueTriageAppendBatchError(
            "E_RTAB_READBACK", "%s: %s" % (exc.code, exc.detail))
    if report["verdict"] != "TRIAGED":
        raise ResidueTriageAppendBatchError(
            "E_RTAB_NOT_TRIAGED",
            "the file re-reads %s with %d untriaged round(s)"
            % (report["verdict"], report["untriaged"]))
    return report


def check(root, round_value):
    """The read-only face: what would a batch have to accept?"""
    current = _round(round_value, "round")
    try:
        report = RT.read(root, "R%d" % current)
    except RT.ResidueTriageError as exc:
        code = "E_RTAB_UNREADABLE"
        if exc.code in ("E_RTR_BAD_ARGS",):
            code = "E_RTAB_BAD_ARGS"
        elif exc.code in ("E_RTR_BAD_STATE",):
            code = "E_RTAB_BAD_STATE"
        raise ResidueTriageAppendBatchError(
            code, "%s: %s" % (exc.code, exc.detail))
    # The live status of every residue round is the status face's reading
    # (AC-RSBF2), imported at CALL time so this module still loads without it
    # and the --append path never reaches it (AC-RSBF4).
    import residue_batch_status_face as RSBF
    try:
        face = RSBF.face(root)
    except RSBF.ResidueBatchStatusFaceError as exc:
        raise ResidueTriageAppendBatchError(
            "E_RTAB_BAD_STATE", "%s: %s" % (exc.code, exc.detail))
    return {
        "action": "check",
        "rounds": list(face["rounds"]),
        "statuses": list(face["statuses"]),
        "declared_by": "-" if report["declared_by"] is None
        else report["declared_by"],
        "until": "-",
        "before_bytes": 0,
        "after_bytes": 0,
        "delta": 0,
        "entries_before": len(report["entries"]),
        "entries_after": len(report["entries"]),
        "residue": list(report["residue"]),
        "declaration": report["declaration"],
        "verdict": report["verdict"],
        "wrote": False,
    }


def one_line(report):
    """The single line an operator reads."""
    rounds = ",".join(report["rounds"]) or "-"
    statuses = ",".join(report["statuses"]) or "-"
    residue = ",".join("R%d" % value for value in report["residue"]) or "-"
    return ("RESIDUE TRIAGE APPEND BATCH action=%s rounds=%s statuses=%s "
            "declared_by=%s until=%s entries=%d->%d bytes=%d->%d delta=%d "
            "residue=%s declaration=%s verdict=%s wrote=%s"
            % (report["action"], rounds, statuses, report["declared_by"],
               report["until"], report["entries_before"],
               report["entries_after"], report["before_bytes"],
               report["after_bytes"], report["delta"], residue,
               report["declaration"], report["verdict"],
               "yes" if report["wrote"] else "no"))


def render(report):
    """The one line, then every round still awaiting an entry."""
    out = [one_line(report)]
    for index, label in enumerate(report["rounds"]):
        out.append("  ROUND %s status=%s"
                   % (label, report["statuses"][index]))
    for value in report["residue"]:
        out.append("  RESIDUE R%d has no dated entry yet" % value)
    return "\n".join(out)


def to_json(report):
    """Serialise in the pinned key order only (byte-stable)."""
    ordered = {}
    for key in REPORT_KEYS:
        ordered[key] = report[key]
    return json.dumps(ordered, ensure_ascii=True, sort_keys=False) + "\n"


USAGE = ("usage: residue_triage_append_batch.py --append --pair R<n>=STATUS\n"
         "         [--pair R<n>=STATUS ...] --by R<n> --reason TEXT\n"
         "         --until R<n> [--dry-run] [--root PATH] [--json]\n"
         "       residue_triage_append_batch.py --check --round R<n>\n"
         "         [--root PATH] [--json]\n"
         "  exit 0 = every pair was written and the file re-reads TRIAGED\n"
         "           (or, for --check, no live residue round is undeclared)\n"
         "  exit 2 = refused over live state (duplicate, disagrees, not in\n"
         "           the residue, until before declared_by, still untriaged)\n"
         "  exit 3 = unreadable or unpinned declaration, bad shape\n"
         "  exit 5 = bad flags\n")


def parse_pair(text, position):
    """`R<n>=STATUS` as a couple, refused rather than guessed."""
    if "=" not in text:
        raise ResidueTriageAppendBatchError(
            "E_RTAB_BAD_ARGS",
            "pair %d must read R<n>=STATUS, not %r" % (position, text))
    head, status = text.split("=", 1)
    if not head.strip():
        raise ResidueTriageAppendBatchError(
            "E_RTAB_BAD_ARGS", "pair %d carries no round" % position)
    return head.strip(), status.strip()


def main(argv):
    mode = None
    as_json = False
    dry_run = False
    round_text = None
    pairs = []
    by = None
    reason = None
    until = None
    root = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg in ("--check", "--append"):
            if mode is not None and mode != arg[2:]:
                sys.stdout.write("E_RTAB_BAD_ARGS: --check and --append are "
                                 "mutually exclusive\n")
                sys.stdout.write(USAGE)
                return 5
            mode = arg[2:]
        elif arg == "--json":
            as_json = True
        elif arg == "--dry-run":
            dry_run = True
        elif arg in ("--round", "--pair", "--by", "--reason", "--until",
                     "--root"):
            index += 1
            if index >= len(argv):
                sys.stdout.write("E_RTAB_BAD_ARGS: %s needs a value\n" % arg)
                sys.stdout.write(USAGE)
                return 5
            value = argv[index]
            if arg == "--round":
                round_text = value
            elif arg == "--pair":
                pairs.append(value)
            elif arg == "--by":
                by = value
            elif arg == "--reason":
                reason = value
            elif arg == "--until":
                until = value
            else:
                root = value
        elif arg in ("--help", "-h"):
            sys.stdout.write(USAGE)
            return 0
        else:
            sys.stdout.write("E_RTAB_BAD_ARGS: unknown flag %s\n" % arg)
            sys.stdout.write(USAGE)
            return 5
        index += 1

    if mode is None:
        sys.stdout.write("E_RTAB_BAD_ARGS: --check or --append is required\n")
        sys.stdout.write(USAGE)
        return 5
    if mode == "check" and round_text is None:
        sys.stdout.write("E_RTAB_BAD_ARGS: --check needs --round\n")
        sys.stdout.write(USAGE)
        return 5
    if mode == "append":
        missing = [flag for flag, value in (("--by", by),
                                            ("--reason", reason),
                                            ("--until", until))
                   if value is None]
        if not pairs:
            missing.insert(0, "--pair")
        if missing:
            sys.stdout.write("E_RTAB_BAD_ARGS: --append needs %s\n"
                             % ", ".join(missing))
            sys.stdout.write(USAGE)
            return 5

    try:
        if mode == "check":
            report = check(root, round_text)
        else:
            couples = []
            for position, text in enumerate(pairs, start=1):
                couples.append(parse_pair(text, position))
            prepared = plan(root, couples, by, reason, until)
            runtime = [("R%d" % entry["round"], entry["status"])
                       for entry in prepared["entries"]]
            if dry_run:
                report = {
                    "action": "dry-run",
                    "rounds": [value[0] for value in runtime],
                    "statuses": [value[1] for value in runtime],
                    "declared_by": "R%s" % by.lstrip("R"),
                    "until": "R%s" % until.lstrip("R"),
                    "before_bytes": prepared["before_bytes"],
                    "after_bytes": prepared["before_bytes"]
                    + prepared["delta"],
                    "delta": prepared["delta"],
                    "entries_before": prepared["entries_before"],
                    "entries_after": prepared["entries_after"],
                    "residue": [],
                    "declaration": "PINNED",
                    "verdict": "DRY-RUN",
                    "wrote": False,
                }
            else:
                reread = apply(root, prepared)
                report = {
                    "action": "append",
                    "rounds": [value[0] for value in runtime],
                    "statuses": [value[1] for value in runtime],
                    "declared_by": "R%s" % by.lstrip("R"),
                    "until": "R%s" % until.lstrip("R"),
                    "before_bytes": prepared["before_bytes"],
                    "after_bytes": prepared["before_bytes"]
                    + prepared["delta"],
                    "delta": prepared["delta"],
                    "entries_before": prepared["entries_before"],
                    "entries_after": prepared["entries_after"],
                    "residue": list(reread["residue"]),
                    "declaration": reread["declaration"],
                    "verdict": reread["verdict"],
                    "wrote": True,
                }
    except ResidueTriageAppendBatchError as exc:
        sys.stdout.write("%s\n" % exc.code)
        if exc.detail:
            sys.stdout.write("  %s\n" % exc.detail)
        if exc.code == "E_RTAB_BAD_ARGS":
            return 5
        if exc.code in UNREADABLE_CODES:
            return 3
        return 2

    if as_json:
        sys.stdout.write(to_json(report))
    else:
        sys.stdout.write(render(report) + "\n")
    if report["action"] == "dry-run":
        return 0
    if report["verdict"] == "TRIAGED":
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))