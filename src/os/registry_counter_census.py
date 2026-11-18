"""registry_counter_census.py - which registry rows can be refuted at run time.

Why this exists: every row of src/sandbox/reconcile_all.py SUITES declares an
expected criteria count, and most of those numbers are typed in exactly one
place, so nothing refuses a second edit that leaves them wrong. R2917 bound ONE
row to its own suite. The R2918 board question is whether that binding is worth
extending, and it cannot be answered without knowing WHICH rows the shipped
battery reader can even read: a suite that prints no parseable counter can never
refute its row.

What is measured, per registry row, by reading the suite SOURCE (never running
it): does the file contain a print of a SUITE row whose leaf shape the shipped
tools/battery_shard.py reader parses? Three classes, total and disjoint:

  READABLE - at least one printed SUITE leaf is parsed by the shipped reader,
             so the battery's crit_mismatch comparison can see a drift.
  UNPARSED - the file prints a SUITE row, but no printed leaf is parseable
             (e.g. "SUITE PASS 163 checks" states no FAIL count, so the
             shipped reader refuses it by design).
  SILENT   - the file prints no SUITE row at all, counting both the literals
             on a print line and the module constants that line references
             (a row printed through `V = "SUITE PASS"` is not silent); the
             row's number is typed and nothing on the run path compares it.

The parser is IMPORTED from the tool, not copied: a second regex family here
would be a second opinion instead of the battery's own one.

Disclosed limits: this is a STATIC upper bound. A shape found in the source is
not proof that the runtime line carries the declared number - a suite may print
a counter whose value is an assertion count rather than its criteria count.
Read-only, ASCII source, stdlib only, zero network.

Criteria AC-RCC1..AC-RCC4 are pre-registered in src/os/backlog.md (R2918 row).
"""
import ast
import importlib.util
import io
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
REGISTRY = os.path.join(ROOT, 'src', 'sandbox', 'reconcile_all.py')
TOOL = os.path.join(ROOT, 'tools', 'battery_shard.py')
PIN = os.path.join(BASE, 'registry_counter_census_pin.json')
LABEL = 'os-registry-counter-census'

PLACEHOLDER = re.compile(r'%[dsrf]|\{[^}]*\}')
PRINT_LINE = re.compile(r'(?:print|write)\s*\(')
STRING_LIT = re.compile(r'"([^"\\]*(?:\\.[^"\\]*)*)"|\'([^\'\\]*(?:\\.[^\'\\]*)*)\'')


class CensusError(Exception):
    def __init__(self, code, detail=''):
        Exception.__init__(self, code)
        self.code = code
        self.detail = detail


def reader():
    """The shipped reader, imported by path so no tool side effect is trusted."""
    spec = importlib.util.spec_from_file_location('bd_battery_shard', TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def registry_rows(path):
    src = io.open(path, encoding='utf-8').read()
    tree = ast.parse(src)
    out = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(t, ast.Name) and t.id == 'SUITES'
                   for t in node.targets):
            continue
        for elt in node.value.elts:
            label = elt.elts[0].value
            path_node = elt.elts[1]
            crit = elt.elts[2].value
            if isinstance(path_node, ast.Call):
                rel = os.path.join(*[a.value for a in path_node.args])
            else:
                rel = path_node.value
            out.append((label, os.path.normpath(rel), crit))
    return out


def _suite_literals(node):
    """String literals containing SUITE reachable from an assignment value.

    ast.walk reaches both arms of an if/else expression, the left operand of a
    `%` format and the literal parts of an f-string, which are the three shapes
    the shipped suites use to name their SUITE row once and print it later.
    """
    out = []
    for sub in ast.walk(node):
        if not isinstance(sub, ast.Constant):
            continue
        if isinstance(sub.value, str) and 'SUITE' in sub.value:
            out.append(sub.value)
    return out


def suite_constants(text):
    """Names bound to a string literal that contains SUITE (simple propagation).

    leaf_lines reads one line at a time, so a suite that prints its row through
    a constant (`V = "SUITE PASS"` ... `print("%s %d/%d" % (V, ...))`) looked
    SILENT - a statement about this reader, not about the suite. Collecting the
    constant assignments (both arms of an if/else) is the smallest propagation
    that makes the class name mean what it says.
    """
    out = {}
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return out
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        literals = _suite_literals(node.value)
        if not literals:
            continue
        for target in node.targets:
            if isinstance(target, ast.Name):
                out.setdefault(target.id, []).extend(literals)
    return out


def leaf_lines(text, consts=None):
    """Every printed leaf that starts with SUITE, placeholders neutralised.

    Returns (leaves, assembled). `assembled` counts print lines whose SUITE row
    is built from more than one literal (print("SUITE PASS", n, "/", m)), i.e.
    rows THIS READER cannot see whole even though the runtime line may be
    parseable - the extractor's own limit, counted rather than hidden in the
    unparsed bucket.

    A print line whose own literals carry no SUITE still counts when it
    references a name from suite_constants(): the row exists in the source even
    though this one line does not spell it.
    """
    out = []
    assembled = 0
    consts = consts or {}
    for line in text.split('\n'):
        if not PRINT_LINE.search(line):
            continue
        literals = [a if a else b for a, b in STRING_LIT.findall(line)]
        hits = [lit for lit in literals if 'SUITE' in lit]
        if not hits:
            for name, values in consts.items():
                if re.search(r'\b%s\b' % re.escape(name), line):
                    hits.extend(values)
        if not hits:
            continue
        if len(literals) > 1:
            assembled += 1
        for literal in hits:
            out.append(PLACEHOLDER.sub('7', literal))
    return out, assembled


def classify(text, module, consts=None):
    leaves, assembled = leaf_lines(text, consts)
    if not leaves:
        return 'SILENT', assembled
    for leaf in leaves:
        if module.parse_suite_row(leaf + '\n') is not None:
            return 'READABLE', assembled
    return 'UNPARSED', assembled


def census(registry=REGISTRY, sandbox=None):
    module = reader()
    rows = registry_rows(registry)
    sandbox = sandbox or os.path.dirname(registry)
    report = {'rows': len(rows), 'READABLE': [], 'UNPARSED': [],
              'SILENT': [], 'assembled': 0}
    for label, rel, crit in rows:
        path = os.path.join(sandbox, rel)
        if not os.path.exists(path):
            raise CensusError('E_RCC_MISSING_SUITE', '%s %s' % (label, rel))
        text = io.open(path, encoding='utf-8', errors='replace').read()
        kind, assembled = classify(text, module, suite_constants(text))
        report['assembled'] += assembled
        report[kind].append(label)
    total = sum(len(report[kind])
                for kind in ('READABLE', 'UNPARSED', 'SILENT'))
    if total != report['rows']:
        raise CensusError('E_RCC_NOT_TOTAL',
                          '%d != %d' % (total, report['rows']))
    return report


def pin_shape(report):
    return {'readable': sorted(report['READABLE']),
            'unparsed': sorted(report['UNPARSED']),
            'silent': sorted(report['SILENT'])}


def compare(report, pinned):
    """Two-way diff per class; an unknown class is a refusal, not a skip."""
    fails = []
    measured = pin_shape(report)
    for key in ('readable', 'unparsed', 'silent'):
        got = set(measured[key])
        want = set(pinned.get(key, []))
        if got != want:
            fails.append('%s +%d -%d' % (key, len(got - want), len(want - got)))
    for key in pinned:
        if key not in measured:
            fails.append('unknown-class %s' % key)
    return fails


def render(report):
    return ('REGISTRY COUNTER CENSUS rows=%d readable=%d unparsed=%d '
            'silent=%d assembled_print_lines=%d'
            % (report['rows'], len(report['READABLE']),
               len(report['UNPARSED']), len(report['SILENT']),
               report['assembled']))


def main(argv):
    as_json = False
    check = False
    write_pin = False
    for arg in argv:
        if arg == '--json':
            as_json = True
        elif arg == '--check':
            check = True
        elif arg == '--write-pin':
            write_pin = True
        elif arg in ('--help', '-h'):
            sys.stdout.write('usage: registry_counter_census.py '
                             '[--json] [--check] [--write-pin]\n')
            return 0
        else:
            sys.stdout.write('E_RCC_BAD_ARGS %s\n' % arg)
            return 5
    try:
        report = census()
    except CensusError as exc:
        sys.stdout.write('%s %s\n' % (exc.code, exc.detail))
        return 2
    if write_pin:
        with io.open(PIN, 'w', encoding='utf-8', newline='\n') as handle:
            handle.write(json.dumps(pin_shape(report), indent=2,
                                    sort_keys=True) + '\n')
    if as_json:
        sys.stdout.write(json.dumps(pin_shape(report), sort_keys=True) + '\n')
    else:
        sys.stdout.write(render(report) + '\n')
    if check:
        if not os.path.exists(PIN):
            sys.stdout.write('E_RCC_NO_PIN %s\n' % PIN)
            return 2
        pinned = json.loads(io.open(PIN, encoding='utf-8').read())
        fails = compare(report, pinned)
        if fails:
            sys.stdout.write('VERDICT FAIL %s\n' % ' '.join(fails))
            return 2
        sys.stdout.write('VERDICT PASS pinned=%d\n'
                         % sum(len(v) for v in pinned.values()))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
