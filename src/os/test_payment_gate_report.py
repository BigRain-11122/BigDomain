"""Battery suite for tools/payment_gate_report.py - criteria AC-PAYGB1..AC-PAYGB11.

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
        allowed = {'argparse', 'copy', 'datetime', 'hashlib', 'html', 'json',
                   'os', 'sys', 'adapters', 'v3', 'value_domain'}
        suite_allowed = {'ast', 'hashlib', 'importlib', 'io', 'json', 'os',
                         're', 'shutil', 'sys', 'tempfile', 'time',
                         'datetime', 'adapters', 'v3'}
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
        ok('AC-PAYGB8 both sources ASCII, whitelisted imports, zero network',
           ascii_tool and ascii_suite
           and tool_imp <= allowed and suite_imp <= suite_allowed
           and not net_tool and not net_suite,
           'tool_imp=%s suite_extra=%s net=%s ascii=%s/%s' % (
               ','.join(sorted(tool_imp)),
               ','.join(sorted(suite_imp - suite_allowed)),
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
