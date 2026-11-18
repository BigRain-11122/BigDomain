"""Battery suite for tools/crawl_runner.py (R2991).

WHY: R2990 landed the record face, and nothing ever wrote a record except the
suite grading the writer - the daily-crawl limb stayed an honest red that no
executor could fill. crawl_runner is that executor, and this suite grades the
two things a crawl executor can be wrong about: the JUDGEMENT (is this page the
same page?) and the DECLARATION (does a failure never look like a crawl?).

PINNED BEFORE THE CODE: AC-RUN1..AC-RUN4 were written into src/os/backlog.md in
this same window, BEFORE crawl_runner.py existed (in-window pre-registration,
disclosed as such).

Scope, stated honestly: no arm here fetches a real page except the one failure
arm against loopback, which is meant to fail. The judgement is graded on saved
fixtures, so this suite never depends on a network being up and never writes
into qa/ - every record lands in a per-run temp directory.

Stdlib only, ASCII source, no clock of its own (fetched_at is passed in).
"""
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
