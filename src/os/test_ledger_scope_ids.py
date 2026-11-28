"""test_ledger_scope_ids.py - the scope face names the archive gaps it counted.

Criteria AC-AMID1..AC-AMID5 were pinned in src/os/backlog.md at R3641 BEFORE
src/os/ledger_lines.py changed and before this file existed.

The measured gap (this window): the union face has always published
`archived_missing=<count>` and never the rounds behind it, while
audit_scope() holds the id list and the archive audit face prints it. A
reader of the default face could not tell WHICH frozen rounds the count
named. The ids now ride the same `scope:` line as a capped tail, because
AC-LGA7 allows only the `lines:`/`kinds:`/`scope: `/`archive_payload: `
prefixes to differ from the default face and AC-ARM3 pins the
`archive_payload:` line to end on its three counts.

The cap matters: R2914 measured archived_missing=787 on the pre-law tree,
so an uncapped tail would grow one advisory line to kilobytes.

Nothing here gates. The archives are frozen history, so a world whose only
gap lives in an archive must still read VERDICT CLEAN in every case below.

Every fixture world is built in the system temp dir; the live archives are
only read, and their (size, mtime_ns) must not move.

Source discipline: pure ASCII, stdlib plus the shipped module, no network.
"""
import io
import os
import re
import shutil
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC_OS = os.path.join(ROOT, 'src', 'os')
REGISTRY = os.path.join(ROOT, 'src', 'sandbox', 'reconcile_all.py')
STATE = os.path.join(SRC_OS, 'state.json')
FAILS = []
CHECKS = []

if SRC_OS not in sys.path:
    sys.path.insert(0, SRC_OS)
import ledger_lines as LL  # noqa: E402

ARCHIVE_NAME = 'state-log-archive-2026-06.md'
# The seven gaps that were already frozen in the shipped archives when this
# law was pinned. They are frozen history: a fold can ADD an id, never drop
# one, so membership is the stable half of the live assertion and the exact
# string is recorded in the round log instead of being pinned here.
STABLE_IDS = [2072, 3112, 3436, 3458, 3459, 3610, 3625]
LIVE = [
    '2026-11-28 R0200 PRODUCT: fixture round',
    'R0200 tokens: local=~1k api=0 api_reason=fixture reason here',
]


def ok(name, cond, detail=''):
    CHECKS.append(name)
    if cond:
        print('  | PASS %s %s' % (name, detail))
    else:
        FAILS.append(name)
        print('  | FAIL %s %s' % (name, detail))


def write(path, text):
    folder = os.path.dirname(path)
    if folder and not os.path.isdir(folder):
        os.makedirs(folder)
    with io.open(path, 'w', encoding='ascii', newline='\n') as fh:
        fh.write(text)


def stamp(path):
    st = os.stat(path)
    return (st.st_size, st.st_mtime_ns)


def scope_line(report):
    rows = [ln for ln in LL.format_report(report)
            if ln.startswith('scope: ')]
    return rows[0] if len(rows) == 1 else ''


def tail_of(line):
    marker = 'archived_missing_ids='
    pos = line.find(marker)
    return line[pos + len(marker):] if pos >= 0 else None


def world(base, name, archive_text):
    folder = os.path.join(base, name)
    write(os.path.join(folder, ARCHIVE_NAME), archive_text)
    scoped = LL.audit_scope(LL.load_archive_lines(folder), list(LIVE))
    return scoped, LL.format_report(scoped)


def main():
    started = time.time()
    with io.open(os.path.join(SRC_OS, 'ledger_lines.py'),
                 encoding='ascii') as fh:
        src = fh.read()
    base = tempfile.mkdtemp(prefix='bd-amid-')
    try:
        # ---- AC-AMID2 a world with no archive gap names none.
        clean_text = ('2026-06-01 R2001 PRODUCT: a folded round\n'
                      'R2001 tokens: local=~1k api=0 '
                      'api_reason=fixture reason here\n')
        scoped_clean, lines_clean = world(base, 'clean', clean_text)
        line_clean = [ln for ln in lines_clean if ln.startswith('scope: ')]
        ok('AC-AMID2 a zero-gap archive world reads archived_missing_ids=none',
           scoped_clean['archived_missing'] == []
           and len(line_clean) == 1
           and tail_of(line_clean[0]) == 'none',
           line_clean[0] if line_clean else 'no scope line')

        # ---- AC-AMID3 three gaps are named in ascending order.
        three = ''.join('2026-06-0%d R200%d PRODUCT: folded, no ledger\n'
                        % (n, n) for n in (3, 1, 2))
        scoped_three, lines_three = world(base, 'three', three)
        line_three = scope_line(scoped_three)
        ok('AC-AMID3 three archive gaps read ascending and comma joined',
           tail_of(line_three) == '2001,2002,2003',
           tail_of(line_three) or 'no tail')
        ok('AC-AMID3 the published count still equals the named ids',
           'archived_missing=3 ' in line_three
           and len(scoped_three['archived_missing']) == 3,
           'archived_missing=%d' % len(scoped_three['archived_missing']))

        # ---- AC-AMID3 the cap holds on a wide gap set.
        wide = ''.join('2026-07-01 R30%02d PRODUCT: folded, no ledger\n' % n
                       for n in range(1, 16))
        scoped_wide, _ = world(base, 'wide', wide)
        line_wide = scope_line(scoped_wide)
        ok('AC-AMID3 fifteen gaps publish the first twelve then +3',
           len(scoped_wide['archived_missing']) == 15
           and tail_of(line_wide)
           == '3001,3002,3003,3004,3005,3006,3007,3008,3009,3010,3011,'
              '3012,+3',
           tail_of(line_wide) or 'no tail')
        ok('AC-AMID3 the cap is the shipped constant, not a local literal',
           LL.ID_TAIL_CAP == 12
           and LL.format_id_tail(range(1, 16)).endswith(',+3')
           and LL.format_id_tail([]) == 'none',
           'cap=%d' % LL.ID_TAIL_CAP)

        # ---- AC-AMID4 a reading is not a ruling: the verdict never moves.
        ok('AC-AMID4 archive gaps never gate - all three worlds stay CLEAN',
           lines_clean[-1] == lines_three[-1] == 'VERDICT CLEAN'
           and scoped_three['clean'] is True
           and scoped_wide['clean'] is True,
           'three=%s wide=%s' % (lines_three[-1], lines_clean[-1]))

        # ---- AC-AMID1 the live tree names the frozen gaps it counts.
        archives = LL.default_logs_dir(STATE)
        before = [stamp(p) for p in sorted(LL.archive_files(archives))]
        live_scoped = LL.audit_scope(LL.load_archive_lines(None, STATE),
                                     LL.load_state_log(STATE))
        line_live = scope_line(live_scoped)
        live_tail = tail_of(line_live) or ''
        published = [int(n) for n in live_tail.split(',')
                     if n.isdigit()]
        after = [stamp(p) for p in sorted(LL.archive_files(archives))]
        ok('AC-AMID1 the live tail republishes the id list audit_scope holds',
           live_tail == LL.format_id_tail(live_scoped['archived_missing'])
           and published == sorted(published)
           and 'archived_missing=%d ' % len(live_scoped['archived_missing'])
           in line_live,
           live_tail)
        ok('AC-AMID1 the frozen ids this window measured are all named',
           all(n in published for n in STABLE_IDS),
           'missing=%r' % [n for n in STABLE_IDS if n not in published])
        ok('AC-AMID1 reading the face leaves the archives byte-identical',
           before == after, 'archives=%d' % len(before))

        # ---- AC-AMID5 the older scope fields keep their shape and order.
        ok('AC-AMID5 the scope line still opens on its four pinned fields',
           re.match(r'^scope: \S+ archive_lines=\d+ live_lines=\d+ '
                    r'archived_missing=\d+ archived_orphan=\d+ '
                    r'archived_missing_ids=\S+$', line_live) is not None,
           line_live[:90])

        # ---- AC-AMID5 hygiene and wiring.
        net = LL.network_imports(src)
        ok('AC-AMID5 the module still imports nothing that touches the network',
           net == [], ','.join(net) or 'none')
        with io.open(REGISTRY, encoding='utf-8') as fh:
            reg = fh.read()
        ok('AC-AMID5 the suite is wired in the registry',
           '("os-ledger-scope-ids",' in reg
           and 'test_ledger_scope_ids.py"), 14)' in reg)
        try:
            io.open(os.path.abspath(__file__), encoding='ascii').read()
            ascii_ok = True
        except UnicodeDecodeError:
            ascii_ok = False
        ok('AC-AMID5 this suite source is pure ASCII', ascii_ok)
        crit = sorted(set(re.findall(r'AC-AMID\d', ' '.join(CHECKS))))
        ok('AC-AMID5 every declared criterion is measured',
           crit == ['AC-AMID1', 'AC-AMID2', 'AC-AMID3', 'AC-AMID4',
                    'AC-AMID5'],
           ','.join(crit))
    finally:
        shutil.rmtree(base, ignore_errors=True)
    total = len(CHECKS)
    if FAILS:
        print('SUITE FAIL %d/%d in %.1fs'
              % (total - len(FAILS), total, time.time() - started))
        print('failed: %s' % ','.join(FAILS))
        return 2
    print('SUITE PASS %d/%d in %.1fs' % (total, total, time.time() - started))
    return 0


if __name__ == '__main__':
    sys.exit(main())
