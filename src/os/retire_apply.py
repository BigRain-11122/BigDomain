# retire_apply.py - the acceptance finally has an acting step, and it MOVES.
# Criteria AC-RAP1..AC-RAP6 were pre-registered in state/queue/tech.md (the
# R2333 seed row, read live at the R2348 head) BEFORE this file existed.
#
# Why this exists: retire_accept RECORDS that six evidence copies are safe to
# retire (until R2350) and retire_candidate keeps that judgement honest, but
# nothing can ACT on the record. The only way to retire one of those copies
# today is a hand move, which leaves no trace of the round it happened in, no
# proof the bytes were the ones judged safe, and no undo path.
#
# This module is that acting step, and it is a MOVE, never a delete:
#   * the entry class and the live verdict are IMPORTED (retire_accept.check
#     answers both), so a patched acceptance reader or a patched resolver moves
#     this module's verdict instead of being re-derived here (AC-RAP1);
#   * the dry run is the DEFAULT and the report names source, destination,
#     entry class and predicted byte count; nothing on disk moves without
#     --execute, proved by a whole-tree digest taken on both sides of the plan
#     (AC-RAP2);
#   * only an ACCEPTED entry is movable. EXPIRED, UNMATCHED and STALE-DECISION
#     each refuse BY CLASS carrying the reason the acceptance reader gave; a
#     script the declaration never mentions refuses; a destination that already
#     holds a file refuses rather than overwriting (AC-RAP3);
#   * an executed apply is ONE os.replace into media/quarantine/R<nnnn>/, and
#     the per-file digest map proves that exactly two paths changed - the
#     source disappearing and the destination appearing - with the destination
#     bytes equal to the source bytes (AC-RAP4);
#   * exits 0 planned or applied, 2 refused over live state, 3 unreadable or
#     missing input, 5 bad flags, and --json is byte-stable over pinned keys
#     (AC-RAP5);
#   * pure ASCII, stdlib only, zero network, no clock, and NO delete path: this
#     module contains no os.remove, no unlink and no rmtree, so the worst a
#     wrong call can do is place a file somewhere else in the tree (AC-RAP6).
#
# The quarantine path lives under media/, which is gitignored, so a retired
# copy leaves the versioned tree while its bytes stay on disk for inspection.

import hashlib
import io
import json
import os
import sys

import retire_accept as RA

DIR = "src/os"
QUARANTINE_REL = "media/quarantine"
STATE_REL = "src/os/state.json"
SKIP_DIRS = (".git",)

PLAN_KEYS = ("script", "class", "source", "destination", "round",
             "source_bytes", "predicted_bytes", "wrote", "read_back_ok",
             "digest_before", "digest_after", "verdict")

LIST_KEYS = ("round", "entries", "accepted", "rows", "verdict")

ROW_KEYS = ("script", "class", "source", "until")

USAGE = ("usage: retire_apply.py --script SCRIPT [--round R<nnnn>]\n"
         "       [--root PATH] [--execute] [--json]\n"
         "       retire_apply.py --list [--round R<nnnn>] [--root PATH]\n"
         "       [--json]\n"
         "exit 0 = planned (dry run), applied, or listed,\n"
         "2 = refused over live state, 3 = unreadable or missing input,\n"
         "5 = bad flags\n")

PLANNED = "PLANNED"
APPLIED = "APPLIED"
LISTED = "LISTED"


class RetireApplyError(Exception):
    """A refused reading: the code names why, the detail names the input."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, code)
        self.code = code
        self.detail = detail


def norm(name):
    """One script name form; the acceptance reader owns it, so ask it."""
    return RA.norm(name)


def script_rel(script, directory=DIR):
    """'evidence_R2248.py' and 'src/os/evidence_R2248.py' name one file."""
    name = norm(script)
    if not name:
        raise RetireApplyError("E_RAP_BAD_ARGS", "script is empty")
    folder = norm(directory).strip("/")
    if not name.startswith(folder + "/"):
        name = folder + "/" + name.lstrip("/")
    return name


def abs_of(root, rel):
    return os.path.join(root, *rel.split("/"))


def quarantine_rel(round_no, script):
    base = os.path.basename(norm(script))
    return "%s/R%d/%s" % (QUARANTINE_REL, round_no, base)


def _file_map(root):
    """Every file under root (minus SKIP_DIRS): relative path -> sha256."""
    out = {}
    for folder, dirs, files in os.walk(root):
        dirs[:] = sorted(name for name in dirs if name not in SKIP_DIRS)
        for name in sorted(files):
            path = os.path.join(folder, name)
            rel = os.path.relpath(path, root).replace(os.sep, "/")
            digest = hashlib.sha256()
            try:
                with io.open(path, "rb") as handle:
                    for chunk in iter(lambda: handle.read(262144), b""):
                        digest.update(chunk)
            except (IOError, OSError) as exc:
                raise RetireApplyError("E_RAP_NO_INPUT", "%s (%s)"
                                       % (rel, exc))
            out[rel] = digest.hexdigest()
    return out


def tree_digest(root):
    """One digest over the whole tree, so a dry run can prove it moved nothing."""
    digest = hashlib.sha256()
    for rel, value in sorted(_file_map(root).items()):
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        digest.update(value.encode("ascii"))
        digest.update(b"\0")
    return digest.hexdigest()


def check_reading(root, round_no=None):
    """The whole acceptance reading, asked of its own reader (AC-RAP1)."""
    try:
        report = RA.check(root, round_no)
    except RA.RetireAcceptError as exc:
        raise RetireApplyError("E_RAP_NO_INPUT", "%s %s" % (exc.code, exc.detail))
    except Exception as exc:  # noqa: BLE001 - an unreadable pile is not a plan
        raise RetireApplyError("E_RAP_NO_INPUT",
                               "%s (%s)" % (type(exc).__name__, exc))
    if not isinstance(report, dict) or not isinstance(report.get("rows"), list):
        raise RetireApplyError("E_RAP_NO_INPUT",
                               "acceptance reader returned %r"
                               % (type(report).__name__,))
    return report


def round_of(report):
    """The round the reading was taken for, as an int (never a clock)."""
    try:
        return RA.parse_round(report.get("round"), "E_RAP_NO_INPUT")
    except RA.RetireAcceptError as exc:
        raise RetireApplyError("E_RAP_NO_INPUT", "%s %s" % (exc.code, exc.detail))


def find_row(report, script, directory=DIR):
    """The ONE row the declaration carries for that script, or None.

    Both sides are put through script_rel first, so a bare file name and the
    full repository-relative one are the same entry rather than two.
    """
    wanted = script_rel(script, directory)
    hits = [row for row in report.get("rows") or []
            if script_rel(row.get("script"), directory) == wanted]
    if len(hits) > 1:
        raise RetireApplyError("E_RAP_AMBIGUOUS",
                               "%d rows carry %s" % (len(hits), wanted))
    return hits[0] if hits else None


def listing(root, round_no=None):
    """Read-only: what is movable right now, without planning a move."""
    report = check_reading(root, round_no)
    round_no = round_of(report)
    rows = []
    for row in report.get("rows") or []:
        rows.append({"script": norm(row.get("script")),
                     "class": row.get("class") or "",
                     "source": script_rel(row.get("script")),
                     "until": row.get("until") or ""})
    return {"round": "R%d" % round_no,
            "entries": len(rows),
            "accepted": sum(1 for row in rows if row["class"] == RA.ACCEPTED),
            "rows": rows,
            "verdict": LISTED}


def plan(root, script, round_no=None, execute=False, directory=DIR):
    """Plan (default) or perform ONE move into the quarantine path."""
    report = check_reading(root, round_no)
    round_no = round_of(report)
    row = find_row(report, script)
    if row is None:
        raise RetireApplyError(
            "E_RAP_NOT_DECLARED",
            "%s carries no accepted entry" % norm(script))
    klass = row.get("class")
    if klass != RA.ACCEPTED:
        reason = (row.get("detail") or row.get("live_verdict") or "").strip()
        raise RetireApplyError(
            "E_RAP_CLASS_" + str(klass or "UNKNOWN").replace("-", "_"),
            "%s %s" % (norm(script), reason or "no reason given"))

    src_rel = script_rel(script, directory)
    src_abs = abs_of(root, src_rel)
    if not os.path.isfile(src_abs):
        raise RetireApplyError("E_RAP_NO_SOURCE", "%s is not on disk" % src_rel)
    dest_rel = quarantine_rel(round_no, src_rel)
    dest_abs = abs_of(root, dest_rel)
    if os.path.exists(dest_abs):
        raise RetireApplyError("E_RAP_DEST_EXISTS",
                               "%s already holds a file" % dest_rel)

    size = os.path.getsize(src_abs)
    before = tree_digest(root)
    result = {"script": norm(script), "class": klass, "source": src_rel,
              "destination": dest_rel, "round": "R%d" % round_no,
              "source_bytes": size, "predicted_bytes": size, "wrote": False,
              "read_back_ok": False, "digest_before": before,
              "digest_after": before, "verdict": PLANNED}
    if not execute:
        after = tree_digest(root)
        if after != before:
            raise RetireApplyError("E_RAP_DRYRUN_MOVED",
                                   "the dry run changed the tree")
        return result

    before_map = _file_map(root)
    source_digest = before_map.get(src_rel)
    if source_digest is None:
        raise RetireApplyError("E_RAP_NO_SOURCE", "%s is not in the map"
                               % src_rel)
    parent = os.path.dirname(dest_abs)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent)
    os.replace(src_abs, dest_abs)
    after_map = _file_map(root)

    gone = sorted(set(before_map) - set(after_map))
    added = sorted(set(after_map) - set(before_map))
    if gone != [src_rel] or added != [dest_rel]:
        raise RetireApplyError(
            "E_RAP_MOVE_UNPROVEN",
            "gone=%s added=%s" % (",".join(gone) or "-",
                                  ",".join(added) or "-"))
    for rel in set(before_map) & set(after_map):
        if before_map[rel] != after_map[rel]:
            raise RetireApplyError("E_RAP_MOVE_UNPROVEN",
                                   "%s changed bytes" % rel)
    if after_map[dest_rel] != source_digest:
        raise RetireApplyError("E_RAP_MOVE_UNPROVEN",
                               "%s bytes differ from the source" % dest_rel)
    with io.open(dest_abs, "rb") as handle:
        read_back = hashlib.sha256(handle.read()).hexdigest()
    if read_back != source_digest:
        raise RetireApplyError("E_RAP_MOVE_UNPROVEN",
                               "%s read back differently" % dest_rel)
    result["wrote"] = True
    result["read_back_ok"] = True
    result["digest_after"] = tree_digest(root)
    result["verdict"] = APPLIED
    return result


def one_line(result):
    return ("RETIRE APPLY script=%s class=%s round=%s source=%s dest=%s "
            "bytes=%d wrote=%s read_back=%s verdict=%s"
            % (result["script"], result["class"], result["round"],
               result["source"], result["destination"], result["source_bytes"],
               "yes" if result["wrote"] else "no",
               "yes" if result["read_back_ok"] else "no", result["verdict"]))


def render(result):
    if result.get("verdict") == LISTED:
        parts = ["RETIRE APPLY LIST round=%s entries=%d accepted=%d "
                 "verdict=%s" % (result["round"], result["entries"],
                                 result["accepted"], result["verdict"])]
        for row in result["rows"]:
            parts.append("ROW %s %s source=%s until=%s"
                         % (row["script"], row["class"], row["source"],
                            row["until"] or "-"))
        return "\n".join(parts)
    return one_line(result)


def to_json(result):
    """One byte-stable rendering over the pinned keys, in pinned order."""
    keys = LIST_KEYS if result.get("verdict") == LISTED else PLAN_KEYS
    ordered = {}
    for key in keys:
        ordered[key] = result.get(key)
    return json.dumps(ordered, ensure_ascii=True, indent=2,
                      sort_keys=False) + "\n"


def parse_args(argv):
    opts = {"script": None, "round": None,
            "root": os.path.dirname(os.path.dirname(os.path.dirname(
                os.path.abspath(__file__)))),
            "execute": False, "json": False, "list": False}
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--script":
            index += 1
            if index >= len(argv) or not argv[index]:
                raise RetireApplyError("E_RAP_BAD_ARGS", "--script needs a value")
            opts["script"] = argv[index]
        elif arg == "--round":
            index += 1
            if index >= len(argv) or not argv[index]:
                raise RetireApplyError("E_RAP_BAD_ARGS", "--round needs a value")
            opts["round"] = argv[index]
        elif arg == "--root":
            index += 1
            if index >= len(argv) or not argv[index]:
                raise RetireApplyError("E_RAP_BAD_ARGS", "--root needs a value")
            opts["root"] = argv[index]
        elif arg == "--execute":
            opts["execute"] = True
        elif arg == "--json":
            opts["json"] = True
        elif arg == "--list":
            opts["list"] = True
        else:
            raise RetireApplyError("E_RAP_BAD_ARGS", "unknown flag %r" % (arg,))
        index += 1
    if opts["list"] and opts["script"] is not None:
        raise RetireApplyError("E_RAP_BAD_ARGS",
                               "--list and --script are exclusive")
    if opts["list"] and opts["execute"]:
        raise RetireApplyError("E_RAP_BAD_ARGS",
                               "--list writes nothing, so --execute has no sense")
    if not opts["list"] and opts["script"] is None:
        raise RetireApplyError("E_RAP_BAD_ARGS",
                               "one of --script or --list is required")
    if opts["round"] is not None:
        try:
            RA.parse_round(opts["round"])
        except RA.RetireAcceptError as exc:
            raise RetireApplyError("E_RAP_BAD_ARGS", "%s %s"
                                   % (exc.code, exc.detail))
    return opts


def main(argv):
    try:
        opts = parse_args(argv)
    except RetireApplyError as exc:
        sys.stderr.write("%s %s\n" % (exc.code, exc.detail))
        return 5
    try:
        if opts["list"]:
            result = listing(opts["root"], opts["round"])
        else:
            result = plan(opts["root"], opts["script"], opts["round"],
                          execute=opts["execute"])
    except RetireApplyError as exc:
        sys.stderr.write("%s %s\n" % (exc.code, exc.detail))
        if exc.code == "E_RAP_NO_INPUT":
            return 3
        return 2
    if opts["json"]:
        sys.stdout.write(to_json(result))
    else:
        sys.stdout.write(render(result) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))