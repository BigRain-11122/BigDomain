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
