"""Battery suite for src/os/scan_five_still.py - criteria AC-SFS1..AC-SFS8.

WHY: the group ledger writes wildcard forms ("no reply cites D-20261114-0x") and
a token regex without a right-hand boundary harvests D-20261114-0 out of them,
inventing a decision that does not exist. Every round's decisions face reads
through this scanner, so the boundary is pinned here.

Criteria AC-SFS1..AC-SFS6 were written into src/os/backlog.md in the SAME window
as this suite, NOT before it: the boundary repair and the measurement came first
and the pinning was recorded afterwards, which is disclosed rather than backdated.

AC-SFS7 (R3325) closes the other half: the ps1 scanner the skill actually runs
carried a [HB] face that NO suite read. Measured before shipping - the python
twin holds zero HB/lag/ahead tokens, the five ps1 mentions inside
test_crawl_runner are all "must not appear" crawl assertions, and the twin has
zero production callers (scheduled action runs iteration_loop.ps1 and names no
scan), so the twin is dead code for the group scan and got no second HB face.
The pin therefore reads the executed source named by SKILL.md - tools/skills/...
- and not the gitignored .codely-cli install, which is what the ps1 harness
test_scan_faces.ps1 points at.
Source discipline: pure ASCII, stdlib only, no clock, no network.
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOL = os.path.join(ROOT, 'src', 'os', 'scan_five_still.py')
DEC = os.path.join(os.path.dirname(os.path.dirname(ROOT)), 'docs', 'decisions.md')
SCAN_PS1 = os.path.join(ROOT, 'tools', 'skills', 'bigdomain-loop-scan',
                        'scripts', 'scan_five_still.ps1')
SKILL_MD = os.path.join(ROOT, 'tools', 'skills', 'bigdomain-loop-scan', 'SKILL.md')
HB_DEBT = r'[HB] FLAG hb_tick=$hbTick state_tick=$stTick lag=$($stTick - $hbTick)'
HB_AHEAD = r'[HB] PASS hb_tick=$hbTick state_tick=$stTick ahead=$($hbTick - $stTick)'
HB_FRESH = r'[HB] PASS hb_tick=$hbTick state_tick=$stTick lag=0'
FAILS = []
CHECKS = []


def live_code(text):
    """Comments out of the count: block comments stripped, comment-only lines
    dropped. Counting the raw text would keep a pin green on a branch somebody
    commented out - measured at R3325 (commented line: raw=1, live=0)."""
    body = re.sub(r'<#.*?#>', '', text, flags=re.S)
    return '\n'.join(ln for ln in body.splitlines()
                     if not ln.lstrip().startswith('#'))


def twin_law(text):
    """The revival law for the dead twin, as a reading of its own bytes.

    R3328 named the divergence in the header; R3330 asked whether a revival
    would be noticed. The reading below is the answer: the header must say the
    file is dead, and while any @BigDomain selector is still a plain substring
    test the header must name the divergence it would reintroduce. Measured
    before shipping - two live substring sites, both in the ledger and group
    orders selectors, and the header names both forms.
    """
    head = text.split('import io', 1)[0]
    status = 'DEAD CODE, NAMED' in head and 'zero production callers' in head
    sub_sites = len(re.findall(r'"@BigDomain" in', text))
    clause = 'KNOWN DIVERGENCE' in head and '@BigDomainX' in head
    return status, sub_sites, clause


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
        print('SUITE FAIL 0/10 tool missing')
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

    # AC-SFS6: hygiene, one registry row whose cell matches the criteria count
    ok('AC-SFS6 tool source is pure ASCII', all(ord(c) < 128 for c in src))
    reg = io.open(os.path.join(ROOT, 'src', 'sandbox', 'reconcile_all.py'),
                  'r', encoding='utf-8').read()
    hits = [m.start() for m in re.finditer(r'"os-scan-five-still"', reg)]
    rows = []
    for pos in hits:
        found = re.search(r'test_scan_five_still\.py"\)\s*,\s*(\d+)', reg[pos:pos + 160])
        if found:
            rows.append(found.group(1))
    ok('AC-SFS6 exactly one battery row for this suite',
       len(rows) == 1, 'rows=%s' % rows)

    # AC-SFS7 (R3325): the [HB] three lines of the ps1 scanner the skill runs.
    if os.path.isfile(SCAN_PS1):
        ptext = io.open(SCAN_PS1, 'r', encoding='utf-8-sig',
                        errors='replace').read()
        live = live_code(ptext)
        got = [live.count(h) for h in (HB_DEBT, HB_AHEAD, HB_FRESH)]
        ok('AC-SFS7 the three [HB] lines appear exactly once each in live ps1 code',
           got == [1, 1, 1], 'counts=%s' % got)
        at = [live.find(h) for h in (HB_DEBT, HB_AHEAD, HB_FRESH)]
        ok('AC-SFS7 the debt branch is tested before ahead and ahead before lag=0',
           at[0] >= 0 and at[0] < at[1] < at[2], 'at=%s' % at)
        commented = '\n'.join(('# ' + ln) if HB_AHEAD in ln else ln
                              for ln in live.splitlines())
        ok('AC-SFS7 a commented-out ahead line drops its live count to zero',
           live_code(commented).count(HB_AHEAD) == 0,
           'decoy_count=%d' % live_code(commented).count(HB_AHEAD))
        skill_src = (io.open(SKILL_MD, 'r', encoding='utf-8-sig',
                             errors='replace').read()
                     if os.path.isfile(SKILL_MD) else '')
        inv = [ln for ln in skill_src.splitlines()
               if 'scan_five_still.ps1' in ln and 'powershell' in ln]
        ok('AC-SFS7 the skill invocation names the pinned source, not the install',
           bool(inv) and 'tools/skills/bigdomain-loop-scan/scripts/'
           'scan_five_still.ps1' in inv[0],
           'invoke=%s' % (inv[0].strip()[:60] if inv else 'none'))
    else:
        ok('AC-SFS7 the ps1 scanner is missing', False, 'path=%s' % SCAN_PS1)

    # AC-SFS8 (R3330): the dead twin's revival law. R3328 named the divergence
    # in the header but left nothing that would notice a revival; the board's
    # own test was "can a text pin hold the header without executing the twin".
    # Two readings, both on bytes: the header's dead-code claim, and the
    # divergence clause bound to the substring selectors that create it.
    status, sub_sites, clause = twin_law(src)
    ok('AC-SFS8 the twin header names its dead-code status', status,
       'status_named=%s' % status)
    ok('AC-SFS8 a live @BigDomain substring selector still names its divergence',
       sub_sites == 0 or clause, 'substring_sites=%d clause=%s'
       % (sub_sites, clause))
    ds, _, _ = twin_law(src.replace('DEAD CODE, NAMED', 'SCANNER'))
    ok('AC-SFS8 a stripped header reddens the same reading', not ds,
       'decoy_status=%s' % ds)
    named_in = []
    for p in (os.path.join(ROOT, 'src', 'os', 'iteration_loop.ps1'),
              os.path.join(ROOT, 'src', 'os', 'register_loop_task.ps1'),
              os.path.join(ROOT, 'src', 'os', 'iteration_prompt.txt'),
              SKILL_MD):
        if os.path.isfile(p):
            t = io.open(p, 'r', encoding='utf-8-sig', errors='replace').read()
            if 'scan_five_still.py' in t:
                named_in.append(os.path.basename(p))
    ok('AC-SFS8 no production entry names the dead twin', not named_in,
       'named_in=%s' % named_in)

    # Declared units (R2860): the AC inventory below is derived from CHECKS,
    # never echoed from the registry - a declaration copied out of the
    # registry could never disagree with it.
    acs = set()
    for name in CHECKS:
        token = name.split(' ', 1)[0]
        for cut in range(len(token), 0, -1):
            if token[cut - 1].isdigit():
                acs.add(token[:cut])
                break
    # R3325: this suite declares no EXPECTED_CRITERIA, so the registry counter
    # (the third SUITES cell) is graded against the count derived above; a new
    # arm added without its cell makes this line red instead of drifting.
    ok('AC-SFS6 the registry cell equals this suite own derived criteria count',
       rows == [str(len(acs))], 'cell=%s derived=%d' % (rows, len(acs)))

    total = len(CHECKS)
    print('suite: %d assertions over %d criteria' % (total, len(acs)))
    if FAILS:
        print('SUITE FAIL %d/%d failed=%s' % (total - len(FAILS), total, FAILS))
        return 1
    print('SUITE PASS %d/%d' % (total, total))
    return 0


if __name__ == '__main__':
    sys.exit(main())
