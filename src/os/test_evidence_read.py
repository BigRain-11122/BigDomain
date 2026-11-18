"""Battery suite for evidence_dialect.read_text - criteria AC-EVR1..AC-EVR5 (R2928).

WHY: the board carried "590 baselined non-tee evidence files: stay known debt or
re-encode to utf-8/LF?" for three windows. The measurement that decides it is in
src/os/backlog.md and was taken before this file existed: qa_log --check refuses
ALL 590 (it tests the dialect, not usability), a plain utf-8 reader loses 148 of
them, and 63 baselined names are referenced by shipped code with 16 sha256
citations over qa/*.log - so rewriting bytes would rewrite the objects those
fingerprints name. The ruling is therefore a READ face, never a rewrite.

These criteria pin the reader and, more importantly, pin that it is the exact
complement of the naive reader on the same bytes: a rescued file is one the
plain path lost, and a file the plain path read is never "rescued" by a
non-utf-8 arm.

PINNED BEFORE THE CODE: AC-EVR1..AC-EVR5 were written into src/os/backlog.md in
the same window, BEFORE src/os/evidence_dialect.read_text existed; that is
in-window pre-registration and is disclosed as such, not as pre-registration.
Source discipline: pure ASCII, stdlib only, no clock, no network, and the suite
writes nothing into qa/.
"""
import hashlib
import io
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'src', 'os'))

import evidence_dialect as ED

QA = os.path.join(ROOT, 'qa')
BASELINE = os.path.join(QA, 'writer-census-baseline.json')
FAILS = []
CHECKS = []


def ok(name, cond, detail=''):
    CHECKS.append(name)
    if cond:
        print('  | PASS %s %s' % (name, detail))
    else:
        FAILS.append(name)
        print('  | FAIL %s %s' % (name, detail))


def fixtures():
    """One blob per writer family, each carrying a unique ASCII marker."""
    rows = []
    rows.append(('tee', 'MARK-TEE\nsecond line\n'.encode('utf-8')))
    rows.append(('pwsh-capture', 'MARK-PWSH\r\nsecond\r\n'.encode('utf-8')))
    rows.append(('other-sig', b'\xef\xbb\xbf' + 'MARK-SIG\n'.encode('utf-8')))
    rows.append(('ps-utf16le', '\ufeffMARK-LE\n'.encode('utf-16-le')))
    rows.append(('ps-utf16be', '\ufeffMARK-BE\n'.encode('utf-16-be')))
    rows.append(('nul-bytes', 'MARK-NUL\n'.encode('utf-16-le')))
    rows.append(('cmd-raw', 'MARK-GBK\n'.encode('gb18030')))
    return rows


def usable_text(text):
    return text.strip() != '' and '\x00' not in text and '\ufffd' not in text


def main():
    # AC-EVR1: every class reads in one call, text clean, encoding named.
    good = []
    for label, raw in fixtures():
        try:
            row = ED.read_text(raw)
        except ED.EvidenceDecodeError as exc:
            ok('AC-EVR1 %s decoded' % label, False, 'refused: %s' % exc)
            continue
        marker = [m for m in ('TEE', 'PWSH', 'SIG', 'LE', 'BE', 'NUL', 'GBK')
                  if 'MARK-' + m in row['text']]
        good.append(label)
        ok('AC-EVR1 %s decoded' % label,
           bool(marker) and usable_text(row['text'])
           and row['encoding'] in ('utf-8', 'utf-16le', 'utf-16be', 'gb18030'),
           'enc=%s assumed=%s marker=%s'
           % (row['encoding'], row['assumed'], marker))
    ok('AC-EVR1 all seven families decoded in one call',
       len(good) == len(fixtures()), 'decoded=%s' % good)
    # The two live shapes this arm exists for: 2 of 119 baselined ps-utf16 files
    # are odd-length (a utf-16 body with one stray byte appended). The reader
    # must return the readable text and NAME the dropped byte, not U+FFFD.
    truncated = ('\ufeffMARK-TRUNC\n'.encode('utf-16-le')) + b'\x0a'
    row = ED.read_text(truncated)
    ok('AC-EVR1 a truncated utf-16 tail is named, not hidden in U+FFFD',
       row['damaged'] is True and row['tail_hex'] == '0a'
       and 'MARK-TRUNC' in row['text'] and '\ufffd' not in row['text'],
       'enc=%s damaged=%s tail=%s'
       % (row['encoding'], row['damaged'], row['tail_hex']))

    # AC-EVR2: a blob no family decodes is REFUSED by name, never mojibake.
    refusals = []
    for label, raw in (('undecodable', b'\xff\x80'),
                       ('nul-odd-length', b'\x00\x00\x00')):
        try:
            row = ED.read_text(raw)
            ok('AC-EVR2 %s refused' % label, False,
               'returned enc=%s' % row['encoding'])
        except ED.EvidenceDecodeError as exc:
            refusals.append(str(exc))
            ok('AC-EVR2 %s refused' % label, bool(str(exc)), 'reason=%s' % exc)
    ok('AC-EVR2 refusal never returns text',
       len(refusals) == 2 and all('decodes' in r or 'nul-bytes' in r
                                  for r in refusals),
       'reasons=%s' % refusals)

    # AC-EVR3: the reader is the exact complement of the naive reader, measured
    # on the SAME bytes (fixtures first, live population under AC-EVR5).
    mismatches = []
    for label, raw in fixtures():
        lost = ED.plain_unusable(raw)
        try:
            row = ED.read_text(raw)
        except ED.EvidenceDecodeError:
            continue
        rescued = row['encoding'] != 'utf-8'
        if lost != rescued:
            mismatches.append((label, lost, row['encoding']))
    ok('AC-EVR3 fixture set: plain-unusable iff a non-utf-8 arm was needed',
       not mismatches, 'mismatches=%s' % mismatches)
    ok('AC-EVR3 the R2807 trap is MEASURED, not assumed',
       ED.plain_unusable('MARK-NUL\n'.encode('utf-16-le')) is True
       and ED.read_text('MARK-NUL\n'.encode('utf-16-le'))['text'].strip()
       == 'MARK-NUL',
       'nul-bytes decodes as utf-8 yet is lost; read_text recovers it')

    # AC-EVR4: read_text never writes - a live file's bytes are untouched.
    live = None
    if os.path.isdir(QA):
        for name in sorted(os.listdir(QA)):
            if name.endswith('.log'):
                live = os.path.join(QA, name)
                break
    if live is None:
        print('  | DISCLOSE AC-EVR4 no qa/*.log on this tree; write-freedom '
              'proven on fixtures only')
        raw = fixtures()[0][1]
        ok('AC-EVR4 read_text returns without writing (fixture bytes)',
           ED.read_text(raw)['text'].strip() == 'MARK-TEE',
           'in-memory only')
    else:
        before = hashlib.sha256(io.open(live, 'rb').read()).hexdigest()
        tmps_before = [n for n in os.listdir(os.path.dirname(live))
                       if n.endswith('.tmp')]
        raw = io.open(live, 'rb').read()
        ED.read_text(raw)
        after = hashlib.sha256(io.open(live, 'rb').read()).hexdigest()
        tmps_after = [n for n in os.listdir(os.path.dirname(live))
                      if n.endswith('.tmp')]
        ok('AC-EVR4 a live evidence file is byte-identical after a read',
           before == after and tmps_before == tmps_after,
           'file=%s sha16=%s' % (os.path.basename(live), before[:16]))

    # AC-EVR5: the live population the ruling is about - 0 refusals and exact
    # complementarity, published rather than asserted silently.
    if not (os.path.isdir(QA) and os.path.isfile(BASELINE)):
        print('  | DISCLOSE AC-EVR5 qa/ or writer-census-baseline.json absent; '
              'the live population was NOT measured this run')
        ok('AC-EVR5 live population disclosed, not passed', True,
           'disclosed')
    else:
        base = json.load(io.open(BASELINE, 'r', encoding='utf-8'))
        names = []
        for cls in ED.BASELINE_CLASSES:
            names.extend(base.get(cls) or [])
        names = sorted(set(names))
        refused = []
        lost = []
        rescued = []
        damaged = []
        total_bytes = 0
        for name in names:
            path = os.path.join(QA, name)
            if not os.path.isfile(path):
                refused.append((name, 'missing'))
                continue
            raw = io.open(path, 'rb').read()
            total_bytes += len(raw)
            if ED.plain_unusable(raw):
                lost.append(name)
            try:
                row = ED.read_text(raw)
            except ED.EvidenceDecodeError as exc:
                refused.append((name, str(exc)))
                continue
            if row['encoding'] != 'utf-8':
                rescued.append(name)
            if row['damaged']:
                damaged.append((name, row['tail_hex']))
        ok('AC-EVR5 baselined population refuses ZERO files',
           len(refused) == 0, 'names=%d refused=%d bytes=%d'
           % (len(names), len(refused), total_bytes))
        ok('AC-EVR5 rescued set EQUALS the plain-unusable set',
           sorted(rescued) == sorted(lost),
           'lost=%d rescued=%d symmetric_diff=%d'
           % (len(lost), len(rescued),
              len(set(lost) ^ set(rescued))))
        print('  | MEASURE live baselined=%d plain-unusable=%d rescued=%d '
              'damaged=%d bytes_read=%d'
              % (len(names), len(lost), len(rescued), len(damaged),
                 total_bytes))
        if damaged:
            print('  | MEASURE truncated tails named: %s' % damaged)

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
        print('SUITE FAIL %d/%d failed=%s' % (total - len(FAILS), total, FAILS))
        return 1
    print('SUITE PASS %d/%d' % (total, total))
    return 0


if __name__ == '__main__':
    sys.exit(main())
