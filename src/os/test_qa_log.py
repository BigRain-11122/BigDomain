"""Battery suite for tools/qa_log.py - criteria AC-QALB1..AC-QALB9.

AC-QALB1..AC-QALB9 were pinned in src/os/backlog.md at R2807 BEFORE this suite
existed, mapping one-to-one onto AC-QAL1..AC-QAL7 that the tool prints, plus one
gate-weight criterion and one criterion for a defect this window measured. The
reason: importing the shipped registry read 691 suites / 5163 criteria and a
full-text search found ZERO AC-QAL* tokens in any of them, so the one writer
every window's evidence passes through was guarded only by its own --selftest.

The defect AC-QALB8 holds, measured before any code was written: read_source
did not recognise BOM-less UTF-16LE, so 'P\\x00A\\x00...' was accepted as
readable text, do_write printed VERDICT PASS over a 61-byte file carrying 30
NUL bytes and 5 phantom lines, and the tool's own classify() read the result
back as utf-8/lf. The census tool has its own classifier and does not ask this
one, so the whole evidence library reads healthy either way.

Isolation: every write, check, tamper and selftest run happens in the system
temp dir. The real qa/ directory is snapshotted by name, size and mtime_ns
before and after and must be identical. The repo files are never written.

Source discipline: pure ASCII, stdlib only, no clock in assertions, no network,
no shell.
"""
import hashlib
import importlib.util
import io
import os
import re
import shutil
import sys
import tempfile
import time
from contextlib import redirect_stdout

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOL = os.path.join(ROOT, 'tools', 'qa_log.py')
QA_DIR = os.path.join(ROOT, 'qa')
ARCH = os.path.join(ROOT, 'logs', 'qa-encoding-preop-R2775',
                    'index-newest-band-R2775.log.utf16le')
LIVE = os.path.join(QA_DIR, 'index-newest-band-R2775.log')
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
    spec = importlib.util.spec_from_file_location('qalog_under_test', TOOL)
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
    with redirect_stdout(buf):
        rc = fn(*a, **kw)
    return rc, buf.getvalue()


def main():
    started = time.time()
    world = tempfile.mkdtemp(prefix='qalb-')
    qa_private = os.path.join(world, 'qa')
    os.makedirs(qa_private)
    pre_qa = qa_snapshot()
    mod = load_tool()
    original_qa = mod.QA
    try:
        # ---- AC-QALB1: every source dialect lands as utf-8/lf, text intact --
        cases = [
            ('utf16bom.log',
             b'\xff\xfe' + 'a\r\nb\r\n'.encode('utf-16-le'), 'a\nb\n'),
            ('utf8bom.log',
             b'\xef\xbb\xbf' + 'hello\nworld\n'.encode('utf-8'),
             'hello\nworld\n'),
            ('gb18030.log',
             u'\u4e2d\u6587\u8bc1\u636e\n\u7b2c\u4e8c\u884c\n'
             .encode('gb18030'),
             u'\u4e2d\u6587\u8bc1\u636e\n\u7b2c\u4e8c\u884c\n'),
            ('plainlf.log', b'x\n\n\n', 'x\n'),
        ]
        landed = []
        for name, raw, expected in cases:
            rc, out = quiet(mod.do_write, name, raw, directory=qa_private)
            body = read_bytes(os.path.join(qa_private, name))
            text = body.decode('utf-8')
            landed.append({
                'name': name, 'rc': rc, 'pass_word': 'VERDICT PASS' in out,
                'no_bom': not body.startswith(b'\xef\xbb\xbf'),
                'no_cr': b'\r' not in body, 'one_nl': body.endswith(b'\n')
                and not body.endswith(b'\n\n'), 'text_eq': text == expected,
            })
        ok('AC-QALB1 four dialects land as utf-8/lf with text intact',
           all(r['rc'] == 0 and r['pass_word'] and r['no_bom'] and r['no_cr']
               and r['one_nl'] and r['text_eq'] for r in landed),
           'rows=%d utf16=%s utf8bom=%s gb18030=%s plain=%s' % (
               len(landed),
               landed[0]['text_eq'], landed[1]['text_eq'],
               landed[2]['text_eq'], landed[3]['text_eq']))

        # ---- AC-QALB2: the printed proof is recomputed here, not trusted ----
        proof_rows = []
        for name, _raw, _exp in cases:
            path = os.path.join(qa_private, name)
            body = read_bytes(path)
            want = (len(body), len(body.decode('utf-8').splitlines()),
                    hashlib.sha256(body).hexdigest()[:16])
            rc, out = quiet(mod.do_write, name, body, directory=qa_private)
            got = re.search(r'bytes=(\d+) lines=(\d+) sha256=([0-9a-f]{16})',
                            out)
            proof_rows.append((rc, got is not None and got.group(1) == str(want[0])
                               and got.group(2) == str(want[1])
                               and got.group(3) == want[2]))
        cr_path = os.path.join(world, 'injected-cr.log')
        with io.open(cr_path, 'wb') as f:
            f.write(b'a\r\nb\n')
        cr_caught = False
        try:
            mod.verify_written(cr_path)
        except ValueError:
            cr_caught = True
        ok('AC-QALB2 printed bytes/lines/sha256 recomputed; CR injection refused',
           all(r[0] == 0 and r[1] for r in proof_rows) and cr_caught,
           'rows_matched=%d/%d cr_caught=%s' % (
               len([r for r in proof_rows if r[1]]), len(proof_rows),
               cr_caught))

        # ---- AC-QALB3: atomic, no .tmp survivor, a refusal writes nothing ---
        atomic = os.path.join(world, 'atomic')
        os.makedirs(atomic)
        for i in range(10):
            quiet(mod.do_write, 'w%02d.log' % i, b'line\n', directory=atomic)
        names = sorted(os.listdir(atomic))
        tmp_left = [n for n in names if n.endswith('.tmp')]
        undecodable_refused = False
        try:
            quiet(mod.do_write, 'bad.log',
                  b'\xff\xfe' + b'\x00\xd8', directory=atomic)
        except ValueError:
            undecodable_refused = True
        names_after = sorted(os.listdir(atomic))
        ok('AC-QALB3 ten atomic writes, zero .tmp, refusal leaves no half file',
           len([n for n in names if n.endswith('.log')]) == 10
           and tmp_left == [] and undecodable_refused
           and 'bad.log' not in names_after
           and [n for n in names_after if n.endswith('.tmp')] == [],
           'logs=%d tmp=%d refused=%s bad_absent=%s' % (
               len([n for n in names if n.endswith('.log')]), len(tmp_left),
               undecodable_refused, 'bad.log' not in names_after))

        # ---- AC-QALB4: --check read-only; four dialects verdict 0/2/2/2 -----
        chk = os.path.join(world, 'check-world')
        os.makedirs(chk)
        with io.open(os.path.join(chk, 'good.log'), 'wb') as f:
            f.write(b'ok\n')
        with io.open(os.path.join(chk, 'ps16.log'), 'wb') as f:
            f.write(b'\xff\xfe' + 'ok\n'.encode('utf-16-le'))
        with io.open(os.path.join(chk, 'u8bom.log'), 'wb') as f:
            f.write(b'\xef\xbb\xbf' + b'ok\n')
        with io.open(os.path.join(chk, 'crlf.log'), 'wb') as f:
            f.write(b'ok\r\n')
        order = ['good.log', 'ps16.log', 'u8bom.log', 'crlf.log']
        before = dict((n, stamp(os.path.join(chk, n))) for n in order)
        mod.QA = chk
        verdicts = [quiet(mod.do_check, n)[0] for n in order]
        mod.QA = original_qa
        after = dict((n, stamp(os.path.join(chk, n))) for n in order)
        ok('AC-QALB4 --check read-only, verdict 0/2/2/2 and stats unchanged',
           verdicts == [0, 2, 2, 2] and before == after,
           'verdicts=%s stats_stable=%s' % (
               ','.join(str(v) for v in verdicts), before == after))

        # ---- AC-QALB5: the archived sample replays byte-equal, no skip ------
        arch_present = os.path.isfile(ARCH)
        live_present = os.path.isfile(LIVE)
        replay_eq = False
        if arch_present and live_present:
            replayed = mod.normalize(mod.read_source(read_bytes(ARCH)))
            replay_eq = replayed.encode('utf-8') == read_bytes(LIVE)
        ok('AC-QALB5 archived R2775 sample replays byte-equal (missing = red)',
           arch_present and live_present and replay_eq,
           'archive=%s live=%s byte_equal=%s' % (
               arch_present, live_present, replay_eq))

        # ---- AC-QALB6: five bad names refused, a good name accepted --------
        bad = ['', 'sub/dir.log', 'C:x.log', '..\\x.log', '.hidden']
        refused = 0
        for name in bad:
            try:
                mod.check_name(name)
            except ValueError:
                refused += 1
        good_accepted = True
        try:
            mod.check_name('probe-R2807.log')
        except ValueError:
            good_accepted = False
        rc_good, _out = quiet(mod.do_write, 'probe-R2807.log', b'ok\n',
                              directory=qa_private)
        ok('AC-QALB6 five bad names refused and one good name really writes',
           refused == 5 and good_accepted and rc_good == 0
           and os.path.isfile(os.path.join(qa_private, 'probe-R2807.log')),
           'refused=%d/5 accepted=%s wrote=%s' % (
               refused, good_accepted, rc_good == 0))

        # ---- AC-QALB7: selftest never touches qa/, source purity -----------
        pre_self = qa_snapshot()
        rc_self, out_self = quiet(mod.selftest)
        post_self = qa_snapshot()
        tool_src = read_text(TOOL)
        suite_src = read_text(os.path.abspath(__file__))
        tool_allowed = {'hashlib', 'io', 'os', 'sys', 'tempfile'}
        suite_allowed = {'hashlib', 'importlib', 'io', 'os', 're', 'shutil',
                         'sys', 'tempfile', 'time', 'contextlib'}

        def imp_names(text):
            names = set()
            for ln in text.splitlines():
                s = ln.strip()
                if s.startswith('import '):
                    names.add(s.split()[1].split('.')[0])
                elif s.startswith('from ') and ' import ' in s:
                    names.add(s.split()[1].split('.')[0])
            return names
        tool_imp = imp_names(tool_src)
        suite_imp = imp_names(suite_src)
        banned = {'socket', 'urllib', 'requests', 'http', 'subprocess'}
        net_tool = sorted(tool_imp & banned) + re.findall(
            r'\b(?:socket|urllib|requests|subprocess)\.\w', tool_src)
        net_suite = sorted(suite_imp & banned) + re.findall(
            r'\b(?:socket|urllib|requests|subprocess)\.\w', suite_src)
        ok('AC-QALB7 selftest 8/8 leaves qa/ identical, both sources pure',
           rc_self == 0 and 'VERDICT PASS 8/8' in out_self
           and pre_self == post_self
           and all(ord(c) < 128 for c in tool_src)
           and all(ord(c) < 128 for c in suite_src)
           and tool_imp <= tool_allowed and suite_imp <= suite_allowed
           and not net_tool and not net_suite,
           'rc=%d verdict=%s qa_stable=%s tool_extra=%s suite_extra=%s net=%s'
           % (rc_self, 'VERDICT PASS 8/8' in out_self, pre_self == post_self,
              ','.join(sorted(tool_imp - tool_allowed)),
              ','.join(sorted(suite_imp - suite_allowed)),
              net_tool + net_suite))

        # ---- AC-QALB8: a NUL-bearing source is refused, not certified ------
        nul_raw = 'PASS line one\nPASS line two\n'.encode('utf-16-le')
        refused_nul = False
        nul_err = ''
        try:
            mod.read_source(nul_raw)
        except ValueError as exc:
            refused_nul = True
            nul_err = str(exc)[:60]
        plant = os.path.join(chk, 'nul-planted.log')
        with io.open(plant, 'wb') as f:
            f.write(nul_raw)
        nul_class = mod.classify(read_bytes(plant))
        mod.QA = chk
        nul_check = quiet(mod.do_check, 'nul-planted.log')[0]
        mod.QA = original_qa
        ok('AC-QALB8 NUL-bearing source refused and a planted NUL file is red',
           refused_nul and nul_class != 'utf-8/lf' and nul_check == 2,
           'refused=%s class=%s check_rc=%d reason=%s' % (
               refused_nul, nul_class, nul_check, nul_err))

        # ---- AC-QALB10: a flag is never a log name, refusal writes nothing --
        flag_names = ['--help', '-x.log', '--from']
        flag_refused = 0
        for name in flag_names:
            try:
                mod.check_name(name)
            except ValueError:
                flag_refused += 1
        before_entries = sorted(os.listdir(qa_private))
        wrote_nothing = True
        for name in flag_names:
            try:
                mod.do_write(name, b'flag probe\n', directory=qa_private)
                wrote_nothing = False
            except ValueError:
                pass
        after_entries = sorted(os.listdir(qa_private))
        rc_probe, _out = quiet(mod.do_write, 'probe-R2809.log', b'ok\n',
                               directory=qa_private)
        ok('AC-QALB10 a leading dash is refused and a refusal writes no file',
           flag_refused == 3 and before_entries == after_entries
           and wrote_nothing and rc_probe == 0
           and os.path.isfile(os.path.join(qa_private, 'probe-R2809.log')),
           'refused=%d/3 dir_stable=%s wrote_nothing=%s good_rc=%d' % (
               flag_refused, before_entries == after_entries,
               wrote_nothing, rc_probe))

        # ---- AC-QALB9: one registry row declares nine ----------------------
        reg = read_text(REGISTRY)
        hits = [m.start() for m in re.finditer(r'"os-qa-log"', reg)]
        declared = []
        for pos in hits:
            found = re.search(r'test_qa_log\.py"\)\s*,\s*(\d+)',
                              reg[pos:pos + 200])
            if found:
                declared.append(found.group(1))
        ok('AC-QALB9 registry declares exactly one row for this suite, ten',
           declared == ['10'], 'rows=%s hits=%d' % (declared, len(hits)))
    finally:
        mod.QA = original_qa
        shutil.rmtree(world, ignore_errors=True)

    leak = os.path.isdir(world)
    ok('AC-QALB9c temp world removed (a leak is loud, not silent)', not leak,
       'removed=%s' % (not leak))
    post_qa = qa_snapshot()
    ok('AC-QALB9b the real qa/ directory is unchanged by the whole suite',
       pre_qa == post_qa, 'entries=%d stable=%s' % (len(post_qa),
                                                    pre_qa == post_qa))

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
