"""Battery suite for the nul-bytes class in src/os/qa_writer_census.py -
criteria AC-NULC1..AC-NULC7.

R2808 added the class and re-froze the baseline, but the only things guarding
the new rule were the tool's own --check and two existing census suites. Those
two derive their expectations from CENSUS.BASELINE_CLASSES on both sides, so
adding a class cannot break them - measured, not assumed - which also means
neither of them can redden if the new branch disappears. AC-NULC1..AC-NULC6
were pinned in src/os/backlog.md at R2808 BEFORE this file existed; AC-NULC7 was
declared here as the registry-declaration criterion (the same shape R2807 used
for AC-QALB9) and is disclosed rather than presented as pre-pinned.

What the class exists for, stated as the defect it holds: a BOM-less UTF-16LE
evidence log has no BOM to name it, and its every-other-byte NUL padding decodes
as VALID utf-8 with zero CR - so the pre-R2808 rule read crlf==0 + utf8==True and
called it `tee`, the healthy dialect. Thirteen files under qa/ were certified
healthy by that path. AC-NULC2 holds both classifiers side by side on the SAME
bytes, so the repair is measured as a difference rather than described.

AC-NULC1 is the ordering criterion: a UTF-16LE file WITH a BOM also carries NUL
bytes, so if the NUL branch ever moves above the BOM branch the ps-utf16 name -
and with it the R2775 refusal face - would be swallowed.

Isolation: every fixture, baseline and check runs inside one system temp dir.
The real qa/ directory is snapshotted by name, size and mtime_ns before and
after and must be identical; no repo byte is written by this suite.

Source discipline: pure ASCII, stdlib only, no network, no shell, no clock in
any assertion.
"""
import importlib.util
import io
import os
import re
import shutil
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOL = os.path.join(ROOT, 'src', 'os', 'qa_writer_census.py')
QA_DIR = os.path.join(ROOT, 'qa')
REGISTRY = os.path.join(ROOT, 'src', 'sandbox', 'reconcile_all.py')
FAILS = []
CHECKS = []


def ok(name, cond, detail=''):
    CHECKS.append(name)
    if cond:
        print('  | PASS %s %s' % (name, detail))
    else:
        FAILS.append(name)
        print('  | FAIL %s %s' % (name, detail))


def load_tool():
    """Import the shipped tool by path. It fixes its own sys.path for the
    qa_decode_probe and reconcile_all single-source imports."""
    spec = importlib.util.spec_from_file_location('census_under_test', TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def read_bytes(path):
    with io.open(path, 'rb') as f:
        return f.read()


def read_text(path):
    with io.open(path, 'r', encoding='utf-8') as f:
        return f.read()


def stamp(path):
    st = os.stat(path)
    return (st.st_size, st.st_mtime_ns)


def qa_snapshot():
    """Name+size+mtime of every entry in the real qa/ dir (no recursion)."""
    rows = []
    for name in sorted(os.listdir(QA_DIR)):
        path = os.path.join(QA_DIR, name)
        try:
            st = os.stat(path)
            rows.append((name, st.st_size, st.st_mtime_ns))
        except OSError:
            rows.append((name, -1, -1))
    return rows


def quiet(fn, *a, **kw):
    """Run a printing tool function and return (rc, stdout text)."""
    buf = io.StringIO()
    old = sys.stdout
    sys.stdout = buf
    try:
        rc = fn(*a, **kw)
    finally:
        sys.stdout = old
    return rc, buf.getvalue()


def nul_payload():
    """BOM-less UTF-16LE: strict utf-8 decodable, zero CR, NUL padding."""
    return 'PASS line one\nPASS line two\n'.encode('utf-16-le')


def bom_payload():
    """UTF-16LE WITH BOM: same NUL padding, but the BOM must win."""
    return b'\xff\xfe' + 'hello\n'.encode('utf-16-le')


def legacy_class(raw, bom_of):
    """The census rule as it stood BEFORE R2808, restated here so the repair
    can be measured on identical bytes. Copied deliberately: this is the
    historical rule under test, not a second source of truth."""
    bom = bom_of(raw)
    crlf = raw.count(b'\r\n')
    bare = raw.count(b'\n') - crlf
    utf8 = True
    try:
        raw.decode('utf-8', 'strict')
    except UnicodeDecodeError:
        utf8 = False
    if bom in ('utf-16le', 'utf-16be'):
        return 'ps-utf16'
    if bom == 'utf-8-sig':
        return 'other'
    if crlf == 0:
        return 'tee' if utf8 else 'other'
    if crlf > bare:
        return 'pwsh-capture' if utf8 else 'cmd-raw'
    return 'other'


def main():
    started = time.time()
    world = tempfile.mkdtemp(prefix='nulc-')
    pre_qa = qa_snapshot()
    mod = load_tool()
    qdp = mod.QDP
    try:
        # ---- AC-NULC1: the BOM branch still wins over the NUL branch -------
        c1 = os.path.join(world, 'c1')
        os.makedirs(c1)
        bom_path = os.path.join(c1, 'with-bom.log')
        with io.open(bom_path, 'wb') as f:
            f.write(bom_payload())
        bom_row = mod.classify_file(bom_path)
        raw_bom = read_bytes(bom_path)
        ok('AC-NULC1 utf-16le BOM sample is ps-utf16, not nul-bytes',
           bom_row['class'] == 'ps-utf16'
           and b'\x00' in raw_bom
           and 'nul-bytes' in mod.CLASSES,
           'class=%s bom=%s has_nul=%s' % (
               bom_row['class'], bom_row['bom'], b'\x00' in raw_bom))

        # ---- AC-NULC2: same bytes, two classifiers, measured difference ----
        c2 = os.path.join(world, 'c2')
        os.makedirs(c2)
        nul_path = os.path.join(c2, 'no-bom.log')
        raw_nul = nul_payload()
        with io.open(nul_path, 'wb') as f:
            f.write(raw_nul)
        cur = mod.classify_file(nul_path)['class']
        old = legacy_class(raw_nul, qdp._bom_of)
        strict_ok = True
        try:
            raw_nul.decode('utf-8', 'strict')
        except UnicodeDecodeError:
            strict_ok = False
        ok('AC-NULC2 legacy rule says tee, shipped rule says nul-bytes',
           old == 'tee' and cur == 'nul-bytes'
           and strict_ok and raw_nul.count(b'\r\n') == 0
           and b'\x00' in raw_nul,
           'legacy=%s current=%s utf8_strict=%s crlf=0 nul=yes' % (
               old, cur, strict_ok))

        # ---- AC-NULC3: baselined-by-name is quiet, a new one still flags ----
        c3 = os.path.join(world, 'c3')
        os.makedirs(c3)
        with io.open(os.path.join(c3, 'known-nul.log'), 'wb') as f:
            f.write(nul_payload())
        with io.open(os.path.join(c3, 'healthy.log'), 'wb') as f:
            f.write(b'ok\n')
        bpath = os.path.join(c3, mod.BASELINE_NAME)
        freeze, freeze_code, _base = mod.write_baseline(c3, bpath)
        frozen = read_bytes(bpath)
        named = mod.census_names(c3)['nul-bytes']
        quiet_lines, quiet_code = mod.check_against_baseline(c3, bpath)
        quiet_blob = '\n'.join(quiet_lines)
        with io.open(os.path.join(c3, 'fresh-nul.log'), 'wb') as f:
            f.write(nul_payload())
        red_lines, red_code = mod.check_against_baseline(c3, bpath)
        red_blob = '\n'.join(red_lines)
        ok('AC-NULC3 nul-bytes is a baseline class: quiet when named, red when new',
           'nul-bytes' in mod.BASELINE_CLASSES
           and named == ['known-nul.log']
           and quiet_code == 0 and '[flag]' not in quiet_blob
           and red_code == 2
           and '[flag] new-dialect: fresh-nul.log (class=nul-bytes)' in red_blob
           and freeze_code == 0 and frozen == read_bytes(bpath),
           'baseline_class=%s named=%s quiet_rc=%d red_rc=%d red_names=%s' % (
               'nul-bytes' in mod.BASELINE_CLASSES, named, quiet_code,
               red_code, 'fresh-nul.log' in red_blob))

        # ---- AC-NULC4: the debt line is always printed and always right -----
        recount = len(mod.census_names(c3)['nul-bytes'])
        found = re.search(r'^nul_bytes=(\d+)$', red_blob, re.M)
        ok('AC-NULC4 --check prints nul_bytes= equal to an independent recount',
           found is not None and int(found.group(1)) == recount
           and recount == 2,
           'printed=%s recounted=%d' % (
               found.group(1) if found else 'absent', recount))

        # ---- AC-NULC5: an old baseline without the key is refused, untouched -
        c5 = os.path.join(world, 'c5')
        os.makedirs(c5)
        with io.open(os.path.join(c5, 'x.log'), 'wb') as f:
            f.write(b'ok\n')
        old_base = dict((c, []) for c in mod.BASELINE_CLASSES
                        if c != 'nul-bytes')
        old_path = os.path.join(c5, 'legacy-baseline.json')
        with io.open(old_path, 'w', encoding='utf-8', newline='\n') as f:
            f.write('{\n')
            f.write(',\n'.join('  "%s": []' % c for c in sorted(old_base)))
            f.write('\n}\n')
        before = read_bytes(old_path)
        before_stat = stamp(old_path)
        r5_lines, r5_code = mod.check_against_baseline(c5, old_path)
        ok('AC-NULC5 baseline missing the nul-bytes key is refused rc=2, byte-stable',
           r5_code == 2
           and 'missing class key nul-bytes' in '\n'.join(r5_lines)
           and read_bytes(old_path) == before
           and stamp(old_path) == before_stat,
           'rc=%d bytes_stable=%s mtime_stable=%s' % (
               r5_code, read_bytes(old_path) == before,
               stamp(old_path) == before_stat))

        # ---- AC-NULC6: everything private, the real qa/ is untouched --------
        post_qa = qa_snapshot()
        inside = os.path.abspath(world)
        outside = [n for n in os.listdir(world)
                   if not os.path.abspath(os.path.join(world, n)).startswith(inside)]
        ok('AC-NULC6 all work inside temp dir, real qa/ byte- and mtime-identical',
           pre_qa == post_qa and outside == [],
           'entries=%d stable=%s escapes=%d' % (
               len(post_qa), pre_qa == post_qa, len(outside)))

        # ---- AC-NULC7: the registry declares exactly one row, seven ---------
        reg = read_text(REGISTRY)
        hits = [m.start() for m in re.finditer(r'"os-census-nul-class"', reg)]
        declared = []
        for pos in hits:
            found_row = re.search(r'test_census_nul_class\.py"\)\s*,\s*(\d+)',
                                  reg[pos:pos + 220])
            if found_row:
                declared.append(found_row.group(1))
        ok('AC-NULC7 registry declares exactly one row for this suite, seven',
           declared == ['7'], 'rows=%s hits=%d' % (declared, len(hits)))
    finally:
        shutil.rmtree(world, ignore_errors=True)

    leak = os.path.isdir(world)
    ok('AC-NULC6b temp world removed (a leak is loud, not silent)', not leak,
       'removed=%s' % (not leak))
    post_qa2 = qa_snapshot()
    ok('AC-NULC6c the real qa/ directory is unchanged by the whole suite',
       pre_qa == post_qa2, 'entries=%d stable=%s' % (len(post_qa2),
                                                     pre_qa == post_qa2))

    total = len(CHECKS)
    if FAILS:
        print('SUITE FAIL %d/%d failed=%s' % (total - len(FAILS), total, FAILS))
        return 1
    print('SUITE PASS %d/%d in %.1fs' % (total, total, time.time() - started))
    return 0


if __name__ == '__main__':
    sys.exit(main())
