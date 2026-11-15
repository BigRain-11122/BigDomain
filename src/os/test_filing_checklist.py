"""Battery suite for tools/filing_checklist.py - criteria AC-FCL1..AC-FCL8.

Criteria were pinned in src/os/backlog.md BEFORE the tool existed. Every check
runs inside a PRIVATE world because AC-FCL7 is a negative control that deletes
the benchmark document - the real docs/ tree is never touched by a test run.

Source discipline: pure ASCII, stdlib only, no clock, no network, no shell.
"""
import importlib.util
import io
import json
import os
import re
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOL = os.path.join(ROOT, 'tools', 'filing_checklist.py')
FAILS = []
CHECKS = []

BENCH_ROW = (
    "| \u5c0f\u7a0b\u5e8f\u5907\u6848 | \u5b98\u65b9\u6307\u5f15 | A | "
    "\u5e73\u53f0\u521d\u5ba1 1-2 \u4e2a\u5de5\u4f5c\u65e5 \u00b7 \u77ed\u4fe1 12381 \u00b7 "
    "\u901a\u7ba1\u5c40 1-20 \u4e2a\u5de5\u4f5c\u65e5 \u00b7 "
    "\u771f\u5b9e\u6027\u6838\u9a8c\u5355 \u00b7 \u7248\u53f7 \u00b7 2.5.35 |"
)


def ok(name, cond, detail=''):
    CHECKS.append(name)
    if cond:
        print('  | PASS %s %s' % (name, detail))
    else:
        FAILS.append(name)
        print('  | FAIL %s %s' % (name, detail))


def w(path, text):
    d = os.path.dirname(path)
    if d and not os.path.isdir(d):
        os.makedirs(d)
    with io.open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)


def rd(path):
    with io.open(path, 'r', encoding='utf-8') as f:
        return f.read()


def build_world():
    d = tempfile.mkdtemp(prefix='fcl-')
    w(os.path.join(d, 'BLUEPRINT.md'), '# B\n\nAIGC labels.\nmsgSecCheck pre-gate.\n')
    w(os.path.join(d, 'docs', 'global-benchmarks.md'), '# Bench\n\n' + BENCH_ROW + '\n')
    w(os.path.join(d, 'preview', 'ceo-blockers.json'),
      json.dumps({'counts': {'PENDING-PHYSICAL': 4}}, ensure_ascii=False))
    for name in ('face-sweep.html', 'platform-live-report.html'):
        w(os.path.join(d, 'preview', name), '<!DOCTYPE html>\n')
    return d


def load_tool():
    spec = importlib.util.spec_from_file_location('filing_under_test', TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    if not os.path.isfile(TOOL):
        print('SUITE FAIL 0/8 tool missing')
        return 1
    src = rd(TOOL)
    world = build_world()
    cwd = os.getcwd()
    try:
        os.chdir(world)
        mod = load_tool()
        html, text, rows, sizes = mod.render(write=True)
        doc = json.loads(text)
        bench = os.path.join('docs', 'global-benchmarks.md')
        bench_text = rd(bench)

        # AC-FCL1 derived rows are live; manual rows are never ready
        ok('AC-FCL1 no MANUAL row is ever presented as ready',
           all(r['state'] != 'READY' for r in rows if r['kind'] == mod.MANUAL),
           'manual=%d' % len([r for r in rows if r['kind'] == mod.MANUAL]))
        w(bench, '# Bench\n\n' + BENCH_ROW.replace('12381 ', '') + '\n')
        fresh = {r['id']: r['state'] for r in mod.build_rows()}
        ok('AC-FCL1 losing a needle flips the playbook row on disk',
           fresh['step-playbook'] == 'OPEN', fresh['step-playbook'])
        on_disk = json.loads(rd(os.path.join('preview', 'filing-checklist.json')))
        stamp = {r['id']: r['state'] for r in on_disk['items']}
        ok('AC-FCL1 the json keeps the old stamp until re-rendered',
           stamp['step-playbook'] == 'READY', stamp['step-playbook'])
        w(bench, bench_text)
        mod.render(write=True)

        # AC-FCL2 official timelines quoted
        need = ('1-2 \u4e2a\u5de5\u4f5c\u65e5', '12381', '24h',
                '1-20 \u4e2a\u5de5\u4f5c\u65e5')
        ok('AC-FCL2 all three official timelines are on the page',
           all(n in html for n in need), 'timelines=%d' % len(need))
        ok('AC-FCL2 the hard-order sentence is quoted, not paraphrased',
           '\u7ba1\u5c40\u5ba1\u6838\u901a\u8fc7\u540e' in html)

        # AC-FCL3 counts equal the registry and the benchmark carries the needles
        c = doc['counts']
        ok('AC-FCL3 counts equal the registry',
           c['materials'] == len(mod.MATERIALS)
           and c['pre_approval'] == len(mod.PRE_APPROVAL)
           and c['filing_types'] == len(mod.TYPES)
           and c['flow_steps'] == len(mod.FLOW),
           'm=%d p=%d t=%d f=%d' % (c['materials'], c['pre_approval'],
                                    c['filing_types'], c['flow_steps']))
        ok('AC-FCL3 the seven/ten/three shapes are what the page claims',
           len(mod.MATERIALS) == 7 and len(mod.PRE_APPROVAL) == 10
           and len(mod.TYPES) == 3, 'ok')

        # AC-FCL4 offline, every link target exists
        ok('AC-FCL4 the page opens offline',
           not any(b in html for b in mod.FORBIDDEN))
        hrefs = re.findall(r'href="([^"]+)"', html)
        ok('AC-FCL4 every relative link target exists on disk',
           all(os.path.isfile(h) for h in hrefs), 'hrefs=%s' % hrefs[:3])

        # AC-FCL5 tick ids, one namespace, one inline script
        ok('AC-FCL5 every row carries a stable data-ck id',
           all(('data-ck="%s"' % r['id']) in html for r in rows),
           'rows=%d' % len(rows))
        ok('AC-FCL5 one inline script and one localStorage namespace',
           html.count('<script>') == 1
           and "var NS='bd-filing-checklist-v1';" in html
           and 'localStorage.setItem(NS' in html)

        # AC-FCL6 sizes fixed point and idempotent render
        hb = os.path.getsize(os.path.join('preview', 'filing-checklist.html'))
        jb = os.path.getsize(os.path.join('preview', 'filing-checklist.json'))
        ok('AC-FCL6 recorded sizes equal the bytes on disk',
           doc['sizes']['html'] == hb and doc['sizes']['json'] == jb,
           'html=%d json=%d' % (hb, jb))
        html2, text2, _, _ = mod.render(write=False)
        ok('AC-FCL6 a second render is byte identical', html2 == html and text2 == text)

        # AC-FCL7 --check is read-only, and the negative control flips red
        hp = os.path.join('preview', 'filing-checklist.html')
        jp = os.path.join('preview', 'filing-checklist.json')
        snap = [(os.path.getsize(hp), os.stat(hp).st_mtime_ns),
                (os.path.getsize(jp), os.stat(jp).st_mtime_ns)]
        clean = mod.check()
        snap2 = [(os.path.getsize(hp), os.stat(hp).st_mtime_ns),
                 (os.path.getsize(jp), os.stat(jp).st_mtime_ns)]
        ok('AC-FCL7 --check writes nothing and the world reads clean',
           snap == snap2 and clean == [], 'fails=%s' % clean[:1])
        keep = rd(bench)
        os.remove(bench)
        red = mod.check()
        ok('AC-FCL7 deleting the benchmark document flips --check red',
           bool(red), 'fails=%d' % len(red))
        rc = mod.main(['--check'])
        ok('AC-FCL7 the CLI exits 2 on a red world', rc == 2, 'rc=%s' % rc)
        w(bench, keep)
        ok('AC-FCL7 restoring the document returns the gate to clean',
           mod.check() == [])

        # AC-FCL8 three hard doors with faces, purity, one registry row at 8
        doors = ('step-hard-door', 'step-playbook', 'step-ceo-pieces')
        bad = [r for r in rows if r['id'] in doors and not os.path.isfile(r['face'])]
        ok('AC-FCL8 the three restated faces all exist on disk', not bad,
           'bad=%d' % len(bad))
        ok('AC-FCL8 tool source is pure ASCII', all(ord(ch) < 128 for ch in src))
        reg = rd(os.path.join(ROOT, 'src', 'sandbox', 'reconcile_all.py'))
        hits = [m.start() for m in re.finditer(r'"os-filing-checklist"', reg)]
        counts = []
        for pos in hits:
            found = re.search(r'test_filing_checklist\.py"\)\s*,\s*(\d+)',
                              reg[pos:pos + 160])
            if found:
                counts.append(found.group(1))
        ok('AC-FCL8 exactly one battery row declares eight criteria',
           counts == ['8'], 'rows=%s' % counts)
    finally:
        os.chdir(cwd)
        shutil.rmtree(world, ignore_errors=True)

    total = len(CHECKS)
    if FAILS:
        print('SUITE FAIL %d/%d failed=%s' % (total - len(FAILS), total, FAILS))
        return 1
    print('SUITE PASS %d/%d' % (total, total))
    return 0


if __name__ == '__main__':
    sys.exit(main())
