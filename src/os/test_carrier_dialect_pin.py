"""Battery suite for the carrier dialect pin - criteria AC-CDPIN1..AC-CDPIN8.

Pinned in src/os/backlog.md at R3208 BEFORE this file existed, from a
read-only probe (tmp/probe_R3208.py, tmp/probe_R3208b.py, tmp/probe_R3208c.py)
run before any code changed.

The defect this suite holds, measured first: src/os/state.json was not pinned
in .gitattributes, and a blob is always stored as LF, so a checkout running
with core.autocrlf=false materialized the WHOLE carrier as bare LF - measured
bytes=59808 crlf=0 bare_lf=78 against the live bytes=59886 crlf=78. That is
the drift the closeout gate refused twice (R3204 bare_lf=49, R3207 bare_lf=70)
and each time repaired by hand. The pin holds for all three measured
add/checkout combinations, and no shipped round writer emits LF, so the pin
closes the only path that could recreate it.

Second half of the same window: state_fold.plan_fold used to fall back to a
bare-LF split, so an already-LF carrier was planned with newline=LF and
composed 77 bare-LF separators with every gate green - the fold propagated the
dialect instead of naming it. It now refuses with E_SF_EOL, matching the
sibling door that has refused an LF carrier since it shipped.

R3209 extended the same law to its SCOPE (AC-CDPIN5..7), from a read-only
probe (tmp/probe_R3209.py). Measured: four more carriers flip to CRLF under a
checkout on an autocrlf=true host (docs/status-export.json 38204->38424B,
heartbeat.txt 10->11B, qa/writer-census-baseline.json 14484->14995B,
logs/state-log-archive-2026-11.md 5666145->5672490B), yet their shipped
readers answer the same on both dialects - heartbeat.read_tick normalises CRLF
before parsing, the other two are read through json.loads, the archives have
no dialect reader - so pinning them would change nothing a machine can judge.
The suite now holds the boundary instead: every hard-reader carrier must be
pinned with the matching eol, NO tolerant carrier may appear as a law line,
and the pin mechanism itself is proven to work on a carrier that needs none.

Isolation: every git repository, state file and archive this suite builds
lives in the system temp dir. The real .gitattributes, state.json and qa/ are
read only, never written. Source is pure ASCII, stdlib only, no clock in
assertions, no network.

R3210 asked whether the two hand-written things in this file - the STRICT
carrier list and the "which readers are hard" judgement behind it - can be
derived from shipped code, and whether the mixed-dialect archives cost a
reader anything (tmp/probe_R3210.py).

R3357 completed the table instead of withdrawing a law line: three law lines
already in .gitattributes had no STRICT row, so AC-CDPIN8 named them
law_unrepresented. Each was measured against its shipped dialect-hard
consumer before the row was added - docs/status-export.json is owed by its
line-anchored writer (R3303, AC-SXF34 grades the raw \r count), and
preview/apimarket-report.{html,json} by check_sizes()' byte comparison
against os.path.getsize (R3292). .gitattributes is not touched by this
window; the table follows the law it already had.

Derivation measured NOT VIABLE: scanning the refusal codes (E_STATE_LAYOUT,
E_SF_EOL, E_CLG_CARRIER_LAYOUT, E_CLG_MATRIX, evidence_dialect, lf_only) and
the path literals beside them reaches 2 of the 5 STRICT rows and, of the 10
literals it reaches, only 2 are carriers at all. The missing three leak
through three different holes: state/queue/tech.md is only named by a one-off
round script and its law is a GLOB, tools/hooks/pre-commit is hard because sh
reads it (a comment in .gitattributes, not a refusal code), and qa/*.log is a
family-level -text whose refusal code never names a path. So the knowledge is
partly in comments, partly in one-off scripts, partly in an execution model.

What was NOT acceptable - and what AC-CDPIN8 now holds - is that the table and
the law lines could drift apart in one direction: AC-CDPIN5 only asked
"table -> law", so a NEW pin line added to .gitattributes without a table row
was invisible. AC-CDPIN8 asks both ends plus the scan (every resolvable
literal beside a refusal code is either a law-covered carrier or a declared
NON_CARRIER, and the set of unresolvable bare names is pinned), which is the
mechanical form of "a new hard reader must enter the table".

The archive half was measured tolerable: logs/state-log-archive-2026-09.md is
mixed (crlf=478 with bare_lf=15500), yet its one shipped reader
(ledger_lines.load_archive, universal newlines) returns the SAME 15611 lines
for the live file and for forced-LF and forced-CRLF copies, with zero accepted
line carrying an embedded CR. R3209's note that "the archives have no dialect
reader at all" was wrong and is corrected there rather than restated here.
"""
import fnmatch
import io
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, 'src', 'os')
ATTRS = os.path.join(ROOT, '.gitattributes')
LIVE = os.path.join(SRC, 'state.json')
REGISTRY = os.path.join(ROOT, 'src', 'sandbox', 'reconcile_all.py')
FAILS = []
CHECKS = []


def ok(name, cond, detail=''):
    CHECKS.append(name)
    if cond:
        print('  | PASS %s %s' % (name, detail))
    else:
        FAILS.append(name)
        print('  | FAIL %s %s' % (name, detail))


def read_bytes(path):
    with io.open(path, 'rb') as handle:
        return handle.read()


def read_text(path):
    with io.open(path, 'r', encoding='utf-8') as handle:
        return handle.read()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def profile(raw):
    crlf = raw.count(b'\r\n')
    return len(raw), crlf, raw.count(b'\n') - crlf


def git(argv, cwd):
    base = ['git', '-c', 'user.email=probe@example.invalid',
            '-c', 'user.name=probe']
    done = subprocess.run(base + argv, cwd=cwd, capture_output=True)
    return done.returncode, done.stdout.decode('utf-8', 'replace').strip(), \
        done.stderr.decode('utf-8', 'replace').strip()


def cycle(attrs_line, add_autocrlf, co_autocrlf, carrier):
    """Commit a carrier, remove it, check it out again; return (blob, landed).

    The whole point of the arm: the ABOVE measurement is what a checkout can
    do to this file on a machine whose git settings differ from this one.
    """
    box = tempfile.mkdtemp(prefix='cdpin_')
    try:
        git(['init', '-q'], box)
        os.makedirs(os.path.join(box, 'src', 'os'))
        if attrs_line is not None:
            with io.open(os.path.join(box, '.gitattributes'), 'w',
                         encoding='utf-8', newline='\n') as handle:
                handle.write(attrs_line + '\n')
        path = os.path.join(box, 'src', 'os', 'state.json')
        with io.open(path, 'wb') as handle:
            handle.write(carrier)
        git(['-c', 'core.autocrlf=%s' % add_autocrlf, 'add',
             'src/os/state.json'], box)
        git(['commit', '-q', '-m', 'x', '--no-verify'], box)
        blob = subprocess.run(
            ['git', 'cat-file', '-p', 'HEAD:src/os/state.json'],
            cwd=box, capture_output=True).stdout
        os.remove(path)
        git(['-c', 'core.autocrlf=%s' % co_autocrlf, 'checkout', '--',
             'src/os/state.json'], box)
        landed = read_bytes(path) if os.path.exists(path) else b''
        return blob, landed
    finally:
        shutil.rmtree(box, ignore_errors=True)


def cycle_at(attrs_line, add_autocrlf, co_autocrlf, carrier, rel):
    """The same decisive cycle for any relative path, not just the state file."""
    box = tempfile.mkdtemp(prefix='cdpin_at_')
    try:
        git(['init', '-q'], box)
        folder = os.path.dirname(os.path.join(box, rel))
        os.makedirs(folder, exist_ok=True)
        if attrs_line is not None:
            with io.open(os.path.join(box, '.gitattributes'), 'w',
                         encoding='utf-8', newline='\n') as handle:
                handle.write(attrs_line + '\n')
        path = os.path.join(box, rel)
        with io.open(path, 'wb') as handle:
            handle.write(carrier)
        git(['-c', 'core.autocrlf=%s' % add_autocrlf, 'add', rel], box)
        git(['commit', '-q', '-m', 'x', '--no-verify'], box)
        os.remove(path)
        git(['-c', 'core.autocrlf=%s' % co_autocrlf, 'checkout', '--', rel],
            box)
        return read_bytes(path) if os.path.exists(path) else b''
    finally:
        shutil.rmtree(box, ignore_errors=True)


PIN = 'src/os/state.json text eol=crlf'

# Measured at R3209 (tmp/probe_R3209.py). A carrier belongs in STRICT only if a
# shipped reader refuses or misreads the other dialect; TOLERANT lists the ones
# whose readers were measured to answer the same on both.
STRICT = [
    ('src/os/state.json', 'text: set', 'eol: crlf'),
    ('state/queue/tech.md', 'text: set', 'eol: lf'),
    ('docs/sandbox-suite-matrix.md', 'text: set', 'eol: lf'),
    ('tools/hooks/pre-commit', 'text: set', 'eol: lf'),
    ('qa/probe-R3208.log', 'text: unset', 'eol: unspecified'),
    # R3357: three law lines added by earlier windows had no row here, so
    # AC-CDPIN8 read them as law_unrepresented. Both are dialect-hard, each
    # measured before the row was added, and the law line stays.
    # docs/status-export.json is owed by its WRITER: tools/status_export_fresh.py
    # anchors every edit on ^<indent>"key": ...(,?)$ and $ does not match
    # before a CR (R3303, graded there as AC-SXF34 via the raw \r count).
    # preview/apimarket-report.{html,json} are owed by a byte-counting READER:
    # src/sandbox/ledger/apimarket_report.py check_sizes() compares the sizes
    # block against os.path.getsize (R3292: 59515 vs 61720 bytes on a flip).
    ('docs/status-export.json', 'text: set', 'eol: lf'),
    ('preview/apimarket-report.html', 'text: set', 'eol: lf'),
    ('preview/apimarket-report.json', 'text: set', 'eol: lf'),
]
TOLERANT = [
    # R3357: docs/status-export.json left this list because R3303 corrected its
    # measurement - the reader tolerates CRLF but the writer refuses it - and
    # the pin it already carries is owed, not decoration.
    'heartbeat.txt',
    'qa/writer-census-baseline.json',
    'logs/state-log-archive-2026-11.md',
]

# R3210: the table stays hand-written (the scan below reaches 2 of 5 rows),
# but every resolvable literal the scan lands on is DISPOSED here: either it is
# a carrier matched by a law line, or it is named as a code file. Digesting a
# new refusal code beside a new carrier path therefore reddens r until the
# table gets a decision. Measured at R3210 with tmp/probe_R3210.py.
SCANNED_FOR_CODES = ['src/os/logs_toolkit.py', 'src/os/state_fold.py',
                     'tools/closeout_gate.py', 'src/os/evidence_dialect.py',
                     'tools/hooks/pre_commit_gate.py',
                     'src/os/seed_queue_R2548.py']
NON_CARRIER = ['src/os/backlog.md', 'src/os/closeout.py',
               'src/os/evidence_dialect.py', 'src/os/logs_toolkit.py',
               'src/os/one_off_round_scripts.py',
               'src/os/suite_matrix_reconcile.py']
CODE_TOKENS = ['E_STATE_LAYOUT', 'E_SF_EOL', 'E_CLG_CARRIER_LAYOUT',
               'E_CLG_MATRIX', 'evidence_dialect', 'lf_only']
# R3357 measured a third blind name: tools/closeout_gate.py:96 and :294 write
# the shipped tool as the bare `qa_log.py`, the same shape as state.json
# (src/os/state.json) and tech.md (state/queue/tech.md) - prose shorthand that
# a law glob cannot resolve and that is not a carrier. Named here rather than
# repaired in the prose it comes from.
BLIND_NAMES = ['qa_log.py', 'state.json', 'tech.md']


def main():
    started = time.time()
    live = read_bytes(LIVE)
    attrs = read_text(ATTRS)

    # ---- AC-CDPIN1: the law is pinned, once, on the right path ----------
    rc, out, err = git(['check-attr', 'text', 'eol', '--',
                        'src/os/state.json'], ROOT)
    pin_lines = [row for row in attrs.splitlines()
                 if row.strip() == PIN]
    # R3209: the old arm counted every mention of the path, so two comments
    # that quote it reddened an otherwise healthy pin. Uniqueness is a property
    # of the LAW lines; prose is not a law. Narrowed, not loosened: a second
    # attribute line naming the path still fails.
    law_rows = [row for row in attrs.splitlines()
                if row.strip() and not row.strip().startswith('#')]
    naming = [row for row in law_rows if row.split()[0] == 'src/os/state.json']
    ok('AC-CDPIN1 the carrier dialect is pinned in .gitattributes',
       rc == 0
       and 'text: set' in out
       and 'eol: crlf' in out
       and len(pin_lines) == 1
       and len(naming) == 1,
       'rc=%d los=%s pins=%d' % (rc, out.replace('\n', ';')[:60],
                                 len(pin_lines)))

    # ---- AC-CDPIN2: the decisive arm - the pin is what stops the drift --
    blob_free, land_free = cycle(None, 'true', 'false', live)
    blob_pin, land_pin = cycle(PIN, 'true', 'false', live)
    blob_pin2, land_pin2 = cycle(PIN, 'false', 'false', live)
    ok('AC-CDPIN2 an unpinned carrier lands bare LF, the pinned one cannot',
       profile(land_free)[1] == 0
       and profile(land_free)[2] == profile(live)[1] > 0
       and land_pin == live
       and land_pin2 == live
       and profile(blob_free)[1] == 0
       and profile(blob_pin)[1] == 0,
       'free=%s pinned=%s pinned2=%s blob_free_crlf=%d'
       % (profile(land_free), profile(land_pin), profile(land_pin2),
          profile(blob_free)[1]))

    # ---- AC-CDPIN3: both fold doors refuse an LF carrier by name --------
    mod = load('state_fold_under_test', os.path.join(SRC, 'state_fold.py'))
    toolkit = load('logs_toolkit_under_test',
                   os.path.join(SRC, 'logs_toolkit.py'))
    log_len = len(json.loads(live.decode('utf-8'))['log'])
    lf_carrier = live.replace(b'\r\n', b'\n')
    code = ''
    detail = ''
    try:
        mod.plan_fold(lf_carrier, json.loads(live.decode('utf-8')), 1, 2,
                      'R0001 probe summary', gate=200000)
    except mod.StateFoldError as exc:
        code = exc.code
        detail = exc.detail
    control, folded = mod.plan_fold(live, json.loads(live.decode('utf-8')),
                                    1, 2, 'R0001 probe summary', gate=200000)
    toolkit_reads_lf = toolkit.split_ps_layout(
        lf_carrier.decode('utf-8'), log_len)
    ok('AC-CDPIN3 the fold names an LF carrier instead of carrying it',
       code == 'E_SF_EOL'
       and 'eol --fix' in detail
       and control['newline'] == 'CRLF'
       and b'\r\n' in folded.encode('utf-8')
       and toolkit_reads_lf is None,
       'code=%s hint=%s control=%s toolkit_lf=%s'
       % (code, '--fix' in detail, control['newline'],
          'refused' if toolkit_reads_lf is None else 'readable'))

    # ---- AC-CDPIN4: the live carrier is clean, and the refusal is one ---
    live_prof = profile(live)
    raises = read_text(os.path.join(SRC, 'state_fold.py')).count('E_SF_EOL')
    ok('AC-CDPIN4 the live carrier needs no repair and the refusal is single',
       live_prof[1] > 0
       and live_prof[2] == 0
       and raises == 2  # the raise plus the docstring mention
       and mod.split_layout(live.decode('utf-8'), log_len) is not None,
       'live=%s e_sf_eol_sites=%d' % (live_prof, raises))

    # ---- AC-CDPIN5: the scope is exactly the hard readers ---------------
    missing = []
    for rel, want_text, want_eol in STRICT:
        rc, out, err = git(['check-attr', 'text', 'eol', '--', rel], ROOT)
        if rc != 0 or want_text not in out or want_eol not in out:
            missing.append('%s(%s)' % (rel, out.replace('\n', ';')[:40]))
    law_lines = [row for row in attrs.splitlines()
                 if row.strip() and not row.strip().startswith('#')]
    decorated = [rel for rel in TOLERANT
                 if any(row.split()[0].rstrip('/') == rel.split('/')[0]
                        or rel in row for row in law_lines)]
    ok('AC-CDPIN5 every hard-reader carrier is pinned and no tolerant one is',
       not missing and not decorated,
       'missing=%s decorated=%s law_lines=%d'
       % (missing or 'none', decorated or 'none', len(law_lines)))

    # ---- AC-CDPIN6: the tolerant readers answer the same on both --------
    hb = load('heartbeat_under_test', os.path.join(SRC, 'heartbeat.py'))
    box = tempfile.mkdtemp(prefix='cdpin_hb_')
    try:
        lf_dir = os.path.join(box, 'lf')
        crlf_dir = os.path.join(box, 'crlf')
        os.makedirs(lf_dir)
        os.makedirs(crlf_dir)
        with io.open(os.path.join(lf_dir, 'heartbeat.txt'), 'wb') as handle:
            handle.write(b'tick 7\n')
        with io.open(os.path.join(crlf_dir, 'heartbeat.txt'), 'wb') as handle:
            handle.write(b'tick 7\r\n')
        lf_tick = hb.read_tick(lf_dir)
        crlf_tick = hb.read_tick(crlf_dir)
    finally:
        shutil.rmtree(box, ignore_errors=True)
    export_lf = read_bytes(os.path.join(ROOT, 'docs', 'status-export.json'))
    base_lf = read_bytes(os.path.join(ROOT, 'qa',
                                      'writer-census-baseline.json'))
    export_eq = (json.loads(export_lf.decode('utf-8'))
                 == json.loads(export_lf.replace(b'\r\n', b'\n')
                               .replace(b'\n', b'\r\n').decode('utf-8')))
    base_eq = (json.loads(base_lf.decode('utf-8'))
               == json.loads(base_lf.replace(b'\n', b'\r\n').decode('utf-8')))
    ok('AC-CDPIN6 the tolerant readers give one answer for both dialects',
       lf_tick == 7 and crlf_tick == 7 and export_eq and base_eq,
       'tick_lf=%r tick_crlf=%r export_eq=%s baseline_eq=%s'
       % (lf_tick, crlf_tick, export_eq, base_eq))

    # ---- AC-CDPIN7: the mechanism generalises, the pin is just unused ---
    export_src = export_lf
    free_land = cycle_at(None, 'false', 'true', export_src,
                         'docs/status-export.json')
    pinned = [cycle_at('docs/status-export.json text eol=lf', a, co,
                       export_src, 'docs/status-export.json')
              for a, co in (('true', 'false'), ('false', 'true'),
                            ('true', 'true'))]
    ok('AC-CDPIN7 the same pin law works on a carrier that needs no pin',
       free_land != export_src
       and profile(free_land)[1] == profile(export_src)[2] > 0
       and all(land == export_src for land in pinned),
       'free=%s pinned=%s'
       % (profile(free_land), [profile(land) for land in pinned]))

    # ---- AC-CDPIN8: the table and the law lines agree BOTH ways ---------
    patterns = [row.split()[0] for row in law_lines]
    unrepresented = [pat for pat in patterns
                     if not any(fnmatch.fnmatch(rel, pat)
                                for rel, _text, _eol in STRICT)]
    unpinned = [rel for rel, _text, _eol in STRICT
                if not any(fnmatch.fnmatch(rel, pat) for pat in patterns)]
    literal_re = re.compile(r'[\w.\-/*]+\.(?:json|md|log|py)|hooks/pre-commit')
    reached = set()
    for rel in SCANNED_FOR_CODES:
        rows = read_text(os.path.join(ROOT, rel)).splitlines()
        for i, row in enumerate(rows):
            if not any(token in row for token in CODE_TOKENS):
                continue
            for near in rows[max(0, i - 20):i + 21]:
                for lit in literal_re.findall(near):
                    lit = lit.rstrip('.')
                    if lit.startswith('tmp/') or 'probe_' in lit:
                        continue
                    reached.add(lit)
    resolvable = [lit for lit in sorted(reached)
                  if os.path.isfile(os.path.join(ROOT, lit))]
    unplaced = [lit for lit in resolvable
                if lit not in NON_CARRIER
                and not any(fnmatch.fnmatch(lit, pat) for pat in patterns)]
    blind = sorted(lit for lit in reached
                   if '/' not in lit
                   and not os.path.isfile(os.path.join(ROOT, lit)))
    ok('AC-CDPIN8 the hand-written table and the law lines cannot drift apart',
       not unrepresented and not unpinned and not unplaced
       and blind == BLIND_NAMES,
       'law_unrepresented=%s strict_unpinned=%s scan_unplaced=%s blind=%s'
       % (unrepresented or 'none', unpinned or 'none', unplaced or 'none',
          blind))

    total = len(CHECKS)
    acs = set()
    for name in CHECKS:
        token = name.split(' ', 1)[0]
        for cut in range(len(token), 0, -1):
            if token[cut - 1].isdigit():
                acs.add(token[:cut])
                break
    print('suite: %d assertions over %d criteria' % (total, len(acs)))
    if FAILS:
        print('SUITE FAIL %d/%d failed=%s'
              % (total - len(FAILS), total, FAILS))
        return 1
    print('SUITE PASS %d/%d in %.1fs' % (total, total, time.time() - started))
    return 0


if __name__ == '__main__':
    sys.exit(main())
