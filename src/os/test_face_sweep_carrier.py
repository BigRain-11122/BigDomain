"""test_face_sweep_carrier.py - the opening scan asks the state carrier too.

Criteria AC-FSC1..AC-FSC6 were pinned in src/os/backlog.md at R3615 BEFORE
tools/face_sweep.py changed and before this file existed.

The measured reason: `tools/face_sweep.py --gates` is the cheapest station of a
round - read-only, renders nothing, writes nothing - and it answered only about
the face gates. The carrier's writability was asked by exactly one consumer,
tools/closeout_gate.py, which sits at the most expensive station. So a carrier
whose tail anchor is broken or whose log lost its tokens row could read green
from the first minute and be refused by the writer in the last minute.

This suite proves the coupling, not a second copy of it: the source is scanned
for one in-process call of the shipped `logs_toolkit.append_check`, and the row
is compared field by field against that face's own return. Every world is built
in the system temp dir; the live carrier is read and its (size, mtime_ns) must
not move.

Source discipline: pure ASCII, stdlib plus the shipped module, no network.
"""
import importlib.util
import io
import json
import os
import re
import shutil
import sys
import tempfile
import time
from contextlib import redirect_stdout

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOL = os.path.join(ROOT, 'tools', 'face_sweep.py')
SRC_OS = os.path.join(ROOT, 'src', 'os')
REGISTRY = os.path.join(ROOT, 'src', 'sandbox', 'reconcile_all.py')
FAILS = []
CHECKS = []

if SRC_OS not in sys.path:
    sys.path.insert(0, SRC_OS)
import logs_toolkit as LT  # noqa: E402

LEDGER = 'R0007 tokens: local=~1k api=0 api_reason=fixture row'
GOOD = ['R0006 narrative row', LEDGER]
PASS_DRIVER = "import sys\nprint('VERDICT PASS 1/1')\nsys.exit(0)\n"


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


def write_carrier(path, items, tick=7, indent=16, eol='\r\n', tail=''):
    pad = ' ' * indent
    rows = ','.join(eol + pad + json.dumps(x) for x in items)
    text = ('{' + eol + '  "log": [' + rows + eol + '  ],' + eol
            + pad + '"tick":' + str(tick) + eol + '}' + tail)
    blob = text.encode('utf-8')
    folder = os.path.dirname(path)
    if folder and not os.path.isdir(folder):
        os.makedirs(folder)
    with open(path, 'wb') as fh:
        fh.write(blob)
    return blob


def write(path, text):
    folder = os.path.dirname(path)
    if folder and not os.path.isdir(folder):
        os.makedirs(folder)
    with open(path, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(text)


def code_only(src):
    """The region with its docstring and comment lines dropped."""
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
    """True only when the row asks the shared face and restates nothing."""
    body = code_only(text)
    if body.count('LT.append_check(') != 1:
        return False
    for banned in ('APPEND_TAIL_RE', 'LEDGER_ROW_RE', '78500', 're.search'):
        if banned in body:
            return False
    return True


def load_tool():
    spec = importlib.util.spec_from_file_location('face_sweep_carrier_under_test', TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def gates_world(tool, base, name, faces):
    """A throwaway world with green stub drivers and their page pairs."""
    world = os.path.join(base, name)
    tools = os.path.join(world, 'tools')
    preview = os.path.join(world, 'preview')
    os.makedirs(tools, exist_ok=True)
    os.makedirs(preview, exist_ok=True)
    write(os.path.join(tools, 'stub-pass.py'), PASS_DRIVER)
    for f in faces:
        write(os.path.join(world, f[3]), '<html>%s</html>\n' % f[0])
        write(os.path.join(world, f[4]), '{"id": "%s"}\n' % f[0])
    tool.ROOT = world
    tool.OUT_HTML = os.path.join(preview, 'face-sweep.html')
    tool.OUT_JSON = os.path.join(preview, 'face-sweep.json')
    tool.FACES = faces
    return world


def face(idx):
    return ('stub-' + idx, 'stub ' + idx, 'tools/stub-pass.py',
            'preview/stub-%s.html' % idx, 'preview/stub-%s.json' % idx,
            'a fixture face, it costs nothing')


def run_quiet(fn):
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = fn()
    return rc, buf.getvalue()


def carrier_rows(out):
    return [ln for ln in out.splitlines() if ln.startswith('CARRIER')]


def summary_row(out):
    rows = [ln for ln in out.splitlines() if ln.startswith('GATES ')]
    return rows[-1] if rows else ''


def main():
    started = time.time()
    tool = load_tool()
    live_carrier = os.path.join(ROOT, 'src', 'os', 'state.json')
    live_before = stamp(live_carrier)
    with io.open(TOOL, encoding='utf-8') as fh:
        src = fh.read()
    base = tempfile.mkdtemp(prefix='face-sweep-carrier-')
    try:
        # ---- AC-FSC1 one shared definition, no local restatement.
        start = src.index('def carrier_face(')
        end = src.index('def gates(')
        body = src[start:end]
        ok('AC-FSC1 the carrier row calls the shared append check once',
           body.count('LT.append_check(') == 1,
           'calls=%d' % body.count('LT.append_check('))
        ok('AC-FSC1 no tail regex, ledger regex or gate number is restated',
           shares_append_check(body))
        mutant = body.replace('going = LT.append_check(target)', 'going = {}')
        ok('AC-FSC1 negative control - deleting the call turns the law red',
           shares_append_check(mutant) is False)

        # ---- AC-FSC2 the row equals the face's own return, field by field.
        good_dir = os.path.join(base, 'good')
        good_path = os.path.join(good_dir, 'state.json')
        write_carrier(good_path, GOOD, tick=7)
        tool.CARRIER = good_path
        gates_world(tool, base, 'good-world', [face('a'), face('b')])
        rc, out = run_quiet(lambda: tool.gates({'gates': True, 'faces_json': None,
                                                'timeout': 30}))
        rows = carrier_rows(out)
        going = LT.append_check(good_path)
        want = ('CARRIER append_ok=true caliber=%d ledger=%s bytes=%d margin=%d'
                % (going['caliber'], going['ledger'], going['bytes'], going['margin']))
        ok('AC-FSC2 a canonical carrier publishes append_ok with the face own numbers',
           rc == 0 and len(rows) == 1 and rows[0] == want,
           rows[0] if rows else 'no CARRIER row')
        ok('AC-FSC2 the four numbers are the face return, not a second count',
           len(rows) == 1 and ('bytes=%d ' % going['bytes']) in rows[0]
           and rows[0].endswith('margin=%d' % going['margin']))

        # ---- AC-FSC3 a red carrier is named and stays off the face rows.
        anchor_dir = os.path.join(base, 'anchor')
        anchor_path = os.path.join(anchor_dir, 'state.json')
        write_carrier(anchor_path, GOOD, tick=7, tail=' ')
        tool.CARRIER = anchor_path
        rc, out = run_quiet(lambda: tool.gates({'gates': True, 'faces_json': None,
                                                'timeout': 30}))
        face_rows = [ln for ln in out.splitlines() if ln.startswith('gate ')]
        ok('AC-FSC3 a broken tail anchor refuses by name and names the writer code',
           rc == 2 and 'CARRIER FAIL %s E_LAC_ANCHOR' % tool.E_FSW_CARRIER in out,
           carrier_rows(out)[0] if carrier_rows(out) else 'no CARRIER row')
        ok('AC-FSC3 the faces stay green while the carrier is red',
           len(face_rows) == 2 and all('rc=0' in ln for ln in face_rows),
           ','.join(ln.split()[1] for ln in face_rows))
        ok('AC-FSC3 the summary carries the unhealthy reading and the exit is 2',
           'carrier=UNHEALTHY' in summary_row(out) and rc == 2, summary_row(out))

        ledger_dir = os.path.join(base, 'ledger')
        ledger_path = os.path.join(ledger_dir, 'state.json')
        write_carrier(ledger_path, ['R0006 narrative row'], tick=7)
        tool.CARRIER = ledger_path
        rc, out = run_quiet(lambda: tool.gates({'gates': True, 'faces_json': None,
                                                'timeout': 30}))
        ok('AC-FSC3 a log with no tokens row refuses with the ledger code',
           rc == 2 and 'CARRIER FAIL %s E_LAC_LEDGER' % tool.E_FSW_CARRIER in out,
           carrier_rows(out)[0] if carrier_rows(out) else 'no CARRIER row')

        # ---- AC-FSC4 read-only and deterministic.
        tool.CARRIER = good_path
        before = (stamp(good_path), stamp(live_carrier))
        rc1, out1 = run_quiet(lambda: tool.gates({'gates': True, 'faces_json': None,
                                                  'timeout': 30}))
        rc2, out2 = run_quiet(lambda: tool.gates({'gates': True, 'faces_json': None,
                                                  'timeout': 30}))
        after = (stamp(good_path), stamp(live_carrier))
        ok('AC-FSC4 neither the private world nor the live carrier moves',
           before == after and rc1 == 0 and rc2 == 0,
           'before=%r after=%r' % (before, after))
        ok('AC-FSC4 the carrier row is byte-identical across runs',
           carrier_rows(out1) == carrier_rows(out2) and len(carrier_rows(out1)) == 1,
           carrier_rows(out1)[0] if carrier_rows(out1) else 'no CARRIER row')

        # ---- AC-FSC5 additive: old shapes keep their bytes, new field is a tail.
        ok('AC-FSC5 the summary prefix is unchanged and the field is appended',
           summary_row(out1).startswith(
               'GATES PASS gates=2 green=2 red=0 red_ids=none mutated=none')
           and summary_row(out1).endswith('carrier=HEALTHY'), summary_row(out1))
        ok('AC-FSC5 the per-face row keeps its shape',
           any(re.match(r'^gate stub-a\s+rc=0\s+mutated=0 ', ln) for ln in out1.splitlines()))
        ok('AC-FSC5 the board sweep and the board check were not touched',
           'carrier' not in code_only(src[src.index('def refresh_face('):
                                        src.index('def _src_os(')]).lower()
           and 'carrier' not in code_only(src[src.index('def check('):
                                          src.index('def main(')]).lower())

        # ---- AC-FSC6 hygiene and wiring.
        try:
            src.encode('ascii')
            ascii_ok = True
        except UnicodeEncodeError:
            ascii_ok = False
        ok('AC-FSC6 the tool source is pure ASCII', ascii_ok)
        body_all = code_only(src)
        banned = [m for m in ('import socket', 'import urllib', 'import requests',
                              'http.client') if m in body_all]
        ok('AC-FSC6 no network import reached the tool', not banned, ','.join(banned) or 'none')
        with io.open(REGISTRY, encoding='utf-8') as fh:
            reg = fh.read()
        ok('AC-FSC6 the suite is wired as os-face-sweep-carrier(6)',
           '("os-face-sweep-carrier",' in reg
           and 'test_face_sweep_carrier.py"), 6)' in reg)
        crit = sorted(set(re.findall(r'AC-FSC\d', ' '.join(CHECKS))))
        ok('AC-FSC6 every declared criterion is measured', crit == ['AC-FSC1', 'AC-FSC2',
           'AC-FSC3', 'AC-FSC4', 'AC-FSC5', 'AC-FSC6'], ','.join(crit))
    finally:
        shutil.rmtree(base, ignore_errors=True)
    total = len(CHECKS)
    if FAILS:
        print('SUITE FAIL %d/%d in %.1fs' % (total - len(FAILS), total, time.time() - started))
        print('failed: %s' % ','.join(FAILS))
        return 2
    print('SUITE PASS %d/%d in %.1fs' % (total, total, time.time() - started))
    return 0


if __name__ == '__main__':
    sys.exit(main())
