"""Census: does every registered suite emit the battery-law closing row?

The law lives in one place, tools/battery_shard.py SUITE_LINE, and two shipped
readers ask the same question (src/os/run_identity.py SUITE_RE and
src/os/runner_suite_timeout_headroom.py SUITE_LINE_RE). This census takes the
pattern FROM the law and asks each registered suite file, by source, whether it
carries a format literal that can produce a matching line.

Read-only, stdlib only, no clock, no network. The verdict is a SOURCE-LEVEL
reading of format literals, not an output-level proof: a suite that builds the
row through a helper module outside its own file is reported as non_law, and the
remedy is to read that file rather than to trust this number.

Usage:
    python tools/suite_closing_row_census.py [--root .] [--quiet-list]
"""

import argparse
import os
import re
import sys

NUM = r"(%d|\{[^{}\n]*\}|\d+)"
LAW_DIRECT = re.compile(r"^SUITE (PASS|FAIL) " + NUM + r"\s*/\s*" + NUM)
LAW_STATUS = re.compile(r"^SUITE %s " + NUM + r"\s*/\s*" + NUM)
NO_STATUS = re.compile(r"^SUITE " + NUM + r"\s*/\s*" + NUM)
LEGACY_PAREN = re.compile(r"^SUITE (%s )?\(%d/%d")
LEGACY_LABEL = re.compile(r"^SUITE [A-Za-z0-9_.-]+: *%d/%d")
LEGACY_STATUS_COLON = re.compile(r"^SUITE %s: ")
NO_NUMBERS = re.compile(r"^SUITE (PASS|FAIL)$")
LEGACY_LOWER = re.compile(r"^suite: %d assertions over %d criteria")
LITERAL = re.compile(r'"([^"\n]*(?:SUITE|suite)[^"\n]*)"'
                     r"|'([^'\n]*(?:SUITE|suite)[^'\n]*)'")
# The 54 no_numbers suites R2845 audited at output level build the row in two
# halves: a conditionally bound verdict name, then a format that slots it in.
SPLIT_BIND = re.compile(r'(\w+)\s*=\s*"SUITE (?:PASS|FAIL)"\s+if\b[^\n]*\belse\s+'
                        r'"SUITE (?:PASS|FAIL)"')
SPLIT_ROW = re.compile(r'"([^"\n]*%s[^"\n]*)"\s*%\s*\(\s*(\w+)')
SPLIT_NUM = re.compile(r"%d\s*/\s*%d")
# The runner derives a verdict from numbers-only rows, so a source literal of
# "SUITE %d/%d" (or the same with a PASS/FAIL word or a %s slot) is law there.
LAW_NUMERIC = re.compile(r"^SUITE " + NUM + r"\s*/\s*" + NUM + r"(\s+(PASS|FAIL))?$")
LAW_NUMERIC_SLOT = re.compile(r"^SUITE " + NUM + r"\s*/\s*" + NUM + r"\s+%s$")


def normalise(lit):
    """Drop a literal leading newline escape so the law can be asked of the text."""
    return lit.replace("\\n", "").replace("\\t", "").strip()


def split_law(src):
    """Does this source build the row as a conditional verdict name plus a format?

    Both halves must hold, and the binding must be conditional: an unconditional
    NAME = "SUITE PASS" would print PASS over a red run, so it stays non-law.
    """
    names = set()
    for m in SPLIT_BIND.finditer(src):
        if "PASS" in m.group(0) and "FAIL" in m.group(0):
            names.add(m.group(1))
    if not names:
        return False
    for m in SPLIT_ROW.finditer(src):
        if m.group(2) in names and SPLIT_NUM.search(m.group(1)):
            return True
    return False


def classify(src):
    """Return the strongest shape family found in this suite's source."""
    shapes = []
    if split_law(src):
        shapes.append("law_split")
    for m in LITERAL.finditer(src):
        lit = normalise(m.group(1) or m.group(2) or "")
        if LAW_DIRECT.match(lit):
            shapes.append("law_direct")
        elif LAW_STATUS.match(lit):
            # the status word is injected: the law holds only if PASS/FAIL is bound
            binds = re.search(r'"PASS"|"FAIL"|PASS if|FAIL if|if not fail|if fail == 0', src)
            shapes.append("law_status" if binds else "suspect_status")
        elif LAW_NUMERIC.match(lit):
            # the runner derives PASS/FAIL from p==t for this shape
            shapes.append("law_numeric")
        elif LAW_NUMERIC_SLOT.match(lit):
            binds = ('"PASS"' in src and '"FAIL"' in src)
            shapes.append("law_numeric_slot" if binds else "no_status")
        elif NO_STATUS.match(lit):
            shapes.append("no_status")
        elif LEGACY_PAREN.match(lit):
            shapes.append("legacy_paren")
        elif LEGACY_LABEL.match(lit):
            shapes.append("legacy_label")
        elif LEGACY_STATUS_COLON.match(lit):
            shapes.append("legacy_status_colon")
        elif NO_NUMBERS.match(lit):
            shapes.append("no_numbers")
        elif LEGACY_LOWER.match(lit):
            shapes.append("legacy_lower")
        else:
            shapes.append("other")
    for name in ("law_direct", "law_status", "law_split", "law_numeric",
                 "law_numeric_slot", "suspect_status", "no_status",
                 "legacy_paren", "legacy_label", "legacy_status_colon",
                 "no_numbers", "legacy_lower", "other"):
        if name in shapes:
            return name
    return "no_row"


def law_pattern(root):
    """The single law: the runner's own pattern, not a copy."""
    sys.path.insert(0, os.path.join(root, "tools"))
    import battery_shard  # noqa: E402
    return battery_shard.SUITE_LINE.pattern


def registry(root):
    """The single list of suites: reconcile_all.SUITES, imported not parsed."""
    sys.path.insert(0, os.path.join(root, "src", "sandbox"))
    import reconcile_all  # noqa: E402
    return list(reconcile_all.SUITES)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--quiet-list", action="store_true")
    args = ap.parse_args(argv)

    root = os.path.abspath(args.root)
    law_re = re.compile(law_pattern(root))
    if not law_re.search("SUITE PASS 1/1") or law_re.search("SUITE PASS (1/1)"):
        print("CENSUS FAIL law pattern disagrees with a known-good line")
        return 2

    rows = registry(root)
    counts, non_law, missing = {}, [], []
    for label, rel, declared in rows:
        path = os.path.join(root, "src", "sandbox", rel)
        if not os.path.isfile(path):
            missing.append(label)
            counts["missing_file"] = counts.get("missing_file", 0) + 1
            continue
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            shape = classify(fh.read())
        counts[shape] = counts.get(shape, 0) + 1
        if shape not in ("law_direct", "law_status", "law_split", "law_numeric",
                         "law_numeric_slot"):
            non_law.append((label, shape))

    law = (counts.get("law_direct", 0) + counts.get("law_status", 0)
           + counts.get("law_split", 0) + counts.get("law_numeric", 0)
           + counts.get("law_numeric_slot", 0))
    print("CENSUS registry=%d law=%d non_law=%d missing=%d"
          % (len(rows), law, len(non_law), len(missing)))
    for name in ("law_direct", "law_status", "law_split", "law_numeric",
                 "law_numeric_slot", "suspect_status", "no_status",
                 "legacy_paren", "legacy_label", "legacy_status_colon",
                 "no_numbers", "legacy_lower", "other", "no_row", "missing_file"):
        if counts.get(name):
            print("CENSUS shape %s=%d" % (name, counts[name]))
    if not args.quiet_list:
        by_shape = {}
        for label, shape in non_law:
            by_shape.setdefault(shape, []).append(label)
        for shape in sorted(by_shape):
            print("CENSUS non_law %s: %s" % (shape, ", ".join(sorted(by_shape[shape]))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
