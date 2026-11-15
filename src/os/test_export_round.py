"""Battery suite for src/os/export_round.py - criteria AC-EXPW1..AC-EXPW10.

AC-EXPW1..AC-EXPW6 were pinned in src/os/backlog.md at R2780 BEFORE this suite or
the tool existed. AC-EXPW7..AC-EXPW10 were pinned at R2805 BEFORE the board-page
exclusion existed. The tool is read against a PRIVATE world built by copying the
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
import time

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


def build_pair_world(rows, tick=9100):
    """A world whose preview/ holds exactly the pairs named in rows.

    rows is a list of (stem, age_seconds): a SMALLER age is a NEWER file, so the
    ordering of the derived line is controlled by the caller instead of by
    whatever mtimes the real tree happens to carry.
    """
    d = tempfile.mkdtemp(prefix='expw-pair-')
    write(os.path.join(d, 'src', 'os', 'state.json'),
          json.dumps({'tick': tick,
                      'log': ['R%s SOMETHING MEASURED IN THIS WINDOW' % tick]},
                     ensure_ascii=False))
    copy(os.path.join(ROOT, 'src', 'os', 'backlog.md'),
         os.path.join(d, 'src', 'os', 'backlog.md'))
    prev = os.path.join(d, 'preview')
    if not os.path.isdir(prev):
        os.makedirs(prev)
    now = time.time()
    for stem, age in rows:
        for ext, body in (('.html', '<!DOCTYPE html>\n'), ('.json', '{}\n')):
            p = os.path.join(prev, stem + ext)
            write(p, body)
            t = now - age
            os.utime(p, (t, t))
    label = 'TICK-ROW-LABEL'
    try:
        import check_export_consistency as cec
        label = cec._load_patterns().get('tick_row_label') or label
    except Exception:
        pass
    face = {'results': [[str(tick), label]], 'outs': ['x'], 'do': 'x',
            'ceo_face': {'current': 'x', 'latest_artifact': 'x',
                         'next_milestone': 'x'},
            'self_drive': {}}
    write(os.path.join(d, 'docs', 'status-export.json'),
          json.dumps(face, ensure_ascii=False, indent=2) + '\n')
    return d


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

        # ---- AC-EXPW7: a meta board page never occupies the product slot ----
        board = tuple(mod.BOARD_PAGES)
        ok('AC-EXPW7 the board set is an explicit constant, not a guess',
           board == ('ceo-blockers', 'face-sweep', 'battery-shard-report',
                     'index'), 'board=%s' % (board,))
        wp = build_pair_world([('ceo-blockers', 0), ('face-sweep', 10),
                               ('battery-shard-report', 20),
                               ('first-yuan-chain', 100)])
        worlds.append(wp)
        sp = json.loads(read(os.path.join(wp, 'src', 'os', 'state.json')))
        dp = mod.derive(wp, sp, 'TP')
        ok('AC-EXPW7 the newest pair on disk being a board page does not move '
           'the line', 'first-yuan-chain.html' in dp['latest']
           and 'ceo-blockers' not in dp['latest'], dp['latest'][:40])
        ok('AC-EXPW7 every skipped name is a member of the same constant',
           [os.path.basename(s).split('.html')[0] for s in dp['board_skipped']]
           == ['ceo-blockers', 'face-sweep', 'battery-shard-report'],
           'skipped=%d' % len(dp['board_skipped']))
        wp2 = build_pair_world([('first-yuan-chain', 0), ('ceo-blockers', 100)])
        worlds.append(wp2)
        sp2 = json.loads(read(os.path.join(wp2, 'src', 'os', 'state.json')))
        dp2 = mod.derive(wp2, sp2, 'TP2')
        ok('AC-EXPW7 a product pair on top needs no exclusion',
           'first-yuan-chain.html' in dp2['latest'] and dp2['board_skipped'] == []
           and dp2['newest_is_board'] is False, dp2['latest'][:40])
        real_stem = os.path.basename(mod.newest_artifact(ROOT)[0][0])[:-5]
        ok('AC-EXPW7 the live tree picks a non-board face',
           real_stem not in board, 'picked=%s' % real_stem)

        # ---- AC-EXPW8: with no product pair the face STATES the fact ----
        wb = build_pair_world([('ceo-blockers', 0), ('index', 10)])
        worlds.append(wb)
        sb = json.loads(read(os.path.join(wb, 'src', 'os', 'state.json')))
        db = mod.derive(wb, sb, 'TB')
        ok('AC-EXPW8 an all-board tree yields a stated fact, not a board name',
           'no product pair on disk' in db['latest']
           and 'preview/ceo-blockers.html' in db['latest'], db['latest'][:52])
        ok('AC-EXPW8 the stated fact is not a pair receipt',
           not re.match(r'^preview/[^ ]+\.html \(\d+B\) \+ ', db['latest']),
           db['latest'][:40])
        wb2 = build_pair_world([('ceo-blockers', 0), ('index', 10),
                                ('first-yuan-chain', 20)])
        worlds.append(wb2)
        sb2 = json.loads(read(os.path.join(wb2, 'src', 'os', 'state.json')))
        db2 = mod.derive(wb2, sb2, 'TB2')
        ok('AC-EXPW8 adding one product pair replaces the fact with its name',
           'no product pair on disk' not in db2['latest']
           and 'first-yuan-chain.html' in db2['latest'], db2['latest'][:40])
        we = build_pair_world([])
        worlds.append(we)
        se = json.loads(read(os.path.join(we, 'src', 'os', 'state.json')))
        de = mod.derive(we, se, 'TE')
        ok('AC-EXPW8 an empty preview keeps the existing empty-tree sentence',
           de['latest'] == '(no preview pair on disk)', de['latest'][:40])

        # ---- AC-EXPW9: what was skipped is published and derived ----
        data_p, d_p = mod.payload(wp, sp, 'TP')
        ok('AC-EXPW9 the face carries the skipped audit and the board flag',
           data_p['ceo_face']['board_pages_skipped'] == d_p['board_skipped']
           and bool(data_p['ceo_face']['newest_pair_on_disk_is_board']) is True,
           'skipped=%d' % len(data_p['ceo_face']['board_pages_skipped']))
        data_p2, d_p2 = mod.payload(wp2, sp2, 'TP2')
        ok('AC-EXPW9 the audit empties when no board pair is newer',
           data_p2['ceo_face']['board_pages_skipped'] == []
           and data_p2['ceo_face']['newest_pair_on_disk_is_board'] is False,
           'skipped=%d' % len(data_p2['ceo_face']['board_pages_skipped']))
        ok('AC-EXPW9 the audit names bytes so it cannot be typed in',
           all(re.search(r'\(\d+B\)$', s) for s in d_p['board_skipped']),
           d_p['board_skipped'][0][-12:] if d_p['board_skipped'] else 'none')

        # ---- AC-EXPW10: the gate carries AC-EXPW7 and AC-EXPW9 ----
        wc = build_pair_world([('ceo-blockers', 0), ('first-yuan-chain', 100)])
        worlds.append(wc)
        sc = json.loads(read(os.path.join(wc, 'src', 'os', 'state.json')))
        face_c = os.path.join(wc, 'docs', 'status-export.json')
        built, _ = mod.payload(wc, sc, 'TC')
        write(face_c, json.dumps(built, ensure_ascii=False, indent=2) + '\n')
        ok('AC-EXPW10 a correct private face reads clean',
           mod.check(wc) == [], 'fails=%s' % mod.check(wc)[:2])
        tampered = json.loads(read(face_c))
        tampered['ceo_face']['latest_artifact'] = \
            'preview/ceo-blockers.html (10B) + preview/ceo-blockers.json (3B)'
        write(face_c, json.dumps(tampered, ensure_ascii=False, indent=2) + '\n')
        fails_c = mod.check(wc)
        ok('AC-EXPW10 naming a board page reddens AC-EXPW7',
           any('AC-EXPW7' in f for f in fails_c), 'fails=%s' % fails_c[:2])
        tampered2 = json.loads(read(face_c))
        tampered2['ceo_face']['latest_artifact'] = \
            mod._fmt_pair(mod.newest_artifact(wc)[0])
        tampered2['ceo_face']['board_pages_skipped'] = []
        write(face_c, json.dumps(tampered2, ensure_ascii=False, indent=2) + '\n')
        fails_c2 = mod.check(wc)
        ok('AC-EXPW10 a silent exclusion reddens AC-EXPW9',
           any('AC-EXPW9' in f for f in fails_c2), 'fails=%s' % fails_c2[:2])
        restored, _ = mod.payload(wc, sc, 'TC')
        write(face_c, json.dumps(restored, ensure_ascii=False, indent=2) + '\n')
        ok('AC-EXPW10 restoring the derived face reads clean again',
           mod.check(wc) == [], 'fails=%s' % mod.check(wc)[:2])

        # ---- AC-EXPW6: hygiene, one battery row, ten criteria ----
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
        ok('AC-EXPW6 exactly one battery row declares ten criteria',
           rows == ['10'], 'rows=%s' % rows)
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
