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

DECLARED LIMITATION (law, R2855): the status-binding test reads DOUBLE-QUOTED
verdict literals only, so a suite that binds its slot with single quotes is
classified suspect_status or no_status. That direction is conservative - it can
over-report debt and can never fake a green - and it is measured, not assumed:
of 706 registered suites, 3 carry a single-quoted PASS/FAIL token and all 3 are
law by a stronger shape (law_direct=2, law_status=1), so the blind set is 0 on
2026-11-17. AC-CEN2 pins both halves of the asymmetry (the same binding read
suspect_status single-quoted and law_status double-quoted), so teaching single
quotes later is a deliberate criterion change and not a silent drift.

Usage:
    python tools/suite_closing_row_census.py [--root .] [--quiet-list]
                                             [--list-unexecuted]

R2963 (AC-CEN9..AC-CEN10): the reading above is a SOURCE reading, and this
header says so; what it did not say was HOW WIDE the gap is. The verdict line
still counts a law literal anywhere in the file, so a suite whose only law row
sits in its docstring is counted as law while it prints a row the battery
cannot read (AC-CEN9 reproduces exactly that escape in a private world and
proves it at output level). The second face below answers the narrower
question with AST positions - is at least one law literal in a slot that can
reach the print? - and prints 'CENSUS exec law=<n> unexecuted=<m>' with
n + m == law, naming the reason families under --list-unexecuted (docstring,
dead, uncalled, unreached). It does NOT change the law count: a row with a
docstring-only law literal is still law on the verdict line, so the difference
between the two lines IS the measured blind set. Out of range and named: a row
whose string is built at run time, a law literal inside a lambda body, and a
row that builds its row in a helper module are not judged by the position face.
"""

import argparse
import ast
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
# The pair joined by other punctuation is the same row as LAW_DIRECT:
# "SUITE PASS (%d/%d criteria green)", "SUITE PASS: %d/%d", "SUITE PASS - %d/%d".
LAW_PUNCT = re.compile(r"^SUITE (PASS|FAIL)\s*[\(\:\-]\s*" + NUM + r"\s*/\s*" + NUM)
# "SUITE apidev: %d/%d criteria pass" names the suite instead of the verdict, so
# the verdict is derived from p==t there, exactly as LAW_NUMERIC does.
LAW_LABEL_PT = re.compile(
    r"^SUITE (?!PASS\b|FAIL\b)[A-Za-z0-9_.-]+:\s*" + NUM + r"\s*/\s*" + NUM)
# The remaining paren/dash skin injects the verdict: "SUITE %s (%d/%d criteria
# pass)", "SUITE %s - %d/%d green". Law only when the slot is bound to PASS/FAIL,
# otherwise the row's verdict is whatever it happened to say (suspect).
LAW_STATUS_PUNCT = re.compile(r"^SUITE %s\s*[\(\:\-]\s*" + NUM + r"\s*/\s*" + NUM)
# Counters are the third skin: criteria/expected-criteria (total), pass/passes/
# pass-lines, fail/fails/fail-lines, in any order. Read like the runner does.
COUNTER_TOTAL = re.compile(r"(?:expected-criteria|criteria)=(?:%d|\{[^{}\n]*\}|\d+)")
COUNTER_PASS = re.compile(r"(?:passes|pass-lines|pass)=(?:%d|\{[^{}\n]*\}|\d+)")
COUNTER_FAIL = re.compile(r"(?:fails|fail-lines|fail)=(?:%d|\{[^{}\n]*\}|\d+)")
# The equals-free dialect: "SUITE PASS: %d criteria, %d pass, %d fail".
COUNTER_WORD_TOTAL = re.compile(r"(?:%d|\{[^{}\n]*\}|\d+)\s+criteria\b")
COUNTER_WORD_PASS = re.compile(r"(?:%d|\{[^{}\n]*\}|\d+)\s+pass\b")
COUNTER_WORD_FAIL = re.compile(r"(?:%d|\{[^{}\n]*\}|\d+)\s+fail\b")


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


BINDS = re.compile(r'"PASS"|"FAIL"|PASS if|FAIL if|if not fail|if fail == 0')

FAMILIES = ("law_direct", "law_status", "law_split", "law_numeric",
            "law_numeric_slot", "law_punct", "law_label_pt",
            "law_counters", "law_status_colon", "law_status_punct",
            "suspect_status", "no_status", "legacy_paren",
            "legacy_label", "no_numbers", "legacy_lower", "other")

LAW_FAMILIES = ("law_direct", "law_status", "law_split", "law_numeric",
                "law_numeric_slot", "law_punct", "law_label_pt",
                "law_counters", "law_status_colon", "law_status_punct")


def shape_of_literal(lit, src):
    """Shape family of ONE literal body, read with the same chain as classify.

    Split out so the position face below asks the same questions of the same
    text that the source face asks; a second copy of this chain would be a
    second law.
    """
    lit = normalise(lit)
    if LAW_DIRECT.match(lit):
        return "law_direct"
    if LAW_STATUS.match(lit):
        # the status word is injected: the law holds only if PASS/FAIL is bound
        return "law_status" if BINDS.search(src) else "suspect_status"
    if LAW_NUMERIC.match(lit):
        # the runner derives PASS/FAIL from p==t for this shape
        return "law_numeric"
    if LAW_NUMERIC_SLOT.match(lit):
        return ("law_numeric_slot" if ('"PASS"' in src and '"FAIL"' in src)
                else "no_status")
    if LAW_PUNCT.match(lit):
        # the verdict word is explicit here, so no binding question arises
        return "law_punct"
    if LAW_LABEL_PT.match(lit):
        # verdict is derived from p==t, the same rule as law_numeric
        return "law_label_pt"
    if LAW_STATUS_PUNCT.match(lit):
        return "law_status_punct" if BINDS.search(src) else "suspect_status"
    if (COUNTER_TOTAL.search(lit) and COUNTER_PASS.search(lit)
            and COUNTER_FAIL.search(lit)) or \
            (COUNTER_WORD_TOTAL.search(lit) and COUNTER_WORD_PASS.search(lit)
             and COUNTER_WORD_FAIL.search(lit)):
        # a counter row carries total, passed and failed, so the verdict is
        # the fail count; a row without all three is not law
        return "law_counters"
    if LEGACY_STATUS_COLON.match(lit):
        # "SUITE %s: %d/%d": law only when the slot is bound to PASS/FAIL,
        # otherwise the verdict is whatever the row happened to say
        return "law_status_colon" if BINDS.search(src) else "suspect_status"
    if NO_STATUS.match(lit):
        return "no_status"
    if LEGACY_PAREN.match(lit):
        return "legacy_paren"
    if LEGACY_LABEL.match(lit):
        return "legacy_label"
    if NO_NUMBERS.match(lit):
        return "no_numbers"
    if LEGACY_LOWER.match(lit):
        return "legacy_lower"
    return "other"


def classify(src):
    """Return the strongest shape family found in this suite's source."""
    shapes = []
    if split_law(src):
        shapes.append("law_split")
    for m in LITERAL.finditer(src):
        shapes.append(shape_of_literal(m.group(1) or m.group(2) or "", src))
    for name in FAMILIES:
        if name in shapes:
            return name
    return "no_row"


def _const_false(node):
    """Is this test a constant that never runs the body? ('if False', 'while 0')"""
    if isinstance(node, ast.Constant):
        return not bool(node.value)
    if isinstance(node, ast.Name) and node.id == "False":
        return True
    return False


def _called_names(tree):
    """Function names the module calls anywhere (Name or attribute call)."""
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                names.add(func.id)
            elif isinstance(func, ast.Attribute):
                names.add(func.attr)
    return names


def _scan(node, position, called, out):
    """Collect (string value, position) for every string constant.

    position is 'live', 'docstring', 'dead' or 'uncalled'. Only a strand that
    can reach the print at run time counts as live: a standalone string
    expression is a docstring by shape, a constant-false test never runs, and a
    function the module never calls does not run when the file is executed.
    """
    if isinstance(node, ast.Constant):
        if isinstance(node.value, str):
            out.append((node.value, position))
        return
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        inner = position
        if node.name not in called and position != "dead":
            inner = "uncalled"
        for stmt in node.body:
            _scan(stmt, inner, called, out)
        for extra in node.decorator_list:
            _scan(extra, position, called, out)
        for extra in node.args.defaults:
            _scan(extra, position, called, out)
        return
    if isinstance(node, ast.If):
        dead = _const_false(node.test)
        for stmt in node.body:
            _scan(stmt, "dead" if (dead and position == "live") else position,
                  called, out)
        for stmt in node.orelse:
            _scan(stmt, position, called, out)
        _scan(node.test, position, called, out)
        return
    if isinstance(node, ast.While):
        dead = _const_false(node.test)
        for stmt in node.body:
            _scan(stmt, "dead" if (dead and position == "live") else position,
                  called, out)
        for stmt in node.orelse:
            _scan(stmt, position, called, out)
        _scan(node.test, position, called, out)
        return
    if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) \
            and isinstance(node.value.value, str):
        # a bare string statement never reaches a print
        out.append((node.value.value,
                    "docstring" if position == "live" else position))
        return
    for child in ast.iter_child_nodes(node):
        _scan(child, position, called, out)


def law_sites(src):
    """Where do this source's law literals sit? None when it will not parse.

    A row is EXECUTING only if at least one law literal sits in a live slot.
    The reason of the first non-live site is reported back so a reader can see
    whether the row is a docstring mention, dead code or an uncalled helper.
    """
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return None
    called = _called_names(tree)
    raw = []
    for stmt in tree.body:
        _scan(stmt, "live", called, raw)
    live = [normalise(value) for value, pos in raw if pos == "live"]
    sites = []
    for value, pos in raw:
        family = shape_of_literal(value, src)
        if family in LAW_FAMILIES:
            sites.append((family, pos))
    if split_law(src):
        for match in SPLIT_ROW.finditer(src):
            body = normalise(match.group(1))
            if body in live:
                sites.append(("law_split", "live"))
            else:
                sites.append(("law_split", "unreached"))
    return sites


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
    ap.add_argument("--list-unexecuted", action="store_true")
    args = ap.parse_args(argv)

    root = os.path.abspath(args.root)
    law_re = re.compile(law_pattern(root))
    if not law_re.search("SUITE PASS 1/1") or law_re.search("SUITE PASS (1/1)"):
        print("CENSUS FAIL law pattern disagrees with a known-good line")
        return 2

    rows = registry(root)
    counts, non_law, missing = {}, [], []
    exec_live, unexecuted, why = 0, [], {}
    for label, rel, declared in rows:
        path = os.path.join(root, "src", "sandbox", rel)
        if not os.path.isfile(path):
            missing.append(label)
            counts["missing_file"] = counts.get("missing_file", 0) + 1
            continue
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            text = fh.read()
        shape = classify(text)
        counts[shape] = counts.get(shape, 0) + 1
        if shape not in LAW_FAMILIES:
            non_law.append((label, shape))
            continue
        sites = law_sites(text)
        if sites is None or any(pos == "live" for _fam, pos in sites):
            # unparsable source is counted as executing: it cannot be proven
            # otherwise, and this face must never fake a narrowed blind set
            exec_live += 1
            continue
        reasons = [pos for _fam, pos in sites]
        reason = "docstring" if "docstring" in reasons else (
            "dead" if "dead" in reasons else (
                "uncalled" if "uncalled" in reasons else "unreached"))
        why[reason] = why.get(reason, 0) + 1
        unexecuted.append((label, shape, reason))

    law = 0
    for name in LAW_FAMILIES:
        law += counts.get(name, 0)
    print("CENSUS registry=%d law=%d non_law=%d missing=%d"
          % (len(rows), law, len(non_law), len(missing)))
    print("CENSUS exec law=%d unexecuted=%d" % (exec_live, len(unexecuted)))
    if unexecuted:
        print("CENSUS exec why " + " ".join(
            "%s=%d" % (name, why[name]) for name in sorted(why)))
    for name in ("law_direct", "law_status", "law_split", "law_numeric",
                 "law_numeric_slot", "law_punct", "law_label_pt",
                 "law_counters", "law_status_colon", "law_status_punct",
                 "suspect_status", "no_status", "legacy_paren",
                 "legacy_label", "no_numbers", "legacy_lower", "other",
                 "no_row", "missing_file"):
        if counts.get(name):
            print("CENSUS shape %s=%d" % (name, counts[name]))
    if not args.quiet_list:
        by_shape = {}
        for label, shape in non_law:
            by_shape.setdefault(shape, []).append(label)
        for shape in sorted(by_shape):
            print("CENSUS non_law %s: %s" % (shape, ", ".join(sorted(by_shape[shape]))))
    if args.list_unexecuted:
        by_reason = {}
        for label, shape, reason in unexecuted:
            by_reason.setdefault(reason, []).append(label)
        for reason in sorted(by_reason):
            print("CENSUS unexecuted %s: %s"
                  % (reason, ", ".join(sorted(by_reason[reason]))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
