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

FAILURE TREND (R2995): a history row alone answered "what was that day" and
nothing compared two of them, and because a row carried only urls=<count> one
page failing three days straight read like three different pages failing once
each. summarize_failure_trend() joins the history (count series) with the side
channel (which source failed which day) into ONE display line: today, the day
before, the mean, the delta, the worst day, and how many sources recurred. The
history row's schema is untouched on purpose - the same fact in two files is two
places to drift - and the line gates nothing.

EVIDENCE FACE (R2996): the trend counted, but it could not say WHICH file it
counted from, so a pruned qa/crawl-failures.jsonl read exactly like a source
that never failed (recurring=0 sources=0 both ways). The line now names its own
evidence: evidence=side when the side channel is on disk, evidence=history when
it is gone and only the day history's newest_error survives (ONE sample, a
degraded read, labelled as such), evidence=none when neither face exists. It
also carries kind=<bucket>:<n>, the most common exception CLASS in the window -
only the class token of 'E_FETCH <ExceptionType>: <msg>' is read, never the
message body, so this is a label and NOT a cause judgement. Ties break on the
bucket name so two readers never disagree.

RECURRENCE WEIGHT + ONE BUCKET (R2997): recurring=<n> counted SOURCES, so a
source failing twice and one failing twelve times read the same; the line now
carries recur=<sources>:<failures> - the same recurring sources and how many
failures the window attributes to them. When the side channel is gone the
honest answer is recur=none (UNMEASURED), never 0:0, because 0:0 would claim
"no recurrence" from evidence that never arrived. The same failure_kind() also
classifies --failures' newest error (kind=<bucket>), so one error string has
exactly one reader.

BASELINE LAW: qa/crawl-baselines.json, one object keyed by url, holding digest /
bytes / fetched_at / excerpt. It is a product file (a person can read what the
page said last time), written atomically after the record is appended.

COVERAGE + THE RETENTION ANSWER (R2998): the group canon
cph4/resource-chain.md section 4.1 requires every append-only file to have a
rotation design (current segment + archive segment + retention). The failure
files are append-only, so that law covers them BY CATEGORY - and this repo has
no rotation design for them, which is stated rather than implied. The measured
reason it is not built here: qa/crawl-failure-days.jsonl is 107B per row, one
row per day, rewritten in place on a same-day beat, so a full year is ~38.1KB;
the side channel qa/crawl-failures.jsonl grows only when a crawl actually
fails, and its worst bound at every beat failing for a year is ~9.07MB - both
two orders of magnitude below the only per-file jsonl water line the group canon
actually states (cph4/resource-chain.md section 3.4, world/*.jsonl, 100MB).
CORRECTION R2999: this header previously divided those numbers by "the
repository's 20MB per-file pre-commit gate", and that gate does not exist in
this checkout - measured, Tools/hooks/pre-commit and Tools/hooks/pre_commit_gate.py
carry no byte threshold at all (they gate round-freeze and evidence dialect).
With no reusable rotation tool in the tree and no size pressure, a second
cleanup mechanism would be machinery without a problem - so the exemption is
numeric, anchored on a line the group canon really states, and written down
here instead of silently assumed. What IS fixed is the other
half: a trimmed history used to read exactly like a repo that had just started
recording, because the line reported rows in the file and never how much of the
requested window was observed. The trend line now carries cov=<first>..<last>
(the history's own usable coverage) and wcov=<covered>/<requested days>, so an
under-observed window answers "1/7" instead of pretending to be complete.
Neither field gates: nothing turns green or red because of them.

SIZE FACE (R2999): the retention exemption above was arithmetic nobody could
check from the product, because --failures printed counts and never the BODY of
the file it counted. That line now carries bytes= (os.path.getsize, 0 when the
file is absent - absence is an answer, never an exception), lines= (every
physical row splitlines() sees, so it includes malformed rows and blank rows),
size_gate= (bytes as a percentage of SIZE_REFERENCE_BYTES, printed with four
decimals) and gate_ref=100MB (the denominator, on the line, so no reader has to
guess which law the percentage divides by). lines - (total+bad) is the blank-row
count, which is why the field is counted from the file and not from the reader:
a reader that silently skips a row shape makes the two disagree.
DISPLAY ONLY: the percentage is not a verdict. Nothing here refuses a write,
pages anyone or turns the scanner - no PASS/FLAG token exists on this line, and
a file above the reference line still prints a number rather than a judgement.
The reference is the group canon's water table line for a single append-only
jsonl, NOT a threshold this repo enforces.

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
FAILURE_KINDS = ('timeout', 'http', 'urlerror', 'dns', 'refused', 'other')
# R2999: the denominator of the display-only size_gate percentage. It is the
# group canon's water-table line for a single append-only jsonl
# (cph4/resource-chain.md section 3.4: world/*.jsonl, 100MB), NOT a threshold
# this repository enforces - this checkout's hook has no byte limb at all.
SIZE_REFERENCE_BYTES = 100 * 1024 * 1024
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
    newest_error = (newest or {}).get('error')
    return {'total': len(rows), 'recent': recent, 'bad': bad,
            'urls': len(urls), 'window_days': window_days,
            'newest_at': (newest or {}).get('failed_at'),
            'newest_error': newest_error,
            # R2997: the same bucket function the trend line uses, so one
            # error string is classified in exactly one place.
            'newest_kind': failure_kind(newest_error) if newest_error else 'none'}


def failure_file_stats(path):
    """(present, bytes, lines) for one failure file; absence is 0/0, not a raise.

    WHY (R2999): the retention exemption argued with numbers nobody could check
    from the product. bytes is the file's own size on disk; lines counts every
    physical row splitlines() sees, so a malformed row and a blank row are both
    visible - which is what makes `lines - (total+bad)` a real cross-check of
    the reader rather than a restatement of its own count. A file that exists
    but cannot be opened keeps its measured bytes and answers lines=0: the size
    is a fact either way, and this is a reader, not a gate.
    """
    try:
        size = os.path.getsize(path)
    except OSError:
        return {'present': False, 'bytes': 0, 'lines': 0}
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as fh:
            text = fh.read()
    except OSError:
        return {'present': True, 'bytes': size, 'lines': 0}
    return {'present': True, 'bytes': size, 'lines': len(text.splitlines())}


def size_gate_pct(nbytes):
    """bytes as a percentage of SIZE_REFERENCE_BYTES - DISPLAY ONLY (R2999).

    Nothing compares this number to 100 to decide anything: the value exists so
    a reader of one line can see how far the file sits from the water line the
    group canon states, instead of trusting a figure written in a header once.
    """
    return round(float(nbytes) * 100.0 / SIZE_REFERENCE_BYTES, 4)


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
    out = _summary_from_rows(rows, bad, day, window_days)
    # R2999: the body of the file, so the retention exemption can be checked
    # from the product instead of from a number written in a header once.
    stats = failure_file_stats(path)
    out['present'] = stats['present']
    out['bytes'] = stats['bytes']
    out['lines'] = stats['lines']
    out['size_gate'] = size_gate_pct(stats['bytes'])
    out['gate_ref_mb'] = SIZE_REFERENCE_BYTES // (1024 * 1024)
    return out


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


def failure_kind(error):
    """Coarse bucket for one failure's exception CLASS - a label, not a cause.

    WHY (R2996): the trend could count failures but not say what KIND they
    were, so "TimeoutError" and "HTTPError" were the same event on the line.
    The writer's own shape is the input law - run() stores
    'E_FETCH <ExceptionType>: <msg>' - so only the class token is read. The
    message body is never inspected, which is what keeps this a DISPLAY label:
    two sources failing with one class are still two unexplained failures, and
    no reader may turn this into a verdict.
    """
    text = str(error or '').strip()
    if not text:
        return 'other'
    head = text
    if head.startswith('E_FETCH'):
        head = head[len('E_FETCH'):].lstrip()
    token = head.split(':', 1)[0].strip().lower()
    if 'timeout' in token:
        return 'timeout'
    if 'http' in token:
        return 'http'
    if 'url' in token:
        return 'urlerror'
    if 'dns' in token or 'gaierror' in token:
        return 'dns'
    if 'refused' in token or 'connect' in token:
        return 'refused'
    return 'other'


def summarize_failure_trend(history_path, failures_path, day, window_days=7):
    """One line for "is today worse than the days before, and is it the same
    page each time?" (R2995).

    WHY: R2994 persisted one row per day, so the numbers were ON DISK - but
    nothing put two of them side by side, a person still compared rows by hand,
    and every row carried only urls=<count>, so one page failing three days
    straight read exactly like three different pages failing once each. This is
    a READER that joins the two faces that already exist: the day history gives
    the count series, the failure side channel gives per-failure source
    identity. Refusing to copy source names into the history row is deliberate -
    one fact stored twice is two places to drift, and the history would start
    looking like a second record face.

    DISPLAY ONLY: the five-still scanner never reads either file, nothing here
    gates, retries or pages, and no verdict changes because of this line.

    LAW: a day nobody snapshotted is ABSENT, not zero (carried from R2994), so
    today answers 'absent' rather than 0 when no row names it - and delta is
    'none' rather than a fabricated drop. recurring counts SOURCES that failed
    on two or more distinct days inside the window: one source failing many
    times on a single day is not a recurrence. The window is the same inclusive
    literal-day range the count summaries use.

    EVIDENCE (R2996): the answer also names WHERE the recurrence/kind facts came
    from, because 'recurring=0 sources=0' read the same whether the side channel
    said so or was simply deleted. evidence=side (side channel on disk),
    evidence=history (side channel gone but the day history is readable - its
    newest_error, when it has one, is a ONE-sample kind; the live repo's own
    shape is a history that exists and records nothing, which is evidence that
    nothing failed rather than no evidence), evidence=none (neither file). kind
    picks the most common exception bucket in the window; ties break on the
    bucket name so the answer is deterministic.
    """
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
    rows, hbad = read_failure_days(history_path)
    span = [r for r in rows
            if not usable
            or threshold <= str(r.get('day') or '')[:10] <= head_day]
    span.sort(key=lambda r: str(r.get('day') or ''))
    counts = [int(r.get('on_day') or 0) for r in span]
    today_row = None
    prev_row = None
    if usable:
        for row in span:
            row_day = str(row.get('day') or '')[:10]
            if row_day == head_day:
                today_row = row
            elif row_day < head_day:
                prev_row = row
    mean = None
    if counts:
        mean = round(float(sum(counts)) / len(counts), 2)
    today = int(today_row['on_day']) if today_row else (
        'absent' if usable else 'unmeasured')
    prev = int(prev_row['on_day']) if prev_row else (
        'none' if usable else 'unmeasured')
    delta = (today - prev) if (today_row and prev_row) else 'none'
    worst_row = None
    if span:
        worst_row = max(span, key=lambda r: (int(r.get('on_day') or 0),
                                             str(r.get('day') or '')))
    frows, _fbad = read_failures(failures_path)
    in_window = []
    for row in frows:
        fday = str(row.get('failed_at') or '')[:10]
        if usable and not (threshold <= fday <= head_day):
            continue
        in_window.append(row)
    days_by_source = {}
    for row in in_window:
        days_by_source.setdefault(row.get('source_url'), set()).add(
            str(row.get('failed_at') or '')[:10])
    recurring = sum(1 for days in days_by_source.values() if len(days) >= 2)
    kinds = {}
    for row in in_window:
        bucket = failure_kind(row.get('error'))
        kinds[bucket] = kinds.get(bucket, 0) + 1
    evidence = 'side' if os.path.isfile(failures_path) else 'none'
    kind = 'none'
    kind_count = 0
    if kinds:
        kind = sorted(kinds.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
        kind_count = kinds[kind]
    if evidence == 'none':
        # Degraded read (R2996): the day history keeps the last error it saw, so
        # a pruned side channel still answers. A history file that exists but
        # records nothing is evidence too - it says "nothing failed here", which
        # is a different statement from "no evidence at all" (the live repo's
        # own shape on 2026-11-19, measured before this branch was written).
        if os.path.isfile(history_path):
            evidence = 'history'
        for row in reversed(span):
            last_error = row.get('newest_error')
            if isinstance(last_error, str) and last_error.strip():
                kind = failure_kind(last_error)
                kind_count = 1
                break
    # R2997: "how many times did the recurring sources fail" - one source
    # failing 2 times and one failing 12 times read the same while the line
    # carried only recurring=<source count>. UNMEASURED, not zero: when the
    # side channel that carries per-source identity is gone, the honest answer
    # is None ('' = cannot be computed), because 0:0 would claim "no
    # recurrence" from evidence that never arrived.
    recur = None
    if evidence == 'side':
        recur_fails = 0
        for row in in_window:
            days = days_by_source.get(row.get('source_url')) or set()
            if len(days) >= 2:
                recur_fails += 1
        recur = (recurring, recur_fails)
    # R2998 COVERAGE: how much history the answer actually rested on. Measured
    # before this was written: a seven-day history trimmed down to today's one
    # row and a repo that started recording yesterday printed the SAME line,
    # because days= counts rows in the file, not the days a window was
    # observed. cov is the file's own first/last usable day; wcov is the days
    # inside the requested window that have a row over the days requested, so
    # an under-observed window is visible instead of silent.
    all_days = sorted({str(r.get('day') or '')[:10] for r in rows})
    cov = (all_days[0], all_days[-1]) if all_days else None
    win = max(1, int(window_days))
    wcov = None
    if usable:
        wcov = (len({str(r.get('day') or '')[:10] for r in span}), win)
    wday, wcount = (None, None)
    if worst_row is not None:
        wday = str(worst_row.get('day') or '')[:10]
        wcount = int(worst_row.get('on_day') or 0)
    return {'days': len(rows), 'in_window': len(span), 'bad': hbad,
            'today': today, 'prev': prev, 'mean': mean, 'delta': delta,
            'worst': (None, None) if worst_row is None else (wday, wcount),
            'recurring': recurring, 'sources': len(days_by_source),
            'recur': recur, 'cov': cov, 'wcov': wcov,
            'evidence': evidence, 'kind': kind, 'kind_count': kind_count,
            'window_days': window_days}


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
                         '(a reader over evidence; carries bytes/lines and a '
                         'display-only size_gate percentage; gates nothing)')
    ap.add_argument('--failure-days', dest='failure_days', action='store_true',
                    help='print the daily failure-count history and exit '
                         '(a display series; gates nothing)')
    ap.add_argument('--failure-trend', dest='failure_trend', action='store_true',
                    help='print the count trend joined with per-day source '
                         'recurrence and exit (a display line; gates nothing)')
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
        print('CRAWL-FAILURES total=%d recent%d=%d bad=%d urls=%d bytes=%d '
              'lines=%d size_gate=%.4f%% gate_ref=%dMB newest=%s error=%s '
              'kind=%s' % (summary['total'], summary['window_days'],
                           summary['recent'], summary['bad'], summary['urls'],
                           summary['bytes'], summary['lines'],
                           summary['size_gate'], summary['gate_ref_mb'],
                           summary['newest_at'] or 'none',
                           summary['newest_error'] or 'none',
                           summary['newest_kind']))
        return 0
    if args.failure_days:
        series = summarize_failure_days(failure_day_path(args.root), args.days)
        pairs = ','.join('%s:%s' % (d, n) for d, n in series['series'])
        print('CRAWL-FAILURE-DAYS days=%d bad=%d first=%s last=%s series=%s'
              % (series['days'], series['bad'], series['first'] or 'none',
                 series['last'] or 'none', pairs or 'none'))
        return 0
    if args.failure_trend:
        stamp = datetime.datetime.now().astimezone().isoformat(
            timespec='seconds')
        trend = summarize_failure_trend(failure_day_path(args.root),
                                        failure_path(args.root), stamp,
                                        args.days)
        wday, wcount = trend['worst']
        worst_txt = 'none' if wday is None else '%s:%d' % (wday, wcount)
        mean_txt = 'none' if trend['mean'] is None else ('%g' % trend['mean'])
        kind_txt = ('none' if trend['kind'] == 'none'
                    else '%s:%d' % (trend['kind'], trend['kind_count']))
        recur_txt = ('none' if trend['recur'] is None
                     else '%d:%d' % trend['recur'])
        cov_txt = ('none' if trend['cov'] is None
                   else '%s..%s' % trend['cov'])
        wcov_txt = ('none' if trend['wcov'] is None
                    else '%d/%d' % trend['wcov'])
        print('CRAWL-FAILURE-TREND days=%d today=%s prev=%s mean=%s delta=%s '
              'worst=%s recurring=%d sources=%d bad=%d evidence=%s kind=%s '
              'recur=%s cov=%s wcov=%s'
              % (trend['days'], trend['today'], trend['prev'], mean_txt,
                 trend['delta'], worst_txt, trend['recurring'],
                 trend['sources'], trend['bad'], trend['evidence'], kind_txt,
                 recur_txt, cov_txt, wcov_txt))
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
