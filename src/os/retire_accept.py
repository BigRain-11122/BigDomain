# retire_accept.py - an accepted retirement is recorded, and kept honest
# Criteria AC-RAC1..AC-RAC6 were pre-registered in state/queue/tech.md (the
# R2331 seed row) BEFORE this file existed.
#
# Why this exists: retire_candidate names the copies that are safe to retire
# (live: six RETIRE-READY), but nothing can ACT on that reading. The resolver
# is read-only by contract and deleting a file is irreversible, so every
# window re-derives the same six and either does nothing or hand-deletes one.
# A hand deletion leaves no record of WHEN it became safe, WHY, or until when
# the judgement was meant to hold.
#
# This module is that record, and nothing else. It pins one acceptance
# declaration (state/queue/retire_accept.json) and reads it back against the
# live resolver, so an entry can never quietly outlive its truth:
#   * the per-script verdicts come from retire_candidate (imported, never
#     re-derived - a patched resolver flows straight through, AC-RAC1);
#   * every entry lands in exactly ONE class (AC-RAC2):
#       ACCEPTED        the live resolver still reads RETIRE-READY and the
#                       entry has not aged out
#       EXPIRED         the entry carries an `until` round earlier than the
#                       current round, and is reported with that round
#       UNMATCHED       the live resolver has no row for the script at all
#       STALE-DECISION  the script reads OWNED again, with the current blocker
#                       named - an acceptance whose fact changed must be red
#                       rather than counted
#     Precedence is pinned and documented: the two integrity classes outrank
#     expiry, because an expired acceptance whose script became owned still
#     has a blocker someone has to work. Within integrity, "no row at all"
#     outranks "owned", because a vanished script is a different fact.
#   * a missing declaration reads UNPINNED with the full live candidate list
#     instead of a fabricated green (AC-RAC3);
#   * appending refuses a duplicate script and an `until` earlier than its own
#     declaring round, and an executed accept is one atomic replace proved by
#     a read-back, leaving every other entry byte-identical (AC-RAC4).
#
# This module NEVER deletes, moves or runs anything: the acceptance is a
# decision with a window, and acting on it is a separate, auditable step.
# Stdlib only, ASCII source, zero network, no clock.

import io
import json
import os
import sys

import retire_candidate as RC

DECL_REL = "state/queue/retire_accept.json"
STATE_REL = "src/os/state.json"
DIR = "src/os"

TEMP_SUFFIX = ".rac-tmp"

ACCEPTED = "ACCEPTED"
EXPIRED = "EXPIRED"
UNMATCHED = "UNMATCHED"
STALE = "STALE-DECISION"
CLASSES = (ACCEPTED, EXPIRED, UNMATCHED, STALE)

ENTRY_KEYS = ("script", "declared", "reason", "until")

REPORT_KEYS = ("decl", "pinned", "round", "entries", "accepted", "expired",
               "unmatched", "stale_decision", "pending", "candidates",
               "rows", "pending_scripts", "verdict")

PLAN_KEYS = ("path", "script", "declared", "reason", "until", "entry_index",
             "entry_count_before", "entry_count_after", "before_bytes",
             "predicted_bytes", "wrote", "read_back_ok")

USAGE = ("usage: retire_accept.py [--check] [--round R<nnnn>] [--root PATH]\n"
         "       [--json]\n"
         "       retire_accept.py --accept SCRIPT --declared R<nnnn>\n"
         "       --reason TEXT [--until R<nnnn>] [--execute] [--json]\n"
         "exit 0 = pinned and no entry reads UNMATCHED or STALE-DECISION,\n"
         "2 = unpinned or a defective entry, 3 = unreadable input,\n"
         "5 = bad flags\n")


class RetireAcceptError(Exception):
    """A refused reading: the code names why, the detail names the input."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, code)
        self.code = code
        self.detail = detail


def norm(name):
    """One script name form, so a declaration is portable across layouts."""
    return str(name or "").replace("\\", "/").strip()


def parse_round(text, code="E_RAC_BAD_ROUND"):
    """'R2333' -> 2333. Anything else refuses instead of guessing."""
    if not isinstance(text, str):
        raise RetireAcceptError(code, "round is %r" % (text,))
    body = text.strip()
    if not body.startswith("R") or len(body) < 5 or not body[1:].isdigit():
        raise RetireAcceptError(code, "not a round: %r" % (text,))
    return int(body[1:])


def render_entry(script, declared, reason, until=None):
    """The one entry shape this declaration carries."""
    name = norm(script)
    if not name:
        raise RetireAcceptError("E_RAC_BAD_ENTRY", "script is empty")
    if not str(reason or "").strip():
        raise RetireAcceptError("E_RAC_BAD_ENTRY", "reason is empty")
    parse_round(declared, "E_RAC_BAD_ENTRY")
    if until is not None:
        parse_round(until, "E_RAC_BAD_ENTRY")
    return {"script": name, "declared": declared.strip(),
            "reason": str(reason).strip(),
            "until": until.strip() if until else None}


def _validate_entries(entries):
    """Every entry must carry the pinned shape; refuse the whole file if not."""
    clean = []
    for index, entry in enumerate(entries, 1):
        if not isinstance(entry, dict):
            raise RetireAcceptError("E_RAC_BAD_DECL",
                                    "entry %d is not an object" % index)
        missing = [key for key in ("script", "declared", "reason")
                   if not entry.get(key)]
        if missing:
            raise RetireAcceptError(
                "E_RAC_BAD_DECL",
                "entry %d is missing %s" % (index, ",".join(missing)))
        parse_round(entry.get("declared"), "E_RAC_BAD_DECL")
        if entry.get("until") is not None:
            parse_round(entry.get("until"), "E_RAC_BAD_DECL")
        clean.append({"script": norm(entry.get("script")),
                      "declared": str(entry.get("declared")).strip(),
                      "reason": str(entry.get("reason")).strip(),
                      "until": (str(entry["until"]).strip()
                                if entry.get("until") else None)})
    seen = set()
    for entry in clean:
        if entry["script"] in seen:
            raise RetireAcceptError("E_RAC_BAD_DECL",
                                    "duplicate script %s" % entry["script"])
        seen.add(entry["script"])
    return clean


def declaration_entries(text):
    """The entries of a declaration TEXT, validated by the pinned shape."""
    try:
        data = json.loads(text)
    except ValueError as exc:
        raise RetireAcceptError("E_RAC_BAD_DECL", "not JSON (%s)" % (exc,))
    if not isinstance(data, dict):
        raise RetireAcceptError("E_RAC_BAD_DECL", "declaration is not an object")
    entries = data.get("entries")
    if not isinstance(entries, list):
        raise RetireAcceptError("E_RAC_BAD_DECL",
                                "declaration carries no entries list")
    return _validate_entries(entries)


def read_declaration(root):
    """Read the pinned declaration; absent means UNPINNED (AC-RAC3)."""
    path = os.path.join(root, DECL_REL)
    if not os.path.isfile(path):
        raise RetireAcceptError(
            "E_RAC_UNPINNED",
            "no acceptance declaration at %s" % DECL_REL.replace(os.sep, "/"))
    try:
        with io.open(path, "r", encoding="utf-8") as handle:
            text = handle.read()
    except (IOError, OSError, UnicodeDecodeError) as exc:
        raise RetireAcceptError("E_RAC_BAD_DECL", "%s (%s)" % (path, exc))
    entries = declaration_entries(text)
    try:
        declared_by = json.loads(text).get("declared_by") or ""
    except ValueError:
        declared_by = ""
    return {"path": DECL_REL.replace(os.sep, "/"), "declared_by": declared_by,
            "entries": entries}


def live_report(root):
    """The live candidate reading, asked of its own resolver (AC-RAC1)."""
    try:
        report = RC.resolve(root, DIR)
    except RC.RetireError as exc:
        raise RetireAcceptError("E_RAC_NO_INPUT",
                                "%s %s" % (exc.code, exc.detail))
    except Exception as exc:  # noqa: BLE001 - an unreadable pile is not clean
        raise RetireAcceptError("E_RAC_NO_INPUT",
                                "%s (%s)" % (type(exc).__name__, exc))
    if not isinstance(report, dict) or not isinstance(report.get("rows"), list):
        raise RetireAcceptError("E_RAC_NO_INPUT",
                                "resolver returned %r"
                                % (type(report).__name__,))
    return report


def live_index(report):
    """Per normalised script name: the resolver's own row."""
    return dict((norm(row.get("script")), row)
                for row in report.get("rows") or [])


def current_round(root):
    """The live round, taken from the house state counter rather than a clock.

    state.json's tick counts COMPLETED rounds, so the round being worked is
    tick + 1. No clock is read, so two readings a minute apart agree.
    """
    path = os.path.join(root, STATE_REL)
    try:
        with io.open(path, "r", encoding="utf-8") as handle:
            state = json.load(handle)
        tick = int(state.get("tick"))
    except (IOError, OSError, ValueError, TypeError, AttributeError) as exc:
        raise RetireAcceptError("E_RAC_NO_ROUND", "%s (%s)" % (path, exc))
    return tick + 1


def judge(entries, live, round_no):
    """One class per entry, over the pinned precedence. Pure."""
    rows = []
    for entry in entries:
        name = norm(entry.get("script"))
        row = live.get(name)
        if row is None:
            klass, detail, verdict = UNMATCHED, "NO-LIVE-ROW", "ABSENT"
        elif row.get("verdict") != RC.READY:
            reason = row.get("reason") or "UNKNOWN"
            extra = row.get("detail") or ""
            klass = STALE
            detail = (reason + " " + extra).strip()
            verdict = row.get("verdict") or ""
        elif entry.get("until") and parse_round(entry["until"]) < round_no:
            klass, detail, verdict = EXPIRED, "until %s" % entry["until"], \
                row.get("verdict") or ""
        else:
            klass, detail, verdict = ACCEPTED, "", row.get("verdict") or ""
        rows.append({"script": name, "class": klass,
                     "declared": entry.get("declared"),
                     "until": entry.get("until") or "",
                     "reason": entry.get("reason") or "",
                     "live_verdict": verdict, "detail": detail})
    accepted = [row for row in rows if row["class"] == ACCEPTED]
    expired = [row for row in rows if row["class"] == EXPIRED]
    unmatched = [row for row in rows if row["class"] == UNMATCHED]
    stale = [row for row in rows if row["class"] == STALE]
    accepted_names = set(row["script"] for row in rows)
    pending = sorted(name for name, row in live.items()
                     if row.get("verdict") == RC.READY
                     and name not in accepted_names)
    return {"entries": len(rows),
            "accepted": len(accepted),
            "expired": len(expired),
            "unmatched": len(unmatched),
            "stale_decision": len(stale),
            "pending": len(pending),
            "rows": rows,
            "pending_scripts": pending}


def check(root, round_no=None):
    """The whole reading: declaration in, classified entries out."""
    if round_no is None:
        round_no = current_round(root)
    live = live_report(root)
    index = live_index(live)
    report = {"decl": DECL_REL.replace(os.sep, "/"), "pinned": False,
              "round": "R%d" % round_no,
              "candidates": live.get("retire_ready", 0)}
    try:
        declaration = read_declaration(root)
    except RetireAcceptError as exc:
        if exc.code != "E_RAC_UNPINNED":
            raise
        report.update({"entries": 0, "accepted": 0, "expired": 0,
                       "unmatched": 0, "stale_decision": 0,
                       "pending": live.get("retire_ready", 0),
                       "rows": [],
                       "pending_scripts": sorted(
                           name for name, row in index.items()
                           if row.get("verdict") == RC.READY),
                       "verdict": "UNPINNED"})
        return report
    report["pinned"] = True
    report["declared_by"] = declaration.get("declared_by", "")
    report.update(judge(declaration["entries"], index, round_no))
    report["verdict"] = ("DEFECTS"
                         if report["unmatched"] or report["stale_decision"]
                         else "PINNED")
    return report


def render(report):
    """One header line plus one line per accepted entry, for a human."""
    parts = ["RETIRE ACCEPT decl=%s pinned=%s round=%s entries=%d "
             "accepted=%d expired=%d unmatched=%d stale_decision=%d "
             "pending=%d candidates=%d verdict=%s"
             % (report["decl"], "yes" if report["pinned"] else "no",
                report["round"], report["entries"], report["accepted"],
                report["expired"], report["unmatched"],
                report["stale_decision"], report["pending"],
                report["candidates"], report["verdict"])]
    for row in report["rows"]:
        parts.append("ROW %s %s declared=%s until=%s live=%s detail=%s"
                     % (row["script"], row["class"], row["declared"] or "-",
                        row["until"] or "-", row["live_verdict"] or "-",
                        row["detail"] or "-"))
    for name in report["pending_scripts"] or []:
        parts.append("PENDING %s %s" % (name, RC.READY))
    return "\n".join(parts)


def to_json(report):
    """One byte-stable rendering over the pinned keys, in pinned order."""
    ordered = {}
    for key in REPORT_KEYS + ("declared_by",):
        if key in report:
            ordered[key] = report[key]
    return json.dumps(ordered, ensure_ascii=True, indent=2,
                      sort_keys=False) + "\n"


def splice(text, entry):
    """Insert one entry before the closing bracket, keeping every prior byte."""
    line = json.dumps(entry, ensure_ascii=True, sort_keys=False)
    marker = "\n  ]"
    pos = text.rfind(marker)
    if pos < 0:
        raise RetireAcceptError("E_RAC_BAD_DECL",
                                "declaration carries no closing bracket")
    head = text[:pos]
    separator = "\n    " if head.rstrip().endswith("[") else ",\n    "
    return head + separator + line + text[pos:]


def _same_entry(reading, entry):
    for key in ENTRY_KEYS:
        if reading.get(key) != entry.get(key):
            return False
    return True


def payload_bytes(raw, post):
    """The bytes to land: the shared dialect law, asked at CALL time.

    Imported here rather than at module level because AC-RAC6 pins this
    module's top-level import set; the import is still resolved per call, so
    a patched law moves this writer's bytes (AC-LDWS2).
    """
    import declaration_writer_dialect_preservation as DWD
    return DWD.encode(raw, post)[1]


def plan(text, entry, live, raw=None):
    """Validate the entry and the post text; return the report and the post."""
    entries = declaration_entries(text)
    name = entry["script"]
    for existing in entries:
        if existing["script"] == name:
            raise RetireAcceptError("E_RAC_DUP", "%s is already declared"
                                    % name)
    if entry.get("until"):
        if parse_round(entry["until"]) < parse_round(entry["declared"]):
            raise RetireAcceptError(
                "E_RAC_UNTIL",
                "until %s is earlier than declared %s"
                % (entry["until"], entry["declared"]))
    row = live.get(name)
    if row is None:
        raise RetireAcceptError("E_RAC_NOT_READY",
                                "%s has no live row" % name)
    if row.get("verdict") != RC.READY:
        raise RetireAcceptError(
            "E_RAC_NOT_READY",
            "%s reads %s (%s)" % (name, row.get("verdict"),
                                  row.get("reason") or "no reason"))
    post = splice(text, entry)
    after = declaration_entries(post)
    if len(after) != len(entries) + 1:
        raise RetireAcceptError("E_RAC_BAD_ENTRY",
                                "post text carries %d entries, expected %d"
                                % (len(after), len(entries) + 1))
    if not _same_entry(after[-1], entry):
        raise RetireAcceptError("E_RAC_BAD_ENTRY",
                                "post text did not keep the rendered entry")
    for before, kept in zip(entries, after[:-1]):
        if not _same_entry(before, kept):
            raise RetireAcceptError("E_RAC_BAD_ENTRY",
                                    "post text moved %s" % before["script"])
    report = {}
    for key in PLAN_KEYS:
        report[key] = entry.get(key)
    report["path"] = DECL_REL.replace(os.sep, "/")
    report["entry_index"] = len(after)
    report["entry_count_before"] = len(entries)
    report["entry_count_after"] = len(after)
    report["before_bytes"] = len(text.encode("utf-8"))
    report["predicted_bytes"] = len(payload_bytes(
        post.encode("utf-8") if raw is None else raw, post))
    report["wrote"] = False
    report["read_back_ok"] = None
    return report, post


def accept(root, script, declared, reason, until=None, execute=False):
    """Plan (and optionally perform) one acceptance append under root."""
    path = os.path.join(root, DECL_REL)
    if not os.path.isfile(path):
        raise RetireAcceptError(
            "E_RAC_UNPINNED",
            "no acceptance declaration at %s" % DECL_REL.replace(os.sep, "/"))
    try:
        with io.open(path, "r", encoding="utf-8") as handle:
            text = handle.read()
        with io.open(path, "rb") as handle:
            raw = handle.read()
    except (IOError, OSError, UnicodeDecodeError) as exc:
        raise RetireAcceptError("E_RAC_BAD_DECL", "%s (%s)" % (path, exc))
    entry = render_entry(script, declared, reason, until)
    report, post = plan(text, entry, live_index(live_report(root)), raw=raw)
    if not execute:
        return report
    data = payload_bytes(raw, post)
    if len(data) != report["predicted_bytes"]:
        raise RetireAcceptError("E_RAC_PREDICT",
                                "payload is %d bytes, predicted %d"
                                % (len(data), report["predicted_bytes"]))
    temp = path + TEMP_SUFFIX
    try:
        with io.open(temp, "wb") as handle:
            handle.write(data)
        os.replace(temp, path)
    except (IOError, OSError) as exc:
        if os.path.exists(temp):
            os.remove(temp)
        raise RetireAcceptError("E_RAC_WRITE", "%s (%s)" % (path, exc))
    try:
        with io.open(path, "rb") as handle:
            landed = handle.read()
    except (IOError, OSError) as exc:
        raise RetireAcceptError("E_RAC_READBACK", "%s (%s)" % (path, exc))
    after = declaration_entries(landed.decode("utf-8"))
    report["wrote"] = True
    report["read_back_ok"] = (landed == data
                              and len(after) == report["entry_count_after"]
                              and _same_entry(after[-1], entry))
    if not report["read_back_ok"]:
        raise RetireAcceptError("E_RAC_READBACK",
                                "%s did not read back as written" % path)
    return report


def one_line(report):
    return ("RETIRE ACCEPT %s index=%d entries=%d->%d bytes=%d->%d "
            "wrote=%s read_back=%s"
            % (report["path"], report["entry_index"],
               report["entry_count_before"], report["entry_count_after"],
               report["before_bytes"], report["predicted_bytes"],
               "yes" if report["wrote"] else "no",
               "-" if report["read_back_ok"] is None
               else ("ok" if report["read_back_ok"] else "bad")))


def parse_args(argv):
    """Pinned flags only; anything else is bad flags (exit 5)."""
    opts = {"mode": "check", "round": None, "root": None, "json": False,
            "script": None, "declared": None, "reason": None, "until": None,
            "execute": False}
    takes = {"--round": "round", "--root": "root", "--accept": "script",
             "--declared": "declared", "--reason": "reason", "--until": "until"}
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--check":
            opts["mode"] = "check"
            index += 1
        elif arg == "--execute":
            opts["execute"] = True
            index += 1
        elif arg == "--json":
            opts["json"] = True
            index += 1
        elif arg in takes:
            if index + 1 >= len(argv) or not argv[index + 1]:
                raise RetireAcceptError("E_RAC_BAD_ARGS", arg + " needs a value")
            opts[takes[arg]] = argv[index + 1]
            if arg == "--accept":
                opts["mode"] = "accept"
            index += 2
        else:
            raise RetireAcceptError("E_RAC_BAD_ARGS", arg)
    if opts["mode"] == "accept":
        for key in ("script", "declared", "reason"):
            if not opts[key]:
                raise RetireAcceptError("E_RAC_BAD_ARGS",
                                        "--accept needs --%s" % key)
    if opts["root"] is None:
        opts["root"] = os.path.normpath(
            os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "..", ".."))
    return opts


def main(argv):
    try:
        opts = parse_args(argv)
    except RetireAcceptError as exc:
        sys.stderr.write("%s %s\n" % (exc.code, exc.detail))
        return 5
    if opts["mode"] == "accept":
        try:
            report = accept(opts["root"], opts["script"], opts["declared"],
                            opts["reason"], until=opts["until"],
                            execute=opts["execute"])
        except RetireAcceptError as exc:
            sys.stderr.write("%s %s\n" % (exc.code, exc.detail))
            if exc.code in ("E_RAC_UNPINNED", "E_RAC_BAD_DECL"):
                return 3
            return 2
        if opts["json"]:
            sys.stdout.write(json.dumps(report, ensure_ascii=True,
                                        indent=2, sort_keys=False) + "\n")
        else:
            sys.stdout.write(one_line(report) + "\n")
        return 0
    try:
        round_no = parse_round(opts["round"]) if opts["round"] else None
        report = check(opts["root"], round_no)
    except RetireAcceptError as exc:
        sys.stderr.write("%s %s\n" % (exc.code, exc.detail))
        return 3
    if opts["json"]:
        sys.stdout.write(to_json(report))
    else:
        sys.stdout.write(render(report) + "\n")
    clean = (report["pinned"] and not report["unmatched"]
             and not report["stale_decision"])
    return 0 if clean else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))