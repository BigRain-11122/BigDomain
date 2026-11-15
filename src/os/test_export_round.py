"""Battery suite for src/os/export_round.py - criteria AC-EXPW1..AC-EXPW6.

AC-EXPW1..AC-EXPW6 were pinned in src/os/backlog.md at R2780 BEFORE this suite or
the tool existed. The tool is read against a PRIVATE world built by copying the
few real inputs it needs, so a test run never rewrites the CEO-visible face.

Source discipline: pure ASCII, stdlib only, no clock, no network, no shell.
"""
import ast
import importlib.util
import io
import json
import os
import re
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOL = os.path.join(ROOT, 'src', 'os', 'export_round.py')
FAILS = []
CHECKS = []
ROUND_LITERAL = re.compile(r'R\d{4}')


def ok(name, cond, detail=''):
    CHECKS.append(name)
    if cond:
        print('  | PASS %s %s' % (name, detail))
    else:
        FAILS.append(name)
        print('  | FAIL %s %s' % (name, detail))


def read(path):
    with io.open(path, 'r', encoding='utf-8') as f:
        return f.read()


def write(path, text):
    d = os.path.dirname(path)
    if d and not os.path.isdir(d):
        os.makedirs(d)
    with io.open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)


def copy(src, dst):
    d = os.path.dirname(dst)
    if d and not os.path.isdir(d):
        os.makedirs(d)
    shutil.copyfile(src, dst)


def build_world(tick, drop_tick_row=False, dupe_tick_row=False):
    """A private world carrying just the inputs the hook reads."""
    import check_export_consistency as cec
    label = cec._load_patterns().get('tick_row_label')
    d = tempfile.mkdtemp(prefix='expw-')
    copy(os.path.join(ROOT, 'src', 'os', 'backlog.md'),
         os.path.join(d, 'src', 'os', 'backlog.md'))
    write(os.path.join(d, 'src', 'os', 'state.json'),
          json.dumps({'tick': tick,
                      'log': ['2026-11-15 R%s SOMETHING MEASURED IN THIS WINDOW'
                              % tick,
                              'R%s tokens: local=1k api=0 api_reason=ledger line'
                              % tick]}, ensure_ascii=False))
    for name in ('main.md', 'tech.md', 'explore.md'):
        src = os.path.join(ROOT, 'state', 'queue', name)
        if os.path.isfile(src):
            copy(src, os.path.join(d, 'state', 'queue', name))
    prev = os.path.join(ROOT, 'preview')
    for name in os.listdir(prev):
        if name.endswith('.html') or name.endswith('.json'):
            copy(os.path.join(prev, name), os.path.join(d, 'preview', name))
    write(os.path.join(d, 'preview', 'zz-late-face.html'), '<!DOCTYPE html>\n')
    write(os.path.join(d, 'preview', 'zz-late-face.json'), '{}\n')
    rows = [['1', 'a past row'], ['2', 'another past row']]
    if not drop_tick_row:
        rows.append([tick, label])
    if dupe_tick_row:
        rows.append([tick, label])
    face = {'results': rows, 'outs': ['x'], 'do': 'x',
            'ceo_face': {'current': 'x', 'latest_artifact': 'x',
                         'next_milestone': 'x'},
            'self_drive': {}}
    write(os.path.join(d, 'docs', 'status-export.json'),
          json.dumps(face, ensure_ascii=False, indent=2) + '\n')
    return d


def load_tool():
    spec = importlib.util.spec_from_file_location('export_round_under_test', TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    if not os.path.isfile(TOOL):
        print('SUITE FAIL 0/%d tool missing' % 6)
        return 1
    sys.path.insert(0, os.path.join(ROOT, 'src', 'os'))
    src = read(TOOL)
    mod = load_tool()
    worlds = []
    try:
        # ---- AC-EXPW1: every line moves with the files, nothing is typed in ----
        w1 = build_world(9001)
        worlds.append(w1)
        s1 = json.loads(read(os.path.join(w1, 'src', 'os', 'state.json')))
        d1 = mod.derive(w1, s1, 'T1')
        w2 = build_world(9002)
        worlds.append(w2)
        s2 = json.loads(read(os.path.join(w2, 'src', 'os', 'state.json')))
        os.remove(os.path.join(w2, 'preview', 'zz-late-face.html'))
        os.remove(os.path.join(w2, 'preview', 'zz-late-face.json'))
        d2 = mod.derive(w2, s2, 'T2')
        ok('AC-EXPW1 current follows the live tick',
           d1['current'].startswith('R9001') and d2['current'].startswith('R9002'),
           d1['current'][:18])
        ok('AC-EXPW1 the ledger line is never mistaken for the narrative',
           'SOMETHING MEASURED' in d1['current']
           and 'tokens:' not in d1['current'], d1['current'][:40])
        ok('AC-EXPW1 latest follows the newest pair on disk',
           'zz-late-face.html' in d1['latest'] and 'zz-late-face' not in d2['latest'],
           d1['latest'][:34])
        ok('AC-EXPW1 next follows the open board row',
           bool(d1['next']) and 'DONE' not in d1['next'].split('.')[0],
           d1['next'][:34])
        tree = ast.parse(src)
        docstrings = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.FunctionDef, ast.ClassDef)):
                body = getattr(node, 'body', [])
                if body and isinstance(body[0], ast.Expr) and \
                        isinstance(body[0].value, ast.Constant) and \
                        isinstance(body[0].value.value, str):
                    docstrings.add(id(body[0].value))
        literals = [n.value for n in ast.walk(tree)
                    if isinstance(n, ast.Constant) and isinstance(n.value, str)
                    and id(n) not in docstrings]
        bad = [s for s in literals if ROUND_LITERAL.search(s)]
        ok('AC-EXPW1 no round-number literal survives in the code strings',
           not bad, 'bad=%s' % bad[:2])

        # ---- AC-EXPW2: read-back equals the derived values, tick row spliced ----
        data, d = mod.payload(w1, s1, 'T1')
        ok('AC-EXPW2 the built face carries the derived three lines',
           data['ceo_face']['current'] == d['current']
           and data['ceo_face']['latest_artifact'] == d['latest']
           and data['ceo_face']['next_milestone'] == d['next'],
           'tick=%s' % d['tick'])
        row = [r for r in data['results'] if isinstance(r, list) and len(r) >= 2
               and str(r[0]) == '9001']
        ok('AC-EXPW2 the tick row slot equals the live tick',
           len(row) == 1, 'rows=%d' % len(row))
        ok('AC-EXPW2 the newest pair heads the outs band',
           data['outs'][0] == d['latest'], data['outs'][0][:30])

        # ---- AC-EXPW3: the self_drive block is the shipped recount, not a copy ----
        import check_export_consistency as cec
        need = ('window', 'window_days', 'log_lines_in_window', 'proposals_total',
                'queue_main_open', 'queue_tech_open', 'queue_explore_open')
        ok('AC-EXPW3 every self_drive key comes from the shipped recompute',
           all(k in cec.recompute()[0] for k in need),
           'keys=%d' % len(need))
        ok('AC-EXPW3 a private world never invents a second derivation',
           data['self_drive'] == json.loads(
               read(os.path.join(w1, 'docs', 'status-export.json')))['self_drive'])

        # ---- AC-EXPW4: --check is read-only ----
        exp = os.path.join(ROOT, 'docs', 'status-export.json')
        snap = (os.path.getsize(exp), os.stat(exp).st_mtime_ns)
        first = mod.check(ROOT)
        snap2 = (os.path.getsize(exp), os.stat(exp).st_mtime_ns)
        ok('AC-EXPW4 --check writes nothing and both bytes and mtime hold',
           snap == snap2 and first == [], 'fails=%s' % first[:1])

        # ---- AC-EXPW5: a missing or duplicated tick row is refused, zero write ----
        w3 = build_world(9003, drop_tick_row=True)
        worlds.append(w3)
        s3 = json.loads(read(os.path.join(w3, 'src', 'os', 'state.json')))
        f3 = os.path.join(w3, 'docs', 'status-export.json')
        before = read(f3)
        err = ''
        try:
            mod.payload(w3, s3, 'T3')
        except ValueError as exc:
            err = str(exc)
        ok('AC-EXPW5 a missing tick row refuses with E_EXP and zero write',
           err.startswith('E_EXP') and read(f3) == before, err[:34])
        w4 = build_world(9004, dupe_tick_row=True)
        worlds.append(w4)
        s4 = json.loads(read(os.path.join(w4, 'src', 'os', 'state.json')))
        f4 = os.path.join(w4, 'docs', 'status-export.json')
        before4 = read(f4)
        err4 = ''
        try:
            mod.payload(w4, s4, 'T4')
        except ValueError as exc:
            err4 = str(exc)
        ok('AC-EXPW5 a duplicated tick row refuses with E_EXP and zero write',
           err4.startswith('E_EXP') and read(f4) == before4, err4[:34])

        # ---- AC-EXPW6: hygiene, one battery row, six criteria ----
        ok('AC-EXPW6 module source is pure ASCII', all(ord(c) < 128 for c in src))
        net = [m for m in ('urllib', 'requests', 'socket', 'http.client')
               if ('import ' + m) in src]
        ok('AC-EXPW6 no network import', not net, 'found=%s' % net)
        reg = read(os.path.join(ROOT, 'src', 'sandbox', 'reconcile_all.py'))
        hits = [m.start() for m in re.finditer(r'"os-export-round"', reg)]
        rows = []
        for pos in hits:
            window = reg[pos:pos + 160]
            found = re.search(r'test_export_round\.py"\)\s*,\s*(\d+)', window)
            if found:
                rows.append(found.group(1))
        ok('AC-EXPW6 exactly one battery row declares six criteria',
           rows == ['6'], 'rows=%s' % rows)
    finally:
        for w in worlds:
            shutil.rmtree(w, ignore_errors=True)

    total = len(CHECKS)
    if FAILS:
        print('SUITE FAIL %d/%d failed=%s' % (total - len(FAILS), total, FAILS))
        return 1
    print('SUITE PASS %d/%d' % (total, total))
    return 0


if __name__ == '__main__':
    sys.exit(main())
