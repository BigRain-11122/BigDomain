"""test_logs_append_round_main.py - battery suite for the R3626 append law.

Criteria AC-LAR1..AC-LAR6 were pinned in src/os/backlog.md at R3626 BEFORE
src/os/logs_toolkit.py learned to ask the round-main reader and before this
file existed. The measured reason: the R3623 window wrote a main row without
the YYYY-MM-DD prefix, only found out from the closeout gate
(E_CLG_ROUND_MAIN / E_RMS_NO_DATE), appended a corrective line, advanced the
tick twice and left R3624 an empty round number.

The law is read, never copied: logs_toolkit imports ledger_lines and asks
check_round_main_shape / format_round_main, so the writer and the gate answer
from one definition.

Isolation: every world is a private tempdir. The repo state.json is only read,
measured by (size, mtime_ns) before and after.

Source discipline: pure ASCII, stdlib only, no clock in assertions, no network.
"""
import io
import json
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOL = os.path.join(ROOT, 'src', 'os', 'logs_toolkit.py')
LIVE = os.path.join(ROOT, 'src', 'os', 'state.json')
REGISTRY = os.path.join(ROOT, 'src', 'sandbox', 'reconcile_all.py')
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
    pad = ' ' * indent
    rows = ','.join(eol + pad + json.dumps(x) for x in items)
    text = ('{' + eol + '  "log": [' + rows + eol + '  ],' + eol
            + pad + '"tick":' + str(tick) + eol + '}')
    with open(path, 'wb') as f:
        f.write(text.encode('utf-8'))


def out(r):
    return (r.stdout.decode('utf-8') + r.stderr.decode('utf-8')).strip()


def main():
    tool_src = io.open(TOOL, 'r', encoding='utf-8').read()
    live_before = stamp(LIVE)
    base = tempfile.mkdtemp(prefix='lar_')
    try:
        # AC-LAR1: one law, imported rather than copied. R3627 moved the two
        # asks behind one bridge (round_main_verdict / round_main_line) and the
        # read face became the third ask, so the pin is now one law call, one
        # formatter call, and exactly three asks through that bridge.
        ok('AC-LAR1 the reader is asked through one bridge, never re-derived',
           tool_src.count('check_round_main_shape(') == 1
           and tool_src.count('format_round_main(') == 1
           and tool_src.count('round_main_verdict(') == 4
           and tool_src.count('round_main_line(') == 3
           and 'def check_round_main_shape' not in tool_src,
           'law=%d fmt=%d bridge=%d line=%d'
           % (tool_src.count('check_round_main_shape('),
              tool_src.count('format_round_main('),
              tool_src.count('round_main_verdict('),
              tool_src.count('round_main_line(')))
        ok('AC-LAR1 no reader code is re-implemented in this file',
           'E_RMS_' not in tool_src and 'ROUND-MAIN' not in tool_src,
           'e_rms=%d roundmain=%d'
           % (tool_src.count('E_RMS_'), tool_src.count('ROUND-MAIN')))
        imports = re.findall(r'^\s+import ledger_lines\b', tool_src, re.M)
        ok('AC-LAR1 the law comes from the shipped ledger_lines module',
           len(imports) == 2, 'imports=%d' % len(imports))

        # AC-LAR2: the R3623 incident itself - an undated round main refuses.
        d = os.path.join(base, 'w2')
        os.makedirs(d)
        p = os.path.join(d, 'state.json')
        write_world(p, ['2026-11-27 R100 PRODUCT: legal'], 100)
        before = read_bytes(p)
        r = run('append', '--round', 'R101', '--line', 'R101 MAIN no date',
                '--file', p)
        ok('AC-LAR2 an undated round line is refused by E_LAP_ROUND_MAIN',
           r.returncode == 2 and 'APPEND REFUSED E_LAP_ROUND_MAIN' in out(r),
           'rc=%d out=%s' % (r.returncode, out(r)[:90]))
        ok('AC-LAR2 the refusal carries the reader own E_RMS_NO_DATE',
           'E_RMS_NO_DATE' in out(r) and 'round=101' in out(r),
           'out=%s' % out(r)[:90])
        ok('AC-LAR2 a refused dry run writes nothing',
           read_bytes(p) == before, 'bytes=%d' % len(before))
        r2 = run('append', '--round', 'R101', '--line', 'R101 MAIN no date',
                 '--execute', '--file', p)
        ok('AC-LAR2 the same refusal holds on --execute',
           r2.returncode == 2 and read_bytes(p) == before,
           'rc=%d bytes=%d' % (r2.returncode, len(read_bytes(p))))

        # AC-LAR3: the label half, and the honest green path.
        write_world(p, ['2026-11-27 R100 PRODUCT: legal'], 100)
        r = run('append', '--round', 'R101', '--line',
                '2026-11-28 R101 main: no label', '--file', p)
        ok('AC-LAR3 a dated row with no UPPERCASE label is E_RMS_NO_LABEL',
           r.returncode == 2 and 'E_RMS_NO_LABEL' in out(r),
           'rc=%d out=%s' % (r.returncode, out(r)[:90]))
        good = run('append', '--round', 'R101', '--line',
                   '2026-11-28 R101 PRODUCT: fine',
                   '--line', 'R101 tokens: local=0 api=0',
                   '--file', p)
        ok('AC-LAR3 a dated labelled row still plans green',
           good.returncode == 0
           and re.match(r'^APPEND PLAN round=R101 tick=101 lines=2 '
                        r'bytes=\d+->\d+ gate=78500 verdict=OK$',
                        out(good)) is not None,
           'out=%s' % out(good)[:100])
        ex = run('append', '--round', 'R101', '--line',
                 '2026-11-28 R101 PRODUCT: fine',
                 '--line', 'R101 tokens: local=0 api=0',
                 '--execute', '--file', p)
        doc = json.loads(read_bytes(p).decode('utf-8'))
        ok('AC-LAR3 execute lands verified with the tick advanced once',
           ex.returncode == 0 and 'verified=true' in out(ex)
           and doc['tick'] == 101
           and doc['log'][-2].startswith('2026-11-28 R101 PRODUCT:')
           and doc['log'][-1].startswith('R101 tokens:'),
           'rc=%d tick=%s last=%r'
           % (ex.returncode, doc.get('tick'), doc['log'][-1][:30]))

        # AC-LAR4: the law blocks the disease, not the writer.
        d4 = os.path.join(base, 'w4')
        os.makedirs(d4)
        q = os.path.join(d4, 'state.json')
        write_world(q, ['R99 old undated'], 99)
        r = run('append', '--round', 'R100', '--line', 'note only',
                '--file', q)
        ok('AC-LAR4 a non-round line into an undated world is not blocked',
           r.returncode == 0 and 'verdict=OK' in out(r),
           'rc=%d out=%s' % (r.returncode, out(r)[:80]))
        r = run('append', '--round', 'R100', '--line', 'R100 MAIN add',
                '--file', q)
        ok('AC-LAR4 the same world refuses once the line claims a round',
           r.returncode == 2 and 'E_LAP_ROUND_MAIN' in out(r),
           'rc=%d' % r.returncode)

        # AC-LAR5: the older faces keep their own readings.
        check = run('append', '--check')
        ok('AC-LAR5 the read face still prints its PASS line',
           check.returncode == 0
           and re.search(r'^APPEND CHECK PASS bytes=\d+ gate=78500 '
                         r'margin=\d+ tick=\d+ log=\d+ ledger=R\d+ api=\d+$',
                         out(check)) is not None,
           'out=%s' % out(check)[:100])
        d5 = os.path.join(base, 'w5')
        os.makedirs(d5)
        broken = os.path.join(d5, 'state.json')
        with open(broken, 'wb') as f:
            f.write(b'{"log": ["a"], "tick": 3}\n')
        r = run('append', '--round', 'R101', '--line', 'x', '--file', broken)
        ok('AC-LAR5 the six older refusals still speak first',
           r.returncode == 2 and 'E_LAP_' in out(r)
           and 'E_LAP_ROUND_MAIN' not in out(r),
           'out=%s' % out(r)[:80])

        # AC-LAR6: hygiene and wiring.
        ok('AC-LAR6 the tool source stays pure ASCII',
           all(ord(ch) < 128 for ch in tool_src), 'bytes=%d' % len(tool_src))
        net = [w for w in ('import socket', 'import urllib', 'import requests')
               if w in tool_src]
        ok('AC-LAR6 no network import reached the tool', not net, str(net))
        registry = io.open(REGISTRY, 'r', encoding='utf-8').read()
        ok('AC-LAR6 the battery row is wired',
           registry.count('os-logs-append-round-main') == 1,
           'rows=%d' % registry.count('os-logs-append-round-main'))
        ok('AC-LAR6 the live carrier was only read',
           stamp(LIVE) == live_before, 'before=%s' % (live_before,))
    finally:
        for root, dirs, files in os.walk(base, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(base)

    print('suite: %d assertions over 6 criteria' % len(CHECKS))
    if FAILS:
        print('SUITE FAIL %d/%d' % (len(FAILS), len(CHECKS)))
        for name in FAILS:
            print('  failed: %s' % name)
        return 1
    print('SUITE PASS %d/%d' % (len(CHECKS), len(CHECKS)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
