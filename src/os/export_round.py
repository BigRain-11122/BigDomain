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
  latest   <- the newest preview/X.html + X.json pair by mtime
  next     <- the topmost open next-window row of src/os/backlog.md
Nothing about a particular round is typed in, so the face cannot describe a
past window without the files disagreeing.

Criteria AC-EXPW1..AC-EXPW6 were pinned in src/os/backlog.md at R2780 BEFORE
this file existed.

Usage:
  python src/os/export_round.py                 # write the face
  python src/os/export_round.py --check         # read-only verdict
  python src/os/export_round.py --root DIR      # operate on a private world
"""
import datetime
import io
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

TZ = datetime.timezone(datetime.timedelta(hours=8))
ROUND_RE = re.compile(r'^(?:\d{4}-\d{2}-\d{2} )?R(\d{4})')
NEXT_ROW_RE = re.compile(r'^- \[ \] \[R\d{4}\] next window')
LEDGER_RE = re.compile(r'^R\d{4} tokens:')
FOLD_RE = re.compile(r'fold of log items')
SHORT = 300


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
        if m and not LEDGER_RE.match(line) and not FOLD_RE.search(line):
            rounds.append(m.group(1))
    if not rounds:
        return log[-1] if log else ''
    last = rounds[-1]
    for line in log:
        m = ROUND_RE.match(line or '')
        if m and m.group(1) == last and not LEDGER_RE.match(line) \
                and not FOLD_RE.search(line):
            return line
    return log[-1]


def newest_pair(repo):
    """The newest preview/X.html that has a sibling X.json, by mtime."""
    prev = os.path.join(repo, 'preview')
    best = None
    if not os.path.isdir(prev):
        return None
    for name in os.listdir(prev):
        if not name.endswith('.html'):
            continue
        stem = name[:-5]
        html = os.path.join(prev, name)
        doc = os.path.join(prev, stem + '.json')
        if not os.path.isfile(doc):
            continue
        m = max(os.path.getmtime(html), os.path.getmtime(doc))
        if best is None or m > best[0]:
            best = (m, 'preview/' + name, 'preview/' + stem + '.json',
                    os.path.getsize(html), os.path.getsize(doc))
    if best is None:
        return None
    return best[1:]


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
    pair = newest_pair(repo)
    if pair:
        latest = '%s (%dB) + %s (%dB)' % (pair[0], pair[2], pair[1], pair[3])
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
    }


def payload(repo, state, stamp):
    """Build the new face WITHOUT writing it (AC-EXPW4 needs a pure path)."""
    import check_export_consistency as cec
    import export_driver_queue_face as EDQF
    exp = os.path.join(repo, 'docs', 'status-export.json')
    if not os.path.isfile(exp):
        raise ValueError('E_EXP no face at ' + exp)
    data = json.loads(_read(exp))
    d = derive(repo, state, stamp)
    rows = data.get('results') or []
    # the tick slot is named by the shipped pattern table, never by a literal
    label = cec._load_patterns().get('tick_row_label')
    stamped = [r for r in rows if isinstance(r, list) and len(r) >= 2
               and label and r[1] == label]
    if len(stamped) != 1:
        raise ValueError('E_EXP expected exactly 1 tick row, found %d'
                         % len(stamped))
    stamped[0][0] = d['tick']
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


def write(repo, stamp):
    import export_driver_queue_face as EDQF
    data, d = payload(repo, json.loads(_read(os.path.join(repo, 'src', 'os',
                                                         'state.json'))), stamp)
    exp = os.path.join(repo, 'docs', 'status-export.json')
    text = json.dumps(data, ensure_ascii=False, indent=2) + '\n'
    proof = EDQF.publish(repo, exp, text)
    back = json.loads(_read(exp))
    ok = (back['ceo_face']['current'] == d['current']
          and back['ceo_face']['latest_artifact'] == d['latest']
          and back['ceo_face']['next_milestone'] == d['next']
          and back['export_ts'] == stamp
          and back['outs'][0] == d['latest']
          and back['self_drive'] == data['self_drive'])
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
    pair = newest_pair(repo)
    if pair and cur.get('latest_artifact') != '%s (%dB) + %s (%dB)' % (
            pair[0], pair[2], pair[1], pair[3]):
        fails.append('AC-EXPW1 latest_artifact is not the newest pair on disk')
    if not str(cur.get('current') or '').startswith('R%s' % state.get('tick')):
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


def main(argv):
    repo = REPO
    if '--root' in argv:
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
