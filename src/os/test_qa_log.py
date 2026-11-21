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
        tool_allowed = {'hashlib', 'io', 'os', 're', 'sys', 'tempfile'}
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
        # JUDGED-CHANGED (R3203): the selftest grew one fixture for AC-QAL9,
        # so its verdict line moved 8/8 -> 9/9. The fixture is asserted below
        # by AC-QALB11; this arm still reads the real printed total, so it
        # would redden if the count drifted without a matching criterion.
        ok('AC-QALB7 selftest 9/9 leaves qa/ identical, both sources pure',
           rc_self == 0 and 'VERDICT PASS 9/9' in out_self
           and pre_self == post_self
           and all(ord(c) < 128 for c in tool_src)
           and all(ord(c) < 128 for c in suite_src)
           and tool_imp <= tool_allowed and suite_imp <= suite_allowed
           and not net_tool and not net_suite,
           'rc=%d verdict=%s qa_stable=%s tool_extra=%s suite_extra=%s net=%s'
           % (rc_self, 'VERDICT PASS 9/9' in out_self, pre_self == post_self,
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
        ok('AC-QALB9 registry declares exactly one row for this suite, twenty',
           declared == ['20'], 'rows=%s hits=%d' % (declared, len(hits)))

        # ---- AC-QALB11: a carried proof line is marked, not certified -----
        # R3203: the generator prints "LOG OK path=... sha16=..." to prove a
        # file it wrote. Storing that stdout through this writer kept the line
        # verbatim inside a different file, whose own sha16 was another number,
        # while both dialect faces read green. Measured before the repair.
        carried_dir = os.path.join(world, 'carried')
        os.makedirs(carried_dir)
        proof_src = (b'PASS one\n'
                     b'LOG OK path=qa/preview.log bytes=661 lines=9 '
                     b'sha16=271ba9eb7b2d1230\n')
        rc_c, out_c = quiet(mod.do_write, 'relog.log', proof_src,
                            directory=carried_dir)
        relog = read_bytes(os.path.join(carried_dir, 'relog.log'))
        rc_c2, _out2 = quiet(mod.do_write, 'relog2.log', relog,
                             directory=carried_dir)
        twice = read_bytes(os.path.join(carried_dir, 'relog2.log'))
        plain_src = b'PASS x\n'
        rc_p, _outp = quiet(mod.do_write, 'plain.log', plain_src,
                            directory=carried_dir)
        plain_out = read_bytes(os.path.join(carried_dir, 'plain.log'))
        near_src = (b'LOG OK path=qa/preview.log bytes=six lines=9 '
                    b'sha16=271ba9eb7b2d1230\n')
        rc_n, out_n = quiet(mod.do_write, 'near.log', near_src,
                            directory=carried_dir)
        near_out = read_bytes(os.path.join(carried_dir, 'near.log'))
        plain_expected = mod.normalize(plain_src.decode('utf-8'))
        ok('AC-QALB11 carried proof marked CARRIED once, exact shapes only',
           rc_c == 0 and rc_c2 == 0 and rc_p == 0 and rc_n == 0
           and relog.count(b'CARRIED LOG OK path=') == 1
           and b'\nLOG OK path=' not in relog
           and 'QA-LOG CARRIED proofs=1' in out_c
           and twice.count(b'CARRIED') == 1
           and plain_out == plain_expected.encode('utf-8')
           and 'CARRIED' not in out_n and near_out == near_src
           and mod.classify(relog) == 'utf-8/lf',
           'rc=%d marked=%d unmarked=%s twice=%d plain_eq=%s near_stable=%s'
           % (rc_c, relog.count(b'CARRIED LOG OK path='),
              b'\nLOG OK path=' in relog, twice.count(b'CARRIED'),
              plain_out == plain_expected.encode('utf-8'),
              near_out == near_src))

        # ---- AC-QALB12: --check names how many carried proofs it saw ------
        # R3204: measured before the repair, three files holding 0, 1 and 2
        # CARRIED lines all read rc=0 with the same text, the census answered
        # class=tee for all three and the pre-commit gate refused none - it
        # reads row["class"] only. The count is exact shapes only, and it is
        # never a verdict.
        counted = os.path.join(world, 'carried-count')
        os.makedirs(counted)
        proof_a = ('LOG OK path=qa/preview.log bytes=661 lines=9 '
                   'sha16=271ba9eb7b2d1230')
        proof_b = ('LOG OK path=qa/other.log bytes=12 lines=1 '
                   'sha16=50522dc2cc6582c6')
        bodies = {
            'c0.log': 'PASS one\n',
            'c1.log': 'PASS one\nCARRIED ' + proof_a + '\n',
            'c2.log': ('PASS one\nCARRIED ' + proof_a + '\nCARRIED '
                       + proof_b + '\n'),
            'near.log': ('CARRIED LOG OK path=qa/p.log bytes=six lines=9 '
                         'sha16=271ba9eb7b2d1230\n' + proof_a + '\n'),
        }
        for cname, cbody in bodies.items():
            with io.open(os.path.join(counted, cname), 'wb') as handle:
                handle.write(cbody.encode('utf-8'))
        with io.open(os.path.join(counted, 'red.log'), 'wb') as handle:
            handle.write(b'\xef\xbb\xbfPASS one\nCARRIED ' +
                         proof_a.encode('utf-8') + b'\n')
        before_cnt = dict((n, stamp(os.path.join(counted, n))) for n in bodies)
        mod.QA = counted
        try:
            seen = dict((n, quiet(mod.do_check, n)) for n in bodies)
            red_rc, red_text = quiet(mod.do_check, 'red.log')
        finally:
            mod.QA = original_qa
        after_cnt = dict((n, stamp(os.path.join(counted, n))) for n in bodies)
        c2_body = read_bytes(os.path.join(counted, 'c2.log')).decode('utf-8')
        recomputed = len([ln for ln in c2_body.splitlines()
                          if ln.startswith('CARRIED ')
                          and mod.PROOF_LINE_RE.match(ln[8:])])
        c1_bytes = os.path.getsize(os.path.join(counted, 'c1.log'))
        live_rc, live_text = quiet(mod.do_check, 'index-newest-band-R2775.log')
        tool_src2 = read_text(TOOL)
        ok('AC-QALB12 --check names carried=N for exact shapes only, read-only',
           seen['c0.log'][0] == 0 and 'carried=0' in seen['c0.log'][1]
           and seen['c1.log'][0] == 0 and 'carried=1' in seen['c1.log'][1]
           and seen['c2.log'][0] == 0 and 'carried=2' in seen['c2.log'][1]
           and recomputed == 2
           and seen['near.log'][0] == 0
           and 'carried=0' in seen['near.log'][1]
           and before_cnt == after_cnt
           and ('bytes=%d ' % c1_bytes) in seen['c1.log'][1]
           and red_rc == 2 and 'carried=' not in red_text
           and live_rc == 0 and 'carried=0' in live_text
           and tool_src2.count('"QA-LOG OK ') == 1,
           'c0=%s c1=%s c2=%s recomputed=%d near=%s stats_stable=%s '
           'red_rc=%d red_has_field=%s live=%s sites=%d'
           % ('carried=0' in seen['c0.log'][1],
              'carried=1' in seen['c1.log'][1],
              'carried=2' in seen['c2.log'][1], recomputed,
              'carried=0' in seen['near.log'][1], before_cnt == after_cnt,
              red_rc, 'carried=' in red_text,
              'carried=0' in live_text,
              tool_src2.count('"QA-LOG OK ')))

        # ---- AC-QALB13: --check names how many UNMARKED proofs it saw ------
        # R3205: measured before the repair, three files holding 0, 1 and 2
        # bare proof lines all read rc=0 with text that differed only in
        # bytes=, the census answered class=tee for all three and the
        # pre-commit gate compares the dialect class only, never the body.
        # A bare line is born without do_write - measured today the only such
        # door is battery_shard.stream_evidence - and the real qa/ tree holds
        # zero of them. The field is a name, not a verdict.
        bare_dir = os.path.join(world, 'bare-count')
        os.makedirs(bare_dir)
        bare_bodies = {
            'u0.log': 'PASS one\n',
            'u1.log': 'PASS one\n' + proof_a + '\n',
            'u2.log': 'PASS one\n' + proof_a + '\n' + proof_b + '\n',
            'ucarried.log': 'PASS one\nCARRIED ' + proof_a + '\n',
            'unear.log': ('PASS one\nLOG OK path=qa/p.log bytes=six lines=9 '
                          'sha16=271ba9eb7b2d1230\n'),
        }
        for uname, ubody in bare_bodies.items():
            with io.open(os.path.join(bare_dir, uname), 'wb') as handle:
                handle.write(ubody.encode('utf-8'))
        with io.open(os.path.join(bare_dir, 'ured.log'), 'wb') as handle:
            handle.write(b'\xef\xbb\xbfPASS one\n' +
                         proof_a.encode('utf-8') + b'\n')
        before_bare = dict((n, stamp(os.path.join(bare_dir, n)))
                           for n in bare_bodies)
        mod.QA = bare_dir
        try:
            useen = dict((n, quiet(mod.do_check, n)) for n in bare_bodies)
            ured_rc, ured_text = quiet(mod.do_check, 'ured.log')
        finally:
            mod.QA = original_qa
        after_bare = dict((n, stamp(os.path.join(bare_dir, n)))
                          for n in bare_bodies)
        u2_text = read_bytes(os.path.join(bare_dir, 'u2.log')).decode('utf-8')
        urecount = len([ln for ln in u2_text.splitlines()
                        if mod.PROOF_LINE_RE.match(ln)])
        u1_bytes = os.path.getsize(os.path.join(bare_dir, 'u1.log'))
        uk_rc, uk_text = quiet(mod.do_check, 'index-newest-band-R2775.log')
        tool_src3 = read_text(TOOL)
        ok('AC-QALB13 --check names bare_proofs=N for exact shapes only',
           useen['u0.log'][0] == 0 and 'bare_proofs=0' in useen['u0.log'][1]
           and useen['u1.log'][0] == 0
           and 'bare_proofs=1' in useen['u1.log'][1]
           and useen['u2.log'][0] == 0
           and 'bare_proofs=2' in useen['u2.log'][1]
           and urecount == 2
           and 'bare_proofs=0' in useen['ucarried.log'][1]
           and 'carried=1' in useen['ucarried.log'][1]
           and 'bare_proofs=0' in useen['unear.log'][1]
           and 'carried=0' in useen['unear.log'][1]
           and before_bare == after_bare
           and ('bytes=%d ' % u1_bytes) in useen['u1.log'][1]
           and ured_rc == 2 and 'bare_proofs=' not in ured_text
           and uk_rc == 0 and 'bare_proofs=0' in uk_text
           and 'carried=0' in uk_text
           and tool_src3.count('"QA-LOG OK ') == 1,
           'u0=%s u1=%s u2=%s recount=%d carried_arm=%s near=%s stable=%s '
           'red_rc=%d red_has_field=%s live=%s sites=%d'
           % ('bare_proofs=0' in useen['u0.log'][1],
              'bare_proofs=1' in useen['u1.log'][1],
              'bare_proofs=2' in useen['u2.log'][1], urecount,
              ('bare_proofs=0' in useen['ucarried.log'][1]
               and 'carried=1' in useen['ucarried.log'][1]),
              'bare_proofs=0' in useen['unear.log'][1],
              before_bare == after_bare, ured_rc,
              'bare_proofs=' in ured_text,
              'bare_proofs=0' in uk_text,
              tool_src3.count('"QA-LOG OK ')))

        # ---- AC-QALB14: the progress door carries the same marking law ------
        # R3206: stream_evidence is the one qa/ door that does not go through
        # do_write, so it was the only place a bare proof line could be born.
        # Measured before the repair: today's three progress shapes (146B
        # RUNNING header, 226B killed-after-one-row, 432B complete) carry zero
        # proof shapes and mark byte for byte unchanged; a body carrying one
        # landed it unmarked while --check named bare_proofs=1. The law is
        # applied at the door, not at the reader, so no future leg needs a
        # reviewer to notice the line.
        shard_spec = importlib.util.spec_from_file_location(
            'shard_under_test', os.path.join(ROOT, 'tools', 'battery_shard.py'))
        shard = importlib.util.module_from_spec(shard_spec)
        shard_spec.loader.exec_module(shard)
        stream_dir = os.path.join(world, 'stream')
        os.makedirs(stream_dir)
        # R3214: the door now reads QA_DIR at call time (parent must equal it),
        # so this suite points it at a private directory instead of qa/.
        saved_shard_qa = shard.QA_DIR
        shard.QA_DIR = stream_dir
        stream_header = ('SHARD scope=SHARD registry_suites=2 '
                         'registry_criteria=2 selected=2 selected_criteria=2 '
                         'cap=600s leg_cap=0s overrides=0 exact=0 state=')
        stream_row = ('SHARD row probe-a rc=0 pass=1 fail=0 detail=PASS 1/1 '
                      'suite=PASS 1/1 crit=1 0.4s')
        stream_closing = ('SHARD rc=0 scope=SHARD selected=2 executed=2 '
                          'green=2 criteria=2 crit_mismatch=0 elapsed=0.8s '
                          'crit_checked=2 crit_unchecked=0')
        stream_shapes = {
            'initial.log': stream_header + 'RUNNING\n',
            'killed.log': stream_header + 'RUNNING\n' + stream_row + '\n',
            'complete.log': (stream_header + 'COMPLETE\n' + stream_row + '\n'
                             + stream_closing + '\n'),
        }
        shape_same = {}
        for sname, sbody in stream_shapes.items():
            starget = os.path.join(stream_dir, sname)
            shard.stream_evidence(starget, sbody)
            shape_same[sname] = read_bytes(starget) == sbody.encode('utf-8')
        bare_body = (stream_header + 'RUNNING\n' + proof_a + '\n'
                     + stream_row + '\n')
        bare_target = os.path.join(stream_dir, 'bare.log')
        shard.stream_evidence(bare_target, bare_body)
        bare_disk = read_bytes(bare_target).decode('utf-8')
        once = [ln for ln in bare_disk.splitlines()
                if ln == 'CARRIED ' + proof_a]
        twice_body = 'PASS x\nCARRIED ' + proof_a + '\n'
        twice_target = os.path.join(stream_dir, 'twice.log')
        shard.stream_evidence(twice_target, twice_body)
        twice_disk = read_bytes(twice_target).decode('utf-8')
        killed_disk = read_bytes(os.path.join(stream_dir, 'killed.log'))
        killed_text = killed_disk.decode('utf-8')
        shard.QA_DIR = saved_shard_qa
        shard_src = read_text(os.path.join(ROOT, 'tools', 'battery_shard.py'))
        ok('AC-QALB14 the progress door marks a bare proof line, nothing else',
           len(once) == 1
           and proof_a in bare_disk
           and mod.count_bare_proofs(bare_disk) == 0
           and mod.count_carried_proofs(bare_disk) == 1
           and len(bare_disk.encode('utf-8'))
           == len(bare_body.encode('utf-8')) + 8
           and all(shape_same.values())
           and twice_disk == twice_body
           and killed_disk.endswith(b'\n')
           and len([ln for ln in killed_text.splitlines()
                    if ln.startswith('SHARD row ')]) == 1
           and 'state=RUNNING' in killed_text
           and 'SHARD rc=' not in killed_text
           and shard_src.count('mark_carried_proofs(') == 1
           and shard_src.count('os.fsync(') == 1
           and shard_src.count(
               'open(path, "w", encoding="utf-8", newline="\\n")') == 1
           and all(ord(ch) < 128 for ch in shard_src),
           'once=%d kept=%s bare=%d carried=%d plus8=%s shapes=%s idem=%s '
           'half_rows=%d half_nl=%s mark_sites=%d fsync=%d open=%d'
           % (len(once), proof_a in bare_disk,
              mod.count_bare_proofs(bare_disk),
              mod.count_carried_proofs(bare_disk),
              len(bare_disk.encode('utf-8'))
              == len(bare_body.encode('utf-8')) + 8,
              all(shape_same.values()), twice_disk == twice_body,
              len([ln for ln in killed_text.splitlines()
                   if ln.startswith('SHARD row ')]),
              killed_disk.endswith(b'\n'),
              shard_src.count('mark_carried_proofs('),
              shard_src.count('os.fsync('),
              shard_src.count(
                  'open(path, "w", encoding="utf-8", newline="\\n")')))
        # ---- AC-QALB15: a suffixless write is refused and lands nothing ----
        # R3213: measured before this guard, qa/NAME without .log landed in the
        # healthy dialect while every reader skipped it by construction - the
        # census and the pre-commit gate enumerate endswith(".log") only, and
        # the closeout files= count reads the census line. Three shapes are
        # refused and one control lands, so the guard is proved to bite and
        # not to over-bite; case matters, because .LOG is enumerated by none.
        suffix_dir = os.path.join(world, 'suffix')
        os.makedirs(suffix_dir)
        bad_shapes = ['plain-R3213', 'run-R3213.log-run2', 'upper-R3213.LOG']
        refused_suffix = []
        for bad in bad_shapes:
            try:
                quiet(mod.do_write, bad, b'x\n', directory=suffix_dir)
                refused_suffix.append(False)
            except ValueError as exc:
                refused_suffix.append('name must end with .log' in str(exc))
        after_bad = sorted(os.listdir(suffix_dir))
        rc_suffix, out_suffix = quiet(mod.do_write, 'ok-R3213.log', b'x\n',
                                      directory=suffix_dir)
        after_good = sorted(os.listdir(suffix_dir))
        ok('AC-QALB15 a suffixless name is refused and writes no file',
           all(refused_suffix) and after_bad == [] and rc_suffix == 0
           and 'VERDICT PASS' in out_suffix
           and after_good == ['ok-R3213.log'],
           'refused=%s landed=%s good_rc=%d good_files=%s'
           % (refused_suffix, after_bad, rc_suffix, after_good))

        # ---- AC-QALB16: the reader face stays open and the law stays one ---
        # The suffixless artifact already on disk must remain readable, and the
        # two shipping enumeration faces must still filter *.log - so the
        # writer now refuses exactly the set the readers skip instead of
        # growing a second, stricter law of its own.
        saved_qa = mod.QA
        try:
            mod.QA = suffix_dir
            with io.open(os.path.join(suffix_dir, 'legacy-R3213'), 'wb') as fh:
                fh.write(b'PASS x\n')
            rc_leg, out_leg = quiet(mod.do_check, 'legacy-R3213')
        finally:
            mod.QA = saved_qa
        live_legacy = os.path.join(QA_DIR, 'round-R2835-closeout')
        rc_live, out_live = quiet(mod.do_check, 'round-R2835-closeout')
        gate_src = read_text(os.path.join(ROOT, 'tools', 'hooks',
                                          'pre_commit_gate.py'))
        census_src = read_text(os.path.join(ROOT, 'src', 'os',
                                            'qa_writer_census.py'))
        ok('AC-QALB16 --check still reads a suffixless name; readers unchanged',
           rc_leg == 0 and 'dialect=' in out_leg
           and os.path.isfile(live_legacy)
           and rc_live in (0, 2) and 'dialect=' in out_live
           and 'endswith(".log")' in gate_src
           and census_src.count('endswith(".log")') >= 3,
           'fixture_rc=%d live_rc=%d gate_has_filter=%s census_sites=%d'
           % (rc_leg, rc_live, 'endswith(".log")' in gate_src,
              census_src.count('endswith(".log")')))

        # ---- AC-QALB17: the shipped examples teach the lawful shape --------
        # A refusal nobody documents only moves the same mistake into a
        # traceback. Every name a shipped usage example shows must end with
        # .log; the --check examples are exempt on purpose, because that face
        # deliberately keeps reading any flat name.
        tool_doc = read_text(TOOL)
        shard_doc = read_text(os.path.join(ROOT, 'tools', 'battery_shard.py'))
        usage_names = []
        for line in tool_doc.splitlines():
            stripped = line.strip()
            if not stripped.startswith('python tools/qa_log.py'):
                continue
            if '--check' in stripped or '--selftest' in stripped:
                continue
            for token in stripped.split()[2:]:
                if token.startswith('--') or token.startswith('#'):
                    continue
                usage_names.append(token)
                break
        evidence_names = re.findall(
            r'--evidence[ =]+(\S+)', '\n'.join(shard_doc.splitlines()[:40]))
        ok('AC-QALB17 shipped usage examples name .log files only',
           bool(usage_names) and bool(evidence_names)
           and all(n.endswith('.log') for n in usage_names)
           and all(n.endswith('.log') for n in evidence_names),
           'usage=%s evidence=%s' % (usage_names, evidence_names))

        # ---- AC-QALB18: the in-place door refuses a bad name or a bad place --
        # R3214: stream_evidence takes a FULL path, so a direct caller could
        # land qa/NAME (skipped by every reader) or any path outside qa/.
        # Measured before the guard over private temp: both landed 141 sane
        # bytes, and only the suffixless case was invisible to --check NAME.log.
        def live_qa_digest():
            rows = {}
            for name in sorted(os.listdir(QA_DIR)):
                p = os.path.join(QA_DIR, name)
                if not os.path.isfile(p):
                    continue
                raw = read_bytes(p)
                rows[name] = (len(raw), hashlib.sha256(raw).hexdigest()[:16])
            return rows

        live_before = live_qa_digest()
        door_dir = os.path.join(world, 'door')
        os.makedirs(door_dir)
        shard.QA_DIR = door_dir
        door_cases = [
            ('suffixless', os.path.join(door_dir, 'NAME')),
            ('outside', os.path.join(world, 'outside', 'x.log')),
            ('traversal', os.path.join(door_dir, '..', 'escape.log')),
        ]
        door_verdicts = []
        for label, target in door_cases:
            try:
                shard.stream_evidence(target, stream_shapes['initial.log'])
                door_verdicts.append((label, 'LANDED'))
            except (ValueError, shard.Refuse) as exc:
                door_verdicts.append((label, str(exc)))
        door_files = sorted(os.listdir(door_dir))
        escaped = [p for p in (os.path.join(world, 'outside', 'x.log'),
                               os.path.join(world, 'escape.log'))
                   if os.path.exists(p)]
        shard.stream_evidence(os.path.join(door_dir, 'control.log'),
                              stream_shapes['initial.log'])
        control_ok = (read_bytes(os.path.join(door_dir, 'control.log'))
                      == stream_shapes['initial.log'].encode('utf-8'))
        shard.QA_DIR = saved_shard_qa
        verdict = dict(door_verdicts)
        ok('AC-QALB18 the in-place door refuses a suffixless name and a path '
           'outside qa/, and lands nothing',
           'name must end with .log' in verdict.get('suffixless', '')
           and verdict.get('outside', '').startswith('E_STREAM_PATH')
           and verdict.get('traversal', '').startswith('E_STREAM_PATH')
           and door_files == [] and escaped == [] and control_ok,
           'verdicts=%s door_files=%s escaped=%s control=%s'
           % (door_verdicts, door_files, escaped, control_ok))

        # ---- AC-QALB19: a lawful progress file keeps the AC-BSGB15 promise --
        shard_body = shard_src[shard_src.index('def stream_evidence('):]
        shard_body = shard_body[:shard_body.index('def do_check(')]
        door_call = shard_body.find('    _progress_name(path)\n')
        mark_call = shard_body.find('mark_carried_proofs(text)')
        killed_rows = [ln for ln in killed_text.splitlines()
                       if ln.startswith('SHARD row ')]
        ok('AC-QALB19 a lawful .log progress file is unchanged and a killed '
           'leg still leaves a readable RUNNING half',
           all(shape_same.values())
           and 'state=RUNNING' in killed_text
           and 'SHARD rc=' not in killed_text
           and killed_disk.endswith(b'\n')
           and len(killed_rows) == 1
           and door_call >= 0 and 0 <= door_call < mark_call
           and shard_src.count('qa_log.check_name(name)') == 1
           and shard_src.count('qa_log.check_log_suffix(name)') == 1
           and shard_src.count('os.fsync(') == 1
           and shard_src.count(
               'open(path, "w", encoding="utf-8", newline="\\n")') == 1,
           'shapes=%s running=%s closing=%s one_row=%d door=%d mark=%d '
           'sites=%d/%d/%d/%d'
           % (all(shape_same.values()), 'state=RUNNING' in killed_text,
              'SHARD rc=' not in killed_text, len(killed_rows), door_call,
              mark_call, shard_src.count('qa_log.check_name(name)'),
              shard_src.count('qa_log.check_log_suffix(name)'),
              shard_src.count('os.fsync('),
              shard_src.count(
                  'open(path, "w", encoding="utf-8", newline="\\n")')))

        # ---- AC-QALB20: no existing evidence byte moved --------------------
        # The arms above wrote only into private temp dirs; the live tree must
        # be identical byte for byte, and the one suffixless artifact already
        # on disk must still be there (the reader-side exemption R3213 kept).
        live_after = live_qa_digest()
        ok('AC-QALB20 the guard moves no existing qa/ byte',
           live_before == live_after
           and live_after.get('round-R2835-closeout') is not None,
           'files=%d stable=%s suffixless=%s'
           % (len(live_after), live_before == live_after,
              live_after.get('round-R2835-closeout')))
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
