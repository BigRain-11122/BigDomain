"""Battery suite for src/os/export_round.py.

R2901: this header no longer enumerates the criteria. The inventory used to be
typed here in prose and drifted silently (it still said "thirty-three criteria"
when the suite printed thirty-nine), so the ONE place the count is declared is
the `os-export-round` row in src/sandbox/reconcile_all.py, which
AC-EXPE4-registry-units grades against what this suite actually prints.

R2898: AC-EXPD7..AC-EXPD9 publish WHICH CLOCK the pair line's date came from
('commit' for the committer time of the last committed content change, 'mtime'
for a dirty, untracked or non-git file), grade that marker in both directions,
and hold the date group and the board-page/evidence faces in place while it
lands.

R2897: AC-EXPD4..AC-EXPD6 move the ORDERING stamp from the filesystem clock to
the committer time of the last committed content change.

R2895: AC-EXPE1..AC-EXPE4 pin the second derived CEO line (`latest_evidence`,
the newest top-level qa/*.log) and the one-line note that says which of the
evidence file and the product pair is newer. The product slot is NOT redefined -
a log is not a product page - and AC-EXPE4 holds the pair law and the registry
unit count in place while the new lines land.

R2878: AC-EXPA1/AC-EXPA2 are the R2877-pinned argument guard, landed under a
fresh prefix because that pin reused AC-EXPW11 (already printed here by the
fold-summary law) and AC-EXPW12 (the declared hole). The rename is recorded in
src/os/backlog.md at R2878; the meaning of the two criteria is unchanged.

R2860: the header above used to say AC-EXPW1..AC-EXPW14, which reads as fourteen
criteria although AC-EXPW12 has never printed, so R2859's both-unit measurement
counted thirteen EXPW ids while the registry counted eighteen - the missing five
were the EXPG family, omitted because only one prefix was counted. The registry
row was right and is unchanged; the header now names the hole and this suite
prints its own count at closeout.

AC-EXPG1..AC-EXPG5 were pinned in src/os/backlog.md at R2834 BEFORE the gate
existed: the exporter must ask the round-main shape law itself, so the face the
CEO downloads can no longer be written from a log whose newest round line lost
its date anchor (the R2831 defect), and the 226 one-off `state_append_R*.py`
appenders must retire with a measured zero-caller proof.

AC-EXPW1..AC-EXPW6 were pinned in src/os/backlog.md at R2780 BEFORE this suite or
the tool existed. AC-EXPW7..AC-EXPW10 were pinned at R2805 BEFORE the board-page
exclusion existed. AC-EXPW11/AC-EXPW12 already stood here (pinned at R2822 for
the fold-summary/narrative reading) when the R2823 pin reused those ids for the
archived-results criteria; the archived-results criteria are therefore landed as
AC-EXPW13/AC-EXPW14, and the R2823 board row carries a correction note rather
than being quietly rewritten. The tool is read against a PRIVATE world built by
copying the few real inputs it needs, so a test run never rewrites the
CEO-visible face.

Source discipline: pure ASCII, stdlib only, no clock, no network, no shell.
"""
import ast
import hashlib
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
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
    # R2895 measured: copy() does not preserve mtimes, so every copied pair lands
    # inside the same clock tick and the newest-pair sort fell through to the
    # NAME - the runner read ugc-gate-report as newest while a direct run read
    # zz-late-face. The fixture now stamps its late pair strictly above the
    # copies instead of relying on write order.
    prev_dir = os.path.join(d, 'preview')
    newest = max(os.path.getmtime(os.path.join(prev_dir, n))
                 for n in os.listdir(prev_dir))
    late = newest + 10
    for ext in ('.html', '.json'):
        p = os.path.join(prev_dir, 'zz-late-face' + ext)
        os.utime(p, (late, late))
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
    # R2834 disclosure: this fixture was written before the round-main shape law
    # existed and its log line carried no date prefix. The law now refuses such a
    # line (`E_EXP_ROUND_SHAPE`), and a fixture that stands for a HEALTHY world
    # must satisfy the law it is graded under - so the line is anchored. No
    # assertion was loosened; the AC-EXPW10 red-then-green is measured.
    write(os.path.join(d, 'src', 'os', 'state.json'),
          json.dumps({'tick': tick,
                      'log': ['2026-11-16 R%s SOMETHING MEASURED IN THIS WINDOW'
                              % tick]},
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


def _git_fixture(world, args, when=None):
    """Run one git command inside a fixture, with fixed identity and date."""
    env = dict(os.environ)
    if when is not None:
        stamp = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(when))
        env['GIT_AUTHOR_DATE'] = stamp
        env['GIT_COMMITTER_DATE'] = stamp
    env['GIT_AUTHOR_NAME'] = 'fixture'
    env['GIT_AUTHOR_EMAIL'] = 'fixture@example.invalid'
    env['GIT_COMMITTER_NAME'] = 'fixture'
    env['GIT_COMMITTER_EMAIL'] = 'fixture@example.invalid'
    return subprocess.run(['git', '-C', world] + args, env=env,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def build_git_pair_world(tick=9200):
    """A private world carrying a REAL git history with two controlled ages.

    R2897 AC-EXPD4 fixture: `touched-old` is committed at T1 and then touched to
    T3, while `genuinely-new` is committed at T2 with T1 < T2 < T3, so the mtime
    law and the content law MUST disagree about which pair is newest. Returns
    (world, t1, t2, t3), or (None, ...) when git itself is unavailable - the
    caller reports that instead of fabricating a green.
    """
    d = tempfile.mkdtemp(prefix='expw-git-')
    write(os.path.join(d, 'src', 'os', 'state.json'),
          json.dumps({'tick': tick,
                      'log': ['2026-11-16 R%s SOMETHING MEASURED IN THIS WINDOW'
                              % tick]}, ensure_ascii=False))
    copy(os.path.join(ROOT, 'src', 'os', 'backlog.md'),
         os.path.join(d, 'src', 'os', 'backlog.md'))
    prev = os.path.join(d, 'preview')
    os.makedirs(prev)
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
    t1 = 1767225600
    t2 = t1 + 86400
    t3 = t2 + 30 * 86400
    try:
        _git_fixture(d, ['init'])
        for stem, when, message in (('touched-old', t1, 'one'),
                                    ('genuinely-new', t2, 'two')):
            for ext, body in (('.html', '<!DOCTYPE html>\n'), ('.json', '{}\n')):
                path = os.path.join(prev, stem + ext)
                write(path, body)
                os.utime(path, (when, when))
            _git_fixture(d, ['add', '--', 'preview/' + stem + '.html',
                             'preview/' + stem + '.json'], when)
            _git_fixture(d, ['-c', 'user.name=fixture',
                             '-c', 'user.email=fixture@example.invalid',
                             'commit', '-m', message], when)
        for ext in ('.html', '.json'):
            path = os.path.join(prev, 'touched-old' + ext)
            os.utime(path, (t3, t3))
    except OSError:
        shutil.rmtree(d, ignore_errors=True)
        return None, t1, t2, t3
    return d, t1, t2, t3


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
        # R2896 AC-EXPD1: newest_artifact now returns the WHOLE _pairs row
        # (mtime, html, json, html_bytes, json_bytes), so the stem lives at
        # index 1 - the fixture follows the reader instead of the reader
        # keeping a stale slice for the fixture's sake.
        real_stem = os.path.basename(mod.newest_artifact(ROOT)[0][1])[:-5]
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
        # R2896: the receipt shape now ends with the pair's own date, so the
        # negative control tests THAT shape - a regex pinned to the old
        # date-less form would pass this arm for the wrong reason.
        ok('AC-EXPW8 the stated fact is not a pair receipt',
           not mod.PAIR_LINE_RE.match(db['latest']),
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
        # R2896: this arm used to type the OLD date-less line by hand, which the
        # new law would redden for the wrong reason (a stale shape, not a board
        # page in the product slot). It now renders the newest pair on disk - the
        # board page - through the shipped formatter, so the ONLY reason left to
        # fail is the exclusion law this arm exists to prove.
        tampered['ceo_face']['latest_artifact'] = \
            mod.fmt_pair(mod._pairs(wc)[0])
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

        # ---- AC-EXPW11: a fold summary is never the current narrative ----
        w11 = build_world(9011)
        worlds.append(w11)
        s11 = json.loads(read(os.path.join(w11, 'src', 'os', 'state.json')))
        headline = 'R9011 ENGINEERING: the round did one measurable thing'
        summary_line = ('2026-11-16 R9011 knife, prose of the operator choice: '
                        'log items 4..9 verbatim in '
                        'logs/state-log-archive-9999-01.md')
        about_fold = ('R9011 FOLD ACCOUNTING: this round folded log items 4..9 '
                      'into logs/state-log-archive-9999-01.md and says so in '
                      'its own headline')
        range_only = ('R9011 NOTES: the window covered log items 12..30 of the '
                      'old file')
        s11['log'] = [summary_line, headline, about_fold, range_only]
        expect = 'R9011 - ENGINEERING: the round did one measurable thing'
        cur = mod.derive(w11, s11, 'T11')['current']
        ok('AC-EXPW11 a summary line above the headline never becomes current',
           cur == expect, cur[:44])
        s11['log'] = [headline, about_fold, range_only]
        cur2 = mod.derive(w11, s11, 'T11')['current']
        ok('AC-EXPW11 removing the summary leaves current unchanged',
           cur2 == expect, cur2[:44])
        ok('AC-EXPW11 a narrative about a fold stays a narrative, a bare range '
           'too, and the summary shape is excluded',
           mod.is_fold_summary(about_fold) is False
           and mod.is_fold_summary(range_only) is False
           and mod.is_fold_summary(summary_line) is True,
           'about=%r range=%r summary=%r'
           % (mod.is_fold_summary(about_fold),
              mod.is_fold_summary(range_only),
              mod.is_fold_summary(summary_line)))

        # ---- AC-EXPW13: R2821 archived the results block, and the writer refuses
        # ---- to notice. An archive that still resolves must not block the write,
        # ---- and must not be re-grown a row at a time.
        w13 = build_pair_world([('zz-face', 0)], tick=9013)
        worlds.append(w13)
        exp13 = os.path.join(w13, 'docs', 'status-export.json')
        doc13 = json.loads(read(exp13))
        logs13 = os.path.join(w13, 'logs')
        if not os.path.isdir(logs13):
            os.makedirs(logs13)
        arc_body = json.dumps({'results': doc13['results']},
                              ensure_ascii=False, indent=2) + '\n'
        arc_rel = 'logs/status-export-legacy-9999-01.json'
        write(os.path.join(w13, arc_rel.replace('/', os.sep)), arc_body)
        digest13 = hashlib.sha256(arc_body.encode('utf-8')).hexdigest()
        with_results = json.loads(json.dumps(doc13))
        doc13.pop('results')
        doc13['results_archive'] = {'path': arc_rel, 'sha256': digest13,
                                    'count': 1,
                                    'bytes': len(arc_body.encode('utf-8'))}
        s13 = json.loads(read(os.path.join(w13, 'src', 'os', 'state.json')))
        write(exp13, json.dumps(doc13, ensure_ascii=False, indent=2) + '\n')
        data13, d13 = mod.payload(w13, s13, 'T13')
        ok('AC-EXPW13 an intact archive does not block the write and is not re-grown',
           'results' not in data13 and bool(data13.get('tick_row_skipped')),
           'skip=%r' % (str(data13.get('tick_row_skipped'))[:44],))
        write(exp13, json.dumps(with_results, ensure_ascii=False, indent=2) + '\n')
        data13b, d13b = mod.payload(w13, s13, 'T13b')
        ok('AC-EXPW13 a live results list still moves the tick slot',
           data13b.get('results')
           and str(data13b['results'][0][0]) == str(s13['tick'])
           and data13b.get('tick_row_skipped') is None,
           'tick_row=%r skipped=%r'
           % (data13b.get('results', [[None]])[0][:1],
              data13b.get('tick_row_skipped')))

        # ---- AC-EXPW14: 'it was archived' cannot be claimed over a lost archive
        def refusal(base, label):
            write(exp13, json.dumps(base, ensure_ascii=False, indent=2) + '\n')
            try:
                mod.payload(w13, s13, label)
            except ValueError as exc:
                return str(exc)
            return ''

        no_pointer = json.loads(json.dumps(doc13))
        no_pointer.pop('results_archive')
        bad_sha = json.loads(json.dumps(doc13))
        bad_sha['results_archive']['sha256'] = '0' * 64
        gone = json.loads(json.dumps(doc13))
        gone['results_archive']['path'] = 'logs/not-there-9999.json'
        said = [refusal(no_pointer, 'T14a'), refusal(bad_sha, 'T14b'),
                refusal(gone, 'T14c')]
        ok('AC-EXPW14 a missing, mismatched or dangling archive is refused by name',
           all('E_EXP_NO_ARCHIVE' in text for text in said),
           'refusals=%r' % [text[:34] for text in said])
        write(exp13, json.dumps(with_results, ensure_ascii=False, indent=2) + '\n')

        # ---- AC-EXPG1..AC-EXPG4: the face may not be written from a round
        # ---- line that lost its date anchor (R2834). Pinned in the board first.
        wg = build_world(9031)
        worlds.append(wg)
        sg = json.loads(read(os.path.join(wg, 'src', 'os', 'state.json')))
        fg = os.path.join(wg, 'docs', 'status-export.json')
        ok('AC-EXPG1 a dated round main line passes the law',
           mod.round_shape_refusal(sg) == '', mod.round_shape_refusal(sg)[:40])
        built_g, _ = mod.payload(wg, sg, 'TG0')
        write(fg, json.dumps(built_g, ensure_ascii=False, indent=2) + '\n')
        ok('AC-EXPG4 an anchored private world grades clean (positive control)',
           mod.check(wg) == [], 'fails=%s' % mod.check(wg)[:2])
        sg_bad = json.loads(json.dumps(sg))
        sg_bad['log'] = [re.sub(r'^\d{4}-\d{2}-\d{2} ', '', sg['log'][0])]
        write(os.path.join(wg, 'src', 'os', 'state.json'),
              json.dumps(sg_bad, ensure_ascii=False))
        before_g = (os.path.getsize(fg), os.stat(fg).st_mtime_ns)
        err_g = ''
        try:
            mod.write(wg, 'TG1')
        except ValueError as exc:
            err_g = str(exc)
        after_g = (os.path.getsize(fg), os.stat(fg).st_mtime_ns)
        ok('AC-EXPG1 an unanchored newest round refuses the write, zero bytes',
           err_g.startswith('E_EXP_ROUND_SHAPE') and before_g == after_g,
           err_g[:44])
        ok('AC-EXPG1 the refusal carries the law code it came from',
           'E_RMS_NO_DATE' in err_g, err_g[:60])
        src_now = read(TOOL)
        ok('AC-EXPG2 the gate is the law module, not a second local regex',
           'check_round_main_shape' in src_now
           and 'E_RMS_' not in src_now
           and not re.search(r'\d{4}-\d{2}-\d{2} R', src_now),
           'law_calls=%d local_codes=%d'
           % (src_now.count('check_round_main_shape'),
              src_now.count('E_RMS_')))
        fails_g = mod.check(wg)
        ok('AC-EXPG3 --check reddens on the unanchored tree, read-only',
           any('E_EXP_ROUND_SHAPE' in f for f in fails_g)
           and os.path.getsize(fg) == before_g[0], 'fails=%s' % fails_g[:1])
        write(os.path.join(wg, 'src', 'os', 'state.json'),
              json.dumps(sg, ensure_ascii=False))
        ok('AC-EXPG4 restoring the anchor clears the refusal again',
           mod.check(wg) == [], 'fails=%s' % mod.check(wg)[:2])
        ok('AC-EXPG4 the live tree still grades clean',
           mod.check(ROOT) == [], 'fails=%s' % mod.check(ROOT)[:2])
        one_offs = [n for n in os.listdir(os.path.join(ROOT, 'src', 'os'))
                    if re.match(r'^state_append_R.*\.py$', n)]
        ok('AC-EXPG5 the one-off state appenders are retired and the single '
           'vehicle remains',
           one_offs == []
           and os.path.isfile(os.path.join(ROOT, 'src', 'os',
                                           'state_append.py')),
           'leftovers=%d' % len(one_offs))

        # ---- AC-EXPA1/AC-EXPA2: the argument guard is measured here, not by
        # ---- hand (R2877 pin; ids renamed at R2878 because AC-EXPW11 already
        # ---- prints a fold-summary law and AC-EXPW12 is the declared hole).
        # ---- The TRACKED face is snapshotted through the shipped helper, so a
        # ---- broken guard reddens the criterion instead of leaving the world
        # ---- changed for the next suite that measures mtime.
        from tree_snapshot import restored as _restored
        face_live = os.path.join(ROOT, 'docs', 'status-export.json')

        def run_tool(args):
            proc = subprocess.Popen([sys.executable, TOOL] + args, cwd=ROOT,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
            out, err = proc.communicate()
            return (proc.returncode, out.decode('utf-8', 'replace'),
                    err.decode('utf-8', 'replace'))

        def face_state():
            with open(face_live, 'rb') as handle:
                body = handle.read()
            return (hashlib.sha256(body).hexdigest(),
                    os.stat(face_live).st_mtime_ns)

        with _restored([face_live]):
            state0 = face_state()
            rc_h, out_h, err_h = run_tool(['--help'])
            rc_h2, out_h2, err_h2 = run_tool(['-h'])
            state1 = face_state()
            ok('AC-EXPA1 --help and -h print usage at rc=0 and write nothing',
               rc_h == 0 and 'usage: export_round.py' in out_h
               and '--check' in out_h and '--root' in out_h
               and rc_h2 == 0 and 'usage: export_round.py' in out_h2
               and state0 == state1
               and 'Traceback' not in (err_h + err_h2),
               'rc=%s,%s face_moved=%s' % (rc_h, rc_h2, state0 != state1))
            rc_typo, out_typo, err_typo = run_tool(['--chek'])
            state2 = face_state()
            rc_root, out_root, err_root = run_tool(['--root'])
            state3 = face_state()
            ok('AC-EXPA2 an undefined flag and a dangling --root fail closed at '
               'rc=2 with the face untouched',
               rc_typo == 2 and out_typo.startswith('E_EXP_ARG')
               and '--chek' in out_typo
               and rc_root == 2 and out_root.startswith('E_EXP_ARG')
               and '--root' in out_root
               and state0 == state2 and state0 == state3
               and 'Traceback' not in (err_typo + err_root),
               'rc=%s,%s face_moved=%s' % (rc_typo, rc_root,
                                           state0 != state2 or state0 != state3))

        # ---- AC-EXPE1..AC-EXPE4 (R2895 pin): the evidence line and its note ----
        # The product slot only ever looked at preview/, so a round whose product
        # is qa/ evidence left the face naming an older preview. These four
        # criteria pin the second derived line and the one-line note that says
        # which of the two is newer - with both arms measured, not assumed.
        wv = build_pair_world([('first-yuan-chain', 500)], tick=9051)
        worlds.append(wv)
        qa_dir = os.path.join(wv, 'qa')
        if not os.path.isdir(qa_dir):
            os.makedirs(qa_dir)
        now_v = time.time()
        ev_age = 60
        for name, age, body in (('older-run.log', 900, 'a\n'),
                                ('zz-evidence-new.log', ev_age, 'b' * 40)):
            p = os.path.join(qa_dir, name)
            write(p, body)
            os.utime(p, (now_v - age, now_v - age))
        # a NEWER non-.log file is a fixture, not a receipt of a measured run
        pj = os.path.join(qa_dir, 'zz-newer-fixture.json')
        write(pj, '{}\n')
        os.utime(pj, (now_v - 5, now_v - 5))
        sv = json.loads(read(os.path.join(wv, 'src', 'os', 'state.json')))
        dv = mod.derive(wv, sv, 'TV')
        ev_line = 'qa/zz-evidence-new.log (40B, %s)' % time.strftime(
            '%Y-%m-%d', time.localtime(now_v - ev_age))
        ok('AC-EXPE1 the evidence line names the newest qa/*.log with its own '
           'bytes and date', dv['evidence'] == ev_line, dv['evidence'][:48])
        ok('AC-EXPE1 a newer non-log fixture and an older log do not move it',
           'zz-newer-fixture' not in dv['evidence']
           and 'older-run' not in dv['evidence'], dv['evidence'][:48])
        ok('AC-EXPE1 evidence never leaks into the product slot',
           'zz-evidence-new' not in dv['latest']
           and 'first-yuan-chain.html' in dv['latest'], dv['latest'][:40])

        built_v, _ = mod.payload(wv, sv, 'TV')
        write(os.path.join(wv, 'docs', 'status-export.json'),
              json.dumps(built_v, ensure_ascii=False, indent=2) + '\n')
        ok('AC-EXPE2 evidence newer than the pair publishes a note naming it',
           'EVIDENCE' in built_v['ceo_face']['latest_artifact_note']
           and 'zz-evidence-new.log'
           in built_v['ceo_face']['latest_artifact_note'],
           str(built_v['ceo_face']['latest_artifact_note'])[:52])
        for ext in ('.html', '.json'):
            p = os.path.join(wv, 'preview', 'first-yuan-chain' + ext)
            os.utime(p, (now_v, now_v))
        dv2 = mod.derive(wv, sv, 'TV2')
        ok('AC-EXPE2 the note empties when the product pair is newer',
           dv2['note'] == '' and dv2['evidence'] == ev_line,
           repr(dv2['note'])[:40])
        for ext in ('.html', '.json'):
            p = os.path.join(wv, 'preview', 'first-yuan-chain' + ext)
            t = now_v - 500
            os.utime(p, (t, t))

        wq = build_pair_world([('first-yuan-chain', 0)], tick=9052)
        worlds.append(wq)
        sq = json.loads(read(os.path.join(wq, 'src', 'os', 'state.json')))
        dq = mod.derive(wq, sq, 'TQ')
        face_q = os.path.join(wq, 'docs', 'status-export.json')
        built_q, _ = mod.payload(wq, sq, 'TQ')
        write(face_q, json.dumps(built_q, ensure_ascii=False, indent=2) + '\n')
        ok('AC-EXPE3 an absent qa/ is a stated fact and publishes no note',
           dq['evidence'] == '(no qa evidence on disk)' and dq['note'] == '',
           dq['evidence'][:40])
        ok('AC-EXPE3 a correct evidence-free face reads clean',
           mod.check(wq) == [], 'fails=%s' % mod.check(wq)[:2])
        tampered_q = json.loads(read(face_q))
        tampered_q['ceo_face']['latest_evidence'] = \
            'qa/invented-9999.log (1B, 1999-01-01)'
        write(face_q, json.dumps(tampered_q, ensure_ascii=False, indent=2) + '\n')
        fails_q = mod.check(wq)
        ok('AC-EXPE3 a fabricated evidence line reddens AC-EXPE1',
           any('AC-EXPE1' in f for f in fails_q), 'fails=%s' % fails_q[:2])
        tampered_n = json.loads(json.dumps(built_q))
        tampered_n['ceo_face']['latest_artifact_note'] = 'an invented note'
        write(face_q, json.dumps(tampered_n, ensure_ascii=False, indent=2) + '\n')
        fails_n = mod.check(wq)
        ok('AC-EXPE3 a note over an evidence-free tree reddens AC-EXPE2',
           any('AC-EXPE2' in f for f in fails_n), 'fails=%s' % fails_n[:2])
        write(face_q, json.dumps(built_q, ensure_ascii=False, indent=2) + '\n')
        ok('AC-EXPE3 restoring the derived face reads clean again',
           mod.check(wq) == [], 'fails=%s' % mod.check(wq)[:2])

        ok('AC-EXPE4 the product slot still derives from the pair law alone',
           dv['latest'] == mod._fmt_pair(mod.newest_artifact(wv)[0]),
           dv['latest'][:40])
        live_face = json.loads(read(os.path.join(ROOT, 'docs',
                                                 'status-export.json')))
        ok('AC-EXPE4 the live face carries the evidence line after its refresh',
           bool((live_face.get('ceo_face') or {}).get('latest_evidence'))
           and live_face.get('latest_evidence')
           == live_face['ceo_face']['latest_evidence'],
           str((live_face.get('ceo_face') or {}).get('latest_evidence'))[:44])

        # ---- AC-EXPD1..AC-EXPD3 (R2896 pin): the pair line carries its own date ----
        # R2895 left the CEO face naming evidence but still publishing the
        # product pair with NO timestamp, so this window's artifact and a
        # two-day-old one read identically. The date is rendered from the pair's
        # own mtime, and both derivations of the field call ONE formatter.
        wd = build_pair_world([('dated-face', 0)], tick=9061)
        worlds.append(wd)
        sd = json.loads(read(os.path.join(wd, 'src', 'os', 'state.json')))
        dd = mod.derive(wd, sd, 'TD')
        html_d = os.path.join(wd, 'preview', 'dated-face.html')
        json_d = os.path.join(wd, 'preview', 'dated-face.json')
        stamp_want = time.strftime('%Y-%m-%d',
                                   time.localtime(os.path.getmtime(html_d)))
        ok('AC-EXPD1 the pair line ends with the pair own mtime date',
           dd['latest'].endswith(' [%s mtime]' % stamp_want)
           and 'preview/dated-face.html' in dd['latest'], dd['latest'][-28:])
        ok('AC-EXPD1 the published shape is the graded shape',
           bool(mod.PAIR_LINE_RE.match(dd['latest']))
           and mod.PAIR_LINE_RE.match(dd['latest']).group(1) == stamp_want,
           dd['latest'][-26:])
        sys.path.insert(0, os.path.join(ROOT, 'tools'))
        import status_export_fresh as sx
        sx_line = sx.newest_artifact(os.path.join(wd, 'preview'))['line']
        ok('AC-EXPD1 both derivations publish the identical line',
           sx_line == dd['latest'] == mod.fmt_pair(mod.newest_artifact(wd)[0]),
           'sx=%s' % sx_line[-28:])

        face_d = os.path.join(wd, 'docs', 'status-export.json')
        built_d, _ = mod.payload(wd, sd, 'TD')
        write(face_d, json.dumps(built_d, ensure_ascii=False, indent=2) + '\n')
        ok('AC-EXPD2 the derived dated line grades clean',
           mod.check(wd) == [], 'fails=%s' % mod.check(wd)[:2])
        old_shape = json.loads(read(face_d))
        old_shape['ceo_face']['latest_artifact'] = \
            'preview/dated-face.html (%dB) + preview/dated-face.json (%dB)' % (
                os.path.getsize(html_d), os.path.getsize(json_d))
        write(face_d, json.dumps(old_shape, ensure_ascii=False, indent=2) + '\n')
        fails_old = mod.check(wd)
        ok('AC-EXPD2 the OLD date-less shape reddens the check',
           any('AC-EXPW1' in f for f in fails_old), 'fails=%s' % fails_old[:2])
        wrong = json.loads(read(face_d))
        wrong['ceo_face']['latest_artifact'] = re.sub(
            r'\[\d{4}-\d{2}-\d{2} (?:commit|mtime)\]$', '[1999-01-01 mtime]',
            dd['latest'])
        write(face_d, json.dumps(wrong, ensure_ascii=False, indent=2) + '\n')
        fails_wrong = mod.check(wd)
        ok('AC-EXPD2 a WRONG date reddens it too',
           any('AC-EXPW1' in f for f in fails_wrong), 'fails=%s' % fails_wrong[:2])
        write(face_d, json.dumps(built_d, ensure_ascii=False, indent=2) + '\n')
        ok('AC-EXPD2 restoring the derived line reads clean again',
           mod.check(wd) == [], 'fails=%s' % mod.check(wd)[:2])

        ok('AC-EXPD3 the board exclusion still holds on the dated line',
           bool(mod.PAIR_LINE_RE.match(dp['latest']))
           and 'ceo-blockers' not in dp['latest'], dp['latest'][:44])
        ok('AC-EXPD3 the all-board fact and the evidence line are unchanged',
           db['latest'].startswith('(no product pair on disk')
           and dv['evidence'].startswith('qa/zz-evidence-new.log'),
           db['latest'][:32])

        # ---- AC-EXPD4..AC-EXPD6 (R2897 pin): the ordering stamp is CONTENT time ----
        # R2896 made the line carry a date but the pair was still CHOSEN by the
        # filesystem clock, so an unchanged page that was touched outranked a
        # genuinely newer one and re-dated itself. Both laws are measured on the
        # SAME world, so the refutation is on the record rather than asserted.
        wg, t1, t2, t3 = build_git_pair_world()
        if wg is not None:
            worlds.append(wg)
        ok('AC-EXPD4 the fixture built a real git work tree',
           bool(wg) and os.path.isdir(os.path.join(wg, '.git')), str(wg))
        if wg is None:
            for name in (
                    'AC-EXPD4 the red control: the mtime law picks the touched page',
                    'AC-EXPD4 the content law picks the genuinely newer page',
                    'AC-EXPD4 the ordering stamp is the committed change time',
                    'AC-EXPD4 the touched page keeps its own commit date'):
                ok(name, False, 'git unavailable in this environment')
        else:
            prev_g = os.path.join(wg, 'preview')
            old_m = max(os.path.getmtime(os.path.join(prev_g,
                                                      'touched-old.html')),
                        os.path.getmtime(os.path.join(prev_g,
                                                      'touched-old.json')))
            new_m = max(os.path.getmtime(os.path.join(prev_g,
                                                      'genuinely-new.html')),
                        os.path.getmtime(os.path.join(prev_g,
                                                      'genuinely-new.json')))
            ok('AC-EXPD4 the red control: the mtime law picks the touched page',
               old_m > new_m, 'old=%.0f new=%.0f' % (old_m, new_m))
            pairs_g = mod._pairs(wg)
            ok('AC-EXPD4 the content law picks the genuinely newer page',
               bool(pairs_g)
               and pairs_g[0][1] == 'preview/genuinely-new.html',
               pairs_g[0][1] if pairs_g else 'none')
            ok('AC-EXPD4 the ordering stamp is the committed change time',
               bool(pairs_g) and int(pairs_g[0][0]) == t2,
               '%d vs t2=%d' % (int(pairs_g[0][0]) if pairs_g else -1, t2))
            ok('AC-EXPD4 the touched page keeps its own commit date',
               len(pairs_g) > 1 and mod.pair_date(pairs_g[1][0])
               == mod.pair_date(float(t1)),
               mod.pair_date(pairs_g[1][0]) if len(pairs_g) > 1 else 'none')

            # AC-EXPD5: a file whose bytes changed AFTER its commit is newer
            # than that commit and must say so; an untracked page participates
            # by its mtime; a git failure answers None rather than raising.
            path_edit = os.path.join(prev_g, 'genuinely-new.html')
            write(path_edit, '<!DOCTYPE html>\n<p>edited after the commit</p>\n')
            t4 = t3 + 86400
            os.utime(path_edit, (t4, t4))
            pairs_edit = mod._pairs(wg)
            ok('AC-EXPD5 uncommitted bytes use their own mtime',
               bool(pairs_edit) and int(pairs_edit[0][0]) == t4
               and pairs_edit[0][1] == 'preview/genuinely-new.html',
               'stamp=%d t4=%d' % (int(pairs_edit[0][0]) if pairs_edit else -1,
                                   t4))
            t5 = t4 + 86400
            for ext, body in (('.html', '<!DOCTYPE html>\n'), ('.json', '{}\n')):
                p_new = os.path.join(prev_g, 'untracked-new' + ext)
                write(p_new, body)
                os.utime(p_new, (t5, t5))
            pairs_new = mod._pairs(wg)
            ok('AC-EXPD5 an untracked page participates by its mtime',
               bool(pairs_new) and int(pairs_new[0][0]) == t5
               and pairs_new[0][1] == 'preview/untracked-new.html',
               'stamp=%d t5=%d' % (int(pairs_new[0][0]) if pairs_new else -1,
                                   t5))
        ok('AC-EXPD5 a non-git world still orders by pure mtime',
           not os.path.isdir(os.path.join(wd, '.git'))
           and int(mod._pairs(wd)[0][0]) == int(os.path.getmtime(html_d)),
           'stamp=%s' % (int(mod._pairs(wd)[0][0]) if mod._pairs(wd) else -1))
        ok('AC-EXPD5 an unreadable repository answers None instead of raising',
           mod._git(os.path.join(wd, 'not-a-repo'), ['status']) is None,
           'no exception')

        # AC-EXPD6: the new ordering clock must leave the published shape, the
        # two-face identity and the --check date control exactly as they were.
        wc2, s1, s2, s3 = build_git_pair_world(tick=9201)
        if wc2 is not None:
            worlds.append(wc2)
        ok('AC-EXPD6 the second git world built', wc2 is not None, str(wc2))
        if wc2 is None:
            for name in ('AC-EXPD6 the published line still matches PAIR_LINE_RE',
                         'AC-EXPD6 a face graded on a git world reads clean',
                         'AC-EXPD6 the date red control still bites'):
                ok(name, False, 'git unavailable in this environment')
        else:
            sc2 = json.loads(read(os.path.join(wc2, 'src', 'os',
                                               'state.json')))
            dc2 = mod.derive(wc2, sc2, 'TC2')
            ok('AC-EXPD6 the published line still matches PAIR_LINE_RE',
               bool(mod.PAIR_LINE_RE.match(dc2['latest']))
               and 'genuinely-new' in dc2['latest'], dc2['latest'][:44])
            face_c2 = os.path.join(wc2, 'docs', 'status-export.json')
            built_c2, _ = mod.payload(wc2, sc2, 'TC2')
            write(face_c2, json.dumps(built_c2, ensure_ascii=False,
                                      indent=2) + '\n')
            ok('AC-EXPD6 a face graded on a git world reads clean',
               mod.check(wc2) == [], 'fails=%s' % mod.check(wc2)[:2])
            wrong_c2 = json.loads(read(face_c2))
            wrong_c2['ceo_face']['latest_artifact'] = re.sub(
                r'\[\d{4}-\d{2}-\d{2} (?:commit|mtime)\]$',
                '[1999-01-01 mtime]', dc2['latest'])
            write(face_c2, json.dumps(wrong_c2, ensure_ascii=False,
                                      indent=2) + '\n')
            ok('AC-EXPD6 the date red control still bites',
               any('AC-EXPW1' in f for f in mod.check(wc2)),
               'fails=%s' % mod.check(wc2)[:2])
            write(face_c2, json.dumps(built_c2, ensure_ascii=False,
                                      indent=2) + '\n')

        # ---- AC-EXPD7..AC-EXPD9 (R2898 pin): the line names its own clock ----
        # R2897 chose the right stamp but published no way to TELL a committed
        # date from a touched-file date: the same shape meant two different
        # clocks. The marker is measured on ONE git world in both states, and on
        # a non-git world, so 'commit' cannot be faked by a tree with no git.
        wp, p1, p2, p3 = build_git_pair_world(tick=9202)
        if wp is not None:
            worlds.append(wp)
        ok('AC-EXPD7 the provenance fixture built', wp is not None, str(wp))
        markers = []
        if wp is None:
            for name in ('AC-EXPD7 a committed pair publishes the commit clock',
                         'AC-EXPD7 the same pair edited after its commit '
                         'publishes the mtime clock',
                         'AC-EXPD8 the derived line grades clean',
                         'AC-EXPD8 the marker-less pre-R2898 line reddens the '
                         'check',
                         'AC-EXPD8 a face claiming the WRONG clock reddens it too',
                         'AC-EXPD9 both derivations publish the identical line',
                         'AC-EXPD9 group 1 of the line is still the DATE'):
                ok(name, False, 'git unavailable in this environment')
        else:
            sp = json.loads(read(os.path.join(wp, 'src', 'os', 'state.json')))
            d_clean = mod.derive(wp, sp, 'TP1')
            m_clean = mod.PAIR_LINE_RE.match(d_clean['latest'])
            markers.append(m_clean.group(2) if m_clean else 'none')
            ok('AC-EXPD7 a committed pair publishes the commit clock',
               bool(m_clean) and m_clean.group(2) == 'commit'
               and 'genuinely-new' in d_clean['latest'],
               d_clean['latest'][-40:])

            face_p = os.path.join(wp, 'docs', 'status-export.json')
            built_p, _ = mod.payload(wp, sp, 'TP1')
            write(face_p, json.dumps(built_p, ensure_ascii=False, indent=2)
                  + '\n')
            ok('AC-EXPD8 the derived line grades clean',
               mod.check(wp) == [], 'fails=%s' % mod.check(wp)[:2])
            old_p = json.loads(json.dumps(built_p))
            old_p['ceo_face']['latest_artifact'] = re.sub(
                r' (?:commit|mtime)\]$', ']', d_clean['latest'])
            write(face_p, json.dumps(old_p, ensure_ascii=False, indent=2)
                  + '\n')
            ok('AC-EXPD8 the marker-less pre-R2898 line reddens the check',
               any('AC-EXPW1' in f for f in mod.check(wp)),
               'fails=%s' % mod.check(wp)[:2])
            wrong_clock = json.loads(json.dumps(built_p))
            wrong_clock['ceo_face']['latest_artifact'] = re.sub(
                r'commit\]$', 'mtime]', d_clean['latest'])
            write(face_p, json.dumps(wrong_clock, ensure_ascii=False,
                                     indent=2) + '\n')
            ok('AC-EXPD8 a face claiming the WRONG clock reddens it too',
               any('AC-EXPW1' in f for f in mod.check(wp)),
               'fails=%s' % mod.check(wp)[:2])
            write(face_p, json.dumps(built_p, ensure_ascii=False, indent=2)
                  + '\n')

            sx_line_p = sx.newest_artifact(os.path.join(wp, 'preview'))['line']
            ok('AC-EXPD9 both derivations publish the identical line',
               sx_line_p == d_clean['latest']
               == mod.fmt_pair(mod.newest_artifact(wp)[0]),
               'sx=%s' % sx_line_p[-30:])

            path_p = os.path.join(wp, 'preview', 'genuinely-new.html')
            write(path_p, '<!DOCTYPE html>\n<p>edited after the commit</p>\n')
            p4 = p3 + 86400
            os.utime(path_p, (p4, p4))
            d_dirty = mod.derive(wp, sp, 'TP2')
            m_dirty = mod.PAIR_LINE_RE.match(d_dirty['latest'])
            markers.append(m_dirty.group(2) if m_dirty else 'none')
            ok('AC-EXPD7 the same pair edited after its commit publishes the '
               'mtime clock',
               bool(m_dirty) and m_dirty.group(2) == 'mtime'
               and m_dirty.group(1) == mod.pair_date(float(p4)),
               d_dirty['latest'][-40:])
            ok('AC-EXPD9 group 1 of the line is still the DATE',
               bool(m_clean) and m_clean.group(1) == mod.pair_date(float(p2))
               and bool(m_dirty) and m_dirty.group(1) == mod.pair_date(float(p4)),
               'clean=%s dirty=%s' % (
                   m_clean.group(1) if m_clean else 'none',
                   m_dirty.group(1) if m_dirty else 'none'))
        m_nogit = mod.PAIR_LINE_RE.match(mod.derive(wd, sd, 'TP3')['latest'])
        markers.append(m_nogit.group(2) if m_nogit else 'none')
        ok('AC-EXPD7 a non-git world publishes the mtime clock',
           markers[-1] == 'mtime', 'markers=%s' % '/'.join(markers))
        ok('AC-EXPD9 the board exclusion and the all-board fact are unchanged',
           bool(mod.PAIR_LINE_RE.match(dp['latest']))
           and 'ceo-blockers' not in dp['latest']
           and db['latest'].startswith('(no product pair on disk'),
           dp['latest'][:40])

        # ---- AC-EXPD10..AC-EXPD12 (R2899 pin): halves that disagree say so ----
        # R2898 named the clock of the half that WON the max and stayed silent
        # about the other half, so a pair whose html is committed and whose json
        # was written after that commit published one clock for two clocks.
        wa = tempfile.mkdtemp(prefix='expw-agree-')
        worlds.append(wa)
        os.makedirs(os.path.join(wa, 'preview'))
        t_same = 1767225600
        for ext, body in (('.html', '<!DOCTYPE html>\n'), ('.json', '{}\n')):
            path = os.path.join(wa, 'preview', 'agreeing' + ext)
            write(path, body)
            os.utime(path, (t_same, t_same))
        row_a = mod._pairs(wa)[0]
        line_a = mod.fmt_pair(row_a)
        ok('AC-EXPD10 an agreeing pair publishes NO disagreement note',
           bool(mod.PAIR_LINE_RE.match(line_a)) and 'halves differ' not in line_a,
           line_a[-40:])
        row_p = mod._pairs(wp)[0] if wp is not None else None
        line_p = mod.fmt_pair(row_p) if row_p else ''
        m_noted = mod.PAIR_LINE_RE.match(line_p)
        ok('AC-EXPD11 a split pair names BOTH halves beside the winner bracket',
           bool(m_noted) and 'halves differ: html [' in line_p
           and '+ json [' in line_p
           and m_noted.group(1) == mod.pair_date(float(p4)),
           line_p[-90:])
        if wp is not None:
            face_n = os.path.join(wp, 'docs', 'status-export.json')
            built_n, _ = mod.payload(wp, sp, 'TN')
            write(face_n, json.dumps(built_n, ensure_ascii=False, indent=2)
                  + '\n')
            ok('AC-EXPD11 the noted line grades clean', mod.check(wp) == [],
               'fails=%s' % mod.check(wp)[:2])
            stripped = json.loads(json.dumps(built_n))
            stripped['ceo_face']['latest_artifact'] = re.sub(
                r' \(halves differ:.*\)$', '', line_p)
            write(face_n, json.dumps(stripped, ensure_ascii=False,
                                     indent=2) + '\n')
            ok('AC-EXPD11 a face that drops the note reddens --check',
               any('AC-EXPW1' in f for f in mod.check(wp)),
               'fails=%s' % mod.check(wp)[:2])
            write(face_n, json.dumps(built_n, ensure_ascii=False, indent=2)
                  + '\n')
            sx_noted = sx.newest_artifact(os.path.join(wp, 'preview'))['line']
            ok('AC-EXPD12 both derivations publish the identical noted line',
               sx_noted == line_p, 'sx=%s' % sx_noted[-40:])
            ok('AC-EXPD12 the noted line still yields date and clock in groups',
               bool(m_noted) and m_noted.group(1) == mod.pair_date(float(p4))
               and m_noted.group(2) == 'mtime',
               'groups=%s' % repr(m_noted.groups() if m_noted else None))
        else:
            for name in ('AC-EXPD11 a split pair names BOTH halves beside the '
                         'winner bracket',
                         'AC-EXPD11 the noted line grades clean',
                         'AC-EXPD11 a face that drops the note reddens --check',
                         'AC-EXPD12 both derivations publish the identical '
                         'noted line',
                         'AC-EXPD12 the noted line still yields date and clock '
                         'in groups'):
                ok(name, False, 'git unavailable in this environment')
        face_d = os.path.join(wd, 'docs', 'status-export.json')
        built_d, _ = mod.payload(wd, sd, 'TD')
        write(face_d, json.dumps(built_d, ensure_ascii=False, indent=2) + '\n')
        dd_line = mod.derive(wd, sd, 'TD')['latest']
        ok('AC-EXPD10 the agreeing control line publishes no note either',
           'halves differ' not in dd_line, dd_line[-40:])
        faked = json.loads(json.dumps(built_d))
        faked['ceo_face']['latest_artifact'] = dd_line + (
            ' (halves differ: html [1999-01-01 commit] + json [1999-01-01 commit])')
        write(face_d, json.dumps(faked, ensure_ascii=False, indent=2) + '\n')
        ok('AC-EXPD12 appending the note to an AGREEING pair reddens',
           any('AC-EXPW1' in f for f in mod.check(wd)),
           'fails=%s' % mod.check(wd)[:2])
        write(face_d, json.dumps(built_d, ensure_ascii=False, indent=2) + '\n')

        # ---- AC-EXPD13..AC-EXPD15 (R2900 pin): the note names WHICH half won ----
        # R2899 made a split pair speak, but two halves that share a DATE and
        # differ only in CLOCK render as the same date twice, so the bracket
        # could describe either half and only a character diff told them apart.
        wn = build_pair_world([('split-face', 0)], tick=9091)
        worlds.append(wn)
        sn = json.loads(read(os.path.join(wn, 'src', 'os', 'state.json')))
        h_n = os.path.join(wn, 'preview', 'split-face.html')
        j_n = os.path.join(wn, 'preview', 'split-face.json')
        t_n = 1767225600
        os.utime(h_n, (t_n, t_n))
        os.utime(j_n, (t_n + 86400, t_n + 86400))
        m_n = mod.PAIR_LINE_RE.match(mod.fmt_pair(mod._pairs(wn)[0]))
        line_n = mod.fmt_pair(mod._pairs(wn)[0])
        ok('AC-EXPD13 a pair whose JSON half is later names json',
           bool(m_n) and '; later=json' in line_n, line_n[-50:])
        os.utime(h_n, (t_n + 172800, t_n + 172800))
        line_n2 = mod.fmt_pair(mod._pairs(wn)[0])
        m_n2 = mod.PAIR_LINE_RE.match(line_n2)
        ok('AC-EXPD13 the MIRRORED pair names html',
           '; later=html' in line_n2, line_n2[-50:])
        face_nw = os.path.join(wn, 'docs', 'status-export.json')
        built_nw, _ = mod.payload(wn, sn, 'TN2')
        write(face_nw, json.dumps(built_nw, ensure_ascii=False, indent=2) + '\n')
        ok('AC-EXPD14 the line carrying a later tag grades clean',
           mod.check(wn) == [], 'fails=%s' % mod.check(wn)[:2])
        stripped_nw = json.loads(json.dumps(built_nw))
        stripped_nw['ceo_face']['latest_artifact'] = re.sub(
            r'; later=(?:html|json)',
            '', built_nw['ceo_face']['latest_artifact'])
        write(face_nw, json.dumps(stripped_nw, ensure_ascii=False, indent=2)
              + '\n')
        ok('AC-EXPD14 stripping the later tag reddens --check',
           any('AC-EXPW1' in f for f in mod.check(wn)),
           'fails=%s' % mod.check(wn)[:2])
        wrong_nw = json.loads(json.dumps(built_nw))
        wrong_nw['ceo_face']['latest_artifact'] = built_nw['ceo_face'][
            'latest_artifact'].replace('; later=html', '; later=json')
        write(face_nw, json.dumps(wrong_nw, ensure_ascii=False, indent=2) + '\n')
        ok('AC-EXPD14 claiming the WRONG half reddens too',
           any('AC-EXPW1' in f for f in mod.check(wn)),
           'fails=%s' % mod.check(wn)[:2])
        write(face_nw, json.dumps(built_nw, ensure_ascii=False, indent=2) + '\n')
        ok('AC-EXPD15 an agreeing pair publishes neither note nor later tag',
           'halves differ' not in line_a and 'later=' not in line_a,
           line_a[-40:])
        ok('AC-EXPD15 groups on a noted line are still date and clock',
           bool(m_n2) and m_n2.group(1) == mod.pair_date(float(t_n + 172800))
           and m_n2.group(2) == 'mtime',
           'groups=%s' % repr(m_n2.groups() if m_n2 else None))

        # ---- AC-EXPD16..AC-EXPD18 (R2901 pin): the tag says LATER, not CHANGED ----
        # R2900 measured which half carries the later stamp and published it as
        # `newer=`, so a reader infers that half CHANGED. The next block proves
        # that inference is false on the line's own numbers, and the word moves.
        ok('AC-EXPD16 the retired newer= shape is refused by PAIR_LINE_RE',
           bool(line_n2) and not mod.PAIR_LINE_RE.match(
               line_n2.replace('; later=', '; newer=')), line_n2[-40:])
        retired_nw = json.loads(json.dumps(built_nw))
        retired_nw['ceo_face']['latest_artifact'] = built_nw['ceo_face'][
            'latest_artifact'].replace('; later=', '; newer=')
        write(face_nw, json.dumps(retired_nw, ensure_ascii=False,
                                  indent=2) + '\n')
        ok('AC-EXPD16 a face still carrying newer= reddens --check',
           any('AC-EXPW1' in f for f in mod.check(wn)),
           'fails=%s' % mod.check(wn)[:2])
        write(face_nw, json.dumps(built_nw, ensure_ascii=False, indent=2) + '\n')
        # AC-EXPD17: the overclaim measured, not argued. The json half is
        # re-saved with IDENTICAL bytes and a later clock, so the tag flips to
        # later=json while the published json byte count does not move - which is
        # exactly why the tag may not say the half changed.
        json_bytes = read(j_n)
        disk_before = len(json_bytes.encode('utf-8'))
        stamp_size = re.compile(r'preview/split-face\.json \((\d+)B\)')
        size_before = stamp_size.search(line_n2).group(1)
        write(j_n, json_bytes)
        disk_after = os.path.getsize(j_n)
        os.utime(j_n, (t_n + 259200, t_n + 259200))
        line_n3 = mod.fmt_pair(mod._pairs(wn)[0])
        size_after = stamp_size.search(line_n3).group(1)
        ok('AC-EXPD17 identical bytes keep the published size unchanged',
           disk_before == disk_after and size_before == size_after
           and size_after == str(disk_after),
           'before=%s after=%s disk=%d/%d'
           % (size_before, size_after, disk_before, disk_after))
        ok('AC-EXPD17 the tag still flips, so it measures the STAMP only',
           '; later=json' in line_n3
           and mod.PAIR_LINE_RE.match(line_n3) is not None, line_n3[-60:])
        # AC-EXPD18: the retired word cannot live in the module's note format,
        # and the ONE formatter still serves both derivations on a NOTED line.
        ok('AC-EXPD18 the note format carries later= and not newer=',
           '; later=%s' in src and '; newer=%s' not in src,
           'later=%s newer=%s' % ('; later=%s' in src, '; newer=%s' in src))
        sx_n3 = sx.newest_artifact(os.path.join(wn, 'preview'))['line']
        ok('AC-EXPD18 both derivations agree on the noted line',
           sx_n3 == line_n3, 'sx=%s' % sx_n3[-40:])

        # ---- AC-EXPW6: hygiene, one battery row, twenty criteria ----
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
        ok('AC-EXPW6 exactly one battery row for this suite',
           len(rows) == 1, 'rows=%s' % rows)
    finally:
        for w in worlds:
            shutil.rmtree(w, ignore_errors=True)

    # AC-EXPE4-registry-units (R2895): a pin that adds an id must move the
    # registry in the same window, so the declared count can never drift from
    # what this suite actually prints - the R2860 both-unit lesson, mechanised
    # in the direction that used to be checked by eye only.
    def crit_set(names):
        found = set()
        for name in names:
            token = name.split(' ', 1)[0]
            for cut in range(len(token), 0, -1):
                if token[cut - 1].isdigit():
                    found.add(token[:cut])
                    break
        return found

    reg_src = read(os.path.join(ROOT, 'src', 'sandbox', 'reconcile_all.py'))
    declared = []
    for pos in [m.start() for m in re.finditer(r'"os-export-round"', reg_src)]:
        found = re.search(r'test_export_round\.py"\)\s*,\s*(\d+)',
                          reg_src[pos:pos + 160])
        if found:
            declared.append(int(found.group(1)))
    will_print = crit_set(CHECKS + ['AC-EXPE4-registry-units'])
    # R2901: the absolute count used to be typed a THIRD time here (36, then 39)
    # and had to be moved by hand whenever a criterion landed. The registry row is
    # the one declaration, so this compares the two units and nothing else. The
    # loss is named: an edit that deletes a criterion AND decrements the registry
    # is silent, and a second typed number would not have caught it either - it
    # would have been a copy that the same edit could move.
    ok('AC-EXPE4-registry-units',
       declared == [len(will_print)],
       'declared=%s printed=%d' % (declared, len(will_print)))

    total = len(CHECKS)
    # Declared units (R2860): the AC inventory below is derived from CHECKS,
    # never echoed from the registry - a declaration copied out of the
    # registry could never disagree with it.
    acs = crit_set(CHECKS)
    print('suite: %d assertions over %d criteria' % (total, len(acs)))
    if FAILS:
        print('SUITE FAIL %d/%d failed=%s' % (total - len(FAILS), total, FAILS))
        return 1
    print('SUITE PASS %d/%d' % (total, total))
    return 0


if __name__ == '__main__':
    sys.exit(main())
