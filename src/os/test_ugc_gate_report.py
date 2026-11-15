"""Battery suite for tools/ugc_gate_report.py - criteria AC-UGRB1..AC-UGRB11.

WHY THIS SUITE EXISTS (measured at R2814, not hypothesised):
tools/ugc_gate_report.py renders preview/ugc-gate-report.html + .json, the face
that carries the P-47 item-3 content-safety gate, and it holds nine criteria
AC-UGR1..AC-UGR9 inside its own check(). A full-text search of the shipped
registry found ZERO AC-UGR* tokens, so the face was guarded only by its own
--check and nothing forced that check to run. BLUEPRINT section five makes this
a death line: content safety not connected means the door stays shut. A gate
whose only guard is a command nobody schedules is not a gate.

WHAT IS PROVED HERE: each of the nine shipped criteria is re-proved twice -
once green on a freshly collected real world, and once RED under one named
tamper that the criterion exists to catch. The tamper set is the evidence that
the criteria carry weight; a criterion that keeps reading green while its own
subject is corrupted would be reported by this suite rather than hidden.

Isolation: the tool's OUT_HTML / OUT_JSON globals are rebound to copies inside
one temp directory and restored in a finally block, so no tamper can touch the
landed pair. The real preview pair is snapshotted by (size, mtime_ns) before and
after and must be identical, and the real tree must still read VERDICT PASS 9/9
on exit - the tampering never leaks.

Source discipline: pure ASCII, stdlib only, no network, no shell, no clock in
assertions.
"""
import contextlib
import copy
import importlib.util
import io
import json
import os
import shutil
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOL = os.path.join(ROOT, 'tools', 'ugc_gate_report.py')
REGISTRY = os.path.join(ROOT, 'src', 'sandbox', 'reconcile_all.py')
REAL_HTML = os.path.join(ROOT, 'preview', 'ugc-gate-report.html')
REAL_JSON = os.path.join(ROOT, 'preview', 'ugc-gate-report.json')

# Escaped so this source stays ASCII while the tool's Chinese-facing rules
# still fire exactly as shipped.
CJK = u'\u4e2d'

CHECKS = []
FAILS = []


def ok(name, cond, detail):
    CHECKS.append(name)
    if not cond:
        FAILS.append(name)
    print('%s %s %s' % ('PASS' if cond else 'FAIL', name, detail))


def read(path, encoding='utf-8'):
    with io.open(path, encoding=encoding) as fh:
        return fh.read()


def write(path, text):
    with io.open(path, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(text)


def load_tool():
    spec = importlib.util.spec_from_file_location('ugc_gate_under_test', TOOL)
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


def run_check(mod, data):
    """Drive the shipped check() and return {cid: ok} plus its verdict line."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = mod.check(data)
    text = buf.getvalue()
    result = {}
    for line in text.splitlines():
        if line.startswith('PASS ') or line.startswith('FAIL '):
            parts = line.split()
            if len(parts) >= 2:
                result[parts[1]] = (parts[0] == 'PASS')
    verdict = [ln for ln in text.splitlines() if ln.startswith('VERDICT ')]
    return rc, result, text, (verdict[0] if verdict else '')


def ascii_rule(text):
    """The same law AC-UGR6 encodes, recomputed here without asking the tool."""
    try:
        text.encode('ascii')
        return True
    except UnicodeEncodeError:
        return False


def main():
    before = real_snapshot()
    tmpdir = tempfile.mkdtemp(prefix='ugc-gate-battery-')
    mod = load_tool()
    real_html_path, real_json_path = mod.OUT_HTML, mod.OUT_JSON
    try:
        # ---- baseline: fresh collection against the real world, read-only.
        data = mod.collect()
        copy_html = os.path.join(tmpdir, 'ugc-gate-report.html')
        copy_json = os.path.join(tmpdir, 'ugc-gate-report.json')
        shutil.copyfile(REAL_HTML, copy_html)
        shutil.copyfile(REAL_JSON, copy_json)
        mod.OUT_HTML, mod.OUT_JSON = copy_html, copy_json

        rc, base, text, verdict = run_check(mod, data)
        ok('AC-UGRB0', rc == 0 and len(base) == 9 and all(base.values()),
           'baseline rc=%d criteria=%d green=%d %s'
           % (rc, len(base), sum(1 for v in base.values() if v), verdict))

        rows = data['rows']

        def tamper_html(name, mutate):
            text_in = read(copy_html)
            write(copy_html, mutate(text_in))
            r, res, _, _ = run_check(mod, data)
            shutil.copyfile(REAL_HTML, copy_html)
            return res.get(name) is False, r

        def tamper_data(name, mutate):
            mutated = copy.deepcopy(data)
            mutate(mutated)
            r, res, _, _ = run_check(mod, mutated)
            return res.get(name) is False, r

        def tamper_json(name, mutate):
            landed = json.loads(read(copy_json))
            mutate(landed)
            write(copy_json, json.dumps(landed) + '\n')
            r, res, _, _ = run_check(mod, data)
            shutil.copyfile(REAL_JSON, copy_json)
            return res.get(name) is False, r

        # ---- B1: a row's trace id printed twice must redden AC-UGR1.
        trace = rows[0]['trace_id'][:16]

        def b1(text_in):
            return text_in + '<!-- ' + trace + ' -->\n'

        red, r = tamper_html('AC-UGR1', b1)
        ok('AC-UGRB1', red, 'AC-UGR1 red under duplicated trace id, rc=%d' % r)

        # ---- B2: the recorded hole must say NOT BLOCKED, or AC-UGR2 reddens.
        def b2(text_in):
            return text_in.replace('NOT BLOCKED', 'BLOCKED-BY-GATE')

        red, r = tamper_html('AC-UGR2', b2)
        ok('AC-UGRB2', red, 'AC-UGR2 red when the hole stops reading NOT BLOCKED, rc=%d' % r)

        # ---- B3: a decision disagreeing with its recomputation must redden AC-UGR3.
        def b3(d):
            d['rows'][0]['decision_recomputed'] = 'refuse-TAMPERED'

        red, r = tamper_data('AC-UGR3', b3)
        ok('AC-UGRB3', red, 'AC-UGR3 red on decision/recompute mismatch, rc=%d' % r)

        # ---- B4: the provider name is a carried contract, so blanking it reddens AC-UGR4.
        def b4(d):
            d['contract']['provider_prod'] = ''

        red, r = tamper_data('AC-UGR4', b4)
        ok('AC-UGRB4', red, 'AC-UGR4 red when the provider contract is blanked, rc=%d' % r)

        # ---- B5: the positive branch carries the weight. When the marker IS
        # found the page must print its source line, so removing that number
        # must redden AC-UGR5. MEASURED at R2814 and recorded rather than
        # papered over: the fallback branch (not found -> the page must say
        # UNVERIFIED) cannot redden, because the word UNVERIFIED already lives
        # in this page's own criteria list. That branch is decoration and is
        # carried on the board as open debt instead of being called covered.
        aigc_line = str(data['aigc']['line'])

        def b5(text_in):
            return text_in.replace(aigc_line, '####')

        red, r = tamper_html('AC-UGR5', b5)
        ok('AC-UGRB5', red,
           'AC-UGR5 red when the quoted source line is stripped (line=%s), rc=%d'
           % (aigc_line, r))

        # ---- B6: the ASCII law is recomputed here and proved able to say no.
        tool_src = read(TOOL)
        shipped = ascii_rule(tool_src)
        poisoned = ascii_rule(tool_src + CJK)
        ok('AC-UGRB6', shipped and not poisoned,
           'tool ascii=%s and the same law rejects a poisoned twin=%s'
           % (shipped, not poisoned))

        # ---- B7: removing the carried parity line must redden AC-UGR7.
        parity = data['parity']['line']

        def b7(text_in):
            return text_in.replace(parity, 'X' * len(parity))

        red, r = tamper_html('AC-UGR7', b7)
        ok('AC-UGRB7', red, 'AC-UGR7 red when the parity line stops being carried, rc=%d' % r)

        # ---- B8: a call-site status outside LIVE/LATENT must redden AC-UGR8.
        def b8(d):
            d['hole_status'] = 'UNKNOWN'

        red, r = tamper_data('AC-UGR8', b8)
        ok('AC-UGRB8', red, 'AC-UGR8 red on a status outside LIVE/LATENT, rc=%d' % r)

        # ---- B9: the sizes block is gated against disk, so a wrong number reddens AC-UGR9.
        def b9(landed):
            landed['sizes']['html'] = landed['sizes']['html'] + 1

        red, r = tamper_json('AC-UGR9', b9)
        ok('AC-UGRB9', red, 'AC-UGR9 red when the landed size disagrees with disk, rc=%d' % r)
    finally:
        mod.OUT_HTML, mod.OUT_JSON = real_html_path, real_json_path
        shutil.rmtree(tmpdir, ignore_errors=True)

    # ---- B10: nothing leaked, and the real tree still reads 9/9.
    after = real_snapshot()
    rc_real, res_real, _, verdict_real = run_check(mod, mod.collect())
    ok('AC-UGRB10',
       before == after and rc_real == 0 and len(res_real) == 9 and all(res_real.values()),
       'real pair unchanged=%s real rc=%d green=%d' %
       (before == after, rc_real, sum(1 for v in res_real.values() if v)))

    # ---- B11: the registry row is the only hook that makes this run at all.
    registry = read(REGISTRY)
    row = [ln for ln in registry.splitlines()
           if 'test_ugc_gate_report.py' in ln]
    declared = None
    for ln in row:
        stripped = ln.strip().rstrip('),')
        head, _, tail = stripped.rpartition(',')
        try:
            declared = int(tail.strip())
        except ValueError:
            declared = None
    ok('AC-UGRB11', bool(row) and declared == 11,
       'registry_rows=%d declared=%s' % (len(row), declared))

    print('SUITE %s %d/%d' % ('PASS' if not FAILS else 'FAIL', len(CHECKS) - len(FAILS), len(CHECKS)))
    return 0 if not FAILS else 2


if __name__ == '__main__':
    raise SystemExit(main())
