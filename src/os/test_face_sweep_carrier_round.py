"""test_face_sweep_carrier_round.py - the opening scan publishes the round-main reading.

Criteria AC-FSR1..AC-FSR5 were pinned in src/os/backlog.md at R3628 BEFORE
tools/face_sweep.py changed and before this file existed.

The measured gap: `logs_toolkit.append_check` already returns `round_main` and
`round` - whether the newest round's narrative main line carries a date and an
uppercase label - but the CARRIER row published by the cheapest station of a
round (`face_sweep --gates`, read-only, zero writes) dropped both keys. So a
carrier that can take the next line but whose newest round main is illegal read
`append_ok=true` for a whole round and was refused at the closeout gate, the
most expensive station.

This suite proves the forwarding, not a second measurement: the source region
is scanned for one in-process call of the shipped check, and every published
field is compared against that face's own return. Every world is built in the
system temp dir; the live carrier is read and its (size, mtime_ns) must not
move.

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
LEGAL = ['2026-11-28 R0006 PRODUCT: fixture row', LEDGER]
UNDATED = ['R0006 narrative row', LEDGER]
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


def write(path, text):
    folder = os.path.dirname(path)
    if folder and not os.path.isdir(folder):
        os.makedirs(folder)
    with open(path, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(text)


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


def forwards_only(body):
    """True only when the region forwards the shared face and measures nothing."""
    text = code_only(body)
    if text.count('LT.append_check(') != 1:
        return False
    for banned in ('round_main_verdict(', 'def check_round_main_shape', 'E_RMS_'):
        if banned in text:
            return False
    return True


def load_tool():
    spec = importlib.util.spec_from_file_location('face_sweep_round_under_test', TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def face(idx):
    return ('stub-' + idx, 'stub ' + idx, 'tools/stub-pass.py',
            'preview/stub-%s.html' % idx, 'preview/stub-%s.json' % idx,
            'a fixture face, it costs nothing')


def gates_world(tool, base, name, faces):
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
    base = tempfile.mkdtemp(prefix='face-sweep-round-')
    try:
        # ---- AC-FSR1 the reading comes from the one shared face.
        start = src.index('def carrier_face(')
        end = src.index('def gates(')
        body = src[start:end]
        ok('AC-FSR1 the carrier row forwards the shared append check once',
           body.count('LT.append_check(') == 1,
           'calls=%d' % body.count('LT.append_check('))
        ok('AC-FSR1 no round-main law is restated inside the row',
           forwards_only(body))
        mutant = body.replace('going = LT.append_check(target)', 'going = {}')
        ok('AC-FSR1 negative control - deleting the call turns the law red',
           forwards_only(mutant) is False)

        # ---- AC-FSR2 the row equals the face return, field by field.
        legal_path = os.path.join(base, 'legal', 'state.json')
        write_carrier(legal_path, LEGAL, tick=7)
        tool.CARRIER = legal_path
        gates_world(tool, base, 'legal-world', [face('a'), face('b')])
        rc, out = run_quiet(lambda: tool.gates({'gates': True, 'faces_json': None,
                                               'timeout': 30}))
        rows = carrier_rows(out)
        going = LT.append_check(legal_path)
        want = ('CARRIER append_ok=true caliber=%d ledger=%s bytes=%d margin=%d'
                ' round_main=%s round=%s'
                % (going['caliber'], going['ledger'], going['bytes'], going['margin'],
                   going['round_main'], going['round']))
        ok('AC-FSR2 a legal round main publishes round_main=OK round=6',
           going['round_main'] == 'OK' and going['round'] == 6,
           'round_main=%s round=%s' % (going['round_main'], going['round']))
        ok('AC-FSR2 the row is the four old fields plus the two forwarded keys',
           rc == 0 and len(rows) == 1 and rows[0] == want,
           rows[0] if rows else 'no CARRIER row')

        # ---- AC-FSR3 the summary forwards it, and a reading is not a ruling.
        ok('AC-FSR3 the summary ends with the forwarded reading',
           summary_row(out).endswith('carrier=HEALTHY round_main=OK'), summary_row(out))
        undated_path = os.path.join(base, 'undated', 'state.json')
        write_carrier(undated_path, UNDATED, tick=7)
        tool.CARRIER = undated_path
        rc, out = run_quiet(lambda: tool.gates({'gates': True, 'faces_json': None,
                                               'timeout': 30}))
        undated_facts = LT.append_check(undated_path)
        ok('AC-FSR3 an undated main line is published as its own reader code',
           len(carrier_rows(out)) == 1
           and ('round_main=%s round=%s' % (undated_facts['round_main'],
                                            undated_facts['round'])) in carrier_rows(out)[0]
           and undated_facts['round_main'] == 'E_RMS_NO_DATE',
           carrier_rows(out)[0] if carrier_rows(out) else 'no CARRIER row')
        ok('AC-FSR3 that reading does not rule: rc stays 0 and the carrier reads HEALTHY',
           rc == 0 and summary_row(out).endswith(
               'carrier=HEALTHY round_main=E_RMS_NO_DATE'), 'rc=%d %s' % (rc, summary_row(out)))
        anchor_path = os.path.join(base, 'anchor', 'state.json')
        write_carrier(anchor_path, LEGAL, tick=7, tail=' ')
        tool.CARRIER = anchor_path
        rc, out = run_quiet(lambda: tool.gates({'gates': True, 'faces_json': None,
                                               'timeout': 30}))
        ok('AC-FSR3 a refused carrier invents no reading - no round_main field at all',
           rc == 2 and 'round_main=' not in summary_row(out)
           and 'E_LAC_ANCHOR' in carrier_rows(out)[0] if carrier_rows(out) else False,
           summary_row(out))

        # ---- AC-FSR4 read-only and deterministic.
        tool.CARRIER = legal_path
        before = (stamp(legal_path), stamp(live_carrier))
        rc1, out1 = run_quiet(lambda: tool.gates({'gates': True, 'faces_json': None,
                                                 'timeout': 30}))
        rc2, out2 = run_quiet(lambda: tool.gates({'gates': True, 'faces_json': None,
                                                 'timeout': 30}))
        after = (stamp(legal_path), stamp(live_carrier))
        ok('AC-FSR4 neither the private world nor the live carrier moves',
           before == after and rc1 == 0 and rc2 == 0,
           'before=%r after=%r' % (before, after))
        ok('AC-FSR4 both published rows are byte-identical across runs',
           carrier_rows(out1) == carrier_rows(out2)
           and summary_row(out1) == summary_row(out2), summary_row(out1))

        # ---- AC-FSR5 hygiene and wiring.
        try:
            src.encode('ascii')
            ascii_ok = True
        except UnicodeEncodeError:
            ascii_ok = False
        ok('AC-FSR5 the tool source is pure ASCII', ascii_ok)
        body_all = code_only(src)
        banned = [m for m in ('import socket', 'import urllib', 'import requests',
                              'http.client') if m in body_all]
        ok('AC-FSR5 no network import reached the tool', not banned, ','.join(banned) or 'none')
        with io.open(REGISTRY, encoding='utf-8') as fh:
            reg = fh.read()
        ok('AC-FSR5 the suite is wired as os-face-sweep-carrier-round(15)',
           '("os-face-sweep-carrier-round",' in reg
           and 'test_face_sweep_carrier_round.py"), 15)' in reg)
        crit = sorted(set(re.findall(r'AC-FSR\d', ' '.join(CHECKS))))
        ok('AC-FSR5 every declared criterion is measured',
           crit == ['AC-FSR1', 'AC-FSR2', 'AC-FSR3', 'AC-FSR4', 'AC-FSR5'],
           ','.join(crit))
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
