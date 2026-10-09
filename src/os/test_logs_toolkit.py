#!/usr/bin/env python3
"""test_logs_toolkit.py - sandbox test suite for src/os/logs_toolkit.py.

AC-LT6 (pre-registered in state/queue/tech.md R1686 claim line, written
before this code): sandbox fixture tree, subprocess CLI surface, asserts
gauge/inventory/prune/catalog behaviors incl. protected-file survival,
mtime floor, idempotence, and prune predicted==actual. Exit 0 = all green.
ASCII-only source; stdlib only; zero network.
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

    # ASCII hygiene self-scan (AC-LT6)
    for src in (TOOL, os.path.abspath(__file__)):
        b = open(src, 'rb').read()
        ok(all(byte < 128 for byte in b), 'ASCII-only source: ' + os.path.basename(src))

    print('SUITE PASS %d checks' % CHECKS)
    return 0


if __name__ == '__main__':
    sys.exit(main())
