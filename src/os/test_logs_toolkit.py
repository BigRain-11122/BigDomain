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
REGISTRY = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        os.pardir, 'sandbox', 'reconcile_all.py')
LABEL = 'os-logs-toolkit'
CHECKS = 0


def registry_crit(path, label):
    """Read one registry row's declared count by text, not by import (AC-QREG7).

    The SUITES table calls os.path.join in its rows, so it is not a literal that
    can be evaluated; importing it would run whatever sits beside the table. A
    scoped match on the label asks exactly the question this suite needs - one
    row, one integer - and returns (None, hits) when the row is missing or
    duplicated, which every caller treats as red rather than as zero.
    """
    with open(path, 'rb') as handle:
        text = handle.read().decode('utf-8')
    pattern = r'\("%s",\s*\n\s*[^\n]*?,\s*(\d+)\)' % re.escape(label)
    hits = re.findall(pattern, text)
    if len(hits) != 1:
        return None, len(hits)
    return int(hits[0]), 1


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
    open(os.path.join(ld, archive_name()), 'wb').write(b'# archive\n')
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


def archive_name():
    """The month-stamped archive filename the tool derives at call time.

    R2747: this fixture used to hardcode state-log-archive-2026-10.md while
    the tool names the archive from datetime.now(CST), so the whole suite
    went red the moment the calendar left 2026-10 - a rot that stayed
    invisible because this suite is not registered in the battery. Derived
    from the tool's own CST so the fixture tracks the calendar instead of
    pinning it.
    """
    import logs_toolkit
    from datetime import datetime as _dt
    return 'state-log-archive-%s.md' % _dt.now(logs_toolkit.CST).strftime('%Y-%m')


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
        with open(os.path.join(root, 'logs', archive_name()), 'wb') as f:
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
    ok(os.path.exists(os.path.join(ld, archive_name())), 'protected archive survived')
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
    arc = os.path.join(sfold, 'logs', archive_name())
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
    ok(plan['round_label'] == 'R9001', 'fold plan round_label echo (AC-LT25)')
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
    arc2 = os.path.join(sf2, 'logs', archive_name())
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
    arc4 = os.path.join(sf4, 'logs', archive_name())
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
    ok(a4.startswith('# logs/' + archive_name() + ' (created by logs_toolkit.py fold')
       and '# --- R9004 fold append (' in a4 and PS_LOGS[-1] in a4,
       'fold created archive carries preamble + header + verbatim window')

    # archive without trailing newline: prepend branch (AC-LT11 write fidelity)
    sf5 = tempfile.mkdtemp(prefix='bd-fold-')
    build_ps_state(sf5, PS_LOGS, archive_text='# archive no trailing newline')
    sfile5 = os.path.join(sf5, 'summary.txt')
    open(sfile5, 'w', encoding='utf-8').write(SUMMARY + '\n')
    arc5 = os.path.join(sf5, 'logs', archive_name())
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

    # ---- fold mid-window slice (AC-LT20..LT23, R1690 slice) ----
    import logs_toolkit as T
    MS_LOGS = [
        '2026-10-09 R800 pair A P-2026-09-25-18 kept-line-one',
        '2026-10-09 R800 tokens: local=1 api=0 api_reason=t',
        '2026-10-09 R801 mid window line D-20260930-19 O-20261009-1246',
        '2026-10-09 R801 tokens: local=1 api=0 api_reason=t',
        '2026-10-09 R802 pair C AC-R4541 tail-side',
    ]
    MS_SUMMARY = ('2026-10-09 mid roll: folds R801 pair keeping '
                  'D-20260930-19 O-20261009-1246 verbatim')
    ms = tempfile.mkdtemp(prefix='bd-mslice-')
    mspath = build_ps_state(ms, MS_LOGS)
    mfile = os.path.join(ms, 'summary.txt')
    open(mfile, 'w', encoding='utf-8').write(MS_SUMMARY + '\n')
    marc = os.path.join(ms, 'logs', archive_name())
    pre_ms = open(mspath, 'rb').read()
    pre_marc = open(marc, 'rb').read()
    mbase = ['fold', '--round', 'R9010', '--fold-no', '470', '--desc', 'x',
             '--summary-file', mfile]
    # misuse faces (AC-LT20): selector arity, format, bounds
    rc, _, err = run(ms, *mbase)
    ok(rc == 2 and 'exactly one of --window-tail / --window-slice' in err,
       'slice mutual-exclusion: no selector exit 2')
    rc, _, err = run(ms, *(mbase + ['--window-tail', '2', '--window-slice', '3:4']))
    ok(rc == 2 and 'exactly one of --window-tail / --window-slice' in err,
       'slice mutual-exclusion: both selectors exit 2')
    rc, _, err = run(ms, *(mbase + ['--window-slice', '2-3']))
    ok(rc == 2 and 'START:END' in err, 'slice malformed format exit 2')
    rc, _, err = run(ms, *(mbase + ['--window-slice', '0:3']))
    ok(rc == 2 and 'E_WINDOW_RANGE' in err, 'slice bounds start<1 exit 2')
    rc, _, err = run(ms, *(mbase + ['--window-slice', '4:3']))
    ok(rc == 2 and 'E_WINDOW_RANGE' in err, 'slice bounds end<start exit 2')
    rc, _, err = run(ms, *(mbase + ['--window-slice', '2:99']))
    ok(rc == 2 and 'E_WINDOW_RANGE' in err, 'slice bounds end>len exit 2')
    ok(open(mspath, 'rb').read() == pre_ms and open(marc, 'rb').read() == pre_marc,
       'slice misuse faces zero mutation (state + archive)')
    # dry-run: plan fields + zero mutation (AC-LT20/22)
    rc, out, _ = run(ms, 'fold', '--round', 'R9010', '--fold-no', '470',
                     '--desc', 'mid probe', '--window-slice', '3:4',
                     '--summary-file', mfile)
    plan = json.loads(out)
    ok(rc == 0, 'slice dry-run exit 0')
    ok(plan['window_mode'] == 'slice' and plan['window_start'] == 3
       and plan['window_end'] == 4, 'slice plan window_mode/bounds fields')
    ok(plan['window_lines'] == 2 and plan['new_log_len'] == 4,
       'slice plan window/new-log count')
    ok(plan['token_ok'] is True and plan['would_fail'] == [],
       'slice plan verdicts green')
    ok('fold R470 mid-window' in plan['archive_header'],
       'slice archive header mid-window wording')
    ok(open(mspath, 'rb').read() == pre_ms and open(marc, 'rb').read() == pre_marc,
       'slice dry-run zero mutation (state + archive)')
    # execute: full-chain fidelity (AC-LT21)
    rc, out, _ = run(ms, 'fold', '--round', 'R9010', '--fold-no', '470',
                     '--desc', 'mid probe', '--window-slice', '3:4',
                     '--summary-file', mfile, '--execute')
    res = json.loads(out)
    ok(rc == 0 and res['predicted_eq_actual'] is True,
       'slice execute exit 0, predicted==actual')
    pst = json.loads(open(mspath, 'rb').read().decode('utf-8'))
    ok(pst['log'] == MS_LOGS[:2] + [MS_SUMMARY] + MS_LOGS[4:],
       'slice new log order: prefix + summary + suffix')
    pre_lines = pre_ms.decode('utf-8').split('\r\n')
    exp_lines = (pre_lines[:5]
                 + [' ' * 16 + T.ps_escape(MS_SUMMARY) + ','] + pre_lines[7:])
    ok(open(mspath, 'rb').read().decode('utf-8').split('\r\n') == exp_lines,
       'slice surgery: prefix+suffix byte-identical, summary comma in place')
    ok(open(os.path.join(ms, 'logs', 'state-preop-R9010.bak'), 'rb').read()
       == pre_ms, 'slice preop backup byte-exact')
    post_marc = open(marc, 'rb').read()
    marc_txt = post_marc.decode('utf-8')
    ok(post_marc.startswith(pre_marc) and MS_LOGS[2] in marc_txt
       and MS_LOGS[3] in marc_txt, 'slice archive append verbatim window lines')
    # census re-read: mid-window appendix stays census-parseable (AC-LT21)
    rc, out, _ = run(ms, 'census')
    cen = json.loads(out)
    ok(rc == 0 and cen['pass'] is True and cen['sections_total'] == 1,
       'slice census re-read green (mid-window section declared==actual)')
    # abort faces in slice mode (AC-LT22)
    ms2 = tempfile.mkdtemp(prefix='bd-mslice2-')
    mspath2 = build_ps_state(ms2, MS_LOGS)
    bad = os.path.join(ms2, 'summary.txt')
    open(bad, 'w', encoding='utf-8').write('2026-10-09 summary with no window tokens\n')
    pre2 = open(mspath2, 'rb').read()
    marc2 = os.path.join(ms2, 'logs', archive_name())
    pre_marc2 = open(marc2, 'rb').read()
    rc, out, _ = run(ms2, 'fold', '--round', 'R9011', '--fold-no', '471',
                     '--desc', 'x', '--window-slice', '3:4', '--summary-file', bad,
                     '--execute')
    ok(rc == 2 and 'token-missing' in out, 'slice token-loss abort exit 2')
    ok(open(mspath2, 'rb').read() == pre2 and open(marc2, 'rb').read() == pre_marc2
       and not os.path.exists(os.path.join(ms2, 'logs', 'state-preop-R9011.bak')),
       'slice token-loss abort zero mutation (state+archive+no backup)')
    good2 = os.path.join(ms2, 'good.txt')
    open(good2, 'w', encoding='utf-8').write(MS_SUMMARY + '\n')
    rc, out, _ = run(ms2, 'fold', '--round', 'R9012', '--fold-no', '472',
                     '--desc', 'x', '--window-slice', '3:4', '--summary-file', good2,
                     '--reserve-bytes', '78500', '--execute')
    ok(rc == 2 and 'gate-exceed' in out, 'slice gate abort exit 2')
    ok(open(mspath2, 'rb').read() == pre2 and open(marc2, 'rb').read() == pre_marc2,
       'slice gate abort zero mutation')

    # ---- fold --round strict form gate (AC-LT25, R1969 slice) ----
    sgate = tempfile.mkdtemp(prefix='bd-roundgate-')
    gpath = build_ps_state(sgate, PS_LOGS)
    gfile = os.path.join(sgate, 'summary.txt')
    open(gfile, 'w', encoding='utf-8').write(SUMMARY + '\n')
    gpre = open(gpath, 'rb').read()
    for bad in ('1968', 'x1968', 'R19', 'R1968x', 'R1968 ', '  R1968', 'r1968'):
        rc, out, err = run(sgate, 'fold', '--round', bad, '--fold-no', '473',
                           '--desc', 'bad round form', '--window-tail', '2',
                           '--summary-file', gfile)
        ok(rc == 2 and 'must match R + 4+ digits' in err,
           'fold --round strict gate rejects %r (AC-LT25)' % bad)
        ok(out == '', 'fold --round gate emits no plan JSON for %r (AC-LT25)' % bad)
        ok(open(gpath, 'rb').read() == gpre,
           'fold --round gate zero mutation for %r (AC-LT25)' % bad)
    rc, out, err = run(sgate, 'fold', '--round', '', '--fold-no', '473',
                       '--desc', 'empty round', '--window-tail', '2',
                       '--summary-file', gfile)
    ok(rc == 2 and open(gpath, 'rb').read() == gpre,
       'fold --round empty string rejected fail-closed (AC-LT25)')
    rc, out, err = run(sgate, 'fold', '--round', 'R9009', '--fold-no', '473',
                       '--desc', 'legal round form', '--window-tail', '2',
                       '--summary-file', gfile)
    gplan = json.loads(out)
    ok(rc == 0 and gplan['round_label'] == 'R9009' and gplan['would_fail'] == [],
       'fold --round legal form passes + plan round_label echo (AC-LT25)')

    # ---- fold --plan-only minimal width (AC-LTP1..AC-LTP5, R3373 slice) ----
    # The execute path always demanded a hand-picked window width, so "how many
    # lines must I fold to clear the gate" was answered outside the tool. These
    # arms pin the read-only answer against the writer that has to obey it.
    def build_big_key_state(broot, blogs, big_bytes):
        """Canonical layout plus one big NON-log key, so folding the whole log
        still cannot reach the gate (the unreachable arm)."""
        import logs_toolkit as T2
        os.makedirs(os.path.join(broot, 'src', 'os'), exist_ok=True)
        os.makedirs(os.path.join(broot, 'logs'), exist_ok=True)
        blines = ['{', '    "big":  "%s",' % ('x' * big_bytes), '    "log":  [']
        for i, s in enumerate(blogs):
            comma = ',' if i < len(blogs) - 1 else ''
            blines.append(' ' * 16 + T2.ps_escape(s) + comma)
        blines.append('            ]')
        blines.append('}')
        bpath = os.path.join(broot, 'src', 'os', 'state.json')
        with open(bpath, 'wb') as f:
            f.write('\r\n'.join(blines).encode('utf-8'))
        return bpath

    PLAN_LOGS = ['2026-11-24 R9001 filler AC-R9001 ' + 'y' * 1500 for _ in range(60)]
    PLAN_SUMMARY = '2026-11-24 roll window line AC-R9001 folded verbatim'
    pw = tempfile.mkdtemp(prefix='bd-foldplan-')
    pspath = build_ps_state(pw, PLAN_LOGS)
    pfile = os.path.join(pw, 'summary.txt')
    open(pfile, 'w', encoding='utf-8').write(PLAN_SUMMARY + '\n')
    pre_plan = open(pspath, 'rb').read()
    parc = os.path.join(pw, 'logs', archive_name())
    pre_parc = open(parc, 'rb').read()

    rc, out, err = run(pw, 'fold', '--plan-only', '--summary-file', pfile)
    pl = json.loads(out)
    W = pl['minimal_window_lines']
    ok(rc == 0 and pl['mode'] == 'plan-only' and 2 <= W < len(PLAN_LOGS),
       'plan-only answers a minimal width inside the log (AC-LTP1)')
    ok(pl['predicted_post_bytes'] <= pl['target_bytes']
       and pl['width_below_minimal_bytes'] > pl['target_bytes']
       and pl['width_below_minimal_clears_gate'] is False,
       'plan minimality witness: W clears the gate and W-1 does not (AC-LTP2)')
    ok(pl['window_token_count'] == 1 and pl['window_tokens'] == ['AC-R9001'],
       'plan reports the window token set it would have to preserve (AC-LTP1)')

    # both sides of the boundary are judged by the writer, not by the plan
    rc, out, err = run(pw, 'fold', '--round', 'R9011', '--fold-no', '910',
                       '--desc', 'plan width arm', '--window-tail', str(W),
                       '--summary-file', pfile)
    fplan = json.loads(out)
    ok(rc == 0 and fplan['predicted_bytes'] == pl['predicted_post_bytes']
       and fplan['gate_ok'] is True,
       'fold at the planned width predicts the very size the plan published (AC-LTP1)')
    rc, out, err = run(pw, 'fold', '--round', 'R9011', '--fold-no', '910',
                       '--desc', 'plan width minus one', '--window-tail', str(W - 1),
                       '--summary-file', pfile)
    ok(rc == 2 and json.loads(out)['would_fail'] == ['gate-exceed'],
       'fold one line narrower is refused by the gate (AC-LTP2)')

    # integer boundary: equality with the target still counts as clearing
    reserve_eq = pl['gate'] - pl['predicted_post_bytes']
    rc, out, err = run(pw, 'fold', '--plan-only', '--summary-file', pfile,
                       '--reserve-bytes', str(reserve_eq))
    pe = json.loads(out)
    ok(rc == 0 and pe['target_bytes'] == pl['predicted_post_bytes']
       and pe['minimal_window_lines'] == W,
       'target exactly equal to the prediction keeps the same width (AC-LTP2)')
    rc, out, err = run(pw, 'fold', '--plan-only', '--summary-file', pfile,
                       '--reserve-bytes', str(reserve_eq + 1))
    pb = json.loads(out)
    ok(rc == 0 and pb['minimal_window_lines'] == W + 1,
       'one byte tighter target needs exactly one more line (AC-LTP2)')

    # purity: a plan that answered for the same tree twice must not have written
    st_before = os.stat(pspath)
    entries_before = sorted(os.listdir(os.path.join(pw, 'logs')))
    rc, out, err = run(pw, 'fold', '--plan-only', '--summary-file', pfile)
    st_after = os.stat(pspath)
    ok(open(pspath, 'rb').read() == pre_plan
       and st_after.st_mtime_ns == st_before.st_mtime_ns
       and open(parc, 'rb').read() == pre_parc
       and sorted(os.listdir(os.path.join(pw, 'logs'))) == entries_before,
       'plan-only writes nothing: state bytes/mtime, archive and logs dir hold (AC-LTP4)')
    rc, out, err = run(pw, 'fold', '--plan-only', '--window-tail', '3',
                       '--summary-file', pfile)
    ok(rc == 2 and out == '' and 'takes no --window-tail' in err,
       'plan-only refuses a window selector by name (AC-LTP4)')

    # unreachable: a big non-log key survives every fold width
    unreach = tempfile.mkdtemp(prefix='bd-foldplan-')
    build_big_key_state(unreach, ['2026-11-24 R9002 small window AC-R9002'], 90000)
    rc, out, err = run(unreach, 'fold', '--plan-only')
    pu = json.loads(out)
    ok(rc == 2 and pu['would_fail'] == ['gate-unreachable']
       and pu['minimal_window_lines'] is None
       and pu['max_fold_post_bytes'] > pu['target_bytes'],
       'folding every line still over the gate reads gate-unreachable (AC-LTP3)')

    # a needed fold with no archive is named, and --allow-create clears the
    # reason WITHOUT creating the archive (a plan is not a writer)
    am = tempfile.mkdtemp(prefix='bd-foldplan-')
    build_ps_state(am, PLAN_LOGS, archive_text=None)
    amfile = os.path.join(am, 'summary.txt')
    open(amfile, 'w', encoding='utf-8').write(PLAN_SUMMARY + '\n')
    rc, out, err = run(am, 'fold', '--plan-only', '--summary-file', amfile)
    pa = json.loads(out)
    ok(rc == 2 and pa['would_fail'] == ['archive-missing']
       and pa['minimal_window_lines'] >= 2,
       'a needed fold with no archive reads archive-missing (AC-LTP3)')
    rc, out, err = run(am, 'fold', '--plan-only', '--summary-file', amfile,
                       '--allow-create')
    ok(rc == 0 and json.loads(out)['would_fail'] == []
       and not os.path.exists(os.path.join(am, 'logs', archive_name())),
       'allow-create clears the reason and still creates nothing (AC-LTP3)')

    # the assumption is declared, and a longer summary moves the prediction
    rc, out, err = run(pw, 'fold', '--plan-only')
    pas = json.loads(out)
    ok(rc == 0 and pas['summary_source'] == 'assumed'
       and pas['summary_item_bytes'] == T.PLAN_SUMMARY_ITEM_BYTES
       and pas['minimal_window_lines'] >= W,
       'no summary file reads a declared assumption and never a smaller width (AC-LTP5)')
    pfile2 = os.path.join(pw, 'summary2.txt')
    open(pfile2, 'w', encoding='utf-8').write(PLAN_SUMMARY + 'z' * 50 + '\n')
    rc, out, err = run(pw, 'fold', '--plan-only', '--summary-file', pfile2)
    p2 = json.loads(out)
    ok(rc == 0 and p2['summary_source'] == 'file'
       and p2['summary_item_bytes'] - pl['summary_item_bytes'] == 50
       and p2['minimal_window_lines'] >= W
       and p2['predicted_post_bytes'] >= pl['predicted_post_bytes'],
       'a +50 byte summary moves the reported item width by exactly +50 (AC-LTP5)')

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

    # ---- census --json (AC-LTC1..AC-LTC4, R3372) ----
    # The flag buys a reader a CONTRACT: one document, keys in the emitted
    # order, one trailing newline, verdict exit code unchanged, zero writes.
    # Measured on the fixture so the arms do not depend on today's live tree.
    rc_off, out_off, _ = run(cf1, 'census')
    rc_on, out_on, _ = run(cf1, 'census', '--json')
    rc_on2, out_on2, _ = run(cf1, 'census', '--json')
    try:
        doc_on = json.loads(out_on)
    except ValueError:
        doc_on = None
    ok(doc_on is not None and isinstance(doc_on, dict) and rc_on == rc_off,
       'census --json exits like the default mode and emits one document AC-LTC1')
    ok(list(doc_on or {}) == list(json.loads(out_off)),
       'census --json key ORDER equals the default block AC-LTC1')
    ok(out_on == out_off and out_on2 == out_on,
       'census --json byte-identical to default and repeatable AC-LTC2')
    def tree_state(root):
        rows = []
        for dirpath, _dirnames, filenames in os.walk(root):
            for name in filenames:
                p = os.path.join(dirpath, name)
                rows.append((os.path.relpath(p, root), open(p, 'rb').read(),
                             os.stat(p).st_mtime_ns))
        return sorted(rows)

    pre_tree = tree_state(cf1)
    rc_bad, out_bad, _ = run(cf1, 'census', '--bogus-flag')
    post_tree = tree_state(cf1)
    ok(pre_tree == post_tree and rc_bad == 2 and out_bad == '',
       'census --json writes nothing and an unknown flag fails closed AC-LTC3')
    ok(rc_on == (0 if (doc_on or {}).get('pass') else 2)
       and rc_off == (0 if json.loads(out_off).get('pass') else 2),
       'census verdict exit code mirrors pass in BOTH modes AC-LTC4')
    rc_fj, out_fj, _ = run(cf2, 'census', '--json')
    rc_fd, out_fd, _ = run(cf2, 'census')
    ok(rc_fj == 2 == rc_fd and out_fj == out_fd,
       'census --json keeps exit 2 and identical bytes on a failing tree AC-LTC4')

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

    # (viii) header shapes (AC-CEN1..2, pinned in src/os/backlog.md R3211
    # BEFORE this edit): five non-canonical header shapes and one annotation
    ARC_V = ('# --- R10 fold append (2026-10-09, 2 lines verbatim: pair, fold R1 window)\n'
             '2026-10-09 R10 a D-20260930-19\n'
             '2026-10-09 R10 b\n'
             '# --- 3113 fold append (2026-10-09, 1 lines verbatim: x, fold R2 window)\n'
             '2026-10-09 R3113 a\n'
             '# --- R2472b fold append (2026-10-09, 1 lines verbatim: y, fold R3 window)\n'
             '2026-10-09 R2472b a\n'
             '# --- R2924-R2925 fold append (2026-10-09, 1 lines verbatim: z, fold R4 window)\n'
             '2026-10-09 R2925 a\n'
             '# --- Fold R2484 (2026-11-06) log items 1..78 ---\n'
             '2026-10-09 R2484 a\n'
             '## Fold R2393\n'
             '2026-10-09 R2393 a\n'
             '# --- 2026-10-09 R2407 repair: annotation stays in the body\n')
    cf8, _ = build_census_fixture(
        ['2026-10-09 window refs ' + SEC + 'R2925 and ' + SEC + 'R3113, both embedded'],
        ARC_V)
    rc, out, _ = run(cf8, 'census')
    cen8 = json.loads(out)
    ok(rc == 0 and cen8['sections_total'] == 6 and cen8['header_lines'] == 7
       and cen8['annotation_lines'] == 1 and cen8['unlabeled_sections'] == []
       and cen8['body_header_lines'] == 0,
       'census variant headers: 6 sections, 7 header lines, 1 annotation (AC-CEN1)')
    ok(cen8['section_line_mismatches'] == [] and cen8['pass'] is True,
       'census variant headers declared==actual, no absorption (AC-CEN2)')
    ok(cen8['pointer_lines'][0]['pointers'] == ['R2925', 'R3113']
       and cen8['pointer_lines'][0]['dangling'] == []
       and cen8['section_aliases'] == {'R2925': 'R2924'},
       'census range alias resolves + missing-R normalised (AC-CEN2)')
    ok(cen['header_lines'] == 3 and cen['annotation_lines'] == 0
       and cen['body_header_lines'] == 0 and cen['pass'] is True,
       'census canonical fixture header accounting unchanged (AC-CEN1)')

    # (ix) residual mismatch adjudication (AC-CEN4..6, pinned in
    # src/os/backlog.md R3212 BEFORE this edit). The two pre-existing
    # declared!=actual residuals are closed on a per-line face, not on a wish
    # to be green: the annotation stays counted as body, and the appended line
    # is proven unique so closing the account loses nothing.
    import logs_toolkit as T9
    LIVE = os.path.abspath(os.path.join(
        os.path.dirname(os.path.abspath(__file__)), os.pardir, os.pardir))
    live_files, live_sections, _hstats = T9.parse_archives(LIVE)
    b2405 = [l for l in live_sections['R2405']['lines'] if l.strip()]
    b2907 = [l for l in live_sections['R2907']['lines'] if l.strip()]
    ok((live_sections['R2405']['declared'], len(b2405)) == (21, 23)
       and (live_sections['R2907']['declared'], len(b2907)) == (20, 21),
       'live residuals stay 21/23 and 20/21 (AC-CEN5)')
    ok(b2405[-2].startswith('# --- 2026-11-03 R2407 repair:')
       and b2405[-1].startswith('2026-11-03 R2395 closeout disclosures,'
                                ' measured not guessed:')
       and b2907[-1].startswith('R2893 tokens: local=~23k api=0'),
       'each residual is one annotation plus one appended round line (AC-CEN5)')
    # the annotation is STILL body: dropping it would read 22/21 and still
    # mismatch, so the counting definition is left alone on purpose.
    ok(sum(1 for l in b2405 if l.startswith('# --- ')) == 1
       and len(b2405) - 1 == 22,
       'annotation counted as body, exclusion would still mismatch (AC-CEN5)')
    hay = []
    for _month, _finfo in sorted(live_files.items()):
        with open(_finfo['path'], 'rb') as _fh:
            hay.append(_fh.read().decode('utf-8'))
    with open(os.path.join(LIVE, 'src', 'os', 'state.json'),
              encoding='utf-8') as _fh:
        _live_items = json.load(_fh)['log']
    # a RECORD is a line that begins with the text; a quotation inside a later
    # round's prose is not a second record. MY OWN ARM WENT RED FIRST: a bare
    # substring count read 2 because the R3212 measured line quotes both
    # markers, so the arm was re-expressed by shape rather than loosened.
    _marks = (b2405[-1][:60], b2907[-1][:60])
    _arc = [sum(1 for _t in hay for _ln in _t.split('\n')
                if _ln.strip().startswith(_m)) for _m in _marks]
    _live = [sum(1 for _l in _live_items if _l.startswith(_m))
             for _m in _marks]
    ok(_arc == [1, 1] and _live == [0, 0],
       'each appended line is one archive record and no live item (AC-CEN5)')
    rc, out, _ = run(LIVE, 'census')
    live_cen = json.loads(out)
    rounds_seen = set(e['round'] for e in live_cen['section_line_mismatches'])
    ok(rounds_seen == {'R1317', 'R1823', 'R2405', 'R2907'},
       'measured residual set is the four known rounds (AC-CEN6)')
    kpath = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         'census_known_findings.json')
    with open(kpath, encoding='utf-8') as _fh:
        krows = {e['round']: e.get('reason', '')
                 for e in json.load(_fh)['section_line_mismatches']}
    ok(all(k in krows and krows[k] for k in rounds_seen)
       and all(n in krows['R2405'] for n in ('21', '23', 'R2395', 'R2407'))
       and all(n in krows['R2907'] for n in ('20', '21', 'R2893', '590400e7')),
       'every residual adjudicated with numbers and source (AC-CEN6)')
    ok(rc == 0 and live_cen['pass'] is True
       and live_cen['unknown_mismatch_count'] == 0
       and len(live_cen['section_line_mismatches']) == 4
       and all(e['adjudicated'] for e in live_cen['section_line_mismatches']),
       'live census green with all four findings visible (AC-CEN4)')

    # ---- closeout EOL repair (AC-EO1..EO6, R1705 slice) ----
    # fresh canonical PS-layout state (CRLF) so this section is self-contained
    build_ps_state(root, ['2026-10-10 R1705 eol case line one D-20261010-01',
                          '2026-10-10 R1705 tokens: local=1 api=0',
                          '2026-10-10 R1705 eol case line three'],
                   archive_text=None)
    spath_eo = os.path.join(root, 'src', 'os', 'state.json')
    healthy = open(spath_eo, 'rb').read()
    # healthy check: exit 0, full profile fields (AC-EO2)
    rc, out, _ = run(root, 'eol')
    eo = json.loads(out)
    ok(rc == 0 and eo['mode'] == 'check' and eo['layout_ok'] and eo['bare_lf'] == 0,
       'eol check healthy CRLF state exit 0')
    ok(eo['crlf'] == eo['total_lf'] and eo['lone_cr'] == 0
       and eo['bytes'] == os.path.getsize(spath_eo),
       'eol profile fields (crlf==total_lf, lone_cr 0, bytes exact)')
    # fix no-op on healthy file: zero write (AC-EO4)
    rc, out, _ = run(root, 'eol', '--fix', '--execute')
    ok(rc == 0 and json.loads(out)['written'] is False,
       'eol fix no-op on healthy file (nothing to fix)')
    # LF-ified copy: check exits 2 with bare_lf FLAG (AC-EO2)
    lfpath = os.path.join(root, 'lf_state.json')
    with open(lfpath, 'wb') as f:
        f.write(healthy.replace(b'\r\n', b'\n'))
    rc, out, _ = run(root, 'eol', '--file', lfpath)
    eo3 = json.loads(out)
    ok(rc == 2 and eo3['bare_lf'] > 0 and eo3['layout_ok'] is False,
       'eol check bare-LF file exit 2 FLAG')
    # dry-run: zero mutation + plan with content_eq/json_eq (AC-EO1/EO3)
    rc, out, _ = run(root, 'eol', '--file', lfpath, '--fix')
    eo4 = json.loads(out)
    ok(rc == 0 and eo4['mode'] == 'fix-dry-run' and eo4['content_eq'] is True
       and eo4['json_eq'] is True and eo4['delta_bytes'] == eo3['bare_lf'],
       'eol fix dry-run: plan + content_eq + json_eq, delta == bare_lf count')
    ok(open(lfpath, 'rb').read() == healthy.replace(b'\r\n', b'\n'),
       'eol dry-run zero mutation (bytes unchanged)')
    # execute: full chain fidelity (AC-EO3/EO4)
    rc, out, _ = run(root, 'eol', '--file', lfpath, '--fix', '--execute')
    eo5 = json.loads(out)
    ok(rc == 0 and eo5['written'] is True and eo5['post_bare_lf'] == 0
       and eo5['predicted_eq_actual'] is True,
       'eol fix execute: written + post bare_lf 0 + predicted==actual')
    ok(open(lfpath, 'rb').read() == healthy,
       'eol repaired bytes == original healthy CRLF bytes (roundtrip identity)')
    ok(json.load(open(lfpath, encoding='utf-8')) == json.load(open(spath_eo, encoding='utf-8')),
       'eol json semantics preserved (deep-equal objects)')
    # idempotent second execute: no-op (AC-EO4)
    rc, out, _ = run(root, 'eol', '--file', lfpath, '--fix', '--execute')
    ok(rc == 0 and json.loads(out)['written'] is False, 'eol fix idempotent second run no-op')
    # non-JSON target via --file: json_eq None, content surgery still valid (AC-EO3)
    txtpath = os.path.join(root, 'plain.txt')
    with open(txtpath, 'wb') as f:
        f.write('alpha\nbeta\n'.encode('utf-8'))
    rc, out, _ = run(root, 'eol', '--file', txtpath, '--fix', '--execute')
    eo7 = json.loads(out)
    ok(rc == 0 and eo7['json_eq'] is None and eo7['post_bare_lf'] == 0
       and open(txtpath, 'rb').read() == b'alpha\r\nbeta\r\n',
       'eol non-JSON --file target: json_eq None + CRLF repair')

    # ---- fold refusal hints + indent conservation (AC-LF1..LF3, R1716) ----
    # fold CRLF-disease fixture: LF-ified canonical state -> fold refuses;
    # stderr hint names the eol --fix repair path; zero mutation (AC-LF1)
    sf5 = tempfile.mkdtemp(prefix='bd-fold-')
    build_ps_state(sf5, ['2026-10-10 R1716 line one D-20261010-01',
                         '2026-10-10 R1716 tokens: local=1 api=0'])
    sfile5 = os.path.join(sf5, 'summary.txt')
    open(sfile5, 'w', encoding='utf-8').write('2026-10-10 roll line\n')
    p5 = os.path.join(sf5, 'src', 'os', 'state.json')
    h5 = open(p5, 'rb').read()
    with open(p5, 'wb') as f:
        f.write(h5.replace(b'\r\n', b'\n'))
    rc, _, err = run(sf5, 'fold', '--round', 'R9005', '--fold-no', '459',
                     '--desc', 'x', '--window-tail', '1', '--summary-file', sfile5)
    ok(rc == 2 and 'E_STATE_LAYOUT: CRLF layout not found' in err
       and 'hint: run: python src/os/logs_toolkit.py eol --fix --execute' in err,
       'fold CRLF refusal stderr carries eol --fix repair hint (AC-LF1)')
    ok(open(p5, 'rb').read() == h5.replace(b'\r\n', b'\n'),
       'fold CRLF refusal zero mutation')
    # the hinted repair actually unblocks fold (message chain semantics)
    rc, out, _ = run(sf5, 'eol', '--fix', '--execute')
    ok(rc == 0 and json.loads(out)['written'] is True,
       'hinted eol --fix --execute repairs the CRLF disease')
    ok(open(p5, 'rb').read() == h5,
       'repaired bytes == original canonical CRLF (roundtrip identity)')
    # fold indent-disease fixture (R1710 form: a json.dump re-write
    # collapsed the 16-space item indent to 8) (AC-LF1): mismatch refusal
    # + indent hint + zero mutation
    sf6 = tempfile.mkdtemp(prefix='bd-fold-')
    build_ps_state(sf6, ['2026-10-10 R1716 line one D-20261010-02',
                         '2026-10-10 R1716 tokens: local=1 api=0'])
    sfile6 = os.path.join(sf6, 'summary.txt')
    open(sfile6, 'w', encoding='utf-8').write('2026-10-10 roll line D-20261010-02\n')
    p6 = os.path.join(sf6, 'src', 'os', 'state.json')
    h6 = open(p6, 'rb').read()
    bad6 = h6.replace(b'\r\n' + b' ' * 16 + b'"', b'\r\n' + b' ' * 8 + b'"')
    with open(p6, 'wb') as f:
        f.write(bad6)
    rc, _, err = run(sf6, 'fold', '--round', 'R9006', '--fold-no', '460',
                     '--desc', 'x', '--window-tail', '1', '--summary-file', sfile6)
    ok(rc == 2 and 'PS item-line layout mismatch' in err
       and 'hint: run: python src/os/logs_toolkit.py eol --fix-indent --execute' in err,
       'fold indent refusal stderr carries --fix-indent hint (AC-LF1/AC-FI5)')
    ok(open(p6, 'rb').read() == bad6, 'fold indent refusal zero mutation')
    # eol check on the indent-disease fixture: exit 2 with CRLF face green
    # and indent face red (AC-LF2) - the R1710 three-round escape is closed
    rc, out, _ = run(sf6, 'eol')
    e6 = json.loads(out)
    ok(rc == 2 and e6['layout_ok'] is True and e6['log_block_found'] is True
       and e6['indent_anomaly'] == 2 and e6['indent16_lines'] == 0
       and e6['indent_ok'] is False,
       'eol check indent-disease exit 2 (CRLF green, indent red) (AC-LF2)')
    # eol fix scope law (AC-LF3): fix is EOL-only, indent bytes untouched
    rc, out, _ = run(sf6, 'eol', '--fix', '--execute')
    e7 = json.loads(out)
    ok(rc == 0 and e7['written'] is False
       and open(p6, 'rb').read() == bad6,
       'eol fix no-op on indent-only disease (scope law, AC-LF3)')
    # eol check on the repaired canonical fixture: both faces green plus
    # the new profile fields (AC-LF2)
    rc, out, _ = run(sf5, 'eol')
    e8 = json.loads(out)
    ok(rc == 0 and e8['indent_ok'] is True and e8['indent_anomaly'] == 0
       and e8['indent16_lines'] == 2 and e8['log_item_lines'] == 2
       and e8['log_block_found'] is True,
       'eol check healthy canonical: indent face green + profile fields (AC-LF2)')
    # non-JSON --file: no log block -> indent face n/a, not red (AC-LF2)
    rc, out, _ = run(root, 'eol', '--file', txtpath)
    e9 = json.loads(out)
    ok(rc == 0 and e9['log_block_found'] is False and e9['indent_ok'] is True,
       'eol check non-JSON --file: indent face n/a not red (AC-LF2)')

    # ---- eol --fix-indent: indent-disease repair toolized ----
    # (AC-FI1..FI7, pre-registered in state/queue/tech.md R1717 claim)
    # AC-FI1: --fix and --fix-indent are mutually exclusive (scope law)
    rc, _, err = run(sf6, 'eol', '--fix', '--fix-indent')
    ok(rc == 2 and 'mutually exclusive' in err,
       'eol --fix + --fix-indent mutually exclusive (AC-FI1)')
    # AC-FI3: dry-run on the indent-disease fixture (sf6 still bad6):
    # predicts both repairs, triple verify green, zero mutation
    rc, out, _ = run(sf6, 'eol', '--fix-indent')
    fi = json.loads(out)
    ok(rc == 0 and fi['mode'] == 'fix-indent-dry-run'
       and fi['repaired_lines'] == 2 and fi['verify_pass'] is True
       and fi['content_eq'] is True and fi['eol_eq'] is True
       and fi['json_eq'] is True,
       'fix-indent dry-run: 2 repairs predicted + triple verify (AC-FI3)')
    ok(open(p6, 'rb').read() == bad6, 'fix-indent dry-run zero mutation (AC-FI3)')
    # AC-FI4: execute full chain - atomic write, post anomaly 0,
    # predicted==actual, repaired bytes == original canonical (roundtrip)
    rc, out, _ = run(sf6, 'eol', '--fix-indent', '--execute')
    fi2 = json.loads(out)
    ok(rc == 0 and fi2['written'] is True and fi2['repaired_lines'] == 2
       and fi2['post_indent_anomaly'] == 0 and fi2['post_indent_ok'] is True
       and fi2['predicted_eq_actual'] is True,
       'fix-indent execute: post indent_ok + predicted==actual (AC-FI4)')
    ok(open(p6, 'rb').read() == h6,
       'repaired bytes == original canonical (indent roundtrip identity)')
    rc, out, _ = run(sf6, 'eol')
    ok(rc == 0 and json.loads(out)['indent_ok'] is True,
       'eol check green after fix-indent (chain closure)')
    # AC-FI4: idempotent second run - no-op zero write
    rc, out, _ = run(sf6, 'eol', '--fix-indent', '--execute')
    fi3 = json.loads(out)
    ok(rc == 0 and fi3['written'] is False and fi3['repaired_lines'] == 0,
       'fix-indent idempotent second run no-op (AC-FI4)')
    # hinted repair unblocks fold (message chain semantics, R1716 CRLF analog)
    rc, out, _ = run(sf6, 'fold', '--round', 'R9007', '--fold-no', '461',
                     '--desc', 'x', '--window-tail', '1', '--summary-file', sfile6)
    ok(rc == 0 and json.loads(out)['would_fail'] == [],
       'fold dry-run unblocked after hinted fix-indent repair')
    # AC-FI5: fresh indent-disease fixture - refusal hint names the flag
    sf7 = tempfile.mkdtemp(prefix='bd-fold-')
    build_ps_state(sf7, ['2026-10-10 R1717 line one D-20261010-04',
                         '2026-10-10 R1717 tokens: local=1 api=0'])
    sfile7 = os.path.join(sf7, 'summary.txt')
    open(sfile7, 'w', encoding='utf-8').write('2026-10-10 roll line D-20261010-04\n')
    p7 = os.path.join(sf7, 'src', 'os', 'state.json')
    h7 = open(p7, 'rb').read()
    bad7 = h7.replace(b'\r\n' + b' ' * 16 + b'"', b'\r\n' + b' ' * 8 + b'"')
    with open(p7, 'wb') as f:
        f.write(bad7)
    rc, _, err = run(sf7, 'fold', '--round', 'R9008', '--fold-no', '462',
                     '--desc', 'x', '--window-tail', '1', '--summary-file', sfile7)
    ok(rc == 2 and 'PS item-line layout mismatch' in err
       and 'hint: run: python src/os/logs_toolkit.py eol --fix-indent --execute' in err,
       'fold indent refusal hint names --fix-indent --execute (AC-FI5)')
    ok(open(p7, 'rb').read() == bad7, 'fold indent refusal zero mutation (AC-FI5)')
    # hinted repair chain actually unblocks fold (AC-FI5 semantics)
    rc, out, _ = run(sf7, 'eol', '--fix-indent', '--execute')
    ok(rc == 0 and json.loads(out)['written'] is True,
       'hinted eol --fix-indent --execute repairs the indent disease')
    ok(open(p7, 'rb').read() == h7, 'hinted repair roundtrip identity (AC-FI5)')
    # AC-FI2: non-state --file no-op + healthy-state no-op
    rc, out, _ = run(root, 'eol', '--fix-indent', '--execute', '--file', txtpath)
    fin = json.loads(out)
    ok(rc == 0 and fin['written'] is False,
       'fix-indent non-state --file no-op not red (AC-FI2)')
    rc, out, _ = run(sf5, 'eol', '--fix-indent', '--execute')
    fin2 = json.loads(out)
    ok(rc == 0 and fin2['written'] is False and fin2['repaired_lines'] == 0,
       'fix-indent healthy state no-op zero write (AC-FI2)')

    # ---- pre-fold bare-round pointer reading (AC-BRC1..AC-BRC6, R3379 slice) ----
    # Pinned in state/queue/explore.md R3176 a before this code. A bare round
    # number is not a PAT token, so this face measures what a fold would lose
    # instead of widening the token law.
    def build_round_state(items):
        rf = tempfile.mkdtemp(prefix='bd-rounds-')
        os.makedirs(os.path.join(rf, 'src', 'os'))
        os.makedirs(os.path.join(rf, 'logs'))
        rp = os.path.join(rf, 'src', 'os', 'state.json')
        with open(rp, 'wb') as f:
            f.write((json.dumps({'tick': 3, 'log': items},
                                ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
        return rf, rp

    R_LOGS = ['2026-11-20 R8001 first item AC-R8001 sits inside a token',
              '2026-11-21 R8002 second item',
              '2026-11-22 R8003 third item']
    rroot, rpath = build_round_state(R_LOGS)
    rsumm = os.path.join(rroot, 'logs', 'sum-R3379.txt')
    open(rsumm, 'wb').write(b'one sentence naming R8002 only\n')
    rrc, rout, _ = run(rroot, 'rounds', '--window-tail', '2', '--file', rsumm)
    rdoc = json.loads(rout)
    ok(rrc == 0 and list(rdoc.keys()) == [
        'state_path', 'window', 'summary_file', 'total', 'covered_by_summary',
        'covered_by_live', 'lost', 'rounds'],
       'rounds document keys are pinned in order (AC-BRC1)')
    ok(list(rdoc['window'].keys()) == ['mode', 'start', 'end', 'items']
       and all(list(r.keys()) == ['round', 'in_summary', 'in_live', 'lost']
               for r in rdoc['rounds']),
       'window and every row carry the pinned keys (AC-BRC1)')
    ok([r['round'] for r in rdoc['rounds']] == ['R8002', 'R8003']
       and rdoc['window'] == {'mode': 'tail', 'start': 2, 'end': 3, 'items': 2},
       'the tail window lists exactly its own rounds and reaches no further (AC-BRC4)')
    cov = {r['round']: r for r in rdoc['rounds']}
    ok(cov['R8002']['in_summary'] and not cov['R8002']['lost']
       and rdoc['covered_by_summary'] == 1,
       'a round named in the summary is covered (AC-BRC2)')
    ok(not cov['R8003']['in_summary'] and not cov['R8003']['in_live']
       and cov['R8003']['lost'] and rdoc['lost'] == 1,
       'a round named nowhere reads lost, and the face says so (AC-BRC3)')
    arc, aout, _ = run(rroot, 'rounds', '--window-slice', '1:1')
    adoc = json.loads(aout)
    ok([r['round'] for r in adoc['rounds']] == ['R8001']
       and adoc['rounds'][0]['in_live'] is False,
       'the bare R8001 is listed while AC-R8001 inside a PAT token is not (AC-BRC1)')
    s4, s4out, _ = run(rroot, 'rounds', '--window-tail', '2', '--file', rsumm,
                       '--strict')
    ok(s4 == 4 and json.loads(s4out)['lost'] == 1,
       '--strict reddens on a lost round while the default stays rc=0 (AC-BRC3)')
    b_rc, b_out, b_err = run(rroot, 'rounds', '--window-slice', '2:9')
    ok(b_rc == 2 and b_out.strip() == '' and 'E_WINDOW_RANGE' in b_err,
       'an out-of-range slice is refused by name with empty stdout (AC-BRC4)')
    tw_rc, tw_out, _ = run(rroot, 'rounds', '--window-tail', '99')
    ok(tw_rc == 2 and tw_out.strip() == '',
       'a tail wider than the log is refused with empty stdout (AC-BRC4)')
    before_r = os.stat(rpath)
    listing_r = sorted(os.listdir(os.path.dirname(rpath)))
    first_r = run(rroot, 'rounds', '--window-tail', '2', '--file', rsumm)[1]
    second_r = run(rroot, 'rounds', '--window-tail', '2', '--file', rsumm)[1]
    after_r = os.stat(rpath)
    ok(first_r == second_r
       and (before_r.st_size, before_r.st_mtime_ns)
       == (after_r.st_size, after_r.st_mtime_ns)
       and sorted(os.listdir(os.path.dirname(rpath))) == listing_r,
       'two runs are byte-identical and write nothing (AC-BRC5)')
    ok(T.PAT.pattern == (r'(?:AC|BD|C|D|O|P|T|XL|OH|R)'
                         r'-[0-9A-Za-z][0-9A-Za-z]*(?:-[0-9A-Za-z]+)*')
       and T.ROUND_TAG.pattern == r'\bR\d{3,5}\b',
       'no token law moved: PAT and round_tag keep their patterns (AC-BRC6)')

    # ---- fold refuses to erase a bare round pointer (AC-RLW1..AC-RLW6, R3380) ----
    # Pinned in src/os/backlog.md R3380 BEFORE this code. `rounds` (R3379) reads
    # the risk; this block pins the writer's refusal, which reuses that reading
    # instead of re-deriving it.
    RL_LOGS = ['2026-11-20 R8001 alpha item',
               '2026-11-21 R8002 beta item',
               '2026-11-22 R8003 gamma item']
    rlroot = tempfile.mkdtemp(prefix='bd-roundloss-')
    rlpath = build_ps_state(rlroot, RL_LOGS)
    rlarc = os.path.join(rlroot, 'logs', archive_name())
    rl_dir_before = sorted(os.listdir(os.path.join(rlroot, 'logs')))
    rl_stat_before = os.stat(rlpath)
    rl_arc_before = open(rlarc, 'rb').read()
    rl_rc, rl_out, rl_err = run(rlroot, 'fold', '--round', 'R9201', '--fold-no',
                               '921', '--desc', 'round-loss refusal',
                               '--window-tail', '2',
                               '--summary-sentence', 'folded two items')
    rl_plan = json.loads(rl_out)
    rl_stat_after = os.stat(rlpath)
    ok(rl_rc == 2 and rl_plan['round_pointer_lost'] == ['R8002', 'R8003']
       and 'round-lost' in rl_plan['would_fail'],
       'an unnamed bare round in the window reddens the fold (AC-RLW1)')
    ok('E_ROUND_LOST' in rl_err and 'R8002' in rl_err and 'R8003' in rl_err,
       'the refusal is named and lists every lost round (AC-RLW1)')
    ok((rl_stat_before.st_size, rl_stat_before.st_mtime_ns)
       == (rl_stat_after.st_size, rl_stat_after.st_mtime_ns)
       and open(rlarc, 'rb').read() == rl_arc_before
       and sorted(os.listdir(os.path.join(rlroot, 'logs'))) == rl_dir_before,
       'the dry-run refusal writes nothing at all (AC-RLW5)')
    rc, out, _ = run(rlroot, 'fold', '--round', 'R9202', '--fold-no', '922',
                     '--desc', 'refusal on execute', '--window-tail', '2',
                     '--summary-sentence', 'folded two items', '--execute')
    ok(rc == 2 and os.stat(rlpath).st_size == rl_stat_before.st_size,
       'the execute path refuses on the same loss, before any byte is written '
       '(AC-RLW1)')
    # AC-RLW3: the writer's lost set is the reading's lost set on the same tree.
    rl3root = tempfile.mkdtemp(prefix='bd-roundloss3-')
    build_ps_state(rl3root, RL_LOGS)
    want_line, werr = T.compose_summary('folded two items', [])
    rl3sum = os.path.join(rl3root, 'logs', 'sum-rlw.txt')
    open(rl3sum, 'wb').write((want_line + '\n').encode('utf-8'))
    _, rout3, _ = run(rl3root, 'rounds', '--window-slice', '2:3',
                      '--file', rl3sum)
    rdoc3 = json.loads(rout3)
    read_lost = [r['round'] for r in rdoc3['rounds'] if r['lost']]
    _, fout3, _ = run(rl3root, 'fold', '--round', 'R9203', '--fold-no', '923',
                      '--desc', 'parity arm', '--window-slice', '2:3',
                      '--summary-file', rl3sum)
    ok(json.loads(fout3)['round_pointer_lost'] == read_lost == ['R8002', 'R8003'],
       "the fold's lost set equals the shipped rounds reading (AC-RLW3)")
    # AC-RLW4 positive control: a bare round named in the human sentence counts.
    _, pout, _ = run(rl3root, 'fold', '--round', 'R9204', '--fold-no', '924',
                     '--desc', 'positive control', '--window-tail', '2',
                     '--summary-sentence', 'items R8002 and R8003 merged')
    ok(json.loads(pout)['round_pointer_lost'] == []
       and json.loads(pout)['would_fail'] == [],
       'naming the rounds in the human sentence clears the loss (AC-RLW4)')
    # AC-RLW4 negative control: a round inside a PAT token is not a bare round.
    rl5root = tempfile.mkdtemp(prefix='bd-roundloss5-')
    build_ps_state(rl5root, ['2026-11-20 pre item',
                             '2026-11-21 AC-R8001 inside a token',
                             '2026-11-22 no round here'])
    _, tout, _ = run(rl5root, 'fold', '--round', 'R9205', '--fold-no', '925',
                     '--desc', 'pat token arm', '--window-tail', '2',
                     '--summary-sentence', 'merged window')
    ok(json.loads(tout)['round_pointer_lost'] == [],
       'a round inside a PAT token is never a bare round (AC-RLW4)')
    # AC-RLW2: --allow-round-loss declares the loss and records it.
    rl6root = tempfile.mkdtemp(prefix='bd-roundloss6-')
    rl6path = build_ps_state(rl6root, RL_LOGS)
    rl6arc = os.path.join(rl6root, 'logs', archive_name())
    rc6, out6, _ = run(rl6root, 'fold', '--round', 'R9206', '--fold-no', '926',
                       '--desc', 'declared loss', '--window-tail', '2',
                       '--summary-sentence', 'folded two items',
                       '--allow-round-loss', '--execute')
    res6 = json.loads(out6)
    ok(rc6 == 0 and res6['round_loss_declared'] is True
       and res6['round_pointer_lost'] == ['R8002', 'R8003']
       and res6['predicted_eq_actual'] is True,
       'a declared loss lands and the result carries the declaration (AC-RLW2)')
    arc6 = open(rl6arc, 'rb').read().decode('utf-8')
    ok('round-loss declared: R8002,R8003' in arc6,
       'the archive header records which pointers were declared away (AC-RLW2)')
    st6 = json.load(open(rl6path, encoding='utf-8'))
    want6, werr6 = T.compose_summary('folded two items', [])
    ok(werr6 is None and st6['log'][-1] == want6 and len(st6['log']) == 2,
       'the landed item is the composer output and the window is gone (AC-RLW2)')
    # AC-RLW6: the token law and the round shapes did not move.
    ok(T.BARE_ROUND.pattern == r'(?<![0-9A-Za-z-])R\d{3,5}(?![0-9A-Za-z-])'
       and T.PAT.pattern == (r'(?:AC|BD|C|D|O|P|T|XL|OH|R)'
                             r'-[0-9A-Za-z][0-9A-Za-z]*(?:-[0-9A-Za-z]+)*'),
       'no token or round pattern moved for this refusal (AC-RLW6)')

    # ---- weights per-item face (AC-LTW1..AC-LTW6, R3377 slice) ----
    # Pinned in state/queue/explore.md R3176 b before this code. The face is
    # read-only and its conservation is measured against the SHIPPED gauge
    # face on the same tree, not against its own arithmetic.
    def build_weight_state(items):
        wf = tempfile.mkdtemp(prefix='bd-weights-')
        os.makedirs(os.path.join(wf, 'src', 'os'))
        os.makedirs(os.path.join(wf, 'logs'))
        wp = os.path.join(wf, 'src', 'os', 'state.json')
        with open(wp, 'wb') as f:
            f.write((json.dumps({'tick': 9, 'log': items},
                                ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
        return wf, wp

    witems = [
        '2026-10-09 R1041 short line D-20260930-19',
        'unlabeled line with no round marker at all',
        '2026-10-10 R1042 ' + 'y' * 400,
        '2026-10-11 R1043 ' + 'z' * 200,
    ]
    wroot, wpath = build_weight_state(witems)
    wrc, wout, _ = run(wroot, 'weights', '--top', '3')
    wdoc = json.loads(wout)
    ok(wrc == 0 and list(wdoc.keys()) == [
        'state_path', 'item_count', 'gate', 'log_content_bytes',
        'sum_item_bytes', 'residual_bytes', 'shares_sum', 'top_n', 'top'],
       'weights document keys are pinned in order (AC-LTW1)')
    ok(all(list(r.keys()) == ['index', 'round', 'bytes',
                              'share_of_log', 'share_of_gate']
           for r in wdoc['top']),
       'every top row carries the pinned five keys (AC-LTW1)')
    g_rc, g_out, _ = run(wroot, 'gauge')
    gdoc = json.loads(g_out)
    ok(g_rc == 0
       and wdoc['log_content_bytes'] == gdoc['log_content_bytes']
       and wdoc['sum_item_bytes'] == gdoc['log_content_bytes']
       and wdoc['residual_bytes'] == 0
       and abs(wdoc['shares_sum'] - 1.0) < 1e-9,
       'weights and gauge agree on log_content_bytes; shares sum to 1 (AC-LTW2)')
    ok(wdoc['top'][0]['index'] == 2 and wdoc['top'][1]['index'] == 3
       and len(wdoc['top']) == 3
       and wdoc['top'][0]['bytes'] > wdoc['top'][1]['bytes'] > wdoc['top'][2]['bytes'],
       'top face reads heaviest first and stops at --top (AC-LTW3)')
    ok(wdoc['top'][0]['share_of_gate'] == float(wdoc['top'][0]['bytes']) / wdoc['gate'],
       'share_of_gate is the item over the published gate (AC-LTW1)')
    zero_rc, zero_out, _ = run(wroot, 'weights', '--top', '0')
    zdoc = json.loads(zero_out)
    ok(zero_rc == 0 and zdoc['top'] == [] and zdoc['item_count'] == wdoc['item_count']
       and zdoc['sum_item_bytes'] == wdoc['sum_item_bytes'],
       '--top 0 empties only the top list and moves no total (AC-LTW3)')
    tie_root, _tie_path = build_weight_state(['R1 aaa', 'R2 bbb'])
    t_rc, t_out, _ = run(tie_root, 'weights', '--top', '2')
    tdoc = json.loads(t_out)
    ok(t_rc == 0 and [r['index'] for r in tdoc['top']] == [0, 1],
       'equal weights break by array index, not by label (AC-LTW3)')
    empty_root, _empty_path = build_weight_state([])
    e_rc, e_out, _ = run(empty_root, 'weights')
    edoc = json.loads(e_out)
    ok(e_rc == 0 and edoc['item_count'] == 0 and edoc['top'] == []
       and edoc['shares_sum'] == 0.0 and edoc['residual_bytes'] == 0,
       'an empty log reads honestly empty, nothing fabricated (AC-LTW4)')
    before = os.stat(wpath)
    listing = sorted(os.listdir(os.path.dirname(wpath)))
    run(wroot, 'weights')
    run(wroot, 'weights', '--top', '99')
    after = os.stat(wpath)
    ok((before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns)
       and sorted(os.listdir(os.path.dirname(wpath))) == listing,
       'two runs write nothing and bless no new file (AC-LTW5)')
    b_rc, b_out, _ = run(wroot, 'weights', '--top', '-1')
    ok(b_rc == 2 and b_out.strip() == '',
       '--top -1 fails closed with nothing on stdout (AC-LTW6)')
    lab = {r['index']: r['round']
           for r in json.loads(run(wroot, 'weights', '--top', '9')[1])['top']}
    ok(lab.get(0) == 'R1041' and lab.get(2) == 'R1042' and lab.get(1) is None,
       'round label is the first bare round token, null when absent (AC-LTW6)')

    # ---- two-part fold summary (AC-2PS1..AC-2PS6, R3378 slice) ----
    # The old contract was "one free-text line": a machine could not verify it
    # and a reader could not read the 70-token form. These arms pin the one
    # composer and the one reading against the writer that has to obey them.
    S2_LOGS = ['2026-11-24 R9101 alpha AC-A1 ' + 'z' * 80,
               '2026-11-24 R9102 beta AC-B2',
               '2026-11-24 R9103 gamma']
    sw = tempfile.mkdtemp(prefix='bd-2ps-')
    s2path = build_ps_state(sw, S2_LOGS)

    composed, cerr = T.compose_summary('one human sentence',
                                       ['AC-B2', 'AC-A1', 'AC-B2'])
    ok(cerr is None and composed == 'one human sentence | tokens: AC-A1,AC-B2',
       'composer dedupes and sorts the token part (AC-2PS1)')
    ok(composed.count(T.SUMMARY_SEP) == 1,
       'composer emits exactly one separator (AC-2PS1)')
    ok(T.compose_summary('s', ['not a token'])[1] is not None,
       'composer refuses a non-PAT token (AC-2PS1)')

    rc, out, err = run(sw, 'fold', '--round', 'R9101', '--fold-no', '911',
                       '--desc', 'two-part dry', '--window-tail', '3',
                       '--summary-sentence', 'two part dry run',
                       '--allow-round-loss')
    pl2 = json.loads(out)
    ok(rc == 0 and pl2['summary_source'] == 'sentence'
       and pl2['summary_two_part'] is True,
       'fold --summary-sentence composes a two-part summary (AC-2PS1)')
    ok(pl2['token_missing'] == [] and pl2['token_ok'] is True,
       'the token part is the folded window own PAT set (AC-2PS2)')
    ok(pl2['summary_head'].endswith('tokens: AC-A1,AC-B2'),
       'dry-run names every window token in the summary (AC-2PS2)')

    rc, out, err = run(sw, 'fold', '--round', 'R9102', '--fold-no', '912',
                       '--desc', 'tokenless', '--window-tail', '1',
                       '--summary-sentence', 'tokenless window',
                       '--allow-round-loss')
    pl3 = json.loads(out)
    ok(rc == 0 and pl3['summary_head'].endswith('tokens: none')
       and pl3['token_ok'] is True,
       'a token-free window composes tokens: none (AC-2PS2)')

    pre_bytes = open(s2path, 'rb').read()
    pre_mtime = os.stat(s2path).st_mtime_ns
    parc_path = os.path.join(sw, 'logs', archive_name())
    pre_arc = open(parc_path, 'rb').read()
    pre_tree = sorted(os.listdir(os.path.join(sw, 'logs')))
    rc, out, err = run(sw, 'fold', '--round', 'R9103', '--fold-no', '913',
                       '--desc', 'budget', '--window-tail', '2',
                       '--summary-sentence', 'budget arm',
                       '--summary-budget', '20')
    ok(rc == 2 and 'E_SUMMARY_BUDGET' in err and out.strip() == '',
       'an over-budget summary refuses by name before any write (AC-2PS3)')
    ok(open(s2path, 'rb').read() == pre_bytes
       and os.stat(s2path).st_mtime_ns == pre_mtime
       and open(parc_path, 'rb').read() == pre_arc
       and sorted(os.listdir(os.path.join(sw, 'logs'))) == pre_tree,
       'a refused fold moves no state, archive or backup byte (AC-2PS3)')
    rc, out, err = run(sw, 'fold', '--round', 'R9104', '--fold-no', '914',
                       '--desc', 'empty', '--window-tail', '1',
                       '--summary-sentence', '   ')
    ok(rc == 2 and 'E_SUMMARY_SENTENCE' in err,
       'an empty sentence refuses by name (AC-2PS3)')
    sfile = os.path.join(sw, 'one.txt')
    open(sfile, 'w', encoding='utf-8').write('one part prose\n')
    rc, out, err = run(sw, 'fold', '--round', 'R9105', '--fold-no', '915',
                       '--desc', 'both', '--window-tail', '1',
                       '--summary-sentence', 'both', '--summary-file', sfile)
    ok(rc == 2 and 'E_SUMMARY_MODE' in err,
       'both summary flags refuse by name (AC-2PS3)')
    rc, out, err = run(sw, 'fold', '--round', 'R9106', '--fold-no', '916',
                       '--desc', 'neither', '--window-tail', '1')
    ok(rc == 2 and '--summary-file is required' in err,
       'no summary flag still reports the required error (AC-2PS3)')

    two = os.path.join(sw, 'two.txt')
    open(two, 'w', encoding='utf-8').write(
        'human sentence | tokens: AC-A1,AC-B2\n')
    pre_two = (os.path.getsize(two), os.stat(two).st_mtime_ns)
    rc, out, err = run(sw, 'summary', '--file', two)
    ok(rc == 0 and out.startswith('SUMMARY-CHECK PASS')
       and 'sentence_ok=True' in out and 'tokens_ok=True' in out,
       'the reading passes a summary that carries both parts (AC-2PS4)')
    ok((os.path.getsize(two), os.stat(two).st_mtime_ns) == pre_two,
       'the reading writes nothing to the file it read (AC-2PS4)')
    rc, out, err = run(sw, 'summary', '--file', sfile)
    ok(rc == 2 and 'E_SUMMARY_SHAPE' in out,
       'a one-part legacy summary is refused by name (AC-2PS4)')
    nonef = os.path.join(sw, 'none.txt')
    open(nonef, 'w', encoding='utf-8').write('no tokens here | tokens: none\n')
    rc, out, err = run(sw, 'summary', '--file', nonef)
    ok(rc == 0 and 'tokens=0 tokens_ok=True' in out,
       'the literal tokens: none reads as a valid second part (AC-2PS4)')

    # execute parity: the composer's line is the line the fold lands
    rc, out, err = run(sw, 'fold', '--round', 'R9107', '--fold-no', '917',
                       '--desc', 'parity dry', '--window-tail', '2',
                       '--summary-sentence', 'parity arm',
                       '--allow-round-loss')
    p_dry = json.loads(out)
    rc, out, err = run(sw, 'fold', '--round', 'R9107', '--fold-no', '917',
                       '--desc', 'parity exec', '--window-tail', '2',
                       '--summary-sentence', 'parity arm',
                       '--allow-round-loss', '--execute')
    p_exec = json.loads(out)
    ok(p_exec['post_bytes'] == p_dry['predicted_bytes']
       and p_exec['predicted_eq_actual'] is True,
       'sentence mode predicted bytes equals the landed size (AC-2PS5)')
    stp = json.load(open(s2path, encoding='utf-8'))
    landed = stp['log'][len(stp['log']) - 1]
    want, werr = T.compose_summary('parity arm', ['AC-B2'])
    ok(werr is None and landed == want,
       'the landed item is byte-identical to the composer output (AC-2PS1)')

    # AC-QREG7..AC-QREG9 (pinned in src/os/backlog.md R2917 BEFORE this edit):
    # the registry row is the ONE typed count and this suite is what refutes it,
    # so a registry edit that forgets this suite reddens HERE rather than being
    # read by nobody.
    reg_before = open(REGISTRY, 'rb').read()
    declared, row_hits = registry_crit(REGISTRY, LABEL)
    ok(open(REGISTRY, 'rb').read() == reg_before,
       'registry reader wrote nothing AC-QREG9')
    # AC-QREG8: the binding is measured on a DOCTORED copy, because a reader
    # that always answered None would still pass the positive arm below.
    anchor = 'os.path.join("..", "os", "test_logs_toolkit.py"), %d)' % declared
    ddir = tempfile.mkdtemp(prefix='qreg8_')
    dpath = os.path.join(ddir, 'reconcile_all.py')
    try:
        raw = reg_before.decode('utf-8')
        ok(raw.count(anchor) == 1, 'registry anchor unique AC-QREG8')
        grown = anchor[:-len(str(declared)) - 1] + str(declared + 1) + ')'
        open(dpath, 'wb').write(raw.replace(anchor, grown).encode('utf-8'))
        doctored = open(dpath, 'rb').read()
        ddeclared, dhits = registry_crit(dpath, LABEL)
        ok(doctored != reg_before and ddeclared == declared + 1 and dhits == 1,
           'doctored registry reads the off-by-one AC-QREG8')
        ok(open(dpath, 'rb').read() == doctored,
           'reader wrote nothing to the doctored copy AC-QREG9')
    finally:
        for name in os.listdir(ddir):
            os.remove(os.path.join(ddir, name))
        os.rmdir(ddir)
    # ASCII hygiene self-scan (AC-LT6)
    for src in (TOOL, os.path.abspath(__file__)):
        b = open(src, 'rb').read()
        ok(all(byte < 128 for byte in b), 'ASCII-only source: ' + os.path.basename(src))
    # AC-QREG7 is the LAST check on purpose: it is the only one that must know
    # the final total, and being last it reads it off CHECKS + itself instead of
    # predicting how many checks follow it (the R2901 lesson about positions).
    ok(declared == CHECKS + 1 and row_hits == 1,
       'registry row %s declares this run total=%d (read=%s rows=%d) AC-QREG7'
       % (LABEL, CHECKS + 1, declared, row_hits))

    # R2962: the closing row used to read 'SUITE PASS %d checks', a shape the
    # battery law REFUSES by design (battery_shard._counter_row needs a total
    # and a fail count; its docstring names this very shape as the refused
    # case), so this suite's 168 declared criteria were unreadable to every
    # machine reader. The count is the assertion count, and every assertion
    # passed, so the pair is equal by construction - main() never reaches this
    # line otherwise.
    print('SUITE PASS %d/%d' % (CHECKS, CHECKS))
    return 0


if __name__ == '__main__':
    sys.exit(main())
