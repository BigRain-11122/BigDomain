"""Map the os-probe-seam entry chain: depth, parent calls per level, fan-out.

R2866 named the deep-class cost as a 2^depth fan-out of parent calls. That
naming rested on ONE cProfile of ONE entry. This tool makes the same claim
enumerable at the source level, so the next window can work a list instead of
re-deriving the chain by hand:

  python tools/probe_seam_fanout_map.py            # table to stdout
  python tools/probe_seam_fanout_map.py --evidence qa/file.log

For every module in src/os that defines module_alias_entry, the tool resolves
the parent link (the module-level alias assignment the entry calls through)
and counts how many times the entry body calls that alias. Two calls per level
means depth d costs about 2**d parent entries - the fan-out. One call per
level would be linear, which is the shape a fix has to reach.

The tool reads source only. It imports each module for its alias, so an import
error is reported as unreadable rather than hidden. It measures SHAPE, never
runtime: it cannot say a suite is slow, only how many parent entries its entry
body asks for.

Pure ASCII, stdlib only, no clock, zero network.
"""

import argparse
import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OS_DIR = os.path.join(BASE, "src", "os")

ENTRY = "module_alias_entry"
ALIAS_RE = re.compile(r"^(_BASE_\w+_ENTRY)[ \t]*=[ \t]*(\w+)\.(\w+)[ \t]*$",
                      re.M)
IMPORT_RE = re.compile(r"^import\s+(\S+)\s+as\s+(\w+)\s*(?:#.*)?$", re.M)
DEF_RE = re.compile(r"^def\s+module_alias_entry\s*\(", re.M)


def entry_body(text):
    """Return the module_alias_entry body, or None when the def is absent."""
    match = DEF_RE.search(text)
    if match is None:
        return None
    rest = text[match.end():]
    lines = rest.splitlines(True)
    out = []
    started = False
    for line in lines:
        if not started:
            # Skip the parameter list of a multi-line signature.
            if line.rstrip().endswith("):") or line.rstrip().endswith(")"):
                started = True
            continue
        if line and not line[0].isspace():
            break
        out.append(line)
    return "".join(out)


def parent_alias(body, text):
    """The alias the entry calls through, plus the (module, function) it names."""
    aliases = dict((m.group(1), (m.group(2), m.group(3)))
                   for m in ALIAS_RE.finditer(text.replace("\r\n", "\n")))
    for alias in aliases:
        if alias + "(" in body:
            return alias, aliases[alias]
    imports = dict((m.group(2), m.group(1))
                   for m in IMPORT_RE.finditer(text.replace("\r\n", "\n")))
    for alias in imports:
        called = re.findall(r"\b" + alias + r"\.(\w+)\(", body)
        if called:
            return alias, (imports[alias], called[0])
    return None, None


def alias_table():
    """Every alias binding in src/os, keyed by (module, function)."""
    table = {}
    for name in sorted(os.listdir(OS_DIR)):
        if not name.endswith(".py"):
            continue
        text, _error = read_module(os.path.join(OS_DIR, name))
        if text is None:
            continue
        module = name[:-3]
        body = entry_body(text)
        entries = []
        for match in ALIAS_RE.finditer(text.replace("\r\n", "\n")):
            entries.append((match.group(1), (match.group(2), match.group(3))))
        if body is not None:
            imports = dict((m.group(2), m.group(1)) for m in
                           IMPORT_RE.finditer(text.replace("\r\n", "\n")))
            for alias, called in [
                    (alias, re.findall(r"\b" + alias + r"\.(\w+)\(", body))
                    for alias in imports]:
                if called:
                    entries.append((alias, (imports[alias], called[0])))
        if entries:
            table[module] = entries
    return table


def depth_of(module, table, seen=None):
    """Longest alias chain from (module) to a root, as a call multiplier."""
    seen = set() if seen is None else seen
    if module in seen:
        return -1
    seen = seen | {module}
    entries = table.get(module) or []
    if not entries:
        return 0
    best = 0
    for _alias, (parent_module, _fn) in entries:
        sub = depth_of(parent_module, table, seen)
        if sub < 0:
            return -1
        if sub + 1 > best:
            best = sub + 1
    return best


def read_module(path):
    with open(path, "rb") as handle:
        raw = handle.read()
    for enc in ("utf-8", "utf-8-sig"):
        try:
            return raw.decode(enc), None
        except UnicodeDecodeError:
            continue
    return None, "not utf-8 decodable"


def scan():
    rows = []
    for name in sorted(os.listdir(OS_DIR)):
        if not name.endswith(".py") or name.startswith("test_"):
            continue
        path = os.path.join(OS_DIR, name)
        text, error = read_module(path)
        if text is None:
            rows.append({"module": name[:-3], "file": name,
                         "state": "unreadable", "detail": error,
                         "depth": None, "calls": None, "parent": None})
            continue
        body = entry_body(text)
        if body is None:
            continue
        alias, parent_import = parent_alias(body, text)
        calls = body.count(alias + "(") if alias else 0
        rows.append({"module": name[:-3], "file": name,
                     "state": "ok" if alias else "root",
                     "detail": "",
                     "depth": None, "calls": calls,
                     "parent": parent_import})
    return rows


def chain_depth(rows, table):
    """Depth = number of alias hops to a root, per entry module."""
    for row in rows:
        row["depth"] = depth_of(row["module"], table)
    return rows


def report(rows):
    lines = []
    lines.append("PROBE-SEAM FANOUT MAP")
    readable = [r for r in rows if r["state"] in ("ok", "root")]
    unreadable = [r for r in rows if r["state"] == "unreadable"]
    chains = sorted([r for r in rows if r["state"] == "ok"],
                    key=lambda r: (-(r["depth"] or 0), r["module"]))
    lines.append("entries=%d readable=%d unreadable=%d"
                 % (len(rows), len(readable), len(unreadable)))
    for row in unreadable:
        lines.append("UNREADABLE %s %s" % (row["file"], row["detail"]))
    fanout = 0
    for row in chains:
        expected = 2 ** (row["depth"] or 0)
        if row["calls"] >= 2:
            fanout += 1
        lines.append("DEPTH %-2s CALLS %s 2^d=%-5s %s"
                     % (row["depth"], row["calls"], expected, row["module"]))
    worst = max([(r["depth"] or 0) for r in chains] or [0])
    lines.append("MAXDEPTH=%d FANOUT_LAYERS=%d THEORETICAL_CALLS=2^%d=%d"
                 % (worst, fanout, worst, 2 ** worst))
    lines.append("SHAPE-ONLY: this counts parent calls per entry body, not "
                 "seconds")
    return lines


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--evidence", default=None)
    args = parser.parse_args(argv)
    rows = chain_depth(scan(), alias_table())
    lines = report(rows)
    text = "\n".join(lines) + "\n"
    sys.stdout.write(text)
    if args.evidence:
        path = args.evidence
        if not os.path.isabs(path):
            path = os.path.join(BASE, path)
        folder = os.path.dirname(path)
        if folder and not os.path.isdir(folder):
            os.makedirs(folder)
        with open(path, "wb") as handle:
            handle.write(text.encode("utf-8"))
        sys.stdout.write("EVIDENCE %s bytes=%d lines=%d\n"
                         % (os.path.basename(path),
                            len(text.encode("utf-8")), len(lines)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
