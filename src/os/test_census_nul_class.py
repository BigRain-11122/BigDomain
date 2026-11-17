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
R2887 replaced the earlier "the real qa/ directory is snapshotted by name, size
and mtime_ns before and after" law, which measured the SHARED directory rather
than this suite: a concurrent writer - another window's evidence, a detached
leg still in flight - reddened it while this suite leaked nothing (measured at
entries=3251 in a 285-suite leg and reproduced at entries=3256 with a foreign
writer, then green with the same writer pointed outside qa/). The criterion now
names the writes THIS process made (builtins.open / io.open / os.open /
os.replace armed for the whole body) and requires none of them under qa/, plus
a negative control that a deliberate write into qa/ is caught and cleaned up.
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


_WRITE_LOG = []
_RECORDER_ON = [False]


def under(path, root):
    try:
        p = os.path.abspath(path)
        r = os.path.abspath(root)
    except Exception:
        return False
    return p == r or p.startswith(r + os.sep)


def record(path):
    if _RECORDER_ON[0] and isinstance(path, str) and path.strip():
        try:
            _WRITE_LOG.append(os.path.abspath(path))
        except Exception:
            pass


def arm_writer_recorder():
    """Record every path THIS process opens for writing.

    R2887 replaced the whole-directory qa/ snapshot with attribution: the old
    AC-NULC6/6c read the shared directory's name+size+mtime before and after,
    so any FOREIGN writer - another window's evidence, a detached leg still in
    flight - reddened them while this suite leaked nothing. Measured: the same
    suite reads 9/9 alone, and reads FAIL 7/9 with entries=3256 the moment a
    concurrent writer appends inside qa/, then 9/9 again when the identical
    writer is pointed outside qa/. A criterion that reddens on someone else's
    legitimate write cannot be a gate for this suite; naming the writes this
    process made is immune to it and is stronger for the leak class, because it
    also sees a write into a name the snapshot never listed.
    """
    if _RECORDER_ON[0]:
        return
    import builtins

    def wrap(orig):
        def inner(file, mode='r', *a, **kw):
            try:
                flags = set(str(mode))
            except Exception:
                flags = set()
            if flags & set('wax+'):
                record(file)
            return orig(file, mode, *a, **kw)
        return inner

    real_os_open = os.open
    real_replace = os.replace

    def os_open_inner(path, flags, *a, **kw):
        if flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND):
            record(path)
        return real_os_open(path, flags, *a, **kw)

    def replace_inner(src, dst):
        record(dst)
        return real_replace(src, dst)

    builtins.open = wrap(builtins.open)
    io.open = wrap(io.open)
    os.open = os_open_inner
    os.replace = replace_inner
    _RECORDER_ON[0] = True


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
    arm_writer_recorder()
    world = tempfile.mkdtemp(prefix='nulc-')
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

        # ---- AC-NULC6: everything private, no write into the real qa/ ------
        inside = os.path.abspath(world)
        outside = [n for n in os.listdir(world)
                   if not os.path.abspath(os.path.join(world, n)).startswith(inside)]
        qa_writes = [p for p in _WRITE_LOG if under(p, QA_DIR)]
        ok('AC-NULC6 no write this suite made landed in the real qa/',
           _RECORDER_ON[0] and len(_WRITE_LOG) > 0
           and qa_writes == [] and outside == [],
           'armed=%s writes=%d qa_writes=%d escapes=%d' % (
               _RECORDER_ON[0], len(_WRITE_LOG), len(qa_writes),
               len(outside)))

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

    # ---- AC-NULC6c: the recorder is not a rubber stamp ---------------------
    # A green that can never redden is the failure mode this battery exists to
    # catch, so the same predicate is pointed at a deliberate write INTO qa/:
    # it must catch exactly that name, and the probe must leave nothing behind.
    probe = os.path.join(QA_DIR, '_nulc6c_escape_probe.tmp')
    probe_name = os.path.basename(probe)
    pre_names = [n for n in os.listdir(QA_DIR) if n == probe_name]
    pre_writes = len(_WRITE_LOG)
    with io.open(probe, 'wb') as fh:
        fh.write(b'probe\n')
    caught = [p for p in _WRITE_LOG[pre_writes:] if under(p, QA_DIR)]
    if os.path.exists(probe):
        os.remove(probe)
    confined = [p for p in _WRITE_LOG[:pre_writes]
                if not (under(p, world) or under(p, tempfile.gettempdir())
                        or p.endswith('.pyc'))]
    ok('AC-NULC6c negative control: a real write into qa/ IS caught, and no '
       'data write escapes temp (interpreter .pyc caching excluded)',
       len(caught) == 1 and not os.path.exists(probe) and pre_names == []
       and confined == [],
       'caught=%d probe_gone=%s confined=%d writes=%d' % (
           len(caught), not os.path.exists(probe), len(confined),
           len(_WRITE_LOG)))

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
