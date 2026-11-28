"""test_logs_append_round_orphan.py - battery suite for the R3627 append law.

Criteria AC-LRO1..AC-LRO6 were pinned in src/os/backlog.md at R3627 BEFORE
src/os/logs_toolkit.py learned the orphan rule and before this file existed.
The measured reason: R3626 made the writer refuse a write that LEAVES the
newest round undated or unlabelled, but nothing refused a ledger row that
names a round the log never anchors. A tokens-only append therefore landed
green, advanced the tick onto a round with no narrative, and the CEO face
anchor (newest round label == tick) only disagreed at closeout - the same
family of cost that burned R3624 an empty round number.

The law is read, never copied: logs_toolkit asks ledger_lines through one
bridge (round_main_verdict / round_main_line), so the writer, the read face
and the closeout gate answer from one definition.

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
    base = tempfile.mkdtemp(prefix='lro_')
    try:
        # AC-LRO1: one bridge to the law, three asks, nothing copied.
        ok('AC-LRO1 the law is reached through one bridge only',
           tool_src.count('check_round_main_shape(') == 1
           and tool_src.count('format_round_main(') == 1
           and tool_src.count('round_main_verdict(') == 4
           and tool_src.count('round_main_line(') == 3,
           'law=%d fmt=%d verdict=%d line=%d'
           % (tool_src.count('check_round_main_shape('),
              tool_src.count('format_round_main('),
              tool_src.count('round_main_verdict('),
              tool_src.count('round_main_line(')))
        ok('AC-LRO1 no reader code and no verdict text is re-implemented',
           'def check_round_main_shape' not in tool_src
           and 'def parse_round_main_line' not in tool_src
           and 'ROUND_MAIN_RE' not in tool_src
           and 'E_RMS_' not in tool_src
           and 'ROUND-MAIN' not in tool_src,
           'rms=%d roundmain=%d regex=%d'
           % (tool_src.count('E_RMS_'), tool_src.count('ROUND-MAIN'),
              tool_src.count('ROUND_MAIN_RE')))
        ok('AC-LRO1 the round vocabulary comes from the shipped reader',
           'reader.LEDGER_PRESENCE_RE' in tool_src
           and 'reader.classify(' in tool_src
           and tool_src.count('reader.NARRATIVE_RE') >= 3,
           'narr=%d' % tool_src.count('reader.NARRATIVE_RE'))

        # AC-LRO2: the birth site - a tokens-only append is refused.
        d2 = os.path.join(base, 'w2')
        os.makedirs(d2)
        p = os.path.join(d2, 'state.json')
        write_world(p, ['2026-11-27 R100 PRODUCT: legal'], 100)
        before = read_bytes(p)
        r = run('append', '--round', 'R101', '--line',
                'R101 tokens: local=0 api=0 api_reason=orphan', '--file', p)
        ok('AC-LRO2 a tokens-only append is refused by E_LAP_ROUND_ORPHAN',
           r.returncode == 2 and 'APPEND REFUSED E_LAP_ROUND_ORPHAN' in out(r),
           'rc=%d out=%s' % (r.returncode, out(r)[:90]))
        ok('AC-LRO2 the refusal names the round, the tick and the anchor',
           'round=101' in out(r) and 'tick=101' in out(r)
           and 'anchored=no' in out(r), 'out=%s' % out(r)[:100])
        r2 = run('append', '--round', 'R101', '--line',
                 'R101 tokens: local=0 api=0 api_reason=orphan',
                 '--execute', '--file', p)
        ok('AC-LRO2 the same refusal holds on --execute and writes nothing',
           r2.returncode == 2 and read_bytes(p) == before,
           'rc=%d bytes=%d' % (r2.returncode, len(read_bytes(p))))

        # AC-LRO3: main row and ledger row in one append still plan green.
        r = run('append', '--round', 'R101', '--line',
                '2026-11-28 R101 PRODUCT: fine', '--line',
                'R101 tokens: local=0 api=0 api_reason=round', '--file', p)
        ok('AC-LRO3 one append carrying both rows plans green',
           r.returncode == 0
           and re.match(r'^APPEND PLAN round=R101 tick=101 lines=2 '
                        r'bytes=\d+->\d+ gate=78500 verdict=OK$',
                        out(r)) is not None, 'out=%s' % out(r)[:90])
        ex = run('append', '--round', 'R101', '--line',
                 '2026-11-28 R101 PRODUCT: fine', '--line',
                 'R101 tokens: local=0 api=0 api_reason=round',
                 '--execute', '--file', p)
        doc = json.loads(read_bytes(p).decode('utf-8'))
        ok('AC-LRO3 execute lands verified with the tick advanced once',
           ex.returncode == 0 and 'verified=true' in out(ex)
           and doc['tick'] == 101
           and doc['log'][-2].startswith('2026-11-28 R101 PRODUCT:')
           and doc['log'][-1].startswith('R101 tokens:'),
           'rc=%d tick=%s last=%r'
           % (ex.returncode, doc.get('tick'), doc['log'][-1][:30]))

        # AC-LRO4: the law blocks the disease, not the writer.
        d4 = os.path.join(base, 'w4')
        os.makedirs(d4)
        q = os.path.join(d4, 'state.json')
        write_world(q, ['2026-11-27 R100 PRODUCT: legal'], 100)
        r = run('append', '--round', 'R101', '--line', 'note only',
                '--file', q)
        ok('AC-LRO4 a line with no round number is not blocked',
           r.returncode == 0 and 'verdict=OK' in out(r),
           'rc=%d out=%s' % (r.returncode, out(r)[:70]))
        kept = read_bytes(q)
        r = run('append', '--round', 'R101', '--line',
                'R100 tokens: local=0 api=0 api_reason=stale round',
                '--file', q)
        ok('AC-LRO4 a ledger row for another round is refused as stale',
           r.returncode == 2 and 'E_LAP_ROUND_ORPHAN' in out(r)
           and 'round=100' in out(r) and 'anchored=yes' in out(r),
           'rc=%d out=%s' % (r.returncode, out(r)[:100]))
        ok('AC-LRO4 the stale refusal writes nothing',
           read_bytes(q) == kept, 'bytes=%d' % len(read_bytes(q)))

        # AC-LRO5: the read face publishes the same law as a reading.
        c = run('append', '--check')
        lines = [ln for ln in out(c).splitlines() if ln.strip()]
        ok('AC-LRO5 the live read face still prints exactly one line',
           c.returncode == 0 and len(lines) == 1
           and re.match(r'^APPEND CHECK PASS bytes=\d+ gate=78500 '
                        r'margin=\d+ tick=\d+ log=\d+ ledger=R\d+ api=\d+$',
                        lines[0]) is not None, 'lines=%d out=%s'
           % (len(lines), out(c)[:90]))
        c2 = run('append', '--check')
        ok('AC-LRO5 the read face leaves the carrier untouched',
           stamp(LIVE) == live_before and out(c2) == out(c),
           'before=%s' % (live_before,))
        d5 = os.path.join(base, 'w5')
        os.makedirs(d5)
        s5 = os.path.join(d5, 'state.json')
        write_world(s5, ['R099 old undated',
                         'R099 tokens: local=1k api=0'
                         ' api_reason=diseased world reading'], 99)
        c3 = run('append', '--check', '--file', s5)
        lines3 = [ln for ln in out(c3).splitlines() if ln.strip()]
        ok('AC-LRO5 a diseased carrier prints the reader own verdict line',
           c3.returncode == 0 and len(lines3) == 2
           and 'ROUND-MAIN FAIL' in lines3[1]
           and 'tick=99' in lines3[1],
           'rc=%d lines=%s' % (c3.returncode, lines3))

        # AC-LRO6: hygiene and wiring.
        ok('AC-LRO6 the tool source stays pure ASCII',
           all(ord(ch) < 128 for ch in tool_src), 'bytes=%d' % len(tool_src))
        net = [w for w in ('import socket', 'import urllib', 'import requests')
               if w in tool_src]
        ok('AC-LRO6 no network import reached the tool', not net, str(net))
        registry = io.open(REGISTRY, 'r', encoding='utf-8').read()
        ok('AC-LRO6 the battery row is wired',
           registry.count('os-logs-append-round-orphan') == 1,
           'rows=%d' % registry.count('os-logs-append-round-orphan'))
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
