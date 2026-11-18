"""Crawl records for the QA charter's daily-crawl face (R2990).

WHY: the five-still scanner judged a day's "daily crawl" by the mtime of
qa/smoke-*.png and qa/smoke-*.log. Measured 2026-11-19: those files are ROUND
EVIDENCE - one day it was a gallery screenshot plus a suite payload, and the
[QA] face still read PASS - so the gate could be green on a day where no crawl
happened at all. This module records a crawl as DATA (source URL, fetch time,
verdict) in qa/crawl-log.jsonl, one line per crawl, and the scanner reads the
record instead of a filename.

HONEST SCOPE: a record is a DECLARATION, not a proof. Nothing here fetches the
URL or re-reads the source; what it removes is the specific false green where a
screenshot of some page counted as a crawl. A round that writes a record without
crawling is telling a lie in a machine-readable format - more visible than the
old mtime test, not impossible.

DATE LAW (mirrored in the scanner, so the two sides cannot drift): a record's
day is the first ten characters of fetched_at taken LITERALLY as YYYY-MM-DD. A
writer that records a UTC stamp must still write the calendar day it means.

Stdlib only. No network. Pure functions over a path; the caller owns the world.
"""

import json
import os

FIELDS = ('source_url', 'fetched_at', 'verdict')
QA_DIR = 'qa'
RECORD_NAME = 'crawl-log.jsonl'


def record_path(repo_root):
    """Where the record lives, derived from a repo root (no globals, no cwd)."""
    return os.path.join(repo_root, QA_DIR, RECORD_NAME)


def _usable_date(value):
    """True when value starts with a literal YYYY-MM-DD calendar day."""
    if not isinstance(value, str) or len(value) < 10:
        return False
    head = value[:10]
    if head[4] != '-' or head[7] != '-':
        return False
    return head[:4].isdigit() and head[5:7].isdigit() and head[8:10].isdigit()


def missing_fields(row):
    """Names of the three fields that are absent or unusable in this row."""
    if not isinstance(row, dict):
        return list(FIELDS)
    out = []
    url = row.get('source_url')
    if not (isinstance(url, str) and (url.startswith('http://') or url.startswith('https://'))):
        out.append('source_url')
    if not _usable_date(row.get('fetched_at')):
        out.append('fetched_at')
    verdict = row.get('verdict')
    if not (isinstance(verdict, str) and verdict.strip()):
        out.append('verdict')
    return out


def day_of(row):
    """The literal calendar day a usable record names, else None."""
    if missing_fields(row):
        return None
    return row['fetched_at'][:10]


def append_record(path, source_url, fetched_at, verdict, note=''):
    """Validate and append one line. Refuses what the reader would call bad."""
    row = {'source_url': source_url, 'fetched_at': fetched_at, 'verdict': verdict}
    if note:
        row['note'] = note
    miss = missing_fields(row)
    if miss:
        raise ValueError('crawl record refused, unusable fields: ' + ','.join(miss))
    parent = os.path.dirname(path)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent)
    line = json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    with open(path, 'a', encoding='utf-8', newline='\n') as fh:
        fh.write(line + '\n')
    return row


def read_records(path):
    """(rows, bad): usable rows in file order, and the count of unusable ones.

    A missing file is zero rows and zero bad lines - absence is the caller's
    question, not an error here. A malformed line and a line with unusable
    fields are both counted bad, so a half-written append stays visible instead
    of being silently dropped.
    """
    rows = []
    bad = 0
    if not os.path.isfile(path):
        return rows, bad
    with open(path, 'r', encoding='utf-8') as fh:
        for line in fh:
            text = line.strip()
            if not text:
                continue
            try:
                row = json.loads(text)
            except ValueError:
                bad += 1
                continue
            if missing_fields(row):
                bad += 1
                continue
            rows.append(row)
    return rows, bad


def today_summary(path, today):
    """The scanner's answer: how many records name `today`, and how many are bad.

    `today` is a literal YYYY-MM-DD string, the same shape the scanner compares.
    """
    rows, bad = read_records(path)
    todays = [r for r in rows if r['fetched_at'][:10] == today]
    return {
        'rows': len(rows),
        'today': len(todays),
        'bad': bad,
        'last': todays[-1] if todays else None,
    }
