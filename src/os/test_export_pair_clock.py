"""test_export_pair_clock.py - battery suite for the R3638 pair-clock law.

Criteria AC-EXPCLK1..AC-EXPCLK4 were pinned in src/os/backlog.md at R3638 BEFORE
src/os/export_round.py learned the lag rule and before this file existed. The
measured reason: the face is written before the commit that ships it, so the
half that won the stamp is dirty and renders 'mtime'; the same commit makes that
content clean and the same pair re-derives as 'commit'. Whole-line equality
asked the face to predict its own commit, so every product round opened with
AC-EXPW1 red for one window (measured: VERDICT FAIL 1 on the live tree, same
pair, same date, only the clock token differing).

Isolation: every world is a private tempdir with its own git history. The repo
state.json and docs/status-export.json are only read.

Source discipline: pure ASCII, stdlib only, fixed git dates, no network.
"""
import io
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'src', 'os'))
import export_round as ER  # noqa: E402

CHECKS = []
FAILS = []


def ok(name, cond, detail=''):
    CHECKS.append(name)
    if cond:
        print('  | PASS %s %s' % (name, detail))
    else:
        FAILS.append(name)
        print('  | FAIL %s %s' % (name, detail))


def git(world, args, when):
    env = dict(os.environ)
    env['GIT_AUTHOR_DATE'] = when
    env['GIT_COMMITTER_DATE'] = when
    env['GIT_AUTHOR_NAME'] = 'fixture'
    env['GIT_AUTHOR_EMAIL'] = 'fixture@example.invalid'
    env['GIT_COMMITTER_NAME'] = 'fixture'
    env['GIT_COMMITTER_EMAIL'] = 'fixture@example.invalid'
    return subprocess.run(['git', '-C', world] + args, env=env,
                          capture_output=True)


def build_world(commit_when):
    """A private world whose pair is dirty first, then committed at `commit_when`.

    Returns (world, dirty_line, committed_line) or (None, '', '') when git is
    unavailable; the dirty line is the face the writer would have published
    before the commit, the committed line is the same pair re-derived after it.
    """
    world = tempfile.mkdtemp(prefix='expclk-')
    os.makedirs(os.path.join(world, 'preview'))
    html = os.path.join(world, 'preview', 'clock-pair.html')
    doc = os.path.join(world, 'preview', 'clock-pair.json')
    io.open(html, 'w', encoding='utf-8', newline='\n').write('<html>clock</html>\n')
    io.open(doc, 'w', encoding='utf-8', newline='\n').write('{"clock": 1}\n')
    pair, _skipped, _board = ER.newest_artifact(world)
    if pair is None:
        return None, '', ''
    dirty_line = ER.fmt_pair(pair)
    init = git(world, ['init'], commit_when)
    if init.returncode != 0:
        return None, '', ''
    git(world, ['add', '--', 'preview/clock-pair.html', 'preview/clock-pair.json'],
        commit_when)
    done = git(world, ['-c', 'user.name=fixture', '-c', 'user.email=fixture@example.invalid',
                       'commit', '-m', 'pair'], commit_when)
    if done.returncode != 0:
        return None, '', ''
    pair2, _s, _b = ER.newest_artifact(world)
    if pair2 is None:
        return None, '', ''
    return world, dirty_line, ER.fmt_pair(pair2)


def today_stamp():
    import datetime
    return datetime.datetime.now().strftime('%Y-%m-%dT12:00:00+08:00')


print('== AC-EXPCLK1: a face that equals the derivation is lawful ==')
_world, dirty, committed = build_world(today_stamp())
ok('AC-EXPCLK1 the fixture built a real git work tree', bool(_world), str(_world))
ok('AC-EXPCLK1 identical lines are lawful', ER.clock_lag_lawful(committed, committed),
   committed)
ok('AC-EXPCLK1 an empty face is never lawful', not ER.clock_lag_lawful('', committed), '')

print('== AC-EXPCLK2: the only lawful drift is mtime -> commit, same date ==')
ok('AC-EXPCLK2 the dirty face reads mtime', ' mtime]' in dirty, dirty)
ok('AC-EXPCLK2 the committed face reads commit', ' commit]' in committed, committed)
ok('AC-EXPCLK2 the pre-commit face is lawful one commit later',
   ER.clock_lag_lawful(dirty, committed), '%s || %s' % (dirty, committed))
ok('AC-EXPCLK2 the bracket bodies are otherwise byte-equal',
   ER.PAIR_BRACKET_RE.sub('[]', dirty) == ER.PAIR_BRACKET_RE.sub('[]', committed), '')
ok('AC-EXPCLK2 exactly one bracket moved', len(ER.PAIR_BRACKET_RE.findall(dirty)) == 1, '')

print('== AC-EXPCLK3: four negative controls still refuse ==')
ok('AC-EXPCLK3 leading (commit claimed on a dirty file) is refused',
   not ER.clock_lag_lawful(committed, dirty), '')


def shift_date(line):
    """Move the bracket's day forward by one, keeping the clock token."""
    match = ER.PAIR_BRACKET_RE.search(line)
    year, month, day = (int(match.group(1)[0:4]), int(match.group(1)[5:7]),
                        int(match.group(1)[8:10]))
    day = day + 1 if day < 28 else 1
    moved = '%04d-%02d-%02d' % (year, month, day)
    return line[:match.start()] + '[%s %s]' % (moved, match.group(2)) + line[match.end():]


def bump_bytes(line):
    """Add one to the first byte count so the identity no longer matches."""
    import re as _re
    return _re.sub(r'\((\d+)B\)', lambda m: '(%dB)' % (int(m.group(1)) + 1), line, count=1)


ok('AC-EXPCLK3 a shifted date with the lagging clock is refused',
   not ER.clock_lag_lawful(shift_date(dirty), committed), shift_date(dirty))
ok('AC-EXPCLK3 a mutated byte count is refused',
   not ER.clock_lag_lawful(bump_bytes(dirty), committed), bump_bytes(dirty))
ok('AC-EXPCLK3 a malformed face is refused',
   not ER.clock_lag_lawful('preview/clock-pair.html (17B) + nonsense', committed), '')

print('== AC-EXPCLK4: the writing half is untouched ==')
stamp = 1709524800.0
day = ER.pair_date(stamp)
pinned = ('preview/x.html (10B) + preview/x.json (20B) [%s commit] '
          '(halves differ: html [%s commit] + json [2026-03-03 commit]; '
          'later=html)' % (day, day))
row = (stamp, 'preview/x.html', 'preview/x.json', 10, 20, 'commit',
       'halves differ: html [%s commit] + json [2026-03-03 commit]; '
       'later=html' % day)
ok('AC-EXPCLK4 fmt_pair still renders the R2899/R2901 shape byte for byte',
   ER.fmt_pair(row) == pinned, ER.fmt_pair(row))
ok('AC-EXPCLK4 the writer is still the only formatter',
   ER._fmt_pair is ER.fmt_pair, '')
ok('AC-EXPCLK4 a 5-tuple still reads mtime',
   ER.fmt_pair((stamp, 'preview/y.html', 'preview/y.json', 1, 2, 'mtime')) ==
   'preview/y.html (1B) + preview/y.json (2B) [%s mtime]' % day, '')

total = len(CHECKS)
fails = len(FAILS)
print('SUITE %s %d/%d' % ('PASS' if not fails else 'FAIL', total - fails, total))
if fails:
    print('FAILED: %s' % ', '.join(FAILS))
sys.exit(0 if not fails else 1)
