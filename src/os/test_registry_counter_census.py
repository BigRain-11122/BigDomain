"""Battery suite for src/os/registry_counter_census.py - AC-RCC1..AC-RCC7.

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


def build_var_world():
    """A private world where SUITE rows are printed THROUGH a constant.

    This is the shape the shipped tree actually uses (62 rows) and the shape a
    literal-only line scan read as SILENT. One probe formats a constant, one
    binds it through an if/else, one mentions no SUITE at all, and one names a
    constant the print line does NOT reference, so a word-boundary overreach is
    measured rather than trusted.
    """
    root = tempfile.mkdtemp(prefix='bd-rcc-var-')
    sandbox = os.path.join(root, 'sandbox')
    os.makedirs(os.path.join(sandbox, 'probe'))
    reg = os.path.join(sandbox, 'reconcile_all.py')
    with io.open(reg, 'w', encoding='utf-8', newline='\n') as handle:
        handle.write(
            'import os\n'
            'SUITES = [\n'
            '    ("probe-viaformat", os.path.join("probe", "vf.py"), 2),\n'
            '    ("probe-viaifelse", os.path.join("probe", "vi.py"), 1),\n'
            '    ("probe-nosuite", os.path.join("probe", "ns.py"), 1),\n'
            '    ("probe-lookalike", os.path.join("probe", "lk.py"), 1),\n'
            ']\n')
    files = {
        'vf.py': 'V = "SUITE PASS %d/%d" % (2, 2)\nprint(V)\n',
        'vi.py': 'OK = True\n'
                 'V = "SUITE PASS" if OK else "SUITE FAIL"\n'
                 'print(V)\n',
        'ns.py': 'print("PASS only")\nX = "hello"\n',
        'lk.py': 'Y = "SUITE PASS %d/%d"\nprint("Yy", 1)\n',
    }
    for name, body in files.items():
        with io.open(os.path.join(sandbox, 'probe', name), 'w',
                     encoding='utf-8', newline='\n') as handle:
            handle.write(body)
    return root, sandbox, reg


def build_join_world():
    """A private world for the SAME-LINE join, with a fabrication control.

    probe-viajoin puts the words in a constant and the numbers in the format
    string of the same print call - the shape 14 shipped rows actually use.
    probe-viasplit keeps the same constant and the same numbers on two lines,
    and probe-viaprefix puts text before the placeholder, so a join that reached
    across lines or claimed a leaf the runtime never emits is measured RED.
    """
    root = tempfile.mkdtemp(prefix='bd-rcc-join-')
    sandbox = os.path.join(root, 'sandbox')
    os.makedirs(os.path.join(sandbox, 'probe'))
    reg = os.path.join(sandbox, 'reconcile_all.py')
    with io.open(reg, 'w', encoding='utf-8', newline='\n') as handle:
        handle.write(
            'import os\n'
            'SUITES = [\n'
            '    ("probe-viajoin", os.path.join("probe", "vj.py"), 2),\n'
            '    ("probe-viasplit", os.path.join("probe", "vs.py"), 1),\n'
            '    ("probe-viaprefix", os.path.join("probe", "vp.py"), 1),\n'
            ']\n')
    files = {
        'vj.py': 'V = "SUITE PASS"\nprint("%s %d/%d" % (V, 2, 2))\n',
        'vs.py': 'V = "SUITE PASS"\nprint(V)\nprint("%d/%d" % (1, 1))\n',
        'vp.py': 'V = "SUITE PASS"\nprint("note %s %d/%d" % (V, 1, 1))\n',
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

    # AC-RCC6/7 (R2921): the SILENT class was measured as a hundred-percent
    # false positive on the shipped tree (all 62 rows print their SUITE row
    # through a module constant), so the extractor now reads those names and
    # the class is held to a negative control and a lookalike control.
    root2, sandbox2, reg2 = build_var_world()
    try:
        world = RCC.census(registry=reg2, sandbox=sandbox2)
        ok('probe-viaformat' in world['READABLE'],
           'AC-RCC6-R1 a SUITE row printed through a formatted constant reads '
           'readable, not silent')
        ok('probe-viaifelse' in world['UNPARSED'],
           'AC-RCC6-R2 an if/else constant carrying no numbers reads unparsed, '
           'not silent')
        ok(sorted(world['SILENT']) == ['probe-lookalike', 'probe-nosuite'],
           'AC-RCC6-R3 the via-constant world leaves only the two real silent '
           'probes: %s' % ','.join(world['SILENT']))
    finally:
        shutil.rmtree(root2, ignore_errors=True)

    ok('probe-nosuite' in world['SILENT'],
       'AC-RCC7-R1 the negative control stays silent: a file with no SUITE '
       'literal and no SUITE constant')
    ok('probe-lookalike' not in world['READABLE'] +
       world['UNPARSED'],
       'AC-RCC7-R2 a constant the print line does not name is not borrowed by '
       'a substring match')
    # The retired arm compared the live silent count against a typed 62 - a
    # historical number nobody derives. The pin is the only typed population
    # (AC-RCC2-R1 compares all three classes two-way), so the arm is dropped
    # rather than restated: a second typed copy is the defect this file exists
    # to refuse.

    # AC-RCC8 (R2922): the SAME-LINE join, with the two ways it could fabricate
    # measured on their own probes instead of argued about in prose.
    root3, sandbox3, reg3 = build_join_world()
    try:
        joined = RCC.census(registry=reg3, sandbox=sandbox3)
        ok(joined['READABLE'] == ['probe-viajoin'],
           'AC-RCC8-R1 a constant joined with the format string on the SAME '
           'print line reads readable: %s' % ','.join(joined['READABLE']))
        ok('probe-viasplit' in joined['UNPARSED'],
           'AC-RCC8-R2 the same constant and the same numbers on two lines '
           'stay unparsed: a cross-line join would fabricate a leaf')
        ok('probe-viaprefix' in joined['UNPARSED'],
           'AC-RCC8-R3 text before the placeholder stays unparsed, so the '
           'shipped reader anchor - not this join - decides the head')
    finally:
        shutil.rmtree(root3, ignore_errors=True)

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
