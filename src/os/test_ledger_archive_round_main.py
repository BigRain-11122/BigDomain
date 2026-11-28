"""test_ledger_archive_round_main.py - the archive face counts rounds whose main line was never confirmed.

Criteria AC-ARM1..AC-ARM3 were pinned in src/os/backlog.md at R3629 BEFORE
src/os/ledger_lines.py changed and before this file existed. AC-ARM4 was
pinned at R3630, after a read-only measurement showed the R3629 board note
over-stated the split-round risk: the union is keyed by round number, so a
round whose narrative and ledger halves sit in two archive files reads once.

The measured gap (this window, read off the live tree): check_round_main_shape()
judges exactly ONE round - the newest - and says so ("older rounds deliberately
not asked"), while audit_archive() counted archived lines by presence and
payload but never asked whether a folded round holds a lawful main line at all.
Over the three shipped archives that is 2109 rounds, of which 68 carry no dated
line and 847 carry dated lines without an UPPERCASE label: 915 rounds whose
main line no face has ever confirmed. The reading is now derived through the
SAME two regexes the round-main law uses, and it is PUBLISHED only - the
archives are frozen history whose pre-law rounds legitimately have no label, so
neither number may gate and the VERDICT must not move.

Every world is built in the system temp dir; the live archive is read and its
(size, mtime_ns) must not move.

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
LEDGER_LINES = os.path.join(SRC_OS, 'ledger_lines.py')
REGISTRY = os.path.join(ROOT, 'src', 'sandbox', 'reconcile_all.py')
FAILS = []
CHECKS = []

if SRC_OS not in sys.path:
    sys.path.insert(0, SRC_OS)
import ledger_lines as LL  # noqa: E402

ARCHIVE_NAME = 'state-log-archive-2026-06.md'
LAWFUL = '2026-06-01 R0010 PRODUCT: a dated main line with a label'
UNLABELLED = '2026-06-02 R0011 main line with a lowercase label'
BARE = 'R0012 narrative row with no date prefix'
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


def stamp(path):
    st = os.stat(path)
    return (st.st_size, st.st_mtime_ns)


def write(path, text):
    folder = os.path.dirname(path)
    if folder and not os.path.isdir(folder):
        os.makedirs(folder)
    with open(path, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(text)


def body_between(src, start_marker, end_marker):
    start = src.index(start_marker)
    return src[start:src.index(end_marker, start)]


def code_only(src):
    """The region with its docstring and comment lines dropped."""
    out = []
    in_doc = False
    for ln in src.splitlines():
        s = ln.strip()
        marks = s.count('"""')
        if in_doc:
            if marks:
                in_doc = False
            continue
        if marks:
            if marks == 1:
                in_doc = True
            continue
        if s.startswith('#'):
            continue
        out.append(ln)
    return '\n'.join(out)


def shared_law(body):
    """True only when the region counts through the shipped pair of regexes."""
    text = code_only(body)
    if text.count('ROUND_MAIN_RE.match(') != 1:
        return False
    if text.count('ROUND_LABEL_RE.match(') != 1:
        return False
    for banned in ('def check_round_main_shape', 'r"^\\d{4}', "r'^\\d{4}"):
        if banned in text:
            return False
    return True


def main():
    started = time.time()
    with io.open(LEDGER_LINES, encoding='ascii') as fh:
        src = fh.read()
    live_archives = os.path.join(ROOT, 'logs')
    live_files = [os.path.join(live_archives, name)
                  for name in sorted(os.listdir(live_archives))
                  if name.startswith('state-log-archive-')]
    live_before = [stamp(path) for path in live_files]
    base = tempfile.mkdtemp(prefix='ledger-archive-main-')
    try:
        # ---- AC-ARM1 the reading is the round-main law, not a second copy.
        body = body_between(src, 'def audit_archive(', 'def default_baseline_path(')
        ok('AC-ARM1 audit_archive counts through the shipped regex pair once each',
           shared_law(body))
        mutant = body.replace('if ROUND_MAIN_RE.match(line):',
                              'if False:')
        ok('AC-ARM1 negative control - dropping the dated count turns the law red',
           shared_law(mutant) is False)
        ok('AC-ARM1 the region restates no round-main law of its own',
           'def check_round_main_shape' not in code_only(body)
           and 'E_RMS_' not in code_only(body))

        # ---- AC-ARM2 three rounds, each failing a different half of the law.
        world = os.path.join(base, 'world')
        archive = os.path.join(world, ARCHIVE_NAME)
        write(archive, '\n'.join(['# rebuild header', '# --- R0010',
                                  LAWFUL, '# --- R0011', UNLABELLED,
                                  '# --- R0012', BARE]) + '\n')
        report = LL.audit_archive(LL.load_archive(archive))
        ok('AC-ARM2 the archive reads three rounds',
           report['rounds_total'] == 3, 'rounds_total=%d' % report['rounds_total'])
        ok('AC-ARM2 the bare narrative names the no-date round',
           report['rounds_without_main'] == [12],
           'without_main=%r' % (report['rounds_without_main'],))
        ok('AC-ARM2 the lowercase label names the no-label round',
           report['rounds_without_label'] == [11],
           'without_label=%r' % (report['rounds_without_label'],))
        before = (stamp(archive), tuple(live_before))
        again = LL.audit_archive(LL.load_archive(archive))
        after = (stamp(archive), tuple(stamp(path) for path in live_files))
        ok('AC-ARM2 the reading is read-only and deterministic',
           before == after and again == report,
           'before=%r after=%r' % (before, after))

        # ---- AC-ARM3 published on the union face, and never a gate.
        archive_lines = LL.load_archive_lines(world)
        scoped = LL.audit_scope(archive_lines, list(LIVE))
        ok('AC-ARM3 audit_scope republishes the three readings field for field',
           scoped['archive_rounds'] == report['rounds_total']
           and scoped['archive_rounds_without_main'] == report['rounds_without_main']
           and scoped['archive_rounds_without_label'] == report['rounds_without_label'])
        rows = [ln for ln in LL.format_report(scoped)
                if ln.startswith('archive_payload: ')]
        ok('AC-ARM3 exactly one archive_payload line, ending on the three counts',
           len(rows) == 1
           and rows[0].endswith('rounds=3 no_main=1 no_label=1'),
           rows[0] if rows else 'no archive_payload line')
        ok('AC-ARM3 frozen history never gates - the verdict stays CLEAN',
           scoped['clean'] is True
           and LL.format_report(scoped)[-1] == 'VERDICT CLEAN')

        # ---- AC-ARM4 a round split across two archive files is counted once.
        # Pinned at R3630 before this arm existed: the R3629 board note claimed
        # the counts are accumulated per archive pass and that a split round
        # would be judged twice. Measured on this fixture instead: the union is
        # taken by load_archive_lines() and keyed by round number, so a split
        # round reads once and pairs across files. The negative control below
        # keeps that claim honest - a union that silently swallowed a really
        # unpaired round would red here.
        split = os.path.join(base, 'split')
        split_first = os.path.join(split, 'state-log-archive-2026-07.md')
        split_second = os.path.join(split, 'state-log-archive-2026-08.md')
        write(split_first, '2026-07-01 R0901 PRODUCT: main half in one file\n')
        write(split_second,
              'R0901 tokens: local=~1k api=0 api_reason=other half file\n')
        split_before = (stamp(split_first), stamp(split_second))
        split_report = LL.audit_archive(LL.load_archive_lines(split))
        split_again = LL.audit_archive(LL.load_archive_lines(split))
        split_after = (stamp(split_first), stamp(split_second))
        ok('AC-ARM4 a round split across two archive files is counted once',
           split_report['rounds_total'] == 1,
           'rounds_total=%d' % split_report['rounds_total'])
        ok('AC-ARM4 neither round-main reading names the split round',
           split_report['rounds_without_main'] == []
           and split_report['rounds_without_label'] == [],
           'without_main=%r without_label=%r'
           % (split_report['rounds_without_main'],
              split_report['rounds_without_label']))
        ok('AC-ARM4 the presence pairing pairs across the two files',
           split_report['rounds_without_ledger'] == []
           and split_report['ledger_without_round'] == [],
           'without_ledger=%r without_round=%r'
           % (split_report['rounds_without_ledger'],
              split_report['ledger_without_round']))
        lonely = os.path.join(base, 'lonely')
        write(os.path.join(lonely, 'state-log-archive-2026-09.md'),
              '2026-09-01 R0902 PRODUCT: this round has no ledger anywhere\n')
        lonely_report = LL.audit_archive(LL.load_archive_lines(lonely))
        ok('AC-ARM4 negative control - an unpaired round is still named',
           lonely_report['rounds_total'] == 1
           and lonely_report['rounds_without_ledger'] == [902],
           'rounds_total=%d without_ledger=%r'
           % (lonely_report['rounds_total'],
              lonely_report['rounds_without_ledger']))
        ok('AC-ARM4 the split reading is read-only and deterministic',
           split_before == split_after and split_again == split_report,
           'before=%r after=%r' % (split_before, split_after))

        # ---- hygiene and wiring.
        net = LL.network_imports(src)
        ok('AC-ARM3 the module still imports nothing that touches the network',
           net == [], ','.join(net) or 'none')
        with io.open(REGISTRY, encoding='utf-8') as fh:
            reg = fh.read()
        ok('AC-ARM3 the suite is wired in the registry',
           '("os-ledger-archive-round-main",' in reg
           and 'test_ledger_archive_round_main.py"), 19)' in reg)
        try:
            io.open(os.path.abspath(__file__), encoding='ascii').read()
            ascii_ok = True
        except UnicodeDecodeError:
            ascii_ok = False
        ok('AC-ARM3 this suite source is pure ASCII', ascii_ok)
        crit = sorted(set(re.findall(r'AC-ARM\d', ' '.join(CHECKS))))
        ok('AC-ARM3 every declared criterion is measured',
           crit == ['AC-ARM1', 'AC-ARM2', 'AC-ARM3', 'AC-ARM4'],
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
