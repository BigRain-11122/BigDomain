"""Battery suite for tools/leg_audit.py - criteria AC-LGA1..AC-LGA6.

WHY: R2886 pinned the law that a leg without a closing `SHARD rc=` row is not a
family measurement, and every window since applied it by reading logs by eye. A
law only a human applies is not a gate. This suite pins the tool that turns that
law into an exit code, and pins BOTH directions: a finished leg must be ADOPTED
(including one that honestly closed red), and a leg that lost its closing row,
lost a row, or ran a suite twice must be REJECTED by name.

PINNED BEFORE THE CODE: these six criteria were written into src/os/backlog.md in
the same window, BEFORE tools/leg_audit.py existed; the tool's first two drafts
were refuted by their own arms and narrowed on the record (see the tool's
comments) rather than by bending a criterion.

Every fixture is built in-process from three rows, so the suite never depends on
a log file that could be cleaned out from under it.
Source discipline: pure ASCII, stdlib only, no clock, no network.
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOL = os.path.join(ROOT, 'tools', 'leg_audit.py')
FAILS = []
CHECKS = []

def hdr(selected=3, crit=17, state='COMPLETE'):
    """A header that agrees with the closing row unless an arm wants it not to."""
    return ('SHARD scope=SHARD registry_suites=%d registry_criteria=%d selected=%d '
            'selected_criteria=%d cap=600s leg_cap=0s overrides=0 exact=0 state=%s'
            % (selected, crit, selected, crit, state))


HDR = hdr()
ROWS = [
    'SHARD row probe-a rc=0 pass=6 fail=0 detail=yes suite=PASS 6/6 crit=6 0.1s',
    'SHARD row probe-b rc=0 pass=9 fail=0 detail=yes suite=PASS 9/6 crit=6 0.1s',
    'SHARD row probe-c rc=0 pass=5 fail=0 detail=yes suite=PASS 5/5 crit=5 0.1s',
]
CLOSE = ('SHARD rc=0 scope=SHARD selected=3 executed=3 green=3 criteria=17 '
         'crit_mismatch=0 elapsed=1.2s')


def ok(name, cond, detail=''):
    CHECKS.append(name)
    if cond:
        print('  | PASS %s %s' % (name, detail))
    else:
        FAILS.append(name)
        print('  | FAIL %s %s' % (name, detail))


def load_tool():
    """The tool is a top-level script; exec it and take its public functions."""
    src = io.open(TOOL, 'r', encoding='utf-8').read()
    ns = {'__name__': 'leg_audit_under_test', '__file__': TOOL}
    exec(compile(src, TOOL, 'exec'), ns)
    return ns, src


def leg(header=None, rows=None, closing=True, close_line=None):
    parts = []
    if header is not False:
        parts.append(HDR if header is None else header)
    parts.extend(ROWS if rows is None else rows)
    if closing:
        parts.append(CLOSE if close_line is None else close_line)
    return '\n'.join(parts) + '\n'


def main():
    if not os.path.isfile(TOOL):
        print('SUITE FAIL 0/6 tool missing')
        return 1
    ns, src = load_tool()
    audit = ns['audit_text']

    # AC-LGA1: a finished green leg is adopted, with the declared aggregate.
    r = audit(leg())
    f = r['facts']
    ok('AC-LGA1 a complete green leg is ADOPTED with its declared aggregate',
       r['verdict'] == 'ADOPT' and not r['reasons']
       and (f['rows'], f['selected'], f['executed'], f['green'], f['criteria'])
       == (3, 3, 3, 3, 17), 'verdict=%s facts=%s' % (r['verdict'], f['criteria']))

    # AC-LGA2: the R2886 law, mechanized - no closing row means no measurement.
    r = audit(leg(closing=False))
    ok('AC-LGA2 a leg with no closing row is REJECTED naming E_NO_CLOSING_ROW',
       r['verdict'] == 'REJECT' and 'E_NO_CLOSING_ROW' in r['reasons'],
       'reasons=%s' % r['reasons'])

    # AC-LGA3: a torn write (one row lost) is refused by three independent sums.
    r = audit(leg(rows=ROWS[:-1]))
    med = set(x.split(':')[0] for x in r['reasons'])
    ok('AC-LGA3 a torn leg is REJECTED by row, green and criteria disagreement',
       r['verdict'] == 'REJECT'
       and {'E_ROW_COUNT', 'E_GREEN_COUNT', 'E_CRITERIA_SUM'} <= med,
       'med=%s' % sorted(med))

    # AC-LGA4: a suite that ran twice is refused, and the name is printed.
    r = audit(leg(rows=ROWS + [ROWS[0]]))
    dupes = [x for x in r['reasons'] if x.startswith('E_DUPLICATE_SUITE')]
    ok('AC-LGA4 a duplicated suite row is REJECTED and the label is named',
       r['verdict'] == 'REJECT' and dupes and 'probe-a' in dupes[0],
       'dupes=%s' % dupes)

    # AC-LGA5: two opposite row controls - a forged row is refused, and a
    # DECLARED timeout is accepted (rc=124 with suite=none is a real shape, not
    # an unparseable one; calling it unparsed was the tool's own second draft).
    forged = ['SHARD row probe-x rc=0 pass=5 fail=1 detail=yes suite=PASS 5/6 crit=6 0.1s']
    r_forged = audit(leg(header=hdr(1, 6), rows=forged, close_line=(
        'SHARD rc=1 scope=SHARD selected=1 executed=1 green=0 criteria=6 '
        'crit_mismatch=0 elapsed=0.2s')))
    to = ['SHARD row probe-t rc=124 pass=0 fail=0 detail=none suite=none crit=6 45.0s timeout=yes']
    r_to = audit(leg(header=hdr(1, 6), rows=to, close_line=(
        'SHARD rc=2 scope=SHARD selected=1 executed=1 green=0 criteria=6 '
        'crit_mismatch=0 elapsed=45.0s')))
    ok('AC-LGA5 a forged row is REJECTED while a declared timeout is not',
       r_forged['verdict'] == 'REJECT'
       and 'E_ROW_VERDICT:probe-x' in r_forged['reasons']
       and r_to['verdict'] == 'ADOPT' and not r_to['reasons'],
       'forged=%s timeout=%s' % (r_forged['reasons'][:2], r_to['reasons']))

    # AC-LGA6: a header that says it is still running cannot attest a finished
    # leg; and hygiene - pure ASCII source, exactly one registry row, six criteria.
    hdr_run = hdr(state='RUNNING')
    r = audit(leg(header=hdr_run))
    reg = io.open(os.path.join(ROOT, 'src', 'sandbox', 'reconcile_all.py'),
                  'r', encoding='utf-8').read()
    rows = []
    for pos in [m.start() for m in re.finditer(r'"os-leg-audit"', reg)]:
        found = re.search(r'test_leg_audit\.py"\)\s*,\s*(\d+)', reg[pos:pos + 160])
        if found:
            rows.append(found.group(1))
    ok('AC-LGA6 a RUNNING header is REJECTED and exactly one registry row exists',
       r['verdict'] == 'REJECT' and any(x.startswith('E_NOT_COMPLETE') for x in r['reasons'])
       and all(ord(c) < 128 for c in src) and rows == ['6'],
       'reasons=%s rows=%s' % (r['reasons'], rows))

    total = len(CHECKS)
    acs = set()
    for name in CHECKS:
        token = name.split(' ', 1)[0]
        for cut in range(len(token), 0, -1):
            if token[cut - 1].isdigit():
                acs.add(token[:cut])
                break
    print('suite: %d assertions over %d criteria' % (total, len(acs)))
    if FAILS:
        print('SUITE FAIL %d/%d failed=%s' % (total - len(FAILS), total, FAILS))
        return 1
    print('SUITE PASS %d/%d' % (total, total))
    return 0


if __name__ == '__main__':
    sys.exit(main())
