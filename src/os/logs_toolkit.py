#!/usr/bin/env python3
"""logs_toolkit.py - BigDomain OSLoop logs/ toolchain reuse + hygiene.

Consolidates the mechanical pieces historically rewritten as one-off
scripts each fold round (water gauge, log-tail inventory, catalog token
extraction with zero-loss presence check) plus logs/ retention
enforcement (dry-run default).

Calibers (R1580 fold precedent):
  - content byte sums are UTF-8; waterline gate = 78500B disk size
    (P-2026-09-25-18 chain);
  - token regex = R1580 PAT (AC/BD/C/D/O/P/T/XL/OH/R families);
  - archive .md files and *.lock are PROTECTED classes: never deletable,
    even when a name also matches a prune class;
  - mtime floor: files modified within --floor-seconds (default 1800)
    are never deleted (in-flight writer protection).

Subcommands (all accept --root, default = repo root two levels up):
  gauge                  water report for src/os/state.json
  inventory              logs/ class breakdown (counts + MB)
  tail [-n N]            state.json log tail inventory (class + bytes)
  prune [--execute]      retention enforcement (dry-run default)
  catalog                window token extraction + presence check
                         (--tail N | --window-file F) --roll-file R
  fold                   state.json fold surgery (pre-op backup +
                         verbatim archive append + text-surgical log
                         window replacement, verify-then-write; window =
                         last --window-tail N log lines, mid-array
                         windows stay manual per precedent)
  census                 archive reverse reconciliation (read-only):
                         section integrity (declared vs actual lines),
                         live-log section pointer resolution, and the
                         informational token census (not_embedded /
                         roll_native / archive_only)

Fold targets the canonical on-disk PS 5.1 serialization (CRLF, 4-space
indent, two spaces after colon, 16-space log items, 12-space closing
bracket) and refuses any other layout (fail-closed E_STATE_LAYOUT).

Exit codes: 0 pass, 2 fail/unknown subcommand, 3 IO error.
Source is ASCII-only per encoding law; stdlib only; zero network.
"""

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
import time
from datetime import datetime, timezone, timedelta

CST = timezone(timedelta(hours=8))
GATE = 78500
PAT = re.compile(r'(?:AC|BD|C|D|O|P|T|XL|OH|R)-[0-9A-Za-z][0-9A-Za-z]*(?:-[0-9A-Za-z]+)*')

# prune classes -> keep-newest counts (retention policy, R1686 AC-LT4)
PRUNE_KEEP = {'tmp-script': 60, 'preop-bak': 12, 'round-transcript': 300}
DEFAULT_FLOOR = 1800
# launcher transcript family has two naming forms: round_<ts>.out/.err and
# run_<ts>.log (first live run discovered the run_*.log family miss)
TRANSCRIPT_RE = re.compile(r'^(round|run)_.*\.(out|err|log)$')


def default_root():
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def ser_state(st):
    return json.dumps(st, ensure_ascii=False, indent=2) + '\n'


def classify(name):
    """Classify a logs/ filename. Returns class tag."""
    if 'state-log-archive' in name or name.endswith('.md'):
        return 'archive-md'
    if name.endswith('.lock'):
        return 'lock'
    if name.startswith('state-preop-') and name.endswith('.bak'):
        return 'preop-bak'
    if name.startswith('tmp_') or name.startswith('tmp-'):
        return 'tmp-script'
    if TRANSCRIPT_RE.match(name):
        return 'round-transcript'
    return 'other'


def classify_log_line(line):
    """Classify a state.json log entry for tail inventory."""
    if 'tokens:' in line:
        return 'tokens'
    if re.match(r'^\d{4}-\d{2}-\d{2}\uff08', line):
        return 'roll-window'
    if 'no-pullable' in line or 'waiting' in line:
        return 'declaration'
    return 'round-main'


def load_state(root):
    path = os.path.join(root, 'src', 'os', 'state.json')
    with open(path, 'rb') as f:
        raw = f.read()
    st = json.loads(raw.decode('utf-8'))
    return path, raw, st


def cmd_gauge(args):
    path, raw, st = load_state(args.root)
    disk = os.path.getsize(path)
    content = sum(len(x.encode('utf-8')) for x in st['log'])
    out = {
        'state_path': path,
        'disk_bytes': disk,
        'gate': GATE,
        'log_lines': len(st['log']),
        'log_content_bytes': content,
        'margin_bytes': GATE - disk,
        'fold_needed': disk > GATE,
        'tick': st.get('tick'),
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def cmd_inventory(args):
    d = os.path.join(args.root, 'logs')
    stats = {}
    for entry in os.scandir(d):
        if not entry.is_file():
            continue
        c = classify(entry.name)
        s = stats.setdefault(c, {'count': 0, 'bytes': 0})
        s['count'] += 1
        try:
            s['bytes'] += entry.stat().st_size
        except OSError:
            pass
    out = {'logs_dir': d, 'classes': {}}
    total = 0
    for c in sorted(stats):
        s = stats[c]
        total += s['count']
        out['classes'][c] = {
            'count': s['count'], 'mb': round(s['bytes'] / 1048576.0, 2),
            'protected': c in ('archive-md', 'lock') or c == 'other',
            'prunable': c in PRUNE_KEEP,
        }
    out['total_files'] = total
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def cmd_tail(args):
    _, _, st = load_state(args.root)
    lines = st['log'][-args.n:]
    base = len(st['log']) - len(lines)
    for i, line in enumerate(lines):
        print(json.dumps({
            'index': base + i,
            'class': classify_log_line(line),
            'utf8_bytes': len(line.encode('utf-8')),
            'head': line[:60],
        }, ensure_ascii=False))
    return 0


def prune_plan(root, floor):
    """Compute the prune plan. Returns (plan, notes).

    plan: {class: [paths to delete]} ; files beyond keep-newest, excluding
    protected names and files newer than the mtime floor.
    """
    d = os.path.join(root, 'logs')
    now = time.time()
    buckets = {c: [] for c in PRUNE_KEEP}
    notes = {'floor_skipped': 0, 'protected_skipped': 0}
    for entry in os.scandir(d):
        if not entry.is_file():
            continue
        name = entry.name
        c = classify(name)
        if c not in PRUNE_KEEP:
            continue
        if 'state-log-archive' in name or name.endswith('.md') or name.endswith('.lock'):
            notes['protected_skipped'] += 1
            continue
        try:
            mtime = entry.stat().st_mtime
        except OSError:
            continue
        if (now - mtime) < floor:
            notes['floor_skipped'] += 1
            continue
        buckets[c].append((mtime, os.path.join(d, name)))
    plan = {}
    for c, items in buckets.items():
        items.sort(reverse=True)  # newest first
        victims = [p for _, p in items[PRUNE_KEEP[c]:]]
        if victims:
            plan[c] = victims
    return plan, notes


def cmd_prune(args):
    plan, notes = prune_plan(args.root, args.floor_seconds)
    total = sum(len(v) for v in plan.values())
    summary = {c: len(v) for c, v in sorted(plan.items())}
    print(json.dumps({
        'mode': 'execute' if args.execute else 'dry-run',
        'policy': {'keep_newest': PRUNE_KEEP, 'floor_seconds': args.floor_seconds},
        'to_delete': summary,
        'to_delete_total': total,
        **notes,
    }, ensure_ascii=False, indent=2))
    if not args.execute:
        return 0
    deleted = {}
    failed = 0
    for c, paths in plan.items():
        n = 0
        for p in paths:
            try:
                os.remove(p)
                n += 1
            except OSError:
                failed += 1
        if n:
            deleted[c] = n
    actual_total = sum(deleted.values())
    mismatch = [c for c in summary if deleted.get(c, 0) != summary[c]]
    print(json.dumps({
        'deleted': deleted, 'deleted_total': actual_total,
        'failed': failed, 'predicted_total': total,
        'prediction_match': not mismatch and actual_total == total,
        'mismatch_classes': mismatch,
    }, ensure_ascii=False, indent=2))
    if mismatch or actual_total != total:
        return 2
    return 0


def cmd_catalog(args):
    if bool(args.tail) == bool(args.window_file):
        print('error: exactly one of --tail or --window-file is required', file=sys.stderr)
        return 2
    if not args.roll_file:
        print('error: --roll-file is required', file=sys.stderr)
        return 2
    if args.tail:
        _, _, st = load_state(args.root)
        window = st['log'][-args.tail:]
    else:
        with open(args.window_file, encoding='utf-8') as f:
            window = [l for l in (x.rstrip('\n').rstrip('\r') for x in f) if l.strip()]
    toks = set()
    for line in window:
        toks |= set(PAT.findall(line))
    with open(args.roll_file, encoding='utf-8') as f:
        roll = f.read()
    missing = sorted(t for t in toks if t not in roll)
    out = {
        'window_lines': len(window),
        'tokens_total': len(toks),
        'tokens': sorted(toks),
        'missing_in_roll': missing,
        'pass': not missing,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if not missing else 2


# --- closeout EOL repair (R1705 slice, AC-EO1..EO6 pre-registered in tech.md) ---
# R1697/R1704 both hit fold's E_STATE_LAYOUT refusal because a round's
# closeout wrote state.json with bare-LF line endings. This subcommand
# toolizes the manual byte surgery done in those rounds: report the EOL
# profile, and repair bare-LF terminators to CRLF with content bytes and
# JSON semantics untouched (verify-then-write).

BARE_LF = re.compile(r'(?<!\r)\n')


def eol_profile(raw):
    """Count terminator classes in raw (utf-8 bytes) without mutating."""
    text = raw.decode('utf-8')
    total_lf = text.count('\n')
    crlf = text.count('\r\n')
    bare_lf = total_lf - crlf
    lone_cr = text.count('\r') - crlf
    # indent conservation (R1710 lesson: a closeout json.dump re-write
    # destroyed the 16-space log-item canonical indent while CRLF stayed
    # healthy, escaping the eol check for three rounds). Same regex class
    # as split_ps_layout's item-line gate: '^ {16}"'.
    lines = re.split(r'\r\n|\n', text)
    log_start = None
    for i, ln in enumerate(lines):
        s = ln.strip()
        if s.startswith('"log"') and s.endswith('['):
            log_start = i
            break
    log_block_found = log_start is not None
    log_item_lines = indent16 = indent_anomaly = 0
    if log_block_found:
        for ln in lines[log_start + 1:]:
            s = ln.strip()
            if s == ']':
                break
            if not s:
                continue
            log_item_lines += 1
            if re.match(r'^ {16}"', ln):
                indent16 += 1
            else:
                indent_anomaly += 1
    return {
        'bytes': len(raw),
        'total_lf': total_lf,
        'crlf': crlf,
        'bare_lf': bare_lf,
        'lone_cr': lone_cr,
        'ends_with_eol': text.endswith('\n') or text.endswith('\r'),
        'layout_ok': bare_lf == 0 and lone_cr == 0,
        'log_block_found': log_block_found,
        'log_item_lines': log_item_lines,
        'indent16_lines': indent16,
        'indent_anomaly': indent_anomaly,
        'indent_ok': (not log_block_found) or indent_anomaly == 0,
    }


def eol_content_lines(text):
    """Terminator-insensitive line-content sequence (CRLF and LF both split)."""
    return re.split(r'\r\n|\n', text)


def fix_indent_text(text):
    """Re-indent log item lines to the 16-space canonical (R1710 manual
    byte surgery toolized, AC-FI2). Only item lines whose stripped body
    starts with a JSON string quote are touched; content bytes and each
    line's own EOL terminator are preserved (EOL disease stays with
    --fix; two diseases, two repairs). Returns (fixed_text, repaired)
    or (None, 0) when no log block exists (non-state shape)."""
    lines = text.splitlines(True)
    log_start = None
    for i, ln in enumerate(lines):
        s = ln.strip()
        if s.startswith('"log"') and s.endswith('['):
            log_start = i
            break
    if log_start is None:
        return None, 0
    out = list(lines)
    repaired = 0
    for j in range(log_start + 1, len(lines)):
        s = lines[j].strip()
        if s == ']':
            break
        if not s:
            continue
        body = lines[j]
        eol = ''
        if body.endswith('\r\n'):
            body, eol = body[:-2], '\r\n'
        elif body.endswith('\n'):
            body, eol = body[:-1], '\n'
        core = body.lstrip(' ')
        if core.startswith('"') and len(body) - len(core) != 16:
            out[j] = ' ' * 16 + core + eol
            repaired += 1
    return ''.join(out), repaired


def eol_fix_indent(args, path, raw, prof):
    """--fix-indent face: indent-only repair, dry-run default (AC-FI2..FI4)."""
    text = raw.decode('utf-8')
    out = {'file': path,
           'mode': 'fix-indent-execute' if args.execute else 'fix-indent-dry-run'}
    out.update(prof)
    fixed, repaired = fix_indent_text(text)
    if fixed is None:
        out['written'] = False
        out['note'] = 'no log block found (non-state shape): nothing to fix'
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0
    fixed_raw = fixed.encode('utf-8')
    new_prof = eol_profile(fixed_raw)
    out['repaired_lines'] = repaired
    out['predicted_bytes'] = len(fixed_raw)
    out['delta_bytes'] = len(fixed_raw) - len(raw)
    # triple verification, all before any write (AC-FI3)
    out['content_eq'] = ([l.strip() for l in eol_content_lines(text)]
                         == [l.strip() for l in eol_content_lines(fixed)])
    out['eol_eq'] = all(prof[k] == new_prof[k]
                        for k in ('bare_lf', 'crlf', 'lone_cr'))
    json_eq = None
    try:
        json_eq = json.loads(text) == json.loads(fixed)
    except ValueError:
        try:
            json.loads(text)
            json_eq = False  # raw parses, fixed does not: semantics broken
        except ValueError:
            json_eq = None   # non-JSON target (--file): equivalence n/a
    out['json_eq'] = json_eq
    out['verify_pass'] = (out['content_eq'] and out['eol_eq']
                          and json_eq is not False)
    if not out['verify_pass']:
        out['error'] = 'E_EOL_VERIFY: content/eol/json equivalence broken (refusing)'
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 2
    if repaired == 0:
        out['written'] = False
        if prof['indent_ok']:
            out['note'] = 'nothing to fix (indent already canonical)'
            print(json.dumps(out, ensure_ascii=False, indent=2))
            return 0
        # anomaly lines exist but none is indent-repairable: content
        # disease, not indent disease - fail-closed, no false green
        out['note'] = ('no indent-repairable item line found while '
                       'indent_anomaly > 0 (content disease?)')
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 2
    if not args.execute:
        out['note'] = 'dry-run: zero mutation'
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0
    dirname = os.path.dirname(path) or '.'
    fd, tmp = tempfile.mkstemp(prefix='eol_fixindent_', dir=dirname)
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(fixed_raw)
        os.replace(tmp, path)
    except OSError:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
    with open(path, 'rb') as f:
        on_disk = f.read()
    post = eol_profile(on_disk)
    out['written'] = True
    out['post_indent_anomaly'] = post['indent_anomaly']
    out['post_indent_ok'] = post['indent_ok']
    out['predicted_eq_actual'] = on_disk == fixed_raw
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if out['predicted_eq_actual'] and post['indent_ok'] else 2


def cmd_eol(args):
    if args.fix and args.fix_indent:
        print('error: --fix and --fix-indent are mutually exclusive '
              '(--fix is EOL-only, --fix-indent is indent-only)', file=sys.stderr)
        return 2
    if args.file:
        path = os.path.abspath(args.file)
    else:
        path = os.path.join(args.root, 'src', 'os', 'state.json')
    with open(path, 'rb') as f:
        raw = f.read()
    prof = eol_profile(raw)
    if args.fix_indent:
        return eol_fix_indent(args, path, raw, prof)
    text = raw.decode('utf-8')
    out = {'file': path, 'mode': 'check'}
    out.update(prof)
    if not args.fix:
        print(json.dumps(out, ensure_ascii=False, indent=2))
        # AC-LF2: exit green only when both the CRLF face (layout_ok) and
        # the indent conservation face (indent_ok) are green.
        return 0 if prof['layout_ok'] and prof['indent_ok'] else 2
    fixed_text = BARE_LF.sub('\r\n', text)
    fixed_raw = fixed_text.encode('utf-8')
    out['mode'] = 'fix-execute' if args.execute else 'fix-dry-run'
    out['predicted_bytes'] = len(fixed_raw)
    out['delta_bytes'] = len(fixed_raw) - len(raw)
    out['content_eq'] = eol_content_lines(text) == eol_content_lines(fixed_text)
    json_eq = None
    try:
        json_eq = json.loads(text) == json.loads(fixed_text)
    except ValueError:
        try:
            json.loads(text)
            json_eq = False  # raw parses, fixed does not: semantics broken
        except ValueError:
            json_eq = None   # non-JSON target (--file): equivalence n/a
    out['json_eq'] = json_eq
    out['verify_pass'] = out['content_eq'] and json_eq is not False
    if not out['verify_pass']:
        out['error'] = 'E_EOL_VERIFY: content or json equivalence broken (refusing)'
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 2
    if prof['bare_lf'] == 0:
        out['written'] = False
        out['note'] = 'nothing to fix (no bare-LF terminator)'
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0
    if not args.execute:
        out['note'] = 'dry-run: zero mutation'
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0
    dirname = os.path.dirname(path) or '.'
    fd, tmp = tempfile.mkstemp(prefix='eol_fix_', dir=dirname)
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(fixed_raw)
        os.replace(tmp, path)
    except OSError:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
    with open(path, 'rb') as f:
        on_disk = f.read()
    out['written'] = True
    out['post_bare_lf'] = eol_profile(on_disk)['bare_lf']
    out['predicted_eq_actual'] = on_disk == fixed_raw
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if out['post_bare_lf'] == 0 and out['predicted_eq_actual'] else 2


# --- fold surgery (R1687 slice, AC-LT8..LT14 pre-registered in tech.md) ---

def ps_escape(s):
    """Serialize one log string as a JSON literal in the on-disk PS 5.1
    style: json escaping plus JavaScriptSerializer-sensitive chars
    (observed live escapes: \\u003c for '<')."""
    j = json.dumps(s, ensure_ascii=False)
    for ch, esc in (('<', '\\u003c'), ('>', '\\u003e'),
                    ('&', '\\u0026'), ("'", '\\u0027')):
        j = j.replace(ch, esc)
    return j


def split_ps_layout(text, log_len):
    """Locate the log array item lines in the canonical PS layout.
    Returns (lines, log_start_idx, item_idx_list, close_idx) or None."""
    lines = text.split('\r\n')
    log_start = None
    for i, ln in enumerate(lines):
        s = ln.strip()
        if s.startswith('"log"') and s.endswith('['):
            log_start = i
            break
    if log_start is None:
        return None
    items, close_idx = [], None
    for j in range(log_start + 1, len(lines)):
        if lines[j].strip() == ']':
            close_idx = j
            break
        if not re.match(r'^ {16}"', lines[j]):
            return None
        items.append(j)
    if close_idx is None or len(items) != log_len:
        return None
    return lines, log_start, items, close_idx


def cmd_fold(args):
    # window selector: exactly one of --window-tail / --window-slice
    # (mid-window support; AC-LT20 pre-registered in tech.md R1690 claim)
    has_tail = args.window_tail > 0
    has_slice = args.window_slice is not None
    if has_tail == has_slice:
        print('error: exactly one of --window-tail / --window-slice is required',
              file=sys.stderr)
        return 2
    window_mode = 'slice' if has_slice else 'tail'
    w_start = w_end = None
    if has_slice:
        parts = str(args.window_slice).split(':')
        if len(parts) != 2:
            print('error: --window-slice must be START:END integers',
                  file=sys.stderr)
            return 2
        try:
            w_start, w_end = int(parts[0]), int(parts[1])
        except ValueError:
            print('error: --window-slice must be START:END integers',
                  file=sys.stderr)
            return 2
    for req, val in (('--round', args.round), ('--fold-no', args.fold_no),
                     ('--desc', args.desc), ('--summary-file', args.summary_file)):
        if not val:
            print('error: %s is required' % req, file=sys.stderr)
            return 2
    with open(args.summary_file, encoding='utf-8') as f:
        slines = [l for l in (x.rstrip('\n').rstrip('\r') for x in f) if l.strip()]
    if len(slines) != 1:
        print('error: summary file must hold exactly one non-empty line (got %d)'
              % len(slines), file=sys.stderr)
        return 2
    summary = slines[0]

    path, raw, st = load_state(args.root)
    text = raw.decode('utf-8')
    if '\r\n' not in text:
        print('error: E_STATE_LAYOUT: CRLF layout not found (refusing)', file=sys.stderr)
        print('hint: run: python src/os/logs_toolkit.py eol --fix --execute', file=sys.stderr)
        return 2
    layout = split_ps_layout(text, len(st['log']))
    if layout is None:
        print('error: E_STATE_LAYOUT: PS item-line layout mismatch (refusing)',
              file=sys.stderr)
        print('hint: run: python src/os/logs_toolkit.py eol --fix-indent --execute',
              file=sys.stderr)
        return 2
    lines, log_start, item_idx, close_idx = layout
    if window_mode == 'tail':
        if args.window_tail > len(st['log']):
            print('error: --window-tail exceeds log length', file=sys.stderr)
            return 2
        w_start = len(st['log']) - args.window_tail + 1  # 1-based inclusive
        w_end = len(st['log'])
    else:
        if w_start < 1 or w_end < w_start or w_end > len(st['log']):
            print('error: E_WINDOW_RANGE: --window-slice out of log bounds',
                  file=sys.stderr)
            return 2

    n = w_end - w_start + 1
    window = st['log'][w_start - 1:w_end]
    new_log = st['log'][:w_start - 1] + [summary] + st['log'][w_end:]

    # verifications (all BEFORE any write; R1157 write-before-verify lesson)
    toks = set()
    for line in window:
        toks |= set(PAT.findall(line))
    missing = sorted(t for t in toks if t not in summary)

    summary_literal = ' ' * 16 + ps_escape(summary)
    if w_end < len(st['log']):
        summary_literal += ','  # mid-window: item lines follow the summary
    first_window_idx = log_start + 1 + (w_start - 1)
    new_lines = (lines[:first_window_idx] + [summary_literal]
                 + lines[first_window_idx + n:])
    new_text = '\r\n'.join(new_lines)
    predicted = len(new_text.encode('utf-8'))
    gate_ok = predicted + args.reserve_bytes <= GATE

    now = datetime.now(CST)
    sha16 = hashlib.sha256(raw).hexdigest()[:16]
    backup_path = os.path.join(args.root, 'logs', 'state-preop-%s.bak' % args.round)
    archive = args.archive_file or os.path.join(
        args.root, 'logs', 'state-log-archive-%s.md' % now.strftime('%Y-%m'))
    date = now.strftime('%Y-%m-%d')
    header = ('# --- %s fold append (%s, %d lines verbatim: %s, '
              'fold R%s %s, pre-op sha16 %s)') % (
        args.round, date, len(window), args.desc, args.fold_no,
        'mid-window' if window_mode == 'slice' else 'window', sha16)
    archive_exists = os.path.exists(archive)
    appendix = (header + '\n' + '\n'.join(window) + '\n').encode('utf-8')
    preamble = None
    if archive_exists:
        with open(archive, 'rb') as f:
            blob = f.read()
        if blob and not blob.endswith(b'\n'):
            appendix = b'\n' + appendix
    elif args.allow_create:
        preamble = ('# logs/%s (created by logs_toolkit.py fold --allow-create %s)\n'
                    % (os.path.basename(archive), date)).encode('utf-8')

    verdicts = {
        'token_missing': missing,
        'token_ok': not missing,
        'gate_ok': gate_ok,
        'predicted_bytes': predicted,
        'reserve_bytes': args.reserve_bytes,
        'gate': GATE,
    }
    plan = {
        'mode': 'execute' if args.execute else 'dry-run',
        'round': args.round, 'fold_no': args.fold_no,
        'window_mode': window_mode, 'window_start': w_start,
        'window_end': w_end,
        'window_lines': len(window),
        'window_content_bytes': sum(len(x.encode('utf-8')) for x in window),
        'summary_head': summary[:60],
        'preop_sha16': sha16,
        'backup_path': backup_path,
        'archive_file': archive,
        'archive_header': header,
        'state_path': path,
        'pre_bytes': len(raw),
        'new_log_len': len(new_log),
        **verdicts,
    }
    fail = []
    if missing:
        fail.append('token-missing')
    if not gate_ok:
        fail.append('gate-exceed')
    if not archive_exists and not args.allow_create:
        fail.append('archive-missing')
    plan['would_fail'] = fail

    if not args.execute:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return 2 if fail else 0

    if fail:
        print('error: refusing fold, failed checks: %s' % ','.join(fail),
              file=sys.stderr)
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return 2

    # step 2: pre-op backup (byte-identical, read back)
    with open(backup_path, 'wb') as f:
        f.write(raw)
    with open(backup_path, 'rb') as f:
        if f.read() != raw:
            print('error: backup verify failed', file=sys.stderr)
            return 2

    # step 3: archive append (single write, byte-verified)
    if archive_exists:
        with open(archive, 'rb') as f:
            before_blob = f.read()
        with open(archive, 'ab') as f:
            f.write(appendix)
        with open(archive, 'rb') as f:
            after_blob = f.read()
        archive_ok = after_blob == before_blob + appendix
    else:
        blob = preamble + appendix
        with open(archive, 'wb') as f:
            f.write(blob)
        with open(archive, 'rb') as f:
            archive_ok = f.read() == blob
    if not archive_ok:
        print('error: archive append verification failed', file=sys.stderr)
        return 2

    # step 4: state.json write (temp + atomic replace), verify-then-read
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), prefix='.state-fold-')
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(new_text.encode('utf-8'))
        os.replace(tmp, path)
    except OSError:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise
    with open(path, 'rb') as f:
        post_raw = f.read()
    post_st = json.loads(post_raw.decode('utf-8'))
    ok_write = (post_raw == new_text.encode('utf-8')
                and post_st['log'] == new_log
                and os.path.getsize(path) == predicted)
    result = {
        **plan,
        'post_bytes': os.path.getsize(path),
        'predicted_eq_actual': ok_write,
        'appendix_bytes': len(appendix),
        'archive_appended': True,
        'backup_written': True,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not ok_write:
        print('error: post-write verification failed', file=sys.stderr)
        return 2
    return 0


# --- census (archive reverse reconciliation, R1688 slice, AC-LT15..LT19
# pre-registered in state/queue/tech.md) ---

# section pointer marker (U+00A7) and original-archive marker (U+539F)
# kept as ASCII \u escapes in patterns per encoding law
CEN_PTR = re.compile(r'\u00a7R([0-9]{2,})')
CEN_FILE_ORIG = re.compile(r'state-log-archive-(\d{4}-\d{2})\.md(.{0,4})\u539f')
CEN_HEADER = re.compile(r'^# --- (R\d+) (.*)$')
CEN_DECLARED = re.compile(r'(\d+) lines verbatim')


def parse_archives(root):
    """Parse all logs/state-log-archive-*.md into (files, sections).

    files: {month: {'path','bytes','sections': [section dicts]}}
    sections: {'R####': first section dict with that round tag}
    section dict: {'round','file','header','declared'(int|None),'lines'}
    """
    ldir = os.path.join(root, 'logs')
    files, sections = {}, {}
    if not os.path.isdir(ldir):
        return files, sections
    for entry in sorted(os.scandir(ldir), key=lambda e: e.name):
        m = re.match(r'^state-log-archive-(\d{4}-\d{2})\.md$', entry.name)
        if not m or not entry.is_file():
            continue
        month = m.group(1)
        with open(entry.path, 'rb') as f:
            raw = f.read()
        text = raw.decode('utf-8')
        cur = None
        secs = []
        for ln in text.split('\n'):
            hm = CEN_HEADER.match(ln)
            if hm:
                cur = {'round': hm.group(1), 'file': month, 'header': ln,
                       'declared': None, 'lines': []}
                dm = CEN_DECLARED.search(hm.group(2))
                if dm:
                    cur['declared'] = int(dm.group(1))
                secs.append(cur)
                if cur['round'] not in sections:
                    sections[cur['round']] = cur
            elif cur is not None:
                cur['lines'].append(ln)
        files[month] = {'path': entry.path, 'bytes': len(raw), 'sections': secs}
    return files, sections


def load_known_findings(path):
    """Load adjudicated known-findings data file (may be absent = none).

    Returns ({known mismatch rounds -> reason}, {known dangling ptrs -> reason}).
    Known findings stay visible in output but are excluded from the FAIL
    verdict; every entry requires an evidence-backed adjudication (R1688).
    """
    if not path or not os.path.exists(path):
        return {}, {}
    with open(path, encoding='utf-8') as f:
        d = json.load(f)
    mm = {e['round']: e.get('reason', '') for e in d.get('section_line_mismatches', [])}
    dg = {e['pointer']: e.get('reason', '') for e in d.get('dangling_pointers', [])}
    return mm, dg


def cmd_census(args):
    _, _, st = load_state(args.root)
    files, sections = parse_archives(args.root)
    known_path = args.known_file or os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 'census_known_findings.json')
    known_mm, known_dg = load_known_findings(known_path)

    # (1) section integrity: declared vs actual non-empty verbatim lines
    # (fold-append headers only; legacy 09-format headers carry no declared)
    mismatches = []
    sec_tokens = {}
    all_archive_toks = set()
    for month, finfo in sorted(files.items()):
        for s in finfo['sections']:
            toks = set()
            for l in s['lines']:
                toks |= set(PAT.findall(l))
            sec_tokens[s['round']] = toks
            all_archive_toks |= toks
            if s['declared'] is None:
                continue
            actual = len([l for l in s['lines'] if l.strip()])
            if s['declared'] != actual:
                e = {'round': s['round'], 'file': month,
                     'declared': s['declared'], 'actual': actual,
                     'adjudicated': s['round'] in known_mm}
                if e['adjudicated']:
                    e['reason'] = known_mm[s['round']]
                mismatches.append(e)

    # (2)+(3) pointer resolution + informational token census
    pointer_lines = []
    dangling_total = 0
    live_toks = set()
    for line in st['log']:
        live_toks |= set(PAT.findall(line))
        ptrs = ['R' + p for p in CEN_PTR.findall(line)]
        origs = sorted(set(m.group(1) for m in CEN_FILE_ORIG.finditer(line)))
        if not ptrs and not origs:
            continue
        line_toks = set(PAT.findall(line))
        dangling = [p for p in ptrs if p not in sections]
        dangling_total += len(dangling)
        union_toks = set()
        not_embedded = {}
        for p in ptrs:
            if p not in sections:
                continue
            t = sec_tokens.get(p, set())
            union_toks |= t
            miss = sorted(t - line_toks)
            if miss:
                not_embedded[p] = miss
        for month in origs:
            if month in files:
                for s in files[month]['sections']:
                    union_toks |= sec_tokens.get(s['round'], set())
        pointer_lines.append({
            'head': line[:60],
            'pointers': ptrs,
            'file_refs': origs,
            'dangling': dangling,
            'not_embedded': not_embedded,
            'roll_native': sorted(line_toks - union_toks),
        })

    archive_only = sorted(all_archive_toks - live_toks)
    unknown_mismatches = [m for m in mismatches if not m['adjudicated']]
    live_dangling = set()
    for pl in pointer_lines:
        live_dangling |= set(pl['dangling'])
    dangling_known = [{'pointer': p, 'reason': known_dg[p]}
                      for p in sorted(live_dangling & set(known_dg))]
    unknown_dangling_total = len(live_dangling - set(known_dg))
    out = {
        'files': {m: {'path': f['path'], 'bytes': f['bytes'],
                      'sections': len(f['sections'])}
                  for m, f in sorted(files.items())},
        'sections_total': sum(len(f['sections']) for f in files.values()),
        'section_line_mismatches': mismatches,
        'pointer_lines': pointer_lines,
        'dangling_total': dangling_total,
        'known_findings_file': known_path if os.path.exists(known_path) else None,
        'dangling_known': dangling_known,
        'unknown_mismatch_count': len(unknown_mismatches),
        'unknown_dangling_count': unknown_dangling_total,
        'archive_tokens_total': len(all_archive_toks),
        'live_tokens_total': len(live_toks),
        'archive_only_count': len(archive_only),
        'archive_only_tokens': archive_only,
        'pass': not unknown_mismatches and unknown_dangling_total == 0,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if out['pass'] else 2


def main(argv=None):
    p = argparse.ArgumentParser(prog='logs_toolkit.py', description=__doc__)
    p.add_argument('--root', default=default_root(), help='repo root (default: auto)')
    sub = p.add_subparsers(dest='cmd', required=True)

    sub.add_parser('gauge', help='water report for src/os/state.json')
    sub.add_parser('inventory', help='logs/ class breakdown')
    pt = sub.add_parser('tail', help='state.json log tail inventory')
    pt.add_argument('-n', type=int, default=10)
    pp = sub.add_parser('prune', help='logs/ retention enforcement')
    pp.add_argument('--execute', action='store_true', help='actually delete (default: dry-run)')
    pp.add_argument('--floor-seconds', type=int, default=DEFAULT_FLOOR)
    pc = sub.add_parser('catalog', help='window token extraction + presence check')
    pc.add_argument('--tail', type=int, help='window = last N state log lines')
    pc.add_argument('--window-file', help='window = non-empty lines of this file')
    pc.add_argument('--roll-file', required=False, help='roll/summary text to check presence against')
    cn = sub.add_parser('census', help='archive reverse reconciliation census (read-only)')
    cn.add_argument('--known-file', help='adjudicated known-findings data file '
                    '(default: census_known_findings.json alongside this tool)')
    pe = sub.add_parser('eol', help='state.json closeout EOL repair (bare-LF report + CRLF surgery)')
    pe.add_argument('--file', default=None, help='target file (default: src/os/state.json)')
    pe.add_argument('--fix', action='store_true', help='perform CRLF surgery (default: read-only check)')
    pe.add_argument('--fix-indent', action='store_true',
                    help='re-indent log item lines to the 16-space canonical '
                         '(mutually exclusive with --fix; default: dry-run)')
    pe.add_argument('--execute', action='store_true', help='with --fix/--fix-indent: actually write (default: dry-run)')
    pf = sub.add_parser('fold', help='state.json fold surgery (verify-then-write)')
    pf.add_argument('--round', help='round label e.g. R1687 (backup + header naming)')
    pf.add_argument('--fold-no', help='fold knife number e.g. 455 (header)')
    pf.add_argument('--desc', help='window description for the archive header')
    pf.add_argument('--window-tail', type=int, default=0, help='window = last N log lines')
    pf.add_argument('--window-slice', default=None,
                    help='window = log lines START:END (1-based inclusive, mid-array)')
    pf.add_argument('--summary-file', help='file holding exactly one non-empty summary line')
    pf.add_argument('--reserve-bytes', type=int, default=3000)
    pf.add_argument('--archive-file', help='override archive path (default: logs/state-log-archive-<month>.md)')
    pf.add_argument('--allow-create', action='store_true', help='create archive if missing (else fail-closed)')
    pf.add_argument('--execute', action='store_true', help='perform surgery (default: dry-run, zero mutation)')

    args = p.parse_args(argv)
    handlers = {'gauge': cmd_gauge, 'inventory': cmd_inventory, 'tail': cmd_tail,
                'prune': cmd_prune, 'catalog': cmd_catalog, 'fold': cmd_fold,
                'census': cmd_census, 'eol': cmd_eol}
    if args.cmd not in handlers:
        return 2
    try:
        return handlers[args.cmd](args)
    except (OSError, ValueError, json.JSONDecodeError) as e:
        print('error: %s' % e, file=sys.stderr)
        return 3


if __name__ == '__main__':
    sys.exit(main())
