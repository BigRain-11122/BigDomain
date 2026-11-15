"""Battery suite for src/os/scan_five_still.py - criteria AC-SFS1..AC-SFS6.

WHY: the group ledger writes wildcard forms ("no reply cites D-20261114-0x") and
a token regex without a right-hand boundary harvests D-20261114-0 out of them,
inventing a decision that does not exist. Every round's decisions face reads
through this scanner, so the boundary is pinned here.

Criteria AC-SFS1..AC-SFS6 were written into src/os/backlog.md in the SAME window
as this suite, NOT before it: the boundary repair and the measurement came first
and the pinning was recorded afterwards, which is disclosed rather than backdated.
Source discipline: pure ASCII, stdlib only, no clock, no network.
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOL = os.path.join(ROOT, 'src', 'os', 'scan_five_still.py')
DEC = os.path.join(os.path.dirname(os.path.dirname(ROOT)), 'docs', 'decisions.md')
FAILS = []
CHECKS = []


def ok(name, cond, detail=''):
    CHECKS.append(name)
    if cond:
        print('  | PASS %s %s' % (name, detail))
    else:
        FAILS.append(name)
        print('  | FAIL %s %s' % (name, detail))


def load_tool():
    """The scanner is a top-level script, so its faces print at exec time."""
    src = io.open(TOOL, 'r', encoding='utf-8').read()
    ns = {'__name__': 'scan_under_test', '__file__': TOOL}
    buf = io.StringIO()
    keep = sys.stdout
    err = ''
    try:
        sys.stdout = buf
        exec(compile(src, TOOL, 'exec'), ns)
    except SystemExit:
        pass
    except Exception as exc:  # noqa: BLE001
        err = 'E_%s: %s' % (type(exc).__name__, exc)
    finally:
        sys.stdout = keep
    return ns, src, buf.getvalue(), err


def main():
    if not os.path.isfile(TOOL):
        print('SUITE FAIL 0/6 tool missing')
        return 1
    ns, src, out, err = load_tool()
    tokre = ns['TOKRE']

    # AC-SFS1: the wildcard forms the group ledger actually writes
    wild = ['no reply cites D-20261114-0x today',
            'C-20261010-0x wildcard',
            'P-2026-1-2-3x tail']
    got = [tokre.findall(t) for t in wild]
    ok('AC-SFS1 a wildcard form yields no token', got == [[], [], []], 'got=%s' % got)

    # AC-SFS2: real tokens are still matched
    real = ['D-20261114-01 stands', 'C-20261010-02 shipped',
            'BD-PROP-009 open', 'OH-20261014 landed',
            'XL-2026-10-14-01 ok', 'P-2026-09-24-56 carried']
    want = ['D-20261114-01', 'C-20261010-02', 'BD-PROP-009',
            'OH-20261014', 'XL-2026-10-14-01', 'P-2026-09-24-56']
    got = [tokre.findall(t) for t in real]
    ok('AC-SFS2 every real token form is still matched',
       [g[0] if g else '' for g in got] == want,
       'got=%s' % [g[0] if g else '' for g in got][:3])

    # AC-SFS3: boundaries that are NOT alphanumeric still close a token
    tails = ['D-20261114-01.', 'D-20261114-01,', 'D-20261114-01)', 'D-20261114-01']
    got = [tokre.findall(t) for t in tails]
    ok('AC-SFS3 punctuation, comma, paren and end-of-line all close a token',
       all(g == ['D-20261114-01'] for g in got), 'got=%s' % got)

    # AC-SFS4: the live face no longer carries the phantom
    phantom = []
    live = 0
    if os.path.isfile(DEC):
        text = io.open(DEC, 'r', encoding='utf-8-sig', errors='replace').read()
        toks = set(re.findall(r'(?:D-\d{8}-\d+|C-\d{8}-\d+)(?![0-9A-Za-z])', text))
        live = len(toks)
        phantom = sorted(t for t in toks if t.endswith('-0'))
    ok('AC-SFS4 the live decisions face carries no zero-suffix phantom',
       not phantom, 'tokens=%d phantom=%s' % (live, phantom[:3]))

    # AC-SFS5: the scan still runs and prints its faces
    faces = [f for f in ('[LEDGER]', '[DEC]', '[ORD]', '[BENCH]') if f in out]
    ok('AC-SFS5 the scan runs and prints its faces',
       not err and len(faces) >= 3, 'err=%s faces=%s' % (err[:40], faces))

    # AC-SFS6: hygiene, one registry row at six criteria
    ok('AC-SFS6 tool source is pure ASCII', all(ord(c) < 128 for c in src))
    reg = io.open(os.path.join(ROOT, 'src', 'sandbox', 'reconcile_all.py'),
                  'r', encoding='utf-8').read()
    hits = [m.start() for m in re.finditer(r'"os-scan-five-still"', reg)]
    rows = []
    for pos in hits:
        found = re.search(r'test_scan_five_still\.py"\)\s*,\s*(\d+)', reg[pos:pos + 160])
        if found:
            rows.append(found.group(1))
    ok('AC-SFS6 exactly one battery row declares six criteria',
       rows == ['6'], 'rows=%s' % rows)

    total = len(CHECKS)
    if FAILS:
        print('SUITE FAIL %d/%d failed=%s' % (total - len(FAILS), total, FAILS))
        return 1
    print('SUITE PASS %d/%d' % (total, total))
    return 0


if __name__ == '__main__':
    sys.exit(main())
