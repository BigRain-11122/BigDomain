"""export_round - the generic per-round refresh hook for docs/status-export.json.

WHY THIS EXISTS: every window since R2431 shipped a BESPOKE driver
(export_R2431.py .. export_R2779.py) whose three CEO lines were typed in by
hand. The driver therefore described ITS OWN round forever: at the R2780 close
the face read tick 2780 while ceo_face.current still narrated the R2779 window
and next_milestone still announced two items that were already done. A CEO-facing
surface that has to be rewritten by hand every round is a surface that goes
stale whenever a window is in a hurry - which is the thirteen-window debt.

This module derives all three lines from live files at write time:
  current  <- the last ROUND narrative line of the live state log
  latest   <- the newest preview/X.html + X.json pair that is NOT a meta page
  next     <- the topmost open next-window row of src/os/backlog.md
Nothing about a particular round is typed in, so the face cannot describe a
past window without the files disagreeing.

Criteria AC-EXPW1..AC-EXPW6 were pinned in src/os/backlog.md at R2780 BEFORE
this file existed.

R2834: the round-main shape law (R2832) had exactly one production call site,
inside state_append (R2833). That still left the CEO-facing face writable from a
log whose newest round line had lost its date anchor - and a face derived from an
unanchored line is precisely what R2831 shipped. The exporter therefore asks the
same law, from the same module, before it publishes and before it grades. No
second regex lives here: the code printed is the law's own. AC-EXPG1..AC-EXPG5
were pinned in src/os/backlog.md at R2834 BEFORE this change.

R2805: the "latest" line used to be the newest pair on disk with no notion of
what the pair WAS, so it named preview/ceo-blockers.html - a census of open work
items - as the CEO's latest artifact while the newest real face sat fourth. A
meta page reports on the tree (blockers, link sweeps, test shards, the entry
index); it is not something the CEO can use as a product. BOARD_PAGES therefore
names those stems and newest_artifact() skips them, publishing what it skipped
so the exclusion is auditable instead of silent. AC-EXPW7..AC-EXPW10 were pinned
in src/os/backlog.md at R2805 BEFORE this change.

Usage:
  python src/os/export_round.py                 # write the face
  python src/os/export_round.py --check         # read-only verdict
  python src/os/export_round.py --root DIR      # operate on a private world
"""
import datetime
import hashlib
import io
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import ledger_lines as LL  # noqa: E402

TZ = datetime.timezone(datetime.timedelta(hours=8))
ROUND_RE = re.compile(r'^(?:\d{4}-\d{2}-\d{2} )?R(\d{4})')
NEXT_ROW_RE = re.compile(r'^- \[ \] \[R\d{4}\] next window')
LEDGER_RE = re.compile(r'^R\d{4} tokens:')
FOLD_RE = re.compile(r'fold of log items')
FOLD_RANGE_RE = re.compile(r'log items \d+\.\.\d+')
ARCHIVE_RE = re.compile(r'state-log-archive')
# R2874 AC-RLBL3: the label shape is not repeated here - it is the write gate's
# own string, so a gate that refuses a label can never disagree with a reader
# that silently skips it.
ROUND_HEAD_RE = re.compile(
    r'^(?:\d{4}-\d{2}-\d{2} )?R\d{4} ' + LL.ROUND_LABEL_SRC)
SHORT = 300


def is_fold_summary(line):
    """True for a fold summary line, whatever prose the operator wrote.

    The knife writes free text, so matching one phrase missed the R2813 second
    knife and its summary became the CEO current line. Detector, then a
    narrowing the first draft needed and is recorded for: a summary carries the
    structural pair (the folded item range AND the archive the window went to),
    BUT this register also writes round narratives ABOUT folds, and those carry
    the same pair. A line that opens with the round-label shape this log uses
    (R#### followed by an uppercase word such as ENGINEERING: or PRODUCT) is a
    narrative no matter what it discusses; a summary never opens that way.
    """
    text = line or ''
    if FOLD_RE.search(text):
        return True
    if not (FOLD_RANGE_RE.search(text) and ARCHIVE_RE.search(text)):
        return False
    return not ROUND_HEAD_RE.match(text)

# Meta pages report on the tree, not on the business: open-work censuses, link
# sweeps, test shard verdicts and the delivered-faces index. They are useful to
# the CEO but they are never "the artifact of this window", so they must not
# occupy the latest-artifact slot (AC-EXPW7). This set is the single definition;
# every reader derives from it rather than repeating the names.
BOARD_PAGES = ('ceo-blockers', 'face-sweep', 'battery-shard-report', 'index')


def _read(path):
    with io.open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()


def last_round_line(state):
    """The headline of the LAST round in the live log.

    Refinement recorded in state log at R2780: the criterion says "the last round
    narrative line", and the most useful reading of that for a CEO-facing line is
    the round HEADLINE (its first narrative line), not its closing disclosures,
    because a round's last lines are its exceptions rather than what it did. The
    ledger line is never a narrative.
    """
    log = state.get('log') or []
    rounds = []
    for line in log:
        m = ROUND_RE.match(line or '')
        if m and not LEDGER_RE.match(line) and not is_fold_summary(line):
            rounds.append(m.group(1))
    if not rounds:
        return log[-1] if log else ''
    last = rounds[-1]
    for line in log:
        m = ROUND_RE.match(line or '')
        if m and m.group(1) == last and not LEDGER_RE.match(line) \
                and not is_fold_summary(line):
            return line
    return log[-1]


def _pairs(repo):
    """Every preview/X.html with a sibling X.json, newest first.

    Returns tuples of (mtime, html_rel, json_rel, html_bytes, json_bytes) so a
    caller can filter without re-statting the tree.
    """
    prev = os.path.join(repo, 'preview')
    rows = []
    if not os.path.isdir(prev):
        return rows
    for name in os.listdir(prev):
        if not name.endswith('.html'):
            continue
        stem = name[:-5]
        html = os.path.join(prev, name)
        doc = os.path.join(prev, stem + '.json')
        if not os.path.isfile(doc):
            continue
        m = max(os.path.getmtime(html), os.path.getmtime(doc))
        rows.append((m, 'preview/' + name, 'preview/' + stem + '.json',
                     os.path.getsize(html), os.path.getsize(doc)))
    rows.sort(key=lambda r: (-r[0], r[1]))
    return rows


def newest_pair(repo):
    """The newest preview/X.html that has a sibling X.json, by mtime."""
    rows = _pairs(repo)
    if not rows:
        return None
    return rows[0][1:]


def newest_artifact(repo):
    """The newest pair that is NOT a meta board page, plus what was skipped.

    Returns (pair, skipped, newest_is_board) where pair is
    (html_rel, json_rel, html_bytes, json_bytes) or None when every pair on disk
    is a meta page, skipped is the list of meta pairs passed over (newest first,
    formatted "path (NB)"), and newest_is_board says whether the newest pair on
    disk at all was one of them (AC-EXPW9: the exclusion is published, not
    silent).
    """
    rows = _pairs(repo)
    if not rows:
        return None, [], False
    newest_is_board = os.path.basename(rows[0][1])[:-5] in BOARD_PAGES
    for idx, r in enumerate(rows):
        if os.path.basename(r[1])[:-5] not in BOARD_PAGES:
            # only the board pairs ABOVE the chosen one were actually passed
            # over; an older meta page is not evidence of an exclusion
            skipped = ['%s (%dB)' % (b[1], b[3]) for b in rows[:idx]
                       if os.path.basename(b[1])[:-5] in BOARD_PAGES]
            return r[1:], skipped, newest_is_board
    skipped = ['%s (%dB)' % (r[1], r[3]) for r in rows
               if os.path.basename(r[1])[:-5] in BOARD_PAGES]
    return None, skipped, newest_is_board


def _fmt_pair(pair):
    return '%s (%dB) + %s (%dB)' % (pair[0], pair[2], pair[1], pair[3])


def next_window_row(repo):
    """The topmost open next-window row, with its markdown and DONE items cut."""
    board = os.path.join(repo, 'src', 'os', 'backlog.md')
    if not os.path.isfile(board):
        return ''
    for line in _read(board).splitlines():
        if NEXT_ROW_RE.match(line.strip()):
            row = line.strip()
            cut = row.find('next window:')
            tail = row[cut + len('next window:'):] if cut >= 0 else row
            parts = re.split(r'\(\d+\)', tail)
            for part in parts[1:]:
                if 'DONE' not in part:
                    return part.strip().strip('-').strip()
            return tail.strip()
    return ''


def derive(repo, state, stamp):
    """Every value the face publishes, derived from files on disk."""
    cur = last_round_line(state).strip()
    cur = re.sub(r'^(?:\d{4}-\d{2}-\d{2} )?R\d{4}\s+', '', cur).strip()
    if len(cur) > SHORT:
        cur = cur[:SHORT].rstrip() + '...'
    pair, skipped, newest_is_board = newest_artifact(repo)
    if pair:
        latest = _fmt_pair(pair)
    elif skipped:
        latest = ('(no product pair on disk - every pair is a meta board page: '
                  + ', '.join(skipped) + ')')
    else:
        latest = '(no preview pair on disk)'
    nxt = next_window_row(repo)
    if len(nxt) > SHORT:
        nxt = nxt[:SHORT].rstrip() + '...'
    if not nxt:
        nxt = 'see the top open row of src/os/backlog.md'
    due = (datetime.datetime.now(TZ) + datetime.timedelta(hours=48)) \
        .replace(microsecond=0).isoformat()
    return {
        'current': 'R%s - %s' % (state.get('tick'), cur),
        'latest': latest,
        'next': nxt,
        'next_due': due,
        'stamp': stamp,
        'tick': str(state.get('tick')),
        'board_skipped': skipped,
        'newest_is_board': newest_is_board,
    }


def archive_state(data, repo):
    """Is the results block legitimately archived, or merely missing?

    AC-EXPW11/AC-EXPW12: R2821 moved the frozen per-round narratives out of the
    document the CEO downloads and left a pointer. A pointer is only an excuse
    while it still resolves - so this returns (True, note) when the archive is
    on disk and its sha256 still matches, and (False, reason) otherwise, which
    keeps "it was archived" from being claimed over a lost archive.
    """
    arch = data.get('results_archive')
    if not isinstance(arch, dict):
        return False, 'results_archive absent'
    rel = arch.get('path') or ''
    if not rel:
        return False, 'results_archive.path is empty'
    path = os.path.join(repo, rel.replace('/', os.sep))
    if not os.path.isfile(path):
        return False, 'results_archive.path %r is not on disk' % rel
    digest = hashlib.sha256()
    with open(path, 'rb') as handle:
        for block in iter(lambda: handle.read(1 << 16), b''):
            digest.update(block)
    actual = digest.hexdigest()
    if actual != (arch.get('sha256') or ''):
        return False, ('archive sha256 %s != disk %s'
                       % ((arch.get('sha256') or '')[:16], actual[:16]))
    return True, ('results archived to %s (count=%s); tick slot not re-grown'
                  % (rel, arch.get('count')))


def payload(repo, state, stamp):
    """Build the new face WITHOUT writing it (AC-EXPW4 needs a pure path)."""
    import check_export_consistency as cec
    import export_driver_queue_face as EDQF
    exp = os.path.join(repo, 'docs', 'status-export.json')
    if not os.path.isfile(exp):
        raise ValueError('E_EXP no face at ' + exp)
    data = json.loads(_read(exp))
    d = derive(repo, state, stamp)
    # the tick slot is named by the shipped pattern table, never by a literal
    label = cec._load_patterns().get('tick_row_label')
    rows = data.get('results')
    d['tick_row_skipped'] = None
    if isinstance(rows, list):
        stamped = [r for r in rows if isinstance(r, list) and len(r) >= 2
                   and label and r[1] == label]
        if len(stamped) != 1:
            raise ValueError('E_EXP expected exactly 1 tick row, found %d'
                             % len(stamped))
        stamped[0][0] = d['tick']
    else:
        # AC-EXPW11: the block is gone on purpose. Re-creating it a row at a
        # time would refill the document R2821 emptied, so the write proceeds
        # and the skip is published instead of raising E_EXP every round.
        ok, note = archive_state(data, repo)
        if not ok:
            raise ValueError('E_EXP_NO_ARCHIVE ' + note)
        d['tick_row_skipped'] = note
        data['tick_row_skipped'] = note
    outs = data.get('outs') or []
    if not outs or outs[0] != d['latest']:
        outs.insert(0, d['latest'])
    data['outs'] = outs
    data['export_ts'] = stamp
    data['do'] = d['current']
    ceo = data.get('ceo_face') or {}
    ceo['current'] = d['current']
    ceo['latest_artifact'] = d['latest']
    ceo['last_artifact'] = d['latest']
    ceo['board_pages_skipped'] = d['board_skipped']
    ceo['newest_pair_on_disk_is_board'] = d['newest_is_board']
    ceo['next_milestone'] = d['next']
    ceo['next_milestone_due'] = d['next_due']
    ceo['updated_at'] = stamp
    data['ceo_face'] = ceo
    # AC-EXPW3: the self_drive block is not a second derivation, it IS the
    # shipped checker's own recount. recompute() reads the module paths, so the
    # block is only refreshed for the real tree; a private world keeps the block
    # it was given and refuses nothing.
    at_write = cec.recompute()[0] if os.path.abspath(repo) == os.path.abspath(REPO) \
        else None
    if at_write is not None:
        data['self_drive'] = {
            'window': at_write['window'],
            'window_days': at_write['window_days'],
            'log_lines_in_window': at_write['log_lines_in_window'],
            'idle_fast_mention_lines': at_write['idle_fast_mention_lines'],
            'no_pullable_mention_lines': at_write['no_pullable_mention_lines'],
            'substantive_non_idle_mention_lines':
                at_write['substantive_non_idle_mention_lines'],
            'proposals_total': at_write['proposals_total'],
            'proposals_open': at_write['proposals_open'],
            'queue_main_open': at_write['queue_main_open'],
            'queue_tech_open': at_write['queue_tech_open'],
            'queue_explore_open': at_write['queue_explore_open'],
        }
    EDQF.refresh(data, repo)
    return data, d


def _grader_reconcile(repo):
    """Publish every copy from the grader's ONE derivation (R2832).

    Measured twice (R2831, R2832): a clean `export_round` run refreshed only
    the ceo_face copies, left the top-level current / next_milestone /
    state_bytes behind, and `tools/status_export_fresh.py --check` then read
    E_SXF_STALE + E_SXF_STATE_BYTES + E_SXF_MILESTONE_STALE straight after a
    successful write. Two derivations of one document always drift, so this
    writer no longer keeps its own opinion: it asks the grader that publishes
    the top-level copies (AC-SXF14/15) and then asks the same grader for the
    verdict. Only the real tree is reconciled - a private world keeps the
    behaviour its suites pin.
    """
    tools = os.path.join(repo, "tools")
    if tools not in sys.path:
        sys.path.insert(0, tools)
    import status_export_fresh as SXF
    exp = os.path.join(repo, "docs", "status-export.json")
    st = os.path.join(repo, "src", "os", "state.json")
    bl = os.path.join(repo, "src", "os", "backlog.md")
    pv = os.path.join(repo, "preview")
    code = SXF.apply(exp, st, bl, pv)
    problems = SXF.check(exp, st)
    return code, problems


def round_shape_refusal(state):
    """Ask the round-main shape law before the CEO face is written (R2834).

    The law landed at R2832 with its only production call site inside
    state_append (R2833). A state log whose newest round line lost its date
    anchor was still writable into the face, and R2831 shipped exactly such a
    face. This returns '' when the law is satisfied and a named refusal, built
    from the law's OWN code and detail, when it is not - so this module never
    grows a second opinion about what a round main line looks like.
    """
    import ledger_lines
    report = ledger_lines.check_round_main_shape(state.get('log') or [])
    if report.get('ok'):
        return ''
    return 'E_EXP_ROUND_SHAPE %s round=%s %s' % (
        report.get('code'), report.get('round'), report.get('detail'))


def write(repo, stamp):
    import export_driver_queue_face as EDQF
    state = json.loads(_read(os.path.join(repo, 'src', 'os', 'state.json')))
    refusal = round_shape_refusal(state)
    if refusal:
        raise ValueError(refusal)
    data, d = payload(repo, state, stamp)
    exp = os.path.join(repo, 'docs', 'status-export.json')
    text = json.dumps(data, ensure_ascii=False, indent=2) + '\n'
    proof = EDQF.publish(repo, exp, text)
    grader_code, grader_problems = (0, [])
    if os.path.abspath(repo) == os.path.abspath(REPO):
        grader_code, grader_problems = _grader_reconcile(repo)
    back = json.loads(_read(exp))
    # AC-RMS7: `current` is no longer compared against this module's own
    # derivation. The grader publishes the dated narrative line and grades it
    # (AC-SXF14/15), so keeping a second expected shape here would only make
    # the two derivations disagree again - measured at R2832 as ok=False over
    # a document the grader had just read PASS.
    ok = (back['ceo_face']['latest_artifact'] == d['latest']
          and back['ceo_face']['board_pages_skipped'] == d['board_skipped']
          and back['ceo_face']['newest_pair_on_disk_is_board']
          == d['newest_is_board']
          # R2834 measured: this used to read `back['export_ts'] == stamp`, which
          # compares TWO clocks. The grader that publishes the stamp takes its own
          # `now()` after this function's stamp exists, so a one-second boundary
          # made a perfectly good write report ok=False while the freshness gate
          # read PASS. The stamp's freshness is the grader's to own; what this
          # write may assert is that the published stamp is not OLDER than the
          # clock it wrote under.
          and str(back.get('export_ts') or '') >= stamp
          and back['outs'][0] == d['latest']
          and back['self_drive'] == data['self_drive']
          and grader_code == 0
          and not grader_problems)
    return ok, d, proof


def check(repo):
    """Read-only verdict: does the face narrate THIS tick with THIS artefacts?"""
    exp = os.path.join(repo, 'docs', 'status-export.json')
    if not os.path.isfile(exp):
        return ['E_EXP no face']
    data = json.loads(_read(exp))
    state = json.loads(_read(os.path.join(repo, 'src', 'os', 'state.json')))
    cur = data.get('ceo_face') or {}
    fails = []
    # AC-EXPG3: the read-only verdict asks the same law, so an unanchored log
    # reddens the gate without anyone writing anything.
    refusal = round_shape_refusal(state)
    if refusal:
        fails.append(refusal)
    pair, skipped, newest_is_board = newest_artifact(repo)
    if pair and cur.get('latest_artifact') != _fmt_pair(pair):
        fails.append('AC-EXPW1 latest_artifact is not the newest product pair '
                     'on disk')
    named = str(cur.get('latest_artifact') or '')
    stem = ''
    m = re.match(r'preview/(.+)\.html', named)
    if m:
        stem = m.group(1)
    if stem in BOARD_PAGES:
        fails.append('AC-EXPW7 latest_artifact names a meta board page (%s)'
                     % stem)
    if newest_is_board and not cur.get('board_pages_skipped'):
        fails.append('AC-EXPW9 newest pair on disk is a board page but the '
                     'skipped audit is empty')
    if not re.match(r'^(?:\d{4}-\d{2}-\d{2}\s+)?R%s\b'
                    % state.get('tick'), str(cur.get('current') or '')):
        fails.append('AC-EXPW1 current does not start with the live tick R%s'
                     % state.get('tick'))
    if not cur.get('next_milestone'):
        fails.append('AC-EXPW1 next_milestone is empty')
    if not cur.get('next_milestone_due'):
        fails.append('AC-EXPW1 next_milestone_due is empty')
    for key in ('current', 'latest_artifact', 'next_milestone'):
        if not cur.get(key):
            fails.append('AC-EXPW2 %s is empty' % key)
    return fails


USAGE = (
    'usage: export_round.py [-h] [--check] [--root DIR]\n'
    '  (no flag)     rewrite docs/status-export.json from live files\n'
    '  --check       read-only verdict, writes nothing\n'
    '  --root DIR    repo root to act on (a private world is fine)\n'
)


def unknown_flags(argv):
    """Flags this tool does not define, so a read-intent typo cannot write."""
    known = ('--check', '-h', '--help')
    found, skip = [], False
    for arg in argv:
        if skip:
            skip = False
            continue
        if arg == '--root':
            skip = True
            continue
        if arg in known:
            continue
        if arg.startswith('-'):
            found.append(arg)
    return found


def main(argv):
    if '-h' in argv or '--help' in argv:
        sys.stdout.write(USAGE)
        return 0
    bad = unknown_flags(argv)
    if bad:
        sys.stdout.write('E_EXP_ARG unknown flag refused, nothing written: %s\n'
                         % ', '.join(bad))
        return 2
    repo = REPO
    if '--root' in argv:
        if argv.index('--root') + 1 >= len(argv):
            sys.stdout.write('E_EXP_ARG --root needs a directory, nothing '
                             'written\n')
            return 2
        repo = argv[argv.index('--root') + 1]
    stamp = datetime.datetime.now(TZ).replace(microsecond=0).isoformat()
    if '--check' in argv:
        fails = check(repo)
        if fails:
            sys.stdout.write('VERDICT FAIL %d\n' % len(fails))
            for f in fails:
                sys.stdout.write('  - ' + f + '\n')
            return 2
        cur = (json.loads(_read(os.path.join(repo, 'docs',
                                             'status-export.json')))
               .get('ceo_face') or {})
        sys.stdout.write('VERDICT PASS tick=%s\n'
                         % str(cur.get('current') or '')[:28])
        return 0
    try:
        ok, d, proof = write(repo, stamp)
    except ValueError as exc:
        sys.stdout.write('%s\n' % exc)
        return 2
    sys.stdout.write('WROTE tick=%s ok=%s queue=%s queue_bytes=%s latest=%s\n'
                     % (d['tick'], ok, proof.get('gate'), proof.get('bytes'),
                        d['latest']))
    return 0 if ok and proof.get('gate') == 'CURRENT' else 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
