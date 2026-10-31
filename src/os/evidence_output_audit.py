"""evidence_output_audit - are the outputs a legacy script declares on disk?

R2282's evidence_output_map reports what each legacy copy DECLARES, but not
whether the declaration is still true: a script can declare
qa/<name>.log that was never written (a renamed round, a failed capture, a
hand-deleted file), and the map still counts that script as owning an output
while the parity reader judges it stale. Two readers pointing opposite ways is
how a retirement decision gets made on a file that does not exist.

This audit joins the map with the evidence directory and answers one question:

    per script every declared literal is EXISTS or ABSENT on disk, every
    template declaration is a FAMILY-HIT with its match count or a
    FAMILY-NONE with zero, and a script whose declarations resolve to nothing
    reads STALE instead of being counted as owned

The declaration law is NOT re-implemented here: it is imported from
evidence_output_map, so a patch to that reader flows straight through this
one. Nothing is run, nothing is written, and no clock is read, so the same
bytes always produce the same reading.

Criteria AC-EOA1..AC-EOA6 were pinned in state/queue/tech.md as the R2296 seed
row BEFORE this code existed. Stdlib only, ASCII source, zero network.
"""

import json
import os
import re
import sys

import evidence_output_map as eom

PATTERN = eom.PATTERN
QA_DEFAULT = "qa"

AUDIT_KEYS = ("dir", "pattern", "qa", "scripts", "declared_total",
              "exists_total", "absent_total", "family_hit_total",
              "family_none_total", "stale_total", "absent", "families",
              "stale", "unreadable", "rows", "verdict")
ROW_KEYS = ("script", "count", "exists", "absent", "family_hit",
            "family_none", "status")
DECL_KEYS = ("path", "line", "verdict", "matches")

# Template slots the house actually writes: printf forms, braces, <angle>,
# and shell-style variables. Everything else is a literal and must match.
SLOT = re.compile(r"%[sdifr]|\$\{[^}]*\}|\$[A-Za-z_]\w*|\{[^}]*\}|<[^>]*>")

USAGE = ("usage: evidence_output_audit.py --dir PATH [--pattern GLOB]\n"
         "       [--qa PATH] [--json] [--root PATH]\n"
         "exit 0 = CLEAN (every declaration resolves, nothing stale),\n"
         "2 = FINDINGS (an absent literal, a family miss or a stale script),\n"
         "3 = unreadable or absent input, 5 = bad flags\n")


class AuditError(Exception):
    """A refused reading: the code names why, detail names the input."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, code)
        self.code = code
        self.detail = detail


def _resolve(root, name):
    if os.path.isabs(name):
        return name
    return os.path.join(root, name)


def split_target(path):
    """`qa/<rest>` -> (relative folder, file name); both slash-normalised."""
    rest = path
    marker = "qa/"
    index = rest.find(marker)
    if index >= 0:
        rest = rest[index + len(marker):]
    rest = rest.replace("\\", "/")
    if "/" in rest:
        head, tail = rest.rsplit("/", 1)
        return head, tail
    return "", rest


def family_regex(name):
    """A template name becomes an anchored regex with one `.+` per slot."""
    parts = []
    last = 0
    for match in SLOT.finditer(name):
        parts.append(re.escape(name[last:match.start()]))
        parts.append(".+")
        last = match.end()
    parts.append(re.escape(name[last:]))
    return re.compile("^" + "".join(parts) + "$")


def family_matches(qa_dir, path, cache):
    """Matches in the declaration's own folder; the listing is read once."""
    head, tail = split_target(path)
    folder = os.path.join(qa_dir, head) if head else qa_dir
    if folder not in cache:
        try:
            cache[folder] = sorted(os.listdir(folder))
        except (IOError, OSError):
            cache[folder] = None
    names = cache[folder]
    if names is None:
        return 0
    pattern = family_regex(tail)
    return sum(1 for name in names if pattern.match(name))


def audit_row(script, declared, qa_dir, cache):
    """One script: its declarations resolved against the evidence folder."""
    literals = []
    templates = []
    for item in declared:
        if eom.is_literal(item["path"]):
            head, tail = split_target(item["path"])
            target = os.path.join(qa_dir, head, tail) if head \
                else os.path.join(qa_dir, tail)
            literals.append({"path": item["path"], "line": item["line"],
                             "verdict": "EXISTS" if os.path.isfile(target)
                             else "ABSENT",
                             "matches": 1 if os.path.isfile(target) else 0})
        else:
            hits = family_matches(qa_dir, item["path"], cache)
            templates.append({"path": item["path"], "line": item["line"],
                              "verdict": "FAMILY-HIT" if hits else
                              "FAMILY-NONE",
                              "matches": hits})
    exists = sum(1 for item in literals if item["verdict"] == "EXISTS")
    absent = len(literals) - exists
    hit = sum(1 for item in templates if item["verdict"] == "FAMILY-HIT")
    missed = len(templates) - hit
    resolved = exists + hit
    if not declared:
        status = "STALE"
        reason = "NO-DECLARATION"
    elif resolved == 0:
        status = "STALE"
        reason = "ALL-UNRESOLVED"
    else:
        status = "OK"
        reason = ""
    return {"script": script, "count": len(declared), "exists": exists,
            "absent": absent, "family_hit": hit, "family_none": missed,
            "status": status, "reason": reason,
            "declarations": literals + templates}


def audit(root, directory, qa=QA_DEFAULT, pattern=PATTERN):
    """The whole audit: rows, absent literals, families, stale scripts."""
    folder = _resolve(root, directory)
    qa_dir = _resolve(root, qa)
    if not os.path.isdir(folder):
        raise AuditError("E_EOA_NO_DIR", directory)
    if not os.path.isdir(qa_dir):
        raise AuditError("E_EOA_NO_QA", qa)
    try:
        mapped = eom.build(root, directory, pattern)
    except eom.OutputMapError as exc:
        raise AuditError("E_EOA_NO_DIR", "%s %s" % (exc.code, exc.detail))
    cache = {}
    rows = []
    for row in mapped["rows"]:
        rows.append(audit_row(row["script"], row["declared"], qa_dir, cache))
    absent = []
    families = []
    for row in rows:
        for item in row["declarations"]:
            entry = {"script": row["script"], "path": item["path"],
                     "line": item["line"], "verdict": item["verdict"],
                     "matches": item["matches"]}
            if item["verdict"] == "ABSENT":
                absent.append(entry)
            elif item["verdict"].startswith("FAMILY"):
                families.append(entry)
    stale = [{"script": row["script"], "reason": row["reason"]}
             for row in rows if row["status"] == "STALE"]
    unreadable = list(mapped["unreadable"])
    declared_total = sum(row["count"] for row in rows)
    exists_total = sum(row["exists"] for row in rows)
    clean = not absent and not stale and not unreadable and \
        all(item["verdict"] == "FAMILY-HIT" for item in families)
    return {"dir": directory, "pattern": pattern, "qa": qa,
            "scripts": len(rows),
            "declared_total": declared_total,
            "exists_total": exists_total,
            "absent_total": len(absent),
            "family_hit_total": sum(1 for item in families
                                    if item["verdict"] == "FAMILY-HIT"),
            "family_none_total": sum(1 for item in families
                                     if item["verdict"] == "FAMILY-NONE"),
            "stale_total": len(stale), "absent": absent, "families": families,
            "stale": stale, "unreadable": unreadable, "rows": rows,
            "verdict": "CLEAN" if clean else "FINDINGS"}


def render_audit(report):
    parts = ["EVIDENCE OUTPUT AUDIT dir=%s qa=%s pattern=%s scripts=%d "
             "declared=%d exists=%d absent=%d family_hit=%d family_none=%d "
             "stale=%d verdict=%s"
             % (report["dir"], report["qa"], report["pattern"],
                report["scripts"], report["declared_total"],
                report["exists_total"], report["absent_total"],
                report["family_hit_total"], report["family_none_total"],
                report["stale_total"], report["verdict"])]
    for row in report["rows"]:
        parts.append("ROW %s declared=%d exists=%d absent=%d family_hit=%d "
                     "family_none=%d status=%s"
                     % (row["script"], row["count"], row["exists"],
                        row["absent"], row["family_hit"],
                        row["family_none"], row["status"]))
    for item in report["absent"]:
        parts.append("ABSENT %s script=%s line=%d"
                     % (item["path"], item["script"], item["line"]))
    for item in report["families"]:
        parts.append("FAMILY %s script=%s matches=%d verdict=%s"
                     % (item["path"], item["script"], item["matches"],
                        item["verdict"]))
    for item in report["stale"]:
        parts.append("STALE %s reason=%s"
                     % (item["script"], item["reason"]))
    for item in report["unreadable"]:
        parts.append("UNREADABLE %s %s"
                     % (item["script"], item["code"]))
    return "\n".join(parts)


def to_json(report):
    """Byte-stable over the pinned key order; rows carry their declarations."""
    ordered = {}
    for key in AUDIT_KEYS:
        value = report[key]
        if key == "rows":
            rows = []
            for row in report["rows"]:
                item = {}
                for name in ROW_KEYS:
                    item[name] = row[name]
                rows.append(item)
            value = rows
        ordered[key] = value
    return json.dumps(ordered, ensure_ascii=True, sort_keys=False) + "\n"


EXIT_BY_CODE = {"E_EOA_NO_DIR": 3, "E_EOA_NO_QA": 3, "E_EOA_BAD_ARGS": 5}


def main(argv):
    directory = None
    pattern = PATTERN
    qa = QA_DEFAULT
    as_json = False
    root = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--json":
            as_json = True
        elif arg in ("--help", "-h"):
            sys.stdout.write(USAGE)
            return 0
        elif arg in ("--dir", "--pattern", "--qa", "--root"):
            index += 1
            if index >= len(argv):
                sys.stdout.write("E_EOA_BAD_ARGS: %s needs a value\n" % arg)
                return 5
            value = argv[index]
            if arg == "--dir":
                directory = value
            elif arg == "--pattern":
                pattern = value
            elif arg == "--qa":
                qa = value
            else:
                root = value
        else:
            sys.stdout.write("E_EOA_BAD_ARGS: unknown flag %s\n" % arg)
            sys.stdout.write(USAGE)
            return 5
        index += 1
    if directory is None:
        sys.stdout.write("E_EOA_BAD_ARGS: --dir is required\n")
        sys.stdout.write(USAGE)
        return 5
    try:
        report = audit(root, directory, qa, pattern)
    except AuditError as exc:
        sys.stdout.write("%s %s\n" % (exc.code, exc.detail))
        sys.stdout.write("REFUSE TO AUDIT\n")
        return EXIT_BY_CODE.get(exc.code, 3)
    sys.stdout.write(to_json(report) if as_json
                     else render_audit(report) + "\n")
    if report["unreadable"]:
        return 3
    return 0 if report["verdict"] == "CLEAN" else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))