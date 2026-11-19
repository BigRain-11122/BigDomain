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
looked afterwards. It also pins that cov= (history face) and rcov= (record face)
are read from different files in the same world, and that malformed rows can
neither widen nor invent a span.
AC-RUN21 (R3004) grades the VERDICT SPLIT: since_ok may say 'no' only when the
record is shown to reach strictly past the failure stamp, so a zero-byte file, a
file whose newest row predates the failure, a file of only malformed rows and a
success stamped in the same second all answer 'unmeasured' - "we never looked"
is not "we looked and it is still broken". It also pins the deliberate split
from flips: a flip is a pair of events already on disk, so since_ok=unmeasured
may sit beside flips=1 without either field lying. AC-RUN20's pre-failure arm
was rewritten to the new verdict on purpose - the contract moved, and an arm
that keeps the old reading would hide it.
AC-RUN22 (R3005) grades WINDOW BREADTH: newest_src/since_ok answer for the one
source that failed last, so three failing pages left two of them without a
verdict. pending=<no>/<judged> counts, over the whole window and each source's
own latest failure, the sources shown looked-at and never back over the sources
that could be judged at all - an unmeasured source is in neither number, because
a since_ok != 'yes' numerator was measured to count a source nobody ever looked
after as pending. It also pins that recur= and pending= answer different
questions in both directions, and that a multi-source window still prints one
line (per-source lines were refused, not forgotten).
AC-RUN23 (R3006) grades NAMING ONE: pending= answered how many sources were
still gone and never which one, so a person still guessed where to start. The
row now carries pending_src=, the pending source waiting longest (its own latest
failure stamp smallest, ties by url ascending), none when nothing is pending. An
unjudged=<n> field was refused on measurement - it always equals sources minus
the pending denominator (0, 1 and 2 in three probe worlds), so it would only
restate two keys already on the line - and the earlier premise that
pending=none and "all came back" read the same was measured false ('none' versus
'0/2'). An unmeasured source is never named.
AC-RUN24 (R3007) grades HOW LONG: the name said where to start, never how long
the wait had been, so a source gone five minutes and one gone a week read the
same. The row now carries pending_age_d=, whole days from the NAMED source's own
latest failure to the window day, taken on the record writer's ten-character day
prefix and no clock of its own. It is deliberately not the failure summary's
newest_at, which is measured across ALL sources (the probe world had it naming a
different source's stamp than pending_src). It reads None - never 0 - when
nothing is named, a date is unusable, or the stamp is later than the reference
day. The other pending sources remain counts: their number is the numerator
minus one (refused as arithmetic) and their names need one line per source
(refused). Six existing key-set arms were widened by this one key, disclosed as
criteria moving with the field rather than being relaxed.
AC-RUN25 (R3008) grades the OTHER END: one age described the source waiting
longest and said nothing about the rest, so with several pending sources a burst
that just started read exactly like a long tail (measured: three pending sources
aged 0/2/4 days read pending_age_d=4 with the 0-day one absent from all 24
keys). The row now also carries pending_age_min_d=, whole days from the NEWEST
pending source's own latest failure to the window day - the same ten-character
day prefix and the same None rules as pending_age_d. Together the two are the
AGE SPAN of the pending set. A pending_age_max_d field was measured and refused:
the named source is by construction the oldest, so a max would restate
pending_age_d. With one pending source, or several sharing one stamp, the two
ages coincide - pinned as a fact so it is never silently 'fixed' into a None.
Seven existing key-set arms were widened by this key (the six above plus
AC-RUN24's own), disclosed as criteria moving with the field.
AC-RUN26 (R3009) grades the MIDDLE: two ends described the span and left
everything between them silent, so "a burst that just started" and "an old tail
with one new arrival" printed the same row (measured: ages 5/3/0 and 5/1/0 were
identical on all 25 keys, and so were 5/5/5/0/0 and 5/0/0/0/0). The row now also
carries pending_age_med_d=, the middle element of the pending set sorted by age,
taking the one nearer the OLD end when the count is even. This is not the max
refused in R3008 - a max equalled pending_age_d by construction in every world,
while the middle coincides with an end only at N<=2 or when the mass piles on
one end, which is the reading it adds. Pointing the reader at the failure-day
file was measured and refused as an alternative (that file carries a urls=
COUNT and no per-source identity or age). Eight existing key-set arms were
widened by this key (the seven above plus AC-RUN25's own), disclosed as criteria
moving with the field.
AC-RUN27 (R3010) grades the OUTSIDE of the window: the window decides who is
counted, so a source whose own latest failure fell before the window start left
every key - measured, a still-broken old source and a repaired one differed only
through rcov, and a side channel trimmed to the window read identical to a
healthy world on all 26 keys. The row now also carries pending_old=<n>/<judged>
over sources whose own latest failure is strictly before the window start: a
third count with its own denominator, so pending= keeps meaning what sources=
names (rewriting pending= to count both was measured and refused - it would
report more judged sources than that population contains). judged==0 answers
None, never 0/0: a trimmed side channel, an empty outside face and a record that
stops before the old failure all mean "nothing was looked at out there". Nine
existing key-set arms were widened by this key (the eight above plus AC-RUN26's
own), disclosed as criteria moving with the field.
AC-RUN28 (R3011) grades the COVERAGE OF THE SIDE CHANNEL: pending_old= counts
over the failure side channel but never said how far back that channel reaches -
measured, two worlds whose channels reached one day and ninety-one days were
identical on all 27 keys (the extra row was an earlier failure of the SAME
source, so every judged fact matched). The row now also carries
fcov=<first>..<last>, the channel's own first and last usable failure day, on
the same day law as cov= and rcov= and following the FILE rather than the window
(measured: same span at 7 and 14 days while pending_old= changed). Every
coverage reading now names its own file: cov= the failure-day history, wcov=
that history's fill inside the window, rcov= the crawl record (success
evidence), fcov= the failure side channel pending_old= judges on. Absent, empty
and all-unusable channels read none, never an empty string; malformed rows never
widen the span. Ten existing key-set arms were widened by this key (the nine
above plus AC-RUN27's own), disclosed as criteria moving with the field.
AC-RUN29 (R3012) grades the AGE OF THE OLD WAITERS: pending_old= names a
fraction but never how long the sources behind it have been gone - measured,
fcov.first= is the oldest failure in the FILE and can belong to a source that
was repaired (probe world: fcov 2026-08-20..2026-11-10 where the failure still
unrepaired was 2026-11-10). The row now also carries pending_old_age_d=<days>,
the still-pending out-of-window source that waited longest, on the same day law
and None rules as the three in-window ages. None when nothing outside was
judged AND none when every judged old source came back - never 0, because a
clean outside population and a waiter aged zero must not print the same digit.
What R3010 refused stays refused (per-source naming, one line per source). Eleven
existing key-set arms were widened by this key (the ten above plus AC-RUN28's
own), disclosed as criteria moving with the field.
AC-RUN30 (R3013) grades the OTHER END OF THE OLD TAIL: one age described only the
longest old wait, so with two old waiters the other was invisible - measured, a
second waiter that failed 90 days ago and one that failed 9 days ago read
IDENTICAL on all 29 keys, including the same file span. The row now also carries
pending_old_age_min_d=<days>, the YOUNGEST still-pending out-of-window source, on
the same day law and the same None rules as the age beside it. A MIDDLE reading
was measured and refused: with two waiters - the count the board itself named -
the middle nearer the old end restates the longest age in both worlds, and at
three or more reading the shape needs one line per source, which the contract
refuses. Pointing a reader at the failure file was refused by measurement too:
with the file byte-identical, one extra record row moved the old fraction from
2/3 to 1/3. With one old waiter the two ages coincide, pinned as a truth rather
than turned into none. Eleven existing key-set arms were widened by this key
(the eleven above, each at its baseB set), disclosed as criteria moving with the
field.

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
    ok('AC-RUN18', tA3['since_ok'] == 'unmeasured'
       and tA3['rcov'] == (TODAY, TODAY),
       'a success only BEFORE the last failure is not a repair - and R3004 makes it UNMEASURED rather than "no", because the record never looked after that failure')

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
                                               'pending', 'pending_src',
                                               'pending_age_d',
                                               'pending_age_min_d', 'pending_age_med_d', 'pending_old', 'pending_old_age_d', 'pending_old_age_min_d', 'fcov', 'rcov'])
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
    ok('AC-RUN19', tB7['flips'] == 0 and tB7['since_ok'] == 'unmeasured',
       'a success and a failure on the same second are never ordered into an invented flip, and R3004 refuses to call the same second "looking afterwards" (unmeasured)')

    _rB8, tB8 = flips_world(['08:00:00+08:00', '10:00:00+08:00'],
                            ['09:00:00+08:00'])
    ok('AC-RUN19', tB8['flips'] == 1 and tB8['newest_src'] == SRC19
       and tB8['since_ok'] == 'unmeasured',
       'the newest failure is taken by time, so the flip before it still counts - and R3004 lets flips stay measured while the now-question is unmeasured')

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
       and set(tB2.keys()) == baseB | set(['flips', 'pending', 'pending_src',
                                           'pending_age_d',
                                           'pending_age_min_d', 'pending_age_med_d', 'pending_old', 'pending_old_age_d', 'pending_old_age_min_d', 'fcov', 'rcov']),
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

    # arm 2: the record STOPS before the failure - the span shows it, and R3004
    # makes the verdict unmeasured instead of claiming the source is still broken
    _rC2, tC2 = rcov_world(
        [(SRC20, '2026-11-17T10:00:00+08:00', 'no-drift')],
        [(SRC20, FAILED20, 'E_FETCH TimeoutError: x')],
        [day_row('2026-11-18', 1)])
    ok('AC-RUN20', tC2['rcov'] == ('2026-11-17', '2026-11-17')
       and tC2['since_ok'] == 'unmeasured',
       'a record ending before the failure shows a span that stops there, and since R3004 the verdict is unmeasured rather than a claim')

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
       and set(tC1.keys()) == baseB | set(['flips', 'pending', 'pending_src',
                                           'pending_age_d',
                                           'pending_age_min_d', 'pending_age_med_d', 'pending_old', 'pending_old_age_d', 'pending_old_age_min_d', 'fcov', 'rcov']),
       'the row names the record span, or none, and adds exactly the one key it names')

    # AC-RUN21 (R3004): the verdict answered 'no' without ever having looked.
    # Measured before the code: a zero-byte record, a record whose newest row
    # predates the failure and a success in the SAME second all answered 'no',
    # so "we looked and it is still broken" and "we never looked" were one word.
    # The law now: 'no' requires the record to reach STRICTLY past the failure
    # stamp, through ANY source, because the pipeline fetching another page
    # afterwards is what proves the pipeline ran.
    SRC21 = 'https://pay.weixin.qq.com/doc/v2/merchant/4011986682'
    OTHER21 = 'https://other.example/page'

    def trend21(record_rows, failure_rows, empty_record=False, junk=None):
        root = world()
        roots.append(root)
        for url, when, verdict in record_rows:
            CR.append_record(CR.record_path(root), url, when, verdict)
        for url, when, err in failure_rows:
            RUN.append_failure(RUN.failure_path(root), url, when, err)
        write_days(RUN.failure_day_path(root), [])
        if empty_record:
            open(CR.record_path(root), 'w').close()
        if junk is not None:
            with open(CR.record_path(root), 'w', encoding='utf-8',
                      newline='\n') as fh:
                fh.write(junk + '\n')
        return root, RUN.summarize_failure_trend(
            RUN.failure_day_path(root), RUN.failure_path(root), TODAY,
            record_path=CR.record_path(root))

    FAIL10 = [(SRC21, TODAY + 'T10:00:00+08:00', 'E_FETCH TimeoutError: x')]

    _rD1, tD1 = trend21([], FAIL10, empty_record=True)
    ok('AC-RUN21', tD1['since_ok'] == 'unmeasured' and tD1['rcov'] is None
       and tD1['flips'] == 0 and os.path.getsize(CR.record_path(_rD1)) == 0,
       'a zero-byte record cannot answer "still broken": zero observations read unmeasured, and flips=0 stays a count rather than a verdict')

    _rD2, tD2 = trend21([(SRC21, TODAY + 'T08:00:00+08:00', 'no-drift')], FAIL10)
    ok('AC-RUN21', tD2['since_ok'] == 'unmeasured' and tD2['flips'] == 1
       and tD2['rcov'] == (TODAY, TODAY),
       'a record stopping before the failure answers unmeasured while flips stays measured - one flip was already on disk')

    _rD3, tD3 = trend21([(OTHER21, TODAY + 'T11:00:00+08:00', 'no-drift')],
                        FAIL10)
    ok('AC-RUN21', tD3['since_ok'] == 'no',
       'a record that fetched ANOTHER page after the failure proves the pipeline looked, so the source not coming back is finally a real "no"')

    _rD4, tD4 = trend21([(SRC21, TODAY + 'T10:00:00+08:00', 'no-drift')], FAIL10)
    ok('AC-RUN21', tD4['since_ok'] == 'unmeasured',
       'a success in the same second as the failure is not "looking afterwards" - unmeasured rather than an invented order')

    _rD5, tD5 = trend21([], FAIL10, junk='not json at all')
    ok('AC-RUN21', tD5['since_ok'] == 'unmeasured',
       'a record of nothing but malformed rows has zero usable observations, so it cannot claim the source is broken')

    # the split is a property of coverage, not of the outcome: the same world
    # gains ONE row for another source and the verdict moves unmeasured -> no
    _rD6, tD6 = trend21(
        [(SRC21, TODAY + 'T08:00:00+08:00', 'no-drift'),
         (OTHER21, TODAY + 'T11:00:00+08:00', 'no-drift')], FAIL10)
    ok('AC-RUN21', tD6['since_ok'] == 'no' and tD2['since_ok'] == 'unmeasured',
       'one extra row for another source moves the same source from unmeasured to no - measurability comes from the pipeline, not from luck')

    _rD7, tD7 = trend21([(SRC21, TODAY + 'T11:00:00+08:00', 'no-drift')], FAIL10)
    bufD7 = io.StringIO()
    with contextlib.redirect_stdout(bufD7):
        rcD7 = RUN.main(['--failure-trend', '--root', _rD3])
    lineD7 = bufD7.getvalue().strip()
    ok('AC-RUN21', tD7['since_ok'] == 'yes' and rcD7 == 0
       and 'since_ok=no' in lineD7 and 'flips=' in lineD7
       and 'rcov=' in lineD7 and 'PASS' not in lineD7
       and 'FLAG' not in lineD7 and 'verdict' not in lineD7
       and 'crawl-failure' not in scan_src18
       and set(tD3.keys()) == baseB | set(['flips', 'pending', 'pending_src',
                                           'pending_age_d',
                                           'pending_age_min_d', 'pending_age_med_d', 'pending_old', 'pending_old_age_d', 'pending_old_age_min_d', 'fcov', 'rcov']),
       'a real repair still reads yes, the CLI carries all three readings, and R3004 adds NO key - the row shape is unchanged')

    # AC-RUN22 (R3005): newest_src/since_ok answer for ONE source - the latest
    # failure in the window - so with three failing pages the other two were
    # counts without a verdict (measured: A repaired, B and C gone, the row
    # named only C). pending=<no>/<judged> answers for the whole window; it
    # counts only sources the record shows were looked at and never came back,
    # over only those that could be judged at all. Printing one line per source
    # was refused: the one-line contract is what the CLI and its arms rest on.
    SRC22A = 'https://a.example/page'
    SRC22B = 'https://b.example/page'
    SRC22C = 'https://c.example/page'
    OTHER22 = 'https://other.example/page'

    def trend22(record_rows, failure_rows):
        root = world()
        roots.append(root)
        for url, when in record_rows:
            CR.append_record(CR.record_path(root), url, when, 'no-drift')
        for url, when, err in failure_rows:
            RUN.append_failure(RUN.failure_path(root), url, when, err)
        write_days(RUN.failure_day_path(root), [])
        return root, RUN.summarize_failure_trend(
            RUN.failure_day_path(root), RUN.failure_path(root), TODAY,
            record_path=CR.record_path(root))

    # arm 1: three sources, three different repair states
    rE1, tE1 = trend22(
        [(SRC22A, TODAY + 'T09:30:00+08:00'),
         (OTHER22, TODAY + 'T11:30:00+08:00')],
        [(SRC22A, TODAY + 'T09:00:00+08:00', 'E_FETCH TimeoutError: a'),
         (SRC22B, TODAY + 'T10:00:00+08:00', 'E_FETCH HTTPError: b'),
         (SRC22C, TODAY + 'T11:00:00+08:00', 'E_FETCH URLError: c')])
    ok('AC-RUN22', tE1['pending'] == (2, 3) and tE1['newest_src'] == SRC22C
       and tE1['since_ok'] == 'no' and tE1['sources'] == 3,
       'three failing sources: pending counts the two shown looked-at and never back over the three judged, while newest_src still answers for one')

    # arm 2: an UNMEASURED source is in neither number - the not-yes rule is
    # measured to be wrong here, not argued about
    rE2, tE2 = trend22(
        [(SRC22A, TODAY + 'T10:00:00+08:00')],
        [(SRC22A, TODAY + 'T09:00:00+08:00', 'E_FETCH TimeoutError: a'),
         (SRC22B, TODAY + 'T12:00:00+08:00', 'E_FETCH HTTPError: b')])
    notyes22 = [RUN._since_ok(CR.record_path(rE2), s, w) for s, w in
                ((SRC22A, TODAY + 'T09:00:00+08:00'),
                 (SRC22B, TODAY + 'T12:00:00+08:00'))]
    notyes22 = sum(1 for v in notyes22 if v != 'yes')
    ok('AC-RUN22', tE2['pending'] == (0, 1) and notyes22 == 1,
       'a source whose newest failure is later than every record row is UNMEASURED, so it is neither pending nor judged - the since_ok != yes numerator would have counted it as 1 pending here')

    # arm 3: recur and pending answer different questions (direction one)
    rE3, tE3 = trend22(
        [(OTHER22, TODAY + 'T11:00:00+08:00')],
        [(SRC22A, TODAY + 'T09:00:00+08:00', 'E_FETCH TimeoutError: a')])
    ok('AC-RUN22', tE3['recur'] == (0, 0) and tE3['pending'] == (1, 1),
       'one source failing on one day is no recurrence (recur=(0,0)) yet it is one judged source that never came back - two readings, two answers')

    # arm 4: and the other direction - recurrence without anything pending
    rE4, tE4 = trend22(
        [(SRC22A, TODAY + 'T09:30:00+08:00'),
         (SRC22B, TODAY + 'T10:30:00+08:00'),
         (OTHER22, TODAY + 'T11:00:00+08:00')],
        [(SRC22A, '2026-11-18T09:00:00+08:00', 'E_FETCH TimeoutError: a'),
         (SRC22A, TODAY + 'T09:00:00+08:00', 'E_FETCH TimeoutError: a'),
         (SRC22B, '2026-11-18T10:00:00+08:00', 'E_FETCH HTTPError: b'),
         (SRC22B, TODAY + 'T10:00:00+08:00', 'E_FETCH HTTPError: b')])
    ok('AC-RUN22', tE4['recur'] == (2, 4) and tE4['pending'] == (0, 2),
       'two sources failing on two days each is recur=(2,4), and with both seen working again nothing is pending - recurrence is not repair')

    # arm 5: each source is judged on its OWN latest failure, so a repair
    # before today failure cannot be reported as today repair
    rE5, tE5 = trend22(
        [(SRC22A, '2026-11-18T12:00:00+08:00')],
        [(SRC22A, '2026-11-18T09:00:00+08:00', 'E_FETCH TimeoutError: a'),
         (SRC22A, TODAY + 'T09:00:00+08:00', 'E_FETCH TimeoutError: a')])
    ok('AC-RUN22', tE5['pending'] is None
       and tE5['rcov'] == ('2026-11-18', '2026-11-18'),
       'judging yesterday recovery as today answer would invent a repair: the record stops before the newest failure, so nothing is judged and pending=none')

    # arm 6: no judgement anywhere reads none, never 0/0
    rE6, tE6 = trend22([], [(SRC22A, TODAY + 'T09:00:00+08:00',
                             'E_FETCH TimeoutError: a')])
    junk_root = world()
    roots.append(junk_root)
    RUN.append_failure(RUN.failure_path(junk_root),
                       SRC22A, TODAY + 'T09:00:00+08:00',
                       'E_FETCH TimeoutError: a')
    write_days(RUN.failure_day_path(junk_root), [])
    with open(CR.record_path(junk_root), 'w', encoding='utf-8',
              newline='\n') as fh:
        fh.write('not json at all\n')
    tE6b = RUN.summarize_failure_trend(
        RUN.failure_day_path(junk_root), RUN.failure_path(junk_root), TODAY,
        record_path=CR.record_path(junk_root))
    empty_root = world()
    roots.append(empty_root)
    tE6s = RUN.summarize_failure_trend(
        RUN.failure_day_path(empty_root), RUN.failure_path(empty_root), TODAY,
        record_path=CR.record_path(empty_root))
    ok('AC-RUN22', tE6['pending'] is None and tE6b['pending'] is None
       and tE6s['pending'] is None and tE6s['evidence'] == 'none',
       'an absent record, a record of nothing but malformed rows and a pruned side channel all answer none - a zero-of-zero would read like "nothing is pending"')

    # arm 7: the one-line contract, the exact key set, and the scanner
    bufE7 = io.StringIO()
    with contextlib.redirect_stdout(bufE7):
        rcE7 = RUN.main(['--failure-trend', '--root', rE1])
    linesE7 = [n for n in bufE7.getvalue().splitlines() if n.strip()]
    lineE7 = linesE7[0] if linesE7 else ''
    ok('AC-RUN22', rcE7 == 0 and len(linesE7) == 1
       and 'pending=2/3' in lineE7
       and 'PASS' not in lineE7 and 'FLAG' not in lineE7
       and 'verdict' not in lineE7 and 'crawl-failure' not in scan_src18
       and set(tE1.keys()) == baseB | set(['flips', 'pending', 'pending_src',
                                           'pending_age_d',
                                           'pending_age_min_d', 'pending_age_med_d', 'pending_old', 'pending_old_age_d', 'pending_old_age_min_d', 'fcov', 'rcov']),
       'a multi-source window still prints ONE line carrying pending=, adds exactly one key, and stays outside the scanner - per-source lines were refused on purpose')

    # AC-RUN23 (R3006): pending=<n>/<judged> answers HOW MANY sources are still
    # gone and never WHICH one, so a person had to guess where to start. Two
    # candidate fixes were measured before the code: an unjudged=<n> field is
    # pure arithmetic (it always equals sources minus the pending denominator -
    # measured reading 0, 1 and 2 in three worlds), and the claim that
    # pending=none and "all came back" read the same was measured FALSE
    # ('none' versus '0/2'). What landed is one NAME: the pending source waiting
    # longest, ties by url ascending, none when nothing is pending. An
    # unmeasured source is never named.
    SRC23A = 'https://a.example/page'
    SRC23B = 'https://b.example/page'
    SRC23C = 'https://c.example/page'
    OTHER23 = 'https://other.example/page'

    def trend23(record_rows, failure_rows_batches):
        root = world()
        roots.append(root)
        for url, when in record_rows:
            CR.append_record(CR.record_path(root), url, when, 'no-drift')
        for batch in failure_rows_batches:
            for url, when, err in batch:
                RUN.append_failure(RUN.failure_path(root), url, when, err)
        write_days(RUN.failure_day_path(root), [])
        return root, RUN.summarize_failure_trend(
            RUN.failure_day_path(root), RUN.failure_path(root), TODAY,
            record_path=CR.record_path(root))

    # arm 1: the pending source is NOT the newest failure - naming must not be a
    # by-product of newest_src (the R3006 probe shape, measured before the pin)
    rG1, tG1 = trend23(
        [(OTHER23, TODAY + 'T09:30:00+08:00'),
         (SRC23B, TODAY + 'T12:30:00+08:00')],
        [[(SRC23A, TODAY + 'T09:00:00+08:00', 'E_FETCH TimeoutError: a'),
          (SRC23B, TODAY + 'T12:00:00+08:00', 'E_FETCH HTTPError: b')]])
    ok('AC-RUN23', tG1['pending'] == (1, 2) and tG1['pending_src'] == SRC23A
       and tG1['newest_src'] == SRC23B and tG1['since_ok'] == 'yes',
       'the source that is still gone is named even though the newest failure was repaired - a name, not a side effect of newest_src')

    # arm 2: two pending sources - the one waiting longest is named
    rG2, tG2 = trend23(
        [(OTHER23, TODAY + 'T13:00:00+08:00')],
        [[(SRC23A, TODAY + 'T09:00:00+08:00', 'E_FETCH TimeoutError: a'),
          (SRC23B, TODAY + 'T12:00:00+08:00', 'E_FETCH HTTPError: b')]])
    ok('AC-RUN23', tG2['pending'] == (2, 2) and tG2['pending_src'] == SRC23A,
       'with two sources pending the one whose failure is oldest is named - start where the wait is longest')

    # arm 3: an equal stamp is broken by url, so two write orders agree
    _rG3a, tG3a = trend23(
        [(OTHER23, TODAY + 'T13:00:00+08:00')],
        [[(SRC23B, TODAY + 'T10:00:00+08:00', 'E_FETCH HTTPError: b')],
         [(SRC23A, TODAY + 'T10:00:00+08:00', 'E_FETCH TimeoutError: a')]])
    _rG3b, tG3b = trend23(
        [(OTHER23, TODAY + 'T13:00:00+08:00')],
        [[(SRC23A, TODAY + 'T10:00:00+08:00', 'E_FETCH TimeoutError: a')],
         [(SRC23B, TODAY + 'T10:00:00+08:00', 'E_FETCH HTTPError: b')]])
    ok('AC-RUN23', tG3a['pending_src'] == tG3b['pending_src'] == SRC23A
       and tG3a['pending'] == (2, 2),
       'two sources stamped the same tick name the lexicographically smaller url on both write orders - no reader has to guess')

    # arm 4: nothing pending reads none in all three shapes
    _rG4a, tG4a = trend23(
        [(SRC23A, TODAY + 'T09:30:00+08:00'),
         (SRC23B, TODAY + 'T12:30:00+08:00')],
        [[(SRC23A, TODAY + 'T09:00:00+08:00', 'E_FETCH TimeoutError: a'),
          (SRC23B, TODAY + 'T12:00:00+08:00', 'E_FETCH HTTPError: b')]])
    _rG4b, tG4b = trend23(
        [], [[(SRC23A, TODAY + 'T09:00:00+08:00',
               'E_FETCH TimeoutError: a')]])
    _rG4c, tG4c = trend23(
        [(OTHER23, TODAY + 'T09:30:00+08:00')],
        [[(SRC23C, TODAY + 'T12:00:00+08:00', 'E_FETCH URLError: c')]])
    ok('AC-RUN23', tG4a['pending'] == (0, 2) and tG4a['pending_src'] is None
       and tG4b['pending'] is None and tG4b['pending_src'] is None
       and tG4c['pending'] is None and tG4c['pending_src'] is None,
       'all repaired, nothing judged and nothing but an unmeasured source all read none - an empty name is never printed as an empty string')

    # arm 5: an unmeasured source is never named - the R3004 split survives
    _rG5, tG5 = trend23(
        [(OTHER23, TODAY + 'T09:30:00+08:00')],
        [[(SRC23A, TODAY + 'T12:00:00+08:00',
           'E_FETCH TimeoutError: a')]])
    ok('AC-RUN23', tG5['pending'] is None and tG5['pending_src'] is None
       and RUN._since_ok(CR.record_path(_rG5), SRC23A,
                         TODAY + 'T12:00:00+08:00') == 'unmeasured',
       'a source nobody looked at after its failure is unmeasured, so it is neither counted nor named - naming it would revive the conflation R3004 removed')

    # arm 6: the exact key set, and the refused field never appears
    rootG6 = world()
    roots.append(rootG6)
    RUN.append_failure(RUN.failure_path(rootG6), SRC23A,
                       TODAY + 'T09:00:00+08:00', 'E_FETCH TimeoutError: a')
    write_days(RUN.failure_day_path(rootG6), [])
    tG6 = RUN.summarize_failure_trend(
        RUN.failure_day_path(rootG6), RUN.failure_path(rootG6), TODAY,
        record_path=CR.record_path(rootG6))
    judged6 = tG6['pending'][1] if tG6['pending'] else 0
    ok('AC-RUN23', set(tG6.keys()) == baseB | set(['flips', 'pending',
                                                   'pending_src', 'pending_age_d',
                                                   'pending_age_min_d', 'pending_age_med_d', 'pending_old', 'pending_old_age_d', 'pending_old_age_min_d', 'fcov', 'rcov'])
       and 'unjudged' not in tG6
       and tG6['sources'] - judged6 == 1,
       'the row grows by exactly one name and carries no unjudged field - the unjudged count is measurable as sources minus the denominator, so a field for it would only restate two keys')

    # arm 7: the one-line contract and the scanner's zero-consumption premise
    bufG7 = io.StringIO()
    with contextlib.redirect_stdout(bufG7):
        rcG7 = RUN.main(['--failure-trend', '--root', rG1])
    linesG7 = [n for n in bufG7.getvalue().splitlines() if n.strip()]
    lineG7 = linesG7[0] if linesG7 else ''
    ok('AC-RUN23', rcG7 == 0 and len(linesG7) == 1
       and ('pending_src=%s' % SRC23A) in lineG7
       and 'pending=1/2' in lineG7
       and 'PASS' not in lineG7 and 'FLAG' not in lineG7
       and 'verdict' not in lineG7 and 'crawl-failure' not in scan_src18,
       'a multi-source window still prints ONE line carrying pending_src=, and the scanner still reads none of it')

    # AC-RUN24 (R3007): pending_src= answered WHICH source to start with and
    # never HOW LONG it had been gone, so a source broken five minutes ago and
    # one broken a week read the same. Measured before this was written: the
    # named source's own stamp was computed inside _pending_sources and
    # discarded (the helper returned three values), and the failure summary's
    # newest_at is taken across ALL sources - in the probe world it named a
    # different source's stamp than pending_src did. pending_age_d= is therefore
    # measured against the NAMED source's own latest failure and the window day,
    # never against newest_at. The other pending sources stay counts: their
    # number is the numerator minus one (arithmetic, refused as a field) and
    # their identities need one line per source (the one-line contract refuses).
    SRC24A = 'https://a.example/page'
    SRC24B = 'https://b.example/page'

    def trend24(record_rows, failure_rows_batches):
        root = world()
        roots.append(root)
        for url, when in record_rows:
            CR.append_record(CR.record_path(root), url, when, 'no-drift')
        for batch in failure_rows_batches:
            for url, when, err in batch:
                RUN.append_failure(RUN.failure_path(root), url, when, err)
        write_days(RUN.failure_day_path(root), [])
        return root, RUN.summarize_failure_trend(
            RUN.failure_day_path(root), RUN.failure_path(root), TODAY,
            record_path=CR.record_path(root))

    # arm 1: the age follows the NAME, not the newest failure
    rH1, tH1 = trend24(
        [(SRC24B, TODAY + 'T12:30:00+08:00')],
        [[(SRC24A, '2026-11-15T09:00:00+08:00', 'E_FETCH TimeoutError: a'),
          (SRC24B, TODAY + 'T12:00:00+08:00', 'E_FETCH HTTPError: b')]])
    summaryH1 = RUN.summarize_failures(RUN.failure_path(rH1), TODAY)
    ok('AC-RUN24', tH1['pending_src'] == SRC24A and tH1['pending_age_d'] == 4
       and str(summaryH1['newest_at']).startswith(TODAY),
       'the age is the named source\'s own (2026-11-15 -> 4 days) while newest_at is today - a reader taking newest_at would answer 0')

    # arm 2: same stamp, two write orders - same name and same age
    rH2a, tH2a = trend24(
        [(SRC24B, TODAY + 'T08:00:00+08:00')],
        [[(SRC24A, '2026-11-17T10:00:00+08:00', 'E_FETCH TimeoutError: a'),
          (SRC24B, '2026-11-17T10:00:00+08:00', 'E_FETCH TimeoutError: b')]])
    rH2b, tH2b = trend24(
        [(SRC24B, TODAY + 'T08:00:00+08:00')],
        [[(SRC24B, '2026-11-17T10:00:00+08:00', 'E_FETCH TimeoutError: b'),
          (SRC24A, '2026-11-17T10:00:00+08:00', 'E_FETCH TimeoutError: a')]])
    ok('AC-RUN24', tH2a['pending_src'] == tH2b['pending_src'] == SRC24A
       and tH2a['pending_age_d'] == tH2b['pending_age_d'] == 2,
       'two equal stamps name the same source and the same age whichever order the rows landed in')

    # arm 3: everything repaired - age is none, never 0
    rH3, tH3 = trend24(
        [(SRC24A, TODAY + 'T09:30:00+08:00')],
        [[(SRC24A, TODAY + 'T09:00:00+08:00', 'E_FETCH TimeoutError: a')]])
    ok('AC-RUN24', tH3['pending'] == (0, 1) and tH3['pending_src'] is None
       and tH3['pending_age_d'] is None,
       'no pending source reads none rather than 0, because 0 would name a source that is not there')

    # arm 4: an unmeasured-only world is none too (the R3004 split holds)
    rH4, tH4 = trend24(
        [('https://seen.example/page', '2026-11-18T08:00:00+08:00')],
        [[(SRC24A, TODAY + 'T12:00:00+08:00', 'E_FETCH TimeoutError: a')]])
    ok('AC-RUN24', tH4['pending'] is None and tH4['pending_src'] is None
       and tH4['pending_age_d'] is None,
       'a source nobody looked after is neither pending nor aged - the verdict split is not aggregated away')

    # arm 5: the pure function's edges - no invented age, no invented clock
    ok('AC-RUN24', RUN._day_age(TODAY, '2026-11-21T00:00:00+08:00') is None
       and RUN._day_age('not-a-day', TODAY + 'T00:00:00+08:00') is None
       and RUN._day_age(TODAY, '') is None
       and RUN._day_age(TODAY, TODAY + 'T23:59:00+08:00') == 0
       and RUN._day_age(TODAY, '2026-11-12T01:00:00+08:00') == 7,
       'a future stamp, a malformed day and an empty stamp all answer None; same day is 0 and a week is 7')

    # arm 6: exactly one new key, and the refused fields never grew
    ok('AC-RUN24', set(tH1.keys()) == baseB | set(['flips', 'pending',
                                                   'pending_src',
                                                   'pending_age_d',
                                                   'pending_age_min_d',
                                                   'pending_age_med_d',
                                                   'pending_old', 'pending_old_age_d', 'pending_old_age_min_d', 'fcov', 'rcov'])
       and 'pending_others' not in tH1 and 'unjudged' not in tH1,
       'the row grows by exactly one age key, and neither refused field (pending_others arithmetic, unjudged restatement) exists')

    # arm 7: the one-line contract and the scanner's zero-consumption premise
    bufH7 = io.StringIO()
    with contextlib.redirect_stdout(bufH7):
        rcH7 = RUN.main(['--failure-trend', '--root', rH1])
    linesH7 = [n for n in bufH7.getvalue().splitlines() if n.strip()]
    lineH7 = linesH7[0] if linesH7 else ''
    bufH7b = io.StringIO()
    with contextlib.redirect_stdout(bufH7b):
        rcH7b = RUN.main(['--failure-trend', '--root', rH3])
    linesH7b = [n for n in bufH7b.getvalue().splitlines() if n.strip()]
    lineH7b = linesH7b[0] if linesH7b else ''
    ok('AC-RUN24', rcH7 == 0 and len(linesH7) == 1 and 'pending_age_d=4' in lineH7
       and rcH7b == 0 and len(linesH7b) == 1 and 'pending_age_d=none' in lineH7b
       and 'PASS' not in lineH7 and 'FLAG' not in lineH7
       and 'verdict' not in lineH7 and 'crawl-failure' not in scan_src18,
       'one line carries pending_age_d= (a number, or none when nothing is pending), and the scanner still reads none of it')

    # AC-RUN25 (R3008): pending_age_d= described the source waiting LONGEST and
    # said nothing about the rest, so with several pending sources a person
    # could not tell a burst that just started from a long tail. Measured before
    # this was written (qa/probe-R3008.log): three pending sources aged 0/2/4
    # days read pending=(3,3) pending_age_d=4 and the 0-day source appeared in
    # none of the 24 keys. A pending_age_max_d field was measured and REFUSED -
    # the named source is by construction the oldest (raw recomputation agreed),
    # so a max would restate pending_age_d. pending_age_min_d= is the NEWEST
    # pending source's own age: together with pending_age_d= it is the AGE SPAN
    # of the pending set, and when one source (or one shared stamp) is pending
    # the two coincide as a fact.
    SRC25A = 'https://a.example/page'
    SRC25B = 'https://b.example/page'
    SRC25C = 'https://c.example/page'

    def trend25(record_rows, failure_rows_batches):
        root = world()
        roots.append(root)
        for url, when in record_rows:
            CR.append_record(CR.record_path(root), url, when, 'no-drift')
        for batch in failure_rows_batches:
            for url, when, err in batch:
                RUN.append_failure(RUN.failure_path(root), url, when, err)
        write_days(RUN.failure_day_path(root), [])
        return root, RUN.summarize_failure_trend(
            RUN.failure_day_path(root), RUN.failure_path(root), TODAY,
            record_path=CR.record_path(root))

    # arm 1: three pending sources - the two ages are NOT the same number
    rI1, tI1 = trend25(
        [('https://keep.example/page', TODAY + 'T13:00:00+08:00')],
        [[(SRC25A, '2026-11-15T09:00:00+08:00', 'E_FETCH TimeoutError: a'),
          (SRC25B, '2026-11-17T10:00:00+08:00', 'E_FETCH TimeoutError: b'),
          (SRC25C, TODAY + 'T08:00:00+08:00', 'E_FETCH HTTPError: c')]])
    ok('AC-RUN25', tI1['pending'] == (3, 3) and tI1['pending_age_d'] == 4
       and tI1['pending_age_min_d'] == 0,
       'the oldest pending source reads 4 days and the youngest (broken today) reads 0 - the second end of the span is no longer blank')

    # arm 2: one pending source - the two ages coincide, and that is the truth
    rI2, tI2 = trend25(
        [('https://keep.example/page', TODAY + 'T13:00:00+08:00')],
        [[(SRC25A, '2026-11-15T09:00:00+08:00', 'E_FETCH TimeoutError: a')]])
    ok('AC-RUN25', tI2['pending'] == (1, 1) and tI2['pending_age_d'] == 4
       and tI2['pending_age_min_d'] == 4,
       'with one pending source both ends read 4 - the coincidence is pinned as a fact so it is never silently turned into None')

    # arm 3: everything repaired - both ages are none, never 0
    rI3, tI3 = trend25(
        [(SRC25A, TODAY + 'T09:30:00+08:00')],
        [[(SRC25A, TODAY + 'T09:00:00+08:00', 'E_FETCH TimeoutError: a')]])
    ok('AC-RUN25', tI3['pending'] == (0, 1) and tI3['pending_age_d'] is None
       and tI3['pending_age_min_d'] is None,
       'no pending source reads none at both ends, because 0 would name a source that is not there')

    # arm 4: an unmeasured-only world is none too (the R3004 split holds)
    rI4, tI4 = trend25(
        [('https://seen.example/page', '2026-11-18T08:00:00+08:00')],
        [[(SRC25A, TODAY + 'T12:00:00+08:00', 'E_FETCH TimeoutError: a')]])
    ok('AC-RUN25', tI4['pending'] is None and tI4['pending_age_d'] is None
       and tI4['pending_age_min_d'] is None,
       'a source nobody looked after is neither pending nor aged at either end - the verdict split is not aggregated away by a second age')

    # arm 5: two pending sources sharing a stamp - both ends coincide
    rI5, tI5 = trend25(
        [('https://keep.example/page', TODAY + 'T13:00:00+08:00')],
        [[(SRC25A, '2026-11-17T10:00:00+08:00', 'E_FETCH TimeoutError: a'),
          (SRC25B, '2026-11-17T10:00:00+08:00', 'E_FETCH TimeoutError: b')]])
    ok('AC-RUN25', tI5['pending'] == (2, 2) and tI5['pending_age_d'] == 2
       and tI5['pending_age_min_d'] == 2,
       'two pending sources that failed at the same moment read the same age at both ends')

    # arm 6: exactly one new key, and the refused fields never grew
    ok('AC-RUN25', set(tI1.keys()) == baseB | set(['flips', 'pending',
                                                   'pending_src',
                                                   'pending_age_d',
                                                   'pending_age_min_d',
                                                   'pending_age_med_d',
                                                   'pending_old', 'pending_old_age_d', 'pending_old_age_min_d', 'fcov', 'rcov'])
       and 'pending_age_max_d' not in tI1
       and 'pending_others' not in tI1 and 'unjudged' not in tI1,
       'the row grows by exactly one age key, and the refused max field (a restatement of pending_age_d, measured) plus the two older refusals never exist')

    # arm 7: the one-line contract and the scanner's zero-consumption premise
    bufI7 = io.StringIO()
    with contextlib.redirect_stdout(bufI7):
        rcI7 = RUN.main(['--failure-trend', '--root', rI1])
    linesI7 = [n for n in bufI7.getvalue().splitlines() if n.strip()]
    lineI7 = linesI7[0] if linesI7 else ''
    bufI7b = io.StringIO()
    with contextlib.redirect_stdout(bufI7b):
        rcI7b = RUN.main(['--failure-trend', '--root', rI3])
    linesI7b = [n for n in bufI7b.getvalue().splitlines() if n.strip()]
    lineI7b = linesI7b[0] if linesI7b else ''
    ok('AC-RUN25', rcI7 == 0 and len(linesI7) == 1
       and 'pending_age_d=4' in lineI7 and 'pending_age_min_d=0' in lineI7
       and rcI7b == 0 and len(linesI7b) == 1
       and 'pending_age_min_d=none' in lineI7b
       and 'PASS' not in lineI7 and 'FLAG' not in lineI7
       and 'verdict' not in lineI7 and 'crawl-failure' not in scan_src18,
       'one line carries both ends of the age span (numbers, or none when nothing is pending), and the scanner still reads none of it')


    # AC-RUN26 (R3009): the two ends described the span and left everything
    # between them silent, so "a burst that just started" and "an old tail with
    # one new arrival" printed the same row. Measured before this was written
    # (qa/probe-R3009.log): worlds with the same ends but different middles
    # (ages 5/3/0 versus 5/1/0) were identical on all 25 keys, and so were a
    # world with the mass old (5/5/5/0/0) and one with it new (5/0/0/0/0). A
    # pointer to the failure-day file was measured and REFUSED as the
    # alternative: that file carries a urls= COUNT and no per-source identity
    # or age. pending_age_med_d= is the middle of the pending set, nearer the
    # old end when the count is even - not the max refused in R3008, which
    # equalled pending_age_d by construction in every world.
    SRC26A = 'https://a.example/page'
    SRC26B = 'https://b.example/page'
    SRC26C = 'https://c.example/page'
    SRC26D = 'https://d.example/page'
    SRC26E = 'https://e.example/page'

    # arm 1: three pending sources - the middle is neither end's restatement
    rJ1, tJ1 = trend25(
        [('https://keep.example/page', TODAY + 'T13:00:00+08:00')],
        [[(SRC26A, '2026-11-14T09:00:00+08:00', 'E_FETCH TimeoutError: a'),
          (SRC26B, '2026-11-16T09:00:00+08:00', 'E_FETCH TimeoutError: b'),
          (SRC26C, TODAY + 'T08:00:00+08:00', 'E_FETCH HTTPError: c')]])
    ok('AC-RUN26', tJ1['pending'] == (3, 3) and tJ1['pending_age_d'] == 5
       and tJ1['pending_age_min_d'] == 0
       and tJ1['pending_age_med_d'] == 3,
       'ages 5/3/0 read a middle of 3 while the ends read 5 and 0 - the middle is no longer blank and is neither end restated')

    # arm 2: same ends, opposite mass - the middle is what separates them
    rJ2a, tJ2a = trend25(
        [('https://keep.example/page', TODAY + 'T13:00:00+08:00')],
        [[(SRC26A, '2026-11-14T09:00:00+08:00', 'E_FETCH TimeoutError: a'),
          (SRC26B, '2026-11-14T10:00:00+08:00', 'E_FETCH TimeoutError: b'),
          (SRC26D, '2026-11-14T11:00:00+08:00', 'E_FETCH TimeoutError: d'),
          (SRC26E, TODAY + 'T07:00:00+08:00', 'E_FETCH TimeoutError: e'),
          (SRC26C, TODAY + 'T08:00:00+08:00', 'E_FETCH TimeoutError: c')]])
    rJ2b, tJ2b = trend25(
        [('https://keep.example/page', TODAY + 'T13:00:00+08:00')],
        [[(SRC26A, '2026-11-14T09:00:00+08:00', 'E_FETCH TimeoutError: a'),
          (SRC26B, TODAY + 'T05:00:00+08:00', 'E_FETCH TimeoutError: b'),
          (SRC26D, TODAY + 'T06:00:00+08:00', 'E_FETCH TimeoutError: d'),
          (SRC26E, TODAY + 'T07:00:00+08:00', 'E_FETCH TimeoutError: e'),
          (SRC26C, TODAY + 'T08:00:00+08:00', 'E_FETCH TimeoutError: c')]])
    ok('AC-RUN26', tJ2a['pending'] == tJ2b['pending'] == (5, 5)
       and tJ2a['pending_age_d'] == tJ2b['pending_age_d'] == 5
       and tJ2a['pending_age_min_d'] == tJ2b['pending_age_min_d'] == 0
       and tJ2a['pending_age_med_d'] == 5
       and tJ2b['pending_age_med_d'] == 0,
       'mass at the old end and mass at the new end are indistinguishable on the count and both ends, and the middle is exactly what tells them apart')

    # arm 3: two pending sources - the even count takes the one nearer the old
    # end, so the middle coincides with pending_age_d. Pinned as a fact.
    rJ3, tJ3 = trend25(
        [('https://keep.example/page', TODAY + 'T13:00:00+08:00')],
        [[(SRC26A, '2026-11-14T09:00:00+08:00', 'E_FETCH TimeoutError: a'),
          (SRC26C, TODAY + 'T08:00:00+08:00', 'E_FETCH TimeoutError: c')]])
    ok('AC-RUN26', tJ3['pending'] == (2, 2) and tJ3['pending_age_d'] == 5
       and tJ3['pending_age_min_d'] == 0
       and tJ3['pending_age_med_d'] == 5,
       'with two pending sources the middle is the older one (the even-count rule), so it equals pending_age_d - the coincidence is pinned rather than silently turned into None')

    # arm 4: one pending source - all three ages coincide, which is the truth
    rJ4, tJ4 = trend25(
        [('https://keep.example/page', TODAY + 'T13:00:00+08:00')],
        [[(SRC26A, '2026-11-14T09:00:00+08:00', 'E_FETCH TimeoutError: a')]])
    ok('AC-RUN26', tJ4['pending'] == (1, 1) and tJ4['pending_age_d'] == 5
       and tJ4['pending_age_min_d'] == 5
       and tJ4['pending_age_med_d'] == 5,
       'one pending source reads the same age at both ends and in the middle')

    # arm 5: nothing pending, and a source nobody looked after - all None
    rJ5a, tJ5a = trend25(
        [(SRC26A, TODAY + 'T09:30:00+08:00')],
        [[(SRC26A, TODAY + 'T09:00:00+08:00', 'E_FETCH TimeoutError: a')]])
    rJ5b, tJ5b = trend25(
        [('https://seen.example/page', '2026-11-18T08:00:00+08:00')],
        [[(SRC26A, TODAY + 'T12:00:00+08:00', 'E_FETCH TimeoutError: a')]])
    ok('AC-RUN26', tJ5a['pending'] == (0, 1)
       and tJ5a['pending_age_d'] is None
       and tJ5a['pending_age_min_d'] is None
       and tJ5a['pending_age_med_d'] is None
       and tJ5b['pending'] is None
       and tJ5b['pending_age_d'] is None
       and tJ5b['pending_age_min_d'] is None
       and tJ5b['pending_age_med_d'] is None,
       'a repaired set and an unmeasured-only set read None in the middle too - the R3004 split is not aggregated away by a third age')

    # arm 6: exactly one new key, and the refused shapes never grew
    ok('AC-RUN26', set(tJ1.keys()) == baseB | set(['flips', 'pending',
                                                   'pending_src',
                                                   'pending_age_d',
                                                   'pending_age_min_d',
                                                   'pending_age_med_d',
                                                   'pending_old', 'pending_old_age_d', 'pending_old_age_min_d', 'fcov', 'rcov'])
       and 'pending_age_max_d' not in tJ1
       and 'pending_hist' not in tJ1
       and 'pending_others' not in tJ1 and 'unjudged' not in tJ1,
       'the row grows by exactly one age key, and the refused max, histogram and the two older refusals never exist')

    # arm 7: the one-line contract and the scanner's zero-consumption premise
    bufJ7 = io.StringIO()
    with contextlib.redirect_stdout(bufJ7):
        rcJ7 = RUN.main(['--failure-trend', '--root', rJ1])
    linesJ7 = [n for n in bufJ7.getvalue().splitlines() if n.strip()]
    lineJ7 = linesJ7[0] if linesJ7 else ''
    bufJ7b = io.StringIO()
    with contextlib.redirect_stdout(bufJ7b):
        rcJ7b = RUN.main(['--failure-trend', '--root', rJ5a])
    linesJ7b = [n for n in bufJ7b.getvalue().splitlines() if n.strip()]
    lineJ7b = linesJ7b[0] if linesJ7b else ''
    ok('AC-RUN26', rcJ7 == 0 and len(linesJ7) == 1
       and 'pending_age_med_d=3' in lineJ7
       and 'pending_age_d=5' in lineJ7 and 'pending_age_min_d=0' in lineJ7
       and rcJ7b == 0 and len(linesJ7b) == 1
       and 'pending_age_med_d=none' in lineJ7b
       and 'PASS' not in lineJ7 and 'FLAG' not in lineJ7
       and 'verdict' not in lineJ7 and 'crawl-failure' not in scan_src18,
       'one line carries the middle (a number, or none when nothing is pending), and the scanner still reads none of it')

    # AC-RUN27 (R3010): the window decides who is counted, so a source whose
    # OWN latest failure fell before the window start left every key. Measured
    # before this was written (qa/probe-R3010.log): still-broken and repaired
    # differed only through rcov, and a side channel trimmed to the window read
    # identical to a healthy world on all 26 keys. pending_old=<n>/<judged>
    # counts only that OUTSIDE population, with its own denominator, so
    # pending= keeps meaning what sources= names; judged==0 answers None so a
    # trimmed side channel cannot read like a clean bill of health.
    SRC27A = 'https://a.example/page'
    SRC27B = 'https://b.example/page'
    SRC27K = 'https://keep.example/page'
    OLD27 = '2026-11-10T10:00:00+08:00'   # 9 days before TODAY: outside a 7-day window
    NEW27 = '2026-11-19T08:00:00+08:00'
    KEEP27 = '2026-11-19T09:00:00+08:00'

    def trend27(record_rows, failure_rows, window=7):
        root = world()
        roots.append(root)
        for url, when in record_rows:
            CR.append_record(CR.record_path(root), url, when, 'no-drift')
        for url, when, err in failure_rows:
            RUN.append_failure(RUN.failure_path(root), url, when, err)
        write_days(RUN.failure_day_path(root), [])
        return root, RUN.summarize_failure_trend(
            RUN.failure_day_path(root), RUN.failure_path(root), TODAY,
            window_days=window, record_path=CR.record_path(root))

    # arm 1: a still-broken source OUTSIDE the window is counted, while the
    # in-window fraction keeps its own population
    rK1, tK1 = trend27(
        [(SRC27K, KEEP27), (SRC27B, KEEP27)],
        [(SRC27A, OLD27, 'TimeoutError: t'), (SRC27B, NEW27, 'TimeoutError: t')])
    ok('AC-RUN27', tK1['pending_old'] == (1, 1)
       and tK1['pending'] == (0, 1) and tK1['sources'] == 1,
       'a source broken nine days ago and never fetched again is counted outside the window, and pending= still describes only the in-window population')

    # arm 2: the same history with that source repaired -> 0 is a MEASURED zero
    rK2, tK2 = trend27(
        [(SRC27K, KEEP27), (SRC27B, KEEP27), (SRC27A, '2026-11-11T09:00:00+08:00')],
        [(SRC27A, OLD27, 'TimeoutError: t'), (SRC27B, NEW27, 'TimeoutError: t')])
    ok('AC-RUN27', tK2['pending_old'] == (0, 1),
       'a repaired old source reads 0 of 1 judged - a measured zero, not None')

    # arm 3: side channel trimmed to the window -> nothing was looked at out
    # there, which must answer None rather than 0
    rK3, tK3 = trend27(
        [(SRC27K, KEEP27), (SRC27B, KEEP27)],
        [(SRC27B, NEW27, 'TimeoutError: t')])
    ok('AC-RUN27', tK3['pending_old'] is None,
       'a side channel holding nothing outside the window answers None, so deleting the evidence cannot read like a repair')

    # arm 4: the record stops before the old failure -> unmeasured, and the
    # R3004 split is not aggregated back by this third count
    rK4, tK4 = trend27(
        [(SRC27K, '2026-11-10T09:00:00+08:00')],
        [(SRC27A, OLD27, 'TimeoutError: t'), (SRC27B, NEW27, 'TimeoutError: t')])
    ok('AC-RUN27', tK4['pending_old'] is None,
       'an old failure nobody looked after is unmeasured, never pending, so it is in neither number')

    # arm 5: the window length is a parameter, not a constant - at 14 days the
    # same source is back INSIDE and the outside face is empty
    rK5, tK5 = trend27(
        [(SRC27K, KEEP27), (SRC27B, KEEP27)],
        [(SRC27A, OLD27, 'TimeoutError: t'), (SRC27B, NEW27, 'TimeoutError: t')],
        window=14)
    ok('AC-RUN27', tK5['pending'] == (1, 2) and tK5['pending_old'] is None,
       'with a 14-day window the same source is in-window (pending 1/2) and the outside count is None - the two fractions never overlap')

    # arm 6: exactly one new key, and no per-source face for the outside set
    ok('AC-RUN27', set(tK1.keys()) == baseB | set(['flips', 'pending',
                                                   'pending_src',
                                                   'pending_age_d',
                                                   'pending_age_min_d',
                                                   'pending_age_med_d',
                                                   'pending_old', 'pending_old_age_d', 'pending_old_age_min_d', 'fcov', 'rcov'])
       and 'pending_old_src' not in tK1,
       'the row grows by exactly one count key, and the refused per-source face (one line per source) never exists - R3012 later landed an AGGREGATE old age, which is the shape R3007 already allowed for the in-window population')

    # arm 7: the one-line contract and the scanner's zero-consumption premise
    bufK7 = io.StringIO()
    with contextlib.redirect_stdout(bufK7):
        rcK7 = RUN.main(['--failure-trend', '--root', rK1])
    linesK7 = [n for n in bufK7.getvalue().splitlines() if n.strip()]
    lineK7 = linesK7[0] if linesK7 else ''
    bufK7b = io.StringIO()
    with contextlib.redirect_stdout(bufK7b):
        rcK7b = RUN.main(['--failure-trend', '--root', rK3])
    linesK7b = [n for n in bufK7b.getvalue().splitlines() if n.strip()]
    lineK7b = linesK7b[0] if linesK7b else ''
    ok('AC-RUN27', rcK7 == 0 and len(linesK7) == 1
       and 'pending_old=1/1' in lineK7 and 'pending=0/1' in lineK7
       and rcK7b == 0 and len(linesK7b) == 1
       and 'pending_old=none' in lineK7b
       and 'PASS' not in lineK7 and 'FLAG' not in lineK7
       and 'verdict' not in lineK7 and 'crawl-failure' not in scan_src18,
       'one line carries pending_old= (a fraction, or none when nothing was judged), and the scanner still reads none of it')

    # AC-RUN28 (R3011): pending_old= counts over the failure side channel but
    # never said how far back that channel reaches. Measured before this was
    # written (qa/probe-R3011.log): a one-day channel and a ninety-one-day
    # channel were identical on all 27 keys - the extra row was an EARLIER
    # failure of the SAME source, so every judged fact matched. fcov=<first>..
    # <last> is the channel's own span, following the FILE and not the window.
    SRC28A = 'https://a.example/page'
    SRC28B = 'https://b.example/page'
    SRC28K = 'https://keep.example/page'
    FAR28 = '2026-08-20T10:00:00+08:00'    # 91 days before TODAY
    EDGE28 = '2026-11-12T10:00:00+08:00'   # just outside a 7-day window
    NEW28 = '2026-11-19T08:00:00+08:00'
    REC28 = [(SRC28K, '2026-11-19T09:00:00+08:00'),
             (SRC28B, '2026-11-19T09:00:00+08:00'),
             (SRC28A, '2026-11-12T12:00:00+08:00')]
    FAIL28 = [(SRC28B, NEW28, 'TimeoutError: t'),
              (SRC28A, EDGE28, 'TimeoutError: t')]

    def trend28(failure_rows, window=7, junk=()):
        root = world()
        roots.append(root)
        for url, when in REC28:
            CR.append_record(CR.record_path(root), url, when, 'no-drift')
        for url, when, err in failure_rows:
            RUN.append_failure(RUN.failure_path(root), url, when, err)
        if junk:
            with open(RUN.failure_path(root), 'a', encoding='utf-8',
                      newline='\n') as fh:
                for text in junk:
                    fh.write(text + '\n')
        write_days(RUN.failure_day_path(root), [])
        return root, RUN.summarize_failure_trend(
            RUN.failure_day_path(root), RUN.failure_path(root), TODAY,
            window_days=window, record_path=CR.record_path(root))

    # arm 1: same judged facts, different evidence length - only fcov= moves
    rL1, tL1 = trend28(FAIL28)
    rL2, tL2 = trend28(FAIL28 + [(SRC28A, FAR28, 'TimeoutError: t')])
    ok('AC-RUN28', tL1['pending_old'] == tL2['pending_old'] == (0, 1)
       and tL1['fcov'] == ('2026-11-12', '2026-11-19')
       and tL2['fcov'] == ('2026-08-20', '2026-11-19'),
       'two channels that read the same pending_old= are separated by how far back their evidence reaches')

    # arm 2: the window is a parameter; fcov follows the file, not the window
    rL2w, tL2w = trend28(FAIL28 + [(SRC28A, FAR28, 'TimeoutError: t')],
                         window=14)
    ok('AC-RUN28', tL2w['fcov'] == tL2['fcov']
       and tL2w['pending_old'] is None and tL2w['pending'] == (0, 2),
       'a 14-day window leaves fcov= byte-identical while pending_old= becomes none - it describes the file')

    # arm 3: a channel trimmed to the window narrows fcov too
    rL3, tL3 = trend28([(SRC28B, NEW28, 'TimeoutError: t')])
    ok('AC-RUN28', tL3['fcov'] == ('2026-11-19', '2026-11-19')
       and tL3['pending_old'] is None,
       'trimming the channel to the window narrows fcov= and empties the outside count')

    # arm 4: malformed rows never widen the span (they only raise the reader's
    # own bad count, which the row does NOT restate for this file)
    rL4, tL4 = trend28(
        FAIL28 + [(SRC28A, FAR28, 'TimeoutError: t')],
        junk=('garbage not json',
              json.dumps({'source_url': SRC28A,
                          'failed_at': '1999-01-01T00:00:00+08:00',
                          'error': ''})))
    bad4 = RUN.read_failures(RUN.failure_path(rL4))[1]
    ok('AC-RUN28', tL4['fcov'] == ('2026-08-20', '2026-11-19') and bad4 == 2,
       'a non-JSON line and an unusable stamp raise bad and leave the span untouched')

    # arm 5: absent, empty and all-unusable channels all answer none
    rL5 = world(); roots.append(rL5)                       # absent
    tL5 = RUN.summarize_failure_trend(RUN.failure_day_path(rL5),
                                      RUN.failure_path(rL5), TODAY,
                                      record_path=CR.record_path(rL5))
    rL6, tL6 = trend28([])                                 # empty
    rL7, tL7 = trend28([], junk=('{not json}',
                                 json.dumps({'source_url': SRC28A,
                                             'failed_at': 'nope',
                                             'error': 'x'})))
    ok('AC-RUN28', tL5['fcov'] is None and tL6['fcov'] is None
       and tL7['fcov'] is None,
       'a channel that is absent, empty or holds no usable row reads none - never an empty string or a zero-day span')

    # arm 6: exactly one new key, and no per-source reach face
    ok('AC-RUN28', set(tL1.keys()) == baseB | set(['flips', 'pending',
                                                   'pending_src',
                                                   'pending_age_d',
                                                   'pending_age_min_d',
                                                   'pending_age_med_d',
                                                   'pending_old',
                                                   'pending_old_age_d', 'pending_old_age_min_d', 'fcov',
                                                   'rcov'])
       and 'fcov_src' not in tL1 and 'fcov_days' not in tL1,
       'the row grows by exactly one span key, and the refused per-source reach face never exists')

    # arm 7: the one-line contract and the scanner's zero-consumption premise
    bufL7 = io.StringIO()
    with contextlib.redirect_stdout(bufL7):
        rcL7 = RUN.main(['--failure-trend', '--root', rL2])
    linesL7 = [n for n in bufL7.getvalue().splitlines() if n.strip()]
    lineL7 = linesL7[0] if linesL7 else ''
    bufL7b = io.StringIO()
    with contextlib.redirect_stdout(bufL7b):
        rcL7b = RUN.main(['--failure-trend', '--root', rL5])
    linesL7b = [n for n in bufL7b.getvalue().splitlines() if n.strip()]
    lineL7b = linesL7b[0] if linesL7b else ''
    ok('AC-RUN28', rcL7 == 0 and len(linesL7) == 1
       and 'fcov=2026-08-20..2026-11-19' in lineL7
       and rcL7b == 0 and len(linesL7b) == 1
       and 'fcov=none' in lineL7b
       and 'PASS' not in lineL7 and 'FLAG' not in lineL7
       and 'verdict' not in lineL7 and 'crawl-failure' not in scan_src18,
       'one line carries fcov= (a span, or none when the channel has no usable row), and the scanner still reads none of it')

    # AC-RUN29 (R3012): pending_old= says how many sources outside the window
    # never came back, never how long they have been gone. Measured before this
    # was written (qa/probe-R3012.log): fcov.first= is the oldest failure in the
    # FILE and can belong to a source repaired long ago - a world with a
    # repaired failure on 2026-08-20 and one still gone since 2026-11-10 read
    # fcov 2026-08-20..2026-11-10, so a single age is not a restatement of it.
    # pending_old_age_d= is the still-pending old source that waited longest.
    SRC29X = 'https://x.example/page'
    SRC29Y = 'https://y.example/page'
    SRC29A = 'https://a.example/page'
    SRC29K = 'https://keep.example/page'
    OLD29 = '2026-08-20T10:00:00+08:00'    # 91 days before TODAY
    FIX29 = '2026-08-21T09:00:00+08:00'    # X repaired the next day
    MID29 = '2026-11-10T10:00:00+08:00'    # Y still gone, 9 days
    NEW29 = '2026-11-19T08:00:00+08:00'

    def trend29(failure_rows, window=7):
        root = world()
        roots.append(root)
        for url, when in ((SRC29X, FIX29), (SRC29K, '2026-11-19T09:00:00+08:00')):
            CR.append_record(CR.record_path(root), url, when, 'no-drift')
        for url, when in failure_rows:
            RUN.append_failure(RUN.failure_path(root), url, when, 'TimeoutError: t')
        write_days(RUN.failure_day_path(root), [])
        return root, RUN.summarize_failure_trend(
            RUN.failure_day_path(root), RUN.failure_path(root), TODAY,
            window_days=window, record_path=CR.record_path(root))

    # arm 1: the age follows the still-pending source, NOT fcov.first
    rM1, tM1 = trend29([(SRC29X, OLD29), (SRC29Y, MID29)])
    ok('AC-RUN29', tM1['pending_old'] == (1, 2)
       and tM1['pending_old_age_d'] == 9
       and tM1['fcov'] == ('2026-08-20', '2026-11-10')
       and RUN._day_age(TODAY, tM1['fcov'][0]) == 91,
       'a repaired older failure leaves fcov.first at 91 days while the source still gone reads 9 - the age is not that span restated')

    # arm 2: one old pending source - the coincidence is pinned as a fact
    rM2, tM2 = trend29([(SRC29A, OLD29)])
    ok('AC-RUN29', tM2['pending_old'] == (1, 1)
       and tM2['pending_old_age_d'] == 91
       and RUN._day_age(TODAY, '2026-08-20T10:00:00+08:00') == 91,
       'with one pending old source the age equals the only stamp it can come from - pinned rather than turned into none')

    # arm 3: every judged old source came back - none, never 0
    rM3, tM3 = trend29([(SRC29X, OLD29)])
    ok('AC-RUN29', tM3['pending_old'] == (0, 1)
       and tM3['pending_old_age_d'] is None,
       'an old population that is entirely repaired reads a zero fraction with a none age - nobody outside is pending is not a waiter aged zero')

    # arm 4: a channel trimmed to the window answers none, not zero
    rM4, tM4 = trend29([(SRC29Y, NEW29)])
    ok('AC-RUN29', tM4['pending_old'] is None
       and tM4['pending_old_age_d'] is None,
       'a channel that never recorded anything outside the window reads none, because nothing was looked at out there')

    # arm 5: the window is a parameter - a 14-day window moves Y back inside
    rM5, tM5 = trend29([(SRC29X, OLD29), (SRC29Y, MID29)], window=14)
    ok('AC-RUN29', tM5['pending_old'] == (0, 1)
       and tM5['pending_old_age_d'] is None
       and tM5['pending'] == (1, 1),
       'at fourteen days the newer old source is in-window pending while the outside population holds only a repaired one - the two populations do not overlap')

    # arm 6: exactly one new key, and none of the refused faces exist
    ok('AC-RUN29', set(tM1.keys()) == baseB | set(['flips', 'pending',
                                                   'pending_src',
                                                   'pending_age_d',
                                                   'pending_age_min_d',
                                                   'pending_age_med_d',
                                                   'pending_old',
                                                   'pending_old_age_d', 'pending_old_age_min_d',
                                                   'fcov', 'rcov'])
       and 'pending_old_src' not in tM1
       and 'pending_old_age_med_d' not in tM1,
       'the row grows by exactly one age key, and the refused per-source and middle old faces never exist')

    # arm 7: the one-line contract and the scanner's zero-consumption premise
    bufM7 = io.StringIO()
    with contextlib.redirect_stdout(bufM7):
        rcM7 = RUN.main(['--failure-trend', '--root', rM1])
    linesM7 = [n for n in bufM7.getvalue().splitlines() if n.strip()]
    lineM7 = linesM7[0] if linesM7 else ''
    bufM7b = io.StringIO()
    with contextlib.redirect_stdout(bufM7b):
        rcM7b = RUN.main(['--failure-trend', '--root', rM4])
    linesM7b = [n for n in bufM7b.getvalue().splitlines() if n.strip()]
    lineM7b = linesM7b[0] if linesM7b else ''
    ok('AC-RUN29', rcM7 == 0 and len(linesM7) == 1
       and 'pending_old_age_d=9' in lineM7
       and rcM7b == 0 and len(linesM7b) == 1
       and 'pending_old_age_d=none' in lineM7b
       and 'PASS' not in lineM7 and 'FLAG' not in lineM7
       and 'verdict' not in lineM7 and 'crawl-failure' not in scan_src18,
       'one line carries pending_old_age_d= (a number, or none when nothing outside was pending), and the scanner still reads none of it')

    # AC-RUN30 (R3013): one age described only the longest old wait, so with two
    # old waiters the other was invisible. Measured before this was written
    # (qa/probe-R3013.log): a second waiter that failed 90 days ago and one that
    # failed 9 days ago read IDENTICAL on all 29 keys. A middle reading was
    # measured and refused - with two waiters it restates the longest age in
    # both worlds - so the row carries the YOUNGEST old waiter instead.
    SRC30A = 'https://a.example/page'
    SRC30B = 'https://b.example/page'
    SRC30C = 'https://c.example/page'
    SRC30E = 'https://e.example/page'
    SRC30K = 'https://keep.example/page'
    OLD30 = '2026-08-20T10:00:00+08:00'    # 91 days before TODAY
    NXT30 = '2026-08-21T10:00:00+08:00'    # 90 days
    MID30 = '2026-11-10T10:00:00+08:00'    # 9 days
    FIX30 = '2026-11-11T09:00:00+08:00'
    NEW30 = '2026-11-19T08:00:00+08:00'

    def trend30(failure_rows, window=7, extra_records=()):
        root = world()
        roots.append(root)
        rows = [(SRC30K, '2026-11-19T09:00:00+08:00', 'no-drift'),
                (SRC30E, FIX30, 'no-drift')] + list(extra_records)
        for url, when, verdict in rows:
            CR.append_record(CR.record_path(root), url, when, verdict)
        for url, when in failure_rows:
            RUN.append_failure(RUN.failure_path(root), url, when,
                               'TimeoutError: t')
        write_days(RUN.failure_day_path(root), [])
        return root, RUN.summarize_failure_trend(
            RUN.failure_day_path(root), RUN.failure_path(root), TODAY,
            window_days=window, record_path=CR.record_path(root))

    # E is a repaired old row in both worlds, so fcov= is the same file span on
    # both sides and only the second waiter's own stamp differs.
    rN1, tN1 = trend30([(SRC30A, OLD30), (SRC30B, NXT30), (SRC30E, MID30)])
    rN2, tN2 = trend30([(SRC30A, OLD30), (SRC30C, MID30), (SRC30E, MID30)])

    # arm 1: the two worlds are identical except for the youngest old age
    ok('AC-RUN30', tN1['pending_old'] == tN2['pending_old'] == (2, 3)
       and tN1['pending_old_age_d'] == tN2['pending_old_age_d'] == 91
       and tN1['fcov'] == tN2['fcov']
       and tN1['pending_old_age_min_d'] == 90
       and tN2['pending_old_age_min_d'] == 9,
       'an old tail and an old tail plus a fresh dropout read the same fraction, the same longest age and the same file span - the youngest age is what separates them')

    # arm 2: three waiters - the youngest is still 9 and the middle is not a key
    rN3, tN3 = trend30([(SRC30A, OLD30), (SRC30B, NXT30), (SRC30C, MID30),
                        (SRC30E, MID30)])
    ok('AC-RUN30', tN3['pending_old'] == (3, 4)
       and tN3['pending_old_age_d'] == 91
       and tN3['pending_old_age_min_d'] == 9
       and 'pending_old_age_med_d' not in tN3,
       'with three old waiters the youngest reads the recent dropout while the middle would read 90 - and the refused middle key never exists')

    # arm 3: one old waiter - the two ages coincide, pinned as a fact
    rN4, tN4 = trend30([(SRC30A, OLD30)])
    ok('AC-RUN30', tN4['pending_old'] == (1, 1)
       and tN4['pending_old_age_d'] == 91
       and tN4['pending_old_age_min_d'] == 91,
       'with one pending old source both ages name the only waiter it can come from - pinned rather than turned into none')

    # arm 4: every shape with nothing outside reads none, never 0
    rN5, tN5 = trend30([(SRC30C, NEW30)])          # trimmed to the window
    rN6, tN6 = trend30([(SRC30E, MID30)])          # all judged old came back
    rN7 = world()
    roots.append(rN7)
    tN7 = RUN.summarize_failure_trend(
        RUN.failure_day_path(rN7), RUN.failure_path(rN7), TODAY,
        record_path=CR.record_path(rN7))
    ok('AC-RUN30', tN5['pending_old'] is None
       and tN5['pending_old_age_min_d'] is None
       and tN6['pending_old'] == (0, 1)
       and tN6['pending_old_age_min_d'] is None
       and tN7['pending_old_age_min_d'] is None,
       'a trimmed channel, a fully repaired old population and an absent channel all read none - nobody outside is pending is not a waiter aged zero')

    # arm 5: the window is a parameter - the recent dropout moves back inside
    rN8, tN8 = trend30([(SRC30A, OLD30), (SRC30C, MID30), (SRC30E, MID30)],
                       window=14)
    ok('AC-RUN30', tN8['pending_old'] == (1, 1)
       and tN8['pending_old_age_d'] == 91
       and tN8['pending_old_age_min_d'] == 91
       and tN8['pending'] == (1, 2),
       'at fourteen days the recent dropout is in-window pending while the outside population holds one waiter aged 91 - the two populations do not overlap')

    # arm 6: exactly one new key, and none of the refused faces exist
    ok('AC-RUN30', set(tN1.keys()) == baseB | set(['flips', 'pending',
                                                   'pending_src',
                                                   'pending_age_d',
                                                   'pending_age_min_d',
                                                   'pending_age_med_d',
                                                   'pending_old',
                                                   'pending_old_age_d',
                                                   'pending_old_age_min_d',
                                                   'fcov', 'rcov'])
       and 'pending_old_age_med_d' not in tN1
       and 'pending_old_src' not in tN1
       and 'pending_old_hist' not in tN1,
       'the row grows by exactly one age key, and the refused middle, per-source and histogram faces never exist on the row')

    # arm 7: the one-line contract and the scanner's zero-consumption premise
    bufN7 = io.StringIO()
    with contextlib.redirect_stdout(bufN7):
        rcN7 = RUN.main(['--failure-trend', '--root', rN1])
    linesN7 = [n for n in bufN7.getvalue().splitlines() if n.strip()]
    lineN7 = linesN7[0] if linesN7 else ''
    bufN7b = io.StringIO()
    with contextlib.redirect_stdout(bufN7b):
        rcN7b = RUN.main(['--failure-trend', '--root', rN7])
    linesN7b = [n for n in bufN7b.getvalue().splitlines() if n.strip()]
    lineN7b = linesN7b[0] if linesN7b else ''
    ok('AC-RUN30', rcN7 == 0 and len(linesN7) == 1
       and 'pending_old_age_min_d=90' in lineN7
       and rcN7b == 0 and len(linesN7b) == 1
       and 'pending_old_age_min_d=none' in lineN7b
       and 'PASS' not in lineN7 and 'FLAG' not in lineN7
       and 'verdict' not in lineN7 and 'crawl-failure' not in scan_src18,
       'one line carries pending_old_age_min_d= (a number, or none when nothing outside is pending), and the scanner still reads none of it')

    # AC-RUN31 (R3014): with three old waiters the row gave two ends and a
    # count - "which ones" had no face. Measured before the pin
    # (qa/probe-R3014.log): two worlds whose second-oldest waiter was a
    # different source read IDENTICAL on all 30 keys, while the same computation
    # held all three witnesses and returned only the first and last. The list is
    # a SEPARATE read-only face over the SAME predicate.
    SRC31A = 'https://a.example/page'
    SRC31B = 'https://b.example/page'
    SRC31B2 = 'https://b2.example/page'
    SRC31C = 'https://c.example/page'
    SRC31D = 'https://d.example/page'
    SRC31K = 'https://keep.example/page'
    SRC31E = 'https://e.example/page'
    OLD31 = '2026-08-20T10:00:00+08:00'    # 91 days before TODAY
    NXT31 = '2026-08-21T10:00:00+08:00'    # 90 days
    MID31 = '2026-11-10T10:00:00+08:00'    # 9 days
    FIX31 = '2026-11-11T09:00:00+08:00'
    BASE31 = [(SRC31K, TODAY + 'T09:00:00+08:00', 'no-drift'),
              (SRC31E, FIX31, 'no-drift')]

    def world31(failures, records, window=7):
        root = world()
        roots.append(root)
        for url, when, verdict in records:
            CR.append_record(CR.record_path(root), url, when, verdict)
        for url, when in failures:
            RUN.append_failure(RUN.failure_path(root), url, when,
                               'TimeoutError: t')
        write_days(RUN.failure_day_path(root), [])
        trend31 = RUN.summarize_failure_trend(
            RUN.failure_day_path(root), RUN.failure_path(root), TODAY,
            window_days=window, record_path=CR.record_path(root))
        listed31 = RUN.list_pending_old(
            CR.record_path(root), RUN.failure_path(root), TODAY, window)
        return root, trend31, listed31

    def ages31(listed):
        return [w['age_d'] for w in listed['waiting']]

    def urls31(listed):
        return [w['source_url'] for w in listed['waiting']]

    def snapshot31(root):
        out = []
        for base, _dirs, files in os.walk(root):
            for name in files:
                p = os.path.join(base, name)
                out.append((os.path.relpath(p, root).replace('\\', '/'),
                            os.path.getsize(p)))
        out.sort()
        return out

    # arm 1: three waiters, all three named, oldest first - and the row keeps
    # only its two ends (the blindness this round closes)
    rW1, tW1, lW1 = world31([(SRC31A, OLD31), (SRC31B, NXT31), (SRC31C, MID31)],
                            BASE31)
    ok('AC-RUN31', urls31(lW1) == [SRC31A, SRC31B, SRC31C]
       and ages31(lW1) == [91, 90, 9]
       and tW1['pending_old'] == (3, 3)
       and tW1['pending_old_age_d'] == 91
       and tW1['pending_old_age_min_d'] == 9,
       'three old waiters are all named with their ages, while the row still carries only the two ends')

    # arm 2: the list and the row are ONE computation - same count, same ends
    rW3, tW3, lW3 = world31(
        [(SRC31A, OLD31), (SRC31B, NXT31),
         (SRC31D, '2026-09-05T10:00:00+08:00')],
        [(SRC31K, '2026-09-01T09:00:00+08:00', 'no-drift'),
         (SRC31B, '2026-08-22T09:00:00+08:00', 'no-drift')])
    ok('AC-RUN31', lW1['pending_old'] == tW1['pending_old']
       and ages31(lW1)[0] == tW1['pending_old_age_d']
       and ages31(lW1)[-1] == tW1['pending_old_age_min_d']
       and tW3['pending_old'] == (1, 2)
       and lW3['pending_old'] == (1, 2)
       and urls31(lW3) == [SRC31A],
       'the list reports the same fraction and the same two ends the row does - one predicate, not a second truth')

    # arm 3: two worlds the row cannot tell apart, separated by the middle name
    rW2, tW2, lW2 = world31([(SRC31A, OLD31), (SRC31B2, NXT31),
                             (SRC31C, MID31)], BASE31)
    ok('AC-RUN31', json.dumps(tW1, sort_keys=True) == json.dumps(
        tW2, sort_keys=True)
       and urls31(lW1)[1] == SRC31B and urls31(lW2)[1] == SRC31B2
       and ages31(lW1) == ages31(lW2),
       'two worlds identical on every row key are separated by which source the list names in the middle')

    # arm 4: a repaired old source and an unmeasured one are never listed
    rW4, tW4, lW4 = world31(
        [(SRC31B, NXT31)],
        [(SRC31K, TODAY + 'T09:00:00+08:00', 'no-drift'),
         (SRC31B, '2026-08-22T09:00:00+08:00', 'no-drift')])
    ok('AC-RUN31', tW4['pending_old'] == (0, 1)
       and lW4['pending_old'] == (0, 1) and lW4['waiting'] == []
       and SRC31B not in urls31(lW3) and SRC31D not in urls31(lW3),
       'a source that came back, and one the record never looked after, are both absent - judged is not the same as listed')

    # arm 5: no evidence out there answers none with ZERO rows, never 0/0
    rW5, tW5, lW5 = world31([(SRC31C, '2026-11-18T08:00:00+08:00')], BASE31)
    rW6 = world()
    roots.append(rW6)
    lW6 = RUN.list_pending_old(CR.record_path(rW6), RUN.failure_path(rW6),
                               TODAY)
    buf31b = io.StringIO()
    with contextlib.redirect_stdout(buf31b):
        rc31b = RUN.main(['--pending-old-list', '--root', rW6])
    lines31b = [n for n in buf31b.getvalue().splitlines() if n.strip()]
    ok('AC-RUN31', tW5['pending_old'] is None and lW5['waiting'] == []
       and lW5['pending_old'] is None and lW6['waiting'] == []
       and rc31b == 0 and len(lines31b) == 1
       and 'pending_old=none' in lines31b[0],
       'a channel trimmed to the window and an absent channel both answer none with zero rows - and the CLI prints one header line, not a fabricated 0/0')

    # arm 6: deterministic order - same stamp breaks on url, two calls agree
    rW7, _tW7, lW7 = world31([(SRC31B, NXT31), (SRC31A, NXT31)], BASE31)
    lW7b = RUN.list_pending_old(CR.record_path(rW7),
                                RUN.failure_path(rW7), TODAY)
    ok('AC-RUN31', urls31(lW7) == [SRC31A, SRC31B]
       and ages31(lW7) == [90, 90]
       and json.dumps(lW7, sort_keys=True) == json.dumps(lW7b, sort_keys=True),
       'two sources sharing a stamp are ordered by url, and two calls over the same world agree byte for byte')

    # arm 7: a pure display - writes nothing, carries no verdict, and the row
    # still refuses the per-source key
    before31 = snapshot31(rW1)
    buf31 = io.StringIO()
    with contextlib.redirect_stdout(buf31):
        rc31 = RUN.main(['--pending-old-list', '--root', rW1])
    after31 = snapshot31(rW1)
    lines31 = [n for n in buf31.getvalue().splitlines() if n.strip()]
    text31 = ''.join(lines31)
    ok('AC-RUN31', rc31 == 0 and before31 == after31
       and len(lines31) == 4
       and lines31[0].startswith('CRAWL-PENDING-OLD-LIST')
       and 'pending_old=3/3' in lines31[0]
       and all(n.startswith('PENDING-OLD ') for n in lines31[1:])
       and 'pending_old_src' not in tW1
       and 'PASS' not in text31 and 'FLAG' not in text31
       and 'verdict' not in text31
       and 'crawl-failure' not in scan_src18,
       'the face leaves the world byte-identical, prints a header plus one line per waiter, and neither the row nor the scanner learns a per-source key')

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
