"""Battery suite for tools/payment_gate_report.py - criteria AC-PAYGB1..AC-PAYGB11
plus AC-PGM1..AC-PGM3 (R3610: the import law resolves from disk, AC-PAYG1 stops
echoing the verdict, and the landed face owes a green --check).

R2860: the pinned range above grew twice (AC-PAYGB10/11 at R2817) while the
registry row moved only 9 -> 10, and this suite's own literal "declares 10"
agreed with the stale row rather than with its own inventory. The row now reads
eleven, which is what AC-PAYGB1..AC-PAYGB11 are (PAYGB9b/9c are sub-assertions
of 9, not criteria of their own), and the number is compared by the runner from
the declaration this suite prints at closeout, not echoed here.

AC-PAYGB1..AC-PAYGB9 were pinned in src/os/backlog.md at R2806 BEFORE this suite
existed, mapping one-to-one onto AC-PAYG1..AC-PAYG8 that the tool prints, plus
one gate-weight criterion of its own. The measured reason: all 690 registered
suites were searched for the eight AC-PAYG* tokens and found ZERO of them, so
the face that decides whether the 19.9 channel may be connected was guarded
only by its own --check.

This suite DRIVES the shipped src/sandbox/pay/adapters.py and pay/v3.py itself
and then compares its own recomputation against what the tool landed - a tool
that prints green while this suite recomputes red is a red suite.

Isolation: every render, check and tamper happens in the system temp dir. The
repo preview/payment-gate-report.{html,json} and pay/config.json are measured
by sha256 before and after and must be unchanged.

Source discipline: pure ASCII, stdlib only, no clock dependency in assertions,
no network, no shell.
"""
import ast
import contextlib
import hashlib
import importlib.util
import io
import json
import os
import re
import shutil
import sys
import tempfile
import time
import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOL = os.path.join(ROOT, 'tools', 'payment_gate_report.py')
PAY_DIR = os.path.join(ROOT, 'src', 'sandbox', 'pay')
CONFIG = os.path.join(PAY_DIR, 'config.json')
PREVIEW_HTML = os.path.join(ROOT, 'preview', 'payment-gate-report.html')
PREVIEW_JSON = os.path.join(ROOT, 'preview', 'payment-gate-report.json')
EXPORT_FACE = os.path.join(ROOT, 'docs', 'status-export.json')
REGISTRY = os.path.join(ROOT, 'src', 'sandbox', 'reconcile_all.py')
SERIAL = 'PUB_KEY_ID_R2806_SUITE'
FAILS = []
CHECKS = []


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


def digest(path):
    if not os.path.isfile(path):
        return 'absent'
    h = hashlib.sha256()
    with io.open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()[:16]


def stamp(path):
    st = os.stat(path)
    return (st.st_size, st.st_mtime_ns)


def load_tool():
    spec = importlib.util.spec_from_file_location('payg_under_test', TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_pay():
    if PAY_DIR not in sys.path:
        sys.path.insert(0, PAY_DIR)
    import adapters
    import v3
    return adapters, v3


def refusal(fn, adapters):
    """Return (adapter_error_raised, class_name, message)."""
    try:
        fn()
    except adapters.AdapterError as exc:
        return True, 'AdapterError', str(exc)
    except Exception as exc:
        return False, type(exc).__name__, str(exc)
    return False, 'none', 'accepted'


def main():
    started = time.time()
    world = tempfile.mkdtemp(prefix='paygb-')
    knowledge = {}
    pre_preview = (digest(PREVIEW_HTML), digest(PREVIEW_JSON))
    pre_export = stamp(EXPORT_FACE) if os.path.isfile(EXPORT_FACE) else None
    pre_cfg = digest(CONFIG)
    try:
        adapters, v3 = load_pay()
        mod = load_tool()
        cfg_src = read(CONFIG)
        cfg = json.loads(cfg_src)
        tool_src = read(TOOL)

        html = os.path.join(world, 'payment-gate-report.html')
        js = os.path.join(world, 'payment-gate-report.json')
        rc = mod.main(['--out', html, '--json', js])
        landed = json.loads(read(js))
        payload = landed

        # ---- AC-PAYGB1: both artifacts land, eight named criteria ----
        ids = [c['id'] for c in landed.get('criteria', [])]
        declared = [c[0] for c in mod.CHECKS]
        ok('AC-PAYGB1 both artifacts land non-empty with eight named criteria',
           rc == 0 and os.path.getsize(html) > 0 and os.path.getsize(js) > 0
           and len(ids) == 8 and ids == declared,
           'rc=%d html=%dB json=%dB ids=%s' % (rc, os.path.getsize(html),
                                               os.path.getsize(js),
                                               ','.join(ids)))

        # ---- AC-PAYGB2: two channels positive, recomputed here ----
        channels = adapters.from_config(cfg)
        pos = []
        for name in ('virtual', 'standard'):
            ch = channels[name]
            cb = ch.make_callback('order-R2806', 1990, 'nonce-%s' % name)
            good, cls, msg = refusal(lambda ch=ch, cb=cb: ch.verify(cb),
                                     adapters)
            pos.append((name, not good, cls, msg))
        accepted = [p for p in pos if p[1]]
        tool_pos = landed.get('channel_positive', [])
        ok('AC-PAYGB2 two shipped channels accept a signed callback (2/2)',
           len(accepted) == 2 and sorted(landed.get('channels_built', []))
           == ['standard', 'virtual']
           and len(tool_pos) == 2 and all(r.get('ok') for r in tool_pos),
           'built=%s accepted=%d/2 tool_rows=%d' % (
               ','.join(sorted(channels.keys())), len(accepted), len(tool_pos)))

        # ---- AC-PAYGB3: three legacy negatives refused by AdapterError ----
        ch = channels['virtual']
        base = ch.make_callback('order-R2806', 1990, 'nonce-neg')
        bad_sig = dict(base)
        bad_sig['sig'] = ('0' if base['sig'][0] != '0' else '1') + base['sig'][1:]
        past = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
            seconds=ch.ts_window + 100)
        legacy = []
        legacy.append(refusal(lambda: ch.verify(bad_sig), adapters))
        legacy.append(refusal(lambda: ch.verify(
            ch.make_callback('order-R2806', 1990, 'nonce-sgn',
                             signer='imposter')), adapters))
        legacy.append(refusal(lambda: ch.verify(
            ch.make_callback('order-R2806', 1990, 'nonce-ts',
                             ts_utc=past.strftime('%Y-%m-%dT%H:%M:%SZ'))),
            adapters))
        ok('AC-PAYGB3 three legacy negatives are refused as AdapterError (3/3)',
           all(r[0] and r[1] == 'AdapterError' for r in legacy)
           and len([r for r in landed.get('legacy_negative', [])
                    if r.get('ok')]) == 3,
           'refused=%d/3 classes=%s' % (
               len([r for r in legacy if r[0]]),
               ','.join(r[1] for r in legacy)))

        # ---- AC-PAYGB4: one V3 callback with four headers accepts ----
        spec = cfg['channels']['virtual']
        v3ch = v3.V3Channel('virtual-v3-r2806', spec['signer'],
                            spec['mock_key'],
                            int(spec.get('ts_window_seconds', 300)), [SERIAL])
        cb = v3ch.make_v3_callback('order-R2806', 1990, 'nonce-v3', serial=SERIAL)
        headers = cb['v3']['headers']
        need = ('Wechatpay-Serial', 'Wechatpay-Signature',
                'Wechatpay-Timestamp', 'Wechatpay-Nonce')
        present = sum(1 for h in need if str(headers.get(h, '')).strip())
        refused, cls, msg = refusal(lambda: v3ch.verify(cb), adapters)
        ok('AC-PAYGB4 one V3 callback with four headers verifies (1/1, 4/4)',
           (not refused) and present == 4
           and bool(landed.get('v3_positive', {}).get('ok')),
           'ok=%s headers=%d/4 tool=%s' % (
               not refused, present, landed.get('v3_positive', {}).get('ok')))

        # ---- AC-PAYGB5: four V3 negatives refused ----
        miss = json.loads(json.dumps(cb))
        del miss['v3']['headers']['Wechatpay-Signature']
        tampered = json.loads(json.dumps(cb))
        tampered['v3']['body'] = tampered['v3']['body'] + ' '
        stale = v3ch.make_v3_callback(
            'order-R2806', 1990, 'nonce-v3-ts', serial=SERIAL,
            ts_unix=int((datetime.datetime.now(datetime.timezone.utc)
                         - datetime.timedelta(seconds=v3ch.ts_window + 100))
                        .timestamp()))
        notpaid = v3ch.make_v3_callback('order-R2806', 1990, 'nonce-v3-np',
                                       serial=SERIAL, trade_state='NOTPAY')
        v3neg = []
        for payload_case in (miss, tampered, stale, notpaid):
            v3neg.append(refusal(
                lambda p=payload_case: v3ch.verify(p), adapters))
        notpay_msg = v3neg[3][2]
        ok('AC-PAYGB5 four V3 negatives refused, NOTPAY by trade_state (4/4)',
           all(r[0] and r[1] == 'AdapterError' for r in v3neg)
           and 'trade_state' in notpay_msg
           and len([r for r in landed.get('v3_negative', [])
                    if r.get('ok')]) == 4,
           'refused=%d/4 notpay_named=%s' % (
               len([r for r in v3neg if r[0]]), 'trade_state' in notpay_msg))

        # ---- AC-PAYGB6: the price is bound, not merely printed ----
        cfg_price = int(cfg['products']['pack_compute_19_9']['price_cent'])
        const = None
        for node in ast.parse(tool_src).body:
            if isinstance(node, ast.Assign):
                for tgt in node.targets:
                    if isinstance(tgt, ast.Name) and tgt.id == 'AMOUNT_CENT':
                        const = ast.literal_eval(node.value)
        row = next((p for p in landed.get('products', [])
                    if p['id'] == 'pack_compute_19_9'), None)
        ok('AC-PAYGB6 config price, tool constant and landed row agree',
           const == cfg_price and row is not None
           and row['price_cent'] == cfg_price and bool(row['needs_ceo']),
           'cfg=%s const=%s landed=%s needs_ceo=%s' % (
               cfg_price, const, row['price_cent'] if row else 'missing',
               row['needs_ceo'] if row else 'missing'))
        knowledge['cfg_price'] = cfg_price

        # ---- AC-PAYGB7: compliance carried verbatim, not paraphrased ----
        comp = cfg.get('compliance', {})
        displayed = landed.get('compliance', {})
        html_src = read(html)
        disc = comp.get('disclaimer', '')
        note = comp.get('note', '')
        ok('AC-PAYGB7 disclaimer is byte-equal to config and AIGC note rides along',
           bool(disc.strip()) and displayed.get('disclaimer', '') == disc
           and bool(displayed.get('aigc_marking_note', '').strip())
           and displayed.get('aigc_marking_note', '') == note
           and disc.strip()[:20] in html_src
           and note.strip()[:12] in html_src,
           'disc=%dB note=%dB verbatim=%s' % (
               len(disc.encode('utf-8')), len(note.encode('utf-8')),
               displayed.get('disclaimer', '') == disc))

        # ---- AC-PAYGB8: source purity on both files ----
        suite_src = read(os.path.abspath(__file__))
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
        # AC-PGM4 (R3610): one law for both files, resolved from disk - stdlib
        # or a module file under tools/, src/os/ or the pay sandbox. The
        # hand-kept whitelist this replaced had drifted from the shipped wiring
        # (board_face_landing) and was red against its own tool.
        def shipped(name):
            if name in sys.stdlib_module_names:
                return True
            for base in (os.path.join(ROOT, 'tools'),
                         os.path.join(ROOT, 'src', 'os'), PAY_DIR):
                if (os.path.isfile(os.path.join(base, name + '.py'))
                        or os.path.isdir(os.path.join(base, name))):
                    return True
            return False
        tool_extra = sorted(n for n in tool_imp if not shipped(n))
        suite_extra = sorted(n for n in suite_imp if not shipped(n))
        # A literal scan would match this block itself and the tool's own
        # guard, so the criterion is measured on USE: a banned module must not
        # be imported and must not be dereferenced.
        banned = {'socket', 'urllib', 'requests', 'http'}
        net_tool = sorted(tool_imp & banned) + re.findall(
            r'\b(?:socket|urllib|requests)\.\w', tool_src)
        net_suite = sorted(suite_imp & banned) + re.findall(
            r'\b(?:socket|urllib|requests)\.\w', suite_src)
        ascii_tool = all(ord(c) < 128 for c in tool_src)
        ascii_suite = all(ord(c) < 128 for c in suite_src)
        ok('AC-PAYGB8 both sources ASCII, resolved imports, zero network',
           ascii_tool and ascii_suite
           and not tool_extra and not suite_extra
           and not net_tool and not net_suite,
           'tool_imp=%s extra=%s net=%s ascii=%s/%s' % (
               ','.join(sorted(tool_imp)),
               ','.join(tool_extra + suite_extra),
               net_tool + net_suite, ascii_tool, ascii_suite))

        # ---- AC-PAYGB9: --check is read-only and its tamper gate weighs ----
        before = (stamp(html), stamp(js))
        rc_clean = mod.main(['--check', '--out', html, '--json', js])
        after = (stamp(html), stamp(js))
        chk_dir = os.path.join(world, 'chk')
        os.makedirs(chk_dir)
        chk_html = os.path.join(chk_dir, 'payment-gate-report.html')
        chk_js = os.path.join(chk_dir, 'payment-gate-report.json')
        shutil.copyfile(html, chk_html)
        shutil.copyfile(js, chk_js)
        tampered_payload = json.loads(read(chk_js))
        tampered_payload['sizes']['html'] = int(
            tampered_payload['sizes']['html']) + 1
        with io.open(chk_js, 'w', encoding='utf-8', newline='\n') as f:
            json.dump(tampered_payload, f, ensure_ascii=False, indent=2,
                      sort_keys=True)
            f.write('\n')
        rc_bad = mod.main(['--check', '--out', chk_html, '--json', chk_js])
        shutil.copyfile(js, chk_js)
        rc_restored = mod.main(['--check', '--out', chk_html, '--json', chk_js])
        reg = read(REGISTRY)
        hits = [m.start() for m in re.finditer(r'"os-payment-gate-report"', reg)]
        declared_rows = []
        for pos in hits:
            found = re.search(r'test_payment_gate_report\.py"\)\s*,\s*(\d+)',
                              reg[pos:pos + 200])
            if found:
                declared_rows.append(found.group(1))
        ok('AC-PAYGB9 --check is read-only, a tamper reddens, one row exists',
           before == after and rc_clean == 0 and rc_bad == 2
           and rc_restored == 0 and len(declared_rows) == 1,
           'clean=%d bad=%d restored=%d stat_stable=%s rows=%s' % (
               rc_clean, rc_bad, rc_restored, before == after,
               declared_rows))

        # isolation: the repo faces and the config were never touched
        post_preview = (digest(PREVIEW_HTML), digest(PREVIEW_JSON))
        ok('AC-PAYGB9b repo preview faces and pay config unchanged',
           post_preview == pre_preview and digest(CONFIG) == pre_cfg,
           'preview=%s->%s cfg=%s' % (pre_preview[0], post_preview[0],
                                      digest(CONFIG) == pre_cfg))

        # ---- AC-PAYGB10/11 (R2817): the price face is compared, not printed ----
        # Both tampered documents are made SELF-CONSISTENT (their sizes key is
        # iterated to the fixed point) so the inherited size guard cannot be the
        # reason they redden - only the new price guard can.
        def selfconsistent(folder, mutate):
            os.makedirs(folder)
            h = os.path.join(folder, 'payment-gate-report.html')
            j = os.path.join(folder, 'payment-gate-report.json')
            shutil.copyfile(html, h)
            doc = json.loads(read(js))
            mutate(doc)
            for _ in range(8):
                doc['sizes'] = {
                    'html': os.path.getsize(h),
                    'json': os.path.getsize(j) if os.path.exists(j) else 0}
                with io.open(j, 'w', encoding='utf-8', newline='\n') as f:
                    json.dump(doc, f, ensure_ascii=False, indent=2,
                              sort_keys=True)
                    f.write('\n')
                if doc['sizes']['json'] == os.path.getsize(j):
                    break
            return h, j

        def stale_price(doc):
            for row in doc['products']:
                if row['id'] == 'birthright_entry':
                    row['price_cent'] = 1990

        def stale_sha(doc):
            doc['config']['sha256'] = '0' * 64

        fresh = mod.collect()
        p_html, p_js = selfconsistent(os.path.join(world, 'stale'), stale_price)
        f_price = mod.check(fresh, p_html, p_js)
        rc_price = mod.main(['--check', '--out', p_html, '--json', p_js])
        ok('AC-PAYGB10 a stale price row reddens --check and names the product',
           rc_price == 2 and any('birthright_entry' in f for f in f_price)
           and not any('sizes' in f for f in f_price),
           'rc=%d fails=%s' % (rc_price, f_price))

        s_html, s_js = selfconsistent(os.path.join(world, 'shadrift'), stale_sha)
        f_sha = mod.check(fresh, s_html, s_js)
        rc_sha = mod.main(['--check', '--out', s_html, '--json', s_js])
        ok('AC-PAYGB11 a document rendered against another config reddens alone',
           rc_sha == 2 and any('config drift' in f for f in f_sha)
           and not any('sizes' in f for f in f_sha),
           'rc=%d fails=%s' % (rc_sha, f_sha))

        # ---- AC-PGM1..AC-PGM3 (R3610): the audit's law and the row it fixed ----
        # AC-PGM1: the resolver reads disk, so the wired local module resolves
        # and only a fabricated third party is refused.
        ok('AC-PGM1 imports resolve from disk: shipped modules resolve, a fabricated third party is refused',
           mod._shipped('json') is True
           and mod._shipped('board_face_landing') is True
           and mod._shipped('value_domain') is True
           and mod._shipped('zz_third_party_dep') is False,
           'json=%s wired=%s value=%s bogus=%s' % (
               mod._shipped('json'), mod._shipped('board_face_landing'),
               mod._shipped('value_domain'), mod._shipped('zz_third_party_dep')))

        # AC-PGM2: one red criterion must not print as two. Blanking the
        # disclaimer reddens AC-PAYG7 alone; AC-PAYG1 keeps its own meaning.
        blank = json.loads(cfg_src)
        blank['compliance']['disclaimer'] = ' '
        blank_cfg = os.path.join(world, 'cfg-blank.json')
        with io.open(blank_cfg, 'w', encoding='utf-8', newline='\n') as fh:
            json.dump(blank, fh, ensure_ascii=False)
        b_html = os.path.join(world, 'b.html')
        b_js = os.path.join(world, 'b.json')
        old_cfg = mod.CONFIG
        mod.CONFIG = blank_cfg
        try:
            rc_blank = mod.main(['--out', b_html, '--json', b_js])
        finally:
            mod.CONFIG = old_cfg
        banked = json.loads(read(b_js))
        rows_b = {c['id']: c for c in banked.get('criteria', [])}
        ok('AC-PGM2 a lone AC-PAYG7 red leaves AC-PAYG1 true (no verdict echo)',
           rc_blank == 2 and banked.get('verdict') == 'FAIL AC-PAYG7'
           and rows_b.get('AC-PAYG7', {}).get('pass') is False
           and rows_b.get('AC-PAYG1', {}).get('pass') is True,
           'rc=%d verdict=%s g1=%s g7=%s' % (
               rc_blank, banked.get('verdict'),
               rows_b.get('AC-PAYG1', {}).get('pass'),
               rows_b.get('AC-PAYG7', {}).get('pass')))

        # AC-PGM3: the repaired face owes a green end to end, read by its own
        # gate on the artifacts this suite's private world just landed.
        rc_self = mod.main(['--check', '--out', html, '--json', js])
        ok('AC-PGM3 landed face verdict=PASS 8/8 and its own --check exits 0',
           landed.get('verdict') == 'PASS' and rc_self == 0
           and all(c['pass'] for c in landed.get('criteria', [])),
           'verdict=%s rc_check=%d' % (landed.get('verdict'), rc_self))

        # ---- AC-PGM4..AC-PGM6 (R3611): the landing guard the board named ----
        # AC-PGM4: the guard is computed from ROOT, not from the flags.
        d_html = os.path.join(ROOT, 'preview', 'payment-gate-report.html')
        d_json = os.path.join(ROOT, 'preview', 'payment-gate-report.json')
        vec = (
            mod._landing_is_default(d_html, d_json),
            mod._landing_is_default(html, d_json),
            mod._landing_is_default(d_html, js),
            mod._landing_is_default(html, js),
        )
        ok('AC-PGM4 guard reads ROOT: (default/only-html/only-json/both) = (True,False,False,False)',
           vec == (True, False, False, False), 'vec=%s' % (vec,))

        # AC-PGM5: a private world's run must not re-derive THIS root's face.
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc_p5 = mod.main(['--out', html, '--json', js])
        face_tok = mod._refresh_face(html, js)
        now_export = stamp(EXPORT_FACE) if os.path.isfile(EXPORT_FACE) else None
        ok('AC-PGM5 a scratch landing prints SKIPPED scratch and leaves the root face untouched',
           rc_p5 in (0, 2)
           and 'face export=SKIPPED scratch' in buf.getvalue()
           and face_tok == 'SKIPPED scratch'
           and now_export == pre_export,
           'rc=%d tok=%s face_unchanged=%s' % (
               rc_p5, face_tok, now_export == pre_export))

        # AC-PGM6: one definition, one call, no local writer, and the call
        # carries BOTH landing paths.
        helper = tool_src.split('def _refresh_face(')[1].split('def main(')[0]
        ok('AC-PGM6 the face writer stays single and its call carries both paths',
           tool_src.count('refresh_export_face') == 1
           and tool_src.count('_refresh_face(') == 2
           and '_refresh_face(args.out, args.json)' in tool_src
           and '.write(' not in helper,
           'refs=%d calls=%d local_write=%s' % (
               tool_src.count('refresh_export_face'),
               tool_src.count('_refresh_face('),
               '.write(' in helper))
    finally:
        shutil.rmtree(world, ignore_errors=True)

    leak = os.path.isdir(world)
    ok('AC-PAYGB9c temp world removed (a leak is loud, not silent)', not leak,
       'removed=%s' % (not leak))

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
