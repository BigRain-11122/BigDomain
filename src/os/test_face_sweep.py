"""Battery suite for tools/face_sweep.py - criteria AC-FSWB1..AC-FSWB17.

AC-FSWB1..AC-FSWB10 were pinned in src/os/backlog.md at R2819 BEFORE this suite
existed; AC-FSWB11..AC-FSWB13 were pinned at R2903, AC-FSWB14..AC-FSWB15 at
R2905 and AC-FSWB16..AC-FSWB17 at R2906, each BEFORE their legs were written.
R2903's three legs grade the reading order (money proof first), the per-row
consequence sentence, and the fact that the rule bites only on the table that owns
the money row. R2905's legs grade that the money row's sentence QUOTES its own
measurement (so a reader can refute it) and that the consequence is authored in one
place rather than two - both measured with red controls on this private world. The reason is measured, not argued: the tool carries eleven criteria in
AC_FSW (AC-FSW0..AC-FSW9 printed by check(), plus AC-FSW10/AC-FSW11 added this
window) and ONE battery row driving EIGHT CEO-openable faces, and a full-text
search of the shipped registry found ZERO AC-FSW* tokens in any row - so the only
thing guarding the eight-panel board was the board's own --check, which nothing
schedules.

The defect AC-FSWB2 holds, measured at open: `python tools/face_sweep.py --check`
read VERDICT PASS 9/9 while the landed board carried
generated_utc=2026-11-15T16:53:40Z and preview/index.html (07:38) and
preview/membership-face.html (07:37) had both been re-rendered AFTER it. The
board's sentence "every face gate exited zero" had become unfalsifiable. R2804
chose that on purpose (AC-FSW4/AC-FSW9 check existence, bytes are a snapshot), so
the fix is a separate criterion rather than a reinterpretation: every face
artifact must be OLDER than the sweep that published its verdict.

Isolation: the whole sweep, every tamper and every refutation runs in the system
temp dir against stub drivers written there. The real preview/ directory is
snapshotted by name, size and mtime_ns before and after and must be identical,
and no repo file is written by this suite.

Source discipline: pure ASCII, stdlib only, no network, no shell.
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
PREVIEW = os.path.join(ROOT, 'preview')
REGISTRY = os.path.join(ROOT, 'src', 'sandbox', 'reconcile_all.py')
FAILS = []
CHECKS = []

PASS_DRIVER = "import sys\nprint('VERDICT PASS 1/1')\nsys.exit(0)\n"
FAIL_DRIVER = "import sys\nprint('VERDICT FAIL 0/1')\nsys.exit(2)\n"
MONEY_DRIVER = "import sys\nprint('VERDICT PASS legs=2 tx=1 reconcile_rc=0')\nsys.exit(0)\n"
MUTATE_DRIVER = ("import sys\n"
                 "open(%r, 'w', encoding='utf-8', newline='\\n').write('rewritten by its own gate')\n"
                 "print('VERDICT PASS 1/1')\n"
                 "sys.exit(0)\n")


def ok(name, cond, detail=''):
    CHECKS.append(name)
    if cond:
        print('  | PASS %s %s' % (name, detail))
    else:
        FAILS.append(name)
        print('  | FAIL %s %s' % (name, detail))


def load_tool():
    spec = importlib.util.spec_from_file_location('face_sweep_under_test', TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def snapshot(dirpath, suffixes):
    out = {}
    if not os.path.isdir(dirpath):
        return out
    for name in sorted(os.listdir(dirpath)):
        if not name.endswith(suffixes):
            continue
        st = os.stat(os.path.join(dirpath, name))
        out[name] = (st.st_size, st.st_mtime_ns)
    return out


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(text)


def run_quiet(fn):
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = fn()
    return rc, buf.getvalue()


def world_setup(tool):
    """Build a private world: stub drivers plus one pair of artifacts per face."""
    world = tempfile.mkdtemp(prefix='face-sweep-world-')
    prev = os.path.join(world, 'preview')
    tools = os.path.join(world, 'tools')
    os.makedirs(prev, exist_ok=True)
    os.makedirs(tools, exist_ok=True)
    write(os.path.join(tools, 'stub-pass.py'), PASS_DRIVER)
    write(os.path.join(tools, 'stub-fail.py'), FAIL_DRIVER)
    faces = [
        dict(id='stub-a', label='stub a', driver='tools/stub-pass.py',
             html='preview/stub-a.html', json='preview/stub-a.json',
             meaning='a red stub-a costs nothing, it is a fixture'),
        dict(id='stub-b', label='stub b', driver='tools/stub-pass.py',
             html='preview/stub-b.html', json='preview/stub-b.json',
             meaning='a red stub-b costs nothing, it is a fixture'),
        dict(id='stub-c', label='stub c', driver='tools/stub-pass.py',
             html='preview/stub-c.html', json='preview/stub-c.json',
             meaning='a red stub-c costs nothing, it is a fixture'),
    ]
    for f in faces:
        write(os.path.join(world, f['html']), '<html>%s</html>\n' % f['id'])
        write(os.path.join(world, f['json']), '{"id": "%s"}\n' % f['id'])
    tool.ROOT = world
    tool.OUT_HTML = os.path.join(world, 'preview', 'face-sweep.html')
    tool.OUT_JSON = os.path.join(world, 'preview', 'face-sweep.json')
    tool.FACES = [(f['id'], f['label'], f['driver'], f['html'], f['json'], f.get('meaning', '')) for f in faces]
    return world, prev, tools, faces


def face_opts():
    return {'check': False, 'faces_json': None, 'timeout': 30}


def main():
    started = time.time()
    pre_preview = snapshot(PREVIEW, ('.html', '.json'))
    tool = load_tool()
    world, prev, tools, faces = world_setup(tool)
    try:
        # ---- AC-FSWB3 positive leg: a real sweep, then every artifact is OLDER than the
        # stamp it published under. Without this leg the new gate could be satisfied by
        # being permanently red, which would say nothing.
        rc, out = run_quiet(lambda: tool.sweep(face_opts()))
        doc = json.load(io.open(tool.OUT_JSON, encoding='utf-8'))
        swept_ns = doc.get('swept_ns')
        ok('AC-FSWB3 sweep exits zero on all-passing stubs', rc == 0, 'rc=%d' % rc)
        mtimes = []
        for f in faces:
            for key in ('html', 'json'):
                mtimes.append((f['id'], key, os.stat(os.path.join(world, f[key])).st_mtime_ns))
        ok('AC-FSWB3b every face artifact is older than swept_ns',
           isinstance(swept_ns, int) and all(m <= swept_ns for _i, _k, m in mtimes),
           'swept_ns=%r newest_delta=%r'
           % (swept_ns, max(m for _i, _k, m in mtimes) - swept_ns if isinstance(swept_ns, int) else None))
        # R2903: the expected total is DERIVED from the tool's one declared criteria list,
        # never typed here. A second copy of the number would move independently of the
        # first, which is the drift R2901 deleted a literal to stop.
        expect = 'VERDICT PASS %d/%d' % (len(tool.CRITERIA), len(tool.CRITERIA))
        rc, out = run_quiet(lambda: tool.check())
        ok('AC-FSWB3c a fresh board reads PASS', rc == 0 and expect in out,
           out.strip().splitlines()[-1] if out.strip() else 'no output')

        # ---- AC-FSWB1 the landed board is self-consistent, and the criteria CARRY weight:
        # flipping one row's exit code in the landed document must redden it.
        tampered = json.load(io.open(tool.OUT_JSON, encoding='utf-8'))
        ok('AC-FSWB1 landed doc states its own sizes and a derived fingerprint',
           tampered.get('sizes') == {'html': os.path.getsize(tool.OUT_HTML),
                                     'json': os.path.getsize(tool.OUT_JSON)}
           and tampered.get('fingerprint') == tool.fingerprint(tampered['faces']),
           'fingerprint=%s' % tampered.get('fingerprint'))
        tampered['faces'][0]['exit'] = 7
        write(tool.OUT_JSON, json.dumps(tampered, ensure_ascii=False, indent=1) + '\n')
        rc, out = run_quiet(lambda: tool.check())
        ok('AC-FSWB1b a row whose exit disagrees with the headline reddens the board',
           rc == 2 and 'FAIL' in out, 'rc=%d' % rc)
        write(tool.OUT_JSON, json.dumps(doc, ensure_ascii=False, indent=1) + '\n')

        # ---- AC-FSWB2 the hole itself, proved as a difference on ONE private world:
        # moving one artifact past the stamp reddens with the face NAMED, restoring it
        # greens again. Size is untouched, so AC-FSW1 cannot be the reason it reddens.
        target = os.path.join(world, faces[1]['html'])
        real = os.stat(target)
        os.utime(target, ns=(real.st_atime_ns, swept_ns + 10 ** 9))
        rc, out = run_quiet(lambda: tool.check())
        ok('AC-FSWB2 an artifact newer than the sweep reddens and names the face',
           rc == 2 and 'E_FACE_STALE' in out and 'stub-b' in out,
           'rc=%d named=%s' % (rc, 'stub-b' in out))
        ok('AC-FSWB2b size untouched, so the size criterion cannot be the cause',
           os.path.getsize(target) == real.st_size,
           'size=%d stable=%s' % (real.st_size, os.path.getsize(target) == real.st_size))
        os.utime(target, ns=(real.st_atime_ns, real.st_mtime_ns))
        rc, out = run_quiet(lambda: tool.check())
        ok('AC-FSWB2c restoring the mtime returns the board to PASS', rc == 0, 'rc=%d' % rc)

        # ---- AC-FSWB4 a legacy board with no sweep stamp is REFUSED, not read as fresh.
        legacy = json.load(io.open(tool.OUT_JSON, encoding='utf-8'))
        legacy.pop('swept_ns', None)
        before = io.open(tool.OUT_JSON, 'rb').read()
        write(tool.OUT_JSON, json.dumps(legacy, ensure_ascii=False, indent=1) + '\n')
        rc, out = run_quiet(lambda: tool.check())
        ok('AC-FSWB4 a board without swept_ns is refused with E_FSW_NO_SWEEP_STAMP',
           rc == 2 and 'E_FSW_NO_SWEEP_STAMP' in out, 'rc=%d' % rc)
        write(tool.OUT_JSON, before.decode('utf-8'))

        # ---- AC-FSWB5 one red gate drags the whole board down.
        fail_faces = [dict(faces[0]),
                      dict(faces[1], driver='tools/stub-fail.py'),
                      dict(faces[2])]
        tool.FACES = [(f['id'], f['label'], f['driver'], f['html'], f['json']) for f in fail_faces]
        rc, out = run_quiet(lambda: tool.sweep(face_opts()))
        doc_fail = json.load(io.open(tool.OUT_JSON, encoding='utf-8'))
        row_b = [r for r in doc_fail['faces'] if r['id'] == 'stub-b'][0]
        ok('AC-FSWB5 a face whose gate exits non-zero is not counted as passing',
           rc == 2 and not tool._passing(row_b) and doc_fail['headline']['verdict'] == 'FAIL',
           'rc=%d verdict=%s' % (rc, doc_fail['headline']['verdict']))

        # ---- AC-FSWB6 a missing driver is MISSING-DRIVER and cannot pass.
        gone_faces = [dict(faces[0]),
                      dict(faces[1], driver='tools/stub-absent.py'),
                      dict(faces[2])]
        tool.FACES = [(f['id'], f['label'], f['driver'], f['html'], f['json']) for f in gone_faces]
        rc, out = run_quiet(lambda: tool.sweep(face_opts()))
        doc_gone = json.load(io.open(tool.OUT_JSON, encoding='utf-8'))
        row_g = [r for r in doc_gone['faces'] if r['id'] == 'stub-b'][0]
        ok('AC-FSWB6 a missing driver reads MISSING-DRIVER and is not passing',
           row_g['verdict'] == 'MISSING-DRIVER' and not tool._passing(row_g) and rc == 2,
           'verdict=%s rc=%d' % (row_g['verdict'], rc))

        # ---- AC-FSWB7 a gate that rewrites its own evidence is caught by mutation.
        write(os.path.join(tools, 'stub-mutate.py'),
              MUTATE_DRIVER % os.path.join(world, faces[0]['html']))
        mut_faces = [dict(faces[0], driver='tools/stub-mutate.py'),
                     dict(faces[1]),
                     dict(faces[2])]
        tool.FACES = [(f['id'], f['label'], f['driver'], f['html'], f['json'], f.get('meaning', ''))
                      for f in mut_faces]
        rc, out = run_quiet(lambda: tool.sweep(face_opts()))
        doc_mut = json.load(io.open(tool.OUT_JSON, encoding='utf-8'))
        row_m = [r for r in doc_mut['faces'] if r['id'] == 'stub-a'][0]
        ok('AC-FSWB7 a driver that rewrites its own artifact is mutated and not passing',
           row_m['mutated'] is True and not tool._passing(row_m) and rc == 2,
           'mutated=%r files=%r' % (row_m['mutated'], row_m['mutated_files']))
        rc, out = run_quiet(lambda: tool.check())
        ok('AC-FSWB7b check() refuses a board carrying a mutated row',
           rc == 2 and 'AC-FSW9' in out, 'rc=%d' % rc)

        # ---- AC-FSWB8 the sweep is read-only toward every face artifact it measures.
        tool.FACES = [(f['id'], f['label'], f['driver'], f['html'], f['json'], f.get('meaning', '')) for f in faces]
        write(os.path.join(world, faces[0]['html']), '<html>stub-a</html>\n')
        pre_pair = snapshot(prev, ('.html', '.json'))
        pre_faces = {f['id']: (os.stat(os.path.join(world, f['html'])).st_mtime_ns,
                               os.stat(os.path.join(world, f['json'])).st_mtime_ns)
                     for f in faces}
        rc, out = run_quiet(lambda: tool.sweep(face_opts()))
        post_faces = {f['id']: (os.stat(os.path.join(world, f['html'])).st_mtime_ns,
                                os.stat(os.path.join(world, f['json'])).st_mtime_ns)
                      for f in faces}
        changed = [k for k in pre_faces if pre_faces[k] != post_faces[k]]
        ok('AC-FSWB8 a passing sweep writes no face artifact',
           not changed, 'changed=%r' % (changed,))

        # ---- AC-FSWB9 the landed page is a real page: three standing lines, the two notes,
        # every row linked, and no external literal.
        page = io.open(tool.OUT_HTML, encoding='utf-8').read()
        doc9 = json.load(io.open(tool.OUT_JSON, encoding='utf-8'))
        standing_ok = all(tool._esc(line) in page for line in tool.STANDING)
        ok('AC-FSWB9 the three standing compliance lines are resident',
           standing_ok and tool._esc(tool.EXCLUDED_NOTE) in page
           and tool._esc(tool.SNAPSHOT_NOTE) in page,
           'standing=%s excluded=%s snapshot=%s'
           % (standing_ok, tool.EXCLUDED_NOTE in page, tool.SNAPSHOT_NOTE in page))
        ok('AC-FSWB9b every row is linked and no external literal appears',
           all(r['html'] in page for r in doc9['faces'])
           and not tool.EXTERNAL_RE.findall(page),
           'rows=%d' % len(doc9['faces']))

        # ---- AC-FSWB10 the registry row did not exist when these criteria were pinned;
        # this criterion is what makes that absence red. The count is read from the tuple
        # itself (label line, then the path+criterion tail) rather than from the line
        # after the path: the first version of this parser read the NEXT line and read
        # rows=[] against a row that was already present, which is a parser defect this
        # window measured and fixed rather than a criterion being relaxed.
        text = io.open(REGISTRY, encoding='utf-8').read()
        hits = [ln for ln in text.splitlines() if 'test_face_sweep.py' in ln]
        declared = re.findall(r'test_face_sweep\.py"\)\s*,\s*(\d+)', text)
        # R2906: the expected count was a typed literal ("15") and went stale the moment this
        # window grew the suite - the same two-places defect R2901 deleted a hand-moved count
        # for. It is now DERIVED from this file's own AC-FSWB inventory (the same quantity the
        # registry row records), not from the tool's AC-FSW list, which is a different count.
        src10 = io.open(__file__, encoding='utf-8').read()
        want = [str(len(set(re.findall(r'AC-FSWB\d+', src10))))]
        ok('AC-FSWB10 the battery registry declares one row for this suite at its own count %s'
           % want[0],
           declared == want and len(hits) == 1,
           'rows=%s hits=%d expected=%s' % (declared, len(hits), want))

        # ---- AC-FSWB11 (R2903) every row must say what its FAIL costs, and the page must
        # quote it. A blank consequence reads as "no consequence", so it is REFUSED rather
        # than rendered as an empty cell. Both directions on one world: the lawful board is
        # green, and the same board with one row's sentence deleted reddens naming that row.
        tool.FACES = [(f['id'], f['label'], f['driver'], f['html'], f['json'], f['meaning'])
                      for f in faces]
        rc, out = run_quiet(lambda: tool.sweep(face_opts()))
        doc11 = json.load(io.open(tool.OUT_JSON, encoding='utf-8'))
        page11 = io.open(tool.OUT_HTML, encoding='utf-8').read()
        ok('AC-FSWB11 every row carries its consequence and the page quotes it',
           rc == 0 and all(r.get('meaning') and tool._esc(r['meaning']) in page11
                           for r in doc11['faces']) and tool.COL_MEANING in page11,
           'rows=%d' % len(doc11['faces']))
        blanked = json.loads(json.dumps(doc11))
        blanked['faces'][0]['meaning'] = ''
        io.open(tool.OUT_JSON, 'w', encoding='utf-8', newline='\n').write(
            json.dumps(blanked, ensure_ascii=False, indent=1) + '\n')
        rc, out = run_quiet(lambda: tool.check())
        ok('AC-FSWB11b a row with no declared consequence reddens and is named',
           rc == 2 and ('AC-FSW12 %s' % doc11['faces'][0]['id']) in out, 'rc=%d' % rc)

        # ---- AC-FSWB12 (R2903) the row order is a READING order declared in the document
        # and equal to the rows it landed; reversing the rows makes page and data disagree
        # about which row a reader should trust first, so it must redden.
        rc, out = run_quiet(lambda: tool.sweep(face_opts()))
        doc12 = json.load(io.open(tool.OUT_JSON, encoding='utf-8'))
        ok('AC-FSWB12 the landed order equals the rows it landed',
           doc12.get('reading_order') == [r['id'] for r in doc12['faces']],
           'order=%r' % (doc12.get('reading_order'),))
        shuffled = json.loads(json.dumps(doc12))
        shuffled['faces'] = list(reversed(shuffled['faces']))
        io.open(tool.OUT_JSON, 'w', encoding='utf-8', newline='\n').write(
            json.dumps(shuffled, ensure_ascii=False, indent=1) + '\n')
        rc, out = run_quiet(lambda: tool.check())
        ok('AC-FSWB12b a reversed document reddens on AC-FSW13', rc == 2 and 'AC-FSW13' in out,
           'rc=%d' % rc)

        # ---- AC-FSWB13 (R2903) the money-first rule BITES where it applies and cannot bite
        # where it does not: a table that owns the money row must land it first (green), and
        # the same table with the money row moved last is refused by name. The rule is scoped
        # to the loaded table, so a fixture world owning no money row is not forced.
        # R2905: the fixture money row now runs a driver that prints a MEASUREMENT, because
        # AC-FSW14 refuses a money row whose verdict carries no legs=/tx= reading - the same
        # dialect the shipped first-yuan-chain gate prints.
        write(os.path.join(world, 'preview', 'money.html'), '<html>money</html>\n')
        write(os.path.join(world, 'preview', 'money.json'), '{"id": "money"}\n')
        write(os.path.join(tools, 'stub-money.py'), MONEY_DRIVER)
        money_row = (tool.MONEY_ID, 'money proof stub', 'tools/stub-money.py',
                     'preview/money.html', 'preview/money.json',
                     'a red money row is zero revenue')
        rest = [(f['id'], f['label'], f['driver'], f['html'], f['json'], f['meaning'])
                for f in faces]
        tool.FACES = [money_row] + rest
        rc, out = run_quiet(lambda: tool.sweep(face_opts()))
        rc2, out2 = run_quiet(lambda: tool.check())
        ok('AC-FSWB13 a table that owns the money row lands it first and reads PASS',
           rc == 0 and rc2 == 0,
           'sweep=%d check=%d' % (rc, rc2))
        tool.FACES = rest + [money_row]
        rc, out = run_quiet(lambda: tool.sweep(face_opts()))
        rc2, out2 = run_quiet(lambda: tool.check())
        ok('AC-FSWB13b the same table with the money row last is refused E_MONEY_NOT_FIRST',
           rc2 == 2 and 'E_MONEY_NOT_FIRST' in out2, 'rc=%d' % rc2)

        # ---- AC-FSWB14 (R2905) the money sentence QUOTES ITS OWN MEASUREMENT, so a reader
        # can refute it without opening another page. Positive: the shipped derivation puts
        # the row's own legs=/tx= into the sentence. Negative: the same landed page with the
        # sentence claiming a number its row did not report reddens naming the row, and a
        # money row whose gate prints no measurement is refused rather than published blank.
        tool.FACES = [money_row] + rest
        rc, out = run_quiet(lambda: tool.sweep(face_opts()))
        doc14 = json.load(io.open(tool.OUT_JSON, encoding='utf-8'))
        row14 = [r for r in doc14['faces'] if r['id'] == tool.MONEY_ID][0]
        legs14, tx14 = tool.money_tokens(row14['verdict'])
        ok('AC-FSWB14 the money sentence carries the reading its own row reported',
           rc == 0 and legs14 is not None and tx14 is not None
           and ('legs=%s' % legs14) in row14['meaning'] and ('tx=%s' % tx14) in row14['meaning'],
           'legs=%r tx=%r' % (legs14, tx14))
        rc, out = run_quiet(lambda: tool.check())
        ok('AC-FSWB14b the lawful measured board reads PASS', rc == 0, 'rc=%d' % rc)
        doctored = json.loads(json.dumps(doc14))
        for r in doctored['faces']:
            if r['id'] == tool.MONEY_ID:
                r['meaning'] = r['meaning'].replace('tx=%s' % tx14, 'tx=9')
        io.open(tool.OUT_JSON, 'w', encoding='utf-8', newline='\n').write(
            json.dumps(doctored, ensure_ascii=False, indent=1) + '\n')
        rc, out = run_quiet(lambda: tool.check())
        ok('AC-FSWB14c a sentence claiming tx=9 over a row reading tx=%s reddens' % tx14,
           rc == 2 and 'AC-FSW14' in out and tool.MONEY_ID in out, 'rc=%d' % rc)
        # the fail-closed arm: a money gate that prints no measurement cannot be published
        write(os.path.join(tools, 'stub-money-bare.py'), PASS_DRIVER)
        bare_row = (tool.MONEY_ID, 'money proof stub', 'tools/stub-money-bare.py',
                    'preview/money.html', 'preview/money.json',
                    'a red money row is zero revenue')
        tool.FACES = [bare_row] + rest
        rc, out = run_quiet(lambda: tool.sweep(face_opts()))
        rc2, out2 = run_quiet(lambda: tool.check())
        bare_doc = json.load(io.open(tool.OUT_JSON, encoding='utf-8'))
        bare_meaning = [r for r in bare_doc['faces'] if r['id'] == tool.MONEY_ID][0]['meaning']
        ok('AC-FSWB14d a money row with no reading is REFUSED, not published bare',
           tool.MONEY_UNMEASURED in bare_meaning and rc2 == 2
           and 'E_FSW_MONEY_UNMEASURED' in out2, 'rc=%d' % rc2)

        # ---- AC-FSWB15 (R2905) ONE AUTHORED PLACE: a row that loses its sentence from its
        # own tuple reddens by id, and the inherited copy is read from the CURRENT table at
        # call time rather than from a stored index - so a spec that declares no sentence for
        # a face the table no longer carries inherits nothing instead of a stale leftover.
        tool.FACES = [money_row] + rest
        rc, out = run_quiet(lambda: tool.sweep(face_opts()))
        rc, out = run_quiet(lambda: tool.check())
        ok('AC-FSWB15 the shipped-shape table reads PASS with every row declaring its own',
           rc == 0, 'rc=%d' % rc)
        short = [(f[0], f[1], f[2], f[3], f[4]) for f in ([money_row] + rest)]
        tool.FACES = short
        rc, out = run_quiet(lambda: tool.check())
        ok('AC-FSWB15b a five-field row reddens and is named',
           rc == 2 and 'AC-FSW15' in out and tool.MONEY_ID in out, 'rc=%d' % rc)
        tool.FACES = [money_row] + rest
        spec = os.path.join(world, 'spec-inherit.json')
        write(spec, json.dumps([
            dict(id=tool.MONEY_ID, label='m', driver='tools/stub-money.py',
                 html='preview/money.html', json='preview/money.json'),
            dict(id='stub-absent-from-table', label='x', driver='tools/stub-money.py',
                 html='preview/money.html', json='preview/money.json'),
        ]))
        loaded = tool.load_faces(spec)
        ok('AC-FSWB15c an undeclared sentence inherits the CURRENT row tuple',
           loaded[0]['meaning'] == money_row[5], 'inherited=%r' % (loaded[0]['meaning'],))
        ok('AC-FSWB15d a face the table does not carry inherits NOTHING, never a leftover',
           loaded[1]['meaning'] == '', 'inherited=%r' % (loaded[1]['meaning'],))

        # ---- AC-FSWB16 (R2906) the OTHER TWO REVENUE ROWS quote their own reading, so the
        # one refutable claim on the board is no longer an exception a reader has to notice.
        # Positive: a payment row whose gate prints products=/tiers= publishes both. Negative:
        # a sentence claiming tiers=9 over a row reading tiers=0 reddens naming that row. The
        # fail-closed arm: a revenue gate printing no such token is refused, not published bare.
        write(os.path.join(tools, 'stub-value.py'),
              "import sys\nprint('value-domain: PASS products=5 tiers=0')\nsys.exit(0)\n")
        write(os.path.join(prev, 'pay.html'), '<html>pay</html>\n')
        write(os.path.join(prev, 'pay.json'), '{"id": "pay"}\n')
        write(os.path.join(prev, 'memb.html'), '<html>memb</html>\n')
        write(os.path.join(prev, 'memb.json'), '{"id": "memb"}\n')
        pay_row = ('payment-gate', 'payment stub', 'tools/stub-value.py',
                   'preview/pay.html', 'preview/pay.json',
                   'a red payment row is lost revenue')
        mem_row = ('membership', 'membership stub', 'tools/stub-value.py',
                   'preview/memb.html', 'preview/memb.json',
                   'a red membership row is zero repeat purchase')
        tool.FACES = [money_row, pay_row, mem_row] + rest
        rc, out = run_quiet(lambda: tool.sweep(face_opts()))
        doc16 = json.load(io.open(tool.OUT_JSON, encoding='utf-8'))
        pay16 = [r for r in doc16['faces'] if r['id'] == 'payment-gate'][0]
        mem16 = [r for r in doc16['faces'] if r['id'] == 'membership'][0]
        ok('AC-FSWB16 the payment row carries products=/tiers= from its own verdict',
           rc == 0 and 'products=5' in pay16['meaning'] and 'tiers=0' in pay16['meaning'],
           'meaning=%r' % (pay16['meaning'],))
        ok('AC-FSWB16b the membership row carries its own reading too',
           'products=5' in mem16['meaning'] and 'tiers=0' in mem16['meaning'],
           'meaning=%r' % (mem16['meaning'],))
        rc, out = run_quiet(lambda: tool.check())
        ok('AC-FSWB16c the lawful three-revenue-row board reads PASS', rc == 0, 'rc=%d' % rc)
        doctored = json.loads(json.dumps(doc16))
        for r in doctored['faces']:
            if r['id'] == 'payment-gate':
                r['meaning'] = r['meaning'].replace('tiers=0', 'tiers=9')
        io.open(tool.OUT_JSON, 'w', encoding='utf-8', newline='\n').write(
            json.dumps(doctored, ensure_ascii=False, indent=1) + '\n')
        rc, out = run_quiet(lambda: tool.check())
        ok('AC-FSWB16d a payment sentence claiming tiers=9 over a row reading tiers=0 reddens',
           rc == 2 and 'AC-FSW16' in out and 'payment-gate' in out, 'rc=%d' % rc)
        bare_pay = ('payment-gate', 'payment stub', 'tools/stub-pass.py',
                    'preview/pay.html', 'preview/pay.json',
                    'a red payment row is lost revenue')
        tool.FACES = [money_row, bare_pay, mem_row] + rest
        rc, out = run_quiet(lambda: tool.sweep(face_opts()))
        rc2, out2 = run_quiet(lambda: tool.check())
        bare_doc = json.load(io.open(tool.OUT_JSON, encoding='utf-8'))
        bare_pay_meaning = [r for r in bare_doc['faces'] if r['id'] == 'payment-gate'][0]['meaning']
        ok('AC-FSWB16e a revenue row with no reading is REFUSED, not published bare',
           tool.MONEY_UNMEASURED in bare_pay_meaning and rc2 == 2
           and 'E_FSW_REVENUE_UNMEASURED' in out2, 'rc=%d' % rc2)

        # ---- AC-FSWB17 (R2906) THE DOCUMENT SAYS WHY only some rows carry a bracket: the
        # scope sentence is on the page, and the rows that actually carry a bracket must be
        # exactly the revenue rows whose verdict supplied one - so prose and data cannot
        # disagree about the scope, and a non-revenue row cannot quietly grow a bracket.
        tool.FACES = [money_row, pay_row, mem_row] + rest
        rc, out = run_quiet(lambda: tool.sweep(face_opts()))
        html17 = io.open(tool.OUT_HTML, encoding='utf-8').read()
        rc, out = run_quiet(lambda: tool.check())
        ok('AC-FSWB17 the scope sentence is on the landed page',
           tool.SCOPE_LINE in html17 and rc == 0, 'rc=%d' % rc)
        doc17 = json.load(io.open(tool.OUT_JSON, encoding='utf-8'))
        doctored = json.loads(json.dumps(doc17))
        for r in doctored['faces']:
            if r['id'] == 'stub-a':
                r['meaning'] = r['meaning'] + tool.ROW_MEASURED % 'products=1 tiers=1'
        io.open(tool.OUT_JSON, 'w', encoding='utf-8', newline='\n').write(
            json.dumps(doctored, ensure_ascii=False, indent=1) + '\n')
        rc, out = run_quiet(lambda: tool.check())
        ok('AC-FSWB17b a non-revenue row that grows a bracket reddens E_FSW_SCOPE_DRIFT',
           rc == 2 and 'E_FSW_SCOPE_DRIFT' in out, 'rc=%d' % rc)
    finally:
        shutil.rmtree(world, ignore_errors=True)

    ok('AC-FSWB8b the temp world is removed (a leak is loud, not silent)',
       not os.path.isdir(world), 'removed=%s' % (not os.path.isdir(world)))
    ok('AC-FSWB8c the real preview/ directory is unchanged by the whole suite',
       pre_preview == snapshot(PREVIEW, ('.html', '.json')),
       'entries=%d' % len(pre_preview))

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
    sys.exit(main())
