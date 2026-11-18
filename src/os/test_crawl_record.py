"""Battery suite for tools/crawl_record.py (R2990).

WHY: the five-still scanner's [QA] limb used to judge a day's crawl by the mtime
of qa/smoke-*.png and qa/smoke-*.log. Measured 2026-11-19: those files are round
evidence, and one of them was a suite payload - so the limb could read PASS on a
day with no crawl. The record module exists so the limb can read a declaration
with three named fields instead of a filename; this suite grades the machinery
that makes the declaration readable and the absence visible.

PINNED BEFORE THE CODE: AC-CR1..AC-CR4 were written into src/os/backlog.md in
this same window, BEFORE crawl_record.py existed (in-window pre-registration,
disclosed as such).

Scope, stated honestly: this suite grades the reader/writer laws, not the crawl.
It cannot prove a URL was fetched - that is the point of the module docstring.
Stdlib only, no network, no clock of its own (today is passed in), and every
write lands in a per-run temp directory, never in qa/.
"""
import json
import os
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'tools'))

import crawl_record as CR

FAILS = []
CHECKS = []
TODAY = '2026-11-19'
YESTERDAY = '2026-11-18'


def ok(name, cond, detail=''):
    CHECKS.append(name)
    if cond:
        print('  | PASS %s %s' % (name, detail))
    else:
        FAILS.append(name)
        print('  | FAIL %s %s' % (name, detail))


def world():
    return tempfile.mkdtemp(prefix='bd_crawlrec_')


def write_lines(path, lines):
    parent = os.path.dirname(path)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent)
    with open(path, 'w', encoding='utf-8', newline='\n') as fh:
        for line in lines:
            fh.write(line + '\n')


def good_row(day=TODAY, url='https://pay.weixin.qq.com/doc/v2/merchant/4011986682'):
    return {'source_url': url, 'fetched_at': day + 'T09:10:00+08:00', 'verdict': 'no-drift'}


def main():
    roots = []

    # AC-CR1: the shipped writer appends one JSONL line that the shipped reader
    # reads back with all three fields intact.
    root = world(); roots.append(root)
    path = CR.record_path(root)
    row = CR.append_record(path, 'https://www.gov.cn/zhengce/content/x.htm',
                           TODAY + 'T07:20:00+08:00', 'new-source', note='charter W1')
    with open(path, 'r', encoding='utf-8') as fh:
        lines = [ln for ln in fh.read().split('\n') if ln.strip()]
    rows, bad = CR.read_records(path)
    ok('AC-CR1', len(lines) == 1 and len(rows) == 1 and bad == 0
       and all(k in rows[0] for k in CR.FIELDS) and rows[0]['verdict'] == 'new-source',
       'one line on disk, three fields back, bad=0')
    ok('AC-CR1', CR.record_path(root) == path and path.replace('\\', '/').endswith('qa/crawl-log.jsonl'),
       'record path is qa/crawl-log.jsonl under the given root')
    ok('AC-CR1', row['note'] == 'charter W1', 'the optional note rides along')

    # AC-CR2: a row the reader cannot use is counted bad and NEVER counts as
    # today - including the two shapes a careless writer would emit. The shipped
    # writer must refuse the same shapes rather than let them reach the file.
    root = world(); roots.append(root)
    path = CR.record_path(root)
    no_url = {'fetched_at': TODAY + 'T09:00:00+08:00', 'verdict': 'no-drift'}
    bad_date = {'source_url': 'https://a.example/x', 'fetched_at': '19/11/2026', 'verdict': 'no-drift'}
    no_verdict = {'source_url': 'https://a.example/x', 'fetched_at': TODAY + 'T09:00:00+08:00', 'verdict': '  '}
    write_lines(path, [json.dumps(no_url), json.dumps(bad_date), json.dumps(no_verdict)])
    summary = CR.today_summary(path, TODAY)
    ok('AC-CR2', summary['today'] == 0 and summary['bad'] == 3 and summary['rows'] == 0,
       'three unusable rows read today=0 bad=3')
    ok('AC-CR2', CR.missing_fields(no_url) == ['source_url']
       and CR.missing_fields(bad_date) == ['fetched_at']
       and CR.missing_fields(no_verdict) == ['verdict'],
       'each defect names its own field')
    refused = 0
    for build in (
        lambda: CR.append_record(path, 'ftp://a.example/x', TODAY + 'T09:00:00+08:00', 'no-drift'),
        lambda: CR.append_record(path, 'https://a.example/x', '', 'no-drift'),
        lambda: CR.append_record(path, 'https://a.example/x', TODAY + 'T09:00:00+08:00', ''),
    ):
        try:
            build()
        except ValueError:
            refused += 1
    ok('AC-CR2', refused == 3, 'the writer refuses the three shapes the reader calls bad')

    # AC-CR3: a malformed line is counted, does not raise, and does not swallow
    # the good rows around it.
    root = world(); roots.append(root)
    path = CR.record_path(root)
    write_lines(path, [json.dumps(good_row()), '{"source_url": "https://a.example/x", ', json.dumps(good_row())])
    summary = CR.today_summary(path, TODAY)
    ok('AC-CR3', summary['rows'] == 2 and summary['today'] == 2 and summary['bad'] == 1,
       'a truncated line reads bad=1 with both good rows kept')
    ok('AC-CR3', CR.read_records(os.path.join(root, 'qa', 'absent.jsonl')) == ([], 0),
       'a missing file is zero rows and zero bad lines, not an exception')

    # AC-CR4: "today" is the literal calendar day carried in fetched_at, so a
    # yesterday row cannot colour today's answer.
    root = world(); roots.append(root)
    path = CR.record_path(root)
    CR.append_record(path, 'https://a.example/y', YESTERDAY + 'T23:50:00+08:00', 'no-drift')
    CR.append_record(path, 'https://a.example/t', TODAY + 'T00:10:00+08:00', 'drift')
    summary = CR.today_summary(path, TODAY)
    ok('AC-CR4', summary['rows'] == 2 and summary['today'] == 1
       and summary['last'] is not None and summary['last']['verdict'] == 'drift',
       'yesterday plus today reads today=1 and names the day\'s own verdict')
    ok('AC-CR4', CR.today_summary(path, YESTERDAY)['today'] == 1,
       'the same file answers yesterday=1, so the day filter is not a constant')

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
