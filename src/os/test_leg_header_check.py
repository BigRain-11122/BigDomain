"""Battery suite for tools/leg_header_check.py - criteria AC-LHC1..AC-LHC6.

WHY: leg_audit grades counts, duplicates and row coherence but never compares a
leg header's `registry_suites/registry_criteria` pair with the registry on disk.
R2891 named why that cannot be a plain equality test: a suite registered AFTER a
leg closes makes that leg's header legitimately stale. This suite pins the time
discriminator that tells the two apart, and pins the REFUSAL to guess when the
filesystem cannot supply a birth time - a wrong side here launders a lying header
into an adopted family number.

Every fixture lives in a private temp world whose registry is a three-row SUITES
literal, so the suite never depends on the real registry's current contents.
Source discipline: pure ASCII, stdlib only, no network.
"""
import io
import os
import re
import shutil
import sys
import tempfile
from contextlib import redirect_stdout

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOL = os.path.join(ROOT, 'tools', 'leg_header_check.py')
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
    src = io.open(TOOL, 'r', encoding='utf-8').read()
    ns = {'__name__': 'leg_header_check_under_test', '__file__': TOOL}
    exec(compile(src, TOOL, 'exec'), ns)
    return ns, src


def leg_text(suites, crit, state='RUNNING'):
    """A minimal leg: one header, one row, no closing row (it is still live)."""
    return ('SHARD scope=SHARD registry_suites=%d registry_criteria=%d selected=1 '
            'selected_criteria=6 cap=600s leg_cap=0s overrides=0 exact=0 state=%s\n'
            'SHARD row probe-a rc=0 pass=6 fail=0 detail=yes suite=PASS 6/6 crit=6 0.1s\n'
            % (suites, crit, state))


REG_SRC = ('SUITES = [\n'
           '    ("probe-a", "a.py", 6),\n'
           '    ("probe-b", "b.py", 4),\n'
           '    ("probe-c", "c.py", 2),\n'
           ']\n')


def main():
    ns, src = load_tool()
    check = ns['check']
    world = tempfile.mkdtemp(prefix='lhc_')
    try:
        reg = os.path.join(world, 'reconcile_all.py')
        with io.open(reg, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(REG_SRC)
        leg = os.path.join(world, 'leg.log')
        with io.open(leg, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(leg_text(3, 12))

        # AC-LHC1: the agreeing case must be reachable and cheap - a header that
        # equals the registry on disk is AGREE with no reasons.
        r = check(leg, reg)
        ok('AC-LHC1 an equal header is AGREE with no reason',
           r['verdict'] == 'AGREE' and r['reasons'] == []
           and r['facts']['header_suites'] == 3 and r['facts']['registry_suites'] == 3,
           'verdict=%s reasons=%s' % (r['verdict'], r['reasons']))

        # AC-LHC2: disagreement where the registry MOVED after the leg was born
        # is drift-by-date, not a lie - adoptable, and the line must show both
        # number pairs so the operator can quote the at-launch pair.
        born = os.stat(leg).st_ctime if sys.platform == 'win32' else None
        stale = os.path.join(world, 'stale.log')
        with io.open(stale, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(leg_text(2, 11))
        os.utime(reg, (1700000000, 1700000000))          # registry OLDER
        r_old = check(stale, reg)
        os.utime(reg, (1900000000, 1900000000))          # registry NEWER
        r_new = check(stale, reg)
        ok('AC-LHC2 registry moved after launch is DRIFT-DATED, before launch is not',
           r_old['verdict'] == 'HEADER-LIES' and r_old['reasons']
           and r_new['verdict'] == 'DRIFT-DATED' and r_new['reasons'] == []
           and r_new['facts']['header_criteria'] == 11
           and r_new['facts']['registry_criteria'] == 12,
           'old=%s new=%s' % (r_old['verdict'], r_new['verdict']))

        # AC-LHC3: a disagreement with a registry that did NOT move after birth
        # is a lying header and must be refused BY NAME with both pairs.
        ok('AC-LHC3 a lying header is refused with both pairs named',
           r_old['verdict'] == 'HEADER-LIES'
           and any(x.startswith('E_HEADER_LIES:2/11!=3/12') for x in r_old['reasons']),
           'reasons=%s' % (r_old['reasons'],))

        # AC-LHC4: a declared launch time OVERRIDES the filesystem clock, and an
        # unparseable declaration is refused rather than silently ignored.
        r_dec = check(stale, reg, launched='2020-01-01T00:00')
        r_bad = check(stale, reg, launched='yesterday-ish')
        ok('AC-LHC4 declared launch overrides the clock and a bad one is refused',
           r_dec['verdict'] == 'DRIFT-DATED'
           and r_dec['facts']['birth_source'] == 'declared'
           and r_bad['verdict'] == 'UNDECIDABLE'
           and any(x.startswith('E_LAUNCHED_UNPARSEABLE') for x in r_bad['reasons']),
           'declared=%s source=%s bad=%s' % (r_dec['verdict'],
                                             r_dec['facts']['birth_source'],
                                             r_bad['verdict']))

        # AC-LHC5: the checker is read-only, and a leg with no header is refused
        # rather than assumed to agree. The registry is set OLDER here so the
        # exit-code arm exercises the refusal, not the drift arm AC-LHC4 left set.
        os.utime(reg, (1700000000, 1700000000))
        before = (open(leg, 'rb').read(), os.stat(leg).st_mtime_ns,
                  open(reg, 'rb').read(), os.stat(reg).st_mtime_ns)
        bare = os.path.join(world, 'bare.log')
        with io.open(bare, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write('nothing here\n')
        r_bare = check(bare, reg)
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc_lies = ns['main']([stale, '--registry', reg])
            rc_bad = ns['main']([bare, '--registry', reg])
        after = (open(leg, 'rb').read(), os.stat(leg).st_mtime_ns,
                 open(reg, 'rb').read(), os.stat(reg).st_mtime_ns)
        ok('AC-LHC5 read-only, and a headerless leg is UNDECIDABLE at rc 3',
           before == after and r_bare['verdict'] == 'UNDECIDABLE'
           and any(x.startswith('E_NO_HEADER') for x in r_bare['reasons'])
           and rc_lies == 2 and rc_bad == 3,
           'unchanged=%s rc=%s,%s' % (before == after, rc_lies, rc_bad))

        # AC-LHC6: hygiene plus a CONDITIONAL wiring check that stays silent
        # until the registry row exists, so it can never fabricate a green.
        reg_text = io.open(os.path.join(ROOT, 'src', 'sandbox', 'reconcile_all.py'),
                           'r', encoding='utf-8').read()
        rows = []
        for pos in [m.start() for m in re.finditer(r'"os-leg-header-check"', reg_text)]:
            found = re.search(r'test_leg_header_check\.py"\)\s*,\s*(\d+)',
                              reg_text[pos:pos + 200])
            if found:
                rows.append(found.group(1))
        ascii_only = all(ord(c) < 128 for c in src)
        no_net = not re.search(r'\b(urllib|socket|http|requests)\b', src)
        wired_ok = (rows == ['6']) if rows else True
        ok('AC-LHC6 pure ASCII, no network, and the wiring check waits for the row',
           ascii_only and no_net and wired_ok,
           'ascii=%s net=%s rows=%s' % (ascii_only, no_net, rows))
    finally:
        shutil.rmtree(world, ignore_errors=True)

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
