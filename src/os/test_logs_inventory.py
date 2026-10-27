#!/usr/bin/env python3
"""test_logs_inventory.py - sandbox suite for the adaptive inventory window.

AC-LTI1..AC-LTI8 (pre-registered in state/queue/tech.md R2156, written
before this suite existed): the historical `inventory` subcommand only ever
scanned `logs/`, so every qa/*.log proof file the rounds produce was absent
from the catalog - a census that claims "the whole disk" would then be green
while blind to the evidence tree. This suite pins the multi-root reading:
default byte identity, evidence coverage, growth adaptivity, zero double
counting across overlapping roots and hard links, fail-closed root gates,
retention protection, and delivery hygiene.

ASCII-only source; stdlib only; zero network.
"""

import json
import os
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
TOOL = os.path.join(HERE, 'logs_toolkit.py')
RECONCILE = os.path.join(HERE, '..', 'sandbox', 'reconcile_all.py')
CHECKS = 0
FAILS = []


def ok(cond, cid, label):
    global CHECKS
    CHECKS += 1
    if cond:
        print('PASS %s %s' % (cid, label))
    else:
        print('FAIL %s %s' % (cid, label))
        FAILS.append('%s %s' % (cid, label))


def run(root, *args):
    p = subprocess.run([sys.executable, TOOL, '--root', root] + list(args),
                       capture_output=True)
    return (p.returncode,
            p.stdout.decode('utf-8', 'replace'),
            p.stderr.decode('utf-8', 'replace'))


def inv(root, *args):
    rc, out, err = run(root, 'inventory', *args)
    if rc != 0:
        raise AssertionError('inventory failed rc=%d err=%s' % (rc, err))
    return json.loads(out)


def build():
    root = tempfile.mkdtemp(prefix='bd-lti-')
    os.makedirs(os.path.join(root, 'src', 'os'))
    os.makedirs(os.path.join(root, 'logs'))
    os.makedirs(os.path.join(root, 'qa'))
    state = {'tick': 1,
             'log': ['2026-10-27 R1 tokens: local=1 api=0 api_reason=fixture']}
    with open(os.path.join(root, 'src', 'os', 'state.json'), 'wb') as f:
        f.write((json.dumps(state, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
    ld = os.path.join(root, 'logs')
    qd = os.path.join(root, 'qa')
    old = time.time() - 90000

    def touch(d, name, body=b'x' * 10, mtime=None):
        p = os.path.join(d, name)
        with open(p, 'wb') as f:
            f.write(body)
        if mtime is not None:
            os.utime(p, (mtime, mtime))
        return p

    # logs/: 2 archive-md, 1 lock, 72 tmp-script (70 old enough for prune),
    # 2 round-transcript, 1 other -> 78 files
    touch(ld, 'state-log-archive-2026-10.md')
    touch(ld, 'notes.md')
    touch(ld, 'round.lock', b'')
    for i in range(70):
        touch(ld, 'tmp_old_%03d.py' % (i + 1), mtime=old - i)
    for i in range(2):
        touch(ld, 'tmp_new_%03d.py' % (i + 1), mtime=time.time())
    touch(ld, 'round_20260101_000001.out', mtime=old)
    touch(ld, 'run_20260101_000002.log', mtime=old)
    touch(ld, 'other.dat')
    # qa/: 5 .log (one deliberately named like a prune candidate and old
    # enough, to prove retention never reaches the evidence tree),
    # 2 side-cars -> 7 files
    for i in range(4):
        touch(qd, 'evidence-%d.log' % (i + 1), mtime=old)
    touch(qd, 'tmp_old_evidence.log', mtime=old - 5000)
    touch(qd, 'meta.json', b'{}')
    touch(qd, 'shot.png', b'\x89PNG')
    return root, ld, qd


def names(d):
    return sorted(e.name for e in os.scandir(d) if e.is_file())


def main():
    root, ld, qd = build()

    # AC-LTI1: the legacy single-root contract is byte-identical.
    rc, out, _ = run(root, 'inventory')
    d = json.loads(out)
    ok(rc == 0 and sorted(d.keys()) == ['classes', 'logs_dir', 'total_files'],
       'AC-LTI1', 'default output key set is exactly {logs_dir, classes, total_files}')
    cls = d['classes']
    ok(d['total_files'] == 78 and sum(c['count'] for c in cls.values()) == 78,
       'AC-LTI1', 'default total_files == 78 == sum of class counts')
    ok(cls['archive-md']['count'] == 2 and cls['lock']['count'] == 1
       and cls['tmp-script']['count'] == 72
       and cls['round-transcript']['count'] == 2 and cls['other']['count'] == 1,
       'AC-LTI1', 'legacy classifier counts unchanged (2/1/72/2/1)')
    ok(cls['archive-md']['protected'] and cls['other']['protected']
       and not cls['archive-md']['prunable'] and cls['tmp-script']['prunable'],
       'AC-LTI1', 'protected/prunable flags keep the historical meaning')
    ok(len(names(ld)) == 78, 'AC-LTI1', 'zero omission: class sum equals the logs/ file count')

    # AC-LTI2: the evidence root is covered.
    d2 = inv(root, '--with-qa')
    c2 = d2['classes']
    ok(sorted(d2['roots'].keys()) == ['logs', 'qa'],
       'AC-LTI2', 'roots face names both roots')
    ok(c2['qa-evidence']['count'] == 5 and c2['evidence-other']['count'] == 2,
       'AC-LTI2', 'qa/*.log -> qa-evidence (5), everything else -> evidence-other (2)')
    ok(d2['counted_entries'] == 85 and d2['duplicates'] == 0
       and d2['total_files'] == 85,
       'AC-LTI2', 'counted_entries 85 == duplicates 0 + total_files 85')
    ok(sum(c['count'] for c in c2.values()) + d2['duplicates'] == d2['counted_entries'],
       'AC-LTI2', 'class counts plus duplicates account for every scanned entry')
    ok(d2['roots']['logs']['files'] == 78 and d2['roots']['qa']['files'] == 7,
       'AC-LTI2', 'per-root entry counts are 78 and 7')

    # AC-LTI3: growth between two readings is seen (no cache).
    for i in range(3):
        with open(os.path.join(qd, 'late-%d.log' % (i + 1)), 'wb') as f:
            f.write(b'late')
    d3 = inv(root, '--with-qa')
    ok(d3['total_files'] == d2['total_files'] + 3,
       'AC-LTI3', 'three new evidence files raise total_files by exactly 3')
    ok(d3['classes']['qa-evidence']['count'] == 8,
       'AC-LTI3', 'qa-evidence count rises 5 -> 8 (adaptive, uncached)')
    ok(d3['roots']['qa']['files'] == 10 and len(names(qd)) == 10,
       'AC-LTI3', 'zero omission after growth: root count == directory count')

    # AC-LTI4: the same directory declared twice is counted once.
    d4 = inv(root, '--roots', 'qa1=qa', '--roots', 'qa2=qa')
    ok(d4['roots']['qa1']['files'] == 10 and d4['roots']['qa2']['files'] == 10,
       'AC-LTI4', 'both overlapping roots report their own 10 entries')
    ok(d4['counted_entries'] == 98 and d4['total_files'] == 88
       and d4['duplicates'] == 10,
       'AC-LTI4', 'counted 98, unique 88, duplicates 10')
    ok(d4['classes']['qa-evidence']['count'] == 8,
       'AC-LTI4', 'class counts are not doubled by the second root')

    # AC-LTI5: a hard link across roots is one file.
    os.link(os.path.join(ld, 'other.dat'), os.path.join(qd, 'hardlink-other.log'))
    d5 = inv(root, '--with-qa')
    ok(d5['duplicates'] == 1 and d5['total_files'] == 88
       and d5['counted_entries'] == 89,
       'AC-LTI5', 'cross-root hard link adds one duplicate, zero new files')
    ok(d5['classes']['qa-evidence']['count'] == 8,
       'AC-LTI5', 'the linked inode is not counted a second time under qa-evidence')

    # AC-LTI6: bad roots fail closed, with no partial green reading.
    rc, out, err = run(root, 'inventory', '--roots', 'qaonly')
    ok(rc == 2 and '{' not in out and 'LABEL=DIR' in err,
       'AC-LTI6', 'root spec without "=" exits 2 and prints no JSON')
    rc, out, err = run(root, 'inventory', '--roots', 'ghost=no-such-dir')
    ok(rc == 3 and '{' not in out,
       'AC-LTI6', 'missing root directory exits 3 and prints no JSON')
    rc, out, err = run(root, 'inventory', '--roots', 'qa=qa', '--roots', 'qa=qa')
    ok(rc == 2 and '{' not in out,
       'AC-LTI6', 'duplicate root label exits 2 and prints no JSON')

    # AC-LTI7: retention never reaches the evidence tree.
    d7 = inv(root, '--with-qa')
    ok(d7['classes']['qa-evidence']['protected'] is True
       and d7['classes']['qa-evidence']['prunable'] is False
       and d7['classes']['evidence-other']['protected'] is True
       and d7['classes']['evidence-other']['prunable'] is False,
       'AC-LTI7', 'both evidence classes are protected and non-prunable')
    before = names(qd)
    sys.path.insert(0, HERE)
    import logs_toolkit as T
    plan, _notes = T.prune_plan(root, T.DEFAULT_FLOOR)
    victims = [p for bucket in plan.values() for p in bucket]
    ok(len(victims) == 10,
       'AC-LTI7', 'prune selects 10 old logs/ tmp-scripts (70 past the floor - keep 60)')
    ok(all(os.path.dirname(p) == ld for p in victims),
       'AC-LTI7', 'every prune victim lives under logs/, none under qa/')
    ok(not any(n in names(qd) for n in (os.path.basename(p) for p in victims)),
       'AC-LTI7', 'no evidence filename appears in the prune plan')
    rc, out, _ = run(root, 'prune')
    ok(rc == 0 and json.loads(out)['to_delete_total'] == 10,
       'AC-LTI7', 'prune dry-run reports the same 10 victims and stays a dry run')
    ok(names(qd) == before,
       'AC-LTI7', 'the evidence tree is byte-frozen by a prune dry-run')

    # AC-LTI8: delivery hygiene.
    src = open(TOOL, encoding='utf-8').read()
    ok(all(ord(ch) < 128 for ch in src),
       'AC-LTI8', 'tool source is pure ASCII')
    import re
    net = re.findall(r'^\s*(?:import|from)\s+(socket|http|urllib|requests|ftplib)\b',
                     src, re.M)
    ok(net == [], 'AC-LTI8', 'tool source has zero network imports')
    rc_a, out_a, _ = run(root, 'inventory', '--with-qa')
    rc_b, out_b, _ = run(root, 'inventory', '--with-qa')
    ok(rc_a == 0 and rc_b == 0 and out_a == out_b,
       'AC-LTI8', 'two runs produce byte-identical output')
    wiring = open(RECONCILE, encoding='utf-8').read()
    ok('"os-logs-inventory"' in wiring and 'test_logs_inventory.py' in wiring,
       'AC-LTI8', 'wired into reconcile_all as os-logs-inventory')

    total = CHECKS
    if FAILS:
        print('SUITE FAIL %d/%d' % (total - len(FAILS), total))
        for f in FAILS:
            print('FAILED: ' + f)
        return 1
    print('SUITE PASS %d/%d' % (total, total))
    return 0


if __name__ == '__main__':
    sys.exit(main())