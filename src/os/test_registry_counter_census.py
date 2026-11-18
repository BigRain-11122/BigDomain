"""Battery suite for src/os/registry_counter_census.py - AC-RCC1..AC-RCC5.

AC-RCC1..AC-RCC4 were pre-registered in src/os/backlog.md (R2918 row) BEFORE
this file existed. The census answers one board question with a measured list
instead of an assumed number: which registry rows can the shipped battery
reader refute at run time, and which cannot.

Scope, stated honestly: the census is STATIC (it reads suite source, never runs
it), and its literal extractor cannot see a SUITE row assembled from several
literals, so its READABLE class is a LOWER bound and its UNPARSED class is an
upper bound on real unreadability. The fixture world below drives that limit
deliberately rather than pretending the reader is exact.

Read-only against the repo: the registry, the pin and the suite sources are
byte-signed before and after. ASCII source, stdlib only, no clock, no network.
"""
import io
import json
import os
import re
import sys
import tempfile
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
TOOL = os.path.join(HERE, 'registry_counter_census.py')
REGISTRY = os.path.join(ROOT, 'src', 'sandbox', 'reconcile_all.py')
PIN = os.path.join(HERE, 'registry_counter_census_pin.json')

if HERE not in sys.path:
    sys.path.insert(0, HERE)
import registry_counter_census as RCC  # noqa: E402

CHECKS = 0
LABELS = []


def ok(cond, label):
    global CHECKS
    assert cond, 'FAIL: ' + label
    CHECKS += 1
    LABELS.append(label)
    print('PASS ' + label)


def digest(path):
    with io.open(path, 'rb') as handle:
        return len(handle.read()), handle.read()


def build_world():
    """A private world: one registry, three suites, one of each class."""
    root = tempfile.mkdtemp(prefix='bd-rcc-')
    sandbox = os.path.join(root, 'sandbox')
    os.makedirs(os.path.join(sandbox, 'probe'))
    reg = os.path.join(sandbox, 'reconcile_all.py')
    with io.open(reg, 'w', encoding='utf-8', newline='\n') as handle:
        handle.write(
            'import os\n'
            'SUITES = [\n'
            '    ("probe-readable", os.path.join("probe", "read.py"), 3),\n'
            '    ("probe-assembled", os.path.join("probe", "asm.py"), 4),\n'
            '    ("probe-silent", os.path.join("probe", "sil.py"), 2),\n'
            ']\n')
    files = {
        'read.py': 'print("SUITE PASS %d/%d" % (3, 3))\n',
        'asm.py': 'print("SUITE PASS", 4, "/", 4)\n',
        'sil.py': 'print("PASS only")\n',
    }
    for name, body in files.items():
        with io.open(os.path.join(sandbox, 'probe', name), 'w',
                     encoding='utf-8', newline='\n') as handle:
            handle.write(body)
    return root, sandbox, reg


def main():
    before_reg = digest(REGISTRY)
    before_pin = digest(PIN)

    report = RCC.census()
    walked = RCC.registry_rows(REGISTRY)
    ok(report['rows'] == len(walked),
       'AC-RCC1-R1 the census walked every row its own AST read: %d == %d'
       % (report['rows'], len(walked)))
    total = sum(len(report[k]) for k in ('READABLE', 'UNPARSED', 'SILENT'))
    ok(total == report['rows'],
       'AC-RCC1-R2 the three classes are total: %d == %d' % (total,
                                                             report['rows']))
    labels = report['READABLE'] + report['UNPARSED'] + report['SILENT']
    ok(len(labels) == len(set(labels)),
       'AC-RCC1-R3 no label is counted twice across classes')

    pinned = json.loads(io.open(PIN, encoding='utf-8').read())
    ok(sum(len(v) for v in pinned.values()) == report['rows'],
       'AC-RCC2-R0 the pin still names every row (a new registry row must '
       'refresh the pin, which is the one place the population is written)')
    ok(RCC.compare(report, pinned) == [],
       'AC-RCC2-R1 the shipped tree matches its pin two-way')
    root, sandbox, reg = build_world()
    try:
        small = RCC.census(registry=reg, sandbox=sandbox)
        ok(len(small['READABLE']) == 1 and small['READABLE'][0] ==
           'probe-readable',
           'AC-RCC2-R2 the fixture world reads exactly one readable row')
        ok(len(small['SILENT']) == 1 and small['SILENT'][0] == 'probe-silent',
           'AC-RCC2-R3 a file that prints no SUITE row reads silent')
        ok(len(small['UNPARSED']) == 1,
           'AC-RCC2-R4 a SUITE row assembled from literals reads unparsed '
           '(the extractor limit, measured rather than assumed)')
        doctored = dict((k, list(v)) for k, v in
                        ((key, small[key]) for key in
                         ('READABLE', 'UNPARSED', 'SILENT')))
        fails = RCC.compare(small, {'readable': ['probe-silent'],
                                    'unparsed': [],
                                    'silent': []})
        ok(fails != [],
           'AC-RCC2-R5 a pin naming the wrong class is refused: %s'
           % ' '.join(fails))
    finally:
        shutil.rmtree(root, ignore_errors=True)

    ok(digest(REGISTRY) == before_reg,
       'AC-RCC3-R1 the registry is byte-identical after the census')
    ok(digest(PIN) == before_pin,
       'AC-RCC3-R2 the pin is byte-identical after the census')
    source = io.open(TOOL, encoding='utf-8').read()
    ok('parse_suite_row' in source and 'SUITE_LINE_PUNCT' not in source,
       'AC-RCC3-R3 the parser is imported from the tool, not re-declared here')
    ok('importlib' in source,
       'AC-RCC3-R4 the reader is loaded by path from tools/battery_shard.py')

    ok(all(ord(ch) < 128 for ch in source),
       'AC-RCC4-R1 the census source is pure ASCII')
    imports = set(re.findall(r'(?m)^import ([a-zA-Z_][\w.]*)', source))
    imports |= set(re.findall(r'(?m)^from ([a-zA-Z_][\w.]*) import', source))
    allowed = {'ast', 'importlib', 'io', 'json', 'os', 're', 'sys',
               'importlib.util'}
    ok(imports <= allowed,
       'AC-RCC4-R2 stdlib only, no network module: %s'
       % ','.join(sorted(imports - allowed)))

    # AC-RCC5 (R2920): this suite must SPEAK the dialect the battery reader can
    # compare, because a bare 'SUITE PASS <n> checks' is refused by that reader
    # (a check count is not a criteria count), which left this row's registry
    # crit unrefuted for two rounds. The declaration is rendered from this run's
    # own numbers and read BACK through the shipped reader, with the declaration
    # stripped as the red control so a reader that always answers cannot pass.
    module = RCC.reader()
    ok(module.parse_criteria_unit('suite: 18 assertions over 5 criteria\n') == 5,
       'AC-RCC5-R1 the shipped reader reads this declaration dialect')
    ok(module.parse_criteria_unit('PASS only\n') is None,
       'AC-RCC5-R2 the same reader reads a missing declaration as None')
    ok(module.parse_suite_row('SUITE PASS %d checks\n' % CHECKS) is None,
       'AC-RCC5-R3 a checks-only leaf stays refused rather than guessed')

    # Both numbers are DERIVED from this run, so the registry row stays the only
    # typed count and a new criterion demands a row edit instead of a hand edit.
    acs = sorted({match.group(0) for match in
                  (re.match(r'AC-[A-Z]+[0-9]*', label) for label in LABELS)
                  if match})
    declared = 'suite: %d assertions over %d criteria\n' % (CHECKS, len(acs))
    assert module.parse_criteria_unit(declared) == len(acs), \
        'FAIL: rendered declaration does not read back as %d' % len(acs)
    print(declared.rstrip('\n'))
    print('SUITE PASS %d checks' % CHECKS)


if __name__ == '__main__':
    main()
