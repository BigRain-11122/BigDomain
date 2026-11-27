"""test_logs_append.py - battery suite for the logs_toolkit append face.

Criteria AC-LAP1..AC-LAP8 were pinned in src/os/backlog.md at R3612 BEFORE
src/os/logs_toolkit.py grew the `append` subcommand and before this file
existed. The measured reason: in the nine rounds before it, the loop wrote its
own state.json log by hand and hurt itself three times - R3604 collapsed the
log indent with a full json.dump rewrite (closeout_gate refused with
indent_anomaly=39), R3606 first omitted the old last item's comma and then
added a trailing one (both caught by a json.loads assert before the write), and
R3609 wrote seven rows at four spaces (refused with indent_anomaly=7).

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


def world(d, name='state.json'):
    return os.path.join(d, name)


def main():
    tool_src = io.open(TOOL, 'r', encoding='utf-8').read()
    base = tempfile.mkdtemp(prefix='lap_')
    try:
        # AC-LAP1: CLI contract - plan line shape, round shape, missing file.
        d1 = os.path.join(base, 'w1')
        os.makedirs(d1)
        p1 = world(d1)
        write_world(p1, ['alpha', 'beta'], 7)
        r = run('append', '--round', 'R3612', '--line', 'one', '--line', 'two',
                '--file', p1)
        out = r.stdout.decode('utf-8').strip()
        ok('AC-LAP1 plan prints one exact line and exits 0',
           r.returncode == 0
           and re.match(r'^APPEND PLAN round=R3612 tick=8 lines=2 '
                        r'bytes=\d+->\d+ gate=78500 verdict=OK$', out)
           is not None,
           'rc=%d out=%r' % (r.returncode, out))
        bad = run('append', '--round', '3612', '--line', 'x', '--file', p1)
        ok('AC-LAP1 bad round shape is E_LAP_ROUND exit 2',
           bad.returncode == 2
           and b'E_LAP_ROUND' in bad.stderr,
           'rc=%d' % bad.returncode)
        missing = os.path.join(d1, 'nope.json')
        m = run('append', '--round', 'R3612', '--line', 'x', '--file', missing)
        ok('AC-LAP1 missing file is E_LAP_NO_FILE exit 3 and creates nothing',
           m.returncode == 3 and b'E_LAP_NO_FILE' in m.stderr
           and not os.path.exists(missing),
           'rc=%d created=%s' % (m.returncode, os.path.exists(missing)))

        # AC-LAP2: byte surgery - prefix bytes, CRLF, caliber, comma, tick.
        before = read_bytes(p1)
        r = run('append', '--round', 'R3612', '--line', 'one', '--line', 'two',
                '--file', p1, '--execute')
        after = read_bytes(p1)
        old = json.loads(before.decode('utf-8'))
        new = json.loads(after.decode('utf-8'))
        anchor = before.index(b'\r\n  ],\r\n')
        prefix_ok = after.startswith(before[:anchor] + b',')
        crlf_ok = after.count(b'\n') == after.count(b'\r\n')
        indent_ok = (b'\r\n' + b' ' * 16 + b'"one"') in after
        ok('AC-LAP2 execute appends with the document caliber and one comma',
           r.returncode == 0
           and prefix_ok and crlf_ok and indent_ok
           and new['log'] == old['log'] + ['one', 'two']
           and new['tick'] == 8,
           'rc=%d prefix=%s crlf=%s indent=%s tick=%s'
           % (r.returncode, prefix_ok, crlf_ok, indent_ok, new['tick']))
        broken = before[:anchor] + b'\r\n' + b' ' * 16 + b'"x"' + before[anchor:]
        try:
            json.loads(broken.decode('utf-8'))
            neg_ok = False
        except ValueError:
            neg_ok = True
        ok('AC-LAP2 negative control: without the comma the carrier is invalid JSON',
           neg_ok, 'negative=%s' % neg_ok)
        d2 = os.path.join(base, 'w2')
        os.makedirs(d2)
        p2 = world(d2)
        write_world(p2, ['two-space world'], 3, indent=2)
        r2 = run('append', '--round', 'R3612', '--line', 'kept',
                 '--file', p2, '--execute')
        text2 = read_bytes(p2).decode('utf-8')
        ok('AC-LAP2 caliber follows the document, not a constant',
           r2.returncode == 0 and '\r\n  "kept"\r\n' in text2
           and ' ' * 16 not in text2,
           'rc=%d' % r2.returncode)

        # AC-LAP3: six named refusals, each leaving bytes identical.
        arms = []
        p4 = world(os.path.join(base, 'w4'))
        os.makedirs(os.path.dirname(p4))
        write_world(p4, ['ok'], 5)
        with open(p4, 'wb') as f:
            f.write(b'{\r\n  "log": [\r\n' + b' ' * 16 + b'"a"\r\n  ],\r\n'
                    + b' ' * 16 + b'"tick":5\r\n}\r\n')
        arms.append(('E_LAP_NO_ANCHOR', p4, ['--line', 'x']))
        p5 = world(os.path.join(base, 'w5'))
        os.makedirs(os.path.dirname(p5))
        write_world(p5, ['ok'], 5, eol='\n')
        arms.append(('E_LAP_EOL', p5, ['--line', 'x']))
        p6 = world(os.path.join(base, 'w6'))
        os.makedirs(os.path.dirname(p6))
        with open(p6, 'wb') as f:
            f.write(b'{\r\n  "log": [\r\n' + b' ' * 16 + b'"a",\r\n'
                    + b' ' * 8 + b'"b"\r\n  ],\r\n' + b' ' * 16
                    + b'"tick":5\r\n}')
        arms.append(('E_LAP_INDENT', p6, ['--line', 'x']))
        p7 = world(os.path.join(base, 'w7'))
        os.makedirs(os.path.dirname(p7))
        write_world(p7, ['ok'], 5)
        arms.append(('E_LAP_MULTILINE', p7, ['--line', 'a\nb']))
        arms.append(('E_LAP_EMPTY', p7, ['--line', '   ']))
        arms.append(('E_LAP_TICK', p7, ['--line', 'x', '--tick', '5']))
        for code, path, extra in arms:
            pre = read_bytes(path) if os.path.exists(path) else b''
            pre_names = set(os.listdir(os.path.dirname(path)))
            res = run('append', '--round', 'R3612', '--file', path, *extra)
            post = read_bytes(path) if os.path.exists(path) else b''
            names = set(os.listdir(os.path.dirname(path)))
            ok('AC-LAP3 %s refuses without touching the carrier' % code,
               res.returncode == 2
               and code.encode() in res.stdout
               and post == pre
               and names == pre_names,
               'rc=%d clean=%s' % (res.returncode, post == pre and names == pre_names))

        # AC-LAP4: the gate refusal names itself and the fold path.
        pg = world(os.path.join(base, 'w8'))
        os.makedirs(os.path.dirname(pg))
        write_world(pg, ['z' * 70000], 9)
        pre = read_bytes(pg)
        res = run('append', '--round', 'R3612', '--line', 'q' * 9000,
                  '--file', pg, '--execute')
        ok('AC-LAP4 a post size over the gate is refused, not written',
           res.returncode == 2
           and b'E_LAP_GATE' in res.stdout
           and b'fold --plan-only' in res.stdout
           and read_bytes(pg) == pre,
           'rc=%d unchanged=%s' % (res.returncode, read_bytes(pg) == pre))

        # AC-LAP5: two consecutive writes keep order and monotonic ticks.
        d9 = os.path.join(base, 'w9')
        os.makedirs(d9)
        p9 = world(d9)
        write_world(p9, ['seed'], 1)
        a = run('append', '--round', 'R3612', '--line', 'second',
                '--file', p9, '--execute')
        b = run('append', '--round', 'R3612', '--line', 'third',
                '--file', p9, '--execute')
        st9 = json.loads(read_bytes(p9).decode('utf-8'))
        ok('AC-LAP5 two sequential appends keep order and bump the tick',
           a.returncode == 0 and b.returncode == 0
           and st9['log'] == ['seed', 'second', 'third']
           and st9['tick'] == 3,
           'rc=%d/%d tick=%s log=%s'
           % (a.returncode, b.returncode, st9['tick'], st9['log']))

        # AC-LAP6: dry-run mutates nothing and leaves no scratch file.
        pre_stamp = stamp(p9)
        pre_names = set(os.listdir(d9))
        res = run('append', '--round', 'R3612', '--line', 'dry', '--file', p9)
        ok('AC-LAP6 dry-run is read-only and creates no scratch file',
           res.returncode == 0 and b'verdict=OK' in res.stdout
           and stamp(p9) == pre_stamp
           and set(os.listdir(d9)) == pre_names,
           'rc=%d unchanged=%s' % (res.returncode, stamp(p9) == pre_stamp))

        # AC-LAP7: purity and determinism.
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
        r1 = run('append', '--round', 'R3612', '--line', 'same', '--file', p9)
        r2 = run('append', '--round', 'R3612', '--line', 'same', '--file', p9)
        ok('AC-LAP7 the face stays stdlib, ASCII and clock-free',
           not banned and not non_ascii
           and r1.stdout == r2.stdout and r1.stdout != b'',
           'banned=%s non_ascii=%d same=%s'
           % (banned, len(non_ascii), r1.stdout == r2.stdout))
    finally:
        shutil.rmtree(base, ignore_errors=True)

    # AC-LAP8: live carrier is only read, and the older faces still answer.
    live_before = stamp(LIVE)
    live = run('append', '--round', 'R3612', '--line', 'live probe',
               '--file', LIVE)
    live_after = stamp(LIVE)
    handlers = sorted(re.findall(r"'(\w+)': cmd_", tool_src))
    ok('AC-LAP8 live dry-run reads OK and leaves the carrier untouched',
       live.returncode == 0 and b'verdict=OK' in live.stdout
       and live_before == live_after,
       'rc=%d unchanged=%s' % (live.returncode, live_before == live_after))
    ok('AC-LAP8 the twelve older faces are still registered',
       handlers == sorted(['gauge', 'weights', 'inventory', 'tail', 'prune',
                           'catalog', 'fold', 'census', 'eol', 'summary',
                           'rounds', 'append']),
       'handlers=%s' % (handlers,))
    ok('AC-LAP8 leftover scratch is a leak and must be absent',
       not os.path.isdir(base), 'removed=%s' % (not os.path.isdir(base)))
    # AC-LAP8 binding: the registry row is the ONE typed count and this suite is
    # what refutes it, so an edit that forgets this suite reddens HERE instead
    # of being read by nobody. Last on purpose: it reads the final total off
    # CHECKS plus itself rather than predicting how many checks follow.
    registry = os.path.join(ROOT, 'src', 'sandbox', 'reconcile_all.py')
    reg = io.open(registry, 'r', encoding='utf-8').read()
    rows = re.findall(
        r'\("os-logs-append",\s*os\.path\.join\("\.\.", "os", '
        r'"test_logs_append\.py"\),\s*(\d+)\)', reg)
    declared = int(rows[0]) if len(rows) == 1 else None
    ok('AC-LAP8 registry row declares this run total',
       declared == len(CHECKS) + 1 and len(rows) == 1,
       'declared=%s expected=%d rows=%d'
       % (declared, len(CHECKS) + 1, len(rows)))

    # Declared units are derived from CHECKS, never echoed from the registry:
    # a declaration copied out of the registry could never disagree with it.
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
