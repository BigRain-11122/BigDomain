"""Battery suite for tools/crawl_runner.py (R2991).

WHY: R2990 landed the record face, and nothing ever wrote a record except the
suite grading the writer - the daily-crawl limb stayed an honest red that no
executor could fill. crawl_runner is that executor, and this suite grades the
two things a crawl executor can be wrong about: the JUDGEMENT (is this page the
same page?) and the DECLARATION (does a failure never look like a crawl?).

PINNED BEFORE THE CODE: AC-RUN1..AC-RUN4 were written into src/os/backlog.md in
this same window, BEFORE crawl_runner.py existed (in-window pre-registration,
disclosed as such). AC-RUN5/AC-RUN6 followed at R2992 and AC-RUN7/AC-RUN8 at
R2993, each pinned in the same board file before the function or arm it grades.
AC-RUN7 grades the failure side channel's first READER (summarize_failures and
`--failures`); AC-RUN8 grades the launcher block offline, since R2992 disclosed
that "the one part no arm covers" was exactly that block. AC-RUN9/AC-RUN10
(R2994) grade the daily failure HISTORY (one row per day, rewritten in place)
and its reader, plus the launcher's --root $Project anchor - all offline.
AC-RUN11/AC-RUN12 (R2995) grade the TREND line that joins the history with the
side channel (today / previous day / mean / delta / worst day / recurrence) and
the launcher's flag ORDER (the snapshot must follow the write), both offline:
nothing here writes a file outside a temp directory and no launcher is started.
AC-RUN13 (R2996) grades the trend's EVIDENCE label (side / history / none) and
the failure CLASS bucket it carries, so a pruned side channel cannot read like
a source that never failed - also offline, temp directories only.
AC-RUN14 (R2997) grades the recurrence WEIGHT (recur=<sources>:<failures>, and
none rather than 0:0 once the side channel is gone) and the single shared
failure_kind() bucket that both --failures and the trend line now read.
AC-RUN16 (R2999) grades the SIZE face --failures gained: the file's own bytes
and physical line count, so `lines - (total+bad)` crosses the reader against the
file, plus a DISPLAY-ONLY size_gate percentage whose denominator (100MB, the
group water table's single-jsonl line) is printed on the same row. The arm that
pins the absence of a verdict deliberately does NOT build a 100MB file; it reads
the summary's key set and the emitted tokens instead, and says so.
AC-RUN17 (R3000) grades the same size face on the HISTORY file, which is the
half of the retention exemption the header argued for it. bytes only - `lines`
was measured to equal days after any beat rewrite, so it would restate the row -
and the above-reference print path is pinned as a pure function rather than by
constructing a 100MB file, which this suite therefore never does.
AC-RUN18 (R3001) grades the trend's FAILURE IDENTITY: newest_src names the last
source by largest failed_at (not by file order) and since_ok answers
yes/no/unmeasured by reading the crawl record for a LATER row of that source -
UNMEASURED, not "no", once the side channel or the record face is gone. Every
arm writes only inside a per-run temp directory; no socket and no clock.
AC-RUN19 (R3002) grades REPAIR STABILITY: flips= counts success -> failure
transitions for the newest source, so a stable repair (fail, ok) and a source
fixed, broken again and fixed again (fail, ok, fail, ok) stop reading the same
- both answer since_ok=yes, and only flips separates them. It also pins that
flips is UNMEASURED (never 0) without a record file or a side channel, that a
same-second success and failure are not ordered into an invented flip, and that
recur keeps answering its own question (same-day flapping is one flip and
recur=0:0 at once).
AC-RUN20 (R3003) grades RECORD COVERAGE: rcov= names how far the crawl record
itself reaches (first..last day of its usable rows), so since_ok=no standing on
a record that stopped before the failure stops reading like a record that
looked afterwards. The arm that pairs a pre-failure record with a visible span
deliberately pins BOTH readings: the span makes the ambiguity visible, and
since_ok staying "no" pins that this round did NOT re-judge the verdict - a
future contract change must move that arm on purpose. It also pins that cov=
(history face) and rcov= (record face) are read from different files in the
same world, and that malformed rows can neither widen nor invent a span.

Scope, stated honestly: no arm here fetches a real page except the one failure
arm against loopback, which is meant to fail. The judgement is graded on saved
fixtures, so this suite never depends on a network being up and never writes
into qa/ - every record lands in a per-run temp directory.

Stdlib only, ASCII source, no clock of its own (fetched_at is passed in).
"""
import contextlib
import io
import json
import os
import shutil
import socket
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'tools'))

import crawl_record as CR
import crawl_runner as RUN

FAILS = []
CHECKS = []
TODAY = '2026-11-19'
PAGE_A = ('<html><head><style>.x{color:red}</style>'
          '<script>var hidden="SCRIPTTEXT";</script></head>'
          '<body><h1>Period charge</h1><p>The merchant must notify the user '
          'before the charge.</p></body></html>')
URL = 'https://pay.weixin.qq.com/doc/v2/merchant/4011986682'


def ok(name, cond, detail=''):
    CHECKS.append(name)
    if cond:
        print('  | PASS %s %s' % (name, detail))
    else:
        FAILS.append(name)
        print('  | FAIL %s %s' % (name, detail))


def world():
    return tempfile.mkdtemp(prefix='bd_crawlrun_')


def main():
    roots = []

    # AC-RUN1: normalisation drops noise and formatting, and keeps meaning.
    text = RUN.normalize(PAGE_A)
    ok('AC-RUN1', 'SCRIPTTEXT' not in text and 'color:red' not in text
       and 'before the charge' in text, 'noise blocks never reach the body')
    reformatted = ('<html>\r\n<body>\n\n  <h1> Period charge </h1>\r\n'
                   '<p>The merchant must notify the user before the   charge.'
                   '</p>\n</body></html>')
    ok('AC-RUN1', RUN.digest(RUN.normalize(PAGE_A)) == RUN.digest(
        RUN.normalize(reformatted)),
       'indentation, blank lines and CRLF collapse to one digest')
    edited = PAGE_A.replace('before the charge', 'after the charge')
    ok('AC-RUN1', RUN.digest(RUN.normalize(PAGE_A)) != RUN.digest(
        RUN.normalize(edited)), 'one real sentence change moves the digest')

    # AC-RUN2: the three verdicts, from a pure function.
    first = RUN.evaluate(URL, PAGE_A, {})
    ok('AC-RUN2', first['verdict'] == 'new-source',
       'an empty store reads new-source, never no-drift')
    store = {URL: {'digest': first['digest']}}
    ok('AC-RUN2', RUN.evaluate(URL, PAGE_A, store)['verdict'] == 'no-drift',
       'the same page reads no-drift against its own digest')
    ok('AC-RUN2', RUN.evaluate(URL, edited, store)['verdict'] == 'drift',
       'a changed page reads drift')
    ok('AC-RUN2', RUN.evaluate(URL, PAGE_A, {URL: {}})['verdict'] == 'new-source',
       'an entry with no digest cannot mean nothing changed')

    # AC-RUN3: the record lands through the shipped writer, and a failed
    # retrieval lands nothing at all.
    root = world(); roots.append(root)
    out = RUN.run(URL, root, body=PAGE_A, fetched_at=TODAY + 'T08:00:00+08:00',
                  write=True)
    path = CR.record_path(root)
    rows, bad = CR.read_records(path)
    ok('AC-RUN3', out['ok'] and len(rows) == 1 and bad == 0
       and rows[0]['verdict'] == 'new-source'
       and rows[0]['fetched_at'][:10] == TODAY,
       'one usable record, three fields, the caller\'s own day')
    bpath = RUN.baseline_path(root)
    store = RUN.load_baselines(bpath)
    ok('AC-RUN3', os.path.isfile(bpath) and URL in store
       and store[URL]['digest'] == RUN.digest(RUN.normalize(PAGE_A)),
       'the baseline store holds this url and its digest')
    again = RUN.run(URL, root, body=PAGE_A, fetched_at=TODAY + 'T09:00:00+08:00',
                    write=True)
    rows2, bad2 = CR.read_records(path)
    ok('AC-RUN3', again['verdict'] == 'no-drift' and len(rows2) == 2
       and bad2 == 0 and rows2[-1]['verdict'] == 'no-drift',
       'a second pass reads the stored baseline back as no-drift')
    dead = 'http://127.0.0.1:9/never'
    fail = RUN.run(dead, root, fetched_at=TODAY + 'T10:00:00+08:00',
                   timeout=3, write=True)
    rows3, bad3 = CR.read_records(path)
    ok('AC-RUN3', fail['ok'] is False and bool(fail['error']) and fail['row'] is None,
       'a failed retrieval answers ok=False with a named error')
    ok('AC-RUN3', len(rows3) == len(rows2) and bad3 == 0
       and dead not in RUN.load_baselines(RUN.baseline_path(root)),
       'a failed fetch writes no record and no baseline')
    same = RUN.evaluate(URL, edited, RUN.load_baselines(RUN.baseline_path(root)))
    third = RUN.run(URL, root, body=edited, fetched_at=TODAY + 'T11:00:00+08:00',
                    write=True)
    rows4, _ = CR.read_records(path)
    ok('AC-RUN3', third['verdict'] == same['verdict'] == 'drift'
       and rows4[-1]['verdict'] == same['verdict'],
       'the record carries the same verdict the judgement produced')

    # AC-RUN4: the dry path cannot touch a socket, and the network lives in one
    # function only.
    root2 = world(); roots.append(root2)
    real_socket = socket.socket

    def refuse(*_a, **_k):
        raise AssertionError('E_SOCKET a dry judgement opened a socket')

    socket.socket = refuse
    try:
        dry = RUN.run(URL, root2, body=PAGE_A, fetched_at=TODAY + 'T12:00:00+08:00')
    finally:
        socket.socket = real_socket
    ok('AC-RUN4', dry['ok'] and dry['verdict'] == 'new-source' and dry['dry'],
       'a fixture judgement answers with sockets refused')
    with open(os.path.join(ROOT, 'tools', 'crawl_runner.py'), 'r',
              encoding='utf-8') as fh:
        src = fh.read()
    ok('AC-RUN4', src.count('urlopen(') == 1
       and src.index('urlopen(') > src.index('def fetch(')
       and src.index('urlopen(') < src.index('def run('),
       'the one network call sits inside fetch(), above run()')

    # AC-RUN5: a failed retrieval leaves EVIDENCE and still lands no crawl.
    root3 = world(); roots.append(root3)
    fpath = RUN.failure_path(root3)
    ok('AC-RUN5', fpath != CR.record_path(root3)
       and os.path.basename(fpath) == 'crawl-failures.jsonl',
       'the side channel is its own path, not the record file')
    fail2 = RUN.run(dead, root3, fetched_at=TODAY + 'T13:00:00+08:00',
                    timeout=3, write=True)
    frows, fbad = RUN.read_failures(fpath)
    ok('AC-RUN5', fail2['ok'] is False and fail2['trace'] == fpath
       and len(frows) == 1 and fbad == 0
       and frows[0]['source_url'] == dead and frows[0]['failed_at'][:10] == TODAY
       and 'E_FETCH' in frows[0]['error'],
       'one traced line with url, day and a named E_FETCH error')
    rrows, rbad = CR.read_records(CR.record_path(root3))
    ok('AC-RUN5', rrows == [] and rbad == 0 and CR.today_summary(
        CR.record_path(root3), TODAY)['today'] == 0
       and not os.path.isfile(RUN.baseline_path(root3)),
       'the same failure writes nothing to the record file, not even a bad row')
    good = RUN.run(URL, root3, body=PAGE_A, fetched_at=TODAY + 'T14:00:00+08:00',
                   write=True)
    frows2, fbad2 = RUN.read_failures(fpath)
    ok('AC-RUN5', good['ok'] and good['verdict'] == 'new-source'
       and len(frows2) == 1 and fbad2 == 0,
       'a successful crawl writes nothing to the side channel')
    with open(fpath, 'a', encoding='utf-8', newline='\n') as fh:
        fh.write('{not json\n')
        fh.write('{"source_url":"https://x","failed_at":"2026-11-19T00:00:00"}\n')
    frows3, fbad3 = RUN.read_failures(fpath)
    ok('AC-RUN5', len(frows3) == 1 and fbad3 == 2,
       'bad lines are counted, usable rows still readable')
    with open(os.path.join(ROOT, 'tools', 'skills', 'bigdomain-loop-scan',
                           'scripts', 'scan_five_still.ps1'), 'r',
              encoding='utf-8', errors='replace') as fh:
        scan_src = fh.read()
    ok('AC-RUN5', 'crawl-failures' not in scan_src
       and 'crawl-log.jsonl' in scan_src,
       'the scanner reads the record and never the failure side channel')
    root4 = world(); roots.append(root4)
    with open(os.path.join(root4, 'qa'), 'w', encoding='utf-8') as fh:
        fh.write('not a directory')
    blind = RUN.run(dead, root4, fetched_at=TODAY + 'T15:00:00+08:00',
                    timeout=3, write=True)
    ok('AC-RUN5', blind['ok'] is False and blind['trace'] is None
       and 'E_FETCH' in blind['error'],
       'an unwritable trace leaves the failure answer intact, never raises')

    # AC-RUN6: the day gate makes a repeating beat idempotent.
    root5 = world(); roots.append(root5)
    CR.append_record(CR.record_path(root5), URL, TODAY + 'T06:00:00+08:00',
                     'no-drift', note='seeded')
    real_socket = socket.socket

    def refuse2(*_a, **_k):
        raise AssertionError('E_SOCKET the day gate opened a socket')

    socket.socket = refuse2
    try:
        due1 = RUN.run(URL, root5, fetched_at=TODAY + 'T16:00:00+08:00',
                       write=True, if_due=True)
    finally:
        socket.socket = real_socket
    rows5, _ = CR.read_records(CR.record_path(root5))
    ok('AC-RUN6', due1['ok'] and due1.get('skipped') is True
       and len(rows5) == 1 and not os.path.isfile(RUN.baseline_path(root5)),
       'a day already crawled answers skipped with no socket and no write')
    root6 = world(); roots.append(root6)
    fresh = RUN.run(URL, root6, body=PAGE_A, fetched_at=TODAY + 'T17:00:00+08:00',
                    write=True, if_due=True)
    ok('AC-RUN6', fresh.get('skipped') is False and fresh['verdict'] == 'new-source',
       'an empty day is due and is judged normally')
    root7 = world(); roots.append(root7)
    CR.append_record(CR.record_path(root7), URL, '2026-11-18T23:00:00+08:00',
                     'no-drift', note='yesterday')
    yday = RUN.run(URL, root7, body=PAGE_A, fetched_at=TODAY + 'T18:00:00+08:00',
                   write=True, if_due=True)
    ok('AC-RUN6', yday.get('skipped') is False,
       'yesterday\'s record does not cover today')
    root8 = world(); roots.append(root8)
    os.makedirs(os.path.join(root8, 'qa'))
    with open(CR.record_path(root8), 'w', encoding='utf-8', newline='\n') as fh:
        fh.write('{"source_url":"%s","fetched_at":"%sT05:00:00+08:00"}\n'
                 % (URL, TODAY))
    badrow = RUN.run(URL, root8, body=PAGE_A, fetched_at=TODAY + 'T19:00:00+08:00',
                     write=True, if_due=True)
    ok('AC-RUN6', badrow.get('skipped') is False,
       'a row with no verdict cannot stand in for a crawl')

    # AC-RUN7 (R2993): the failure side channel gets its first READER - the file
    # had a writer and no consumer outside this suite, which is evidence nobody
    # opens. Every arm below reads; none of them gates, retries or pages.
    root9 = world(); roots.append(root9)
    empty = RUN.summarize_failures(RUN.failure_path(root9), TODAY)
    ok('AC-RUN7', empty['total'] == 0 and empty['recent'] == 0
       and empty['bad'] == 0 and empty['urls'] == 0
       and empty['newest_at'] is None,
       'an absent side channel reads all zeroes, never an exception')
    fpath9 = RUN.failure_path(root9)
    RUN.append_failure(fpath9, 'https://a.example/1', TODAY + 'T01:00:00+08:00',
                       'E_FETCH TimeoutError: today')
    RUN.append_failure(fpath9, 'https://b.example/2', '2026-11-16T02:00:00+08:00',
                       'E_FETCH URLError: three days ago')
    RUN.append_failure(fpath9, 'https://c.example/3', '2026-10-20T03:00:00+08:00',
                       'E_FETCH URLError: thirty days ago')
    with open(fpath9, 'a', encoding='utf-8', newline='\n') as fh:
        fh.write('{oops\n')
    summ = RUN.summarize_failures(fpath9, TODAY)
    ok('AC-RUN7', summ['total'] == 3 and summ['recent'] == 2 and summ['bad'] == 1
       and summ['urls'] == 3
       and str(summ['newest_at'] or '').startswith(TODAY),
       'three usable rows (one inside the window pair), one bad line, three '
       'sources, newest names today')
    frows9, _ = RUN.read_failures(fpath9)
    newest_row = max(frows9, key=lambda r: str(r.get('failed_at') or ''))
    ok('AC-RUN7', summ['newest_error'] == newest_row['error']
       and summ['newest_at'] == newest_row['failed_at'],
       'the summary and read_failures name the same newest row')
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc9 = RUN.main(['--failures', '--root', root9])
    line9 = buf.getvalue().strip()
    ok('AC-RUN7', rc9 == 0 and 'CRAWL-FAILURES' in line9
       and 'total=3' in line9 and 'recent7=2' in line9
       and 'bad=1' in line9 and 'urls=3' in line9,
       'the CLI answers rc=0 with one line carrying every count')
    root10 = world(); roots.append(root10)
    RUN.append_failure(RUN.failure_path(root10), 'https://d.example/4',
                       TODAY + 'T04:00:00+08:00', 'E_FETCH URLError: solo')
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc10 = RUN.main(['--failures', '--root', root10])
    line10 = buf.getvalue().strip()
    ok('AC-RUN7', rc10 == 0 and 'total=1' in line10 and 'd.example' not in line10,
       '--root reads the world it is given, not the real checkout')
    root11 = world(); roots.append(root11)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc11 = RUN.main(['--failures', '--root', root11])
    line11 = buf.getvalue().strip()
    ok('AC-RUN7', rc11 == 0 and 'total=0' in line11 and 'newest=none' in line11,
       'zero failures is an honest answer with rc=0, not an error code')

    # AC-RUN8 (R2993): the launcher block R2992 added described itself as
    # "the one part no arm covers". This arm reads it offline - no launcher is
    # started, no socket is opened, and the block's own behaviour is unchanged.
    loop_path = os.path.join(ROOT, 'src', 'os', 'iteration_loop.ps1')
    with open(loop_path, 'rb') as fh:
        loop_raw = fh.read()
    loop = loop_raw.decode('ascii')
    call = loop.find(r"'tools\crawl_runner.py') --if-due --write")
    ok('AC-RUN8', call > 0,
       'the launcher calls the runner with the day gate on the call line')
    try_at = loop.rfind('try {', 0, call) if call > 0 else -1
    catch_at = loop.find('catch', call) if call > 0 else -1
    ok('AC-RUN8', try_at > 0 and catch_at > call
       and 'exit' not in loop[try_at:catch_at]
       and 'throw' not in loop[try_at:catch_at],
       'the call sits inside a try/catch that neither exits nor throws')
    spawn_at = loop.find('Start-Process')
    ok('AC-RUN8', spawn_at > call > 0,
       'the crawl beat precedes the round spawn')
    ok('AC-RUN8', all(byte < 128 for byte in loop_raw)
       and b'\r' not in loop_raw,
       'the launcher stays pure ASCII with no CR bytes')
    ok('AC-RUN8', 'crawl-daily.log' in loop[try_at:catch_at],
       'the block logs its own evidence file')

    # AC-RUN9 (R2994): the failure face gains a HISTORY - one row per day, so
    # "is today worse than yesterday" has an answer instead of being re-typed.
    # A DISPLAY face only: no arm here turns a judgement green, and arm 6 pins
    # that the scanner never reads it.
    root12 = world(); roots.append(root12)
    empty_day = RUN.snapshot_failure_day(root12, TODAY + 'T20:00:00+08:00')
    drows0, dbad0 = RUN.read_failure_days(RUN.failure_day_path(root12))
    ok('AC-RUN9', empty_day['day'] == TODAY and empty_day['on_day'] == 0
       and empty_day['total'] == 0 and empty_day['recent'] == 0
       and empty_day['bad'] == 0 and empty_day['urls'] == 0
       and len(drows0) == 1 and dbad0 == 0,
       'an absent side channel still lands one honest zero row')
    f12 = RUN.failure_path(root12)
    RUN.append_failure(f12, 'https://a.example/1', TODAY + 'T01:00:00+08:00',
                       'E_FETCH TimeoutError: today')
    RUN.append_failure(f12, 'https://b.example/2', '2026-11-16T02:00:00+08:00',
                       'E_FETCH URLError: three days ago')
    RUN.append_failure(f12, 'https://b.example/2', '2026-11-16T03:00:00+08:00',
                       'E_FETCH URLError: three days ago again')
    row2 = RUN.snapshot_failure_day(root12, TODAY + 'T20:05:00+08:00')
    ok('AC-RUN9', row2['on_day'] == 1 and row2['total'] == 3
       and row2['recent'] == 3,
       'three failures read on_day=1 total=3 recent7=3')
    dpath12 = RUN.failure_day_path(root12)
    seeded = {'day': '2026-11-18', 'on_day': 4, 'total': 9, 'recent': 4,
              'bad': 0, 'urls': 2, 'newest_at': '2026-11-18T01:00:00+08:00',
              'newest_error': 'E_FETCH URLError: seeded'}
    with open(dpath12, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(json.dumps(seeded, sort_keys=True, separators=(',', ':')) + '\n')
        fh.write(json.dumps(row2, sort_keys=True, separators=(',', ':')) + '\n')
    RUN.append_failure(f12, 'https://c.example/3', TODAY + 'T04:00:00+08:00',
                       'E_FETCH URLError: later today')
    row3 = RUN.snapshot_failure_day(root12, TODAY + 'T21:00:00+08:00')
    drows3, dbad3 = RUN.read_failure_days(dpath12)
    ok('AC-RUN9', row3['on_day'] == 2 and len(drows3) == 2 and dbad3 == 0
       and [r['day'] for r in drows3] == ['2026-11-18', TODAY]
       and drows3[0]['on_day'] == 4,
       'a same-day snap rewrites its own row and leaves the seeded day as it was')
    with open(f12, 'a', encoding='utf-8', newline='\n') as fh:
        fh.write('{oops\n')
    with open(dpath12, 'a', encoding='utf-8', newline='\n') as fh:
        fh.write('{nope\n')
    drows_pre, dbad_pre = RUN.read_failure_days(dpath12)
    ok('AC-RUN9', dbad_pre == 1 and len(drows_pre) == 2,
       'a malformed history line is counted by the reader')
    row4 = RUN.snapshot_failure_day(root12, TODAY + 'T22:00:00+08:00')
    drows4, dbad4 = RUN.read_failure_days(dpath12)
    ok('AC-RUN9', row4['bad'] == 1 and row4['total'] == 4
       and len(drows4) == 2 and dbad4 == 0,
       'a malformed failure line is counted while the rewrite drops only the '
       'unusable history line')
    root13 = world(); roots.append(root13)
    RUN.append_failure(RUN.failure_path(root13), 'https://e.example/5',
                       '2026-11-18T10:00:00+08:00', 'E_FETCH URLError: yesterday')
    t_day = RUN.snapshot_failure_day(root13, TODAY + 'T20:00:00+08:00')
    y_day = RUN.snapshot_failure_day(root13, '2026-11-18T20:00:00+08:00')
    ok('AC-RUN9', t_day['on_day'] == 0 and y_day['on_day'] == 1,
       'the day is the literal first ten characters, on both sides')
    ok('AC-RUN9', RUN.failure_day_path(root13) != RUN.failure_path(root13)
       and RUN.failure_day_path(root13) != CR.record_path(root13)
       and 'crawl-failure-days' not in scan_src,
       'the history is its own path and the scanner never reads it')

    # AC-RUN10 (R2994): the history gets a READER and the launcher gets its
    # root anchor pinned. Both are offline: no socket, no launcher started.
    root14 = world(); roots.append(root14)
    real_day = RUN.failure_day_path(ROOT)
    real_before = (os.path.getmtime(real_day) if os.path.isfile(real_day)
                   else None)
    RUN.append_failure(RUN.failure_path(root14), 'https://f.example/6',
                       TODAY + 'T09:00:00+08:00', 'E_FETCH URLError: solo')
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc14 = RUN.main(['--snapshot-failures', '--root', root14])
    line14 = buf.getvalue().strip()
    real_after = (os.path.getmtime(real_day) if os.path.isfile(real_day)
                  else None)
    ok('AC-RUN10', rc14 == 0 and 'CRAWL-FAILURE-DAY' in line14
       and 'on_day=1' in line14 and os.path.isfile(RUN.failure_day_path(root14))
       and real_before == real_after,
       'the standalone snap answers on one line and writes in the world it '
       'was given')
    RUN.snapshot_failure_day(root14, '2026-11-18T20:00:00+08:00')
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc15 = RUN.main(['--failure-days', '--root', root14])
    line15 = buf.getvalue().strip()
    ok('AC-RUN10', rc15 == 0 and 'CRAWL-FAILURE-DAYS' in line15
       and 'days=2' in line15 and ('2026-11-18:0' in line15)
       and (TODAY + ':1') in line15,
       'the reader names both days and their on_day counts')
    root15 = world(); roots.append(root15)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc16 = RUN.main(['--failure-days', '--root', root15])
    line16 = buf.getvalue().strip()
    ok('AC-RUN10', rc16 == 0 and 'days=0' in line16 and 'series=none' in line16,
       'an empty history is an honest answer with rc=0')
    snap_row14 = RUN.snapshot_failure_day(root14, TODAY + 'T23:00:00+08:00')
    drows14, _ = RUN.read_failure_days(RUN.failure_day_path(root14))
    last14 = drows14[-1]
    ok('AC-RUN10', last14 == snap_row14 and last14.get('day') == TODAY,
       'the last history row the reader sees is the row the writer returned')
    call_at10 = loop.find(r"'tools\crawl_runner.py')")
    line_end10 = loop.find('\n', call_at10)
    call_line10 = loop[call_at10:line_end10]
    ok('AC-RUN10', call_at10 > 0
       and '--if-due' in call_line10 and '--write' in call_line10
       and '--snapshot-failures' in call_line10
       and '--root $Project' in call_line10,
       'the launcher call line carries the day gate, the write, the snapshot '
       'and the root anchor')
    ok('AC-RUN10', try_at < call_at10 < spawn_at,
       'the anchored call stays inside the try and before the spawn')

    # AC-RUN11 (R2995): the history gains a TREND reader - two days side by side
    # plus whether the same source recurred. Display only: it reads the two
    # files that already exist and writes nothing.
    root16 = world(); roots.append(root16)
    h16 = RUN.failure_day_path(root16)
    f16 = RUN.failure_path(root16)
    empty_trend = RUN.summarize_failure_trend(h16, f16,
                                              TODAY + 'T20:00:00+08:00')
    ok('AC-RUN11', empty_trend['days'] == 0 and empty_trend['today'] == 'absent'
       and empty_trend['prev'] == 'none' and empty_trend['mean'] is None
       and empty_trend['delta'] == 'none'
       and empty_trend['worst'] == (None, None)
       and empty_trend['recurring'] == 0 and empty_trend['sources'] == 0,
       'two empty faces answer absent/none instead of raising')
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc17 = RUN.main(['--failure-trend', '--root', root16])
    line17 = buf.getvalue().strip()
    ok('AC-RUN11', rc17 == 0 and line17.startswith('CRAWL-FAILURE-TREND')
       and 'days=0 today=absent prev=none mean=none delta=none worst=none'
       in line17 and 'recurring=0 sources=0' in line17,
       'the CLI answers one line with every count on an empty world')
    os.makedirs(os.path.dirname(h16), exist_ok=True)
    with open(h16, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(json.dumps({'day': '2026-11-18', 'on_day': 2, 'total': 2,
                             'recent': 2, 'bad': 0, 'urls': 1},
                            sort_keys=True, separators=(',', ':')) + '\n')
        fh.write(json.dumps({'day': TODAY, 'on_day': 1, 'total': 3,
                             'recent': 3, 'bad': 0, 'urls': 2},
                            sort_keys=True, separators=(',', ':')) + '\n')
    RUN.append_failure(f16, 'https://a.example/1',
                       '2026-11-18T01:00:00+08:00', 'E_FETCH A: one')
    RUN.append_failure(f16, 'https://a.example/1',
                       '2026-11-18T02:00:00+08:00', 'E_FETCH A: again')
    RUN.append_failure(f16, 'https://a.example/1', TODAY + 'T03:00:00+08:00',
                       'E_FETCH A: today')
    trend16 = RUN.summarize_failure_trend(h16, f16, TODAY + 'T20:00:00+08:00')
    ok('AC-RUN11', trend16['today'] == 1 and trend16['prev'] == 2
       and trend16['delta'] == -1 and trend16['mean'] == 1.5
       and trend16['worst'] == ('2026-11-18', 2)
       and trend16['recurring'] == 1 and trend16['sources'] == 1,
       'two days read today=1 prev=2 delta=-1 mean=1.5, worst on the harder day')
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc18 = RUN.main(['--failure-trend', '--root', root16])
    line18 = buf.getvalue().strip()
    ok('AC-RUN11', rc18 == 0 and 'days=2' in line18 and 'mean=1.5' in line18
       and 'worst=2026-11-18:2' in line18 and 'recurring=1 sources=1' in line18,
       'the printed line names the harder day and the recurrence')
    root17 = world(); roots.append(root17)
    h17 = RUN.failure_day_path(root17)
    f17 = RUN.failure_path(root17)
    for hour in ('01', '02', '03'):
        RUN.append_failure(f17, 'https://b.example/2',
                           TODAY + 'T%s:00:00+08:00' % hour, 'E_FETCH B: same day')
    RUN.snapshot_failure_day(root17, TODAY + 'T20:00:00+08:00')
    t17 = RUN.summarize_failure_trend(h17, f17, TODAY + 'T21:00:00+08:00')
    ok('AC-RUN11', t17['today'] == 3 and t17['recurring'] == 0
       and t17['sources'] == 1 and t17['prev'] == 'none'
       and t17['delta'] == 'none',
       'three failures by one source on one day are no recurrence')
    t17b = RUN.summarize_failure_trend(h17, f17, '2026-11-21T09:00:00+08:00')
    ok('AC-RUN11', t17b['today'] == 'absent' and t17b['prev'] == 3
       and t17b['delta'] == 'none',
       'a day nobody snapshotted reads absent, never a fabricated zero')
    root18 = world(); roots.append(root18)
    h18 = RUN.failure_day_path(root18)
    f18 = RUN.failure_path(root18)
    os.makedirs(os.path.dirname(h18), exist_ok=True)
    with open(h18, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(json.dumps({'day': '2026-11-09', 'on_day': 9},
                            sort_keys=True, separators=(',', ':')) + '\n')
        fh.write(json.dumps({'day': TODAY, 'on_day': 1},
                            sort_keys=True, separators=(',', ':')) + '\n')
    RUN.append_failure(f18, 'https://c.example/3', '2026-11-09T01:00:00+08:00',
                       'E_FETCH C: old day')
    RUN.append_failure(f18, 'https://c.example/3', TODAY + 'T01:00:00+08:00',
                       'E_FETCH C: today')
    wide = RUN.summarize_failure_trend(h18, f18, TODAY + 'T20:00:00+08:00', 14)
    narrow = RUN.summarize_failure_trend(h18, f18, TODAY + 'T20:00:00+08:00', 7)
    ok('AC-RUN11', wide['mean'] == 5.0
       and wide['worst'] == ('2026-11-09', 9) and wide['recurring'] == 1
       and narrow['mean'] == 1.0 and narrow['worst'] == (TODAY, 1)
       and narrow['recurring'] == 0,
       'the same bytes read two ways: a day outside the window leaves mean, '
       'worst and recurrence alone')
    with open(h18, 'a', encoding='utf-8', newline='\n') as fh:
        fh.write('{oops\n')
    bad_trend = RUN.summarize_failure_trend(h18, f18, TODAY + 'T20:00:00+08:00',
                                            7)
    ok('AC-RUN11', bad_trend['bad'] == 1 and bad_trend['in_window'] == 1
       and bad_trend['days'] == 2,
       'a malformed history line is counted and never becomes a day')

    # AC-RUN12 (R2995): the snapshot must run AFTER the write on the same call
    # line, so the row it lands can see the failure this very beat produced.
    # Pure string order - no launcher started, no socket opened.
    write_at12 = call_line10.find('--write')
    snap_at12 = call_line10.find('--snapshot-failures')
    ok('AC-RUN12', write_at12 > 0 and snap_at12 > write_at12,
       'the snapshot flag sits after --write on the anchored call line')
    ok('AC-RUN12', 0 < call_line10.find('--if-due') < write_at12 < snap_at12
       and '--root $Project' in call_line10,
       'the order is day gate, write, snapshot, root anchor')
    ok('AC-RUN12', try_at < call_at10 < spawn_at
       and all(byte < 128 for byte in loop_raw) and b'\r' not in loop_raw,
       'the ordered line stays inside the try, before the spawn, pure ASCII')

    # AC-RUN13 (R2996): the trend line names its own EVIDENCE and the failure
    # CLASS it saw. The defect being graded: after the side channel was pruned,
    # 'recurring=0 sources=0' read exactly like a source that never failed.
    buckets = [RUN.failure_kind(x) for x in (
        'E_FETCH TimeoutError: slow', 'E_FETCH HTTPError: 403',
        'E_FETCH URLError: <urlopen error>', 'E_FETCH gaierror: dns',
        'E_FETCH ConnectionRefusedError: x', 'E_FETCH ValueError: x', '',
        None, 'socket.timeout')]
    ok('AC-RUN13',
       buckets == ['timeout', 'http', 'urlerror', 'dns', 'refused', 'other',
                   'other', 'other', 'timeout'],
       'the class token buckets to timeout/http/urlerror/dns/refused/other')
    root19 = world(); roots.append(root19)
    h19 = RUN.failure_day_path(root19)
    f19 = RUN.failure_path(root19)
    RUN.snapshot_failure_day(root19, TODAY + 'T09:00:00+08:00')
    RUN.append_failure(f19, 'https://d.example/4', TODAY + 'T10:00:00+08:00',
                       'E_FETCH TimeoutError: one')
    RUN.append_failure(f19, 'https://d.example/5', TODAY + 'T11:00:00+08:00',
                       'E_FETCH TimeoutError: two')
    RUN.append_failure(f19, 'https://d.example/6', TODAY + 'T12:00:00+08:00',
                       'E_FETCH HTTPError: 403')
    t19 = RUN.summarize_failure_trend(h19, f19, TODAY + 'T20:00:00+08:00')
    ok('AC-RUN13', t19['evidence'] == 'side' and t19['kind'] == 'timeout'
       and t19['kind_count'] == 2,
       'a side channel on disk reads evidence=side with the modal class')
    root20 = world(); roots.append(root20)
    h20 = RUN.failure_day_path(root20)
    f20 = RUN.failure_path(root20)
    RUN.append_failure(f20, 'https://e.example/7', TODAY + 'T01:00:00+08:00',
                       'E_FETCH TimeoutError: x')
    RUN.append_failure(f20, 'https://e.example/8', TODAY + 'T02:00:00+08:00',
                       'E_FETCH HTTPError: 500')
    t20 = RUN.summarize_failure_trend(h20, f20, TODAY + 'T20:00:00+08:00')
    ok('AC-RUN13', t20['kind'] == 'http' and t20['kind_count'] == 1,
       'a tie breaks on the bucket name, so two readers cannot disagree')
    root21 = world(); roots.append(root21)
    h21 = RUN.failure_day_path(root21)
    f21 = RUN.failure_path(root21)
    for hour in range(5):
        RUN.append_failure(f21, 'https://f.example/9',
                           '2026-11-09T0%d:00:00+08:00' % hour,
                           'E_FETCH HTTPError: old')
    RUN.append_failure(f21, 'https://f.example/9', TODAY + 'T01:00:00+08:00',
                       'E_FETCH TimeoutError: today')
    t21 = RUN.summarize_failure_trend(h21, f21, TODAY + 'T20:00:00+08:00')
    ok('AC-RUN13', t21['kind'] == 'timeout' and t21['kind_count'] == 1,
       'a day outside the window never sets the modal class')
    root22 = world(); roots.append(root22)
    h22 = RUN.failure_day_path(root22)
    f22 = RUN.failure_path(root22)
    os.makedirs(os.path.dirname(h22), exist_ok=True)
    with open(h22, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(json.dumps({'day': '2026-11-18', 'on_day': 3, 'total': 3,
                             'newest_at': '2026-11-18T05:00:00+08:00',
                             'newest_error': 'E_FETCH TimeoutError: gone'},
                            sort_keys=True, separators=(',', ':')) + '\n')
    t22 = RUN.summarize_failure_trend(h22, f22, TODAY + 'T20:00:00+08:00')
    ok('AC-RUN13', t22['evidence'] == 'history' and t22['kind'] == 'timeout'
       and t22['kind_count'] == 1 and t22['sources'] == 0
       and t22['recurring'] == 0,
       'a pruned side channel is NAMED and its zero sources stay zero')
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc22 = RUN.main(['--failure-trend', '--root', root22])
    line22 = buf.getvalue().strip()
    ok('AC-RUN13', rc22 == 0 and 'evidence=history' in line22
       and 'kind=timeout:1' in line22,
       'the printed line carries the degraded label and its one sample')
    root23 = world(); roots.append(root23)
    t23 = RUN.summarize_failure_trend(RUN.failure_day_path(root23),
                                      RUN.failure_path(root23),
                                      TODAY + 'T20:00:00+08:00')
    ok('AC-RUN13', t23['evidence'] == 'none' and t23['kind'] == 'none'
       and t23['kind_count'] == 0,
       'neither face answers none instead of raising')
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc23 = RUN.main(['--failure-trend', '--root', root23])
    line23 = buf.getvalue().strip()
    ok('AC-RUN13', rc23 == 0 and 'evidence=none kind=none' in line23,
       'the CLI prints both faces on an empty world')
    root24 = world(); roots.append(root24)
    RUN.snapshot_failure_day(root24, TODAY + 'T09:00:00+08:00')
    t24 = RUN.summarize_failure_trend(RUN.failure_day_path(root24),
                                      RUN.failure_path(root24),
                                      TODAY + 'T20:00:00+08:00')
    ok('AC-RUN13', t24['evidence'] == 'history' and t24['kind'] == 'none'
       and t24['kind_count'] == 0 and t24['today'] == 0,
       'a history that exists and records nothing is evidence, not silence')

    # AC-RUN14 (R2997): the recurrence line carries WEIGHT, not just a source
    # count, and an unmeasurable recurrence is named rather than reported as 0.
    root25 = world(); roots.append(root25)
    h25 = RUN.failure_day_path(root25)
    f25 = RUN.failure_path(root25)
    RUN.snapshot_failure_day(root25, TODAY + 'T09:00:00+08:00')
    RUN.append_failure(f25, 'https://g.example/1', '2026-11-18T05:00:00+08:00',
                       'E_FETCH TimeoutError: a')
    RUN.append_failure(f25, 'https://g.example/1', TODAY + 'T01:00:00+08:00',
                       'E_FETCH TimeoutError: b')
    RUN.append_failure(f25, 'https://g.example/1', TODAY + 'T02:00:00+08:00',
                       'E_FETCH TimeoutError: c')
    RUN.append_failure(f25, 'https://h.example/2', TODAY + 'T03:00:00+08:00',
                       'E_FETCH HTTPError: 403')
    t25 = RUN.summarize_failure_trend(h25, f25, TODAY + 'T20:00:00+08:00')
    ok('AC-RUN14', t25['recur'] == (1, 3) and t25['recurring'] == 1
       and t25['sources'] == 2,
       'recur names the recurring source count AND its window failures')
    root26 = world(); roots.append(root26)
    h26 = RUN.failure_day_path(root26)
    f26 = RUN.failure_path(root26)
    for hour in range(3):
        RUN.append_failure(f26, 'https://i.example/3',
                           TODAY + 'T0%d:00:00+08:00' % hour,
                           'E_FETCH TimeoutError: x')
    t26 = RUN.summarize_failure_trend(h26, f26, TODAY + 'T20:00:00+08:00')
    ok('AC-RUN14', t26['recur'] == (0, 0) and t26['recurring'] == 0
       and t26['sources'] == 1,
       'three failures on ONE day are not a recurrence')
    root27 = world(); roots.append(root27)
    h27 = RUN.failure_day_path(root27)
    os.makedirs(os.path.dirname(h27), exist_ok=True)
    with open(h27, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(json.dumps({'day': '2026-11-18', 'on_day': 2, 'total': 2,
                             'newest_at': '2026-11-18T05:00:00+08:00',
                             'newest_error': 'E_FETCH TimeoutError: gone'},
                            sort_keys=True, separators=(',', ':')) + '\n')
    t27 = RUN.summarize_failure_trend(h27, RUN.failure_path(root27),
                                      TODAY + 'T20:00:00+08:00')
    ok('AC-RUN14', t27['recur'] is None and t27['evidence'] == 'history',
       'a pruned side channel answers recur=None, never a fabricated 0:0')
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc27 = RUN.main(['--failure-trend', '--root', root27])
    line27 = buf.getvalue().strip()
    ok('AC-RUN14', rc27 == 0 and 'recur=none' in line27,
       'the printed line spells the unmeasured recurrence as none')
    root28 = world(); roots.append(root28)
    f28 = RUN.failure_path(root28)
    RUN.append_failure(f28, 'https://j.example/4', TODAY + 'T01:00:00+08:00',
                       'E_FETCH TimeoutError: slow')
    s28 = RUN.summarize_failures(f28, TODAY + 'T20:00:00+08:00')
    ok('AC-RUN14', s28['newest_kind'] == RUN.failure_kind(s28['newest_error'])
       and s28['newest_kind'] == 'timeout',
       '--failures reads the SAME bucket function as the trend line')
    root29 = world(); roots.append(root29)
    f29 = RUN.failure_path(root29)
    RUN.append_failure(f29, 'https://k.example/5', TODAY + 'T01:00:00+08:00',
                       'E_FETCH HTTPError: old')
    RUN.append_failure(f29, 'https://k.example/5', TODAY + 'T05:00:00+08:00',
                       'E_FETCH TimeoutError: new')
    s29 = RUN.summarize_failures(f29, TODAY + 'T20:00:00+08:00')
    ok('AC-RUN14', s29['newest_kind'] == 'timeout',
       'the bucket follows the NEWEST failure, not the first one seen')
    root30 = world(); roots.append(root30)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc30a = RUN.main(['--failures', '--root', root30])
    line30a = buf.getvalue().strip()
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc30b = RUN.main(['--failure-trend', '--root', root30])
    line30b = buf.getvalue().strip()
    ok('AC-RUN14', rc30a == 0 and rc30b == 0 and 'kind=none' in line30a
       and 'recur=none' in line30b,
       'an empty world answers none on both faces without raising')

    # AC-RUN15 (R2998): the trend names how much history it actually had. A
    # trimmed file used to read exactly like a repo that had just started
    # recording; the coverage fields are the only place the difference shows.
    week = ['2026-11-13', '2026-11-14', '2026-11-15', '2026-11-16',
            '2026-11-17', '2026-11-18', TODAY]
    root31 = world(); roots.append(root31)
    h31 = RUN.failure_day_path(root31)
    os.makedirs(os.path.dirname(h31), exist_ok=True)
    with open(h31, 'w', encoding='utf-8', newline='\n') as fh:
        for day in week:
            fh.write(json.dumps({'day': day, 'on_day': 1, 'total': 1},
                                sort_keys=True,
                                separators=(',', ':')) + '\n')
    t31 = RUN.summarize_failure_trend(h31, RUN.failure_path(root31),
                                      TODAY + 'T20:00:00+08:00', 7)
    ok('AC-RUN15', t31['wcov'] == (7, 7) and t31['cov'] == (week[0], TODAY),
       'a complete seven-day history reads wcov=7/7 with its own first day')

    root32 = world(); roots.append(root32)
    h32 = RUN.failure_day_path(root32)
    os.makedirs(os.path.dirname(h32), exist_ok=True)
    with open(h32, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(json.dumps({'day': TODAY, 'on_day': 1, 'total': 1},
                            sort_keys=True, separators=(',', ':')) + '\n')
    t32 = RUN.summarize_failure_trend(h32, RUN.failure_path(root32),
                                      TODAY + 'T20:00:00+08:00', 7)
    ok('AC-RUN15', t32['wcov'] == (1, 7) and t32['days'] == 1
       and t32['today'] == 1 and t32['mean'] == 1.0,
       'a trimmed history answers wcov=1/7 while today/mean stay unchanged')

    t31b = RUN.summarize_failure_trend(h31, RUN.failure_path(root31),
                                       TODAY + 'T20:00:00+08:00', 3)
    ok('AC-RUN15', t31b['wcov'] == (3, 3),
       'a three-day window over seven rows of history reads wcov=3/3')

    root33 = world(); roots.append(root33)
    h33 = RUN.failure_day_path(root33)
    os.makedirs(os.path.dirname(h33), exist_ok=True)
    with open(h33, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write('{not json\n')
        fh.write(json.dumps({'day': TODAY, 'on_day': 0, 'total': 0},
                            sort_keys=True, separators=(',', ':')) + '\n')
    t33 = RUN.summarize_failure_trend(h33, RUN.failure_path(root33),
                                      TODAY + 'T20:00:00+08:00', 7)
    ok('AC-RUN15', t33['wcov'] == (1, 7) and t33['bad'] == 1,
       'a malformed row is not a covered day')

    root34 = world(); roots.append(root34)
    buf34 = io.StringIO()
    with contextlib.redirect_stdout(buf34):
        rc34 = RUN.main(['--failure-trend', '--root', root34])
    line34 = buf34.getvalue().strip()
    ok('AC-RUN15', rc34 == 0 and 'cov=none' in line34 and 'wcov=0/7' in line34,
       'a missing history answers cov=none wcov=0/7 without raising')

    buf35 = io.StringIO()
    with contextlib.redirect_stdout(buf35):
        rc35 = RUN.main(['--failure-trend', '--root', root31, '--days', '7'])
    line35 = buf35.getvalue().strip()
    scan_src = ''
    scan_path = os.path.join(ROOT, 'tools', 'skills', 'bigdomain-loop-scan',
                             'scripts', 'scan_five_still.ps1')
    if os.path.isfile(scan_path):
        with open(scan_path, 'r', encoding='utf-8', errors='replace') as fh:
            scan_src = fh.read()
    ok('AC-RUN15', rc35 == 0
       and ('cov=%s..%s' % (week[0], TODAY)) in line35
       and 'wcov=7/7' in line35 and 'wcov' not in scan_src
       and 'crawl-failure-days' not in scan_src,
       'the CLI carries both coverage fields and stays outside the gate face')

    # AC-RUN16 (R2999): the retention exemption argued with numbers nobody
    # could check from the product. --failures now carries the file's own BODY
    # (bytes / lines) plus a DISPLAY-ONLY percentage of the group water line.
    root36 = world(); roots.append(root36)
    f36 = RUN.failure_path(root36)
    RUN.append_failure(f36, 'https://a.example/1', TODAY + 'T01:00:00+08:00',
                       'E_FETCH TimeoutError: a')
    RUN.append_failure(f36, 'https://b.example/2', TODAY + 'T02:00:00+08:00',
                       'E_FETCH HTTPError: b')
    with open(f36, 'a', encoding='utf-8', newline='\n') as fh:
        fh.write('{broken\n')
        fh.write('\n')
    s36 = RUN.summarize_failures(f36, TODAY)
    ok('AC-RUN16', s36['bytes'] == os.path.getsize(f36) and s36['lines'] == 4
       and s36['total'] == 2 and s36['bad'] == 1,
       'bytes equal the file on disk; lines count physical rows, malformed and blank included')
    ok('AC-RUN16', s36['lines'] - (s36['total'] + s36['bad']) == 1,
       'lines minus (total+bad) is exactly the blank-row count, so the two counts are independent')

    root37 = world(); roots.append(root37)
    s37 = RUN.summarize_failures(RUN.failure_path(root37), TODAY)
    ok('AC-RUN16', s37['bytes'] == 0 and s37['lines'] == 0
       and s37['size_gate'] == 0.0 and s37['present'] is False,
       'a missing side channel answers zero bytes and zero lines without raising')
    buf37 = io.StringIO()
    with contextlib.redirect_stdout(buf37):
        rc37 = RUN.main(['--failures', '--root', root37])
    line37 = buf37.getvalue().strip()
    ok('AC-RUN16', rc37 == 0 and 'bytes=0' in line37 and 'lines=0' in line37,
       'the CLI answers rc=0 with zero size on a world that has no side channel')

    root38 = world(); roots.append(root38)
    f38 = RUN.failure_path(root38)
    os.makedirs(os.path.dirname(f38), exist_ok=True)
    target38 = RUN.SIZE_REFERENCE_BYTES // 100  # exactly one percent
    head38 = json.dumps({'source_url': 'https://p.example/1',
                         'failed_at': TODAY + 'T03:00:00+08:00',
                         'error': 'E_FETCH TimeoutError: pad'},
                        sort_keys=True, separators=(',', ':')) + '\n'
    with open(f38, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(head38)
        fh.write('x' * (target38 - len(head38) - 1) + '\n')
    s38 = RUN.summarize_failures(f38, TODAY)
    ok('AC-RUN16', s38['bytes'] == target38 and s38['size_gate'] == 1.0
       and s38['gate_ref_mb'] == 100,
       'a file padded to one hundredth of the reference line reads size_gate=1.0 against gate_ref=100MB')

    keys38 = set(s38.keys())
    buf38 = io.StringIO()
    with contextlib.redirect_stdout(buf38):
        rc38 = RUN.main(['--failures', '--root', root38])
    line38 = buf38.getvalue().strip()
    ok('AC-RUN16', rc38 == 0
       and 'bytes=' in line38 and 'lines=' in line38
       and 'size_gate=' in line38 and 'gate_ref=100MB' in line38
       and not (keys38 & set(['pass', 'flag', 'verdict', 'ok', 'gate_ok']))
       and 'PASS' not in line38 and 'FLAG' not in line38,
       'one row carries size, row count and the named denominator, and carries no verdict '
       '(a file above the reference line was NOT built this arm)')

    scan_src16 = ''
    scan_path16 = os.path.join(ROOT, 'tools', 'skills', 'bigdomain-loop-scan',
                               'scripts', 'scan_five_still.ps1')
    if os.path.isfile(scan_path16):
        with open(scan_path16, 'r', encoding='utf-8', errors='replace') as fh:
            scan_src16 = fh.read()
    census_src16 = ''
    census_path16 = os.path.join(ROOT, 'src', 'os', 'qa_writer_census.py')
    if os.path.isfile(census_path16):
        with open(census_path16, 'r', encoding='utf-8', errors='replace') as fh:
            census_src16 = fh.read()
    ok('AC-RUN16', 'crawl-failure' not in scan_src16
       and 'crawl-failure' not in census_src16
       and 'endswith(".log")' in census_src16,
       'neither the scanner nor the writer census reads either failure file')

    # AC-RUN17 (R3000): the retention exemption's OTHER half - the history file's
    # own body - finally has a face. bytes only; `lines` was measured to restate
    # days after any beat rewrite, and the >100% path is pinned as a pure
    # function instead of by building a 100MB file.
    def day_row(day, n):
        return {'day': day, 'on_day': n, 'total': n, 'recent': n, 'bad': 0,
                'urls': 1, 'newest_at': None, 'newest_error': None}

    def write_days(path, rows, junk=()):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8', newline='\n') as fh:
            for row in rows:
                fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True,
                                    separators=(',', ':')) + '\n')
            for text in junk:
                fh.write(text + '\n')

    root39 = world(); roots.append(root39)
    h39 = RUN.failure_day_path(root39)
    write_days(h39, [day_row('2026-11-17', 2), day_row('2026-11-18', 0),
                     day_row('2026-11-19', 1)], junk=['{broken', ''])
    s39 = RUN.summarize_failure_days(h39)
    ok('AC-RUN17', s39['bytes'] == os.path.getsize(h39)
       and s39['days'] == 3 and s39['bad'] == 1 and s39['present'] is True,
       'bytes equal the history file on disk while days counts only usable rows')

    root40 = world(); roots.append(root40)
    s40 = RUN.summarize_failure_days(RUN.failure_day_path(root40))
    buf40 = io.StringIO()
    with contextlib.redirect_stdout(buf40):
        rc40 = RUN.main(['--failure-days', '--root', root40])
    line40 = buf40.getvalue().strip()
    ok('AC-RUN17', rc40 == 0 and s40['bytes'] == 0 and s40['days'] == 0
       and s40['size_gate'] == 0.0 and s40['present'] is False
       and 'bytes=0' in line40,
       'a missing history answers zero bytes without raising, and the CLI prints it')

    root41 = world(); roots.append(root41)
    h41 = RUN.failure_day_path(root41)
    target41 = RUN.SIZE_REFERENCE_BYTES // 100  # exactly one percent
    head41 = json.dumps(day_row('2026-11-19', 0), sort_keys=True,
                        separators=(',', ':')) + '\n'
    write_days(h41, [day_row('2026-11-19', 0)])
    with open(h41, 'a', encoding='utf-8', newline='\n') as fh:
        fh.write('x' * (target41 - len(head41) - 1) + '\n')
    s41 = RUN.summarize_failure_days(h41)
    ok('AC-RUN17', os.path.getsize(h41) == target41
       and s41['size_gate'] == 1.0
       and s41['size_gate'] == RUN.size_gate_pct(os.path.getsize(h41)),
       'the history percentage is the same helper the side channel uses, not a second formula')

    ref42 = RUN.SIZE_REFERENCE_BYTES
    ok('AC-RUN17', RUN.size_gate_pct(2 * ref42) == 200.0
       and RUN.size_gate_pct(ref42) == 100.0
       and RUN.size_gate_pct(ref42 - 2000) < 100.0
       and RUN.size_gate_pct(ref42 // 1000) == 0.1,
       'the above-reference print path is pinned by a pure function; no 100MB file is built')

    root43 = world(); roots.append(root43)
    h43 = RUN.failure_day_path(root43)
    write_days(h43, [day_row('2026-11-13', 0), day_row('2026-11-14', 1),
                     day_row('2026-11-15', 0), day_row('2026-11-16', 0),
                     day_row('2026-11-17', 3), day_row('2026-11-18', 2),
                     day_row('2026-11-19', 1)])
    s43 = RUN.summarize_failure_days(h43, 3)
    ok('AC-RUN17', set(s43.keys()) == set(['days', 'bad', 'first', 'last',
                                           'series', 'present', 'bytes',
                                           'size_gate', 'gate_ref_mb'])
       and s43['days'] == 7 and s43['bad'] == 0
       and s43['first'] == '2026-11-13' and s43['last'] == '2026-11-19'
       and len(s43['series']) == 3
       and s43['bytes'] == os.path.getsize(h43),
       'the added fields are purely additive and bytes covers the whole file, not the printed tail')

    scan_src17 = ''
    scan_path17 = os.path.join(ROOT, 'tools', 'skills', 'bigdomain-loop-scan',
                               'scripts', 'scan_five_still.ps1')
    if os.path.isfile(scan_path17):
        with open(scan_path17, 'r', encoding='utf-8', errors='replace') as fh:
            scan_src17 = fh.read()
    buf43 = io.StringIO()
    with contextlib.redirect_stdout(buf43):
        rc43 = RUN.main(['--failure-days', '--root', root43, '--days', '7'])
    line43 = buf43.getvalue().strip()
    ok('AC-RUN17', rc43 == 0 and 'bytes=' in line43 and 'size_gate=' in line43
       and 'gate_ref=100MB' in line43 and 'lines=' not in line43
       and 'PASS' not in line43 and 'FLAG' not in line43
       and 'verdict' not in line43
       and 'crawl-failure' not in scan_src17,
       'one row carries body size and the named denominator, carries no physical line count, no verdict, and stays outside the scanner '
       '(the CRAWL-FAILURE-DAYS label itself contains FAIL, so that token is not the anchor)')

    root44 = world(); roots.append(root44)
    h44 = RUN.failure_day_path(root44)
    write_days(h44, [day_row('2026-11-18', 1)], junk=['{broken', ''])
    RUN.snapshot_failure_day(root44, TODAY)
    ok('AC-RUN17', (RUN.failure_file_stats(h44)['lines']
                    == RUN.summarize_failure_days(h44)['days']),
       'after one beat rewrite the physical line count equals days - the measured reason lines= is not printed')

    # AC-RUN18 (R3001): the trend could count failures and repeat them, but it
    # could not NAME the last source nor say whether that source was seen
    # succeeding since. Identity lives only in the side channel (the history row
    # stores urls=<count> on purpose), so a pruned side channel answers
    # UNMEASURED rather than "no page failed".
    def two_failures(root, first_url, first_at, second_url, second_at):
        fp = RUN.failure_path(root)
        RUN.append_failure(fp, first_url, first_at, 'E_FETCH TimeoutError: a')
        RUN.append_failure(fp, second_url, second_at, 'E_FETCH HTTPError: b')
        return fp

    rootA1 = world(); roots.append(rootA1)
    two_failures(rootA1, 'https://a.example/1', TODAY + 'T08:00:00+08:00',
                 'https://b.example/2', TODAY + 'T10:00:00+08:00')
    tA1 = RUN.summarize_failure_trend(RUN.failure_day_path(rootA1),
                                      RUN.failure_path(rootA1), TODAY,
                                      record_path=CR.record_path(rootA1))
    ok('AC-RUN18', tA1['newest_src'] == 'https://b.example/2'
       and tA1['since_ok'] == 'unmeasured',
       'the latest failure by time names its source; no record face means the repair question is UNMEASURED')

    rootA2 = world(); roots.append(rootA2)
    two_failures(rootA2, 'https://a.example/1', TODAY + 'T08:00:00+08:00',
                 'https://b.example/2', TODAY + 'T10:00:00+08:00')
    CR.append_record(CR.record_path(rootA2), 'https://b.example/2',
                     TODAY + 'T11:00:00+08:00', 'no-drift')
    tA2 = RUN.summarize_failure_trend(RUN.failure_day_path(rootA2),
                                      RUN.failure_path(rootA2), TODAY,
                                      record_path=CR.record_path(rootA2))
    ok('AC-RUN18', tA2['newest_src'] == 'https://b.example/2'
       and tA2['since_ok'] == 'yes',
       'a later successful row for that source reads since_ok=yes')

    rootA3 = world(); roots.append(rootA3)
    two_failures(rootA3, 'https://a.example/1', TODAY + 'T08:00:00+08:00',
                 'https://b.example/2', TODAY + 'T10:00:00+08:00')
    CR.append_record(CR.record_path(rootA3), 'https://b.example/2',
                     TODAY + 'T09:00:00+08:00', 'no-drift')
    tA3 = RUN.summarize_failure_trend(RUN.failure_day_path(rootA3),
                                      RUN.failure_path(rootA3), TODAY,
                                      record_path=CR.record_path(rootA3))
    ok('AC-RUN18', tA3['since_ok'] == 'no',
       'a success only BEFORE the last failure does not count as a repair')

    rootA4 = world(); roots.append(rootA4)
    two_failures(rootA4, 'https://a.example/1', TODAY + 'T08:00:00+08:00',
                 'https://b.example/2', TODAY + 'T10:00:00+08:00')
    tA4 = RUN.summarize_failure_trend(
        RUN.failure_day_path(rootA4), RUN.failure_path(rootA4), TODAY,
        record_path=os.path.join(rootA4, 'nope.jsonl'))
    ok('AC-RUN18', tA4['newest_src'] == 'https://b.example/2'
       and tA4['since_ok'] == 'unmeasured',
       'a missing record file answers UNMEASURED while identity still comes from the side channel')

    rootA5 = world(); roots.append(rootA5)
    write_days(RUN.failure_day_path(rootA5), [day_row('2026-11-19', 0)])
    tA5 = RUN.summarize_failure_trend(RUN.failure_day_path(rootA5),
                                      RUN.failure_path(rootA5), TODAY,
                                      record_path=CR.record_path(rootA5))
    base_keys = set(['days', 'in_window', 'bad', 'today', 'prev', 'mean',
                     'delta', 'worst', 'recurring', 'sources', 'recur', 'cov',
                     'wcov', 'evidence', 'kind', 'kind_count', 'window_days'])
    ok('AC-RUN18', tA5['newest_src'] is None and tA5['since_ok'] == 'unmeasured'
       and set(tA5.keys()) == base_keys | set(['newest_src', 'since_ok', 'flips',
                                               'rcov'])
       and tA5['evidence'] == 'history' and tA5['today'] == 0,
       'a pruned side channel answers none/unmeasured and leaves every existing field where it was')

    rootA6 = world(); roots.append(rootA6)
    fpA6 = RUN.failure_path(rootA6)
    RUN.append_failure(fpA6, 'https://b.example/2', TODAY + 'T10:00:00+08:00',
                       'E_FETCH HTTPError: new first in file')
    RUN.append_failure(fpA6, 'https://a.example/1', TODAY + 'T08:00:00+08:00',
                       'E_FETCH TimeoutError: old second in file')
    tA6 = RUN.summarize_failure_trend(RUN.failure_day_path(rootA6), fpA6, TODAY,
                                      record_path=CR.record_path(rootA6))
    ok('AC-RUN18', tA6['newest_src'] == 'https://b.example/2',
       'the latest failure is chosen by time, not by the order rows sit in the file')

    bufA7 = io.StringIO()
    with contextlib.redirect_stdout(bufA7):
        rcA7 = RUN.main(['--failure-trend', '--root', rootA2])
    lineA7 = bufA7.getvalue().strip()
    scan_src18 = ''
    scan_path18 = os.path.join(ROOT, 'tools', 'skills', 'bigdomain-loop-scan',
                               'scripts', 'scan_five_still.ps1')
    if os.path.isfile(scan_path18):
        with open(scan_path18, 'r', encoding='utf-8', errors='replace') as fh:
            scan_src18 = fh.read()
    ok('AC-RUN18', rcA7 == 0 and 'newest_src=https://b.example/2' in lineA7
       and 'since_ok=yes' in lineA7
       and 'PASS' not in lineA7 and 'FLAG' not in lineA7
       and 'verdict' not in lineA7
       and 'crawl-failure' not in scan_src18,
       'one display row carries identity and the repair reading, carries no verdict, and stays outside the scanner')

    # AC-RUN19 (R3002): "is it fixed now" and "does it stay fixed" read the same
    # on the R3001 line - measured before the code: a stable repair (fail, ok)
    # and a source fixed, broken and fixed again (fail, ok, fail, ok) BOTH print
    # since_ok=yes with recur=(0,0). flips= counts success -> failure transitions
    # for the newest source on the merged timeline of the two faces already on
    # disk; it is display-only and unmeasured wherever since_ok is.
    def flips_world(fail_times, ok_times):
        root = world()
        roots.append(root)
        for when in fail_times:
            RUN.append_failure(RUN.failure_path(root), SRC19, TODAY + 'T' + when,
                               'E_FETCH TimeoutError: x')
        for when in ok_times:
            CR.append_record(CR.record_path(root), SRC19, TODAY + 'T' + when,
                             'no-drift')
        return root, RUN.summarize_failure_trend(
            RUN.failure_day_path(root), RUN.failure_path(root), TODAY,
            record_path=CR.record_path(root))

    SRC19 = 'https://pay.weixin.qq.com/doc/v2/merchant/4011986682'

    _rB1, tB1 = flips_world(['08:00:00+08:00'], ['09:00:00+08:00'])
    ok('AC-RUN19', tB1['flips'] == 0 and tB1['since_ok'] == 'yes',
       'a stable repair (fail, ok) answers flips=0, never read as flapping')

    _rB2, tB2 = flips_world(['08:00:00+08:00', '10:00:00+08:00'],
                            ['09:00:00+08:00', '11:00:00+08:00'])
    ok('AC-RUN19', tB2['flips'] == 1 and tB2['since_ok'] == 'yes',
       'fixed, broken again and fixed again reads since_ok=yes AND flips=1 - the pair this round separates')

    _rB3, tB3 = flips_world(['08:00:00+08:00', '08:30:00+08:00'],
                            ['09:00:00+08:00'])
    ok('AC-RUN19', tB3['flips'] == 0 and tB3['since_ok'] == 'yes',
       'two failures before the first success never worked in between, so no flip is invented')

    _rB4, tB4 = flips_world(['08:00:00+08:00', '09:00:00+08:00'],
                            ['08:30:00+08:00'])
    ok('AC-RUN19', tB4['flips'] == 1 and tB4['recur'] == (0, 0)
       and tB4['recurring'] == 0,
       'same-day flapping is one flip while recur stays 0:0 - two different questions')

    _rB5, _t = flips_world(['08:00:00+08:00'], [])
    CR.append_record(CR.record_path(_rB5),
                     'https://other.example/page',
                     TODAY + 'T09:00:00+08:00', 'no-drift')
    tB5 = RUN.summarize_failure_trend(
        RUN.failure_day_path(_rB5), RUN.failure_path(_rB5), TODAY,
        record_path=CR.record_path(_rB5))
    ok('AC-RUN19', tB5['flips'] == 0 and tB5['since_ok'] == 'no'
       and os.path.isfile(CR.record_path(_rB5)),
       'a record file that holds no row for the source answers 0, measured rather than missing')

    _rB6, tB6 = flips_world(['08:00:00+08:00', '10:00:00+08:00'], [])
    tB6b = RUN.summarize_failure_trend(
        RUN.failure_day_path(_rB6), RUN.failure_path(_rB6), TODAY,
        record_path=os.path.join(_rB6, 'nope.jsonl'))
    sideB6 = RUN.summarize_failure_trend(
        RUN.failure_day_path(_rB6), os.path.join(_rB6, 'no-side.jsonl'), TODAY,
        record_path=CR.record_path(_rB6))
    ok('AC-RUN19', tB6b['flips'] is None and tB6b['since_ok'] == 'unmeasured'
       and sideB6['flips'] is None and sideB6['since_ok'] == 'unmeasured',
       'a missing record file and a pruned side channel both answer UNMEASURED, never 0')

    _rB7, tB7 = flips_world(['10:00:00+08:00'], ['10:00:00+08:00'])
    ok('AC-RUN19', tB7['flips'] == 0 and tB7['since_ok'] == 'no',
       'a success and a failure on the same second are never ordered into an invented flip')

    _rB8, tB8 = flips_world(['08:00:00+08:00', '10:00:00+08:00'],
                            ['09:00:00+08:00'])
    ok('AC-RUN19', tB8['flips'] == 1 and tB8['newest_src'] == SRC19
       and tB8['since_ok'] == 'no',
       'the newest failure is taken by time, so the flip before it still counts')

    baseB = set(['days', 'in_window', 'bad', 'today', 'prev', 'mean', 'delta',
                 'worst', 'recurring', 'sources', 'recur', 'cov', 'wcov',
                 'evidence', 'kind', 'kind_count', 'newest_src', 'since_ok',
                 'window_days'])
    bufB9 = io.StringIO()
    with contextlib.redirect_stdout(bufB9):
        rcB9 = RUN.main(['--failure-trend', '--root', _rB2])
    lineB9 = bufB9.getvalue().strip()
    ok('AC-RUN19', rcB9 == 0 and 'flips=1' in lineB9
       and 'since_ok=yes' in lineB9 and 'PASS' not in lineB9
       and 'FLAG' not in lineB9 and 'verdict' not in lineB9
       and 'crawl-failure' not in scan_src18
       and set(tB2.keys()) == baseB | set(['flips', 'rcov']),
       'one display row carries the stability count, adds exactly one key, and stays outside the scanner')

    # AC-RUN20 (R3003): the trend answered "was it seen working afterwards" but
    # never "how far did the record it read actually reach" - measured before
    # this existed: a record stopping BEFORE the failure and one covering the
    # days after (through another source) printed the SAME row. rcov= names the
    # span; the verdict itself is deliberately left where it was.
    def rcov_world(record_rows, failure_rows, history_rows):
        root = world()
        roots.append(root)
        for row in record_rows:
            CR.append_record(CR.record_path(root), row[0], row[1], row[2])
        for row in failure_rows:
            RUN.append_failure(RUN.failure_path(root), row[0], row[1], row[2])
        write_days(RUN.failure_day_path(root), history_rows)
        return root, RUN.summarize_failure_trend(
            RUN.failure_day_path(root), RUN.failure_path(root), TODAY,
            record_path=CR.record_path(root))

    SRC20 = 'https://pay.weixin.qq.com/doc/v2/merchant/4011986682'
    OTHER20 = 'https://other.example/page'
    FAILED20 = '2026-11-18T09:00:00+08:00'

    # arm 1: a record covering the days after the failure
    _rC1, tC1 = rcov_world(
        [(SRC20, '2026-11-18T08:00:00+08:00', 'no-drift'),
         (OTHER20, '2026-11-19T10:00:00+08:00', 'no-drift')],
        [(SRC20, FAILED20, 'E_FETCH TimeoutError: x')],
        [day_row('2026-11-18', 1)])
    ok('AC-RUN20', tC1['rcov'] == ('2026-11-18', '2026-11-19'),
       'the span names both days the record actually reaches, sorted by day')

    # arm 2: the record STOPS before the failure - the span shows it, and the
    # verdict is pinned as unchanged so a silent re-judge cannot pass
    _rC2, tC2 = rcov_world(
        [(SRC20, '2026-11-17T10:00:00+08:00', 'no-drift')],
        [(SRC20, FAILED20, 'E_FETCH TimeoutError: x')],
        [day_row('2026-11-18', 1)])
    ok('AC-RUN20', tC2['rcov'] == ('2026-11-17', '2026-11-17')
       and tC2['since_ok'] == 'no',
       'a record ending before the failure shows a span that stops there, while the verdict is left as shipped')

    # arm 3: no record file at all
    _rC3, tC3 = rcov_world(
        [],
        [(SRC20, FAILED20, 'E_FETCH TimeoutError: x')],
        [day_row('2026-11-18', 1)])
    ok('AC-RUN20', tC3['rcov'] is None and tC3['since_ok'] == 'unmeasured',
       'no record file answers none - a span from no rows would be invented')

    # arm 4: a zero-byte record file is present and still answers none
    _rC4, _tC4 = rcov_world([], [], [day_row('2026-11-18', 1)])
    open(CR.record_path(_rC4), 'w').close()
    tC4 = RUN.summarize_failure_trend(
        RUN.failure_day_path(_rC4), RUN.failure_path(_rC4), TODAY,
        record_path=CR.record_path(_rC4))
    ok('AC-RUN20', tC4['rcov'] is None and os.path.isfile(CR.record_path(_rC4))
       and os.path.getsize(CR.record_path(_rC4)) == 0,
       'a present but empty record answers none - coverage is measured, not assumed from existence')

    # arm 5: malformed rows neither widen nor invent a span
    _rC5, _tC5 = rcov_world(
        [(SRC20, '2026-11-18T08:00:00+08:00', 'no-drift'),
         (OTHER20, '2026-11-19T10:00:00+08:00', 'no-drift')],
        [], [day_row('2026-11-18', 0)])
    with open(CR.record_path(_rC5), 'a', encoding='utf-8', newline='\n') as fh:
        fh.write('{"fetched_at":"2027-01-01T00:00:00+08:00",\n')
    tC5 = RUN.summarize_failure_trend(
        RUN.failure_day_path(_rC5), RUN.failure_path(_rC5), TODAY,
        record_path=CR.record_path(_rC5))
    _rC5b, _tC5b = rcov_world([], [], [day_row('2026-11-18', 0)])
    with open(CR.record_path(_rC5b), 'w', encoding='utf-8',
              newline='\n') as fh:
        fh.write('not json at all\n')
    tC5b = RUN.summarize_failure_trend(
        RUN.failure_day_path(_rC5b), RUN.failure_path(_rC5b), TODAY,
        record_path=CR.record_path(_rC5b))
    ok('AC-RUN20', tC5['rcov'] == ('2026-11-18', '2026-11-19')
       and tC5b['rcov'] is None,
       'a broken line cannot stretch the span, and a file of nothing but broken lines has no span')

    # arm 6: cov (history face) and rcov (record face) answer from different
    # files in the same world - neither reading may explain the other
    _rC6, tC6 = rcov_world(
        [(SRC20, '2026-11-19T10:00:00+08:00', 'no-drift')],
        [], [day_row('2026-11-13', 0), day_row('2026-11-19', 0)])
    ok('AC-RUN20', tC6['cov'] == ('2026-11-13', '2026-11-19')
       and tC6['rcov'] == ('2026-11-19', '2026-11-19'),
       'the history spans six days while the record spans one - two faces, two answers')

    # arm 7: one CLI row carries rcov=, adds exactly one key, stays outside the
    # scanner; a missing record prints none rather than dropping the field
    bufC7 = io.StringIO()
    with contextlib.redirect_stdout(bufC7):
        rcC7 = RUN.main(['--failure-trend', '--root', _rC1])
    lineC7 = bufC7.getvalue().strip()
    bufC8 = io.StringIO()
    with contextlib.redirect_stdout(bufC8):
        rcC8 = RUN.main(['--failure-trend', '--root', _rC3])
    lineC8 = bufC8.getvalue().strip()
    ok('AC-RUN20', rcC7 == 0 and 'rcov=2026-11-18..2026-11-19' in lineC7
       and rcC8 == 0 and 'rcov=none' in lineC8
       and 'PASS' not in lineC7 and 'FLAG' not in lineC7
       and 'verdict' not in lineC7
       and 'crawl-failure' not in scan_src18
       and set(tC1.keys()) == baseB | set(['flips', 'rcov']),
       'the row names the record span, or none, and adds exactly the one key it names')

    for root in roots:
        shutil.rmtree(root, ignore_errors=True)

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
        print('FAILED: ' + ', '.join(FAILS))
        print('SUITE FAIL %d/%d' % (total - len(FAILS), total))
        return 1
    print('SUITE PASS %d/%d' % (total, total))
    return 0


if __name__ == '__main__':
    sys.exit(main())
