"""test_logs_append_check.py - battery suite for the logs_toolkit append --check face.

Criteria AC-LAC1..AC-LAC6 were pinned in src/os/backlog.md at R3613 BEFORE
src/os/logs_toolkit.py grew the --check flag and before this file existed. The
measured reason: the append write face already refuses six malformed carriers
by name, but until now the only way to ask "is this carrier still appendable?"
was to fake an append or read the tool source, so neither a sweep nor the
closeout chain could take that reading without side effects.

Isolation: every world is a private tempdir. The repo state.json is only ever
read, measured by (size, mtime_ns) before and after.

Source discipline: pure ASCII, stdlib only, no clock in assertions, no
network, no shell.
"""
import ast
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOL = os.path.join(ROOT, 'src', 'os', 'logs_toolkit.py')
LIVE = os.path.join(ROOT, 'src', 'os', 'state.json')
LEDGER = 'R3612 tokens: local=~1k api=0 api_reason=suite world'
CHECKS = []
FAILS = []


def ok(name, cond, detail=''):
    CHECKS.append(name)
    if cond:
        print('  | PASS %s %s' % (name, detail))
    else:
        FAILS.append(name)
        print('  | FAIL %s %s' % (name, detail))


def run(*args):
    return subprocess.run([sys.executable, TOOL] + list(args),
                          capture_output=True)


def read_bytes(path):
    with open(path, 'rb') as f:
        return f.read()


def stamp(path):
    st = os.stat(path)
    return (st.st_size, st.st_mtime_ns)


def write_world(path, items, tick, indent=16, eol='\r\n'):
    """Write a minimal carrier in the shape the real state.json uses."""
    pad = ' ' * indent
    rows = ','.join(eol + pad + json.dumps(x) for x in items)
    text = ('{' + eol + '  "log": [' + rows + eol + '  ],' + eol
            + pad + '"tick":' + str(tick) + eol + '}')
    blob = text.encode('utf-8')
    with open(path, 'wb') as f:
        f.write(blob)
    return blob


def world(base, name):
    d = os.path.join(base, name)
    os.makedirs(d)
    return os.path.join(d, 'state.json'), d


def main():
    tool_src = io.open(TOOL, 'r', encoding='utf-8').read()
    base = tempfile.mkdtemp(prefix='lac_')
    try:
        # AC-LAC1: CLI contract - one exact PASS line, check wins over round.
        # R3627: the healthy fixture is now round-main lawful too (a dated main
        # row for the carrier tick), because the read face publishes the
        # round-main reading when - and only when - it disagrees. The arm's
        # meaning is unchanged: one line, byte-pinned, exit 0.
        p1, d1 = world(base, 'w1')
        blob1 = write_world(p1, ['2026-11-28 R3612 PRODUCT: legal', LEDGER],
                            3612)
        r = run('append', '--check', '--file', p1)
        out = r.stdout.decode('utf-8').strip()
        ok('AC-LAC1 a healthy carrier prints one PASS line and exits 0',
           r.returncode == 0
           and re.match(r'^APPEND CHECK PASS bytes=%d gate=78500 margin=%d '
                        r'tick=3612 log=2 ledger=R3612 api=0$'
                        % (len(blob1), 78500 - len(blob1)), out) is not None,
           'rc=%d out=%r' % (r.returncode, out))
        before1 = read_bytes(p1)
        r2 = run('append', '--check', '--round', 'R3613', '--line', 'x',
                 '--file', p1)
        ok('AC-LAC1 check with append arguments stays read-only',
           r2.returncode == 0 and b'APPEND CHECK PASS' in r2.stdout
           and read_bytes(p1) == before1,
           'rc=%d unchanged=%s' % (r2.returncode, read_bytes(p1) == before1))
        r3 = run('append', '--check', '--round', '3613', '--file', p1)
        ok('AC-LAC1 a bad round shape does not gate the check face',
           r3.returncode == 0 and b'APPEND CHECK PASS' in r3.stdout,
           'rc=%d' % r3.returncode)
        missing = os.path.join(d1, 'nope.json')
        r4 = run('append', '--check', '--file', missing)
        ok('AC-LAC1 a missing file is E_LAC_NO_FILE exit 3 and creates nothing',
           r4.returncode == 3 and b'E_LAC_NO_FILE' in r4.stderr
           and not os.path.exists(missing),
           'rc=%d created=%s' % (r4.returncode, os.path.exists(missing)))

        # AC-LAC2: the six readings come off the carrier, not off defaults.
        p2, _ = world(base, 'w2')
        write_world(p2, ['head', 'R3601 tokens: local=1k api=2 '
                         'api_reason=older', 'tail'], 41)
        r = run('append', '--check', '--file', p2)
        out = r.stdout.decode('utf-8').strip()
        ok('AC-LAC2 ticket and log count are read off the carrier',
           r.returncode == 0 and 'tick=41 log=3 ' in out,
           'out=%r' % out)
        ok('AC-LAC2 the ledger reading takes the newest ledger row',
           r.returncode == 0 and 'ledger=R3601 api=2' in out,
           'out=%r' % out)
        p2b, _ = world(base, 'w2b')
        write_world(p2b, ['alpha', LEDGER], 7)
        r = run('append', '--check', '--file', p2b)
        ok('AC-LAC2 the margin is the gate minus the measured byte count',
           r.returncode == 0
           and ('margin=%d' % (78500 - len(read_bytes(p2b)))) in
           r.stdout.decode('utf-8'),
           'out=%r' % r.stdout.decode('utf-8').strip())

        # AC-LAC3: every disease is refused by name and nothing is touched.
        cases = []

        pA, dA = world(base, 'wA')
        with open(pA, 'wb') as f:
            f.write(b'{not json')
        cases.append(('E_LAC_PARSE', pA, dA))

        pB, dB = world(base, 'wB')
        with open(pB, 'wb') as f:
            f.write(b'{\r\n  "log": [],\r\n  "tick":1\r\n}')
        cases.append(('E_LAC_LOG', pB, dB))

        pC, dC = world(base, 'wC')
        write_world(pC, ['alpha', LEDGER], 7, indent=4)
        cases.append(('E_LAC_LAYOUT', pC, dC))

        pD, dD = world(base, 'wD')
        write_world(pD, ['alpha', LEDGER], 7, eol='\n')
        cases.append(('E_LAC_EOL', pD, dD))

        pE, dE = world(base, 'wE')
        write_world(pE, ['alpha', LEDGER], 7)
        with open(pE, 'ab') as f:
            f.write(b'\r\n')
        cases.append(('E_LAC_ANCHOR', pE, dE))

        pF, dF = world(base, 'wF')
        write_world(pF, ['alpha', 'beta'], 7)
        cases.append(('E_LAC_LEDGER', pF, dF))

        pG, dG = world(base, 'wG')
        write_world(pG, ['x' * 79000, LEDGER], 7)
        cases.append(('E_LAC_GATE', pG, dG))

        for code, path, d in cases:
            pre = read_bytes(path)
            names = set(os.listdir(d))
            r = run('append', '--check', '--file', path)
            ok('AC-LAC3 %s is named and leaves the carrier untouched' % code,
               r.returncode == 2 and ('code=%s' % code).encode('ascii')
               in r.stdout and read_bytes(path) == pre
               and set(os.listdir(d)) == names,
               'rc=%d unchanged=%s' % (r.returncode, read_bytes(path) == pre))

        # AC-LAC4: the check and the write face refuse the same diseases.
        a_lf = run('append', '--round', 'R3613', '--line', 'x', '--file', pD)
        ok('AC-LAC4 a bare-LF carrier is refused by both faces',
           a_lf.returncode == 2 and b'E_LAP_EOL' in a_lf.stdout,
           'rc=%d out=%r' % (a_lf.returncode, a_lf.stdout.strip()))
        a_in = run('append', '--round', 'R3613', '--line', 'x', '--file', pC)
        ok('AC-LAC4 a non-canonical indent is refused by both faces',
           a_in.returncode == 2 and b'E_LAP_INDENT' in a_in.stdout,
           'rc=%d out=%r' % (a_in.returncode, a_in.stdout.strip()))
        a_an = run('append', '--round', 'R3613', '--line', 'x', '--file', pE)
        ok('AC-LAC4 a broken append anchor is refused by both faces',
           a_an.returncode == 2 and b'E_LAP_NO_ANCHOR' in a_an.stdout,
           'rc=%d out=%r' % (a_an.returncode, a_an.stdout.strip()))
        a_ok = run('append', '--round', 'R3613', '--line', 'x', '--file', p1)
        ok('AC-LAC4 a carrier the check passes is one the plan accepts',
           a_ok.returncode == 0 and b'APPEND PLAN' in a_ok.stdout,
           'rc=%d out=%r' % (a_ok.returncode, a_ok.stdout.strip()))

        # AC-LAC5: stdout is clock-free, so two runs are byte-identical.
        s1 = run('append', '--check', '--file', p1)
        s2 = run('append', '--check', '--file', p1)
        ok('AC-LAC5 two runs over one carrier print identical bytes',
           s1.returncode == 0 and s1.stdout == s2.stdout and s1.stdout != b'',
           'same=%s' % (s1.stdout == s2.stdout))

        # AC-LAC6: the source stays pure and the old faces stay registered.
        tree = ast.parse(tool_src)
        names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names.update(a.name.split('.')[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                names.add(node.module.split('.')[0])
        banned = sorted(names & {'urllib', 'socket', 'http', 'requests',
                                 'ftplib', 'telnetlib', 'smtplib'})
        non_ascii = [ln for ln in tool_src.splitlines()
                     if any(ord(c) > 127 for c in ln)]
        handlers = sorted(re.findall(r"'(\w+)': cmd_", tool_src))
        ok('AC-LAC6 the toolkit stays stdlib, ASCII and fully registered',
           not banned and not non_ascii
           and handlers == sorted(['gauge', 'weights', 'inventory', 'tail',
                                   'prune', 'catalog', 'fold', 'census',
                                   'eol', 'summary', 'rounds', 'append']),
           'banned=%s non_ascii=%d handlers=%d'
           % (banned, len(non_ascii), len(handlers)))
    finally:
        shutil.rmtree(base, ignore_errors=True)

    # AC-LAC5 on the live carrier: read only, never derived from.
    live_before = stamp(LIVE)
    live = run('append', '--check', '--file', LIVE)
    live_after = stamp(LIVE)
    ok('AC-LAC5 the live carrier is only read and leaves a PASS line',
       live.returncode == 0 and b'APPEND CHECK PASS' in live.stdout
       and live_before == live_after,
       'rc=%d unchanged=%s' % (live.returncode, live_before == live_after))
    ok('AC-LAC6 leftover scratch is a leak and must be absent',
       not os.path.isdir(base), 'removed=%s' % (not os.path.isdir(base)))
    # AC-LAC6 binding: the registry row is the ONE typed count and this suite is
    # what refutes it, so an edit that forgets this suite reddens HERE instead
    # of being read by nobody. Last on purpose: it reads the final total off
    # CHECKS plus itself rather than predicting how many checks follow.
    registry = os.path.join(ROOT, 'src', 'sandbox', 'reconcile_all.py')
    reg = io.open(registry, 'r', encoding='utf-8').read()
    rows = re.findall(
        r'\("os-logs-append-check",\s*os\.path\.join\("\.\.", "os", '
        r'"test_logs_append_check\.py"\),\s*(\d+)\)', reg)
    declared = int(rows[0]) if len(rows) == 1 else None
    ok('AC-LAC6 registry row declares this run total',
       declared == len(CHECKS) + 1 and len(rows) == 1,
       'declared=%s expected=%d rows=%d'
       % (declared, len(CHECKS) + 1, len(rows)))

    acs = set()
    for name in CHECKS:
        token = name.split(' ', 1)[0]
        for cut in range(len(token), 0, -1):
            if token[cut - 1].isdigit():
                acs.add(token[:cut])
                break
    print('suite: %d assertions over %d criteria' % (len(CHECKS), len(acs)))
    if FAILS:
        print('SUITE FAIL %d/%d failed=%s'
              % (len(CHECKS) - len(FAILS), len(CHECKS), FAILS))
        return 1
    print('SUITE PASS %d/%d' % (len(CHECKS), len(CHECKS)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
