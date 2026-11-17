"""Adjudicate a battery shard leg log: a leg is a measurement only if it CLOSED.

WHY: R2886 pinned the law that a leg carrying no closing `SHARD rc=` row is not
a family measurement. Every window since has applied that law by reading the log
by eye, and a law only a human applies is not a gate - the crit_mismatch=13
number survived twenty-three windows as prose for exactly that reason. This tool
re-derives every aggregate from the per-row lines and refuses the leg when the
closing row, the header, and the rows disagree, so "is this leg admissible"
becomes a command with an exit code instead of a judgement call.

Usage:
    python tools/leg_audit.py <leg.log> [<leg2.log> ...] [--json]

Exit codes: 0 = ADOPT, 2 = REJECT, 3 = unreadable input.
Source discipline: pure ASCII, stdlib only, no clock, no network.
"""
import io
import json
import re
import sys

ROW_RE = re.compile(r'^SHARD row (\S+)\s+(.*)$')
SUITE_RE = re.compile(r'suite=(PASS|FAIL) (\d+)/(\d+)')


def _kv(rest):
    """Parse `k=v` tokens from the tail of a SHARD line; bare tokens are skipped."""
    out = {}
    for tok in rest.split():
        if '=' in tok:
            key, val = tok.split('=', 1)
            out[key] = val
    return out


def _int(d, key):
    """An integer field, or None when absent/unparseable - never a silent zero."""
    raw = d.get(key)
    if raw is None:
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def parse(text):
    """Split a leg log into its header, its rows, its closing row and strays."""
    header = None
    closing = None
    rows = []
    stray = 0
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if not line.startswith('SHARD'):
            stray += 1
            continue
        if line.startswith('SHARD row '):
            m = ROW_RE.match(line)
            if not m:
                stray += 1
                continue
            name, rest = m.group(1), m.group(2)
            pair = SUITE_RE.search(line)
            rows.append({'name': name, 'kv': _kv(rest),
                         'pair': (int(pair.group(2)), int(pair.group(3))) if pair else None})
            continue
        fields = _kv(line[len('SHARD'):])
        if 'row' in fields:
            stray += 1
        elif 'rc' in fields and 'executed' in fields:
            closing = fields
        elif 'selected' in fields and header is None:
            header = fields
        else:
            stray += 1
    return {'header': header, 'rows': rows, 'closing': closing, 'stray': stray}


def audit_text(text):
    """Return {'verdict', 'reasons', 'facts'} for one leg log's text."""
    p = parse(text)
    header, rows, closing = p['header'], p['rows'], p['closing']
    reasons = []

    # A leg is admissible only when it closed. Everything below is subordinate
    # to that: an unfinished leg has no trustworthy aggregate to compare with.
    if closing is None:
        reasons.append('E_NO_CLOSING_ROW')
    if header is None:
        reasons.append('E_NO_HEADER')
    # Older headers carry no state key at all; absence is not a failure, but a
    # header that SAYS it is still running cannot attest a finished leg.
    if header is not None and header.get('state', 'COMPLETE') != 'COMPLETE':
        reasons.append('E_NOT_COMPLETE:%s' % header.get('state'))

    names = [r['name'] for r in rows]
    reds = [r['name'] for r in rows if _int(r['kv'], 'rc') != 0]
    crit_sum = sum(_int(r['kv'], 'crit') or 0 for r in rows)
    green = sum(1 for r in rows if _int(r['kv'], 'rc') == 0)

    if len(set(names)) != len(names):
        dupes = sorted({n for n in names if names.count(n) > 1})
        reasons.append('E_DUPLICATE_SUITE:%s' % ','.join(dupes[:4]))

    # Row shape. NARROWED TWICE ON THE RECORD. The first draft required the pair
    # to equal pass+fail and a green 285-leg reddened SEVENTY legitimate rows.
    # The second draft required PASS to read n/n and two shipped rows still
    # reddened: `suite=PASS 8/6` is a real shape, because the pair prints the
    # suite's OWN claim (assertions over criteria, or passed over total) and the
    # two dialects cannot be told apart from the line. What a row must satisfy is
    # only what the line can actually prove: a FAIL has a short numerator, a PASS
    # has a non-zero one, a rc of 124 with suite=none is a DECLARED timeout red,
    # and rc agrees with the verdict.
    for r in rows:
        kv = r['kv']
        p_, f_ = _int(kv, 'pass'), _int(kv, 'fail')
        rc_ = _int(kv, 'rc')
        verdict = kv.get('suite')
        if p_ is None or f_ is None:
            reasons.append('E_ROW_UNPARSED:%s' % r['name'])
            continue
        if verdict == 'none':
            if kv.get('timeout') != 'yes' or rc_ == 0:
                reasons.append('E_ROW_UNPARSED:%s' % r['name'])
            continue
        if verdict not in ('PASS', 'FAIL'):
            reasons.append('E_ROW_UNPARSED:%s' % r['name'])
            continue
        if (verdict == 'PASS' and f_ != 0) or (verdict == 'FAIL' and f_ == 0):
            reasons.append('E_ROW_VERDICT:%s' % r['name'])
        if rc_ is not None and ((rc_ == 0) != (verdict == 'PASS')):
            reasons.append('E_ROW_RC_VERDICT:%s' % r['name'])
        if r['pair'] is None:
            reasons.append('E_ROW_PAIR_ABSENT:%s' % r['name'])
            continue
        lo, hi = r['pair']
        if hi <= 0 or (verdict == 'PASS' and lo <= 0) or (verdict == 'FAIL' and lo >= hi):
            reasons.append('E_ROW_PAIR_SHAPE:%s' % r['name'])

    if closing is not None:
        c_exec = _int(closing, 'executed')
        c_sel = _int(closing, 'selected')
        c_green = _int(closing, 'green')
        c_crit = _int(closing, 'criteria')
        if c_exec is not None and c_exec != len(rows):
            reasons.append('E_ROW_COUNT:%s!=%d' % (c_exec, len(rows)))
        if c_sel is not None and c_exec is not None and c_sel != c_exec:
            reasons.append('E_PARTIAL:%s!=%s' % (c_sel, c_exec))
        if c_green is not None and c_green != green:
            reasons.append('E_GREEN_COUNT:%s!=%d' % (c_green, green))
        if c_crit is not None and c_crit != crit_sum:
            reasons.append('E_CRITERIA_SUM:%s!=%d' % (c_crit, crit_sum))
        if header is not None:
            if _int(header, 'selected') != c_sel:
                reasons.append('E_SELECTED_DRIFT')
            if _int(header, 'selected_criteria') != c_crit:
                reasons.append('E_SELECTED_CRITERIA_DRIFT')
        # The closing rc must agree with what the rows say: 0 exactly when every
        # row is green and no unit disagreement was reported.
        c_rc = _int(closing, 'rc')
        c_mis = _int(closing, 'crit_mismatch')
        if c_rc is not None:
            clean = (green == len(rows)) and not reds and (c_mis == 0)
            if clean and c_rc != 0:
                reasons.append('E_CLOSING_RC:%s' % c_rc)
            if (not clean) and c_rc == 0 and c_exec == len(rows):
                reasons.append('E_CLOSING_RC_GREEN')

    facts = {
        'rows': len(rows),
        'unique': len(set(names)),
        'green': green,
        'reds': reds,
        'criteria': crit_sum,
        'selected': _int(closing, 'selected') if closing else None,
        'executed': _int(closing, 'executed') if closing else None,
        'crit_mismatch': _int(closing, 'crit_mismatch') if closing else None,
        'elapsed': closing.get('elapsed') if closing else None,
        'registry_suites': _int(header, 'registry_suites') if header else None,
        'stray': p['stray'],
    }
    # R2913 AC-LGA7: "unfinished" and "inconsistent" are two different facts and
    # a reader deciding whether to quote a number needs to tell them apart. A leg
    # that never wrote its closing row has no aggregate at all - every row it did
    # print can be green and the run is still not a measurement (the killed R2912
    # launch: 89 rows, 89 green, no closing row). A leg that DID close but whose
    # counts disagree is a different failure: it measured, and the arithmetic is
    # broken. `verdict` keeps its old two values so every pre-R2913 consumer reads
    # the same thing; `cls` is the new discriminator.
    if not reasons:
        cls = 'ADOPT'
    elif closing is None:
        cls = 'FAILED-LAUNCH'
    else:
        cls = 'REJECT'
    return {
        'verdict': 'REJECT' if reasons else 'ADOPT',
        'cls': cls,
        'reasons': reasons,
        'facts': facts,
    }


def render(path, result):
    """One line, in the same shape the leg itself prints.

    R2913: the leading token is the CLASS (ADOPT / REJECT / FAILED-LAUNCH), so a
    killed launch can no longer be skim-read as a green one. `LEG-AUDIT ADOPT`
    and `LEG-AUDIT REJECT` keep their exact pre-R2913 spelling.
    """
    f = result['facts']
    reasons = result['reasons']
    named = ','.join(reasons[:6])
    if len(reasons) > 6:
        named += ',+%d-more' % (len(reasons) - 6)
    return ('LEG-AUDIT %s file=%s rows=%d unique=%d selected=%s executed=%s '
            'green=%d crit=%d mismatch=%s elapsed=%s reds=%d reasons=%s'
            % (result.get('cls', result['verdict']), path, f['rows'], f['unique'],
               f['selected'], f['executed'], f['green'], f['criteria'],
               f['crit_mismatch'], f['elapsed'], len(f['reds']), named or 'none'))


def main(argv):
    paths = [a for a in argv if not a.startswith('-')]
    as_json = '--json' in argv
    if not paths:
        print('usage: leg_audit.py <leg.log> [...] [--json]')
        return 3
    report = []
    worst = 0
    for path in paths:
        try:
            text = io.open(path, 'r', encoding='utf-8-sig', errors='replace').read()
        except OSError as exc:
            report.append({'file': path, 'verdict': 'REJECT',
                           'reasons': ['E_UNREADABLE:%s' % exc]})
            worst = max(worst, 3)
            continue
        result = audit_text(text)
        result['file'] = path
        report.append(result)
        if result['verdict'] != 'ADOPT':
            worst = max(worst, 2)
        if not as_json:
            print(render(path, result))
    if as_json:
        print(json.dumps(report, indent=1, sort_keys=True))
    return worst


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
