#!/usr/bin/env python3
"""fold_caliber_check — the log-item indent caliber measured from the document.

WHY THIS FILE EXISTS (measured at R2745, prescribed at R2746, built at R2746)

Two shipped tools disagree about what a healthy state.json log block looks like:

  * state_io.write_document emits log items at TWO spaces and calls the file
    CANON-CLEAN (off_indent=0).
  * logs_toolkit.split_ps_layout demands EXACTLY SIXTEEN spaces on every item
    line (a bare `^ {16}"` gate) and cmd_fold hardcodes its inserted summary
    literal at sixteen, while eol_profile scores every non-sixteen item line
    as indent_anomaly.

So on the real canonical document `logs_toolkit fold` refuses with
E_STATE_LAYOUT, and the shipped hint `eol --fix-indent` would rewrite the file
to sixteen spaces, which state_io then reads as CANON-DRIFT off_indent=88 -
the exact drift R2744 measured and rolled back.

THE REPAIR, PER THE R2746 BOARD LINE: derive the caliber FROM THE DOCUMENT.
A block whose item lines are uniformly TWO spaces is canonical and healthy; a
block uniformly at SIXTEEN is the legacy caliber and stays accepted; anything
uniform-but-other (eight, four, zero) is refused, and a mixed block is refused,
so the existing AC-LF1 / AC-FI5 gates keep gating.

This module is the read side of that repair: pure functions plus a CLI that
answers, for any document, what caliber it uses, whether the shipped gate would
accept it, whether eol would call it healthy, and what indent a summary literal
must carry. It never writes. The next window can wire its own gates onto these
functions instead of re-deriving the answer.

ASCII only. No clock, no network, no shell.
"""

import json
import os
import re
import sys

CALIBER_CANONICAL = 2
CALIBER_LEGACY = 16
ACCEPTED = (CALIBER_CANONICAL, CALIBER_LEGACY)

E_NO_LOG_BLOCK = 'E_FCB_NO_LOG_BLOCK'
E_MIXED = 'E_FCB_MIXED_INDENT'
E_OTHER = 'E_FCB_UNACCEPTED_INDENT'
E_NO_ITEMS = 'E_FCB_EMPTY_BLOCK'

LEGACY_GATE = re.compile(r'^ {16}"')


def split_lines(text):
    """Split on CRLF or LF (the shipped gate split on CRLF alone)."""
    return re.split(r'\r\n|\n', text)


def is_close_line(line):
    """A log-array close line: `]` alone, or `],` when a sibling key follows.

    The canonical document closes its log array with `  ],` because another key
    follows it, while the shipped gates compare `strip() == ']'` and therefore
    never see the close at all. That is the third facet of the same defect and
    it is why eol_profile counted 99 lines as items on a 98-item log.
    """
    s = line.strip()
    if s.endswith(','):
        s = s[:-1].rstrip()
    return s == ']'


def find_log_block(lines):
    """Index of the '"log": [' opening line, or None."""
    for i, ln in enumerate(lines):
        s = ln.strip()
        if s.startswith('"log"') and s.endswith('['):
            return i
    return None


def item_span(lines, log_start):
    """(first_item_idx, close_idx, item_idx_list) for the log array."""
    items, close_idx = [], None
    for j in range(log_start + 1, len(lines)):
        if is_close_line(lines[j]):
            close_idx = j
            break
        if not lines[j].strip():
            continue
        items.append(j)
    return items, close_idx


def indent_of(line):
    return len(line) - len(line.lstrip(' '))


def detect_caliber(text):
    """Measure the log-item indent caliber FROM THE DOCUMENT.

    Returns a dict: ok, caliber, codes, item_lines, indents, log_start.
    """
    lines = split_lines(text)
    log_start = find_log_block(lines)
    out = {'ok': False, 'caliber': None, 'codes': [], 'item_lines': 0,
           'indents': [], 'log_start': log_start}
    if log_start is None:
        out['codes'].append(E_NO_LOG_BLOCK)
        return out
    items, close_idx = item_span(lines, log_start)
    out['item_lines'] = len(items)
    if not items or close_idx is None:
        out['codes'].append(E_NO_ITEMS)
        return out
    indents = sorted({indent_of(lines[i]) for i in items})
    out['indents'] = indents
    if len(indents) > 1:
        out['codes'].append(E_MIXED)
        return out
    caliber = indents[0]
    if caliber not in ACCEPTED:
        out['codes'].append(E_OTHER)
        return out
    out['caliber'] = caliber
    out['ok'] = True
    return out


def shipped_gate_verdict(text, log_len):
    """Reproduce logs_toolkit.split_ps_layout's decision without importing it.

    Mirrored faithfully, quirks included, so the refusal is reported truthfully:
    it splits on CRLF only, demands `^ {16}"` on every item line, and treats a
    line as the close only when `strip() == ']'` - which the canonical `  ],`
    never matches.
    """
    lines = text.split('\r\n')
    log_start = find_log_block(lines)
    if log_start is None:
        return {'accepts': False, 'reason': E_NO_LOG_BLOCK}
    items = 0
    for j in range(log_start + 1, len(lines)):
        if lines[j].strip() == ']':
            return {'accepts': items == log_len,
                    'reason': 'count-match' if items == log_len
                              else 'count-mismatch %d!=%d' % (items, log_len)}
        if not re.match(r'^ {16}"', lines[j]):
            return {'accepts': False, 'reason': 'indent-gate-16'}
        items += 1
    return {'accepts': False, 'reason': 'no-close-literal-bracket'}


def generalized_gate_verdict(text, log_len):
    """The prescribed gate: the item indent comes from the document."""
    measured = detect_caliber(text)
    if not measured['ok']:
        return {'accepts': False, 'reason': measured['codes'][0],
                'caliber': measured['caliber']}
    lines = split_lines(text)
    items, _ = item_span(lines, measured['log_start'])
    if len(items) != log_len:
        return {'accepts': False,
                'reason': 'count-mismatch %d!=%d' % (len(items), log_len),
                'caliber': measured['caliber']}
    return {'accepts': True, 'reason': 'caliber-%d' % measured['caliber'],
            'caliber': measured['caliber']}


def eol_health(text):
    """eol_profile's indent face, taught both accepted calibers.

    Healthy means: a log block exists, every item line carries the SAME
    indent, and that indent is 2 (canonical) or 16 (legacy).
    """
    measured = detect_caliber(text)
    if not measured['ok'] and measured['codes'] == [E_NO_LOG_BLOCK]:
        return {'indent_ok': True, 'caliber': None, 'item_lines': 0,
                'codes': [E_NO_LOG_BLOCK],
                'note': 'no log block: nothing to score (shipped behaviour)'}
    return {'indent_ok': measured['ok'], 'caliber': measured['caliber'],
            'item_lines': measured['item_lines'], 'codes': measured['codes'],
            'indents': measured['indents']}


def render_summary_literal(caliber, escaped_summary, trailing_comma=False):
    """The literal cmd_fold inserts, at the caliber the document measured.

    Takes an ALREADY-ESCAPED body (logs_toolkit.ps_escape) so this module owns
    the indent decision and nothing else.
    """
    literal = ' ' * caliber + escaped_summary
    if trailing_comma:
        literal += ','
    return literal


def measure_text(text, log_len=None):
    """One flat report for a document."""
    measured = detect_caliber(text)
    report = {'caliber': measured['caliber'], 'codes': measured['codes'],
              'item_lines': measured['item_lines'], 'ok': measured['ok'],
              'indents': measured['indents'],
              'eol': eol_health(text)}
    if log_len is not None:
        report['shipped_gate'] = shipped_gate_verdict(text, log_len)
        report['generalized_gate'] = generalized_gate_verdict(text, log_len)
        report['summary_literal_prefix_spaces'] = measured['caliber']
    return report


def read_state(root):
    path = os.path.join(root, 'src', 'os', 'state.json')
    with open(path, 'rb') as handle:
        raw = handle.read()
    text = raw.decode('utf-8')
    payload = json.loads(text)
    return path, raw, text, payload


def main(argv):
    root = '.'
    as_json = False
    rest = list(argv)
    while rest:
        flag = rest.pop(0)
        if flag == '--root':
            if not rest:
                return 2
            root = rest.pop(0)
        elif flag == '--json':
            as_json = True
        elif flag == '--check':
            continue
        else:
            return 2
    try:
        path, raw, text, payload = read_state(root)
    except (IOError, OSError) as exc:
        print('E_FCB_READ %s' % exc)
        return 3
    report = measure_text(text, len(payload.get('log') or []))
    report['path'] = path
    report['bytes'] = len(raw)
    report['bom'] = raw[:3] == b'\xef\xbb\xbf'
    report['crlf'] = raw.count(b'\r\n')
    report['bare_lf'] = raw.count(b'\n') - raw.count(b'\r\n')
    if as_json:
        print(json.dumps(report, sort_keys=True))
        return 0
    print('FOLD CALIBER caliber=%s ok=%s item_lines=%d indents=%s'
          % (report['caliber'], report['ok'], report['item_lines'],
             report['indents']))
    print('  eol indent_ok=%s' % report['eol']['indent_ok'])
    print('  shipped_gate accepts=%s (%s)'
          % (report['shipped_gate']['accepts'],
             report['shipped_gate']['reason']))
    print('  generalized_gate accepts=%s (%s)'
          % (report['generalized_gate']['accepts'],
             report['generalized_gate']['reason']))
    print('  summary literal must carry %s spaces'
          % report['generalized_gate']['caliber'])
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
