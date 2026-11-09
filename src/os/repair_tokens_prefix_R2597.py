"""Heal a round's ledger line that landed without its round label.

Criteria (stated before this module existed, R2597):

AC-RTP1  --check reads the live state log and reports every round that
         carries a round narrative but no ledger line, together with the
         unlabelled 'tokens:' line that would heal it; DIRTY exits 2 and
         writes nothing, CLEAN exits 0.
AC-RTP2  --apply labels ONLY a line whose stripped form begins with
         'tokens: ' AND whose labelled form the shipped classifier reads
         as a ledger line; nothing else is ever rewritten.
AC-RTP3  idempotent: a second --apply reads CLEAN and writes no byte.
AC-RTP4  the write goes through state_io.write_canon and is proved: the
         decoded payload is byte-equal before and after except for that
         one string, and a failed proof leaves the target untouched.
AC-RTP5  refuses E_RTP_AMBIGUOUS when two or more unlabelled tokens lines
         sit in one round block, and refuses E_RTP_HAS_LEDGER when that
         round already carries a ledger line.
AC-RTP6  pure ASCII, standard library only, no network; the only two
         actions are --check and --apply.

Usage:
  python src/os/repair_tokens_prefix_R2597.py --check
  python src/os/repair_tokens_prefix_R2597.py --apply
"""

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import ledger_lines as LL
import state_io as SIO

STATE = os.path.join(HERE, 'state.json')
ROUND_NO_RE = re.compile(r'R(\d{3,5})')
TOKENS_RE = re.compile(r'^tokens:\s')


class RepairError(Exception):
    def __init__(self, code, detail):
        Exception.__init__(self, '%s: %s' % (code, detail))
        self.code = code
        self.detail = detail


def _round_of(line):
    m = ROUND_NO_RE.search(line or '')
    return m.group(1) if m else None


def measure(raw):
    """Return (payload, findings). Findings are dicts, never prose."""
    payload = json.loads(raw.decode('utf-8'))
    log = payload.get('log') or []
    kinds = [LL.classify(x) for x in log]
    rounds = []
    ledgers = []
    for i, line in enumerate(log):
        if kinds[i] == 'round':
            r = _round_of(line)
            if r:
                rounds.append(r)
        elif kinds[i] == 'ledger':
            m = LL.LEDGER_PREFIX_RE.match(line)
            if m:
                ledgers.append(m.group(1))
    missing = [r for r in rounds if r not in ledgers]
    findings = []
    for round_no in sorted(set(missing)):
        candidates = [i for i, line in enumerate(log)
                      if isinstance(line, str) and TOKENS_RE.match(line.strip())
                      and kinds[i] != 'ledger']
        mine = []
        for i in candidates:
            owner = None
            for j in range(i - 1, -1, -1):
                if kinds[j] == 'round':
                    owner = _round_of(log[j])
                    break
                if kinds[j] == 'ledger':
                    break
            if owner == round_no:
                mine.append(i)
        findings.append({'round': round_no, 'items': mine})
    return payload, findings


def repair(payload, findings):
    """Return the new log list, or raise a named refusal."""
    log = list(payload['log'])
    for f in findings:
        round_no = f['round']
        items = f['items']
        if any(LL.LEDGER_PREFIX_RE.match(x) and
               LL.LEDGER_PREFIX_RE.match(x).group(1) == round_no for x in log):
            raise RepairError('E_RTP_HAS_LEDGER', 'R%s' % round_no)
        if len(items) != 1:
            raise RepairError('E_RTP_AMBIGUOUS',
                              'R%s candidates=%d' % (round_no, len(items)))
        i = items[0]
        line = log[i]
        labelled = 'R%s %s' % (round_no, line.lstrip())
        if LL.classify(labelled) != 'ledger':
            raise RepairError('E_RTP_NOT_LEDGER', 'R%s' % round_no)
        log[i] = labelled
    return log


def _literal(value):
    """The exact JSON string literal this document would carry for value."""
    return json.dumps(value, ensure_ascii=False)


def apply(state_path=STATE):
    raw = open(state_path, 'rb').read()
    text = raw.decode('utf-8')
    payload, findings = measure(raw)
    if not findings:
        return {'action': 'apply', 'rounds': 0, 'bytes': len(raw),
                'verdict': 'CLEAN'}
    new_log = repair(payload, findings)
    expect = sorted(i for f in findings for i in f['items'])
    # A text-level literal swap only: the document layout is the writer's
    # business and this repair must not reformat a single other byte.
    new_text = text
    for i in expect:
        old_lit = _literal(payload['log'][i])
        new_lit = _literal(new_log[i])
        if new_text.count(old_lit) != 1:
            raise RepairError('E_RTP_PROOF',
                              'literal occurrences=%d' % new_text.count(old_lit))
        new_text = new_text.replace(old_lit, new_lit, 1)
    before = payload
    after = json.loads(new_text)
    differ = [i for i in range(max(len(before['log']), len(after['log'])))
              if before['log'][i] != after['log'][i]]
    if differ != expect:
        raise RepairError('E_RTP_PROOF',
                          'differ=%r expect=%r' % (differ, expect))
    for key in before:
        if key == 'log':
            continue
        if before[key] != after[key]:
            raise RepairError('E_RTP_PROOF', 'key %s moved' % key)
    tmp = state_path + '.rtp-tmp'
    with open(tmp, 'wb') as fh:
        fh.write(new_text.encode('utf-8'))
    os.replace(tmp, state_path)
    written = open(state_path, 'rb').read()
    if written != new_text.encode('utf-8'):
        raise RepairError('E_RTP_PROOF', 'read-back differs')
    return {'action': 'apply', 'rounds': [f['round'] for f in findings],
            'items': expect, 'bytes': len(written), 'verdict': 'REPAIRED'}


def check(state_path=STATE):
    raw = open(state_path, 'rb').read()
    _payload, findings = measure(raw)
    if not findings:
        return 0, {'verdict': 'CLEAN', 'rounds': 0}
    detail = [{'round': f['round'], 'items': f['items']} for f in findings]
    return 2, {'verdict': 'DIRTY', 'rounds': len(findings),
               'detail': detail}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--state', default=STATE)
    args = ap.parse_args(argv)
    if args.check:
        code, report = check(args.state)
        print(json.dumps(report, ensure_ascii=False))
        return code
    if args.apply:
        try:
            report = apply(args.state)
        except RepairError as exc:
            print(json.dumps({'verdict': 'REFUSED', 'code': exc.code,
                              'detail': exc.detail}, ensure_ascii=False))
            return 3
        print(json.dumps(report, ensure_ascii=False))
        return 0
    print('usage: --check | --apply')
    return 1


if __name__ == '__main__':
    sys.exit(main())