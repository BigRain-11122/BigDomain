"""Crawl runner for the QA charter's daily-crawl face (R2991).

WHY: R2990 landed the record face (qa/crawl-log.jsonl via tools/crawl_record.py)
so the five-still scanner could stop judging a crawl by a smoke file's mtime -
but nothing ever WROTE a record except the suite that grades the writer. The
honest state on 2026-11-19 was [QA] FLAG crawl_today=0: the face was truthful
and still unfillable without a human typing a line. This module is the missing
executor: it fetches one source, judges it against a stored baseline, and lands
the result through the shipped writer.

HONEST SCOPE (unchanged from the record module): a record is a DECLARATION.
This runner really does fetch, so the declaration covers a real retrieval - but
it does not prove the fetched bytes are the page a human would see (scripts,
personalisation, A/B variants and CDN edges are outside it), and it does not
decide whether a drift matters. Drift means: the visible text I normalised
tonight differs from the visible text I normalised the last time I stored it.

TWO-FACE DESIGN (so the judgement can be graded offline):
  * fetch()    - the only network call in this file, one urlopen.
  * evaluate() - pure: normalised text + stored baseline -> {verdict, digest}.
A window that wants to grade the judgement hands evaluate() a saved page and no
socket is ever opened; AC-RUN4 pins exactly that.

VERDICT LAW: no stored baseline for the url -> new-source; same visible-text
digest -> no-drift; different digest -> drift. A failed retrieval is NOT a
crawl: run() answers ok=False and writes NOTHING to the record or the baseline -
a failed fetch landing a record would turn the scanner green on a day nobody
read the source.

FAILURE TRACE (R2992): writing nothing made "did not run" and "ran and failed"
the same on disk, because a headless round's stdout only reaches a gitignored
log. A failed retrieval now appends ONE line to qa/crawl-failures.jsonl
(source_url / failed_at / error). That file is a SIDE CHANNEL: the scanner does
not read it, it never feeds a verdict, and it is physically separate from the
record file, so it cannot turn any face green or red. A trace that cannot be
written is reported as trace=None and never replaces the failure answer.

R2993 gives that file its first product READER: summarize_failures() and the
`--failures` command answer "how many, how recently, from which sources, and
what was the last error" in ONE readable line. That is deliberately still not a
gate: the scanner is untouched (AC-RUN5 pins that it never reads this file), a
failure count can turn nothing green or red, and nothing here retries or pages.
Evidence that nobody opens has the same weight as no evidence - this only makes
it openable.

DAY GATE (R2992): if_due=True makes a beat idempotent without a scheduler of
its own - when a usable record already names today, run() answers skipped=True
BEFORE any socket is opened and writes nothing. That is what makes it safe to
call this from a ten-minute grid: at most one real retrieval per day.

FAILURE HISTORY (R2994): --failures answers "what is on disk right now", so
"is today worse than yesterday" had no answer and the same page failing three
days straight read exactly like one bad afternoon. snapshot_failure_day()
persists ONE row per day in qa/crawl-failure-days.jsonl (on_day, total, recent,
bad, urls, newest), rewriting that day's row in place so a ten-minute beat does
not append duplicates. It is a DISPLAY face only: the scanner never reads it
(AC-RUN9 arm 6), the closeout census only classifies *.log, and nothing here
gates, retries or pages. A history write that fails prints its own line and
never changes the crawl's answer.

BASELINE LAW: qa/crawl-baselines.json, one object keyed by url, holding digest /
bytes / fetched_at / excerpt. It is a product file (a person can read what the
page said last time), written atomically after the record is appended.

DATE LAW: the caller passes fetched_at; this module never invents a day for the
record. qa/crawl_record.py owns validation and the literal-first-ten-chars day.

Stdlib only. ASCII source. No shell.
"""

import argparse
import datetime
import hashlib
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import crawl_record as CR

BASELINE_DIR = 'qa'
BASELINE_NAME = 'crawl-baselines.json'
FAILURE_DIR = 'qa'
FAILURE_NAME = 'crawl-failures.jsonl'
FAILURE_DAY_DIR = 'qa'
FAILURE_DAY_NAME = 'crawl-failure-days.jsonl'
EXCERPT_CHARS = 240
DEFAULT_URL = 'https://pay.weixin.qq.com/doc/v2/merchant/4011986682'
UA = 'Mozilla/5.0 (compatible; BigDomain-Crawl/1.0)'

NOISE_RE = re.compile(r'(?is)<(script|style)\b.*?</\1\s*>')
TAG_RE = re.compile(r'(?s)<[^>]+>')
SPACE_RE = re.compile(r'\s+')


def baseline_path(repo_root):
    """Where the baseline store lives, derived from a repo root."""
    return os.path.join(repo_root, BASELINE_DIR, BASELINE_NAME)


def failure_path(repo_root):
    """Side channel for failed retrievals - deliberately NOT the record path."""
    return os.path.join(repo_root, FAILURE_DIR, FAILURE_NAME)


def failure_day_path(repo_root):
    """Daily failure-count history - a DISPLAY face, never a judgement input."""
    return os.path.join(repo_root, FAILURE_DAY_DIR, FAILURE_DAY_NAME)


def _usable_day(value):
    """True when value starts with a literal YYYY-MM-DD day (the record law)."""
    if not isinstance(value, str) or len(value) < 10:
        return False
    head = value[:10]
    if head[4] != '-' or head[7] != '-':
        return False
    return head[:4].isdigit() and head[5:7].isdigit() and head[8:10].isdigit()


def append_failure(path, source_url, failed_at, error):
    """Append one failure line; refuses a row no reader could use.

    Kept apart from CR.append_record on purpose: a failure must never be able to
    reach the record file, so this writer has its own path and its own fields.
    """
    row = {'source_url': source_url, 'failed_at': failed_at, 'error': error}
    bad = []
    if not isinstance(source_url, str) or not (
            source_url.startswith('http://') or source_url.startswith('https://')):
        bad.append('source_url')
    if not _usable_day(failed_at):
        bad.append('failed_at')
    if not (isinstance(error, str) and error.strip()):
        bad.append('error')
    if bad:
        raise ValueError('crawl failure refused, unusable fields: ' + ','.join(bad))
    parent = os.path.dirname(path)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent)
    line = json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    with open(path, 'a', encoding='utf-8', newline='\n') as fh:
        fh.write(line + '\n')
    return row


def read_failures(path):
    """(rows, bad): usable failure rows, plus the count of unusable ones.

    Absence is zero rows, not an error - the same law as CR.read_records, so a
    reader can ask "what failed?" without a prior write.
    """
    rows = []
    bad = 0
    if not os.path.isfile(path):
        return rows, bad
    with open(path, 'r', encoding='utf-8', errors='replace') as fh:
        for line in fh:
            text = line.strip()
            if not text:
                continue
            try:
                row = json.loads(text)
            except ValueError:
                bad += 1
                continue
            if (not isinstance(row, dict) or not _usable_day(row.get('failed_at'))
                    or not str(row.get('error') or '').strip()):
                bad += 1
                continue
            rows.append(row)
    return rows, bad


def _summary_from_rows(rows, bad, day, window_days=7):
    """Counts over already-validated rows; the one place the window law lives."""
    head_day = (day or '')[:10]
    usable = _usable_day(head_day)
    threshold = head_day
    if usable:
        try:
            start = datetime.date.fromisoformat(head_day) - datetime.timedelta(
                days=max(1, int(window_days)) - 1)
            threshold = start.isoformat()
        except ValueError:
            usable = False
    recent = 0
    urls = set()
    newest = None
    for row in rows:
        urls.add(row.get('source_url'))
        row_day = str(row.get('failed_at') or '')[:10]
        if usable and threshold <= row_day <= head_day:
            recent += 1
        if newest is None or str(row.get('failed_at') or '') > str(
                newest.get('failed_at') or ''):
            newest = row
    return {'total': len(rows), 'recent': recent, 'bad': bad,
            'urls': len(urls), 'window_days': window_days,
            'newest_at': (newest or {}).get('failed_at'),
            'newest_error': (newest or {}).get('error')}


def summarize_failures(path, day, window_days=7):
    """Readable answer to "did retrievals fail, and how recently?" (R2993).

    WHY: the side channel had a writer and NO reader outside its own suite, so
    evidence nobody opens is the same weight as no evidence. This turns the rows
    read_failures already validates into the one line a person can act on: how
    many failures in total, how many inside the window, how many unusable lines,
    how many distinct sources, and the newest failure. An absent file is zeroes,
    never an exception - "nothing failed" is an honest answer, not an error.

    The window is inclusive of `day` and `window_days` long, compared on the
    literal first ten characters of failed_at, the same day law the record face
    uses, so the summary and the writer cannot drift apart. Nothing here gates,
    retries or pages: this is a READER over evidence, not enforcement.
    """
    rows, bad = read_failures(path)
    return _summary_from_rows(rows, bad, day, window_days)


def read_failure_days(path):
    """(rows, bad) for the daily history; a missing file is zero rows."""
    rows = []
    bad = 0
    if not os.path.isfile(path):
        return rows, bad
    with open(path, 'r', encoding='utf-8', errors='replace') as fh:
        for line in fh:
            text = line.strip()
            if not text:
                continue
            try:
                row = json.loads(text)
            except ValueError:
                bad += 1
                continue
            if (not isinstance(row, dict) or not _usable_day(row.get('day'))
                    or not isinstance(row.get('on_day'), int)):
                bad += 1
                continue
            rows.append(row)
    return rows, bad


def snapshot_failure_day(repo_root, day, window_days=7):
    """Persist today's failure counts as ONE row, replacing that day's own row.

    WHY (R2994): --failures answers "what is on disk now" and forgets the last
    time it was asked, so a page failing three days straight and one bad
    afternoon read the same. This writes the window counts down once per day so
    two days can be compared. Same-day re-runs REWRITE the row rather than
    appending: the beat fires every ten minutes, and a file that grows a row per
    beat would be noise rather than history. Only the days somebody actually
    snapshotted appear - a gap is an honest gap, not a zero.
    """
    head_day = (day or '')[:10]
    if not _usable_day(head_day):
        raise ValueError('crawl failure day refused, unusable day: %r' % (day,))
    rows, bad = read_failures(failure_path(repo_root))
    summary = _summary_from_rows(rows, bad, head_day, window_days)
    on_day = 0
    for row in rows:
        if str(row.get('failed_at') or '')[:10] == head_day:
            on_day += 1
    row = {'day': head_day, 'on_day': on_day, 'total': summary['total'],
           'recent': summary['recent'], 'bad': summary['bad'],
           'urls': summary['urls'], 'newest_at': summary['newest_at'],
           'newest_error': summary['newest_error']}
    path = failure_day_path(repo_root)
    history, _ignored = read_failure_days(path)
    kept = [r for r in history if r.get('day') != head_day]
    kept.append(row)
    kept.sort(key=lambda r: str(r.get('day') or ''))
    tmp = path + '.tmp'
    parent = os.path.dirname(path)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent)
    with open(tmp, 'w', encoding='utf-8', newline='\n') as fh:
        for item in kept:
            fh.write(json.dumps(item, ensure_ascii=False, sort_keys=True,
                                separators=(',', ':')) + '\n')
    os.replace(tmp, path)
    return row


def summarize_failure_days(path, limit=7):
    """Readable series over the daily history; zero rows is an honest answer."""
    rows, bad = read_failure_days(path)
    tail = rows[-max(1, int(limit)):]
    return {'days': len(rows), 'bad': bad,
            'first': (rows[0].get('day') if rows else None),
            'last': (rows[-1].get('day') if rows else None),
            'series': [(r.get('day'), r.get('on_day')) for r in tail]}


def crawled_today(repo_root, day):
    """True when a usable record already names `day` (the day gate's input)."""
    summary = CR.today_summary(CR.record_path(repo_root), day)
    return summary['today'] >= 1


def normalize(body):
    """Visible text of a page: noise blocks dropped, tags stripped, ws collapsed.

    Formatting-only edits (indentation, blank lines, attribute order) collapse to
    the same string on purpose, so a digest change means the text a reader sees
    changed rather than the markup around it.
    """
    if isinstance(body, bytes):
        body = body.decode('utf-8', 'replace')
    text = NOISE_RE.sub(' ', body)
    text = TAG_RE.sub(' ', text)
    for src, dst in (('&nbsp;', ' '), ('&amp;', '&'), ('&lt;', '<'),
                     ('&gt;', '>'), ('&quot;', '"'), ('&#39;', "'")):
        text = text.replace(src, dst)
    return SPACE_RE.sub(' ', text).strip()


def digest(text):
    """Stable id for a normalised page body."""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def evaluate(url, body, baseline):
    """Pure judgement: (verdict, digest, excerpt) from a page and a stored store.

    `baseline` is the parsed store (url -> entry). A missing url is new-source,
    never no-drift - an empty store cannot mean "nothing changed".
    """
    text = normalize(body)
    dg = digest(text)
    prev = baseline.get(url) if isinstance(baseline, dict) else None
    if not isinstance(prev, dict) or not prev.get('digest'):
        verdict = 'new-source'
    elif prev.get('digest') == dg:
        verdict = 'no-drift'
    else:
        verdict = 'drift'
    return {'verdict': verdict, 'digest': dg, 'text': text,
            'excerpt': text[:EXCERPT_CHARS]}


def load_baselines(path):
    """Parsed store; an absent, unreadable or non-object file reads as empty."""
    try:
        with open(path, 'r', encoding='utf-8') as fh:
            doc = json.load(fh)
    except (OSError, ValueError):
        return {}
    return doc if isinstance(doc, dict) else {}


def save_baselines(path, doc):
    """Atomic replace so a half-written store never becomes the next baseline."""
    parent = os.path.dirname(path)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent)
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(doc, fh, ensure_ascii=False, sort_keys=True, indent=1)
        fh.write('\n')
    os.replace(tmp, path)
    return path


def fetch(url, timeout=20):
    """The only network call here: one GET, decoded with replacement."""
    import urllib.request

    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        status = getattr(resp, 'status', 200)
        body = resp.read()
    if int(status) != 200:
        raise IOError('E_HTTP status=%s' % status)
    return body


def run(url, repo_root, body=None, fetched_at=None, timeout=20, write=False,
        if_due=False):
    """Fetch-or-judge one url and (optionally) land a record.

    body given  -> dry run: no socket, no retrieval, judgement only.
    body None   -> real fetch; a failure answers ok=False, traces itself to the
                   side channel, and writes nothing to the record or baseline.
    if_due      -> when a usable record already names today, answer skipped=True
                   BEFORE any socket is opened and write nothing.
    """
    dry = body is not None
    stamp = fetched_at or datetime.datetime.now().astimezone().isoformat(
        timespec='seconds')
    if if_due and crawled_today(repo_root, stamp[:10]):
        # Idempotent beat: the day is already covered, so this call is a no-op
        # rather than a second retrieval that would only re-write the baseline.
        return {'ok': True, 'error': None, 'verdict': 'skip', 'digest': None,
                'row': None, 'record': None, 'baseline': None, 'trace': None,
                'dry': dry, 'skipped': True}
    if body is None:
        try:
            body = fetch(url, timeout=timeout)
        except Exception as exc:  # every network fault is one named answer
            # A retrieval that did not happen is not a crawl, so nothing is
            # written to the record: landing one here would let the scanner read
            # a failed day as green. It is still EVIDENCE, so it goes to the
            # side channel that no judgement face reads.
            error = 'E_FETCH %s: %s' % (type(exc).__name__, exc)
            trace = None
            try:
                trace = failure_path(repo_root)
                append_failure(trace, url, stamp, error)
            except Exception:
                trace = None  # evidence that cannot land never hides the failure
            return {'ok': False, 'error': error, 'verdict': None,
                    'row': None, 'record': None, 'baseline': None, 'trace': trace,
                    'dry': dry, 'skipped': False}
    bpath = baseline_path(repo_root)
    store = load_baselines(bpath)
    verdict = evaluate(url, body, store)
    note = 'bytes=%d digest=%s%s' % (
        len(body), verdict['digest'][:12], ' dry' if dry else '')
    row = {'source_url': url, 'fetched_at': stamp,
           'verdict': verdict['verdict'], 'note': note}
    record_path = None
    baseline_written = None
    if write:
        record_path = CR.append_record(CR.record_path(repo_root), url, stamp,
                                       verdict['verdict'], note=note)
        store[url] = {'digest': verdict['digest'], 'bytes': len(body),
                      'fetched_at': stamp, 'excerpt': verdict['excerpt']}
        baseline_written = save_baselines(bpath, store)
    return {'ok': True, 'error': None, 'verdict': verdict['verdict'],
            'digest': verdict['digest'], 'row': row, 'record': record_path,
            'baseline': baseline_written, 'trace': None, 'dry': dry,
            'skipped': False}


def main(argv=None):
    ap = argparse.ArgumentParser(
        description='Fetch one source, judge it against the stored baseline, '
                    'and (with --write) land a record through the shipped writer.')
    ap.add_argument('--url', action='append', default=[],
                    help='source to fetch/judge; repeatable')
    ap.add_argument('--fixture', default='',
                    help='saved page to judge instead of fetching (dry run)')
    ap.add_argument('--root', default=os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), help='repo root (default: this checkout)')
    ap.add_argument('--write', action='store_true',
                    help='append the record and update the baseline store')
    ap.add_argument('--if-due', dest='if_due', action='store_true',
                    help='no-op when a usable record already names today '
                         '(safe to call from a repeating beat)')
    ap.add_argument('--timeout', type=int, default=20)
    ap.add_argument('--failures', action='store_true',
                    help='print the failure side channel summary and exit '
                         '(a reader over evidence; gates nothing)')
    ap.add_argument('--failure-days', dest='failure_days', action='store_true',
                    help='print the daily failure-count history and exit '
                         '(a display series; gates nothing)')
    ap.add_argument('--snapshot-failures', dest='snapshot_failures',
                    action='store_true',
                    help='persist today\'s failure counts as one history row '
                         '(same-day rows are rewritten, never duplicated)')
    ap.add_argument('--days', type=int, default=7,
                    help='window length in days for the failure faces (default 7)')
    args = ap.parse_args(argv)
    if args.failures:
        stamp = datetime.datetime.now().astimezone().isoformat(
            timespec='seconds')
        summary = summarize_failures(failure_path(args.root), stamp, args.days)
        print('CRAWL-FAILURES total=%d recent%d=%d bad=%d urls=%d newest=%s '
              'error=%s' % (summary['total'], summary['window_days'],
                            summary['recent'], summary['bad'],
                            summary['urls'], summary['newest_at'] or 'none',
                            summary['newest_error'] or 'none'))
        return 0
    if args.failure_days:
        series = summarize_failure_days(failure_day_path(args.root), args.days)
        pairs = ','.join('%s:%s' % (d, n) for d, n in series['series'])
        print('CRAWL-FAILURE-DAYS days=%d bad=%d first=%s last=%s series=%s'
              % (series['days'], series['bad'], series['first'] or 'none',
                 series['last'] or 'none', pairs or 'none'))
        return 0
    standalone_snapshot = (args.snapshot_failures and not args.url
                           and not args.if_due)
    if standalone_snapshot:
        stamp = datetime.datetime.now().astimezone().isoformat(
            timespec='seconds')
        try:
            row = snapshot_failure_day(args.root, stamp[:10], args.days)
        except Exception as exc:  # a display write must never look like a crawl
            print('CRAWL-FAILURE-DAY error=%s: %s' % (type(exc).__name__, exc))
            return 3
        print('CRAWL-FAILURE-DAY day=%s on_day=%d total=%d recent%d=%d bad=%d '
              'urls=%d' % (row['day'], row['on_day'], row['total'],
                           row['recent'], row['recent'], row['bad'],
                           row['urls']))
        return 0
    if not args.url and args.if_due:
        args.url = [DEFAULT_URL]
    if not args.url:
        print('E_NO_URL need at least one --url')
        return 2
    body = None
    if args.fixture:
        try:
            with open(args.fixture, 'r', encoding='utf-8', errors='replace') as fh:
                body = fh.read()
        except OSError as exc:
            print('E_FIXTURE %s' % exc)
            return 2
    rc = 0
    for url in args.url:
        out = run(url, args.root, body=body, timeout=args.timeout,
                  write=args.write, if_due=args.if_due)
        if out.get('skipped'):
            print('CRAWL url=%s ok=True skipped=1 why=already-crawled-today'
                  % url)
            continue
        if not out['ok']:
            print('CRAWL url=%s ok=False dry=%s error=%s trace=%s'
                  % (url, out['dry'], out['error'], out['trace'] or 'none'))
            rc = 3
            continue
        print('CRAWL url=%s ok=True dry=%s verdict=%s digest=%s record=%s '
              'baseline=%s' % (url, out['dry'], out['verdict'],
                               out['digest'][:12], out['record'] or 'none',
                               out['baseline'] or 'none'))
    if args.snapshot_failures:
        # Runs AFTER the retrieval on purpose: a failure this very beat must be
        # in the row that names today, not in tomorrow's.
        now = datetime.datetime.now().astimezone().isoformat(timespec='seconds')
        try:
            row = snapshot_failure_day(args.root, now[:10], args.days)
            print('CRAWL-FAILURE-DAY day=%s on_day=%d total=%d recent%d=%d '
                  'bad=%d urls=%d' % (row['day'], row['on_day'], row['total'],
                                      row['recent'], row['recent'], row['bad'],
                                      row['urls']))
        except Exception as exc:
            # History is display: a broken display prints its own line and
            # never rewrites the crawl's answer.
            print('CRAWL-FAILURE-DAY error=%s: %s' % (type(exc).__name__, exc))
    return rc


if __name__ == '__main__':
    sys.exit(main())
