"""test_closeout_carrier_append.py - battery suite for the closeout carrier/append coupling.

Criteria AC-CGA1..AC-CGA6 were pinned in src/os/backlog.md at R3614 BEFORE
tools/closeout_gate.py changed and before this file existed. The measured
reason: the closeout carrier row judged the carrier's own shape (bytes, gate,
layout, newline items) but never asked the face that will write next, so a
tail anchor that no longer ends the file or a log with no tokens ledger row
could read PASS at closeout and be refused by the very next append.

The reading is taken by calling logs_toolkit.append_check in process. This
suite proves the coupling, not a second copy of it: the source is scanned for
the call, and the numbers on the row are compared field by field with the
check face's own return.

Isolation: every world is a private tempdir. The repo state.json is only ever
read, measured by (size, mtime_ns) before and after.

Source discipline: pure ASCII, stdlib only, no clock in assertions, no
network, no shell beyond running the older suite.
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
TOOLS = os.path.join(ROOT, 'tools')
SRC_OS = os.path.join(ROOT, 'src', 'os')
LIVE = os.path.join(SRC_OS, 'state.json')
LEDGER = 'R3613 tokens: local=~1k api=0 api_reason=suite world'

sys.path.insert(0, TOOLS)
sys.path.insert(0, SRC_OS)

import closeout_gate as CG          # noqa: E402
import logs_toolkit as LT           # noqa: E402

CHECKS = []
FAILS = []


def ok(name, cond, detail=''):
    CHECKS.append(name)
    if cond:
        print('  | PASS %s %s' % (name, detail))
    else:
        FAILS.append(name)
        print('  | FAIL %s %s' % (name, detail))


def stamp(path):
    st = os.stat(path)
    return (st.st_size, st.st_mtime_ns)


def write_world(path, items, tick, indent=16, eol='\r\n'):
    pad = ' ' * indent
    rows = ','.join(eol + pad + json.dumps(x) for x in items)
    text = ('{' + eol + '  "log": [' + rows + eol + '  ],' + eol
            + pad + '"tick":' + str(tick) + eol + '}')
    blob = text.encode('utf-8')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        f.write(blob)
    return blob


def world(base, name, items, tick=7, indent=16, eol='\r\n'):
    d = os.path.join(base, name)
    p = os.path.join(d, 'src', 'os', 'state.json')
    blob = write_world(p, items, tick, indent=indent, eol=eol)
    return d, p, blob


GOOD = ['R3613 narrative row', LEDGER]


def code_only(src):
    """The body with its docstring and its comment lines dropped."""
    out = []
    in_doc = False
    for ln in src.splitlines():
        s = ln.strip()
        marks = s.count('"""')
        if in_doc:
            if marks:
                in_doc = False
            continue
        if marks:
            if marks == 1:
                in_doc = True
            continue
        if s.startswith('#'):
            continue
        out.append(ln)
    return '\n'.join(out)


def shares_append_check(text):
    """True only when the body asks the shared face and restates nothing."""
    body = code_only(text)
    if body.count('LT.append_check(') != 1:
        return False
    for banned in ('APPEND_TAIL_RE', 'LEDGER_ROW_RE', '78500'):
        if banned in body:
            return False
    return True


def main():
    body = io.open(os.path.join(TOOLS, 'closeout_gate.py'), 'r',
                   encoding='utf-8').read()
    start = body.index('def check_carrier(')
    end = body.index('def check_ledger(')
    carrier_src = body[start:end]

    base = tempfile.mkdtemp(prefix='cga_')
    try:
        # AC-CGA1: one shared definition, no local restatement.
        ok('AC-CGA1 the carrier body calls the shared append check once',
           carrier_src.count('LT.append_check(') == 1,
           'calls=%d' % carrier_src.count('LT.append_check('))
        ok('AC-CGA1 no tail regex, ledger regex or gate number is restated',
           shares_append_check(carrier_src))
        mutant = carrier_src.replace('going = LT.append_check(state)',
                                     'going = {}')
        ok('AC-CGA1 negative control - deleting the call turns the law red',
           not shares_append_check(mutant))

        # AC-CGA2: the positive world, and the row agrees with the face.
        d, p, blob = world(base, 'good', GOOD)
        good_ok, good_row = CG.check_carrier(d)
        reading = LT.append_check(p)
        ok('AC-CGA2 a canonical carrier passes and publishes append_ok',
           good_ok and 'append_ok=true caliber=16' in good_row, good_row)
        ok('AC-CGA2 the row repeats the face own ledger, not a typed one',
           ('ledger=%s' % reading['ledger']) in good_row
           and reading['ledger'] == 'R3613')
        got_bytes = int(re.search(r'\bbytes=(\d+)\b', good_row).group(1))
        got_margin = int(re.search(r'\bmargin=(-?\d+)\b', good_row).group(1))
        ok('AC-CGA2 bytes and margin are the face own numbers',
           got_bytes == reading['bytes'] == len(blob)
           and got_margin == reading['margin'])
        ok('AC-CGA2 the ten older fields keep their order ahead of the new',
           re.search(r'^CARRIER bytes=\d+ gate=\d+ margin=-?\d+ '
                     r'fold_needed=(true|false) layout_ok=(true|false) '
                     r'crlf=\d+ bare_lf=\d+ indent_anomaly=\d+ '
                     r'log_items=\d+ newline_items=\d+ append_ok=true ',
                     good_row) is not None)

        # AC-CGA3: the tail anchor is the writer's law too.
        d, p, blob = world(base, 'anchor', GOOD)
        with open(p, 'wb') as f:
            f.write(blob + b' ')
        a_ok, a_row = CG.check_carrier(d)
        raised = ''
        try:
            LT.append_check(p)
        except LT.AppendCheckError as exc:
            raised = str(exc)
        ok('AC-CGA3 a broken tail anchor refuses the closeout by name',
           (not a_ok) and 'CARRIER FAIL %s' % CG.E_CLG_CARRIER_APPEND
           in a_row and 'E_LAC_ANCHOR' in a_row, a_row)
        ok('AC-CGA3 the write face names the same code', raised == 'E_LAC_ANCHOR',
           raised)

        # AC-CGA4: a log with no parseable tokens row is the other disease.
        d, p, blob = world(base, 'noledger', ['R3613 narrative row'])
        n_ok, n_row = CG.check_carrier(d)
        ok('AC-CGA4 a log with no tokens row refuses as E_LAC_LEDGER',
           (not n_ok) and 'E_LAC_LEDGER' in n_row
           and 'E_CLG_CARRIER_APPEND' in n_row, n_row)
        d, p, blob = world(base, 'badledger',
                           ['R3613 tokens: local=x api=two api_reason=y'])
        b_ok, b_row = CG.check_carrier(d)
        ok('AC-CGA4 a tokens row whose api is not a number refuses alike',
           (not b_ok) and 'E_LAC_LEDGER' in b_row, b_row)

        # AC-CGA5: read-only and deterministic, in a world and on the live tree.
        d, p, blob = world(base, 'again', GOOD)
        before = stamp(p)
        r1 = CG.check_carrier(d)
        mid = stamp(p)
        r2 = CG.check_carrier(d)
        after = stamp(p)
        ok('AC-CGA5 a private world is left byte and mtime identical',
           before == mid == after, '%s' % (before,))
        ok('AC-CGA5 two runs are byte-identical, so no clock leaks in',
           r1 == r2 and r1[0])
        live_before = stamp(LIVE)
        live_ok, live_row = CG.check_carrier(ROOT)
        live_after = stamp(LIVE)
        ok('AC-CGA5 the live carrier is read, not rewritten',
           live_before == live_after, '%s' % (live_before,))
        ok('AC-CGA5 the live row is green and names its own ledger',
           live_ok and 'append_ok=true' in live_row
           and re.search(r'\bledger=R\d{3,5}\b', live_row) is not None,
           live_row)

        # AC-CGA6: additive only - the three older refusals still speak.
        d, p, blob = world(base, 'barelf', GOOD, eol='\n')
        l_ok, l_row = CG.check_carrier(d)
        ok('AC-CGA6 a bare-LF carrier still refuses as LAYOUT',
           (not l_ok) and CG.E_CLG_CARRIER_LAYOUT in l_row, l_row)
        d, p, blob = world(base, 'multiline', ['R3613 line one\nline two', LEDGER])
        m_ok, m_row = CG.check_carrier(d)
        ok('AC-CGA6 a multi-line log item still refuses as NEWLINE',
           (not m_ok) and CG.E_CLG_CARRIER_NEWLINE in m_row, m_row)
        older = subprocess.run(
            [sys.executable, os.path.join(SRC_OS, 'test_closeout_gate.py')],
            capture_output=True)
        tail = (older.stdout or b'').decode('utf-8', 'replace').strip()
        ok('AC-CGA6 the older closeout suite still reads green',
           older.returncode == 0 and 'SUITE PASS' in tail,
           tail.splitlines()[-1] if tail else 'no output')
        src = io.open(os.path.abspath(__file__), 'r', encoding='utf-8').read()
        pure = all(ord(ch) < 128 for ch in src)
        mods = set()
        for node in ast.walk(ast.parse(src)):
            if isinstance(node, ast.Import):
                mods.update(a.name.split('.')[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                mods.add(node.module.split('.')[0])
        net = mods & {'sock' + 'et', 'url' + 'lib', 'http', 'requests'}
        ok('AC-CGA6 this suite is pure ASCII and imports no network module',
           pure and not net, 'mods=%d net=%s' % (len(mods), sorted(net)))
    finally:
        shutil.rmtree(base, ignore_errors=True)

    total = len(CHECKS)
    if FAILS:
        print('SUITE FAIL %d/%d over 6 criteria' % (total - len(FAILS), total))
        for name in FAILS:
            print('  FAILED %s' % name)
        return 1
    print('SUITE PASS %d/%d over 6 criteria' % (total, total))
    return 0


if __name__ == '__main__':
    sys.exit(main())
