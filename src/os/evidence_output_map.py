"""evidence_output_map - which legacy scripts claim which qa outputs?

R2282 shipped evidence_parity, which says whether a legacy per-round script
still performs the whole evidence ritual. That is necessary but not enough to
retire one: every legacy copy also declares the qa evidence paths it writes,
and nothing reports two scripts writing the SAME path (so retiring one silently
deletes a file another author still owns) or a cited output that no script
declares at all (so retiring it breaks a citation the record still depends on).

This reader answers that one question over the pile, by static analysis only:

    per script its declared output paths, every collision naming both scripts
    and the line each declaration sits on, and the declared-but-absent set

A declaration is a literal or template token shaped like `qa/<name>.<ext>` in
the script body, because that is the form this house writes evidence paths in.
A cited output is a LITERAL token of the same shape read out of an optional
citations file (the round records are the usual one); a template cannot claim
a literal citation, so a template never hides an absence.

The reader never runs the scripts it judges, never writes anything, and reads
no clock, so the same bytes always produce the same reading.

Criteria AC-EOM1..AC-EOM6 were pinned in state/queue/tech.md as the R2282 seed
row BEFORE this code existed. Stdlib only, ASCII source, zero network.
"""

import hashlib
import json
import os
import re
import sys

PATTERN = "evidence_R*.py"
EXTENSIONS = ("log", "json", "md", "txt")

TOKEN = re.compile(
    r"qa/[A-Za-z0-9._%{}<>$@+/-]*[A-Za-z0-9_%{}<>$@+-]\.(?:log|json|md|txt)")

# The house writes evidence paths as os.path.join(ROOT, "qa", "<name>.<ext>"),
# so the folder and the file name sit in two literals. Reading only the joined
# literal form would report every one of those scripts as declaring nothing.
JOINED = re.compile(
    r"""['"]qa[/\\]?['"]\s*,\s*['"]([^'"]+\.(?:log|json|md|txt))['"]""")

# A third form concatenates the folder, a separator and the name.
CONCAT = re.compile(
    r"""['"]qa[/\\]?['"]\s*\+\s*(?:os\.sep|['"][\\/]{1,2}['"])\s*\+\s*"""
    r"""['"]([^'"]+\.(?:log|json|md|txt))['"]""")

# A fourth form binds the folder to a module constant once and joins it later:
#     QA = os.path.join(BASE, "..", "..", "qa")
#     LOG = os.path.join(QA, "reconcile-all-R1977.log")
ALIAS = re.compile(
    r"""([A-Za-z_]\w*)\s*=\s*os\.path\.join\([^()]*"""
    r"""(?:\([^()]*\)[^()]*)*['"]qa['"]\s*\)""")
ALIAS_JOIN = (r"""os\.path\.join\(\s*%s\s*,\s*['"]([^'"]+\.(?:log|json|md|"""
              r"""txt))['"]""")

ROW_KEYS = ("script", "bytes", "sha16", "declared", "count", "verdict")
MAP_KEYS = ("dir", "pattern", "scripts", "declared_total",
            "collision_total", "collisions", "absent_total", "absent",
            "unreadable", "rows", "verdict")
DECL_KEYS = ("path", "line")

USAGE = ("usage: evidence_output_map.py --dir PATH [--pattern GLOB]\n"
         "       [--citations PATH] [--json] [--root PATH]\n"
         "exit 0 = CLEAN (no collision, no absent output), 2 = FINDINGS,\n"
         "3 = unreadable or absent input, 5 = bad flags\n")


class OutputMapError(Exception):
    """A refused reading: the code names why, detail names the input."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, code)
        self.code = code
        self.detail = detail


def _resolve(root, name):
    if os.path.isabs(name):
        return name
    return os.path.join(root, name)


def read_text(path, code, detail):
    """Bytes then decode. Absent and unreadable are separate refusals."""
    if not os.path.isfile(path):
        raise OutputMapError(code, detail)
    try:
        with open(path, "rb") as handle:
            raw = handle.read()
    except (IOError, OSError):
        raise OutputMapError("E_EOM_UNREADABLE", detail)
    try:
        return raw, raw.decode("utf-8")
    except UnicodeDecodeError:
        raise OutputMapError("E_EOM_UNREADABLE", detail)


def declarations(text):
    """The `qa/<name>.<ext>` tokens one script declares, first line wins.

    Three written forms count, because all three are the house style: the
    joined literal `qa/<name>.<ext>`, the split os.path.join(..., "qa",
    "<name>") which may wrap across lines, and the concatenation of the folder
    with a separator and the name. A name computed into a variable is not a
    declaration and reads NONE.
    """
    found = []
    for match in TOKEN.finditer(text):
        found.append((match.start(), match.group(0)))
    for pattern in (JOINED, CONCAT):
        for match in pattern.finditer(text):
            found.append((match.start(), "qa/" + match.group(1)))
    for alias in sorted(set(ALIAS.findall(text))):
        pattern = re.compile(ALIAS_JOIN % re.escape(alias))
        for match in pattern.finditer(text):
            found.append((match.start(), "qa/" + match.group(1)))
    seen = {}
    order = []
    for position, token in sorted(found):
        if token not in seen:
            seen[token] = text.count("\n", 0, position) + 1
            order.append(token)
    return [{"path": token, "line": seen[token]} for token in order]


def is_literal(path):
    """A template declares a family; only a literal can cite one file."""
    return "%" not in path and "{" not in path and "$" not in path


def cited(path):
    """Literal tokens in a citations file, first line wins per path."""
    seen = {}
    order = []
    for number, line in enumerate(path.splitlines(), 1):
        for match in TOKEN.finditer(line):
            token = match.group(0)
            if not is_literal(token) or token in seen:
                continue
            seen[token] = number
            order.append(token)
    return [{"path": token, "line": seen[token]} for token in order]


def row_for(root, script):
    """One row per pile file. Writes nothing, reads no clock."""
    path = _resolve(root, script)
    try:
        raw, text = read_text(path, "E_EOM_NO_FILE", script)
    except OutputMapError as exc:
        return {"script": script, "bytes": 0, "sha16": "",
                "declared": [], "count": 0, "verdict": "UNREADABLE",
                "code": exc.code}
    found = declarations(text)
    return {"script": script, "bytes": len(raw),
            "sha16": hashlib.sha256(raw).hexdigest()[:16],
            "declared": found, "count": len(found),
            "verdict": "DECLARED" if found else "NONE"}


def build(root, directory, pattern=PATTERN, citations=None):
    """The whole map: rows, collisions, the declared-but-absent set."""
    folder = _resolve(root, directory)
    if not os.path.isdir(folder):
        raise OutputMapError("E_EOM_NO_DIR", directory)
    names = sorted(name for name in os.listdir(folder)
                   if re.match(pattern.replace("*", ".*") + "$", name))
    rows = []
    for name in names:
        script = (os.path.join(folder, name) if os.path.isabs(directory)
                  else os.path.join(directory, name))
        rows.append(row_for(root, script))
    owners = {}
    for row in rows:
        for item in row["declared"]:
            owners.setdefault(item["path"], []).append(
                {"script": row["script"], "line": item["line"]})
    collisions = [{"path": path, "scripts": owners[path]}
                  for path in sorted(owners) if len(owners[path]) > 1]
    cited_rows = []
    if citations is not None:
        raw, text = read_text(_resolve(root, citations), "E_EOM_NO_CITATIONS",
                              citations)
        del raw
        cited_rows = cited(text)
    absent = [item for item in cited_rows if item["path"] not in owners]
    unreadable = [{"script": row["script"], "code": row["code"]}
                  for row in rows if row["verdict"] == "UNREADABLE"]
    declared_total = sum(row["count"] for row in rows)
    clean = (not collisions and not absent and not unreadable)
    return {"dir": directory, "pattern": pattern,
            "scripts": len(names),
            "declared_total": declared_total,
            "collision_total": len(collisions), "collisions": collisions,
            "absent_total": len(absent), "absent": absent,
            "unreadable": unreadable, "rows": rows,
            "verdict": "CLEAN" if clean else "FINDINGS"}


def render_map(report):
    parts = ["EVIDENCE OUTPUT MAP dir=%s pattern=%s scripts=%d "
             "declared=%d collision=%d absent=%d verdict=%s"
             % (report["dir"], report["pattern"], report["scripts"],
                report["declared_total"], report["collision_total"],
                report["absent_total"], report["verdict"])]
    for row in report["rows"]:
        parts.append("ROW %s count=%d verdict=%s"
                     % (row["script"], row["count"], row["verdict"]))
    for item in report["collisions"]:
        parts.append("COLLISION %s scripts=%s"
                     % (item["path"], ",".join(
                         "%s:%d" % (owner["script"], owner["line"])
                         for owner in item["scripts"])))
    for item in report["absent"]:
        parts.append("ABSENT %s cited_line=%d"
                     % (item["path"], item["line"]))
    for item in report["unreadable"]:
        parts.append("UNREADABLE %s %s" % (item["script"], item["code"]))
    return "\n".join(parts)


def to_json(report):
    """Byte-stable over the pinned key order; declarations carry path+line."""
    ordered = {}
    for key in MAP_KEYS:
        value = report[key]
        if key == "rows":
            rows = []
            for row in report["rows"]:
                item = {}
                for name in ROW_KEYS:
                    value2 = row[name]
                    if name == "declared":
                        value2 = [dict((k, dec[k]) for k in DECL_KEYS)
                                  for dec in row["declared"]]
                    item[name] = value2
                rows.append(item)
            value = rows
        ordered[key] = value
    return json.dumps(ordered, ensure_ascii=True, sort_keys=False) + "\n"


EXIT_BY_CODE = {"E_EOM_NO_DIR": 3, "E_EOM_NO_CITATIONS": 3,
                "E_EOM_UNREADABLE": 3, "E_EOM_BAD_ARGS": 5}


def main(argv):
    directory = None
    pattern = PATTERN
    citations = None
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
        elif arg in ("--dir", "--pattern", "--citations", "--root"):
            index += 1
            if index >= len(argv):
                sys.stdout.write("E_EOM_BAD_ARGS: %s needs a value\n" % arg)
                return 5
            value = argv[index]
            if arg == "--dir":
                directory = value
            elif arg == "--pattern":
                pattern = value
            elif arg == "--citations":
                citations = value
            else:
                root = value
        else:
            sys.stdout.write("E_EOM_BAD_ARGS: unknown flag %s\n" % arg)
            sys.stdout.write(USAGE)
            return 5
        index += 1
    if directory is None:
        sys.stdout.write("E_EOM_BAD_ARGS: --dir is required\n")
        sys.stdout.write(USAGE)
        return 5
    try:
        report = build(root, directory, pattern, citations)
    except OutputMapError as exc:
        sys.stdout.write("%s %s\n" % (exc.code, exc.detail))
        sys.stdout.write("REFUSE TO MAP\n")
        return EXIT_BY_CODE.get(exc.code, 3)
    sys.stdout.write(to_json(report) if as_json
                     else render_map(report) + "\n")
    if report["unreadable"]:
        return 3
    return 0 if report["verdict"] == "CLEAN" else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))