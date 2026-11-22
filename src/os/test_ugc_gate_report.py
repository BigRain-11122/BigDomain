"""Battery suite for tools/ugc_gate_report.py - criteria AC-UGRB0..AC-UGRB19.

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
import re
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
        ok('AC-UGRB0', rc == 0 and len(base) == 14 and all(base.values()),
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

        # ---- B12: the R3235 change itself must be proved both ways. Moving a
        # line number inside the same file has NO safety meaning (frontdoor.py
        # is edited most rounds; the old exact file:line pin reddened this face
        # on every edit above the site), so AC-UGR8 must stay green.
        def move_lines(d):
            d['call_sites'] = [
                s.rsplit(':', 1)[0] + ':%d' % (int(s.rsplit(':', 1)[1]) + 18)
                for s in d['call_sites']]

        moved = copy.deepcopy(data)
        move_lines(moved)
        r12, res12, _, _ = run_check(mod, moved)
        ok('AC-UGRB12', res12.get('AC-UGR8') is True,
           'AC-UGR8 stays green when only line numbers move (rc=%d)' % r12)

        # ---- B13: the safety event it exists for must still redden it: a
        # constructing file the landed face never names.
        def b13(d):
            d['call_sites'] = d['call_sites'] + ['src/sandbox/new_door.py:12']

        red, r = tamper_data('AC-UGR8', b13)
        ok('AC-UGRB13', red,
           'AC-UGR8 red when a constructing file is not named on the face, rc=%d' % r)
        # ---- B14..B16: the READER of the site set (R3237). The substring scan
        # this criterion used to stand on invented two sites out of a docstring
        # and a comment, and dropped a construction written on a `def` line.
        # Proven in private worlds so the live tree is never touched.
        def world_scan(files):
            world = tempfile.mkdtemp(prefix='ugc-gate-reader-')
            sandbox = os.path.join(world, 'src', 'sandbox')
            os.makedirs(sandbox)
            for fname, body in files.items():
                with io.open(os.path.join(sandbox, fname), 'w',
                             encoding='utf-8', newline='\n') as fh:
                    fh.write(body)
            real_root = mod.ROOT
            mod.ROOT = world
            try:
                return mod.direct_call_sites()
            finally:
                mod.ROOT = real_root
                shutil.rmtree(world, ignore_errors=True)

        prose_hits, _ = world_scan({
            'alpha.py': (
                '"""Alpha.\n\n'
                'Example that MUST refuse: SecGate([], []) - prose, not a door.\n'
                '"""\n'
                '# historical note: SecGate([], []) used to pass here\n'
                'def clean(value):\n'
                '    return value\n'
            ),
        })
        ok('AC-UGRB14', prose_hits == [],
           'a name in prose is not a construction: hits=%s' % (prose_hits,))

        def_hits, _ = world_scan({
            'beta.py': 'def make_gate(w1, w2): return build(SecGate(w1, w2))\n',
        })
        ok('AC-UGRB15', def_hits == ['src/sandbox/beta.py:1'],
           'a construction sharing a def line is counted: hits=%s' % (def_hits,))

        alias_hits, _ = world_scan({
            'gamma.py': ('from sec_gate import SecGate as Ctor\n'
                         'gate = Ctor([], [])\n'),
            'delta.py': ('import sec_gate as sg\n'
                         'Ctor = sg.SecGate\n'
                         'gate = Ctor([], [])\n'),
        })
        ok('AC-UGRB16',
           alias_hits == ['src/sandbox/delta.py:3', 'src/sandbox/gamma.py:2'],
           'one-level module aliases are followed: hits=%s' % (alias_hits,))

        # ---- B18/B19: the getattr spelling (R3238). The page used to say a
        # package re-export was invisible; measured, it is visible, and the one
        # spelling that really was invisible at the alias table was a literal
        # getattr. B18 buys the door, B19 buys the boundary: an undecidable
        # form must NOT be counted, or the file set would accuse innocent files.
        getattr_hits, _ = world_scan({
            'epsilon.py': ('import sec_gate as sg\n'
                           'Door = getattr(sg, "SecGate")\n'
                           'gate = Door([], [])\n'),
        })
        ok('AC-UGRB18', getattr_hits == ['src/sandbox/epsilon.py:3'],
           'a literal getattr alias is counted: hits=%s' % (getattr_hits,))

        dynamic_body = ('import sec_gate as sg\n'
                        'Door = getattr(sg, name)\n'
                        'gate = Door([], [])\n'
                        'other = getattr(sg, "SecGate", None)\n'
                        'gate2 = other([], [])\n')
        dynamic_hits, _ = world_scan({'zeta.py': dynamic_body})
        ok('AC-UGRB19', dynamic_hits == [],
           'a getattr with a non-literal or defaulted class name is not counted: hits=%s'
           % (dynamic_hits,))

        # ---- B20: the reader now has its own --check judge (R3239). A reader
        # degraded to bare names only - the exact form measured blind in
        # qa/probe-R3239.log, where 4 sites collapsed to 2 against a landed page
        # naming 3 files - must redden AC-UGR12 while AC-UGR8 stays green. One
        # arm, both halves: the new criterion catches what the old one cannot.
        attr = re.compile(r'\b[A-Za-z_]\w*\s*\.\s*SecGate\s*\(')

        def attr_blind(sources=None):
            world = sources if sources is not None else mod._sandbox_sources()
            texts = dict(world)
            hits, skipped = orig_hits(sources=world)
            kept = []
            for hit in hits:
                rel, ln = hit.rsplit(':', 1)
                line = texts[rel].splitlines()[int(ln) - 1]
                if not attr.search(line):
                    kept.append(hit)
            return kept, skipped

        orig_hits = mod.direct_call_sites
        mod.direct_call_sites = attr_blind
        try:
            rc20, res20, _text20, _v20 = run_check(mod, data)
        finally:
            mod.direct_call_sites = orig_hits
        ok('AC-UGRB20',
           res20.get('AC-UGR12') is False and res20.get('AC-UGR8') is True,
           'degraded reader: AC-UGR12=%s (must be FAIL) AC-UGR8=%s (stays PASS) rc=%d'
           % (res20.get('AC-UGR12'), res20.get('AC-UGR8'), rc20))

        # ---- B21/B22: the walk's two sides are graded by two criteria and do
        # not impersonate each other (R3240). Measured in qa/probe-R3240.log: a
        # real door written at src/sandbox/test_gate_factory.py, and the same
        # bytes under data/, each left the whole check VERDICT PASS, while the
        # same door at a visible path reddened AC-UGR8. B21 buys the new side,
        # B22 proves it does not swallow the old one's job.
        def b21(d):
            slot = d['refused'].setdefault(
                'test_prefix', {'files': 0, 'doors': [], 'unparsed': []})
            slot['doors'] = list(slot.get('doors') or []) + [
                'src/sandbox/test_named_door.py']

        mutated21 = copy.deepcopy(data)
        b21(mutated21)
        r21, res21, _t21, _v21 = run_check(mod, mutated21)
        ok('AC-UGRB21', res21.get('AC-UGR13') is False and res21.get('AC-UGR8') is True,
           'a refused door not named on the face: AC-UGR13=%s (must be FAIL) '
           'AC-UGR8=%s (stays PASS) rc=%d'
           % (res21.get('AC-UGR13'), res21.get('AC-UGR8'), r21))

        def b22(d):
            d['call_sites'] = list(d['call_sites']) + ['src/sandbox/visible_door.py:7']

        mutated22 = copy.deepcopy(data)
        b22(mutated22)
        r22, res22, _t22, _v22 = run_check(mod, mutated22)
        ok('AC-UGRB22', res22.get('AC-UGR8') is False and res22.get('AC-UGR13') is True,
           "a visible door is AC-UGR8's job and leaves AC-UGR13 green: "
           'AC-UGR8=%s (must be FAIL) AC-UGR13=%s rc=%d'
           % (res22.get('AC-UGR8'), res22.get('AC-UGR13'), r22))

        # ---- B23: the two structural closes, in private worlds. (a) `data` is
        # no longer a skipped name, so a door there is READ - measured before
        # the change as the ARM-B blindness. (b) a test_-prefixed door stays out
        # of the site set but is NAMED by the refused census, which is what makes
        # B21's event visible at all.
        def world_tree(files):
            world = tempfile.mkdtemp(prefix='ugc-gate-walk-')
            for rel, body in files.items():
                path = os.path.join(world, *rel.split('/'))
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with io.open(path, 'w', encoding='utf-8', newline='\n') as fh:
                    fh.write(body)
            return world

        data_world = world_tree({
            'src/sandbox/data/hidden_gate.py':
                'from lobby.sec_gate import SecGate\nG = SecGate([], [])\n',
            'src/sandbox/plain.py': 'x = 1\n',
        })
        test_world = world_tree({
            'src/sandbox/test_hidden.py':
                'from lobby.sec_gate import SecGate\nG = SecGate([], [])\n',
            'src/sandbox/.venv/lib/vendor.py':
                'from lobby.sec_gate import SecGate\nG = SecGate([], [])\n',
        })
        real_root = mod.ROOT
        try:
            mod.ROOT = data_world
            data_hits, _ = mod.direct_call_sites()
            mod.ROOT = test_world
            test_hits, _ = mod.direct_call_sites()
            census = mod.refused_census()
        finally:
            mod.ROOT = real_root
            shutil.rmtree(data_world, ignore_errors=True)
            shutil.rmtree(test_world, ignore_errors=True)
        ok('AC-UGRB23',
           data_hits == ['src/sandbox/data/hidden_gate.py:2']
           and test_hits == []
           and (census.get('test_prefix') or {}).get('doors')
           == ['src/sandbox/test_hidden.py']
           and (census.get('vendor_dir') or {}).get('files') == 1
           and (census.get('vendor_dir') or {}).get('doors') == [],
           'data door read=%s test door hits=%s refused doors=%s vendor files=%s'
           % (data_hits, test_hits,
              (census.get('test_prefix') or {}).get('doors'),
              (census.get('vendor_dir') or {}).get('files')))

        # ---- B24/B25: the reader's unreadable side is graded (R3241). Measured
        # in qa/probe-R3241.log: a broken frontdoor.py moved 4 sites in 3 files
        # to 3 sites in 2 files while the whole check still read PASS 11/11, and
        # a ghost unparsed name the page could never carry changed nothing. B24
        # is the data-level split (old criterion blind, new one red); B25 renders
        # a private world where the broken source IS named on the page and proves
        # that naming alone does not buy green.
        def b24(d):
            victim = 'src/sandbox/frontdoor.py'
            d['call_sites'] = [s for s in d['call_sites']
                               if not s.startswith(victim + ':')]
            d['unparsed'] = [victim]

        mutated24 = copy.deepcopy(data)
        b24(mutated24)
        r24, res24, _t24, _v24 = run_check(mod, mutated24)
        ok('AC-UGRB24',
           res24.get('AC-UGR14') is False and res24.get('AC-UGR8') is True,
           'a constructing file dropped as unparsed: AC-UGR14=%s (must be FAIL) '
           'AC-UGR8=%s (stays PASS) rc=%d'
           % (res24.get('AC-UGR14'), res24.get('AC-UGR8'), r24))

        broken_world = world_tree({
            'src/sandbox/visible.py':
                'from lobby.sec_gate import SecGate\nG = SecGate([], [])\n',
            'src/sandbox/broken_gate.py':
                'from lobby.sec_gate import SecGate\nG = SecGate([], []\n',
        })
        real_root = mod.ROOT
        real_html, real_json = mod.OUT_HTML, mod.OUT_JSON
        try:
            mod.ROOT = broken_world
            mod.OUT_HTML = os.path.join(broken_world, 'out.html')
            mod.OUT_JSON = os.path.join(broken_world, 'out.json')
            mod.write_outputs(mod.collect())
            with io.open(mod.OUT_HTML, 'r', encoding='utf-8') as fh:
                bhtml = fh.read()
            rc25, res25, _t25, _v25 = run_check(mod, mod.collect())
        finally:
            mod.ROOT = real_root
            mod.OUT_HTML, mod.OUT_JSON = real_html, real_json
            shutil.rmtree(broken_world, ignore_errors=True)
        ok('AC-UGRB25',
           res25.get('AC-UGR14') is False
           and res25.get('AC-UGR8') is True
           and 'src/sandbox/broken_gate.py' in bhtml
           and 'src/sandbox/visible.py' in bhtml,
           'named yet still red: on_page=%s AC-UGR14=%s (must be FAIL) '
           'AC-UGR8=%s rc=%d'
           % ('src/sandbox/broken_gate.py' in bhtml, res25.get('AC-UGR14'),
              res25.get('AC-UGR8'), rc25))

        # ---- B26/B27/B28: refusal by OWNERSHIP and the vendor mention census
        # (R3242). Measured in qa/probe-R3242.log: of 455 refused vendor .py
        # files, zero textually mention the gate (0.31 s to read all), and the
        # two under ygo-poc are a bundled Go toolchain (data/toolchain/goroot,
        # untracked), so the directory NAME decided nothing. B26: a mention in a
        # vendor tree is counted and named, and is never a door. B27: the same
        # door bytes are invisible under the old name-skip and read under the
        # ownership rule, while a toolchain door stays refused. B28: the printed
        # mention count is graded, so an unprinted count reddens AC-UGR13 while
        # AC-UGR8 (which only sees read files) stays green.
        mention_world = world_tree({
            'src/sandbox/.venv/lib/vendor_mention.py':
                'DOC = "SecGate builds the gate"\n',
            'src/sandbox/plain.py': 'x = 1\n',
        })
        real_root = mod.ROOT
        try:
            mod.ROOT = mention_world
            m_hits, _m_skip = mod.direct_call_sites()
            m_census = mod.refused_census()
        finally:
            mod.ROOT = real_root
            shutil.rmtree(mention_world, ignore_errors=True)
        v_slot = m_census.get('vendor_dir') or {}
        ok('AC-UGRB26',
           m_hits == []
           and v_slot.get('files') == 1
           and v_slot.get('doors') == []
           and v_slot.get('mentions') == ['src/sandbox/.venv/lib/vendor_mention.py'],
           'vendor mention: hits=%s files=%s doors=%s mentions=%s (a mention is '
           'not a construction)'
           % (m_hits, v_slot.get('files'), v_slot.get('doors'),
              v_slot.get('mentions')))

        own_world = world_tree({
            'src/sandbox/ygo-poc/mypoc_gate.py':
                'from lobby.sec_gate import SecGate\nG = SecGate([], [])\n',
            'src/sandbox/ygo-poc/data/toolchain/goroot/tool_gate.py':
                'from lobby.sec_gate import SecGate\nG = SecGate([], [])\n',
        })
        real_root = mod.ROOT
        old_vendor_dirs = mod.VENDOR_DIRS
        try:
            mod.ROOT = own_world
            new_hits, _new_skip = mod.direct_call_sites()
            mod.VENDOR_DIRS = tuple(old_vendor_dirs) + ('ygo-poc',)
            old_hits, _old_skip = mod.direct_call_sites()
        finally:
            mod.VENDOR_DIRS = old_vendor_dirs
            mod.ROOT = real_root
            shutil.rmtree(own_world, ignore_errors=True)
        ok('AC-UGRB27',
           new_hits == ['src/sandbox/ygo-poc/mypoc_gate.py:2']
           and old_hits == [],
           'ownership: project-local ygo-poc door read=%s under the shipped set, '
           'read=%s under the old name-skip, and the toolchain door stayed refused'
           % (new_hits, old_hits))

        def b28(d):
            slot = d['refused'].setdefault(
                'vendor_dir', {'files': 0, 'doors': [], 'unparsed': [], 'mentions': []})
            slot['mentions'] = ['src/sandbox/.venv/lib/ghost_vendor.py']

        mutated28 = copy.deepcopy(data)
        b28(mutated28)
        r28, res28, _t28, _v28 = run_check(mod, mutated28)
        ok('AC-UGRB28',
           res28.get('AC-UGR13') is False and res28.get('AC-UGR8') is True,
           'an unprinted vendor mention reddens AC-UGR13=%s (must be FAIL) while '
           'AC-UGR8=%s stays PASS rc=%d'
           % (res28.get('AC-UGR13'), res28.get('AC-UGR8'), r28))

        # ---- B29/B30/B31: refusal is judged by OWNERSHIP EVIDENCE, with the
        # name rule kept as a NAMED fallback (R3243). Measured in
        # qa/probe-R3243.log: zero .py files under any of the five skip names are
        # git tracked today, and a gate written under OUR OWN
        # src/sandbox/mypoc/toolchain/ answered zero sites while the same bytes
        # one level up were seen. B29 proves the evidence closes that hole while
        # an untracked sibling stays refused; B30 proves the fallback is not
        # silent (a world git cannot answer for keeps today's behaviour and the
        # page must say `name`); B31 proves the printed rule/count/names are
        # graded, and that AC-UGR13 does not inherit the job.
        own_vendor = world_tree({
            'src/sandbox/mypoc/toolchain/door.py':
                'from lobby.sec_gate import SecGate\nG = SecGate([], [])\n',
            'src/sandbox/mypoc/toolchain/plain.py': 'x = 1\n',
        })
        real_root = mod.ROOT
        real_tracked = mod._tracked_sources
        try:
            mod.ROOT = own_vendor
            mod._tracked_sources = lambda: {'src/sandbox/mypoc/toolchain/door.py'}
            e_hits, _e_skip = mod.direct_call_sites()
            e_census = mod.refused_census()
            _e_read, _e_ref, e_owned, _e_dec = mod._sandbox_walk()
            mod._tracked_sources = lambda: None
            n_hits, _n_skip = mod.direct_call_sites()
            n_census = mod.refused_census()
            _n_read, _n_ref, n_owned, _n_dec = mod._sandbox_walk()
        finally:
            mod._tracked_sources = real_tracked
            mod.ROOT = real_root
            shutil.rmtree(own_vendor, ignore_errors=True)
        e_vendor = e_census.get('vendor_dir') or {}
        n_vendor = n_census.get('vendor_dir') or {}
        ok('AC-UGRB29',
           e_hits == ['src/sandbox/mypoc/toolchain/door.py:2']
           and e_owned == ['src/sandbox/mypoc/toolchain/door.py']
           and e_vendor.get('files') == 1
           and e_vendor.get('doors') == []
           and e_vendor.get('mentions') == [],
           'ownership evidence: gate under our own toolchain/ read=%s owned=%s '
           'refused_files=%s (the untracked sibling stays refused)'
           % (e_hits, e_owned, e_vendor.get('files')))
        ok('AC-UGRB30',
           n_hits == [] and n_owned == [] and n_vendor.get('files') == 2,
           'name fallback where git cannot answer: read=%s owned=%s refused_files=%s '
           '(today behaviour kept, and the face must say name)'
           % (n_hits, n_owned, n_vendor.get('files')))

        def b31(d):
            d['vendor_owned'] = ['src/sandbox/.venv/lib/ghost_owned.py']

        mutated31 = copy.deepcopy(data)
        b31(mutated31)
        r31, res31, _t31, _v31 = run_check(mod, mutated31)
        ok('AC-UGRB31',
           res31.get('AC-UGR15') is False and res31.get('AC-UGR13') is True,
           'an unprinted owned path reddens AC-UGR15=%s (must be FAIL) while '
           'AC-UGR13=%s stays PASS rc=%d'
           % (res31.get('AC-UGR15'), res31.get('AC-UGR13'), r31))

        # ---- B32/B33/B34: where git CANNOT answer, ownership falls back to a
        # SECOND named evidence (R3244). Measured in qa/probe-R3244.log: in a
        # world with no .git, a gate of OURS beside an installed package was
        # refused by name and answered zero sites, while the two RECORDs under
        # .venv list all 453 of its .py files. B32 proves RECORD membership
        # decides in both directions inside one root (listed refused, unlisted
        # read); B33 proves a root with no marker still says `name`; B34 proves
        # the printed per-rule counts are graded and AC-UGR15 does not inherit
        # the job.
        marker_world = world_tree({
            'src/sandbox/.venv/pip/core/vendor.py': 'x = 1\n',
            'src/sandbox/.venv/pip/pip-1.0.dist-info/METADATA': 'Name: pip\n',
            'src/sandbox/.venv/pip/pip-1.0.dist-info/RECORD':
                'core/vendor.py,sha256=aa,12\n',
            'src/sandbox/.venv/our_gate.py':
                'from lobby.sec_gate import SecGate\nG = SecGate([], [])\n',
        })
        no_marker_world = world_tree({
            'src/sandbox/mypoc/toolchain/door.py':
                'from lobby.sec_gate import SecGate\nG = SecGate([], [])\n',
            'src/sandbox/mypoc/toolchain/plain.py': 'x = 1\n',
        })
        try:
            mod.ROOT = marker_world
            mod._tracked_sources = lambda: None
            m_hits, _m_skip = mod.direct_call_sites()
            m_census = mod.refused_census()
            _m_read, _m_ref, m_owned, m_dec = mod._sandbox_walk()
            mod.ROOT = no_marker_world
            nm_hits, _nm_skip = mod.direct_call_sites()
            nm_census = mod.refused_census()
            _nm_read, _nm_ref, nm_owned, nm_dec = mod._sandbox_walk()
        finally:
            mod._tracked_sources = real_tracked
            mod.ROOT = real_root
            shutil.rmtree(marker_world, ignore_errors=True)
            shutil.rmtree(no_marker_world, ignore_errors=True)
        m_vendor = m_census.get('vendor_dir') or {}
        nm_vendor = nm_census.get('vendor_dir') or {}
        ok('AC-UGRB32',
           m_hits == ['src/sandbox/.venv/our_gate.py:2']
           and m_owned == ['src/sandbox/.venv/our_gate.py']
           and m_vendor.get('files') == 1
           and dict(m_dec) == {'src/sandbox/.venv/pip/core/vendor.py': 'marker',
                               'src/sandbox/.venv/our_gate.py': 'marker'},
           'RECORD evidence, no git: read=%s owned=%s refused_files=%s decisions=%s '
           '(the unlisted file beside an installed package is READ)'
           % (m_hits, m_owned, m_vendor.get('files'), dict(m_dec)))
        ok('AC-UGRB33',
           nm_hits == [] and nm_owned == [] and nm_vendor.get('files') == 2
           and all(rule == 'name' for _p, rule in nm_dec),
           'no marker, no git: read=%s refused_files=%s decisions=%s '
           '(the name rule stays, and it is named)'
           % (nm_hits, nm_vendor.get('files'), dict(nm_dec)))

        def b34(d):
            d['vendor_decisions'] = {'evidence': 454, 'marker': 1, 'name': 0}

        mutated34 = copy.deepcopy(data)
        b34(mutated34)
        r34, res34, _t34, _v34 = run_check(mod, mutated34)
        ok('AC-UGRB34',
           res34.get('AC-UGR16') is False and res34.get('AC-UGR15') is True,
           'an unprinted marker count reddens AC-UGR16=%s (must be FAIL) while '
           'AC-UGR15=%s stays PASS rc=%d'
           % (res34.get('AC-UGR16'), res34.get('AC-UGR15'), r34))

        # ---- B17: the live tree must read the same site set as before the
        # reader changed (pure addition): three files, four constructions.
        live_hits, live_skipped = mod.direct_call_sites()
        live_files = sorted(set(s.rsplit(':', 1)[0] for s in live_hits))
        ok('AC-UGRB17',
           live_files == ['src/sandbox/frontdoor.py', 'src/sandbox/journey_demo.py',
                          'src/sandbox/lobby/msgsec_stub.py']
           and len(live_hits) == 4 and live_skipped == [],
           'live reader: files=%d sites=%d unparsed=%d'
           % (len(live_files), len(live_hits), len(live_skipped)))
    finally:
        mod.OUT_HTML, mod.OUT_JSON = real_html_path, real_json_path
        shutil.rmtree(tmpdir, ignore_errors=True)

    # ---- B10: nothing leaked, and the real tree still reads 9/9.
    after = real_snapshot()
    rc_real, res_real, _, verdict_real = run_check(mod, mod.collect())
    ok('AC-UGRB10',
       before == after and rc_real == 0 and len(res_real) == 14 and all(res_real.values()),
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
    ok('AC-UGRB11', bool(row) and declared == 35,
       'registry_rows=%d declared=%s' % (len(row), declared))

    law_verdict = "PASS" if not FAILS else "FAIL"
    print('SUITE %s %d/%d' % (law_verdict, len(CHECKS) - len(FAILS), len(CHECKS)))
    return 0 if not FAILS else 2


if __name__ == '__main__':
    raise SystemExit(main())
