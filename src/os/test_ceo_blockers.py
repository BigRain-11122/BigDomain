"""Battery suite for tools/ceo_blockers.py - criteria AC-CBXB0..AC-CBXB11.

R2860: AC-CBXB0 (isolation - the real preview pair and the temp world are left
untouched) is a criterion of its own, numbered as B0 rather than as a suffix of
another id, so this suite's inventory is twelve and the registry row moves
11 -> 12. The number is compared by the runner from the declaration printed at
closeout, not echoed from the row inside this file.

WHY THIS SUITE EXISTS (measured at R2811, not hypothesised):
tools/ceo_blockers.py renders preview/ceo-blockers.html + .json, the one page
that tells the CEO which pieces only he can unblock, and it carries nine
criteria AC-CBX1..AC-CBX9 in AC_CBX. Importing the shipped registry read 693
suites / 5181 criteria and NOT ONE of them held an AC-CBX* token, so the face
was guarded only by its own --check. Nothing forced that check to run, and the
cost was measurable at open: the landed page still carried "Tick 2770" while
src/os/state.json read tick 2810, so the CEO's own unblock page had been stale
for forty rounds and no gate reddened. Re-rendering turned --check from
VERDICT FAIL 8/9 (AC-CBX9 banner=True disclaimer=True tick=2810) to PASS 9/9.

WHAT IS PROVED HERE: every one of the nine shipped criteria is re-proved in a
PRIVATE world - fixture sources, fixture faces, fixture state - and every one
is proved CARRYING WEIGHT, i.e. a tamper that the criterion is supposed to
catch actually reddens it. A criterion that passes on a tampered world would be
decoration, and this suite would report that instead of hiding it.

The defect AC-CBXB10 holds is the one measured at open: a rendered page whose
tick is one behind the live state reads FAIL AC-CBX9, and re-rendering it reads
PASS. AC-CBXB11 asserts the registry row exists, which is the only hook that
makes this suite run at all; the row's NUMBER is the runner's to compare from
this suite's own declaration (R2860) instead of being echoed here.

Isolation: the tool's REPO / HTML_PATH / JSON_PATH / STATE_PATH globals are
rebound to a fresh temp directory, its BLOCKERS list is replaced by three
fixture rows, and both are restored in a finally block. The real
preview/ceo-blockers.* pair is snapshotted by size and mtime_ns before and
after and must be identical.

Source discipline: pure ASCII, stdlib only, no network, no shell, no clock in
assertions.
"""
import importlib.util
import io
import json
import os
import re
import shutil
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOL = os.path.join(ROOT, 'tools', 'ceo_blockers.py')
REGISTRY = os.path.join(ROOT, 'src', 'sandbox', 'reconcile_all.py')
REAL_HTML = os.path.join(ROOT, 'preview', 'ceo-blockers.html')
REAL_JSON = os.path.join(ROOT, 'preview', 'ceo-blockers.json')

CHECKS = []
FAILS = []

# Fixture keywords. Escaped so this source stays ASCII while the tool's
# declared rules (which match Chinese) still fire exactly as shipped.
ZERO_ARRIVED = u'\u96f6\u5230\u4f4d'          # "zero delivered"
ROUTE_APPROVAL = u'\u5448\u6279'              # "route for approval"
PHYSICAL = u'\u7269\u7406\u4ef6'              # "physical piece"

FIXTURE_BLUEPRINT = (
    'row one: PHYSROW pieces: server + domain, ' + ZERO_ARRIVED + ' after 11 days\n'
    'row two: DECROW pricing batch ' + ROUTE_APPROVAL + '\n'
    'row three: UNKROW a plain statement with no declared keyword\n'
)


def ok(name, cond, detail):
    CHECKS.append(name)
    if not cond:
        FAILS.append(name)
    print('%s %s %s' % ('PASS' if cond else 'FAIL', name, detail))


def read(path):
    with io.open(path, encoding='utf-8-sig') as fh:
        return fh.read()


def write(path, text):
    parent = os.path.dirname(path)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent)
    with io.open(path, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(text)


def load_tool():
    spec = importlib.util.spec_from_file_location('ceo_blockers_under_test', TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def real_snapshot():
    out = []
    for path in (REAL_HTML, REAL_JSON):
        if os.path.isfile(path):
            st = os.stat(path)
            out.append((os.path.basename(path), st.st_size, st.st_mtime_ns))
        else:
            out.append((os.path.basename(path), None, None))
    return out


def fixture_rows():
    return [
        {
            'id': 'X1-phys',
            'title': 'fixture physical row',
            'path': 'BLUEPRINT.md',
            'anchor': r'PHYSROW',
            'action': 'fixture action',
            'face': 'preview/face-a.html',
        },
        {
            'id': 'X2-dec',
            'title': 'fixture decision row',
            'path': 'BLUEPRINT.md',
            'anchor': r'DECROW',
            'action': 'fixture action',
            'face': 'preview/face-a.html',
        },
        {
            'id': 'X3-unk',
            'title': 'fixture unmatched row',
            'path': 'BLUEPRINT.md',
            'anchor': r'UNKROW',
            'action': 'fixture action',
            'face': 'preview/face-a.html',
        },
    ]


def verdicts(mod):
    return dict((name, good) for name, good, _detail in mod.check())


def main():
    started = time.time()
    repo_before = real_snapshot()
    mod = load_tool()
    original = (mod.REPO, mod.HTML_PATH, mod.JSON_PATH, mod.STATE_PATH,
                list(mod.BLOCKERS), mod.QUOTE_CHARS)
    world = tempfile.mkdtemp(prefix='ceo-blockers-suite-')
    try:
        write(os.path.join(world, 'BLUEPRINT.md'), FIXTURE_BLUEPRINT)
        write(os.path.join(world, 'preview', 'face-a.html'), '<p>fixture face</p>\n')
        write(os.path.join(world, 'src', 'os', 'state.json'),
              json.dumps({'tick': 999}, indent=1) + '\n')

        mod.REPO = world
        mod.HTML_PATH = os.path.join(world, 'preview', 'ceo-blockers.html')
        mod.JSON_PATH = os.path.join(world, 'preview', 'ceo-blockers.json')
        mod.STATE_PATH = os.path.join(world, 'src', 'os', 'state.json')
        mod.BLOCKERS = fixture_rows()

        mod.write_artifacts()
        base = verdicts(mod)
        doc = mod.collect()
        rows = doc['rows']

        # ---- AC-CBXB1 <- AC-CBX1 ------------------------------------------
        zero = mod.resolve_row(dict(mod.BLOCKERS[0], anchor=r'NOT-THERE'))
        write(os.path.join(world, 'two.md'), 'DUP row a\nDUP row b\n')
        two = mod.resolve_row(dict(mod.BLOCKERS[0], path='two.md', anchor=r'DUP'))
        ok('AC-CBXB1 every row resolves, and 0-or-2 anchor hits read unresolved',
           base['AC-CBX1'] and all(r['resolved'] and r['quote'] for r in rows)
           and zero['resolved'] is False and '0 lines' in zero['reason']
           and two['resolved'] is False and '2 lines' in two['reason'],
           'resolved=%d/%d zero=%r two=%r' % (
               sum(1 for r in rows if r['resolved']), len(rows),
               zero['reason'], two['reason']))

        # ---- AC-CBXB2 <- AC-CBX2 -----------------------------------------
        saved = mod.BLOCKERS[1]['anchor']
        mod.BLOCKERS[1]['anchor'] = mod.BLOCKERS[0]['anchor']
        dup = verdicts(mod)
        dup_detail = [d for n, _g, d in mod.check() if n == 'AC-CBX2'][0]
        mod.BLOCKERS[1]['anchor'] = saved
        ok('AC-CBXB2 duplicate anchors redden the gate instead of passing',
           base['AC-CBX2'] and dup['AC-CBX2'] is False and 'PHYSROW' in dup_detail,
           'green_then_red=%s detail=%r' % (not dup['AC-CBX2'], dup_detail))

        # ---- AC-CBXB3 <- AC-CBX3 -----------------------------------------
        status = dict((r['id'], r['status']) for r in rows)
        reason = dict((r['id'], r['reason']) for r in rows)
        allowed = ('PENDING-PHYSICAL', 'PENDING-DECISION', 'UNKNOWN')
        derived = (mod.derive_status('a ' + PHYSICAL + ' block'),
                   mod.derive_status('a plain sentence'))
        ok('AC-CBXB3 statuses come from declared rules; no match reads UNKNOWN',
           base['AC-CBX3']
           and status == {'X1-phys': 'PENDING-PHYSICAL',
                          'X2-dec': 'PENDING-DECISION', 'X3-unk': 'UNKNOWN'}
           and all(s in allowed for s in status.values())
           and reason['X3-unk'] == 'no declared rule matched the quoted text'
           and derived == (('PENDING-PHYSICAL', 'source names a physical piece as the block'),
                           ('UNKNOWN', 'no declared rule matched the quoted text')),
           'statuses=%s derived=%r' % (status, derived[1][0]))

        # ---- AC-CBXB4 <- AC-CBX4 -----------------------------------------
        saved_face = mod.BLOCKERS[0]['face']
        mod.BLOCKERS[0]['face'] = 'preview/gone.html'
        missing_state = mod.face_state('preview/gone.html')
        miss = verdicts(mod)
        miss_detail = [d for n, _g, d in mod.check() if n == 'AC-CBX4'][0]
        mod.BLOCKERS[0]['face'] = saved_face
        ok('AC-CBXB4 a missing face reads MISSING and reddens the gate by name',
           base['AC-CBX4'] and missing_state == {
               'path': 'preview/gone.html', 'state': 'MISSING', 'bytes': None}
           and miss['AC-CBX4'] is False and 'X1-phys' in miss_detail,
           'state=%s detail=%r' % (missing_state['state'], miss_detail))

        # ---- AC-CBXB5 <- AC-CBX5 -----------------------------------------
        before = [(os.path.getsize(p), os.stat(p).st_mtime_ns)
                  for p in (mod.HTML_PATH, mod.JSON_PATH)]
        mod.check()
        after = [(os.path.getsize(p), os.stat(p).st_mtime_ns)
                 for p in (mod.HTML_PATH, mod.JSON_PATH)]
        ok('AC-CBXB5 --check does not author the artifacts it verifies',
           base['AC-CBX5'] and before == after,
           'unchanged=%s' % (before == after))

        # ---- AC-CBXB6 <- AC-CBX6 -----------------------------------------
        html_text = read(mod.HTML_PATH)
        scan = re.compile(r'https?://[A-Za-z0-9]')
        write(mod.HTML_PATH, html_text + '<a href="http://planted.example">x</a>\n')
        planted = scan.search(read(mod.HTML_PATH))
        red = verdicts(mod)
        mod.write_artifacts()
        ok('AC-CBXB6 the page carries no network literal and a planted one is caught',
           base['AC-CBX6'] and scan.search(html_text) is None
           and planted is not None and red['AC-CBX6'] is False,
           'clean=%s planted=%r' % (scan.search(html_text) is None,
                                    planted.group(0) if planted else None))

        # ---- AC-CBXB7 <- AC-CBX7 -----------------------------------------
        landed = json.loads(read(mod.JSON_PATH))
        disk = {'html': os.path.getsize(mod.HTML_PATH),
                'json': os.path.getsize(mod.JSON_PATH)}
        landed['sizes'] = {'html': disk['html'] + 1, 'json': disk['json']}
        write(mod.JSON_PATH, json.dumps(landed, ensure_ascii=False, indent=1,
                                       sort_keys=True) + '\n')
        tampered = dict((n, g) for n, g, _d in mod.check_landed(mod.collect()))
        mod.write_artifacts()
        fixed = dict((n, g) for n, g, _d in mod.check_landed(mod.collect()))
        ok('AC-CBXB7 the sizes block is a fixed point and a one-byte lie reddens it',
           base['AC-CBX7'] and landed is not None and tampered['AC-CBX7'] is False
           and fixed['AC-CBX7'] is True,
           'sizes=%s disk=%s tampered_red=%s' % (
               base and 'ok', disk, not tampered['AC-CBX7']))

        # ---- AC-CBXB8 <- AC-CBX8 -----------------------------------------
        html_text = read(mod.HTML_PATH)
        cards = html_text.count('<div class="card ')
        header = re.search(r'(\d+) rows &middot; generated by', html_text)
        write(mod.HTML_PATH, html_text.replace('<div class="card ', '<div class="cardZ ', 1))
        short = dict((n, g) for n, g, _d in mod.check_landed(mod.collect()))
        mod.write_artifacts()
        ok('AC-CBXB8 one card per registry row, and a dropped card reddens the gate',
           base['AC-CBX8'] and cards == len(rows) == 3
           and header is not None and int(header.group(1)) == 3
           and short['AC-CBX8'] is False,
           'cards=%d header=%s dropped_red=%s' % (
               cards, header.group(1) if header else 'absent',
               not short['AC-CBX8']))

        # ---- AC-CBXB9 <- AC-CBX9 -----------------------------------------
        html_text = read(mod.HTML_PATH)
        ok('AC-CBXB9 banner, non-advisory notice and the live tick are on the page',
           base['AC-CBX9'] and mod.BANNER in html_text
           and mod.DISCLAIMER in html_text and 'Tick 999' in html_text
           and doc['tick'] == '999',
           'banner=%s disclaimer=%s tick=%s' % (
               mod.BANNER in html_text, mod.DISCLAIMER in html_text, doc['tick']))

        # ---- AC-CBXB10: the defect measured at open ----------------------
        write(mod.STATE_PATH, json.dumps({'tick': 1000}, indent=1) + '\n')
        drifted = verdicts(mod)
        drifted_tick = mod.collect()['tick']
        mod.write_artifacts()
        after_render = verdicts(mod)
        ok('AC-CBXB10 a page one tick behind the state reddens AC-CBX9, re-render greens it',
           drifted['AC-CBX9'] is False and drifted_tick == '1000'
           and after_render['AC-CBX9'] is True
           and 'Tick 1000' in read(mod.HTML_PATH),
           'drift_red=%s tick=%s after_render=%s' % (
               not drifted['AC-CBX9'], drifted_tick,
               after_render['AC-CBX9']))

        # ---- AC-CBXB11: the registry row that makes this suite run -------
        reg = read(REGISTRY)
        declared = []
        for hit in re.finditer(r'"os-ceo-blockers"', reg):
            found = re.search(r'test_ceo_blockers\.py"\)\s*,\s*(\d+)',
                              reg[hit.start():hit.start() + 200])
            if found:
                declared.append(found.group(1))
        ok('AC-CBXB11 registry declares exactly one row for this suite',
           len(declared) == 1, 'rows=%s' % (declared,))
    finally:
        (mod.REPO, mod.HTML_PATH, mod.JSON_PATH, mod.STATE_PATH,
         blocklist, mod.QUOTE_CHARS) = original
        mod.BLOCKERS = blocklist
        shutil.rmtree(world, ignore_errors=True)

    repo_after = real_snapshot()
    ok('AC-CBXB0 the real preview pair and the temp world are left untouched',
       repo_before == repo_after and not os.path.isdir(world),
       'preview_stable=%s world_removed=%s' % (repo_before == repo_after,
                                              not os.path.isdir(world)))

    total = len(CHECKS)
    # Declared units (R2860): the AC inventory below is derived from CHECKS,
    # never echoed from the registry - a declaration copied out of the
    # registry could never disagree with it.
    acs = set()
    for name in CHECKS:
        token = name.split(' ', 1)[0]
        for cut in range(len(token), 0, -1):
            if token[cut - 1].isdigit():
                acs.add(token[:cut])
                break
    print('suite: %d assertions over %d criteria' % (total, len(acs)))
    if FAILS:
        print('SUITE FAIL %d/%d failed=%s' % (total - len(FAILS), total, FAILS))
        return 1
    print('SUITE PASS %d/%d in %.1fs' % (total, total, time.time() - started))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
