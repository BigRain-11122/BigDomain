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

R2895: the `latest` slot only ever looks at `preview/`, so a round whose product
is a tool plus `qa/` evidence left the CEO face naming an OLDER preview - the
face was honest about the newest product page and silent about the newest thing
the round actually produced. The product slot is NOT redefined (a `.log` is not
a product page); instead a second derived line `latest_evidence` names the newest
top-level `qa/*.log` with its bytes and date, and `latest_artifact_note` appears
IFF that evidence is strictly newer than the newest non-board pair, naming it
verbatim. Both lines are derived by the same reader that grades them, so the
face cannot disagree with the disk without `--check` saying so. AC-EXPE1..
AC-EXPE4 were pinned in src/os/backlog.md at R2895 BEFORE this change.

R2897: the `latest` pair was ordered by filesystem mtime alone, so an unchanged
page that was touched, copied or restored outranked a genuinely newer one - the
line dated it "today" while its content could be days old. The ordering stamp is
now the committer time of the file's last committed CONTENT change, with mtime
kept only as the fallback for uncommitted/untracked files and for trees with no
git at all. AC-EXPD4..AC-EXPD6 were pinned in src/os/backlog.md at R2897 BEFORE
this change.

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
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import ledger_lines as LL  # noqa: E402

TZ = datetime.timezone(datetime.timedelta(hours=8))
GIT_TIMEOUT = 20
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


def _git(repo, args):
    """Run one read-only git command; None means "no answer", never a raise.

    R2897: the export face must keep working on a tree that has no git at all
    (every private test world does), so every git question here is answered
    with None rather than an exception and the caller falls back to mtime.
    """
    try:
        proc = subprocess.run(['git', '-C', repo] + args,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.DEVNULL,
                              timeout=GIT_TIMEOUT)
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout.decode('utf-8', 'replace')


def _git_content_times(repo):
    """preview/ path -> committer time of the last commit that changed it.

    R2897 AC-EXPD4: git records WHEN THE CONTENT changed, which is the question
    the artifact line claims to answer; a filesystem clock moves when a file is
    merely touched, copied or restored. One `git log` is asked for the whole
    preview/ tree, newest commit first, so the first time a path appears is its
    most recent content change.
    """
    if not os.path.exists(os.path.join(repo, '.git')):
        return {}
    text = _git(repo, ['log', '--format=%x00%ct', '--name-only', '--', 'preview'])
    if text is None:
        return {}
    times = {}
    stamp = None
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith('\x00'):
            try:
                stamp = float(line[1:])
            except ValueError:
                stamp = None
            continue
        if stamp is not None and line not in times:
            times[line.replace('\\', '/')] = stamp
    return times


def _git_uncommitted(repo):
    """preview/ paths whose committed bytes are NOT what is on disk.

    R2897 AC-EXPD5: a file written after the commit that git would name must use
    its own mtime, because its content really is newer than that commit - and an
    untracked file is uncommitted by definition.
    """
    if not os.path.exists(os.path.join(repo, '.git')):
        return set()
    text = _git(repo, ['status', '--porcelain', '--', 'preview'])
    if text is None:
        return set()
    dirty = set()
    for line in text.splitlines():
        if len(line) < 4:
            continue
        rel = line[3:].strip()
        if ' -> ' in rel:
            rel = rel.split(' -> ', 1)[1]
        dirty.add(rel.replace('\\', '/'))
    return dirty


def _pairs(repo):
    """Every preview/X.html with a sibling X.json, newest first.

    Returns tuples of (content_time, html_rel, json_rel, html_bytes,
    json_bytes, provenance) so a caller can filter without re-statting the tree.

    R2897 AC-EXPD4: the ordering stamp is the pair's CONTENT time - the
    committer time of the file's last committed change - because an unchanged
    page whose mtime was touched must not outrank a genuinely newer one. The
    disk clock is kept only to break a tie inside one commit, where the writing
    order is the only remaining evidence.

    R2898 AC-EXPD7: provenance names WHICH clock the winning stamp came from -
    'commit' when it is the committer time of that file's last committed
    content change, 'mtime' when the file that won is dirty, untracked or sits
    in a tree with no git. It is reported for the file whose stamp won, so the
    marker always describes the date next to it rather than the pair in general.
    """
    prev = os.path.join(repo, 'preview')
    rows = []
    if not os.path.isdir(prev):
        return rows
    times = _git_content_times(repo)
    dirty = _git_uncommitted(repo)
    for name in os.listdir(prev):
        if not name.endswith('.html'):
            continue
        stem = name[:-5]
        html = os.path.join(prev, name)
        doc = os.path.join(prev, stem + '.json')
        if not os.path.isfile(doc):
            continue
        html_rel = 'preview/' + name
        json_rel = 'preview/' + stem + '.json'
        h_m = os.path.getmtime(html)
        j_m = os.path.getmtime(doc)
        # AC-EXPD5: committed and clean uses git's content time; dirty,
        # untracked and non-git fall back to the file's own mtime.
        # AC-EXPD7: the branch taken is remembered, because the published date
        # must say which of the two clocks it is.
        if html_rel in dirty:
            h_c, h_src = h_m, 'mtime'
        elif html_rel in times:
            h_c, h_src = times[html_rel], 'commit'
        else:
            h_c, h_src = h_m, 'mtime'
        if json_rel in dirty:
            j_c, j_src = j_m, 'mtime'
        elif json_rel in times:
            j_c, j_src = times[json_rel], 'commit'
        else:
            j_c, j_src = j_m, 'mtime'
        if h_c >= j_c:
            stamp, src = h_c, h_src
            win = 'html'
        else:
            stamp, src = j_c, j_src
            win = 'json'
        # R2899 AC-EXPD10/AC-EXPD11: the stamp above belongs to the half that
        # won, so a pair whose halves carry different (date, clock) would publish
        # one half and stay silent about the other. The note names both halves
        # and is EMPTY when they agree, so it can never become chatter.
        # R2900 AC-EXPD13: the note also names WHICH half the bracket describes,
        # because two halves sharing a date and differing only in clock render as
        # the same date twice and the winner is not readable from the note.
        # R2901 AC-EXPD16: that tag reads `later=`, not `newer=`. What is
        # measured is which half carries the later STAMP; whether the bytes
        # CHANGED is not measurable from one snapshot (a re-save with identical
        # bytes moves the stamp and no number on this line moves with it), so the
        # word that asserts change is the defect rather than a missing digest.
        h_lab = '%s %s' % (pair_date(h_c), h_src)
        j_lab = '%s %s' % (pair_date(j_c), j_src)
        note = '' if h_lab == j_lab else (
            'halves differ: html [%s] + json [%s]; later=%s'
            % (h_lab, j_lab, win))
        rows.append((stamp, max(h_m, j_m), html_rel, json_rel,
                     os.path.getsize(html), os.path.getsize(doc), src, note))
    rows.sort(key=lambda r: (-r[0], -r[1], r[2]))
    return [(r[0], r[2], r[3], r[4], r[5], r[6], r[7]) for r in rows]



def newest_pair(repo):
    """The newest preview/X.html that has a sibling X.json, by content time.

    Returns the whole _pairs row minus its ordering stamp, i.e. (html_rel,
    json_rel, html_bytes, json_bytes, provenance) - R2898 kept provenance in
    the row, so a caller that drops it here would lose the clock the published
    date came from.
    """
    rows = _pairs(repo)
    if not rows:
        return None
    return rows[0][1:]


# R2895 AC-EXPE1: evidence is a top-level `qa/*.log` only. Recursing would make
# the line name a shard log nested under a driver's own output directory, and a
# `.json`/`.html` next to it is a fixture, not a receipt of a measured run.
EVIDENCE_DIR = 'qa'
EVIDENCE_EXT = '.log'
NO_EVIDENCE = '(no qa evidence on disk)'
# The line this module writes, read back by --check so a published name can be
# verified against the file instead of trusted.
EVIDENCE_LINE_RE = re.compile(
    r'^(qa/[^\s]+\.log) \((\d+)B, (\d{4}-\d{2}-\d{2})\)$')


def _evidence_rows(repo):
    """Every top-level qa/*.log, newest first: (mtime, rel, bytes)."""
    qa = os.path.join(repo, EVIDENCE_DIR)
    rows = []
    if not os.path.isdir(qa):
        return rows
    for name in os.listdir(qa):
        if not name.endswith(EVIDENCE_EXT):
            continue
        path = os.path.join(qa, name)
        if not os.path.isfile(path):
            continue
        rows.append((os.path.getmtime(path), EVIDENCE_DIR + '/' + name,
                     os.path.getsize(path)))
    rows.sort(key=lambda r: (-r[0], r[1]))
    return rows


def newest_evidence(repo):
    """The newest top-level qa/*.log as (rel, bytes, date, mtime), or None.

    The date is rendered from the file's OWN mtime rather than from a clock, so
    a private world with fixed stamps reads the same line every run.
    """
    rows = _evidence_rows(repo)
    if not rows:
        return None
    mtime, rel, size = rows[0]
    stamp = datetime.datetime.fromtimestamp(mtime, TZ).strftime('%Y-%m-%d')
    return (rel, size, stamp, mtime)


def newest_product_mtime(repo):
    """The birth stamp of the newest NON-board preview pair, or None."""
    for row in _pairs(repo):
        if os.path.basename(row[1])[:-5] not in BOARD_PAGES:
            return row[0]
    return None


def _fmt_evidence(ev):
    return '%s (%dB, %s)' % (ev[0], ev[1], ev[2])


def newest_artifact(repo):
    """The newest pair that is NOT a meta board page, plus what was skipped.

    Returns (pair, skipped, newest_is_board) where pair is the whole _pairs row
    (mtime, html_rel, json_rel, html_bytes, json_bytes) or None when every pair
    on disk is a meta page, skipped is the list of meta pairs passed over (newest
    first, formatted "path (NB)"), and newest_is_board says whether the newest
    pair on disk at all was one of them (AC-EXPW9: the exclusion is published,
    not silent).

    R2896 AC-EXPD1: the row is returned WHOLE rather than sliced, because the
    pair's mtime is now part of the published line and dropping it here would
    make the date unrenderable at the one call site that publishes it.
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
            return r, skipped, newest_is_board
    skipped = ['%s (%dB)' % (r[1], r[3]) for r in rows
               if os.path.basename(r[1])[:-5] in BOARD_PAGES]
    return None, skipped, newest_is_board


# R2896 AC-EXPD1: the published pair line read back from a face. A date-less
# line and a line with a wrong date are both shapes this regex accepts textually
# - the DATE ITSELF is graded against the file by comparing against fmt_pair(),
# never by trusting the string, so a stale face cannot read clean by shape.
# R2898 AC-EXPD7: the date is followed by the clock it was rendered from, so a
# committed stamp and a touched-file stamp can no longer read alike. Group 1 is
# still the DATE, which every pre-R2898 consumer reads; group 2 is the marker.
# R2901 AC-EXPD16: the tail tag is `later=` and the retired `newer=` shape is not
# accepted, so a face that claims the older word is refused at the shape level
# instead of merely disagreeing with the derived line.
PAIR_LINE_RE = re.compile(
    r'^preview/\S+\.html \(\d+B\) \+ preview/\S+\.json \(\d+B\) '
    r'\[(\d{4}-\d{2}-\d{2}) (commit|mtime)\]'
    r'(?: \(halves differ: html \[\d{4}-\d{2}-\d{2} (?:commit|mtime)\] '
    r'\+ json \[\d{4}-\d{2}-\d{2} (?:commit|mtime)\]; later=(?:html|json)\))?$')


def pair_date(mtime):
    """The pair's OWN date, rendered from its content stamp, not from a clock.

    R2897: the stamp is the committer time of the pair's last committed content
    change (or its mtime while uncommitted), so touching an old page no longer
    re-dates it.
    """
    return datetime.datetime.fromtimestamp(mtime, TZ).strftime('%Y-%m-%d')


def fmt_pair(pair):
    """The published pair line: both files' bytes, the pair's own date, its clock.

    R2896 AC-EXPD1: the line carried bytes only, so this window's artifact and a
    two-day-old one read identically at a glance - the same blindness the R2895
    evidence line removed from the other slot. The date is the pair's content
    stamp, so a private world with fixed stamps reads the same line every run, and
    tools/status_export_fresh.py calls THIS function rather than re-formatting the
    field a second time (AC-SXF15: one field, one formatter).

    R2898 AC-EXPD7: the date is followed by the clock it came from - 'commit' or
    'mtime'. A 5-tuple (a caller still holding a pre-R2898 row) reads 'mtime',
    which is what that row's date always meant.

    R2899 AC-EXPD11: when the two halves carry different (date, clock) the line
    says so in a trailing note naming BOTH halves, because the bracket above
    describes only the half that won the max. The note is empty when they agree,
    so an agreeing pair publishes exactly the R2898 shape.

    R2901 AC-EXPD16: the note's tag reads 'later=<half>' and means the half whose
    STAMP is later, never the half whose bytes changed - a re-save with identical
    bytes moves the stamp while no number on the line moves with it.
    """
    prov = pair[5] if len(pair) > 5 else 'mtime'
    line = '%s (%dB) + %s (%dB) [%s %s]' % (
        pair[1], pair[3], pair[2], pair[4], pair_date(pair[0]), prov)
    note = pair[6] if len(pair) > 6 else ''
    return line + (' (%s)' % note if note else '')


_fmt_pair = fmt_pair


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


def heartbeat_block(repo, state):
    """The heartbeat birth site's own verdict, PUBLISHED instead of printed.

    R3113 measured: of eleven repo hits naming the closeout's `hb=` reading,
    zero parse it in production (two are the writer's own format strings, two
    are assertions inside its test, the rest are prose copies). A reading no
    surface consumes is a reading that cannot be missed. This block hands it to
    the CEO face: every value comes from heartbeat.verify() over the tree, so a
    PASS cannot be typed into the document either.
    """
    import heartbeat
    try:
        state_tick = int(state.get('tick'))
    except (TypeError, ValueError):
        state_tick = None
    verdict = heartbeat.verify(repo, state_tick)
    return {
        'tick': verdict.get('tick'),
        'state_tick': verdict.get('state'),
        'lag': verdict.get('lag'),
        'verdict': verdict.get('status'),
        'reason': verdict.get('reason'),
    }


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
    # AC-EXPE1/AC-EXPE2: the evidence line stands on its own, and the note says
    # out loud which of the two is newer. The product slot keeps its own law -
    # a log is never promoted into `latest` (AC-EXPE4).
    ev = newest_evidence(repo)
    evidence = _fmt_evidence(ev) if ev else NO_EVIDENCE
    prod_m = newest_product_mtime(repo)
    note = ''
    if ev and (prod_m is None or ev[3] > prod_m):
        note = ('newest artifact this window is EVIDENCE, not a product page: '
                + _fmt_evidence(ev))
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
        'evidence': evidence,
        'note': note,
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


def corpus_block(corpus):
    """Publish the tree-gate corpus reading, or nothing at all (R3128).

    Measured before this existed: the corpus is derived in exactly ONE place
    (tools/closeout_gate.py hands its `stats` out-parameter of
    qa_writer_census.check_against_baseline into the verdict), and the OK path
    runs the gate BEFORE the writer - so handing the block in costs zero extra
    walking. Asking this module to run the census itself would re-read the
    whole qa tree (4219 files / 508.1MB at R3124) every round.

    Absent input publishes NOTHING rather than a zero: a fabricated 0/0 would
    read as a measured empty corpus, which is the opposite of "not measured".
    The MB divisor is decimal because the label says MB (R3126).

    R3130: a zero-file corpus is ALSO unpublishable, because the one supply
    path can never produce one. Measured (qa/probe-R3130.log): an empty qa/
    directory and a missing qa/ directory both make check_against_baseline
    return rc=3 BEFORE it writes `stats`, so the gate refuses as E_CLG_EMPTY
    with an empty corpus and the block is never built; only-unreadable
    entries read files=1/readable=0, and zero-byte files read files=2. Across
    the six corpus blocks a published face has ever carried (two historical
    revisions x two levels, plus the live face x two) files is 4230 or 4240 -
    never 0. So `files <= 0` is a caller error, not an empty corpus, and the
    card would otherwise print "CORPUS files=0 readable=0 mb=0.0" as if the
    tree had been read and found empty.
    """
    if not isinstance(corpus, dict):
        return None
    files = corpus.get('files')
    total = corpus.get('bytes')
    if files is None or total is None:
        return None
    try:
        files = int(files)
        total = int(total)
    except (TypeError, ValueError):
        return None
    block = {'files': files, 'bytes': total, 'mb': round(total / 1e6, 1)}
    readable = corpus.get('readable')
    try:
        readable = int(readable)
    except (TypeError, ValueError):
        # R3131: a corpus that cannot state how many entries it could read is
        # a caller error, not a corpus of unknown readability. Measured
        # (qa/probe-R3131.log): the one shipped caller is inside this module's
        # payload(), the census writes files/readable/bytes in ONE block
        # (qa_writer_census.py:465-467), all 8 corpus blocks a published face
        # has ever carried state readable (files 4230/4240/4248), and a
        # readable-less block is invisible to the freshness gate (live face
        # copy: same FRESH verdict and empty error set with or without it) -
        # while the card prints "readable=none", which reads like "measured,
        # could not read". So readable is mandatory: absent or unparseable
        # publishes NOTHING.
        return None
    block['readable'] = readable
    if readable > files:
        # R3133: a corpus that claims more readings than entries is a caller
        # error, not a very readable tree. Measured (qa/probe-R3133.log): the
        # census derives files and readable from ONE enumeration (one scandir,
        # one `corpus_readable += 1` inside the names loop), a private world of
        # 4 entries with 2 denied reads reads files=4 readable=2, and across
        # the 10 corpus blocks a published face has ever carried the pairs are
        # 4230/4230, 4240/4240, 4248/4248 and 4256/4256 - never an over-count
        # and never a negative unread. So readable > files cannot come from the
        # supply path, and refusing here keeps `unread` non-negative by
        # construction instead of publishing unread=-2.
        return None
    # The token appears ONLY when the two disagree, so a clean corpus
    # publishes no unread key instead of a decorative zero.
    if readable != files:
        block['unread'] = files - readable
    if files <= 0:
        # R3130: refused AFTER the derivation above so the shape is visible to
        # a reader of this function, and refused at all because no shipped
        # caller can hand it a measured zero (the census refuses empty targets
        # with rc=3 before stats exists).
        return None
    return block


def payload(repo, state, stamp, corpus=None):
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
    # AC-EXPE1/AC-EXPE2: both copies of the evidence line move together, for the
    # same reason AC-SXF15 pins two copies of latest_artifact - one writer, one
    # value, so a reader cannot find two opinions in one document.
    ceo['latest_evidence'] = d['evidence']
    ceo['latest_artifact_note'] = d['note']
    data['latest_evidence'] = d['evidence']
    # R3113: the heartbeat reading gets a consumer. Two copies of ONE derivation,
    # for the same reason the evidence line carries two - a reader must never
    # find two opinions about the same file in one document.
    hb = heartbeat_block(repo, state)
    data['heartbeat'] = hb
    ceo['heartbeat'] = hb
    # R3128: the tree-gate corpus reading gets the same treatment - two copies
    # of ONE derivation, and only when the caller actually measured it. An
    # unmeasured writer REMOVES the pair instead of leaving the previous
    # round's counts behind, because a stale count reads exactly like a live
    # one on a face that carries no age of its own.
    cb = corpus_block(corpus)
    if cb is not None:
        data['corpus'] = cb
        ceo['corpus'] = cb
    else:
        data.pop('corpus', None)
        ceo.pop('corpus', None)
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


UNJUDGEABLE_CODES = ('E_EXP_BAD_TS', 'E_EXP_BAD_FILE', 'E_EXP_NO_FILE',
                     'E_EXP_BAD_FACE')


def face_judgeable(exp, now=None):
    """AC-EXPR2 (R3116): can the shipped gate JUDGE the face just landed?

    R3116 measured that all four birth sites compare shapes and not one asks
    the gate that actually reads the face whether it can read it - a naive
    stamp would pass every shape check and still print `unreadable` on the
    CEO card. Returns (code, report); code None means judgeable.

    Only the four refusal codes count: freshness and the milestone window are
    deliberately NOT judged here. A face is a snapshot, and an absent due
    stamp is an honest unknown rather than a defect - the writer has no
    standing to convict the milestone window.
    """
    import export_freshness as EF
    if now is None:
        now = datetime.datetime.now(TZ)
    try:
        report = EF.assess(exp, now)
    except EF.ExportFreshnessError as exc:
        return exc.code, None
    if not report.get('present'):
        return 'E_EXP_NO_FILE', report
    return None, report


def write(repo, stamp, corpus=None):
    import export_driver_queue_face as EDQF
    state = json.loads(_read(os.path.join(repo, 'src', 'os', 'state.json')))
    refusal = round_shape_refusal(state)
    if refusal:
        raise ValueError(refusal)
    data, d = payload(repo, state, stamp, corpus=corpus)
    exp = os.path.join(repo, 'docs', 'status-export.json')
    text = json.dumps(data, ensure_ascii=False, indent=2) + '\n'
    proof = EDQF.publish(repo, exp, text)
    grader_code, grader_problems = (0, [])
    if os.path.abspath(repo) == os.path.abspath(REPO):
        grader_code, grader_problems = _grader_reconcile(repo)
    back = json.loads(_read(exp))
    # AC-EXPR2 (R3116): shape equality is not judgement. Ask the shipped gate
    # whether the face this writer just landed can be judged at all before
    # reporting ok - a naive stamp passes every shape check above and still
    # prints `unreadable` on the only face the CEO keeps rendering.
    unjudgeable, _report = face_judgeable(exp)
    if unjudgeable:
        raise ValueError('E_EXPR_UNPROVEN the face cannot be judged '
                         'face=WRITTEN code=%s' % unjudgeable)
    # AC-RMS7: `current` is no longer compared against this module's own
    # derivation. The grader publishes the dated narrative line and grades it
    # (AC-SXF14/15), so keeping a second expected shape here would only make
    # the two derivations disagree again - measured at R2832 as ok=False over
    # a document the grader had just read PASS.
    ok = (back['ceo_face']['latest_artifact'] == d['latest']
          and back['ceo_face']['board_pages_skipped'] == d['board_skipped']
          and back['ceo_face']['newest_pair_on_disk_is_board']
          == d['newest_is_board']
          and back['ceo_face'].get('latest_evidence') == d['evidence']
          and back['ceo_face'].get('latest_artifact_note') == d['note']
          and back.get('latest_evidence') == d['evidence']
          # R3113: the writer must publish the heartbeat reading it derived -
          # this is the consumer the R3113 probe measured as missing.
          and back.get('heartbeat') == data.get('heartbeat')
          and (back.get('ceo_face') or {}).get('heartbeat')
          == back.get('heartbeat')
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
    # AC-EXPR1: the published heartbeat block is graded for INTERNAL
    # consistency, never for freshness. The face is a snapshot at export_ts and
    # a heartbeat legitimately lags between rounds, so comparing it to the live
    # tree here would redden every round - a gate that cannot pass is not a gate.
    hb = data.get('heartbeat')
    if isinstance(hb, dict):
        if hb.get('verdict') not in ('PASS', 'FLAG'):
            fails.append('AC-EXPR1 heartbeat verdict %r is not PASS/FLAG'
                         % (hb.get('verdict'),))
        if hb.get('tick') is not None and hb.get('state_tick') is not None:
            try:
                want = int(hb['state_tick']) - int(hb['tick'])
            except (TypeError, ValueError):
                fails.append('AC-EXPR1 heartbeat ticks are not integers')
            else:
                if hb.get('lag') != want:
                    fails.append('AC-EXPR1 heartbeat lag %r != state_tick - tick'
                                 % (hb.get('lag'),))
        if cur.get('heartbeat') != hb:
            fails.append('AC-EXPR1 the two heartbeat copies disagree')
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
    # AC-EXPE1/AC-EXPE2: the evidence line and its note are graded against the
    # file the line NAMES, not against "whatever is newest right now". Measured
    # at R2895 under the runner: a battery leg writes its own qa/*.log while the
    # suite runs, so a "must equal the newest on disk" law reddens every leg
    # that produces evidence - the same shape as the R2890 stale-derived-value
    # defect. The face is a SNAPSHOT at export_ts: what it may assert is that
    # the file it names exists and that its bytes and date are true.
    ev_all = _evidence_rows(repo)
    named = str(cur.get('latest_evidence') or '')
    ev_ref = None
    if named == NO_EVIDENCE:
        if ev_all:
            fails.append('AC-EXPE1 the face states no qa evidence exists while '
                         '%d qa/*.log file(s) are on disk' % len(ev_all))
    else:
        m = EVIDENCE_LINE_RE.match(named)
        if not m:
            fails.append('AC-EXPE1 latest_evidence is not in the derived line '
                         'shape: %r' % named[:60])
        else:
            rel, size, date = m.group(1), int(m.group(2)), m.group(3)
            path = os.path.join(repo, rel.replace('/', os.sep))
            if not os.path.isfile(path):
                fails.append('AC-EXPE1 latest_evidence names a file that is not '
                             'on disk: %s' % rel)
            else:
                real_m = os.path.getmtime(path)
                real_date = datetime.datetime.fromtimestamp(real_m, TZ) \
                    .strftime('%Y-%m-%d')
                real_size = os.path.getsize(path)
                if real_size != size or real_date != date:
                    fails.append('AC-EXPE1 latest_evidence lies about %s '
                                 '(claims %dB/%s, disk %dB/%s)'
                                 % (rel, size, date, real_size, real_date))
                else:
                    ev_ref = (rel, real_size, real_date, real_m)
    prod_m = newest_product_mtime(repo)
    want_note = bool(ev_ref and (prod_m is None or ev_ref[3] > prod_m))
    have_note = str(cur.get('latest_artifact_note') or '').strip()
    if want_note and not have_note:
        fails.append('AC-EXPE2 evidence is newer than the product pair but no '
                     'note is published')
    if want_note and have_note and (ev_ref[0] not in have_note):
        fails.append('AC-EXPE2 the note does not name the evidence file %r'
                     % ev_ref[0])
    if not want_note and have_note:
        fails.append('AC-EXPE2 a note is published although no evidence file '
                     'is newer than the product pair')
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
