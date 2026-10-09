#!/usr/bin/env python3
"""test_logs_toolkit.py - sandbox test suite for src/os/logs_toolkit.py.

AC-LT6 (pre-registered in state/queue/tech.md R1686 claim line, written
before this code): sandbox fixture tree, subprocess CLI surface, asserts
gauge/inventory/prune/catalog behaviors incl. protected-file survival,
mtime floor, idempotence, and prune predicted==actual. Exit 0 = all green.

AC-LT14 (R1687 fold slice, pre-registered before code): fold cases on a
canonical PS 5.1 layout fixture - dry-run zero mutation, execute full
chain fidelity (backup byte-exact, archive verbatim append, text-surgical
state write, predicted==actual), gate/token fail-closed aborts with zero
mutation, archive missing fail-closed + --allow-create, layout refusal,
summary arity check. ASCII-only source; stdlib only; zero network.
"""

import json
import os
import re
import subprocess
import sys
import tempfile
import time

TOOL = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs_toolkit.py')
CHECKS = 0


def ok(cond, label):
    global CHECKS
    assert cond, 'FAIL: ' + label
    CHECKS += 1
    print('PASS ' + label)


def run(root, *args):
    p = subprocess.run([sys.executable, TOOL, '--root', root] + list(args),
                       capture_output=True)
    return p.returncode, p.stdout.decode('utf-8', 'replace'), p.stderr.decode('utf-8', 'replace')


def build_fixture():
    root = tempfile.mkdtemp(prefix='bd-ltk-')
    os.makedirs(os.path.join(root, 'src', 'os'))
    os.makedirs(os.path.join(root, 'logs'))
    st = {
        'tick': 42,
        'last_order': 'x',
        'log': [
            '2026-10-09 R41 fold R9 reorg: window P-2026-09-25-18 chain, AC-R9 part',
            '2026-10-09 R41 tokens: local=1 api=0 api_reason=test',
            '2026-10-09 R42 waiting on external artifact D-20260930-19',
        ],
    }
    spath = os.path.join(root, 'src', 'os', 'state.json')
    with open(spath, 'wb') as f:
        f.write((json.dumps(st, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
    ld = os.path.join(root, 'logs')
    old = time.time() - 90000
    fresh = time.time() - 60
    for i in range(20):
        p = os.path.join(ld, 'state-preop-R%04d.bak' % (i + 1))
        open(p, 'wb').write(b'x' * 10)
        os.utime(p, (old - i, old - i))
    for i in range(80):
        p = os.path.join(ld, 'tmp_gen_%03d.py' % (i + 1))
        open(p, 'wb').write(b'x' * 10)
        os.utime(p, (old - 100 - i, old - 100 - i))
    pfresh = os.path.join(ld, 'tmp_fresh_inflight.py')
    open(pfresh, 'wb').write(b'x' * 10)
    os.utime(pfresh, (fresh, fresh))
    for i in range(320):
        p = os.path.join(ld, 'round_20260101_%06d.out' % (i + 1))
        open(p, 'wb').write(b'x' * 10)
        os.utime(p, (old - 200 - i, old - 200 - i))
    for i in range(40):  # run_*.log launcher transcript family (R1686 live finding)
        p = os.path.join(ld, 'run_20260101_%06d.log' % (i + 1))
        open(p, 'wb').write(b'x' * 10)
        os.utime(p, (old - 300 - i, old - 300 - i))
    open(os.path.join(ld, 'state-log-archive-2026-10.md'), 'wb').write(b'# archive\n')
    open(os.path.join(ld, 'round.lock'), 'wb').write(b'')
    open(os.path.join(ld, 'tmp_must_not_die.md'), 'wb').write(b'protected')
    open(os.path.join(ld, 'other.dat'), 'wb').write(b'keepme')
    return root, spath, ld


def count_class(ld, cls, classify):
    n = 0
    import logs_toolkit as T
    for e in os.scandir(ld):
        if e.is_file() and classify(e.name) == cls:
            n += 1
    return n


def split_json_blocks(out):
    blocks, buf, depth = [], [], 0
    for ln in out.splitlines():
        buf.append(ln)
        depth += ln.count('{') - ln.count('}')
        if depth == 0 and buf:
            blocks.append('\n'.join(buf))
            buf = []
    return [b for b in blocks if b.strip()]


def build_ps_state(root, logs, archive_text='# archive\n'):
    """Canonical PS 5.1 layout fixture: CRLF, 4-space indent, two spaces
    after colon, 16-space log items, 12-space closing bracket, no trailing
    newline (matches live src/os/state.json byte format)."""
    import logs_toolkit as T
    os.makedirs(os.path.join(root, 'src', 'os'), exist_ok=True)
    os.makedirs(os.path.join(root, 'logs'), exist_ok=True)
    lines = ['{', '    "tick":  42,', '    "log":  [']
    for i, s in enumerate(logs):
        comma = ',' if i < len(logs) - 1 else ''
        lines.append(' ' * 16 + T.ps_escape(s) + comma)
    lines.append('            ]')
    lines.append('}')
    path = os.path.join(root, 'src', 'os', 'state.json')
    with open(path, 'wb') as f:
        f.write('\r\n'.join(lines).encode('utf-8'))
    if archive_text is not None:
        with open(os.path.join(root, 'logs', 'state-log-archive-2026-10.md'), 'wb') as f:
            f.write(archive_text.encode('utf-8'))
    return path


def main():
    root, spath, ld = build_fixture()
    sys.path.insert(0, os.path.dirname(TOOL))
    import logs_toolkit as T

    # unknown subcommand -> exit 2 (AC-LT1)
    rc, _, _ = run(root, 'bogus')
    ok(rc == 2, 'unknown subcommand exit 2')

    # gauge (AC-LT2)
    rc, out, _ = run(root, 'gauge')
    g = json.loads(out)
    ok(rc == 0, 'gauge exit 0')
    ok(g['disk_bytes'] == os.path.getsize(spath), 'gauge disk bytes exact')
    ok(g['log_lines'] == 3 and g['tick'] == 42, 'gauge log count/tick')
    ok(g['log_content_bytes'] == sum(len(x.encode('utf-8')) for x in json.load(open(spath, encoding='utf-8'))['log']),
       'gauge content byte sum')
    ok(g['fold_needed'] is False and g['gate'] == 78500, 'gauge verdict under gate')

    # inventory (AC-LT3)
    rc, out, _ = run(root, 'inventory')
    inv = json.loads(out)
    ok(rc == 0, 'inventory exit 0')
    c = inv['classes']
    ok(c['archive-md']['count'] == 2 and c['archive-md']['protected'], 'inventory archive-md protected (md glob)')
    ok(c['lock']['count'] == 1 and c['lock']['protected'], 'inventory lock protected')
    ok(c['preop-bak']['count'] == 20 and c['preop-bak']['prunable'], 'inventory preop count/prunable')
    ok(c['tmp-script']['count'] == 81 and c['tmp-script']['prunable'], 'inventory tmp count 81 (md-named tmp counted protected)')
    ok(c['round-transcript']['count'] == 360 and c['round-transcript']['prunable'], 'inventory transcript count (320 round_*.out + 40 run_*.log)')
    ok(c['other']['count'] == 1 and c['other']['protected'], 'inventory other protected')

    # tail classification (AC-LT1 tail surface)
    rc, out, _ = run(root, 'tail', '-n', '3')
    rows = [json.loads(l) for l in out.strip().splitlines()]
    ok(rc == 0 and len(rows) == 3, 'tail 3 rows')
    ok(rows[0]['class'] == 'round-main' and rows[1]['class'] == 'tokens' and rows[2]['class'] == 'declaration',
       'tail classification main/tokens/declaration')

    # prune dry-run (AC-LT4)
    rc, out, _ = run(root, 'prune')
    plan = json.loads(out)
    ok(rc == 0, 'prune dry-run exit 0')
    ok(plan['mode'] == 'dry-run', 'prune dry-run default no-delete')
    ok(plan['to_delete'] == {'preop-bak': 8, 'round-transcript': 60, 'tmp-script': 20},
       'prune dry-run predicted counts (keep 12/300/60; fresh floor-skipped out of bucket)')
    ok(plan['protected_skipped'] == 0, 'prune class-level protection handles md/lock before plan guard (0 in-plan skips)')
    n_before = len(os.listdir(ld))
    ok(n_before == 2 + 1 + 20 + 81 + 360 + 1, 'dry-run deleted nothing (file count unchanged)')

    # prune execute (AC-LT4)
    rc, out, _ = run(root, 'prune', '--execute')
    # execute prints two JSON blocks: plan summary then deleted summary
    blocks = split_json_blocks(out)
    ex = json.loads(blocks[-1])
    ok(rc == 0, 'prune execute exit 0')
    ok(ex['prediction_match'] is True and ex['deleted_total'] == 88, 'prune predicted==actual 88')
    ok(ex['deleted'] == {'preop-bak': 8, 'round-transcript': 60, 'tmp-script': 20}, 'prune per-class deleted counts')
    ok(os.path.exists(os.path.join(ld, 'state-log-archive-2026-10.md')), 'protected archive survived')
    ok(os.path.exists(os.path.join(ld, 'round.lock')), 'protected lock survived')
    ok(os.path.exists(os.path.join(ld, 'tmp_must_not_die.md')), 'protected md-named tmp survived')
    ok(os.path.exists(os.path.join(ld, 'other.dat')), 'other class untouched')
    ok(os.path.exists(os.path.join(ld, 'tmp_fresh_inflight.py')), 'mtime floor protected in-flight file')
    ok(count_class(ld, 'preop-bak', T.classify) == 12, 'preop keep-newest 12')
    ok(count_class(ld, 'tmp-script', T.classify) == 61, 'tmp remaining 60+fresh')
    ok(count_class(ld, 'round-transcript', T.classify) == 300, 'transcript keep-newest 300')

    # idempotent second run (AC-LT4)
    rc, out, _ = run(root, 'prune', '--execute')
    ok(rc == 0 and json.loads(split_json_blocks(out)[0])['to_delete_total'] == 0,
       'prune second execute 0 further deletes')

    # catalog pass (AC-LT5)
    wf = os.path.join(root, 'win.txt')
    open(wf, 'w', encoding='utf-8').write(
        '2026-10-09 R1685 fold R454 chain P-2026-09-25-18 AC-R4541 AC-R4546\n'
        '2026-10-09 R1685 tokens: local=1 api=0\n')
    rf = os.path.join(root, 'roll.txt')
    open(rf, 'w', encoding='utf-8').write(
        'roll summary mentions R1685 fold R454 P-2026-09-25-18 AC-R4541 AC-R4546 everything\n')
    rc, out, _ = run(root, 'catalog', '--window-file', wf, '--roll-file', rf)
    cat = json.loads(out)
    ok(rc == 0 and cat['pass'] and cat['missing_in_roll'] == [], 'catalog zero-loss pass exit 0')
    ok(cat['tokens_total'] == 3, 'catalog token count {P-2026-09-25-18,AC-R4541,AC-R4546} == 3 (PAT is dash-form only, bare R1685/R454 out)')
    # catalog fail path
    rf2 = os.path.join(root, 'roll2.txt')
    open(rf2, 'w', encoding='utf-8').write('roll missing the AC tokens\n')
    rc, out, _ = run(root, 'catalog', '--window-file', wf, '--roll-file', rf2)
    cat2 = json.loads(out)
    ok(rc == 2 and not cat2['pass'] and len(cat2['missing_in_roll']) >= 3, 'catalog missing-token fail exit 2')

    # --tail window mode (AC-LT5): tail-3 window tokens = {P-..., AC-R9, D-20260930-19}
    rc, out, _ = run(root, 'catalog', '--tail', '3', '--roll-file', rf)
    cat3 = json.loads(out)
    ok(rc == 2 and 'AC-R9' in cat3['missing_in_roll'] and 'D-20260930-19' in cat3['missing_in_roll'],
       'catalog --tail mode window extraction (AC-R9 + D-20260930-19 missing)')

    # ---- fold surgery (AC-LT8..LT14, R1687 slice) ----
    PS_LOGS = [
        '2026-10-09 R1670 dec batch D-20261009-01 ack + gord note, kept line with < sensitive',
        '2026-10-09 R1670 tokens: local=1 api=0 api_reason=test',
        '2026-10-09 R1671 fold window pair P-2026-09-25-18 AC-R4531 verbatim',
        '2026-10-09 R1672 pair line D-20260930-19 O-20261009-1246 in window',
    ]
    SUMMARY = ('2026-10-09 roll window line: folds R1671+R1672 keeping '
               'P-2026-09-25-18 AC-R4531 D-20260930-19 O-20261009-1246, < kept')
    sfold = tempfile.mkdtemp(prefix='bd-fold-')
    spath = build_ps_state(sfold, PS_LOGS)
    sfile = os.path.join(sfold, 'summary.txt')
    open(sfile, 'w', encoding='utf-8').write(SUMMARY + '\n')
    arc = os.path.join(sfold, 'logs', 'state-log-archive-2026-10.md')
    pre_state = open(spath, 'rb').read()
    pre_arc = open(arc, 'rb').read()

    # dry-run: plan + zero mutation (AC-LT9)
    rc, out, err = run(sfold, 'fold', '--round', 'R9001', '--fold-no', '455',
                       '--desc', 'R1671+R1672 two pairs', '--window-tail', '2',
                       '--summary-file', sfile)
    plan = json.loads(out)
    ok(rc == 0, 'fold dry-run exit 0')
    ok(plan['window_lines'] == 2 and plan['new_log_len'] == 3, 'fold plan window/new-log count')
    ok(plan['token_ok'] is True and plan['gate_ok'] is True and plan['would_fail'] == [],
       'fold plan verdicts green')
    ok(plan['preop_sha16'] == __import__('hashlib').sha256(pre_state).hexdigest()[:16],
       'fold plan preop sha16 exact')
    ok(plan['archive_header'].startswith('# --- R9001 fold append (')
       and 'fold R455 window' in plan['archive_header'], 'fold plan archive header format')
    ok(open(spath, 'rb').read() == pre_state and open(arc, 'rb').read() == pre_arc,
       'fold dry-run zero mutation (state + archive)')

    # execute: full chain fidelity (AC-LT10/11)
    rc, out, err = run(sfold, 'fold', '--round', 'R9001', '--fold-no', '455',
                       '--desc', 'R1671+R1672 two pairs', '--window-tail', '2',
                       '--summary-file', sfile, '--execute')
    res = json.loads(out)
    ok(rc == 0, 'fold execute exit 0')
    ok(res['predicted_eq_actual'] is True and res['predicted_bytes'] == plan['predicted_bytes'],
       'fold predicted==actual (dry-run plan == execute result)')
    bak = os.path.join(sfold, 'logs', 'state-preop-R9001.bak')
    ok(open(bak, 'rb').read() == pre_state, 'fold preop backup byte-exact')
    post_arc = open(arc, 'rb').read()
    appendix = (plan['archive_header'] + '\n'
                + '\n'.join(PS_LOGS[-2:]) + '\n').encode('utf-8')
    ok(post_arc == pre_arc + appendix, 'fold archive append verbatim (header + window)')
    post_state = open(spath, 'rb').read()
    ok(os.path.getsize(spath) == res['predicted_bytes'], 'fold disk size == predicted')
    pst = json.loads(post_state.decode('utf-8'))
    ok(pst['log'] == PS_LOGS[:2] + [SUMMARY], 'fold new log == kept + summary')
    ok(pst['log'][0].count('<') == 1 and pst['log'][-1].count('<') == 1,
       'fold escape round-trip (< restored by parser)')
    ok(b'\\u003c' in post_state, 'fold PS-style escape written (\\u003c on disk)')
    pre_lines = pre_state.decode('utf-8').split('\r\n')
    post_lines = post_state.decode('utf-8').split('\r\n')
    ok(post_lines[:5] == pre_lines[:5] and post_lines[-1] == pre_lines[-1]
       and post_lines[-2] == pre_lines[-2],
       'fold text surgery prefix+suffix lines byte-identical')
    ok(post_state.count(b'\r\n') == pre_state.count(b'\r\n') - 1,
       'fold CRLF layout preserved (one window line net removed)')

    # token-missing abort: fail-closed, zero mutation (AC-LT13)
    sf2 = tempfile.mkdtemp(prefix='bd-fold-')
    build_ps_state(sf2, PS_LOGS)
    sfile2 = os.path.join(sf2, 'summary.txt')
    open(sfile2, 'w', encoding='utf-8').write('2026-10-09 roll line missing all tokens\n')
    pre2 = open(os.path.join(sf2, 'src', 'os', 'state.json'), 'rb').read()
    arc2 = os.path.join(sf2, 'logs', 'state-log-archive-2026-10.md')
    prearc2 = open(arc2, 'rb').read()
    rc, out, _ = run(sf2, 'fold', '--round', 'R9002', '--fold-no', '456',
                     '--desc', 'x', '--window-tail', '2', '--summary-file', sfile2,
                     '--execute')
    j = json.loads(out)
    ok(rc == 2 and 'token-missing' in j['would_fail'] and len(j['token_missing']) == 4,
       'fold token-loss abort exit 2 (4 tokens missing)')
    ok(open(os.path.join(sf2, 'src', 'os', 'state.json'), 'rb').read() == pre2
       and open(arc2, 'rb').read() == prearc2
       and not os.path.exists(os.path.join(sf2, 'logs', 'state-preop-R9002.bak')),
       'fold abort zero mutation (no state/archive/backup writes)')

    # gate abort: big KEPT line keeps predicted over gate, fail-closed (AC-LT12)
    sf3 = tempfile.mkdtemp(prefix='bd-fold-')
    big = 'x' * 76000
    build_ps_state(sf3, ['2026-10-09 R1 big kept ' + big, '2026-10-09 R2 small window'])
    sfile3 = os.path.join(sf3, 'summary.txt')
    open(sfile3, 'w', encoding='utf-8').write('2026-10-09 roll summary line\n')
    pre3 = open(os.path.join(sf3, 'src', 'os', 'state.json'), 'rb').read()
    rc, out, _ = run(sf3, 'fold', '--round', 'R9003', '--fold-no', '457',
                     '--desc', 'x', '--window-tail', '1', '--summary-file', sfile3,
                     '--reserve-bytes', '3000')
    j = json.loads(out)
    ok(rc == 2 and j['would_fail'] == ['gate-exceed']
       and j['predicted_bytes'] + 3000 > 78500,
       'fold gate abort exit 2 (predicted+reserve over 78500)')
    ok(open(os.path.join(sf3, 'src', 'os', 'state.json'), 'rb').read() == pre3,
       'fold gate abort zero mutation')

    # archive missing: fail-closed without --allow-create, created with it (AC-LT8/10)
    sf4 = tempfile.mkdtemp(prefix='bd-fold-')
    build_ps_state(sf4, PS_LOGS, archive_text=None)
    sfile4 = os.path.join(sf4, 'summary.txt')
    open(sfile4, 'w', encoding='utf-8').write(SUMMARY + '\n')
    arc4 = os.path.join(sf4, 'logs', 'state-log-archive-2026-10.md')
    rc, out, _ = run(sf4, 'fold', '--round', 'R9004', '--fold-no', '458',
                     '--desc', 'x', '--window-tail', '2', '--summary-file', sfile4,
                     '--execute')
    j = json.loads(out)
    ok(rc == 2 and j['would_fail'] == ['archive-missing'] and not os.path.exists(arc4),
       'fold archive-missing fail-closed (no create without --allow-create)')
    rc, out, _ = run(sf4, 'fold', '--round', 'R9004', '--fold-no', '458',
                     '--desc', 'x', '--window-tail', '2', '--summary-file', sfile4,
                     '--allow-create', '--execute')
    ok(rc == 0 and os.path.exists(arc4), 'fold --allow-create creates archive + executes')
    a4 = open(arc4, encoding='utf-8').read()
    ok(a4.startswith('# logs/state-log-archive-2026-10.md (created by logs_toolkit.py fold')
       and '# --- R9004 fold append (' in a4 and PS_LOGS[-1] in a4,
       'fold created archive carries preamble + header + verbatim window')

    # archive without trailing newline: prepend branch (AC-LT11 write fidelity)
    sf5 = tempfile.mkdtemp(prefix='bd-fold-')
    build_ps_state(sf5, PS_LOGS, archive_text='# archive no trailing newline')
    sfile5 = os.path.join(sf5, 'summary.txt')
    open(sfile5, 'w', encoding='utf-8').write(SUMMARY + '\n')
    arc5 = os.path.join(sf5, 'logs', 'state-log-archive-2026-10.md')
    pre5 = open(arc5, 'rb').read()
    rc, _, _ = run(sf5, 'fold', '--round', 'R9005', '--fold-no', '459',
                   '--desc', 'x', '--window-tail', '2', '--summary-file', sfile5,
                   '--execute')
    post5 = open(arc5, 'rb').read()
    ok(rc == 0 and post5.startswith(pre5 + b'\n'),
       'fold archive no-trailing-newline prepend branch')

    # layout refusal on non-PS serialization (AC-LT11 fail-closed)
    rc, _, err = run(root, 'fold', '--round', 'R9006', '--fold-no', '460',
                     '--desc', 'x', '--window-tail', '2', '--summary-file', sfile)
    ok(rc == 2 and 'E_STATE_LAYOUT' in err,
       'fold layout refusal exit 2 on non-PS fixture (zero mutation)')

    # summary arity + window bounds (AC-LT8)
    two = os.path.join(sfold, 'two.txt')
    open(two, 'w', encoding='utf-8').write('line one\nline two\n')
    rc, _, err = run(sfold, 'fold', '--round', 'R9007', '--fold-no', '461',
                     '--desc', 'x', '--window-tail', '2', '--summary-file', two)
    ok(rc == 2 and 'exactly one non-empty line' in err, 'fold summary arity check exit 2')
    rc, _, err = run(sfold, 'fold', '--round', 'R9008', '--fold-no', '462',
                     '--desc', 'x', '--window-tail', '99', '--summary-file', sfile)
    ok(rc == 2 and 'exceeds log length' in err, 'fold window-tail bounds check exit 2')

    # ---- census (AC-LT15..LT17, R1688 slice; non-ASCII markers via escapes) ----
    SEC = '\u00a7'   # section pointer marker
    YUAN = '\u539f'  # original-archive marker

    def build_census_fixture(state_logs, arc10, arc09=None):
        cf = tempfile.mkdtemp(prefix='bd-census-')
        os.makedirs(os.path.join(cf, 'src', 'os'))
        os.makedirs(os.path.join(cf, 'logs'))
        stpath = os.path.join(cf, 'src', 'os', 'state.json')
        with open(stpath, 'wb') as f:
            f.write((json.dumps({'tick': 7, 'log': state_logs},
                                ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
        with open(os.path.join(cf, 'logs', 'state-log-archive-2026-10.md'), 'wb') as f:
            f.write(arc10.encode('utf-8'))
        if arc09 is not None:
            with open(os.path.join(cf, 'logs', 'state-log-archive-2026-09.md'), 'wb') as f:
                f.write(arc09.encode('utf-8'))
        return cf, stpath

    ARC10 = ('# --- R10 fold append (2026-10-09, 2 lines verbatim: pair, fold R1 window)\n'
             '2026-10-09 R10 line one with P-2026-09-25-18 and D-20260930-19\n'
             '2026-10-09 R10 tokens: local=1 api=0\n'
             '# --- R11 fold append (2026-10-09, 3 lines verbatim: trio, fold R2 window)\n'
             '2026-10-09 R11 a O-20261009-1246\n'
             '2026-10-09 R11 b C-20261009-03 R9999\n'
             '2026-10-09 R11 tokens: local=1 api=0\n')
    ARC09 = ('# --- R300 append (pre re-org round 1, tick 299, 2026-09-26, 81000 bytes) ---\n'
             '2026-09-26 R300 legacy line with P-2026-09-24-47\n')
    LINE_OK = ('2026-10-09 roll window: archive ' + SEC + 'R10 section 2 lines verbatim '
               'keeping P-2026-09-25-18 D-20260930-19, evidence AC-R9001, plus '
               'logs/state-log-archive-2026-09.md ' + YUAN + ' P-2026-09-24-47')

    # (i) clean case: declared==actual, pointers resolve, full embed, orig file ref
    cf1, cpath1 = build_census_fixture([LINE_OK], ARC10, ARC09)
    pre_c = open(cpath1, 'rb').read()
    rc, out, _ = run(cf1, 'census')
    cen = json.loads(out)
    ok(rc == 0 and cen['pass'] is True, 'census clean case exit 0')
    ok(cen['sections_total'] == 3 and cen['files']['2026-09']['sections'] == 1
       and cen['files']['2026-10']['sections'] == 2, 'census sections parsed (10 two + 09 one)')
    ok(cen['section_line_mismatches'] == [], 'census declared==actual all sections')
    ok(all(m['file'] != '2026-09' for m in cen['section_line_mismatches']),
       'census legacy 09 header (no declared) exempt from mismatch face')
    pl = cen['pointer_lines'][0]
    ok(len(cen['pointer_lines']) == 1 and pl['pointers'] == ['R10']
       and pl['file_refs'] == ['2026-09'] and pl['dangling'] == [],
       'census pointer + orig-file-ref extraction, zero dangling')
    ok(pl['not_embedded'] == {}, 'census full-embed not_embedded empty')
    ok(pl['roll_native'] == ['AC-R9001'], 'census roll_native = evidence-pointer class only')
    ok(cen['archive_only_tokens'] == ['C-20261009-03', 'O-20261009-1246'],
       'census archive_only lists unreferenced-section tokens')
    ok('R9999' not in cen['archive_only_tokens']
       and cen['archive_tokens_total'] == 5,
       'census PAT single-source: bare R9999 never counted (5 dash-form tokens)')
    ok(open(cpath1, 'rb').read() == pre_c, 'census read-only zero mutation (state)')

    # (ii) dangling pointer -> exit 2
    cf2, _ = build_census_fixture(
        ['2026-10-09 line refs archive ' + SEC + 'R99 missing section'],
        '# --- R10 fold append (2026-10-09, 1 lines verbatim: x, fold R1 window)\n'
        '2026-10-09 R10 a D-20260930-19\n')
    rc, out, _ = run(cf2, 'census')
    cen2 = json.loads(out)
    ok(rc == 2 and cen2['pass'] is False and cen2['dangling_total'] == 1
       and cen2['pointer_lines'][0]['dangling'] == ['R99'],
       'census dangling pointer exit 2')

    # (iii) declared vs actual mismatch (NUL-clobber class) -> exit 2
    cf3, _ = build_census_fixture(
        ['2026-10-09 line refs archive ' + SEC + 'R10 verbatim D-20260930-19'],
        '# --- R10 fold append (2026-10-09, 9 lines verbatim: clobbered, fold R1 window)\n'
        '2026-10-09 R10 a D-20260930-19\n'
        '2026-10-09 R10 b\n'
        '2026-10-09 R10 c\n'
        '2026-10-09 R10 d\n')
    rc, out, _ = run(cf3, 'census')
    cen3 = json.loads(out)
    ok(rc == 2 and cen3['section_line_mismatches'] ==
       [{'round': 'R10', 'file': '2026-10', 'declared': 9, 'actual': 4,
         'adjudicated': False}],
       'census declared!=actual mismatch exit 2 (clobber class)')

    # (iv) not_embedded census is informational: exit 0 with listing
    cf4, _ = build_census_fixture(
        ['2026-10-09 line refs archive ' + SEC + 'R10 verbatim D-20260930-19 only'],
        '# --- R10 fold append (2026-10-09, 2 lines verbatim: pair, fold R1 window)\n'
        '2026-10-09 R10 a D-20260930-19\n'
        '2026-10-09 R10 b C-3 extra token not embedded\n')
    rc, out, _ = run(cf4, 'census')
    cen4 = json.loads(out)
    ok(rc == 0 and cen4['pass'] is True
       and cen4['pointer_lines'][0]['not_embedded'] == {'R10': ['C-3']},
       'census not_embedded informational (listed, still exit 0)')

    # (vii) known-findings adjudication: visible but not failing (AC-LT15 amend)
    KNOWN = {'section_line_mismatches': [
                 {'round': 'R10', 'reason': 'adjudicated fixture', 'adjudicated': 'x'}],
             'dangling_pointers': [
                 {'pointer': 'R99', 'reason': 'adjudicated fixture', 'adjudicated': 'x'}]}
    kfile = os.path.join(cf3, 'known.json')
    open(kfile, 'w', encoding='utf-8').write(json.dumps(KNOWN))
    rc, out, _ = run(cf3, 'census', '--known-file', kfile)
    cen5 = json.loads(out)
    ok(rc == 0 and cen5['pass'] is True and cen5['unknown_mismatch_count'] == 0
       and cen5['section_line_mismatches'][0]['adjudicated'] is True
       and 'reason' in cen5['section_line_mismatches'][0],
       'census known mismatch adjudicated: listed + reason, exit 0')
    rc, out, _ = run(cf2, 'census', '--known-file', kfile)
    cen6 = json.loads(out)
    ok(rc == 0 and cen6['pass'] is True and cen6['unknown_dangling_count'] == 0
       and cen6['dangling_known'] == [{'pointer': 'R99', 'reason': 'adjudicated fixture'}]
       and cen6['dangling_total'] == 1,
       'census known dangling adjudicated: raw count kept, verdict green')
    kfile2 = os.path.join(cf3, 'known_other.json')
    open(kfile2, 'w', encoding='utf-8').write(json.dumps(
        {'section_line_mismatches': [{'round': 'R77'}], 'dangling_pointers': []}))
    rc, out, _ = run(cf3, 'census', '--known-file', kfile2)
    cen7 = json.loads(out)
    ok(rc == 2 and cen7['unknown_mismatch_count'] == 1
       and cen7['section_line_mismatches'][0]['adjudicated'] is False,
       'census non-listed finding still fails with known-file present')

    # ASCII hygiene self-scan (AC-LT6)
    for src in (TOOL, os.path.abspath(__file__)):
        b = open(src, 'rb').read()
        ok(all(byte < 128 for byte in b), 'ASCII-only source: ' + os.path.basename(src))

    print('SUITE PASS %d checks' % CHECKS)
    return 0


if __name__ == '__main__':
    sys.exit(main())
